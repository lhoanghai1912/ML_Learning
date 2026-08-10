# Phần B — Chẩn đoán nguyên nhân

_Phần của [`EDA_FINDINGS.md`](./EDA_FINDINGS.md) — tóm tắt + dashboard đọc ở đó, đây là bản phân tích chi tiết đầy đủ của riêng phần này._


### Doanh thu khách mới vs khách cũ
**1. Hiện trạng — con số đáng báo động nhất toàn notebook**

| Năm | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2022 |
|---|---|---|---|---|---|---|---|---|
| % doanh thu từ khách cũ | 66.1% | 83.4% | 89.3% | 92.3% | 93.8% | 94.7% | 95.6% | **96.4%** |
| Doanh thu khách mới (tỷ) | 0.562 | 0.312 | 0.202 | 0.163 | 0.119 | 0.099 | 0.050 | **0.042** |
| Số khách mua lần đầu | 25,099 | 13,293 | 8,828 | 6,392 | 4,789 | 3,717 | 1,898 | **1,322** |

Số khách mua lần đầu giảm **−94.7%** (25,099 → 1,322). Doanh thu từ khách mới giảm **−92.5%**.

**2. Nguyên nhân + phát hiện then chốt về thời điểm**
Đường "khách mới" (đỏ) **teo lại liên tục từ 2013**, tức **5–6 năm TRƯỚC** cú sụp doanh thu 2019. Trong khi đó tổng doanh thu vẫn tăng tới 2016 và chỉ giảm nhẹ 2017–2018.

Cơ chế: doanh nghiệp **sống bằng tệp khách cũ tích lũy** trong khi kênh nạp khách mới đã hỏng từ lâu. Tệp cũ có quán tính (khách cũ mua lặp lại nhiều năm) nên che giấu vấn đề — đến khi tệp này bão hòa/rời bỏ thì doanh thu sụp và **không có nguồn thay thế**.

Đây chính là câu trả lời cho câu hỏi "vì sao 2019 sụp": nguyên nhân đã được gieo từ 2014–2016, biến cố 2019 chỉ là thời điểm hệ thống mất khả năng bù đắp.

**3. Mối liên hệ**
- Khớp trực tiếp với ô **ASP vs Volume**: khách active giảm −28% (2018→2019), số đơn giảm −40.2%.
- Khớp với ô **RFM**: nhóm "New Customers" chỉ còn 4,865 khách (5.5%), trong khi "Lost" tới 21,682 (24.6%).
- ️ Cần đọc kèm cảnh báo ở ô **cohort retention**: trường `signup_date` trong `customers.csv` không phản ánh đúng thời điểm bắt đầu quan hệ khách hàng (xem phân tích ở đó), nên "khách mới" ở chart này được định nghĩa theo **ngày đơn hàng đầu tiên** — cách định nghĩa này đáng tin hơn `signup_date`.

**4. Hệ quả kéo theo**
- Ở mức 1,322 khách mới/năm so với ~24,700 khách active, **tỷ lệ nạp mới chỉ ~5.4%/năm** — thấp hơn nhiều so với tỷ lệ rời bỏ tự nhiên → tệp khách sẽ tiếp tục co lại về mặt cơ học.
- Doanh thu 96.4% phụ thuộc khách cũ = **rủi ro tập trung cực đại**: một cú sốc làm tệp cũ rời đi sẽ không có đệm nào.

**5. Dự đoán**
Nếu không có thay đổi về acquisition, tệp khách active tiếp tục giảm ~1–3%/năm (đúng như 2020→2022: 24,335 → 23,984 → 24,696, đã gần như đi ngang ở mức thấp). Doanh thu 2023–2024 do đó **khó vượt mức 2022** nếu chỉ dựa vào tăng ASP.

**6. Giới hạn**
"Khách mới" xác định bằng `min(order_date)` trên toàn bộ lịch sử. Với khách mua lần đầu năm 2012 (năm khuyết 6 tháng), phân loại có thể lệch nhẹ ở biên đầu chuỗi — không ảnh hưởng kết luận xu hướng.

### Waterfall: Gross booked → Net thực thu
**1. Hiện trạng (2013–2022)**
| Tầng | Giá trị | % Gross |
|---|---|---|
| Gross booked | **15.689 tỷ** | 100% |
| − Hủy đơn | −1.447 tỷ | **−9.2%** |
| − Chiết khấu | −0.681 tỷ | −4.3% |
| − Hoàn tiền | −0.511 tỷ | −3.3% |
| **= Net thực thu** | **13.050 tỷ** | **83.2%** |

Tổng hao hụt **16.8%**, trong đó **hủy đơn chiếm hơn một nửa**.

