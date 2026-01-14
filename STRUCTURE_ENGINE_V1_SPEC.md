# STRUCTURE_ENGINE_V1_SPEC.md

## 1. Purpose
Market Structure Reasoning Engine (non-predictive). Quantix resolves market "state" using deterministic rules based on Price Action principles (SMC/Market Structure).

## 2. Inputs
- **Clean Feed v1** candles only.
- **Price Type**: BID price only.
- **Timeframes**: H1, H4, D1.

## 3. Outputs (STATE REASONING)
- **State**: `bullish` / `bearish` / `range` / `unclear`.
- **Confidence**: Consistency-based score [0.0 - 1.0]. Represents the agreement of multiple structural pieces of evidence.
- **Dominance**: Quantitative ratio of bullish vs bearish pressure.
- **Evidence**: Human-readable list of structural facts (e.g., "Bullish BOS confirmed", "No fakeout after swing break").

## 4. Non-goals
- **No price targets**: Does not predict where the price will go.
- **No signals**: Does not provide buy/sell recommendations in the core engine.
- **No ML**: No black-box neural networks or non-deterministic optimization.

## 5. Persistence
Structure state is calculated bar-by-bar. Persistence measures how many candles a specific state has been maintained without contradiction.

## 6. Failure Policy
**FAIL HARD**: If data is missing or candle count is insufficient, the engine returns `unclear` state with 0.0 confidence. It does not perform "best effort" estimation on dirty data.
