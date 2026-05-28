'use client';

import { useEffect, useState } from 'react';
import { AreaChart, Area, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

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

export default function TradingDashboard() {
  const [monitorStatus, setMonitorStatus] = useState<'running' | 'stopped'>('stopped');
  const [pendingTrades, setPendingTrades] = useState<PendingTrade[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [account, setAccount] = useState<AccountData | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const priceHistory = [
    { time: '09:00', EURUSD: 1.1600, XAUUSD: 4380, BTCUSD: 73000, AUDUSD: 0.712 },
    { time: '10:00', EURUSD: 1.1605, XAUUSD: 4385, BTCUSD: 73100, AUDUSD: 0.713 },
    { time: '11:00', EURUSD: 1.1603, XAUUSD: 4382, BTCUSD: 73050, AUDUSD: 0.712 },
    { time: '12:00', EURUSD: 1.1608, XAUUSD: 4388, BTCUSD: 73200, AUDUSD: 0.714 },
    { time: '13:00', EURUSD: 1.1610, XAUUSD: 4390, BTCUSD: 73300, AUDUSD: 0.715 },
    { time: '14:00', EURUSD: 1.1606, XAUUSD: 4380, BTCUSD: 73098, AUDUSD: 0.7121 },
  ];

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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Animated background accent */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500 opacity-10 blur-3xl rounded-full animate-pulse"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500 opacity-10 blur-3xl rounded-full animate-pulse" style={{animationDelay: '1s'}}></div>
      </div>

      {/* Header */}
      <div className="sticky top-0 z-50 backdrop-blur-xl bg-slate-900/80 border-b border-slate-700/50">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-black bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">Trading Dashboard</h1>
              <p className="text-sm text-slate-400 mt-2">⏰ {lastUpdate} ADL</p>
            </div>
            <button
              onClick={toggleMonitor}
              className={`px-8 py-3 rounded-xl font-bold text-white transition transform hover:scale-105 shadow-lg ${
                monitorStatus === 'running'
                  ? 'bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 shadow-red-500/50'
                  : 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 shadow-emerald-500/50'
              }`}
            >
              {monitorStatus === 'running' ? '⏹ STOP' : '▶ START'}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 py-8 relative z-10">
        {/* Premium KPI Cards */}
        {account && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[
              { label: 'Balance', value: account.balance, subtext: 'Total Account', icon: '💰', gradient: 'from-blue-600 to-cyan-500', topColor: 'top-0 left-0 w-1 h-12 bg-gradient-to-b from-blue-400 to-transparent' },
              { label: 'Equity', value: account.equity, subtext: 'Current Value', icon: '📊', gradient: 'from-purple-600 to-pink-500', topColor: 'top-0 left-0 w-1 h-12 bg-gradient-to-b from-purple-400 to-transparent' },
              { label: 'Unrealized P&L', value: account.unrealizedPnL, subtext: account.unrealizedPnL >= 0 ? 'Winning' : 'Losing', icon: account.unrealizedPnL >= 0 ? '📈' : '📉', gradient: account.unrealizedPnL >= 0 ? 'from-emerald-600 to-teal-500' : 'from-red-600 to-orange-500', topColor: account.unrealizedPnL >= 0 ? 'top-0 left-0 w-1 h-12 bg-gradient-to-b from-emerald-400 to-transparent' : 'top-0 left-0 w-1 h-12 bg-gradient-to-b from-red-400 to-transparent' },
              { label: 'Margin Buffer', value: account.marginBuffer, suffix: '%', subtext: 'Safe Zone', icon: '🛡️', gradient: 'from-orange-600 to-yellow-500', topColor: 'top-0 left-0 w-1 h-12 bg-gradient-to-b from-orange-400 to-transparent' },
            ].map((m, i) => (
              <div key={i} className="group relative bg-gradient-to-br from-slate-800 to-slate-700 rounded-2xl p-6 border border-slate-600 hover:border-slate-500 transition overflow-hidden backdrop-blur-sm hover:shadow-2xl hover:shadow-slate-900/50">
                <div className={`absolute ${m.topColor} rounded-full blur-2xl opacity-50 group-hover:opacity-100 transition`}></div>
                <div className="relative z-10">
                  <div className="flex justify-between items-start mb-4">
                    <p className="text-sm font-semibold text-slate-400 uppercase tracking-wider">{m.label}</p>
                    <span className="text-2xl">{m.icon}</span>
                  </div>
                  <p className={`text-4xl font-black bg-gradient-to-r ${m.gradient} bg-clip-text text-transparent mb-2`}>
                    ${typeof m.value === 'number' ? m.value.toLocaleString('en-US', {maximumFractionDigits: m.suffix ? 1 : 2}) : m.value}{m.suffix || ''}
                  </p>
                  <p className="text-xs text-slate-500">{m.subtext}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Charts Section - Beautiful Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Price History - Large Chart */}
          <div className="lg:col-span-2 bg-gradient-to-br from-slate-800 to-slate-700 rounded-2xl p-6 border border-slate-600 backdrop-blur-sm">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <span className="text-2xl">📈</span> Price Movement
            </h2>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={priceHistory} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorEUR" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorXAU" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,116,139,0.3)" />
                <XAxis dataKey="time" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#e2e8f0' }} />
                <Area type="monotone" dataKey="EURUSD" stroke="#3b82f6" fillOpacity={1} fill="url(#colorEUR)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Account Health Pie Chart */}
          <div className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-2xl p-6 border border-slate-600 backdrop-blur-sm">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <span className="text-2xl">💎</span> Portfolio
            </h2>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={account ? [
                    { name: 'Balance', value: account.balance },
                    { name: 'Unrealized P&L', value: Math.max(1, Math.abs(account.unrealizedPnL)) },
                  ] : []}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${percent ? (percent * 100).toFixed(0) : '0'}%`}
                  labelLine={false}
                >
                  <Cell fill="#3b82f6" />
                  <Cell fill={account && account.unrealizedPnL >= 0 ? '#10b981' : '#ef4444'} />
                </Pie>
                <Tooltip formatter={(value) => value ? `$${value.toLocaleString()}` : '$0'} contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#e2e8f0' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* RSI Status - Beautiful Bar Chart */}
        <div className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-2xl p-6 border border-slate-600 backdrop-blur-sm mb-8">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span className="text-2xl">📊</span> RSI Status
          </h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={[
              { symbol: 'EURUSD', value: 69.63, fill: '#ef4444' },
              { symbol: 'XAUUSD', value: 46.88, fill: '#f59e0b' },
              { symbol: 'BTCUSD', value: 59.19, fill: '#f59e0b' },
              { symbol: 'AUDUSD', value: 35.0, fill: '#10b981' },
            ]}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(100,116,139,0.3)" />
              <XAxis dataKey="symbol" stroke="#94a3b8" />
              <YAxis domain={[0, 100]} stroke="#94a3b8" />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#e2e8f0' }} />
              <Bar dataKey="value" radius={[12, 12, 0, 0]}>
                {[
                  { fill: '#ef4444' },
                  { fill: '#f59e0b' },
                  { fill: '#f59e0b' },
                  { fill: '#10b981' },
                ].map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-4 gap-4 mt-6">
            {[
              { label: 'EURUSD', value: '69.63', color: 'text-red-400', bg: 'bg-red-500/20' },
              { label: 'XAUUSD', value: '46.88', color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
              { label: 'BTCUSD', value: '59.19', color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
              { label: 'AUDUSD', value: '35.0', color: 'text-green-400', bg: 'bg-green-500/20' },
            ].map((item, i) => (
              <div key={i} className={`${item.bg} rounded-xl p-4 text-center border border-slate-600`}>
                <p className={`text-lg font-bold ${item.color}`}>{item.value}</p>
                <p className="text-xs text-slate-400 mt-1">{item.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Open Positions - Premium Table */}
        <div className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-2xl p-6 border border-slate-600 backdrop-blur-sm mb-8">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span className="text-2xl">🎯</span> Open Positions
          </h2>
          {positions.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <p className="text-lg">No open positions</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-600">
                    <th className="px-6 py-4 text-left font-semibold text-slate-300">Symbol</th>
                    <th className="px-6 py-4 text-left font-semibold text-slate-300">Direction</th>
                    <th className="px-6 py-4 text-right font-semibold text-slate-300">Entry</th>
                    <th className="px-6 py-4 text-right font-semibold text-slate-300">Current</th>
                    <th className="px-6 py-4 text-right font-semibold text-slate-300">Stop</th>
                    <th className="px-6 py-4 text-right font-semibold text-slate-300">Target</th>
                    <th className="px-6 py-4 text-right font-semibold text-slate-300">P&L $</th>
                    <th className="px-6 py-4 text-right font-semibold text-slate-300">P&L %</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((pos) => (
                    <tr key={pos.symbol} className="border-b border-slate-700 hover:bg-slate-700/50 transition">
                      <td className="px-6 py-4 font-bold text-white">{pos.symbol}</td>
                      <td className="px-6 py-4"><span className={`px-3 py-1 rounded-lg text-xs font-bold ${pos.direction === 'short' ? 'bg-red-500/30 text-red-300' : 'bg-emerald-500/30 text-emerald-300'}`}>{pos.direction.toUpperCase()}</span></td>
                      <td className="px-6 py-4 text-right font-mono text-slate-300">{pos.entry.toFixed(5)}</td>
                      <td className="px-6 py-4 text-right font-mono font-bold text-cyan-400">{pos.current.toFixed(5)}</td>
                      <td className="px-6 py-4 text-right font-mono text-red-400">{pos.stop.toFixed(5)}</td>
                      <td className="px-6 py-4 text-right font-mono text-emerald-400">{pos.target.toFixed(2)}</td>
                      <td className="px-6 py-4 text-right font-bold text-emerald-400">+${pos.pnl.toFixed(2)}</td>
                      <td className="px-6 py-4 text-right font-bold text-emerald-400">+{pos.pnlPercent.toFixed(2)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pending Trades - CRITICAL SECTION */}
        <div className="bg-gradient-to-br from-red-900/40 to-rose-900/40 rounded-2xl p-6 border border-red-600/60 backdrop-blur-sm">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-red-300 flex items-center gap-2">
              <span className="text-2xl">🚨</span> Pending Approval
            </h2>
            <span className="bg-gradient-to-r from-red-600 to-pink-600 text-white px-4 py-2 rounded-lg font-bold shadow-lg shadow-red-600/50">{pendingTrades.length}</span>
          </div>
          {pendingTrades.length === 0 ? (
            <div className="text-center py-12 text-red-300">
              <p className="text-lg">✅ No pending trades</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-red-600/40">
                    <th className="px-6 py-4 text-left font-semibold text-red-300">Symbol</th>
                    <th className="px-6 py-4 text-left font-semibold text-red-300">Direction</th>
                    <th className="px-6 py-4 text-right font-semibold text-red-300">Entry</th>
                    <th className="px-6 py-4 text-right font-semibold text-red-300">Stop</th>
                    <th className="px-6 py-4 text-right font-semibold text-red-300">Risk</th>
                    <th className="px-6 py-4 text-right font-semibold text-red-300">R:R</th>
                    <th className="px-6 py-4 text-center font-semibold text-red-300">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingTrades.map((trade) => (
                    <tr key={trade.id} className="border-b border-red-600/20 hover:bg-red-600/20 transition">
                      <td className="px-6 py-4 font-bold text-white">{trade.symbol}</td>
                      <td className="px-6 py-4"><span className={`px-3 py-1 rounded-lg text-xs font-bold ${trade.direction === 'BUY' ? 'bg-emerald-500/30 text-emerald-300' : 'bg-red-500/30 text-red-300'}`}>{trade.direction}</span></td>
                      <td className="px-6 py-4 text-right font-mono text-slate-300">{trade.entry_level.toFixed(2)}</td>
                      <td className="px-6 py-4 text-right font-mono text-red-400">{trade.stop_level.toFixed(2)}</td>
                      <td className="px-6 py-4 text-right font-bold text-slate-300">${trade.risk_amount}</td>
                      <td className="px-6 py-4 text-right font-bold text-blue-400">{trade.rr.toFixed(1)}:1</td>
                      <td className="px-6 py-4 text-center space-x-2">
                        <button onClick={() => approveTrade(trade.id)} className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white rounded-lg font-bold text-xs transition transform hover:scale-105 shadow-lg shadow-emerald-600/30">✅ Approve</button>
                        <button onClick={() => rejectTrade(trade.id)} className="px-4 py-2 bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 text-white rounded-lg font-bold text-xs transition transform hover:scale-105">❌ Reject</button>
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
  );
}
