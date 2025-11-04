"""
Happy Medical Centre Webhook Server
Handles incoming call webhooks from OpenAI Realtime API SIP connector
Multi-agent system for medical centre,
with receptionist, dentist, and nutritionist
"""

import asyncio
import json
import logging
import os
import threading
from pathlib import Path

import requests
import websockets
from dotenv import load_dotenv
from flask import Flask, Response, request
from openai import OpenAI

from src.transcript_storage import TranscriptStorage

# Load environment variables from config/.env
env_path = Path(__file__).parent / "config" / ".env"
load_dotenv(dotenv_path=env_path)

# Load prompts configuration
prompts_path = Path(__file__).parent / "config" / "prompts.json"
with open(prompts_path) as f:
    PROMPTS_CONFIG = json.load(f)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    # Get from OpenAI dashboard
    webhook_secret=os.getenv("OPENAI_WEBHOOK_SECRET"),
)

AUTH_HEADER = {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"}

# Transcription configuration
ENABLE_TRANSCRIPTION = os.getenv("ENABLE_TRANSCRIPTION", "true").lower() == "true"
TRANSCRIPTION_MODEL = os.getenv("TRANSCRIPTION_MODEL", "gpt-4o-transcribe")
TRANSCRIPTION_LANGUAGE = os.getenv("TRANSCRIPTION_LANGUAGE", "en")

# Initialize transcript storage
transcript_storage = TranscriptStorage(
    db_path="data/transcripts.db", openai_api_key=os.getenv("OPENAI_API_KEY")
)


def get_agent_config(agent_name: str = "receptionist") -> dict:
    """
    Get agent configuration from prompts.json with optional transcription

    Args:
        agent_name: Name of the agent (receptionist, dentist, nutritionist)

    Returns:
        Dictionary with agent configuration including transcription settings
    """
    agent = PROMPTS_CONFIG["agents"].get(agent_name, {})

    if not agent:
        logger.warning(f"Agent {agent_name} not found, using receptionist")
        agent = PROMPTS_CONFIG["agents"]["receptionist"]

    # Get functions from prompts.json and convert to tools format
    tools = []
    for func in PROMPTS_CONFIG.get("functions", []):
        tools.append(
            {
                "type": "function",
                "name": func["name"],
                "description": func["description"],
                "parameters": func["parameters"],
            }
        )

    # IMPORTANT: Call accept only supports 3 parameters
    # tools must be configured via WebSocket session.update
    config = {"type": "realtime", "model": "gpt-realtime", "instructions": agent["instructions"]}

    # Add transcription configuration if enabled
    if ENABLE_TRANSCRIPTION:
        config["audio"] = {
            "input": {
                "transcription": {"model": TRANSCRIPTION_MODEL, "language": TRANSCRIPTION_LANGUAGE}
            }
        }
        logger.info(
            f"Transcription enabled: model={TRANSCRIPTION_MODEL}, language={TRANSCRIPTION_LANGUAGE}"
        )

    return config


def get_session_tools() -> list:
    """
    Get tools configuration for WebSocket session.update

    Returns:
        List of tool configurations from prompts.json
    """
    tools = []
    for func in PROMPTS_CONFIG.get("functions", []):
        tools.append(
            {
                "type": "function",
                "name": func["name"],
                "description": func["description"],
                "parameters": func["parameters"],
            }
        )

    return tools


def get_initial_greeting(agent_name: str = "receptionist") -> dict:
    """
    Get initial greeting response for agent

    Args:
        agent_name: Name of the agent (receptionist, dentist, nutritionist)

    Returns:
        Dictionary with initial response configuration
    """
    prompts = PROMPTS_CONFIG["prompts"].get(agent_name, {})
    greeting = prompts.get(
        "greeting", f"Hello! Welcome to {PROMPTS_CONFIG['medical_centre']['name']}."
    )

    return {"type": "response.create", "response": {"instructions": f"Say: {greeting}"}}


async def handle_transfer_call(websocket, call_id: str, func_call_id: str, arguments: str):
    """
    Handle transfer_call function - transfer to another agent

    Args:
        websocket: WebSocket connection
        call_id: Call identifier
        func_call_id: Function call identifier
        arguments: JSON string with target_agent, reason, caller_name
    """
    try:
        args = json.loads(arguments)
        target_agent = args.get("target_agent", "receptionist")
        reason = args.get("reason", "")

        logger.info(f"Call {call_id}: Transferring to {target_agent} " f"(Reason: {reason})")

        # Get target agent greeting
        target_prompts = PROMPTS_CONFIG["prompts"].get(target_agent, {})
        greeting = target_prompts.get("greeting", f"Hello, this is {target_agent}.")

        # Send function call output
        output_msg = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": func_call_id,
                "output": json.dumps(
                    {
                        "status": "transferred",
                        "target_agent": target_agent,
                        "message": f"Transferring to {target_agent}",
                    }
                ),
            },
        }
        await websocket.send(json.dumps(output_msg))

        # Update session to use target agent's instructions
        agent_config = PROMPTS_CONFIG["agents"].get(target_agent, {})
        session_update = {
            "type": "session.update",
            "session": {
                "type": "realtime",
                "model": "gpt-realtime",
                "instructions": agent_config.get("instructions", ""),
            },
        }
        await websocket.send(json.dumps(session_update))

        # Create response with target agent greeting
        response_msg = {"type": "response.create", "response": {"instructions": f"Say: {greeting}"}}
        await websocket.send(json.dumps(response_msg))

        logger.info(f"Call {call_id}: Successfully transferred to {target_agent}")

    except Exception as e:
        logger.error(f"Call {call_id}: Error handling transfer_call: {e}")
        # Send error as function output
        error_output = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": func_call_id,
                "output": json.dumps({"status": "error", "message": str(e)}),
            },
        }
        await websocket.send(json.dumps(error_output))


