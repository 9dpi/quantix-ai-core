# CLEAN FEED V1 - FROZEN SPECIFICATION
**Status**: LOCKED - Immutable  
**Version**: 1.0.0  
**Effective Date**: 2026-01-15  
**Authority**: Quantix AI Core System of Record  

---

## I. SOURCE OF TRUTH

| Property | Value | Rationale |
|----------|-------|-----------|
| **Provider** | Dukascopy | Public, no geo-block, tick-level precision |
| **Data Level** | Tick-level | Ground truth, not aggregated |
| **Price** | **BID ONLY** | Consistent, deterministic, Structure Engine requirement |
| **Timezone** | UTC | No conversion, clean boundaries |
| **Access** | Public HTTP | No auth, no vendor lock-in |

---

## II. INGESTION GUARANTEES

### Client (Dukascopy)
```python
# Month indexing: 0-11 (Dukascopy native)
url = f"{BASE_URL}/{symbol}/{year:04d}/{month-1:02d}/{day:02d}/{hour:02d}h_ticks.bi5"
```

**FAIL HARD on:**
- HTTP 200 + empty body (0 bytes)
- LZMA decompression error
- Tick data corruption

**Retry Policy:**
- Network errors: exponential backoff
- 5xx errors: retry up to 5 attempts
- 4xx errors: FAIL HARD (no retry)

**Timeout:** 30 seconds (explicit)

### Tick Parser
```python
# Timestamp: CUMULATIVE from hour start
cumulative_ms += timestamp_delta
timestamp = hour_start + timedelta(milliseconds=cumulative_ms)

# Validation (STRICT):
assert bid > 0
assert ask > bid
assert timestamps_strictly_increasing
```

**NO silent skip** - corruption raises `ValueError`

---

## III. CANDLE CONSTRUCTION (FROZEN)

### Resampling Rules

**Timeframes:** H4, D1 (extendable with same rules)

**Boundaries (UTC-aligned):**
- H4: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00
- D1: 00:00

**OHLC Formula (BID PRICE ONLY):**
```python
open  = first_tick.bid
close = last_tick.bid
high  = max(tick.bid for tick in window)
low   = min(tick.bid for tick in window)
volume = sum(tick.bid_volume for tick in window)
```

### Completeness Rule (CRITICAL)
```python
complete = (tick_count >= MIN_TICKS)  # default MIN_TICKS = 10
```

**Absolute Rules:**
- ❌ NO auto-fill
- ❌ NO synthetic candles
- ❌ NO partial candles persisted

---

## IV. VALIDATION GATE (FAIL HARD)

### Integrity Checks
```python
assert high >= max(open, close)
assert low <= min(open, close)
assert high >= low
assert all(isfinite(v) for v in [open, high, low, close])
assert all(v > 0 for v in [open, high, low, close])
```

### Time Integrity
```python
# H4 alignment
assert timestamp.hour in [0, 4, 8, 12, 16, 20]
assert timestamp.minute == 0
assert timestamp.second == 0

# Sequence
assert timestamps_strictly_increasing
assert no_overlaps
```

### Acceptance Rule
```
ONLY candles with:
  complete == True
  AND
  validator.validate(candle).valid == True
are allowed to persist
```

---

## V. PERSISTENCE CONTRACT

### Table: `market_candles_v1`

**Schema (FROZEN):**
```sql
CREATE TABLE market_candles_v1 (
    id BIGSERIAL PRIMARY KEY,
    provider TEXT NOT NULL,           -- "dukascopy"
    instrument TEXT NOT NULL,         -- "EURUSD"
    timeframe TEXT NOT NULL,          -- "H4", "D1"
    timestamp TIMESTAMPTZ NOT NULL,   -- candle OPEN time (UTC)
    
    open NUMERIC(10,5) NOT NULL,
    high NUMERIC(10,5) NOT NULL,
    low  NUMERIC(10,5) NOT NULL,
    close NUMERIC(10,5) NOT NULL,
    volume BIGINT,
    complete BOOLEAN NOT NULL,
    
    source_id TEXT NOT NULL,
    ingested_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE (provider, instrument, timeframe, timestamp)
);
```

**Properties:**
- Append-only (no UPDATE)
- Idempotent upsert via UNIQUE constraint
- Audit trail: `ingested_at`, `source_id`, `validator_version`

---

## VI. SYSTEM INVARIANTS (DO NOT BREAK)

### The 5 Commandments

1. **BID price only** - Structure Engine depends on this
2. **No silent correction** - FAIL HARD or pass, no middle ground
3. **No inferred data** - If missing, it's missing
4. **Deterministic** - Same input → Same output, always
5. **Structure Engine NEVER sees dirty data** - Validator is gatekeeper

---

## VII. VERSIONING POLICY

### Breaking Changes
Any change to these rules requires **Clean Feed v2**:
- Price source (BID → MID)
- Timezone handling
- Completeness criteria
- OHLC formula
- Validation rules

### Non-Breaking Changes (Allowed in v1.x)
- Performance optimizations (same output)
- Additional metadata fields
- New timeframes (following same rules)
- Bug fixes that restore spec compliance

### Version Pinning
```python
# Structure Engine MUST pin feed version
structure_engine = StructureEngineV1(
    feed_version="v1",
    feed_provider="dukascopy"
)
```

---

## VIII. IMPLICATIONS

### What This Enables

✅ **End-to-end explainability** - Every state traceable to source ticks  
✅ **Reproducible backtests** - Same data → Same results  
✅ **No vendor lock-in** - Dukascopy replaceable if rules preserved  
✅ **No data drift mystery** - Deterministic pipeline  
✅ **No AI hallucination** - Clean data → Clean reasoning  

### What Quantix AI Is Now

**NOT:** "AI prediction tool"  
**IS:** "Market Structure Analysis System"

```
Raw Ticks (Ground Truth)
    ↓
Clean Candles (Validated)
    ↓
Structure States (Reasoned)
    ↓
Evidence (Explainable)
```

---

## IX. COMPLIANCE CHECKLIST

Before any code change touching Clean Feed v1:

- [ ] Does it modify OHLC formula? → **v2 required**
- [ ] Does it change validation rules? → **v2 required**
- [ ] Does it alter completeness logic? → **v2 required**
- [ ] Does it add silent corrections? → **FORBIDDEN**
- [ ] Does it infer missing data? → **FORBIDDEN**
- [ ] Is output deterministic? → **REQUIRED**

---

## X. AUDIT TRAIL

| Date | Version | Change | Approved By |
|------|---------|--------|-------------|
| 2026-01-15 | 1.0.0 | Initial frozen spec | System Architect |

---

**This specification is IMMUTABLE.**  
**Modifications require version bump to v2.**  
**Structure Engine depends on these guarantees.**

---

*Quantix AI Clean Feed v1 - The Single Source of Truth*
