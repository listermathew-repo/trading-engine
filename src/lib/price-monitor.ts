/**
 * Real-Time Price Monitor
 * Checks Stage 5 conditions every 5 seconds
 * Queues trades when conditions match
 */

import { CapitalWebSocketClient, PriceUpdate } from './capital-websocket';
import {
  checkStage5Signal,
  TradeSignal,
  STAGE5_CONDITIONS,
} from './stage5-conditions';

interface MonitoredPrice {
  symbol: string;
  bid: number;
  ask: number;
  rsi: number;
  timestamp: number;
}

class PriceMonitor {
  private wsClient: CapitalWebSocketClient;
  private prices: Map<string, MonitoredPrice> = new Map();
  private checkInterval: NodeJS.Timeout | null = null;
  private lastSignalTime: Map<string, number> = new Map();
  private signalCooldown = 30000; // 30 sec cooldown between same signal
  private onSignal: (signal: TradeSignal) => Promise<void>;
  private onAlert: (message: string) => Promise<void>;

  constructor(
    apiKey: string,
    email: string,
    password: string,
    onSignalCallback: (signal: TradeSignal) => Promise<void>,
    onAlertCallback: (message: string) => Promise<void>
  ) {
    this.wsClient = new CapitalWebSocketClient(apiKey, email, password);
    this.onSignal = onSignalCallback;
    this.onAlert = onAlertCallback;
  }

  /**
   * Start monitoring prices
   */
  async start(): Promise<boolean> {
    try {
      const connected = await this.wsClient.connect();
      if (!connected) {
        console.error('Failed to connect to Capital.com WebSocket');
        return false;
      }

      // Subscribe to each instrument
      const instruments = Object.keys(STAGE5_CONDITIONS);
      for (const symbol of instruments) {
        this.wsClient.subscribe(symbol, (update: PriceUpdate) => {
          this.handlePriceUpdate(update);
        });
      }

      // Start 5-second check interval
      this.checkInterval = setInterval(() => {
        this.checkAllConditions();
      }, 5000);

      console.log('✅ Price monitor started (5-sec interval)');
      return true;
    } catch (error) {
      console.error('Error starting price monitor:', error);
      return false;
    }
  }

  /**
   * Handle incoming price update from WebSocket
   */
  private handlePriceUpdate(update: PriceUpdate) {
    // Store latest price
    const existing = this.prices.get(update.epic) || {
      symbol: update.epic,
      bid: update.bid,
      ask: update.ask,
      rsi: 50, // Placeholder (would need separate RSI stream)
      timestamp: update.timestamp,
    };

    this.prices.set(update.epic, {
      ...existing,
      bid: update.bid,
      ask: update.ask,
      timestamp: update.timestamp,
    });
  }

  /**
   * Check all conditions every 5 seconds
   */
  private async checkAllConditions() {
    const instruments = Object.keys(STAGE5_CONDITIONS);

    for (const symbol of instruments) {
      const price = this.prices.get(symbol);
      if (!price) continue;

      const signal = checkStage5Signal(
        symbol,
        (price.bid + price.ask) / 2,
        price.rsi,
        price.bid,
        price.ask
      );

      if (signal) {
        await this.handleSignal(signal);
      }
    }
  }

  /**
   * Handle a detected Stage 5 signal
   */
  private async handleSignal(signal: TradeSignal) {
    // Check cooldown (don't spam same signal)
    const lastSignal = this.lastSignalTime.get(signal.symbol) || 0;
    if (Date.now() - lastSignal < this.signalCooldown) {
      return;
    }

    this.lastSignalTime.set(signal.symbol, Date.now());

    console.log(
      `🎯 Stage 5 Signal: ${signal.symbol} ${signal.direction} @ ${signal.entryPrice}`
    );

    // Send alert
    const alertMessage = `
🎯 STAGE 5 SIGNAL: ${signal.symbol}
Direction: ${signal.direction}
Entry: ${signal.entryPrice.toFixed(4)}
Stop: ${signal.stopPrice.toFixed(4)}
Target: ${signal.targetPrice.toFixed(4)}
R:R: ${signal.rr.toFixed(1)}:1
Confidence: ${signal.confidence}%
⏰ ${new Date(signal.timestamp).toLocaleString('en-AU')}
    `.trim();

    await this.onAlert(alertMessage);

    // Queue trade
    try {
      await this.onSignal(signal);
      console.log(`✅ Trade queued: ${signal.symbol}`);
    } catch (error) {
      console.error('Error queuing trade:', error);
      await this.onAlert(`❌ Error queuing trade: ${signal.symbol}`);
    }
  }

  /**
   * Update RSI manually (would call from /api/health or external data source)
   */
  updateRSI(symbol: string, rsi: number) {
    const price = this.prices.get(symbol);
    if (price) {
      price.rsi = rsi;
    }
  }

  /**
   * Stop monitoring
   */
  stop() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
    this.wsClient.disconnect();
    console.log('Price monitor stopped');
  }

  /**
   * Get current prices
   */
  getPrices(): Record<string, MonitoredPrice> {
    const result: Record<string, MonitoredPrice> = {};
    this.prices.forEach((price, symbol) => {
      result[symbol] = price;
    });
    return result;
  }
}

export { PriceMonitor };
export type { MonitoredPrice };
