# PHASE 2 - STEP 4: TELEGRAM MESSAGE MAPPING
## Specification v2.0 - By State

---

## 🎯 PRINCIPLE

**1 State = 1 Message Type**

Each state transition triggers a specific Telegram message. No reuse of old templates.

---

## 📨 MESSAGE TEMPLATES

### 🟢 STATE 1: WAITING_FOR_ENTRY

**Trigger:** Signal created (from `continuous_analyzer.py`)  
**Purpose:** Notify that signal is waiting for price to reach entry

```
🚨 NEW SIGNAL

Asset: EURUSD
Timeframe: M15
Direction: BUY

Status: ⏳ WAITING FOR ENTRY
Entry Price: 1.19371
Take Profit: 1.19471
Stop Loss: 1.19271

Confidence: 97%
Valid Until: 15:45 UTC

⚠️ This signal is waiting for price to reach the entry level.
```

**UX Notes:**
- ✅ KHÔNG dùng từ "expired"
- ✅ "Waiting for entry" = dễ hiểu cho retail
- ✅ Nhấn mạnh: chưa vào lệnh
- ✅ Hiển thị expiry time để user biết deadline

---

### 🔵 STATE 2: ENTRY_HIT

**Trigger:** Price touches entry level  
**Purpose:** Confirm entry was triggered, now monitoring TP/SL

```
✅ ENTRY HIT

EURUSD | M15
BUY @ 1.19371

Status: 📡 LIVE
Now monitoring Take Profit and Stop Loss.
```

**UX Notes:**
- ✅ Ngắn gọn
- ✅ Rõ "market đã chạm"
- ✅ KHÔNG nhắc lại confidence (đã qua)
- ✅ Quan trọng để user tin hệ thống

---

### 🟢 STATE 3a: TP_HIT

**Trigger:** Price touches Take Profit  
**Purpose:** Report profitable result

```
🎯 TAKE PROFIT HIT

EURUSD | M15
BUY @ 1.19371

Result: ✅ PROFIT
```

**UX Notes:**
- ✅ KHÔNG hiển thị % winrate
- ✅ KHÔNG khoe
- ✅ Chỉ là event fact
- ✅ Professional, không hype

---

### 🔴 STATE 3b: SL_HIT

**Trigger:** Price touches Stop Loss  
**Purpose:** Report loss result

```
🛑 STOP LOSS HIT

EURUSD | M15
BUY @ 1.19371

Result: ❌ LOSS
```

**UX Notes:**
- ✅ RẤT quan trọng để giữ uy tín
- ✅ KHÔNG né loss
- ✅ KHÔNG biện minh
- ✅ Transparent = trust

---

### ⚪ STATE 4: CANCELLED

**Trigger:** Expiry time reached without entry  
**Purpose:** Explain why no trade happened

```
⚠️ SIGNAL CANCELLED

EURUSD | M15

Price did not reach the entry level within the valid time.
No trade was triggered.
```

**UX Notes:**
- ✅ "Cancelled" mềm hơn "Expired"
- ✅ Rõ: không trade, không win, không loss
- ✅ Đúng câu Irfan: "If 2,3 or 4 is not updated → bad signal"

---

## 🔄 MESSAGE FLOW

```
Signal Created
    ↓
🚨 NEW SIGNAL (WAITING_FOR_ENTRY)
    ↓
    ├─→ Entry Touched
    │       ↓
    │   ✅ ENTRY HIT
    │       ↓
    │       ├─→ TP Touched
    │       │       ↓
    │       │   🎯 TAKE PROFIT HIT
    │       │
    │       └─→ SL Touched
    │               ↓
    │           🛑 STOP LOSS HIT
    │
    └─→ Expiry without Entry
            ↓
        ⚠️ SIGNAL CANCELLED
```

---

## 📐 TEMPLATE MAPPING

| State | Template | Emoji | Key Message |
|-------|----------|-------|-------------|
| WAITING_FOR_ENTRY | NEW SIGNAL | 🚨 | "waiting for price to reach entry" |
| ENTRY_HIT | ENTRY HIT | ✅ | "Now monitoring TP/SL" |
| TP_HIT | TAKE PROFIT HIT | 🎯 | "Result: PROFIT" |
| SL_HIT | STOP LOSS HIT | 🛑 | "Result: LOSS" |
| CANCELLED | SIGNAL CANCELLED | ⚠️ | "No trade was triggered" |

---

## 🚫 WHAT NOT TO DO

### ❌ Don't Reuse Old Templates
- Old "ULTRA SIGNAL" template → Deprecated
- Old "ACTIVE" template → Deprecated
- Old "EXPIRED" template → Deprecated

### ❌ Don't Add Unnecessary Info
- No winrate in TP/SL messages
- No confidence in ENTRY_HIT message
- No "dashboard link" (removed per user request)

### ❌ Don't Hide Losses
- Always send SL_HIT message
- Never skip CANCELLED message
- Transparency = credibility

---

## 💾 DATA REQUIREMENTS

### For WAITING_FOR_ENTRY Message:
```python
{
    "asset": "EURUSD",
    "timeframe": "M15",
    "direction": "BUY",
    "entry_price": 1.19371,
    "tp": 1.19471,
    "sl": 1.19271,
    "ai_confidence": 0.97,
    "expiry_at": "2026-01-30T15:45:00Z"
}
```

### For ENTRY_HIT Message:
```python
{
    "asset": "EURUSD",
    "timeframe": "M15",
    "direction": "BUY",
    "entry_price": 1.19371
}
```

### For TP_HIT / SL_HIT Messages:
```python
{
    "asset": "EURUSD",
    "timeframe": "M15",
    "direction": "BUY",
    "entry_price": 1.19371
}
```

### For CANCELLED Message:
```python
{
    "asset": "EURUSD",
    "timeframe": "M15"
}
```

---

## 🧪 TESTING CHECKLIST

- [ ] WAITING_FOR_ENTRY message displays correctly
- [ ] Expiry time formatted as "HH:MM UTC"
- [ ] ENTRY_HIT message sent when entry touched
- [ ] TP_HIT message sent when TP touched
- [ ] SL_HIT message sent when SL touched
- [ ] CANCELLED message sent on expiry
- [ ] All messages use Markdown formatting
- [ ] No old template remnants

---

## 📋 IMPLEMENTATION NOTES

### Markdown Formatting:
- Use `*bold*` for headers
- Use `@` for entry price
- Use emoji for visual clarity
- Keep line breaks consistent

### Timezone Display:
```python
# Convert UTC timestamp to readable format
expiry_time = datetime.fromisoformat(expiry_at)
expiry_str = expiry_time.strftime("%H:%M UTC")
# Example: "15:45 UTC"
```

### Direction Emoji:
```python
dir_emoji = "🟢" if direction == "BUY" else "🔴"
```

---

**Version:** 2.0  
**Status:** 🔒 FROZEN - Ready for Implementation  
**Replaces:** All v1 templates (ULTRA, ACTIVE, EXPIRED)
