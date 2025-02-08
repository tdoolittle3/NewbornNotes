from utils import setup_logging
from config import LOG_FORMAT, LOG_LEVEL
from bot import NoteBot

import time
import logging

def main():
    # Setup logging
    setup_logging(LOG_FORMAT, LOG_LEVEL)
    logger = logging.getLogger(__name__)
    
    while True:
        try:
            # Create and run the bot
            bot = NoteBot()
            bot.run()
        except Exception as e:
            logger.error(f"Bot crashed with error: {e}")
            logger.info("Restarting bot in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    main()
