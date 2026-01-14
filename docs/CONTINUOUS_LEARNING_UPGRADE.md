# Quantix AI Core v3.2 - Continuous Learning Upgrade

## 🚀 Major Upgrade: From Static to Learning AI

This document explains the transformation from v3.1 (static pattern matching) to v3.2 (continuous learning system).

---

## 📊 Architecture Overview

### The Continuous Learning Loop

```
Market Data Stream (OANDA)
        ↓
Candle Quality Gate (Forex-grade validator)
        ↓
Validated Market Memory (market_candles_clean)
        ↓
Signal Generation (Pattern matching)
        ↓
Outcome Feedback (TP / SL / Expired)
        ↓
Confidence Adjustment (Learning rules)
        ↓
Learning Memory Update (Pattern intelligence)
        ↓
[Loop back to Signal Generation with updated confidence]
```

### Key Principle

**Quantix does NOT learn from all data.**  
**It ONLY learns from data with proven outcomes.**

---

## 🗄️ Three-Layer Memory Architecture

### Layer 1: `market_candles_clean`

**Purpose:** Store only validated, tradable candles.

**Quality Gate Rules:**
- ✅ Timestamp must be UTC-aligned
- ✅ Spread < 2.5x average
- ✅ No abnormal spikes (range < 3x average)
- ✅ Wick ratio < 75%
- ✅ Volume > minimum threshold
- ✅ Must be during London/NY session

**If ANY check fails → Candle is DISCARDED (not stored, not learned from)**

### Layer 2: `signal_outcomes`

**Purpose:** The learning source. Quantix learns from RESULTS, not candles.

**What's stored:**
- Entry context (price, time, session, volatility)
- Exit outcome (TP, SL, EXPIRED)
- Performance (pips, duration)
- Pattern hash (links to learning memory)

**This is the TRUTH that drives learning.**

### Layer 3: `learning_memory`

**Purpose:** The brain. Pattern intelligence.

**What's stored:**
- Pattern performance stats (win rate, avg pips)
- Confidence weight (learning adjustment)
- Context (session, volatility)
- Last adjustment reason (explainability)

**This is what makes Quantix smarter over time.**

---

## 🧠 Learning Engine: Explainable AI

### NOT a Black Box

Quantix uses **rule-based learning**, not neural networks.

### Learning Rules (Auditable)

```python
Rule 1: Poor Performance
IF win_rate < 45% AND sample_size >= 30
THEN reduce confidence_weight by 0.3
REASON: "Pattern shows poor win rate with sufficient sample size"

Rule 2: Strong Overlap Performance
IF win_rate > 60% AND sample_size >= 20 AND session == 'overlap'
THEN boost confidence_weight by 0.2
REASON: "Strong performance during London-NY overlap"

Rule 3: Extreme Volatility
IF volatility_state == 'extreme'
THEN reduce confidence_weight by 0.2
REASON: "Extreme volatility reduces pattern reliability"

Rule 4: Consistent Winner
IF win_rate > 65% AND sample_size >= 50
THEN boost confidence_weight by 0.3
REASON: "Proven consistent performance over large sample"

Rule 5: New Pattern
IF sample_size < 10
THEN reduce confidence_weight by 0.1
REASON: "Insufficient data - conservative approach"
```

### Why This Matters

- ✅ **Explainable:** Every adjustment has a clear reason
- ✅ **Auditable:** You can trace why confidence changed
- ✅ **No Overfitting:** Rules are simple and robust
- ✅ **Transparent:** No hidden layers or black-box magic

---

## 🌍 Session Intelligence (Internal)

### No External API Needed

Quantix has built-in session detection:

```python
Sessions:
- London:   07:00-16:00 UTC (Score: 0.85)
- New York: 13:00-22:00 UTC (Score: 0.90)
- Overlap:  13:00-16:00 UTC (Score: 1.00) ⭐
- Asia:     00:00-07:00 UTC (Score: 0.50)
- Off-hours: (Score: 0.30)
```

