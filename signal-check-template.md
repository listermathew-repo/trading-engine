# 15:00 Signal Check — Daily Template
# Trigger phrase: "15:00 check"
# Claude reads TradingView via MCP + parses ForexFactory calendar you pasted at 08:30
# Output is generated within 2 minutes. ntfy alert fires at end of check.

══════════════════════════════════════════════
📊 15:00 SIGNAL CHECK — [Day] [Date] [Year]
══════════════════════════════════════════════

⚠️  NEWS ASSESSMENT (ACST)
────────────────────────────────────────────
[List released events — no impact]
[🔴 RED events within ±30min of 15:30 — HARD BLOCK]
[🟡 YELLOW events — caution, reduced size]
[✅ Session clear / 🔴 Blocked pairs listed]

ENTRY WINDOW STATUS: ✅ CLEAR / ⚠️ CAUTION / 🔴 BLOCKED
══════════════════════════════════════════════

GOLD — Scenario [1/3/4] [✅ ACTIVE / 🚫 SKIP]  |  Bias: [LONG / SKIP]
──────────────────────────────────────────────
Price:      [X]    |  BASE: [X]  |  [+X pts above / ❌ BELOW BASE]
EMA10:      [X]    |  EMA20: [X]  |  EMA21: [X]

Condition 1 — Price bouncing off VWAP:   [✅ / ❌]
  VWAP: [X]  |  Price: [X] — [above/below/at] VWAP

Condition 2 — RSI 40–60:                 [✅ / ❌]
  RSI: [value] — [in zone / overbought / oversold]

Condition 3 — EMA10 > EMA21:             [✅ / ❌]
  [X] [> or <] [X]

Condition 4 — Price > EMA20:             [✅ / ❌]
  [X] [> or <] [X]

Condition 5 — Scenario 1 confirmed:      [✅ / ❌]
  Morning video: [Scenario 1 ACTIVE / Scenario 3 / Scenario 4 — SKIP]

Gate 6 — Spread within limit:            [✅ / ❌ — CHECK AT 15:28]
  Gold max 0.50 | AUDUSD/EURUSD max 0.8 pips
  Live spread at 15:28: [X] — [CLEAR / TOO WIDE — wait or skip]

SETUP GRADE:    [A+ / A / B / NO SETUP]
CONDITIONS MET: [X of 5]
ENTRY ZONE:     [price range near VWAP]
SL:             [BASE level or below EMA20, whichever lower]
TARGET:         [Tier target — e.g. T2: 1.5R = $XXX profit]
TIER:           [T1 / T2 / T3 — based on grade]
RISK:           $[200 / 400 / 600]
──────────────────────────────────────────────
AUDUSD — Scenario [1/3/4] [✅ / 🚫]  |  Bias: [LONG / SKIP]
Price: [X]  |  Key level: [X]
[Brief status — one line]
──────────────────────────────────────────────
EURUSD — Scenario [1/3/4] [✅ / 🚫]  |  Bias: [LONG / SKIP]
Price: [X]  |  Key level: [X]
[Brief status — one line]
══════════════════════════════════════════════
DECISION:
  GOLD    → [🟢 ENTER at [X] / 👀 WATCH — [reason] / 🔴 STAND DOWN]
  AUDUSD  → [🟢 ENTER / 👀 WATCH / 🔴 STAND DOWN]
  EURUSD  → [🟢 ENTER / 👀 WATCH / 🔴 STAND DOWN]

VERDICT: [TRADE [PAIR] / WATCH AND WAIT / NO SETUP — STAND DOWN]
ntfy:    [signal -Pair [X] / nosetup] — FIRED ✅
══════════════════════════════════════════════

---

## Setup Grade Reference

| Grade | Conditions | Tier | Risk |
|-------|-----------|------|------|
| A+    | All 5 met + spread clear + multi-pair confluence | T3–T4 | $600–800 |
| A     | All 5 met + spread clear | T2–T3 | $400–600 |
| B     | 4 of 5 met + spread clear (weak technical) | T1–T2 | $200–400 |
| NO SETUP | Scenario not 1, spread too wide, or fewer than 4 conditions | Skip | — |

## Timeframe Stack Used

| Timeframe | Purpose |
|-----------|---------|
| 4H | Scenario confirmation, EMA alignment, BASE level |
| 1H | VWAP structure, intermediate momentum |
| 15M | Entry timing at London open (15:30 ACST) |

## Daily Trigger

User types: "15:00 check"
Claude responds with this template filled in from live TradingView data.
ntfy alert fires at end: "signal" or "nosetup"

## Breakeven Reminder (built into trade management)

- T1 ($200 risk): Move SL to BE at $100 profit (0.5R)
- T2 ($400 risk): Move SL to BE at $200 profit (0.5R)
- T3 ($600 risk): Move SL to BE at $240 profit (0.4R) — TIGHTER
- T4 ($800 risk): Move SL to BE at $320 profit (0.4R) — TIGHTER
