/**
 * Stage 5 Entry Conditions Monitor
 * Defines exact conditions for queuing trades based on user's analysis
 */

interface InstrumentConditions {
  symbol: string;
  bias: 'LONG' | 'SHORT' | 'NEUTRAL';
  rsiThreshold: {
    min: number;
    max: number;
  };
  priceZones: {
    support: number;
    resistance: number;
    pullbackMin: number;
    pullbackMax: number;
  };
  confluenceRequired: string[];
  maxRiskPerTrade: number;
  minRR: number;
}

interface TradeSignal {
  symbol: string;
  direction: 'BUY' | 'SELL';
  entryPrice: number;
  stopPrice: number;
  targetPrice: number;
  riskAmount: number;
  rr: number;
  confidence: number;
  timestamp: number;
}

// Define Stage 5 conditions for each instrument
// Based on your trading rules (2026-05-28)
// 4 instruments: EURUSD, XAUUSD, AUDUSD, BTCUSD

export const STAGE5_CONDITIONS: Record<string, InstrumentConditions> = {
  EURUSD: {
    symbol: 'EURUSD',
    bias: 'NEUTRAL', // Waiting for pullback + retest
    rsiThreshold: {
      min: 30,
      max: 70,
    },
    priceZones: {
      support: 1.15950,
      resistance: 1.16615,
      pullbackMin: 1.16200,
      pullbackMax: 1.16400,
    },
    confluenceRequired: [
      'RSI recovery from < 30',
      'Break above pullback level',
      '1H + 15M alignment',
    ],
    maxRiskPerTrade: 350,
    minRR: 2,
  },

  XAUUSD: {
    symbol: 'XAUUSD',
    bias: 'SHORT', // Scenario 2 confirmed
    rsiThreshold: {
      min: 20,
      max: 40, // Pullback zone before re-entry
    },
    priceZones: {
      support: 4396.44,
      resistance: 4773.57, // Previous high = "highest point"
      pullbackMin: 4430,
      pullbackMax: 4450,
    },
    confluenceRequired: [
      'RSI < 30 on 4H/1H/15M',
      'Price below resistance ceiling',
      'Pullback to support zone (4396-4430)',
      'Stage 5 short entry candle on 5M',
    ],
    maxRiskPerTrade: 350,
    minRR: 3,
  },

  AUDUSD: {
    symbol: 'AUDUSD',
    bias: 'SHORT', // Already in position
    rsiThreshold: {
      min: 20,
      max: 60,
    },
    priceZones: {
      support: 0.70800,
      resistance: 0.72000,
      pullbackMin: 0.71100,
      pullbackMax: 0.71400,
    },
    confluenceRequired: ['Manage existing position', 'Watch for exit signals'],
    maxRiskPerTrade: 350,
    minRR: 3,
  },

  BTCUSD: {
    symbol: 'BTCUSD',
    bias: 'SHORT', // Scenario 2 pattern
    rsiThreshold: {
      min: 20,
      max: 40, // Pullback zone before re-entry
    },
    priceZones: {
      support: 74000,
      resistance: 82132, // Previous high = "highest point"
      pullbackMin: 76000,
      pullbackMax: 78000,
    },
    confluenceRequired: [
      'RSI < 30 on 4H/1H/15M',
      'Price below resistance ceiling',
      'Pullback to support zone (74000-76000)',
      'Stage 5 short entry candle on 5M',
    ],
    maxRiskPerTrade: 350,
    minRR: 3,
  },
};

/**
 * Check if current price + RSI matches Stage 5 entry conditions
 */
export function checkStage5Signal(
  symbol: string,
  currentPrice: number,
  rsi: number,
  bid: number,
  ask: number
): TradeSignal | null {
  const conditions = STAGE5_CONDITIONS[symbol];
  if (!conditions) return null;

  // Check RSI threshold
  if (rsi < conditions.rsiThreshold.min || rsi > conditions.rsiThreshold.max) {
    return null;
  }

  // Check price zone
  const inPullbackZone =
    currentPrice >= conditions.priceZones.pullbackMin &&
    currentPrice <= conditions.priceZones.pullbackMax;

  if (!inPullbackZone && conditions.bias !== 'NEUTRAL') {
    return null;
  }

  // Generate signal based on bias
  if (conditions.bias === 'SHORT') {
    // Short entry: enter at ask (sell at market ask)
    const entryPrice = ask;
    const stopPrice = conditions.priceZones.resistance;
    const targetPrice = conditions.priceZones.support;

    // For crypto, adjust pips calculation
    let riskAmount = conditions.maxRiskPerTrade;
    let rr = 5; // Default to 5:1

    if (symbol.includes('USD') && !symbol.includes('AUD')) {
      // Crypto: BTCUSD, etc
      riskAmount = (stopPrice - entryPrice) * 1; // 1 contract
      rr = (entryPrice - targetPrice) / (stopPrice - entryPrice);
    } else if (symbol === 'XAUUSD') {
      // Gold
      riskAmount = (stopPrice - entryPrice) * 10; // 10 oz
      rr = (entryPrice - targetPrice) / (stopPrice - entryPrice);
    }

    if (rr < conditions.minRR) {
      return null; // R:R too low
    }

    return {
      symbol,
      direction: 'SELL',
      entryPrice,
      stopPrice,
      targetPrice,
      riskAmount: Math.abs(riskAmount),
      rr,
      confidence: calculateConfidence(rsi, currentPrice, conditions),
      timestamp: Date.now(),
    };
  }

  if (conditions.bias === 'LONG') {
    // Long entry: enter at bid (buy at market bid)
    const entryPrice = bid;
    const stopPrice = conditions.priceZones.support;
    const targetPrice = conditions.priceZones.resistance;

    const riskAmount = conditions.maxRiskPerTrade;
    const rr = (targetPrice - entryPrice) / (entryPrice - stopPrice);

    if (rr < conditions.minRR) {
      return null;
    }

    return {
      symbol,
      direction: 'BUY',
      entryPrice,
      stopPrice,
      targetPrice,
      riskAmount,
      rr,
      confidence: calculateConfidence(rsi, currentPrice, conditions),
      timestamp: Date.now(),
    };
  }

  return null;
}

/**
 * Calculate confidence score (0-100) based on indicator confluence
 */
function calculateConfidence(
  rsi: number,
  price: number,
  conditions: InstrumentConditions
): number {
  let score = 50;

  // RSI proximity to threshold
  const rsiDistance =
    conditions.bias === 'SHORT'
      ? Math.abs(rsi - conditions.rsiThreshold.min)
      : Math.abs(rsi - conditions.rsiThreshold.max);

  if (rsiDistance < 5) score += 20;
  else if (rsiDistance < 10) score += 10;

  // Price in pullback zone
  const priceDistance = Math.min(
    Math.abs(price - conditions.priceZones.pullbackMin),
    Math.abs(price - conditions.priceZones.pullbackMax)
  );

  if (priceDistance < 50) score += 20;
  else if (priceDistance < 200) score += 10;

  // Cap at 95 (never 100 - always room for manual override)
  return Math.min(score, 95);
}

export type { InstrumentConditions, TradeSignal };
