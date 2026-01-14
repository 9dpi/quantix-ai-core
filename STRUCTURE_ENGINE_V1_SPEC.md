# STRUCTURE ENGINE V1 — OFFICIAL SPEC

## Purpose
Structure Engine v1 is a deterministic Market Structure Reasoning Engine.
It analyzes validated market candles to infer structural state, not to predict price.

Quantix Structure Engine is NOT a trading signal generator.

---

## Inputs
- Source: Clean Feed v1 ONLY
- Data type: OHLC candles
- Price: BID price only
- Timezone: UTC
- Completeness: complete=True candles only

---

## Core Concepts
- Swing High / Swing Low
- Break of Structure (BOS)
- Change of Character (CHoCH)
- Fake Breakout (filtered)

---

## Outputs
```json
{
  "feature": "structure",
  "state": "bullish | bearish | range | unclear",
  "confidence": 0.0 - 1.0,
  "dominance": {
    "bullish": float,
    "bearish": float
  },
  "evidence": [string],
  "trace_id": string,
  "source": string,
  "timeframe": string
}
```

## Confidence Definition
Confidence represents consistency and dominance of structural evidence,
not probability of price movement.

## Non-Goals (Explicit)
- ❌ No price prediction
- ❌ No entry/exit levels
- ❌ No buy/sell signals
- ❌ No machine learning
- ❌ No optimization against outcomes

## Determinism
Same input candles MUST always produce the same output state.

## Contract Stability
This spec is frozen as v1.
Any change requires a version bump (v2).
