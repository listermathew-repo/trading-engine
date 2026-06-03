"""Position sizing and risk management calculations."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PositionQualityRating(Enum):
    """Trade setup quality rating."""
    A_PLUS = "A+"       # Highest quality: $800
    A = "A"             # High quality: $600
    B = "B"             # Medium quality: $400
    C = "C"             # Lower quality: $200


@dataclass
class TradeSetup:
    """Trade setup information for position sizing."""
    entry_price: float
    stop_loss: float
    direction: str  # "BUY" or "SELL"
    quality: PositionQualityRating
    account_balance: float
    risk_percent: float = 0.005  # 0.5% default risk per trade


class PositionSizer:
    """Calculate position sizes based on risk management rules."""

    # Quality-based position sizing (default)
    POSITION_SIZE_BY_QUALITY = {
        PositionQualityRating.A_PLUS: 800.0,   # $800
        PositionQualityRating.A: 600.0,        # $600
        PositionQualityRating.B: 400.0,        # $400
        PositionQualityRating.C: 200.0,        # $200
    }

    # EUR/USD pip value: 1 lot = $10 per pip
    EUR_USD_PIP_VALUE = 10.0

    @staticmethod
    def calculate_size_by_quality(quality: PositionQualityRating) -> float:
        """
        Calculate position size based on setup quality.

        Risk per trade varies by setup quality:
        - A+ setup: $800 risk (highest quality FVG, perfect entry)
        - A setup: $600 risk (good FVG, confirmed entry)
        - B setup: $400 risk (OK FVG, some confirmation)
        - C setup: $200 risk (marginal FVG, risky entry)

        Args:
            quality: PositionQualityRating enum

        Returns:
            Position size in lots for EUR/USD (0.01 = 1 micro-lot)
        """
        return PositionSizer.POSITION_SIZE_BY_QUALITY.get(quality, 200.0)

    @staticmethod
    def calculate_size_by_risk(
        entry_price: float,
        stop_loss: float,
        risk_amount: float,
        pip_value: float = EUR_USD_PIP_VALUE,
    ) -> float:
        """
        Calculate position size based on risk amount and stop loss.

        Formula: Position Size = Risk Amount / (Stop Loss Distance * Pip Value)

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_amount: Dollar amount willing to risk
            pip_value: Value per pip (EUR/USD = $10 per lot)

        Returns:
            Position size in lots
        """
        stop_pips = abs(entry_price - stop_loss) / 0.0001  # Convert to pips

        if stop_pips == 0:
            return 0.01  # Minimum size

        size = risk_amount / (stop_pips * pip_value)
        return max(0.01, round(size, 2))

    @staticmethod
    def calculate_risk_reward_ratio(
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        direction: str,
    ) -> float:
        """
        Calculate risk-reward ratio.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            direction: "BUY" or "SELL"

        Returns:
            Risk-reward ratio (e.g., 1.5 = 1.5:1)
        """
        if direction == "BUY":
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
        else:  # SELL
            risk = stop_loss - entry_price
            reward = entry_price - take_profit

        if risk == 0:
            return 0.0

        return reward / risk

    @staticmethod
    def calculate_r_multiples(
        entry_price: float,
        stop_loss: float,
        exit_price: float,
        direction: str,
    ) -> float:
        """
        Calculate R multiples for a trade.

        R = entry price - stop loss (the "risk unit")
        Trade Result in R = (Exit Price - Entry Price) / R

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            exit_price: Exit price (actual or TP)
            direction: "BUY" or "SELL"

        Returns:
            R multiples gained/lost (positive = profit, negative = loss)
        """
        r_unit = abs(entry_price - stop_loss)

        if r_unit == 0:
            return 0.0

        if direction == "BUY":
            pnl = exit_price - entry_price
        else:  # SELL
            pnl = entry_price - exit_price

        return pnl / r_unit

    @staticmethod
    def calculate_monthly_r_summary(trades: list) -> dict:
        """
        Calculate monthly R accumulation statistics.

        Args:
            trades: List of trade dicts with:
                   - entry_price, stop_loss, exit_price, direction, status

        Returns:
            Dictionary with:
                - total_r: Sum of all R
                - avg_r: Average R per trade
                - winning_r: Sum of positive R
                - losing_r: Sum of negative R
                - win_count: Number of wins
                - loss_count: Number of losses
                - r_factor: Win avg R / Loss avg R (higher is better)
        """
        if not trades:
            return {
                "total_r": 0.0,
                "avg_r": 0.0,
                "winning_r": 0.0,
                "losing_r": 0.0,
                "win_count": 0,
                "loss_count": 0,
                "r_factor": 0.0,
            }

        r_values = []
        winning_r_values = []
        losing_r_values = []

        for trade in trades:
            r = PositionSizer.calculate_r_multiples(
                trade["entry_price"],
                trade["stop_loss"],
                trade["exit_price"],
                trade["direction"],
            )
            r_values.append(r)

            if r > 0:
                winning_r_values.append(r)
            elif r < 0:
                losing_r_values.append(r)

        total_r = sum(r_values)
        win_count = len(winning_r_values)
        loss_count = len(losing_r_values)

        avg_r = total_r / len(trades) if trades else 0.0
        winning_r = sum(winning_r_values) if winning_r_values else 0.0
        losing_r = sum(losing_r_values) if losing_r_values else 0.0

        # R Factor = (Win Count * Avg Win R) / (Loss Count * Avg Loss R)
        avg_win_r = (winning_r / win_count) if win_count > 0 else 0.0
        avg_loss_r = abs(losing_r / loss_count) if loss_count > 0 else 0.0
        r_factor = (avg_win_r / avg_loss_r) if avg_loss_r > 0 else 0.0

        return {
            "total_r": total_r,
            "avg_r": avg_r,
            "winning_r": winning_r,
            "losing_r": losing_r,
            "win_count": win_count,
            "loss_count": loss_count,
            "r_factor": r_factor,
            "avg_win_r": avg_win_r,
            "avg_loss_r": avg_loss_r,
        }

    @staticmethod
    def calculate_equity_curve(
        starting_balance: float,
        trades: list,
    ) -> list[float]:
        """
        Calculate equity curve over time.

        Args:
            starting_balance: Starting account balance
            trades: List of trade dicts with 'pnl' key

        Returns:
            List of balance values after each trade
        """
        equity = [starting_balance]
        current_balance = starting_balance

        for trade in trades:
            pnl = trade.get("pnl", 0.0)
            current_balance += pnl
            equity.append(current_balance)

        return equity

    @staticmethod
    def calculate_drawdown(equity_curve: list[float]) -> tuple[float, float, int]:
        """
        Calculate maximum drawdown.

        Args:
            equity_curve: List of balance values over time

        Returns:
            Tuple of (max_drawdown_pct, max_drawdown_value, peak_index)
        """
        if len(equity_curve) < 2:
            return 0.0, 0.0, 0

        max_equity = 0.0
        max_drawdown = 0.0
        max_drawdown_pct = 0.0
        peak_index = 0

        for i, balance in enumerate(equity_curve):
            if balance > max_equity:
                max_equity = balance
                peak_index = i

            drawdown = max_equity - balance
            drawdown_pct = (drawdown / max_equity * 100) if max_equity > 0 else 0

            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown_pct

        return max_drawdown_pct, max_drawdown, peak_index

    @staticmethod
    def calculate_sharpe_ratio(
        returns: list[float],
        risk_free_rate: float = 0.02,
    ) -> float:
        """
        Calculate Sharpe ratio for a series of returns.

        Sharpe Ratio = (Mean Return - Risk Free Rate) / Std Dev

        Args:
            returns: List of returns (as decimals, e.g., 0.05 = 5%)
            risk_free_rate: Annual risk-free rate (default 2%)

        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0

        import statistics

        mean_return = statistics.mean(returns)
        stdev = statistics.stdev(returns)

        if stdev == 0:
            return 0.0

        return (mean_return - (risk_free_rate / 252)) / stdev


