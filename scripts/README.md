# Trading Engine Scripts

## e2e_test.ps1

End-to-end test script that verifies the complete trading workflow.

### Prerequisites

- FastAPI server running on `http://localhost:8000`
- Valid `WEBHOOK_API_KEY` environment variable set
- Trading engine initialized with database

### Usage

```powershell
# Run with default settings (test XAUUSD BUY)
.\e2e_test.ps1

# Run with custom parameters
.\e2e_test.ps1 -WebhookUrl "http://localhost:8000/webhook" `
              -ApiKey "your-32-char-key" `
              -Symbol "EURUSD" `
              -Action "sell" `
              -Price "1.0850" `
              -Stop "1.0800"
```

### What It Tests

1. **Server Connectivity** — Verifies webhook server is running
2. **Trade Queuing** — Sends webhook alert and verifies trade is queued (202 response)
3. **Pending Queue** — Confirms trade appears in approval queue
4. **Trade Approval** — Approves trade execution
5. **Trade History** — Verifies trade is logged and removed from pending queue

### Expected Output

```
========================================
Trading Webhook E2E Test
========================================

ℹ Configuration:
  Webhook URL: http://localhost:8000/webhook
  API Key: generate_...
  Symbol: XAUUSD | Action: buy
  Price: 2450.50 | Stop: 2445.00

ℹ Step 1: Testing webhook connectivity...
✓ Webhook server is running
  Status: ok
  Simulation mode: True

ℹ Step 2: Sending webhook request to queue trade...
✓ Trade queued successfully
  Trade ID: 12345-67890-abcdef
  Status: accepted
  Expires at: 2026-05-20T15:05:30.123456

ℹ Step 3: Listing pending trades...
✓ Retrieved pending trades
  Pending count: 1
  Our trade in queue: True

ℹ Step 4: Approving trade...
✓ Trade approved and executed
  Status: ok
  Execution time: 0.123s
  Result: [SIMULATED] BUY XAUUSD @ 2450.5

ℹ Step 5: Verifying trade execution...
✓ Trade removed from queue (execution verified)
  Remaining pending: 0

========================================
✓ E2E Test Completed Successfully
========================================
```

### Troubleshooting

**"Cannot connect to webhook server"**
- Start the FastAPI server: `python -m uvicorn api.index:app --reload`

**"Failed to queue trade" - 401 error**
- Ensure `WEBHOOK_API_KEY` environment variable is set
- Verify the API key in the script matches the env var

**"Trade still in pending queue"**
- Check if Capital.com API is accessible (if not in simulation mode)
- Review error logs for trade execution failures

### Security Notes

- Do NOT commit actual API keys to version control
- The script shows only the first 8 characters of the API key
- Always test in simulation mode first (`SIMULATE_TRADES=true`)
- Review ntfy notifications to verify alerts are working
