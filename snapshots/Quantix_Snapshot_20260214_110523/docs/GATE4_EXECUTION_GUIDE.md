# GATE 4 — ENABLE TELEGRAM (CONTROLLED RELEASE)

**Status:** ✅ READY TO EXECUTE  
**Mode:** LIVE (Telegram Enabled)  
**Duration:** 15-30 minutes (observe 1 complete lifecycle)

---

## 🎯 OBJECTIVE

Enable Telegram notifications and verify messages are sent correctly for each state transition.

**Success Criteria:**
- ✅ Each state sends exactly 1 message
- ✅ Message content matches template v2
- ✅ No duplicate messages
- ✅ No spam
- ✅ Messages arrive in correct order

---

## 🔐 PRINCIPLES (DO NOT BREAK)

❌ **Don't:**
- Resend old signals
- Spam messages
- Change watcher logic
- Infer performance from messages

✅ **Do:**
- One message per state transition
- Telegram is projection layer only
- Keep state machine unchanged

---

## 📋 STATE → TELEGRAM MAP

| State | Send Telegram | Meaning |
|-------|---------------|---------|
| `WAITING_FOR_ENTRY` | ✅ | First signal (new) |
| `ENTRY_HIT` | ✅ | Entry confirmed |
| `TP_HIT` | ✅ | Closed - Profit |
| `SL_HIT` | ✅ | Closed - Loss |
| `CANCELLED` | ✅ | Entry never hit (expired) |

---

## 🚀 EXECUTION STEPS

### 🔹 STEP 1: Stop Current Watcher

```powershell
# In watcher terminal, press Ctrl+C
```

### 🔹 STEP 2: Enable Telegram Mode

```powershell
cd d:\Automator_Prj\Quantix_AI_Core\backend

# Make sure venv is activated
.\.venv\Scripts\activate

# Start watcher with Telegram ENABLED
.\start_watcher_telegram.bat
```

**OR manually:**

```powershell
$env:WATCHER_OBSERVE_MODE="false"
$env:WATCHER_CHECK_INTERVAL="60"
python run_signal_watcher.py
```

---

### 🔹 STEP 3: Verify Startup

**Expected Log:**
```
============================================================
SIGNAL WATCHER STARTING
============================================================
✅ Supabase client initialized
✅ TwelveData client initialized
✅ Telegram notifier initialized
Check interval: 60 seconds
Observe mode: False
✅ SignalWatcher initialized
🔍 SignalWatcher started
[INFO] Watching X active signals
```

**Key difference from GATE 3:**
- ❌ NO "OBSERVE MODE: Telegram notifications DISABLED"
- ✅ Telegram notifier initialized

---

### 🔹 STEP 4: Monitor Telegram Channel

**Open Telegram and watch for messages.**

**Expected Flow (for 1 complete lifecycle):**

#### 1️⃣ New Signal Created (WAITING_FOR_ENTRY)

```
🟡 SIGNAL LIVE
EURUSD | M15
BUY
Entry: 1.19371
TP: 1.19471 (+10 pips)
SL: 1.19271 (-10 pips)
State: WAITING_FOR_ENTRY
Expires: 15 minutes
```

#### 2️⃣ Entry Touched (ENTRY_HIT)

```
🟢 ENTRY CONFIRMED
EURUSD | M15
Direction: BUY
Entry price: 1.19371
TP: 1.19471
SL: 1.19271
```

#### 3️⃣ TP/SL Hit (CLOSED)

**If TP:**
```
✅ TRADE CLOSED — TP HIT
EURUSD | M15
Result: PROFIT
Entry: 1.19371
Exit: 1.19471
Pips: +10
```

**If SL:**
```
🛑 TRADE CLOSED — SL HIT
EURUSD | M15
Result: LOSS
Entry: 1.19371
Exit: 1.19271
Pips: -10
```

**If Cancelled:**
```
⚠️ SIGNAL CANCELLED
EURUSD | M15
Reason: Entry not hit before expiry
```

---

### 🔹 STEP 5: Verify Message Quality

**Checklist:**

- [ ] Content matches template v2
- [ ] No "expired" wording (bad UX)
- [ ] Timestamps reasonable
- [ ] No duplicate messages
- [ ] Messages in correct channel
- [ ] Emojis display correctly
- [ ] No spam (max 1 message per state)

---

## 🧪 DRY-RUN RECOMMENDATION

**You only need to observe 1 complete lifecycle:**

1. Wait for new signal (WAITING_FOR_ENTRY)
2. Watch for entry touch (ENTRY_HIT)
3. Watch for TP/SL (CLOSED)

**Time:** ~15-30 minutes depending on market

---

## 🚦 GO/NO-GO DECISION

### ✅ GO to GATE 5 if:

- [ ] Messages sent for all state transitions
- [ ] No duplicate messages
- [ ] Content correct and professional
- [ ] No spam
- [ ] Watcher stable (no crashes)

### ❌ NO-GO if:

- [ ] Duplicate messages sent
- [ ] Messages missing
- [ ] Wrong content/format
- [ ] Spam (multiple messages per state)
- [ ] Watcher crashes

---

## 🧯 ROLLBACK (IF NEEDED)

**Quick disable:**

```powershell
# Stop watcher (Ctrl+C)

# Restart in observe mode
$env:WATCHER_OBSERVE_MODE="true"
python run_signal_watcher.py
```

**Watcher will:**
- ✅ Continue running
- ✅ State machine still writes to DB
- ✅ Telegram goes silent immediately

---

## 📊 MONITORING

### Watch Logs

```
[INFO] Watching X active signals
[INFO] ✅ Entry touched for signal abc-123
[SUCCESS] Signal abc-123 → ENTRY_HIT
[INFO] Sending Telegram: ENTRY_HIT
[INFO] 🎯 TP hit for signal abc-123
[SUCCESS] Signal abc-123 → TP_HIT (PROFIT)
[INFO] Sending Telegram: TP_HIT
```

### Check Telegram

- Open Telegram app
- Go to configured channel
- Watch for messages

---

## ✅ GATE 4 SUCCESS

**When you see:**
- ✅ At least 1 complete message flow (WAITING → ENTRY → CLOSE)
- ✅ All messages correct
- ✅ No duplicates
- ✅ No spam
- ✅ Watcher stable

**Then:**
- ✅ GATE 4 COMPLETE
- ✅ GO to GATE 5 (24-hour monitoring)

---

## 📝 NOTES

- **Observe mode default:** `true` (safe)
- **Telegram enabled when:** `WATCHER_OBSERVE_MODE=false`
- **Check interval:** 60 seconds (unchanged)
- **Only need 1 lifecycle** to verify
- **Can rollback instantly** if issues

---

**Version:** 1.0  
**Last Updated:** 2026-01-30  
**Next:** GATE 5 - 24h Live Monitoring
