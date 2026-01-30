# PHASE 3 EXECUTION RUNBOOK
## Step-by-Step Execution with GO/NO-GO Gates

---

## 🎯 EXECUTION PRINCIPLE

**Each GATE must pass before proceeding to next.**  
**If any GATE fails → STOP and rollback.**

---

## 🔐 GATE 0 — FREEZE INPUT (5 minutes)

### Objective
Ensure clean state before migration - no concurrent processes.

### Steps

1. **Tạm dừng signal emission (if running)**
   ```bash
   # Stop continuous analyzer
   pkill -f run_continuous.py
   
   # Verify stopped
   ps aux | grep run_continuous
   # Should show: no results
   ```

2. **Confirm no old jobs running**
   ```bash
   # Check for any Python processes
   ps aux | grep python | grep quantix
   
   # Should show: only your terminal session
   ```

3. **Tag codebase**
   ```bash
   cd d:\Automator_Prj\Quantix_AI_Core
   git tag -a quantix-core@pre-phase3-exec -m "Snapshot before Phase 3 execution"
   git push origin quantix-core@pre-phase3-exec
   ```

4. **Verify tag created**
   ```bash
   git tag | grep pre-phase3-exec
   # Should show: quantix-core@pre-phase3-exec
   ```

### ✅ GO Criteria
- [ ] No signal emission running
- [ ] No concurrent processes
- [ ] Git tag created and pushed

### ❌ NO-GO → STOP
If any process still running → kill and retry

**👉 DO NOT SKIP THIS STEP**

---

## 🧱 GATE 1 — DATABASE MIGRATION (15 minutes)

### Objective
Execute schema migration safely with verification.

### Steps

1. **Manual backup Supabase**
   - Go to: https://app.supabase.com/project/YOUR_PROJECT/database/backups
   - Click "Create Backup"
   - Wait for completion
   - Note backup ID: `________________`
   - Timestamp: `________________`

2. **Run migration SQL**
   - Open: https://app.supabase.com/project/YOUR_PROJECT/sql
   - Copy content from: `supabase/007_migration_v1_to_v2.sql`
   - Paste into SQL Editor
   - Click "Run"
   - Wait for completion (~30 seconds)

3. **Verify: state column active**
   ```sql
   SELECT column_name, data_type, is_nullable
   FROM information_schema.columns
   WHERE table_name = 'fx_signals'
   AND column_name = 'state';
   ```
   **Expected:** 1 row showing `state | character varying | YES`

4. **Verify: Index exists**
   ```sql
   SELECT indexname
   FROM pg_indexes
   WHERE tablename = 'fx_signals'
   AND indexname LIKE 'idx_fx_signals_%';
   ```
   **Expected:** 4 rows (state, expiry, entry_hit, active)

5. **Verify: No constraint error**
   ```sql
   SELECT conname
   FROM pg_constraint
   WHERE conrelid = 'fx_signals'::regclass
   AND conname LIKE 'chk_%';
   ```
   **Expected:** 2 rows (chk_state_valid, chk_result_valid)

### ✅ GO Criteria
- [ ] Backup created successfully
- [ ] Migration executed without errors
- [ ] `state` column exists
- [ ] 4 indexes created
- [ ] 2 constraints active

### ❌ NO-GO → ROLLBACK IMMEDIATELY
```sql
-- Rollback script (from migration file)
ALTER TABLE fx_signals DROP COLUMN IF EXISTS state;
ALTER TABLE fx_signals DROP COLUMN IF EXISTS entry_price;
-- ... (see full rollback in migration file)
```

**If clean → PROCEED**

---

## ⚙️ GATE 2 — ENABLE ENTRY CALCULATOR (10 minutes)

### Objective
Switch analyzer to future entry logic and verify output.

### Steps

1. **Update `continuous_analyzer.py`**
   
   Find this section (around line 110):
   ```python
   # OLD (v1)
   entry = price
   ```
   
   Replace with:
   ```python
   # NEW (v2 - Future Entry)
   from quantix_core.utils.entry_calculator import EntryCalculator
   
   entry_calc = EntryCalculator(offset_pips=5.0)
   entry, is_valid, msg = entry_calc.calculate_and_validate(price, direction)
   
   if not is_valid:
       logger.warning(f"SKIPPED_INVALID_ENTRY: {msg}")
       return  # Skip this signal
   
   logger.info(
       f"Entry calculated: market={price}, entry={entry}, "
       f"offset={abs(entry - price):.5f} ({abs(entry - price) / 0.0001:.1f} pips)"
   )
   ```

2. **Add new signal fields**
   
   Find `signal_base` dict (around line 135):
   ```python
   signal_base = {
       "asset": "EURUSD",
       "direction": direction,
       # ... existing fields ...
       
       # ADD THESE:
       "entry_price": entry,  # NEW
       "state": "WAITING_FOR_ENTRY",  # NEW
       "expiry_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),  # NEW
   }
   ```

