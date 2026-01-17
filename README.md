# DTEK Python Project

A Python project with Telegram bot integration for sending messages with time-based restrictions.

## Features

- **Telegram Bot Integration**: Send messages to Telegram chats
- **Time-based Restrictions**: Restrict message sending between 23:30 and 00:30 (unless forced)
- **Silent Mode**: Send notifications without sound
- **Force Send**: Override time restrictions when needed
- **Environment Configuration**: All parameters managed via .env file

## Project Structure

```
dtek_python/
├── .github/
│   └── copilot-instructions.md
├── src/
│   ├── __init__.py
│   ├── main.py
│   └── telegram_bot.py
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── test_telegram_bot.py
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

## Getting Started

### 1. Set up virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows
# source venv/bin/activate      # On macOS/Linux
```

### 2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables:

Create a `.env` file in the project root:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
LOG_LEVEL=INFO
DEBUG=False
```

To get your bot token:
1. Create a bot with [@BotFather](https://t.me/botfather) on Telegram
2. Copy the token provided

To get your chat ID:
1. Add your bot to a chat
2. Send any message
3. Get updates from bot: `https://api.telegram.org/bot<TOKEN>/getUpdates`

### 4. Run the project:
```bash
python src/main.py
```

### 5. Run tests:
```bash
python -m pytest tests/ -v
```

## Telegram Bot Usage

### Basic Example

```python
from src.telegram_bot import TelegramBot

# Initialize bot
bot = TelegramBot()

# Send a simple message
bot.send_message_sync(
    text="Hello from Telegram Bot!",
    chat_id="123456789"
)
```

### With Silent Mode

```python
# Send without notification sound
bot.send_message_sync(
    text="Silent message",
    chat_id="123456789",
    silent_mode=True
)
```

### With Time Restrictions

```python
# Between 23:30 and 00:30, you must set force_send=True
try:
    bot.send_message_sync(
        text="Night time message",
        chat_id="123456789",
        force_send=True  # Override time restriction
    )
except ValueError as e:
    print(f"Error: {e}")
```

### Check Restricted Time Status

```python
info = bot.get_restricted_time_info()
print(f"Current time: {info['current_time']}")
print(f"Restricted: {info['restricted_time_active']}")
print(f"Window: {info['restriction_window']}")
```

## Telegram Bot Class Reference

### TelegramBot

#### `__init__()`
Initializes the bot with credentials from environment variables.

**Required Environment Variables:**
- `TELEGRAM_BOT_TOKEN`: Your bot token
- `TELEGRAM_CHAT_ID`: Default chat ID (optional, can be overridden per message)

#### `send_message_sync(text, chat_id=None, silent_mode=False, force_send=False)`
Synchronous method to send a message.

**Parameters:**
- `text` (str): Message text
- `chat_id` (str, optional): Target chat ID (uses default if not provided)
- `silent_mode` (bool): If True, sends without notification (default: False)
- `force_send` (bool): If True, bypasses time restrictions (default: False)

**Returns:** bool - True if sent successfully, False otherwise

**Raises:**
- `ValueError`: If no chat_id available or message blocked by time restriction
- `TelegramError`: If Telegram API returns an error

#### `_is_restricted_time()`
Checks if current time is in the restricted window (23:30 - 00:30).

**Returns:** bool - True if in restricted time, False otherwise

#### `get_restricted_time_info()`
Returns information about the restricted time window.

**Returns:** dict with keys:
- `restricted_time_active`: Current restriction status
- `current_time`: Current time in HH:MM:SS format
- `restriction_window`: Time window description

## Time Restriction Logic

- **Restricted Period**: 23:30 - 00:30 (11:30 PM - 12:30 AM)
- **During Restricted Time**: Messages blocked unless `force_send=True`
- **Outside Restricted Time**: Messages sent normally
- **Use Case**: Avoid notifications during night hours, with emergency override

## Requirements

- Python 3.8+
- python-telegram-bot >= 20.0
- python-dotenv >= 1.0.0
- pytest >= 7.0.0

## License

MIT

