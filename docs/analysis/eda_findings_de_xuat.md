# Phần D — Đề xuất hành động

_Phần của [`EDA_FINDINGS.md`](./EDA_FINDINGS.md) — tóm tắt + dashboard đọc ở đó, đây là bản phân tích chi tiết đầy đủ của riêng phần này._


### ️ Phân tích chi tiết — Đề xuất 1: Floor price = giá vốn
**1. Hiện trạng**
- **714,669** dòng order_items toàn lịch sử, trong đó **133,052 dòng (18.62%)** bán dưới giá vốn.
- Margin hiện tại: **13.80%** (2.267 tỷ VND).
- Nếu áp sàn giá bằng giá vốn: **16.15%** (2.729 tỷ) → **+2.36 điểm %, +0.462 tỷ VND**.

**2. Phân rã theo category — chênh lệch cực lớn**
| Category | Doanh thu | Margin hiện tại | Margin sau floor | **Thu hồi được** | % tổng thu hồi |
|---|---|---|---|---|---|
| **Streetwear** | 13.131 tỷ | 13.24% | 15.86% | **+0.4088 tỷ** | **88.4%** |
| Outdoor | 2.495 tỷ | 16.37% | 17.73% | +0.0410 tỷ | 8.9% |
| Casual | 0.461 tỷ | 11.75% | 13.29% | +0.0082 tỷ | 1.8% |
| GenZ | 0.344 tỷ | 19.13% | 19.94% | +0.0035 tỷ | 0.8% |

**Streetwear một mình chiếm 88.4% giá trị thu hồi.** Lưu ý điều này **đảo ngược thứ hạng** so với chart "% dòng dưới giá vốn" (nơi Casual đứng đầu với 22.30%) — vì Casual chỉ có 23,352 dòng còn Streetwear có 377,723 dòng. **Ưu tiên hành động phải dựa trên số tuyệt đối, không dựa trên tỷ lệ %.**

**3. Nguyên nhân gốc — đã truy được ở Phần 2**
Nguồn lỗ tập trung ở 5 chương trình `promo_type = fixed` ("Urban Blowout", `discount_value = 50`, nhắm đúng Streetwear): 20,950 dòng với **99.65% bán dưới giá vốn**, giá bán chỉ bằng **59.6%** giá vốn. Vậy đề xuất "floor price" thực chất tương đương với đề xuất cụ thể hơn: **bỏ hoặc chuyển 5 chương trình `fixed` sang dạng `percentage`**.

**4. Mối liên hệ + so sánh độ lớn các đòn bẩy**
| Đòn bẩy | Giá trị | Ghi chú |
|---|---|---|
| Hủy đơn (waterfall) | **1.447 tỷ** | Lớn nhất, nhưng **chưa có dữ liệu lý do hủy** để hành động |
| **Floor pricing** | **0.462 tỷ** | Nguyên nhân đã truy rõ tới từng promo_id → **khả thi nhất** |
| Chiết khấu (waterfall) | 0.681 tỷ | Một phần trùng với floor pricing |
| Win‑back RFM | 0.033 tỷ | Nhỏ hơn **14 lần** |
| Pricing theo vùng | 0.038 tỷ | Nhỏ hơn **12 lần** |

Floor pricing là đề xuất có **tỷ lệ (độ lớn tác động ÷ độ chắc chắn của bằng chứng)** tốt nhất trong toàn bộ Phần 4.

**5. Dự đoán / điều kiện để con số này đúng**
+0.462 tỷ là **cận trên**, đạt được **chỉ khi khối lượng bán không đổi** sau khi nâng giá. Trên thực tế nâng giá từ 59.6% lên 100% giá vốn (+68%) gần như chắc chắn làm giảm lượng. Với các kịch bản co giãn cầu:
- Cầu không co giãn (lượng giữ nguyên): thu hồi **0.462 tỷ**
- Co giãn −0.5 (lượng giảm 34%): thu hồi ~**0.30 tỷ**
- Co giãn −1.0 (lượng giảm 68%): thu hồi ~**0.15 tỷ**, kèm mất doanh thu

️ Dữ liệu hiện có **không cho phép ước lượng độ co giãn thật** (không có thí nghiệm giá) → 3 con số trên là minh họa kịch bản, không phải dự báo.

