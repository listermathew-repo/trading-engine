"""Slippage and commission modeling for realistic backtest results."""

from enum import Enum
from dataclasses import dataclass


class SlippageModel(Enum):
    """Slippage modeling approach."""
    NONE = "none"           # No slippage
    FIXED_PIPS = "fixed"    # Fixed pip slippage
    PERCENTAGE = "percentage"  # Percentage of price
    VOLATILITY_BASED = "volatility"  # Based on price volatility


class CommissionModel(Enum):
    """Commission calculation method."""
    NONE = "none"           # No commission
    PER_TRADE = "per_trade"  # Fixed per trade
    PER_LOT = "per_lot"     # Per lot traded
    PERCENTAGE = "percentage"  # Percentage of PnL


@dataclass
class SlippageConfig:
    """Configuration for slippage modeling."""
    model: SlippageModel = SlippageModel.FIXED_PIPS
    value: float = 0.5      # Pips (for FIXED_PIPS) or % (for PERCENTAGE)
    volatility_multiplier: float = 1.0  # Multiplier for volatility-based model


@dataclass
class CommissionConfig:
    """Configuration for commission modeling."""
    model: CommissionModel = CommissionModel.PER_TRADE
    value: float = 5.0      # $ per trade (PER_TRADE), $ per lot (PER_LOT), or % (PERCENTAGE)
    round_trip: bool = True  # If True, commission applies on entry + exit


class SlippageCalculator:
    """Calculate slippage costs for trades."""

    @staticmethod
    def calculate_entry_slippage(
        entry_price: float,
        direction: str,
        config: SlippageConfig,
        atr: float = None,  # Average True Range for volatility
    ) -> float:
        """
        Calculate slippage on entry.

        Args:
            entry_price: Entry price
            direction: "BUY" or "SELL"
            config: SlippageConfig object
            atr: Average True Range for volatility-based model

        Returns:
            Slippage in pips (positive value)
        """
        if config.model == SlippageModel.NONE:
            return 0.0

        if config.model == SlippageModel.FIXED_PIPS:
            return config.value

        if config.model == SlippageModel.PERCENTAGE:
            slippage_amount = entry_price * (config.value / 100) / 0.0001
            return slippage_amount

        if config.model == SlippageModel.VOLATILITY_BASED:
            if atr is None:
                atr = entry_price * 0.01  # Default to 1% if ATR not provided
            slippage_pips = (atr / 0.0001) * config.volatility_multiplier
            return slippage_pips

        return 0.0

    @staticmethod
    def apply_entry_slippage(
        entry_price: float,
        direction: str,
        slippage_pips: float,
    ) -> float:
        """
        Apply slippage to entry price.

        Args:
            entry_price: Original entry price
            direction: "BUY" or "SELL"
            slippage_pips: Slippage in pips

        Returns:
            Adjusted entry price (worse for trader)
        """
        slippage_amount = slippage_pips * 0.0001

        if direction == "BUY":
            # Slippage worsens BUY entry (price goes up)
            return entry_price + slippage_amount
        else:  # SELL
            # Slippage worsens SELL entry (price goes down)
            return entry_price - slippage_amount

    @staticmethod
    def apply_exit_slippage(
        exit_price: float,
        direction: str,
        slippage_pips: float,
    ) -> float:
        """
        Apply slippage to exit price.

        Args:
            exit_price: Original exit price
            direction: "BUY" or "SELL"
            slippage_pips: Slippage in pips

        Returns:
            Adjusted exit price (worse for trader)
        """
        slippage_amount = slippage_pips * 0.0001

        if direction == "BUY":
            # Slippage worsens BUY exit (price goes down)
            return exit_price - slippage_amount
        else:  # SELL
            # Slippage worsens SELL exit (price goes up)
            return exit_price + slippage_amount


class CommissionCalculator:
    """Calculate trading commissions."""

    @staticmethod
    def calculate_commission(
        entry_price: float,
        exit_price: float,
        direction: str,
        size: float,
        config: CommissionConfig,
        pnl: float = None,
    ) -> float:
        """
        Calculate total commission cost.

        Args:
            entry_price: Entry price
            exit_price: Exit price
            direction: "BUY" or "SELL"
            size: Position size in lots
            config: CommissionConfig object
            pnl: Trade PnL (for PERCENTAGE model)

        Returns:
            Commission in dollars (positive value, deducted from PnL)
        """
        if config.model == CommissionModel.NONE:
            return 0.0

        if config.model == CommissionModel.PER_TRADE:
            # Fixed commission per trade
            commission = config.value
            if config.round_trip:
                commission *= 2  # Entry + exit
            return commission

        if config.model == CommissionModel.PER_LOT:
            # Commission per lot
            commission = config.value * size
            if config.round_trip:
                commission *= 2
            return commission

        if config.model == CommissionModel.PERCENTAGE:
            # Percentage of PnL
            if pnl is None:
                # Estimate PnL
                pnl = abs(exit_price - entry_price) * size * 10.0  # EUR/USD pip value
            commission = pnl * (config.value / 100)
            if config.round_trip:
                commission *= 2
            return commission

        return 0.0

    @staticmethod
    def apply_commission_to_pnl(
        pnl: float,
        commission: float,
    ) -> float:
        """
        Apply commission to trade PnL.

        Args:
            pnl: Trade profit/loss in dollars
            commission: Commission in dollars

        Returns:
            Net PnL after commission
        """
        return pnl - commission


