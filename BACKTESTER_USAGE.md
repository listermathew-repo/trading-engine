# Backtester Usage Guide

## Quick Start

### Demo (No API Required)
```bash
cd trading-engine
python backtester/demo_backtest.py
```

This runs a backtest on synthetic data and demonstrates the backtester functionality without needing Capital.com credentials.

### Live Backtest (Capital.com Required)
```bash
# Set up environment variables
cp .env.example .env
# Edit .env with your Capital.com credentials

# Run backtest for February 2026 EUR/USD
python backtester/run_backtest.py
```

## What the Backtester Does

The FVG backtester simulates the following trading strategy on EUR/USD:

### 1. **Fair Value Gap Detection (1H Timeframe)**
Identifies unmitigated gaps between hourly candles:
- **Bullish FVG**: Current hour's low > Previous hour's high (gap up)
- **Bearish FVG**: Current hour's high < Previous hour's low (gap down)

### 2. **Entry Signal (15-Minute Timeframe)**
When price enters an FVG zone:
- Find the **lowest red candle** (close < open) within the FVG
- **Entry**: At the HIGH of that lowest red candle
- **Trigger**: On candle close (not intracandle)

### 3. **Stop Loss Placement**
Tested at three different lookback periods:
- **5-candle lookback**: SL placed 1 pip below lowest low of last 5 candles
- **10-candle lookback**: SL placed 1 pip below lowest low of last 10 candles
- **20-candle lookback**: SL placed 1 pip below lowest low of last 20 candles

Creates separate trades for each lookback period to identify optimal swing detection window.

### 4. **Take Profit**
- **Fixed 1R**: Risk unit = entry price - stop loss
- **BUY**: TP = entry + (entry - SL)
- **SELL**: TP = entry - (entry - SL)

### 5. **Trade Outcomes**
- **Win**: Take profit hit before stop loss
- **Loss**: Stop loss hit before take profit
- **Non-Progressive**: Stop loss hit on entry candle (immediate failure)
- **Pending**: Trade still open at end of data

### 6. **Session Filtering**
Only takes trades during:
- **Adelaide ACDT**: 9:00 a.m. - 10:00 p.m. (UTC+10:30 in February)
- **UTC Equivalent**: 10:30 p.m. - 11:30 a.m. (previous day to current day)

## Output Files

### CSV Report
**Location**: `backtester/results/fvg_backtest_YYYYMMDD_HHMMSS.csv`

Contains one row per trade with:
- Entry time and price
- Stop loss and take profit levels
- FVG zone information
- Exit price and result
- Risk multiples (R) gained/lost
- PnL in dollars
- Swing lookback period used
- Session type

### Summary Report
**Location**: `backtester/results/fvg_backtest_YYYYMMDD_HHMMSS_summary.txt`

Contains:
- Overall statistics (total trades, wins, losses, non-progressives)
- Win rate percentage
- Total and average R gained
- Total and average PnL
- Analysis broken down by swing lookback period

### Console Output
Printed to terminal:
- Overall summary
- Performance by swing lookback period (5, 10, 20 candles)
- Performance by trading session
- Sample of individual trades

## Example Output

```
================================================================================
                           BACKTEST SUMMARY
================================================================================

Total Trades: 45
Winning Trades: 28
Losing Trades: 12
Non-Progressive Trades: 5

Win Rate: 62.2%
Total R: +34.50
Avg R per Trade: +0.77
Total PnL: $3,450.00
Avg PnL per Trade: $76.67

================================================================================
                ANALYSIS BY SWING LOOKBACK PERIOD
================================================================================

5-Candle Swing Low:
  Trades: 15 | Wins: 10 | Losses: 4 | NP: 1
  Win Rate: 66.7%
  Total R: +12.50 | Avg R: +0.83
  Total PnL: $1,250.00 | Avg PnL: $83.33

10-Candle Swing Low:
  Trades: 15 | Wins: 9 | Losses: 5 | NP: 1
  Win Rate: 60.0%
  Total R: +11.00 | Avg R: +0.73
  Total PnL: $1,100.00 | Avg PnL: $73.33

20-Candle Swing Low:
  Trades: 15 | Wins: 9 | Losses: 3 | NP: 3
  Win Rate: 60.0%
  Total R: +11.00 | Avg R: +0.73
  Total PnL: $1,100.00 | Avg PnL: $73.33

================================================================================
```

## Key Metrics Explained

### R (Risk Multiple)
- **1R** = entry price - stop loss price
- **Winning trade with 1R TP** = you made exactly 1 risk unit as profit
- **Losing trade at SL** = you lost exactly 1 risk unit
- **Non-progressive at SL same candle** = you lost 1R before price could move

**Total R** = sum of all R gained/lost across all trades
**Avg R** = Total R divided by number of trades

### Win Rate
Percentage of trades that reach take profit before stop loss

