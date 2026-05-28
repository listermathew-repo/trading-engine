/**
 * Insert a pending trade into the database
 * @param trade - The trade object with signal details
 */
export async function insertPendingTrade(trade: {
  id: string;
  symbol: string;
  direction: 'long' | 'short';
  entry_level: number;
  stop_level: number;
  retap_level: number;
  risk_amount: number;
  scenario: string;
  status: string;
  message: string;
}): Promise<string> {
  try {
    // TODO: Replace with actual database insert (Prisma, SQLite, etc.)
    console.log('[DB] Inserting pending trade:', {
      ...trade,
      timestamp: new Date().toISOString(),
    });

    return trade.id;
  } catch (error) {
    console.error('[DB Error] Failed to insert pending trade:', error);
    throw error;
  }
}

/**
 * Send alert via ntfy.sh webhook
 * @param title - Alert title
 * @param message - Alert message
 * @param priority - Alert priority (1-5, where 5 is URGENT)
 */
export async function sendAlert(
  title: string,
  message: string,
  priority: number = 3
): Promise<void> {
  try {
    const ntfyUrl = process.env.NTFY_URL || 'https://ntfy.sh/mgm-7k4x-live';

    const response = await fetch(ntfyUrl, {
      method: 'POST',
      headers: {
        'Title': title,
        'Priority': priority.toString(),
        'Tags': 'trading,stage5',
      },
      body: message,
    });

    if (!response.ok) {
      console.warn(`[Ntfy] Warning: ${response.status} ${response.statusText}`);
    } else {
      console.log(`[Ntfy] Alert sent: ${title}`);
    }
  } catch (error) {
    console.error('[Ntfy Error] Failed to send alert:', error);
    // Don't throw - ntfy failures shouldn't stop the trading system
  }
}

/**
 * Log system health check
 */
export async function logHealthCheck(component: string, status: string, message?: string): Promise<void> {
  console.log(`[Health] ${component}: ${status}${message ? ` - ${message}` : ''}`);
}

/**
 * Create an alert callback function for PriceMonitor
 * Wraps sendAlert to match the (message: string) => Promise<void> signature
 * @returns Alert callback function suitable for PriceMonitor.onAlert
 */
export function createAlertCallback(): (message: string) => Promise<void> {
  return async (message: string) => {
    // Send as NORMAL priority (3) by default for price monitor alerts
    // Use higher priority (4) for critical errors
    const priority = message.includes('❌') ? 4 : 3;
    const title = message.includes('❌') ? '[ERROR]' : '[SIGNAL]';
    await sendAlert(title, message, priority);
  };
}
