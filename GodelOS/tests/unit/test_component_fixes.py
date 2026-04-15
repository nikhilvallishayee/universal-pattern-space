#!/usr/bin/env python3
"""
Test script to validate that our component initialization fixes are working.
"""

import sys
import os
import asyncio
import traceback
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_component_initialization():
    """Test that all components initialize correctly."""
    print("🔍 Testing GödelOS Component Initialization Fixes...")
    print("=" * 60)
    
    try:
        # Import the integration module
        print("📦 Importing GödelOS integration...")
        from backend.godelos_integration import GödelOSIntegration
        print("✅ Import successful")
        
        # Create integration instance
        print("🏗️  Creating integration instance...")
        integration = GödelOSIntegration()
        print("✅ Instance created")
        
        # Initialize all components
        print("🚀 Initializing all components...")
        await integration.initialize()
        print("✅ All components initialized successfully!")
        
        # Check health status
        print("🏥 Checking health status...")
        health = await integration.get_health_status()
        
        print("\n📊 HEALTH STATUS REPORT:")
        print(f"   Overall Healthy: {health['healthy']}")
        print(f"   Initialized: {health['initialized']}")
        print(f"   Essential Components Ready: {health['essential_components_ready']}")
        print(f"   All Components Ready: {health['all_components_ready']}")
        print(f"   Error Count: {health['error_count']}")
        
        print("\n🔧 COMPONENT STATUS:")
        for component, status in health['components'].items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {component}: {status}")
        
        # Test a simple query to verify functionality
        print("\n🧠 Testing natural language processing...")
        query_result = await integration.process_natural_language_query(
            "Where is John?", 
            include_reasoning=False
        )
        print(f"   Query Response: {query_result['response']}")
        print(f"   Confidence: {query_result['confidence']}")
        
        # Shutdown
        print("\n🛑 Shutting down integration...")
        await integration.shutdown()
        print("✅ Shutdown complete")
        
        # Final assessment
        print("\n" + "=" * 60)
        if health['healthy'] and health['essential_components_ready']:
            print("🎉 SUCCESS: All component initialization fixes are working!")
            print("   The backend should now report healthy status to the frontend.")
            return True
        else:
            print("⚠️  PARTIAL SUCCESS: Components initialized but some issues remain.")
            failed_components = [name for name, status in health['components'].items() if not status]
            if failed_components:
                print(f"   Failed components: {failed_components}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_component_initialization())
    
    if success:
        print("\n✅ CONCLUSION: The backend component initialization fixes are working correctly!")
        print("   The 'essential_components_ready: false' issue should now be resolved.")
        sys.exit(0)
    else:
        print("\n❌ CONCLUSION: There are still issues that need to be addressed.")
        sys.exit(1)
