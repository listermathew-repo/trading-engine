# Prop Firm Shadow Challenge Tracker
# Mirrors Prop Firm $100k account rules against your real Capital.com trades
# Start date: April 21, 2026
# Reset this every time you formally attempt a real Prop Firm challenge

## CHALLENGE PARAMETERS (Prop Firm $100k Swing Account)
- Starting balance:    $100,000 (simulated)
- Profit target:       $10,000 (10%) — reach this to pass Phase 1
- Daily loss limit:    $5,000 (5%) — breach this = FAIL day (note it)
- Max drawdown:        $10,000 (10% of starting balance) — breach this = FAIL challenge
- Min trading days:    4 (trivial)
- Account floor:       $90,000 (if equity hits this = challenge over)

## SCALING FACTOR
Your real account: $80,000 | Prop Firm challenge: $100,000
Scale factor: 1.25x (multiply your real $ result by 1.25 for shadow tracking)
Example: Real +$400 profit = Shadow +$500 (400 × 1.25)

---

## RUNNING TOTALS
| Metric | Value |
|--------|-------|
| Shadow starting balance | $100,000 |
| Shadow current balance | $100,000 |
| Shadow P&L to date | $0 |
| Shadow P&L vs target | $0 / $10,000 (0%) |
| Max adverse equity (worst point) | $100,000 |
| Max drawdown reached | $0 (limit: $10,000) |
| Days traded | 0 (minimum: 4) |
| Challenge status | ⏳ IN PROGRESS |

---

## DAILY LOG

| Date | Day | Real P&L | Shadow P&L (×1.25) | Shadow Balance | Daily DD Used | Status |
|------|-----|----------|-------------------|----------------|--------------|--------|
| Apr 21, 2026 | Tue | — | — | $100,000 | — | First day |

*Add a row after every trading session.*

---

## HOW TO UPDATE THIS FILE AFTER EACH SESSION

1. Open post-session-log.md and note the real P&L
2. Multiply real P&L by 1.25 = shadow P&L
3. Update shadow balance (previous balance ± shadow P&L)
4. Update max adverse equity if today's low was worse than any previous day
5. Calculate max drawdown = $100,000 - lowest shadow balance ever reached
6. Update challenge status:
   - ✅ PASSING — shadow balance above $100,000 and drawdown under $10,000
   - ⚠️ CAUTION — drawdown between $5,000–$8,000 (reduce to T1 only)
   - ❌ FAILED — shadow balance hit $90,000 or daily loss exceeded $5,000

---

## PASS CRITERIA CHECKLIST (review after 30 trading days)
[ ] Shadow P&L reached +$10,000 (10% target)
[ ] No single day lost more than $5,000 (5% daily limit)
[ ] Max drawdown never exceeded $10,000 (10% of $100k)
[ ] Traded at least 4 different days
[ ] Psychology score was 3+ on all entry days
[ ] Entry checklist completed 100% of entry days

If all 6 boxes checked → GREEN LIGHT to attempt real Prop Firm $100k Swing challenge.

---

## REAL Prop Firm $100K CHALLENGE COST REFERENCE
| Account size | Cost (EUR) | Profit target | Daily DD | Max DD |
|-------------|-----------|--------------|---------|--------|
| $25,000 | €155 | $2,500 | $1,250 | $2,500 |
| $50,000 | €250 | $5,000 | $2,500 | $5,000 |
| **$100,000** | **€540** | **$10,000** | **$5,000** | **$10,000** |
| $200,000 | €1,080 | $20,000 | $10,000 | $20,000 |

Fee is REFUNDED with your first payout. Net cost = $0 if you pass and get paid.

---

## DAY 1 (Prop Firm) vs DAY 2 (FUTURES) — DECISION FRAMEWORK

### Day 1: Prop Firm Swing $100k (~€540 one-time)
- Exact instruments: XAUUSD spot, AUDUSD, EURUSD — zero adaptation
- Swing account: no overnight restrictions, no news restrictions
- Profit split: 80% (you) → scales to 90%
- Apply when: 90-day shadow challenge shows consistent passing

### Day 2: FundedNext Futures Rapid $50k (~$150 one-time)
- Instruments: MGC (micro gold futures), 6A (AUD/USD futures), 6E (EUR/USD futures)
- No daily drawdown limit — most forgiving for London-open momentum style
- Apply when: Prop Firm attempt fails, or running parallel to learn futures execution

---

## NOTES
- Update this file after EVERY session — takes 2 minutes
- Review weekly in the Sunday planning session
- If the shadow tracker shows 2+ consecutive months of passing → schedule the real Prop Firm challenge
