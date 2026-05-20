import pytest
import os
import sqlite3
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.index import app
from api.database import DB_PATH


@pytest.fixture
def setup_env():
    """Set up environment variables for testing"""
    os.environ["NTFY_TOPIC"] = "test-topic"
    os.environ["SIMULATE_TRADES"] = "true"
    os.environ["WEBHOOK_API_KEY"] = "test-key"
    yield
    os.environ.pop("NTFY_TOPIC", None)
    os.environ.pop("SIMULATE_TRADES", None)
    os.environ.pop("WEBHOOK_API_KEY", None)


@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def clean_db(setup_env):
    """Clear database tables before each test to prevent rate limit interference"""
    # Clean tables before test
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM trade_attempts")
        cursor.execute("DELETE FROM pending_trades")
        cursor.execute("DELETE FROM trades")
        cursor.execute("DELETE FROM system_events")
        conn.commit()
    except Exception as e:
        print(f"Warning: Could not clean database: {e}")
    finally:
        conn.close()

    yield

    # Clean tables after test
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM trade_attempts")
        cursor.execute("DELETE FROM pending_trades")
        cursor.execute("DELETE FROM trades")
        cursor.execute("DELETE FROM system_events")
        conn.commit()
    except Exception as e:
        print(f"Warning: Could not clean database: {e}")
    finally:
        conn.close()


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
    assert response.status_code == 202


@patch('api.index.send_ntfy_notification')
def test_webhook_queues_trade(mock_ntfy, client, clean_db):
    """Test webhook queues trade instead of executing immediately"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    response = client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            "action": "buy",
            "price": "2450.50",
            "stop": "2445.00"
        },
        headers={"X-API-Key": "test-key"}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert "trade_id" in data
    assert "expires_at" in data
    assert data["message"] == "Trade queued for approval"


@patch('api.index.send_ntfy_notification')
def test_webhook_buy_order(mock_ntfy, client, clean_db):
    """Test webhook processes BUY action"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    response = client.post(
        "/webhook",
        json={
            "symbol": "EURUSD",
            "action": "buy",
            "price": "1.0850",
            "stop": "1.0800"
        },
        headers={"X-API-Key": "test-key"}
    )

    assert response.status_code == 202
    assert "trade_id" in response.json()


@patch('api.index.send_ntfy_notification')
def test_webhook_sell_order(mock_ntfy, client, clean_db):
    """Test webhook processes SELL action"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    response = client.post(
        "/webhook",
        json={
            "symbol": "AUDUSD",
            "action": "sell",
            "price": "0.6500",
            "stop": "0.6550"
        },
        headers={"X-API-Key": "test-key"}
    )

    assert response.status_code == 202
    assert "trade_id" in response.json()


def test_webhook_missing_required_field(client, clean_db):
    """Test webhook with missing required field"""
    response = client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            # Missing 'action'
            "price": "2450.50"
        },
        headers={"X-API-Key": "test-key"}
    )

    assert response.status_code == 422  # Validation error


def test_webhook_missing_price(client, clean_db):
    """Test webhook with missing price field"""
    response = client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            "action": "buy",
            # Missing 'price'
            "stop": "2445.00"
        },
        headers={"X-API-Key": "test-key"}
    )

    assert response.status_code == 422  # Validation error


@patch('api.index.send_ntfy_notification')
def test_webhook_optional_stop_level(mock_ntfy, client, clean_db):
    """Test webhook with optional stop level omitted"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    response = client.post(
        "/webhook",
        json={
            "symbol": "GBPUSD",
            "action": "buy",
            "price": "1.2650"
            # stop is optional
        },
        headers={"X-API-Key": "test-key"}
    )

    assert response.status_code == 202
    data = response.json()
    assert "trade_id" in data


