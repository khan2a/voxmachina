# Sentiment Analysis Feature

## Overview
Happy Medical Centre now includes **automatic sentiment analysis** for every patient call. Using GPT-4, the system analyzes the patient's emotional state, satisfaction level, and identifies any concerns that require attention.

## Features

### ✅ Emotional State Detection
- Identifies key emotions: anxious, frustrated, satisfied, confused, worried, happy, etc.
- Tracks overall sentiment: positive, neutral, negative, or urgent
- Provides confidence scores (0-100%)

### ✅ Patient Satisfaction Tracking
- Measures satisfaction level: satisfied, neutral, dissatisfied
- Helps identify service quality issues
- Enables proactive follow-up for dissatisfied patients

### ✅ Concern Identification
- Flags pain mentions and severity
- Detects urgency indicators
- Identifies communication barriers (e.g., language issues)
- Highlights dissatisfaction signals

### ✅ Quality Monitoring
- Track emotional trends across calls
- Identify agents needing additional training
- Measure improvements over time
- Generate satisfaction reports

## How It Works

### During Call Summary Generation

When a call ends, the system:

1. **Collects full transcript** of patient conversation
2. **Sends to GPT-4** for sentiment analysis
3. **Extracts key metrics**:
   - Overall sentiment (positive/neutral/negative/urgent)
   - Confidence score (0-100%)
   - Key emotions detected
   - Patient satisfaction level
   - Specific concerns or red flags
4. **Stores in database** alongside call summary
5. **Logs results** for monitoring

### Sentiment Analysis Response Structure

```json
{
  "overall_sentiment": "neutral",
  "confidence": 70,
  "key_emotions": ["anxious", "confused"],
  "satisfaction": "neutral",
  "concerns": ["pain in left molar", "language barrier"]
}
```

## Database Schema

### Updated `call_summaries` Table

```sql
CREATE TABLE call_summaries (
    id INTEGER PRIMARY KEY,
    call_id TEXT UNIQUE NOT NULL,
    summary TEXT,
    full_transcript TEXT,
    agent_name TEXT,
    sentiment_analysis TEXT,      -- JSON data with full analysis
    overall_sentiment TEXT,        -- Quick lookup: positive/neutral/negative/urgent
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Viewing Sentiment Analysis

### CLI Tool

```bash
# View call summary with sentiment
python view_transcripts.py --call-id rtc_xxxxx --summary

# Output includes:
# 🎭 Sentiment Analysis:
#   Overall: 😐 NEUTRAL (70% confidence)
#   Emotions: anxious, confused
#   Satisfaction: neutral
#   ⚠️  Concerns: pain in left molar, language barrier
```

### Programmatic Access

```python
from src.transcript_storage import TranscriptStorage

storage = TranscriptStorage(db_path="data/transcripts.db")

# Get call summary with sentiment
summary = storage.get_call_summary("rtc_xxxxx")

# Access sentiment data
import json
sentiment = json.loads(summary['sentiment_analysis'])

print(f"Overall: {sentiment['overall_sentiment']}")
print(f"Confidence: {sentiment['confidence']}%")
print(f"Emotions: {', '.join(sentiment['key_emotions'])}")
print(f"Concerns: {', '.join(sentiment['concerns'])}")
```

## Use Cases

### 1. Quality Assurance
- Review calls with negative sentiment
- Identify patterns in patient dissatisfaction
- Coach agents on emotional intelligence
- Improve service quality

### 2. Urgent Follow-Up
- Flag calls with "urgent" sentiment
- Identify patients in pain or distress
- Prioritize callbacks for dissatisfied patients
- Escalate to supervisor if needed

### 3. Training & Improvement
- Analyze emotion patterns across agents
- Identify common patient frustrations
- Train agents on empathy and communication
- Share examples of positive interactions

### 4. Patient Satisfaction Reporting
```sql
-- Get satisfaction distribution
SELECT
    JSON_EXTRACT(sentiment_analysis, '$.satisfaction') as satisfaction,
    COUNT(*) as count
FROM call_summaries
GROUP BY satisfaction;

-- Find dissatisfied patients
SELECT call_id, agent_name,
       JSON_EXTRACT(sentiment_analysis, '$.concerns') as concerns
FROM call_summaries
WHERE JSON_EXTRACT(sentiment_analysis, '$.satisfaction') = 'dissatisfied';
```

### 5. Trend Analysis
```sql
-- Track sentiment over time
SELECT
    DATE(created_at) as date,
    overall_sentiment,
    COUNT(*) as calls,
    AVG(JSON_EXTRACT(sentiment_analysis, '$.confidence')) as avg_confidence
