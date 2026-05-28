@echo off
REM Start Price Monitor via authenticated browser session
REM This gets a session, then uses it to start the monitor

cd /d "C:\Users\mathe\Documents\tradingview-mcp"

echo.
echo ========================================
echo   PRICE MONITOR STARTUP
echo ========================================
echo.

echo [*] Getting authenticated session...
curl -s http://localhost:3000/ -c cookies.txt > nul

echo [*] Starting price monitor...
echo.

curl -X POST http://localhost:3000/api/monitor ^
  -H "Content-Type: application/json" ^
  -d "{""action"":""start""}" ^
  -b cookies.txt

echo.
echo [*] Monitor started! Checking status...
timeout /t 2 /nobreak
echo.

curl http://localhost:3000/api/monitor?q=status -b cookies.txt

echo.
echo ========================================
echo   MONITOR RUNNING
echo ========================================
echo.
echo Monitor is now listening to Capital.com WebSocket
echo Instruments: EURUSD, AUDUSD, XAUUSD, BTCUSD
echo Check interval: Every 5 seconds
echo Stage 5 detection: Enabled
echo.
echo When signals trigger:
echo   1. ntfy alert sent to your phone
echo   2. Trade queued in pending_trades table
echo   3. You approve via /api/pending/[id]/approve
echo.
pause
