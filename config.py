import os

# Telegram Bot Token - Use environment variable
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Storage file path
NOTES_FILE = "notes.json"

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'DEBUG'