# GATE 3 — PRODUCTION-SAFE SETUP GUIDE
## Python 3.11 Virtual Environment Setup

**Status:** 🔴 BLOCKER - Python 3.14 incompatibility  
**Solution:** Create Python 3.11 venv  
**Time:** ~10 minutes

---

## 🎯 PROBLEM SUMMARY

**Current Issue:**
- Python 3.14 (bleeding-edge) causing compatibility issues
- `supabase`, `twelvedata`, `loguru` not fully tested on 3.14
- stdout suppression preventing debugging

**Solution:**
- Use Python 3.11.x (stable, production-ready)
- Create isolated venv for Quantix AI Core
- Install dependencies in clean environment

---

## ✅ SETUP STEPS

### 🔹 STEP 1: Install Python 3.11 (if not installed)

**Download:**
- Go to: https://www.python.org/downloads/
- Download: **Python 3.11.x** (latest 3.11 version)
- **Important:** ✔️ Tick "Add Python 3.11 to PATH"

**Verify Installation:**
```powershell
python --version
# Should show: Python 3.11.x
```

**If multiple Python versions:**
```powershell
# Find Python 3.11 executable
where.exe python
# Look for path containing "Python311"
# Example: C:\Python311\python.exe
```

---

### 🔹 STEP 2: Create Virtual Environment

```powershell
cd d:\Automator_Prj\Quantix_AI_Core\backend

# Create venv with Python 3.11
python -m venv .venv

# OR if you have multiple Python versions:
# C:\Python311\python.exe -m venv .venv

# Activate venv
.\.venv\Scripts\activate
```

**Expected Output:**
```
(.venv) PS d:\Automator_Prj\Quantix_AI_Core\backend>
```

**Verify venv Python version:**
```powershell
python --version
# Should show: Python 3.11.x (NOT 3.14)
```

---

### 🔹 STEP 3: Upgrade pip

```powershell
python -m pip install --upgrade pip
```

**Expected Output:**
```
Successfully installed pip-24.x.x
```

---

### 🔹 STEP 4: Install Dependencies

```powershell
pip install supabase twelvedata python-dotenv loguru
```

**Expected Output:**
```
Collecting supabase
  Downloading supabase-2.27.2-py3-none-any.whl
...
Successfully installed supabase-2.27.2 twelvedata-x.x.x python-dotenv-x.x.x loguru-x.x.x
```

**Time:** ~2-3 minutes

---

### 🔹 STEP 5: Verify Installation (CRITICAL)

```powershell
python -c "import supabase; print('✅ supabase OK')"
python -c "from twelvedata import TDClient; print('✅ twelvedata OK')"
python -c "from dotenv import load_dotenv; print('✅ dotenv OK')"
python -c "from loguru import logger; print('✅ loguru OK')"
```

**Expected Output:**
```
✅ supabase OK
✅ twelvedata OK
✅ dotenv OK
✅ loguru OK
```

**If all pass:** ✅ **BLOCKER RESOLVED**

---

### 🔹 STEP 6: Start Signal Watcher (OBSERVE MODE)

```powershell
# Make sure venv is activated
# You should see (.venv) in prompt

# Set environment variables
$env:WATCHER_OBSERVE_MODE="true"
$env:WATCHER_CHECK_INTERVAL="60"

# Start watcher
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
[INFO] Watching 0 active signals
```

---

## 🔍 MONITORING (After Watcher Starts)

### Watch Logs

Watcher will poll every 60 seconds. Watch for:

```
[INFO] Watching X active signals
[INFO] ✅ Entry touched for signal abc-123
[SUCCESS] Signal abc-123 → ENTRY_HIT
[INFO] 🎯 TP hit for signal abc-123
[SUCCESS] Signal abc-123 → TP_HIT (PROFIT)
```

### Run Verification (in separate terminal)

**Open NEW PowerShell:**
```powershell
cd d:\Automator_Prj\Quantix_AI_Core\backend
.\.venv\Scripts\activate
python verify_gate3_atomicity.py
```

**Expected Output:**
```
✓ Test 1: Checking for TP/SL before ENTRY_HIT...
  ✅ No TP/SL before ENTRY_HIT
...
✅ ATOMICITY VERIFICATION COMPLETE
✅ No critical violations detected
```

---

## 🚦 GATE 3 SUCCESS CRITERIA

### ✅ GO to GATE 4 if:

- [ ] Watcher runs without crashes
- [ ] State transitions logged correctly
- [ ] Atomicity verification: 0 violations
- [ ] No TP/SL before ENTRY_HIT
- [ ] Logs match database state
- [ ] No Telegram messages sent

### ❌ NO-GO if:

- [ ] TP/SL fires before ENTRY_HIT
- [ ] Duplicate ENTRY_HIT transitions
- [ ] Watcher crashes repeatedly
- [ ] State stuck in WAITING_FOR_ENTRY > 30 min

---

## 🛑 HOW TO STOP WATCHER

Press `Ctrl+C` in watcher terminal.

**Verify stopped:**
```powershell
Get-Process | Where-Object {$_.CommandLine -like "*run_signal_watcher*"}
# Should return nothing
```

---

## 📝 TROUBLESHOOTING

### Issue: "python not found" after venv activation

**Solution:**
```powershell
# Deactivate and reactivate
deactivate
.\.venv\Scripts\activate
```

### Issue: pip install fails with SSL error

**Solution:**
```powershell
python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org supabase
```

### Issue: Import errors after installation

**Solution:**
```powershell
# Verify you're in venv
python -c "import sys; print(sys.executable)"
# Should show: d:\Automator_Prj\Quantix_AI_Core\backend\.venv\Scripts\python.exe
```

---

## 🎯 AFTER GATE 3 COMPLETE

1. **Stop watcher** (Ctrl+C)
2. **Review logs** and verification results
3. **Report:** ✅ GO or ❌ NO-GO
4. **If GO:** Proceed to GATE 4 (Enable Telegram v2)

---

## 📌 IMPORTANT NOTES

- ✅ **Always activate venv** before running Quantix scripts
- ✅ **Python 3.11 is production-stable** (used by most packages)
- ✅ **Venv is isolated** - won't affect Python 3.14
- ⚠️ **Don't use Python 3.14** for production until ecosystem catches up

---

**Version:** 1.0  
**Last Updated:** 2026-01-30  
**Next:** GATE 4 - Telegram Live
