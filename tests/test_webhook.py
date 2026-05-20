import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.index import app


@pytest.fixture
def setup_env():
    """Set up environment variables for testing"""
    os.environ["NTFY_TOPIC"] = "test-topic"
    os.environ["SIMULATE_TRADES"] = "true"
    yield
    os.environ.pop("NTFY_TOPIC", None)
    os.environ.pop("SIMULATE_TRADES", None)


@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "ok"


@patch.dict(os.environ, {"WEBHOOK_API_KEY": "test-key-12345"})
def test_webhook_requires_api_key(client):
    """Test webhook rejects requests without API key"""
    response = client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            "action": "buy",
            "price": "2450.50",
            "stop": "2445.00"
        }
    )
    assert response.status_code == 401
    assert "API" in response.json()["detail"]


@patch.dict(os.environ, {"WEBHOOK_API_KEY": "test-key-12345"})
def test_webhook_rejects_invalid_api_key(client):
    """Test webhook rejects invalid API key"""
    response = client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            "action": "buy",
            "price": "2450.50",
            "stop": "2445.00"
        },
        headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 401


@patch("api.index.send_ntfy_notification")
@patch.dict(os.environ, {"WEBHOOK_API_KEY": "test-key-12345"})
def test_webhook_accepts_valid_api_key(mock_ntfy, client):
    """Test webhook accepts requests with valid API key"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    response = client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            "action": "buy",
            "price": "2450.50",
            "stop": "2445.00"
        },
        headers={"X-API-Key": "test-key-12345"}
    )
    assert response.status_code == 200


@patch('api.index.send_ntfy_notification')
def test_webhook_simulation_mode(mock_ntfy, client, setup_env):
    """Test webhook in simulation mode"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    response = client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            "action": "buy",
            "price": "2450.50",
            "stop": "2445.00"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["simulate"] is True
    assert "[SIMULATED]" in data["result"]
    assert data["status"] == "ok"
    mock_ntfy.assert_called_once()


@patch('api.index.send_ntfy_notification')
def test_webhook_buy_order(mock_ntfy, client, setup_env):
    """Test webhook processes BUY action"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    response = client.post(
        "/webhook",
        json={
            "symbol": "EURUSD",
            "action": "buy",
            "price": "1.0850",
            "stop": "1.0800"
        }
    )

    assert response.status_code == 200
    assert "BUY" in response.json()["result"]


@patch('api.index.send_ntfy_notification')
def test_webhook_sell_order(mock_ntfy, client, setup_env):
    """Test webhook processes SELL action"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    response = client.post(
        "/webhook",
        json={
            "symbol": "AUDUSD",
            "action": "sell",
            "price": "0.6500",
            "stop": "0.6550"
        }
    )

    assert response.status_code == 200
    assert "SELL" in response.json()["result"]


def test_webhook_missing_required_field(client, setup_env):
    """Test webhook with missing required field"""
    response = client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            # Missing 'action'
            "price": "2450.50"
        }
    )

    assert response.status_code == 422  # Validation error


def test_webhook_missing_price(client, setup_env):
    """Test webhook with missing price field"""
    response = client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            "action": "buy",
            # Missing 'price'
            "stop": "2445.00"
        }
    )

    assert response.status_code == 422  # Validation error


@patch('api.index.send_ntfy_notification')
def test_webhook_optional_stop_level(mock_ntfy, client, setup_env):
    """Test webhook with optional stop level omitted"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    response = client.post(
        "/webhook",
        json={
            "symbol": "GBPUSD",
            "action": "buy",
            "price": "1.2650"
            # stop is optional
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["simulate"] is True


@patch('api.index.send_ntfy_notification')
def test_webhook_ntfy_notification_called(mock_ntfy, client, setup_env):
    """Test that ntfy notification is always called"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            "action": "buy",
            "price": "2450.50",
            "stop": "2445.00"
        }
    )

    # Verify ntfy was called with correct parameters
    assert mock_ntfy.call_count == 1
    call_kwargs = mock_ntfy.call_args[1]
    assert "message" in call_kwargs
    assert "title" in call_kwargs


@patch('api.index.send_ntfy_notification')
def test_webhook_ntfy_failure_handling(mock_ntfy, client, setup_env):
    """Test webhook handles ntfy notification failures"""
    mock_ntfy.return_value = {"success": False, "message": "Notification failed"}

    response = client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            "action": "buy",
            "price": "2450.50",
            "stop": "2445.00"
        }
    )

    # Even with ntfy failure, webhook should complete successfully in simulation mode
    assert response.status_code == 200
    assert response.json()["ntfy"]["success"] is False


@patch('api.index.send_ntfy_notification')
def test_webhook_payload_parsing(mock_ntfy, client, setup_env):
    """Test webhook correctly parses payload"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    response = client.post(
        "/webhook",
        json={
            "symbol": "USDJPY",
            "action": "sell",
            "price": "150.50",
            "timeframe": "D",
            "stop": "151.00"
        }
    )

    assert response.status_code == 200
    result_msg = response.json()["result"]
    assert "SELL" in result_msg
    assert "USDJPY" in result_msg
    assert "150.5" in result_msg
