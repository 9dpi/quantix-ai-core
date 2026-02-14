# QUANTIX ROADMAP V2 (RESEARCH GRADE)

## 🎯 OBJECTIVE
Transform Quantix from a static structure resolver into a dynamic market intelligence system with deeper persistence and stability metrics.

## 🧱 V2 RESEARCH MODULES (NON-PREDICTIVE)

### 1. Regime Engine
- **Purpose**: Classify market into distinct regimes: High-Vol Trend, Low-Vol Range, Mean Reversion.
- **Metric**: Derived from structural persistence and ADR (Average Daily Range) ratios.
- **Rule**: Purely descriptive. Categorizes *what* is happening now.

### 2. Persistence Metrics
- **State Half-life**: Measuring the historical time a state remains valid before flipping.
- **Stability Score**: A metric for structural noise levels.
- **Flip Frequency**: Detection of choppy environments where structure is unreliable.

### 3. Confidence Decay Logic
- **Mechanism**: Confidence naturally decays over time if no new BOS (Break of Structure) or HL/HH occurs.
- **Benefit**: Eliminates "stale" reasoning that relies on old market data.

### 4. Auto Data Miner (Phase 2)
- **Controlled Ingestion**: Automated collection of (Regime × Outcome) matrices.
- **Purpose**: Statistical analysis of how specific regimes historically transition.
- **Safety**: Results are processed offline. No auto-update to core logic.

## 🚫 EXCLUSIONS (STRICT BOUNDARIES)
The following will **NEVER** be implemented in v2 Core:
- **Online learning**: No real-time logic modification.
- **Reinforcement learning**: No reward-based pathfinding.
- **Auto trading**: No trade execution hooks.
- **Black-box models**: No architectures that cannot be explained via SMC/Structure principles.

## 🏁 SUCCESS CRITERIA
- 99.9% Reproducibility of all v2 metrics.
- Comprehensive audit trail for every regime shift.
- Legal positioning maintained as a "Research Intelligence Tool".
