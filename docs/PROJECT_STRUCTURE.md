# VoxMachina Project Structure

## Overview

VoxMachina uses OpenAI's native SIP connector for direct telephony integration. This eliminates the need for custom audio bridges, Asterisk PBX, or RTP streaming code.

## Directory Structure

```
voxmachina/
├── webhook_server.py          # Main application - Flask webhook server (~200 lines)
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
├── QUICKSTART.md             # 5-minute setup guide
├── PROJECT_STRUCTURE.md      # This file - architecture documentation
├── LICENSE                    # MIT License
│
├── config/
│   ├── .env                  # Environment variables (not in git)
│   ├── .env.example          # Environment template
│   └── prompts.json          # AI conversation prompts
│
├── docs/
│   ├── OPENAI_SIP_SETUP.md   # Comprehensive setup guide
|
│
├── tests/
│   ├── conftest.py           # Pytest configuration
│   └── test_webhook_server.py # Webhook server tests
│
└── .github/
    └── instructions/
        └── copilot.instructions.md  # AI coding agent instructions
```

## Core Components

### 1. webhook_server.py (Main Application)

**Purpose:** Flask server that handles OpenAI webhooks and monitors calls

**Key Functions:**
- `webhook()` - Receives `realtime.call.incoming` events
- `monitor_call_websocket()` - Connects to OpenAI WebSocket to track conversation
- `health()` - Health check endpoint

**Flow:**
1. OpenAI sends webhook when call arrives
2. Server accepts call via POST to `/v1/realtime/calls/{call_id}/accept`
3. Server optionally monitors call via WebSocket
4. Logs transcripts and events

**Configuration:**
- `call_accept_config` - AI personality, voice, turn detection
- `initial_response` - Greeting message to start conversation

**Dependencies:**
- Flask (webhook server)
- OpenAI SDK (webhook verification, API calls)
- websockets (call monitoring)
- requests (HTTP API calls)
- python-dotenv (environment variables)

### 2. config/.env

**Purpose:** Store sensitive credentials and configuration

**Required Variables:**
```bash
OPENAI_API_KEY=sk-proj-...
OPENAI_PROJECT_ID=proj_...
OPENAI_WEBHOOK_SECRET=whsec_...
OPENAI_VOICE=alloy
WEBHOOK_PORT=5000
```

**Optional Variables:**
```bash
LOG_LEVEL=INFO
VONAGE_NUMBER=+1234567890  # For reference only
```

## Data Flow

### Incoming Call Flow

```
1. Caller dials Vonage number
   └─> Vonage SIP Trunk
       └─> OpenAI SIP Endpoint (sip:PROJECT_ID@sip.api.openai.com)
           └─> OpenAI sends webhook to your server
               └─> webhook_server.py receives event
                   ├─> Validates signature
                   ├─> Accepts call via API
                   └─> Starts WebSocket monitoring (optional)

2. Conversation starts
   ├─> OpenAI handles audio streaming (SIP/RTP)
   ├─> OpenAI performs speech recognition (Whisper)
   ├─> OpenAI generates responses (GPT-4)
   ├─> OpenAI synthesizes speech (TTS)
   └─> Your server receives events via WebSocket
       ├─> User speech transcripts
       ├─> AI response transcripts
       └─> Conversation metadata

3. Call ends
   └─> OpenAI sends "realtime.call.ended" webhook
       └─> webhook_server.py logs call completion
```

### WebSocket Events

When monitoring a call, you receive:

```python
# User spoke
{
    "type": "conversation.item.input_audio_transcription.completed",
    "transcript": "Hello, can you help me?"
}

# AI is responding
{
    "type": "response.audio_transcript.delta",
    "delta": "Of course! How can I assist you today?"
}

# Audio chunk being sent to caller (high frequency)
{
    "type": "response.audio.delta",
    "delta": "base64_encoded_audio..."
}

# Error occurred
{
    "type": "error",
    "error": {"message": "...", "code": "..."}
}
```

## Deployment Options

### 1. Local Development (Mac + ngrok)

```bash
# Terminal 1: Start webhook server
cd /path/to/voxmachina
python webhook_server.py

# Terminal 2: Expose via ngrok
ngrok http 5000
```

**Use Case:** Quick testing, development, hackathons

### 2. Production (nginx + Let's Encrypt)

```bash
# Run webhook server as systemd service
sudo systemctl start voxmachina

# nginx proxies HTTPS to localhost:5000
# SSL certificate from Let's Encrypt
```

**Use Case:** Production deployments with custom domain

### 3. Cloud (Heroku, Railway, Render)

