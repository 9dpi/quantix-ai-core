# Quantix Engine Rules - Critical Architecture Principles

**Last Updated:** 2026-01-15  
**Status:** ENFORCED - Violation causes production incidents

---

## 🔴 RULE ZERO: No Module-Level Heavy Init

### ❌ FORBIDDEN PATTERN (Causes Infinite Hanging)

```python
# ❌ NEVER DO THIS - Blocks entire application
from quantix_core.engine.structure_engine_v1 import StructureEngineV1
from quantix_core.ingestion.dukascopy import DukascopyFetcher

# ❌ Module-level init = blocking on import
structure_engine = StructureEngineV1(sensitivity=2)
fetcher = DukascopyFetcher()

@router.get("/endpoint")
def endpoint():
    # Even if you don't use them here, import already blocked
    return {"status": "ok"}
```

**Why This Kills Performance:**
- Python executes module-level code **on import**
- `StructureEngineV1()` may load models, setup state (heavy)
- `DukascopyFetcher()` may setup connection pools (network I/O)
- **Every request waits** for these to complete
- In production: **infinite hanging, timeouts, 502 errors**

### ✅ CORRECT PATTERN (Lazy Init or Worker-Only)

```python
# ✅ OPTION 1: No init at all (for read-only endpoints)
from loguru import logger

@router.get("/snapshot")
def get_snapshot():
    # Read from cache/snapshot store only
    return snapshot_store.get_latest()

# ✅ OPTION 2: Lazy init (only when explicitly called)
def get_engine():
    """Lazy singleton - only init when needed"""
    if not hasattr(get_engine, "_instance"):
        get_engine._instance = StructureEngineV1(sensitivity=2)
    return get_engine._instance

# ✅ OPTION 3: Worker-only (async background job)
# Engine runs in Celery/RQ worker, writes to snapshot store
# API only reads snapshots
```

---

## 🏗️ QUANTIX ARCHITECTURE LAYERS

### Layer Separation Rules

| Layer | Allowed Operations | Forbidden |
|-------|-------------------|-----------|
| **API Endpoints** (`/api/v1/*`) | Read snapshots, validate input, format output | Engine init, data fetch, heavy compute |
| **Lab Endpoints** (`/api/v1/lab/*`) | Read cached snapshots ONLY | ANY engine execution |
| **Engine Layer** | Run in async workers, write to snapshot store | Direct HTTP exposure |
| **Ingestion Layer** | Scheduled jobs, background workers | Synchronous API calls |

### Critical Rules

1. **API = Read-Only Interface**
   - ✅ Read from snapshot store
   - ✅ Format and validate
   - ❌ Never run engine pipeline
   - ❌ Never fetch live data

2. **Engine = Async Worker**
   - ✅ Run in background (Celery, cron, RQ)
   - ✅ Write results to snapshot store
   - ❌ Never exposed to HTTP directly

3. **Lab = Experimental Snapshots**
   - ✅ Read-only cached results
   - ✅ Mock data for demo
   - ❌ NO live engine execution
   - ❌ NO data fetching

---

## 🚨 REAL INCIDENT: Infinite Hanging (2026-01-15)

### What Happened
```python
# File: backend/quantix_core/api/routes/lab_reference.py
# Lines 17-18 (BEFORE FIX)

structure_engine = StructureEngineV1(sensitivity=2)  # ❌ BLOCKING
fetcher = DukascopyFetcher()  # ❌ BLOCKING
```

**Impact:**
- `/api/v1/lab/market-reference` endpoint hung indefinitely
- Frontend spinner never stopped
- No error, no timeout, just infinite wait
- Railway showed "healthy" but requests never completed

**Root Cause:**
- Module-level init executed on **every import**
- Even though endpoint used mock data, import was blocking
- `StructureEngineV1()` init was heavy (model loading)
- `DukascopyFetcher()` setup connection pool

**Fix:**
```python
# ✅ AFTER FIX - Zero dependencies
from fastapi import APIRouter
from loguru import logger

# NO ENGINE IMPORT
# NO FETCHER IMPORT
# Pure mock response
```

**Result:**
- Response time: ∞ → **< 50ms**
- Zero blocking imports
- Instant JSON response

---

## 📋 ENFORCEMENT CHECKLIST

Before merging ANY API endpoint code:

- [ ] No module-level `StructureEngine` init
- [ ] No module-level `DukascopyFetcher` init
- [ ] No module-level DB connection init
- [ ] No heavy imports at top of file
- [ ] Endpoint returns in < 100ms (for read-only)
- [ ] Frontend has timeout fallback (5s max)

---

## 🎯 FUTURE ARCHITECTURE (Proper Async)

```
┌─────────────────────┐
│   Async Worker      │ ← Runs engine every 15min
│   (Celery/Cron)     │    Fetches data, analyzes
└──────────┬──────────┘
           │ writes
           ▼
┌─────────────────────┐
│  Snapshot Store     │ ← Redis/JSON/Memory
│  (Fast Read Cache)  │    Latest state only
└──────────┬──────────┘
           │ reads (< 10ms)
           ▼
┌─────────────────────┐
│   API Endpoints     │ ← Pure read-only
│   (/lab, /signals)  │    No compute
└─────────────────────┘
```

**Benefits:**
- API always fast (< 50ms)
- Engine can be slow (doesn't block users)
- Snapshots are deterministic
- Easy to scale (cache layer)

---

## 🔗 Related Documentation

- `IMPORT_ARCHITECTURE.md` - Import path rules
- `DEPLOYMENT_COMPLETE.md` - Production deployment guide
- `DUKASCOPY_IMPLEMENTATION.md` - Data fetcher architecture

---

**REMEMBER:** If an endpoint takes > 1 second, you're doing it wrong.
