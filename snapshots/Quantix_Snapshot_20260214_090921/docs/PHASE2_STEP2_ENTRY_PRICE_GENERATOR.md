# PHASE 2 - STEP 2: ENTRY PRICE GENERATOR
## Specification & Implementation

---

## 🎯 OBJECTIVE

Generate `entry_price` that is **different** from current market price, based on market structure analysis.

**Core Principle:**  
Entry price represents a **future price level** where we expect the market to reach, not where it is now.

---

## 📐 ENTRY PRICE CALCULATION RULES

### Rule 1: Entry Must Be Away from Market Price

**Minimum Distance:** 5 pips (0.0005 for EURUSD)

```python
MIN_ENTRY_DISTANCE = 0.0005  # 5 pips
```

**Why 5 pips?**
- Prevents immediate execution (not a market order)
- Allows for natural price retracement
- Filters out noise/spread

---

### Rule 2: Entry Direction Based on Signal Type

#### For BUY Signals:
```
Entry = Market Price - Offset
(Buy the dip - wait for price to pull back)
```

#### For SELL Signals:
```
Entry = Market Price + Offset
(Sell the rally - wait for price to bounce up)
```

---

## 🧮 ENTRY OFFSET CALCULATION

### Strategy A: Fixed Offset (Simple, Recommended for v2.0)

**Formula:**
```python
FIXED_OFFSET = 0.0005  # 5 pips

if direction == "BUY":
    entry_price = market_price - FIXED_OFFSET
else:  # SELL
    entry_price = market_price + FIXED_OFFSET
```

**Pros:**
- ✅ Simple, predictable
- ✅ Easy to backtest
- ✅ Consistent behavior

**Cons:**
- ⚠️ Doesn't adapt to volatility
- ⚠️ May miss entries in fast markets

---

### Strategy B: ATR-Based Offset (Advanced, for v2.1+)

**Formula:**
```python
# Calculate ATR (Average True Range) from last 14 candles
atr = calculate_atr(df, period=14)

# Entry offset = 50% of ATR
entry_offset = atr * 0.5

if direction == "BUY":
    entry_price = market_price - entry_offset
else:  # SELL
    entry_price = market_price + entry_offset
```

**Pros:**
- ✅ Adapts to market volatility
- ✅ Better in ranging vs trending markets

**Cons:**
- ⚠️ More complex
- ⚠️ Requires ATR calculation

---

### Strategy C: Structure-Based Offset (Future, v3.0)

**Formula:**
```python
# Use recent swing high/low from structure analysis
if direction == "BUY":
    # Entry at recent swing low
    entry_price = last_swing_low
else:  # SELL
    # Entry at recent swing high
    entry_price = last_swing_high
```

**Pros:**
- ✅ Aligned with market structure
- ✅ Higher probability entries

**Cons:**
- ⚠️ Requires swing point detection
- ⚠️ May be too far from market

---

## ✅ RECOMMENDED IMPLEMENTATION (v2.0)

**Use Strategy A: Fixed Offset**

### Implementation Code:

```python
def calculate_entry_price(
    market_price: float,
    direction: str,
    offset: float = 0.0005
) -> float:
    """
    Calculate entry price for future entry signal.
    
    Args:
        market_price: Current market price (P₀)
        direction: "BUY" or "SELL"
        offset: Distance from market price (default 5 pips)
    
    Returns:
        Entry price (E) where E ≠ P₀
    
    Raises:
        ValueError: If direction is invalid
    """
    if direction == "BUY":
        entry = market_price - offset
    elif direction == "SELL":
        entry = market_price + offset
    else:
        raise ValueError(f"Invalid direction: {direction}")
    
    # Round to 5 decimal places
    entry = round(entry, 5)
    
    # Validate minimum distance
    if abs(entry - market_price) < 0.0001:
        raise ValueError(f"Entry too close to market: {entry} vs {market_price}")
    
    return entry
```

---

## 🧪 VALIDATION LOGIC

### Validation Function:

```python
def validate_entry_price(
    entry: float,
    market_price: float,
    direction: str
) -> tuple[bool, str]:
    """
    Validate entry price meets all requirements.
    
    Returns:
        (is_valid, error_message)
    """
    MIN_DISTANCE = 0.0001  # 1 pip
    
    # Check 1: Entry ≠ Market Price
    if abs(entry - market_price) < MIN_DISTANCE:
        return False, f"Entry too close to market ({abs(entry - market_price):.5f} < {MIN_DISTANCE})"
    
    # Check 2: Entry in correct direction
    if direction == "BUY" and entry >= market_price:
        return False, f"BUY entry must be below market ({entry} >= {market_price})"
    
    if direction == "SELL" and entry <= market_price:
        return False, f"SELL entry must be above market ({entry} <= {market_price})"
    
    # Check 3: Entry is reasonable (not too far)
    MAX_DISTANCE = 0.0050  # 50 pips
    if abs(entry - market_price) > MAX_DISTANCE:
        return False, f"Entry too far from market ({abs(entry - market_price):.5f} > {MAX_DISTANCE})"
    
    return True, "Valid"
```

