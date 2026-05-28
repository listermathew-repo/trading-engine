#!/usr/bin/env node

/**
 * Standalone Price Monitor Starter
 * Requires TypeScript to be compiled first: npm run build
 * Usage: npm run start:monitor
 *
 * This script starts the Capital.com WebSocket listener independently
 * of the Next.js server, bypassing HTTP authentication requirements.
 */

console.log('🚀 Price Monitor Startup Script');
console.log('━'.repeat(50));
console.log('');

// Check required environment variables
const requiredEnv = ['CAPITAL_API_KEY', 'CAPITAL_EMAIL', 'CAPITAL_PASSWORD'];
const missingEnv = requiredEnv.filter(key => !process.env[key]);

if (missingEnv.length > 0) {
  console.error(`❌ Missing credentials in environment:`);
  missingEnv.forEach(key => {
    console.error(`   - ${key}`);
  });
  console.error('');
  console.error('Solution: Ensure .env.local contains:');
  console.error('  CAPITAL_API_KEY=<your_key>');
  console.error('  CAPITAL_EMAIL=<your_email>');
  console.error('  CAPITAL_PASSWORD=<your_password>');
  console.error('  NTFY_URL=https://ntfy.sh/<your_topic>');
  process.exit(1);
}

console.log('✅ Environment variables loaded:');
console.log(`   Capital.com API: ${process.env.CAPITAL_API_KEY.substring(0, 8)}...`);
console.log(`   Email: ${process.env.CAPITAL_EMAIL}`);
console.log(`   Webhook: ${process.env.NTFY_URL || 'https://ntfy.sh/mgm-7k4x-live'}`);
console.log('');

console.log('⚠️  Note: Price monitor requires compiled TypeScript.');
console.log('   If you see import errors, run: npm run build');
console.log('');

// Dynamically import the compiled code
(async () => {
  try {
    console.log('📦 Loading compiled modules...');

    const { PriceMonitor } = await import('./.next/server/lib/price-monitor.js');
    const db = await import('./.next/server/lib/db.js');

    const { createAlertCallback, insertPendingTrade, sendAlert } = db;

    /**
     * Queue a trade when Stage 5 signal detected
     */
    async function queueTradeFromSignal(signal) {
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

        await sendAlert(
          'success',
          `🎯 Stage 5 Signal Queued: ${signal.symbol} ${signal.direction} @ ${signal.entryPrice.toFixed(4)} (R:R ${signal.rr.toFixed(1)}:1)`
        );
      } catch (error) {
        console.error('Error queuing trade:', error);
      }
    }

    console.log('🎯 Starting Capital.com Price Monitor');
    console.log('   Instruments: EURUSD, AUDUSD, XAUUSD, BTCUSD');
    console.log('   Check Interval: 5 seconds');
    console.log('   Stage 5 Detection: Enabled');
    console.log('');

    const priceMonitor = new PriceMonitor(
      process.env.CAPITAL_API_KEY,
      process.env.CAPITAL_EMAIL,
      process.env.CAPITAL_PASSWORD,
      queueTradeFromSignal,
      createAlertCallback()
    );

    const started = await priceMonitor.start();

    if (!started) {
      console.error('❌ Failed to connect to Capital.com WebSocket');
      console.error('Possible causes:');
      console.error('  • Invalid API credentials');
      console.error('  • Capital.com API is down');
      console.error('  • Network connectivity issue');
      process.exit(1);
    }

    console.log('✅ Price Monitor Started Successfully');
    console.log('');
    console.log('📊 Monitor Status:');
    console.log('   • Connected to Capital.com WebSocket');
    console.log('   • Monitoring: EURUSD, AUDUSD, XAUUSD, BTCUSD');
    console.log('   • Checking conditions every 5 seconds');
    console.log('   • Alerts: Enabled via ntfy.sh');
    console.log('');
    console.log('🛑 Press Ctrl+C to stop the monitor');
    console.log('━'.repeat(50));
    console.log('');

    // Handle graceful shutdown
    process.on('SIGINT', () => {
      console.log('\n🛑 Stopping price monitor...');
      priceMonitor.stop();
      console.log('✅ Monitor stopped gracefully');
      process.exit(0);
    });

  } catch (error) {
    if (error.code === 'ERR_MODULE_NOT_FOUND') {
      console.error('❌ Module not found - TypeScript not compiled');
      console.error('');
      console.error('Solution: Run the build first');
      console.error('  npm run build');
      console.error('  npm run start:monitor');
    } else {
      console.error('❌ Fatal error:', error.message);
    }
    process.exit(1);
  }
})();
