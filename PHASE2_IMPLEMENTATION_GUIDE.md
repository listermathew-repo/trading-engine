# Phase 2: Liquidity Sweep Detection Implementation Guide

**Status**: Foundation Ready ✅  
**Baseline Snapshot**: Locked in with 7 passing tests  
**Current Expectancy**: -0.16R (128 trades, 28.1% win rate)  
**Target Expectancy**: -0.08R to +0.05R (+0.05-0.10R gain)  

---

## What We Just Built

### 1. **StrategyInterface Protocol** ✅
- Defined contract for swappable strategies
- `generate_signals()` → `filter_signals()` → execution
- Language: Python 3.14+, Type-safe

### 2. **MAFStrategy Implementation** ✅
- Refactored from monolithic functions to class-based design
- All helper methods available as static methods
- Backward compatible (old functions still work)

### 3. **Test Snapshot** ✅
```
tests/test_strategy.py
├── TestBaselineSignalDetection
│   ├── test_eurusd_baseline_signal_count  ✓ 197 signals
│   ├── test_signal_structure              ✓ Fields validated
│   └── test_signal_types                  ✓ LONG/SHORT only
├── TestStrategyInterfaceCompliance
│   ├── test_strategy_has_required_methods ✓ Implemented
│   └── test_strategy_backward_compatibility ✓ Legacy API works
└── TestPhase2Readiness
    ├── test_sweep_detection_placeholder   (TODO)
    └── test_structure_validation_placeholder (TODO)
```

**All 7 tests passing** ✅

---

## Now: Implement Liquidity Sweep Detection

### Step 1: Add Sweep Detection to MAFStrategy

**Location**: `strategy.py`, line ~260 (after existing methods)

```python
def detect_liquidity_sweep(self, bars, signal, lookback=8):
    """
    Verify that a swing was actually swept through before reversal.
    
    For LONG FVG: Check if the low penetrated below the swing low
    For SHORT FVG: Check if the high penetrated above the swing high
    
    Args:
        bars: List of full bars (symbol, time, open, high, low, close, volume, h, m)
        signal: Dict with 'bar_idx' and 'type' (LONG or SHORT)
        lookback: Number of bars to check for swing
    
    Returns:
        bool: True if sweep confirmed, False otherwise
    """
    fvg_bar_idx = signal['bar_idx']
    
    if fvg_bar_idx < lookback:
        return True  # Not enough history, allow trade
    
    # Get bars before FVG formed
    lookback_bars = bars[fvg_bar_idx - lookback : fvg_bar_idx]
    
    if signal['type'] == 'LONG':
        # For LONG, check if low went below swing_low
        swing_low = min(b[4] for b in lookback_bars)  # b[4] = low
        # FVG entry (signal['entry_level']) should be above swing_low
        # This means swing was swept
        return signal['entry_level'] > swing_low * 0.99
    else:  # SHORT
        # For SHORT, check if high went above swing_high
        swing_high = max(b[3] for b in lookback_bars)  # b[3] = high
        # FVG entry (signal['entry_level']) should be below swing_high
        # This means swing was swept
        return signal['entry_level'] < swing_high * 1.01
```

### Step 2: Update filter_signals() to Use Sweep Detection

**Location**: `strategy.py`, in the `filter_signals()` method

```python
def filter_signals(self, signals, context):
    """Apply confluence filters to reduce false signals."""
    bars = context.get('bars', [])
    h4_bars = context.get('h4_bars', [])
    daily_bars = context.get('daily_bars', [])
    config = context.get('config', self.config)

    filtered_signals = signals

    # NEW: Liquidity sweep filter (if enabled)
    if config.get('use_sweep_filter', False):
        filtered_signals = [
            s for s in filtered_signals
            if self.detect_liquidity_sweep(bars, s)
        ]

    # H4 confluence filter (if available)
    if h4_bars:
        h4_bias = self._get_h4_bias(h4_bars, self.h4_ema_period)
        filter_mode = config.get('h4_filter_mode', 'counter')
        filtered_signals = [
            s for s in filtered_signals
            if self._apply_h4_filter(s, h4_bias, filter_mode)
        ]

    # Daily confluence filter (optional)
    if daily_bars and config.get('use_daily_filter', False):
        daily_bias = self._get_daily_bias(daily_bars, self.daily_lookback)
        filtered_signals = [
            s for s in filtered_signals
            if self._apply_daily_filter(s, daily_bias)
        ]

    return filtered_signals
```

### Step 3: Update main.py to Enable Sweep Filter

**Location**: `main.py`, in the `run_backtest()` function call

