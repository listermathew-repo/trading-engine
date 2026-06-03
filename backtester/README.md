# Fair Value Gap (FVG) Backtester

A sophisticated backtesting engine for the Fair Value Gap trading strategy on EUR/USD 15-minute timeframe.

## Overview

The FVG backtester simulates the following strategy:

1. **FVG Detection (1H Timeframe)**
   - Detects unmitigated gaps between hourly candles
   - Bullish FVG: Current candle's low > Previous candle's high (gap up)
   - Bearish FVG: Current candle's high < Previous candle's low (gap down)

2. **Entry Signal (15-Minute Timeframe)**
   - Price enters the FVG zone
   - Identifies the lowest red candle (close < open) within the FVG
   - Entry at the HIGH of that lowest red candle
   - Entry triggers on candle close

3. **Stop Loss (Variable Lookback)**
   - Just below the swing low
   - Tests three lookback periods: 5, 10, and 20 candles
   - Identifies the lowest point before entry within the lookback window

4. **Take Profit**
   - Fixed 1R above entry price (for BUY)
   - Fixed 1R below entry price (for SELL)
   - R = distance from entry to stop loss

5. **Session Filtering**
   - Adelaide time: 9 a.m. - 10 p.m. (ACDT)
   - Equivalent to 10:30 p.m. - 11:30 a.m. UTC (approximately)

## Trade Outcomes

- **Win**: Take profit hit before stop loss
- **Loss**: Stop loss hit before take profit
- **Non-Progressive**: Stop loss hit on entry candle (immediate failure)
- **Pending**: Trade still open at end of data

## Module Structure

```
backtester/
├── __init__.py           # Package exports
├── capital_data.py       # Capital.com API data fetching
├── fvg_detector.py       # FVG detection logic
├── swing_detector.py     # Swing low detection
├── strategy.py           # Core backtesting strategy
├── results.py            # Results reporting and CSV export
├── run_backtest.py       # Main backtest runner
└── README.md            # This file
```

## Components

### capital_data.py
Fetches historical OHLCV data from Capital.com API.

**Key Classes:**
- `OHLCV`: Data class for candlestick data
- `CapitalDataClient`: Authenticates and fetches price history

**Usage:**
```python
from capital_data import CapitalDataClient

client = CapitalDataClient()
candles = client.get_price_history(
    epic="EURUSD",
    resolution="MINUTE_15",
    num_points=500,
)
```

### fvg_detector.py
Detects Fair Value Gaps on the 1-hour timeframe.

**Key Classes:**
- `FVG`: Represents a single Fair Value Gap
- `FVGDetector`: Static methods for FVG detection

**Usage:**
```python
from fvg_detector import FVGDetector

fvgs = FVGDetector.detect_fvgs(hourly_candles)
unmitigated = FVGDetector.filter_unmitigated(fvgs, all_candles)
```

### swing_detector.py
Detects swing lows for stop loss placement.

**Key Classes:**
- `SwingDetector`: Static methods for swing detection

**Usage:**
```python
from swing_detector import SwingDetector

swing_low_5 = SwingDetector.find_swing_low(candles, lookback=5)
swing_low_10 = SwingDetector.find_swing_low(candles, lookback=10)
swing_low_20 = SwingDetector.find_swing_low(candles, lookback=20)

swings = SwingDetector.find_multiple_swing_lows(
    candles, 
    lookback_periods=[5, 10, 20]
)
```

### strategy.py
Core backtesting engine.

**Key Classes:**
- `BacktestTrade`: Single trade record
- `BacktestResults`: Aggregated backtest results
- `FVGStrategy`: Main strategy class

**Usage:**
```python
from strategy import FVGStrategy

strategy = FVGStrategy(
    risk_per_trade=100.0,      # $ per trade
    lookback_periods=[5, 10, 20]  # Swing lookback periods to test
)

results = strategy.backtest(hourly_candles, minute15_candles)
```

### results.py
Generates reports and CSV exports.

**Key Classes:**
- `ResultsReporter`: Static methods for reporting

**Usage:**
```python
from results import ResultsReporter
from pathlib import Path

# Export to CSV
output_path = Path("backtest_results.csv")
ResultsReporter.export_csv(results, output_path)

# Print summaries
ResultsReporter.print_summary(results)
ResultsReporter.print_individual_trades(results, limit=20)

# Analyze by lookback period
lookback_analysis = ResultsReporter.analyze_by_lookback(results)
ResultsReporter.print_lookback_analysis(lookback_analysis)

# Analyze by session
session_analysis = ResultsReporter.analyze_by_session(results)
ResultsReporter.print_session_analysis(session_analysis)
```

## Running the Backtest

