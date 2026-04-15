# GödelOS Backend API

FastAPI backend that interfaces with the GödelOS system to provide a web demonstration interface with natural language query processing, knowledge base management, and real-time cognitive state monitoring.

## Features

- **Natural Language Query Processing**: Process user queries through the GödelOS NLU/NLG pipeline
- **Knowledge Base Management**: Add, retrieve, and manage knowledge in the GödelOS system
- **Real-time Cognitive Monitoring**: Stream cognitive events and system state via WebSocket
- **RESTful API**: Clean, documented API endpoints with automatic OpenAPI documentation
- **WebSocket Support**: Real-time bidirectional communication for cognitive events
- **Health Monitoring**: System health checks and performance metrics
- **CORS Support**: Configured for frontend integration

## Quick Start

### Prerequisites

- Python 3.8+
- GödelOS system (parent directory)
- Required Python packages (see requirements.txt)

### Installation

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Start the server:
```bash
python start_server.py
```

Or for development with auto-reload:
```bash
python start_server.py --debug
```

### Alternative startup methods:

Using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Using the FastAPI app directly:
```bash
python -m backend.main
```

## API Endpoints

### Core Endpoints

- `GET /` - Root endpoint with basic info
- `GET /health` - Health check and system status
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

### Query Processing

- `POST /api/query` - Process natural language queries
  ```json
  {
    "query": "Where is John?",
    "context": {},
    "include_reasoning": false
  }
  ```

### Knowledge Management

- `GET /api/knowledge` - Retrieve knowledge base information
  - Query parameters: `context_id`, `knowledge_type`, `limit`
- `POST /api/knowledge` - Add new knowledge to the system
  ```json
  {
    "content": "John is a person",
    "knowledge_type": "fact",
    "context_id": "FACTS",
    "metadata": {}
  }
  ```

### Cognitive State

- `GET /api/cognitive-state` - Get current cognitive layer states
  - Returns manifest consciousness, agentic processes, daemon threads, working memory, attention focus, and metacognitive state

### WebSocket

- `WS /ws/cognitive-stream` - Real-time cognitive event stream
  - Supports event subscriptions and broadcasts

## Configuration

The backend can be configured via environment variables or a `.env` file:

```bash
# Server configuration
GODELOS_HOST=0.0.0.0
GODELOS_PORT=8000
GODELOS_DEBUG=false

# CORS configuration
GODELOS_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Logging
GODELOS_LOG_LEVEL=INFO
GODELOS_LOG_FILE=backend/logs/godelos_backend.log

# Performance
GODELOS_MAX_CONCURRENT_QUERIES=10
GODELOS_CACHE_SIZE=100
GODELOS_CACHE_TTL=300

# WebSocket
GODELOS_WS_PING_INTERVAL=30
GODELOS_WS_MAX_CONNECTIONS=100
```

## Architecture

### Components

1. **FastAPI Application** (`main.py`) - Core API server with endpoint definitions
2. **GödelOS Integration** (`godelos_integration.py`) - Adapter layer connecting to GödelOS modules
3. **WebSocket Manager** (`websocket_manager.py`) - Real-time event broadcasting
4. **Data Models** (`models.py`) - Pydantic models for request/response validation
5. **Configuration** (`config.py`) - Environment-based configuration management

### Integration with GödelOS

The backend integrates with these GödelOS components:

- **Core KR System**: Type system, knowledge store, formal logic parser
- **Inference Engine**: Resolution prover, inference coordinator
- **NLU/NLG Pipelines**: Natural language understanding and generation
- **Metacognition System**: Self-monitoring and meta-knowledge
- **Unified Agent Core**: Cognitive state management

### Data Flow

1. **Query Processing**:
   - Receive natural language query via REST API
   - Parse query using NLU pipeline (or fallback pattern matching)
   - Convert to formal logic representation
   - Submit to inference engine
   - Generate natural language response via NLG pipeline
   - Return structured response with reasoning steps

2. **Knowledge Management**:
   - Accept knowledge in natural language or formal representation
   - Parse and validate knowledge content
   - Store in appropriate knowledge base context
   - Broadcast knowledge updates via WebSocket

3. **Cognitive Monitoring**:
   - Continuously monitor cognitive system state
   - Track active processes, working memory, attention
   - Stream real-time events to connected WebSocket clients
   - Provide snapshots via REST API

## Testing

Run the test suite:
```bash
pytest backend/test_api.py -v
```

Run integration test:
```bash
python backend/test_api.py
```

## Development

### Project Structure
```
backend/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application
├── models.py                # Pydantic data models
├── godelos_integration.py   # GödelOS system integration
├── websocket_manager.py     # WebSocket event management
├── config.py                # Configuration management
├── start_server.py          # Server startup script
├── test_api.py              # Test suite
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── logs/                    # Log files directory
```

### Adding New Endpoints

1. Define request/response models in `models.py`
2. Add endpoint handler in `main.py`
3. Implement business logic in `godelos_integration.py`
4. Add tests in `test_api.py`
5. Update documentation

### WebSocket Events

The system broadcasts these event types:

- `connection_established` - New client connected
- `query_processed` - Natural language query completed
- `knowledge_added` - New knowledge added to system
- `cognitive_event` - General cognitive system events
- `system_status` - System health/status updates
- `inference_progress` - Real-time inference progress

## Deployment

### Development
```bash
python start_server.py --debug --log-level DEBUG
```

### Production
```bash
# Set environment
export GODELOS_ENVIRONMENT=production
export GODELOS_API_KEY=your-secure-api-key

# Start server
python start_server.py --host 0.0.0.0 --port 8000
```

### Docker (Future)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "start_server.py"]
```

## Monitoring

- Health endpoint: `GET /health`
- Logs: `backend/logs/godelos_backend.log`
- WebSocket connection stats via WebSocket manager
- System metrics via cognitive state endpoint

## Troubleshooting

### Common Issues

1. **GödelOS initialization fails**
   - Check that all GödelOS dependencies are installed
   - Verify Python path includes parent directory
   - Check logs for specific import errors

2. **WebSocket connections fail**
   - Verify CORS configuration
   - Check firewall/proxy settings
   - Ensure WebSocket support in client

3. **Query processing errors**
   - Check NLU/NLG pipeline initialization
   - Verify knowledge base is populated
   - Review inference engine logs

### Debug Mode

Enable debug mode for detailed logging:
```bash
python start_server.py --debug --log-level DEBUG
```

## API Documentation

When the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## License

Part of the GödelOS project. See main project license.