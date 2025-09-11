import os
import re
import json
import requests
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from datetime import datetime

# Configure the logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] - %(message)s')

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Validate required environment variables early
required_env_vars = ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "NOWSECURE_API_TOKEN", "GROUP_ID"]
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]

if missing_vars:
    print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
    print("\nPlease set the following environment variables:")
    print("- SLACK_BOT_TOKEN: Your bot token (starts with xoxb-)")
    print("- SLACK_APP_TOKEN: Your app token for Socket Mode (starts with xapp-)")
    print("- NOWSECURE_API_TOKEN: Your NowSecure API token")
    print("- GROUP_ID: Your NowSecure group ID (UUID)")
    print("\nYou can create a .env file based on .env.example")
    exit(1)

# Initialize the Slack app with Socket Mode
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

@app.message()
def handle_message(message, say, client):
    """
    Handle all messages and look for NowSecure assessment notifications.
    """
    #DEBUG: message=json.loads('{"user": "U08V222T3UG", "type": "message", "ts": "1753295337.014299", "bot_id": "B08V222T3DE", "app_id": "A05KZDQCUBS", "text": "A new Assessment is available for Windy", "team": "T08TH7V7XTM", "bot_profile": {"id": "B08V222T3DE", "deleted": false, "name": "NowSecure Platform", "updated": 1748443888, "app_id": "A05KZDQCUBS", "user_id": "U08V222T3UG", "icons": {"image_36": "https://avatars.slack-edge.com/2023-09-05/5851506896994_3f8f02a454ac334e9a50_36.png", "image_48": "https://avatars.slack-edge.com/2023-09-05/5851506896994_3f8f02a454ac334e9a50_48.png", "image_72": "https://avatars.slack-edge.com/2023-09-05/5851506896994_3f8f02a454ac334e9a50_72.png"}, "team_id": "T08TH7V7XTM"}, "blocks": [{"type": "header", "block_id": "E0WXk", "text": {"type": "plain_text", "text": "A new Assessment is available for Windy", "emoji": true}}, {"type": "section", "block_id": "AT7lw", "text": {"type": "mrkdwn", "text": "A new Assessment is available for Windy. Click below to view details in NowSecure Platform.", "verbatim": false}}, {"type": "actions", "block_id": "Link1", "elements": [{"type": "button", "action_id": "Kenb+", "text": {"type": "plain_text", "text": "View Assessment", "emoji": true}, "value": "View Assessment", "url": "https://app.nowsecure.com/app/4e64d9f2-67ea-11f0-b9a8-aff90e5cdf17/assessment/51ae3f5e-67ea-11f0-a4ca-13a2b5de6b23"}]}], "channel": "C08UK5BBA90", "event_ts": "1753295337.014299", "channel_type": "channel"}')

    # Get message details
    channel = message.get("channel")
    text = message.get("text", "")
    ts = message.get("ts")

    logging.debug(f"Received Slack message: {message}")

    # Check if the message is from the NowSecure bot
    if not message.get('bot_profile', {}).get('name') == 'NowSecure Platform':
        return  # Ignore other messages

    match = re.search(r"A new Assessment is available for (.+)$", text)
    if not match:
        match = re.search(r"The latest assessment for (.+) failed$", text)
    if not match:
        logging.debug("No NowSecure assessment notification found in the message.")
        return
    app_name = match.group(1).strip()

    # Extract the assessment URL from the message blocks
    assessment_url = None
    blocks = message.get("blocks", [])
    for block in blocks:
        if block.get("type") == "actions":
            elements = block.get("elements", [])
            for element in elements:
                if element.get("type") == "button" and element.get("value") == "View Assessment" and "url" in element:
                    assessment_url = element["url"]
                    break
            if assessment_url:
                break

    match = re.search(r"/assessment/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$", assessment_url)
    if match:
        assessment_id = match.group(1)
        logging.info(f"Found NowSecure assessment notification for app '{app_name}' with assessment ID: {assessment_id}")
    else:
        logging.warning(f"No valid assessment ID found in the URL: {assessment_url}")
        return

    pdf_url = (
        f"https://api.nowsecure.com/report/assessment/ref/{assessment_id}.pdf?"
        "status=detected&screenshots=false&finding.stepsToReproduce=false"
        "&finding.businessImpact=false&finding.remediationResources=false"
        "&evidenceFormats[]=inline"
    )
    headers = {"Authorization": f"Bearer {os.environ.get("NOWSECURE_API_TOKEN")}"}

    try:
        pdf_response = requests.get(pdf_url, headers=headers)
        pdf_response.raise_for_status()
        pdf_bytes = pdf_response.content
    except Exception as e:
        logging.error(f"Error downloading PDF: {e}")
        return

    logging.info(f"Downloaded PDF report for assessment ID: {assessment_id}, size: {len(pdf_bytes)} bytes")

    try:
        upload_response = client.files_upload_v2(
            channel=channel,
            file=pdf_bytes,
            filename=f"report-{assessment_id}.pdf",
            title=f"PDF report for app '{app_name}'",
            initial_comment=f"PDF report for app '{app_name}'",
            thread_ts=ts
        )
        logging.info(f"Uploaded PDF report to Slack: {upload_response}")
    except Exception as e:
        logging.error(f"Error uploading PDF to Slack: {e}")

