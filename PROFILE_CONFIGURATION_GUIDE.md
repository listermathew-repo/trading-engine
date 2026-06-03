# Profile-Based Configuration System

**Date**: June 3, 2026  
**Status**: IMPLEMENTED ✓  
**Purpose**: Replace CLI arguments with symbol-specific YAML configuration profiles

---

## Overview

The profile-based configuration system allows symbol-specific trading parameters to be managed in YAML files rather than command-line arguments. This enables:

- **Symbol-specific optimization**: Different filters for EURUSD vs AUDUSD
- **Reproducibility**: Configurations are version-controlled and consistent
- **Scalability**: Easy to add new symbols and their optimal settings
- **Maintainability**: Central location for all trading parameters

---

## Directory Structure

```
maf_backtest_v1/
├── config/
│   ├── default.yaml          # Default/fallback configuration
│   ├── eurusd.yaml           # EURUSD-specific profile
│   └── audusd.yaml           # AUDUSD-specific profile
├── config_loader.py          # Configuration loader utility
└── main.py                   # Updated to load profiles
```

---

## Configuration Files

### EURUSD Profile (`config/eurusd.yaml`)

```yaml
symbol: capital.com:EURUSD
description: "Euro vs US Dollar - H4 Counter biased approach"

strategy:
  atr_threshold: 0.25
  atr_period: 14
  lookback: 8
  h4_ema_period: 20
  daily_lookback: 20

filters:
  use_sweep_filter: true         # Modest positive impact
  use_bos_filter: false          # Disabled
  use_h4_filter: true            # H4 Counter enabled
  h4_filter_mode: counter        # Trade reversals
  use_daily_filter: false        # Not needed

expectations:
  expectancy: -0.25R
  trades: 44
  win_rate: 25.0%
```

### AUDUSD Profile (`config/audusd.yaml`)

```yaml
symbol: capital.com:AUDUSD
description: "Australian Dollar - Sweep + H4 Counter optimized"

strategy:
  atr_threshold: 0.25
  atr_period: 14
  lookback: 8
  h4_ema_period: 20
  daily_lookback: 20

filters:
  use_sweep_filter: true         # HIGHLY EFFECTIVE (+0.12R!)
  use_bos_filter: false          # Disabled
  use_h4_filter: true            # H4 Counter enabled
  h4_filter_mode: counter        # Trade reversals
  use_daily_filter: false        # Not needed

expectations:
  expectancy: -0.07R
  trades: 81
  win_rate: 30.9%
```

### Default Profile (`config/default.yaml`)

Fallback configuration for symbols without specific profiles. Conservative settings with H4 Counter only.

---

## Usage

### Using Profile-Based Configuration (Default)

```bash
# Automatically loads config from eurusd.yaml
python -c "from main import run_backtest; run_backtest('capital.com:EURUSD')"

# Or in code:
from main import run_backtest
metrics, trades = run_backtest('capital.com:EURUSD', use_profile_config=True)
```

### Overriding Profile Settings

```bash
# Load profile but override sweep filter
from main import run_backtest
metrics, trades = run_backtest(
    'capital.com:EURUSD',
    use_profile_config=True,
    use_sweep_filter=False  # Override profile setting
)
```

### Manual Configuration (Legacy)

```bash
# Disable profile loading and use direct parameters
from main import run_backtest
metrics, trades = run_backtest(
    'capital.com:EURUSD',
    use_profile_config=False,
    use_h4_filter=True,
    h4_filter_mode='counter'
)
```

### Profile-Based Test Suite

```bash
# Run tests with symbol-specific profiles
python -c "from main import run_all_tests; run_all_tests(use_profiles=True)"
```

---

## ConfigLoader API

The `ConfigLoader` class provides programmatic access to profiles:

```python
from config_loader import ConfigLoader

loader = ConfigLoader()

# Load full configuration for a symbol
config = loader.get_full_config('capital.com:EURUSD')

# Get just the strategy settings
strategy_config = loader.get_strategy_config('capital.com:EURUSD')

# Get just the filter settings
filter_config = loader.get_filter_config('capital.com:EURUSD')

# Convert symbol to config key (e.g., 'capital.com:EURUSD' -> 'eurusd')
symbol_key = loader.get_symbol_from_config('capital.com:EURUSD')
```

---

## Adding a New Symbol Profile

1. Create a new YAML file in `config/` directory:

```bash
touch config/gbpusd.yaml
```

