"""Fair Value Gap (FVG) backtesting strategy for EUR/USD."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional
from enum import Enum
from .capital_data import OHLCV
from .fvg_detector import FVG, FVGDetector
from .swing_detector import SwingDetector
from .slippage_model import RealisticBacktestSimulator, REALISTIC_FOREX_CONFIG


class TradeStatus(Enum):
    """Trade status enumeration."""
    PENDING = "pending"
    FILLED = "filled"
    WIN = "win"
    LOSS = "loss"
    NON_PROGRESSIVE = "non-progressive"  # SL hit immediately


class SessionType(Enum):
    """Trading session type."""
    LONDON_OPEN = "london_open"
    LONDON_CLOSE = "london_close"
    ASIAN_CLOSE = "asian_close"
    UNKNOWN = "unknown"


@dataclass
class BacktestTrade:
    """Single trade in the backtest."""
    entry_index: int          # Index in 15m candle list
    entry_time: datetime      # Entry timestamp
    entry_price: float        # Entry price (high of lowest red candle - theoretical)
    stop_loss: float          # Stop loss price
    take_profit: float        # Take profit price (1R - theoretical)
    direction: str            # "BUY" or "SELL"
    risk_per_trade: float     # Risk amount in $ (position sizing)
    fvg_zone: FVG             # Associated FVG
    swing_lookback: int       # Which swing lookback was used (5, 10, or 20)
    session: str              # Session type at entry
    exit_index: Optional[int] = None      # Index where trade exited
    exit_time: Optional[datetime] = None  # Exit timestamp
    exit_price: Optional[float] = None    # Exit price (theoretical)
    status: TradeStatus = TradeStatus.PENDING
    r_gained: float = 0.0     # R multiples gained/lost
    pnl: float = 0.0          # Profit/loss in $ (theoretical)
    pnl_realistic: float = 0.0  # Profit/loss with slippage/commission
    liquidity_level: str = "normal"  # "high" or "low" based on time

    def __repr__(self) -> str:
        status_str = self.status.value.upper() if self.status else "UNKNOWN"
        r_str = f"R{self.r_gained:+.2f}" if self.r_gained != 0 else "PENDING"
        pnl_str = f"${self.pnl:+.2f}"
        exit_str = f"@ {self.exit_price:.4f}" if self.exit_price else "OPEN"

        return (
            f"{self.direction} | "
            f"Entry: {self.entry_time.strftime('%Y-%m-%d %H:%M')} @ {self.entry_price:.4f} | "
            f"SL: {self.stop_loss:.4f} | TP: {self.take_profit:.4f} | "
            f"Exit: {exit_str} | "
            f"Status: {status_str} | {r_str} | {pnl_str} | "
            f"Lookback: {self.swing_lookback}C"
        )


@dataclass
class BacktestResults:
    """Results of a backtest run."""
    trades: list[BacktestTrade] = field(default_factory=list)
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    non_progressive_trades: int = 0
    win_rate: float = 0.0
    total_r: float = 0.0
    avg_r_per_trade: float = 0.0
    total_pnl: float = 0.0
    avg_pnl_per_trade: float = 0.0

    def __repr__(self) -> str:
        return (
            f"BacktestResults: {self.total_trades} trades | "
            f"{self.winning_trades}W {self.losing_trades}L {self.non_progressive_trades}NP | "
            f"WR: {self.win_rate:.1%} | "
            f"Total R: {self.total_r:+.2f} | "
            f"Avg R: {self.avg_r_per_trade:+.2f} | "
            f"PnL: ${self.total_pnl:+.2f}"
        )


class FVGStrategy:
    """Fair Value Gap strategy backtester with realistic slippage modeling."""

    def __init__(
        self,
        risk_per_trade: float = 100.0,  # $ per trade
        lookback_periods: list[int] = [5, 10, 20],
        use_realistic_slippage: bool = True,  # Account for slippage and commission
    ):
        self.risk_per_trade = risk_per_trade
        self.lookback_periods = lookback_periods
        self.use_realistic_slippage = use_realistic_slippage

        # Initialize slippage simulator for realistic backtesting
        if use_realistic_slippage:
            self.simulator = RealisticBacktestSimulator(REALISTIC_FOREX_CONFIG)
        else:
            self.simulator = None

    @staticmethod
    def to_adelaide_time(utc_time: datetime) -> datetime:
        """Convert UTC to Adelaide time (ACDT, UTC+10:30)."""
        acdt_offset = timedelta(hours=10, minutes=30)
        acdt = timezone(acdt_offset)
        return utc_time.astimezone(acdt)

    @staticmethod
    def is_in_session_window(
        timestamp: datetime,
        session_start_hour: int = 9,
        session_end_hour: int = 22,
    ) -> bool:
        """
        Check if timestamp is within trading session (Adelaide time).

        Default: 9 a.m. - 10 p.m. Adelaide (ACDT).

        Args:
            timestamp: Datetime in UTC
            session_start_hour: Session start hour in Adelaide time (0-23)
            session_end_hour: Session end hour in Adelaide time (0-23)

        Returns:
            True if within session window
        """
        adelaide_time = FVGStrategy.to_adelaide_time(timestamp)
        hour = adelaide_time.hour

        if session_start_hour < session_end_hour:
            # Normal range (e.g., 9-22)
            return session_start_hour <= hour < session_end_hour
        else:
            # Range crosses midnight (e.g., 22-6)
            return hour >= session_start_hour or hour < session_end_hour

    @staticmethod
    def classify_session(timestamp: datetime) -> SessionType:
        """
        Classify the trading session based on UTC timestamp.

        - London Open: ~08:00 UTC (high liquidity for EUR/USD)
        - London Close: ~17:00 UTC
        - Asian Close: ~11:00 UTC

        Args:
            timestamp: Datetime in UTC

        Returns:
            SessionType enum
        """
        hour_utc = timestamp.hour

        if 7 <= hour_utc < 12:
            return SessionType.LONDON_OPEN
        elif 15 <= hour_utc < 18:
            return SessionType.LONDON_CLOSE
        elif 8 <= hour_utc < 11:
            return SessionType.ASIAN_CLOSE
        else:
            return SessionType.UNKNOWN

    def backtest(
        self,
        hourly_candles: list[OHLCV],
        minute15_candles: list[OHLCV],
    ) -> BacktestResults:
        """
        Run the FVG strategy backtest.

        Args:
            hourly_candles: 1H OHLCV candles for FVG detection
            minute15_candles: 15m OHLCV candles for entry/exit

        Returns:
            BacktestResults with all trades and statistics
        """
        results = BacktestResults()

        # Detect FVGs on 1H timeframe
        detected_fvgs = FVGDetector.detect_fvgs(hourly_candles)
        unmitigated_fvgs = FVGDetector.filter_unmitigated(detected_fvgs, minute15_candles)

        if not unmitigated_fvgs:
            print("[WARN] No unmitigated FVGs detected")
            return results

        print(f"[INFO] Detected {len(unmitigated_fvgs)} unmitigated FVGs")

        # Process each 15m candle looking for entry signals
        for idx, candle in enumerate(minute15_candles):
            # Check session window (9am-10pm Adelaide time)
            if not self.is_in_session_window(candle.timestamp):
                continue

            # Check if price is in an active FVG zone
            active_fvgs = FVGDetector.get_active_fvgs_at_time(
                unmitigated_fvgs,
                candle.timestamp
            )

            for fvg in active_fvgs:
                if not fvg.contains_price(candle.close):
                    continue

                # Found a candle within FVG zone
                # Now look for entry signal: lowest red candle in this FVG
                fvg_start_idx = self._find_fvg_start_index(
                    minute15_candles, fvg.detected_at, idx
                )

                if fvg_start_idx is None:
                    continue

                # Find the lowest red candle within the FVG zone
                lowest_red_idx = SwingDetector.find_lowest_red_candle_in_range(
                    minute15_candles,
                    fvg_start_idx,
                    idx + 1,
                )

                if lowest_red_idx is None:
                    continue

                lowest_red_candle = minute15_candles[lowest_red_idx]

                # Entry signal: entry at HIGH of lowest red candle (on close of that candle)
                entry_price = lowest_red_candle.high
                entry_time = lowest_red_candle.timestamp

                # Determine direction based on FVG type
                if fvg.direction == "bullish":
                    direction = "BUY"
                    # Stop loss just below swing low
                    swing_lows = SwingDetector.find_multiple_swing_lows_at_index(
                        minute15_candles,
                        lowest_red_idx,
                        self.lookback_periods,
                    )

                    # Create trades for each swing lookback period
                    for lookback, swing_low in swing_lows.items():
                        if swing_low is None:
                            continue

                        # Stop loss 1 pip below swing low
                        stop_loss = swing_low - 0.0001
                        risk_distance = entry_price - stop_loss
                        r_multiple = 1.0  # 1R take profit

                        take_profit = entry_price + (risk_distance * r_multiple)

                        trade = BacktestTrade(
                            entry_index=lowest_red_idx,
                            entry_time=entry_time,
                            entry_price=entry_price,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            direction=direction,
                            risk_per_trade=self.risk_per_trade,
                            fvg_zone=fvg,
                            swing_lookback=lookback,
                            session=self.classify_session(entry_time).value,
                        )

                        # Simulate trade exit
                        self._simulate_exit(trade, minute15_candles, lowest_red_idx)
                        results.trades.append(trade)

                else:  # bearish FVG
                    direction = "SELL"
                    swing_lows = SwingDetector.find_multiple_swing_lows_at_index(
                        minute15_candles,
                        lowest_red_idx,
                        self.lookback_periods,
                    )

                    for lookback, swing_low in swing_lows.items():
                        if swing_low is None:
                            continue

                        # Stop loss 1 pip above swing low (for SELL)
                        stop_loss = swing_low + 0.0001
                        risk_distance = stop_loss - entry_price
                        r_multiple = 1.0

                        take_profit = entry_price - (risk_distance * r_multiple)

                        trade = BacktestTrade(
                            entry_index=lowest_red_idx,
                            entry_time=entry_time,
                            entry_price=entry_price,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            direction=direction,
                            risk_per_trade=self.risk_per_trade,
                            fvg_zone=fvg,
                            swing_lookback=lookback,
                            session=self.classify_session(entry_time).value,
                        )

                        self._simulate_exit(trade, minute15_candles, lowest_red_idx)
                        results.trades.append(trade)

        # Calculate statistics
        self._calculate_statistics(results)
        return results

    @staticmethod
    def _find_fvg_start_index(
        candles: list[OHLCV],
        fvg_time: datetime,
        current_idx: int,
    ) -> Optional[int]:
        """Find the candle index where the FVG was detected."""
        for i in range(current_idx, -1, -1):
            if candles[i].timestamp <= fvg_time:
                return i
        return None

    def _simulate_exit(
        self,
        trade: BacktestTrade,
        candles: list[OHLCV],
        entry_idx: int,
    ) -> None:
        """
        Simulate trade exit by walking forward through candles.

        Exit when:
        - Stop loss is hit (loss)
        - Take profit is hit (win)
        - End of data (still open)
        """
        for idx in range(entry_idx + 1, len(candles)):
            candle = candles[idx]

            # Check for non-progressive (SL hit immediately on same candle)
            if idx == entry_idx:
                if trade.direction == "BUY":
                    if candle.low <= trade.stop_loss:
                        trade.status = TradeStatus.NON_PROGRESSIVE
                        trade.exit_index = idx
                        trade.exit_time = candle.timestamp
                        trade.exit_price = trade.stop_loss
                        risk_distance = trade.entry_price - trade.stop_loss
                        trade.r_gained = -1.0
                        trade.pnl = -trade.risk_per_trade
                        trade.pnl_realistic = self._calculate_realistic_pnl(trade)
                        return
                else:  # SELL
                    if candle.high >= trade.stop_loss:
                        trade.status = TradeStatus.NON_PROGRESSIVE
                        trade.exit_index = idx
                        trade.exit_time = candle.timestamp
                        trade.exit_price = trade.stop_loss
                        risk_distance = trade.stop_loss - trade.entry_price
                        trade.r_gained = -1.0
                        trade.pnl = -trade.risk_per_trade
                        trade.pnl_realistic = self._calculate_realistic_pnl(trade)
                        return

            # Check for stop loss or take profit hit
            if trade.direction == "BUY":
                if candle.low <= trade.stop_loss:
                    trade.status = TradeStatus.LOSS
                    trade.exit_index = idx
                    trade.exit_time = candle.timestamp
                    trade.exit_price = trade.stop_loss
                    risk_distance = trade.entry_price - trade.stop_loss
                    trade.r_gained = -1.0
                    trade.pnl = -trade.risk_per_trade
                    trade.pnl_realistic = self._calculate_realistic_pnl(trade)
                    return

                if candle.high >= trade.take_profit:
                    trade.status = TradeStatus.WIN
                    trade.exit_index = idx
                    trade.exit_time = candle.timestamp
                    trade.exit_price = trade.take_profit
                    risk_distance = trade.entry_price - trade.stop_loss
                    trade.r_gained = (trade.take_profit - trade.entry_price) / risk_distance
                    trade.pnl = trade.risk_per_trade * trade.r_gained
                    trade.pnl_realistic = self._calculate_realistic_pnl(trade)
                    return

            else:  # SELL
                if candle.high >= trade.stop_loss:
                    trade.status = TradeStatus.LOSS
                    trade.exit_index = idx
                    trade.exit_time = candle.timestamp
                    trade.exit_price = trade.stop_loss
                    risk_distance = trade.stop_loss - trade.entry_price
                    trade.r_gained = -1.0
                    trade.pnl = -trade.risk_per_trade
                    trade.pnl_realistic = self._calculate_realistic_pnl(trade)
                    return

                if candle.low <= trade.take_profit:
                    trade.status = TradeStatus.WIN
                    trade.exit_index = idx
                    trade.exit_time = candle.timestamp
                    trade.exit_price = trade.take_profit
                    risk_distance = trade.stop_loss - trade.entry_price
                    trade.r_gained = (trade.entry_price - trade.take_profit) / risk_distance
                    trade.pnl = trade.risk_per_trade * trade.r_gained
                    trade.pnl_realistic = self._calculate_realistic_pnl(trade)
                    return

        # Trade still open at end of data
        trade.status = TradeStatus.PENDING

    def _calculate_realistic_pnl(
        self,
        trade: BacktestTrade,
    ) -> float:
        """Calculate net PnL with slippage and commission."""
        if not self.simulator or trade.exit_price is None:
            return trade.pnl

        # Adjust entry and exit prices for slippage
        adjusted_entry, entry_slippage = self.simulator.simulate_entry(
            trade.entry_price,
            trade.direction,
        )

        adjusted_exit = self.simulator.apply_exit_slippage(
            trade.exit_price,
            trade.direction,
            entry_slippage,  # Reuse entry slippage for consistency
        )

        # Calculate gross PnL with adjusted prices
        if trade.direction == "BUY":
            gross_pnl = (adjusted_exit - adjusted_entry) * 10000  # Approximate for 1 lot
        else:  # SELL
            gross_pnl = (adjusted_entry - adjusted_exit) * 10000

        # Calculate net PnL with commission
        net_pnl = self.simulator.calculate_net_pnl(
            gross_pnl,
            adjusted_entry,
            adjusted_exit,
            trade.direction,
            1.0,  # 1 lot assumed
        )

        return net_pnl

    @staticmethod
    def _calculate_statistics(results: BacktestResults) -> None:
        """Calculate backtest statistics."""
        results.total_trades = len(results.trades)

        if results.total_trades == 0:
            return

        for trade in results.trades:
            if trade.status == TradeStatus.WIN:
                results.winning_trades += 1
                results.total_r += trade.r_gained
                results.total_pnl += trade.pnl

            elif trade.status == TradeStatus.LOSS:
                results.losing_trades += 1
                results.total_r += trade.r_gained
                results.total_pnl += trade.pnl

            elif trade.status == TradeStatus.NON_PROGRESSIVE:
                results.non_progressive_trades += 1
                results.total_r += trade.r_gained
                results.total_pnl += trade.pnl

        closed_trades = results.winning_trades + results.losing_trades + results.non_progressive_trades

        if closed_trades > 0:
            results.win_rate = results.winning_trades / closed_trades
            results.avg_r_per_trade = results.total_r / results.total_trades
            results.avg_pnl_per_trade = results.total_pnl / results.total_trades
