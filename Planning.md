# Quantix AI Core - System Evolution Plan (Feb 2026)

## 📊 1. Hiện trạng Hệ thống (Current State - Feb 24, 2026)

Hệ thống đã hoàn thành giai đoạn chuyển đổi sang vận hành **100% Online (Railway Cloud)** và giải quyết xong các nút thắt về hạ tầng dữ liệu.

### 🎯 Mục đích Hệ thống (System Identity)
Quantix AI Core là một công cụ phân tích và thực thi tín hiệu giao dịch Forex (ưu tiên EURUSD) dựa trên trí tuệ nhân tạo. Hệ thống tập trung vào việc xác định các vùng cấu trúc thị trường (Market Structure) có xác suất thắng cao, sau đó giám sát và chứng thực kết quả một cách minh bạch và tự động hoàn toàn trên môi trường Cloud.

### ⚙️ Các Dịch vụ Phân tán (Distributed Services)
Hệ thống vận hành theo mô hình tách rời (Decoupled) với 4 dịch vụ chính:
*   **Analyzer (Bộ não):** Quét dữ liệu biểu đồ nến 15 phút (M15). Sử dụng thuật toán `StructureEngineV1` để tìm điểm Entry, TP, SL và tính toán độ tin cậy (Confidence).
*   **Watcher (Bộ thực thi):** Theo dõi giá thị trường mỗi 30-60 giây. Chịu trách nhiệm chuyển trạng thái lệnh (Khớp Entry, Chạm TP, Cắt lỗ) và gửi thông báo.
*   **Validator (Trọng tài):** Một luồng giám sát độc lập, sử dụng nguồn dữ liệu giá khác biệt để đối soát và ghi nhận "Trader Proof" (Bằng chứng giao dịch), đảm bảo tính minh bạch.
*   **Web API (Giao diện):** Cung cấp dữ liệu cho Dashboard và API công khai cho người dùng theo dõi trạng thái hệ thống.

### 📉 Cách thức & Quy tắc Tín hiệu (Signal Rules)
*   **Global Hard Lock:** Tại một thời điểm, chỉ có duy nhất **1 tín hiệu** được phép hoạt động (trạng thái Waiting hoặc Active). Điều này đảm bảo tính tập trung và quản lý rủi ro.
*   **Vòng đời tín hiệu (Cycle):**
    1.  `WAITING_FOR_ENTRY`: Tín hiệu vừa được phát, chờ giá chạm điểm vào. (Hiệu lực: 35 phút).
    2.  `ENTRY_HIT`: Giá chạm điểm vào, chuyển sang trạng thái hoặt động.
    3.  `CLOSED (TP/SL)`: Lệnh kết thúc có lợi nhuận hoặc thua lỗ.
    4.  `CANCELLED / EXPIRED`: Tín hiệu bị hủy nếu không khớp entry trong 35 phút hoặc vượt quá thời gian giao dịch tối đa (90 phút).
*   **Ngưỡng Tin cậy:** Chỉ phát tín hiệu khi điểm Confidence đạt từ **90%** trở lên.

### 📱 Hệ thống Thông báo Telegram (Telegram Messaging)
Hệ thống sử dụng Bot Telegram để giao tiếp thời gian thực:
*   **Tin nhắn Tín hiệu Mới:** Gửi đầy đủ thông số Entry, TP, SL, tỉ lệ Confidence và thời gian hiệu lực.
*   **Tin nhắn Cập nhật (Reply):** Bot tự động Reply (trả lời) chính tin nhắn tín hiệu gốc khi có biến động: "📍 ENTRY PRICE HIT", "✅ TAKE PROFIT HIT", hoặc "🛑 STOP LOSS HIT".
*   **Admin Control:** Hỗ trợ lệnh `/unblock` để giải phóng hệ thống thủ công trong trường hợp có sự cố nghẽn dữ liệu.

