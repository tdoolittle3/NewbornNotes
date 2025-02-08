import sqlite3
import logging
from typing import List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class NoteStorage:

    def __init__(self, db_path: str = "notes.db"):
        """Initialize the SQLite database connection and create table if needed."""
        self.db_path = db_path
        self._initialize_db()

    def _connect(self):
        """Create a database connection."""
        return sqlite3.connect(self.db_path)

    def _initialize_db(self):
        """Create the notes table if it doesn't exist."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        username TEXT NOT NULL,
                        note TEXT NOT NULL,
                        timestamp TEXT NOT NULL
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")

    def add_note(self, chat_id: int, user_id: int, username: str,
                 note: str) -> bool:
        """Add a note for a chat."""
        try:
            logger.debug(
                f"Adding note for chat {chat_id} with user {user_id} and username {username}"
            )

            timestamp = datetime.utcnow().isoformat(
            )  # Use UTC time for consistency
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO notes (chat_id, user_id, username, note, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (chat_id, user_id, username, note, timestamp))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding note: {str(e)}")
            return False

    def get_notes(self, chat_id: int) -> List[Tuple[str, str]]:
        """Retrieve all notes for a specific chat along with timestamps."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT note, timestamp, username FROM notes WHERE chat_id = ? ORDER BY timestamp DESC",
                    (chat_id, ))
                return cursor.fetchall(
                )  # Returns list of (note, timestamp) tuples
        except Exception as e:
            logger.error(f"Error getting notes: {str(e)}")
            return []

    def search_notes(self, chat_id: int, query: str) -> List[Tuple[str, str]]:
        """Search for notes containing a specific query, returning the note and timestamp."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT note, timestamp FROM notes 
                    WHERE chat_id = ? AND note LIKE ? 
                    ORDER BY timestamp DESC
                """, (chat_id, f"%{query}%"))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error searching notes: {str(e)}")
            return []