### Performance by Swing Lookback
Shows which swing low detection period (5, 10, or 20 candles) works best:
- Compare win rates
- Compare total R
- Compare average R per trade
- Choose the lookback with highest Avg R (efficiency metric)

## Configuration

### Adjust Risk Per Trade
Modify in `backtester/run_backtest.py`:
```python
strategy = FVGStrategy(
    risk_per_trade=200.0,  # Change from $100 to $200
    lookback_periods=[5, 10, 20],
)
```

### Adjust Lookback Periods
Test different periods:
```python
strategy = FVGStrategy(
    risk_per_trade=100.0,
    lookback_periods=[3, 5, 7, 10, 15, 20],  # Test more periods
)
```

### Adjust Session Window
Modify time filtering in `backtester/strategy.py`:
```python
is_in_window = FVGStrategy.is_in_session_window(
    timestamp,
    session_start_hour=8,   # Start at 8am Adelaide
    session_end_hour=23,    # End at 11pm Adelaide
)
```

### Use Live Capital.com API
```bash
# Set environment variable
export CAPITAL_ENVIRONMENT=live

# Then run backtest
python backtester/run_backtest.py
```

## Troubleshooting

### No trades generated
**Causes**:
1. **No FVGs detected** → Increase gap size in synthetic data or use different date range
2. **All FVGs mitigated** → Later candles filled all the gaps
3. **No red candles in FVG zones** → Strategy requires red candles for entry
4. **No trades within session window** → Trades happened outside 9am-10pm Adelaide

**Solution**:
- Check FVG detection logs: `[INFO] Detected X FVGs`, `[INFO] X are unmitigated`
- Verify Capital.com has data for the requested date range
- Check that your session window filter includes trade times

### Capital.com API Error
**Error**: `Failed to authenticate with Capital.com`

**Solution**:
1. Verify credentials in `.env` file
2. Check that API key is valid and not expired
3. Use `CAPITAL_ENVIRONMENT=demo` for testing
4. Ensure network connectivity

### Slow Performance
**Cause**: Large date ranges with 500-candle API limits require pagination

**Solution**:
- Use shorter date ranges (e.g., one week instead of one month)
- Modify `backtester/run_backtest.py` to fetch data in chunks
- Consider pre-fetching and caching data

## Advanced Usage

### Analyze Specific Time Periods
Modify `run_backtest.py`:
```python
start_date = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
end_date = datetime(2026, 2, 7, 23, 59, 59, tzinfo=timezone.utc)  # One week
```

### Monte Carlo Analysis
Generate multiple backtests with:
```bash
for i in {1..100}; do
    python backtester/run_backtest.py >> results_summary.txt
done
```

### Optimize Stop Loss Placement
Add multiple buffer distances:
```python
# In strategy.py, modify SL calculation:
for buffer_pips in [0.5, 1.0, 2.0, 5.0]:
    stop_loss = swing_low - (buffer_pips * 0.0001)
    # Create trade with this SL...
```

## File Structure

```
backtester/
├── capital_data.py          # Capital.com API integration
├── fvg_detector.py          # FVG detection logic
├── swing_detector.py        # Swing low detection
├── strategy.py              # Core backtest engine
├── results.py               # Reporting and CSV export
├── run_backtest.py          # Main backtest runner
├── demo_backtest.py         # Demo with synthetic data
├── __init__.py              # Package exports
├── README.md                # Module documentation
└── results/                 # Output directory
    ├── fvg_backtest_*.csv   # Trade data
    └── fvg_backtest_*_summary.txt  # Summary report
```

## Testing

Run unit tests:
```bash
python -m pytest tests/test_backtester.py -v
```

Tests cover:
- FVG detection on synthetic data
- Swing low identification
- Session filtering
- Trade simulation logic
- Timezone conversions

## Next Steps

1. **Run demo**: `python backtester/demo_backtest.py`
2. **Set up API**: Edit `.env` with Capital.com credentials
3. **Run backtest**: `python backtester/run_backtest.py`
4. **Analyze results**: Open CSV in spreadsheet software
5. **Optimize**: Adjust swing lookback periods based on performance
6. **Paper trade**: Use insights from backtest to trade on demo account
7. **Go live**: When confident, switch to live account and trade

## Support

For questions about:
- **Backtester logic**: See `backtester/README.md`
- **API integration**: See `backtester/capital_data.py` docstrings
- **Strategy rules**: See `backtester/strategy.py` and this guide
- **Test cases**: See `tests/test_backtester.py`

## Limitations

⚠️ **Important**:
- Backtester assumes **perfect execution** at entry/SL/TP prices
- **No slippage** or commission modeling
- **No gap opening** handling (only within-session moves)
- **No partial fills** or position management
- Results are **backtested only** — live performance may differ

**Use for**: Strategy validation, parameter optimization, expected value estimation
**Don't use for**: Financial predictions, risk management guarantees, live decisions without judgment
