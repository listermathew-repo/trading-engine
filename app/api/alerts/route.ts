import { z } from 'zod';
import { PrismaClient } from '@prisma/client';
import { NextRequest, NextResponse } from 'next/server';

const prisma = new PrismaClient();

// Define the expected schema based on the Pine Script JSON template
const alertSchema = z.object({
  ticker: z.string().min(1, 'Ticker is required'),
  direction: z.enum(['long', 'short'], { errorMap: () => ({ message: 'Direction must be "long" or "short"' }) }),
  entry_level: z.number().positive('Entry level must be positive'),
  stop_level: z.number().positive('Stop level must be positive'),
  take_profit: z.number().positive('Take profit must be positive'),
  setup_type: z.string().min(1, 'Setup type is required'),
  timeframe: z.string().min(1, 'Timeframe is required'),
});

async function logAlert(level: 'info' | 'warn' | 'error', message: string, payload?: unknown, error?: unknown) {
  try {
    await prisma.alertLog.create({
      data: {
        level,
        message,
        payload: payload ? JSON.stringify(payload) : null,
        error: error ? String(error) : null,
      },
    });
  } catch (err) {
    console.error('Failed to log alert:', err);
  }
}

export async function POST(req: NextRequest) {
  const startTime = Date.now();
  let body: unknown;

  try {
    // Parse JSON body
    body = await req.json();
  } catch (err) {
    await logAlert('error', 'Invalid JSON payload', null, err);
    return NextResponse.json(
      { error: 'Invalid JSON payload', message: String(err) },
      { status: 400 }
    );
  }

  try {
    // Validate against schema
    const validatedData = alertSchema.parse(body);

    // Store in database
    const tradeAlert = await prisma.tradeAlert.create({
      data: {
        ticker: validatedData.ticker,
        direction: validatedData.direction,
        entryLevel: validatedData.entry_level,
        stopLevel: validatedData.stop_level,
        takeProfit: validatedData.take_profit,
        setupType: validatedData.setup_type,
        timeframe: validatedData.timeframe,
        status: 'pending',
      },
    });

    await logAlert('info', `Alert received for ${validatedData.ticker} ${validatedData.direction}`, {
      ticker: validatedData.ticker,
      direction: validatedData.direction,
      setupType: validatedData.setup_type,
    });

    const duration = Date.now() - startTime;

    return NextResponse.json(
      {
        success: true,
        message: 'Alert received and stored',
        alertId: tradeAlert.id,
        alert: {
          ticker: tradeAlert.ticker,
          direction: tradeAlert.direction,
          entryLevel: tradeAlert.entryLevel,
          stopLevel: tradeAlert.stopLevel,
          takeProfit: tradeAlert.takeProfit,
          setupType: tradeAlert.setupType,
          timeframe: tradeAlert.timeframe,
          createdAt: tradeAlert.createdAt,
        },
        processingTime: `${duration}ms`,
      },
      { status: 201 }
    );
  } catch (err) {
    if (err instanceof z.ZodError) {
      const errors = err.errors.map((e) => ({
        field: e.path.join('.'),
        message: e.message,
        code: e.code,
      }));

      await logAlert('warn', 'Validation error', body, { errors });

      return NextResponse.json(
        {
          error: 'Validation failed',
          details: errors,
        },
        { status: 400 }
      );
    }

    await logAlert('error', 'Unexpected error processing alert', body, err);

    return NextResponse.json(
      { error: 'Internal server error', message: String(err) },
      { status: 500 }
    );
  } finally {
    await prisma.$disconnect();
  }
}

export async function GET() {
  try {
    const alerts = await prisma.tradeAlert.findMany({
      orderBy: { createdAt: 'desc' },
      take: 10,
    });

    const stats = {
      total: await prisma.tradeAlert.count(),
      pending: await prisma.tradeAlert.count({ where: { status: 'pending' } }),
      executed: await prisma.tradeAlert.count({ where: { status: 'executed' } }),
      cancelled: await prisma.tradeAlert.count({ where: { status: 'cancelled' } }),
    };

    return NextResponse.json(
      {
        stats,
        recentAlerts: alerts,
      },
      { status: 200 }
    );
  } catch (err) {
    await logAlert('error', 'Failed to fetch alerts', null, err);
    return NextResponse.json(
      { error: 'Failed to fetch alerts', message: String(err) },
      { status: 500 }
    );
  } finally {
    await prisma.$disconnect();
  }
}
