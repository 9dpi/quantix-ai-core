# MIGRATION GUIDE: v1 (Market Now) → v2 (Future Entry)

## 📋 OVERVIEW

This document outlines the step-by-step migration from the **Reactive (Market Now)** model to the **Proactive (Future Entry)** model.

---

## 🔄 WHAT'S CHANGING

### Before (v1 - Market Now)
```
Signal = Market State Snapshot at T₀
Entry = Current Market Price (P₀)
Lifecycle: ACTIVE → EXPIRED (90 min)
```

### After (v2 - Future Entry)
```
Signal = Future Price Level Prediction
Entry = Future Price (E ≠ P₀)
Lifecycle: WAITING_FOR_ENTRY → ENTRY_HIT → TP_HIT/SL_HIT
```

---

## 🎯 MIGRATION STEPS

### Phase 1: Database Schema Update

#### 1.1 Add New Columns to `fx_signals`

```sql
-- Add new state column
ALTER TABLE fx_signals 
ADD COLUMN state VARCHAR(50) DEFAULT 'WAITING_FOR_ENTRY';

-- Add entry tracking
ALTER TABLE fx_signals 
ADD COLUMN entry_hit_at TIMESTAMP;

-- Add result tracking
ALTER TABLE fx_signals 
ADD COLUMN result VARCHAR(20);

-- Add expiry tracking
ALTER TABLE fx_signals 
ADD COLUMN expiry_at TIMESTAMP;

-- Add closed tracking
ALTER TABLE fx_signals 
ADD COLUMN closed_at TIMESTAMP;
```

#### 1.2 Update Existing Records (Backward Compatibility)

```sql
-- Map old status to new state
UPDATE fx_signals 
SET state = CASE 
    WHEN status = 'ACTIVE' THEN 'ENTRY_HIT'
    WHEN status = 'EXPIRED' THEN 'CANCELLED'
    WHEN status = 'CANDIDATE' THEN 'CANCELLED'
    ELSE 'WAITING_FOR_ENTRY'
END
WHERE state IS NULL;
```

---

### Phase 2: Code Changes

#### 2.1 Update `continuous_analyzer.py`

**Key Changes:**
1. Entry calculation must be **different** from current price
2. Add expiry time calculation
3. Update Telegram template to show "WAITING FOR ENTRY"

**Before:**
```python
entry = price  # Market price at T₀
```

**After:**
```python
# Calculate future entry based on structure
if direction == "BUY":
    entry = price - 0.0005  # 5 pips below current
else:
    entry = price + 0.0005  # 5 pips above current

# Validate entry ≠ market price
if abs(entry - price) < 0.0001:
    logger.warning("Entry too close to market price, skipping signal")
    return
```

#### 2.2 Create New Signal Tracker

Create `signal_tracker.py` to monitor:
- Entry hits
- TP/SL hits
- Expiry without entry

**Pseudocode:**
```python
class SignalTracker:
    def check_entry_hit(self, signal, current_price):
        if signal.state != "WAITING_FOR_ENTRY":
            return
        
        if signal.direction == "BUY" and current_price <= signal.entry:
            self.mark_entry_hit(signal)
        elif signal.direction == "SELL" and current_price >= signal.entry:
            self.mark_entry_hit(signal)
    
    def check_tp_sl_hit(self, signal, current_price):
        if signal.state != "ENTRY_HIT":
            return
        
        # Check TP
        if (signal.direction == "BUY" and current_price >= signal.tp) or \
           (signal.direction == "SELL" and current_price <= signal.tp):
            self.mark_tp_hit(signal)
        
        # Check SL
        elif (signal.direction == "BUY" and current_price <= signal.sl) or \
             (signal.direction == "SELL" and current_price >= signal.sl):
            self.mark_sl_hit(signal)
    
    def check_expiry(self, signal):
        if signal.state != "WAITING_FOR_ENTRY":
            return
        
        if datetime.now(UTC) >= signal.expiry_at:
            self.mark_cancelled(signal)
```

---

### Phase 3: Telegram Template Updates

#### 3.1 New Template: WAITING_FOR_ENTRY

