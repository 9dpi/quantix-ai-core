# Railway Deployment Guide - Validation Layer

## 🚀 Deploy Validator to Railway

### Prerequisites:
- ✅ Railway Hobby Plan ($5/month)
- ✅ GitHub repository connected
- ✅ Existing services running (analyzer, watcher)

---

## 📝 Changes Made:

### 1. **Procfile** - Added validator service
```procfile
web: uvicorn quantix_core.api.main:app --host 0.0.0.0 --port $PORT
analyzer: python -m quantix_core.engine.continuous_analyzer
watcher: python run_signal_watcher.py
validator: python run_pepperstone_validator.py  ← NEW
```

### 2. **run_pepperstone_validator.py** - Cloud-compatible logging
```python
# Auto-detects Railway environment
# Railway: Logs to stdout (captured by Railway)
# Local: Logs to file (validation_audit.jsonl)
```

---

## 🎯 Deployment Steps:

### Step 1: Commit Changes
```bash
cd d:\Automator_Prj\Quantix_AI_Core

git add Procfile
git add backend/run_pepperstone_validator.py
git commit -m "feat: add validation layer service for Railway"
git push origin main
```

### Step 2: Add Validator Service in Railway Dashboard

1. Go to Railway Dashboard: https://railway.app
2. Select your Quantix AI Core project
3. Click "New Service" → "From Existing Repo"
4. Select the validator service:
   - **Service Name:** `validator`
   - **Start Command:** `python run_pepperstone_validator.py`
   - **Working Directory:** `backend`

### Step 3: Configure Environment Variables

Validator uses the same `.env` as main system:
- ✅ `SUPABASE_URL` (already set)
- ✅ `SUPABASE_KEY` (already set)
- ✅ `RAILWAY_ENVIRONMENT=production` (auto-set by Railway)

No additional config needed!

### Step 4: Deploy

Railway will auto-deploy when you push to GitHub.

Or manually trigger:
1. Go to validator service
2. Click "Deploy"
3. Wait for build to complete (~2 minutes)

---

## 📊 Monitoring:

### View Logs in Railway:
```
1. Go to validator service
2. Click "Logs" tab
3. See real-time validation logs
```

### Check for Discrepancies:
```
# In Railway logs, search for:
"DISCREPANCY_DATA"

# Example:
DISCREPANCY_DATA: {"type":"TP_MISMATCH","signal_id":"abc-123",...}
```

---

## 🔍 Verification:

### After deployment, check:

1. **Service Status:**
   - Railway dashboard → validator service → "Running" ✅

2. **Logs:**
   ```
   2026-02-14 02:30:00 | INFO | 🔍 Pepperstone Validator initialized
   2026-02-14 02:30:01 | INFO | 🚀 Validation Layer started
   2026-02-14 02:30:02 | INFO | Validating 1 active signals
   ```

3. **No Errors:**
   - No "ERROR" or "FAILED" in logs

---

## 💰 Cost Impact:

```
Before: $5/month (web + analyzer + watcher)
After:  $5/month (web + analyzer + watcher + validator)

Additional cost: $0 (included in Hobby Plan)
```

---

## 🎛️ Resource Usage:

```
Estimated:
- Validator RAM: ~50 MB
- Total RAM: ~200 MB / 512 MB (39%)
- CPU: Minimal (sleep-based loop)

✅ Well within Hobby Plan limits
```

---

## 🔄 Rollback Plan:

If validator causes issues:

### Option 1: Stop Service
```
Railway Dashboard → validator service → Settings → Stop
```

### Option 2: Remove from Procfile
```bash
# Edit Procfile, remove validator line
git commit -m "rollback: remove validator"
git push origin main
```

---

## 📈 Next Steps After Deployment:

### Day 1 (Today):
- [x] Deploy validator to Railway
- [ ] Verify logs are appearing
- [ ] Check no impact on main system

### Day 2 (Tomorrow):
- [ ] Review 24h of logs
- [ ] Check for discrepancies
- [ ] Analyze validation results

### Week 2:
- [ ] Run full Phase 1 analysis
- [ ] Decide on Phase 2 (MT5 integration)

---

## 🆘 Troubleshooting:

### Issue: Validator not starting
```
Check:
1. Procfile syntax correct?
2. run_pepperstone_validator.py in backend/?
3. Railway environment variables set?
```

### Issue: No logs appearing
```
Check:
1. Railway logs tab
2. Filter by "validator" service
3. Time range set correctly?
```

### Issue: High memory usage
```
Action:
1. Check Railway metrics
2. If > 400 MB, investigate memory leak
3. Restart service if needed
```

---

## ✅ Success Criteria:

- [ ] Validator service shows "Running" in Railway
- [ ] Logs appear in Railway dashboard
- [ ] No errors in logs for 1 hour
- [ ] Main system (analyzer/watcher) unaffected
- [ ] Validation checks running every 60 seconds

---

**Ready to deploy? Run the git commands above!** 🚀