FROM call_summaries
GROUP BY DATE(created_at), overall_sentiment
ORDER BY date DESC;
```

## Sentiment Categories

### Overall Sentiment

| Sentiment | Emoji | Description | Action Required |
|-----------|-------|-------------|-----------------|
| **positive** | 😊 | Patient satisfied, no concerns | Standard follow-up |
| **neutral** | 😐 | Professional, no strong emotions | Monitor for patterns |
| **negative** | 😟 | Patient frustrated or dissatisfied | Review call, follow up |
| **urgent** | 🚨 | Patient in pain or needs immediate help | Immediate escalation |

### Key Emotions

**Common Positive Emotions:**
- satisfied, happy, relieved, grateful, confident

**Common Neutral Emotions:**
- professional, matter-of-fact, calm

**Common Negative Emotions:**
- anxious, confused, frustrated, worried, dissatisfied, angry

**Urgent Indicators:**
- distressed, panicked, severe pain, emergency

### Concerns

**Medical Concerns:**
- "severe pain", "bleeding", "swelling"
- "can't eat", "can't sleep", "worsening"
- "allergic reaction", "infection"

**Service Concerns:**
- "long wait time", "couldn't reach anyone"
- "appointment cancelled", "no callback"
- "rude staff", "not helpful"

**Communication Concerns:**
- "language barrier", "didn't understand"
- "confused about instructions"
- "need clarification"

## Benefits

### For Medical Centre
- ✅ **Quality Monitoring**: Track service quality objectively
- ✅ **Risk Management**: Identify at-risk patients early
- ✅ **Training Data**: Use real examples for staff training
- ✅ **Performance Metrics**: Measure agent effectiveness

### For Patients
- ✅ **Better Care**: Dissatisfied patients get prioritized follow-up
- ✅ **Faster Resolution**: Urgent cases escalated immediately
- ✅ **Improved Experience**: Centre learns from feedback

### For Staff
- ✅ **Objective Feedback**: Data-driven performance insights
- ✅ **Training Support**: Specific areas for improvement
- ✅ **Recognition**: Positive sentiment tracked
- ✅ **Workload Balance**: Difficult calls identified

## Configuration

### Sentiment Analysis Prompt

The system uses GPT-4 with a specialized prompt:

```python
"""Analyze the patient's sentiment and emotional state in this medical call.
Provide:
1. Overall sentiment (positive/neutral/negative/urgent)
2. Confidence score (0-100)
3. Key emotions detected (e.g., anxious, frustrated, satisfied, confused, worried)
4. Any concerns or red flags (e.g., pain level, urgency, dissatisfaction)
5. Patient satisfaction indicator (satisfied/neutral/dissatisfied)

Return as JSON with these exact keys:
overall_sentiment, confidence, key_emotions (array), concerns (array), satisfaction
"""
```

### Customization

Edit `src/transcript_storage.py` to modify:
- Emotion categories
- Concern keywords
- Confidence thresholds
- Response format

## Cost Considerations

**Sentiment Analysis Costs:**
- ~300 tokens per analysis
- Using GPT-4: ~$0.009 per call
- Total with summary: ~$0.024 per call

**Cost Optimization:**
- Use GPT-4-mini for lower cost (~$0.002 per call)
- Batch analyze multiple calls
- Only analyze flagged calls

## Alerts & Automation

### Future Enhancements

```python
# Example: Auto-escalate negative calls
if sentiment['overall_sentiment'] == 'negative':
    send_email_to_supervisor(call_id, sentiment['concerns'])

# Example: Auto-schedule follow-up for pain
if 'pain' in ' '.join(sentiment['concerns']).lower():
    schedule_follow_up_call(patient_info, days=1)

# Example: Flag for review
if sentiment['satisfaction'] == 'dissatisfied':
    add_to_review_queue(call_id, priority='high')
```

## Testing

### Test Sentiment Analysis

```bash
# Make a test call with various emotions
# View the sentiment analysis
python view_transcripts.py --call-id rtc_xxxxx --summary

# Expected output:
# 🎭 Sentiment Analysis:
#   Overall: 😟 NEGATIVE (85% confidence)
#   Emotions: frustrated, anxious
#   Satisfaction: dissatisfied
#   ⚠️  Concerns: long wait time, scheduling confusion
```

## Troubleshooting

### No Sentiment Data
**Problem:** Sentiment analysis field is empty
**Solution:**
1. Check OpenAI API key is valid
2. Verify GPT-4 access
3. Check logs for errors
4. Regenerate summary: Delete from call_summaries and wait for new call

### Inaccurate Sentiment
**Problem:** Sentiment doesn't match call tone
**Solution:**
1. Review transcript for context
2. Adjust sentiment prompt for better accuracy
3. Consider confidence score (low confidence = uncertain)
4. Provide feedback examples to improve prompt

### Database Errors
**Problem:** Missing sentiment columns
**Solution:**
```bash
sqlite3 data/transcripts.db "
ALTER TABLE call_summaries ADD COLUMN sentiment_analysis TEXT;
ALTER TABLE call_summaries ADD COLUMN overall_sentiment TEXT;
"
```

## Best Practices

### 1. Review Negative Sentiment Calls
- Set up daily review of negative sentiment calls
- Contact patients with "dissatisfied" satisfaction
- Investigate patterns in negative feedback

### 2. Celebrate Positive Interactions
- Share positive sentiment calls with team
- Recognize agents with consistently positive sentiment
- Use as training examples

### 3. Track Trends
- Monitor overall sentiment week-over-week
- Identify seasonal patterns
- Measure impact of service changes

### 4. Use Concerns for Triage
- Priority follow-up for pain/urgency keywords
- Route language barrier calls to bilingual staff
- Flag complex cases for specialist review

## Future Enhancements

- [ ] Real-time sentiment during call (WebSocket streaming)
- [ ] Sentiment-based call routing
- [ ] Automatic satisfaction surveys for negative calls
- [ ] Sentiment trend dashboard
- [ ] Agent performance leaderboard
- [ ] Patient emotion history tracking
- [ ] Voice tone analysis (pitch, speed, volume)
- [ ] Integration with CRM systems

---

**Last Updated:** November 4, 2025
**Version:** 1.0.0
**Status:** ✅ ACTIVE
