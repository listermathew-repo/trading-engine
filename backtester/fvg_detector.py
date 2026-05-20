"""Detect Fair Value Gaps (FVGs) on the chart."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from capital_data import OHLCV


@dataclass
class FVG:
    """Fair Value Gap (unmitigated imbalance)."""
    detected_at: datetime  # Timestamp when gap was detected
    direction: str  # "bullish" or "bearish"
    top: float     # Upper bound of the gap zone
    bottom: float  # Lower bound of the gap zone
    gap_size: float  # Size of the gap in pips (approximate)

    def __repr__(self) -> str:
        return (
            f"FVG({self.direction.upper()} | "
            f"Zone: {self.bottom:.4f}-{self.top:.4f} | "
            f"Gap: {self.gap_size:.4f} pips | "
            f"At: {self.detected_at.strftime('%Y-%m-%d %H:%M')})"
        )

    def contains_price(self, price: float) -> bool:
        """Check if price is within the FVG zone."""
        return self.bottom <= price <= self.top

    def is_mitigated_by_candle(self, candle: OHLCV) -> bool:
        """
        Check if this FVG has been mitigated (filled) by the given candle.

        For a bullish FVG (gap up):
        - Mitigated if any candle's low crosses into the gap zone

        For a bearish FVG (gap down):
        - Mitigated if any candle's high crosses into the gap zone
        """
        if self.direction == "bullish":
            # Bullish FVG is mitigated if price goes down into the gap
            return candle.low < self.bottom
        else:  # bearish
            # Bearish FVG is mitigated if price goes up into the gap
            return candle.high > self.top


class FVGDetector:
    """Detect Fair Value Gaps on 1H timeframe."""

    @staticmethod
    def detect_fvgs(hourly_candles: list[OHLCV]) -> list[FVG]:
        """
        Detect all FVGs from a list of hourly candles.

        FVGs are unmitigated gaps between consecutive candles:
        - Bullish FVG: Current candle's low > Previous candle's high (gap up)
        - Bearish FVG: Current candle's high < Previous candle's low (gap down)

        Args:
            hourly_candles: List of OHLCV candles (1H resolution)

        Returns:
            List of FVG objects (only unmitigated gaps)
        """
        fvgs = []

        for i in range(1, len(hourly_candles)):
            prev_candle = hourly_candles[i - 1]
            curr_candle = hourly_candles[i]

            # Bullish FVG: gap up
            if curr_candle.low > prev_candle.high:
                fvg = FVG(
                    detected_at=curr_candle.timestamp,
                    direction="bullish",
                    bottom=prev_candle.high,
                    top=curr_candle.low,
                    gap_size=(curr_candle.low - prev_candle.high) * 10000,  # Convert to pips
                )
                fvgs.append(fvg)

            # Bearish FVG: gap down
            elif curr_candle.high < prev_candle.low:
                fvg = FVG(
                    detected_at=curr_candle.timestamp,
                    direction="bearish",
                    bottom=curr_candle.high,
                    top=prev_candle.low,
                    gap_size=(prev_candle.low - curr_candle.high) * 10000,  # Convert to pips
                )
                fvgs.append(fvg)

        return fvgs

    @staticmethod
    def filter_unmitigated(fvgs: list[FVG], all_candles: list[OHLCV]) -> list[FVG]:
        """
        Filter FVGs to only include unmitigated ones (not yet filled).

        An FVG is mitigated when subsequent candles fill the gap zone.

        Args:
            fvgs: List of detected FVGs
            all_candles: All OHLCV candles to check for mitigation

        Returns:
            List of unmitigated FVGs
        """
        unmitigated = []

        for fvg in fvgs:
            is_mitigated = False

            # Check all candles after the FVG was detected
            for candle in all_candles:
                if candle.timestamp <= fvg.detected_at:
                    continue

                if fvg.is_mitigated_by_candle(candle):
                    is_mitigated = True
                    break

            if not is_mitigated:
                unmitigated.append(fvg)

        return unmitigated

    @staticmethod
    def get_active_fvgs_at_time(
        fvgs: list[FVG],
        reference_time: datetime,
    ) -> list[FVG]:
        """
        Get all FVGs that were active (detected) at or before a given time.

        Args:
            fvgs: List of FVG objects
            reference_time: Reference timestamp

        Returns:
            List of FVGs detected at or before reference_time
        """
        return [fvg for fvg in fvgs if fvg.detected_at <= reference_time]

    @staticmethod
    def find_fvg_for_price(
        price: float,
        fvgs: list[FVG],
        reference_time: Optional[datetime] = None,
    ) -> Optional[FVG]:
        """
        Find the FVG zone that contains a given price.

        If multiple FVGs contain the price, returns the most recent one.

        Args:
            price: Price level to check
            fvgs: List of FVG objects
            reference_time: Optional reference time for filtering

        Returns:
            FVG object if price is in a gap zone, None otherwise
        """
        matching_fvgs = []

        for fvg in fvgs:
            if reference_time and fvg.detected_at > reference_time:
                continue
            if fvg.contains_price(price):
                matching_fvgs.append(fvg)

        if not matching_fvgs:
            return None

        # Return most recent FVG
        return max(matching_fvgs, key=lambda f: f.detected_at)
