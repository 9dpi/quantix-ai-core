# Quantix AI Confidence Formula 

Hệ thống tính toán AI Confidence qua hai lớp lọc (Two-Layer Scoring System) để đảm bảo tín hiệu không chỉ mạnh về kỹ thuật mà còn an toàn về bối cảnh thị trường.

## 1. Tầng 1: Raw AI Confidence (Technical Analysis)
Điểm số này do `StructureEngineV1` tính toán dựa trên cấu trúc thị trường tại khung M15.

### Bảng thành phần điểm (Evidence Scoring)
| Thành phần | Trọng số / Logic | Ý nghĩa |
| :--- | :--- | :--- |
| **Base Score** | BOS: 0.6 \| CHoCH: 0.5 \| Swing Break: 0.4 | Điểm nền tảng theo loại sự kiện cấu trúc. |
| **Strength** | `0.5 + (Body_Strength * 0.3) + Close_Bonus(0.2)` | Lực nến (thân nến dài và đóng cửa qua cản). |
| **Quality** | `0.7 + Body_Boost(±0.2)` | Độ "sạch" và dứt khoát của pha phá vỡ. |
| **Effective Score** | `Base Score * Strength * Quality` | Điểm hiệu quả của từng bằng chứng đơn lẻ. |

### Công thức Final Raw Confidence
> **`Raw Confidence = |Bullish_Score - Bearish_Score| / (Total_Score)`**
*Giá trị này thể hiện mức độ áp đảo của một phe so với phe còn lại.*

---

## 2. Tầng 2: Release Confidence (Market Context Filter)
Đây là điểm số cuối cùng được ghi vào Database và hiển thị lên Telegram/Web (IMMUTABLE RULE).

### Công thức tổng quát (Refinement)
> **`Release Score = Raw AI Confidence × Session Weight × Spread Factor × Volatility Factor`**
*(Lưu ý: Kết quả được giới hạn tối đa là 100%)*

### Bảng hệ số Refiner
| Hệ số | Giá trị | Điều kiện áp dụng |
| :--- | :--- | :--- |
| **Session Weight** | **1.2** | **Giờ vàng:** London & New York Overlap (13:00 - 17:00 UTC). |
| | **1.0** | **Giờ chuẩn:** Phiên London (Từ 06:00 UTC). |
| | **0.8** | **Giờ rủi ro:** Phiên Á hoặc ngoài giờ thanh khoản cao. |
| **Spread Factor** | **0.5** | **Phí cao:** Khung giờ Rollover (21:00 - 23:00 UTC). |
| | **1.0** | **Bình thường:** Thanh khoản ổn định. |
| **Volatility Factor**| **1.0** | Dựa trên ATR (Hiện tại duy trì baseline 1.0). |

---

## 🚦 Quy tắc Duyệt Tín hiệu (The Gatekeeper)

Hệ thống chỉ thực hiện **RELEASE** (Phát bản tin) khi và chỉ khi:
1. **Release Confidence ≥ 65% (0.65)**.
2. Không có tín hiệu nào đang Active (Anti-Burst Rule).
3. Hết thời gian cooldown (30 phút từ tín hiệu trước).

### Ví dụ minh họa
* **Trường hợp A:** AI phân tích cực mạnh (**Raw 85%**) nhưng phát hiện lúc **9h sáng VN (Phiên Á)**.
  * Tính toán: `0.85 * 0.8 = 0.68` (68%) → **Đạt điều kiện Release**.
* **Trường hợp B:** AI phân tích trung bình (**Raw 70%**) nhưng vào **Giờ Vàng (15h VN)**.
  * Tính toán: `0.70 * 1.2 = 0.84` (84%) → **Release với độ tin cậy ưu tiên cao**.

---
*Tài liệu này là một phần của Rules v3.1 – Tuyệt đối tuân thủ Immutable Rule.*
