"""
STRATEGY MODULE
Detects FVG signals and calculates risk parameters.
Does NOT execute trades—just defines the setup.
"""

import pandas as pd
import numpy as np


def calculate_atr(bars, period=14):
    """Calculate Average True Range for volatility measurement.

    bars is list of tuples: (high, low, close) or (high, low, close, ...)
    """
    if len(bars) < period:
        return None
    trs = []
    prev_close = bars[0][2] if len(bars[0]) >= 3 else bars[0][2]  # close is index 2 in (h, l, c)
    for bar in bars:
        high, low, close = bar[0], bar[1], bar[2]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
        prev_close = close
    return sum(trs[-period:]) / period


def detect_fvgs(bars, atr_threshold=0.25):
    """
    Detect Fair Value Gaps (unfiltered: gap > 0 pips).

    Input: List of bars (symbol, time, open, high, low, close, volume, hour_utc, minute_utc)
    Output: List of FVG signals {timestamp, type, entry, gap_pips, bar_idx}
    """
    signals = []
    rolling_bars = []

    for i in range(len(bars) - 1):
        current = bars[i]
        next_bar = bars[i + 1]

        sym, time_str, o, h, l, c, vol, utc_h, utc_m = current[:9]
        next_h, next_l = next_bar[3], next_bar[4]

        rolling_bars.append((h, l, c))
        if len(rolling_bars) > 14:
            rolling_bars.pop(0)

        atr = calculate_atr(rolling_bars, 14)
        if atr is None or atr == 0:
            continue

        gap_threshold = atr_threshold * atr
        fvg_type = None
        entry_price = None
        gap_size = 0

        # LONG FVG: current low > next high
        if l > next_h:
            fvg_type = 'LONG'
            entry_price = l
            gap_size = (l - next_h) * 10000

        # SHORT FVG: current high < next low
        elif h < next_l:
            fvg_type = 'SHORT'
            entry_price = h
            gap_size = (next_l - h) * 10000

        if fvg_type:
            signals.append({
                'bar_idx': i,
                'timestamp': time_str,
                'symbol': sym,
                'type': fvg_type,
                'entry_level': entry_price,
                'gap_pips': gap_size,
                'utc_h': utc_h,
                'utc_m': utc_m,
            })

    return signals


def get_swing_stop(bars, fvg_bar_idx, lookback=8):
    """
    Find swing high/low BEFORE the FVG formed.

    For LONG: Find lowest low in bars[fvg_bar_idx-lookback : fvg_bar_idx]
    For SHORT: Find highest high in bars[fvg_bar_idx-lookback : fvg_bar_idx]

    Returns dict with both swing_low and swing_high
    """
    start_idx = max(0, fvg_bar_idx - lookback)
    lookback_bars = bars[start_idx:fvg_bar_idx]

    if len(lookback_bars) == 0:
        return None

    swing_low = min(b[4] for b in lookback_bars)  # b[4] = low
    swing_high = max(b[3] for b in lookback_bars)  # b[3] = high

    return {
        'swing_low': swing_low - 0.0001,  # 1 pip below
        'swing_high': swing_high + 0.0001,  # 1 pip above
    }


def calculate_risk_targets(entry_price, stop_loss, rr_ratio=2.0, side='LONG'):
    """
    Calculate take profit from risk-reward ratio.

    Input: entry, stop, R:R ratio (2.0 = 1:2)
    Output: {risk_distance, risk_pips, take_profit, r_ratio}
    """
    if side == 'LONG':
        risk = entry_price - stop_loss
        take_profit = entry_price + (risk * rr_ratio)
    else:  # SHORT
        risk = stop_loss - entry_price
        take_profit = entry_price - (risk * rr_ratio)

    return {
        'risk_distance': abs(risk),
        'risk_pips': abs(risk) * 10000,
        'take_profit': take_profit,
        'r_ratio': rr_ratio,
    }


def get_h4_bias(h4_bars, ema_period=20):
    """
    Determine H4 structural trend using EMA.

    Input: H4 bars list
    Returns: 1 (Bullish), -1 (Bearish), 0 (Neutral)
    """
    if len(h4_bars) < ema_period:
        return 0

    closes = [b[5] for b in h4_bars]
    ema_values = pd.Series(closes).ewm(span=ema_period, adjust=False).mean()

    current_close = closes[-1]
    current_ema = ema_values.iloc[-1]

    if current_close > current_ema:
        return 1  # Bullish
    elif current_close < current_ema:
        return -1  # Bearish
    else:
        return 0  # Neutral


def get_daily_bias(daily_bars, lookback=20):
    """
    Determine Daily structural trend using recent swing highs/lows.

    Simple method: If current close > average of last 20 highs, bullish.
    If current close < average of last 20 lows, bearish.

    Input: Daily bars list
    Returns: 1 (Bullish), -1 (Bearish), 0 (Neutral)
    """
    if len(daily_bars) < lookback:
        return 0

    recent_bars = daily_bars[-lookback:]
    highs = [b[3] for b in recent_bars]
    lows = [b[4] for b in recent_bars]
    closes = [b[5] for b in recent_bars]

    avg_high = sum(highs) / len(highs)
    avg_low = sum(lows) / len(lows)
    current_close = closes[-1]

    if current_close > avg_high:
        return 1  # Bullish (above recent highs)
    elif current_close < avg_low:
        return -1  # Bearish (below recent lows)
    else:
        return 0  # Neutral


# Export functions for use in engine.py
__all__ = [
    'calculate_atr',
    'detect_fvgs',
    'get_swing_stop',
    'calculate_risk_targets',
    'get_h4_bias',
    'get_daily_bias',
]
