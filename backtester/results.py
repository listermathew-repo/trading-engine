"""Results reporting and CSV export for backtesting."""

import csv
from pathlib import Path
from datetime import datetime
from typing import Optional
from .strategy import BacktestTrade, BacktestResults, TradeStatus


class ResultsReporter:
    """Generate reports and CSV exports for backtest results."""

    @staticmethod
    def export_csv(
        results: BacktestResults,
        output_path: Path,
    ) -> None:
        """
        Export trades to CSV in the specified format.

        Format:
        Date | Time | Indices | Session | Direction | Entry Price | SL | TP |
        Status | R | Trade $ | Return | Exit Price | Lookback | Notes

        Args:
            results: BacktestResults object
            output_path: Path to write CSV file
        """
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow([
                'Date',
                'Time',
                'Entry Candle Index',
                'Session',
                'Direction',
                'Entry Price',
                'Stop Loss',
                'Take Profit',
                'Status',
                'R Gained',
                'Trade PnL',
                'Return %',
                'Exit Price',
                'Exit Time',
                'Swing Lookback',
                'FVG Direction',
                'FVG Zone Low',
                'FVG Zone High',
                'Liquidity',
            ])

            # Write trades
            for trade in results.trades:
                return_pct = (
                    (trade.r_gained * 100) if trade.r_gained != 0 else 0
                )

                writer.writerow([
                    trade.entry_time.strftime('%Y-%m-%d'),
                    trade.entry_time.strftime('%H:%M'),
                    trade.entry_index,
                    trade.session,
                    trade.direction,
                    f"{trade.entry_price:.4f}",
                    f"{trade.stop_loss:.4f}",
                    f"{trade.take_profit:.4f}",
                    trade.status.value,
                    f"{trade.r_gained:+.2f}",
                    f"${trade.pnl:+.2f}",
                    f"{return_pct:+.1f}%",
                    f"{trade.exit_price:.4f}" if trade.exit_price else "OPEN",
                    trade.exit_time.strftime('%Y-%m-%d %H:%M') if trade.exit_time else "OPEN",
                    f"{trade.swing_lookback}C",
                    trade.fvg_zone.direction.upper(),
                    f"{trade.fvg_zone.bottom:.4f}",
                    f"{trade.fvg_zone.top:.4f}",
                    trade.liquidity_level,
                ])

    @staticmethod
    def print_summary(results: BacktestResults) -> None:
        """Print backtest summary to console."""
        print("\n" + "=" * 80)
        print("BACKTEST SUMMARY".center(80))
        print("=" * 80)

        print(f"\nTotal Trades: {results.total_trades}")
        print(f"Winning Trades: {results.winning_trades}")
        print(f"Losing Trades: {results.losing_trades}")
        print(f"Non-Progressive Trades: {results.non_progressive_trades}")

        if results.total_trades > 0:
            print(f"\nWin Rate: {results.win_rate:.1%}")
            print(f"Total R: {results.total_r:+.2f}")
            print(f"Avg R per Trade: {results.avg_r_per_trade:+.2f}")
            print(f"Total PnL: ${results.total_pnl:+.2f}")
            print(f"Avg PnL per Trade: ${results.avg_pnl_per_trade:+.2f}")

        print("\n" + "=" * 80)

    @staticmethod
    def analyze_by_lookback(results: BacktestResults) -> dict:
        """
        Analyze results grouped by swing lookback period.

        Args:
            results: BacktestResults object

        Returns:
            Dictionary with analysis by lookback period
        """
        lookback_analysis = {}

        for trade in results.trades:
            lookback = trade.swing_lookback

            if lookback not in lookback_analysis:
                lookback_analysis[lookback] = {
                    'total': 0,
                    'wins': 0,
                    'losses': 0,
                    'non_progressive': 0,
                    'total_r': 0.0,
                    'total_pnl': 0.0,
                    'trades': [],
                }

            lookback_analysis[lookback]['total'] += 1
            lookback_analysis[lookback]['trades'].append(trade)

            if trade.status == TradeStatus.WIN:
                lookback_analysis[lookback]['wins'] += 1
            elif trade.status == TradeStatus.LOSS:
                lookback_analysis[lookback]['losses'] += 1
            elif trade.status == TradeStatus.NON_PROGRESSIVE:
                lookback_analysis[lookback]['non_progressive'] += 1

            lookback_analysis[lookback]['total_r'] += trade.r_gained
            lookback_analysis[lookback]['total_pnl'] += trade.pnl

        return lookback_analysis

    @staticmethod
    def print_lookback_analysis(lookback_analysis: dict) -> None:
        """Print analysis grouped by swing lookback period."""
        print("\n" + "=" * 80)
        print("ANALYSIS BY SWING LOOKBACK PERIOD".center(80))
        print("=" * 80)

        for lookback in sorted(lookback_analysis.keys()):
            stats = lookback_analysis[lookback]
            total = stats['total']

            if total == 0:
                continue

            win_rate = stats['wins'] / total if total > 0 else 0
            avg_r = stats['total_r'] / total if total > 0 else 0
            avg_pnl = stats['total_pnl'] / total if total > 0 else 0

            print(f"\n{lookback}-Candle Swing Low:")
            print(f"  Trades: {total} | Wins: {stats['wins']} | Losses: {stats['losses']} | NP: {stats['non_progressive']}")
            print(f"  Win Rate: {win_rate:.1%}")
            print(f"  Total R: {stats['total_r']:+.2f} | Avg R: {avg_r:+.2f}")
            print(f"  Total PnL: ${stats['total_pnl']:+.2f} | Avg PnL: ${avg_pnl:+.2f}")

        print("\n" + "=" * 80)

    @staticmethod
    def analyze_by_session(results: BacktestResults) -> dict:
        """
        Analyze results grouped by trading session.

        Args:
            results: BacktestResults object

        Returns:
            Dictionary with analysis by session
        """
        session_analysis = {}

        for trade in results.trades:
            session = trade.session

            if session not in session_analysis:
                session_analysis[session] = {
                    'total': 0,
                    'wins': 0,
                    'losses': 0,
                    'non_progressive': 0,
                    'total_r': 0.0,
                    'total_pnl': 0.0,
                }

            session_analysis[session]['total'] += 1

            if trade.status == TradeStatus.WIN:
                session_analysis[session]['wins'] += 1
            elif trade.status == TradeStatus.LOSS:
                session_analysis[session]['losses'] += 1
            elif trade.status == TradeStatus.NON_PROGRESSIVE:
                session_analysis[session]['non_progressive'] += 1

            session_analysis[session]['total_r'] += trade.r_gained
            session_analysis[session]['total_pnl'] += trade.pnl

        return session_analysis

    @staticmethod
    def print_session_analysis(session_analysis: dict) -> None:
        """Print analysis grouped by trading session."""
        print("\n" + "=" * 80)
        print("ANALYSIS BY TRADING SESSION".center(80))
        print("=" * 80)

        for session in sorted(session_analysis.keys()):
            stats = session_analysis[session]
            total = stats['total']

            if total == 0:
                continue

            win_rate = stats['wins'] / total if total > 0 else 0
            avg_r = stats['total_r'] / total if total > 0 else 0
            avg_pnl = stats['total_pnl'] / total if total > 0 else 0

            print(f"\n{session.upper()}:")
            print(f"  Trades: {total} | Wins: {stats['wins']} | Losses: {stats['losses']} | NP: {stats['non_progressive']}")
            print(f"  Win Rate: {win_rate:.1%}")
            print(f"  Total R: {stats['total_r']:+.2f} | Avg R: {avg_r:+.2f}")
            print(f"  Total PnL: ${stats['total_pnl']:+.2f} | Avg PnL: ${avg_pnl:+.2f}")

        print("\n" + "=" * 80)

    @staticmethod
    def print_individual_trades(
        results: BacktestResults,
        limit: Optional[int] = None,
    ) -> None:
        """
        Print individual trade details.

        Args:
            results: BacktestResults object
            limit: Maximum number of trades to print (None = all)
        """
        print("\n" + "=" * 120)
        print("INDIVIDUAL TRADES".center(120))
        print("=" * 120)

        trades_to_print = results.trades[:limit] if limit else results.trades

        for i, trade in enumerate(trades_to_print, 1):
            print(f"\nTrade #{i}:")
            print(f"  Entry: {trade.entry_time.strftime('%Y-%m-%d %H:%M')} @ {trade.entry_price:.4f} ({trade.direction})")
            print(f"  Stop Loss: {trade.stop_loss:.4f} | Take Profit: {trade.take_profit:.4f}")
            print(f"  FVG Zone: {trade.fvg_zone.direction.upper()} | {trade.fvg_zone.bottom:.4f} - {trade.fvg_zone.top:.4f}")
            print(f"  Swing Lookback: {trade.swing_lookback} candles | Session: {trade.session}")

            if trade.exit_time:
                print(f"  Exit: {trade.exit_time.strftime('%Y-%m-%d %H:%M')} @ {trade.exit_price:.4f}")
                print(f"  Result: {trade.status.value.upper()} | R: {trade.r_gained:+.2f} | PnL: ${trade.pnl:+.2f}")
            else:
                print(f"  Result: OPEN")

        print("\n" + "=" * 120)
