# 🚀 VoxMachina Quick Start

```
Phone → Vonage → OpenAI SIP → Webhook → Done! ✅
```

## 5-Minute Setup

### 1️⃣ Get Your OpenAI Project ID
Visit: https://platform.openai.com/settings/organization/general
Copy the **Project ID** (starts with `proj_`)

### 2️⃣ Configure Webhook
Visit: https://platform.openai.com/settings/organization/webhooks

Click **"Add webhook endpoint"**

For testing (with ngrok):
```bash
# On Mac
brew install ngrok
ngrok http 5000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Add to OpenAI: https://abc123.ngrok.io/webhook
```

Subscribe to: `realtime.call.incoming` + `realtime.call.ended`

Copy the **Webhook Secret** (starts with `whsec_`)

### 3️⃣ Update Environment

Edit `config/.env`:

```bash
OPENAI_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
OPENAI_PROJECT_ID=proj_abc123xyz
WEBHOOK_PORT=5000
```

### 4️⃣ Install Dependencies

```bash
cd /path/to/voxmachina
pip install -r requirements.txt
```

### 5️⃣ Update Vonage

**Option A: Dashboard** (easiest)
1. Go to: https://dashboard.nexmo.com/voice/your-numbers
2. Click on `+447520648361`
3. Forward to SIP: `sip:proj_YOUR_PROJECT_ID@sip.api.openai.com;transport=tls`
4. Save

**Option B: API**
```bash
# Replace proj_abc123xyz with your actual Project ID
curl -X POST https://api.nexmo.com/v1/applications \
  -u "c859b7c1:MY7tmruNN$" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "VoxMachina OpenAI",
    "capabilities": {
      "voice": {
        "webhooks": {
          "answer_url": {
            "address": "sip:proj_YOUR_PROJECT_ID@sip.api.openai.com;transport=tls",
            "http_method": "POST"
          }
        }
      }
    }
  }'
```

### 6️⃣ Run Everything

**Terminal 1: Install ngrok (first time only)**
```bash
# On Mac
brew install ngrok

# Auth ngrok (get token from https://dashboard.ngrok.com/get-started/your-authtoken)
ngrok config add-authtoken YOUR_NGROK_TOKEN
```

**Terminal 1: Run ngrok**
```bash
ngrok http 5000
# Leave running, copy HTTPS URL (e.g., https://abc123.ngrok.io)
```

**Terminal 2: Webhook Server**
```bash
cd /path/to/voxmachina
python webhook_server.py
```

**Alternative: Use Cloudflare Tunnel (no account needed)**
```bash
# Terminal 1
brew install cloudflare/cloudflare/cloudflared
cloudflared tunnel --url http://localhost:5000
# Copy the HTTPS URL provided
```

### 7️⃣ Test It!

Call your number: **+447520648361**

Expected logs:
```
Received webhook: realtime.call.incoming
Incoming call: call_abc123
Call call_abc123 accepted successfully
WebSocket connected for call call_abc123
Call call_abc123: AI speaking: Hello! I'm the VoxMachina AI assistant...
```

## Troubleshooting

**"Webhook Secret validation failed"**
```bash
# Verify secret in .env matches OpenAI dashboard exactly
echo $OPENAI_WEBHOOK_SECRET  # Should start with whsec_
```

**"Call not connecting"**
```bash
# Check Vonage SIP URI
# Should be: sip:proj_YOUR_PROJECT_ID@sip.api.openai.com;transport=tls
# NOT: sip:your-server-ip:5060
```

**"No audio"**
```bash
# Verify OpenAI Project ID is correct
# Check OpenAI API key has Realtime API access
# Ensure transport=tls is in SIP URI
```

**"Webhook not receiving calls"**
```bash
# Test ngrok URL is public
curl https://YOUR_NGROK_ID.ngrok.io/health

# Should return: {"status": "healthy", "service": "voxmachina-webhook"}
```

## Customize AI

Edit `webhook_server.py`, line 31:

**Personality:**
```python
"instructions": "You are a friendly robot assistant named VoxMachina..."
```

**Voice:**
```python
"voice": "alloy"  # Options: alloy, echo, shimmer
```

**Turn Detection (sensitivity):**
```python
"turn_detection": {
    "threshold": 0.5,  # Lower = more sensitive (0.0 - 1.0)
    "silence_duration_ms": 500  # How long to wait for user
}
```

## What You Get

✅ **Automatic speech recognition** - OpenAI Whisper
✅ **AI conversation** - GPT-4 Realtime
✅ **Natural voice synthesis** - OpenAI TTS
✅ **SIP/RTP handling** - OpenAI manages all audio
✅ **Call transcripts** - Logged automatically
✅ **Function calling** - Extend with custom actions
✅ **Recording** - Enable in config

## Cost

~$0.30/minute = ~$18/hour of conversation

For hackathon testing: $5-10 budget is plenty

## Files

- `webhook_server.py` - Main webhook server (Flask)
- `docs/OPENAI_SIP_SETUP.md` - Full setup guide
- `config/.env` - Environment variables
- `requirements.txt` - Python dependencies

## Resources

📖 [Full Setup Guide](docs/OPENAI_SIP_SETUP.md)
🔗 [OpenAI Realtime SIP Docs](https://platform.openai.com/docs/guides/realtime-sip)
🔗 [OpenAI Dashboard](https://platform.openai.com/settings)
🔗 [Vonage Dashboard](https://dashboard.nexmo.com)

## Status

🔴 **Old Asterisk Approach**: Abandoned (External Media 404)
🟢 **New OpenAI SIP Approach**: Ready to test

**Next Step**: Get OpenAI Project ID → Configure webhook → Test call
