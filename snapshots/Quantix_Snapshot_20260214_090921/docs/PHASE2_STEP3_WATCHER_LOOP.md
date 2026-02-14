# PHASE 2 - STEP 3: WATCHER LOOP
## Specification & Implementation

---

## 🎯 OBJECTIVE

Create a monitoring loop that watches active signals and performs atomic state transitions based on market price movements.

**Core Principle:**  
One loop handles all state transitions: `WAITING_FOR_ENTRY` → `ENTRY_HIT` → `TP_HIT`/`SL_HIT`/`CANCELLED`

---

## 🔄 WATCHER RESPONSIBILITIES

### 1. Monitor Active Signals
- Query signals in states: `WAITING_FOR_ENTRY`, `ENTRY_HIT`
- Fetch latest market price (candle data)
- Check touch conditions

### 2. Detect State Transitions
- **Entry Touch**: Price reaches entry level
- **TP Touch**: Price reaches take profit
- **SL Touch**: Price reaches stop loss
- **Expiry**: Time exceeds expiry_at

### 3. Execute Atomic Updates
- Update signal state in database
- Record timestamps (entry_hit_at, closed_at)
- Set result (PROFIT, LOSS, CANCELLED)
- Send Telegram notifications

---

## 📐 WATCHER ARCHITECTURE

```
┌─────────────────────────────────────────┐
│         SIGNAL WATCHER LOOP             │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  1. Fetch Active Signals          │ │
│  │     - WAITING_FOR_ENTRY           │ │
│  │     - ENTRY_HIT                   │ │
│  └───────────────────────────────────┘ │
│                 ↓                       │
│  ┌───────────────────────────────────┐ │
│  │  2. Get Latest Market Data        │ │
│  │     - Fetch M15 candle            │ │
│  │     - Extract high/low/close      │ │
│  └───────────────────────────────────┘ │
│                 ↓                       │
│  ┌───────────────────────────────────┐ │
│  │  3. Check Touch Conditions        │ │
│  │     - Entry touch?                │ │
│  │     - TP touch?                   │ │
│  │     - SL touch?                   │ │
│  │     - Expiry?                     │ │
│  └───────────────────────────────────┘ │
│                 ↓                       │
│  ┌───────────────────────────────────┐ │
│  │  4. Execute State Transition      │ │
│  │     - Update database             │ │
│  │     - Send Telegram               │ │
│  │     - Log event                   │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Sleep 60 seconds → Repeat              │
└─────────────────────────────────────────┘
```

---

## 🧮 TOUCH DETECTION LOGIC

### For WAITING_FOR_ENTRY Signals:

```python
def check_entry_touch(signal, candle):
    """
    Check if entry price was touched in this candle.
    
    Args:
        signal: Signal object with entry_price and direction
        candle: Candle data with high, low, close
    
    Returns:
        bool: True if entry was touched
    """
    entry = signal.entry_price
    
    if signal.direction == "BUY":
        # BUY entry touched when price goes down to entry
        return candle.low <= entry
    
    elif signal.direction == "SELL":
        # SELL entry touched when price goes up to entry
        return candle.high >= entry
    
    return False
```

### For ENTRY_HIT Signals:

```python
def check_tp_sl_touch(signal, candle):
    """
    Check if TP or SL was touched.
    
    Returns:
        ("TP_HIT", timestamp) or ("SL_HIT", timestamp) or (None, None)
    """
    tp = signal.tp
    sl = signal.sl
    
    if signal.direction == "BUY":
        # Check TP first (priority)
        if candle.high >= tp:
            return "TP_HIT", candle.timestamp
        
        # Check SL
        if candle.low <= sl:
            return "SL_HIT", candle.timestamp
    
    elif signal.direction == "SELL":
        # Check TP first (priority)
        if candle.low <= tp:
            return "TP_HIT", candle.timestamp
        
        # Check SL
        if candle.high >= sl:
            return "SL_HIT", candle.timestamp
    
    return None, None
```

### Expiry Check:

```python
def check_expiry(signal, current_time):
    """
    Check if signal has expired without entry.
    
    Only applies to WAITING_FOR_ENTRY state.
    """
    if signal.state != "WAITING_FOR_ENTRY":
        return False
    
    return current_time >= signal.expiry_at
```

---

## 🔄 STATE TRANSITION PRIORITY

When multiple conditions are met in the same cycle, apply this priority:

1. **Entry Touch** (highest priority)
2. **TP Touch** (if in ENTRY_HIT)
3. **SL Touch** (if in ENTRY_HIT)
4. **Expiry** (if in WAITING_FOR_ENTRY)

**Example:**
```python
# If entry touched at 15:44:50 and expiry at 15:45:00
# → Entry takes priority, signal moves to ENTRY_HIT
```

---

## 💾 DATABASE OPERATIONS

### Update Signal State:

```python
def update_signal_state(signal_id, new_state, **kwargs):
    """
    Atomically update signal state in database.
    
    Args:
        signal_id: UUID of signal
        new_state: New state value
        **kwargs: Additional fields to update
            - entry_hit_at
            - closed_at
            - result
    """
    update_data = {
        "state": new_state,
        **kwargs
    }
    
    supabase.table("fx_signals").update(update_data).eq("id", signal_id).execute()
```

