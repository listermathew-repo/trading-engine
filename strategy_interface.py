"""
STRATEGY INTERFACE (Protocol)
Defines the contract that any strategy must follow.
The engine will only interact with strategies through these methods.
"""

from typing import Protocol, List, Dict, Any


class StrategyInterface(Protocol):
    """
    Interface for trading strategies.
    Any strategy following this protocol can be plugged into the engine.
    """

    def generate_signals(self, data: List[Any]) -> List[Dict[str, Any]]:
        """
        Detect trading signals from raw price data.

        Args:
            data: List of bars (symbol, time, open, high, low, close, volume, hour_utc, minute_utc)

        Returns:
            List of signal dicts with keys:
            - 'bar_idx': int (index of FVG formation bar)
            - 'timestamp': str (ISO timestamp)
            - 'symbol': str (trading pair)
            - 'type': str ('LONG' or 'SHORT')
            - 'entry_level': float (FVG boundary price)
            - 'gap_pips': float (gap size in pips)
            - 'utc_h', 'utc_m': int (time of signal)
        """
        ...

    def calculate_indicators(self, data: List[Any]) -> Dict[str, Any]:
        """
        Calculate all technical indicators for context.

        Args:
            data: List of bars

        Returns:
            Dict with keys like:
            - 'atr': float (volatility)
            - 'h4_bias': int (1=bull, -1=bear, 0=neutral)
            - 'daily_bias': int (1=bull, -1=bear, 0=neutral)
        """
        ...

    def filter_signals(
        self, signals: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply confluence filters to reduce false signals.

        Args:
            signals: List of unfiltered signals from generate_signals()
            context: Dict with keys:
                - 'bars': List of M15 bars
                - 'h4_bars': List of H4 bars (or None)
                - 'daily_bars': List of Daily bars (or None)
                - 'config': Dict of configuration parameters

        Returns:
            Filtered list of signals that pass all confluence tests.
        """
        ...