2. Define the symbol configuration:

```yaml
symbol: capital.com:GBPUSD
description: "British Pound vs US Dollar"

strategy:
  atr_threshold: 0.25
  atr_period: 14
  lookback: 8
  h4_ema_period: 20
  daily_lookback: 20

filters:
  use_sweep_filter: false        # Test to determine optimal
  use_bos_filter: false
  use_h4_filter: true
  h4_filter_mode: counter
  use_daily_filter: false

expectations:
  expectancy: -0.14R             # From H4 Counter baseline
  trades: null
  win_rate: 28.8%
  comment: "Using default/conservative settings"
```

3. The symbol will automatically use this profile when backtested.

---

## Key Changes to main.py

### run_backtest Function

**Before:**
```python
def run_backtest(
    symbol: str = 'capital.com:EURUSD',
    use_sweep_filter: bool = True,
    use_bos_filter: bool = False,
    # ... more CLI parameters
):
```

**After:**
```python
def run_backtest(
    symbol: str = 'capital.com:EURUSD',
    use_profile_config: bool = True,  # NEW: Enable profile loading
    use_sweep_filter: Optional[bool] = None,  # Optional override
    # ... other parameters as overrides
):
```

**Behavior:**
1. If `use_profile_config=True`: Loads symbol-specific YAML profile
2. If override parameters provided: They supersede profile settings
3. If profile doesn't exist: Falls back to `default.yaml`

### run_all_tests Function

**Before:**
```python
def run_all_tests(symbols=None, ...):
    # Only supported hardcoded test scenarios
```

**After:**
```python
def run_all_tests(symbols=None, ..., use_profiles=True):
    # Can run profile-based tests or legacy manual scenarios
```

**New Mode: Profile-Based Testing**
```
TEST 1: SYMBOL-SPECIFIC PROFILES
  - Loads eurusd.yaml for EURUSD
  - Loads audusd.yaml for AUDUSD
  - Runs backtest with optimal symbol-specific filters
  - Reports aggregated results across all symbols
```

---

## Migration Guide

### Migrating from CLI Arguments to Profiles

**Old way (CLI arguments):**
```bash
python main.py --use_sweep_filter=True --use_h4_filter=True --h4_filter_mode=counter
```

**New way (profiles):**
```bash
# Just specify the symbol, profile loads automatically
python -c "from main import run_backtest; run_backtest('capital.com:EURUSD')"
```

### For Existing Scripts

Update your scripts to use the new API:

```python
# Old
from main import run_backtest
run_backtest(
    'capital.com:EURUSD',
    use_sweep_filter=True,
    use_h4_filter=True,
    h4_filter_mode='counter'
)

# New (cleaner, more maintainable)
from main import run_backtest
run_backtest('capital.com:EURUSD', use_profile_config=True)
```

---

## Benefits

✅ **Symbol-specific optimization**: Different symbols get optimal filter settings
✅ **Version control**: Configurations are tracked in git
✅ **Reproducibility**: Same symbol always uses same parameters
✅ **Scalability**: Easy to add new symbols
✅ **Maintainability**: Central location for all settings
✅ **Documentation**: Expectations documented in config files
✅ **Backward compatible**: Can still use manual parameters if needed

---

## Current Profiles Summary

| Symbol | Sweep | H4 Counter | BOS | Daily | Expected Expectancy | Expected Win Rate |
|--------|-------|-----------|-----|-------|---------------------|------------------|
| EURUSD | Yes | Yes | No | No | -0.25R | 25.0% |
| AUDUSD | Yes | Yes | No | No | -0.07R | 30.9% |
| Default | No | Yes | No | No | -0.14R | 28.8% |

---

## Next Steps

1. **Phase 3**: Test sweep filter on GBPUSD, NZDUSD, XAUUSD
2. **Profile Optimization**: Create optimal profiles for each symbol
3. **Ensemble Approach**: Portfolio-level optimization using symbol-specific settings
4. **Automation**: Auto-generate profiles based on backtest optimization

---

## Files Changed

- **New**: `config/eurusd.yaml`, `config/audusd.yaml`, `config/default.yaml`
- **New**: `config_loader.py` (ConfigLoader class)
- **Modified**: `main.py` (refactored for profile loading)

---

## Git Commit

```
9813bf7 [Profile System] Add profile-based configuration (YAML) with symbol-specific settings
```

---

*Profile system implemented as part of Phase 2 completion and Phase 3 preparation.*
