# Starting the Price Monitor — Quick Guide

**Current Time**: 15:17 ADL (Market ACTIVE)  
**Status**: Ready to deploy ✅

---

## Step 1: Open Dashboard in Browser

1. Open your browser
2. Navigate to: **http://localhost:3000**
3. Log in with your credentials (wiki-auth)

You should see the **TradingView Alert Dashboard** with stats and pending trades.

---

## Step 2: Get Session Cookie

Once logged in, your browser has an authenticated session. We'll use this to start the monitor.

**Option A: Copy the Cookie (Manual)**
1. Press `F12` to open Developer Tools
2. Go to **Application** tab
3. Click **Cookies** → **http://localhost:3000**
4. Look for a cookie named `wiki-auth` or `sessionid`
5. Copy the cookie value

**Option B: Save Cookie via Terminal** (Easier)
Run this command to save your session:
```bash
curl -c cookies.txt -b "wiki-auth=<PASTE_COOKIE_HERE>" http://localhost:3000
```

Or simpler - just run the curl commands below and the session will persist.

---

## Step 3: Start the Price Monitor

Open a terminal in the project directory and run:

```bash
curl -X POST http://localhost:3000/api/monitor \
  -H "Content-Type: application/json" \
  -d '{"action":"start"}' \
  -c cookies.txt
```

**Expected Response**:
```json
{
  "status": "started",
  "message": "Real-time price monitor started (5-sec interval)",
  "instruments": ["EURUSD", "AUDUSD", "XAUUSD", "BTCUSD"]
}
```

If you get a redirect to `/login`, you need to authenticate first (see Step 2).

---

## Step 4: Check Monitor Status

Once running, check the status every 5 seconds:

```bash
curl http://localhost:3000/api/monitor?q=status \
  -b cookies.txt | python3 -m json.tool
```

**Expected Output** (while monitoring):
```json
{
  "monitoring": true,
  "lastSignals": [
    {
      "symbol": "XAUUSD",
      "direction": "SELL",
      "entryPrice": 4410.50,
      "rr": 5.2,
      "confidence": 82,
      "timestamp": 1748413800000
    }
  ],
  "connectedAt": "2026-05-28T15:17:00Z"
}
```

---

## Step 5: Check Current Prices

View real-time bid/ask for all 4 instruments:

```bash
curl http://localhost:3000/api/monitor?q=prices \
  -b cookies.txt | python3 -m json.tool
```

**Expected Output**:
```json
{
  "monitoring": true,
  "prices": {
    "EURUSD": {
      "symbol": "EURUSD",
      "bid": 1.16353,
      "ask": 1.16365,
      "rsi": 45,
      "timestamp": 1748413800000
    },
    "XAUUSD": {
      "symbol": "XAUUSD",
      "bid": 4410.50,
      "ask": 4410.60,
      "rsi": 28,
      "timestamp": 1748413800000
    },
    "AUDUSD": {
      "symbol": "AUDUSD",
      "bid": 0.71250,
      "ask": 0.71265,
      "rsi": 35,
      "timestamp": 1748413800000
    },
    "BTCUSD": {
      "symbol": "BTCUSD",
      "bid": 77500.25,
      "ask": 77510.50,
      "rsi": 32,
      "timestamp": 1748413800000
    }
  },
  "timestamp": 1748413800000
}
```

---

## Step 6: View Pending Trades

Check trades queued for approval:

```bash
curl http://localhost:3000/api/pending \
  -b cookies.txt | python3 -m json.tool
```

**Example** (when Stage 5 signal triggers):
```json
{
  "count": 1,
  "trades": [
    {
      "id": "signal-XAUUSD-1748413800000",
      "symbol": "XAUUSD",
      "direction": "short",
      "entry_level": 4410.50,
      "stop_level": 4450.00,
      "retap_level": 4396.44,
      "confidence": 82,
      "status": "pending",
      "created_at": "2026-05-28T15:17:00Z"
    }
  ]
}
```

---

## Step 7: Approve a Trade

When a Stage 5 signal is queued, approve it:

```bash
curl -X POST http://localhost:3000/api/pending/signal-XAUUSD-1748413800000/approve \
  -b cookies.txt | python3 -m json.tool
```