**6. Giới hạn**
- Tính trên **toàn bộ lịch sử** (714,669 dòng, gồm cả 2012 và các đơn cancelled), **rộng hơn** phạm vi 2013–2022 dùng ở Phần 2 — nên tỷ lệ 18.62% ở đây khác với các số theo năm ở ô below‑cost.
- Chỉ tính lỗ **gộp** (chưa gồm chi phí vận hành/vận chuyển) → margin thực tế sau floor price sẽ thấp hơn 16.15%.
- Bỏ qua khả năng "loss leader" (bán lỗ để kéo đơn kèm). Nếu hiệu ứng này tồn tại, lợi ích ròng sẽ nhỏ hơn.

### Đề xuất 2: Win‑back theo RFM segment
**1. Hiện trạng**
| Segment | Số khách | AOV | +5pp | +10pp | +15pp |
|---|---|---|---|---|---|
| At Risk | **7,989** | 20,756đ | 8.29 tr | 16.58 tr | **24.87 tr** |
| Can't Lose Them | 2,251 | 25,393đ | 2.86 tr | 5.72 tr | **8.57 tr** |
| **Tổng** | 10,240 | — | 11.15 tr | 22.30 tr | **33.45 tr** |

**2. Đặt độ lớn vào đúng bối cảnh — điểm quan trọng nhất**
Kịch bản lạc quan nhất (+15pp cho cả 2 nhóm) mang lại **33.4 triệu VND**, tương đương:
- **0.20%** doanh thu 10 năm (16.43 tỷ)
- **2.9%** doanh thu một năm 2022 (1.170 tỷ)
- **7.2%** so với đề xuất floor pricing (0.462 tỷ) — **nhỏ hơn 14 lần**

> ️ *Đính chính:* bản phân tích trước của notebook này ghi nhầm tỷ lệ là "~0.0002%" — sai **1000 lần** do nhầm giữa tỷ số và phần trăm. Con số đúng là **0.20%**. Ghi lại để người đọc sau đối chiếu được.

**3. Nguyên nhân khiến quy mô nhỏ**
Hai nhóm mục tiêu có Monetary rất thấp: At Risk **0.646 tỷ (4.5% giá trị)**, Can't Lose Them **0.492 tỷ (3.5%)** — cộng lại chỉ **8.0%** tổng giá trị tệp khách. Dù có win‑back được **toàn bộ**, trần lý thuyết vẫn giới hạn ở mức đó.

**4. Rủi ro về giả định — recency quá xa**
- At Risk: recency trung bình **2,010 ngày (5.5 năm)**
- Can't Lose Them: recency trung bình **1,783 ngày (4.9 năm)**

Khách không mua gì trong ~5 năm về thực chất **đã rời bỏ**, không phải "có nguy cơ rời bỏ". Giả định uplift 5–15% cho nhóm này là **lạc quan đáng kể** so với benchmark win‑back thông thường (thường áp dụng cho nhóm rời bỏ 3–12 tháng). Nhãn segment do quy tắc R/F/M tạo ra, **không phản ánh khoảng cách thời gian thực tế**.

**5. Mối liên hệ + gợi ý mục tiêu tốt hơn**
Nếu mục tiêu là bảo vệ doanh thu, nhóm đáng chú ý hơn là **Champions** (22,575 khách, **62.9% giá trị**, recency trung bình 274 ngày ≈ 9 tháng). Giữ chân 1% Champions ≈ 89.5 triệu VND — **gấp 2.7 lần** toàn bộ kịch bản win‑back +15pp ở trên, với xác suất thành công cao hơn hẳn vì họ vẫn đang hoạt động.

**6. Dự đoán / khuyến nghị đọc số**
Giá trị thật của đề xuất win‑back **không nằm ở quy mô doanh thu** mà ở chi phí thử nghiệm thấp và khả năng học nhanh (test A/B trên 10,240 khách). Nên định vị nó là **thí nghiệm**, không phải sáng kiến tăng trưởng.

**7. Giới hạn**
- `uplift_scenario` 5/10/15pp là **giả định do người phân tích đặt ra**, không phải ước lượng từ dữ liệu — mọi con số ở đây đều là kịch bản có điều kiện.
- AOV dùng `monetary / frequency` (giá trị trung bình mỗi đơn trong quá khứ), giả định khách win‑back sẽ chi tiêu bằng mức cũ — cũng là giả định chưa kiểm chứng.

