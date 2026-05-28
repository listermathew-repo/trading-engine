#!/bin/bash

# TradingView Webhook cURL Examples
# Run these commands to test your webhook endpoint

BASE_URL="http://localhost:3000/api/alerts"

echo "TradingView Webhook Testing Examples"
echo "===================================="
echo ""
echo "Base URL: $BASE_URL"
echo ""

# ============================================
# 1. VALID REQUESTS
# ============================================

echo "=== 1. VALID REQUESTS ==="
echo ""

# 1.1 Simple Long Trade
echo "1.1 Long Trade Alert (EURUSD)"
echo "Command:"
echo "curl -X POST $BASE_URL \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"ticker\": \"EURUSD\", \"direction\": \"long\", \"entry_level\": 1.16353, \"stop_level\": 1.16170, \"take_profit\": 1.16902, \"setup_type\": \"LTF CHOCH FVG\", \"timeframe\": \"15\"}'"
echo ""
echo "Running..."
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "EURUSD",
    "direction": "long",
    "entry_level": 1.16353,
    "stop_level": 1.16170,
    "take_profit": 1.16902,
    "setup_type": "LTF CHOCH FVG",
    "timeframe": "15"
  }' | jq '.'
echo ""
echo ""

# 1.2 Short Trade
echo "1.2 Short Trade Alert (AAPL)"
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "direction": "short",
    "entry_level": 150.50,
    "stop_level": 151.20,
    "take_profit": 149.30,
    "setup_type": "Resistance Breakout",
    "timeframe": "60"
  }' | jq '.'
echo ""
echo ""

# 1.3 Crypto Trade
echo "1.3 Crypto Trade Alert (BTCUSD)"
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "BTCUSD",
    "direction": "long",
    "entry_level": 42500.00,
    "stop_level": 42000.00,
    "take_profit": 45000.00,
    "setup_type": "Support Bounce",
    "timeframe": "D"
  }' | jq '.'
echo ""
echo ""

# ============================================
# 2. VALIDATION ERRORS
# ============================================

echo "=== 2. VALIDATION ERRORS (Expected 400) ==="
echo ""

# 2.1 Invalid Direction
echo "2.1 Invalid Direction"
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "EURUSD",
    "direction": "invalid",
    "entry_level": 1.16353,
    "stop_level": 1.16170,
    "take_profit": 1.16902,
    "setup_type": "Test",
    "timeframe": "15"
  }' | jq '.'
echo ""
echo ""

# 2.2 Missing Ticker
echo "2.2 Missing Ticker"
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "direction": "long",
    "entry_level": 1.16353,
    "stop_level": 1.16170,
    "take_profit": 1.16902,
    "setup_type": "Test",
    "timeframe": "15"
  }' | jq '.'
echo ""
echo ""

# 2.3 Negative Entry Level
echo "2.3 Negative Entry Level"
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "EURUSD",
    "direction": "long",
    "entry_level": -1.16353,
    "stop_level": 1.16170,
    "take_profit": 1.16902,
    "setup_type": "Test",
    "timeframe": "15"
  }' | jq '.'
echo ""
echo ""

# 2.4 Zero Entry Level
echo "2.4 Zero Entry Level"
curl -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "EURUSD",
    "direction": "long",
    "entry_level": 0,
    "stop_level": 1.16170,
    "take_profit": 1.16902,
    "setup_type": "Test",
    "timeframe": "15"
  }' | jq '.'
echo ""
echo ""

# ============================================
# 3. GET ENDPOINT
# ============================================

echo "=== 3. GET ENDPOINT ==="
echo ""
echo "3.1 Get Recent Alerts and Stats"
curl -X GET $BASE_URL | jq '.'
echo ""
echo ""

# ============================================
# 4. SILENT MODE (For Scripting)
# ============================================

echo "=== 4. SILENT MODE (No Output) ==="
echo ""
echo "To send alerts silently without output, use -s flag:"
echo "curl -s -X POST $BASE_URL -H 'Content-Type: application/json' -d '{...}'"
echo ""

# Example: Send 5 alerts quickly without output
echo "4.1 Sending 5 test alerts (silent mode)..."
for i in {1..5}; do
  curl -s -X POST $BASE_URL \
    -H "Content-Type: application/json" \
    -d "{
      \"ticker\": \"EURUSD\",
      \"direction\": \"long\",
      \"entry_level\": 1.16353,
      \"stop_level\": 1.16170,
      \"take_profit\": 1.16902,
      \"setup_type\": \"Test $i\",
      \"timeframe\": \"15\"
    }" > /dev/null
  echo "  ✓ Alert $i sent"
done
echo ""

# ============================================
# 5. ADVANCED EXAMPLES
# ============================================

echo "=== 5. ADVANCED EXAMPLES ==="
echo ""

# 5.1 Save response to file
echo "5.1 Save Response to File"
echo "Command:"
echo "curl -X POST $BASE_URL -H 'Content-Type: application/json' -d '{...}' > response.json"
echo ""

# 5.2 Measure response time
echo "5.2 Measure Response Time"
echo "Command:"
echo "curl -w 'Time: %{time_total}s\n' -X POST $BASE_URL -H 'Content-Type: application/json' -d '{...}'"
echo ""
curl -w 'Total Time: %{time_total}s\n' -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "EURUSD",
    "direction": "long",
    "entry_level": 1.16353,
    "stop_level": 1.16170,
    "take_profit": 1.16902,
    "setup_type": "Performance Test",
    "timeframe": "15"
  }' > /dev/null
echo ""

# 5.3 Include response headers
echo "5.3 Include Response Headers"
echo "Command:"
echo "curl -i -X POST $BASE_URL -H 'Content-Type: application/json' -d '{...}'"
echo ""

# 5.4 Follow redirects
echo "5.4 Follow Redirects (if needed)"
echo "Command:"
echo "curl -L -X POST $BASE_URL -H 'Content-Type: application/json' -d '{...}'"
echo ""

echo "=== Examples Complete ==="
echo ""
echo "Tips:"
echo "  - Use 'jq' for pretty-printing JSON (install: brew install jq)"
echo "  - Use '-s' flag to silence output"
echo "  - Use '-w' flag to add timing information"
echo "  - Use '-i' flag to include response headers"
echo "  - Use '-X' to specify HTTP method (POST, GET, etc)"
echo "  - Use '-H' to add headers"
echo "  - Use '-d' to send request body"
echo ""