```python
def format_waiting_for_entry(signal):
    return (
        f"🚨 *SIGNAL*\n\n"
        f"Asset: {signal.asset}\n"
        f"Timeframe: {signal.timeframe}\n"
        f"Direction: {signal.direction}\n\n"
        f"Status: ⏳ WAITING FOR ENTRY\n"
        f"Entry: {signal.entry}\n"
        f"TP: {signal.tp}\n"
        f"SL: {signal.sl}\n\n"
        f"Valid until: {signal.expiry_at.strftime('%H:%M UTC')}"
    )
```

#### 3.2 New Template: ENTRY_HIT

```python
def format_entry_hit(signal):
    return (
        f"✅ *ENTRY HIT*\n\n"
        f"{signal.asset} | {signal.timeframe}\n"
        f"{signal.direction} @ {signal.entry}\n\n"
        f"Now monitoring TP / SL"
    )
```

#### 3.3 New Template: TP_HIT / SL_HIT

```python
def format_tp_hit(signal):
    return (
        f"🎯 *TAKE PROFIT HIT*\n\n"
        f"{signal.asset} | {signal.timeframe}\n"
        f"{signal.direction} @ {signal.entry}\n"
        f"Result: PROFIT"
    )

def format_sl_hit(signal):
    return (
        f"🛑 *STOP LOSS HIT*\n\n"
        f"{signal.asset} | {signal.timeframe}\n"
        f"{signal.direction} @ {signal.entry}\n"
        f"Result: LOSS"
    )
```

---

### Phase 4: Testing Strategy

#### 4.1 Unit Tests

```python
def test_entry_calculation():
    """Entry must be different from market price"""
    signal = create_signal(market_price=1.19371)
    assert abs(signal.entry - 1.19371) >= 0.0001

def test_entry_hit_detection():
    """BUY entry hits when price <= entry"""
    signal = Signal(direction="BUY", entry=1.19371, state="WAITING_FOR_ENTRY")
    tracker.check_entry_hit(signal, current_price=1.19370)
    assert signal.state == "ENTRY_HIT"

def test_expiry_without_entry():
    """Signal cancels if entry not hit before expiry"""
    signal = Signal(state="WAITING_FOR_ENTRY", expiry_at=datetime.now(UTC) - timedelta(minutes=1))
    tracker.check_expiry(signal)
    assert signal.state == "CANCELLED"
```

#### 4.2 Integration Tests

1. **End-to-End Flow:**
   - Create signal with future entry
   - Simulate price movement to entry
   - Verify ENTRY_HIT state
   - Simulate price to TP
   - Verify TP_HIT state

2. **Expiry Flow:**
   - Create signal with 5-minute expiry
   - Wait 6 minutes
   - Verify CANCELLED state

---

### Phase 5: Rollout Plan

#### 5.1 Staging Environment

1. Deploy to staging
2. Run with mock data for 24 hours
3. Verify all state transitions
4. Check Telegram messages

#### 5.2 Production Rollout

**Option A: Hard Cutover (Recommended)**
- Deploy v2 at market close (Friday)
- All new signals use v2 logic
- Old signals remain in v1 state

**Option B: Gradual Migration**
- Run v1 and v2 in parallel
- 10% of signals use v2
- Gradually increase to 100%

---

### Phase 6: Monitoring & Validation

#### 6.1 Key Metrics to Watch

- Entry hit rate (should be > 0%)
- Time to entry hit
- TP/SL hit distribution
- Cancellation rate

#### 6.2 Alerts

```python
# Alert if no entry hits in 24 hours
if entry_hit_count_24h == 0:
    send_alert("No entry hits detected - check entry calculation")

# Alert if cancellation rate > 80%
if cancellation_rate > 0.8:
    send_alert("High cancellation rate - entry levels may be too aggressive")
```

---

## 🚨 ROLLBACK PLAN

If v2 shows critical issues:

```bash
# Rollback to v1
git checkout quantix-core@pre-entry-wait

# Restore database
psql < backup_pre_v2.sql

# Restart services
./restart_quantix.sh
```

---

## ✅ CHECKLIST

- [ ] Database schema updated
- [ ] `continuous_analyzer.py` updated
- [ ] `signal_tracker.py` created
- [ ] Telegram templates updated
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Staging deployment successful
- [ ] Production deployment scheduled
- [ ] Monitoring dashboards updated
- [ ] Team notified of changes

---

**Version**: 1.0  
**Last Updated**: 2026-01-30  
**Author**: Quantix AI Team