### ✅ Các thành tựu đã đạt được:
*   **Infrastructure:** Tách rời hoàn toàn khỏi Local Services. Analyzer, Watcher và Validator chạy độc lập trên Railway.
*   **Data Resilience:** Đã triển khai **Binance Proxy Feed** làm nguồn dữ liệu chính/dự phòng, giải quyết triệt để vấn đề cạn kiệt hạn ngạch (quota) của TwelveData.
*   **Monitoring Baseline:** Thiết lập cơ chế **Heartbeat (Nhịp tim)** cho tất cả các Worker để giám sát trạng thái sống/chết thông qua Database.
*   **Data Consistency:** Fix lỗi logic "Future Timestamp" và cơ chế "Zombie Janitor" để tự động dọn dẹp các tín hiệu bị kẹt.

### ⚠️ Các rủi ro còn tồn tại:
*   **Discovery Lag:** Khi một dịch vụ trên Cloud bị treo (Validator Stall), hệ thống không thông báo ngay cho quản trị viên, dẫn đến trễ dữ liệu trên Web.
*   **Data Integrity:** Chưa có bộ lọc nhiễu (Sanity Check) cho dữ liệu giá từ các Feed nguồn, dễ bị kẹt lệnh nếu giá có "spike" ảo.
*   **Visibility:** Admin chưa có Dashboard điều hành trực quan để theo dõi nhịp tim các worker theo thời gian thực.

---

## 🚀 2. Kế hoạch Nâng cấp (Upgrade Roadmap)

Mục tiêu: Chuyển đổi từ hệ thống "Tự động" sang hệ thống **"Tự vận hành (Semi-Autonomous) & Có tính kháng lỗi (Fault-Tolerant)"**.

### 🛠 Giai đoạn 1: Hệ thống Giám sát & Cảnh báo (Immediate)
*   **Dịch vụ Watchdog (Telegram Alert):** Xây dựng một worker siêu nhẹ chạy mỗi 5-10 phút để quét `fx_analysis_log`. Nếu dịch vụ nào mất nhịp tim > 15 phút, sẽ bắn cảnh báo đỏ vào Telegram Admin.
*   **Sanity Middleware:** Thêm lớp kiểm tra (Validation Layer) cho dữ liệu giá. Loại bỏ nến có Timestamp tương lai hoặc giá trị bất thường (outliers).

### 🧠 Giai đoạn 2: Trí tuệ hóa Vòng lặp (Short-term)
*   **Feedback Loop Integration:** Tự động lưu trữ kết quả Win/Loss của từng tín hiệu sau khi đóng. 
*   **AI Refinement:** Cập nhật bộ `ConfidenceRefiner` để tự động điều chỉnh ngưỡng Confidence dựa trên tỷ lệ thắng gần nhất của từng Strategy.

### 🖥️ Giai đoạn 3: Giao diện Trung tâm (Mid-term)
*   **Real-time Command Dashboard:** Nâng cấp `index.html` tích hợp WebSockets/Pooling để hiển thị:
    *   Trạng thái nhịp tim (Live/Stall) của 3 Worker chính.
    *   Biểu đồ giá Live có vẽ điểm Entry/TP/SL của lệnh đang chạy.
    *   Bảng nhật ký AI Thinking trực quan.

---

## 📅 3. Kế hoạch Thực thi (Action Plan - Tuần này)

| Nhiệm vụ | Trọng tâm | Trạng thái |
| :--- | :--- | :--- |
| **Deploy Watchdog** | Cảnh báo Telegram khi worker Cloud bị sập | ⏳ Chuẩn bị |
| **Sanity Filter** | Ngăn chặn lỗi thời gian tương lai/giá ảo | ⏳ Chuẩn bị |
| **Binance History** | Tối ưu hóa việc fetch nến M15 từ Binance | ✅ Hoàn thành |
| **Local Cleanup** | Loại bỏ toàn bộ file rác và bypass local | ✅ Hoàn thành |

---
*Báo cáo được lập bởi Quantix AI - Sẵn sàng thực thi theo yêu cầu của Engineer.*
