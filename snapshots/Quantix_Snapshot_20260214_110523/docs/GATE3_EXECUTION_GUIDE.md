# GATE 3 — SIGNAL WATCHER (OBSERVE MODE)
## Execution Instructions

**Status:** ⏳ READY TO EXECUTE  
**Mode:** OBSERVE (No Telegram)  
**Duration:** 30-60 minutes

---

## 🎯 OBJECTIVE

Verify signal watcher correctly performs state transitions WITHOUT sending Telegram messages.

**Success Criteria:**
- ✅ State flow: WAITING_FOR_ENTRY → ENTRY_HIT → TP_HIT/SL_HIT
- ✅ No TP/SL before ENTRY_HIT
- ✅ No duplicate transitions
- ✅ Logs match database 1:1

---

## 📋 EXECUTION STEPS

### Step 1: Start Watcher in Observe Mode

```bash
cd d:\Automator_Prj\Quantix_AI_Core\backend

# Set observe mode (Telegram disabled)
$env:WATCHER_OBSERVE_MODE="true"
$env:WATCHER_CHECK_INTERVAL="60"

# Run watcher
python run_signal_watcher.py
```

**Expected Output:**
```
============================================================
SIGNAL WATCHER STARTING
============================================================
✅ Supabase client initialized
✅ TwelveData client initialized
Check interval: 60 seconds
Observe mode: True
🔍 OBSERVE MODE: Telegram notifications DISABLED
Only logging state transitions to verify correctness
✅ SignalWatcher initialized
🔍 SignalWatcher started
```

---

### Step 2: Monitor Logs

**Watch for state transitions:**

```
[INFO] Watching 1 active signals
[INFO] ✅ Entry touched for signal abc-123
[SUCCESS] Signal abc-123 → ENTRY_HIT
[INFO] 🎯 TP hit for signal abc-123
[SUCCESS] Signal abc-123 → TP_HIT (PROFIT)
```

**Expected Sequences:**

**Case A: Entry → TP**
```
WAITING_FOR_ENTRY → ENTRY_HIT → TP_HIT
```

**Case B: Entry → SL**
```
WAITING_FOR_ENTRY → ENTRY_HIT → SL_HIT
```

**Case C: No Entry (Expired)**
```
WAITING_FOR_ENTRY → CANCELLED
```

---

### Step 3: Run Atomicity Verification

**While watcher is running**, open new terminal:

```bash
cd d:\Automator_Prj\Quantix_AI_Core\backend
python verify_gate3_atomicity.py
```

**Expected Output:**
```
✓ Test 1: Checking for TP/SL before ENTRY_HIT...
  ✅ No TP/SL before ENTRY_HIT

✓ Test 2: Checking for ENTRY_HIT with closed_at...
  ✅ No ENTRY_HIT with premature closed_at

✓ Test 3: Checking state distribution...
  Total signals: 335
    ENTRY_HIT: 305
    CANCELLED: 30

✓ Test 4: Checking WAITING_FOR_ENTRY signals...
  WAITING_FOR_ENTRY signals: 2
    ✅ entry_price | ✅ expiry_at | abc123...

✓ Test 5: Recent state transitions...
  ...

✅ ATOMICITY VERIFICATION COMPLETE
✅ No critical violations detected
```

---

## 🚦 GO/NO-GO DECISION

### ✅ GO Criteria

- [ ] Watcher runs without crashes
- [ ] State transitions logged correctly
- [ ] No TP/SL before ENTRY_HIT (Test 1 = 0 violations)
- [ ] No duplicate ENTRY_HIT
- [ ] Logs match database state
- [ ] No Telegram messages sent

### ❌ NO-GO Triggers

- ❌ TP/SL fires before ENTRY_HIT
- ❌ ENTRY_HIT happens multiple times for same signal
- ❌ Signal stuck in WAITING_FOR_ENTRY > 30 minutes
- ❌ Watcher crashes repeatedly

---

## 🔍 MONITORING QUERIES

### Check Active Signals

```sql
SELECT id, state, entry_price, expiry_at,
       (NOW() - generated_at) as age
FROM fx_signals
WHERE state IN ('WAITING_FOR_ENTRY', 'ENTRY_HIT')
ORDER BY generated_at DESC
LIMIT 10;
```

### Check for Violations

```sql
-- CRITICAL: This MUST return 0 rows
SELECT id, state, entry_hit_at, closed_at
FROM fx_signals
WHERE (state IN ('TP_HIT','SL_HIT') AND entry_hit_at IS NULL)
   OR (state='ENTRY_HIT' AND closed_at IS NOT NULL);
```

### State Distribution

```sql
SELECT state, COUNT(*) as count
FROM fx_signals
GROUP BY state
ORDER BY count DESC;
```

---

## 📊 EXPECTED BEHAVIOR

### Normal Flow (30-60 min observation)

1. **Signals created** by analyzer (if running)
   - State: WAITING_FOR_ENTRY
   - entry_price set
   - expiry_at = +15 min

2. **Watcher detects entry touch**
   - Log: "Entry touched"
   - DB: state → ENTRY_HIT
   - DB: entry_hit_at = timestamp

3. **Watcher detects TP/SL**
   - Log: "TP hit" or "SL hit"
   - DB: state → TP_HIT or SL_HIT
   - DB: result = PROFIT or LOSS
   - DB: closed_at = timestamp

4. **OR: Signal expires**
   - Log: "Signal expired without entry"
   - DB: state → CANCELLED
   - DB: result = CANCELLED

---

## 🛑 STOP CONDITIONS

**Stop watcher if:**
1. Atomicity verification shows violations
2. Watcher crashes 3+ times
3. Logs show duplicate transitions
4. You've observed 3+ complete lifecycles successfully

**How to stop:**
- Press `Ctrl+C` in watcher terminal
- Verify process stopped: `Get-Process | Where-Object {$_.ProcessName -like "*python*"}`

---

## ✅ GATE 3 SUCCESS

**When you see:**
- ✅ At least 1 complete lifecycle (WAITING → ENTRY → TP/SL)
- ✅ Atomicity verification passes (0 violations)
- ✅ Logs are clean and match DB
- ✅ No Telegram messages sent

**Then:**
- ✅ GATE 3 COMPLETE
- ✅ GO to GATE 4 (Enable Telegram)

---

## 📝 NOTES

- **Observe mode is default** (`WATCHER_OBSERVE_MODE=true`)
- **Telegram is disabled** in observe mode
- **Check interval = 60 seconds** (can be faster for testing: 10-30s)
- **No need for perfect signals** - just need correct state flow
- **A losing signal with correct flow = PASS**

---

**Version:** 1.0  
**Last Updated:** 2026-01-30  
**Next:** GATE 4 - Telegram Live
