# Real-Time Call Transcription Feature

## Overview
Happy Medical Centre now includes automatic call transcription powered by OpenAI's Realtime API. Every patient call is transcribed in real-time, stored in a database, and automatically summarized using GPT-4.

## Features

### ✅ Real-Time Transcription
- Automatic speech-to-text conversion during calls
- Uses OpenAI's `gpt-4o-transcribe` model for high accuracy
- Supports incremental streaming and complete transcripts

### ✅ Transcript Storage
- SQLite database stores all transcripts with timestamps
- Speaker identification (patient vs agent)
- Agent tracking (receptionist, dentist, nutritionist)
- Searchable and exportable

### ✅ AI-Generated Summaries
- GPT-4 automatically generates medical summaries
- Structured format: Patient Info, Reason, Discussion, Action Items
- Saved alongside transcripts for quick reference

### ✅ Transcript Viewer CLI
- View full transcripts from command line
- Display AI summaries
- Export call data to JSON
- List recent calls

## Configuration

### Environment Variables (`config/.env`)
```bash
# Enable/disable transcription
ENABLE_TRANSCRIPTION=true

# Transcription model (gpt-4o-transcribe, whisper-1)
TRANSCRIPTION_MODEL=gpt-4o-transcribe

# Language code (en, es, fr, etc.)
TRANSCRIPTION_LANGUAGE=en
```

## Database Schema

### Transcripts Table
```sql
CREATE TABLE transcripts (
    id INTEGER PRIMARY KEY,
    call_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    speaker TEXT NOT NULL,          -- "patient" or "agent"
    transcript TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    agent_name TEXT                 -- "receptionist", "dentist", "nutritionist"
)
```

### Call Summaries Table
```sql
CREATE TABLE call_summaries (
    id INTEGER PRIMARY KEY,
    call_id TEXT UNIQUE NOT NULL,
    summary TEXT,
    full_transcript TEXT,
    agent_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

## Usage

### Viewing Transcripts

**List recent calls:**
```bash
python view_transcripts.py --list
```

**View specific call transcript:**
```bash
python view_transcripts.py --call-id rtc_abc123 --transcript
```

**View AI summary:**
```bash
python view_transcripts.py --call-id rtc_abc123 --summary
```

**View both transcript and summary:**
```bash
python view_transcripts.py --call-id rtc_abc123
```

**Export call data to JSON:**
```bash
python view_transcripts.py --call-id rtc_abc123 --export output.json
```

### Programmatic Access

```python
from src.transcript_storage import TranscriptStorage

# Initialize storage
storage = TranscriptStorage(
    db_path="data/transcripts.db",
    openai_api_key="your-api-key"
)

# Get full transcript
transcript = storage.get_full_transcript("rtc_abc123")
print(transcript)

# Get AI summary
summary = storage.get_call_summary("rtc_abc123")
print(summary['summary'])

