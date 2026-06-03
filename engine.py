"""
ENGINE MODULE
Simulates limit order fills, position management, and P&L calculation.
Orchestrates the trading flow from signal to closed trade.
"""

from strategy import get_swing_stop, calculate_risk_targets, get_h4_bias


def apply_h4_confluence_filter(signal, h4_bars, filter_mode='aligned'):
    """
    Filter FVG signal based on H4 structural alignment or counter-trend.

    Two modes:
    - 'aligned': Only trade when FVG direction MATCHES H4 bias (trend following)
    - 'counter': Only trade when FVG direction OPPOSES H4 bias (reversal trades)

    Input: signal dict, H4 bars list, filter mode
    Output: True if signal passes filter, False otherwise
    """
    h4_bias = get_h4_bias(h4_bars, ema_period=20)

    if h4_bias == 0:  # Neutral H4
        return False  # Skip neutral environment

    if filter_mode == 'aligned':
        # Trade with trend: LONG when bullish, SHORT when bearish
        if signal['type'] == 'LONG':
            return h4_bias == 1
        else:  # SHORT
            return h4_bias == -1
    else:  # 'counter' mode
        # Trade counter-trend: LONG when bearish, SHORT when bullish
        if signal['type'] == 'LONG':
            return h4_bias == -1  # Bullish FVG during bearish H4 = reversal
        else:  # SHORT
            return h4_bias == 1  # Bearish FVG during bullish H4 = reversal


def simulate_limit_orders(bars, signals, h4_bars=None, daily_bars=None, max_wait_bars=96, use_h4_filter=False, h4_filter_mode='aligned', use_daily_filter=False):
    """
    Simulate limit order mitigation with optional H4 confluence filter.

    For each signal, check if price retraces to fill the limit order.
    Then track the trade to either stop or target.

    Input: bars (list), signals (list from detect_fvgs), h4_bars, filter mode ('aligned' or 'counter')
    Output: List of closed trades {entry, fill_bar, stop, target, exit, pnl_r}
    """
    trades = []

    for signal in signals:
        bar_idx = signal['bar_idx']
        fvg_type = signal['type']
        limit_price = signal['entry_level']

        # Apply H4 confluence filter if enabled
        if use_h4_filter and h4_bars:
            if not apply_h4_confluence_filter(signal, h4_bars, filter_mode=h4_filter_mode):
                continue  # Skip this signal - failed H4 filter

        # Apply Daily confluence filter if enabled (veto mode: skip neutral only)
        if use_daily_filter and daily_bars:
            from strategy import get_daily_bias
            daily_bias = get_daily_bias(daily_bars, lookback=20)
            if daily_bias == 0:  # Neutral daily - too choppy, skip
                continue
            # If Daily is biased, allow trade in any direction (H4 Counter handles direction)

        # Get swing-based stop (look back from bar_idx - 1)
        swing_stops = get_swing_stop(bars, bar_idx - 1, lookback=8)
        if swing_stops is None:
            continue

        if fvg_type == 'LONG':
            stop_loss = swing_stops['swing_low']
        else:  # SHORT
            stop_loss = swing_stops['swing_high']

        # Calculate risk and target
        risk_data = calculate_risk_targets(limit_price, stop_loss, rr_ratio=2.0, side=fvg_type)
        take_profit = risk_data['take_profit']
        risk_pips = risk_data['risk_pips']

        # PHASE 1: Wait for limit order fill (price retraces to entry)
        filled = False
        fill_bar = None
        bars_waited = 0

        for j in range(bar_idx + 1, min(bar_idx + 1 + max_wait_bars, len(bars))):
            fut_h, fut_l = bars[j][3], bars[j][4]
            bars_waited += 1

            if fvg_type == 'LONG':
                if fut_l <= stop_loss:  # Stop hit before fill - invalidated
                    break
                elif fut_l <= limit_price:  # Limit order filled!
                    filled = True
                    fill_bar = j
                    break
            else:  # SHORT
                if fut_h >= stop_loss:  # Stop hit before fill - invalidated
                    break
                elif fut_h >= limit_price:  # Limit order filled!
                    filled = True
                    fill_bar = j
                    break

        if not filled:
            continue

        # PHASE 2: Manage open trade to exit (stop or target)
        exit_price = None
        exit_reason = None

        for j in range(fill_bar + 1, len(bars)):
            fut_h, fut_l = bars[j][3], bars[j][4]

            if fvg_type == 'LONG':
                if fut_l <= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'stop'
                    break
                elif fut_h >= take_profit:
                    exit_price = take_profit
                    exit_reason = 'tp'
                    break
            else:  # SHORT
                if fut_h >= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'stop'
                    break
                elif fut_l <= take_profit:
                    exit_price = take_profit
                    exit_reason = 'tp'
                    break

        if exit_price is None:
            continue

        # Calculate P&L
        if fvg_type == 'LONG':
            pnl_pips = (exit_price - limit_price) * 10000
        else:  # SHORT
            pnl_pips = (limit_price - exit_price) * 10000

        pnl_r = pnl_pips / risk_pips if risk_pips > 0 else 0

        trades.append({
            'signal_idx': signal['bar_idx'],
            'timestamp': signal['timestamp'],
            'symbol': signal['symbol'],
            'type': fvg_type,
            'entry_price': limit_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'fill_bar': fill_bar,
            'bars_waited': bars_waited,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'pnl_pips': pnl_pips,
            'pnl_r': pnl_r,
            'risk_pips': risk_pips,
        })

    return trades


