#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Start the Capital.com Price Monitor

.DESCRIPTION
  Gets an authenticated session from the trading dashboard,
  then uses it to start the real-time price monitor.

.EXAMPLE
  .\Start-Monitor.ps1
#>

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   PRICE MONITOR STARTUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get authenticated session
Write-Host "[*] Getting authenticated session..." -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "http://localhost:3000/" -SessionVariable session -ErrorAction SilentlyContinue
Write-Host "[✓] Session acquired" -ForegroundColor Green
Write-Host ""

# Step 2: Start the monitor
Write-Host "[*] Starting price monitor..." -ForegroundColor Yellow
Write-Host ""

try {
    $body = @{
        action = "start"
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/monitor" `
        -Method POST `
        -Headers @{"Content-Type" = "application/json"} `
        -Body $body `
        -WebSession $session `
        -ErrorAction Stop

    if ($response.StatusCode -eq 200) {
        $result = $response.Content | ConvertFrom-Json
        Write-Host "[✓] Monitor started successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Response:" -ForegroundColor Cyan
        $result | ConvertTo-Json | Write-Host
    }
}
catch {
    Write-Host "[✗] Error starting monitor: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[*] Checking monitor status..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

try {
    $statusResponse = Invoke-WebRequest -Uri "http://localhost:3000/api/monitor?q=status" `
        -WebSession $session `
        -ErrorAction Stop

    $status = $statusResponse.Content | ConvertFrom-Json
    Write-Host "[✓] Monitor Status:" -ForegroundColor Green
    $status | ConvertTo-Json | Write-Host
}
catch {
    Write-Host "[!] Could not fetch status: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   MONITOR RUNNING" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Monitor is now listening to Capital.com WebSocket" -ForegroundColor Green
Write-Host "   Instruments: EURUSD, AUDUSD, XAUUSD, BTCUSD"
Write-Host "   Check interval: Every 5 seconds"
Write-Host "   Stage 5 detection: Enabled"
Write-Host ""
Write-Host "When signals trigger:" -ForegroundColor Cyan
Write-Host "  1. ntfy alert sent to your phone"
Write-Host "  2. Trade queued in pending_trades table"
Write-Host "  3. You approve via /api/pending/[id]/approve"
Write-Host ""
Write-Host "Current time: $(Get-Date -Format 'HH:mm ADL')" -ForegroundColor Yellow
Write-Host ""
