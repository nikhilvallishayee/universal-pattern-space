#!/usr/bin/env python3
"""
Test Wikipedia import flow specifically
"""

import asyncio
import aiohttp
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_wikipedia_flow():
    """Test the Wikipedia import flow with detailed monitoring."""
    
    websocket_uri = "ws://localhost:8000/ws/unified-cognitive-stream"
    api_base = "http://localhost:8000"
    
    print("🧪 Testing Wikipedia Import Flow")
    print("=" * 40)
    
    events_received = []
    
    try:
        # Connect to WebSocket
        print("\n1. Connecting to WebSocket...")
        websocket = await websockets.connect(websocket_uri)
        print("✅ WebSocket connected successfully")
        
        # Set up WebSocket event listener
        async def listen_for_events():
            try:
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        event_type = data.get('type', 'unknown')
                        
                        if event_type in ['import_started', 'import_progress', 'import_completed', 'import_failed']:
                            events_received.append(data)
                            print(f"📨 {event_type}: {data.get('message', 'No message')}")
                            if 'progress' in data:
                                print(f"   Progress: {data['progress']}%")
                            print()
                            
                    except json.JSONDecodeError:
                        continue
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed")
        
        # Start listening for events
        event_listener_task = asyncio.create_task(listen_for_events())
        
        # Give a moment for WebSocket to settle
        await asyncio.sleep(1)
        
        # Test Wikipedia import
        print("2. Submitting Wikipedia import request...")
        
        async with aiohttp.ClientSession() as session:
            wikipedia_data = {
                "source": {
                    "source_type": "wikipedia",
                    "source_identifier": "Artificial Intelligence",
                    "metadata": {"source": "test_flow"}
                },
                "page_title": "Artificial Intelligence",
                "language": "en",
                "include_references": True,
                "section_filter": []
            }
            
            print(f"📤 Sending request: {json.dumps(wikipedia_data, indent=2)}")
            
            async with session.post(f"{api_base}/api/knowledge/import/wikipedia", 
                                  json=wikipedia_data) as response:
                result = await response.json()
                
                print(f"📥 Response status: {response.status}")
                print(f"📥 Response body: {json.dumps(result, indent=2)}")
                
                if response.status == 200:
                    import_id = result.get('import_id')
                    print(f"✅ Wikipedia import initiated: {import_id}")
                    
                    # Wait for events to be processed
                    print("⏳ Waiting for import to complete...")
                    await asyncio.sleep(8)  # Give more time for processing
                    
                else:
                    print(f"❌ Wikipedia import failed: {response.status} - {result}")
                    return
        
        # Cancel the event listener
        event_listener_task.cancel()
        
        try:
            await event_listener_task
        except asyncio.CancelledError:
            pass
        
        # Close WebSocket
        await websocket.close()
        
        # Analyze results
        print("\n3. Event Flow Analysis:")
        print("=" * 30)
        
        print(f"Total events received: {len(events_received)}")
        
        for i, event in enumerate(events_received):
            print(f"Event {i+1}: {event.get('type')} - {event.get('message')} - Progress: {event.get('progress', 'N/A')}%")
        
        # Check for expected flow
        event_types = [event.get('type') for event in events_received]
        
        if 'import_started' in event_types:
            print("✅ import_started event received")
        else:
            print("❌ import_started event missing")
            
        if 'import_progress' in event_types:
            print("✅ import_progress events received")
        else:
            print("❌ import_progress events missing")
            
        if 'import_completed' in event_types:
            print("✅ import_completed event received")
        elif 'import_failed' in event_types:
            print("⚠️  import_failed event received")
        else:
            print("❌ No completion event received")
        
        if len(events_received) >= 3 and ('import_completed' in event_types or 'import_failed' in event_types):
            print("🎉 Wikipedia import flow test PASSED!")
        else:
            print("⚠️  Wikipedia import flow test needs attention")
            print("Expected: import_started → import_progress → import_completed")
            print(f"Received: {' → '.join(event_types)}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_wikipedia_flow())