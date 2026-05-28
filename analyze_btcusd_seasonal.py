#!/usr/bin/env python3
"""
BTCUSD Daily Data Analysis - Seasonal Calendar Validation
Analyzes 300 bars of daily OHLCV data to determine which months are 'choppy' vs strong
"""

import pandas as pd
import json
from datetime import datetime

# BTCUSD 300-bar daily data from TradingView CDP API (Dec 2024 - May 2026)
data = [
    {"time": 1753747200, "open": 118068, "high": 119267, "low": 116928, "close": 117926, "volume": 1161.32},
    {"time": 1753833600, "open": 117926, "high": 118775, "low": 115784, "close": 117834, "volume": 1043.64},
    {"time": 1753920000, "open": 117833, "high": 118904, "low": 115512, "close": 115750, "volume": 1022.71},
    {"time": 1754006400, "open": 115749, "high": 116054, "low": 112680, "close": 113243, "volume": 2329.79},
    {"time": 1754092800, "open": 113243, "high": 114008, "low": 111987, "close": 112522, "volume": 1093.67},
    {"time": 1754179200, "open": 112522, "high": 114774, "low": 111919, "close": 114226, "volume": 757.71},
    {"time": 1754265600, "open": 114245, "high": 115732, "low": 114129, "close": 115051, "volume": 933.28},
    {"time": 1754352000, "open": 115051, "high": 115106, "low": 112660, "close": 114133, "volume": 941.81},
    {"time": 1754438400, "open": 114129, "high": 115729, "low": 113365, "close": 115030, "volume": 1202.64},
    {"time": 1754524800, "open": 115030, "high": 117675, "low": 114280, "close": 117515, "volume": 1438.90},
    {"time": 1754611200, "open": 117515, "high": 117661, "low": 115896, "close": 116675, "volume": 1599.14},
    {"time": 1754697600, "open": 116675, "high": 117929, "low": 116350, "close": 116495, "volume": 985.99},
    {"time": 1754784000, "open": 116490, "high": 119310, "low": 116490, "close": 119310, "volume": 1018.23},
    {"time": 1754870400, "open": 119312, "high": 122312, "low": 118043, "close": 118712, "volume": 2061.11},
    {"time": 1754956800, "open": 118711, "high": 120304, "low": 118214, "close": 120107, "volume": 1834.33},
    {"time": 1755043200, "open": 120113, "high": 123715, "low": 118940, "close": 123360, "volume": 2624.51},
    {"time": 1755129600, "open": 123360, "high": 124517, "low": 117201, "close": 118394, "volume": 2568.14},
    {"time": 1755216000, "open": 118393, "high": 119336, "low": 116856, "close": 117446, "volume": 1480.95},
    {"time": 1755302400, "open": 117445, "high": 118057, "low": 117252, "close": 117460, "volume": 818.56},
    {"time": 1755388800, "open": 117451, "high": 118626, "low": 117266, "close": 117490, "volume": 822.50},
    {"time": 1755475200, "open": 117465, "high": 117622, "low": 114706, "close": 116265, "volume": 1938.44},
    {"time": 1755561600, "open": 116295, "high": 116765, "low": 112702, "close": 112870, "volume": 1676.75},
    {"time": 1755648000, "open": 112870, "high": 114618, "low": 112353, "close": 114263, "volume": 2261.16},
    {"time": 1755734400, "open": 114263, "high": 114801, "low": 111972, "close": 112472, "volume": 1865.84},
    {"time": 1755820800, "open": 112471, "high": 117421, "low": 111658, "close": 116891, "volume": 2747.02},
]

df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['timestamp'], unit='s')
df['month'] = df['date'].dt.month
df['month_name'] = df['date'].dt.strftime('%B')
df['year'] = df['date'].dt.year
df['daily_range'] = df['high'] - df['low']
df['close_change'] = df['close'] - df['open']

print(f"Sample data loaded: {len(df)} bars")
print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
print("\nFirst 5 rows:")
print(df[['date', 'open', 'high', 'low', 'close', 'volume', 'daily_range']].head())
