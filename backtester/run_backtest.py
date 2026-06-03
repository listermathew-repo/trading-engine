"""Main backtest runner for Fair Value Gap strategy."""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from capital_data import CapitalDataClient, OHLCV
from fvg_detector import FVGDetector
from strategy import FVGStrategy, BacktestResults
from results import ResultsReporter


def aggregate_candles_to_hourly(minute15_candles: list[OHLCV]) -> list[OHLCV]:
    """
    Aggregate 15-minute candles into 1-hour candles.

    Args:
        minute15_candles: List of 15m OHLCV candles

    Returns:
        List of 1H OHLCV candles
    """
    if not minute15_candles:
        return []

    hourly_candles = []
    current_hour_candles = []
    last_hour = None

    for candle in minute15_candles:
        # Get the hour of this candle (rounded down)
        candle_hour = candle.timestamp.replace(minute=0, second=0, microsecond=0)

        # If we've moved to a new hour, aggregate the previous hour
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

    # Don't forget the last hour
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


def run_backtest_february() -> None:
    """
    Run backtest for EUR/USD February 2026.

    Data: 15-minute candles for all of February 2026 (Adelaide time 9am-10pm)
    FVG Detection: 1-hour timeframe
    Entries: 15-minute candle high of lowest red candle within FVG
    Stop Loss: Below swing low (test 5, 10, 20-candle lookback)
    Take Profit: 1R fixed
    """
    print("[INFO] Starting FVG Backtest for EUR/USD - February 2026")
    print("[INFO] Session: 9 a.m. - 10 p.m. Adelaide time (ACDT)")
    print()

    # Initialize Capital.com data client
    print("[INFO] Initializing Capital.com API connection...")
    try:
        data_client = CapitalDataClient()
        print("[OK] Connection successful")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Capital.com client: {e}")
        return

    # Fetch 15-minute data for February 2026
    # Note: Capital.com API may have limitations on historical data
    # Adjust start/end dates based on what's available
    print("[INFO] Fetching 15-minute OHLCV data for February 2026...")

    # February 2026: 1st to 28th
    start_date = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_date = datetime(2026, 2, 28, 23, 59, 59, tzinfo=timezone.utc)

    try:
        minute15_candles = data_client.get_price_history(
            epic="EURUSD",
            resolution="MINUTE_15",
            num_points=500,  # Fetch max available
        )

        if not minute15_candles:
            print("[ERROR] No data fetched from Capital.com")
            return

        print(f"[OK] Fetched {len(minute15_candles)} 15-minute candles")
        print(f"     Date range: {minute15_candles[0].timestamp} to {minute15_candles[-1].timestamp}")

    except Exception as e:
        print(f"[ERROR] Failed to fetch price history: {e}")
        return

    # Aggregate 15-minute candles to 1-hour candles for FVG detection
    print("[INFO] Aggregating 15-minute candles to 1-hour...")
    hourly_candles = aggregate_candles_to_hourly(minute15_candles)
    print(f"[OK] Generated {len(hourly_candles)} hourly candles")

    # Run the strategy backtest
    print("[INFO] Running FVG strategy backtest...")
    strategy = FVGStrategy(
        risk_per_trade=100.0,  # $100 per trade
        lookback_periods=[5, 10, 20],  # Test all swing lookback periods
    )

    results = strategy.backtest(hourly_candles, minute15_candles)

    if not results.trades:
        print("[WARN] No trades generated from backtest")
        return

    print(f"[OK] Backtest complete: {len(results.trades)} trades generated")

    # Export results to CSV
    print("[INFO] Exporting results to CSV...")
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)

    csv_file = output_dir / f"fvg_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        ResultsReporter.export_csv(results, csv_file)
        print(f"[OK] Results exported to: {csv_file}")
    except Exception as e:
        print(f"[ERROR] Failed to export CSV: {e}")

    # Print summary
    print()
    ResultsReporter.print_summary(results)

    # Analyze by swing lookback period
    lookback_analysis = ResultsReporter.analyze_by_lookback(results)
    ResultsReporter.print_lookback_analysis(lookback_analysis)

    # Analyze by session
    session_analysis = ResultsReporter.analyze_by_session(results)
    ResultsReporter.print_session_analysis(session_analysis)

    # Print top trades
    print()
    ResultsReporter.print_individual_trades(results, limit=20)

    # Save summary to text file
    summary_file = output_dir / f"fvg_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}_summary.txt"
    with open(summary_file, 'w') as f:
        f.write("FVG BACKTEST SUMMARY - EUR/USD February 2026\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Total Trades: {results.total_trades}\n")
        f.write(f"Winning Trades: {results.winning_trades}\n")
        f.write(f"Losing Trades: {results.losing_trades}\n")
        f.write(f"Non-Progressive Trades: {results.non_progressive_trades}\n\n")

        if results.total_trades > 0:
            f.write(f"Win Rate: {results.win_rate:.1%}\n")
            f.write(f"Total R: {results.total_r:+.2f}\n")
            f.write(f"Avg R per Trade: {results.avg_r_per_trade:+.2f}\n")
            f.write(f"Total PnL: ${results.total_pnl:+.2f}\n")
            f.write(f"Avg PnL per Trade: ${results.avg_pnl_per_trade:+.2f}\n\n")

        f.write("ANALYSIS BY SWING LOOKBACK PERIOD\n")
        f.write("-" * 80 + "\n\n")

        for lookback in sorted(lookback_analysis.keys()):
            stats = lookback_analysis[lookback]
            total = stats['total']

            if total > 0:
                win_rate = stats['wins'] / total
                avg_r = stats['total_r'] / total
                avg_pnl = stats['total_pnl'] / total

                f.write(f"{lookback}-Candle Swing Low:\n")
                f.write(f"  Trades: {total} | Wins: {stats['wins']} | Losses: {stats['losses']} | NP: {stats['non_progressive']}\n")
                f.write(f"  Win Rate: {win_rate:.1%}\n")
                f.write(f"  Total R: {stats['total_r']:+.2f} | Avg R: {avg_r:+.2f}\n")
                f.write(f"  Total PnL: ${stats['total_pnl']:+.2f} | Avg PnL: ${avg_pnl:+.2f}\n\n")

    print(f"\n[OK] Summary saved to: {summary_file}")


if __name__ == "__main__":
    run_backtest_february()
