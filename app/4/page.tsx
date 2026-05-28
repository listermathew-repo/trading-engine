'use client';

import { useEffect, useState } from 'react';

interface PendingTrade {
  id: string;
  symbol: string;
  direction: string;
  entry_level: number;
  stop_level: number;
  retap_level: number;
  risk_amount: number;
  confidence: number;
  rr: number;
  created_at: string;
}

interface AccountData {
  balance: number;
  equity: number;
  realizedPnL: number;
  unrealizedPnL: number;
  margin: number;
  availableFunds: number;
  marginBuffer: number;
}

interface Position {
  symbol: string;
  direction: string;
  size: number;
  entry: number;
  current: number;
  stop: number;
  target: number;
  pnl: number;
  pnlPercent: number;
  tradValue: number;
}

export default function DesignFour() {
  const [monitorStatus, setMonitorStatus] = useState<'running' | 'stopped'>('stopped');
  const [pendingTrades, setPendingTrades] = useState<PendingTrade[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [account, setAccount] = useState<AccountData | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 5000);
    return () => clearInterval(interval);
  }, []);

  async function fetchDashboardData() {
    try {
      const statusRes = await fetch('/api/monitor?q=status');
      if (statusRes.ok) setMonitorStatus('running');
      const posRes = await fetch('/api/positions');
      if (posRes.ok) {
        const posData = await posRes.json();
        setPositions(posData.positions || []);
        setAccount(posData.account);
      }
      const tradesRes = await fetch('/api/pending');
      if (tradesRes.ok) {
        const tradesData = await tradesRes.json();
        setPendingTrades(tradesData.trades || []);
      }
      setLastUpdate(new Date().toLocaleTimeString('en-AU', { timeZone: 'Australia/Adelaide' }));
    } catch (err) {
      setMonitorStatus('stopped');
    }
  }

  async function toggleMonitor() {
    const action = monitorStatus === 'running' ? 'stop' : 'start';
    try {
      const res = await fetch('/api/monitor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      });
      if (res.ok) {
        setMonitorStatus(action === 'start' ? 'running' : 'stopped');
        fetchDashboardData();
      }
    } catch (err) {
      console.error(err);
    }
  }

  async function approveTrade(tradeId: string) {
    try {
      const res = await fetch(`/api/pending/${tradeId}/approve`, { method: 'POST' });
      if (res.ok) fetchDashboardData();
    } catch (err) {
      console.error(err);
    }
  }

  async function rejectTrade(tradeId: string) {
    try {
      const res = await fetch(`/api/pending/${tradeId}/reject`, { method: 'POST' });
      if (res.ok) fetchDashboardData();
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header with colorful accent */}
        <div className="mb-8">
          <h1 className="text-4xl font-black mb-2">
            <span className="bg-gradient-to-r from-pink-600 via-purple-600 to-blue-600 bg-clip-text text-transparent">
              DESIGN 4: Colorful Analytics
            </span>
          </h1>
          <div className="flex justify-between items-center mt-4">
            <p className="text-gray-600">Last update: {lastUpdate} ADL</p>
            <button onClick={toggleMonitor} className={`px-6 py-2 rounded-lg font-bold text-white ${monitorStatus === 'running' ? 'bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700' : 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700'}`}>
              {monitorStatus === 'running' ? '⏹ STOP' : '▶ START'}
            </button>
          </div>
        </div>

        {/* Colorful Metrics Grid */}
        {account && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[
              { label: 'Total Balance', value: account.balance, icon: '💰', colors: 'from-blue-400 to-blue-600', textColor: 'text-blue-600' },
              { label: 'Equity', value: account.equity, icon: '📊', colors: 'from-purple-400 to-purple-600', textColor: 'text-purple-600' },
              { label: 'Unrealized P&L', value: account.unrealizedPnL, icon: '📈', colors: account.unrealizedPnL >= 0 ? 'from-green-400 to-emerald-600' : 'from-red-400 to-pink-600', textColor: account.unrealizedPnL >= 0 ? 'text-green-600' : 'text-red-600' },
              { label: 'Margin Buffer', value: account.marginBuffer, icon: '🛡️', colors: 'from-yellow-400 to-orange-600', textColor: 'text-orange-600' },
            ].map((m, i) => (
              <div key={i} className="bg-white rounded-xl shadow-lg border-2 border-b-4 overflow-hidden hover:shadow-xl transition">
                <div className={`h-1 bg-gradient-to-r ${m.colors}`}></div>
                <div className="p-6">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-gray-600 text-sm font-semibold uppercase mb-2">{m.label}</p>
                      <p className={`text-3xl font-black ${m.textColor}`}>
                        ${typeof m.value === 'number' ? m.value.toLocaleString('en-US', {maximumFractionDigits: 2}) : m.value}
                      </p>
                    </div>
                    <span className="text-3xl">{m.icon}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Market Cards with Progress Bars */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Market Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { symbol: 'EURUSD', price: 1.16076, rsi: 69.63, color: 'from-yellow-400 to-orange-500', percentage: 69 },
              { symbol: 'XAUUSD', price: 4380.03, rsi: 46.88, color: 'from-blue-400 to-blue-500', percentage: 46 },
              { symbol: 'BTCUSD', price: 73097.98, rsi: 59.19, color: 'from-orange-400 to-orange-500', percentage: 59 },
              { symbol: 'AUDUSD', price: 0.71212, rsi: 35.0, color: 'from-green-400 to-emerald-500', percentage: 35 },
            ].map((inst) => (
              <div key={inst.symbol} className="bg-white rounded-xl shadow-md p-5 border-l-4 border-gray-300">
                <div className="flex justify-between items-center mb-3">
                  <p className="font-bold text-gray-900">{inst.symbol}</p>
                  <p className="text-lg font-mono font-bold text-gray-700">{inst.price.toLocaleString()}</p>
                </div>
                <div className="mb-3">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-600">RSI</span>
                    <span className="font-bold">{inst.rsi.toFixed(1)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div className={`h-full bg-gradient-to-r ${inst.color}`} style={{width: `${inst.percentage}%`}}></div>
                  </div>
                </div>
                <p className="text-xs text-gray-500">
                  {inst.rsi > 70 ? '🔴 Overbought' : inst.rsi < 30 ? '🟢 Oversold' : '🟡 Neutral'}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Positions Detailed View */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Open Positions</h2>
          <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
            {positions.length === 0 ? (
              <div className="p-12 text-center">
                <p className="text-gray-500 text-lg">No open positions</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gradient-to-r from-purple-50 to-blue-50 border-b-2 border-purple-200">
                    <tr>
                      <th className="px-6 py-4 text-left font-bold text-purple-900">Symbol</th>
                      <th className="px-6 py-4 text-left font-bold text-purple-900">Direction</th>
                      <th className="px-6 py-4 text-right font-bold text-purple-900">Entry</th>
                      <th className="px-6 py-4 text-right font-bold text-purple-900">Current</th>
                      <th className="px-6 py-4 text-right font-bold text-purple-900">P&L %</th>
                      <th className="px-6 py-4 text-right font-bold text-purple-900">P&L $</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.map((pos) => (
                      <tr key={pos.symbol} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="px-6 py-4 font-bold text-gray-900">{pos.symbol}</td>
                        <td className="px-6 py-4"><span className={`px-3 py-1 rounded-full text-xs font-bold ${pos.direction === 'short' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>{pos.direction.toUpperCase()}</span></td>
                        <td className="px-6 py-4 text-right font-mono">{pos.entry.toFixed(5)}</td>
                        <td className="px-6 py-4 text-right font-mono font-bold">{pos.current.toFixed(5)}</td>
                        <td className="px-6 py-4 text-right"><span className="text-green-600 font-bold">+{pos.pnlPercent.toFixed(2)}%</span></td>
                        <td className="px-6 py-4 text-right font-bold text-green-600">+${pos.pnl.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Critical Pending Trades Section */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-red-700">🚨 PENDING APPROVAL</h2>
            <span className="bg-gradient-to-r from-red-500 to-pink-600 text-white px-4 py-2 rounded-lg font-bold text-xl">{pendingTrades.length}</span>
          </div>
          <div className="bg-white rounded-xl shadow-lg overflow-hidden border-l-4 border-red-500">
            {pendingTrades.length === 0 ? (
              <div className="p-12 text-center">
                <p className="text-gray-500 text-lg">✅ No pending trades</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gradient-to-r from-red-50 to-pink-50 border-b-2 border-red-200">
                    <tr>
                      <th className="px-6 py-4 text-left font-bold text-red-900">Symbol</th>
                      <th className="px-6 py-4 text-left font-bold text-red-900">Direction</th>
                      <th className="px-6 py-4 text-right font-bold text-red-900">Entry</th>
                      <th className="px-6 py-4 text-right font-bold text-red-900">Risk</th>
                      <th className="px-6 py-4 text-right font-bold text-red-900">Confidence</th>
                      <th className="px-6 py-4 text-center font-bold text-red-900">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingTrades.map((trade) => (
                      <tr key={trade.id} className="border-b border-gray-100 hover:bg-red-50">
                        <td className="px-6 py-4 font-bold text-gray-900">{trade.symbol}</td>
                        <td className="px-6 py-4"><span className={`px-3 py-1 rounded-full text-xs font-bold ${trade.direction === 'BUY' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{trade.direction}</span></td>
                        <td className="px-6 py-4 text-right font-mono">{trade.entry_level.toFixed(2)}</td>
                        <td className="px-6 py-4 text-right font-bold">${trade.risk_amount}</td>
                        <td className="px-6 py-4 text-right">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mx-auto">
                            <div className="h-full bg-gradient-to-r from-yellow-500 to-green-500 rounded-full" style={{width: `${Math.min(trade.confidence, 100)}%`}}></div>
                          </div>
                          <p className="text-xs font-bold mt-1">{trade.confidence}%</p>
                        </td>
                        <td className="px-6 py-4 text-center space-x-2">
                          <button onClick={() => approveTrade(trade.id)} className="px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded font-bold text-xs transition">✅ Approve</button>
                          <button onClick={() => rejectTrade(trade.id)} className="px-4 py-2 bg-gradient-to-r from-gray-400 to-gray-500 hover:from-gray-500 hover:to-gray-600 text-white rounded font-bold text-xs transition">❌ Reject</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