**2. Nguyên nhân — kiểm tra xem hao hụt có xấu đi theo thời gian không**
Tách theo năm cho thấy 3 tỷ lệ **cực kỳ ổn định**, không hề xấu đi:

| | 2013 | 2016 | 2018 | 2020 | 2022 | Biên độ |
|---|---|---|---|---|---|---|
| Hủy đơn % | 9.21 | 9.12 | 9.27 | 9.55 | 9.29 | **9.01–9.55** |
| Chiết khấu % | 4.77 | 3.99 | 3.96 | 4.19 | 4.20 | 3.96–4.77 |

Biên độ dao động **dưới 0.6 điểm %** suốt 10 năm → đây là **hằng số của hệ thống**, gần như chắc chắn là tham số cố định của bộ sinh dữ liệu, **không phải** vấn đề vận hành đang xấu đi.

Phân bố `order_status` toàn kỳ: delivered 79.87%, cancelled **9.19%**, returned 5.59%, shipped 2.13%, paid 2.10%, created 1.12%.

**3. Mối liên hệ**
- Vì tỷ lệ hủy/chiết khấu **không đổi**, chúng **không thể** là nguyên nhân của cú sụp doanh thu 2019 → loại trừ thêm một giả thuyết, củng cố kết luận "nguyên nhân là mất khách/khối lượng" ở ô ASP‑Volume.
- `sales.csv` (target Phần B) = **GROSS**, tức tính cả đơn cancelled → nhánh "− Hủy đơn" **không ảnh hưởng** con số cần dự báo. Đây là điểm dễ nhầm nhất khi làm Phần B.

**4. Hệ quả kéo theo**
- Nếu muốn cải thiện, hủy đơn (1.447 tỷ) là đòn bẩy **lớn gấp 3 lần** floor‑pricing (0.462 tỷ ở Phần 4) — nhưng notebook này không có dữ liệu **lý do hủy**, nên không thể đề xuất hành động cụ thể. Đây là khoảng trống dữ liệu đáng chú ý nhất.
- 39,939 lượt hoàn tiền, refund trung vị 7,889đ / trung bình 12,785đ → phân bố lệch phải (một số đơn hoàn giá trị lớn kéo trung bình lên).

**5. Dự đoán**
Với tỷ lệ ổn định như trên, Net 2023–2024 ≈ **83.2% của Gross dự báo**, sai số kỳ vọng dưới ±0.6 điểm %.

**6. Giới hạn**
Refund lấy từ toàn bộ `returns.csv` (không lọc năm 2013–2022 như 2 tầng kia) → tầng "− Hoàn tiền" **không hoàn toàn cùng phạm vi thời gian** với 2 tầng trước. Với 39,939 dòng trải đều toàn kỳ, sai lệch nhỏ, nhưng con số 3.3% nên đọc là xấp xỉ.

### ️ Phân tích chi tiết — AOV: đơn có promo vs không promo
**1. Hiện trạng — kết quả ngược trực giác**
- AOV **không** promo: **27,945 VND** (366,921 đơn)
- AOV **có** promo: **21,896 VND** (248,242 đơn) → **thấp hơn 21.6%**

Tỷ lệ dòng hàng có promo toàn kỳ: **40.77%**.

**2. Nguyên nhân — cần cẩn thận, đây KHÔNG phải "promo làm giảm giá trị đơn"**
Ba cơ chế đều có thể tạo ra kết quả này, và dữ liệu hiện có **không tách được** chúng:
1. **Hiệu ứng cơ học của chiết khấu**: promo giảm giá bán → `quantity × unit_price` nhỏ đi dù mua cùng số lượng. Bằng chứng ủng hộ: tỷ lệ `unit_price/cogs` trung vị chỉ **1.014 khi có promo** so với **1.221 khi không promo** — hàng promo bán gần như đúng giá vốn.
2. **Thiên lệch lựa chọn (selection bias)**: promo áp cho SKU giá rẻ / mua bốc đồng, đơn giá trị cao vốn dĩ không cần promo.
3. **Artifact của cách nhóm**: đơn *vừa có vừa không có* dòng promo bị tách làm 2 "đơn" riêng (theo `groupby(["order_id","has_promo"])`), nên đây **không phải AOV theo đúng nghĩa** giá trị đơn hàng.

Lý do 1 có bằng chứng số trực tiếp; lý do 3 là hạn chế phương pháp đã biết. **Không kết luận nhân quả.**

**3. Mối liên hệ**
- Tỷ lệ dòng có promo dao động theo chu kỳ chẵn/lẻ đúng như margin: **năm lẻ 44.4–46.5%**, **năm chẵn 33.6–37.3%** → thêm một xác nhận cho cơ chế "Urban Blowout chỉ chạy năm lẻ".
- Kết nối trực tiếp với ô below‑cost kế tiếp: promo là điều kiện gần như cần để bán dưới giá vốn.

