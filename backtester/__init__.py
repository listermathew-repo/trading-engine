"""Fair Value Gap (FVG) backtesting module."""

from .capital_data import CapitalDataClient, OHLCV
from .fvg_detector import FVG, FVGDetector
from .swing_detector import SwingDetector
from .strategy import FVGStrategy, BacktestTrade, BacktestResults, TradeStatus
from .results import ResultsReporter

__all__ = [
    "CapitalDataClient",
    "OHLCV",
    "FVG",
    "FVGDetector",
    "SwingDetector",
    "FVGStrategy",
    "BacktestTrade",
    "BacktestResults",
    "TradeStatus",
    "ResultsReporter",
]
