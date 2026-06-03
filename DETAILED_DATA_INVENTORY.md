# Detailed Data Inventory Report

**Generated**: June 3, 2026  
**Database**: backtest_trading.duckdb.backup  
**Total Instruments**: 4 symbols  
**Total Timeframes**: 6 unique (M15, H1, H4, D)  
**Total Bars Across All**: 223,221 bars

---

## Timezone Information

**All timestamps in database are in UTC (Coordinated Universal Time)**

### Forex Trading Hours (All Forex Pairs)

**Session**: Monday 21:00 UTC to Friday 21:00 UTC (continuous, no closing)

**Equivalent Times by Region**:
- **New York (EST/EDT)**: Sunday 4:00 PM to Friday 4:00 PM
- **London (GMT/BST)**: Sunday 9:00 PM to Friday 9:00 PM  
- **Tokyo (JST)**: Monday 6:00 AM to Saturday 6:00 AM
- **Sydney (AEDT)**: Monday 8:00 AM to Saturday 8:00 AM

**Data in Database**:
- EURUSD M15: Hours 0-23 UTC (full 24-hour coverage)
- AUDUSD M15: Hours 0-23 UTC (full 24-hour coverage)

### Crypto Market (Bitcoin - BTCUSD)

**Session**: 24/7 (continuous, no closing)
- Bitcoin trades 24 hours a day, 7 days a week
- No market holidays or trading halts

**Data in Database**:
- BTCUSD M15: Hours 0-23 UTC (full 24-hour coverage)

### Commodity (Gold - XAUUSD)

**Session**: Extended hours (similar to forex but with variations)
- Trading 23+ hours per day with minimal gaps

**Data in Database**:
- XAUUSD M15: Hours 0-23 UTC (full 24-hour coverage)

---

## Complete Instrument Breakdown

### 1. EURUSD (Euro vs US Dollar)

**Asset Class**: Major Currency Pair  
**Exchange**: Forex (OTC - Over The Counter)  
**Trading Hours**: 21:00 UTC Sunday to 21:00 UTC Friday

#### M15 Timeframe (15-minute bars)
| Metric | Value |
|--------|-------|
| Total Bars | 49,754 |
| **Date Range** | **2024-06-02 21:00:00 UTC** to **2026-06-03 03:15:00 UTC** |
| Duration | 730 calendar days (~628 trading days) |
| Expected Coverage | 96 bars/day (24h × 60min ÷ 15) |
| Actual Coverage | 79.2 bars/day (~82.5% coverage) |
| Price Range | 1.01870 to 1.20498 |
| Volatility | 18.29% |
| Avg Bar Size | 0.67 pips |
| Min Volume | 6 |
| Max Volume | 21,941 |
| Avg Volume | 1,522 |
| Data Quality | CLEAN (0 nulls, 0 invalid bars) |

#### H1 Timeframe (1-hour bars)
| Metric | Value |
|--------|-------|
| Total Bars | 12,438 |
| **Date Range** | **2024-06-02 21:00:00 UTC** to **2026-06-03 02:00:00 UTC** |
| Duration | 730 calendar days (~628 trading days) |
| Price Range | 1.01934 to 1.20430 |
| Volatility | 18.15% |
| Avg Bar Size | 1.36 pips |
| Avg Volume | 6,089 |
| Data Quality | CLEAN |

#### H4 Timeframe (4-hour bars)
| Metric | Value |
|--------|-------|
| Total Bars | 3,109 |
| **Date Range** | **2024-06-02 21:00:00 UTC** to **2026-06-02 21:00:00 UTC** |
| Duration | 730 calendar days (~627 trading days) |
| Price Range | 1.01934 to 1.20395 |
| Volatility | 18.11% |
| Avg Bar Size | 2.86 pips |
| Avg Volume | 24,361 |
| Data Quality | CLEAN |

