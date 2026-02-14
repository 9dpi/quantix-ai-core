# Pepperstone Validation Layer - Integration Guide

## 🎯 Mục đích
Layer này chạy **song song** với hệ thống chính để:
- Validate tín hiệu bằng Pepperstone feed thực tế
- Phát hiện sai lệch giữa Binance và Pepperstone
- Không ảnh hưởng đến production system

---

## 🏗️ Kiến trúc

```
Main System (Production)          Validation Layer (Observer)
┌─────────────────────┐          ┌──────────────────────┐
│  Analyzer (Binance) │          │                      │
│         ↓           │          │  Pepperstone Feed    │
│    Database         │◄─────────│  (Read-only)         │
│         ↓           │          │         ↓            │
│  Watcher (Binance)  │          │  Validator           │
└─────────────────────┘          │         ↓            │
                                 │  Discrepancy Log     │
                                 └──────────────────────┘
```

---

## 🚀 Cách sử dụng

### 1. Khởi động Validation Layer
```bash
START_VALIDATION_LAYER.bat
```

### 2. Validation Layer sẽ:
- Đọc signals từ Database (passive)
- Lấy dữ liệu từ Pepperstone feed
- So sánh với quyết định của Main System
- Ghi log nếu có sai lệch

### 3. Kiểm tra kết quả
```bash
# Xem log validation
backend/validation_audit.jsonl

# Xem discrepancies
backend/validation_discrepancies.jsonl
```

---

## 📊 Output Format

### Discrepancy Log Example:
```json
{
  "type": "TP_MISMATCH",
  "signal_id": "abc-123",
  "timestamp": "2026-02-14T02:30:00Z",
  "pepperstone_says": "TP_HIT",
  "main_system_says": "ENTRY_HIT",
  "tp_price": 1.1010,
  "market_high": 1.1012,
  "market_low": 1.1005
}
```

---

## 🔧 Cấu hình Pepperstone Feed

### Option 1: Binance Proxy (Hiện tại)
```python
validator = PepperstoneValidator(feed_source="binance_proxy")
```

### Option 2: MT5 API (Recommended)
```python
# Install: pip install MetaTrader5
validator = PepperstoneValidator(feed_source="mt5_api")
```

### Option 3: cTrader Open API
```python
validator = PepperstoneValidator(feed_source="ctrader_api")
```

### Option 4: FIX API (Advanced)
```python
validator = PepperstoneValidator(feed_source="fix_api")
```

---

## 📈 Phân tích Discrepancies

### Sau 1 tuần chạy, phân tích:
```python
import json

discrepancies = []
with open("validation_discrepancies.jsonl") as f:
    for line in f:
        discrepancies.append(json.loads(line))

# Tính tỷ lệ sai lệch
total_signals = len(set(d["signal_id"] for d in discrepancies))
print(f"Signals with discrepancies: {total_signals}")

# Phân loại
entry_mismatches = [d for d in discrepancies if d["type"] == "ENTRY_MISMATCH"]
tp_mismatches = [d for d in discrepancies if d["type"] == "TP_MISMATCH"]
sl_mismatches = [d for d in discrepancies if d["type"] == "SL_MISMATCH"]

print(f"Entry mismatches: {len(entry_mismatches)}")
print(f"TP mismatches: {len(tp_mismatches)}")
print(f"SL mismatches: {len(sl_mismatches)}")
```

---

## ⚠️ Lưu ý quan trọng

1. **Không ảnh hưởng Production:**
   - Layer này chỉ READ database
   - Không WRITE gì vào DB
   - Có thể tắt bất cứ lúc nào

2. **Spread Awareness:**
   - Pepperstone spread: 0.1-0.3 pips
   - Binance: mid-price (no spread)
   - Sai lệch < 0.5 pips là chấp nhận được

3. **Latency:**
   - Validation chạy mỗi 60 giây
   - Không real-time như Main System
   - Chỉ để audit, không để execute

---

## 🎯 Roadmap

### Phase 1 (Hiện tại):
- ✅ Binance proxy validation
- ✅ Discrepancy logging

### Phase 2 (Tuần tới):
- ⏳ MT5 API integration
- ⏳ Real Pepperstone feed

### Phase 3 (Tương lai):
- ⏳ Auto-adjust spread buffer
- ⏳ Statistical analysis dashboard

---

## 📞 Support

Nếu phát hiện nhiều discrepancies (> 10%):
1. Kiểm tra Pepperstone feed connection
2. Xem lại spread settings
3. Cân nhắc tăng TP/SL buffer
