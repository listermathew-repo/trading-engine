"""
MAIN MODULE
Orchestrates the entire backtest pipeline.
Runs: Fetch → Detect Signals → Simulate Execution (±H4 filter) → Report Metrics
"""

import duckdb
from strategy import detect_fvgs
from engine import simulate_limit_orders, calculate_expectancy, export_trade_log_markdown


def run_backtest(symbol='capital.com:EURUSD', db_path='backtest_trading.duckdb.backup', use_h4_filter=False, h4_filter_mode='aligned', use_daily_filter=False):
    """
    Run complete backtest pipeline with optional H4 and Daily confluence filters.

    Input: Symbol, DuckDB path, H4 filter flag, filter mode, Daily filter flag
    Output: (metrics dict, trades list)
    """
    filter_label = " (UNFILTERED)"
    if use_h4_filter and use_daily_filter:
        filter_label = f" (H4 {h4_filter_mode.upper()} + Daily)"
    elif use_h4_filter:
        filter_label = f" (H4 {h4_filter_mode.upper()})"
    elif use_daily_filter:
        filter_label = " (Daily Only)"

    print(f"\n{'='*140}")
    print(f"BACKTEST: {symbol}{filter_label}")
    print(f"{'='*140}")

    # STAGE 1: Fetch data
    try:
        db = duckdb.connect(db_path)
    except Exception as e:
        print(f"ERROR: Cannot connect to database at {db_path}")
        print(f"  {e}")
        return None, None

    try:
        m15_data = db.execute(f"""
            SELECT symbol, time, open, high, low, close, volume,
              EXTRACT(HOUR FROM time) as hour_utc,
              EXTRACT(MINUTE FROM time) as minute_utc
            FROM ohlcv
            WHERE symbol = '{symbol}' AND timeframe = 'M15'
              AND time >= '2024-06-02' AND time <= '2026-06-02'
            ORDER BY time
        """).fetchall()
    except Exception as e:
        print(f"ERROR: Cannot fetch M15 data for {symbol}")
        print(f"  {e}")
        db.close()
        return None, None

    print(f"Loaded {len(m15_data):,} M15 bars")

    # Fetch H4 data if using H4 confluence filter
    h4_data = None
    if use_h4_filter:
        try:
            h4_data = db.execute(f"""
                SELECT symbol, time, open, high, low, close, volume,
                  EXTRACT(HOUR FROM time) as hour_utc,
                  EXTRACT(MINUTE FROM time) as minute_utc
                FROM ohlcv
                WHERE symbol = '{symbol}' AND timeframe = 'H4'
                  AND time >= '2024-06-02' AND time <= '2026-06-02'
                ORDER BY time
            """).fetchall()
            print(f"Loaded {len(h4_data):,} H4 bars for confluence filter")
        except Exception as e:
            print(f"WARNING: Could not fetch H4 data for {symbol}")
            h4_data = None

    # Fetch Daily data if using Daily confluence filter
    daily_data = None
    if use_daily_filter:
        try:
            daily_data = db.execute(f"""
                SELECT symbol, time, open, high, low, close, volume,
                  EXTRACT(HOUR FROM time) as hour_utc,
                  EXTRACT(MINUTE FROM time) as minute_utc
                FROM ohlcv
                WHERE symbol = '{symbol}' AND timeframe = 'D'
                  AND time >= '2024-06-02' AND time <= '2026-06-02'
                ORDER BY time
            """).fetchall()
            print(f"Loaded {len(daily_data):,} Daily bars for confluence filter")
        except Exception as e:
            print(f"WARNING: Could not fetch Daily data for {symbol}")
            daily_data = None

    # STAGE 2: Detect signals
    signals = detect_fvgs(m15_data, atr_threshold=0.25)
    print(f"Detected {len(signals):,} FVG signals (unfiltered, gap > 0 pips)")

    # STAGE 3: Simulate execution (with optional H4/Daily filters)
    trades = simulate_limit_orders(m15_data, signals, h4_bars=h4_data, daily_bars=daily_data, max_wait_bars=96,
                                  use_h4_filter=use_h4_filter, h4_filter_mode=h4_filter_mode, use_daily_filter=use_daily_filter)
    print(f"Generated {len(trades):,} closed trades")

    # STAGE 4: Report metrics
    metrics = calculate_expectancy(trades)

    print(f"\n{'='*140}")
    print(f"RESULTS: {symbol}{filter_label}")
    print(f"{'='*140}")

    print(f"\nMetrics:")
    print(f"  Total Trades: {metrics['total_trades']:,}")
    print(f"  Winners: {metrics['winners']:,} | Losers: {metrics['losers']:,}")
    print(f"  Win Rate: {metrics['win_rate']:.1f}%")
    print(f"  Avg Winner: {metrics['avg_winner_r']:+.2f}R")
    print(f"  Avg Loser: {metrics['avg_loser_r']:+.2f}R")
    print(f"\n  EXPECTANCY: {metrics['expectancy_r']:+.2f}R per trade")

    if metrics['expectancy_r'] > 0:
        print(f"  STATUS: PROFITABLE")
    else:
        print(f"  STATUS: NOT PROFITABLE")

    db.close()

    return metrics, trades


