---
applyTo: '**'
---

# Happy Medical Centre: Direct OpenAI SIP Integration

## Project Overview
Happy Medical Centre is a streamlined AI voice assistant implementing real-time speech-to-speech conversations using:
- **OpenAI Realtime API with Native SIP Connector** - handles all audio processing and AI conversations
- **Vonage SIP Trunking** - provides phone number and PSTN connectivity
- **Python Flask Webhook Server** - receives webhooks and manages call acceptance
- **WebSocket Monitoring** - optional real-time event monitoring

**Key Simplification:** OpenAI's native SIP endpoint eliminates the need for Asterisk PBX, custom RTP handlers, or audio bridges. The entire solution is ~200 lines of Python.

## Architecture Components

### 1. OpenAI SIP Endpoint (Core)
- **Endpoint**: `sip:proj_PROJECT_ID@sip.api.openai.com;transport=tls`
- Receives inbound SIP calls directly from Vonage
- Handles all audio processing (speech-to-text, AI response, text-to-speech)
- Manages the realtime conversation session
- Sends `realtime.call.incoming` webhooks to your server

### 2. Vonage SIP Trunking (Telephony)
- Provides phone number (+447520648361)
- Routes PSTN calls to OpenAI SIP endpoint
- Configuration: Point SIP trunk at OpenAI's SIP endpoint with your project ID

### 3. Python Webhook Server (Control)
- **File**: `webhook_server.py` (Flask application)
- Receives `realtime.call.incoming` webhooks from OpenAI
- Accepts/rejects calls via OpenAI REST API
- Configures AI behavior (instructions, model, voice)
- Optionally monitors call events via WebSocket

## Environment Setup

### Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Core dependencies:
# - openai>=1.3.0 (OpenAI SDK with webhook support)
# - flask>=3.0.0 (webhook server)
# - websockets>=12.0 (optional monitoring)
# - python-dotenv>=1.0.0 (environment config)
# - requests>=2.31.0 (HTTP calls)
```

### No Asterisk Required
The original architecture used Asterisk PBX, but this has been **completely removed** in favor of OpenAI's native SIP connector. All Asterisk-related code is archived in `docs/archive/`

## Project Structure

```
voxmachina/
├── webhook_server.py          # Main Flask webhook server (200 lines)
├── config/
│   ├── .env                   # Environment variables
│   └── prompts.json           # AI conversation prompts
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration utilities
│   └── openai_client.py       # OpenAI SDK helpers
├── tests/
│   ├── test_webhook_server.py
│   ├── test_config.py
│   └── conftest.py
├── docs/
│   ├── QUICKSTART.md
│   ├── OPENAI_SIP_SETUP.md
│   ├── ARCHITECTURE_COMPARISON.md
│   └── archive/               # Old Asterisk implementation
├── requirements.txt
└── README.md
```

## Key Code Patterns

### Webhook Handler (webhook_server.py)
```python
from flask import Flask, request, Response
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='config/.env')

app = Flask(__name__)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    webhook_secret=os.getenv("OPENAI_WEBHOOK_SECRET")
)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Verify webhook signature
    event = client.webhooks.unwrap(request.data, request.headers)

    if event.type == "realtime.call.incoming":
        call_id = event.data.call_id

        # Accept the call with minimal config
        requests.post(
            f"https://api.openai.com/v1/realtime/calls/{call_id}/accept",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "type": "realtime",
                "model": "gpt-realtime",
                "instructions": "You are a helpful voice assistant..."
            }
        )
        return Response(status=200)
