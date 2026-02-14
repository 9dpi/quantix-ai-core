# 📄 BÁO CÁO KỸ THUẬT: HỆ THỐNG QUANTIX AI CORE (V1.0)
**Dành cho mục đích nhân bản & phát triển dự án mới**

---

## 1. TỔNG QUAN HỆ THỐNG (SYSTEM OVERVIEW)
Quantix AI Core là một nền tảng tạo và quản lý tín hiệu giao dịch Forex (mục tiêu chính: EUR/USD M15) dựa trên trí tuệ nhân tạo và mô hình dữ liệu cấu trúc. Hệ thống tuân thủ hai triết lý cốt lõi:
- **Database First:** Mọi dữ liệu phải được ghi vào DB trước khi công khai.
- **Telegram Proof:** Tín hiệu chỉ được coi là hợp lệ khi có bằng chứng (Message ID) trên Telegram.

## 2. KIẾN TRÚC HỆ THỐNG (ARCHITECTURE)
Hệ thống sử dụng mô hình **Decoupled-Cloud (Chia tách dịch vụ)** để đảm bảo tính ổn định và khả năng mở rộng:

1.  **Quantix_API_Server (Web):** Cổng giao tiếp REST API (FastAPI/Uvicorn). Phục vụ dữ liệu cho Dashboard và các App di động.
2.  **Quantix_Analyzer (Worker 1):** Bộ não phân tích thị trường. Quét dữ liệu từ TwelveData, tính toán điểm tin cậy và tạo tín hiệu mới.
3.  **Quantix_Watcher (Worker 2):** Bộ phận thực thi vòng đời. Theo dõi biến động giá để xác nhận khớp lệnh (Entry), chốt lời (TP), cắt lỗ (SL) hoặc đóng lệnh quá hạn (Timeout).

## 3. CÁC THÀNH PHẦN CỐT LÕI (CORE COMPONENTS)

### 3.1. StructureEngineV1 (Bộ máy phân tích)
- **Chức năng:** Phân tích cấu trúc thị trường (Bullish/Bearish) và tính toán độ mạnh của xu hướng (Strength).
- **Đặc điểm:** Độ nhạy (Sensitivity) có thể điều chỉnh để lọc nhiễu.

### 3.2. ConfidenceRefiner (Bộ lọc tin cậy)
- **Công thức:** `Release Confidence = Raw Confidence × Session Weight × Volatility Factor × Spread Factor`.
- **Session Weight:** Ưu tiên khung giờ Overlap giữa London và New York (13:00 - 17:00 UTC) với hệ số nhân 1.2x.
- **Output:** Giới hạn tối đa 100% để đảm bảo tính logic cho người dùng.

### 3.3. ContinuousAnalyzer (Vòng lặp scan 24/7)
- **Anti-Burst Rule (Hard Lock):** Chỉ cho phép duy nhất một tín hiệu hoạt động tại một thời điểm để tối ưu hóa vốn.
- **Auto-Janitor (Fail-Safe):** Cơ chế tự động giải phóng "đường ống" sau mỗi 3 phút nếu phát hiện lệnh kẹt quá 35 phút (Pending) hoặc 95 phút (Active).

### 3.4. SignalWatcher (Quản lý vòng đời)
- **Touch Detection:** Thuật toán phát hiện giá chạm Entry/TP/SL dựa trên nến M15.
- **Atomic State Transitions:** Chuyển đổi trạng thái lệnh một chiều (WAITING -> ENTRY_HIT -> CLOSED) để tránh trùng lặp thông báo.

## 4. CHIẾN THUẬT GIAO DỊCH (TRADING STRATEGY)
- **Asset:** EUR/USD (M15).
- **Entry Logic:** Future Entry (Cách giá thị trường 5 pips) để đảm bảo lệnh chỉ khớp khi xu hướng thực sự xác nhận.
- **Risk management:** TP 10 pips, SL 10 pips (Tỷ lệ R:R cố định 1:1 cho MVP).
- **Time-based Exit:** Tự hủy lệnh nếu sau 30 phút không khớp, hoặc tự đóng lệnh sau 90 phút nếu đang chạy.

## 5. THIẾT KẾ CƠ SỞ DỮ LIỆU (DATABASE SCHEMA - SUPABASE)
Hệ thống sử dụng 2 bảng chính:
1.  **`fx_signals`:** Lưu giữ toàn bộ vòng đời tín hiệu (ID, trạng thái, giá vào/ra, Telegram ID, kết quả).
    - *Ràng buộc:* `result` chỉ nhận giá trị `PROFIT`, `LOSS`, `CANCELLED`.
2.  **`fx_analysis_log`:** Telemetry dữ liệu thô từ AI (Heartbeat), dùng cho mục đích hậu kiểm và huấn luyện AI trong tương lai.

## 6. QUẢN TRỊ VÀ VẬN HÀNH (TROUBLESHOOTING)
Hệ thống hỗ trợ quản trị từ xa 100% thông qua Bot Telegram:
- **`/log`:** Chẩn đoán sức khỏe hệ thống (Check DB, API, Invariants).
- **`/unblock`:** Lệnh khẩn cấp để giải phóng hệ thống khi bị kẹt tín hiệu cũ.
- **`/status`:** Báo cáo hiệu suất trong ngày (Số lần quét, số tín hiệu, tỉ lệ thắng).

## 7. CÔNG NGHỆ SỬ DỤNG (TECH STACK)
- **Ngôn ngữ:** Python 3.9+.
- **Database:** Supabase (PostgreSQL).
- **Dữ liệu thị trường:** TwelveData API.
- **Thông báo:** Telegram Bot API (Async Polling).
- **Môi trường:** Docker, Railway Cloud.

---
**Ghi chú cho dự án mới:** Để triển khai dự án tương tự cho một tài sản khác (Ví dụ: Vàng - XAU/USD), chỉ cần cập nhật `settings.py` và cấu trúc nến của `ConfidenceRefiner` mà không cần thay đổi kiến trúc cốt lõi.
