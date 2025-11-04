"""
Transcript Storage System for Happy Medical Centre
Stores call transcripts with timestamps and generates AI summaries
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from openai import OpenAI

logger = logging.getLogger(__name__)


class TranscriptStorage:
    """Manages storage and retrieval of call transcripts"""

    def __init__(self, db_path: str = "data/transcripts.db", openai_api_key: str = None):
        """
        Initialize transcript storage

        Args:
            db_path: Path to SQLite database file
            openai_api_key: OpenAI API key for summary generation
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.client = OpenAI(api_key=openai_api_key) if openai_api_key else None
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create transcripts table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                speaker TEXT NOT NULL,
                transcript TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                agent_name TEXT,
                UNIQUE(call_id, item_id)
            )
        """
        )

        # Create call_summaries table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS call_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT UNIQUE NOT NULL,
                summary TEXT,
                full_transcript TEXT,
                agent_name TEXT,
                sentiment_analysis TEXT,
                overall_sentiment TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create indexes for faster queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_call_id
            ON transcripts(call_id)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON transcripts(timestamp)
        """
        )

        conn.commit()
        conn.close()
        logger.info(f"Transcript database initialized at {self.db_path}")

    def save_transcript(
        self,
        call_id: str,
        item_id: str,
        transcript: str,
        speaker: str = "patient",
        agent_name: str = "receptionist",
    ) -> bool:
        """
        Save a transcript segment to database

        Args:
            call_id: Unique call identifier
            item_id: Item ID from OpenAI event
            transcript: Transcribed text
            speaker: Who is speaking (patient/agent)
            agent_name: Which agent handled this part

        Returns:
            True if saved successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO transcripts
                (call_id, item_id, speaker, transcript, agent_name)
                VALUES (?, ?, ?, ?, ?)
            """,
                (call_id, item_id, speaker, transcript, agent_name),
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Saved transcript for call {call_id}: " f"{speaker} - {transcript[:50]}..."
            )
            return True

        except Exception as e:
            logger.error(f"Error saving transcript: {e}")
            return False

    def get_call_transcripts(self, call_id: str) -> list[dict]:
        """
        Get all transcripts for a specific call

        Args:
            call_id: Unique call identifier

        Returns:
            List of transcript dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM transcripts
                WHERE call_id = ?
                ORDER BY timestamp ASC
            """,
                (call_id,),
            )

            results = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return results

        except Exception as e:
            logger.error(f"Error retrieving transcripts: {e}")
            return []

    def get_full_transcript(self, call_id: str) -> str:
        """
        Get full conversation transcript as formatted text

        Args:
            call_id: Unique call identifier

        Returns:
            Formatted transcript string
        """
        transcripts = self.get_call_transcripts(call_id)

        if not transcripts:
            return ""

        full_text = []
        for t in transcripts:
            speaker_label = t["speaker"].upper()
            full_text.append(f"{speaker_label}: {t['transcript']}")

        return "\n".join(full_text)

    def _analyze_sentiment(self, full_transcript: str) -> dict:
        """
        Analyze sentiment of patient conversation using GPT-4

        Args:
            full_transcript: Complete conversation transcript

        Returns:
            Dictionary with sentiment analysis data
        """
        if not self.client:
            return {
                "overall_sentiment": "unknown",
                "confidence": 0,
                "key_emotions": [],
                "concerns": [],
            }

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze the patient's sentiment and
                        emotional state in this medical call. Provide:
                        1. Overall sentiment (positive/neutral/negative/urgent)
                        2. Confidence score (0-100)
                        3. Key emotions detected (e.g., anxious, frustrated,
                           satisfied, confused, worried)
                        4. Any concerns or red flags (e.g., pain level,
                           urgency, dissatisfaction)
                        5. Patient satisfaction indicator (satisfied/neutral/
                           dissatisfied)

                        Return as JSON with these exact keys:
                        overall_sentiment, confidence, key_emotions (array),
                        concerns (array), satisfaction""",
                    },
                    {"role": "user", "content": f"Analyze patient sentiment:\n\n{full_transcript}"},
                ],
                temperature=0.3,
                max_tokens=300,
            )

            # Parse JSON response
            content = response.choices[0].message.content
            # Try to extract JSON from response
            if "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end]
                sentiment_data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
            logger.info(
                f"Sentiment analysis: {sentiment_data.get('overall_sentiment')} "
                f"({sentiment_data.get('confidence')}% confidence)"
            )
            return sentiment_data

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                "overall_sentiment": "unknown",
                "confidence": 0,
                "key_emotions": [],
                "concerns": ["analysis_failed"],
            }

    async def generate_call_summary(
        self, call_id: str, agent_name: str = "receptionist"
    ) -> str | None:
        """
        Generate AI summary of call using GPT-4

        Args:
            call_id: Unique call identifier
            agent_name: Agent who handled the call

        Returns:
            Summary text or None if failed
        """
        if not self.client:
            logger.warning("OpenAI client not initialized, cannot generate summary")
            return None

        try:
            full_transcript = self.get_full_transcript(call_id)

            if not full_transcript:
                logger.warning(f"No transcript found for call {call_id}")
                return None

            # Generate summary using GPT-4
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a medical assistant summarizing
                        patient calls. Create a concise summary with:
                        1. Patient Information (name if mentioned)
                        2. Reason for Call
                        3. Key Discussion Points
                        4. Action Items/Outcome
                        5. Follow-up Required (if any)

                        Keep it professional and under 200 words.""",
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this medical centre call:\n\n{full_transcript}",
                    },
                ],
                temperature=0.3,
                max_tokens=500,
            )

            summary = response.choices[0].message.content

            # Generate sentiment analysis
            sentiment_data = self._analyze_sentiment(full_transcript)
            sentiment_json = json.dumps(sentiment_data)
            overall_sentiment = sentiment_data.get("overall_sentiment", "neutral")

            # Save summary and sentiment to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO call_summaries
                (call_id, summary, full_transcript, agent_name,
                 sentiment_analysis, overall_sentiment)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (call_id, summary, full_transcript, agent_name, sentiment_json, overall_sentiment),
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Generated summary for call {call_id} " f"(sentiment: {overall_sentiment})"
            )
            return summary

        except Exception as e:
            logger.error(f"Error generating call summary: {e}")
            return None

    def get_call_summary(self, call_id: str) -> dict | None:
        """
        Retrieve existing call summary

        Args:
            call_id: Unique call identifier

        Returns:
            Dictionary with summary data or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM call_summaries
                WHERE call_id = ?
            """,
                (call_id,),
            )

            result = cursor.fetchone()
            conn.close()

            return dict(result) if result else None

        except Exception as e:
            logger.error(f"Error retrieving summary: {e}")
            return None

    def export_call_data(self, call_id: str, output_path: str = None) -> str | None:
        """
        Export complete call data (transcripts + summary) to JSON

        Args:
            call_id: Unique call identifier
            output_path: Optional custom output path

        Returns:
            Path to exported file or None if failed
        """
        try:
            transcripts = self.get_call_transcripts(call_id)
            summary = self.get_call_summary(call_id)

            export_data = {
                "call_id": call_id,
                "transcripts": transcripts,
                "summary": summary,
                "exported_at": datetime.now().isoformat(),
            }

            if not output_path:
                output_path = (
                    f"data/exports/call_{call_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w") as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Exported call data to {output_file}")
            return str(output_file)

        except Exception as e:
            logger.error(f"Error exporting call data: {e}")
            return None
