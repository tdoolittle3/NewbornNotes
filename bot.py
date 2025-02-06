import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, BotCommand, BotCommandScopeDefault, MenuButtonCommands
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from dbstorage import NoteStorage
from utils import format_notes_response, format_help_message
from config import BOT_TOKEN
from notes_summarizer import NotesSummarizer
import os

logger = logging.getLogger(__name__)

# Define conversation states
ASKING = 1
NOTING = 2

class NoteBot:
    def __init__(self):
        self.storage = NoteStorage("notes.db")
        openai_key = os.environ.get("OPENAI_API_KEY")
        self.summarizer = NotesSummarizer(self.storage, openai_key)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command and display the menu."""
        welcome_message = (
            "👋 Welcome to NoteTaker Bot!\n\n"
            "I can help you take and manage your notes.\n"
            f"{format_help_message()}"
        )

        # Create a custom keyboard for quick command access
        keyboard = [
            [KeyboardButton("/note"), KeyboardButton("/ask")],
            [KeyboardButton("/help"), KeyboardButton("/cancel")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(welcome_message, reply_markup=reply_markup)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command"""
        await update.message.reply_text(format_help_message())

    async def note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /note command, supporting both inline and follow-up input."""
        if context.args:
            # If user provides note inline
            note_text = ' '.join(context.args)
            user_id = update.effective_user.id

            if self.storage.add_note(user_id, note_text):
                await update.message.reply_text("✅ Note saved successfully!")
            else:
                await update.message.reply_text("❌ Failed to save note. Please try again.")

            return ConversationHandler.END

        # If no note provided, prompt the user
        await update.message.reply_text("📝 Please enter your note:")
        return NOTING

    async def receive_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle follow-up input after /note without a message."""
        note_text = update.message.text
        user_id = update.effective_user.id

        if self.storage.add_note(user_id, note_text):
            await update.message.reply_text("✅ Note saved successfully!")
        else:
            await update.message.reply_text("❌ Failed to save note. Please try again.")

        return ConversationHandler.END

    async def ask(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /ask command, allowing both inline queries and follow-up input."""
        if context.args:
            query = ' '.join(context.args)
            user_id = update.effective_user.id
            matching_notes = self.storage.search_notes(user_id, query)

            response = format_notes_response(matching_notes)
            await update.message.reply_text(response)
            return ConversationHandler.END

        await update.message.reply_text("🤔 What would you like to search for?")
        return ASKING

    async def receive_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle follow-up input after /ask without a query."""
        query = update.message.text
        user_id = update.effective_user.id
        matching_notes = self.storage.search_notes(user_id, query)

        response = format_notes_response(matching_notes)
        await update.message.reply_text(response)

        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user canceling an interaction."""
        await update.message.reply_text("❌ Action canceled.")
        return ConversationHandler.END

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Error occurred: {context.error}")
        if isinstance(update, Update):
            await update.message.reply_text(
                "❌ An error occurred while processing your request. Please try again."
            )

    async def set_bot_commands(self, application: Application):
        """Set up the bot menu buttons in Telegram's UI."""
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("note", "Save a new note"),
            BotCommand("ask", "Search for a note"),
            BotCommand("help", "Show help message"),
            BotCommand("cancel", "Cancel current action"),
        ]

        # Set persistent commands (for menu button)
        await application.bot.set_my_commands(commands, scope=BotCommandScopeDefault())
        await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())

    def run(self):
        """Run the bot"""
        try:
            async def post_init_callback(app: Application):
                await self.set_bot_commands(app)

            # Create application with post_init
            application = Application.builder().token(BOT_TOKEN).post_init(post_init_callback).build()

            # Add command handlers
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(CommandHandler("help", self.help))

            # Add conversation handler for /note command
            note_handler = ConversationHandler(
                entry_points=[CommandHandler("note", self.note)],
                states={
                    NOTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_note)],
                },
                fallbacks=[CommandHandler("cancel", self.cancel)],
            )
            application.add_handler(note_handler)

            # Add conversation handler for /ask command
            ask_handler = ConversationHandler(
                entry_points=[CommandHandler("ask", self.ask)],
                states={
                    ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_query)],
                },
                fallbacks=[CommandHandler("cancel", self.cancel)],
            )
            application.add_handler(ask_handler)

            # Add error handler
            application.add_error_handler(self.error_handler)

            # Start the bot
            application.run_polling()
        except Exception as e:
            logger.error(f"Failed to start bot: {str(e)}")
            raise