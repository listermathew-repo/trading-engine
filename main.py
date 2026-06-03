"""
MAIN MODULE — ORCHESTRATION LAYER
Orchestrates the entire backtest pipeline using StrategyInterface.
Runs: Fetch → Strategy.generate_signals() → Strategy.filter_signals() → Engine.simulate_execution() → Report Metrics

This layer is strategy-agnostic: you can swap strategies without changing this code.
Supports profile-based configuration via YAML files in config/ directory.
"""

import duckdb
from typing import Dict, Tuple, List, Any, Optional
from strategy import MAFStrategy
from strategy_interface import StrategyInterface
from engine import simulate_limit_orders, calculate_expectancy
from config_loader import ConfigLoader


def run_backtest(
    symbol: str = 'capital.com:EURUSD',
    db_path: str = 'backtest_trading.duckdb.backup',
    strategy: Optional[StrategyInterface] = None,
    use_profile_config: bool = True,
    use_sweep_filter: Optional[bool] = None,
    use_bos_filter: Optional[bool] = None,
    use_h4_filter: Optional[bool] = None,
    h4_filter_mode: Optional[str] = None,
    use_daily_filter: Optional[bool] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]]]:
    """
    Run complete backtest pipeline using a pluggable strategy.

    Supports two configuration modes:
    1. Profile-based (default): Load symbol-specific config from YAML files
    2. Manual: Pass filter parameters directly

    Args:
        symbol: Trading pair (e.g., 'capital.com:EURUSD')
        db_path: Path to DuckDB file
        strategy: StrategyInterface implementation (defaults to MAFStrategy)
        use_profile_config: Load config from YAML profiles (default: True)
        use_sweep_filter: Override sweep filter setting
        use_bos_filter: Override BOS filter setting
        use_h4_filter: Override H4 filter setting
        h4_filter_mode: Override H4 filter mode ('aligned' or 'counter')
        use_daily_filter: Override daily filter setting

    Returns:
        (metrics dict, trades list) or (None, None) on error
    """
    # Load configuration
    filter_config = {}
    strategy_config = {
        'atr_threshold': 0.25,
        'atr_period': 14,
        'lookback': 8,
        'h4_ema_period': 20,
        'daily_lookback': 20,
    }

    if use_profile_config:
        # Load profile-based configuration
        loader = ConfigLoader()
        profile_config = loader.get_full_config(symbol)

        # Merge strategy config from profile
        if 'strategy' in profile_config:
            strategy_config.update(profile_config['strategy'])

        # Use filter config from profile
        if 'filters' in profile_config:
            filter_config = profile_config['filters'].copy()

    # Override with explicit parameters if provided
    if use_sweep_filter is not None:
        filter_config['use_sweep_filter'] = use_sweep_filter
    if use_bos_filter is not None:
        filter_config['use_bos_filter'] = use_bos_filter
    if use_h4_filter is not None:
        filter_config['use_h4_filter'] = use_h4_filter
    if h4_filter_mode is not None:
        filter_config['h4_filter_mode'] = h4_filter_mode
    if use_daily_filter is not None:
        filter_config['use_daily_filter'] = use_daily_filter

    # Set defaults if not loaded from profile or provided explicitly
    filter_config.setdefault('use_sweep_filter', False)
    filter_config.setdefault('use_bos_filter', False)
    filter_config.setdefault('use_h4_filter', False)
    filter_config.setdefault('h4_filter_mode', 'aligned')
    filter_config.setdefault('use_daily_filter', False)

    # Merge filter config into strategy config
    strategy_config.update(filter_config)

    # Use provided strategy or create default
    if strategy is None:
        strategy = MAFStrategy(strategy_config)

    # Format output label
    filter_parts = []
    if filter_config.get('use_sweep_filter'):
        filter_parts.append("Sweep")
    if filter_config.get('use_bos_filter'):
        filter_parts.append("BOS")
    if filter_config.get('use_h4_filter'):
        filter_parts.append(f"H4-{filter_config.get('h4_filter_mode', 'aligned').upper()}")
    if filter_config.get('use_daily_filter'):
        filter_parts.append("Daily")

    filter_label = " (UNFILTERED)"
    if filter_parts:
        filter_label = f" ({' + '.join(filter_parts)})"

    # Add profile indicator if loaded from config
    profile_indicator = ""
    if use_profile_config:
        loader = ConfigLoader()
        symbol_key = loader.get_symbol_from_config(symbol)
        profile_indicator = f" [Profile: {symbol_key}]"

    print(f"\n{'='*140}")
    print(f"BACKTEST: {symbol}{filter_label}{profile_indicator}")
    print(f"{'='*140}")

    # STAGE 1: Fetch data
    db = None
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
        if db:
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

    if db:
        db.close()

    # STAGE 2: Generate signals using strategy
    signals = strategy.generate_signals(m15_data)
    print(f"Detected {len(signals):,} FVG signals (unfiltered, gap > 0 pips)")

    # STAGE 3: Filter signals using strategy
    filter_context = {
        'bars': m15_data,
        'h4_bars': h4_data,
        'daily_bars': daily_data,
        'config': {
            'use_sweep_filter': use_sweep_filter,
            'use_bos_filter': use_bos_filter,
            'h4_filter_mode': h4_filter_mode,
            'use_daily_filter': use_daily_filter,
        }
    }
    # Apply filters if any are enabled
    should_filter = use_sweep_filter or use_bos_filter or use_h4_filter or use_daily_filter
    filtered_signals = strategy.filter_signals(signals, filter_context) if should_filter else signals

    # Report filtering results
    if should_filter and len(filtered_signals) < len(signals):
        reduction = (1 - len(filtered_signals) / len(signals)) * 100
        print(f"Applied filters: {len(filtered_signals):,} signals remain ({reduction:.1f}% filtered)")
    elif should_filter:
        print(f"Applied filters: {len(filtered_signals):,} signals remain (no reduction)")

    # STAGE 4: Execute trades via engine
    trades = simulate_limit_orders(
        m15_data,
        filtered_signals,
        h4_bars=h4_data,
        daily_bars=daily_data,
        max_wait_bars=96,
        use_h4_filter=use_h4_filter,
        h4_filter_mode=h4_filter_mode,
        use_daily_filter=use_daily_filter
    )
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

    return metrics, trades


