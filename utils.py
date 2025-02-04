import logging
from typing import List

def setup_logging(log_format: str, log_level: str):
    """Setup logging configuration"""
    logging.basicConfig(
        format=log_format,
        level=getattr(logging, log_level)
    )

def format_notes_response(notes: List[str]) -> str:
    """Format notes for display"""
    if not notes:
        return "No notes found."
    
    response = "📝 Your Notes:\n\n"
    for i, note in enumerate(notes, 1):
        response += f"{i}. {note}\n"
    return response

def format_help_message() -> str:
    """Format help message"""
    return """
🤖 Available commands:

/note <text> - Save a new note
/ask <search term> - Search through your notes
/help - Show this help message

Examples:
/note Remember to buy milk
/ask milk
"""