---

## 📊 EXAMPLES

### Example 1: BUY Signal
```python
market_price = 1.19371
direction = "BUY"
offset = 0.0005

entry = calculate_entry_price(market_price, direction, offset)
# entry = 1.19321 (5 pips below market)

# Validation
is_valid, msg = validate_entry_price(entry, market_price, direction)
# is_valid = True
```

### Example 2: SELL Signal
```python
market_price = 1.19371
direction = "SELL"
offset = 0.0005

entry = calculate_entry_price(market_price, direction, offset)
# entry = 1.19421 (5 pips above market)

# Validation
is_valid, msg = validate_entry_price(entry, market_price, direction)
# is_valid = True
```

### Example 3: Invalid Entry (Too Close)
```python
market_price = 1.19371
direction = "BUY"
offset = 0.00005  # Only 0.5 pips

entry = calculate_entry_price(market_price, direction, offset)
# entry = 1.19366

# Validation
is_valid, msg = validate_entry_price(entry, market_price, direction)
# is_valid = False, msg = "Entry too close to market"
```

---

## 🔄 INTEGRATION WITH CONTINUOUS ANALYZER

### Update `continuous_analyzer.py`:

```python
# In run_cycle() method, after getting market price:

# OLD (v1 - Market Now):
# entry = price  # ❌ Entry = Market Price

# NEW (v2 - Future Entry):
from quantix_core.utils.entry_calculator import calculate_entry_price, validate_entry_price

# Calculate future entry price
entry = calculate_entry_price(
    market_price=price,
    direction=direction,
    offset=0.0005  # 5 pips
)

# Validate entry
is_valid, error_msg = validate_entry_price(entry, price, direction)
if not is_valid:
    logger.warning(f"Invalid entry price: {error_msg}")
    return  # Skip this signal

# Continue with TP/SL calculation (based on entry, not market price)
if direction == "BUY":
    tp = entry + 0.0010  # TP from entry
    sl = entry - 0.0010  # SL from entry
else:
    tp = entry - 0.0010
    sl = entry + 0.0010
```

---

## 📋 TESTING REQUIREMENTS

### Unit Tests:

```python
def test_buy_entry_below_market():
    """BUY entry must be below market price"""
    entry = calculate_entry_price(1.19371, "BUY", 0.0005)
    assert entry < 1.19371
    assert entry == 1.19321

def test_sell_entry_above_market():
    """SELL entry must be above market price"""
    entry = calculate_entry_price(1.19371, "SELL", 0.0005)
    assert entry > 1.19371
    assert entry == 1.19421

def test_entry_minimum_distance():
    """Entry must be at least 1 pip away"""
    entry = calculate_entry_price(1.19371, "BUY", 0.00005)
    is_valid, _ = validate_entry_price(entry, 1.19371, "BUY")
    assert not is_valid

def test_entry_maximum_distance():
    """Entry should not be too far from market"""
    entry = calculate_entry_price(1.19371, "BUY", 0.0100)  # 100 pips
    is_valid, _ = validate_entry_price(entry, 1.19371, "BUY")
    assert not is_valid
```

---

## 🚀 DEPLOYMENT CHECKLIST

- [ ] Create `entry_calculator.py` module
- [ ] Implement `calculate_entry_price()` function
- [ ] Implement `validate_entry_price()` function
- [ ] Write unit tests
- [ ] Update `continuous_analyzer.py` to use new entry logic
- [ ] Test with mock data
- [ ] Verify entry prices in database
- [ ] Monitor first 10 real signals

---

## 📊 CONFIGURATION

### Environment Variables (Optional):

```bash
# .env
ENTRY_OFFSET_PIPS=5  # Default 5 pips
ENTRY_MIN_DISTANCE_PIPS=1  # Minimum 1 pip
ENTRY_MAX_DISTANCE_PIPS=50  # Maximum 50 pips
```

---

**Version:** 1.0  
**Status:** 🔒 FROZEN - Ready for Implementation  
**Next Step:** Bước 3 - Watcher Loop
