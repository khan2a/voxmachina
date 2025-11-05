# VoxMachina 🎙️

**AI Phone Assistant powered by OpenAI + Vonage**

Turn any phone number into an intelligent voice assistant that can have natural conversations, schedule appointments, and transfer calls between specialists.

---

## 🎯 What is This?

**VoxMachina** = Phone System + OpenAI GPT-4 Voice

A simple Python application that connects your phone number to OpenAI's Realtime API, creating an AI assistant that answers calls and has natural voice conversations.

### 🏥 Live Demo: Happy Medical Centre

Call our demo: **+44 7520 648361**

Meet our AI team:
- 🎀 **Susan** (Receptionist) - Answers calls, schedules appointments
- 🦷 **Dr. Miller** (Dentist) - Dental health advice
- 🥗 **William** (Nutritionist) - Diet and nutrition guidance

### 🎥 Watch It In Action

See VoxMachina handling real calls with natural conversations, agent transfers, and appointment scheduling:

**[📺 Watch Demo Video](https://github.com/khan2a/voxmachina/raw/main/docs/demo.mp4)** - Complete call flow demonstration (click to view)

---

## 🏗️ How It Works

### Simple Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Caller    │  PSTN   │   Vonage    │   SIP   │   OpenAI    │
│  (Phone)    │◄───────►│ SIP Trunk   │◄───────►│     SIP     │
│             │         │             │         │  Endpoint   │
└─────────────┘         └─────────────┘         └──────┬──────┘
                                                       │
                                                   Webhook
                                                       │
                                                ┌──────▼──────┐
                                                │ VoxMachina  │
                                                │   Python    │
                                                │   Server    │
                                                └─────────────┘
```

### Call Flow Diagram

```
1. 📞 Caller dials your Vonage number
          │
          ▼
2. 📡 Vonage routes call to OpenAI SIP endpoint
          │
          ▼
3. 🔔 OpenAI sends webhook: "Incoming call!"
          │
          ▼
4. ✅ Your Python server accepts call + configures AI
          │
          ▼
5. 🎙️ OpenAI handles ALL audio & conversation
          │
          ▼
6. 📝 Your server monitors & logs (optional)
```

**Key Insight:** OpenAI does all the heavy lifting (speech recognition, AI thinking, voice synthesis). You just configure it!

---

## ✨ Features

### Core Features
- ✅ **Real-time voice conversations** with GPT-4
- ✅ **Multi-agent system** - Transfer between specialists
- ✅ **Function calling** - Schedule appointments, transfer calls
- ✅ **Call transcription** - Automatic speech-to-text
- ✅ **AI summaries** - GPT-4 generates call summaries
- ✅ **Sentiment analysis** - Track caller emotions

### Technical Features
- ✅ **Simple webhook server** (~500 lines of Python)
- ✅ **No Asterisk/PBX required** - Direct SIP integration
- ✅ **SQLite database** - Store transcripts and summaries
- ✅ **WebSocket monitoring** - Real-time event streaming
- ✅ **Pre-commit hooks** - Code quality with Ruff & Black

---

## 📋 Requirements

- ✅ **Low latency** - Direct connection, no intermediary servers- **Public IP address** (for SIP connectivity)

- ✅ **Easy deployment** - Single Python file, minimal dependencies- **OpenAI API key** with Realtime API access

- **Vonage account** with SIP trunk and phone number

## 📋 Prerequisites

### What You Need

- **OpenAI API key** with Realtime API access → [Get it here](https://platform.openai.com)
- **Vonage account** with phone number → [Sign up](https://dashboard.nexmo.com)
- **Python 3.11+** installed on your system
- **Public HTTPS URL** for webhooks (ngrok works great!)

---

## 🚀 Quick Start

### Step 1: Clone & Install

```bash
# Clone the repository
git clone https://github.com/khan2a/voxmachina.git
cd voxmachina

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks (optional, for development)
pre-commit install
```

### Step 2: Configure Environment

Create `config/.env` with your credentials:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_PROJECT_ID=proj_your-project-id
OPENAI_WEBHOOK_SECRET=whsec_your-webhook-secret

# Vonage Configuration
VONAGE_NUMBER=+447520648361

# Transcription (optional)
ENABLE_TRANSCRIPTION=true
TRANSCRIPTION_MODEL=gpt-4o-transcribe
TRANSCRIPTION_LANGUAGE=en

# Server Configuration
WEBHOOK_PORT=5000
LOG_LEVEL=INFO
```

### Step 3: Expose Webhook Endpoint

**Using ngrok (easiest for testing):**

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com

# Start tunnel
ngrok http 5000

# Copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)
```

### Step 4: Configure OpenAI Webhook

1. Go to [OpenAI Webhooks](https://platform.openai.com/settings/organization/webhooks)
2. Click **"Add webhook endpoint"**
3. Enter URL: `https://YOUR-NGROK-URL/webhook`
4. Subscribe to: `realtime.call.incoming` ✅
5. Copy the **Webhook Secret** to your `.env` file

### Step 5: Configure Vonage SIP Trunk

Point your Vonage number at OpenAI's SIP endpoint:

**Via Vonage Dashboard:**
1. Go to [Vonage Voice Settings](https://dashboard.nexmo.com/voice/your-numbers)
2. Select your phone number
3. Under "Forward to", choose **SIP**
4. Enter: `sip:proj_YOUR_PROJECT_ID@sip.api.openai.com;transport=tls`
5. Save ✅

### Step 6: Start the Server

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Start webhook server
python webhook_server.py
```

You should see:

```
INFO - Starting webhook server on port 5000...
INFO - Transcription enabled: model=gpt-4o-transcribe, language=en
INFO - Server running at http://0.0.0.0:5000
```

### Step 7: Make a Test Call 📞

Call your Vonage number and talk to the AI!

**Demo conversation:**
- "Hello!" → Susan (receptionist) answers
- "I need dental advice" → Transferred to Dr. Miller
- "My tooth hurts" → Gets professional dental guidance

---

## 📁 Project Structure

```
voxmachina/
├── webhook_server.py          # Main Flask webhook server (500 lines)
├── view_transcripts.py        # CLI tool to view call transcripts
├── config/
│   ├── .env                   # Your credentials (create this)
│   └── prompts.json           # AI agent configurations
├── src/
│   ├── transcript_storage.py  # Database & AI summaries
│   └── __init__.py
├── data/
│   ├── transcripts.db         # SQLite database (auto-created)
│   └── exports/               # Exported call data
├── docs/
│   ├── QUICKSTART.md
│   ├── OPENAI_SIP_SETUP.md
│   ├── TRANSCRIPTION_FEATURE.md
│   ├── CODE_QUALITY.md
│   └── PROJECT_STRUCTURE.md
├── tests/                     # Unit tests
├── requirements.txt           # Python dependencies
├── .pre-commit-config.yaml    # Code quality hooks
├── ruff.toml                  # Linter configuration
└── pyproject.toml             # Black formatter config
```

---

## 🎨 Customization Guide

### 1. Modify AI Agents

Edit `config/prompts.json` to change agent behavior:

```json
{
  "agents": {
    "receptionist": {
      "name": "Susan",
      "voice": "coral",
      "instructions": "You are a friendly receptionist..."
    }
  }
}
```

**Available Voices:**
- 🎀 `coral` - Warm female (receptionist)
- 📣 `echo` - Professional male (dentist)
- ⚫ `onyx` - Deep masculine male (nutritionist)
- ✨ `alloy`, `shimmer`, `sage`, `verse`, `ballad` - Other options

### 2. View Call Transcripts

```bash
# List recent calls
python view_transcripts.py --list

# View transcript
python view_transcripts.py --transcript call_xyz123

# View AI summary
python view_transcripts.py --summary call_xyz123

# Export to JSON
python view_transcripts.py --export call_xyz123
```

### 3. Add Custom Functions

**Step 1:** Define function in `config/prompts.json`:

```json
{
  "functions": [
    {
      "name": "check_inventory",
      "description": "Check if product is in stock",
      "parameters": {
        "type": "object",
        "properties": {
          "product_id": {"type": "string"}
        },
        "required": ["product_id"]
      }
    }
  ]
}
```

**Step 2:** Implement handler in `webhook_server.py`:

```python
async def handle_check_inventory(websocket, call_id, func_call_id, arguments):
    args = json.loads(arguments)
    product_id = args.get("product_id")

    # Check your database
    in_stock = your_database_check(product_id)

    # Send result to AI
    await websocket.send(json.dumps({
        "type": "conversation.item.create",
        "item": {
            "type": "function_call_output",
            "call_id": func_call_id,
            "output": json.dumps({"in_stock": in_stock})
        }
    }))
```

---

## 🔧 Configuration Options

### Turn Detection Settings

Control how AI detects when user stops speaking:

```json
"turn_detection": {
  "type": "server_vad",
  "threshold": 0.5,        // 0-1, lower = more sensitive
  "prefix_padding_ms": 300, // Audio before speech
  "silence_duration_ms": 500 // Wait time after speech
}
```

### Transcription Settings

In `config/.env`:

```bash
ENABLE_TRANSCRIPTION=true
TRANSCRIPTION_MODEL=gpt-4o-transcribe
TRANSCRIPTION_LANGUAGE=en  # Options: en, es, fr, de, ja, zh, etc.
```

### Logging Levels

```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

---

## 💰 Cost Breakdown

### OpenAI Realtime API
- **Input Audio:** $0.06/minute
- **Output Audio:** $0.24/minute
- **GPT-4 Summaries:** ~$0.01/call
- **Total: ~$0.30/minute** ($18/hour)

### Vonage
- **Phone Number:** $1-5/month
- **Incoming Calls:** $0.0040-0.0120/minute (varies by country)

### Example Budget
- **1-hour hackathon demo:** ~$20
- **100 calls @ 2 min avg:** ~$60
- **Production (100 calls/day):** ~$600/month

💡 **Tip:** Use short test calls during development!

---

## 🐛 Troubleshooting

### Webhook Not Receiving Calls

**Check these:**
1. ✅ ngrok tunnel is running
2. ✅ Webhook URL in OpenAI dashboard is correct
3. ✅ `OPENAI_WEBHOOK_SECRET` matches exactly
4. ✅ Flask server is running on port 5000

**Test webhook:**
```bash
curl https://your-ngrok-url.ngrok-free.app/webhook
# Should return: "Webhook endpoint is active"
```

### Call Connects But No Audio

**Common causes:**
- ❌ Wrong OpenAI Project ID in Vonage SIP URI
- ❌ Missing `transport=tls` in SIP URI
- ❌ OpenAI API key doesn't have Realtime API access

**Verify SIP URI format:**
```
sip:proj_YOUR_PROJECT_ID@sip.api.openai.com;transport=tls
```

### AI Not Responding

**Debug steps:**
1. Check WebSocket logs in terminal
2. Verify API quota: https://platform.openai.com/usage
3. Test instructions are clear in `prompts.json`
4. Check `turn_detection` threshold isn't too high

### "Invalid Webhook Signature" Error

- ✅ Copy secret exactly from OpenAI dashboard (no extra spaces)
- ✅ Restart server after updating `.env`
- ✅ Check no proxy/middleware is modifying requests

### Database Errors

```bash
# Reset database if corrupted
rm data/transcripts.db
python webhook_server.py  # Will recreate automatically
```

---

## 📚 Documentation

- 📖 [OpenAI Realtime API Docs](https://platform.openai.com/docs/guides/realtime)
- 📖 [OpenAI SIP Integration](https://platform.openai.com/docs/guides/realtime-sip)
- 📖 [Vonage Voice API](https://developer.vonage.com/en/voice/voice-api/overview)
- 📖 [Project Documentation](docs/)

**Project Docs:**
- `docs/QUICKSTART.md` - Quick setup guide
- `docs/OPENAI_SIP_SETUP.md` - Detailed OpenAI configuration
- `docs/TRANSCRIPTION_FEATURE.md` - Transcription system overview
- `docs/CODE_QUALITY.md` - Development tools & linting

---

## 🧪 Testing

### Run Unit Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_webhook_server.py -v
```

### Test Webhook Health

```bash
curl http://localhost:5000/health
# Expected: {"status": "healthy"}
```

### Manual Call Test

1. Start server: `python webhook_server.py`
2. Call your Vonage number
3. Watch logs in terminal
4. Verify conversation works
5. Check database: `python view_transcripts.py --list`

---

## 🚀 Deployment

### Option 1: Render.com (Recommended)

```bash
# 1. Create render.yaml
services:
  - type: web
    name: voxmachina
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python webhook_server.py
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: OPENAI_PROJECT_ID
        sync: false
```

### Option 2: Railway.app

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login & deploy
railway login
railway init
railway up
```

### Option 3: DigitalOcean

```bash
# 1. Create Droplet (Ubuntu 22.04)
# 2. SSH into server
ssh root@your-server-ip

# 3. Clone & setup
git clone https://github.com/khan2a/voxmachina.git
cd voxmachina
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure systemd service
sudo nano /etc/systemd/system/voxmachina.service
```

**systemd service file:**
```ini
[Unit]
Description=VoxMachina Webhook Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/voxmachina
Environment=PATH=/root/voxmachina/venv/bin
ExecStart=/root/voxmachina/venv/bin/python webhook_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable & start
sudo systemctl enable voxmachina
sudo systemctl start voxmachina
sudo systemctl status voxmachina
```

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Code Quality

We use pre-commit hooks with ruff and black:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Or use script
./check_code_quality.sh
```

**Coding Standards:**
- Line length: 100 characters
- Use type hints
- Add docstrings to functions
- Write unit tests for new features

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- 🤖 **OpenAI** - For the incredible Realtime API
- 📞 **Vonage** - For reliable SIP infrastructure
- 🐍 **Python Community** - For amazing tools and libraries

---

## 📞 Get Help

- 💬 [GitHub Discussions](https://github.com/khan2a/voxmachina/discussions)
- 🐛 [Report Issues](https://github.com/khan2a/voxmachina/issues)
- 📧 Email: [your-email@example.com]
- 🌐 Demo: Call **+44 7520 648361**

---

## 🌟 Show Your Support

If VoxMachina helped you build something cool:
- ⭐ **Star this repository**
- 🔀 **Fork and customize**
- 📢 **Share your project**
- 💬 **Tell us about your use case**

---

<div align="center">

**Built with ❤️ for developers building voice AI applications**

![OpenAI](https://img.shields.io/badge/OpenAI-Realtime%20API-412991?style=flat&logo=openai)
![Vonage](https://img.shields.io/badge/Vonage-SIP%20Trunk-00B2A9?style=flat)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

**[Try the Demo](tel:+447520648361) • [Read the Docs](docs/) • [Report Bug](https://github.com/khan2a/voxmachina/issues)**

</div>