@dataclass
class RealismConfig:
    """Complete configuration for realistic backtesting."""
    slippage: SlippageConfig
    commission: CommissionConfig
    spread_pips: float = 1.0  # Bid-ask spread in pips


class RealisticBacktestSimulator:
    """Apply slippage and commission to backtest results."""

    def __init__(self, config: RealismConfig):
        self.config = config
        self.slippage_calc = SlippageCalculator()
        self.commission_calc = CommissionCalculator()

    def simulate_entry(
        self,
        entry_price: float,
        direction: str,
        atr: float = None,
    ) -> tuple[float, float]:
        """
        Simulate realistic entry with slippage.

        Args:
            entry_price: Intended entry price
            direction: "BUY" or "SELL"
            atr: Average True Range for volatility model

        Returns:
            Tuple of (adjusted_entry_price, slippage_cost_pips)
        """
        slippage_pips = self.slippage_calc.calculate_entry_slippage(
            entry_price, direction, self.config.slippage, atr
        )

        # Add spread
        total_slippage_pips = slippage_pips + (self.config.spread_pips / 2)

        adjusted_price = self.slippage_calc.apply_entry_slippage(
            entry_price, direction, total_slippage_pips
        )

        return adjusted_price, total_slippage_pips

    def simulate_exit(
        self,
        exit_price: float,
        direction: str,
        atr: float = None,
    ) -> tuple[float, float]:
        """
        Simulate realistic exit with slippage.

        Args:
            exit_price: Intended exit price
            direction: "BUY" or "SELL"
            atr: Average True Range for volatility model

        Returns:
            Tuple of (adjusted_exit_price, slippage_cost_pips)
        """
        slippage_pips = self.slippage_calc.calculate_entry_slippage(
            exit_price, direction, self.config.slippage, atr
        )

        # Add spread
        total_slippage_pips = slippage_pips + (self.config.spread_pips / 2)

        adjusted_price = self.slippage_calc.apply_exit_slippage(
            exit_price, direction, total_slippage_pips
        )

        return adjusted_price, total_slippage_pips

    def calculate_net_pnl(
        self,
        gross_pnl: float,
        entry_price: float,
        exit_price: float,
        direction: str,
        size: float,
    ) -> float:
        """
        Calculate net PnL after slippage and commission.

        Args:
            gross_pnl: Gross PnL before costs
            entry_price: Entry price
            exit_price: Exit price
            direction: "BUY" or "SELL"
            size: Position size in lots

        Returns:
            Net PnL after all costs
        """
        commission = self.commission_calc.calculate_commission(
            entry_price, exit_price, direction, size, self.config.commission, gross_pnl
        )

        return self.commission_calc.apply_commission_to_pnl(gross_pnl, commission)


# Preset configurations for different brokers/conditions

REALISTIC_FOREX_CONFIG = RealismConfig(
    slippage=SlippageConfig(
        model=SlippageModel.FIXED_PIPS,
        value=1.5,  # 1.5 pip slippage
    ),
    commission=CommissionConfig(
        model=CommissionModel.PER_TRADE,
        value=3.0,  # $3 per round-trip
    ),
    spread_pips=1.0,
)

TIGHT_CONDITIONS_CONFIG = RealismConfig(
    slippage=SlippageConfig(
        model=SlippageModel.FIXED_PIPS,
        value=0.5,
    ),
    commission=CommissionConfig(
        model=CommissionModel.PER_TRADE,
        value=1.0,
    ),
    spread_pips=0.5,
)

VOLATILE_CONDITIONS_CONFIG = RealismConfig(
    slippage=SlippageConfig(
        model=SlippageModel.VOLATILITY_BASED,
        value=1.0,
        volatility_multiplier=2.0,
    ),
    commission=CommissionConfig(
        model=CommissionModel.PER_TRADE,
        value=5.0,
    ),
    spread_pips=2.0,
)
