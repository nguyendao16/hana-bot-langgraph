import uvicorn
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from os import getenv
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from agent.agent import create_graph
from agent.utils.memory import RedisSaver
from agent.utils.pgconpool import Postgres
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, Response
from typing import Optional, Dict
import json
import asyncio
import websockets
import logging
import base64
import io
import sounddevice as sd
import soundfile as sf
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
PG_HOST=getenv("PG_HOST")
PG_DBNAME=getenv("PG_DBNAME")
PG_USER=getenv("PG_USER")
PG_PASSWORD=getenv("PG_PASSWORD")

# WebSocket client configuration
STT_SERVER_URL = getenv("STT_SERVER_URL", "ws://localhost:8765")
TTS_SERVER_URL = getenv("TTS_SERVER_URL", "ws://localhost:8766")  # TTS WebSocket server
DEFAULT_THREAD_ID = getenv("DEFAULT_THREAD_ID", "voice-session-001")

@asynccontextmanager
async def lifespan(app: FastAPI):
    RedisSaver.initialize_pool(url = getenv("REDIS_URL"))
    redis_client = RedisSaver()
    await Postgres.initialize_pool(host=PG_HOST, 
                                    database=PG_DBNAME,
                                    user=PG_USER, 
                                    password=PG_PASSWORD)
    postgres_client = Postgres()
    graph = await create_graph(redis_client, postgres_client)
    app.state.graph = graph
    app.state.redis = redis_client
    app.state.postgres = postgres_client
    
    # WebSocket connections storage
    app.state.tts_websocket = None
    app.state.websocket_lock = asyncio.Lock()
    
    # Start WebSocket client connections
    app.state.stt_task = asyncio.create_task(connect_to_stt_server(app))
    app.state.tts_task = asyncio.create_task(connect_to_tts_server(app))
    
    yield
    
    # Cleanup
    if hasattr(app.state, 'stt_task'):
        app.state.stt_task.cancel()
        try:
            await app.state.stt_task
        except asyncio.CancelledError:
            pass
    
    if hasattr(app.state, 'tts_task'):
        app.state.tts_task.cancel()
        try:
            await app.state.tts_task
        except asyncio.CancelledError:
            pass
    
    await RedisSaver.close_pool()
    await app.state.postgres.close_pool()

