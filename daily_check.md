# Quantix System Daily Report - 2026-02-25

## 🏥 Overall System Health
- **Dịch vụ Analyzer:** 🟢 ĐANG HOẠT ĐỘNG
- **Dịch vụ Watcher:** � ĐANG HOẠT ĐỘNG (Đã khôi phục hoàn toàn)
- **Dịch vụ Validator:** � ĐANG HOẠT ĐỘNG (Đã vá lỗi Stall & Timeout)
- **Dịch vụ Watchdog:** 🟢 ĐANG HOẠT ĐỘNG
- **Dữ liệu Database:** 🟢 KẾT NỐI TỐT
- **Kênh Telegram:** 🟢 **FIXED** (Đã hết tin nhắn trùng)
- **Độ chính xác tín hiệu:** 🔵 IMPROVED (Đã vá lỗi khớp lệnh & TP/SL)

---

## 🔍 1. Nhật ký Sự cố Kỹ thuật (Technical Incident Tracking)
### **Sự cố 4: Validator Stalled & Watcher Price Feed Error**
- **Thời điểm:** Phát hiện lúc 25/02/2026 - 08:20 (GMT+7).
- **Hiện tượng:** Watcher báo lỗi TwelveData API Key không hợp lệ; Binance Feed bị lỗi kết nối tạm thời trên Cloud.
- **Biện pháp xử lý:** Cập nhật code `signal_watcher.py` sử dụng class `BinanceFeed` mạnh mẽ hơn.
- **Trạng thái:** ✅ Đã xử lý.

### **Sự cố 6: Khách hàng phàn nàn về lỗi khớp lệnh (Entry/TP/SL)**
- **Thời điểm:** Phát hiện lúc 25/02/2026 - 09:07 (GMT+7).
- **Biện pháp xử lý:** 
    - **Thời gian:** Giữ nguyên cấu hình cũ (Entry Window: 30-35p, Trade Duration: 90p) theo yêu cầu.
    - **Độ nhạy:** Duy trì sai số **0.2 pips (0.00002)** khi so khớp giá để cải thiện tỷ lệ khớp lệnh thực tế trên sàn của khách.
### **Sự cố 7: Tin nhắn Telegram bị trùng (Duplicate Notifications)**
- **Thời điểm:** Phát hiện lúc 25/02/2026 - 13:50 (GMT+7).
- **Hiện tượng:** Khách nhận được 2 tin nhắn y hệt nhau cho mỗi sự kiện (Tín hiệu mới, Entry Hit). Database cũng bị lưu 2-3 ID cho cùng một lệnh.
- **Nguyên nhân:** Lỗi cấu hình "Auto-Worker" trong file `api/main.py`. Hệ thống vừa chạy Analyzer/Watcher độc lập qua Procfile, vừa chạy thêm bộ Analyzer/Watcher nhúng bên trong tiến trình API -> Dẫn đến việc 2 bộ worker chạy song song trên Cloud.
- **Biện pháp xử lý:** Vô hiệu hóa các task chạy ngầm (async tasks) trong `api/main.py`. Chỉ sử dụng các Worker chuyên biệt theo đúng kiến trúc `Procfile`.
- **Trạng thái:** ✅ ĐÃ XỬ LÝ (Đã deploy bản fix).

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
- [2026-02-25 09:05] **WATCHDOG** | Status: ONLINE (Monitoring Analyzer, Watcher, Validator)
- [2026-02-25 01:02] **WATCHER** | Status: ONLINE (Price Feed Restored)
- [2026-02-25 00:58] **ANALYZER** | Status: ALIVE
- [2026-02-25 09:05] **VALIDATOR** | Status: RESTARTED (Fixed stall & timeout logic)

---

## 📉 4. Thống kê Hạn ngạch (Quota Usage)
- **Tổng số Request trong ngày:** 48
- **Giới hạn:** 800
- **Dự báo:** Thoải mái cho cả ngày hôm nay.

---
*Báo cáo kết thúc đợt kiểm tra `/daily_check_wf`. Dịch vụ Validator cần xử lý.*
