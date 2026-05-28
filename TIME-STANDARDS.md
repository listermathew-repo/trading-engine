# Time Standards & Timezone Conversion

## Adelaide Local Time (ADL) — Trading System Standard

All trading system operations use **Adelaide (ADL)** timezone:
- **Timezone**: UTC+9:30 (South Australia Standard Time)
- **Trading Hours**: 09:00 ADL - 22:00 ADL daily
- **Atomic Clock**: https://time.is/Adelaide
- **Reference**: https://timeanddate.com/worldclock/australia/adelaide

## Format Rules

### ✅ CORRECT
- "09:30 ADL" (timestamp with zone marker)
- "14:45 ADL" (afternoon trading)
- "22:15 ADL" (evening session)

### ❌ NEVER USE
- "09:30" (no timezone marker)
- "Yesterday at 14:41 UTC" (wrong timezone)
- "UTC+9:30" (not a valid format)
- "9:30am" (no timezone marker)

---

## API Response Conversion (CRITICAL)

**API endpoints return UTC timestamps** (ending in "Z" suffix)

### Conversion Rule
```
ADL Time = UTC Time + 9 hours 30 minutes
```

### Examples
| UTC Time | ADL Time | Context |
|----------|----------|---------|
| 05:47Z | 15:17 ADL | Health check response |
| 00:00Z | 09:30 ADL | Next day morning |
| 21:30Z | 07:00 ADL | Next day (crosses midnight) |

### Implementation
When displaying API response times to user:
1. Parse timestamp (format: `YYYY-MM-DDTHH:MM:SSZ`)
2. Add 9 hours 30 minutes
3. Display as "HH:MM ADL"

---

## Database Timestamps

All database DATETIME columns store **Adelaide local times** (no Z suffix in storage)

### Example
```sql
-- Database stores ADL time directly
INSERT INTO pending_trades (created_at) VALUES ('2026-05-28 15:17:00');
-- This is 15:17 ADL, NOT UTC
```

---

## Logging & Alerts

### Log Format
```
[15:17 ADL] Trade executed: EURUSD BUY @ 1.1635
[15:18 ADL] Stage 5 signal: BTCUSD SHORT
[15:19 ADL] Position tracking: 3 open trades
```

### ntfy.sh Notifications
All alerts include ADL timestamp in message body:
```
🎯 STAGE 5 SIGNAL: EURUSD
Entry: 1.1635
⏰ 15:17 ADL
```

---

## When to Apply Timezone Conversion

✅ **Always convert these API responses:**
- Health check endpoint: `curl http://localhost:3000/api/health`
- Price monitor status: `curl http://localhost:3000/api/monitor?q=status`
- Pending trades list: `curl http://localhost:3000/api/pending`
- Trade history: `curl http://localhost:3000/api/history`

❌ **Never convert (already ADL):**
- Database queries (stored as ADL)
- TradingView chart times (already ADL via Trading Hours)
- System log files (logged in ADL)

---

## Quick Reference

| Item | Format | Example |
|------|--------|---------|
| API Response Time | UTC, add 9:30 | `2026-05-28T05:47:07Z` → 15:17 ADL |
| Database DATETIME | ADL direct | `2026-05-28 15:17:00` |
| Log Output | ADL format | `[15:17 ADL] Trade queued` |
| Notification | ADL format | `⏰ 15:17 ADL` |
| Documentation | ADL notation | "09:30 ADL" |

---

**Last Updated**: 2026-05-28  
**Status**: ✅ Standard (do not ask for timezone again — convert automatically)
