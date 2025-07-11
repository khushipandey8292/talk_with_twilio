import base64
import json
from fastapi import FastAPI, WebSocket, Request
from fastapi.templating import Jinja2Templates
from speechclientbridge import SpeechClientBridge
from tts_engine import generate_tts_and_encode
import asyncio
from bark.bark.generation import preload_models
import logging

app = FastAPI()
logger = logging.getLogger("uvicorn")
bark_ready = False 
@app.on_event("startup")
async def preload_bark():
    global bark_ready
    print("📦 Preloading Bark models...")
    preload_models()
    bark_ready = True
    print("✅ Bark models ready.")
    
templates = Jinja2Templates(directory="templates")

@app.post("/twiml")
async def return_twiml(request: Request):
    print(f"📞 Twilio hit /twiml endpoint! Request from: {request.client.host}")
    return templates.TemplateResponse("streams.xml", {"request": request})

from starlette.websockets import WebSocketState

async def on_transcription_response(response, websocket: WebSocket):
    if not response.results:
        return
    result = response.results[0]
    if not result.alternatives:
        return
    transcript = result.alternatives[0].transcript
    print("✅ Transcription:", transcript)

    # Generate TTS reply
    reply_ulaw = generate_tts_and_encode(f"You said: {transcript}")
    payload = base64.b64encode(reply_ulaw).decode("utf-8")

    # ✅ Only send if WebSocket is still connected
    if websocket.client_state == WebSocketState.CONNECTED:
        try:
            await websocket.send_text(json.dumps({
                "event": "media",
                "media": {
                    "payload": payload
                }
            }))
        except Exception as e:
            print(f"⚠️ WebSocket send failed: {e}")
    else:
        print("⚠️ Skipped sending: WebSocket already closed")

# async def on_transcription_response(response, websocket: WebSocket):
#     if not response.results:
#         return
#     result = response.results[0]
#     if not result.alternatives:
#         return
#     transcript = result.alternatives[0].transcript
#     print("✅ Transcription:", transcript)

#     # Generate TTS reply
#     reply_ulaw = generate_tts_and_encode(f"You said: {transcript}")
#     import base64
#     payload = base64.b64encode(reply_ulaw).decode("utf-8")

#     # Send back to Twilio
#     await websocket.send_text(json.dumps({
#         "event": "media",
#         "media": {
#             "payload": payload
#         }
#     }))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print(f"🟢 WebSocket connected from {websocket.client.host}")
    
    try:
        with open("beep.wav", "rb") as f:
            beep_bytes = f.read()
            beep_payload = base64.b64encode(beep_bytes).decode("utf-8")
            await websocket.send_text(json.dumps({
                "event": "media",
                "media": {
                    "payload": beep_payload
                }
            }))
        print("✅ Beep sent")
    except Exception as e:
        print(f"❌ Failed to send beep.wav: {e}")
        
    # 🔊 Send welcome message
    welcome_ulaw = generate_tts_and_encode("Hello! Start speaking after the beep.")
    welcome_payload = base64.b64encode(welcome_ulaw).decode("utf-8")
    print("Sending welcome audio payload to Twilio...")
    await websocket.send_text(json.dumps({
        "event": "media",
        "media": {
            "payload": welcome_payload
        }
    }))

    # 🔁 Setup transcription stream
    bridge = SpeechClientBridge(
        streaming_config=None,
        on_response=lambda r: asyncio.create_task(on_transcription_response(r, websocket))
    )

    try:
        while True:
            message = await websocket.receive_text()
            if not message:
                break
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                print("❌ Invalid JSON message:", message)
                continue

            event = data.get("event")
            if event in ("connected", "start"):
                print(f"🔔 Received event: {event}")
                continue

            if event == "media":
                media = data.get("media")
                if media and "payload" in media:
                    chunk = base64.b64decode(media["payload"])
                    bridge.add_request(chunk)
                else:
                    print("⚠️ Missing 'media' or 'payload' in message.")
            if event == "stop":
                print("🛑 Received 'stop' event.")
                break
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        bridge.terminate()
        print("🔴 WebSocket connection closed")


































