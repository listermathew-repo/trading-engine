"""Detect swing lows for stop loss placement."""

from typing import Optional
from .capital_data import OHLCV


class SwingDetector:
    """Detect swing lows on the 15-minute timeframe."""

    @staticmethod
    def find_swing_low(
        candles: list[OHLCV],
        lookback: int = 10,
    ) -> Optional[float]:
        """
        Find the lowest low within the lookback period.

        Args:
            candles: List of OHLCV candles
            lookback: Number of candles to look back (e.g., 5, 10, 20)

        Returns:
            The lowest price (low) within the lookback period, or None if insufficient candles
        """
        if not candles or len(candles) < lookback:
            return None

        # Get the last 'lookback' candles
        recent_candles = candles[-lookback:]

        # Find the lowest low
        swing_low = min(candle.low for candle in recent_candles)
        return swing_low

    @staticmethod
    def find_swing_low_at_index(
        candles: list[OHLCV],
        index: int,
        lookback: int = 10,
    ) -> Optional[float]:
        """
        Find the lowest low before a given candle index.

        Args:
            candles: List of OHLCV candles
            index: Index of the current candle
            lookback: Number of candles to look back

        Returns:
            The lowest price (low) within the lookback period before the given index
        """
        if index < lookback:
            return None

        # Get lookback candles before the current index
        start_idx = max(0, index - lookback)
        end_idx = index
        lookback_candles = candles[start_idx:end_idx]

        if not lookback_candles:
            return None

        swing_low = min(candle.low for candle in lookback_candles)
        return swing_low

    @staticmethod
    def find_multiple_swing_lows(
        candles: list[OHLCV],
        lookback_periods: list[int] = [5, 10, 20],
    ) -> dict[int, Optional[float]]:
        """
        Find swing lows for multiple lookback periods.

        Args:
            candles: List of OHLCV candles
            lookback_periods: List of lookback periods to check (e.g., [5, 10, 20])

        Returns:
            Dictionary mapping lookback period to swing low price
        """
        result = {}
        for lookback in lookback_periods:
            result[lookback] = SwingDetector.find_swing_low(candles, lookback)
        return result

    @staticmethod
    def find_multiple_swing_lows_at_index(
        candles: list[OHLCV],
        index: int,
        lookback_periods: list[int] = [5, 10, 20],
    ) -> dict[int, Optional[float]]:
        """
        Find swing lows at a specific index for multiple lookback periods.

        Args:
            candles: List of OHLCV candles
            index: Index of the current candle
            lookback_periods: List of lookback periods to check

        Returns:
            Dictionary mapping lookback period to swing low price
        """
        result = {}
        for lookback in lookback_periods:
            result[lookback] = SwingDetector.find_swing_low_at_index(
                candles, index, lookback
            )
        return result

    @staticmethod
    def is_red_candle(candle: OHLCV) -> bool:
        """
        Check if a candle is red (close < open).

        Args:
            candle: OHLCV candle

        Returns:
            True if close < open (bearish candle)
        """
        return candle.close < candle.open

    @staticmethod
    def find_lowest_red_candle_in_range(
        candles: list[OHLCV],
        start_idx: int,
        end_idx: int,
    ) -> Optional[int]:
        """
        Find the index of the red candle with the lowest low in a range.

        Args:
            candles: List of OHLCV candles
            start_idx: Start index (inclusive)
            end_idx: End index (exclusive)

        Returns:
            Index of the lowest red candle, or None if no red candles found
        """
        lowest_idx = None
        lowest_price = float('inf')

        for i in range(start_idx, end_idx):
            if i < len(candles) and SwingDetector.is_red_candle(candles[i]):
                if candles[i].low < lowest_price:
                    lowest_price = candles[i].low
                    lowest_idx = i

        return lowest_idx
