# Trading Alerts — Project Status

**Last updated:** 2026-04-23

## Status: Local Webhook Operational ✅

### Completed
- [x] PowerShell alert scripts built and scheduled (`trading-alerts/`)
- [x] ntfy.sh push notification pipeline confirmed working (topic: `Mathew-Trading-Alerts`)
- [x] TradingView MCP integration operational (`tradingview-mcp-jackson/`)
- [x] Signal check workflow automated (15:00 ACST daily trigger)
- [x] **Local FastAPI webhook server tested and operational**
  - Accepted POST requests from TradingView alert webhooks
  - XAU/USD (GOLD) test payload received and processed successfully via curl
  - Server running locally on localhost (default FastAPI port 8000)

- [x] **Repository initialised and prepped for GitHub/Vercel deployment**
  - `api/index.py` — FastAPI app with `/webhook` POST and `/` health endpoints
  - `requirements.txt` — all runtime dependencies pinned
  - `vercel.json` — Vercel Python runtime config, routes all traffic to `api/index.py`
  - `.gitignore` — excludes `.env`, `__pycache__`, Vercel build artefacts, and log files
  - Initial git commit created: "Initial commit: Webhook and Capital.com Client"

### In Progress
- [ ] Push repository to GitHub and connect to Vercel project
- [ ] Set `NTFY_TOPIC` environment variable in Vercel dashboard
- [ ] TradingView alert → webhook → ntfy.sh pipeline (end-to-end live test pending)

### Next Steps
1. Push to GitHub: `git remote add origin <repo-url> && git push -u origin master`
2. Import repo in Vercel — it will auto-detect `vercel.json` and deploy
3. Copy the Vercel deployment URL and paste it into TradingView alert webhook field
4. Create TradingView alert on GOLD targeting `https://<vercel-url>/webhook`
5. Confirm end-to-end: TradingView fires alert → FastAPI receives → ntfy.sh push fires on phone

## System Architecture

```
TradingView Alert (GOLD/AUDUSD/EURUSD)
    ↓ HTTP POST (JSON payload)
FastAPI Webhook Server (localhost:8000/webhook)
    ↓ Parse symbol, action, price
ntfy.sh push notification (phone)
    ↓
Mathew reviews signal at desk (15:30 ACST)
```

## Key Files

| File | Purpose |
|------|---------|
| `trading-alerts/manual-alerts.ps1` | Manual ntfy.sh alert trigger |
| `trading-alerts/signal-check-template.md` | Standard signal check output format |
| `tradingview-mcp-jackson/rules.json` | Full trading rules and risk framework |
| `tradingview-mcp-jackson/CLAUDE.md` | MCP tool usage guide |
