# 🎯 Quantix Lab – Confidence & Trade Bias Mapping Table

**Version:** 1.0 (Official)  
**Last Updated:** 2026-01-15  
**Applicability:** Quantix Lab API, Signals, Frontend, Legal Docs

---

## 1️⃣ Definition

**Confidence (%)** reflects the consistency between market structure, volatility regime, and historical pattern alignment within a specific timeframe & session.

- 📌 **Confidence does NOT predict price.**
- 📌 **Confidence does NOT guarantee profit.**

> *"Confidence indicates statistical signal quality, not probability of profit."*

---

## 2️⃣ Mapping Logic (The "Spine" of Quantix)

| Confidence Range | Trade Bias | UI Label | User Action / Meaning |
| :--- | :--- | :--- | :--- |
| **0% – 39%** | ⛔ `NO TRADE` | **Neutral** | Market is noisy / No edge detected. |
| **40% – 54%** | ⚪ `WAIT` | **Weak Bias** | Direction exists but conviction is low. |
| **55% – 64%** | 🟡 `BUY / SELL` | **Cautious** | Weak bias. Experienced traders only. |
| **65% – 74%** | 🟢 `BUY / SELL` | **Valid** | Valid signal. Good structure alignment. |
| **75% – 84%** | 🔵 `BUY / SELL` | **Strong** | Clear edge. High structure agreement. |
| **85% – 100%** | 🔥 `BUY / SELL` | **High Confidence** | Strong consensus. High conviction setup. |

---

## 3️⃣ Implementation Rules (Backend/Frontend)

### Determining Direction vs. Action
- **Trade Direction** = Determined by `Market Structure Bias` (Bullish/Bearish).
- **Final Action** = Determined by `Confidence`.

### Rules
1.  **Bias Threshold:** Never display a trade direction (BUY/SELL) if Confidence < **55%**.
    - If < 55%, Status should be `NEUTRAL` or `WAIT`.
2.  **Terminology:**
    - ❌ Never use: "Guaranteed", "High Win Rate", "Sure Trade".
    - ✅ Use: "Statistical Alignment", "Structural Bias", "Signal Quality".
3.  **Override:** No manual overrides allowed on the frontend. Output is purely deterministic from the engine.

---

## 4️⃣ JSON Schema (API Standard)

```json
{
  "confidence": 78,
  "direction": "BUY",
  "bias_level": "STRONG",
  "label": "STRONG BUY",
  "trade_allowed": true,
  "ui_color": "blue",
  "description": "Clear bullish structure with strong historical alignment"
}
```

---

## 5️⃣ Legal Disclaimer (Site-Wide)

> *Quantix AI provides research-based market intelligence only. Confidence scores indicate structural alignment and statistical quality, not a guarantee of future performance. Trading involves risk.*
