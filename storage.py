import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class NoteStorage:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        """Create storage file if it doesn't exist"""
        if not Path(self.file_path).exists():
            self._save_notes({})

    def _load_notes(self) -> Dict:
        """Load notes from storage file"""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("Corrupted storage file, creating new one")
            return {}
        except Exception as e:
            logger.error(f"Error loading notes: {str(e)}")
            return {}

    def _save_notes(self, notes: Dict):
        """Save notes to storage file"""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(notes, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving notes: {str(e)}")

    def add_note(self, user_id: int, note: str) -> bool:
        """Add a note for a user"""
        try:
            notes = self._load_notes()
            user_notes = notes.get(str(user_id), [])
            user_notes.append(note)
            notes[str(user_id)] = user_notes
            self._save_notes(notes)
            return True
        except Exception as e:
            logger.error(f"Error adding note: {str(e)}")
            return False

    def get_notes(self, user_id: int) -> List[str]:
        """Get all notes for a user"""
        try:
            notes = self._load_notes()
            return notes.get(str(user_id), [])
        except Exception as e:
            logger.error(f"Error getting notes: {str(e)}")
            return []

    def search_notes(self, user_id: int, query: str) -> List[str]:
        """Search user's notes containing the query"""
        notes = self.get_notes(user_id)
        return [note for note in notes if query.lower() in note.lower()]