**4. Hệ quả kéo theo**
Promo hiện đang **vừa giảm giá trị đơn vừa tạo lỗ gộp** (xem ô sau) mà **không có bằng chứng nào trong dữ liệu cho thấy nó tăng khối lượng bù lại** — số đơn có promo (248K) ít hơn không promo (367K). Đây là tổ hợp xấu nhất có thể.

**5. Dự đoán**
Nếu cắt các chương trình `fixed` sâu (Urban Blowout), AOV trung bình toàn shop sẽ tăng và margin tăng ~2.4 điểm % (xem ô floor‑price) — **với điều kiện** khối lượng không giảm. Rủi ro: dữ liệu hiện có **không cho phép ước lượng độ co giãn cầu theo giá**, nên đây là giả định chưa kiểm chứng được.

**6. Giới hạn**
Như lý do 3 ở trên — chỉ tiêu này giữ nguyên cách tính của báo cáo gốc để đối chiếu số (27,945 / 21,896), **không sửa** cho "đúng" hơn. Muốn AOV đúng nghĩa cần nhóm theo `order_id` rồi mới gán nhãn có/không promo ở cấp đơn.

### Q1: ASP vs Volume (index 2018 = 100)
**1. Hiện trạng — trả lời dứt điểm câu hỏi "vì sao 2019 sụt"**

| Chỉ số 2018→2019 | Thay đổi |
|---|---|
| Revenue | **−38.6%** |
| **ASP (giá bán TB)** | **+2.4%** ⬆️ |
| Qty (số lượng bán) | **−40.0%** |
| Số đơn | **−40.2%** |
| Khách active | −28.0% |

**ASP TĂNG trong khi doanh thu giảm 38.6%** → loại trừ hoàn toàn giả thuyết "giảm giá/chiến tranh giá". Toàn bộ sụt giảm đến từ **khối lượng**.

**2. Phân tích sâu hơn — có 2 lớp, không phải 1**
Số đơn giảm **−40.2%** nhưng khách active chỉ giảm **−28.0%**. Chênh lệch 12 điểm % này có nghĩa: **khách còn ở lại cũng mua ít lần hơn**.

Kiểm chứng bằng số đơn/khách/năm: đỉnh **2.025 (2015)** → 1.833 (2018) → **1.523 (2019)** → **1.458 (2022)**, giảm **−28%** so đỉnh. Số lượng sản phẩm mỗi đơn cũng giảm đều nhưng nhẹ: 5.108 (2013) → 4.752 (2022), −7%.

Vậy cú sụp gồm 2 tầng cộng dồn: **mất 28% số khách** × **mỗi khách mua ít hơn 17%**.

**3. Xu hướng dài hạn — bức tranh còn rõ hơn**
| | 2013 | 2016 | 2018 | 2022 | Tổng |
|---|---|---|---|---|---|
| ASP (VND) | 4,222 | 5,135 | 5,479 | **6,837** | **+62.0%** |
| Qty | 392,522 | 409,893 | 337,646 | **171,088** | **−56.4%** |
| AOV (VND) | 21,564 | 25,589 | 26,617 | **32,489** | **+50.7%** |

Giá tăng liên tục **62%** trong khi khối lượng giảm **56%** suốt 10 năm — đây là xu hướng **dài hạn**, không phải sự kiện riêng của 2019. 2019 chỉ là năm nó tăng tốc đột ngột.

**4. Mối liên hệ**
- Nguồn gốc thực nằm ở ô **khách mới vs khách cũ**: khách mua lần đầu đã cạn dần từ 2013 (25,099 → 3,717 vào 2018) — tức "kho" khách để chuyển thành khách active đã rỗng trước khi số khách active bắt đầu rơi.
- Loại trừ được nguyên nhân theo kênh (mọi kênh giảm đều), theo vùng (mọi vùng giảm), theo tuổi (mọi nhóm giảm).

**5. Dự đoán / hàm ý cho Phần B**
- 2020→2022 các chỉ số đã **ổn định ở mặt bằng thấp** (khách active 24.3K → 24.0K → 24.7K; qty 167K → 165K → 171K) → hệ đã tìm được điểm cân bằng mới.
- Dự báo 2023–2024 nên giả định **đi ngang quanh mức 2022**, với rủi ro nghiêng nhẹ về phía tăng (2022 đã +12.1% YoY nhờ ASP +8.0% và qty +3.9%).

