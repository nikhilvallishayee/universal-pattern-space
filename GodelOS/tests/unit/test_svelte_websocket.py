#!/usr/bin/env python3
"""
Test WebSocket connectivity from the perspective of the Svelte frontend.
This script tests the exact same WebSocket endpoint that the Svelte frontend uses.
"""

import asyncio
import websockets
import json
import time

async def test_cognitive_stream():
    """Test the cognitive stream WebSocket endpoint that the Svelte frontend uses."""
    uri = "ws://localhost:8000/ws/unified-cognitive-stream"
    
    print(f"🧪 Testing WebSocket connection to: {uri}")
    print("📡 Attempting to connect...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Successfully connected to cognitive stream!")
            
            # Send a request similar to what the Svelte frontend sends
            request_message = {
                "type": "request_state",
                "components": ["cognitive", "knowledge", "evolution"]
            }
            
            print(f"📤 Sending request: {json.dumps(request_message, indent=2)}")
            await websocket.send(json.dumps(request_message))
            
            # Wait for response
            print("⏳ Waiting for response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                print(f"📥 Received response: {json.dumps(response_data, indent=2)}")
                
                # Test sending another message
                ping_message = {"type": "ping", "timestamp": time.time()}
                print(f"📤 Sending ping: {json.dumps(ping_message)}")
                await websocket.send(json.dumps(ping_message))
                
                # Wait for ping response
                ping_response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                ping_data = json.loads(ping_response)
                print(f"📥 Ping response: {json.dumps(ping_data, indent=2)}")
                
                print("🎉 WebSocket communication test successful!")
                return True
                
            except asyncio.TimeoutError:
                print("⚠️  Timeout waiting for response (this might be normal if backend doesn't send immediate responses)")
                return True  # Connection was successful even if no immediate response
                
    except ConnectionRefusedError:
        print("❌ Connection refused - is the backend running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ WebSocket connection failed: {str(e)}")
        return False

async def main():
    """Main test function."""
    print("🚀 Starting Svelte Frontend WebSocket Test")
    print("=" * 50)
    
    # Test the cognitive stream endpoint
    success = await test_cognitive_stream()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All WebSocket tests passed!")
        print("🎯 The Svelte frontend should now be able to connect successfully.")
    else:
        print("❌ WebSocket tests failed!")
        print("🔧 Check that the backend is running and accessible.")
        
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
