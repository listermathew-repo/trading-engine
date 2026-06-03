# MAF Backtest System Architecture v1.0

## Purpose
Transform the MAF (Market Alignment Framework) from a prototype into a production-grade trading engine.

## Core Principle
**Single Responsibility**: Each module does one thing well. Signal detection ≠ Order execution ≠ Reporting.

---

## Data Schema

### Input: Raw OHLCV from DuckDB
```
symbol, time, open, high, low, close, volume, hour_utc, minute_utc
```

### Processing Pipeline

#### STAGE 1: Signal Detection (strategy.py)
**Input**: Raw M15 bars
**Output**: Signal list
```
{
  'bar_idx': 100,
  'timestamp': '2024-06-15 10:30',
  'symbol': 'EURUSD',
  'type': 'LONG',
  'entry_level': 1.0750,
  'gap_pips': 15.2,
  'utc_h': 1,
  'utc_m': 30
}
```

#### STAGE 2: Risk Calculation (strategy.py)
**Input**: Signal
**Output**: Risk parameters
```
{
  'stop_loss': 1.0720,
  'take_profit': 1.0810,
  'risk_distance': 0.0030,
  'risk_pips': 30.0,
  'r_ratio': 2.0
}
```

#### STAGE 3: Execution Simulation (engine.py)
**Input**: Risk setup + bars
**Output**: Closed trade
```
{
  'entry_price': 1.0750,
  'fill_bar': 102,
  'bars_waited': 2,
  'exit_price': 1.0810,
  'exit_reason': 'tp',
  'pnl_pips': 60.0,
  'pnl_r': 2.00
}
```

#### STAGE 4: Analytics (engine.py)
**Input**: All closed trades
**Output**: Metrics
```
{
  'total_trades': 287,
  'win_rate': 35.2%,
  'expectancy': +0.22R,
  'avg_winner': +2.00R,
  'avg_loser': -1.00R
}
```

---

## Module Responsibilities

### strategy.py
- `calculate_atr(bars, period=14)` → float ATR value
- `detect_fvgs(bars, atr_threshold=0.25)` → list of signals
- `get_swing_stop(bars, fvg_bar_idx, lookback=8)` → dict with swing_low, swing_high
- `calculate_risk_targets(entry, stop, rr_ratio=2.0, side)` → dict with risk, tp, r_ratio
- `get_h4_bias(h4_bars, ema_period=20)` → 1 (Bullish), -1 (Bearish), 0 (Neutral)

### engine.py
- `simulate_limit_orders(bars, signals, max_wait_bars=96)` → list of closed trades
- `calculate_expectancy(trades)` → dict of metrics

### main.py
- `run_backtest(symbol, db_path)` → Execute full pipeline and return metrics + trades

---

## Critical Rules (MUST OBEY)

1. **No Lookahead Bias**: H4 candle closing at 12:00 can only be used for M15 candles AFTER 12:00
2. **Perfect Fill Assumption**: Price touches entry = instant fill (no slippage yet)
3. **Stop Placement**: BELOW entry for LONG, ABOVE for SHORT (verify every run)
4. **State Integrity**: Each trade has exactly one of {Pending, Filled, Closed, Invalidated}
5. **Trade Log**: Every trade must export timestamp, entry, stop, target, fill, exit, P&L

---

## Version History

- **v0.1**: forex_swing_backtest.py (Prototype, tangled logic, -0.19R baseline discovered)
- **v1.0**: (Current) Modular architecture, clean separation of concerns
- **v1.1**: (Next) Add H4 confluence filter, Daily POI detection
- **v2.0**: (Future) Add slippage model, spread costs, realistic fills

---

## Test Checklist Before Running

- [ ] DuckDB file path is correct
- [ ] M15 data loads successfully
- [ ] Signals are detected (should be ~400+ for 2-year window)
- [ ] Trades close with proper P&L calculation
- [ ] Expectancy is approximately -0.19R (honest baseline)
- [ ] Export shows win rate ~26.8%, not fake 62%