3. **Dry-run test**
   ```bash
   # Run analyzer once manually
   cd d:\Automator_Prj\Quantix_AI_Core\backend
   python run_continuous.py
   ```
   
   **Watch logs for:**
   ```
   Entry calculated: market=1.19371, entry=1.19321, offset=0.00050 (5.0 pips)
   ```

4. **Verify entry ≠ market**
   ```python
   # In logs, check:
   assert entry != market_price
   assert abs(entry - market_price) >= 0.0001  # At least 1 pip
   ```

### ✅ GO Criteria
- [ ] Code updated successfully
- [ ] Dry-run executes without errors
- [ ] Log shows: `market price`, `entry price`, `offset (pips)`
- [ ] Entry is future price (not market price)
- [ ] Offset = 5 pips

### ❌ NO-GO → STOP
**If `entry == market` → STOP IMMEDIATELY**

Possible causes:
- Entry calculator not imported
- Validation logic skipped
- Offset = 0

Fix and re-test before proceeding.

**If entry future valid → PROCEED**

---

## 👁️ GATE 3 — DEPLOY SIGNAL WATCHER (30-60 minutes)

### Objective
Run watcher in observe mode first, verify state flow before enabling Telegram.

### Steps

1. **Run watcher in observe mode**
   
   Temporarily disable Telegram in `run_signal_watcher.py`:
   ```python
   # Comment out Telegram initialization
   # telegram_notifier = TelegramNotifierV2(...)
   telegram_notifier = None  # Observe mode
   ```

2. **Start watcher**
   ```bash
   cd d:\Automator_Prj\Quantix_AI_Core\backend
   python run_signal_watcher.py
   ```

3. **Watch logs for state transitions**
   ```
   Expected log pattern:
   
   [INFO] Watching 1 active signals
   [INFO] ✅ Entry touched for signal abc-123
   [SUCCESS] Signal abc-123 → ENTRY_HIT
   [INFO] 🎯 TP hit for signal abc-123
   [SUCCESS] Signal abc-123 → TP_HIT (PROFIT)
   ```

4. **Verify state flow**
   ```sql
   -- Check state transitions in DB
   SELECT id, state, generated_at, entry_hit_at, closed_at, result
   FROM fx_signals
   WHERE generated_at > NOW() - INTERVAL '1 hour'
   ORDER BY generated_at DESC
   LIMIT 5;
   ```

5. **Check for issues**
   - [ ] No duplicate transitions (same signal → same state twice)
   - [ ] No TP/SL before ENTRY_HIT
   - [ ] No stuck signals in WAITING_FOR_ENTRY > 15 min
   - [ ] State flow: WAITING → ENTRY_HIT → TP/SL ✅

### ✅ GO Criteria
- [ ] Watcher runs without crashes
- [ ] State transitions logged correctly
- [ ] DB shows correct state flow
- [ ] No duplicate transitions
- [ ] No TP/SL before entry

### ❌ NO-GO → DEBUG
Common issues:
- Touch detection logic error
- Database update failure
- Race condition in state check

**If state flow correct → ENABLE TELEGRAM**

---

## 📲 GATE 4 — TELEGRAM V2 (LIVE)

### Objective
Enable Telegram notifications and verify message flow.

### Steps

1. **Enable Telegram notifier**
   
   In `run_signal_watcher.py`, uncomment:
   ```python
   # Enable Telegram
   telegram_notifier = TelegramNotifierV2(telegram_token, telegram_chat_id)
   ```

2. **Restart watcher**
   ```bash
   # Stop current watcher (Ctrl+C)
   # Restart with Telegram enabled
   python run_signal_watcher.py
   ```

3. **Watch 1 market only: EURUSD**
   
   Ensure analyzer is only generating EURUSD signals.

4. **Observe Telegram messages**
   
   **Expected sequence for 1 signal:**
   
   **Message 1 (WAITING_FOR_ENTRY):**
   ```
   🚨 NEW SIGNAL
   
   Asset: EURUSD
   Timeframe: M15
   Direction: 🟢 BUY
   
   Status: ⏳ WAITING FOR ENTRY
   Entry Price: 1.19321
   Take Profit: 1.19421
   Stop Loss: 1.19221
   
   Confidence: 97%
   Valid Until: 15:45 UTC
   
   ⚠️ This signal is waiting for price to reach the entry level.
   ```
   
   **Message 2 (ENTRY_HIT):**
   ```
   ✅ ENTRY HIT
   
   EURUSD | M15
   BUY @ 1.19321
   
   Status: 📡 LIVE
   Now monitoring Take Profit and Stop Loss.
   ```
   
   **Message 3a (TP_HIT) OR 3b (SL_HIT):**
   ```
   🎯 TAKE PROFIT HIT
   
   EURUSD | M15
   BUY @ 1.19321
   
   Result: ✅ PROFIT
   ```

