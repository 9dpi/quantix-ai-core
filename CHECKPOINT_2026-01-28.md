# Quantix AI Core - Checkpoint 2026-01-28
## Tình trạng dự án: Đã thông dữ liệu Real-time & Cloud Residency

### 1. Mục tiêu đã hoàn thành (Session Summary)
- **Dữ liệu thực tế 100%**: Đã dọn dẹp toàn bộ dữ liệu Mock/Test. Miner hiện đang đào giá thực từ Twelve Data (EURUSD M15).
- **Hóa Mây (Cloud Migration)**: 
    - Tạo bảng `fx_analysis_log` trên Supabase.
    - Chuyển đổi toàn bộ "Bộ não học tập" từ lưu trữ file local sang Database Cloud. 
    - Đảm bảo dữ liệu không bao giờ bị reset về 0 nữa.
- **Tự động hóa thông báo (Auto-Broadcast)**:
    - Bot Telegram đã được kết nối với Group cộng đồng (`-1003211826302`).
    - Thiết lập giao thức **ULTRA Signal (>95% confidence)**: Tự động nổ bản tin không giới hạn số lượng.
    - Thiết lập giao thức **ACTIVE Signal (>=75%)**: Tự động thông báo và tuân thủ giới hạn 1 lệnh/ngày.
- **Sửa lỗi Schema**: Đồng bộ các cột dữ liệu giữa Python và Supabase (`explainability`).
- **Bảo hiểm hệ thống**: Tạo công cụ `CREATE_SNAPSHOT.py` giúp đóng gói toàn bộ dự án (Code + Config + Data) thành file ZIP.

### 2. Thông số kỹ thuật hiện tại
- **Database**: Supabase (Bảng: `fx_signals`, `fx_analysis_log`).
- **Telegram Group ID**: `-1003211826302`.
- **Dữ liệu học tập**: Đã tích lũy >53 mẫu thực tế đầu tiên.
- **Tỉ lệ làm mới**: 120 giây (Miner) / 30 phút (Auto-push Dashboard).

### 3. Triết lý vận hành đã thống nhất
- **Confidence**: Trả lời câu hỏi "Phe nào áp đảo?"
- **Entry**: Trả lời câu hỏi "Ở mức giá nào thì cam kết kích hoạt?"
- **TP/SL**: Là hệ quả tất yếu của cấu trúc thị trường để quản trị rủi ro.

### 4. Kế hoạch tiếp theo (Tăng cường Confidence)
- **Multi-Timeframe (MTF)**: Kiểm tra thêm khung H1/H4 để xác nhận xu hướng M15.
- **Momentum Filter**: Tích hợp RSI/ATR để lọc các cú phá vỡ yếu.
- **Session Filter**: Ưu tiên bắt tín hiệu trong phiên London/New York.

---
*Lưu ý: Để khôi phục hoàn toàn, hãy sử dụng File ZIP trong thư mục `/snapshots`.*