**6. Giới hạn**
ASP = Revenue/Qty là **giá bình quân gia quyền**, chịu ảnh hưởng của thay đổi cơ cấu sản phẩm (mix effect). ASP tăng 62% có thể do bán nhiều hàng đắt hơn chứ không do tăng giá từng món — notebook chưa tách được 2 hiệu ứng này (cần phân tích price‑mix decomposition ở cấp SKU).

### Q2: Tỷ lệ bán dưới giá vốn theo category
**1. Hiện trạng — con số gây sốc nhất**
| | % dòng bán dưới giá vốn |
|---|---|
| Dòng **CÓ** promo | **47.86%** |
| Dòng **KHÔNG** promo | **0.18%** |

Chênh nhau **266 lần**. Gần một nửa số dòng hàng có khuyến mãi đang bán lỗ.

Theo category: Casual **22.30%** (23,352 dòng), Streetwear **21.36%** (377,723 dòng), Outdoor 18.10% (240,740), GenZ 9.83% (35,847).

**2. Nguyên nhân — truy tới từng chương trình khuyến mãi cụ thể**
Không phải mọi promo đều như nhau. Tách theo `promo_type`:

| Loại promo | Số dòng | % dưới giá vốn | Giá bán / giá vốn (trung vị) |
|---|---|---|---|
| `fixed` (**Urban Blowout**) | 20,950 | **99.65%** | **0.596** |
| `percentage` (còn lại) | 255,366 | 43.61% | 1.04 |

**"Urban Blowout" bán lỗ gần như 100% số dòng, ở mức chỉ bằng 59.6% giá vốn.** Nguyên nhân cơ chế: `discount_value = 50` là **số tiền tuyệt đối**, áp lên nhóm hàng Streetwear có giá đơn vị thấp → chiết khấu vượt cả biên lãi lẫn giá vốn. Trong khi `percentage` (10–20%) chỉ ăn vào biên lãi.

**Phân bố theo tháng** khớp hoàn hảo với lịch chạy các chương trình:
| Tháng | T5 | T10 | T1 | T8 | T7 | T9 | **T12** |
|---|---|---|---|---|---|---|---|
| % dòng có promo | **0.00** | 3.95 | 8.05 | 29.71 | 61.92 | 93.92 | **99.60** |
| % dưới giá vốn | 0.20 | 1.52 | 4.15 | 29.23 | 31.93 | 34.93 | **47.29** |
| margin tháng | **+19.95** | +19.57 | +18.82 | **−0.14** | +8.89 | +9.95 | **+0.74** |

Tương quan giữa % dòng bán dưới giá vốn và margin tháng: **r = −0.89** (gần như tuyến tính hoàn hảo). Với % có promo: r = −0.67.

**T8 tách chẵn/lẻ** là bằng chứng cuối cùng: năm chẵn **0.41%** dưới giá vốn, năm lẻ **57.21%** — chênh 140 lần, đúng bằng sự hiện diện/vắng mặt của Urban Blowout.

**3. Mối liên hệ**
Đây là mảnh ghép cuối khép kín chuỗi nhân quả đã lần theo từ đầu notebook:
> `promo fixed 50` → bán dưới giá vốn 99.65% → margin T8 năm lẻ −34.5% → 5/7 tháng margin âm toàn lịch sử → biến động T8 std 2.15 trong hình dạng mùa vụ.

**4. Hệ quả kéo theo**
- **Casual có % lỗ cao nhất (22.30%) nhưng chỉ 23,352 dòng**; **Streetwear 21.36% trên 377,723 dòng** → về số tuyệt đối, Streetwear gây ra **~88% tổng thiệt hại** (xem định lượng ở ô floor‑price Phần 4). Xếp hạng theo % gây hiểu nhầm về mức độ ưu tiên.
- Đòn bẩy đúng **không phải "sửa category"** mà là **"sửa cơ chế promo `fixed`"** — chỉ 5 chương trình trong 50.

**5. Dự đoán**
- 2023 là năm **lẻ** → Urban Blowout 2023 (nếu bộ dữ liệu giữ quy luật) sẽ lại kéo T8/2023 xuống margin âm ~−35%.
- Nếu đổi 5 chương trình `fixed` sang `percentage 20%`, ước tính từ ô floor‑price: thu hồi khoảng **0.41 tỷ VND** riêng ở Streetwear.

**6. Giới hạn**
`below_cost` so `unit_price` với `cogs` ở cấp **dòng hàng**, chưa tính chi phí chung/vận chuyển → đây là lỗ gộp (gross), **không phải** lỗ ròng. Ngoài ra một số chiến lược bán lỗ có chủ đích (loss leader) có thể hợp lý nếu kéo được đơn kèm — dữ liệu hiện có không kiểm chứng được điều này.
---

