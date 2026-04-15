"""
Test Fixtures for GödelOS Testing

Common test fixtures and data for consistent testing across all test suites.
"""

import json
import pytest
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock

# Import test data models
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.models import (
    QueryRequest, QueryResponse, KnowledgeRequest, KnowledgeResponse,
    CognitiveStateResponse, ReasoningStep
)
from backend.knowledge_models import KnowledgeItem, ImportSource


# Common Test Data
SAMPLE_QUERIES = [
    "What is artificial intelligence?",
    "How do neural networks work?",
    "Explain machine learning algorithms",
    "What is the difference between AI and ML?",
    "How does natural language processing work?"
]

SAMPLE_KNOWLEDGE_ITEMS = [
    {
        "concept": "Machine Learning",
        "definition": "A subset of AI that enables computers to learn without explicit programming",
        "category": "technology"
    },
    {
        "concept": "Neural Network",
        "definition": "A computing system inspired by biological neural networks",
        "category": "ai"
    },
    {
        "concept": "Deep Learning",
        "definition": "A subset of machine learning based on artificial neural networks",
        "category": "ai"
    }
]

SAMPLE_COGNITIVE_STATE = {
    "manifest_consciousness": {
        "current_focus": "Processing user query",
        "awareness_level": 0.85,
        "coherence_level": 0.90,
        "integration_level": 0.80,
        "phenomenal_content": ["Query analysis", "Knowledge retrieval"],
        "access_consciousness": {"active_query": "What is AI?"}
    },
    "agentic_processes": [
        {
            "process_id": "inference_1",
            "process_type": "logical_inference",
            "status": "active",
            "priority": 5,
            "started_at": time.time(),
            "progress": 0.7,
            "description": "Processing logical inference for query",
            "metadata": {"query_id": "test_query_1"}
        },
        {
            "process_id": "kb_search_1",
            "process_type": "knowledge_search",
            "status": "active",
            "priority": 4,
            "started_at": time.time(),
            "progress": 0.5,
            "description": "Searching knowledge base for relevant information",
            "metadata": {"search_terms": ["artificial", "intelligence"]}
        }
    ],
    "daemon_threads": [
        {
            "process_id": "memory_consolidation",
            "process_type": "background_learning",
            "status": "running",
            "priority": 2,
            "started_at": time.time() - 3600,
            "progress": 0.3,
            "description": "Consolidating recent knowledge into long-term memory",
            "metadata": {"items_processed": 15}
        },
        {
            "process_id": "pattern_recognition",
            "process_type": "pattern_analysis",
            "status": "running",
            "priority": 3,
            "started_at": time.time() - 1800,
            "progress": 0.6,
            "description": "Analyzing patterns in user interactions",
            "metadata": {"patterns_found": 8}
        }
    ],
    "working_memory": {
        "active_items": [
            {
                "item_id": "wm_1",
                "content": "Current user query about AI",
                "activation_level": 0.9,
                "created_at": time.time(),
                "last_accessed": time.time(),
                "access_count": 1
            },
            {
                "item_id": "wm_2", 
                "content": "Retrieved AI definition from knowledge base",
                "activation_level": 0.7,
                "created_at": time.time() - 10,
                "last_accessed": time.time() - 5,
                "access_count": 3
            }
        ]
    },
    "attention_focus": [
        {
            "item_id": "focus_1",
            "item_type": "query",
            "salience": 0.95,
            "duration": 15.5,
            "description": "User query about artificial intelligence"
        },
        {
            "item_id": "focus_2",
            "item_type": "knowledge",
            "salience": 0.6,
            "duration": 8.2,
            "description": "AI definition from knowledge base"
        }
    ],
    "metacognitive_state": {
        "self_awareness_level": 0.75,
        "confidence_in_reasoning": 0.85,
        "cognitive_load": 0.4,
        "learning_rate": 0.6,
        "adaptation_level": 0.7,
        "introspection_depth": 3
    }
}


# Pytest Fixtures