def calculate_expectancy(trades):
    """
    Calculate key metrics from closed trades.

    Input: List of trade dictionaries
    Output: {win_rate, avg_winner, avg_loser, expectancy, total_trades}
    """
    if not trades:
        return {
            'total_trades': 0,
            'winners': 0,
            'losers': 0,
            'win_rate': 0,
            'avg_winner_r': 0,
            'avg_loser_r': 0,
            'expectancy_r': 0,
        }

    winners = [t for t in trades if t['pnl_pips'] > 0]
    losers = [t for t in trades if t['pnl_pips'] <= 0]

    total = len(trades)
    win_rate = 100 * len(winners) / total if total else 0

    avg_win_r = sum(t['pnl_r'] for t in winners) / len(winners) if winners else 0
    avg_loss_r = abs(sum(t['pnl_r'] for t in losers) / len(losers)) if losers else 0

    expectancy = (win_rate/100 * avg_win_r) - ((1 - win_rate/100) * avg_loss_r)

    return {
        'total_trades': total,
        'winners': len(winners),
        'losers': len(losers),
        'win_rate': win_rate,
        'avg_winner_r': avg_win_r,
        'avg_loser_r': avg_loss_r,
        'expectancy_r': expectancy,
    }


def export_trade_log_markdown(trades):
    """
    Export trades as markdown table for manual review.

    Shows: Timestamp, Symbol, Type, Entry, Stop, Target, Exit, Reason, P&L, R-Multiple
    """
    if not trades:
        return "No trades to export."

    markdown = """
| # | Timestamp | Symbol | Type | Entry | Stop | Target | Exit | Reason | P&L Pips | R-Multiple |
|---|-----------|--------|------|-------|------|--------|------|--------|----------|------------|
"""

    for i, trade in enumerate(trades[:50], 1):  # Show first 50 for review
        markdown += f"| {i} | {trade['timestamp']} | {trade['symbol']} | {trade['type']} | {trade['entry_price']:.5f} | {trade['stop_loss']:.5f} | {trade['take_profit']:.5f} | {trade['exit_price']:.5f} | {trade['exit_reason']:4} | {trade['pnl_pips']:7.1f} | {trade['pnl_r']:+.2f}R |\n"

    return markdown


__all__ = [
    'simulate_limit_orders',
    'calculate_expectancy',
    'export_trade_log_markdown',
    'apply_h4_confluence_filter',
]
