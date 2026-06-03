"""Unit tests for backtester module."""

import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtester.capital_data import OHLCV
from backtester.fvg_detector import FVG, FVGDetector
from backtester.swing_detector import SwingDetector
from backtester.strategy import FVGStrategy, BacktestTrade, TradeStatus


@pytest.fixture
def sample_15m_candles():
    """Create sample 15-minute candles."""
    base_time = datetime(2026, 2, 1, 9, 0, 0, tzinfo=timezone.utc)
    candles = []

    prices = [
        (1.0800, 1.0820, 1.0795, 1.0810),  # 0
        (1.0810, 1.0825, 1.0805, 1.0815),  # 1
        (1.0815, 1.0830, 1.0810, 1.0825),  # 2 - high = 1.0830
        (1.0840, 1.0850, 1.0835, 1.0840),  # 3 - gap up! low (1.0835) > prev high (1.0830)
        (1.0840, 1.0845, 1.0828, 1.0830),  # 4 - red candle (close < open)
        (1.0830, 1.0840, 1.0815, 1.0820),  # 5 - red candle
        (1.0820, 1.0850, 1.0810, 1.0840),  # 6 - green, TP hit?
        (1.0840, 1.0860, 1.0835, 1.0850),  # 7
        (1.0850, 1.0855, 1.0840, 1.0845),  # 8
        (1.0845, 1.0850, 1.0825, 1.0830),  # 9
    ]

    for i, (o, h, l, c) in enumerate(prices):
        candles.append(OHLCV(
            timestamp=base_time + timedelta(minutes=15 * i),
            open=o,
            high=h,
            low=l,
            close=c,
            volume=1000 + i * 100,
        ))

    return candles


@pytest.fixture
def sample_1h_candles():
    """Create sample 1-hour candles."""
    base_time = datetime(2026, 2, 1, 9, 0, 0, tzinfo=timezone.utc)
    candles = []

    prices = [
        (1.0800, 1.0830, 1.0795, 1.0825),  # Hour 1
        (1.0825, 1.0850, 1.0820, 1.0835),  # Hour 2 - gap up to 1.0850
        (1.0835, 1.0860, 1.0815, 1.0840),  # Hour 3
        (1.0840, 1.0845, 1.0810, 1.0820),  # Hour 4
    ]

    for i, (o, h, l, c) in enumerate(prices):
        candles.append(OHLCV(
            timestamp=base_time + timedelta(hours=i),
            open=o,
            high=h,
            low=l,
            close=c,
            volume=4000 + i * 400,
        ))

    return candles


class TestFVGDetector:
    """Test FVG detection."""

    def test_detect_bullish_fvg(self, sample_15m_candles):
        """Test detection of bullish FVG (gap up)."""
        # Use 15m candles for testing (they already have a gap at index 2->3)
        fvgs = FVGDetector.detect_fvgs(sample_15m_candles)

        # Should detect at least one bullish FVG
        bullish_fvgs = [f for f in fvgs if f.direction == "bullish"]
        assert len(bullish_fvgs) > 0

        # Check FVG properties
        fvg = bullish_fvgs[0]
        assert fvg.bottom == 1.0830  # Previous candle high
        assert fvg.top == 1.0835     # Current candle low
        assert fvg.gap_size > 0

    def test_filter_unmitigated(self, sample_1h_candles):
        """Test filtering unmitigated FVGs."""
        fvgs = FVGDetector.detect_fvgs(sample_1h_candles)
        unmitigated = FVGDetector.filter_unmitigated(fvgs, sample_1h_candles)

        # Some FVGs may be mitigated, others not
        assert len(unmitigated) <= len(fvgs)

    def test_fvg_contains_price(self):
        """Test FVG price containment check."""
        fvg = FVG(
            detected_at=datetime.now(timezone.utc),
            direction="bullish",
            bottom=1.0800,
            top=1.0850,
            gap_size=50,
        )

        assert fvg.contains_price(1.0825)
        assert fvg.contains_price(1.0800)
        assert fvg.contains_price(1.0850)
        assert not fvg.contains_price(1.0751)
        assert not fvg.contains_price(1.0851)


class TestSwingDetector:
    """Test swing low detection."""

    def test_find_swing_low(self, sample_15m_candles):
        """Test finding swing low."""
        swing_low = SwingDetector.find_swing_low(sample_15m_candles, lookback=5)

        # Should return the lowest low in last 5 candles
        assert swing_low is not None
        assert isinstance(swing_low, float)

    def test_find_swing_low_multiple_lookbacks(self, sample_15m_candles):
        """Test finding swing lows for multiple lookback periods."""
        swings = SwingDetector.find_multiple_swing_lows(
            sample_15m_candles,
            lookback_periods=[5, 10, 20]
        )

        assert len(swings) == 3
        assert all(isinstance(v, (float, type(None))) for v in swings.values())

    def test_is_red_candle(self, sample_15m_candles):
        """Test red candle detection."""
        # Candle at index 4 should be red (close < open)
        candle = sample_15m_candles[4]
        assert SwingDetector.is_red_candle(candle)

    def test_find_lowest_red_candle(self, sample_15m_candles):
        """Test finding lowest red candle in range."""
        idx = SwingDetector.find_lowest_red_candle_in_range(
            sample_15m_candles, 3, 6
        )

        # Should find a red candle index
        assert idx is not None
        assert sample_15m_candles[idx].close < sample_15m_candles[idx].open


class TestFVGStrategy:
    """Test FVG strategy."""

    def test_is_in_session_window(self):
        """Test session window check."""
        # 9 a.m. Adelaide time = ~10:30 p.m. UTC (previous day)
        # Need to be careful with timezone conversion

        utc_time = datetime(2026, 2, 1, 10, 30, 0, tzinfo=timezone.utc)
        assert FVGStrategy.is_in_session_window(utc_time, session_start_hour=9, session_end_hour=22)

    def test_classify_session(self):
        """Test session classification."""
        # London Open: ~8:00 UTC
        london_open = datetime(2026, 2, 1, 8, 0, 0, tzinfo=timezone.utc)
        session = FVGStrategy.classify_session(london_open)
        assert session.value == "london_open"

    def test_backtest_with_sample_data(self, sample_1h_candles, sample_15m_candles):
        """Test backtest execution."""
        strategy = FVGStrategy(
            risk_per_trade=100.0,
            lookback_periods=[5, 10],
        )

        results = strategy.backtest(sample_1h_candles, sample_15m_candles)

        # Should complete without errors
        assert results is not None
        assert isinstance(results.total_trades, int)
        assert results.total_trades >= 0


class TestAdelaideTimeConversion:
    """Test Adelaide timezone conversion."""

    def test_adelaide_time_conversion(self):
        """Test converting UTC to Adelaide time."""
        # 2026-02-01 10:30:00 UTC = 2026-02-01 21:00:00 ACDT (UTC+10:30)
        utc_time = datetime(2026, 2, 1, 10, 30, 0, tzinfo=timezone.utc)
        adelaide_time = FVGStrategy.to_adelaide_time(utc_time)

        assert adelaide_time.hour == 21
        assert adelaide_time.minute == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
