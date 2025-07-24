# NowSecure Appvetting Slack Connector

Performs basic operations on the NowSecure app inventory via the Slack channel. This bot monitors a channel for NowSecure platform assessment notifications and responds automatically.

## Features

- Monitors Slack channels for NowSecure assessment notifications
- Downloads the report in PDF and replies in the thread
- Implements /appvetting command

## Setup

### 1. Create a Slack App

Go to [Slack API](https://api.slack.com/apps) and create a new app using manifest slack_bot_manifest.json

### 2. Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Fill in your tokens in the `.env` file:
   ```bash
   SLACK_BOT_TOKEN=xoxb-your-bot-token-here
   SLACK_APP_TOKEN=xapp-your-app-token-here
   NOWSECURE_API_TOKEN=nowsecuretoken
   GROUP_ID=UUID
   ```

GROUP_ID is UUID of the corresponding NowSecure group

### 3. Install Dependencies

Using uv (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

### 4. Run the Bot

```bash
python main.py
uv run main.py
```

## Usage

The bot automatically monitors all channels it has access to and looks for messages from NowSecure bot. When such a message is detected, PDF report is downloaded and posted in a thread.
To trigger a new assessment use /appvetting command. Without parameters the command shows help.