### Prerequisites

1. **Capital.com Account** (Demo or Live)
2. **Environment Variables** in `.env`:
   ```
   CAPITAL_API_KEY=your_api_key
   CAPITAL_IDENTIFIER=your_identifier
   CAPITAL_PASSWORD=your_password
   CAPITAL_ENVIRONMENT=demo  # or "live"
   ```

3. **Python 3.9+**

### Execution

```bash
cd trading-engine
python backtester/run_backtest.py
```

### Output

The backtest generates:
1. **CSV File**: `backtester/results/fvg_backtest_YYYYMMDD_HHMMSS.csv`
2. **Summary File**: `backtester/results/fvg_backtest_YYYYMMDD_HHMMSS_summary.txt`
3. **Console Output**: Summary statistics, trade analysis by lookback period

## CSV Export Format

| Column | Description |
|--------|-------------|
| Date | Trade entry date |
| Time | Trade entry time (Adelaide) |
| Entry Candle Index | Index in 15-minute candle list |
| Session | Trading session (london_open, london_close, etc.) |
| Direction | BUY or SELL |
| Entry Price | Entry price (HIGH of lowest red candle) |
| Stop Loss | Stop loss price |
| Take Profit | Take profit price (1R) |
| Status | win, loss, non-progressive, or pending |
| R Gained | Risk multiples gained/lost |
| Trade PnL | Profit/loss in dollars |
| Return % | Return as percentage |
| Exit Price | Exit price (SL or TP hit) |
| Exit Time | Exit timestamp |
| Swing Lookback | Number of candles for swing low (5, 10, or 20) |
| FVG Direction | bullish or bearish |
| FVG Zone Low | FVG zone lower bound |
| FVG Zone High | FVG zone upper bound |
| Liquidity | high or low (based on session) |

## Analysis Metrics

### Per Trade
- **Win Rate**: Percentage of winning trades
- **R Gained**: Risk multiples (1R = risk unit)
- **Profit/Loss**: Dollar amount

### Aggregated
- **Total R**: Sum of all R gained/lost
- **Avg R per Trade**: Average R across all trades
- **Total PnL**: Total profit/loss in dollars
- **Avg PnL per Trade**: Average per trade

### By Swing Lookback Period
Tests optimization of swing low lookback:
- 5-candle lookback
- 10-candle lookback
- 20-candle lookback

Shows which lookback period performs best.

### By Trading Session
Analyzes performance across:
- London Open (high liquidity)
- London Close
- Asian Close
- Other times

## Key Features

✅ **Accurate FVG Detection**: Correctly identifies unmitigated gaps
✅ **Multi-timeframe Analysis**: 1H FVG, 15m entries
✅ **Variable Stop Loss**: Tests 3 swing lookback periods
✅ **Session Filtering**: Adelaide time window (9am-10pm)
✅ **Risk Management**: Fixed 1R take profit, stop loss below swing
✅ **Comprehensive Reporting**: CSV export + detailed analysis
✅ **Trade Classification**: Wins, losses, non-progressives
✅ **Performance Analysis**: By lookback period and session

## Customization

### Adjust Risk Per Trade
```python
strategy = FVGStrategy(risk_per_trade=200.0)  # $200 per trade
```

### Adjust Swing Lookback Periods
```python
strategy = FVGStrategy(lookback_periods=[3, 5, 8, 15])
```

### Adjust Session Window
Modify `FVGStrategy.is_in_session_window()` in strategy.py:
```python
is_in = FVGStrategy.is_in_session_window(
    timestamp,
    session_start_hour=9,
    session_end_hour=22,
)
```

## Testing

Run unit tests:
```bash
cd trading-engine
python -m pytest tests/test_backtester.py -v
```

Tests cover:
- FVG detection
- Swing low identification
- Session filtering
- Trade simulation
- Results calculation

## Limitations

1. **Capital.com API Constraints**: Max 500 candles per request
2. **Historical Data**: Limited by API availability
3. **Slippage/Fees**: Not modeled (backtester assumes exact fills)
4. **Gap Openings**: Not modeled (only within-session price moves)
5. **Real-time Behavior**: Backtester is synchronous on candle close

## Future Enhancements

- [ ] Add partial position management
- [ ] Model slippage and commissions
- [ ] Trailing stop loss logic
- [ ] Dynamic risk sizing based on volatility
- [ ] Monte Carlo analysis
- [ ] Out-of-sample validation
- [ ] Real-time paper trading mode

## Support

For issues or questions about the backtester:
1. Check the README section above
2. Review test cases in `tests/test_backtester.py`
3. Enable debug logging in `run_backtest.py`

## License

Part of the Trading Operations System