5. **Verify:**
   - [ ] Message order: 1 → 2 → 3
   - [ ] No duplicate messages
   - [ ] Timing makes sense (entry before TP/SL)
   - [ ] Wording matches templates

### ✅ GO Criteria
- [ ] Telegram messages sent successfully
- [ ] Message order correct (1 → 2 → 3)
- [ ] No duplicates
- [ ] Timing logical
- [ ] Templates match spec

### 👉 AT THIS POINT: IRFAN WILL SEE THE DIFFERENCE

**If Telegram flow correct → PROCEED TO MONITORING**

---

## 👀 GATE 5 — LIVE MONITORING (24h first)

### Objective
Monitor system health, NOT performance.

### What to Watch

1. **Signal stuck**
   ```sql
   -- Signals in WAITING_FOR_ENTRY > 30 min
   SELECT id, asset, entry_price, expiry_at,
          (NOW() - generated_at) as age
   FROM fx_signals
   WHERE state = 'WAITING_FOR_ENTRY'
   AND generated_at < NOW() - INTERVAL '30 minutes';
   ```

2. **Entry never hit**
   ```sql
   -- Cancelled signals (entry never reached)
   SELECT COUNT(*) as cancelled_count
   FROM fx_signals
   WHERE state = 'CANCELLED'
   AND generated_at > NOW() - INTERVAL '24 hours';
   ```

3. **TP/SL fire before entry (❌ CRITICAL BUG)**
   ```sql
   -- This should return 0 rows
   SELECT id, state, entry_hit_at, closed_at
   FROM fx_signals
   WHERE state IN ('TP_HIT', 'SL_HIT')
   AND entry_hit_at IS NULL;
   ```
   **Expected:** 0 rows (if any rows → CRITICAL BUG)

### What NOT to Do

- ❌ **Do NOT** optimize entry offset
- ❌ **Do NOT** debate performance
- ❌ **Do NOT** judge win rate
- ❌ **Do NOT** change TP/SL logic

### Monitoring Dashboard

```sql
-- 24h Summary
SELECT 
    state,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM fx_signals
WHERE generated_at > NOW() - INTERVAL '24 hours'
GROUP BY state
ORDER BY count DESC;
```

### ✅ Success Indicators
- Entry hit rate > 0% (some signals reach entry)
- No TP/SL before entry
- No stuck signals > 2 hours
- Telegram order always correct

### ❌ Failure Indicators → ROLLBACK
- TP/SL firing before entry
- Duplicate state transitions
- Telegram out of sync with DB

---

## 🚨 ROLLBACK PROCEDURE

### Trigger Rollback If:
- ❌ TP/SL before entry detected
- ❌ Duplicate ENTRY_HIT messages
- ❌ Telegram mismatch vs DB state
- ❌ System crashes repeatedly

### Rollback Steps:

1. **Stop all services**
   ```bash
   pkill -f run_continuous.py
   pkill -f run_signal_watcher.py
   ```

2. **Restore database backup**
   - Go to Supabase Dashboard → Backups
   - Select backup from GATE 1
   - Click "Restore"
   - Wait for completion

3. **Revert code to pre-Phase 3**
   ```bash
   cd d:\Automator_Prj\Quantix_AI_Core
   git checkout quantix-core@pre-phase3-exec
   ```

4. **Restart v1 services**
   ```bash
   python run_continuous.py
   ```

5. **Analyze failure**
   - Review logs
   - Identify root cause
   - Fix in development
   - Re-test before re-attempting Phase 3

---

## 📋 EXECUTION CHECKLIST

### Pre-Execution
- [ ] Read entire runbook
- [ ] Understand each GATE
- [ ] Prepare rollback plan
- [ ] Notify team of maintenance window

### GATE 0: Freeze Input
- [ ] Signal emission stopped
- [ ] No concurrent processes
- [ ] Git tag created

### GATE 1: Database Migration
- [ ] Backup created
- [ ] Migration executed
- [ ] Verification passed
- [ ] GO decision made

### GATE 2: Entry Calculator
- [ ] Code updated
- [ ] Dry-run successful
- [ ] Entry ≠ market verified
- [ ] GO decision made

### GATE 3: Signal Watcher
- [ ] Observe mode tested
- [ ] State flow verified
- [ ] No duplicates
- [ ] GO decision made

### GATE 4: Telegram Live
- [ ] Notifier enabled
- [ ] Message flow correct
- [ ] Irfan sees difference
- [ ] GO decision made

### GATE 5: Monitoring
- [ ] 24h monitoring active
- [ ] No critical bugs
- [ ] System stable

---

## 🎯 FINAL SUCCESS CHECK

**Can a third party read Telegram and see:**
```
Signal → Entry → Outcome
```
**without explanation?**

✅ **YES** → Phase 3 SUCCESS  
❌ **NO** → Debug and iterate

---

**Execution Time Estimate:** 2-3 hours  
**Monitoring Period:** 24 hours  
**Rollback Time:** 15 minutes
