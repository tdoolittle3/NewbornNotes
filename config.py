import os

# Telegram Bot Token - Use environment variable
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'DEBUG'