@dataclass
class RiskManagementRules:
    """Risk management rules for trading."""
    max_risk_per_trade: float = 0.005  # 0.5% of account
    max_daily_loss: float = 0.02        # 2% of account
    max_monthly_loss: float = 0.05      # 5% of account
    max_consecutive_losses: int = 3     # Stop after 3 losses
    max_drawdown_threshold: float = 0.15  # 15% max drawdown
    min_risk_reward_ratio: float = 1.0  # 1:1 minimum R:R


class RiskValidator:
    """Validate trades against risk management rules."""

    @staticmethod
    def validate_position(
        setup: TradeSetup,
        rules: RiskManagementRules,
    ) -> tuple[bool, str]:
        """
        Validate if a position meets risk management rules.

        Args:
            setup: TradeSetup object
            rules: RiskManagementRules object

        Returns:
            Tuple of (is_valid, reason)
        """
        risk_amount = setup.account_balance * rules.max_risk_per_trade

        stop_pips = abs(setup.entry_price - setup.stop_loss) / 0.0001

        if stop_pips == 0:
            return False, "Stop loss too close to entry"

        position_size = PositionSizer.calculate_size_by_risk(
            setup.entry_price,
            setup.stop_loss,
            risk_amount,
        )

        max_loss_value = position_size * stop_pips * 10.0  # EUR/USD = $10/pip

        if max_loss_value > risk_amount:
            return False, f"Position size exceeds max risk: ${max_loss_value:.2f} > ${risk_amount:.2f}"

        return True, "Position valid"

    @staticmethod
    def check_daily_loss_limit(
        current_daily_loss: float,
        rules: RiskManagementRules,
        account_balance: float,
    ) -> tuple[bool, str]:
        """Check if daily loss limit has been exceeded."""
        max_daily_loss = account_balance * rules.max_daily_loss

        if current_daily_loss > max_daily_loss:
            return False, f"Daily loss limit exceeded: ${current_daily_loss:.2f} > ${max_daily_loss:.2f}"

        return True, "Daily loss limit OK"

    @staticmethod
    def check_consecutive_losses(
        num_consecutive_losses: int,
        rules: RiskManagementRules,
    ) -> tuple[bool, str]:
        """Check if consecutive loss limit has been exceeded."""
        if num_consecutive_losses >= rules.max_consecutive_losses:
            return False, f"Consecutive loss limit reached: {num_consecutive_losses}"

        return True, "Consecutive loss limit OK"
