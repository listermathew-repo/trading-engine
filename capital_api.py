"""
CAPITAL.COM EXECUTION LAYER
Production API client for trade execution, market data, and position management.

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

    def __init__(self):
        """Initialize with credentials from .env file."""
        self.identifier = os.getenv('CAPITAL_IDENTIFIER')
        self.password = os.getenv('CAPITAL_PASSWORD')
        self.api_key = os.getenv('CAPITAL_API_KEY')

        self.cst = None
        self.security_token = None
        self.session = requests.Session()

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
        Returns True if authentication successful, False otherwise.
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
                self.cst = response.headers.get('CST')
                self.security_token = response.headers.get('X-SECURITY-TOKEN')

                if not self.cst or not self.security_token:
                    logger.error("Missing CST or X-SECURITY-TOKEN in response")
                    return False

                logger.info(f"Authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Authentication error: {type(e).__name__}: {e}")
            return False

    def get_market_data(self, epic: str = "AUDUSD") -> Optional[Dict[str, Any]]:
        """
        Retrieve live market data using authenticated session.
        """
        if not self.cst or not self.security_token:
            logger.error("Not authenticated. Call authenticate() first.")
            return None

        logger.info(f"Fetching market data for {epic}...")

        headers = {
            "X-CAP-API-KEY": self.api_key,
            "CST": self.cst,
            "X-SECURITY-TOKEN": self.security_token,
            "Accept": "application/json"
        }

        try:
            response = requests.get(
                self.MARKETS_ENDPOINT,
                headers=headers,
                params={"epics": epic},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if 'marketDetails' in data and len(data['marketDetails']) > 0:
                    market = data['marketDetails'][0]
                    return {
                        'epic': market.get('epic'),
                        'bid': market.get('bid'),
                        'offer': market.get('offer'),
                        'updateTime': market.get('updateTime'),
                    }
            else:
                logger.error(f"Market data failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Market data error: {type(e).__name__}: {e}")
            return None

    def place_order(self, trade: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Place a trade order via Capital.com API.
        """
        if not self.cst or not self.security_token:
            logger.error("Not authenticated. Call authenticate() first.")
            return None

        logger.info(f"Placing {trade['direction']} order for {trade['epic']}")

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
            "size": trade.get('quantity', 10000),
            "orderType": trade.get('order_type', 'MARKET'),
            "stopLevel": trade.get('stop_level'),
            "forceOpen": True,
        }

        try:
            response = requests.post(
                self.POSITIONS_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Order placed: {data.get('dealReference')}")
                return {
                    'status': 'SUCCESS',
                    'deal_reference': data.get('dealReference'),
                    'timestamp': datetime.utcnow().isoformat(),
                }
            else:
                logger.error(f"Order failed: {response.status_code}")
                return {'status': 'FAILED', 'error': response.text}

        except Exception as e:
            logger.error(f"Order error: {type(e).__name__}: {e}")
            return {'status': 'ERROR', 'error': str(e)}

    def get_open_positions(self) -> Optional[list]:
        """Retrieve all open positions from the account."""
        if not self.cst or not self.security_token:
            logger.error("Not authenticated.")
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
                logger.info(f"Retrieved {len(data.get('positions', []))} positions")
                return data.get('positions', [])
            else:
                logger.error(f"Positions fetch failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Positions error: {type(e).__name__}: {e}")
            return None

    def logout(self) -> bool:
        """Close session with Capital.com API."""
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
                logger.info("Session closed")
                return True
            else:
                logger.warning(f"Logout returned {response.status_code}")
                return True

        except Exception as e:
            logger.warning(f"Logout failed: {e}")
            return True
