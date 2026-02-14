# QUANTIX SIGNAL LOGIC v2 – FUTURE_ENTRY
## State Machine Specification (2026-01-30)

---

## 🎯 PRINCIPLE

Signal được tạo **trước** khi market chạm entry.  
Entry là **future price level**, không phải market price hiện tại.

---

## 0️⃣ DEFINITIONS (RẤT QUAN TRỌNG)

| Symbol | Meaning |
|--------|---------|
| **T₀** | Thời điểm signal được phát hành |
| **P₀** | Market price tại T₀ |
| **Entry (E)** | Future price level ≠ P₀ |
| **TP / SL** | Được tính từ E (không phải P₀) |
| **Expiry** | Thời điểm signal không còn chờ entry |

---

## 1️⃣ STATE LIST (CANONICAL)

| State | Ý nghĩa |
|-------|---------|
| `CREATED` | Signal vừa được sinh ra |
| `WAITING_FOR_ENTRY` | Đã phát, đang chờ market chạm entry |
| `ENTRY_HIT` | Market đã chạm entry |
| `TP_HIT` | Take profit đạt |
| `SL_HIT` | Stop loss đạt |
| `CANCELLED` | Signal hết hạn mà chưa chạm entry |

⚠️ **Lưu ý quan trọng:**
- Không có `EXPIRED` cho entry hit
- `CANCELLED` chỉ dùng khi chưa entry

---

## 2️⃣ STATE FLOW (HIGH LEVEL)

```
CREATED
   ↓
WAITING_FOR_ENTRY
   ├──→ CANCELLED   (expiry without entry)
   ↓
ENTRY_HIT
   ├──→ TP_HIT
   └──→ SL_HIT
```

---

## 3️⃣ STATE TRANSITIONS (CHI TIẾT)

### 🔹 1. CREATED → WAITING_FOR_ENTRY

**Trigger:**
- Signal generated at T₀

**Actions:**
1. Freeze:
   - Entry price (E)
   - TP, SL
   - Expiry time (T_exp)
2. Send Telegram message #1

**Telegram #1:**
```
🚨 SIGNAL

Asset: EURUSD
Timeframe: M15
Direction: BUY

Status: ⏳ WAITING FOR ENTRY
Entry: 1.19371
TP: 1.19471
SL: 1.19271

Valid until: 15:45 UTC
```

---

### 🔹 2. WAITING_FOR_ENTRY → ENTRY_HIT

**Trigger:**
- Market price touches Entry (E)
  - BUY: `price <= E`
  - SELL: `price >= E`

**Conditions:**
- Current time < Expiry
- Entry not previously hit

**Actions:**
1. Record `entry_hit_time`
2. Lock execution context
3. Send Telegram message #2

**Telegram #2:**
```
✅ ENTRY HIT

EURUSD | M15
BUY @ 1.19371

Now monitoring TP / SL
```

---

### 🔹 3a. ENTRY_HIT → TP_HIT

**Trigger:**
- Market touches TP

**Actions:**
1. Record `result = PROFIT`
2. Record time to TP
3. Send Telegram message #3

**Telegram #3:**
```
🎯 TAKE PROFIT HIT

EURUSD | M15
BUY @ 1.19371
Result: PROFIT
```

---

### 🔹 3b. ENTRY_HIT → SL_HIT

**Trigger:**
- Market touches SL

**Actions:**
1. Record `result = LOSS`
2. Record time to SL
3. Send Telegram message #4

**Telegram #4:**
```
🛑 STOP LOSS HIT

EURUSD | M15
BUY @ 1.19371
Result: LOSS
```

---

### 🔹 4. WAITING_FOR_ENTRY → CANCELLED

**Trigger:**
- Current time ≥ Expiry
- Entry never touched

**Actions:**
1. Mark as `CANCELLED`
2. No TP/SL tracking
3. Send optional Telegram update (or silent)

**Telegram (optional):**
```
⚠️ SIGNAL CANCELLED

EURUSD | M15
Entry was not reached
```

📌 **Theo formula Irfan:**  
Nếu không có #2 / #3 / #4 → signal bị coi là bad / not triggered

---

## 4️⃣ KEY DESIGN RULES (BẮT BUỘC)

### ❗ Rule 1 – Entry ≠ Market Price

Nếu:
```python
abs(E - P₀) < tick_size
```
→ **KHÔNG phát signal**

### ❗ Rule 2 – One-way lifecycle

- Entry hit chỉ xảy ra **1 lần**
- TP/SL **mutually exclusive**

### ❗ Rule 3 – Expiry chỉ áp dụng trước entry

- Sau `ENTRY_HIT` → **không expiry**

---

## 5️⃣ DATA MODEL (MINIMAL)

```json
{
  "signal_id": "uuid",
  "asset": "EURUSD",
  "direction": "BUY",
  "timeframe": "M15",

  "entry_price": 1.19371,
  "tp": 1.19471,
  "sl": 1.19271,

  "state": "WAITING_FOR_ENTRY",

  "created_at": "2026-01-30T15:30:00Z",
  "expiry_at": "2026-01-30T15:45:00Z",

  "entry_hit_at": null,
  "closed_at": null,
  "result": null
}
```

---

## 6️⃣ TẠI SAO STATE MACHINE NÀY LÀ "ĐÚNG"

✅ Đúng 100% formula Irfan  
✅ Telegram thấy rõ: signal → entry → result  
✅ Không còn "expired ngay khi gửi"  
✅ Tự động validation, không tranh luận  

---

## 7️⃣ LƯU Ý QUAN TRỌNG CHO QUANTIX CORE

**Quantix KHÔNG chịu trách nhiệm performance**

Quantix chỉ:
1. Phát signal trước market
2. Ghi nhận market chạm level

👉 **Mọi win-rate / dashboard = SignalGeniusAI layer**

---

**Version**: 2.0  
**Status**: 🟢 ACTIVE SPECIFICATION  
**Migration Path**: See `MIGRATION_v1_to_v2.md`