"""
    reply_text = f"📱 New assessment detected for: **{app_name}**\n🔍 Processing NowSecure assessment notification..."

    try:
        client.chat_postMessage(
            channel=channel,
            text=reply_text,
            thread_ts=ts  # This makes it a threaded reply
        )
        print(f"Successfully replied to message with app name: {app_name}")
    except Exception as e:
        print(f"Error posting reply: {e}")
"""

@app.error
def error_handler(error, body, logger):
    logger.exception(f"Error: {error}")

@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)

def trigger_nowsecure_assessment(platform, bundle_id):
    """
    Trigger Application Assessment on NowSecure platform.
    
    This function submits an application for security assessment on the NowSecure platform.
    The application is identified by its platform (iOS/Android) and bundle ID.
    
    Args:
        platform (string): Platform of the application. Could be 'ios' or 'android'.
        bundle_id (string): Bundle ID/Package name of the application.
                           Example: 'com.openai.chatgpt'
    
    Returns:
        tuple: (success: bool, text: str)
               - success: True if submission was successful, False otherwise
               - text: Status message from the API or error description
               
    Example:
        >>> success, status = trigger_nowsecure_assessment("android", "com.openai.chatgpt")
        >>> print(f"Success: {success}, Status: {status}")
        Success: True, Status: pending
        
    API Details:
        - Makes POST request to NowSecure Lab API
        - Requires NOWSECURE_API_TOKEN and GROUP_ID environment variables
        - Returns task_status on success, error message on failure
    """

    logging.info(f"Triggering NowSecure assessment for {platform} app with bundle ID: {bundle_id}")

    # Validate input parameters
    if not platform or not bundle_id:
        return False, "Both platform and bundle_id parameters are required"
    
    # Validate platform
    if platform not in ['ios', 'android']:
        return False, "Platform must be either 'ios' or 'android'"
    
    url = f"https://lab-api.nowsecure.com/app/{platform}/{bundle_id}/assessment/?appstore_download=*&group={os.environ.get('GROUP_ID')}"
    headers = {"Authorization": f"Bearer {os.environ.get('NOWSECURE_API_TOKEN')}"}
    
    try:
        response = requests.post(url, headers=headers)
        response_data = response.json()
        logging.debug(f"NowSecure API response: {response_data}")

        if response.status_code >= 200 and response.status_code < 300:
            # Success case
            task_status = response_data.get('task_status', 'unknown')
            return True, task_status
        else:
            # Error case
            error_message = response_data.get('message', f'HTTP {response.status_code} error')
            return False, error_message
            
    except requests.exceptions.RequestException as e:
        return False, f"Network error: {str(e)}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON response: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def process_appvetting_new(url):
    logging.info(f"Processing new appvetting request for URL: {url}")

    # Basic URL validation
    try:
        parsed = urllib.parse.urlparse(url)
        if not (parsed.scheme and parsed.netloc):
            return "❌ Invalid URL"
    except Exception:
        return "❌ Invalid URL"

    # Android
    if url.startswith("https://play.google.com/store/apps/"):
        query = urllib.parse.parse_qs(parsed.query)
        bundle_id = query.get("id", [None])[0]
        if not bundle_id:
            return "❌ Invalid URL or unable to extract package name."

        # Trigger NowSecure assessment
        success, status_text = trigger_nowsecure_assessment('android', bundle_id)
        if success:
            return(f"✅ Android app `{bundle_id}` referred by {url} submitted for assessment.\nStatus: {status_text}")
        else:
            return(f"❌ Failed to submit Android app `{bundle_id}` for assessment.\nError: {status_text}")

    # iOS
    if url.startswith("https://apps.apple.com/"):
        # Extract numeric id from the URL (after '/id' and before optional '?')
        match = re.search(r'/id(\d+)', url)
        if not match:
            return "❌ Invalid URL or unable to extract bundle ID."
        app_id = match.group(1)
        # Call iTunes lookup API
        try:
            resp = requests.get(f"https://itunes.apple.com/lookup?id={app_id}", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            bundle_id = data["results"][0]["bundleId"] if data.get("resultCount", 0) > 0 else None
            if not bundle_id:
                return "❌ Invalid app ID."
        except Exception:
            return "❌ Unable to retrieve bundle ID."

        # Trigger NowSecure assessment
        success, status_text = trigger_nowsecure_assessment('ios', bundle_id)
        if success:
            return(f"✅ iOS app `{bundle_id}` referred by {url} submitted for assessment.\nStatus: {status_text}")
        else:
            return(f"❌ Failed to submit iOS app `{bundle_id}` for assessment.\nError: {status_text}")

    # Unknown
    return "❌ Invalid App Store URL"

@app.command("/appvetting")
def handle_appvetting_command(ack, respond, command):
    """Handle the /appvetting slash command"""
    ack() # Acknowledge the command request

    help_text = """
*Appvetting Command Help*

*Usage:*
• `/appvetting` - Show this help message
• `/appvetting new client_tag <app-store-url>` - Submit a new app for vetting

*Examples:*
• `/appvetting new Schindler https://apps.apple.com/us/app/rakuten-viber-messenger/id382617920`
• `/appvetting new Fannie_Mae https://play.google.com/store/apps/details?id=com.sadadcompany.sadad&hl=en_IN&pli=1`

Note: The `client_tag` is a short identifier for your reference (no spaces).
"""

    # Get the command text (everything after /appvetting)
    text = command.get('text', '').strip()
    
    if not text:
        # No parameters - show help
        respond(help_text)
        return

    # Parse the command
    parts = text.split()
    subcommand = parts[0].lower()

    if subcommand == "new":
        if len(parts) < 3:
            respond("❌ Missing client_tag or URL parameter")
            return

        client_tag = parts[1]
        url = parts[2]

        # Log the appvetting request to file
        log_entry = f"{datetime.now().isoformat()} - {client_tag} - {url}\n"
        try:
            with open("appvetting.log", "a") as log_file:
                log_file.write(log_entry)
        except Exception as e:
            logging.error(f"Failed to write to appvetting.log: {e}")

        respond(process_appvetting_new(url))

    elif subcommand == "help":
        respond(help_text)
        
    else:
        respond(f"❌ Unknown command: `{subcommand}`\n\n{help_text}")

if __name__ == "__main__":
    # Start the Socket Mode handler
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
