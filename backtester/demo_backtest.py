"""
Demo backtest using synthetic data (no Capital.com API required).

This demonstrates the FVG strategy backtester on generated price data.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add backtester to path
sys.path.insert(0, str(Path(__file__).parent))

from capital_data import OHLCV
from strategy import FVGStrategy
from results import ResultsReporter


def generate_synthetic_data(num_candles: int = 500) -> list[OHLCV]:
    """
    Generate synthetic EUR/USD price data with FVG opportunities.

    Creates realistic price movement with gaps for FVG detection.
    """
    import random
    random.seed(42)  # For reproducibility

    candles = []
    base_time = datetime(2026, 2, 1, 9, 0, 0, tzinfo=timezone.utc)
    price = 1.0800

    for i in range(num_candles):
        timestamp = base_time + timedelta(minutes=15 * i)

        # Generate movement
        movement = random.gauss(0, 0.0003)  # Small random walk
        open_price = price
        close_price = price + movement

        # Create gaps (for FVG detection) - increased probability
        if random.random() < 0.25:  # 25% chance of gap (increased from 15%)
            gap_direction = random.choice([1, -1])
            gap_size = random.uniform(0.0005, 0.0012) * gap_direction  # Larger gaps
            open_price = price + gap_size
            close_price = open_price + random.gauss(0, 0.0002)

        # High and low
        if open_price > close_price:
            high = open_price + random.uniform(0.0001, 0.0003)
            low = close_price - random.uniform(0, 0.0002)
        else:
            high = close_price + random.uniform(0, 0.0002)
            low = open_price - random.uniform(0.0001, 0.0003)

        # Ensure OHLC integrity
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)

        candles.append(OHLCV(
            timestamp=timestamp,
            open=open_price,
            high=high,
            low=low,
            close=close_price,
            volume=random.randint(500, 5000),
        ))

        price = close_price

    return candles


def aggregate_to_hourly(candles: list[OHLCV]) -> list[OHLCV]:
    """Aggregate 15-minute candles to 1-hour candles."""
    if not candles:
        return []

    hourly_candles = []
    current_hour_candles = []
    last_hour = None

    for candle in candles:
        candle_hour = candle.timestamp.replace(minute=0, second=0, microsecond=0)

        if last_hour is not None and candle_hour != last_hour:
            if current_hour_candles:
                hourly_candle = OHLCV(
                    timestamp=last_hour,
                    open=current_hour_candles[0].open,
                    high=max(c.high for c in current_hour_candles),
                    low=min(c.low for c in current_hour_candles),
                    close=current_hour_candles[-1].close,
                    volume=sum(c.volume for c in current_hour_candles),
                )
                hourly_candles.append(hourly_candle)

            current_hour_candles = []

        current_hour_candles.append(candle)
        last_hour = candle_hour

    if current_hour_candles:
        hourly_candle = OHLCV(
            timestamp=last_hour,
            open=current_hour_candles[0].open,
            high=max(c.high for c in current_hour_candles),
            low=min(c.low for c in current_hour_candles),
            close=current_hour_candles[-1].close,
            volume=sum(c.volume for c in current_hour_candles),
        )
        hourly_candles.append(hourly_candle)

    return hourly_candles


def main():
    """Run demo backtest."""
    print("[INFO] FVG Backtest Demo (Synthetic Data)")
    print("[INFO] " + "=" * 70)
    print()

    # Generate synthetic data
    print("[INFO] Generating synthetic EUR/USD 15-minute data...")
    minute15_candles = generate_synthetic_data(num_candles=500)
    print(f"[OK] Generated {len(minute15_candles)} candles")
    print(f"     Date range: {minute15_candles[0].timestamp} to {minute15_candles[-1].timestamp}")
    print()

    # Aggregate to hourly
    print("[INFO] Aggregating to 1-hour timeframe...")
    hourly_candles = aggregate_to_hourly(minute15_candles)
    print(f"[OK] Generated {len(hourly_candles)} hourly candles")
    print()

    # Check for FVGs
    print("[INFO] Detecting FVGs on 1-hour timeframe...")
    from fvg_detector import FVGDetector
    detected_fvgs = FVGDetector.detect_fvgs(hourly_candles)
    print(f"[INFO] Detected {len(detected_fvgs)} FVGs")
    unmitigated_fvgs = FVGDetector.filter_unmitigated(detected_fvgs, minute15_candles)
    print(f"[INFO] {len(unmitigated_fvgs)} are unmitigated")
    if unmitigated_fvgs:
        for fvg in unmitigated_fvgs[:5]:
            print(f"       {fvg}")
    print()

    # Run strategy
    print("[INFO] Running FVG strategy backtest...")
    strategy = FVGStrategy(
        risk_per_trade=100.0,
        lookback_periods=[5, 10, 20],
    )

    results = strategy.backtest(hourly_candles, minute15_candles)
    print(f"[OK] Backtest complete: {len(results.trades)} trades generated")
    print()

    # Print results
    if results.trades:
        print("[INFO] Results Summary:")
        print()
        ResultsReporter.print_summary(results)
        print()

        # Analysis by lookback
        lookback_analysis = ResultsReporter.analyze_by_lookback(results)
        ResultsReporter.print_lookback_analysis(lookback_analysis)
        print()

        # Analysis by session
        session_analysis = ResultsReporter.analyze_by_session(results)
        ResultsReporter.print_session_analysis(session_analysis)
        print()

        # Sample trades
        ResultsReporter.print_individual_trades(results, limit=10)

    else:
        print("[WARN] No trades generated from backtest")
        print("[INFO] This may indicate:")
        print("       - No FVGs detected in the data")
        print("       - No trades within session window")
        print("       - No red candles within FVG zones")
        print()

    print("[INFO] Demo complete!")
    print()


if __name__ == "__main__":
    main()
