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

export default function DesignThree() {
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-teal-900 to-slate-900">
      <div className="max-w-7xl mx-auto p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-4xl font-black bg-gradient-to-r from-teal-400 to-cyan-300 bg-clip-text text-transparent">DESIGN 3: Modern Dark</h1>
              <p className="text-teal-300 text-sm mt-2">Updated {lastUpdate} ADL</p>
            </div>
            <button onClick={toggleMonitor} className={`px-8 py-3 rounded-lg font-bold text-white transition transform hover:scale-105 ${monitorStatus === 'running' ? 'bg-red-600 hover:bg-red-700' : 'bg-emerald-600 hover:bg-emerald-700'}`}>
              {monitorStatus === 'running' ? '⏹ STOP MONITOR' : '▶ START MONITOR'}
            </button>
          </div>
        </div>

        {/* Gauge Metrics */}
        {account && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            {[
              { label: 'Balance', value: account.balance, prefix: '$', color: 'from-cyan-500 to-blue-500' },
              { label: 'Equity', value: account.equity, prefix: '$', color: 'from-teal-500 to-emerald-500' },
              { label: 'Unrealized P&L', value: account.unrealizedPnL, prefix: '$', color: account.unrealizedPnL >= 0 ? 'from-emerald-500 to-green-500' : 'from-red-500 to-pink-500' },
              { label: 'Margin Buffer', value: account.marginBuffer, suffix: '%', color: 'from-violet-500 to-purple-500' },
            ].map((m, i) => (
              <div key={i} className={`bg-gradient-to-br ${m.color} rounded-2xl p-6 text-white shadow-2xl border border-opacity-20 border-white`}>
                <p className="text-sm opacity-80 font-semibold uppercase tracking-wide">{m.label}</p>
                <p className="text-4xl font-black mt-4">{m.prefix}{typeof m.value === 'number' ? m.value.toLocaleString('en-US', {maximumFractionDigits: m.suffix ? 1 : 2}) : m.value}{m.suffix || ''}</p>
              </div>
            ))}
          </div>
        )}

        {/* Markets Grid */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4">Market Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { symbol: 'EURUSD', price: 1.16076, rsi: 69.63, status: 'Waiting', badge: 'from-yellow-500 to-orange-500' },
              { symbol: 'XAUUSD', price: 4380.03, rsi: 46.88, status: 'Monitoring', badge: 'from-blue-500 to-cyan-500' },
              { symbol: 'BTCUSD', price: 73097.98, rsi: 59.19, status: 'Waiting', badge: 'from-gray-500 to-slate-600' },
              { symbol: 'AUDUSD', price: 0.71212, rsi: 35.0, status: 'Active', badge: 'from-emerald-500 to-green-500' },
            ].map((inst) => (
              <div key={inst.symbol} className={`bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 hover:border-slate-600 transition`}>
                <p className="text-teal-300 font-bold text-lg">{inst.symbol}</p>
                <p className="text-3xl font-black text-white mt-2">{inst.price.toLocaleString()}</p>
                <div className="mt-4 flex justify-between items-center">
                  <span className={`text-sm font-bold ${inst.rsi > 70 ? 'text-red-400' : inst.rsi < 30 ? 'text-green-400' : 'text-yellow-400'}`}>RSI: {inst.rsi.toFixed(1)}</span>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold text-white bg-gradient-to-r ${inst.badge}`}>{inst.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Positions Table */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4">Active Positions</h2>
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl overflow-hidden border border-slate-700">
            {positions.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-slate-400">No active positions</p>
              </div>
            ) : (
              <table className="w-full text-sm text-slate-300">
                <thead className="bg-slate-900 border-b border-slate-700">
                  <tr>
                    <th className="px-6 py-4 text-left font-bold text-cyan-400">Symbol</th>
                    <th className="px-6 py-4 text-left font-bold text-cyan-400">Direction</th>
                    <th className="px-6 py-4 text-right font-bold text-cyan-400">Entry</th>
                    <th className="px-6 py-4 text-right font-bold text-cyan-400">Current</th>
                    <th className="px-6 py-4 text-right font-bold text-cyan-400">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((pos) => (
                    <tr key={pos.symbol} className="border-b border-slate-700 hover:bg-slate-800 transition">
                      <td className="px-6 py-4 font-bold text-white">{pos.symbol}</td>
                      <td className="px-6 py-4"><span className={`px-3 py-1 rounded font-bold text-xs ${pos.direction === 'short' ? 'bg-red-500 bg-opacity-20 text-red-300' : 'bg-green-500 bg-opacity-20 text-green-300'}`}>{pos.direction.toUpperCase()}</span></td>
                      <td className="px-6 py-4 text-right">{pos.entry.toFixed(5)}</td>
                      <td className="px-6 py-4 text-right text-cyan-300 font-bold">{pos.current.toFixed(5)}</td>
                      <td className="px-6 py-4 text-right text-emerald-400 font-bold">+${pos.pnl.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Pending Trades Critical */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-red-400 mb-4">🚨 Pending Approval <span className="text-white bg-red-600 px-3 py-1 rounded-lg text-lg">{pendingTrades.length}</span></h2>
          <div className="bg-gradient-to-br from-red-900 to-slate-900 rounded-xl overflow-hidden border border-red-700">
            {pendingTrades.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-slate-400">✅ No pending trades</p>
              </div>
            ) : (
              <table className="w-full text-sm text-slate-300">
                <thead className="bg-slate-900 border-b border-red-700">
                  <tr>
                    <th className="px-6 py-4 text-left font-bold text-red-400">Symbol</th>
                    <th className="px-6 py-4 text-left font-bold text-red-400">Direction</th>
                    <th className="px-6 py-4 text-right font-bold text-red-400">Entry</th>
                    <th className="px-6 py-4 text-right font-bold text-red-400">Risk</th>
                    <th className="px-6 py-4 text-center font-bold text-red-400">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingTrades.map((trade) => (
                    <tr key={trade.id} className="border-b border-red-700 hover:bg-red-900 hover:bg-opacity-20 transition">
                      <td className="px-6 py-4 font-bold text-white">{trade.symbol}</td>
                      <td className="px-6 py-4"><span className={`px-3 py-1 rounded font-bold text-xs ${trade.direction === 'BUY' ? 'bg-green-500 bg-opacity-30 text-green-300' : 'bg-red-500 bg-opacity-30 text-red-300'}`}>{trade.direction}</span></td>
                      <td className="px-6 py-4 text-right">{trade.entry_level.toFixed(2)}</td>
                      <td className="px-6 py-4 text-right">${trade.risk_amount}</td>
                      <td className="px-6 py-4 text-center space-x-2">
                        <button onClick={() => approveTrade(trade.id)} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-bold text-xs transition">✅ Approve</button>
                        <button onClick={() => rejectTrade(trade.id)} className="px-4 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded font-bold text-xs transition">❌ Reject</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
