import logging
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    BotCommand,
    BotCommandScopeDefault,
    MenuButtonCommands,
)
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
            [KeyboardButton("/help")]
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

            return ConversationHandler.END  # End if note was provided inline

        # If no note provided, prompt the user
        await update.message.reply_text("📝 Please enter your note:")
        return NOTING  # Wait for user input

    async def receive_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle follow-up input after /note without a message."""
        note_text = update.message.text
        user_id = update.effective_user.id

        if self.storage.add_note(user_id, note_text):
            await update.message.reply_text("✅ Note saved successfully!")
        else:
            await update.message.reply_text("❌ Failed to save note. Please try again.")

        return ConversationHandler.END  # End conversation

    async def ask(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /ask command, allowing both inline queries and follow-up input."""
        if context.args:
            # If user provides a query inline
            query = ' '.join(context.args)
            user_id = update.effective_user.id
            matching_notes = self.storage.search_notes(user_id, query)

            response = format_notes_response(matching_notes)
            await update.message.reply_text(response)
            return ConversationHandler.END  # End if query was provided inline

        # If no query provided, prompt the user
        await update.message.reply_text("🤔 What would you like to ask about?")
        return ASKING  # Wait for user input

    async def receive_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle follow-up input after /ask without a query."""
        query = update.message.text
        user_id = update.effective_user.id
        matching_notes = self.storage.search_notes(user_id, query)

        response = format_notes_response(matching_notes)
        await update.message.reply_text(response)

        return ConversationHandler.END  # End conversation

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Error occurred: {context.error}")
        if isinstance(update, Update):
            await update.message.reply_text(
                "❌ An error occurred while processing your request. Please try again."
            )

    async def log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /log command - show last 10 notes"""
        user_id = update.effective_user.id
        notes = self.storage.get_notes(user_id)[:10]  # Get last 10 notes

        if not notes:
            await update.message.reply_text("No notes found.")
            return

        response = "📋 Your Last 10 Notes:\n\n"
        for i, (note, timestamp) in enumerate(notes, 1):
            response += f"{i}. [{timestamp}] {note}\n"

        await update.message.reply_text(response)

    async def set_bot_commands(self, application: Application):
        """Set up the bot menu buttons in Telegram's UI."""
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("note", "Save a new note"),
            BotCommand("ask", "Search for a note"),
            BotCommand("help", "Show help message"),
            BotCommand("log", "Show last 10 notes"),
        ]

        # Set persistent commands (for menu button)
        await application.bot.set_my_commands(commands, scope=BotCommandScopeDefault())

        # Set the expandable menu button next to the input field
        await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())

    def run(self):
        """Run the bot"""
        try:
            # Correct way to set bot commands after initialization
            async def post_init_callback(app: Application):
                await self.set_bot_commands(app)

            # Create application with post_init
            application = Application.builder().token(BOT_TOKEN).post_init(post_init_callback).build()

            # Add command handlers
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(CommandHandler("help", self.help))
            application.add_handler(CommandHandler("log", self.log))

            # Add conversation handler for /note command
            note_handler = ConversationHandler(
                entry_points=[CommandHandler("note", self.note)],
                states={
                    NOTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_note)],
                },
                fallbacks=[],
            )
            application.add_handler(note_handler)

            # Add conversation handler for /ask command
            ask_handler = ConversationHandler(
                entry_points=[CommandHandler("ask", self.ask)],
                states={
                    ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_query)],
                },
                fallbacks=[],
            )
            application.add_handler(ask_handler)

            # Add error handler
            application.add_error_handler(self.error_handler)

            # Start the bot
            application.run_polling()
        except Exception as e:
            logger.error(f"Failed to start bot: {str(e)}")
            raise