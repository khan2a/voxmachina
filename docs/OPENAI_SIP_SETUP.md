# OpenAI SIP Connector Setup Guide

## Architecture Overview

**New Simple Flow:**
```
Vonage Number → OpenAI SIP Endpoint → Webhook Server → Monitor via WebSocket
```

OpenAI handles **all audio processing** automatically. Your server just:
1. Receives webhook when call arrives
2. Accepts/rejects the call via API
3. Monitors conversation via WebSocket (optional)

## Prerequisites

- ✅ OpenAI API account with Realtime API access
- ✅ Vonage account with SIP trunk
- ✅ Mac with Python 3.9+
- ✅ ngrok or Cloudflare Tunnel for webhook URL

## Step 1: Get OpenAI Project ID

Your OpenAI Project ID is needed for the SIP endpoint.

1. Visit https://platform.openai.com/settings/organization/general
2. Find your **Project ID** (starts with `proj_`)
3. Save it - you'll use: `sip:YOUR_PROJECT_ID@sip.api.openai.com;transport=tls`

**Example:**
```
Project ID: proj_abc123xyz
SIP Endpoint: sip:proj_abc123xyz@sip.api.openai.com;transport=tls
```

## Step 2: Configure Webhook in OpenAI

1. Go to https://platform.openai.com/settings/organization/webhooks
2. Click **"Add webhook endpoint"**
3. Enter your webhook URL (use ngrok for testing):
   ```
   https://YOUR_NGROK_ID.ngrok.io/webhook
   ```
   Or your production domain:
   ```
   https://yourdomain.com/webhook
   ```

4. Subscribe to events:
   - ✅ `realtime.call.incoming` (required)
   - ✅ `realtime.call.ended` (optional)

5. Save the **Webhook Secret** that OpenAI generates
6. Add to your `.env`:
   ```bash
   OPENAI_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
   ```

## Step 3: Install Dependencies

```bash
cd /path/to/voxmachina
pip install -r requirements.txt
```

## Step 4: Update Environment Variables

Edit `config/.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-...
OPENAI_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx  # From Step 2
OPENAI_PROJECT_ID=proj_abc123xyz  # From Step 1

# Webhook Server
WEBHOOK_PORT=5000

# Logging
LOG_LEVEL=INFO
```

## Step 5: Configure Vonage SIP Trunk

**IMPORTANT:** Point Vonage directly at OpenAI, not your Asterisk server.

### Option A: Via Vonage Dashboard

1. Go to https://dashboard.nexmo.com/voice/your-numbers
2. Click on your number: `+447520648361`
3. Under "Forward to", select **"SIP"**
4. Enter SIP URI:
   ```
   sip:proj_YOUR_PROJECT_ID@sip.api.openai.com;transport=tls
   ```
5. Save changes

### Option B: Via Vonage API

```bash
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

## Step 6: Expose Webhook Server

You need a public HTTPS endpoint for OpenAI to send webhooks to.

### Option A: ngrok (Easiest for Testing)

```bash
# Install ngrok on Mac
brew install ngrok

# Auth ngrok (get token from https://dashboard.ngrok.com/get-started/your-authtoken)
ngrok config add-authtoken YOUR_NGROK_TOKEN

# Start tunnel
ngrok http 5000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Update OpenAI webhook config with: https://abc123.ngrok.io/webhook
```

### Option B: Cloudflare Tunnel (Free, No Account Required)

```bash
# Install cloudflared on Mac
brew install cloudflare/cloudflare/cloudflared

# Start tunnel
cloudflared tunnel --url http://localhost:5000

# Copy the HTTPS URL and update OpenAI webhook config
```

### Option C: Production Deployment

For production, deploy to a cloud service with a public IP:
- AWS EC2, Google Cloud, DigitalOcean, etc.
- Use Let's Encrypt for SSL certificates
- Configure firewall to allow HTTPS (port 443)
### Option B: Cloudflare Tunnel (Recommended for Raspberry Pi)

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/

# Start tunnel
cloudflared tunnel --url http://localhost:5000

# Copy the HTTPS URL and update OpenAI webhook config
```

### Option C: Nginx + Let's Encrypt (Production)

```bash
# Install nginx and certbot
sudo apt-get install nginx certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com

# Configure nginx proxy (see nginx config below)
sudo systemctl restart nginx
```

