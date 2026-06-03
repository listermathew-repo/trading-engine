"""
Capital.com client wrapper for trade execution.
Provides CapitalClient class for API integration.
"""

from capital_api import CapitalAPI
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class TradeResult:
    """Result of a trade execution."""
    success: bool
    deal_reference: Optional[str]
    size: float
    direction: str
    epic: str
    message: str


class CapitalClient:
    """Capital.com API client wrapper."""
    
    def __init__(self):
        """Initialize Capital.com client."""
        self.api = CapitalAPI()
    
    def authenticate(self) -> bool:
        """Authenticate with Capital.com."""
        return self.api.authenticate()
    
    def place_market_order(self, symbol: str, direction: str, 
                          entry_price: float, stop_price: Optional[float]) -> TradeResult:
        """Place a market order."""
        trade = {
            'epic': symbol,
            'direction': direction.upper(),
            'quantity': 10000,
            'order_type': 'MARKET',
            'stop_level': stop_price,
        }
        
        result = self.api.place_order(trade)
        
        if result and result.get('status') == 'SUCCESS':
            return TradeResult(
                success=True,
                deal_reference=result.get('deal_reference'),
                size=1.0,
                direction=direction,
                epic=symbol,
                message=f"Order placed: {result.get('deal_reference')}"
            )
        else:
            return TradeResult(
                success=False,
                deal_reference=None,
                size=0.0,
                direction=direction,
                epic=symbol,
                message=result.get('error', 'Unknown error') if result else 'API error'
            )
    
    def get_open_positions(self) -> list:
        """Get open positions."""
        return self.api.get_open_positions() or []