def run_all_tests(
    symbols: Optional[List[str]] = None,
    db_path: str = 'backtest_trading.duckdb.backup',
    strategy: Optional[StrategyInterface] = None,
    use_profiles: bool = True,
) -> None:
    """
    Run comprehensive backtest suite using pluggable strategy and profile-based configs.

    Supports two modes:
    1. Profile-based (default): Load symbol-specific configs from config/ directory
    2. Manual: Run hardcoded test scenarios

    Args:
        symbols: List of symbols to test (defaults to EURUSD, AUDUSD)
        db_path: Path to DuckDB file
        strategy: StrategyInterface implementation (defaults to MAFStrategy)
        use_profiles: Load symbol-specific configurations from YAML profiles
    """
    if symbols is None:
        symbols = ["capital.com:EURUSD", "capital.com:AUDUSD"]

    if strategy is None:
        strategy = MAFStrategy()

    print("="*140)
    print("MARKET ALIGNMENT FRAMEWORK — COMPREHENSIVE BACKTEST")
    if use_profiles:
        print("Configuration: Profile-based (from config/ directory)")
    else:
        print("Configuration: Manual (hardcoded test scenarios)")
    print("="*140)

    if use_profiles:
        # Profile-based: Run with symbol-specific configurations
        print("\n\nTEST 1: SYMBOL-SPECIFIC PROFILES")
        print("=" * 140)
        all_trades_profiles = []
        for symbol in symbols:
            metrics, trades = run_backtest(symbol, db_path, strategy=strategy, use_profile_config=True)
            if trades:
                all_trades_profiles.extend(trades)

        profile_agg = calculate_expectancy(all_trades_profiles)
        print(f"\n{'='*140}")
        print(f"PROFILE-BASED RESULTS")
        print(f"{'='*140}")
        print(f"Total Trades: {profile_agg['total_trades']:,}")
        print(f"Win Rate: {profile_agg['win_rate']:.1f}%")
        print(f"EXPECTANCY: {profile_agg['expectancy_r']:+.2f}R per trade")
        if profile_agg['expectancy_r'] > 0:
            print(f"STATUS: PROFITABLE!")
        else:
            print(f"STATUS: NOT PROFITABLE (yet)")
        print(f"{'='*140}")
        return

    # Manual mode: Run hardcoded test scenarios
    # Test 1: Baseline (no filters)
    print("\n\nTEST 1: UNFILTERED BASELINE")
    print("=" * 140)
    all_trades_baseline = []
    for symbol in symbols:
        metrics, trades = run_backtest(symbol, db_path, strategy=strategy, use_profile_config=False)
        if trades:
            all_trades_baseline.extend(trades)

    # Test 2: H4 Counter filter (best approach so far)
    print("\n\nTEST 2: H4 COUNTER FILTER")
    print("=" * 140)
    all_trades_h4_counter = []
    for symbol in symbols:
        metrics, trades = run_backtest(
            symbol, db_path, strategy=strategy,
            use_profile_config=False,
            use_h4_filter=True, h4_filter_mode='counter'
        )
        if trades:
            all_trades_h4_counter.extend(trades)

    # Test 3: H4 Counter + Daily confluence
    print("\n\nTEST 3: H4 COUNTER + DAILY CONFLUENCE")
    print("=" * 140)
    all_trades_combo = []
    for symbol in symbols:
        metrics, trades = run_backtest(
            symbol, db_path, strategy=strategy,
            use_profile_config=False,
            use_h4_filter=True, h4_filter_mode='counter',
            use_daily_filter=True
        )
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