async def handle_schedule_appointment(websocket, call_id: str, func_call_id: str, arguments: str):
    """
    Handle schedule_appointment function

    Args:
        websocket: WebSocket connection
        call_id: Call identifier
        func_call_id: Function call identifier
        arguments: JSON string with name, phone, date, time, reason
    """
    try:
        args = json.loads(arguments)
        name = args.get("name", "")
        phone = args.get("phone", "")
        date = args.get("date", "")
        time = args.get("time", "")
        reason = args.get("reason", "")

        logger.info(f"Call {call_id}: Scheduling appointment for {name} " f"on {date} at {time}")

        # TODO: Implement actual appointment scheduling logic
        # For now, just log and confirm

        # Send function call output
        output_msg = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": func_call_id,
                "output": json.dumps(
                    {
                        "status": "scheduled",
                        "appointment": {
                            "name": name,
                            "phone": phone,
                            "date": date,
                            "time": time,
                            "reason": reason,
                        },
                        "confirmation": (
                            f"Appointment scheduled for {name} " f"on {date} at {time}"
                        ),
                    }
                ),
            },
        }
        await websocket.send(json.dumps(output_msg))

        # Create response to confirm
        response_msg = {"type": "response.create"}
        await websocket.send(json.dumps(response_msg))

        logger.info(f"Call {call_id}: Appointment scheduled successfully")

    except Exception as e:
        logger.error(f"Call {call_id}: Error scheduling appointment: {e}")
        # Send error as function output
        error_output = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": func_call_id,
                "output": json.dumps({"status": "error", "message": str(e)}),
            },
        }
        await websocket.send(json.dumps(error_output))


