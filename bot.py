import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from storage import NoteStorage
from utils import format_notes_response, format_help_message
from config import BOT_TOKEN, NOTES_FILE

logger = logging.getLogger(__name__)

class NoteBot:
    def __init__(self):
        self.storage = NoteStorage(NOTES_FILE)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command"""
        welcome_message = (
            "👋 Welcome to NoteTaker Bot!\n\n"
            "I can help you take and manage your notes.\n"
            f"{format_help_message()}"
        )
        await update.message.reply_text(welcome_message)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command"""
        await update.message.reply_text(format_help_message())

    async def note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /note command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide some text for your note.\n"
                "Example: /note Remember to buy milk"
            )
            return

        note_text = ' '.join(context.args)
        user_id = update.effective_user.id

        if self.storage.add_note(user_id, note_text):
            await update.message.reply_text("✅ Note saved successfully!")
        else:
            await update.message.reply_text("❌ Failed to save note. Please try again.")

    async def ask(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /ask command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a search term.\n"
                "Example: /ask milk"
            )
            return

        query = ' '.join(context.args)
        user_id = update.effective_user.id
        matching_notes = self.storage.search_notes(user_id, query)

        response = format_notes_response(matching_notes)
        await update.message.reply_text(response)

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Error occurred: {context.error}")
        if isinstance(update, Update):
            await update.message.reply_text(
                "❌ An error occurred while processing your request. Please try again."
            )

    def run(self):
        """Run the bot"""
        try:
            # Create application and pass bot token
            application = Application.builder().token(BOT_TOKEN).build()

            # Add handlers
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(CommandHandler("help", self.help))
            application.add_handler(CommandHandler("note", self.note))
            application.add_handler(CommandHandler("ask", self.ask))

            # Add error handler
            application.add_error_handler(self.error_handler)

            # Start the bot
            application.run_polling()
        except Exception as e:
            logger.error(f"Failed to start bot: {str(e)}")
            raise