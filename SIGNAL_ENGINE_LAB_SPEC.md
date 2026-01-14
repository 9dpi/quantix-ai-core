# SIGNAL ENGINE LAB — EXPERIMENTAL SPEC

⚠️ WARNING:
This module is EXPERIMENTAL and NOT part of Quantix Core.
It exists solely for research and controlled decision-support experiments.

---

## Purpose
To explore mapping between Structure Engine confidence and
human-readable decision candidates.

---

## Inputs
- Structure Engine v1 output (read-only)
- No direct access to raw market data

---

## Output
```json
{
  "decision": "BUY_CANDIDATE | SELL_CANDIDATE | NO_ACTION",
  "confidence": float,
  "valid_for": "N candles",
  "lab_only": true,
  "explain": [string]
}
```

## Decision Mapping (Example)
| Structure State | Confidence | Decision |
| :--- | :--- | :--- |
| Bullish | ≥ 0.90 | BUY_CANDIDATE |
| Bearish | ≥ 0.90 | SELL_CANDIDATE |
| Otherwise | < 0.90 | NO_ACTION |

## Safeguards
- Feature flag gated
- Disabled by default
- No price levels
- No execution logic
- No auto-learning

## Legal Position
Signal Engine Lab does NOT provide financial advice
and MUST be presented as experimental decision support only.
