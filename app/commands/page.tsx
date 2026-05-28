'use client';

export default function CommandsPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">⚙️ Trading System API Commands</h1>

        <div className="space-y-8">
          {/* Health Check */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-green-400 mb-4">Health Check</h2>
            <div className="bg-black p-4 rounded mb-3 font-mono text-sm overflow-x-auto">
              <div>curl -s http://localhost:3000/api/health | python3 -m json.tool</div>
            </div>
            <p className="text-sm text-gray-300 mb-2"><span className="font-semibold">Response includes:</span> Component status (webhook, database, capital_com, ntfy), last webhook received, last trade executed, error count</p>
            <p className="text-sm text-yellow-300">🔔 Run this daily at 09:00 ADL before starting monitor</p>
          </div>

          {/* Start Price Monitor */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-blue-400 mb-4">Start Price Monitor</h2>
            <div className="bg-black p-4 rounded mb-3 font-mono text-sm overflow-x-auto">
              <div>curl -X POST http://localhost:3000/api/monitor \</div>
              <div>&nbsp;&nbsp;-H "Content-Type: application/json" \</div>
              <div>&nbsp;&nbsp;-d '{`{"action":"start"}`}'</div>
            </div>
            <p className="text-sm text-gray-300 mb-2"><span className="font-semibold">What it does:</span> Connects to Capital.com WebSocket, subscribes to EURUSD, XAUUSD, AUDUSD, BTCUSD, checks Stage 5 conditions every 5 seconds</p>
            <p className="text-sm text-yellow-300">⭐ Or click START button on dashboard</p>
          </div>

          {/* Check Monitor Status */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-blue-400 mb-4">Check Monitor Status</h2>
            <div className="bg-black p-4 rounded mb-3 font-mono text-sm overflow-x-auto">
              <div>curl http://localhost:3000/api/monitor?q=status</div>
            </div>
            <p className="text-sm text-gray-300"><span className="font-semibold">Returns:</span> monitoring (true/false), lastSignals (Stage 5 triggers), connectedAt (connection timestamp)</p>
          </div>

          {/* Get Real-time Prices */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-blue-400 mb-4">Get Real-time Prices</h2>
            <div className="bg-black p-4 rounded mb-3 font-mono text-sm overflow-x-auto">
              <div>curl http://localhost:3000/api/monitor?q=prices</div>
            </div>
            <p className="text-sm text-gray-300"><span className="font-semibold">Returns:</span> Current bid/ask for all 4 instruments, RSI values, timestamp</p>
          </div>

          {/* Stop Price Monitor */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-red-400 mb-4">Stop Price Monitor</h2>
            <div className="bg-black p-4 rounded mb-3 font-mono text-sm overflow-x-auto">
              <div>curl -X POST http://localhost:3000/api/monitor \</div>
              <div>&nbsp;&nbsp;-H "Content-Type: application/json" \</div>
              <div>&nbsp;&nbsp;-d '{`{"action":"stop"}`}'</div>
            </div>
            <p className="text-sm text-gray-300">⏹️ Stop monitoring. Run at 22:00 ADL or when done trading</p>
          </div>

          {/* Pending Trades */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-yellow-400 mb-4">View Pending Trades</h2>
            <div className="bg-black p-4 rounded mb-3 font-mono text-sm overflow-x-auto">
              <div>curl http://localhost:3000/api/pending</div>
            </div>
            <p className="text-sm text-gray-300"><span className="font-semibold">Returns:</span> All trades in approval queue (queued by Stage 5 signals)</p>
            <p className="text-sm text-yellow-300">💼 Or view on dashboard in "PENDING APPROVAL" section</p>
          </div>

          {/* Approve Trade */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-green-400 mb-4">Approve & Execute Trade</h2>
            <div className="bg-black p-4 rounded mb-3 font-mono text-sm overflow-x-auto">
              <div>curl -X POST http://localhost:3000/api/pending/TRADE_ID/approve</div>
            </div>
            <p className="text-sm text-gray-300 mb-2"><span className="font-semibold">What it does:</span> Executes trade on Capital.com, updates status to "executed", sends ntfy alert</p>
            <p className="text-sm text-yellow-300">✅ Or click Approve button in dashboard (recommended)</p>
          </div>

          {/* Reject Trade */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-gray-400 mb-4">Reject Trade</h2>
            <div className="bg-black p-4 rounded mb-3 font-mono text-sm overflow-x-auto">
              <div>curl -X POST http://localhost:3000/api/pending/TRADE_ID/reject</div>
            </div>
            <p className="text-sm text-gray-300 mb-2"><span className="font-semibold">What it does:</span> Cancels trade, updates status to "rejected"</p>
            <p className="text-sm text-yellow-300">❌ Or click Reject button in dashboard (recommended)</p>
          </div>

          {/* Get Positions */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-purple-400 mb-4">Get Current Positions & Account</h2>
            <div className="bg-black p-4 rounded mb-3 font-mono text-sm overflow-x-auto">
              <div>curl http://localhost:3000/api/positions</div>
            </div>
            <p className="text-sm text-gray-300"><span className="font-semibold">Returns:</span> Open positions (symbol, entry, current, P&L), account balance, equity, margin</p>
            <p className="text-sm text-yellow-300">📊 Automatically displayed on dashboard</p>
          </div>

          {/* Daily Routine */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700 mt-8">
            <h2 className="text-2xl font-bold text-green-400 mb-4">📅 Daily Trading Routine (08:55 ADL)</h2>
            <ul className="space-y-3 text-sm list-disc list-inside">
              <li>Health check: <code className="bg-black px-1 rounded">curl -s http://localhost:3000/api/health</code></li>
              <li>Log in to http://localhost:3000 via browser</li>
              <li>Click START button on dashboard to begin price monitoring</li>
              <li>Load Auto Alert Generator on TradingView (XAUUSD, BTCUSD charts)</li>
              <li>Monitor dashboard for Stage 5 signals (every 5 seconds)</li>
              <li>Review & approve/reject trades in PENDING APPROVAL section</li>
              <li>At 22:00 ADL: Click STOP button to end monitoring</li>
            </ul>
          </div>

          {/* Troubleshooting */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-red-400 mb-4">❌ Troubleshooting</h2>
            <div className="space-y-3 text-sm">
              <div>
                <p className="font-semibold text-yellow-300">Monitor won't start?</p>
                <p className="text-gray-300">→ Log in via browser first, then start monitor from dashboard button</p>
              </div>
              <div>
                <p className="font-semibold text-yellow-300">No prices showing?</p>
                <p className="text-gray-300">→ Check Capital.com internet connection & credentials in .env.local</p>
              </div>
              <div>
                <p className="font-semibold text-yellow-300">Trades not appearing?</p>
                <p className="text-gray-300">→ Stage 5 conditions haven't been met. Monitor is working, waiting for signals</p>
              </div>
              <div>
                <p className="font-semibold text-yellow-300">No ntfy alerts?</p>
                <p className="text-gray-300">→ Check ntfy.sh is accessible & notifications enabled on phone</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
