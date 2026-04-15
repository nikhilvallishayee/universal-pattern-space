#!/usr/bin/env python3
"""
Test the complete import flow including WebSocket events
"""

import asyncio
import aiohttp
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_flow():
    """Test the complete import flow with WebSocket monitoring."""
    
    # WebSocket connection for monitoring events
    websocket_uri = "ws://localhost:8000/ws/unified-cognitive-stream"
    api_base = "http://localhost:8000"
    
    print("🧪 Testing Complete Import Flow with WebSocket Monitoring")
    print("=" * 60)
    
    try:
        # Connect to WebSocket
        print("\n1. Connecting to WebSocket...")
        websocket = await websockets.connect(websocket_uri)
        print("✅ WebSocket connected successfully")
        
        # Set up WebSocket event listener
        async def listen_for_events():
            events_received = []
            try:
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        event_type = data.get('type', 'unknown')
                        timestamp = data.get('timestamp', 0)
                        
                        if event_type in ['import_started', 'import_progress', 'import_completed', 'import_failed']:
                            events_received.append(data)
                            print(f"📨 WebSocket Event: {event_type}")
                            if 'import_id' in data:
                                print(f"   Import ID: {data['import_id']}")
                            if 'progress' in data:
                                print(f"   Progress: {data['progress']}%")
                            if 'message' in data:
                                print(f"   Message: {data['message']}")
                            if 'status' in data:
                                print(f"   Status: {data['status']}")
                            print()
                            
                    except json.JSONDecodeError:
                        continue
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed")
            return events_received
        
        # Start listening for events
        event_listener_task = asyncio.create_task(listen_for_events())
        
        # Give a moment for WebSocket to settle
        await asyncio.sleep(1)
        
        # Test text import
        print("2. Testing Text Import...")
        
        async with aiohttp.ClientSession() as session:
            text_data = {
                "source": {
                    "source_type": "text",
                    "source_identifier": "Test Import Flow",
                    "metadata": {"source": "flow_test"}
                },
                "content": "This is a comprehensive test of the import flow including WebSocket events.",
                "title": "Test Import Flow",
                "format_type": "plain",
                "categorization_hints": ["test", "flow", "websocket"]
            }
            
            async with session.post(f"{api_base}/api/knowledge/import/text", 
                                  json=text_data) as response:
                result = await response.json()
                
                if response.status == 200:
                    import_id = result.get('import_id')
                    print(f"✅ Text import initiated successfully: {import_id}")
                    
                    # Wait for events to be processed
                    print("⏳ Waiting for import to complete...")
                    await asyncio.sleep(5)  # Give time for processing
                    
                else:
                    print(f"❌ Text import failed: {response.status} - {result}")
        
        # Cancel the event listener
        event_listener_task.cancel()
        
        try:
            events = await event_listener_task
        except asyncio.CancelledError:
            events = []
        
        # Close WebSocket
        await websocket.close()
        
        # Analyze results
        print("\n3. Event Flow Analysis:")
        print("=" * 30)
        
        event_types = [event.get('type') for event in events]
        expected_events = ['import_started', 'import_progress', 'import_completed']
        
        print(f"Events received: {len(events)}")
        print(f"Event types: {event_types}")
        
        for expected in expected_events:
            if expected in event_types:
                print(f"✅ {expected} event received")
            else:
                print(f"❌ {expected} event missing")
        
        if len(events) >= 3 and 'import_completed' in event_types:
            print("🎉 Complete flow test PASSED!")
        else:
            print("⚠️  Complete flow test needs attention")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_flow())