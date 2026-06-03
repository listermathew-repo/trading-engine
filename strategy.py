"""
STRATEGY MODULE
Market Alignment Framework (MAF) strategy implementation.
Detects FVG signals and calculates risk parameters.
Does NOT execute trades—just defines the setup.

Implements StrategyInterface protocol for pluggable strategy architecture.
"""

from typing import List, Dict, Any
import pandas as pd
import numpy as np
from strategy_interface import StrategyInterface


class MAFStrategy:
    """
    Market Alignment Framework strategy.
    Implements the StrategyInterface protocol for use with the backtest engine.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize strategy with configuration parameters.

        Args:
            config: Dict with keys like 'atr_threshold', 'atr_period', 'lookback', etc.
        """
        self.config = config or {}
        self.atr_period = self.config.get('atr_period', 14)
        self.atr_threshold = self.config.get('atr_threshold', 0.25)
        self.lookback = self.config.get('lookback', 8)
        self.h4_ema_period = self.config.get('h4_ema_period', 20)
        self.daily_lookback = self.config.get('daily_lookback', 20)

    def generate_signals(self, data: List[Any]) -> List[Dict[str, Any]]:
        """
        Detect Fair Value Gap (FVG) signals from M15 price data.

        Args:
            data: List of bars (symbol, time, open, high, low, close, volume, hour_utc, minute_utc)

        Returns:
            List of FVG signal dicts with keys:
            - 'bar_idx', 'timestamp', 'symbol', 'type', 'entry_level', 'gap_pips', 'utc_h', 'utc_m'
        """
        signals = []
        rolling_bars = []

        for i in range(len(data) - 1):
            current = data[i]
            next_bar = data[i + 1]

            sym, time_str, o, h, l, c, vol, utc_h, utc_m = current[:9]
            next_h, next_l = next_bar[3], next_bar[4]

            rolling_bars.append((h, l, c))
            if len(rolling_bars) > self.atr_period:
                rolling_bars.pop(0)

            atr = self._calculate_atr(rolling_bars, self.atr_period)
            if atr is None or atr == 0:
                continue

            gap_threshold = self.atr_threshold * atr
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


    def calculate_indicators(self, data: List[Any]) -> Dict[str, Any]:
        """
        Calculate all technical indicators from M15, H4, and Daily data.

        Args:
            data: List of M15 bars (last bar is most recent)

        Returns:
            Dict with keys: 'atr', 'h4_bias', 'daily_bias'
            (h4_bias and daily_bias depend on having H4/Daily data available)
        """
        recent_data = data[-200:] if len(data) > 200 else data
        rolling_bars = [(b[3], b[4], b[5]) for b in recent_data]
        atr = self._calculate_atr(rolling_bars, self.atr_period)

        return {
            'atr': atr,
            'h4_bias': 0,  # Will be set by engine if H4 data available
            'daily_bias': 0,  # Will be set by engine if Daily data available
        }

    def filter_signals(
        self, signals: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply confluence filters to reduce false signals.

        Currently applies H4 bias filter if H4 data is provided in context.
        Filter mode: 'counter' (trade reversals against H4 bias)

        Args:
            signals: Unfiltered FVG signals
            context: Dict with 'bars', 'h4_bars', 'daily_bars', 'config'

        Returns:
            Filtered signals that pass all confluence tests
        """
        bars = context.get('bars', [])
        h4_bars = context.get('h4_bars', [])
        daily_bars = context.get('daily_bars', [])
        config = context.get('config', self.config)

        filtered_signals = signals

        # Liquidity sweep filter (if enabled)
        if config.get('use_sweep_filter', True) and bars:
            filtered_signals = [
                s for s in filtered_signals
                if self._detect_liquidity_sweep(bars, s)
            ]

        # H4 confluence filter (if available)
        if h4_bars:
            h4_bias = self._get_h4_bias(h4_bars, self.h4_ema_period)
            filter_mode = config.get('h4_filter_mode', 'counter')
            filtered_signals = [
                s for s in filtered_signals
                if self._apply_h4_filter(s, h4_bias, filter_mode)
            ]

        # Daily confluence filter (optional)
        if daily_bars and config.get('use_daily_filter', False):
            daily_bias = self._get_daily_bias(daily_bars, self.daily_lookback)
            filtered_signals = [
                s for s in filtered_signals
                if self._apply_daily_filter(s, daily_bias)
            ]

        return filtered_signals

    # ========== HELPER METHODS (Static for reusability) ==========

    @staticmethod
    def _calculate_atr(bars, period=14):
        """Calculate Average True Range for volatility measurement.

        Args:
            bars: List of tuples (high, low, close)
            period: ATR lookback period

        Returns:
            float or None if insufficient bars
        """
        if len(bars) < period:
            return None
        trs = []
        prev_close = bars[0][2]
        for bar in bars:
            high, low, close = bar[0], bar[1], bar[2]
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            trs.append(tr)
            prev_close = close
        return sum(trs[-period:]) / period

    @staticmethod
    def _get_swing_stop(bars, fvg_bar_idx, lookback=8):
        """Find swing high/low BEFORE the FVG formed.

        Returns dict with both swing_low and swing_high
        """
        start_idx = max(0, fvg_bar_idx - lookback)
        lookback_bars = bars[start_idx:fvg_bar_idx]

        if len(lookback_bars) == 0:
            return None

        swing_low = min(b[4] for b in lookback_bars)
        swing_high = max(b[3] for b in lookback_bars)

        return {
            'swing_low': swing_low - 0.0001,
            'swing_high': swing_high + 0.0001,
        }

    @staticmethod
    def _calculate_risk_targets(entry_price, stop_loss, rr_ratio=2.0, side='LONG'):
        """Calculate take profit from risk-reward ratio."""
        if side == 'LONG':
            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * rr_ratio)
        else:
            risk = stop_loss - entry_price
            take_profit = entry_price - (risk * rr_ratio)

        return {
            'risk_distance': abs(risk),
            'risk_pips': abs(risk) * 10000,
            'take_profit': take_profit,
            'r_ratio': rr_ratio,
        }

    @staticmethod
    def _get_h4_bias(h4_bars, ema_period=20):
        """Determine H4 structural trend using EMA."""
        if len(h4_bars) < ema_period:
            return 0

        closes = [b[5] for b in h4_bars]
        ema_values = pd.Series(closes).ewm(span=ema_period, adjust=False).mean()

        current_close = closes[-1]
        current_ema = ema_values.iloc[-1]

        if current_close > current_ema:
            return 1
        elif current_close < current_ema:
            return -1
        else:
            return 0

    @staticmethod
    def _get_daily_bias(daily_bars, lookback=20):
        """Determine Daily structural trend using swing highs/lows."""
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
            return 1
        elif current_close < avg_low:
            return -1
        else:
            return 0

    @staticmethod
    def _apply_h4_filter(signal, h4_bias, filter_mode='counter'):
        """Apply H4 confluence filter to a signal.

        filter_mode='counter': Trade reversals (LONG when bearish, SHORT when bullish)
        filter_mode='aligned': Trade with trend (LONG when bullish, SHORT when bearish)
        """
        if h4_bias == 0:
            return False

        if filter_mode == 'counter':
            if signal['type'] == 'LONG':
                return h4_bias == -1
            else:
                return h4_bias == 1
        else:
            if signal['type'] == 'LONG':
                return h4_bias == 1
            else:
                return h4_bias == -1

    @staticmethod
    def _apply_daily_filter(signal, daily_bias):
        """Apply Daily confluence filter (veto mode)."""
        return daily_bias != 0

    @staticmethod
    def _detect_liquidity_sweep(bars, signal, lookback=8):
        """
        Verify that the FVG entry is at a swept structural level.

        For LONG FVG: Entry level should be at/near the swing low (price reached that level)
        For SHORT FVG: Entry level should be at/near the swing high (price reached that level)

        A swept level means price actually tested that support/resistance before reversal.

        Args:
            bars: List of bars (symbol, time, open, high, low, close, volume, h, m)
            signal: Dict with 'bar_idx' (int), 'type' ('LONG' or 'SHORT'), 'entry_level' (float)
            lookback: Number of bars to check for swing (default 8)

        Returns:
            bool: True if entry is at a swept structural level, False otherwise
        """
        fvg_bar_idx = signal['bar_idx']

        if fvg_bar_idx < lookback:
            return True  # Not enough history, allow trade

        # Get bars BEFORE FVG formed
        lookback_bars = bars[fvg_bar_idx - lookback : fvg_bar_idx]

        if len(lookback_bars) == 0:
            return True

        if signal['type'] == 'LONG':
            # For LONG FVG: Entry should be CLOSE to the swing low
            # This confirms price tested the swing before reversing up
            swing_low = min(b[4] for b in lookback_bars)  # b[4] = low
            # Entry within 0.3% of swing low = strong structural level
            distance = abs(signal['entry_level'] - swing_low) / swing_low
            return distance < 0.003  # 0.3% tolerance
        else:  # SHORT
            # For SHORT FVG: Entry should be CLOSE to the swing high
            # This confirms price tested the swing before reversing down
            swing_high = max(b[3] for b in lookback_bars)  # b[3] = high
            # Entry within 0.3% of swing high = strong structural level
            distance = abs(signal['entry_level'] - swing_high) / swing_high
            return distance < 0.003  # 0.3% tolerance


# ========== BACKWARD COMPATIBILITY FUNCTIONS ==========
# Keep module-level functions for existing code that uses them directly

def calculate_atr(bars, period=14):
    """Deprecated: Use MAFStrategy._calculate_atr() instead."""
    return MAFStrategy._calculate_atr(bars, period)


def detect_fvgs(bars, atr_threshold=0.25):
    """Deprecated: Use MAFStrategy().generate_signals() instead."""
    strategy = MAFStrategy({'atr_threshold': atr_threshold})
    return strategy.generate_signals(bars)


def get_swing_stop(bars, fvg_bar_idx, lookback=8):
    """Deprecated: Use MAFStrategy._get_swing_stop() instead."""
    return MAFStrategy._get_swing_stop(bars, fvg_bar_idx, lookback)


def calculate_risk_targets(entry_price, stop_loss, rr_ratio=2.0, side='LONG'):
    """Deprecated: Use MAFStrategy._calculate_risk_targets() instead."""
    return MAFStrategy._calculate_risk_targets(entry_price, stop_loss, rr_ratio, side)


def get_h4_bias(h4_bars, ema_period=20):
    """Deprecated: Use MAFStrategy._get_h4_bias() instead."""
    return MAFStrategy._get_h4_bias(h4_bars, ema_period)


def get_daily_bias(daily_bars, lookback=20):
    """Deprecated: Use MAFStrategy._get_daily_bias() instead."""
    return MAFStrategy._get_daily_bias(daily_bars, lookback)


# Export for backward compatibility
__all__ = [
    'MAFStrategy',
    'calculate_atr',
    'detect_fvgs',
    'get_swing_stop',
    'calculate_risk_targets',
    'get_h4_bias',
    'get_daily_bias',
]
