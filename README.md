# TradingView MCP CLI Access

Quick command-line access to TradingView data for trading analysis without needing Chrome DevTools Protocol (CDP).

## Setup

### 1. Python CLI Tool (Recommended)

**Requirements:**
- Python 3.8+
- No external dependencies (uses only standard library)

**Install:**
```bash
cd C:\Users\mathe\Documents\tradingview-mcp
python tradingview-cli.py help
```

### 2. Usage Examples

#### Chart Read - Record indicator values from TradingView
```bash
# EURUSD at 15:00
python tradingview-cli.py chart-read EURUSD --price 1.0850 --vwap 1.0845 --rsi 55 --ema10 1.0841 --ema21 1.0840 --ema20 1.0835

# GOLD
python tradingview-cli.py chart-read GOLD --price 2450.50 --vwap 2448.00 --rsi 58 --ema10 2449.25 --ema21 2447.50 --ema20 2448.75

# BTCUSD
python tradingview-cli.py chart-read BTCUSD --price 62500 --vwap 62300 --rsi 45 --ema10 62400 --ema21 62200 --ema20 62350

# AUDUSD
python tradingview-cli.py chart-read AUDUSD --price 0.6750 --vwap 0.6745 --rsi 52 --ema10 0.6748 --ema21 0.6742 --ema20 0.6746
```

#### Signal Check - Verify 5-condition gate
```bash
# All conditions met for GOLD (Scenario 4)
python tradingview-cli.py signal-check GOLD --scenario "Scenario 4" --c1 true --c2 true --c3 true --c4 true --c5 false

# Partial conditions met for BTCUSD (Scenario 2)
python tradingview-cli.py signal-check BTCUSD --scenario "Scenario 2" --c1 true --c2 true --c3 false --c4 true --c5 true
```

#### Batch Check - Process all 4 pairs
```bash
# Runs all pairs from the signal check template
python tradingview-cli.py batch-check data/signal-check-15-00-template.json
```

## 15:00 Check Workflow

1. **Open TradingView charts** for EURUSD, BTCUSD, GOLD, AUDUSD
2. **Read each chart** and run the CLI command:
   ```bash
   python tradingview-cli.py chart-read [PAIR] --price X --vwap X --rsi X --ema10 X --ema21 X --ema20 X
   ```
3. **Check 5 conditions** for entry readiness:
   ```bash
   python tradingview-cli.py signal-check [PAIR] --scenario "Scenario X" --c1 [true/false] --c2 [true/false] --c3 [true/false] --c4 [true/false] --c5 [true/false]
   ```
4. **Review summary** of which pairs are trade-ready

## MCP Integration

To use this via Claude Code MCP:

```bash
# In your Claude Code settings, add this command permission:
"Bash(python C:\\Users\\mathe\\Documents\\tradingview-mcp\\tradingview-cli.py *)"
```

Then you can call it from Claude Code:
```
/run python tradingview-cli.py chart-read EURUSD --price 1.0850 --vwap 1.0845 --rsi 55 --ema10 1.0841 --ema21 1.0840 --ema20 1.0835
```

## File Structure

```
tradingview-mcp/
├── tradingview-cli.py          # Main CLI tool
├── README.md                   # This file
├── data/
│   ├── signal-check-15-00-template.json
│   └── signal-checks-log.json
└── .claude/
    ├── settings.local.json
    └── launch.json
```

## Scenarios Quick Reference

- **Scenario 1**: Clear long bias, all conditions strong → Entry ready
- **Scenario 2**: Cautious long setup, some caution needed → Check all conditions
- **Scenario 3**: Ambiguous/neutral bias → Usually no entry
- **Scenario 4**: Risk-off or downside bias → No long entry unless clear retest

## 5-Condition Gate

All 5 must be met for entry:

| Condition | Requirement |
|-----------|-------------|
| **C1** | VWAP bounce - Price reclaiming VWAP from below |
| **C2** | RSI 40–60 - Momentum zone (not overbought/oversold) |
| **C3** | EMA10 > EMA21 - Short-term trend aligned bullish |
| **C4** | Price > EMA20 - Above 20-period moving average |
| **C5** | Scenario confirmed - Morning video bias still active |

## Troubleshooting

**Python not found:**
```bash
# Use full path
C:\Users\mathe\AppData\Local\Programs\Python\Python312\python.exe tradingview-cli.py help
```

**Permission denied:**
```bash
# Run as admin or in WSL
wsl python tradingview-cli.py help
```

## Next Steps

- [ ] Run 15:00 check at 15:00 ACST
- [ ] Record results for all 4 pairs
- [ ] Confirm entry-ready pairs
- [ ] Execute trades 15:30–17:00 ACST
- [ ] Log post-session results

---

**Questions?** Use `python tradingview-cli.py help` for quick reference.