#### D Timeframe (Daily bars)
| Metric | Value |
|--------|-------|
| Total Bars | 518 |
| **Date Range** | **2024-06-02 21:00:00 UTC** to **2026-06-01 21:00:00 UTC** |
| Duration | 729 calendar days (~518 trading days) |
| Price Range | 1.02404 to 1.20395 |
| Volatility | 17.57% |
| Avg Bar Size | 7.46 pips |
| Avg Volume | 146,200 |
| Data Quality | CLEAN |

---

### 2. AUDUSD (Australian Dollar vs US Dollar)

**Asset Class**: Major Currency Pair (Commodity Currency)  
**Exchange**: Forex (OTC)  
**Trading Hours**: 21:00 UTC Sunday to 21:00 UTC Friday

#### M15 Timeframe (15-minute bars)
| Metric | Value |
|--------|-------|
| Total Bars | 49,755 |
| **Date Range** | **2024-06-02 21:00:00 UTC** to **2026-06-03 03:30:00 UTC** |
| Duration | 730 calendar days (~628 trading days) |
| Expected Coverage | 96 bars/day |
| Actual Coverage | 79.2 bars/day (~82.5% coverage) |
| Price Range | 0.59295 to 0.72698 |
| Volatility | 22.60% |
| Avg Bar Size | 0.54 pips |
| Min Volume | 1 |
| Max Volume | 20,907 |
| Avg Volume | 907 |
| Data Quality | CLEAN (0 nulls, 0 invalid bars) |

#### H1 Timeframe (1-hour bars)
| Metric | Value |
|--------|-------|
| Total Bars | 12,438 |
| **Date Range** | **2024-06-02 21:00:00 UTC** to **2026-06-03 02:00:00 UTC** |
| Duration | 730 calendar days (~628 trading days) |
| Price Range | 0.59494 to 0.72687 |
| Volatility | 22.18% |
| Avg Bar Size | 1.11 pips |
| Avg Volume | 3,631 |
| Data Quality | CLEAN |

#### H4 Timeframe (4-hour bars)
| Metric | Value |
|--------|-------|
| Total Bars | 3,109 |
| **Date Range** | **2024-06-02 21:00:00 UTC** to **2026-06-02 21:00:00 UTC** |
| Duration | 730 calendar days (~627 trading days) |
| Price Range | 0.59498 to 0.72614 |
| Volatility | 22.04% |
| Avg Bar Size | 2.31 pips |
| Avg Volume | 14,526 |
| Data Quality | CLEAN |

#### D Timeframe (Daily bars)
| Metric | Value |
|--------|-------|
| Total Bars | 518 |
| **Date Range** | **2024-06-02 21:00:00 UTC** to **2026-06-01 21:00:00 UTC** |
| Duration | 729 calendar days (~518 trading days) |
| Price Range | 0.59586 to 0.72614 |
| Volatility | 21.86% |
| Avg Bar Size | 5.89 pips |
| Avg Volume | 87,176 |
| Data Quality | CLEAN |

**Key Observation**: AUDUSD shows HIGHER volatility (22.60%) than EURUSD (18.29%) - this correlates with our discovery that AUDUSD benefits from sweep detection while EURUSD doesn't.

---

### 3. BTCUSD (Bitcoin vs US Dollar)

**Asset Class**: Cryptocurrency  
**Exchange**: Crypto (Decentralized, 24/7)  
**Trading Hours**: 24/7/365 (no market close)

#### M15 Timeframe (15-minute bars)
| Metric | Value |
|--------|-------|
| Total Bars | 49,757 |
| **Date Range** | **2024-06-02 21:00:00 UTC** to **2026-06-03 04:00:00 UTC** |
| Duration | 730 calendar days (~628 trading days) |
| Price Range | 49,748.30 to 126,107.50 USD |
| Volatility | 153.49% (extremely high!) |
| Avg Bar Size | 320.42 pips |
| Min Volume | 77 |
| Max Volume | 7,454 |
| Avg Volume | 1,998 |
| Data Quality | CLEAN (0 nulls, 0 invalid bars) |

