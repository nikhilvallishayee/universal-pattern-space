#!/usr/bin/env python3
"""
Test and restart backend script
"""

import subprocess
import time
import requests
import sys
import os

def kill_existing_servers():
    """Kill any existing uvicorn processes."""
    try:
        subprocess.run(["pkill", "-f", "uvicorn"], check=False)
        print("✅ Killed existing servers")
        time.sleep(2)
    except Exception as e:
        print(f"Warning: Could not kill servers: {e}")

def start_backend():
    """Start the backend server."""
    try:
        # Change to project directory
        os.chdir("/Users/oli/code/GödelOS.md")
        
        # Start the backend
        print("🚀 Starting backend server...")
        process = subprocess.Popen([
            "uvicorn", "backend.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(5)
        
        return process
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return None

def test_endpoints():
    """Test the key endpoints."""
    endpoints = [
        "/api/health",
        "/api/knowledge/evolution", 
        "/api/knowledge/graph",
        "/api/capabilities"
    ]
    
    base_url = "http://localhost:8000"
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"🔍 Testing {endpoint}...")
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint} - Status: {response.status_code}")
                # Print first 200 chars of response for debugging
                content = response.text[:200]
                print(f"   Response preview: {content}...")
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Connection error: {e}")
        except Exception as e:
            print(f"❌ {endpoint} - Unexpected error: {e}")

def main():
    print("🔧 GödelOS Backend Test & Restart Script")
    print("=" * 50)
    
    # Kill existing servers
    kill_existing_servers()
    
    # Start backend
    process = start_backend()
    if not process:
        print("❌ Failed to start backend")
        sys.exit(1)
    
    try:
        # Test endpoints
        test_endpoints()
        
        print("\n✅ Backend testing complete!")
        print("🏃 Backend is running in the background...")
        print("💡 Use Ctrl+C to stop this script (backend will continue running)")
        
        # Keep the script running so the subprocess doesn't terminate
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n🛑 Script interrupted")
        print("🔧 Backend server will continue running in background")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        if process:
            process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()