@pytest.fixture
def sample_query_request():
    """Create a sample query request."""
    return QueryRequest(
        query="What is artificial intelligence?",
        context={"domain": "technology", "complexity": "intermediate"},
        include_reasoning=True
    )


@pytest.fixture
def sample_query_response():
    """Create a sample query response."""
    reasoning_steps = [
        ReasoningStep(
            step_number=1,
            operation="knowledge_retrieval",
            description="Retrieved AI definition from knowledge base",
            premises=["User asked about AI"],
            conclusion="AI is artificial intelligence",
            confidence=0.9
        ),
        ReasoningStep(
            step_number=2,
            operation="synthesis",
            description="Synthesized comprehensive response",
            premises=["AI definition", "Context about technology"],
            conclusion="Provided detailed AI explanation",
            confidence=0.85
        )
    ]
    
    return QueryResponse(
        response="Artificial intelligence (AI) is a branch of computer science focused on creating systems that can perform tasks typically requiring human intelligence.",
        confidence=0.88,
        reasoning_steps=reasoning_steps,
        inference_time_ms=250.5,
        knowledge_used=["ai_definition", "ai_history", "ai_applications"]
    )


@pytest.fixture
def sample_knowledge_request():
    """Create a sample knowledge request."""
    return KnowledgeRequest(
        content="Python is a high-level programming language known for its simplicity and readability.",
        knowledge_type="fact",
        context_id="programming",
        metadata={"source": "documentation", "confidence": 0.95}
    )


@pytest.fixture
def sample_knowledge_items():
    """Create sample knowledge items."""
    items = []
    for i, item_data in enumerate(SAMPLE_KNOWLEDGE_ITEMS):
        knowledge_item = KnowledgeItem(
            id=f"item_{i+1}",
            title=item_data["concept"],
            content=item_data["definition"],
            knowledge_type="concept",
            source=ImportSource(
                source_type="manual",
                source_identifier=f"test_source_{i+1}",
                metadata={"category": item_data["category"]}
            ),
            categories=[item_data["category"]],
            auto_categories=[],
            manual_categories=[],
            quality_score=0.8 + (i * 0.05),
            confidence=0.85 + (i * 0.03),
            validation_status="validated",
            extracted_at=time.time() - (i * 3600),
            access_count=i + 1,
            last_accessed=time.time() - (i * 1800)
        )
        items.append(knowledge_item)
    
    return items


@pytest.fixture
def sample_cognitive_state():
    """Create a sample cognitive state."""
    return SAMPLE_COGNITIVE_STATE.copy()


@pytest.fixture
def mock_godelos_integration():
    """Create a mock GödelOS integration."""
    mock = MagicMock()
    
    # Mock async methods
    mock.initialize = AsyncMock()
    mock.shutdown = AsyncMock()
    mock.get_health_status = AsyncMock(return_value={
        "healthy": True,
        "components": {
            "inference_engine": True,
            "knowledge_base": True,
            "cognitive_layers": True
        },
        "error_count": 0,
        "uptime_seconds": 3600.0,
        "memory_usage_mb": 512.0,
        "cpu_usage_percent": 25.5
    })
    
    mock.process_natural_language_query = AsyncMock(return_value={
        "response": "This is a test response from the mock integration.",
        "confidence": 0.85,
        "reasoning_steps": [
            {
                "step_number": 1,
                "operation": "test_operation",
                "description": "Mock reasoning step",
                "premises": ["test premise"],
                "conclusion": "test conclusion",
                "confidence": 0.85
            }
        ],
        "inference_time_ms": 150.0,
        "knowledge_used": ["mock_knowledge_1", "mock_knowledge_2"]
    })
    
    mock.add_knowledge = AsyncMock(return_value={
        "status": "success",
        "knowledge_id": "mock_knowledge_123",
        "message": "Knowledge added successfully"
    })
    
    mock.get_knowledge = AsyncMock(return_value={
        "facts": [],
        "rules": [],
        "concepts": [
            {
                "id": "concept_1",
                "content": "Mock concept for testing",
                "knowledge_type": "concept",
                "confidence": 0.9
            }
        ],
        "total_count": 1
    })
    
    mock.get_cognitive_state = AsyncMock(return_value=SAMPLE_COGNITIVE_STATE)
    
    return mock


