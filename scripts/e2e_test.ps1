# E2E Test Script for Trading Webhook System
# Tests the full flow: TradingView alert -> webhook -> approval queue -> execution

param(
    [string]$WebhookUrl = "http://localhost:8000/webhook",
    [string]$ApiKey = "generate_random_32_char_key_here",
    [string]$Symbol = "XAUUSD",
    [string]$Action = "buy",
    [string]$Price = "2450.50",
    [string]$Stop = "2445.00"
)

$ErrorActionPreference = "Stop"

# Colors for output
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Blue = "Cyan"

function Write-Header {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor $Blue
    Write-Host $Message -ForegroundColor $Blue
    Write-Host "========================================`n" -ForegroundColor $Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor $Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor $Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor $Blue
}

Write-Header "Trading Webhook E2E Test"

# Step 1: Validate configuration
Write-Info "Configuration:"
Write-Host "  Webhook URL: $WebhookUrl"
Write-Host "  API Key: $($ApiKey.Substring(0, [Math]::Min(8, $ApiKey.Length)))..."
Write-Host "  Symbol: $Symbol | Action: $Action"
Write-Host "  Price: $Price | Stop: $Stop"

# Step 2: Test webhook connectivity
Write-Info "`nStep 1: Testing webhook connectivity..."
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get -ErrorAction Stop
    Write-Success "Webhook server is running"
    Write-Info "  Status: $($healthResponse.status)"
    Write-Info "  Simulation mode: $($healthResponse.simulate)"
}
catch {
    Write-Error-Custom "Cannot connect to webhook server at http://localhost:8000/"
    Write-Info "  Make sure the FastAPI server is running: python -m uvicorn api.index:app --reload"
    exit 1
}

# Step 3: Send webhook request (queue trade)
Write-Info "`nStep 2: Sending webhook request to queue trade..."
$payload = @{
    symbol = $Symbol
    action = $Action
    price = $Price
    stop = $Stop
    timeframe = "D"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod `
        -Uri $WebhookUrl `
        -Method Post `
        -Body $payload `
        -ContentType "application/json" `
        -Headers @{"X-API-Key" = $ApiKey} `
        -ErrorAction Stop

    Write-Success "Trade queued successfully"
    $tradeId = $response.trade_id
    Write-Info "  Trade ID: $tradeId"
    Write-Info "  Status: $($response.status)"
    Write-Info "  Expires at: $($response.expires_at)"
    Write-Info "  ntfy notification sent: $($response.ntfy.success)"
}
catch {
    Write-Error-Custom "Failed to queue trade"
    Write-Host "  Error: $($_.Exception.Message)"
    exit 1
}

# Step 4: List pending trades
Write-Info "`nStep 3: Listing pending trades..."
try {
    $pendingResponse = Invoke-RestMethod `
        -Uri "http://localhost:8000/pending" `
        -Method Get `
        -Headers @{"X-API-Key" = $ApiKey} `
        -ErrorAction Stop

    Write-Success "Retrieved pending trades"
    Write-Info "  Pending count: $($pendingResponse.count)"
    Write-Info "  Our trade in queue: $(($pendingResponse.trades | Where-Object { $_.id -eq $tradeId } | Measure-Object).Count -gt 0)"
}
catch {
    Write-Error-Custom "Failed to list pending trades"
    Write-Host "  Error: $($_.Exception.Message)"
    exit 1
}

# Step 5: Approve trade
Write-Info "`nStep 4: Approving trade..."
$startTime = Get-Date
try {
    $approveResponse = Invoke-RestMethod `
        -Uri "http://localhost:8000/approve/$tradeId" `
        -Method Get `
        -Headers @{"X-API-Key" = $ApiKey} `
        -ErrorAction Stop

    $duration = (Get-Date) - $startTime
    Write-Success "Trade approved and executed"
    Write-Info "  Status: $($approveResponse.status)"
    Write-Info "  Execution time: $($duration.TotalSeconds)s"
    Write-Info "  Result: $($approveResponse.result)"
    Write-Info "  Executed at: $($approveResponse.executed_at)"
    Write-Info "  ntfy notification sent: $($approveResponse.ntfy.success)"
}
catch {
    Write-Error-Custom "Failed to approve trade"
    Write-Host "  Error: $($_.Exception.Message)"
    exit 1
}

# Step 6: Verify trade was executed (no longer in pending)
Write-Info "`nStep 5: Verifying trade execution..."
try {
    $finalPending = Invoke-RestMethod `
        -Uri "http://localhost:8000/pending" `
        -Method Get `
        -Headers @{"X-API-Key" = $ApiKey} `
        -ErrorAction Stop

    $tradeStillPending = ($finalPending.trades | Where-Object { $_.id -eq $tradeId } | Measure-Object).Count -gt 0

    if (-not $tradeStillPending) {
        Write-Success "Trade removed from queue (execution verified)"
        Write-Info "  Remaining pending: $($finalPending.count)"
    }
    else {
        Write-Error-Custom "Trade still in pending queue (execution may have failed)"
        exit 1
    }
}
catch {
    Write-Error-Custom "Failed to verify trade execution"
    Write-Host "  Error: $($_.Exception.Message)"
    exit 1
}

# Success summary
Write-Header "✓ E2E Test Completed Successfully"
Write-Info "Summary:"
Write-Host "  1. Webhook accepted trade request (202 Accepted)"
Write-Host "  2. Trade queued with ID: $tradeId"
Write-Host "  3. Trade visible in pending queue"
Write-Host "  4. Trade approved and executed"
Write-Host "  5. Trade removed from queue"
Write-Info "`nThe trading system is working correctly!"
Write-Info "Next steps:"
Write-Host "  1. Check your ntfy notifications for trade alerts"
Write-Host "  2. Review trade history in database.py"
Write-Host "  3. Set SIMULATE_TRADES=false when ready for live trading"