# Generate new summary
import asyncio
summary = asyncio.run(
    storage.generate_call_summary("rtc_abc123", "receptionist")
)
```

## How It Works

### 1. Call Acceptance
When a call is accepted, transcription is enabled in the session configuration:
```python
config = {
    "type": "realtime",
    "model": "gpt-realtime",
    "instructions": "...",
    "audio": {
        "input": {
            "transcription": {
                "model": "gpt-4o-transcribe",
                "language": "en"
            }
        }
    }
}
```

### 2. Real-Time Events
During the call, OpenAI sends transcription events:

**Delta Event (streaming):**
```json
{
    "type": "conversation.item.input_audio_transcription.delta",
    "item_id": "item_003",
    "delta": "Hello,"
}
```

**Completed Event:**
```json
{
    "type": "conversation.item.input_audio_transcription.completed",
    "item_id": "item_003",
    "transcript": "Hello, how are you?"
}
```

### 3. Storage
When a completed transcription is received:
1. Extract transcript text and item_id
2. Save to database with call_id, speaker, agent_name, timestamp
3. Log the transcript for monitoring

### 4. Summary Generation
When the call ends (WebSocket closes):
1. Retrieve all transcripts for the call
2. Send to GPT-4 for summarization
3. Store summary in database
4. Log summary for review

## Data Storage

### Directory Structure
```
voxmachina/
├── data/
│   ├── transcripts.db          # SQLite database
│   └── exports/                # Exported JSON files
│       └── call_rtc_abc123_20251104_120000.json
```

### Exported JSON Format
```json
{
    "call_id": "rtc_abc123",
    "transcripts": [
        {
            "id": 1,
            "call_id": "rtc_abc123",
            "item_id": "item_001",
            "speaker": "patient",
            "transcript": "I need to schedule an appointment",
            "timestamp": "2025-11-04 12:00:00",
            "agent_name": "receptionist"
        }
    ],
    "summary": {
        "call_id": "rtc_abc123",
        "summary": "Patient requested appointment scheduling...",
        "agent_name": "receptionist",
        "created_at": "2025-11-04 12:05:00"
    },
    "exported_at": "2025-11-04T12:10:00"
}
```

## Benefits

### For Medical Centre
- ✅ **Legal Documentation**: Complete record of all patient interactions
- ✅ **Quality Assurance**: Review calls for training and improvement
- ✅ **Compliance**: Meet HIPAA and regulatory requirements
- ✅ **Efficiency**: Auto-generated medical notes save time

### For Patients
- ✅ **Accuracy**: Precise record of medical discussions
- ✅ **Transparency**: Access to call summaries if needed
- ✅ **Better Care**: More accurate follow-up based on transcripts

### For Staff
- ✅ **Reduced Documentation**: AI generates summaries automatically
- ✅ **Performance Tracking**: Monitor call quality and outcomes
- ✅ **Training**: Use real call examples for improvement

## Cost Considerations

**Transcription Costs:**
- Included in OpenAI Realtime API audio pricing
- No additional per-minute charges
- ~$0.01-0.05 per minute of call

**Storage Costs:**
- Minimal: ~1KB per minute of transcription
- SQLite database is lightweight and efficient
- Can archive old calls to reduce storage

## Security & Privacy

### Data Protection
- Database stored locally on server
- Encrypted at rest (file system level)
- Access controlled via server permissions

### HIPAA Compliance
- Store in HIPAA-compliant infrastructure
- Implement encryption for PHI data
- Set up access logging and audit trails
- Establish data retention policies

### Best Practices
1. **Encrypt database file** using filesystem encryption
2. **Limit access** to authorized personnel only
3. **Regular backups** with encryption
4. **Data retention policy**: Delete after X years
5. **Patient consent**: Inform patients about recording

## Troubleshooting

### Transcripts Not Appearing
1. Check `ENABLE_TRANSCRIPTION=true` in `.env`
2. Verify WebSocket connection is working
3. Check logs for transcription events
4. Confirm OpenAI API key has access

### Summary Generation Fails
1. Ensure OpenAI API key is valid
2. Check GPT-4 API access
3. Verify transcript exists in database
4. Check logs for error messages

### Database Issues
1. Ensure `data/` directory exists and is writable
2. Check SQLite database file permissions
3. Try deleting and recreating database:
   ```bash
   rm data/transcripts.db
   python webhook_server.py  # Will recreate on startup
   ```

## Future Enhancements

### Planned Features
- [ ] Real-time sentiment analysis
- [ ] Keyword detection and alerts
- [ ] Multi-language support
- [ ] Voice emotion detection
- [ ] Automated follow-up scheduling
- [ ] Integration with EHR systems
- [ ] Patient portal access to transcripts

## Support

For issues or questions about transcription:
1. Check logs: `tail -f /tmp/webhook.log`
2. Review this documentation
3. Check OpenAI Realtime API docs
4. Contact system administrator

---

**Last Updated:** November 4, 2025
**Version:** 1.0.0
