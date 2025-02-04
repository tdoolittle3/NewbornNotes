from utils import setup_logging
from config import LOG_FORMAT, LOG_LEVEL
from bot import NoteBot

def main():
    # Setup logging
    setup_logging(LOG_FORMAT, LOG_LEVEL)
    
    # Create and run the bot
    bot = NoteBot()
    bot.run()

if __name__ == "__main__":
    main()