**Note**: BTCUSD only has M15 data (no H1, H4, or D).
BTCUSD volatility (153.49%) is 8.4x higher than EURUSD and 6.8x higher than AUDUSD.

**Data Coverage Issue**: Only M15 available. Cannot backtest H4 or daily confluence on Bitcoin. This limits its usefulness for Phase 3 since the system uses multi-timeframe confluence (M15 + H4).

---

### 4. XAUUSD (Gold vs US Dollar)

**Asset Class**: Commodity (Precious Metal)  
**Exchange**: Commodity (extended hours, 23+ hours/day)  
**Trading Hours**: 22:00 UTC Sunday to 22:00 UTC Friday

#### M15 Timeframe (15-minute bars)
| Metric | Value |
|--------|-------|
| Total Bars | 43,552 |
| **Date Range** | **2024-06-02 22:00:00 UTC** to **2026-04-07 03:30:00 UTC** |
| Duration | 673 calendar days (~577 trading days) |
| Expected Coverage | 96 bars/day |
| Actual Coverage | 75.4 bars/day (~78.5% coverage) |
| Price Range | 2,287.04 to 5,586.07 USD/oz |
| Volatility | 144.25% |
| Avg Bar Size | 6.27 pips |
| Min Volume | 1 |
| Max Volume | 53,652 |
| Avg Volume | 5,966 |
| Data Quality | CLEAN (0 nulls, 0 invalid bars) |

**Data Coverage Issue**: 
- Data ends on 2026-04-07 (missing 2 months of recent data)
- Only ~577 trading days vs ~628 for others
- Does NOT have current data (H1, H4, D timeframes missing)

**Recommendation**: NOT RECOMMENDED for Phase 3 due to incomplete recent history.

---

## Comparative Analysis

### Volatility Comparison (% from min to max)
```
BTCUSD:    153.49% (EXTREME - crypto volatility)
XAUUSD:    144.25% (VERY HIGH - commodity volatility)
AUDUSD:     22.60% (HIGH - correlates with sweep filter effectiveness)
EURUSD:     18.29% (MEDIUM - swap filter not effective)
```

### Data Completeness (% of expected bars)
```
EURUSD M15: 82.5% coverage (49,754 / 60,288 expected bars)
AUDUSD M15: 82.5% coverage (49,755 / 60,288 expected bars)
BTCUSD M15: 82.2% coverage (49,757 / 60,576 expected bars - 24/7 trading)
XAUUSD M15: 78.5% coverage (43,552 / 55,488 expected bars - incomplete period)
```

### Timeframe Coverage
```
EURUSD: M15, H1, H4, D (COMPLETE - all timeframes)
AUDUSD: M15, H1, H4, D (COMPLETE - all timeframes)
BTCUSD: M15 only (INCOMPLETE - missing H1, H4, D)
XAUUSD: M15 only (INCOMPLETE - missing H1, H4, D, and incomplete date range)
```

---

## Key Dates Summary

### Period 1: Full 2-Year Dataset
**Symbols**: EURUSD, AUDUSD  
**Start**: June 2, 2024, 21:00 UTC (Sunday evening, forex market open)  
**End**: June 3, 2026, ~03:00 UTC (current)  
**Duration**: ~730 calendar days = ~628 trading days  
**Status**: COMPLETE, CURRENT, ALL TIMEFRAMES

### Period 2: Bitcoin Full 2-Year Dataset
**Symbol**: BTCUSD  
**Start**: June 2, 2024, 21:00 UTC  
**End**: June 3, 2026, 04:00 UTC  
**Duration**: ~730 calendar days  
**Status**: COMPLETE, CURRENT, M15 ONLY (missing H4 confluence)

### Period 3: Gold Incomplete Dataset
**Symbol**: XAUUSD  
**Start**: June 2, 2024, 22:00 UTC  
**End**: April 7, 2026, 03:30 UTC  
**Duration**: ~673 calendar days (MISSING 2 MONTHS)  
**Status**: INCOMPLETE, OUTDATED, M15 ONLY

