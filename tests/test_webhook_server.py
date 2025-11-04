"""
Tests for VoxMachina webhook server
"""

import json
from unittest.mock import Mock, patch

import pytest

from webhook_server import app


@pytest.fixture
def client():
    """Create test client"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert data["service"] == "voxmachina-webhook"


def test_webhook_requires_post(client):
    """Test that webhook only accepts POST requests"""
    response = client.get("/webhook")
    assert response.status_code == 405  # Method Not Allowed


@patch("webhook_server.client.webhooks.unwrap")
@patch("webhook_server.requests.post")
def test_incoming_call_webhook(mock_post, mock_unwrap, client):
    """Test incoming call webhook handling"""
    # Mock webhook event
    mock_event = Mock()
    mock_event.type = "realtime.call.incoming"
    mock_event.data.call_id = "call_test123"
    mock_event.data.sip_headers = [
        Mock(name="From", value="+1234567890"),
        Mock(name="To", value="+447520648361"),
    ]
    mock_unwrap.return_value = mock_event

    # Mock successful call acceptance
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    # Send webhook
    response = client.post(
        "/webhook",
        data=json.dumps({"type": "realtime.call.incoming"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 200
    mock_unwrap.assert_called_once()
    mock_post.assert_called_once()


@patch("webhook_server.client.webhooks.unwrap")
def test_call_ended_webhook(mock_unwrap, client):
    """Test call ended webhook handling"""
    # Mock webhook event
    mock_event = Mock()
    mock_event.type = "realtime.call.ended"
    mock_event.data.call_id = "call_test123"
    mock_unwrap.return_value = mock_event

    # Send webhook
    response = client.post(
        "/webhook",
        data=json.dumps({"type": "realtime.call.ended"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 200


@patch("webhook_server.client.webhooks.unwrap")
def test_invalid_webhook_signature(mock_unwrap, client):
    """Test webhook with invalid signature"""
    # Mock signature verification failure
    mock_unwrap.side_effect = Exception("Invalid signature")

    # Send webhook with invalid signature
    response = client.post(
        "/webhook",
        data=json.dumps({"type": "realtime.call.incoming"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400


def test_webhook_call_accept_config():
    """Test that call accept config has required fields"""
    from webhook_server import call_accept_config

    assert "type" in call_accept_config
    assert call_accept_config["type"] == "realtime"
    assert "model" in call_accept_config
    assert "instructions" in call_accept_config
    assert "voice" in call_accept_config
    assert "turn_detection" in call_accept_config


def test_webhook_initial_response():
    """Test that initial response is properly formatted"""
    from webhook_server import initial_response

    assert "type" in initial_response
    assert initial_response["type"] == "response.create"
    assert "response" in initial_response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