@patch('api.index.send_ntfy_notification')
def test_webhook_ntfy_notification_called(mock_ntfy, client, clean_db):
    """Test that ntfy notification is called on webhook"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            "action": "buy",
            "price": "2450.50",
            "stop": "2445.00"
        },
        headers={"X-API-Key": "test-key"}
    )

    # Verify ntfy was called with correct parameters
    assert mock_ntfy.call_count == 1
    call_kwargs = mock_ntfy.call_args[1]
    assert "message" in call_kwargs
    assert "title" in call_kwargs


@patch('api.index.send_ntfy_notification')
def test_webhook_payload_parsing(mock_ntfy, client, clean_db):
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
        },
        headers={"X-API-Key": "test-key"}
    )

    assert response.status_code == 202
    assert "trade_id" in response.json()


@patch('api.index.send_ntfy_notification')
def test_list_pending_trades(mock_ntfy, client, clean_db):
    """Test GET /pending lists queued trades"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    # Queue a trade
    client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            "action": "buy",
            "price": "2450.50",
            "stop": "2445.00"
        },
        headers={"X-API-Key": "test-key"}
    )

    # Get pending trades
    response = client.get("/pending", headers={"X-API-Key": "test-key"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["count"] >= 1
    assert "trades" in data


@patch('api.index.send_ntfy_notification')
def test_approve_pending_trade(mock_ntfy, client, clean_db):
    """Test GET /approve/{trade_id} executes pending trade"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    # Queue a trade
    webhook_response = client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            "action": "buy",
            "price": "2450.50",
            "stop": "2445.00"
        },
        headers={"X-API-Key": "test-key"}
    )
    trade_id = webhook_response.json()["trade_id"]

    # Approve the trade
    response = client.get(f"/approve/{trade_id}", headers={"X-API-Key": "test-key"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["trade_id"] == trade_id
    assert "executed_at" in data


@patch('api.index.send_ntfy_notification')
def test_approve_nonexistent_trade(mock_ntfy, client, clean_db):
    """Test approval of non-existent trade returns 404"""
    response = client.get("/approve/nonexistent-trade-id", headers={"X-API-Key": "test-key"})
    assert response.status_code == 404


@patch('api.index.send_ntfy_notification')
def test_duplicate_trade_prevention(mock_ntfy, client, clean_db):
    """Test rate limiting prevents duplicate trades within 30 seconds"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    # First trade should succeed
    response1 = client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            "action": "buy",
            "price": "2450.50",
            "stop": "2445.00"
        },
        headers={"X-API-Key": "test-key"}
    )
    assert response1.status_code == 202

    # Second identical trade within 30 seconds should be blocked
    response2 = client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            "action": "buy",
            "price": "2450.50",
            "stop": "2445.00"
        },
        headers={"X-API-Key": "test-key"}
    )
    assert response2.status_code == 429
    assert "Duplicate trade rejected" in response2.json()["detail"]


@patch('api.index.send_ntfy_notification')
def test_positions_endpoint(mock_ntfy, client, clean_db):
    """Test GET /positions returns open positions"""
    response = client.get("/positions", headers={"X-API-Key": "test-key"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["simulate"] == True  # Should be in simulation mode
    assert "positions" in data
    assert "count" in data


@patch('api.index.send_ntfy_notification')
def test_health_check_with_monitoring(mock_ntfy, client, clean_db):
    """Test health check includes monitoring metrics"""
    mock_ntfy.return_value = {"success": True, "message": "Notification sent"}

    # Queue a trade to generate some events
    client.post(
        "/webhook",
        json={
            "symbol": "XAUUSD",
            "action": "buy",
            "price": "2450.50",
            "stop": "2445.00"
        },
        headers={"X-API-Key": "test-key"}
    )

    response = client.get("/")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert "monitoring" in data
    monitoring = data["monitoring"]
    assert "last_webhook_received" in monitoring
    assert "last_trade_executed" in monitoring
    assert "error_count_last_hour" in monitoring
    assert "capital_com_status" in monitoring