```

### Call Accept Configuration (IMPORTANT)
**Only 3 parameters are documented and supported:**
```python
call_accept_config = {
    "type": "realtime",              # Required: must be "realtime"
    "model": "gpt-realtime",         # Required: model identifier
    "instructions": "Your prompt..."  # Required: AI behavior instructions
    "turn_detection": {
        "type": "server_vad",
        "threshold": 0.5,
        "prefix_padding_ms": 300,
        "silence_duration_ms": 500
}

# ⚠️ CRITICAL: Unsupported parameters will cause 400 errors
# Do NOT include: voice, turn_detection, temperature, modalities, etc.
# These must be configured through other means or have defaults
```

### WebSocket Monitoring (Optional)
```python
async def monitor_call_websocket(call_id: str):
    """Monitor call events in real-time"""
    uri = f"wss://api.openai.com/v1/realtime?call_id={call_id}"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    async with websockets.connect(uri, additional_headers=headers) as ws:
        # Send initial response to greet caller
        await ws.send(json.dumps({
            "type": "response.create",
            "response": {
                "instructions": "Greet the caller warmly"
            }
        }))

        # Listen for events
        async for message in ws:
            event = json.loads(message)
            logger.info(f"Call event: {event['type']}")
```

## Environment Configuration

**File: `config/.env`**
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-...
OPENAI_WEBHOOK_SECRET=whsec_...
OPENAI_PROJECT_ID=proj_...

# Vonage Configuration
VONAGE_NUMBER=+447520648361

# Server Configuration
WEBHOOK_PORT=5000

# Logging
LOG_LEVEL=INFO
```

## Development Guidelines

### Getting Information from OpenAI Docs
1. Use the following official OpenAI resources:
    - OpenAI Realtime API Docs: https://platform.openai.com/docs/guides/realtime
    - OpenAI Realtime SIP Guide: https://platform.openai.com/docs/guides/realtime-sip
    - OpenAI Using realtime models: https://platform.openai.com/docs/guides/realtime-models-prompting
    - OpenAI Managing Conversation: https://platform.openai.com/docs/guides/realtime-conversations
    - OpenAI Webhooks and server-side controls: https://platform.openai.com/docs/guides/realtime-server-controls
    - OpenAI Realtime transcription: https://platform.openai.com/docs/guides/realtime-transcription
    - OpenAI Voice Agents: https://openai.github.io/openai-agents-js/guides/voice-agents
    - OpenAI Building Voice Agents: https://openai.github.io/openai-agents-js/guides/voice-agents/build/
    - Vonage SIP Trunking Docs: https://developer.vonage.com/en/voice/sip/overview
2. Refer to the OpenAI API Reference: https://platform.openai.com/docs/api-reference for detailed information on endpoints and parameters.
3. Get the LLM and Agentic Voice Agent guides from OpenAI GitHub for advanced use cases.
4. Propose new features for Happy Medical Centre based on OpenAI offerings and Voice Agent capabilities.

### Testing Strategy
1. **Unit Tests**: Test webhook handler, configuration loading
2. **Integration Tests**: Test with OpenAI webhook simulator
3. **Manual Testing**: Use real phone calls with ngrok for webhook URL
4. **Production Testing**: Deploy to server with public IP or use ngrok tunnel

### Key Debugging Tips
- **400 Bad Request errors**: Ensure call accept config only has type, model, instructions
- **Webhook signature errors**: Verify OPENAI_WEBHOOK_SECRET is correct
- **Call not connecting**: Check Vonage SIP trunk points to OpenAI endpoint
- **No audio**: OpenAI handles all audio - check call events via WebSocket

### Error Handling
- Implement reconnection logic for WebSocket drops
- Log all OpenAI API errors with full context
- Gracefully handle call disconnections
- Monitor token usage to prevent quota exhaustion

### Security Considerations
- Store API keys in environment variables, never in code
- Use Vonage IP allowlisting for SIP trunk security
- Use HTTPS for webhook endpoint (required by OpenAI)
- Verify webhook signatures to prevent spoofing

## Common Commands

```bash
# Start webhook server
python webhook_server.py

# Check webhook server logs
tail -f /tmp/webhook.log

# Test with ngrok (for local development)
ngrok http 5000

# Run Python app
python webhook_server.py

# Run with debug logging
LOG_LEVEL=DEBUG python webhook_server.py
```

## Vonage SIP Trunk Setup

1. Create application in Vonage Dashboard
2. Configure SIP trunk to point at OpenAI SIP endpoint
3. Set SIP URI: `sip:proj_YOUR_PROJECT_ID@sip.api.openai.com;transport=tls`
4. Configure webhook URL in OpenAI dashboard (Settings > Webhooks)
5. Link phone number to application

## OpenAI Realtime API Key Points

- SIP Endpoint: `sip:proj_PROJECT_ID@sip.api.openai.com;transport=tls`
- Webhook Events: Listen for `realtime.call.incoming`
- Accept Endpoint: `POST https://api.openai.com/v1/realtime/calls/{call_id}/accept`
- WebSocket Monitoring: `wss://api.openai.com/v1/realtime?call_id={call_id}`
- Authentication: Bearer token in Authorization header
- Webhook Signature Verification: Use OpenAI SDK `client.webhooks.unwrap()`

## Quick Start Checklist

- [ ] Install Python dependencies (pip install -r requirements.txt)
- [ ] Configure environment variables in config/.env
- [ ] Set up OpenAI webhook in dashboard (Settings > Webhooks)
- [ ] Configure Vonage SIP trunk to point at OpenAI SIP endpoint
- [ ] Link Vonage phone number to application
- [ ] Start webhook server (python webhook_server.py)
- [ ] Expose webhook server with ngrok or public IP
- [ ] Test with real phone call
- [ ] Monitor logs for webhook events and call acceptance
- [ ] Verify AI answers and conversation works
