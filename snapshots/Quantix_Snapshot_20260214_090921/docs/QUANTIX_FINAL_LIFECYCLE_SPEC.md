# 🔁 QUANTIX SIGNAL LIFECYCLE WORKFLOW (FINAL)

## Mục tiêu
Đảm bảo Telegram tự động kể trọn vòng đời của 1 signal, giúp người xem biết rõ:
1. Có vào lệnh không? (Entry Hit)
2. Kết quả là thắng hay thua? (TP hay SL)
3. Không cần giải thích thêm, minh bạch tuyệt đối qua Live Audit Trail.

---

## 🧩 TỔNG QUAN TRẠNG THÁI
**DETECTED** → **PUBLISHED** → **ENTRY_HIT** → **CLOSED** (với Result là TP/SL/Cancelled)

---

## 🛠 CHI TIẾT 9 BƯỚC THỰC THI

### Bước 1 – Market Scan (Continuous)
- **Chu kỳ:** 120 giây.
- **Dữ liệu:** 100 nến M15 (EURUSD) từ TwelveData [T0].
- **Mục đích:** Tìm kiếm setup kỹ thuật liên tục.

### Bước 2 – Structure Reasoning (AI Core)
- **Phương pháp:** Deterministic (không ML) để tránh sai số.
- **Logic:** Phân tích Pivot / BOS / CHoCH / Fake breakout filter.
- **Đầu ra:** 
  - `raw_confidence` ∈ [0,1]
  - `direction` (BUY / SELL)

### Bước 3 – Release Scoring (Anti-Spam Filter)
- **Công cụ:** `ConfidenceRefiner`.
- **Điều kiện:** Chỉ xét trong phiên London / London-NY overlap (Thanh khoản cao).
- **Công thức:** `release_score = raw_confidence × session_weight × volatility_factor`.
- **Ngưỡng:** Nếu `release_score ≥ 0.75` -> Chuyển sang bước phát hành.

### Bước 4 – Trade Plan Calculation
- **Phương pháp:** Future-based (chờ giá hồi về).
- **Entry:** Cách giá hiện tại 5 pips (Vùng an toàn).
- **TP / SL:** Cố định 10 pips (R:R 1:1, bảo vệ tài khoản tối đa).

### Bước 5 – SAVE CANDIDATE (Audit First)
- **Hành động:** Lưu vào Database ngay khi phát hiện.
- **Trạng thái:** `status = DETECTED`.
- **Mục đích:** Bằng chứng AI đã thấy setup ngay cả khi Telegram gặp sự cố.

### Bước 6 – PUBLISH SIGNAL (Telegram #1)
- **📢 FIRST SIGNAL:** Gửi thông báo "WAITING FOR ENTRY".
- **Nội dung:** Asset, Direction, Entry, TP/SL, Confidence, Timestamp.
- **Cập nhật DB:** `status = PUBLISHED`, gán `telegram_message_id`.
- **Ý nghĩa:** Đây là Public Anchor – Điểm mốc không thể sửa đổi.

### Bước 7 – ENTRY WATCHER (Realtime Monitor)
- **Hành động:** Theo dõi giá thị trường từng giây.
- **Khi giá chạm Entry:** 
  - **🔔 Telegram #2:** Trả lời (Reply) tin nhắn cũ: "ENTRY CONFIRMED ✅".
  - **Cập nhật DB:** `status = ENTRY_HIT`, ghi lại thời gian khớp lệnh.

### Bước 8 – OUTCOME WATCHER (Final Result)
- **Hệ thống theo dõi:**
  - 🟢 **Nếu chạm TP:** Telegram #3: "TAKE PROFIT HIT ✅". `status = CLOSED`, `result = PROFIT`.
  - 🔴 **Nếu chạm SL:** Telegram #3: "STOP LOSS HIT ❌". `status = CLOSED`, `result = LOSS`.
  - ⚠️ **Nếu hết hạn (Expiry):** Telegram #3: "SIGNAL EXPIRED (No Trade)". `status = CLOSED`, `result = CANCELLED`.

### Bước 9 – CYCLE END
- Signal được đóng vĩnh viễn.
- Không cập nhật thêm bất kỳ dữ liệu nào.
- Dữ liệu trên Telegram và trang History khớp 1:1.

---

## 🎯 KẾT QUẢ ĐẠT ĐƯỢC
- ✅ **Tự động hóa hoàn toàn.**
- ✅ **Telegram = Live Audit Trail (Chuỗi bằng chứng sống).**
- ✅ **Báo cáo Win-rate thực tế, không cần quảng cáo.**
