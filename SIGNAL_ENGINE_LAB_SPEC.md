# SIGNAL_ENGINE_LAB_SPEC.md

**(Sandbox – không thuộc Quantix Core)**

## 1. Purpose
Signal Engine Lab là lớp Decision Support thử nghiệm, chuyển đổi:
**Market Structure State + Confidence → Buy/Sell Candidate**

👉 Không phải prediction engine
👉 Không kết nối trading
👉 Không can thiệp Structure Engine

## 2. Scope Boundary (HARD WALL)
| Layer | Access |
| :--- | :--- |
| **Clean Feed v1** | ❌ Forbidden |
| **Candles** | ❌ Forbidden |
| **Structure Engine v1** | ✅ Read-only |
| **analytics_snapshots_v1** | ✅ Access |
| **Core DB** | ❌ Forbidden |
| **Trading API** | ❌ Forbidden |

## 3. Inputs
```json
{
  "asset": "EURUSD",
  "timeframe": "H4",
  "structure_state": "bullish",
  "confidence": 0.92,
  "dominance": 0.71,
  "persistence": 3,
  "engine_version": "structure_engine_v1",
  "snapshot_id": "snap-2026-01-15-001"
}
```

## 4. Outputs (LAB ONLY)
```json
{
  "signal_id": "LAB_EURUSD_H4_2026-01-15T08",
  "classification": "BUY_CANDIDATE",
  "confidence": 0.92,
  "reason": "Sustained bullish structure with high dominance",
  "expires_in": "2 candles",
  "lab_only": true,
  "audit": {
    "snapshot_id": "snap-2026-01-15-001",
    "ruleset": "signal_mapping_v1"
  }
}
```
🚫 Không TP | 🚫 Không SL | 🚫 Không RR | 🚫 Không winrate

## 5. Learning Constraints
✅ **Allowed**:
- Confidence bucket statistics
- Continuation / failure rate
- Persistence decay analysis

❌ **Forbidden**:
- Auto-weight tuning
- Online learning
- Self-reinforcement
- Live trading hooks

## 6. CONFIDENCE → SIGNAL MAPPING (v1 – Explicit)
### 6.1 Eligibility Matrix
| Condition | Requirement |
| :--- | :--- |
| **Structure State** | Bullish / Bearish |
| **Confidence** | ≥ threshold |
| **Dominance** | ≥ threshold |
| **Persistence** | ≥ candles |
| **Fakeout Flag** | MUST be false |

### 6.2 Concrete Thresholds
#### 🟢 BUY CANDIDATE
- `structure_state`: bullish
- `confidence`: ≥ 0.88
- `dominance`: ≥ 0.65
- `persistence`: ≥ 2 candles
- `fake_breakout`: false

#### 🔴 SELL CANDIDATE
- `structure_state`: bearish
- `confidence`: ≥ 0.88
- `dominance`: ≥ 0.65
- `persistence`: ≥ 2 candles
- `fake_breakout`: false

#### ⚪ NO SIGNAL
- `confidence` < 0.75
- `dominance` < 0.55
- `range` / `unclear`
- `structure flip` < 2 candles
👉 *NO SIGNAL là trạng thái mặc định*

## 7. RISK & LEGAL POSITIONING
### 7.1 Quantix KHÔNG LÀ:
- Signal provider
- Trading system
- Investment advisor
- Automated trading bot

### 7.2 Quantix LÀ:
- Market Structure Analysis System
- Decision-support research platform
