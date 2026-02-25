---
description: Toàn bộ quy trình kiểm tra sức khỏe hệ thống Quantix AI Core hàng ngày
---

Hệ thống check-list vận hành để đảm bảo các dịch vụ hoạt động ổn định và không có tín hiệu bị treo.

// turbo
1. Xem tín hiệu và Sức khỏe hệ thống (Heartbeats, Analysis, Quota)
```powershell
$env:PYTHONPATH="backend"; python backend/debug_signals_status.py
$env:PYTHONPATH="backend"; python backend/system_health_check.py
```

// turbo
2. Dọn dẹp các tín hiệu bị kẹt (Stuck Signals)
```powershell
$env:PYTHONPATH="backend"; python backend/expire_old_signals.py
```

3. Kiểm tra tính đồng bộ của lớp Validation (Validator)
```powershell
$env:PYTHONPATH="backend"; python backend/monitor_validation.py
```

4. Xác nhận hồ sơ trên Frontend
Mở trình duyệt truy cập:
- [Signal Genius AI Dashboard](https://signalgeniusai.com)
- [Tele Signal Interface](https://9dpi.github.io/telesignal/)