### Record Lifecycle Event:

```python
def record_lifecycle_event(signal_id, event_type, state_from, state_to):
    """
    Record state transition in lifecycle table.
    """
    supabase.table("fx_signal_lifecycle").insert({
        "signal_id": signal_id,
        "event_type": event_type,
        "state_from": state_from,
        "state_to": state_to,
        "event_time": datetime.now(UTC)
    }).execute()
```

---

## 📨 TELEGRAM NOTIFICATIONS

### Notification Triggers:

| State Transition | Telegram Message |
|------------------|------------------|
| WAITING_FOR_ENTRY → ENTRY_HIT | "✅ ENTRY HIT" |
| ENTRY_HIT → TP_HIT | "🎯 TAKE PROFIT HIT" |
| ENTRY_HIT → SL_HIT | "🛑 STOP LOSS HIT" |
| WAITING_FOR_ENTRY → CANCELLED | "⚠️ SIGNAL CANCELLED" (optional) |

**Note:** Initial signal creation sends "🚨 SIGNAL" message (handled by continuous_analyzer)

---

## 🔧 IMPLEMENTATION

### SignalWatcher Class:

```python
"""
Signal Watcher - Monitors active signals and executes state transitions
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from loguru import logger
from supabase import Client

class SignalWatcher:
    """
    Watches active signals and performs state transitions based on market data.
    """
    
    def __init__(self, supabase_client: Client, td_client):
        """
        Initialize signal watcher.
        
        Args:
            supabase_client: Supabase database client
            td_client: TwelveData API client for market data
        """
        self.db = supabase_client
        self.td_client = td_client
        self.check_interval = 60  # seconds
        
        logger.info("SignalWatcher initialized")
    
    def run(self):
        """
        Main watcher loop - runs continuously.
        """
        logger.info("🔍 SignalWatcher started")
        
        while True:
            try:
                self.check_cycle()
            except Exception as e:
                logger.error(f"Error in watcher cycle: {e}")
            
            time.sleep(self.check_interval)
    
    def check_cycle(self):
        """
        Single check cycle - fetch signals, check conditions, update states.
        """
        # 1. Fetch active signals
        signals = self.fetch_active_signals()
        
        if not signals:
            logger.debug("No active signals to watch")
            return
        
        logger.info(f"Watching {len(signals)} active signals")
        
        # 2. Get latest market data
        candle = self.fetch_latest_candle()
        
        if not candle:
            logger.warning("Failed to fetch market data")
            return
        
        # 3. Check each signal
        for signal in signals:
            self.check_signal(signal, candle)
    
    def fetch_active_signals(self) -> List[dict]:
        """
        Fetch signals in WAITING_FOR_ENTRY or ENTRY_HIT states.
        """
        response = self.db.table("fx_signals").select("*").in_(
            "state", 
            ["WAITING_FOR_ENTRY", "ENTRY_HIT"]
        ).execute()
        
        return response.data
    
    def fetch_latest_candle(self) -> Optional[dict]:
        """
        Fetch latest M15 candle from TwelveData.
        """
        try:
            data = self.td_client.get_time_series(
                symbol="EUR/USD",
                interval="15min",
                outputsize=1
            )
            
            if data and len(data) > 0:
                candle = data[0]
                return {
                    "timestamp": candle["datetime"],
                    "open": float(candle["open"]),
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                    "close": float(candle["close"])
                }
        except Exception as e:
            logger.error(f"Error fetching candle: {e}")
        
        return None
    
    def check_signal(self, signal: dict, candle: dict):
        """
        Check single signal for state transitions.
        """
        signal_id = signal["id"]
        current_state = signal["state"]
        
        logger.debug(f"Checking signal {signal_id} (state={current_state})")
        
        if current_state == "WAITING_FOR_ENTRY":
            self.check_waiting_signal(signal, candle)
        
        elif current_state == "ENTRY_HIT":
            self.check_entry_hit_signal(signal, candle)
    
    def check_waiting_signal(self, signal: dict, candle: dict):
        """
        Check WAITING_FOR_ENTRY signal for entry touch or expiry.
        """
        signal_id = signal["id"]
        
        # Priority 1: Check entry touch
        if self.is_entry_touched(signal, candle):
            logger.info(f"✅ Entry touched for signal {signal_id}")
            self.transition_to_entry_hit(signal, candle)
            return
        
        # Priority 2: Check expiry
        current_time = datetime.now(timezone.utc)
        expiry_at = datetime.fromisoformat(signal["expiry_at"].replace("Z", "+00:00"))
        
        if current_time >= expiry_at:
            logger.info(f"⚠️ Signal {signal_id} expired without entry")
            self.transition_to_cancelled(signal)
    
    def check_entry_hit_signal(self, signal: dict, candle: dict):
        """
        Check ENTRY_HIT signal for TP or SL touch.
        """
        signal_id = signal["id"]
        
        # Priority 1: Check TP
        if self.is_tp_touched(signal, candle):
            logger.info(f"🎯 TP hit for signal {signal_id}")
            self.transition_to_tp_hit(signal, candle)
            return
        
        # Priority 2: Check SL
        if self.is_sl_touched(signal, candle):
            logger.info(f"🛑 SL hit for signal {signal_id}")
            self.transition_to_sl_hit(signal, candle)
    
    # Touch detection methods
    def is_entry_touched(self, signal: dict, candle: dict) -> bool:
        """Check if entry was touched"""
        entry = signal["entry_price"]
        direction = signal["direction"]
        
        if direction == "BUY":
            return candle["low"] <= entry
        else:  # SELL
            return candle["high"] >= entry
    
    def is_tp_touched(self, signal: dict, candle: dict) -> bool:
        """Check if TP was touched"""
        tp = signal["tp"]
        direction = signal["direction"]
        
        if direction == "BUY":
            return candle["high"] >= tp
        else:  # SELL
            return candle["low"] <= tp
    
    def is_sl_touched(self, signal: dict, candle: dict) -> bool:
        """Check if SL was touched"""
        sl = signal["sl"]
        direction = signal["direction"]
        
        if direction == "BUY":
            return candle["low"] <= sl
        else:  # SELL
            return candle["high"] >= sl
    
    # State transition methods
    def transition_to_entry_hit(self, signal: dict, candle: dict):
        """Transition: WAITING_FOR_ENTRY → ENTRY_HIT"""
        self.db.table("fx_signals").update({
            "state": "ENTRY_HIT",
            "entry_hit_at": candle["timestamp"]
        }).eq("id", signal["id"]).execute()
        
        # Send Telegram notification
        self.send_telegram_entry_hit(signal)
    
    def transition_to_tp_hit(self, signal: dict, candle: dict):
        """Transition: ENTRY_HIT → TP_HIT"""
        self.db.table("fx_signals").update({
            "state": "TP_HIT",
            "result": "PROFIT",
            "closed_at": candle["timestamp"]
        }).eq("id", signal["id"]).execute()
        
        # Send Telegram notification
        self.send_telegram_tp_hit(signal)
    
    def transition_to_sl_hit(self, signal: dict, candle: dict):
        """Transition: ENTRY_HIT → SL_HIT"""
        self.db.table("fx_signals").update({
            "state": "SL_HIT",
            "result": "LOSS",
            "closed_at": candle["timestamp"]
        }).eq("id", signal["id"]).execute()
        
        # Send Telegram notification
        self.send_telegram_sl_hit(signal)
    
    def transition_to_cancelled(self, signal: dict):
        """Transition: WAITING_FOR_ENTRY → CANCELLED"""
        self.db.table("fx_signals").update({
            "state": "CANCELLED",
            "result": "CANCELLED",
            "closed_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", signal["id"]).execute()
        
        # Optional: Send Telegram notification
        # self.send_telegram_cancelled(signal)
    
    # Telegram notification methods (to be implemented in Step 4)
    def send_telegram_entry_hit(self, signal: dict):
        """Send 'Entry Hit' Telegram message"""
        pass  # Implemented in Step 4
    
    def send_telegram_tp_hit(self, signal: dict):
        """Send 'TP Hit' Telegram message"""
        pass  # Implemented in Step 4
    
    def send_telegram_sl_hit(self, signal: dict):
        """Send 'SL Hit' Telegram message"""
        pass  # Implemented in Step 4
```

