"""
Unit tests for main FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "MERE AI Agent API Server"
    assert data["status"] == "running"

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "mere-ai-agent"

def test_websocket_connection():
    """Test WebSocket connection (basic)"""
    # This will be expanded when WebSocket logic is implemented
    with client.websocket_connect("/ws/test-user") as websocket:
        # Send a test message
        test_message = {"message": "Hello MERE", "type": "text"}
        websocket.send_json(test_message)
        
        # Receive response
        data = websocket.receive_json()
        assert data["type"] == "text_response"
        assert "Received: Hello MERE" in data["message"]
        assert data["user_id"] == "test-user"