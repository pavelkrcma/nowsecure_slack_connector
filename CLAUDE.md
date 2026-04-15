# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Slack bot that monitors NowSecure Platform assessment notifications and automates PDF report downloads. Also provides `/appvetting` slash command to trigger new security assessments from App Store URLs.

## Architecture

Single-file application (`main.py`) using Slack Bolt framework with Socket Mode. Key workflows:

1. **Message Handler**: Listens for "NowSecure Platform" bot messages, extracts assessment ID from URL, downloads PDF via NowSecure API, uploads to Slack thread
2. **Slash Command**: `/appvetting new <client_tag> <url>` parses App Store URLs, resolves bundle IDs (iTunes API for iOS), triggers assessment via NowSecure Lab API
3. **Healthcheck Loop**: Background thread pings HC_URL every 5 minutes

### API Integration Points

- **NowSecure Report API**: `https://api.nowsecure.com/report/assessment/ref/{assessment_id}.pdf` - requires Bearer token, has various query params for report customization
- **NowSecure Lab API**: `https://lab-api.nowsecure.com/app/{platform}/{bundle_id}/assessment/` - handles 429 rate limits with Retry-After header
- **iTunes Lookup API**: `https://itunes.apple.com/{country_code}/lookup?id={app_id}` - resolves numeric App ID to bundle ID

### Error Handling

- PDF size validation: <120KB triggers failure notification and user mention
- Assessment status codes: BINARY_UNAVAILABLE/BINARY_RESTORING trigger 60s retry
- Rate limiting: 429 responses retry up to 4 times with Retry-After delay
- Failed assessments: In-channel notification with user mention to U08TH7V81R9

## Development Commands

Run the bot:
```bash
uv run main.py
# or
python main.py
```

Install dependencies:
```bash
uv sync
# or
pip install -r requirements.txt
```

## Configuration

Required environment variables in `.env`:
- `SLACK_BOT_TOKEN` - bot OAuth token (xoxb-)
- `SLACK_APP_TOKEN` - app-level token for Socket Mode (xapp-)
- `NOWSECURE_API_TOKEN` - NowSecure Platform API token
- `GROUP_ID` - NowSecure group UUID
- `HC_URL` - healthcheck endpoint

Bot manifest at `slack_bot_manifest.json` defines permissions: channels:history, channels:read, chat:write, files:write, commands.

## Testing Slash Command

Message parsing regex patterns:
- iOS: `/id(\d+)` extracts numeric App ID from apple.com URLs
- Android: `id` query parameter from play.google.com URLs
- Country code extraction for iOS from URL path segments, defaults to 'us'

Valid client_tag: Cannot be "clienttag" or "client_tag" placeholders.

Appvetting requests logged to `appvetting.log` with timestamp, client_tag, URL.
