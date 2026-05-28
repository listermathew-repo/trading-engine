'use client';

export default function RulesPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">📋 Stage 5 Trading Rules</h1>

        <div className="space-y-8">
          {/* EURUSD */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
            <h2 className="text-2xl font-bold text-blue-400 mb-4">EURUSD</h2>
            <div className="space-y-3 text-sm">
              <p><span className="font-semibold">Bias:</span> Neutral (wait for pullback + retest)</p>
              <p><span className="font-semibold">RSI Range:</span> 30 - 70 (no extremes)</p>
              <p><span className="font-semibold">Minimum R:R:</span> 2:1</p>
              <p><span className="font-semibold">Max Risk Per Trade:</span> $350</p>
              <p><span className="font-semibold">Pullback Zone:</span> 1.16200 - 1.16300</p>
              <p><span className="font-semibold">Entry Condition:</span> Price pulls back to 1.16200+, RSI bounces from oversold, retap of resistance at 1.16365</p>
            </div>
          </div>

          {/* XAUUSD */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
            <h2 className="text-2xl font-bold text-yellow-400 mb-4">XAUUSD (Gold)</h2>
            <div className="space-y-3 text-sm">
              <p><span className="font-semibold">Bias:</span> SHORT</p>
              <p><span className="font-semibold">RSI Threshold:</span> &lt; 30 (oversold entry)</p>
              <p><span className="font-semibold">Minimum R:R:</span> 3:1</p>
              <p><span className="font-semibold">Max Risk Per Trade:</span> $350</p>
              <p><span className="font-semibold">Support Level:</span> 4396.44</p>
              <p><span className="font-semibold">Resistance Level:</span> 4450.00</p>
              <p><span className="font-semibold">Entry Condition:</span> Price breaks below 4410, RSI &lt; 30, target 4396.44</p>
            </div>
          </div>

          {/* AUDUSD */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
            <h2 className="text-2xl font-bold text-green-400 mb-4">AUDUSD</h2>
            <div className="space-y-3 text-sm">
              <p><span className="font-semibold">Bias:</span> SHORT (manage position)</p>
              <p><span className="font-semibold">RSI Threshold:</span> Watch for reversal signals</p>
              <p><span className="font-semibold">Minimum R:R:</span> 3:1</p>
              <p><span className="font-semibold">Max Risk Per Trade:</span> $350</p>
              <p><span className="font-semibold">Current Position:</span> 423,076 units short @ 0.71750</p>
              <p><span className="font-semibold">Stop Level:</span> 0.72000</p>
              <p><span className="font-semibold">Target Level:</span> 0.70800</p>
            </div>
          </div>

          {/* BTCUSD */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
            <h2 className="text-2xl font-bold text-orange-400 mb-4">BTCUSD (Bitcoin)</h2>
            <div className="space-y-3 text-sm">
              <p><span className="font-semibold">Bias:</span> SHORT (scenario-dependent)</p>
              <p><span className="font-semibold">RSI Threshold:</span> &lt; 40 (overbought entry)</p>
              <p><span className="font-semibold">Minimum R:R:</span> 3:1</p>
              <p><span className="font-semibold">Max Risk Per Trade:</span> $350</p>
              <p><span className="font-semibold">Resistance Level:</span> 82132</p>
              <p><span className="font-semibold">Entry Condition:</span> Price bounces off resistance 82132, RSI &lt; 40, Scenario 2 pattern confirmation</p>
            </div>
          </div>

          {/* Account Requirements */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700 mt-8">
            <h2 className="text-2xl font-bold text-purple-400 mb-4">Account Requirements</h2>
            <div className="space-y-3 text-sm">
              <p><span className="font-semibold">Account Balance:</span> $110,430.38</p>
              <p><span className="font-semibold">Available Funds:</span> $106,131.79</p>
              <p><span className="font-semibold">Margin Available:</span> $6,644.81</p>
              <p><span className="font-semibold">Margin Buffer:</span> 94.11% (safe)</p>
              <p><span className="font-semibold">Max Simultaneous Positions:</span> 4 (EURUSD, XAUUSD, AUDUSD, BTCUSD)</p>
            </div>
          </div>

          {/* Daily Checklist */}
          <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
            <h2 className="text-2xl font-bold text-green-400 mb-4">✅ Daily Trading Checklist</h2>
            <ol className="space-y-2 text-sm list-decimal list-inside">
              <li>Verify health check: <code className="bg-black px-1 rounded">curl http://localhost:3000/api/health</code></li>
              <li>Check economic calendar for high-impact events (pause if within ±15 min)</li>
              <li>Load Auto Alert Generator on all 4 charts (TradingView)</li>
              <li>Start price monitor via dashboard button</li>
              <li>Monitor pending trades in approval queue</li>
              <li>Approve/reject trades within 5 minutes</li>
              <li>Stop monitor at 22:00 ADL</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}