async def monitor_call_websocket(call_id: str, agent_name: str = "receptionist"):
    """
    Monitor the call via WebSocket and log events
    Connect to OpenAI's Realtime API to track the conversation

    Args:
        call_id: The unique call identifier
        agent_name: The agent handling the call (default: receptionist)
    """
    ws_url = f"wss://api.openai.com/v1/realtime?call_id={call_id}"

    try:
        logger.info(f"Connecting to WebSocket for call {call_id}")

        async with websockets.connect(ws_url, additional_headers=AUTH_HEADER) as websocket:
            logger.info(f"WebSocket connected for call {call_id}")

            # Configure session with tools (functions)
            # session.update requires type and model fields
            tools = get_session_tools()
            if tools:
                session_update = {
                    "type": "session.update",
                    "session": {
                        "type": "realtime",
                        "model": "gpt-realtime",
                        "tools": tools,
                        "tool_choice": "auto",
                    },
                }
                await websocket.send(json.dumps(session_update))
                logger.info(f"Call {call_id}: Configured {len(tools)} tools")

            # Send initial greeting request
            initial_greeting = get_initial_greeting(agent_name)
            await websocket.send(json.dumps(initial_greeting))
            logger.info(f"Sent initial greeting for call {call_id}")

            # Listen for events
            while True:
                try:
                    message = await websocket.recv()
                    event = json.loads(message)

                    event_type = event.get("type", "unknown")

                    # Log important events
                    if event_type == "conversation.item.created":
                        item = event.get("item", {})
                        if item.get("type") == "function_call":
                            func_name = item.get("name", "unknown")
                            logger.info(f"Call {call_id}: Function call - {func_name}")
                        else:
                            logger.info(f"Call {call_id}: Conversation item created")
                    elif event_type == "response.audio.delta":
                        # Audio is being sent to caller
                        pass  # Too verbose to log every audio chunk
                    elif event_type == "response.audio_transcript.delta":
                        transcript = event.get("delta", "")
                        if transcript:
                            logger.info(f"Call {call_id}: AI speaking: {transcript}")
                    elif event_type == "conversation.item.input_audio_transcription.delta":
                        # Real-time transcription streaming (incremental)
                        delta = event.get("delta", "")
                        if delta and ENABLE_TRANSCRIPTION:
                            logger.debug(f"Call {call_id}: Transcription delta: {delta}")
                    elif event_type == "conversation.item.input_audio_transcription.completed":
                        # Complete transcription of patient's speech
                        transcript = event.get("transcript", "")
                        item_id = event.get("item_id", "")
                        logger.info(f"Call {call_id}: Patient said: {transcript}")

                        # Store transcript in database
                        if ENABLE_TRANSCRIPTION and transcript:
                            transcript_storage.save_transcript(
                                call_id=call_id,
                                item_id=item_id,
                                transcript=transcript,
                                speaker="patient",
                                agent_name=agent_name,
                            )
                    elif event_type == "response.function_call_arguments.done":
                        # Function call completed
                        func_name = event.get("name", "")
                        args = event.get("arguments", "")
                        call_id_func = event.get("call_id", "")
                        logger.info(
                            f"Call {call_id}: Function {func_name} " f"called with args: {args}"
                        )

                        # Handle transfer_call function
                        if func_name == "transfer_call":
                            await handle_transfer_call(websocket, call_id, call_id_func, args)
                        elif func_name == "schedule_appointment":
                            await handle_schedule_appointment(
                                websocket, call_id, call_id_func, args
                            )
                    elif event_type == "error":
                        error_msg = event.get("error", {})
                        logger.error(f"Call {call_id}: Error - {error_msg}")
                    else:
                        logger.debug(f"Call {call_id}: Event - {event_type}")

                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"WebSocket closed for call {call_id}")

                    # Generate call summary when call ends
                    if ENABLE_TRANSCRIPTION:
                        logger.info(f"Generating summary for call {call_id}...")
                        summary = await transcript_storage.generate_call_summary(
                            call_id=call_id, agent_name=agent_name
                        )
                        if summary:
                            logger.info(f"Call {call_id} summary: {summary[:100]}...")
                    break
                except Exception as e:
                    logger.error(f"Error processing WebSocket message " f"for call {call_id}: {e}")

    except Exception as e:
        logger.error(f"WebSocket connection error for call {call_id}: {e}")


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Handle incoming webhooks from OpenAI
    This receives realtime.call.incoming events when someone calls
    """
    try:
        # Verify webhook signature (important for security)
        event = client.webhooks.unwrap(request.data, request.headers)

        logger.info(f"Received webhook: {event.type}")

        if event.type == "realtime.call.incoming":
            call_id = event.data.call_id
            sip_headers = event.data.sip_headers

            # Log call details
            from_number = next((h.value for h in sip_headers if h.name == "From"), "Unknown")
            to_number = next((h.value for h in sip_headers if h.name == "To"), "Unknown")

            logger.info(f"Incoming call: {call_id}")
            logger.info(f"  From: {from_number}")
            logger.info(f"  To: {to_number}")

            # Get receptionist agent config (default entry point)
            agent_name = "receptionist"
            call_config = get_agent_config(agent_name)

            # Accept the call with receptionist configuration
            accept_url = f"https://api.openai.com/v1/realtime/calls/{call_id}/accept"

            try:
                logger.info(f"Accepting call as {agent_name}: " f"{json.dumps(call_config)}")
                response = requests.post(
                    accept_url,
                    headers={**AUTH_HEADER, "Content-Type": "application/json"},
                    json=call_config,
                    timeout=10,
                )
                logger.info(f"Accept response status: {response.status_code}")

                if response.status_code == 200:
                    logger.info(f"Call {call_id} accepted as {agent_name}")

                    # Start WebSocket monitoring in background thread
                    threading.Thread(
                        target=lambda: asyncio.run(monitor_call_websocket(call_id, agent_name)),
                        daemon=True,
                    ).start()

                else:
                    logger.error(f"Failed to accept call {call_id}: {response.status_code}")
                    logger.error(f"Response headers: {dict(response.headers)}")
                    logger.error(f"Response body: {response.text}")
                    try:
                        error_json = response.json()
                        logger.error(f"Error details: {error_json}")
                    except Exception:
                        pass

            except Exception as e:
                logger.error(f"Error accepting call {call_id}: {e}")

            return Response(status=200)

        elif event.type == "realtime.call.ended":
            call_id = event.data.call_id
            logger.info(f"Call ended: {call_id}")
            return Response(status=200)

        else:
            logger.info(f"Unhandled webhook type: {event.type}")
            return Response(status=200)

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return Response(f"Error: {str(e)}", status=400)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    medical_centre_name = PROMPTS_CONFIG["medical_centre"]["name"]
    return {
        "status": "healthy",
        "service": f"{medical_centre_name} Webhook Server",
        "agents": list(PROMPTS_CONFIG["agents"].keys()),
    }


if __name__ == "__main__":
    # Get port from environment or default to 5000
    port = int(os.getenv("WEBHOOK_PORT", 5000))

    medical_centre_name = PROMPTS_CONFIG["medical_centre"]["name"]
    agents = ", ".join(PROMPTS_CONFIG["agents"].keys())

    logger.info("=" * 60)
    logger.info(f"Starting {medical_centre_name} Webhook Server")
    logger.info("=" * 60)
    logger.info(f"Port: {port}")
    logger.info(f"Medical Centre: {medical_centre_name}")
    logger.info(f"Available Agents: {agents}")
    api_key_status = "Set" if os.getenv("OPENAI_API_KEY") else "NOT SET"
    logger.info(f"OpenAI API Key: {api_key_status}")
    webhook_status = "Set" if os.getenv("OPENAI_WEBHOOK_SECRET") else "NOT SET"
    logger.info(f"Webhook Secret: {webhook_status}")
    logger.info("=" * 60)

    # Run Flask server
    app.run(host="0.0.0.0", port=port, debug=False)
