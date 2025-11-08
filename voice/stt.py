import asyncio
import websockets
import json
from RealtimeSTT import AudioToTextRecorder
from threading import Thread, Event
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class STTServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.recorder = None
        self.clients = set()
        self.recording_event = Event()
        
    def initialize_recorder(self):
        """Initialize the STT recorder"""
        logger.info("Initializing STT recorder...")
        
        self.recorder = AudioToTextRecorder(
            model="medium.en"
        )
        logger.info("STT recorder initialized successfully")
        
    def start_recording_thread(self):
        """Run recorder in a separate thread"""
        def recording_loop():
            logger.info("=== STT Server Ready ===")
            logger.info("Press Enter to start recording, then speak your message.")
            
            while True:
                try:
                    input("\n>>> Press Enter to start recording... ")
                    logger.info("Recording... Speak now!")
                    self.recorder.start()
                    input(">>> Press Enter to stop recording... ")
                    
                    logger.info("Stopping recording...")
                    self.recorder.stop()
                    text = self.recorder.text()
                    
                    if text and text.strip():
                        logger.info(f"Transcription: {text}")
                        asyncio.run(self.broadcast_message(text))
                    else:
                        logger.info("No speech detected")
                        
                except KeyboardInterrupt:
                    logger.info("\nRecording stopped by user")
                    break
                except Exception as e:
                    logger.error(f"Error in recording loop: {e}")
                    
        thread = Thread(target=recording_loop, daemon=True)
        thread.start()
        logger.info("Recording thread started")
        
    async def broadcast_message(self, text):
        """Send message to all connected clients"""
        if self.clients:
            message = json.dumps({"type": "transcription", "text": text})
            disconnected_clients = set()
            
            for client in self.clients.copy():
                try:
                    await client.send(message)
                    logger.info(f"Sent to client: {text}")
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)
                    logger.info("Client disconnected during broadcast")
                except Exception as e:
                    logger.error(f"Error sending to client: {e}")
                    disconnected_clients.add(client)
            
            self.clients -= disconnected_clients
                    
    async def handle_client(self, websocket):
        """Handle individual client connections"""
        client_id = id(websocket)
        logger.info(f"New client connected: {client_id}")
        self.clients.add(websocket)
        
        try:
            await websocket.send(json.dumps({
                "type": "connection", 
                "status": "connected",
                "message": "Connected to STT server"
            }))
            
            # Keep connection alive and handle any incoming messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"Received from client {client_id}: {data}")
                    
                    # Handle client commands if needed
                    if data.get("type") == "ping":
                        await websocket.send(json.dumps({"type": "pong"}))
                        
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from client {client_id}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            self.clients.discard(websocket)
            logger.info(f"Client {client_id} removed from active clients")
            
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info(f"STT WebSocket server is running on ws://{self.host}:{self.port}")
            logger.info("Waiting for clients to connect...")
            await asyncio.Future()
            
    def run(self):
        """Main entry point to run the server"""
        self.initialize_recorder()
        self.start_recording_thread()
        asyncio.run(self.start_server())

if __name__ == '__main__':
    logger.info("STT Server - Manual Input Mode")
    logger.info("You will need to press Enter to start/stop recording")
    
    server = STTServer(host="localhost", port=8765)
    server.run()