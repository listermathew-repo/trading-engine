# Trading Alerts — Project Status

**Last updated:** 2026-04-23

## Status: Broker API Wired — Simulation Mode ✅

### Completed
- [x] PowerShell alert scripts built and scheduled
- [x] ntfy.sh push notification pipeline confirmed working (topic: `Mathew-Trading-Alerts`)
- [x] TradingView MCP integration operational (`tradingview-mcp-jackson/`)
- [x] Signal check workflow automated (15:00 ACST daily trigger)
- [x] **Local FastAPI webhook server tested and operational**
  - `api/index.py` — FastAPI app with `/webhook` POST and `/` health endpoints
  - XAU/USD (GOLD) test payload received and processed successfully via curl
  - `vercel.json` configured for Vercel deployment
- [x] **Capital.com broker API integration built**
  - `api/capital_client.py` — handles auth (demo + live), position sizing, market orders
  - Risk model: Tier 2 = 0.5% ($400 on $80k account) per `rules.json`
  - Position size formula: `Risk Amount ÷ (stop_pips × pip_value) = Lot Size`
  - `SIMULATE_TRADES=true` by default — no live orders until you flip this flag
  - `.env` created with credential placeholders (gitignored, never committed)

### In Progress
- [x] Push repository to GitHub and connect to Vercel project
- [x] Set environment variables in Vercel dashboard (CAPITAL_*, NTFY_TOPIC, SIMULATE_TRADES)
- [x] TradingView alert repointed to cloaked production URL: `https://sys-log-worker-72.vercel.app/webhook`
- [ ] End-to-end live test: TradingView fires → webhook receives → ntfy fires → no broker order

### Next Steps
1. **End-to-end simulate test** — trigger a TradingView alert manually and confirm ntfy fires on your phone
2. Verify Capital.com Gold contract spec (pip_value=1.0 USD/lot/pip — confirm before going live)
3. Flip `SIMULATE_TRADES=false` in Vercel env vars for live demo execution

### Completed Setup
- Deployed to Vercel at `https://sys-log-worker-72.vercel.app`
- TradingView alert repointed to cloaked webhook URL: `https://sys-log-worker-72.vercel.app/webhook`
- All env vars set in Vercel dashboard

### Original TradingView Alert Payload
4. *(reference)* TradingView alert on GOLD targeting the webhook with payload:
   ```json
   {"symbol": "XAUUSD", "action": "{{strategy.order.action}}", "price": "{{close}}", "timeframe": "{{interval}}", "stop": "YOUR_STOP_LEVEL"}
   ```
5. Test simulate mode end-to-end: TradingView fires → webhook receives → ntfy fires → no broker order
6. Verify Capital.com Gold contract spec (pip_value=1.0 USD/lot/pip — confirm before going live)
7. Flip `SIMULATE_TRADES=false` in Vercel env vars for live demo execution

## System Architecture

```
TradingView Alert (GOLD/AUDUSD/EURUSD)
    ↓ HTTP POST (JSON: symbol, action, price, stop)
FastAPI Webhook Server (api/index.py — Vercel or local)
    ↓ Parse payload
    ├─ SIMULATE=true  → skip broker, fire ntfy only
    └─ SIMULATE=false → CapitalClient.place_market_order()
           ↓ authenticate() → get_account_balance() → _calculate_size()
           ↓ POST /positions to Capital.com API (demo or live)
    ↓
ntfy.sh push notification (phone) — FILLED or FAILED
    ↓
Mathew reviews result (15:30 ACST)
```

## Key Files

| File | Purpose |
|------|---------|
| `api/index.py` | FastAPI webhook server — receives TradingView alerts |
| `api/capital_client.py` | Capital.com API client — auth, sizing, order placement |
| `.env` | Credentials + feature flags (gitignored — never committed) |
| `.env.template` | Committed template showing required variables |
| `requirements.txt` | Python dependencies |
| `vercel.json` | Vercel deployment config |
| `tradingview-mcp-jackson/rules.json` | Full trading rules and risk framework |

## Risk Framework (from rules.json)

| Tier | Risk % | Dollar Risk | Usage |
|------|--------|-------------|-------|
| T1 | 0.25% | $200 | B-grade setups, new pairs |
| **T2** | **0.50%** | **$400** | **Standard — use 80% of trades** |
| T3 | 0.75% | $600 | High-confidence, multi-pair confluence |
| T4 | 1.00% | $800 | A+ only, after 2 consecutive wins |

Position size formula: `size (lots) = Risk ($) ÷ (stop_pips × pip_value_per_lot)`
- Forex (EURUSD/AUDUSD/GBPUSD): pip = 0.0001, pip_value = $10/lot
- Gold (XAUUSD): pip = 0.10, pip_value = $1/lot *(verify Capital.com contract spec before live)*
