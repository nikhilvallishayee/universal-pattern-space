#!/usr/bin/env python3
"""
GödelOS Backend Startup Script

Initializes and starts the GödelOS FastAPI backend server with proper
configuration and error handling.
"""

import asyncio
import logging
import os
import sys
import signal
import argparse
from pathlib import Path

# Add parent directory to path for GödelOS imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

import uvicorn
from backend.main import app
# DEPRECATED: from backend.websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/godelos_backend.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)


class GödelOSServer:
    """GödelOS backend server manager."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
        """Initialize the server manager."""
        self.host = host
        self.port = port
        self.debug = debug
        self.server = None
        self.shutdown_event = asyncio.Event()
        
        # Ensure log directory exists
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
    
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def startup(self):
        """Start the server."""
        logger.info("Starting GödelOS Backend Server...")
        logger.info(f"Server will run on {self.host}:{self.port}")
        logger.info(f"Debug mode: {self.debug}")
        
        try:
            # Verify GödelOS components are available
            await self.verify_dependencies()
            
            # Configure uvicorn
            config = uvicorn.Config(
                app,
                host=self.host,
                port=self.port,
                log_level="debug" if self.debug else "info",
                reload=self.debug,
                access_log=True,
                server_header=False,
                date_header=False
            )
            
            self.server = uvicorn.Server(config)
            
            logger.info("GödelOS Backend Server started successfully")
            logger.info(f"API documentation available at: http://{self.host}:{self.port}/docs")
            logger.info(f"WebSocket endpoint: ws://{self.host}:{self.port}/ws/unified-cognitive-stream")
            
            # Start the server
            await self.server.serve()
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise
    
    async def verify_dependencies(self):
        """Verify that required dependencies are available."""
        logger.info("Verifying dependencies...")
        
        try:
            # Test GödelOS imports
            from godelOS.core_kr.type_system.manager import TypeSystemManager
            from godelOS.inference_engine.coordinator import InferenceCoordinator
            logger.info("✓ GödelOS core components available")
            
            # Test FastAPI
            from fastapi import FastAPI
            logger.info("✓ FastAPI available")
            
            # Test WebSocket support
            from fastapi import WebSocket
            logger.info("✓ WebSocket support available")
            
            # Test async support
            import asyncio
            logger.info("✓ Asyncio support available")
            
            logger.info("All dependencies verified successfully")
            
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            raise
    
    async def shutdown(self):
        """Gracefully shutdown the server."""
        logger.info("Shutting down GödelOS Backend Server...")
        
        if self.server:
            self.server.should_exit = True
        
        self.shutdown_event.set()
        logger.info("Server shutdown completed")
    
    async def run(self):
        """Run the server with proper error handling."""
        try:
            self.setup_signal_handlers()
            await self.startup()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            await self.shutdown()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="GödelOS Backend Server")
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with auto-reload"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    return parser.parse_args()


def setup_environment():
    """Set up the environment for the server."""
    # Set environment variables
    os.environ.setdefault("PYTHONPATH", str(Path(__file__).parent.parent))
    
    # Configure logging level
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    logging.getLogger().setLevel(getattr(logging, log_level))


async def main():
    """Main entry point."""
    args = parse_arguments()
    setup_environment()
    
    # Set logging level from arguments
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create and run server
    server = GödelOSServer(
        host=args.host,
        port=args.port,
        debug=args.debug
    )
    
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)