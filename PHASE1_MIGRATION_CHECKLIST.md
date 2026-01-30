# Phase 1: Database Schema Update - Checklist

## 📋 Pre-Migration Checklist

- [ ] **Backup Current Database**
  ```bash
  # Create backup via Supabase Dashboard
  # Project Settings → Database → Backups → Create Backup
  ```

- [ ] **Review Migration Script**
  - [ ] Read `supabase/007_migration_v1_to_v2.sql`
  - [ ] Understand all column additions
  - [ ] Review data migration logic
  - [ ] Check rollback script

- [ ] **Test Environment Setup**
  - [ ] Verify Supabase connection
  - [ ] Check environment variables (SUPABASE_URL, SUPABASE_KEY)

---

## 🚀 Migration Steps

### Step 1: Execute Migration Script

**Option A: Via Supabase Dashboard (Recommended)**

1. Go to: https://app.supabase.com/project/YOUR_PROJECT/sql
2. Open file: `supabase/007_migration_v1_to_v2.sql`
3. Copy entire content
4. Paste into SQL Editor
5. Click "Run"
6. Wait for completion (should take < 30 seconds)

**Option B: Via Python Script**

```bash
cd d:\Automator_Prj\Quantix_AI_Core\backend
python run_migration_v2.py
```

---

### Step 2: Verify Migration

Run these queries in Supabase SQL Editor:

#### 2.1 Check New Columns
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'fx_signals'
AND column_name IN ('state', 'entry_price', 'entry_hit_at', 'expiry_at', 'result', 'closed_at')
ORDER BY column_name;
```

**Expected Result:** 6 rows showing all new columns

#### 2.2 Check State Distribution
```sql
SELECT state, COUNT(*) as count
FROM fx_signals
GROUP BY state
ORDER BY count DESC;
```

**Expected Result:** Distribution of signals across states (mostly ENTRY_HIT or CANCELLED for old data)

#### 2.3 Check Indexes
```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'fx_signals'
AND indexname LIKE 'idx_fx_signals_%';
```

**Expected Result:** 4 new indexes (state, expiry, entry_hit, active)

#### 2.4 Check Constraints
```sql
SELECT conname, contype, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'fx_signals'::regclass
AND conname LIKE 'chk_%';
```

**Expected Result:** 2 check constraints (state_valid, result_valid)

---

### Step 3: Test Data Integrity

#### 3.1 Check for NULL entry_price in WAITING_FOR_ENTRY
```sql
SELECT COUNT(*) as null_entry_count
FROM fx_signals
WHERE state = 'WAITING_FOR_ENTRY'
AND entry_price IS NULL;
```

**Expected Result:** 0 (no NULL entry_price for waiting signals)

#### 3.2 Check expiry_at is set
```sql
SELECT COUNT(*) as missing_expiry
FROM fx_signals
WHERE state = 'WAITING_FOR_ENTRY'
AND expiry_at IS NULL;
```

**Expected Result:** 0 (all waiting signals have expiry)

#### 3.3 Sample Active Signals
```sql
SELECT id, asset, direction, state, entry_price, expiry_at,
       (expiry_at - NOW()) as time_remaining
FROM fx_signals
WHERE state = 'WAITING_FOR_ENTRY'
ORDER BY generated_at DESC
LIMIT 5;
```

**Expected Result:** List of recent signals with proper data

---

## ✅ Post-Migration Checklist

- [ ] **All verification queries passed**
- [ ] **No NULL values in critical columns**
- [ ] **Indexes created successfully**
- [ ] **Constraints applied correctly**
- [ ] **Sample data looks correct**

---

## 🔄 Rollback Plan (If Needed)

If migration fails or causes issues:

1. **Stop all services**
   ```bash
   # Stop AI Core
   # Stop Signal Tracker
   ```

2. **Execute rollback script**
   ```sql
   -- Copy rollback section from 007_migration_v1_to_v2.sql
   -- Run in Supabase SQL Editor
   ```

3. **Restore from backup**
   - Go to Supabase Dashboard → Database → Backups
   - Select pre-migration backup
   - Click "Restore"

4. **Verify rollback**
   ```sql
   SELECT column_name
   FROM information_schema.columns
   WHERE table_name = 'fx_signals'
   AND column_name IN ('state', 'entry_price');
   ```
   **Expected:** No results (columns removed)

---

## 📊 Migration Status

| Step | Status | Notes |
|------|--------|-------|
| Backup Created | ⏳ Pending | |
| Migration Script Reviewed | ⏳ Pending | |
| Migration Executed | ⏳ Pending | |
| Columns Verified | ⏳ Pending | |
| Indexes Verified | ⏳ Pending | |
| Constraints Verified | ⏳ Pending | |
| Data Integrity Checked | ⏳ Pending | |

---

## 🚨 Common Issues & Solutions

### Issue 1: "column already exists"
**Solution:** Migration is idempotent, this is safe to ignore

### Issue 2: "constraint violation"
**Solution:** Check existing data, may need to clean up invalid states

### Issue 3: "permission denied"
**Solution:** Ensure you're using service_role key, not anon key

---

## 📝 Notes

- Migration is **idempotent** - safe to run multiple times
- Old `status` column is kept for backward compatibility
- New code should use `state` column
- Existing signals will be auto-migrated to new states

---

**Last Updated:** 2026-01-30  
**Migration Version:** v1 → v2  
**Estimated Time:** 5-10 minutes
