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

export default function DesignOne() {
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
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 z-50">
          <div className="px-8 py-4 flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">DESIGN 1: Crypto White (Kraken Style)</h1>
            <div className="flex gap-4 items-center">
              <button onClick={toggleMonitor} className={`px-6 py-2 rounded font-semibold text-white ${monitorStatus === 'running' ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'}`}>
                {monitorStatus === 'running' ? '⏹ STOP' : '▶ START'}
              </button>
              <span className="text-sm text-gray-500">{lastUpdate} ADL</span>
            </div>
          </div>
        </div>

        {/* Summary Cards */}
        {account && (
          <div className="px-8 py-6 bg-gray-50 border-b border-gray-200">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Balance', value: `$${account.balance.toLocaleString('en-US', {minimumFractionDigits: 2})}` },
                { label: 'Equity', value: `$${account.equity.toLocaleString('en-US', {minimumFractionDigits: 2})}` },
                { label: 'Unrealized P&L', value: `${account.unrealizedPnL >= 0 ? '+' : ''}$${account.unrealizedPnL.toLocaleString('en-US', {minimumFractionDigits: 2})}`, color: account.unrealizedPnL >= 0 ? 'text-green-600' : 'text-red-600' },
                { label: 'Margin Buffer', value: `${account.marginBuffer.toFixed(1)}%` },
              ].map((m, i) => (
                <div key={i} className="bg-white p-4 rounded border border-gray-200">
                  <p className="text-xs text-gray-600 font-semibold uppercase mb-1">{m.label}</p>
                  <p className={`text-lg font-bold text-gray-900 ${m.color || ''}`}>{m.value}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Markets Table */}
        <div className="px-8 py-6">
          <h2 className="text-lg font-bold mb-4 text-gray-900">Markets</h2>
          <div className="border border-gray-200 rounded overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left font-semibold text-gray-700">Instrument</th>
                  <th className="px-6 py-3 text-right font-semibold text-gray-700">Price</th>
                  <th className="px-6 py-3 text-right font-semibold text-gray-700">RSI</th>
                  <th className="px-6 py-3 text-left font-semibold text-gray-700">Status</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { symbol: 'EURUSD', price: 1.16076, rsi: 69.63, status: 'Waiting pullback', badge: 'bg-yellow-100 text-yellow-800' },
                  { symbol: 'XAUUSD', price: 4380.03, rsi: 46.88, status: 'Monitoring', badge: 'bg-blue-100 text-blue-800' },
                  { symbol: 'BTCUSD', price: 73097.98, rsi: 59.19, status: 'Waiting signal', badge: 'bg-gray-100 text-gray-800' },
                  { symbol: 'AUDUSD', price: 0.71212, rsi: 35.0, status: 'Position open', badge: 'bg-green-100 text-green-800' },
                ].map((inst) => (
                  <tr key={inst.symbol} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-6 py-4 font-semibold text-gray-900">{inst.symbol}</td>
                    <td className="px-6 py-4 text-right font-mono text-gray-900">{inst.price.toLocaleString()}</td>
                    <td className="px-6 py-4 text-right font-semibold">{inst.rsi > 70 ? <span className="text-red-600">{inst.rsi.toFixed(1)}</span> : inst.rsi < 30 ? <span className="text-green-600">{inst.rsi.toFixed(1)}</span> : <span className="text-orange-600">{inst.rsi.toFixed(1)}</span>}</td>
                    <td className="px-6 py-4"><span className={`px-3 py-1 rounded text-xs font-semibold ${inst.badge}`}>{inst.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Open Positions */}
        <div className="px-8 py-6 border-t border-gray-200">
          <h2 className="text-lg font-bold mb-4 text-gray-900">Open Positions</h2>
          <div className="border border-gray-200 rounded overflow-hidden">
            {positions.length === 0 ? (
              <div className="p-8 text-center bg-gray-50">
                <p className="text-gray-500">No open positions</p>
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left font-semibold text-gray-700">Symbol</th>
                    <th className="px-6 py-3 text-left font-semibold text-gray-700">Direction</th>
                    <th className="px-6 py-3 text-right font-semibold text-gray-700">Entry</th>
                    <th className="px-6 py-3 text-right font-semibold text-gray-700">Current</th>
                    <th className="px-6 py-3 text-right font-semibold text-gray-700">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((pos) => (
                    <tr key={pos.symbol} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-6 py-4 font-semibold text-gray-900">{pos.symbol}</td>
                      <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs font-semibold ${pos.direction === 'short' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>{pos.direction.toUpperCase()}</span></td>
                      <td className="px-6 py-4 text-right font-mono">{pos.entry.toFixed(5)}</td>
                      <td className="px-6 py-4 text-right font-mono font-semibold">{pos.current.toFixed(5)}</td>
                      <td className="px-6 py-4 text-right font-semibold"><span className="text-green-600">+${pos.pnl.toFixed(2)}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Pending Trades */}
        <div className="px-8 py-6 border-t border-gray-200">
          <h2 className="text-lg font-bold mb-4 text-gray-900">Pending Approval ({pendingTrades.length})</h2>
          <div className="border border-gray-200 rounded overflow-hidden">
            {pendingTrades.length === 0 ? (
              <div className="p-8 text-center bg-gray-50">
                <p className="text-gray-500">No pending trades</p>
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left font-semibold text-gray-700">Symbol</th>
                    <th className="px-6 py-3 text-left font-semibold text-gray-700">Direction</th>
                    <th className="px-6 py-3 text-right font-semibold text-gray-700">Entry</th>
                    <th className="px-6 py-3 text-right font-semibold text-gray-700">Risk</th>
                    <th className="px-6 py-3 text-center font-semibold text-gray-700">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingTrades.map((trade) => (
                    <tr key={trade.id} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-6 py-4 font-semibold text-gray-900">{trade.symbol}</td>
                      <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs font-semibold ${trade.direction === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{trade.direction}</span></td>
                      <td className="px-6 py-4 text-right font-mono">{trade.entry_level.toFixed(2)}</td>
                      <td className="px-6 py-4 text-right">${trade.risk_amount}</td>
                      <td className="px-6 py-4 text-center space-x-2">
                        <button onClick={() => approveTrade(trade.id)} className="px-3 py-1 bg-green-500 text-white rounded text-xs font-semibold hover:bg-green-600">✅ Approve</button>
                        <button onClick={() => rejectTrade(trade.id)} className="px-3 py-1 bg-gray-400 text-white rounded text-xs font-semibold hover:bg-gray-500">❌ Reject</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div className="h-12"></div>
      </div>
    </div>
  );
}
