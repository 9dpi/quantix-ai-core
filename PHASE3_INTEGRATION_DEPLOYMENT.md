# PHASE 3 — INTEGRATION & DEPLOYMENT PLAN
## SignalGeniusAI x Quantix Core — State Machine v2

---

## 🎯 SUCCESS DEFINITION

**A third party can read the Telegram channel and clearly see:**
```
Signal → Entry → Outcome
```
**without explanation.**

If achieved → **Phase 3 DONE**.

---

## 1️⃣ DATABASE MIGRATION (Production Cutover)

### 1.1 Pre-flight Checklist

- [ ] **Supabase manual backup created**
  - Go to: Project Settings → Database → Backups
  - Click "Create Backup"
  - Note backup ID and timestamp

- [ ] **Current signal ingestion paused** (or maintenance window)
  - Option A: Stop `continuous_analyzer.py` temporarily
  - Option B: Schedule during low-activity hours (e.g., 3-4 AM UTC)

- [ ] **Snapshot tag exists**
  - Verify: `git tag | grep quantix-core@pre-entry-wait`
  - Should show: `quantix-core@pre-entry-wait`

### 1.2 Execute Migration

**Steps:**
1. Open Supabase SQL Editor
2. Copy content from `supabase/007_migration_v1_to_v2.sql`
3. Paste and click "Run"
4. Wait for completion (~30 seconds)

**Verify:**

```sql
-- Check columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'fx_signals' 
AND column_name IN ('state', 'entry_price', 'entry_hit_at', 'expiry_at', 'result');

-- Check constraints active
SELECT conname 
FROM pg_constraint 
WHERE conrelid = 'fx_signals'::regclass 
AND conname LIKE 'chk_%';

-- Check indexes created
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'fx_signals' 
AND indexname LIKE 'idx_fx_signals_%';
```

### 1.3 Post-migration Sanity Checks

```sql
-- State distribution query
SELECT state, COUNT(*) as count
FROM fx_signals
GROUP BY state
ORDER BY count DESC;

-- Ensure no signal stuck in invalid state
SELECT id, state, generated_at
FROM fx_signals
WHERE state NOT IN ('CREATED', 'WAITING_FOR_ENTRY', 'ENTRY_HIT', 'TP_HIT', 'SL_HIT', 'CANCELLED')
LIMIT 10;

-- Confirm idempotency (re-run safe)
-- Re-run migration script - should not error
```

**📌 Exit Criteria:** DB accepts v2 lifecycle without errors

---

## 2️⃣ UPDATE CONTINUOUS_ANALYZER.PY

### 2.1 Replace Entry Logic

**Remove:**
```python
# OLD (v1 - Market Now)
entry = price  # ❌ Market price now
```

**Inject:**
```python
# NEW (v2 - Future Entry)
from quantix_core.utils.entry_calculator import EntryCalculator

entry_calc = EntryCalculator(offset_pips=5.0)
entry, is_valid, msg = entry_calc.calculate_and_validate(price, direction)

if not is_valid:
    logger.warning(f"Invalid entry: {msg}")
    return  # Skip this signal
```

**Offset:** ±5 pips  
**Validation:** `abs(entry - market) >= min_tick * n`

### 2.2 Enforce Rule Zero

**If entry too close → do not emit signal**

```python
# Validation check
if abs(entry - price) < 0.0001:  # Less than 1 pip
    logger.warning(f"SKIPPED_INVALID_ENTRY: entry={entry}, market={price}")
    return  # Do not create signal
```

**Log as:** `SKIPPED_INVALID_ENTRY`

### 2.3 Update Signal Creation

**Add new fields:**
```python
signal_base = {
    # ... existing fields ...
    "entry_price": entry,  # NEW
    "state": "WAITING_FOR_ENTRY",  # NEW
    "expiry_at": (datetime.now(UTC) + timedelta(minutes=15)).isoformat(),  # NEW
}
```

**📌 Exit Criteria:** Analyzer emits only `WAITING_FOR_ENTRY` signals

---

## 3️⃣ DEPLOY SIGNAL WATCHER (Background Service)

### 3.1 Watcher Responsibilities

**Poll active signals:**
- `WAITING_FOR_ENTRY`
- `ENTRY_HIT`

**Detect:**
- Touch entry
- Touch TP / SL
- Expiry (pre-entry only)

### 3.2 Atomic Transitions

**One DB transaction per transition**

**State guard:**
```python
# Prevent double-entry
if signal.state != "WAITING_FOR_ENTRY":
    return  # Already processed

# Prevent TP/SL before ENTRY_HIT
if signal.state != "ENTRY_HIT":
    return  # Not ready for TP/SL check
```

### 3.3 Observability

**Structured logs:**
```python
logger.info(
    "State transition",
    signal_id=signal_id,
    from_state=old_state,
    to_state=new_state,
    price_at_event=candle["close"],
    timestamp=datetime.now(UTC).isoformat()
)
```

**Error alerts on failed transition:**
```python
if not transition_success:
    logger.error(
        "CRITICAL: State transition failed",
        signal_id=signal_id,
        error=str(e)
    )
    # Send alert to monitoring system
```

**📌 Exit Criteria:** State transitions are deterministic & replay-safe

---

## 4️⃣ TELEGRAM INTEGRATION (v2 Templates)

### 4.1 One-to-One Mapping

| State | Message |
|-------|---------|
| `WAITING_FOR_ENTRY` | 🚨 NEW SIGNAL |
| `ENTRY_HIT` | ✅ ENTRY HIT |
| `TP_HIT` | 🎯 PROFIT |
| `SL_HIT` | 🛑 LOSS |
| `CANCELLED` | ⚠️ CANCELLED |