**Nginx Config (`/etc/nginx/sites-available/voxmachina`):**
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location /webhook {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Step 7: Run Webhook Server

```bash
cd /path/to/voxmachina

# Run webhook server
python webhook_server.py
```

**Expected Output:**
```
============================================================
Starting VoxMachina Webhook Server
============================================================
Port: 5000
OpenAI API Key: Set
Webhook Secret: Set
============================================================
 * Serving Flask app 'webhook_server'
 * Running on http://0.0.0.0:5000
```

## Step 8: Test End-to-End

1. **Check webhook health:**
   ```bash
   curl http://localhost:5000/health
   # Should return: {"status": "healthy", "service": "voxmachina-webhook"}
   ```

2. **Call your Vonage number:** `+447520648361`

3. **Watch logs:**
   ```
   Received webhook: realtime.call.incoming
   Incoming call: call_abc123
     From: +1234567890
     To: +447520648361
   Call call_abc123 accepted successfully
   WebSocket connected for call call_abc123
   Sent initial response request for call call_abc123
   Call call_abc123: AI speaking: Hello! I'm the VoxMachina AI assistant...
   Call call_abc123: User said: Hello, can you help me?
   ```

4. **Have a conversation!** OpenAI handles everything:
   - Speech recognition (your voice → text)
   - AI generation (GPT-4 response)
   - Speech synthesis (text → voice)
   - Audio streaming over SIP

## Customization

### Change AI Personality

Edit `webhook_server.py`, line 31:

```python
call_accept_config = {
    "instructions": "You are a pirate captain named Blackbeard. Respond to all questions with pirate slang and nautical themes. Be enthusiastic!",
    "voice": "echo",  # More theatrical voice
}
```

### Add Function Calling

Enable the AI to take actions (e.g., check weather, book appointments):

```python
call_accept_config = {
    "tools": [
        {
            "type": "function",
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    ],
    # ... rest of config
}
```

Then handle function calls in the WebSocket monitor.

### Enable Call Recording

```python
call_accept_config = {
    "enable_recording": True,
    # ... rest of config
}
```

Recordings will be available via OpenAI API after the call ends.

## Troubleshooting

### Webhook not receiving calls
- ✅ Verify OpenAI webhook URL is correct and publicly accessible
- ✅ Check OpenAI webhook logs: https://platform.openai.com/settings/organization/webhooks
- ✅ Ensure webhook secret in `.env` matches OpenAI dashboard
- ✅ Test webhook endpoint: `curl https://your-url/webhook` should return 400 (not 200)

### Call connects but no audio
- ✅ Verify Vonage SIP URI points to OpenAI, not Asterisk
- ✅ Check OpenAI Project ID is correct in SIP URI
- ✅ Ensure `transport=tls` is in SIP URI
- ✅ Check OpenAI API key has Realtime API access

### AI not responding
- ✅ Check WebSocket logs for errors
- ✅ Verify `initial_response` is being sent
- ✅ Check OpenAI API quotas: https://platform.openai.com/usage
- ✅ Test voice instructions are clear and specific

### Webhook secret validation fails
- ✅ Copy webhook secret exactly from OpenAI dashboard (starts with `whsec_`)
- ✅ Ensure no extra spaces or newlines in `.env`
- ✅ Restart webhook server after updating `.env`

## Advantages Over Asterisk Approach

✅ **No audio bridge needed** - OpenAI handles SIP/RTP natively
✅ **No codec conversion** - OpenAI manages all audio formats
✅ **No RTP streaming** - No need for custom packet handling
✅ **Simpler deployment** - Just one Python process, no Asterisk
✅ **Better latency** - Fewer hops in audio path
✅ **Official support** - OpenAI maintains the SIP connector
✅ **Built-in features** - Recording, transcription, function calling included

## Cost Estimate

**Per Minute Pricing:**
- Audio input: ~$0.06/min (at 24kHz)
- Audio output: ~$0.24/min (text-to-speech)
- Total: ~$0.30/min or **$18/hour** of conversation

**For hackathon testing:** ~$5-10 should be plenty

## Next Steps

1. ✅ Get OpenAI Project ID
2. ✅ Configure webhook endpoint
3. ✅ Install dependencies and run webhook server
4. ✅ Update Vonage to point to OpenAI SIP
5. ✅ Test with real phone call
6. 🎉 You have a working AI voice agent!

## Resources

- [OpenAI Realtime SIP Docs](https://platform.openai.com/docs/guides/realtime-sip)
- [OpenAI Realtime API Reference](https://platform.openai.com/docs/api-reference/realtime)
- [Vonage SIP Documentation](https://developer.vonage.com/en/voice/sip/overview)
- [OpenAI Webhook Events](https://platform.openai.com/docs/api-reference/webhooks)
