# Magic Discord Bot

A Discord bot with spam commands and Flask web server integration.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
   - Copy `.env.example` to `.env` (if available)
   - Add your Discord bot token to `.env`:
```
DISCORD_TOKEN=your_discord_bot_token_here
```

3. Run the bot:
```bash
python app.py
```

## Features

- **Spam Commands**: Send spam requests to Free Fire players
- **Channel Management**: Configure allowed channels for spam commands
- **Web Server**: Flask server for health checks
- **Logging**: Comprehensive logging system

## Commands

- `/spam <uid> <server>` - Send spam requests to a Free Fire player
- `/setspamchannel <channel>` - Allow a channel for spam commands (Admin only)
- `/removespamchannel <channel>` - Remove a channel from spam commands (Admin only)
- `/spamchannels` - List allowed channels for spam commands

## Configuration

The bot uses JSON files for configuration:
- `spam_channels.json` - Channel permissions per server
- `allowed_guilds.json` - Guild configuration (created automatically)

## Requirements

- Python 3.8+
- Discord bot token
- Required packages (see requirements.txt)