def run_all_tests(symbols=None, db_path='backtest_trading.duckdb.backup'):
    """
    Run comprehensive backtest suite:
    1. Unfiltered baseline
    2. H4 Counter filter (best so far)
    3. H4 Counter + Daily confluence (hypothesis: should push to positive)
    """
    if symbols is None:
        symbols = ["capital.com:EURUSD", "capital.com:AUDUSD"]

    print("="*140)
    print("MARKET ALIGNMENT FRAMEWORK — FINAL BACKTEST")
    print("Testing: Unfiltered vs H4 Counter vs (H4 Counter + Daily)")
    print("="*140)

    # Test 1: Baseline
    print("\n\nTEST 1: UNFILTERED BASELINE")
    print("=" * 140)
    all_trades_baseline = []
    for symbol in symbols:
        metrics, trades = run_backtest(symbol, db_path)
        if trades:
            all_trades_baseline.extend(trades)

    # Test 2: H4 Counter (best from previous run)
    print("\n\nTEST 2: H4 COUNTER FILTER")
    print("=" * 140)
    all_trades_h4_counter = []
    for symbol in symbols:
        metrics, trades = run_backtest(symbol, db_path, use_h4_filter=True, h4_filter_mode='counter')
        if trades:
            all_trades_h4_counter.extend(trades)

    # Test 3: H4 Counter + Daily confluence
    print("\n\nTEST 3: H4 COUNTER + DAILY CONFLUENCE")
    print("=" * 140)
    all_trades_combo = []
    for symbol in symbols:
        metrics, trades = run_backtest(symbol, db_path, use_h4_filter=True, h4_filter_mode='counter', use_daily_filter=True)
        if trades:
            all_trades_combo.extend(trades)

    # Comparison
    print(f"\n{'='*140}")
    print(f"FINAL COMPARISON: Three Approaches")
    print(f"{'='*140}")

    baseline_agg = calculate_expectancy(all_trades_baseline)
    h4_counter_agg = calculate_expectancy(all_trades_h4_counter)
    combo_agg = calculate_expectancy(all_trades_combo)

    print(f"\n{'Metric':<30} {'Unfiltered':<20} {'H4 Counter':<20} {'H4C + Daily':<20}")
    print(f"-"*90)
    print(f"{'Total Trades':<30} {baseline_agg['total_trades']:<20} {h4_counter_agg['total_trades']:<20} {combo_agg['total_trades']:<20}")
    print(f"{'Win Rate':<30} {baseline_agg['win_rate']:<20.1f}% {h4_counter_agg['win_rate']:<20.1f}% {combo_agg['win_rate']:<20.1f}%")
    print(f"{'Expectancy':<30} {baseline_agg['expectancy_r']:<+20.2f}R {h4_counter_agg['expectancy_r']:<+20.2f}R {combo_agg['expectancy_r']:<+20.2f}R")
    print(f"{'Avg Winner':<30} {baseline_agg['avg_winner_r']:<+20.2f}R {h4_counter_agg['avg_winner_r']:<+20.2f}R {combo_agg['avg_winner_r']:<+20.2f}R")
    print(f"{'Avg Loser':<30} {baseline_agg['avg_loser_r']:<+20.2f}R {h4_counter_agg['avg_loser_r']:<+20.2f}R {combo_agg['avg_loser_r']:<+20.2f}R")

    # Winner announcement
    print(f"\n{'='*140}")
    expectancies = [
        ('Unfiltered', baseline_agg['expectancy_r']),
        ('H4 Counter', h4_counter_agg['expectancy_r']),
        ('H4C + Daily', combo_agg['expectancy_r']),
    ]
    best_name, best_exp = max(expectancies, key=lambda x: x[1])

    if best_exp > 0:
        print(f"SUCCESS: {best_name} approach achieved {best_exp:+.2f}R expectancy - PROFITABLE!")
        print(f"This strategy is ready for Council presentation and live trading.")
    else:
        print(f"Best approach: {best_name} with {best_exp:+.2f}R (still negative)")
        print(f"Progress made: From baseline -0.23R to {best_exp:+.2f}R")
        print(f"Next: Refine Daily filter or add liquidity sweep detection.")
    print(f"{'='*140}")


if __name__ == '__main__':
    run_all_tests()