@pytest.fixture
def mock_websocket_manager():
    """Create a mock WebSocket manager."""
    mock = MagicMock()
    
    # Mock async methods
    mock.connect = AsyncMock()
    mock.disconnect = MagicMock()
    mock.broadcast = AsyncMock()
    mock.subscribe_to_events = AsyncMock()
    mock.has_connections = MagicMock(return_value=True)
    mock.ping_connections = AsyncMock()
    
    # Mock connection stats
    mock.get_connection_stats = MagicMock(return_value={
        "total_connections": 2,
        "total_events_sent": 150,
        "avg_connection_duration_seconds": 300.5,
        "event_queue_size": 10,
        "subscription_summary": {
            "query_processed": 2,
            "knowledge_added": 1,
            "cognitive_state_update": 2
        }
    })
    
    return mock


@pytest.fixture
def mock_knowledge_management_service():
    """Create a mock knowledge management service."""
    mock = MagicMock()
    
    # Mock async methods
    mock.initialize = AsyncMock()
    mock.search_knowledge = AsyncMock()
    mock.get_knowledge_item = AsyncMock()
    mock.delete_knowledge_item = AsyncMock(return_value=True)
    mock.get_categories = AsyncMock(return_value=[])
    mock.create_category = AsyncMock(return_value=True)
    mock.categorize_items = AsyncMock(return_value=5)
    mock.get_knowledge_statistics = AsyncMock()
    
    return mock


@pytest.fixture
def temporary_test_directory():
    """Create a temporary directory for testing."""
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_test_files(temporary_test_directory):
    """Create sample test files in temporary directory."""
    test_dir = Path(temporary_test_directory)
    
    # Create sample text file
    text_file = test_dir / "sample.txt"
    text_file.write_text("This is a sample text file for testing knowledge ingestion.")
    
    # Create sample JSON file
    json_file = test_dir / "sample.json"
    json_data = {
        "title": "Sample JSON Data",
        "content": "This is sample JSON content for testing",
        "metadata": {"source": "test", "type": "sample"}
    }
    json_file.write_text(json.dumps(json_data, indent=2))
    
    # Create sample knowledge file
    knowledge_file = test_dir / "knowledge.txt"
    knowledge_file.write_text("""
    Machine Learning: A subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.
    
    Neural Networks: Computing systems inspired by biological neural networks, consisting of interconnected nodes (neurons) that process and transmit information.
    
    Deep Learning: A machine learning technique based on artificial neural networks with multiple layers, capable of learning complex patterns in data.
    """)
    
    return {
        "text_file": text_file,
        "json_file": json_file,
        "knowledge_file": knowledge_file,
        "directory": test_dir
    }


@pytest.fixture
def mock_external_apis():
    """Create mocks for external APIs."""
    return {
        "wikipedia": MagicMock(),
        "web_scraper": MagicMock(),
        "file_processor": MagicMock()
    }


@pytest.fixture(scope="session")
def performance_baseline():
    """Performance baseline metrics for testing."""
    return {
        "api_response_time_ms": 500,
        "query_processing_time_ms": 1000,
        "knowledge_search_time_ms": 200,
        "websocket_message_latency_ms": 50,
        "memory_usage_mb": 1024,
        "cpu_usage_percent": 50
    }


# Test Data Generators

def generate_test_queries(count: int = 10) -> List[str]:
    """Generate test queries for testing."""
    base_queries = [
        "What is {}?",
        "How does {} work?",
        "Explain {} in detail",
        "What are the benefits of {}?",
        "How can I use {}?"
    ]
    
    topics = [
        "artificial intelligence", "machine learning", "neural networks",
        "deep learning", "natural language processing", "computer vision",
        "robotics", "data science", "algorithms", "programming"
    ]
    
    queries = []
    for i in range(count):
        query_template = base_queries[i % len(base_queries)]
        topic = topics[i % len(topics)]
        queries.append(query_template.format(topic))
    
    return queries


