# 🏁 CHECKPOINT: Unified Signal Lifecycle & Hard-Lock Anti-Burst
**Date:** 2026-02-03 21:15 (VN Time)
**Status:** PRODUCTION READY 🔒

## 1. 🔄 Unified Signal Lifecycle (9-Step Workflow)
- **Standardized States:** `DETECTED` -> `PUBLISHED` -> `ENTRY_HIT` -> `CLOSED`.
- **Database First:** Signals are saved as `DETECTED` before any public broadcast.
- **Telegram Anchor:** Public signals are linked via `telegram_message_id`.
- **Threaded Audit Trail:** State transitions (`ENTRY_HIT`, `TP_HIT`, `SL_HIT`, `CANCELLED`) are sent as **Replies** to the original Telegram message.

## 2. 🛡️ Anti-Burst Rule (Hard Lock implementation)
- **Hard Lock:** Chặn tuyệt đối việc bắn tín hiệu mới nếu đang có tín hiệu cùng cặp (Asset) và khung thời gian (Timeframe) ở trạng thái `PUBLISHED` hoặc `ENTRY_HIT`.
- **Cooldown:** Duy trì khoảng nghỉ 30 phút giữa các lần bắn tín hiệu.
- **Daily Cap:** Giới hạn 5 tín hiệu/ngày để đảm bảo chất lượng và tránh spam.

## 3. 🛠️ Technical Fixes & Reliability
- **Centralized Settings:** Khắc phục lỗi crash `AttributeError` bằng cách đưa `TELEGRAM_ADMIN_CHAT_ID` vào `Settings` và chuẩn hóa toàn bộ các module sử dụng chung file cấu hình.
- **Fail-Fast Init:** Notifier sẽ báo lỗi ngay lập tức nếu thiếu cấu hình thay vì im lặng crash lúc runtime.
- **Cleanup:** Đã dọn dẹp toàn bộ tiến trình chạy ngầm tại local để tránh tình trạng "Duplicate Signals" trên Cloud (Railway).

## 4. ✅ Verification Status
- **E2E Test:** Đã chạy script test toàn diện vòng đời (PROFIT, LOSS, EXPIRED, DETECTED_ONLY) thành công 100%.
- **Nhãn [TEST]:** Tự động thêm tiền tố `[TEST]` cho các tín hiệu thử nghiệm.
- **Sync:** Database, Telegram và Website đã đồng bộ hóa hoàn toàn theo logic mới.

---
**Next Step:** Monitor live performance on Railway and wait for market setups.
