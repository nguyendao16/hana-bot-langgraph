import asyncio
import websockets
import json
import logging
from kittentts import KittenTTS
import soundfile as sf
import io
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize TTS model
m = KittenTTS("KittenML/kitten-tts-nano-0.2")

# Fixed voice - always use expr-voice-5-f
DEFAULT_VOICE = 'expr-voice-5-f'

async def handle_client(websocket):
    """Handle incoming WebSocket connections from chatbot client"""
    client_id = id(websocket)
    logger.info(f"Client {client_id} connected from {websocket.remote_address}")
    
    try:
        # Send connection confirmation
        await websocket.send(json.dumps({
            "type": "connection",
            "message": "Connected to TTS server",
            "voice": DEFAULT_VOICE
        }))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from client {client_id}: {data}")
                
                if data.get("type") == "tts_request":
                    text = data.get("text", "")
                    # Always use default voice, ignore voice parameter from client
                    voice = DEFAULT_VOICE
                    
                    if not text:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "No text provided"
                        }))
                        continue
                    
                    logger.info(f"Generating TTS for: '{text}' with voice: {voice}")
                    
                    try:
                        # Generate audio
                        audio = m.generate(text, voice=voice)
                        
                        # Convert audio to bytes
                        buffer = io.BytesIO()
                        sf.write(buffer, audio, 24000, format='WAV')
                        audio_bytes = buffer.getvalue()
                        
                        # Encode to base64 for transmission
                        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                        
                        # Send audio data back to client
                        await websocket.send(json.dumps({
                            "type": "audio_ready",
                            "text": text,
                            "voice": voice,
                            "audio": audio_base64,
                            "format": "wav",
                            "sample_rate": 24000
                        }))
                        
                        logger.info(f"Audio sent to client {client_id}")
                        
                    except Exception as e:
                        logger.error(f"Error generating TTS: {e}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": f"TTS generation failed: {str(e)}"
                        }))
                        
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")

async def main():
    """Start the TTS WebSocket server"""
    host = "localhost"
    port = 8766
    
    logger.info(f"Starting TTS WebSocket server on ws://{host}:{port}")
    
    # Tăng max_size lên 10MB để xử lý audio lớn
    async with websockets.serve(handle_client, host, port, max_size=1024 * 1024 * 1024):
        logger.info("TTS Server is running. Press Ctrl+C to stop.")
        logger.info("WebSocket max message size: 10MB")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
