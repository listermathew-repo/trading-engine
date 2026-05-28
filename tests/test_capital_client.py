import pytest
import os
from unittest.mock import patch, MagicMock
from api.capital_client import CapitalClient, TradeResult


@pytest.fixture
def setup_env():
    """Set required environment variables for CapitalClient"""
    os.environ["CAPITAL_API_KEY"] = "test-key"
    os.environ["CAPITAL_IDENTIFIER"] = "test-identifier"
    os.environ["CAPITAL_PASSWORD"] = "test-password"
    os.environ["CAPITAL_ENVIRONMENT"] = "demo"
    yield
    # Cleanup
    for key in ["CAPITAL_API_KEY", "CAPITAL_IDENTIFIER", "CAPITAL_PASSWORD", "CAPITAL_ENVIRONMENT"]:
        os.environ.pop(key, None)


def test_client_initialization(setup_env):
    """Test CapitalClient initializes correctly"""
    client = CapitalClient()
    assert client.api_key == "test-key"
    assert client.identifier == "test-identifier"
    assert client.password == "test-password"
    assert "demo-api-capital" in client.base_url


def test_resolve_instrument_known_symbol(setup_env):
    """Test instrument resolution for known symbols"""
    client = CapitalClient()

    # Test GOLD mapping
    result = client._resolve_instrument("XAUUSD")
    assert result["epic"] == "GOLD"
    assert result["pip_size"] == 0.10
    assert result["pip_value"] == 1.0

    # Test EURUSD
    result = client._resolve_instrument("EURUSD")
    assert result["epic"] == "EURUSD"
    assert result["pip_size"] == 0.0001
    assert result["pip_value"] == 10.0


def test_resolve_instrument_unknown_symbol(setup_env):
    """Test instrument resolution for unknown symbols (default to forex specs)"""
    client = CapitalClient()

    result = client._resolve_instrument("UNKNOWN")
    assert result["epic"] == "UNKNOWN"
    assert result["pip_size"] == 0.0001
    assert result["pip_value"] == 10.0


def test_calculate_position_size(setup_env):
    """Test position sizing formula"""
    client = CapitalClient()

    # Test: balance=$80k, risk=0.5%, entry=2450, stop=2445
    # Risk amount = 80000 * 0.005 = $400
    # Stop pips = (2450 - 2445) / 0.10 = 50 pips
    # Size = 400 / (50 * 1.0) = 8.0 lots
    size = client._calculate_size(
        balance=80000.0,
        entry_price=2450.0,
        stop_price=2445.0,
        pip_size=0.10,
        pip_value=1.0
    )
    assert size == 8.0


def test_calculate_position_size_minimum_lot(setup_env):
    """Test that position sizing respects minimum lot size"""
    client = CapitalClient()

    # Test with very close stop loss - should return minimum 0.01 lot
    size = client._calculate_size(
        balance=80000.0,
        entry_price=2450.0,
        stop_price=2449.99,
        pip_size=0.10,
        pip_value=1.0
    )
    assert size >= 0.01


def test_calculate_size_zero_stop_pips(setup_env):
    """Test position sizing handles zero stop distance"""
    client = CapitalClient()

    # Same entry and stop should return minimum lot
    size = client._calculate_size(
        balance=80000.0,
        entry_price=2450.0,
        stop_price=2450.0,
        pip_size=0.10,
        pip_value=1.0
    )
    assert size == 0.01


@patch('api.capital_client.requests.post')
@patch('api.capital_client.requests.get')
def test_place_market_order_success(mock_get, mock_post, setup_env):
    """Test successful trade placement"""
    client = CapitalClient()

    # Mock authentication
    mock_post.return_value.status_code = 200
    mock_post.return_value.headers = {
        "CST": "mock-cst",
        "X-SECURITY-TOKEN": "mock-token"
    }

    # Mock get_account_balance
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "accounts": [
            {
                "preferred": True,
                "balance": {"balance": 80000.0}
            }
        ]
    }

    # Mock order placement response
    mock_post.return_value.json.return_value = {"dealReference": "REF-12345"}

    result = client.place_market_order(
        symbol="XAUUSD",
        direction="BUY",
        entry_price=2450.0,
        stop_price=2445.0
    )

    assert result.success is True
    assert result.deal_reference == "REF-12345"
    assert result.direction == "BUY"
    assert result.epic == "GOLD"


@patch('api.capital_client.requests.post')
def test_place_market_order_invalid_direction(mock_post, setup_env):
    """Test order placement with invalid direction"""
    client = CapitalClient()

    result = client.place_market_order(
        symbol="XAUUSD",
        direction="INVALID",
        entry_price=2450.0,
        stop_price=2445.0
    )

    assert result.success is False
    assert "Invalid direction" in result.message


@patch('api.capital_client.requests.post')
@patch('api.capital_client.requests.get')
def test_place_market_order_no_stop(mock_get, mock_post, setup_env):
    """Test order placement without stop loss (minimum lot size)"""
    client = CapitalClient()

    # Mock authentication
    mock_post.return_value.status_code = 200
    mock_post.return_value.headers = {
        "CST": "mock-cst",
        "X-SECURITY-TOKEN": "mock-token"
    }

    # Mock get_account_balance
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "accounts": [
            {
                "preferred": True,
                "balance": {"balance": 80000.0}
            }
        ]
    }

    # Mock order placement
    mock_post.return_value.json.return_value = {"dealReference": "REF-67890"}

    result = client.place_market_order(
        symbol="EURUSD",
        direction="SELL",
        entry_price=1.0850,
        stop_price=None
    )

    assert result.success is True
    assert result.size == 0.01  # Minimum lot without stop