### 4.2 Delivery Rules

- ✅ **Exactly 1 message per state**
- ✅ **No edits, no deletes**
- ✅ **Retry-on-fail with idempotent message key**

**Implementation:**
```python
# Idempotent message tracking
message_key = f"{signal_id}:{state}"

if message_key in sent_messages:
    logger.debug(f"Message already sent: {message_key}")
    return

# Send message
success = telegram.send_message(...)

if success:
    sent_messages.add(message_key)
```

**📌 Exit Criteria:** Telegram tells full lifecycle story, no spam

---

## 5️⃣ END-TO-END LIFECYCLE TESTING

### 5.1 Dry Run (Paper Test)

**Force mock prices:**

```python
# Test Scenario 1: Entry Hit → TP Hit
mock_candles = [
    {"low": 1.19320, "high": 1.19350},  # Entry touched
    {"low": 1.19400, "high": 1.19425},  # TP touched
]

# Test Scenario 2: Entry Hit → SL Hit
mock_candles = [
    {"low": 1.19320, "high": 1.19350},  # Entry touched
    {"low": 1.19200, "high": 1.19250},  # SL touched
]

# Test Scenario 3: Expiry without Entry
mock_candles = [
    {"low": 1.19350, "high": 1.19400},  # Entry NOT touched
    # ... wait for expiry ...
]
```

### 5.2 Live Shadow Test (Real Feed, No Marketing)

**1 market only:** EURUSD

**Observe:**
- Timing (signal → entry → outcome)
- Message order (1 → 2 → 3/4)
- No "expired on send"

**Checklist:**
- [ ] Signal created with `WAITING_FOR_ENTRY`
- [ ] Entry touched → `ENTRY_HIT` message sent
- [ ] TP/SL touched → Result message sent
- [ ] No duplicate messages
- [ ] Telegram order matches DB state transitions

**📌 Exit Criteria:** Irfan sees exactly `1→2→3/4` flow

---

## 6️⃣ MONITORING FIRST REAL SIGNALS

### 6.1 What to Watch (First 24h)

**Metrics:**
- % signals reaching `ENTRY_HIT`
- Avg time:
  - Signal → Entry
  - Entry → TP/SL
- Any stuck states

**Queries:**
```sql
-- Entry hit rate
SELECT 
    COUNT(CASE WHEN state = 'ENTRY_HIT' THEN 1 END) * 100.0 / COUNT(*) as entry_hit_rate
FROM fx_signals
WHERE generated_at > NOW() - INTERVAL '24 hours';

-- Avg time to entry
SELECT 
    AVG(EXTRACT(EPOCH FROM (entry_hit_at - generated_at))) / 60 as avg_minutes_to_entry
FROM fx_signals
WHERE entry_hit_at IS NOT NULL
AND generated_at > NOW() - INTERVAL '24 hours';

-- Stuck signals
SELECT id, state, generated_at, expiry_at
FROM fx_signals
WHERE state IN ('WAITING_FOR_ENTRY', 'ENTRY_HIT')
AND generated_at < NOW() - INTERVAL '2 hours';
```

### 6.2 What NOT to Judge

- ❌ Win rate
- ❌ Profitability
- ❌ R:R performance

**📌 Goal:** Prove mechanics, not results

---

## 7️⃣ ROLLBACK PLAN (Always Ready)

### Trigger Rollback If:

- ❌ Duplicate `ENTRY_HIT` messages
- ❌ TP/SL before entry
- ❌ Telegram mismatch vs DB state

### Rollback Steps:

1. **Stop watcher**
   ```bash
   # Kill signal watcher process
   pkill -f run_signal_watcher.py
   ```

2. **Restore backup**
   - Go to Supabase Dashboard → Backups
   - Select pre-migration backup
   - Click "Restore"

3. **Revert analyzer to v1**
   ```bash
   git checkout quantix-core@pre-entry-wait
   ```

4. **Resume after fix**
   - Analyze root cause
   - Fix issue
   - Re-test in staging
   - Re-deploy

---

## 📋 PHASE 3 EXECUTION CHECKLIST

### Pre-Deployment
- [ ] Database backup created
- [ ] Git snapshot tag verified
- [ ] Migration script reviewed
- [ ] Rollback plan documented

### Deployment
- [ ] Database migration executed
- [ ] Migration verified (columns, indexes, constraints)
- [ ] `continuous_analyzer.py` updated
- [ ] Entry calculator integrated
- [ ] Signal watcher deployed
- [ ] Telegram notifier v2 configured

### Testing
- [ ] Dry run tests passed
- [ ] Live shadow test completed
- [ ] Telegram message flow verified
- [ ] No duplicate messages
- [ ] State transitions atomic

### Monitoring
- [ ] First 24h metrics collected
- [ ] No stuck signals
- [ ] Entry hit rate > 0%
- [ ] Telegram order correct

### Sign-off
- [ ] Irfan confirms `1→2→3/4` flow visible
- [ ] Third party can understand lifecycle from Telegram
- [ ] No rollback triggers detected

---

## 🎯 SUCCESS METRICS

| Metric | Target | Actual |
|--------|--------|--------|
| Migration success | 100% | - |
| Entry hit rate | > 0% | - |
| Duplicate messages | 0 | - |
| Stuck signals | 0 | - |
| Telegram order correctness | 100% | - |
| Rollback events | 0 | - |

---

**Version:** 1.0  
**Status:** 🟢 READY FOR EXECUTION  
**Owner:** Quantix AI Team  
**Reviewer:** Irfan (SignalGeniusAI)
