# PHASE 2 - LOGIC LAYER SPECIFICATION
## Bước 1: Freeze Spec (Technical Definitions)

---

## 🎯 CRITICAL DEFINITIONS

### 1. What is "Touch"?

**Definition:**  
A price level is considered "touched" when the market price **crosses or equals** that level.

#### For BUY Signals:
```
Entry Touch: current_price <= entry_price
TP Touch:    current_price >= tp_price
SL Touch:    current_price <= sl_price
```

#### For SELL Signals:
```
Entry Touch: current_price >= entry_price
TP Touch:    current_price <= tp_price
SL Touch:    current_price >= sl_price
```

#### Touch Detection Method:
- **Source**: Candle High/Low (not just Close)
- **Precision**: 5 decimal places (0.00001)
- **Frequency**: Every candle close (M15 = every 15 minutes)

**Example:**
```python
# BUY signal with entry = 1.19371
# Candle: open=1.19380, high=1.19390, low=1.19365, close=1.19375

if candle.low <= 1.19371:  # Touch detected!
    mark_entry_hit()
```

---

### 2. Expiry Precision

**Rule:** Expiry is checked at **candle close**, not real-time seconds.

#### Expiry Window:
- **Duration**: 15 minutes from signal creation
- **Check Frequency**: Every M15 candle close
- **Precision**: Minute-level (not second-level)

#### Expiry Logic:
```python
# Signal created at 2026-01-30 15:30:00 UTC
signal.generated_at = datetime(2026, 1, 30, 15, 30, 0, tzinfo=UTC)
signal.expiry_at = signal.generated_at + timedelta(minutes=15)
# expiry_at = 2026-01-30 15:45:00 UTC

# Check at next candle close (15:45:00)
if current_time >= signal.expiry_at:
    if signal.state == "WAITING_FOR_ENTRY":
        mark_as_cancelled()
```

#### Why Candle Close?
- ✅ Prevents false triggers from intra-candle noise
- ✅ Aligns with how TP/SL are checked
- ✅ Consistent with market structure analysis

---

### 3. State Transition Atomicity

**Rule:** State transitions are **atomic** - only one transition per check cycle.

#### Priority Order (if multiple conditions met):
1. **Entry Hit** (highest priority)
2. **TP Hit** (if already in ENTRY_HIT)
3. **SL Hit** (if already in ENTRY_HIT)
4. **Expiry** (if still in WAITING_FOR_ENTRY)

#### Example Conflict Resolution:
```python
# Scenario: Entry and Expiry both triggered in same candle
# (Price touched entry at 15:44:50, expiry at 15:45:00)

# Resolution: Entry takes priority
if entry_touched and current_time < expiry_at:
    state = "ENTRY_HIT"  # ✅ Entry wins
elif current_time >= expiry_at:
    state = "CANCELLED"  # Only if entry not touched
```

---

### 4. Candle Data Requirements

**Minimum Data Needed:**
```python
{
    "timestamp": "2026-01-30T15:45:00Z",
    "open": 1.19380,
    "high": 1.19395,  # ← Required for touch detection
    "low": 1.19365,   # ← Required for touch detection
    "close": 1.19375,
    "volume": 1234
}
```

**Data Source:** TwelveData API (same as current)

---

### 5. Time Synchronization

**Rule:** All timestamps use **UTC** timezone.

```python
from datetime import datetime, timezone

# Always use UTC
now = datetime.now(timezone.utc)

# Never use local time
# ❌ now = datetime.now()  # WRONG!
```

---

## 📋 VALIDATION RULES

### Rule 1: Entry Must Be Different from Market Price

```python
def validate_entry_price(entry: float, market_price: float) -> bool:
    """Entry must be at least 1 pip away from market price"""
    MIN_DISTANCE = 0.0001  # 1 pip for EURUSD
    
    if abs(entry - market_price) < MIN_DISTANCE:
        return False  # Too close, reject signal
    
    return True
```

### Rule 2: Entry Must Be in Expected Direction

```python
def validate_entry_direction(direction: str, entry: float, market_price: float) -> bool:
    """
    BUY: entry should be below market (buy the dip)
    SELL: entry should be above market (sell the rally)
    """
    if direction == "BUY":
        return entry < market_price
    elif direction == "SELL":
        return entry > market_price
    
    return False
```

### Rule 3: TP/SL Must Be Valid Distances

```python
def validate_tp_sl(direction: str, entry: float, tp: float, sl: float) -> bool:
    """Ensure TP is profit direction, SL is loss direction"""
    if direction == "BUY":
        return tp > entry and sl < entry
    elif direction == "SELL":
        return tp < entry and sl > entry
    
    return False
```

---

## 🔄 STATE TRANSITION MATRIX

| Current State | Condition | Next State | Action |
|---------------|-----------|------------|--------|
| CREATED | Signal generated | WAITING_FOR_ENTRY | Send Telegram #1 |
| WAITING_FOR_ENTRY | Entry touched | ENTRY_HIT | Send Telegram #2 |
| WAITING_FOR_ENTRY | Expiry reached | CANCELLED | Send Telegram (optional) |
| ENTRY_HIT | TP touched | TP_HIT | Send Telegram #3 |
| ENTRY_HIT | SL touched | SL_HIT | Send Telegram #4 |

**Terminal States:** `TP_HIT`, `SL_HIT`, `CANCELLED`  
(No further transitions allowed)

---

## 🚨 EDGE CASES

### Edge Case 1: Entry and TP in Same Candle
```
Scenario: BUY signal, entry=1.19371, tp=1.19471
Candle: low=1.19365, high=1.19480

Resolution:
1. Mark ENTRY_HIT (entry touched first logically)
2. Next cycle: Check TP → Mark TP_HIT
```

### Edge Case 2: Entry Touched After Expiry
```
Scenario: Entry touched at 15:46, expiry at 15:45

Resolution:
- Signal already CANCELLED at 15:45
- Entry touch ignored (too late)
```

### Edge Case 3: Multiple Signals Same Asset
```
Scenario: 2 BUY signals for EURUSD active simultaneously

Resolution:
- Each signal tracked independently
- No interference between signals
```

---

## 📊 PERFORMANCE REQUIREMENTS

| Metric | Target | Notes |
|--------|--------|-------|
| Check Frequency | Every 15 min | Aligned with M15 candles |
| Touch Detection Latency | < 1 min | From candle close to state update |
| Database Write Latency | < 2 sec | State transition to DB |
| Telegram Send Latency | < 5 sec | State update to message sent |

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Touch detection works for all 3 levels (Entry, TP, SL)
- [ ] Expiry triggers correctly at candle close
- [ ] State transitions are atomic (no race conditions)
- [ ] All timestamps use UTC
- [ ] Entry validation prevents market price signals
- [ ] Edge cases handled correctly

---

**Version:** 1.0  
**Status:** 🔒 FROZEN - Ready for Implementation  
**Next Step:** Bước 2 - Entry Price Generator
