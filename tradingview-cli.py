#!/usr/bin/env python3
"""
TradingView CLI - Access TradingView data via command line
Provides quick chart reads and signal checks without needing CDP
"""

import json
import sys
from datetime import datetime
from pathlib import Path

class TradingViewCLI:
    def __init__(self):
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.log_file = self.data_dir / "signal-checks-log.json"

    def chart_read(self, pair, vwap=None, rsi=None, ema10=None, ema21=None, ema20=None, price=None):
        """
        Record a chart read for a pair
        Usage: python tradingview-cli.py chart-read EURUSD --vwap 1.0850 --rsi 55 --ema10 1.0845 --ema21 1.0840 --ema20 1.0835 --price 1.0860
        """
        data = {
            "pair": pair,
            "timestamp": datetime.now().isoformat(),
            "indicators": {
                "price": price,
                "vwap": vwap,
                "rsi": rsi,
                "ema10": ema10,
                "ema21": ema21,
                "ema20": ema20
            }
        }

        print(f"\n📊 CHART READ: {pair}")
        print(f"{'─' * 50}")
        print(f"Price:  {price}")
        print(f"VWAP:   {vwap}")
        print(f"RSI:    {rsi}")
        print(f"EMA10:  {ema10}")
        print(f"EMA21:  {ema21}")
        print(f"EMA20:  {ema20}")
        print(f"Time:   {datetime.now().strftime('%H:%M:%S ACST')}")

        return data

    def signal_check(self, pair, scenario, c1=False, c2=False, c3=False, c4=False, c5=False):
        """
        Run a 5-condition signal check
        """
        conditions = {
            "C1_VWAP_Bounce": c1,
            "C2_RSI_40_60": c2,
            "C3_EMA10_gt_EMA21": c3,
            "C4_Price_gt_EMA20": c4,
            "C5_Scenario_Confirmed": c5
        }

        met_count = sum(conditions.values())
        all_met = met_count == 5
        entry_ready = all_met and scenario in ["Scenario 1", "Scenario 2"]

        print(f"\n🎯 SIGNAL CHECK: {pair} ({scenario})")
        print(f"{'─' * 50}")
        for condition, status in conditions.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {condition}")

        print(f"\n📈 Result: {met_count}/5 conditions met")
        print(f"🚀 Entry Ready: {'YES ✅' if entry_ready else 'NO ❌'}")

        return {
            "pair": pair,
            "scenario": scenario,
            "conditions": conditions,
            "conditions_met": met_count,
            "entry_ready": entry_ready,
            "timestamp": datetime.now().isoformat()
        }

    def batch_check(self, data_file):
        """
        Run all pairs from a JSON data file
        Usage: python tradingview-cli.py batch-check path/to/signal-check-data.json
        """
        with open(data_file, 'r') as f:
            data = json.load(f)

        print(f"\n{'=' * 60}")
        print(f"15:00 SIGNAL CHECK SUMMARY")
        print(f"{'=' * 60}")

        entry_ready_count = 0

        for pair_data in data.get('pairs', []):
            pair = pair_data['pair']
            scenario = pair_data['scenario_status']['current_scenario']

            conditions = pair_data['conditions']
            c1 = conditions['c1_vwap_bounce']['met']
            c2 = conditions['c2_rsi_40_60']['met']
            c3 = conditions['c3_ema10_gt_ema21']['met']
            c4 = conditions['c4_price_gt_ema20']['met']
            c5 = conditions['c5_scenario_confirmed']['met']

            result = self.signal_check(pair, scenario, c1, c2, c3, c4, c5)

            if result['entry_ready']:
                entry_ready_count += 1

        print(f"\n{'=' * 60}")
        print(f"SUMMARY: {entry_ready_count}/4 pairs ready for entry")
        print(f"Entry window: 15:30–17:00 ACST")
        print(f"{'=' * 60}\n")

    def help(self):
        """Show help message"""
        help_text = """
TradingView CLI - Quick chart access without CDP

USAGE:
  python tradingview-cli.py [command] [options]

COMMANDS:
  chart-read PAIR         Record indicator values from chart
    --price PRICE         Current price
    --vwap VWAP          VWAP level
    --rsi RSI            RSI value
    --ema10 EMA10        EMA10 value
    --ema21 EMA21        EMA21 value
    --ema20 EMA20        EMA20 value

  signal-check PAIR       Run 5-condition signal check
    --scenario [1-4]      Current scenario
    --c1 [true/false]     VWAP bounce
    --c2 [true/false]     RSI 40-60
    --c3 [true/false]     EMA10 > EMA21
    --c4 [true/false]     Price > EMA20
    --c5 [true/false]     Scenario confirmed

  batch-check FILE        Run all pairs from JSON file
    FILE                  Path to signal-check data JSON

EXAMPLES:
  # Record chart data for EURUSD
  python tradingview-cli.py chart-read EURUSD --price 1.0850 --vwap 1.0845 --rsi 55 --ema10 1.0841 --ema21 1.0840 --ema20 1.0835

  # Check if all 5 conditions are met
  python tradingview-cli.py signal-check GOLD --scenario "Scenario 4" --c1 true --c2 true --c3 true --c4 true --c5 false

  # Batch process all pairs
  python tradingview-cli.py batch-check data/signal-check-15-00-template.json

FOR MORE INFO:
  See: C:\\Users\\mathe\\Documents\\tradingview-mcp\\README.md
"""
        print(help_text)

def main():
    cli = TradingViewCLI()

    if len(sys.argv) < 2:
        cli.help()
        return

    command = sys.argv[1].lower()

    if command == "help":
        cli.help()
    elif command == "chart-read":
        if len(sys.argv) < 3:
            print("Usage: python tradingview-cli.py chart-read PAIR [--price X] [--vwap X] [--rsi X] [--ema10 X] [--ema21 X] [--ema20 X]")
            return

        pair = sys.argv[2]
        kwargs = {}
        for i in range(3, len(sys.argv), 2):
            if i+1 < len(sys.argv):
                key = sys.argv[i].lstrip('--')
                value = sys.argv[i+1]
                try:
                    kwargs[key] = float(value)
                except ValueError:
                    kwargs[key] = value

        cli.chart_read(pair, **kwargs)

    elif command == "signal-check":
        if len(sys.argv) < 3:
            print("Usage: python tradingview-cli.py signal-check PAIR --scenario [Scenario X] [--c1 true/false] ...")
            return

        pair = sys.argv[2]
        scenario = None
        conditions = {'c1': False, 'c2': False, 'c3': False, 'c4': False, 'c5': False}

        for i in range(3, len(sys.argv), 2):
            if i+1 < len(sys.argv):
                key = sys.argv[i].lstrip('--')
                value = sys.argv[i+1].lower()

                if key == 'scenario':
                    scenario = value
                elif key.startswith('c') and key[1:].isdigit():
                    conditions[key] = value in ['true', '1', 'yes']

        cli.signal_check(pair, scenario, **conditions)

    elif command == "batch-check":
        if len(sys.argv) < 3:
            print("Usage: python tradingview-cli.py batch-check FILE")
            return
        cli.batch_check(sys.argv[2])

    else:
        print(f"Unknown command: {command}")
        cli.help()

if __name__ == "__main__":
    main()
