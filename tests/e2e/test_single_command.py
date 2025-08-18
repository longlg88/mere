#!/usr/bin/env python3
"""
Single command test for debugging
"""
import asyncio
import websockets
import json
import logging
from datetime import datetime

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

WEBSOCKET_URL = "ws://localhost:8000/ws/debug-test-user"

async def test_create_memo():
    """Test single create_memo command with detailed logging"""
    try:
        # Connect to WebSocket
        websocket = await websockets.connect(WEBSOCKET_URL)
        
        # Wait for connection ACK
        response = await websocket.recv()
        data = json.loads(response)
        print(f"Connection: {data}")
        
        # Send create memo command
        command = {
            "type": "text_command",
            "text": "우유 사는 거 기억해줘",
            "timestamp": datetime.now().isoformat(),
            "user_id": "debug-test-user"
        }
        
        print(f"Sending: {json.dumps(command, ensure_ascii=False)}")
        await websocket.send(json.dumps(command))
        
        # Get processing status
        processing = await websocket.recv()
        print(f"Processing: {json.loads(processing)}")
        
        # Get final response
        response = await websocket.recv()
        response_data = json.loads(response)
        print(f"Response: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        await websocket.close()
        
    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Test failed")

if __name__ == "__main__":
    asyncio.run(test_create_memo())