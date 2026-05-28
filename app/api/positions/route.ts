import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Return hardcoded positions based on your screenshot
    // In production, this would fetch from Capital.com API
    return NextResponse.json({
      account: {
        balance: 110430.38,
        equity: 112776.60,
        realizedPnL: 10430.38,
        unrealizedPnL: 2346.23,
        margin: 6644.81,
        availableFunds: 106131.79,
        marginBuffer: 94.11,
      },
      positions: [
        {
          symbol: 'AUDUSD',
          direction: 'short',
          size: 423076,
          entry: 0.71750,
          current: 0.71212,
          stop: 0.72000,
          target: 0.70800,
          pnl: 2276.15,
          pnlPercent: 0.75,
          tradValue: 303557.03,
        },
        {
          symbol: 'XAUUSD',
          direction: 'short',
          size: 6,
          entry: 4389.58,
          current: 4377.90,
          stop: 4450.00,
          target: 4396.44,
          pnl: 70.08,
          pnlPercent: 0.27,
          tradValue: 26337.48,
        },
      ],
    });
  } catch (error) {
    return NextResponse.json(
      { error: String(error) },
      { status: 500 }
    );
  }
}