```bash
# Deploy to cloud platform
git push heroku main

# Platform provides HTTPS endpoint automatically
```

**Use Case:** Scalable production, multiple concurrent calls

## Testing

### Unit Tests

```bash
pytest tests/
```

**Test Files:**
- `test_config.py` - Configuration loading
- `test_openai_client.py` - OpenAI client functionality

### Integration Tests

```bash
# Test webhook health
curl http://localhost:5000/health

# Test OpenAI connectivity (requires API key)
python -c "from openai import OpenAI; print(OpenAI().models.list())"
```

### End-to-End Tests

1. Call your Vonage number
2. Verify webhook receives event
3. Check WebSocket connects
4. Have conversation with AI
5. Verify transcripts are logged

## Monitoring & Logs

### Log Levels

```bash
# Set in .env
LOG_LEVEL=DEBUG  # Verbose, includes all WebSocket events
LOG_LEVEL=INFO   # Standard, includes call events and transcripts
LOG_LEVEL=WARNING # Errors and warnings only
```

### Log Output

```
2024-11-03 10:30:15 - INFO - Received webhook: realtime.call.incoming
2024-11-03 10:30:15 - INFO - Incoming call: call_abc123
2024-11-03 10:30:15 - INFO -   From: +1234567890
2024-11-03 10:30:15 - INFO -   To: +447520648361
2024-11-03 10:30:15 - INFO - Call call_abc123 accepted successfully
2024-11-03 10:30:16 - INFO - WebSocket connected for call call_abc123
2024-11-03 10:30:17 - INFO - Call call_abc123: AI speaking: Hello! I'm...
2024-11-03 10:30:20 - INFO - Call call_abc123: User said: Hello, can you...
```

## Scaling Considerations

### Single Server

- **Capacity:** ~10-20 concurrent calls
- **Bottleneck:** CPU for webhook processing
- **Solution:** Use multiple worker processes (gunicorn)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 webhook_server:app
```

### Multiple Servers

- **Load Balancer:** nginx, HAProxy, or cloud load balancer
- **Session Affinity:** Not required (webhooks are stateless)
- **Database:** Optional, for call history/analytics

### Cloud Auto-Scaling

- Deploy to Kubernetes, AWS ECS, or Google Cloud Run
- Auto-scale based on webhook traffic
- Use Redis for shared state (if needed)

## Security

### Webhook Verification

**Always verify webhook signatures:**

```python
from openai import OpenAI

client = OpenAI(webhook_secret=os.getenv("OPENAI_WEBHOOK_SECRET"))
event = client.webhooks.unwrap(request.data, request.headers)
```

This prevents spoofed webhooks from malicious actors.

### API Key Security

- **Never commit** `.env` to git (already in `.gitignore`)
- **Use environment variables** in production
- **Rotate keys** periodically
- **Limit scope** to Realtime API only

### HTTPS Only

- Webhooks **must** use HTTPS in production
- Use Let's Encrypt for free SSL certificates
- ngrok/Cloudflare Tunnel provide HTTPS automatically

## Cost Optimization

### Reduce API Costs

1. **Shorter instructions** - Less processing time
2. **Higher VAD threshold** - AI waits longer before responding
3. **Lower temperature** - More deterministic, fewer tokens
4. **Disable recording** - If not needed

### Monitor Usage

- Check dashboard: https://platform.openai.com/usage
- Set billing alerts
- Log call duration for accounting

## Troubleshooting

### Common Issues

1. **Webhook not receiving calls**
   - Check URL is publicly accessible
   - Verify webhook secret matches
   - Check OpenAI webhook logs

2. **Call connects but silent**
   - Verify Project ID in Vonage SIP URI
   - Ensure `transport=tls` is present
   - Check OpenAI API key has Realtime access

3. **AI not responding**
   - Check instructions are clear
   - Verify API quota not exhausted
   - Check WebSocket connection logs

4. **High latency**
   - Reduce instruction length
   - Optimize WebSocket monitoring
   - Check network path (traceroute)

## Development Workflow

1. **Make changes** to `webhook_server.py`
2. **Test locally** with ngrok
3. **Commit changes** to git
4. **Deploy** to production server
5. **Monitor logs** for issues

## Contributing

When contributing:

1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Test with real phone calls before submitting PR

## Resources

- [OpenAI Realtime SIP Docs](https://platform.openai.com/docs/guides/realtime-sip)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference/realtime)
- [Vonage SIP Documentation](https://developer.vonage.com/en/voice/sip/overview)
- [Flask Documentation](https://flask.palletsprojects.com/)

## License

MIT License - See [LICENSE](LICENSE) file