### ️ Phân tích chi tiết — Đề xuất 3: Nhân rộng pricing của vùng margin tốt nhất
**1. Hiện trạng**
| Vùng | Margin toàn phần | Doanh thu |
|---|---|---|
| **West** | **14.204%** | 3.669 tỷ |
| East | 13.305% | **7.289 tỷ** |
| Central | 13.148% | 4.731 tỷ |

Khoảng cách West vs Central chỉ **1.06 điểm %** — nhỏ hơn nhiều so với ấn tượng thị giác từ biểu đồ (trục y bị thu hẹp quanh vùng 13–14%).

**2. Kết quả kịch bản (60% khoảng cách margin)**
- Tổng thu hồi: **+0.038 tỷ VND**
- Margin toàn shop: 13.47% → **13.71%** (**+0.24 điểm %**)

Phân rã: Central‑Streetwear +0.0146 tỷ, East‑Streetwear +0.0126, East‑Outdoor +0.0069, Central‑Outdoor +0.0034, phần còn lại ~0.

**3. Phát hiện làm suy yếu chính đề xuất**
Xét theo từng category, West **không hề vượt trội toàn diện**:

| Category | West | East | Central | Vùng tốt nhất |
|---|---|---|---|---|
| Outdoor | **16.74%** | 15.37% | 15.72% | West  |
| Streetwear | **13.28%** | 12.93% | 12.67% | West  |
| Casual | **11.78%** | 11.31% | 11.59% | West  |
| GenZ | 18.28% | 18.83% | **19.95%** | **Central**  |

Ở **GenZ, West thấp nhất** (18.28% vs Central 19.95%) → khoảng cách âm, bị `clip(lower=0)` đưa về 0. Nghĩa là logic "West là hình mẫu" **không đúng với mọi category** — West thắng ở 3/4 nhóm với biên độ mỏng, và thua ở nhóm còn lại.

Vì sao West vẫn dẫn đầu tổng thể: West có **tỷ trọng Outdoor cao hơn** (0.946/3.669 = 25.8% doanh thu, so với East 11.5%), mà Outdoor là category margin cao (16–17%). Vậy phần lớn lợi thế của West đến từ **cơ cấu danh mục (mix effect)**, không phải từ năng lực định giá tốt hơn.

**4. Mối liên hệ + nghịch lý**
West có margin tốt nhất nhưng lại là vùng **suy giảm doanh thu nhanh nhất (−38.7%, CAGR −5.29%)** — xem ô doanh thu theo vùng. Điều này gợi ý West có thể đang **giữ giá cao và đánh đổi bằng khối lượng**, tức "hình mẫu" này chưa chắc đáng nhân rộng.

**5. So sánh độ lớn — kết luận thẳng**
| Đề xuất | Giá trị | So với đề xuất này |
|---|---|---|
| Floor pricing | 0.462 tỷ | **gấp 12.2 lần** |
| Win‑back RFM | 0.033 tỷ | tương đương |
| **Pricing theo vùng** | **0.038 tỷ** | — |

Với **+0.24 điểm % margin** và giả định nền (60% gap) không có căn cứ từ dữ liệu, đề xuất này **không đáng ưu tiên**. Nên xếp sau floor pricing và sau việc điều tra nguyên nhân hủy đơn (1.447 tỷ).

**6. Giới hạn**
- Hệ số **`PRICE_EFFECT_SHARE = 0.60`** ("60% chênh lệch margin là do giá") là **giả định do người phân tích đặt**, không ước lượng từ dữ liệu. Toàn bộ con số 0.038 tỷ tỷ lệ thuận trực tiếp với giả định này — chọn 0.3 thì kết quả giảm một nửa.
- Mô hình giữ nguyên doanh thu và chỉ hạ `cogs`, tức giả định **cải thiện margin đến từ mua hàng/chi phí tốt hơn** chứ không phải nâng giá bán. Nếu thực hiện bằng cách nâng giá, cần tính tới rủi ro mất khối lượng — mà West đang là ví dụ cảnh báo cho chính rủi ro đó.
---