---

## 🧪 TESTING STRATEGY

### Unit Tests:

```python
def test_entry_touch_detection_buy():
    """Test entry touch for BUY signal"""
    signal = {"direction": "BUY", "entry_price": 1.19321}
    candle = {"low": 1.19320, "high": 1.19400}
    
    assert watcher.is_entry_touched(signal, candle) is True

def test_tp_touch_detection_sell():
    """Test TP touch for SELL signal"""
    signal = {"direction": "SELL", "tp": 1.19321}
    candle = {"low": 1.19320, "high": 1.19400}
    
    assert watcher.is_tp_touched(signal, candle) is True
```

### Integration Tests:

1. **Full Lifecycle Test:**
   - Create signal in WAITING_FOR_ENTRY
   - Simulate price touching entry
   - Verify state → ENTRY_HIT
   - Simulate price touching TP
   - Verify state → TP_HIT

---

## 📋 DEPLOYMENT CHECKLIST

- [ ] Create `signal_watcher.py` module
- [ ] Implement `SignalWatcher` class
- [ ] Write unit tests for touch detection
- [ ] Write integration tests for state transitions
- [ ] Create systemd service or supervisor config
- [ ] Test with mock data
- [ ] Deploy to production
- [ ] Monitor first 24 hours

---

## ⚙️ CONFIGURATION

```bash
# .env
WATCHER_CHECK_INTERVAL=60  # seconds
WATCHER_ENABLED=true
```

---

**Version:** 1.0  
**Status:** 🔒 FROZEN - Ready for Implementation  
**Next Step:** Bước 4 - Telegram Mapping
