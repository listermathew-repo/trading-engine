"""
CAPITAL.COM EXECUTION LAYER
Production API client for trade execution, market data, and position management.
Evolved from capital_api_staging.py with order placement capability.

Handles:
1. Authentication (session token extraction)
2. Market data retrieval
3. Live trade order placement
4. Position tracking
5. Graceful error handling with logging
"""

import os
import requests
import json
import logging
from dotenv import load_dotenv
from typing import Tuple, Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class CapitalAPI:
    """
    Production client for Capital.com API.
    Handles authentication, market data, and trade execution.
    """

    BASE_URL = "https://api-capital.backend-capital.com/api/v1"
    SESSION_ENDPOINT = f"{BASE_URL}/session"
    MARKETS_ENDPOINT = f"{BASE_URL}/markets"
    POSITIONS_ENDPOINT = f"{BASE_URL}/positions"
    DEALS_ENDPOINT = f"{BASE_URL}/deals"
    ORDERS_ENDPOINT = f"{BASE_URL}/workingorders"

    def __init__(self):
        """Initialize with credentials from .env file."""
        self.identifier = os.getenv('CAPITAL_IDENTIFIER')
        self.password = os.getenv('CAPITAL_PASSWORD')
        self.api_key = os.getenv('CAPITAL_API_KEY')

        self.cst = None
        self.security_token = None
        self.session = requests.Session()
        self.account_id = None

        # Validate credentials
        if not all([self.identifier, self.password, self.api_key]):
            raise ValueError(
                "Missing credentials. Ensure .env contains:\n"
                "  CAPITAL_IDENTIFIER=...\n"
                "  CAPITAL_PASSWORD=...\n"
                "  CAPITAL_API_KEY=..."
            )

    def authenticate(self) -> bool:
        """
        Authenticate against Capital.com API.
        Extracts CST and X-SECURITY-TOKEN from response headers.

        Returns:
            True if authentication successful, False otherwise
        """
        logger.info("Authenticating to Capital.com API...")

        payload = {
            "identifier": self.identifier,
            "password": self.password,
            "encryptionVersion": "V2"
        }

        headers = {
            "X-CAP-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = requests.post(
                self.SESSION_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                # Extract tokens from response headers
                self.cst = response.headers.get('CST')
                self.security_token = response.headers.get('X-SECURITY-TOKEN')

                if not self.cst or not self.security_token:
                    logger.error("Missing CST or X-SECURITY-TOKEN in response")
                    return False

                logger.info(f"Authentication successful. CST: {self.cst[:20]}...")
                return True
            else:
                logger.error(f"Authentication failed with status {response.status_code}: {response.text}")
                return False

        except requests.exceptions.Timeout:
            logger.error("Authentication request timed out (10s)")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e}")
            return False

    def get_market_data(self, epic: str = "AUDUSD") -> Optional[Dict[str, Any]]:
        """
        Retrieve live market data using authenticated session.

        Args:
            epic: Market epic code (default: AUDUSD)

        Returns:
            Dict with market data if successful, None otherwise
        """
        if not self.cst or not self.security_token:
            logger.error("Not authenticated. Call authenticate() first.")
            return None

        logger.info(f"Fetching live market data for {epic}...")

        headers = {
            "X-CAP-API-KEY": self.api_key,
            "CST": self.cst,
            "X-SECURITY-TOKEN": self.security_token,
            "Accept": "application/json"
        }

        params = {"epics": epic}

        try:
            response = requests.get(
                self.MARKETS_ENDPOINT,
                headers=headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                if 'marketDetails' in data and len(data['marketDetails']) > 0:
                    market = data['marketDetails'][0]
                    return {
                        'epic': market.get('epic'),
                        'instrumentName': market.get('instrumentName'),
                        'bid': market.get('bid'),
                        'offer': market.get('offer'),
                        'bid_size': market.get('bidSize'),
                        'offer_size': market.get('offerSize'),
                        'percentage_change': market.get('percentageChange'),
                        'netChange': market.get('netChange'),
                        'updateTime': market.get('updateTime'),
                    }
                else:
                    logger.error("No market details in response")
                    return None
            else:
                logger.error(f"Market data request failed with status {response.status_code}: {response.text}")
                return None

        except requests.exceptions.Timeout:
            logger.error("Market data request timed out (10s)")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e}")
            return None

    def place_order(self, trade: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Place a trade order via Capital.com API.

        Args:
            trade: Dict with keys:
                - 'epic': Instrument epic (e.g., 'AUDUSD')
                - 'direction': 'BUY' or 'SELL'
                - 'quantity': Position size (e.g., 10000)
                - 'order_type': 'MARKET' or 'LIMIT' (default: MARKET)
                - 'limit_price': Required if order_type='LIMIT'
                - 'stop_level': Stop loss price
                - 'take_profit_level': Take profit price (optional)

        Returns:
            Dict with deal reference and trade details, or None on error
        """
        if not self.cst or not self.security_token:
            logger.error("Not authenticated. Call authenticate() first.")
            return None

        logger.info(f"Placing {trade['direction']} order for {trade['epic']} x {trade['quantity']}")

        headers = {
            "X-CAP-API-KEY": self.api_key,
            "CST": self.cst,
            "X-SECURITY-TOKEN": self.security_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "epic": trade['epic'],
            "direction": trade['direction'],
            "size": trade['quantity'],
            "orderType": trade.get('order_type', 'MARKET'),
            "stopLevel": trade.get('stop_level'),
            "takeProfitLevel": trade.get('take_profit_level'),
            "forceOpen": True,
        }

        # Add limit price if order is limit type
        if trade.get('order_type') == 'LIMIT':
            payload['limitLevel'] = trade.get('limit_price')

        try:
            response = requests.post(
                self.POSITIONS_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Order placed successfully. Deal reference: {data.get('dealReference')}")
                return {
                    'status': 'SUCCESS',
                    'deal_reference': data.get('dealReference'),
                    'deal_status': data.get('dealStatus'),
                    'timestamp': datetime.utcnow().isoformat(),
                    'epic': trade['epic'],
                    'direction': trade['direction'],
                    'quantity': trade['quantity'],
                }
            else:
                logger.error(f"Order placement failed with status {response.status_code}: {response.text}")
                return {
                    'status': 'FAILED',
                    'error': response.text,
                    'timestamp': datetime.utcnow().isoformat(),
                }

        except requests.exceptions.Timeout:
            logger.error("Order placement request timed out (10s)")
            return {
                'status': 'TIMEOUT',
                'error': 'API timeout after 10 seconds',
                'timestamp': datetime.utcnow().isoformat(),
            }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return {
                'status': 'CONNECTION_ERROR',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e}")
            return {
                'status': 'ERROR',
                'error': f"{type(e).__name__}: {e}",
                'timestamp': datetime.utcnow().isoformat(),
            }

    def get_open_positions(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve all open positions from the account.

        Returns:
            Dict with open positions list, or None on error
        """
        if not self.cst or not self.security_token:
            logger.error("Not authenticated. Call authenticate() first.")
            return None

        logger.info("Fetching open positions...")

        headers = {
            "X-CAP-API-KEY": self.api_key,
            "CST": self.cst,
            "X-SECURITY-TOKEN": self.security_token,
            "Accept": "application/json"
        }

        try:
            response = requests.get(
                self.POSITIONS_ENDPOINT,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Retrieved {len(data.get('positions', []))} open positions")
                return data
            else:
                logger.error(f"Position retrieval failed with status {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error retrieving positions: {type(e).__name__}: {e}")
            return None

    def close_position(self, position_id: str) -> Optional[Dict[str, Any]]:
        """
        Close an open position.

        Args:
            position_id: The position ID to close

        Returns:
            Dict with closure details, or None on error
        """
        if not self.cst or not self.security_token:
            logger.error("Not authenticated. Call authenticate() first.")
            return None

        logger.info(f"Closing position {position_id}...")

        headers = {
            "X-CAP-API-KEY": self.api_key,
            "CST": self.cst,
            "X-SECURITY-TOKEN": self.security_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {"orderType": "MARKET"}

        try:
            response = requests.post(
                f"{self.POSITIONS_ENDPOINT}/{position_id}/close",
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 201]:
                logger.info(f"Position {position_id} closed successfully")
                return response.json()
            else:
                logger.error(f"Position close failed with status {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error closing position: {type(e).__name__}: {e}")
            return None

    def logout(self) -> bool:
        """
        Close session with Capital.com API.

        Returns:
            True if logout successful
        """
        if not self.cst or not self.security_token:
            logger.warning("Not authenticated, skipping logout")
            return True

        logger.info("Closing session...")

        headers = {
            "X-CAP-API-KEY": self.api_key,
            "CST": self.cst,
            "X-SECURITY-TOKEN": self.security_token,
            "Accept": "application/json"
        }

        try:
            response = requests.delete(
                self.SESSION_ENDPOINT,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 204]:
                logger.info("Session closed successfully")
                return True
            else:
                logger.warning(f"Logout returned status {response.status_code}")
                return True

        except Exception as e:
            logger.warning(f"Logout failed: {e}")
            return True
