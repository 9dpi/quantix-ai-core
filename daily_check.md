# Quantix System Daily Report - 2026-02-25

## 🏥 Overall System Health
- **Dịch vụ Analyzer:** 🟢 ĐANG HOẠT ĐỘNG (Phát hiện tín hiệu 0e8ea5 lúc 08:18)
- **Dịch vụ Watcher:** 🟡 **DEGRADED** (Vừa được vá lỗi kết nối Price Feed)
- **Dịch vụ Validator:** 🔴 **NGOẠI TUYẾN (STALLED)** - Đang chờ nhịp tim mới sau Deploy
- **Dữ liệu Database:** 🟢 KẾT NỐI TỐT
- **Hạn ngạch API:** 🟢 AN TOÀN (60/800 credits - 7%)

---

## 🔍 1. Nhật ký Sự cố Kỹ thuật (Technical Incident Tracking)
### **Sự cố 4: Validator Stalled & Watcher Price Feed Error**
- **Thời điểm:** Phát hiện lúc 25/02/2026 - 08:20 (GMT+7).
- **Hiện tượng:** 
    - Watcher báo lỗi TwelveData API Key không hợp lệ (mặc dù Analyzer vẫn dùng được).
    - Binance Feed bị lỗi kết nối tạm thời trên Cloud khiến Watcher không lấy được giá.
- **Biện pháp xử lý:** 
    - Đã cập nhật code `signal_watcher.py` sử dụng class `BinanceFeed` mạnh mẽ hơn (hỗ trợ xoay vòng endpoint) để lấy giá live mà không cần phụ thuộc TwelveData.
    - Đã dọn dẹp các lệnh rác từ hôm qua.
- **Trạng thái:** Tín hiệu mới `0e8ea547` (SELL EURUSD) đang được giám sát chặt chẽ.

---

## 🎯 2. Trạng thái Tín hiệu (Latest Signals Today)
| Thời gian (UTC) | Asset | Trạng thái | Hướng | ID |
| :--- | :--- | :--- | :--- | :--- |
| 2026-02-25 01:03 | EURUSD | ANALYZED (Low Conf: 0.29) | BUY | - |
| 2026-02-25 00:58 | EURUSD | ANALYZED (Conf: 0.70) | SELL | - |
| 2026-02-24 16:39 | EURUSD | CANCELLED | SELL | 6a4f7536 |

*Lưu ý: Tín hiệu 0.70 (SELL) lúc 00:58 không được phát hành do có thể bị ảnh hưởng bởi logic lọc của refiner hoặc Cooldown.*

---

## 💓 3. Nhịp tim Hệ thống (Live Heartbeats)
*Nhật ký Heartbeats gần nhất từ Cloud (Railway):*
- [2026-02-25 01:02] **WATCHER** | Status: WATCHER_ONLINE_C850
- [2026-02-25 00:58] **ANALYZER** | Status: ALIVE_C170
- [2026-02-24 07:51] **VALIDATOR** | Status: ONLINE | cycle=350 (⚠️ STALE)

---

## 📉 4. Thống kê Hạn ngạch (Quota Usage)
- **Tổng số Request trong ngày:** 48
- **Giới hạn:** 800
- **Dự báo:** Thoải mái cho cả ngày hôm nay.

---
*Báo cáo kết thúc đợt kiểm tra `/daily_check_wf`. Dịch vụ Validator cần xử lý.*