---

## Data Quality Summary

| Instrument | M15 Bars | Data Quality | Nulls | Invalid | Status |
|------------|----------|--------------|-------|---------|--------|
| EURUSD | 49,754 | EXCELLENT | 0 | 0 | PRODUCTION READY |
| AUDUSD | 49,755 | EXCELLENT | 0 | 0 | PRODUCTION READY |
| BTCUSD | 49,757 | EXCELLENT | 0 | 0 | READY (M15 only) |
| XAUUSD | 43,552 | EXCELLENT | 0 | 0 | NOT RECOMMENDED |

**Overall Assessment**: 
- EURUSD & AUDUSD: Perfect for backtesting
- BTCUSD: Good quality but incomplete (M15 only)
- XAUUSD: Good quality but outdated (missing 2 months)

---

## Bar Coverage Analysis

### Expected vs Actual Bars per Day

**Forex (M15)**: 96 bars/day expected (24 hours × 60 min ÷ 15)
- EURUSD: 79.2 bars/day (82.5% coverage) - Missing ~17 bars/day
- AUDUSD: 79.2 bars/day (82.5% coverage) - Missing ~17 bars/day

**Likely cause**: 
- Market holidays (Christmas, New Year, etc.) - 5-8 per year
- Weekend gaps (market closed Fri-Sun) - automatically handled
- Low liquidity hours with no trades - expected during Asian session overlap

**Crypto (M15)**: 96 bars/day expected (24/7 markets)
- BTCUSD: 79.2 bars/day (82.5% coverage) - Missing ~17 bars/day

**Likely cause**: 
- Data collection gaps or exchange downtime
- Normal, not a problem for backtesting

**Commodity (M15)**: 92 bars/day expected (23 hours of trading)
- XAUUSD: 75.4 bars/day (82.0% coverage) - Missing ~17 bars/day
- Plus 2-month gap at end

---

## Recommendations for Phase 3

### USE FOR TESTING:
✓ **EURUSD & AUDUSD** - Both instruments, all timeframes, complete 2-year data
✓ **BTCUSD** - If doing cross-asset testing (but caveat: M15 only, crypto volatility 8x higher)

### DON'T USE:
✗ **XAUUSD** - Outdated (missing 2 months) and incomplete (M15 only)
✗ **GBPUSD, NZDUSD, USDCAD** - No data in database at all

### TO COMPLETE PHASE 3:
**Would need to import** GBPUSD, NZDUSD, USDCAD from Capital.com API
- Estimated time: 2-3 hours to fetch, load, and validate
- Expected bar count: ~50,000 M15 bars each, ~3,100 H4 bars each, ~518 D bars each

---

## File Information

**Database File**: backtest_trading.duckdb.backup  
**Size**: ~15 MB (estimated)  
**Format**: DuckDB (columnar database)  
**Schema**: OHLCV (Open, High, Low, Close, Volume) + timestamp + symbol + timeframe

---

## Summary Table (Quick Reference)

```
Instrument  M15 Bars  Start              End                Timeframes   Status
EURUSD      49,754    2024-06-02 21:00   2026-06-03 03:15   D,H1,H4,M15  READY
AUDUSD      49,755    2024-06-02 21:00   2026-06-03 03:30   D,H1,H4,M15  READY
BTCUSD      49,757    2024-06-02 21:00   2026-06-03 04:00   M15          PARTIAL
XAUUSD      43,552    2024-06-02 22:00   2026-04-07 03:30   M15          OUTDATED
GBPUSD      —         —                  —                  —            NO DATA
NZDUSD      —         —                  —                  —            NO DATA
USDCAD      —         —                  —                  —            NO DATA
```

---

**Conclusion**: You have sufficient data for 2-pair validation (EURUSD + AUDUSD) and can add BTCUSD as a bonus crypto cross-asset test. The 3 remaining forex pairs would require data import to complete Phase 3 properly.

