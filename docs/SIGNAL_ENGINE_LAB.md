# 🧪 Signal Engine Lab (Experimental)

## 🎯 Purpose
Signal Engine Lab generates **Market Reference snapshots** derived from Quantix Structure Engine outputs. 

This layer is:
- ❌ NOT a trading signal engine
- ❌ NOT financial advice
- ✅ A deterministic, explainable reference model
- ✅ Fully derived from Structure Engine v1

---

## 📥 Input
Source API: `GET /api/v1/internal/feature-state/structure`

Required fields:
- `structure_state` (bullish | bearish | range | unclear)
- `confidence` (0.0 – 1.0)
- `timeframe` / `symbol`
- `generated_at` (UTC)

---

## ⚖️ Confidence Mapping Rules (The Lab Logic)

| Structure State | Confidence | Trade Bias | Bias Strength |
|-----------------|------------|------------|---------------|
| Bullish         | ≥ 0.85     | BUY        | Strong        |
| Bullish         | 0.70–0.84  | BUY        | Weak          |
| Bullish         | < 0.70     | NEUTRAL    | N/A           |
| Bearish         | ≥ 0.85     | SELL       | Strong        |
| Bearish         | 0.70–0.84  | SELL       | Weak          |
| Bearish         | < 0.70     | NEUTRAL    | N/A           |
| Range / Unclear | Any        | NEUTRAL    | N/A           |

---

## 📤 Output (Market Reference JSON)
The final schema provided to the frontend includes:
- **Trade Bias:** BUY / SELL / NEUTRAL
- **Entry Zone:** Derived from recent ATR/Volatility
- **TP / SL:** Rule-based (Reward/Risk focus)
- **Auto-expiry:** Session-based (New York Close)

---

## 🔒 Constraints
1. **No Execution:** This is a reference only.
2. **Snapshot-based:** Non-streaming. User must refresh manually.
3. **Traceable:** Every snapshot is derived from a specific Structure Engine state.

---

**Status:** 🧪 LAB / EXPERIMENTAL  
**Last Updated:** 2026-01-15 10:15 UTC