**Expected Response**:
```json
{
  "status": "approved",
  "message": "Trade executed on Capital.com",
  "deal_reference": "DEAL_12345",
  "execution_price": 4410.50
}
```

You'll receive an ntfy.sh alert on your phone immediately.

---

## Step 8: Stop the Monitor

When you're done trading:

```bash
curl -X POST http://localhost:3000/api/monitor \
  -H "Content-Type: application/json" \
  -d '{"action":"stop"}' \
  -b cookies.txt
```

**Expected Response**:
```json
{
  "status": "stopped"
}
```

---

## Complete Monitoring Loop (Bash Script)

Save this as `monitor.sh` and run `bash monitor.sh`:

```bash
#!/bin/bash

# Create session file
COOKIES="monitor-session.txt"

echo "🔐 Authenticating..."
curl -s http://localhost:3000 -c $COOKIES > /dev/null

echo "🚀 Starting price monitor..."
curl -s -X POST http://localhost:3000/api/monitor \
  -H "Content-Type: application/json" \
  -d '{"action":"start"}' \
  -b $COOKIES | python3 -m json.tool

echo ""
echo "📊 Monitoring prices (updating every 5 sec)..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Time: $(date '+%H:%M:%S ADL')"
  echo ""
  
  # Show status
  echo "📈 Monitor Status:"
  curl -s http://localhost:3000/api/monitor?q=status \
    -b $COOKIES | python3 -m json.tool | head -20
  
  echo ""
  echo "💰 Current Prices:"
  curl -s http://localhost:3000/api/monitor?q=prices \
    -b $COOKIES | python3 -c "
import sys, json
data = json.load(sys.stdin)
for symbol, price in data.get('prices', {}).items():
    print(f'  {symbol}: {price[\"bid\"]:.5f} / {price[\"ask\"]:.5f}')
"
  
  echo ""
  echo "📋 Pending Trades:"
  curl -s http://localhost:3000/api/pending \
    -b $COOKIES | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['count'] == 0:
    print('  (None - waiting for Stage 5 signals)')
else:
    for trade in data['trades']:
        print(f'  {trade[\"symbol\"]} {trade[\"direction\"].upper()} @ {trade[\"entry_level\"]:.2f}')
"
  
  sleep 10
done
```

Run it:
```bash
bash monitor.sh
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **curl: 307 Temporary Redirect** | You're not authenticated. Run step 2 first (log in via browser) |
| **"monitoring": false** | Monitor isn't running. Run the start command (step 3) |
| **No prices shown** | Capital.com WebSocket not connected. Check internet & credentials |
| **Pending trades not appearing** | Stage 5 conditions haven't been met. Monitor will queue them automatically |
| **ntfy alerts not received** | Check NTFY_URL in .env.local; phone notification permissions |

---

## Daily Ritual (09:00 ADL - Before Trading)

```bash
# 1. Verify system health
curl -s http://localhost:3000/api/health | python3 -m json.tool

# 2. Log in to dashboard
# → http://localhost:3000

# 3. Start price monitor
curl -X POST http://localhost:3000/api/monitor \
  -H "Content-Type: application/json" \
  -d '{"action":"start"}' \
  -b cookies.txt

# 4. Run monitoring script
bash monitor.sh
```

---

## What the Price Monitor Does

✅ **Every 5 seconds**:
- Fetches real-time prices from Capital.com WebSocket
- Checks if prices match Stage 5 entry conditions
- **AUTO-QUEUES trades** when conditions are met
- Sends **ntfy.sh alert** to your phone

✅ **Your job**:
- Receive alert notification
- Review the queued trade in `/api/pending`
- **Approve** the trade → Executes on Capital.com
- Or **reject** if conditions changed

✅ **Stage 5 Conditions** (hardcoded):
- **EURUSD**: Neutral (2:1 R:R minimum)
- **XAUUSD**: SHORT (3:1 R:R minimum, RSI < 30)
- **BTCUSD**: SHORT (3:1 R:R minimum, Scenario 2 pattern)
- **AUDUSD**: SHORT (3:1 R:R minimum, manage position)

---

**Status**: Ready to go! 🚀  
**Next Step**: Open http://localhost:3000 and log in