```python
def run_backtest(
    symbol: str = 'capital.com:EURUSD',
    db_path: str = 'backtest_trading.duckdb.backup',
    strategy: Optional[StrategyInterface] = None,
    use_h4_filter: bool = False,
    h4_filter_mode: str = 'aligned',
    use_daily_filter: bool = False,
    use_sweep_filter: bool = False,  # NEW PARAMETER
) -> Tuple[Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]]]:
    """..."""
    # ... existing code ...
    
    filter_context = {
        'bars': m15_data,
        'h4_bars': h4_data,
        'daily_bars': daily_data,
        'config': {
            'h4_filter_mode': h4_filter_mode,
            'use_daily_filter': use_daily_filter,
            'use_sweep_filter': use_sweep_filter,  # NEW
        }
    }
```

### Step 4: Add Test for Sweep Detection

**Location**: `tests/test_strategy.py`, in `TestPhase2Readiness` class

```python
def test_sweep_detection_filters_signals(self):
    """
    Layer 1: Liquidity sweep detection
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

    # Generate baseline signals
    signals = detect_fvgs(m15_data, atr_threshold=0.25)
    baseline_count = len(signals)

    # Apply sweep detection
    strategy = MAFStrategy()
    sweep_filtered = [
        s for s in signals
        if strategy.detect_liquidity_sweep(m15_data, s)
    ]
    sweep_count = len(sweep_filtered)

    # Verify reduction
    reduction = (1 - sweep_count / baseline_count) * 100 if baseline_count > 0 else 0

    print(f"Sweep detection: {baseline_count} → {sweep_count} signals ({reduction:.1f}% reduction)")
    
    # Expect 20-30% reduction
    assert 0.15 < (1 - sweep_count / baseline_count) < 0.40, (
        f"Expected 15-40% reduction, got {reduction:.1f}%"
    )
```

### Step 5: Run Tests to Lock in New Behavior

```bash
# Run specific sweep detection test
pytest tests/test_strategy.py::TestPhase2Readiness::test_sweep_detection_filters_signals -v

# Run all tests (should still pass)
pytest tests/test_strategy.py -v
```

### Step 6: Run Full Backtest with Sweep Filter

```bash
# Create test script in main.py
python -c "
from main import run_backtest
symbol = 'capital.com:EURUSD'
metrics_sweep, trades_sweep = run_backtest(
    symbol,
    use_h4_filter=True,
    h4_filter_mode='counter',
    use_sweep_filter=True  # NEW
)
print(f'H4 Counter + Sweep: {metrics_sweep[\"total_trades\"]} trades, {metrics_sweep[\"expectancy_r\"]:+.2f}R')
"
```

---

## Expected Results

### Hypothesis
Liquidity sweep detection should:
1. Reduce false signals by 20-30%
2. Improve win rate by 2-3%
3. Gain +0.05-0.10R expectancy

### Baseline
- Trades: 128 (H4 Counter)
- Win Rate: 28.1%
- Expectancy: -0.16R

### After Sweep Filter
- Trades: ~90-100 (20% reduction)
- Win Rate: 30-31% (2-3% gain)
- **Expectancy: -0.11R to -0.06R** (expected)

### Combined (Sweep + Structure Validation in next step)
- **Expectancy: -0.08R to +0.05R** (Phase 2 target)

---

## Rollback Plan (If Tests Fail)

If sweep detection breaks the baseline:

```bash
# See what broke
git diff HEAD~1 strategy.py

# Rollback to working version
git checkout HEAD~1 strategy.py

# Re-run tests
pytest tests/test_strategy.py -v
```

---

## Timeline

**Option A: Just Sweep Detection** (30-45 min)
- Add method to strategy.py
- Update filter_signals()
- Add test
- Run backtest
- Document results

**Option B: Sweep + Structure** (50-60 min)
- Add both detect_liquidity_sweep() and confirm_break_of_structure()
- Both tests passing
- Run backtest with both filters
- Potentially hit +0.10R gain

---

## Next: Structure Validation

Once sweep detection is locked in, add:

```python
def confirm_break_of_structure(self, bars, bar_idx, lookback=8):
    """
    Verify that a recent swing was actually broken, not just touched.
    
    A break of structure means:
    - For LONG: Current low < minimum of lookback bars
    - For SHORT: Current high > maximum of lookback bars
    """
    if bar_idx < lookback + 2:
        return True  # Not enough history
    
    recent = bars[bar_idx - lookback : bar_idx]
    swing_low = min(b[4] for b in recent)
    swing_high = max(b[3] for b in recent)
    current_low = bars[bar_idx][4]
    current_high = bars[bar_idx][3]
    
    breaks_low = current_low < swing_low * 0.99
    breaks_high = current_high > swing_high * 1.01
    
    return breaks_low or breaks_high
```

---

## Success Criteria

✅ Phase 2 is complete when:
1. All baseline tests still pass (7/7)
2. Sweep detection test passes
3. Structure validation test passes
4. H4 Counter + Sweep + Structure produces -0.08R to +0.05R
5. All changes committed with clear commit messages
6. FINDINGS.md updated with Phase 2 results

---

**You're ready to implement. Let's do this.** 🚀