### Purpose

1. **Score session favorability**
2. **Explain "Why this time is favorable"**
3. **Disable learning during off-hours**

### Example Explanation

> "London-New York overlap detected. This 3-hour window (13:00-16:00 UTC) offers peak market liquidity and institutional participation. Price action is most reliable during this period, with tighter spreads and higher probability of trend continuation."

---

## 📅 Learning Frequency

| Event | Frequency |
|-------|-----------|
| Candle Ingest | Every M15 |
| Signal Evaluation | When TP/SL/Expired |
| Learning Update | End of session |
| Memory Decay | Weekly |

**NOT real-time tick-by-tick learning.**

---

## 🛡️ Auto-Safety Rules

Quantix knows when to STOP learning:

```python
IF volatility_extreme OR high_impact_news:
    learning_disabled = True
```

**During these periods:**
- Data is observed but NOT learned from
- Confidence is penalized
- Signals may be suppressed

---

## 📈 Data Source: OANDA (Institutional-Grade)

### Why OANDA?

- ✅ Institutional-grade data
- ✅ UTC timestamps (no timezone issues)
- ✅ No repaint
- ✅ Tick-volume proxy
- ✅ Real spreads

### Supported Pairs

- EUR/USD
- GBP/USD
- USD/JPY

**DO NOT replace with TradingView scraping.**

---

## 🔄 How Learning Works (Step-by-Step)

### Step 1: Signal Generated

```
Pattern detected → Generate signal
Base confidence: 75%
Pattern hash: abc123...
```

### Step 2: Signal Outcome

```
Signal hits TP after 2 hours
Pips: +35
Session: overlap
Volatility: normal
```

### Step 3: Learning Update

```
Fetch learning_memory for pattern abc123...
Current stats:
  - Total signals: 49
  - Wins: 32
  - Win rate: 65.3%
  
Apply learning rules:
  ✅ Rule 4 triggered: "Consistent winner"
  → Boost confidence_weight by 0.3
  
New confidence_weight: 1.3
Reason: "Proven consistent performance over large sample"
```

### Step 4: Next Signal

```
Same pattern detected again
Base confidence: 75%
Adjusted confidence: 75% × 1.3 = 97.5%

Explanation:
"This pattern has a 65.3% win rate over 50 signals,
with strong performance during overlap sessions."
```

---

## 🎯 Key Differences from v3.1

| Aspect | v3.1 (Old) | v3.2 (New) |
|--------|-----------|-----------|
| Learning | Static patterns | Continuous from outcomes |
| Data Storage | All candles | Only validated candles |
| Confidence | Fixed | Dynamically adjusted |
| Explainability | Limited | Full reasoning |
| Session Awareness | Basic | Advanced with scoring |
| Safety | Manual | Auto-disable rules |

---

## 🚦 Implementation Checklist

- [x] Create 3-layer database schema
- [x] Implement Quality Gate validator
- [x] Build Session Engine
- [x] Develop Learning Engine
- [ ] Integrate with existing signal generation
- [ ] Deploy database migrations to Supabase
- [ ] Update API endpoints
- [ ] Test end-to-end learning loop
- [ ] Monitor first learning cycle

---

## 📝 Next Steps

1. **Deploy Schema:** Run `006_continuous_learning_schema.sql` on Supabase
2. **Integrate Components:** Connect Quality Gate → Learning Engine
3. **Test Learning Loop:** Simulate signal outcomes
4. **Monitor Performance:** Track confidence adjustments
5. **Iterate:** Refine learning rules based on results

---

## ⚠️ Important Notes

- **This is NOT a neural network.** It's explainable, rule-based learning.
- **Learning is conservative.** New patterns start with reduced confidence.
- **Safety first.** Learning is disabled during extreme conditions.
- **Transparency.** Every decision is auditable and explainable.

---

**Quantix AI Core v3.2 - Learning from Reality, Not Assumptions**