def generate_test_knowledge_items(count: int = 20) -> List[Dict[str, Any]]:
    """Generate test knowledge items."""
    categories = ["technology", "science", "mathematics", "programming", "ai"]
    types = ["fact", "concept", "rule", "procedure"]
    
    items = []
    for i in range(count):
        item = {
            "id": f"test_item_{i+1}",
            "title": f"Test Knowledge Item {i+1}",
            "content": f"This is test knowledge content for item {i+1}. It contains information about various topics for testing purposes.",
            "knowledge_type": types[i % len(types)],
            "category": categories[i % len(categories)],
            "confidence": 0.7 + (i % 4) * 0.1,
            "quality_score": 0.6 + (i % 5) * 0.1,
            "source_type": "test",
            "created_at": time.time() - (i * 3600)
        }
        items.append(item)
    
    return items


def generate_cognitive_events(count: int = 50) -> List[Dict[str, Any]]:
    """Generate test cognitive events."""
    event_types = [
        "query_processed", "knowledge_added", "inference_started", 
        "inference_completed", "memory_updated", "attention_shifted"
    ]
    
    events = []
    for i in range(count):
        event = {
            "event_id": f"event_{i+1}",
            "event_type": event_types[i % len(event_types)],
            "timestamp": time.time() - (i * 60),
            "source_process": f"process_{(i % 5) + 1}",
            "description": f"Test cognitive event {i+1}",
            "data": {
                "query_id": f"query_{i+1}" if i % 3 == 0 else None,
                "confidence": 0.5 + (i % 5) * 0.1,
                "processing_time_ms": 50 + (i % 10) * 20
            },
            "metadata": {"test": True, "sequence": i+1}
        }
        events.append(event)
    
    return events


# Utility Functions for Tests

def assert_valid_query_response(response: Dict[str, Any]):
    """Assert that a query response has valid structure."""
    required_fields = ["response", "confidence", "inference_time_ms"]
    for field in required_fields:
        assert field in response, f"Query response missing required field: {field}"
    
    assert isinstance(response["response"], str), "Response should be a string"
    assert 0.0 <= response["confidence"] <= 1.0, "Confidence should be between 0 and 1"
    assert response["inference_time_ms"] >= 0, "Inference time should be non-negative"


def assert_valid_cognitive_state(state: Dict[str, Any]):
    """Assert that a cognitive state has valid structure."""
    required_fields = [
        "manifest_consciousness", "agentic_processes", "daemon_threads",
        "working_memory", "attention_focus", "metacognitive_state"
    ]
    
    for field in required_fields:
        assert field in state, f"Cognitive state missing required field: {field}"
    
    assert isinstance(state["agentic_processes"], list), "Agentic processes should be a list"
    assert isinstance(state["daemon_threads"], list), "Daemon threads should be a list"


def assert_valid_knowledge_item(item: Dict[str, Any]):
    """Assert that a knowledge item has valid structure."""
    required_fields = ["id", "content", "knowledge_type"]
    for field in required_fields:
        assert field in item, f"Knowledge item missing required field: {field}"
    
    assert isinstance(item["content"], str), "Content should be a string"
    assert len(item["content"]) > 0, "Content should not be empty"


def create_mock_websocket():
    """Create a mock WebSocket for testing."""
    mock_ws = MagicMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.receive_json = AsyncMock()
    mock_ws.receive_text = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


# Test Configuration

TEST_CONFIG = {
    "backend_url": "http://localhost:8000",
    "frontend_url": "http://localhost:3000",
    "websocket_url": "ws://localhost:8000/ws/unified-cognitive-stream",
    "test_timeout": 10,
    "concurrent_users": 5,
    "performance_thresholds": {
        "api_response_time_ms": 2000,
        "query_processing_time_ms": 5000,
        "websocket_latency_ms": 100
    }
}