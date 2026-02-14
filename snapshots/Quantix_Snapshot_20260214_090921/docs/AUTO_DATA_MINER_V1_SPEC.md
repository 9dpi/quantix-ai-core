# AUTO DATA MINER v1 – TECHNICAL SPEC (READ-ONLY)

## 1. PURPOSE (WHAT IT IS / IS NOT)
✅ **IS**
- Tự động quan sát thị trường
- Ghi nhận Structure State
- Tạo snapshot + statistics
- Làm nền cho học có kiểm soát

❌ **IS NOT**
- Không dự đoán
- Không Buy/Sell
- Không điều chỉnh logic
- Không tự học

## 2. INPUT / OUTPUT CONTRACT
### 🔹 INPUT (LOCKED)
| Source | Version |
| :--- | :--- |
| **Clean Feed** | v1 🔒 |
| **Candles** | H1 / H4 / D1 |
| **Engine** | Structure Engine v1 🔒 |

### 🔹 OUTPUT
#### 2.1 Snapshot (atomic, immutable)
```json
{
  "snapshot_id": "EURUSD_H4_2025-01-10",
  "asset": "EURUSD",
  "timeframe": "H4",
  "window": "2025-01-10",
  "structure_state": "bullish",
  "confidence": 0.91,
  "dominance": 0.73,
  "evidence": {
    "bos": true,
    "higher_highs": true,
    "range_break": false,
    "volatility_expansion": true
  },
  "feed_version": "clean_feed_v1",
  "engine_version": "structure_engine_v1",
  "created_at": "2026-01-15T02:11:00Z"
}
```
👉 *Snapshot là bằng chứng, không phải signal*

## 3. MODULES
### 3.1 Scheduler
- Daily backfill
- Rolling window
- Resume-safe

### 3.2 Snapshot Generator
- 1 snapshot / (symbol, tf, day)
- Deterministic
- Idempotent

### 3.3 Statistics Engine (AGGREGATION ONLY)
- **State duration**: Bullish kéo dài X ngày
- **Transition**: Bull → Range probabilities
- **Evidence frequency**: BOS xuất hiện X%

### 3.4 Drift Detector (NO AUTO FIX)
- Báo động khi phân phối Confidence hoặc Evidence thay đổi quá ngưỡng baseline.

## 4. DATABASES
- `analytics_snapshots_v1` (append-only)
- `analytics_stats_v1`
- `analytics_drift_v1`

❌ **Không join ngược Core**
❌ **Không update snapshot cũ**

## 5. DATA LAW INHERITANCE
Auto Data Miner thừa kế 100% Data Law:
- BID only
- UTC
- No inference
- Deterministic
- FAIL HARD
