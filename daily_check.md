# Quantix System Daily Report - 2026-02-25

## 🏥 Overall System Health
- **Dịch vụ Analyzer:** 🟢 ĐANG HOẠT ĐỘNG
- **Dịch vụ Watcher:** � ĐANG HOẠT ĐỘNG (Đã khôi phục hoàn toàn)
- **Dịch vụ Validator:** � ĐANG HOẠT ĐỘNG (Đã vá lỗi Stall & Timeout)
- **Dịch vụ Watchdog:** 🔵 **NEW** (Đã kích hoạt giám sát 24/7)
- **Dữ liệu Database:** 🟢 KẾT NỐI TỐT
- **Hạn ngạch API:** 🟢 AN TOÀN (Hoạt động ổn định)

---

## 🔍 1. Nhật ký Sự cố Kỹ thuật (Technical Incident Tracking)
### **Sự cố 4: Validator Stalled & Watcher Price Feed Error**
- **Thời điểm:** Phát hiện lúc 25/02/2026 - 08:20 (GMT+7).
- **Hiện tượng:** Watcher báo lỗi TwelveData API Key không hợp lệ; Binance Feed bị lỗi kết nối tạm thời trên Cloud.
- **Biện pháp xử lý:** Cập nhật code `signal_watcher.py` sử dụng class `BinanceFeed` mạnh mẽ hơn.
- **Trạng thái:** ✅ Đã xử lý.

### **Sự cố 5: Frontend Data Fetch Failed & Validator Hang**
- **Thời điểm:** Phát hiện lúc 25/02/2026 - 09:00 (GMT+7).
- **Hiện tượng:** 
    - Web Dashboard báo lỗi "Failed to fetch" khi API Railway gặp sự cố 502.
    - Validator bị treo (Stall) do không có cơ chế Timeout khi gọi Database/Feed.
- **Biện pháp xử lý:** 
    - **Frontend:** Triển khai cơ chế **Hybrid API** (Railway + Supabase Fallback). Nếu Railway lỗi, web tự động chuyển sang đọc Supabase trực tiếp. (Đã áp dụng cho cả `quantix-live-execution` và `Telesignal`).
    - **Core:** Bổ sung **Timeout (10s)** cho tất cả yêu cầu Database trong `connection.py` và bộ lọc **Sanity Filter** (loại bỏ giá ảo/spikes) trong `BinanceFeed`.
    - **Giám sát:** Phát triển và triển khai **Dịch vụ Watchdog** mới để cảnh báo Telegram ngay lập tức nếu bất kỳ dịch vụ nào ngừng hoạt động quá 15 phút.
- **Trạng thái:** ✅ ĐÃ KHÔI PHỤC TOÀN BỘ (FULL RECOVERY).

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