app = FastAPI(lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Chatbot(BaseModel):
    message: str
    thread_id: str

async def process_chatbot_message(message: str, thread_id: str):
    """Process message through chatbot and return response"""
    graph_input = {
        "messages": [HumanMessage(content=message)],
        "thread_id": thread_id,
    }
    
    logger.info(f"Processing message for thread {thread_id}: {message}")
    
    try:
        agen = app.state.graph.astream(graph_input)
        response_text = ""
        
        async for chunk in agen:
            print(chunk)
            if isinstance(chunk, dict):
                node_output = chunk.get("write_memory") 
                if node_output and isinstance(node_output, dict):
                    bot_message_content = node_output.get("bot_message")
                    
                    if bot_message_content and isinstance(bot_message_content, str):
                        response_text = bot_message_content
                        logger.info(f"Bot response: {response_text}")
        
        return response_text
    except Exception as e:
        logger.error(f"Error processing chatbot message: {e}")
        return f"Error: {str(e)}"

async def send_to_tts(text: str):
    """Send text to TTS server via WebSocket"""
    try:
        async with app.state.websocket_lock:
            if app.state.tts_websocket:
                try:
                    message = json.dumps({
                        "type": "tts_request",
                        "text": text
                    })
                    await app.state.tts_websocket.send(message)
                    logger.info(f"Sent to TTS server: {text}")
                    return True
                except Exception as send_error:
                    logger.warning(f"Failed to send to TTS: {send_error}")
                    app.state.tts_websocket = None
                    return False
            else:
                logger.warning("TTS WebSocket is not connected")
                return False
    except Exception as e:
        logger.error(f"Error sending to TTS: {e}")
        return False

async def connect_to_tts_server(app_instance):
    """Connect to TTS WebSocket server and maintain connection"""
    retry_delay = 5
    max_retry_delay = 30
    consecutive_failures = 0
    
    while True:
        try:
            logger.info(f"Connecting to TTS server at {TTS_SERVER_URL}...")
            # Tăng max_size lên 10MB để nhận audio lớn
            async with websockets.connect(TTS_SERVER_URL, max_size=1024 * 1024 * 1024) as websocket:
                logger.info("Connected to TTS server successfully!")
                consecutive_failures = 0
                
                # Store websocket connection
                async with app_instance.state.websocket_lock:
                    app_instance.state.tts_websocket = websocket
                
                # Keep connection alive and handle incoming messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        logger.info(f"Received from TTS server: {data.get('type')}")
                        
                        # Xử lý các message từ TTS server
                        if data.get("type") == "audio_ready":
                            logger.info("Audio is ready, playing...")
                            # Decode base64 audio
                            audio_base64 = data.get("audio")
                            if audio_base64:
                                try:
                                    # Decode base64 to bytes
                                    audio_bytes = base64.b64decode(audio_base64)
                                    
                                    # Read audio from bytes
                                    audio_buffer = io.BytesIO(audio_bytes)
                                    audio_data, sample_rate = sf.read(audio_buffer)
                                    
                                    # Play audio
                                    logger.info(f"Playing audio: {len(audio_data)} samples at {sample_rate}Hz")
                                    sd.play(audio_data, sample_rate)
                                    sd.wait()  # Wait until audio finishes playing
                                    logger.info("Audio playback completed")
                                except Exception as audio_error:
                                    logger.error(f"Error playing audio: {audio_error}")
                        elif data.get("type") == "error":
                            logger.error(f"TTS error: {data.get('message')}")
                            
                    except json.JSONDecodeError:
                        logger.error("Failed to decode message from TTS server")
                    except Exception as e:
                        logger.error(f"Error processing TTS message: {e}")
                        
        except websockets.exceptions.ConnectionClosed as e:
            async with app_instance.state.websocket_lock:
                app_instance.state.tts_websocket = None
            consecutive_failures += 1
            current_delay = min(retry_delay * consecutive_failures, max_retry_delay)
            logger.warning(f"TTS server connection closed: {e}. Retry {consecutive_failures}, waiting {current_delay}s...")
            await asyncio.sleep(current_delay)
        except ConnectionRefusedError:
            async with app_instance.state.websocket_lock:
                app_instance.state.tts_websocket = None
            consecutive_failures += 1
            current_delay = min(retry_delay * consecutive_failures, max_retry_delay)
            logger.error(f"TTS server refused connection. Is the server running? Retry {consecutive_failures}, waiting {current_delay}s...")
            await asyncio.sleep(current_delay)
        except Exception as e:
            async with app_instance.state.websocket_lock:
                app_instance.state.tts_websocket = None
            consecutive_failures += 1
            current_delay = min(retry_delay * consecutive_failures, max_retry_delay)
            logger.error(f"Error connecting to TTS server: {e}. Retry {consecutive_failures}, waiting {current_delay}s...")
            await asyncio.sleep(current_delay)

async def connect_to_stt_server(app_instance):
    """Connect to STT WebSocket server and handle incoming transcriptions"""
    retry_delay = 5
    max_retry_delay = 30
    consecutive_failures = 0
    
    while True:
        try:
            logger.info(f"Connecting to STT server at {STT_SERVER_URL}...")
            async with websockets.connect(STT_SERVER_URL, max_size=1024 * 1024 * 1024) as websocket:
                logger.info("Connected to STT server successfully!")
                consecutive_failures = 0
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        logger.info(f"Received from STT server: {data}")
                        
                        if data.get("type") == "transcription":
                            text = data.get("text", "")
                            if text:
                                # Process through chatbot
                                response = await process_chatbot_message(
                                    text, 
                                    DEFAULT_THREAD_ID
                                )
                                logger.info(f"Chatbot response: {response}")
                                
                                # Send response to TTS server
                                if response:
                                    await send_to_tts(response)
                                
                        elif data.get("type") == "connection":
                            logger.info(f"Connection status: {data.get('message')}")
                            
                    except json.JSONDecodeError:
                        logger.error("Failed to decode message from STT server")
                    except Exception as e:
                        logger.error(f"Error processing STT message: {e}")
                        
        except websockets.exceptions.ConnectionClosed as e:
            consecutive_failures += 1
            current_delay = min(retry_delay * consecutive_failures, max_retry_delay)
            logger.warning(f"STT server connection closed: {e}. Retry {consecutive_failures}, waiting {current_delay}s...")
            await asyncio.sleep(current_delay)
        except ConnectionRefusedError:
            consecutive_failures += 1
            current_delay = min(retry_delay * consecutive_failures, max_retry_delay)
            logger.error(f"STT server refused connection. Is the server running? Retry {consecutive_failures}, waiting {current_delay}s...")
            await asyncio.sleep(current_delay)
        except Exception as e:
            consecutive_failures += 1
            current_delay = min(retry_delay * consecutive_failures, max_retry_delay)
            logger.error(f"Error connecting to STT server: {e}. Retry {consecutive_failures}, waiting {current_delay}s...")
            await asyncio.sleep(current_delay)

@app.post("/chat")
async def chat_endpoint(request: Chatbot):
    thread_id = request.threadID
    redis_client = app.state.redis
    
    graph_input = {
        "messages": [HumanMessage(content=request.message)],
        "thread_id": thread_id,
    }

    async def stream_answer():
        agen = app.state.graph.astream(graph_input)
        try:
            async for chunk in agen:
                print(chunk)
                if isinstance(chunk, dict):
                    node_output = chunk.get("write_memory") 
                    if node_output and isinstance(node_output, dict):
                        bot_message_content = node_output.get("bot_message")
                        
                        if bot_message_content and isinstance(bot_message_content, str):
                            yield json.dumps({"answer": bot_message_content}, ensure_ascii=False)

        except Exception as e:
            print(f"An error occurred during streaming for {thread_id}: {e}")
    
    return StreamingResponse(stream_answer(), media_type="text/plain")


# Run the server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8200)