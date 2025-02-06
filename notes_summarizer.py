
import openai
import logging
from typing import List, Optional
from dbstorage import NoteStorage  # Import the NoteStorage class

logger = logging.getLogger(__name__)

class NotesSummarizer:
    def __init__(self, note_storage: NoteStorage, openai_api_key: str):
        """Initialize with a NoteStorage instance and OpenAI API key."""
        self.note_storage = note_storage
        self.client = openai.OpenAI(api_key=openai_api_key)

    def _format_notes(self, user_id: int) -> Optional[str]:
        """Retrieve and format a user's notes as a structured list."""
        notes = self.note_storage.get_notes(user_id)
        if not notes:
            return None

        return "\n".join([f"- {note[0]}" for note in notes])  # Extract notes (ignoring timestamps)

    def summarize_notes(self, user_id: int) -> Optional[str]:
        """Generate a concise summary of a user's notes using OpenAI."""
        notes_text = self._format_notes(user_id)
        if not notes_text:
            return "You have no notes to summarize."

        prompt = f"Summarize the following notes briefly:\n\n{notes_text}"

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error summarizing notes: {str(e)}")
            return "Failed to summarize notes. Please try again later."

    def ask_about_notes(self, user_id: int, question: str) -> Optional[str]:
        """Answer a user's question based on their stored notes using OpenAI."""
        notes_text = self._format_notes(user_id)
        if not notes_text:
            return "You have no notes to reference."

        prompt = f"""You are analyzing notes about baby/newborn activities like feeding, sleeping, diaper changes etc. 
Organize these activities into a clear timeline and provide relevant insights.
When answering questions, consider patterns and timing between activities.

Notes:\n{notes_text}\n\nQuestion: {question}

Remember to:
- Note time gaps between activities
- Group similar activities (feeding, sleeping, etc.)
- Point out any patterns
- Mention if something seems missing or irregular"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return "Failed to process your question. Please try again later."
