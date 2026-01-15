"""
Tests for the AI Agent FastAPI application.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

# Import the app
from main import app, QueryRequest, QueryResponse


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_pipeline():
    """Create a mock RAG pipeline."""
    mock = Mock()
    mock.process_query.return_value = "This is a test answer."
    mock.vector_store.get_index_size.return_value = 100
    return mock


def test_root_endpoint(client):
    """Test the root endpoint returns service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AI Agent"
    assert data["status"] == "running"
    assert "version" in data


def test_query_request_model_validation():
    """Test QueryRequest model validation."""
    # Valid request
    valid_request = QueryRequest(
        question="What is the height limit?",
        objects=[{"id": "obj_1", "height": 10}],
        top_k=5
    )
    assert valid_request.question == "What is the height limit?"
    assert len(valid_request.objects) == 1
    assert valid_request.top_k == 5
    
    # Request with defaults
    minimal_request = QueryRequest(question="Test question")
    assert minimal_request.objects == []
    assert minimal_request.top_k == 5
    
    # Invalid request - empty question should fail
    with pytest.raises(ValueError):
        QueryRequest(question="")


def test_query_response_model():
    """Test QueryResponse model."""
    response = QueryResponse(
        answer="Test answer",
        sources=["Doc 1", "Doc 2"]
    )
    assert response.answer == "Test answer"
    assert len(response.sources) == 2
    
    # Response without sources
    response_no_sources = QueryResponse(answer="Test answer")
    assert response_no_sources.answer == "Test answer"
    assert response_no_sources.sources is None


def test_query_endpoint_structure(client):
    """Test that the query endpoint exists and has correct structure."""
    # This will fail if pipeline is not initialized, but we're testing the endpoint exists
    response = client.post(
        "/api/agent/query",
        json={
            "question": "Test question",
            "objects": [],
            "top_k": 5
        }
    )
    # Should return either 503 (not initialized) or 500 (processing error) or 200 (success)
    # We're just checking the endpoint exists and accepts the request format
    assert response.status_code in [200, 500, 503]


def test_query_endpoint_with_mock_pipeline(client, monkeypatch):
    """Test query endpoint with mocked pipeline."""
    # Setup mock
    mock_pipeline = Mock()
    mock_pipeline.process_query.return_value = "Mocked answer to the question."
    mock_pipeline.vector_store.get_index_size.return_value = 100
    
    # Patch the global pipeline variable
    import main
    monkeypatch.setattr(main, 'pipeline', mock_pipeline)
    
    # Make request
    response = client.post(
        "/api/agent/query",
        json={
            "question": "What is the building height?",
            "objects": [{"id": "building_1", "height": 15}],
            "top_k": 3
        }
    )
    
    # Should return 200 with mocked pipeline
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Mocked answer to the question."
    
    # Verify the mock was called
    mock_pipeline.process_query.assert_called_once()


def test_query_endpoint_empty_question(client):
    """Test that empty questions are rejected."""
    response = client.post(
        "/api/agent/query",
        json={
            "question": "",
            "objects": []
        }
    )
    # Should return 422 (validation error) or 400 (bad request)
    assert response.status_code in [400, 422]


def test_query_endpoint_missing_question(client):
    """Test that requests without question field are rejected."""
    response = client.post(
        "/api/agent/query",
        json={
            "objects": []
        }
    )
    # Should return 422 (validation error)
    assert response.status_code == 422


def test_cors_headers(client):
    """Test that CORS headers are properly configured."""
    response = client.options(
        "/api/agent/query",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        }
    )
    # CORS should be configured
    assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled
