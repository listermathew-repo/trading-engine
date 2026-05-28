/**
 * GET /api/monitor - Real-time price monitoring endpoint
 * Manages Capital.com WebSocket listener + Stage 5 condition checker
 *
 * Lifecycle:
 * - POST /api/monitor/start → Starts Capital.com WebSocket + 5-sec checker
 * - GET /api/monitor/status → Returns current prices + latest signals
 * - GET /api/monitor/prices → Returns real-time bid/ask for all 4 instruments
 * - POST /api/monitor/stop → Stops the monitor
 */

import { NextRequest, NextResponse } from 'next/server';
import { PriceMonitor } from '@/lib/price-monitor';
import { TradeSignal } from '@/lib/stage5-conditions';
import { insertPendingTrade, sendAlert } from '@/lib/db';

// Global instance (persists across requests in same process)
let priceMonitor: PriceMonitor | null = null;
let isMonitoring = false;
let lastSignals: TradeSignal[] = [];

/**
 * Queue a trade when Stage 5 signal detected
 */
async function queueTradeFromSignal(signal: TradeSignal): Promise<void> {
  try {
    // Insert into pending_trades table
    await insertPendingTrade({
      id: `signal-${signal.symbol}-${Date.now()}`,
      symbol: signal.symbol,
      direction: signal.direction === 'BUY' ? 'long' : 'short',
      entry_level: signal.entryPrice,
      stop_level: signal.stopPrice,
      retap_level: signal.targetPrice,
      risk_amount: Math.round(signal.riskAmount),
      scenario: 'Stage 5 Auto-Detect',
      status: 'pending',
      message: `Auto-detected Stage 5 signal (confidence: ${signal.confidence}%, R:R: ${signal.rr.toFixed(1)}:1)`,
    });

    // Store for GET /api/monitor/status
    lastSignals.push(signal);
    if (lastSignals.length > 50) lastSignals.shift(); // Keep last 50

    // Send alert
    await sendAlert(
      'success',
      `🎯 Stage 5 Signal Queued: ${signal.symbol} ${signal.direction} @ ${signal.entryPrice.toFixed(4)} (R:R ${signal.rr.toFixed(1)}:1)`
    );
  } catch (error) {
    console.error('Error queuing trade:', error);
    throw error;
  }
}

/**
 * Send alert via ntfy
 */
async function sendNtfyAlert(message: string): Promise<void> {
  try {
    await fetch('https://ntfy.sh/mgm-7k4x-live', {
      method: 'POST',
      headers: {
        Title: '[STAGE 5 SIGNAL]',
        Priority: '4',
      },
      body: message,
    });
  } catch (error) {
    console.error('Error sending ntfy alert:', error);
  }
}

export async function POST(request: NextRequest) {
  try {
    const { action } = await request.json();

    if (action === 'start') {
      if (isMonitoring) {
        return NextResponse.json(
          { status: 'already_running' },
          { status: 200 }
        );
      }

      const apiKey = process.env.CAPITAL_API_KEY;
      const email = process.env.CAPITAL_EMAIL;
      const password = process.env.CAPITAL_PASSWORD;

      if (!apiKey || !email || !password) {
        return NextResponse.json(
          { error: 'Missing Capital.com credentials in .env.local' },
          { status: 401 }
        );
      }

      // Create and start monitor
      priceMonitor = new PriceMonitor(
        apiKey,
        email,
        password,
        queueTradeFromSignal,
        sendNtfyAlert
      );

      const started = await priceMonitor.start();

      if (!started) {
        return NextResponse.json(
          { error: 'Failed to connect to Capital.com WebSocket' },
          { status: 503 }
        );
      }

      isMonitoring = true;

      return NextResponse.json(
        {
          status: 'started',
          message: 'Real-time price monitor started (5-sec interval)',
          instruments: ['EURUSD', 'AUDUSD', 'XAUUSD', 'BTCUSD'],
        },
        { status: 200 }
      );
    }

    if (action === 'stop') {
      if (priceMonitor) {
        priceMonitor.stop();
      }
      isMonitoring = false;

      return NextResponse.json(
        { status: 'stopped' },
        { status: 200 }
      );
    }

    return NextResponse.json(
      { error: 'Unknown action. Use "start" or "stop".' },
      { status: 400 }
    );
  } catch (error) {
    console.error('Monitor POST error:', error);
    return NextResponse.json(
      { error: String(error) },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q');

  // GET /api/monitor/status
  if (query === 'status') {
    return NextResponse.json({
      monitoring: isMonitoring,
      lastSignals: lastSignals.slice(-10), // Last 10 signals
      connectedAt: isMonitoring ? new Date(Date.now() - 300000) : null, // Approximate
    });
  }

  // GET /api/monitor/prices
  if (query === 'prices') {
    if (!priceMonitor) {
      return NextResponse.json(
        { error: 'Monitor not started' },
        { status: 503 }
      );
    }

    return NextResponse.json({
      monitoring: isMonitoring,
      prices: priceMonitor.getPrices(),
      timestamp: Date.now(),
    });
  }

  // Default: status summary
  return NextResponse.json({
    monitoring: isMonitoring,
    message: 'Use ?q=status for status or ?q=prices for current prices',
  });
}
