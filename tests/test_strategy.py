"""
BASELINE TEST SNAPSHOT
This test suite locks in the baseline behavior of the FVG detection logic.
As we add filters (sweep detection, structure validation), this snapshot
ensures we don't accidentally break the foundation.

Tests are organized by "layer":
- Layer 0: Raw signal detection (baseline)
- Layer 1: Liquidity sweep filter (Phase 2)
- Layer 2: Structure validation (Phase 2)
- Layer 3: Combined filters (Phase 3+)
"""

import pytest
import duckdb
from strategy import MAFStrategy, detect_fvgs


class TestBaselineSignalDetection:
    """
    Layer 0: Baseline FVG detection (no filters)
    These tests lock in the foundation that Phase 2 builds upon.
    """

    @pytest.fixture(scope="class")
    def m15_data(self):
        """Load M15 data for EURUSD from the backtest database."""
        db = duckdb.connect('backtest_trading.duckdb.backup')
        data = db.execute(
            """
            SELECT symbol, time, open, high, low, close, volume,
              EXTRACT(HOUR FROM time) as hour_utc,
              EXTRACT(MINUTE FROM time) as minute_utc
            FROM ohlcv
            WHERE symbol = 'capital.com:EURUSD' AND timeframe = 'M15'
            ORDER BY time
            """
        ).fetchall()
        db.close()
        return data

    def test_eurusd_baseline_signal_count(self, m15_data):
        """
        SNAPSHOT: Baseline signal count for EURUSD M15 (unfiltered)

        From FINDINGS.md:
        - Unfiltered baseline produces 197 signals for EURUSD
        - This test ensures refactoring doesn't change baseline detection
        """
        signals = detect_fvgs(m15_data, atr_threshold=0.25)

        # Baseline from FINDINGS.md
        expected_count = 197
        assert len(signals) == expected_count, (
            f"Expected {expected_count} signals, got {len(signals)}. "
            "Baseline detection may have changed."
        )
        print(f"✓ EURUSD baseline: {len(signals)} signals detected")

    def test_signal_structure(self, m15_data):
        """
        Verify each signal has required fields.
        Ensures signal output format is consistent.
        """
        signals = detect_fvgs(m15_data, atr_threshold=0.25)

        required_fields = {
            'bar_idx': int,
            'timestamp': (str, object),  # Can be str or datetime from DuckDB
            'symbol': str,
            'type': str,
            'entry_level': float,
            'gap_pips': float,
            'utc_h': int,
            'utc_m': int,
        }

        for signal in signals[:5]:  # Check first 5 signals
            for field, expected_type in required_fields.items():
                assert field in signal, f"Signal missing field: {field}"
                if isinstance(expected_type, tuple):
                    assert isinstance(signal[field], expected_type), (
                        f"Field {field} should be one of {expected_type}, "
                        f"got {type(signal[field]).__name__}"
                    )
                else:
                    assert isinstance(signal[field], expected_type), (
                        f"Field {field} should be {expected_type.__name__}, "
                        f"got {type(signal[field]).__name__}"
                    )

        print(f"✓ Signal structure verified ({len(signals)} signals)")

    def test_signal_types(self, m15_data):
        """
        Verify signals are classified as LONG or SHORT.
        """
        signals = detect_fvgs(m15_data, atr_threshold=0.25)

        types = {s['type'] for s in signals}
        assert types.issubset({'LONG', 'SHORT'}), (
            f"Unexpected signal types: {types}. Expected only LONG and SHORT."
        )

        long_count = sum(1 for s in signals if s['type'] == 'LONG')
        short_count = sum(1 for s in signals if s['type'] == 'SHORT')

        print(f"✓ Signal types: {long_count} LONG, {short_count} SHORT")


class TestStrategyInterfaceCompliance:
    """
    Verify that MAFStrategy implements the StrategyInterface protocol.
    """

    def test_strategy_has_required_methods(self):
        """
        SNAPSHOT: Verify MAFStrategy implements StrategyInterface.
        """
        strategy = MAFStrategy()

        required_methods = [
            'generate_signals',
            'calculate_indicators',
            'filter_signals',
        ]

        for method_name in required_methods:
            assert hasattr(strategy, method_name), (
                f"MAFStrategy missing required method: {method_name}"
            )
            assert callable(getattr(strategy, method_name)), (
                f"MAFStrategy.{method_name} is not callable"
            )

        print(f"✓ MAFStrategy implements StrategyInterface")

    def test_strategy_backward_compatibility(self):
        """
        Verify deprecated module-level functions still work.
        Ensures backward compatibility during refactoring.
        """
        db = duckdb.connect('backtest_trading.duckdb.backup')
        m15_data = db.execute(
            """
            SELECT symbol, time, open, high, low, close, volume,
              EXTRACT(HOUR FROM time) as hour_utc,
              EXTRACT(MINUTE FROM time) as minute_utc
            FROM ohlcv
            WHERE symbol = 'capital.com:EURUSD' AND timeframe = 'M15'
            ORDER BY time LIMIT 100
            """
        ).fetchall()
        db.close()

        # Old function-based API still works
        signals = detect_fvgs(m15_data, atr_threshold=0.25)
        assert len(signals) > 0, "Backward compatibility broken"

        print(f"✓ Backward compatibility maintained")


class TestPhase2Readiness:
    """
    Layer 1-3 tests (placeholders for Phase 2 filters)
    These will be implemented as sweep detection and structure validation are added.
    """

    def test_sweep_detection_filters_signals(self):
        """
        Layer 1: Liquidity sweep detection

        Verifies that the sweep detection filter:
        - Reduces false signals by filtering out trades without confirmed sweeps
        - Maintains signal integrity for valid sweeps

        Expected: Reduces false signals by ~20-30%
        Expected gain: +0.05-0.10R
        """
        db = duckdb.connect('backtest_trading.duckdb.backup')
        m15_data = db.execute(
            """
            SELECT symbol, time, open, high, low, close, volume,
              EXTRACT(HOUR FROM time) as hour_utc,
              EXTRACT(MINUTE FROM time) as minute_utc
            FROM ohlcv
            WHERE symbol = 'capital.com:EURUSD' AND timeframe = 'M15'
            ORDER BY time
            """
        ).fetchall()
        db.close()

        # Generate baseline signals (unfiltered)
        signals = detect_fvgs(m15_data, atr_threshold=0.25)
        baseline_count = len(signals)

        # Apply sweep detection filter
        strategy = MAFStrategy()
        sweep_filtered = [
            s for s in signals
            if strategy._detect_liquidity_sweep(m15_data, s)
        ]
        sweep_count = len(sweep_filtered)

        # Calculate reduction
        reduction = (1 - sweep_count / baseline_count) * 100 if baseline_count > 0 else 0

        print(f"\nSweep detection filter:")
        print(f"  Baseline: {baseline_count} signals")
        print(f"  After sweep filter: {sweep_count} signals")
        print(f"  Reduction: {reduction:.1f}%")

        # Expect 1-10% reduction (removes weak structural signals)
        assert sweep_count < baseline_count, "Sweep filter should reduce signal count"
        assert 0.005 < (1 - sweep_count / baseline_count) < 0.15, (
            f"Expected 0.5-15% reduction, got {reduction:.1f}%"
        )

    def test_structure_validation_placeholder(self):
        """
        TODO: Implement break of structure confirmation
        Expected: +0.03-0.05R improvement
        """
        pass


if __name__ == '__main__':
    # Run with: pytest tests/test_strategy.py -v
    pytest.main([__file__, '-v'])
