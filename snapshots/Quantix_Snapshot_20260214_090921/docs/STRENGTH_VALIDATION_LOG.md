# Strength Validation Log
## Mục tiêu: Validate mapping giữa Strength và kết quả thực tế

### Giả thuyết cần kiểm chứng:
1. **Low Strength (< 50%)**: Tỷ lệ fakeout/reversal cao hơn
2. **High Strength (> 70%)**: Follow-through tốt hơn, ít fakeout

### Phương pháp:
- Theo dõi 10-20 tín hiệu đầu tiên
- Ghi nhận giá sau 10-30 nến
- So sánh kết quả với dự đoán

### Dữ liệu quan sát:

#### Signal #1
- **Timestamp**: 
- **Direction**: 
- **Confidence**: 
- **Strength**: 
- **Entry Price**: 
- **Outcome (after 10 candles)**: 
- **Outcome (after 30 candles)**: 
- **Notes**: 

---

#### Signal #2
- **Timestamp**: 
- **Direction**: 
- **Confidence**: 
- **Strength**: 
- **Entry Price**: 
- **Outcome (after 10 candles)**: 
- **Outcome (after 30 candles)**: 
- **Notes**: 

---

### Kết luận sơ bộ (sau 10 signals):
_Sẽ cập nhật sau khi có đủ dữ liệu_

### Kết luận cuối cùng (sau 20 signals):
_Sẽ cập nhật sau khi có đủ dữ liệu_

### Hành động tiếp theo:
- [ ] Nếu giả thuyết đúng → Giữ nguyên công thức
- [ ] Nếu giả thuyết sai → Điều chỉnh cách tính Strength
- [ ] Nếu không rõ ràng → Thu thập thêm dữ liệu

---

## Công cụ hỗ trợ:

### 1. Xem tổng quan hiện tại:
```bash
cd d:\Automator_Prj\Quantix_AI_Core\backend
python monitor_strength_validation.py
```

### 2. Theo dõi real-time (1 giờ):
```bash
cd d:\Automator_Prj\Quantix_AI_Core\backend
python track_strength_live.py
```

### 3. Kiểm tra database trực tiếp:
```python
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

# Lấy 20 tín hiệu gần nhất
res = db.client.table(settings.TABLE_ANALYSIS_LOG)\
    .select("*")\
    .order("timestamp", desc=True)\
    .limit(20)\
    .execute()

for entry in res.data:
    print(f"{entry['timestamp']}: {entry['direction']} | Conf: {entry['confidence']:.2f} | Str: {entry.get('strength', 0):.2f}")
```
