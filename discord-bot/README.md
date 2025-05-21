
## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Commands](#commands)
- [Events](#events)
- [Configuration](#configuration)
- [Logging](#logging)

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd discord-bot
   ```

2. Install the dependencies:
   ```
   npm install
   ```

3. Create a `.env` file in the root directory and add your Discord bot token and other environment variables:
   ```
   DISCORD_TOKEN=your_discord_bot_token
   ```

## Usage

To start the bot, run the following command:
```
npm start
```

The bot will connect to Discord and be ready to respond to commands and events.

## Commands

The bot currently supports the following commands:
- `!hello`: Responds with a greeting message.

## Events

The bot listens for various events, including:
- `messageCreate`: Processes new messages in channels.
- `ready`: Triggered when the bot successfully connects to Discord.

## Configuration

Configuration settings are loaded from the `.env` file. Ensure that all required environment variables are set before starting the bot.

## Logging

The bot includes a logging utility to log messages with different severity levels. This helps in monitoring the bot's activity and debugging issues.