# MASTER_CONTEXT: Quantix AI Core DNA (v4.6.1)
> **Session State**: 2026-03-13 12:20 VN
> **Status**: 🟢 PRODUCTION STABLE - M5 SCALPING MODE (v4.6.1+)


## 1. Kiến trúc Tổng thể (Architecture)
Multi-Agent Cloud-Native Trading System:
- **Launcher (`start_railway_consolidated.py`)**: Gộp Web API, Analyzer, và Validator vào một tiến trình duy nhất. 
    - *Đặc điểm*: Thêm **Silence Watchdog** (Tự giết & restart nếu service im lặng > 15p).
- **Core Engine (`continuous_analyzer.py`)**: Chạy vòng lặp vô tận (Infinity Loop).
    - *Embedded Watcher*: Logic giám sát lệnh tích hợp trực tiếp, không chạy process rời.
    - *Janitor Sync*: Tự động dọn dẹp lệnh cũ ngay đầu mỗi chu kỳ.
- **MT4 Bridge**: `Signal_Genius.mq4` (v1.2.0) tương tác qua API `/mt4/signals/`.
    - *Optimization*: Tối ưu cho Mac Mini/macOS (WebRequest handling & Wine stability).

## 2. Trạng thái Hiện tại (Current State)
- **Done**:
    - **Open Flow Mode**: Gỡ bỏ hoàn toàn Daily Cap & Global Lock. Khớp lệnh ngay khi `Confidence >= 0.75`.
    - **Stability Fix**: Thêm `timeout` (30-60s) cho tất cả lệnh Subprocess (Git/API) để chống treo hệ thống.
    - **Mac Support**: Hoàn thiện tài liệu và EA v1.2.0 cho nhóm khách hàng dùng Mac Mini.
    - **Heartbeat Upgrade**: Log nhịp tim ngay đầu `run_cycle` để đảm bảo báo cáo liveness chính xác.
- **Bugs/Issues**:
    - *System Heartbeat Failures*: Đã fix tình trạng treo Analyzer dẫn đến [FAIL] status.
    - *Slow Git Push*: Đã fix bằng timeout trong `analyze_heartbeat.py`.

## 3. Stack Kỹ thuật & Quy ước
- **Backend**: Python 3.11, FastAPI, Loguru.
- **Data**: Supabase (PostgreSQL) + Local Audit (`.jsonl`).
- **Convention**:
    - *Status Mapping*: `PUBLISHED` -> `ENTRY_HIT` -> `TP_HIT` / `SL_HIT`.
    - *Folder Structure*: `backend/quantix_core/` (Lõi), `mt4_expert_advisor/` (EA), `docs/` (Tài liệu).

## 4. Logic Cốt lõi (Core Logic)
- **`run_cycle()`**: Nhịp tim hệ thống. Thực thi: Heartbeat -> Janitor -> MarketHours -> Analyze -> Learning Sync.
- **M5 Scalping Logic (v4.6.1)**: 
    - **Signal**: Khung M5 (100 nến) - Thích nghi cực nhanh với biến động ngắn hạn.
    - **Trend Filter**: Khung M15 (200 nến) - Đảm bảo trade thuận xu hướng trung hạn.
    - **H1 Trend**: Đã loại bỏ hoàn toàn để tránh hiện tượng "kẹt trend" lâu ngày.
- **Confidence Logic**: 2:1 R:R (10p TP / 5p SL). Điều kiện kích hoạt: `Confidence >= 0.75`.
- **`CalculateLotSize()`**: Trong EA, tính Lot theo % Equity (Mặc định 2.0% risk - Irfan Standard).

## 5. Mục tiêu Tiếp theo (Next Steps)
1. **Giao tệp khách hàng**: Gửi `Signal_Genius_AI_MT4_Package_v1.2.zip` cho khách hàng dùng Mac Mini.
2. **Monitor Open Flow**: Theo dõi hiện tượng "Signal Cluster" (nhiều lệnh cùng lúc) khi thị trường biến động mạnh.
3. **Audit Learning Data**: Kiểm tra hiệu quả của `analyze_heartbeat.py` sau khi thêm timeout.

---
**Hệ thống v4.6.0 hiện đã đạt trạng thái tự phục hồi (Self-Healing) nhờ Watchdog mới.** 🛡️
