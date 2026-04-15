#!/usr/bin/env python3
"""
Quick WebSocket connection test for the GödelOS backend
"""
import asyncio
import json
import websockets

async def test_websocket():
    try:
        print('Attempting to connect to ws://localhost:8000/ws/unified-cognitive-stream...')
        async with websockets.connect('ws://localhost:8000/ws/unified-cognitive-stream') as websocket:
            print('✅ WebSocket connected successfully!')
            
            # Send a ping
            await websocket.send(json.dumps({'type': 'ping'}))
            print('📤 Sent ping')
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f'📨 Received: {response}')
            
    except Exception as e:
        print(f'❌ WebSocket connection failed: {e}')
        print(f'Error type: {type(e).__name__}')

if __name__ == '__main__':
    asyncio.run(test_websocket())
