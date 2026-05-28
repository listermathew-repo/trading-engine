/**
 * PUBLIC Monitor Endpoint (No Authentication Required)
 * Mirrors /api/monitor but bypasses auth middleware
 *
 * This is a system endpoint that needs to work autonomously
 * without requiring user authentication
 */

import { NextRequest, NextResponse } from 'next/server';
import { PriceMonitor } from '@/lib/price-monitor';
import type { TradeSignal } from '@/lib/stage5-conditions';
import { insertPendingTrade, sendAlert, createAlertCallback } from '@/lib/db';

// Global instance (persists across requests in same process)
let priceMonitor: PriceMonitor | null = null;
let isMonitoring = false;
let lastSignals: TradeSignal[] = [];

/**
 * Queue a trade when Stage 5 signal detected
 */
async function queueTradeFromSignal(signal: TradeSignal): Promise<void> {
  try {
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

    lastSignals.push(signal);
    if (lastSignals.length > 50) lastSignals.shift();

    await sendAlert(
      'success',
      `🎯 Stage 5 Signal Queued: ${signal.symbol} ${signal.direction} @ ${signal.entryPrice.toFixed(4)} (R:R ${signal.rr.toFixed(1)}:1)`
    );
  } catch (error) {
    console.error('Error queuing trade:', error);
    throw error;
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

      priceMonitor = new PriceMonitor(
        apiKey,
        email,
        password,
        queueTradeFromSignal,
        createAlertCallback()
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

  if (query === 'status') {
    return NextResponse.json({
      monitoring: isMonitoring,
      lastSignals: lastSignals.slice(-10),
      connectedAt: isMonitoring ? new Date(Date.now() - 300000) : null,
    });
  }

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

  return NextResponse.json({
    monitoring: isMonitoring,
    message: 'Use ?q=status for status or ?q=prices for current prices',
  });
}
