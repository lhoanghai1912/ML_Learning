# EDA Findings — Vin Datathon 2026

Tài liệu tổng hợp toàn bộ phân tích chi tiết EDA (Phần A), tách ra từ notebook để giữ notebook ngắn gọn. Notebook tương ứng (chỉ code + kết luận 1-3 câu/chart): `notebooks/02a_eda_thoi_vu.ipynb`, `02b_eda_nguyen_nhan.ipynb`, `02c_eda_khach_hang.ipynb`, `02d_eda_de_xuat.ipynb`.

Nguồn dữ liệu: 14 bảng raw CSV (`data/raw/`), `sales` qua Trino mart `mart_revenue_daily`. Coverage 2012-07-04 → 2022-12-31 (2012 chỉ nửa năm, không so YoY 2013). Mọi số trong tài liệu này verify được lại bằng cách chạy code cell tương ứng trong 4 notebook trên.

## Tóm tắt — 10 phát hiện chính

1. **Đỉnh doanh thu thật là 2016** (2.105 tỷ VND/năm), không phải 2018. Suy giảm bắt đầu **Quý 4/2018** (YoY tháng 10 -23.6%, tháng 11 -32.7%), không phải đột ngột 01/01/2019. 2022 mới hồi phục 63% mức đỉnh, chưa về lại quỹ đạo cũ.
2. **Nguyên nhân sụt giảm 2018→2019: 100% do khối lượng, không phải giá.** ASP tăng nhẹ +2.4% trong khi Revenue -38.6%; Qty -40%, số đơn/khách active -28%. Đồng đều trên mọi vùng/kênh/nhóm tuổi — cú sốc hệ thống, không phải 1 phân khúc cụ thể.
3. **Gốc rễ dài hạn: khách mới cạn dần từ 2013** — 5-6 năm TRƯỚC khi doanh thu sụt. Doanh nghiệp sống bằng tệp khách cũ tích lũy tới khi cạn (% doanh thu khách cũ: 66.1%→96.4%, 2013→2022).
4. **Chu kỳ khuyến mãi "Urban Blowout" (`fixed`, năm LẺ, Tháng 8) là nguyên nhân trực tiếp margin âm định kỳ** — 99.65% dòng hàng liên quan bán dưới giá vốn, giá bán chỉ 59.6% giá vốn. T8 năm chẵn margin +19.9%, năm lẻ -34.5%.
5. **Hiệu ứng Tết phần lớn là nhiễu trộn với mùa vụ** — top 5 ngày doanh thu cao nhất TOÀN KỲ đều rơi cuối T5-đầu T6 (mùa cao điểm), không phải ngày Tết nào. Mùa cao điểm thật: T4-T6; thấp điểm: T11-T1 (ngược mùa mua sắm cuối năm phương Tây).
6. **Giá trị khách hàng cực lệch (Pareto gắt)**: Champions 25.6% khách nắm 62.9% giá trị. Lost 24.6% khách (gần bằng Champions về số lượng) chỉ còn 3.2% giá trị.
7. **Bug dữ liệu nghiêm trọng đã phát hiện + fix**: `customers.signup_date` không phản ánh quan hệ mua bán thật (89.3% khách có đơn TRƯỚC ngày signup). Cohort retention tính trên trường này chỉ là base rate ngẫu nhiên (~3%), KHÔNG PHẢI retention thật. Đã fix ở tầng dbt (model song song `int_cohort_first_order`) — retention thật cao gấp ~2 lần số cũ.
8. **Đáy retention là hiệu ứng MÙA VỤ, không phải vòng đời khách hàng** — 10/12 nhóm cohort (83%) có đáy retention rơi đúng Tháng 1 dương lịch dù offset kể từ ngày mua đầu trải rộng 1-10 tháng tùy tháng bắt đầu.
9. **3 đề xuất định lượng, độ lớn chênh nhau rất xa**: floor-pricing (+0.462 tỷ VND) lớn hơn win-back (~0.033 tỷ) và đồng bộ pricing vùng (0.038 tỷ) khoảng 12-14 lần. Ưu tiên floor-pricing (sửa 5 chương trình khuyến mãi `fixed`) trước.
10. **Model forecast (Phần B) học đúng hướng** (dự báo đi ngang theo mức 2022, không ngoại suy tăng) nhưng có rủi ro cụ thể đã định lượng: T8/2023 (năm lẻ, đúng chu kỳ Urban Blowout) khả năng bị over-forecast vì `lag_365` tra về T8/2022 (năm chẵn, bình thường).

## Cách đọc tài liệu này

4 phần dưới đây map 1-1 với 4 notebook đã tách — mỗi mục là bản đầy đủ (hiện trạng/nguyên nhân/mối liên hệ/hệ quả/dự đoán/giới hạn) của đúng 1 chart trong notebook tương ứng. Notebook chỉ giữ code + 1-3 câu kết luận, phân tích sâu đọc ở đây.

---

## Phần A — Thời vụ & biến động theo thời gian

_Notebook: `notebooks/02a_eda_thoi_vu.ipynb`_

### Revenue theo ngày + MA30 (2012–2022)
**1. Hiện trạng đọc từ biểu đồ**
| Năm | 2012 | 2013 | 2014 | 2015 | **2016** | 2017 | 2018 | 2019 | 2020 | **2021** | 2022 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tổng (tỷ) | 0.741¹ | 1.657 | 1.872 | 1.890 | **2.105** | 1.911 | 1.850 | 1.137 | 1.055 | **1.043** | 1.170 |
| TB (tr/ngày) | 4.10 | 4.54 | 5.13 | 5.18 | **5.75** | 5.24 | 5.07 | 3.11 | 2.88 | **2.86** | 3.20 |
| YoY % | — | +123¹ | +13.0 | +1.0 | +11.4 | **−9.2** | **−3.2** | **−38.6** | −7.2 | −1.1 | **+12.1** |

¹ 2012 chỉ có 181 ngày (shop mở 04/07/2012) → YoY 2013 không so sánh được.

Đỉnh thật là **2016 (2.105 tỷ)**, không phải 2018. Đáy **2021 (1.043 tỷ)** = **−50.4%** so đỉnh.

**2. Nguyên nhân — SỬA LẠI cách đọc "break 2019"**
Nhìn MA30 dễ kết luận "gãy đột ngột đầu 2019". Kiểm chứng bằng YoY theo tháng cho thấy **KHÔNG phải vậy** — suy giảm bắt đầu từ **Quý 4/2018**:

| Tháng | 2018‑09 | 2018‑10 | 2018‑11 | 2018‑12 | 2019‑01 | … | 2019‑06 | 2019‑08 |
|---|---|---|---|---|---|---|---|---|
| YoY % | −12.6 | −23.6 | −32.7 | −26.8 | −19.8 | | −49.3 | **−58.1** |

Thêm nữa doanh thu đã **giảm 2 năm liên tiếp trước đó** (2017 −9.2%, 2018 −3.2%). Vậy chuỗi sự kiện đúng là: **đạt đỉnh 2016 → suy yếu 2017–2018 → tăng tốc sụp đổ từ Q4/2018 → chạm đáy 2021 → hồi nhẹ 2022**. Mốc "2019‑01‑01" chỉ là hiệu ứng thị giác do MA30 làm mượt và do trục năm.

**3. Mối liên hệ**
- Nguyên nhân định lượng nằm ở **ô "ASP vs Volume" (Phần 2 – Q1)**: sụt do **khối lượng**, không do giá.
- Nguồn gốc dài hạn nằm ở **ô "khách mới vs khách cũ"**: số khách mua lần đầu giảm liên tục **từ 2013**, tức 5 năm TRƯỚC khi doanh thu gãy — doanh thu còn giữ được tới 2016–2018 nhờ khách cũ mua tiếp, đến khi tệp cũ cạn thì sụp.

**4. Hệ quả kéo theo**
- 2022 hồi phục +12.1% nhưng vẫn chỉ bằng **63.2% mức 2018** và **55.6% mức đỉnh 2016** → chưa phải hồi phục thật, mới là nảy kỹ thuật từ đáy.
- Độ biến động (CV = std/mean) tăng dần 0.411 (2012) → **0.625 (2018)** rồi hạ về 0.523 (2022): giai đoạn trước sụp đổ là giai đoạn *bất ổn nhất*, phù hợp mô hình "hệ đang mất ổn định trước khi gãy".

**5. Dự đoán / hàm ý cho Phần B (forecast 548 ngày 2023‑01‑01 → 2024‑07‑01)**
- Mức nền hợp lý để neo dự báo là **2020–2022 (1.04–1.17 tỷ/năm ≈ 2.86–3.20 tr/ngày)**, KHÔNG phải trung bình 11 năm (4.29 tr/ngày) — dùng trung bình toàn kỳ sẽ **overestimate ~34–50%**.
- Xu hướng 2021→2022 là dương (+12.1%) nhưng chỉ 1 năm, chưa đủ xác nhận đảo chiều → dự báo nên **đi ngang quanh mức 2022**, không ngoại suy đà tăng.

**6. Giới hạn khi đọc**
- MA30 làm trễ tín hiệu ~15 ngày → mọi mốc thời gian đọc từ đường đỏ đều **lệch muộn**, phải đối chiếu YoY tháng như trên mới định vị đúng.
- Đây là dữ liệu **mô phỏng**; các mốc gãy phản ánh tham số bộ sinh dữ liệu, không nên diễn giải thành sự kiện kinh tế có thật.

### Doanh thu tháng & biên lãi gộp
**1. Hiện trạng**
Chỉ **7/126 tháng (5.6%) margin âm**, nhưng phân bố **không ngẫu nhiên chút nào**:

| Nhóm | Các tháng | margin_pct |
|---|---|---|
| Tháng 8 năm **LẺ** | 2013, 2015, 2017, 2019, 2021 | −30.68, −32.35, −35.39, −34.24, **−40.09** |
| Tháng 12 gần đây | 2021, 2022 | −2.07, −1.97 |

Margin trung bình theo tháng (toàn kỳ): cao nhất **T5 +19.87%**, **T10 +19.45%**, **T2 +18.89%**; thấp nhất **T8 −4.86%**, **T12 +2.40%**, T7 +9.86%, T9 +10.78%.

**2. Nguyên nhân — truy được tới tận dòng dữ liệu gốc**
Tách T8 theo năm chẵn/lẻ cho kết quả rất sạch:

| T8 | Revenue TB | COGS TB | margin |
|---|---|---|---|
| Năm **CHẴN** | 0.169 tỷ | 0.135 tỷ | **+19.87%** |
| Năm **LẺ** | 0.101 tỷ | 0.135 tỷ | **−34.55%** |

**COGS gần như y hệt nhau (0.135 tỷ)** — nghĩa là lượng hàng bán ra tương đương, chỉ có **doanh thu bị bốc hơi 40%**. Đây là dấu hiệu kinh điển của **bán phá giá**, không phải sụt cầu.

Truy vào bảng `promotions` tìm ra thủ phạm chính xác: chương trình **"Urban Blowout"** — `promo_type = fixed`, `discount_value = 50`, `applicable_category = Streetwear`, chạy **30/07 → 02/09** và **CHỈ tồn tại ở năm lẻ** (PROMO‑0005/0015/0025/0035/0045 tương ứng 2013/2015/2017/2019/2021). Trong 20,950 dòng gắn promo này, **99.65% bán dưới giá vốn**, giá bán trung vị chỉ bằng **0.596 lần giá vốn**. Chi tiết định lượng ở ô "tỷ lệ bán dưới giá vốn" (Phần 2 – Q2).

Tương tự với T12: `COGS/Revenue` = **0.98–1.02 ở MỌI năm** (không trừ năm nào) do chương trình "Year‑End Sale" (percentage 20%, 18/11 → 02/01) chạy hằng năm → T12 luôn hòa vốn, 2 năm gần nhất lỗ nhẹ.

**3. Mối liên hệ**
- Giải thích trực tiếp **T8 std = 2.15 điểm %** (cao gấp 3–4 lần các tháng khác) ở ô "hình dạng mùa vụ".
- Là nguồn gốc của **7 tháng chấm dưới trục 0** — đồng thời giải thích vì sao margin trung bình **năm lẻ luôn thấp hơn năm chẵn**: 2013 10.57%, 2015 10.35%, 2017 9.67%, 2019 10.30%, 2021 **8.14%** vs năm chẵn 14.74–20.74%.

**4. Hệ quả kéo theo**
- **Chu kỳ margin 2 năm** là hiện tượng có thật trong dữ liệu, không phải nhiễu — mọi mô hình chỉ dùng feature `month` sẽ **sai hệ thống ở T8**: dự báo trung bình giữa +19.9% và −34.5%, tức sai cả dấu ở mọi năm.
- COGS T8 KHÔNG giảm theo doanh thu → nếu forecast COGS bằng cách nhân Revenue với tỷ lệ cố định, T8 năm lẻ sẽ sai rất nặng.

**5. Dự đoán kiểm chứng được**
Horizon Phần B gồm **T8/2023 (năm LẺ)** và T8/2024 (năm chẵn). Nếu quy luật giữ nguyên:
- **T8/2023: Revenue ≈ 0.10 tỷ, COGS ≈ 0.135 tỷ → COGS > Revenue, margin ≈ −35%.**
- T8/2024: Revenue ≈ 0.17 tỷ, margin ≈ +20%.

Đây là dự đoán **có thể phủ định được** (falsifiable) — chỉ cần bộ chấm công bố actual T8/2023 là biết đúng/sai.

**6. Giới hạn**
Quy luật chẵn/lẻ gần như chắc chắn là **artifact của bộ sinh dữ liệu mô phỏng**, không phải hành vi doanh nghiệp thật. Dùng để dự báo trong cuộc thi thì hợp lệ; suy ra khuyến nghị kinh doanh thực tế thì **không**.

### Heatmap doanh thu Năm × Tháng
**1. Hiện trạng**
- **5 ô nóng nhất**: 2018‑06 (0.272 tỷ), 2016‑05 (0.268), 2017‑06 (0.267), 2016‑04 (0.267), 2017‑05 (0.263) — tất cả đều là **T4–T6 của giai đoạn 2016–2018**.
- **5 ô lạnh nhất**: 2020‑12 (0.0437), 2020‑11 (0.046), 2021‑01 (0.046), 2020‑01 (0.048), 2019‑12 (0.048) — tất cả đều là **T11–T1 của giai đoạn 2019–2021**.
- Chênh lệch ô nóng nhất / lạnh nhất = **6.2 lần**.
- 2012 khuyết T1–T6 (ô trắng) — shop mở 04/07/2012, đúng kỳ vọng, **không phải thiếu dữ liệu**.

**2. Nguyên nhân — heatmap là tích của 2 hiệu ứng độc lập**
- **Chiều dọc (năm)**: tổng theo năm 2016 đỉnh 2.105 tỷ → 2021 đáy 1.043 tỷ.
- **Chiều ngang (tháng)**: tổng toàn kỳ T5 2.038 tỷ, T4 1.960, T6 1.928 vs T1 0.803, T12 0.861, T11 0.862.

Ô nóng/lạnh nhất chính là **giao điểm cực trị của 2 chiều** (năm mạnh nhất × tháng mạnh nhất, và ngược lại) — không cần giả thuyết riêng nào để giải thích.

**3. Mối liên hệ**
Hai chiều này được tách riêng ở 2 ô kế tiếp: chiều tháng → "hình dạng mùa vụ"; chiều năm → đã phân tích ở ô MA30 phía trên.

**4. Hệ quả kéo theo**
Vì 2 hiệu ứng **nhân** nhau chứ không **cộng**, biên độ tuyệt đối co lại theo năm: chênh T5 vs T12 trong năm 2016 lớn hơn nhiều so với chênh cùng cặp tháng năm 2021. Mô hình dự báo dùng hiệu ứng mùa vụ **cộng tính** (additive) sẽ sai; cần **nhân tính** (multiplicative) hoặc dùng lag theo tỷ lệ.

**5. Dự đoán**
Với mức nền 2022 (~1.17 tỷ/năm) và tỷ trọng mùa vụ giữ nguyên, 2023–2024 kỳ vọng:
- **T4–T6: ~0.14–0.15 tỷ/tháng**
- **T11–T1: ~0.05–0.06 tỷ/tháng**

**6. Giới hạn**
Thang màu tuyến tính khiến toàn bộ vùng 2019–2022 trông "nhạt đều", che mất biến động nội bộ giai đoạn này. Muốn đọc chi tiết giai đoạn sau 2019 nên vẽ lại heatmap chuẩn hóa theo từng năm (% của năm).

### Hình dạng mùa vụ 10 năm chồng nhau
**1. Hiện trạng**
| Tháng | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | T10 | T11 | T12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TB % năm | 5.11 | 6.32 | 9.95 | 12.50 | **12.95** | 12.18 | 9.17 | 8.62 | 7.20 | 6.47 | 4.83 | **4.71** |
| std | 0.58 | 0.53 | 1.01 | 0.64 | 0.74 | 1.27 | 0.62 | **2.15** | 0.55 | 0.53 | 0.55 | 0.74 |

Đỉnh **T5 (12.95%)** / đáy **T12 (4.71%)** = **2.75 lần**. Các đường năm chồng lên nhau rất khít — mùa vụ **ổn định phi thường** qua 10 năm.

**2. Nguyên nhân của điểm bất thường duy nhất (T8, std 2.15 — gấp 3–4 lần mọi tháng khác)**
Không phải nhiễu ngẫu nhiên mà là **lưỡng cực chẵn/lẻ**:
- Năm **chẵn** (2014, 2016, 2018, 2020, 2022): T8 chiếm **9.71 – 11.58%**
- Năm **lẻ** (2013, 2015, 2017, 2019, 2021): T8 chiếm **6.14 – 7.17%**

Hai cụm **không giao nhau chút nào**. Nguyên nhân đã truy được ở ô margin phía trên: chương trình "Urban Blowout" (fixed 50, Streetwear, 30/07–02/09) chỉ chạy năm lẻ, kéo doanh thu T8 xuống ~40%.

**3. Mối liên hệ**
- Mùa cao điểm T4–T6 giải thích trực tiếp **top 5 ngày doanh thu cao nhất toàn kỳ đều rơi vào 30/05–02/06** (xem ô hiệu ứng Tết).
- Đáy T11–T12 trùng đúng vùng "ô lạnh" của heatmap.
- Mùa vụ này **ngược chiều** pattern e‑commerce phương Tây (Black Friday/Giáng sinh cuối năm) — ở đây T11–T12 là *thấp nhất*.

**4. Hệ quả kéo theo**
- Feature `month` / `month_sin` / `month_cos` có sức dự báo cao (std thấp) → hợp lý khi mô hình Phần B dùng chúng.
- Nhưng **riêng T8 cần thêm cờ chẵn/lẻ năm**: dùng một hệ số mùa vụ duy nhất cho T8 sẽ sai lệch cỡ **±2.2 điểm % tỷ trọng năm ≈ ±25 triệu VND/tháng** theo mức nền hiện tại.

**5. Dự đoán**
Horizon 2023 (lẻ) → T8/2023 ≈ **6.5–7.2%** doanh thu năm; 2024 (chẵn) → T8/2024 ≈ **9.7–11.6%**. Chênh nhau gần **gấp rưỡi** cho cùng một tháng ở 2 năm liên tiếp.

**6. Giới hạn**
Tỷ trọng là **số tương đối** — một tháng có thể tăng tỷ trọng chỉ vì các tháng khác giảm mạnh hơn. Cần đọc kèm giá trị tuyệt đối ở heatmap để tránh kết luận sai về "tháng đó bán tốt lên".

### Doanh thu trung bình theo thứ trong tuần
**1. Hiện trạng**
Xếp hạng: **T4 4.68** > T5 4.52 > T3 4.47 > T2 4.31 > CN 4.07 > T6 4.05 > **T7 3.91** (triệu VND/ngày). Chênh cao nhất–thấp nhất **19.8%**.

**2. Kiểm định thống kê (không chỉ nhìn cột cao thấp)**
t‑test Welch T4 vs T7: **t = 4.700, p = 0.000003** (n = 548 mỗi nhóm) → khác biệt **có ý nghĩa thống kê mạnh**, không phải nhiễu mẫu.

**3. Nguyên nhân — thành thật là CHƯA giải thích được**
Pattern "giữa tuần > cuối tuần" **ngược** với kỳ vọng thông thường của thương mại điện tử thời trang. Dữ liệu hiện có trong notebook **không đủ** để xác định nguyên nhân. Các giả thuyết có thể kiểm chứng nếu điều tra thêm (chưa làm ở đây):
- Phân bố `order_source` khác nhau theo thứ (kênh B2B/email chạy ngày làm việc)?
- Lịch chạy khuyến mãi neo vào ngày trong tuần?
- Đơn giản là tham số của bộ sinh dữ liệu mô phỏng.

**Không kết luận nguyên nhân khi chưa có bằng chứng** — ghi nhận là hiện tượng cần điều tra.

**4. Mối liên hệ + kiểm tra tính bền**
Tách 2 giai đoạn để xem pattern có bền qua cú sụp 2019 không:
- **2012–2018**: T4 5.55 cao nhất, T7 4.62 thấp nhất → chênh **20.2%**
- **2019–2022**: T4 3.26 cao nhất, T7 2.75 thấp nhất → chênh **18.7%**

Thứ tự các thứ **giữ nguyên**, biên độ gần như không đổi → đây là **đặc tính cấu trúc**, độc lập hoàn toàn với biến cố sụt doanh thu.

**5. Hệ quả kéo theo**
- Feature `day_of_week` (và `dow_sin`/`dow_cos`) trong Phần B là **hợp lệ và ổn định** — biên độ ~20% đủ lớn để cải thiện dự báo ngày.
- Do biên độ không đổi giữa 2 giai đoạn, hiệu ứng này nên được mô hình hóa **nhân tính** (tỷ lệ), không phải cộng tính.

**6. Giới hạn**
Trung bình theo thứ **trộn lẫn mọi tháng và mọi năm**; vì mùa vụ mạnh (2.75 lần) và số ngày mỗi thứ không phân bố hoàn toàn đều giữa các tháng, một phần nhỏ chênh lệch có thể do lẫn mùa vụ. Chênh 19.8% lớn hơn nhiều so với sai lệch này nên kết luận vẫn đứng vững, nhưng con số chính xác nên đọc là "khoảng 20%", không phải "đúng 19.8%".

### Hiệu ứng Tết (trung bình 10 cái Tết 2013–2022)
**1. Hiện trạng đọc từ biểu đồ**
Đường Revenue: ngày −30 (3.08 tr) → −7 (2.90) → −1 (2.93) → **mồng 1 (3.28)** → **mồng 2 (3.70 — đỉnh cục bộ)** → +7 (3.25) → +14 (3.57) → **+30 (4.26 — cao nhất toàn khung)**.

Nhìn chart, kết luận tự nhiên sẽ là "Tết tạo cú tăng mạnh và kéo dài cả tháng sau".

**2. Nguyên nhân — kết luận đó phần lớn SAI vì nhiễu mùa vụ (confounding)**
Tết rơi vào **cuối T1 – giữa T2**. Cửa sổ −30/+30 ngày do đó trải từ **T12–T1 (đáy mùa vụ: 4.71%–5.11% doanh thu năm)** sang **T3 (9.95%)**. Đường dốc lên sau Tết **trùng khớp với đà tăng mùa vụ tự nhiên vào mùa cao điểm T4–T6**, chứ không chứng minh được là do Tết.

Kiểm chứng bằng cách khử mùa vụ — so doanh thu 7 ngày sau Tết với **trung bình chính tháng chứa Tết đó**:

| Tết | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 |
|---|---|---|---|---|---|---|---|---|---|---|
| post7 vs TB tháng | −11.9% | −4.5% | **+32.7%** | −8.5% | **+47.8%** | +1.0% | −26.6% | **+56.6%** | −2.4% | −32.2% |

**5 năm dương, 5 năm âm**, biên độ dao động từ −32% đến +57%. Không có hiệu ứng Tết ổn định khi đã kiểm soát mùa vụ.

Bằng chứng phụ trợ mạnh: **top 5 ngày doanh thu cao nhất toàn bộ 11 năm** là 2018‑05‑30 (20.9 tr), 2018‑05‑31 (19.3), 2018‑06‑01 (19.2), 2017‑06‑01 (17.6), 2018‑06‑02 (17.5) — **không có ngày Tết nào**. Đỉnh thật của năm nằm ở cuối T5 – đầu T6.

**3. Mối liên hệ khác**
- Corr(Revenue, COGS) theo ngày = **0.9760**, tỷ lệ COGS/Revenue trung bình 0.875 (std 0.127) → COGS bám rất sát doanh thu, nên **đường COGS trên chart gần như song song** với Revenue, không mang thêm thông tin độc lập.

**4. Hệ quả kéo theo**
- Feature `days_from_tet` trong Phần B **có giá trị thấp hơn nhiều so với vẻ ngoài của chart này**. Nó vẫn có thể hữu ích ở chi tiết ngày (mồng 1–2 nhích lên thật) nhưng **không phải driver chính**.
- Rủi ro thực tế: nếu tin chart này, dễ gán trọng số quá lớn cho biến Tết và **làm mô hình lệch vào T1–T2**, đúng vùng đáy mùa vụ.

**5. Dự đoán**
Horizon Phần B chứa Tết **2023‑01‑22** và **2024‑02‑10**. Dự đoán: sai số mô hình quanh 2 mốc này sẽ **KHÔNG cải thiện đáng kể** khi thêm/bớt biến Tết — trong khi bỏ biến `month` sẽ làm sai số tăng vọt.

**6. Giới hạn / bài học đọc biểu đồ**
Đây là ví dụ điển hình về **confounding**: chart đúng về mặt vẽ, nhưng cách đọc trực giác dẫn tới kết luận sai. Muốn khẳng định hiệu ứng Tết cần so với **baseline cùng mùa vụ** (như bảng trên), không so với chính vùng lân cận.

### Tỷ trọng doanh thu theo category
**1. Hiện trạng — tương đối và tuyệt đối kể 2 câu chuyện KHÁC NHAU**

| Category | Share 2013 | Share 2022 | Doanh thu 2013 | Doanh thu 2022 | Tổng thay đổi | CAGR |
|---|---|---|---|---|---|---|
| Streetwear | 76.8% | **83.8%** ↑ | 1.273 tỷ | 0.981 tỷ | **−23.0%** ↓ | −2.86%/năm |
| Outdoor | 19.8% | **9.0%** ↓ | 0.328 tỷ | 0.106 tỷ | **−67.8%** ↓ | −11.83%/năm |
| Casual | 1.8% | 4.6% ↑ | 0.029 tỷ | 0.054 tỷ | **+86.4%** ↑ | +7.16%/năm |
| GenZ | 1.6% | 2.5% ↑ | 0.027 tỷ | 0.029 tỷ | +9.6% ↑ | +1.02%/năm |

️ **Bẫy đọc số quan trọng**: Streetwear *tăng* thị phần (76.8% → 83.8%) nhưng doanh thu tuyệt đối **giảm 23%**. Nó "thắng" chỉ vì Outdoor giảm nhanh hơn (−67.8%). Đây **không phải** câu chuyện Streetwear phát triển.

**2. Nguyên nhân**
- Outdoor sụp mạnh nhất và **sớm nhất** — đã giảm từ 2016 (0.325 tỷ) qua 2018 (0.207 tỷ) **trước** khi tổng doanh thu gãy, tức là suy giảm riêng của ngành hàng chứ không chỉ do cú sốc chung 2019.
- Casual/GenZ tăng trưởng dương nhưng xuất phát từ **nền cực nhỏ** (0.029/0.027 tỷ) — cộng lại 2022 chỉ 0.083 tỷ, **không đủ bù** 0.222 tỷ mà Outdoor đánh mất.

**3. Mối liên hệ**
- Streetwear là category bị chương trình **"Urban Blowout"** (fixed 50, chỉ năm lẻ) nhắm trúng → nó vừa là category lớn nhất vừa là nguồn lỗ gộp lớn nhất (xem ô below‑cost và ô floor‑price).
- Streetwear chiếm **377,723/677,662 dòng (55.7%)** — thống trị cả về doanh thu lẫn khối lượng giao dịch.

**4. Hệ quả kéo theo**
- **Rủi ro tập trung cực cao**: 83.8% doanh thu phụ thuộc 1 category, và category đó đang giảm 2.86%/năm.
- Vì Streetwear cũng có margin thấp gần nhất (13.24%, chỉ trên Casual 11.75%), cơ cấu đang dịch chuyển về phía **hàng bán nhiều nhưng lãi mỏng** → margin toàn shop chịu áp lực giảm cấu trúc.

**5. Dự đoán**
Ngoại suy CAGR hiện tại tới 2024: Streetwear ~0.93 tỷ, Outdoor ~0.082 tỷ (thị phần rớt xuống ~7%), Casual ~0.062 tỷ. Nếu Outdoor giữ nhịp −11.8%/năm, nó sẽ **thu nhỏ dưới mức Casual+GenZ trước 2030**.

**6. Giới hạn**
Biểu đồ cột chồng 100% **về bản chất che giấu quy mô tuyệt đối** — không thể thấy tổng doanh thu đã giảm một nửa. Luôn phải đọc kèm bảng tuyệt đối như trên.

### ️ Phân tích chi tiết — Doanh thu theo vùng (region)
**1. Hiện trạng**
| Vùng | 2013 | Đỉnh (2016) | 2022 | Tổng thay đổi 2013→2022 | CAGR |
|---|---|---|---|---|---|
| East | 0.781 tỷ | 0.970 | 0.546 | −30.1% | −3.90%/năm |
| Central | 0.484 tỷ | 0.605 | 0.383 | **−20.9%** (nhẹ nhất) | −2.56%/năm |
| West | 0.392 tỷ | 0.529 | 0.240 | **−38.7%** (nặng nhất) | −5.29%/năm |

**Cả 3 vùng đều giảm. Không vùng nào tăng trưởng bù đắp** → suy giảm mang tính **toàn hệ thống**, không phải dịch chuyển địa lý.

**2. Nguyên nhân + kiểm tra tính đồng nhất**
Cả 3 vùng đạt đỉnh **cùng năm 2016** và gãy **cùng lúc 2019** → chịu chung một cú sốc, không có vùng nào "miễn nhiễm". Điều này loại trừ giả thuyết nguyên nhân mang tính địa phương (đối thủ vùng, đứt gãy logistics vùng...).

Thị phần dịch chuyển nhẹ: East giữ ổn định **45.1–47.2%** suốt 10 năm; Central **tăng** 29.20% → 32.75%; West **giảm** 23.66% → 20.55%. Vậy West vừa nhỏ nhất vừa mất thị phần nhanh nhất.

**3. Mối liên hệ**
- Cùng pattern "giảm đồng đều mọi lát cắt" với ô **kênh đặt hàng** (mọi kênh giảm 37–41%) và ô **nhóm tuổi** (mọi nhóm giảm ~35–40%). Ba lát cắt độc lập cùng cho một kết luận → củng cố rất mạnh giả thuyết cú sốc hệ thống (mất khách), thay vì mất một phân khúc cụ thể.
- Nghịch lý đáng chú ý: **West suy giảm nhanh nhất nhưng lại có margin cao nhất (14.20%)** — xem ô "margin theo vùng" ở Phần 4.

**4. Hệ quả kéo theo**
- Không có vùng nào để "nhân rộng mô hình thành công" — vì không vùng nào thành công.
- East chiếm ~46–47% doanh thu → mọi cải thiện margin/doanh thu ở East có tác động gần gấp đôi Central và gấp ba West.

**5. Dự đoán**
Giữ CAGR hiện tại tới 2024: East ~0.50 tỷ, Central ~0.36 tỷ, West ~0.22 tỷ. Thị phần West tiếp tục co về ~19–20%.

**6. Giới hạn**
`region` được lấy qua `geography.zip` — join `orders.zip → geography.zip`. Nếu tồn tại đơn có zip không khớp bảng geography, doanh thu tương ứng rơi vào nhóm NULL và **không xuất hiện trên chart này**; notebook chưa kiểm tra tỷ lệ join miss, nên tổng 3 vùng có thể nhỏ hơn tổng thực.

### Doanh thu theo kênh đặt hàng
**1. Hiện trạng**
Thị phần các kênh **gần như bất động** suốt 10 năm:

| Kênh | Share 2013 | Share 2022 | Biên độ 10 năm |
|---|---|---|---|
| organic_search | 28.18% | 27.58% | 27.58 – 28.33 |
| paid_search | 21.87% | 21.83% | 21.72 – 22.33 |
| social_media | 19.62% | 20.24% | 19.62 – 20.33 |
| email_campaign | 12.32% | 12.00% | 11.76 – 12.32 |
| referral | 9.92% | 10.13% | 9.55 – 10.50 |
| direct | 8.08% | 8.22% | 7.76 – 8.22 |

**Không kênh nào dịch chuyển quá 1 điểm % trong 10 năm.**

**2. Nguyên nhân của cú sụp 2018→2019 — đồng đều đến mức bất thường**
| Kênh | email | social | referral | organic | direct | paid |
|---|---|---|---|---|---|---|
| Δ 2018→2019 | **−41.0%** | −39.9% | −39.1% | −37.7% | −37.4% | **−37.3%** |

Chênh lệch giữa kênh tệ nhất và tốt nhất chỉ **3.7 điểm %**. Nếu nguyên nhân là một kênh cụ thể hỏng (mất ngân sách quảng cáo, bị phạt SEO, tài khoản social bị khóa...), ta sẽ thấy **một kênh sụp sâu và các kênh khác gần như nguyên vẹn**. Thực tế ngược lại hoàn toàn.

**Kết luận**: cú sốc tác động ở tầng **cầu/khách hàng**, không phải tầng **kênh phân phối**.

**3. Mối liên hệ**
Đây là bằng chứng độc lập thứ ba (cùng với vùng và nhóm tuổi) cho cùng một kết luận. Ba lát cắt hoàn toàn khác nhau về bản chất mà cùng cho pattern "giảm đều" → gần như loại trừ mọi giả thuyết nguyên nhân cục bộ.

**4. Hệ quả kéo theo**
- **Không có kênh nào để "đổ thêm ngân sách vào"** như một giải pháp — vấn đề không nằm ở kênh.
- Thị phần bất động 10 năm là dấu hiệu rõ của dữ liệu mô phỏng bằng tỷ lệ cố định → **không nên** rút ra khuyến nghị marketing mix từ chart này.

**5. Dự đoán**
2023–2024 tỷ trọng kênh gần như chắc chắn giữ nguyên (organic ~28%, paid ~22%, social ~20%). Đây là dự đoán rất an toàn nhưng cũng ít giá trị.

**6. Giới hạn**
`order_source` là thuộc tính của đơn, không phải hành trình khách hàng thực (không có multi‑touch attribution). Không thể kết luận kênh nào "tạo ra" khách, chỉ biết đơn được ghi nhận ở kênh nào.
---

## Phần B — Chẩn đoán nguyên nhân

_Notebook: `notebooks/02b_eda_nguyen_nhan.ipynb`_

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

## Phần C — Phân khúc khách hàng

_Notebook: `notebooks/02c_eda_khach_hang.ipynb`_

### Tỷ trọng doanh thu theo nhóm tuổi
**1. Hiện trạng — ổn định đến mức gần như là hằng số**
| Nhóm tuổi | 2013 | 2022 | Biên độ 10 năm | Dao động max−min |
|---|---|---|---|---|
| 25‑34 | 29.58% | 30.12% | 29.37 – 30.12 | **0.74 điểm %** |
| 35‑44 | 26.33% | 26.42% | 25.96 – 26.46 | **0.50 điểm %** |
| 45‑54 | 19.39% | 19.10% | 18.90 – 19.61 | 0.71 điểm % |
| 18‑24 | 13.34% | 13.50% | 13.34 – 14.13 | 0.79 điểm % |
| 55+ | 11.35% | 10.86% | 10.86 – 11.45 | 0.59 điểm % |

Không nhóm nào dịch chuyển quá **0.8 điểm %** trong cả thập kỷ, kể cả xuyên qua cú sụp 2019.

**2. Nguyên nhân / ý nghĩa**
Cơ cấu tuổi bất động khi doanh thu giảm một nửa có nghĩa: **mọi nhóm tuổi mất doanh thu theo cùng một tỷ lệ**. Kiểm chứng bằng giá trị tuyệt đối (2016 → 2022): 25‑34: 0.619 → 0.352 tỷ (−43%); 35‑44: 0.553 → 0.309 (−44%); 45‑54: 0.413 → 0.223 (−46%); 18‑24: 0.283 → 0.158 (−44%); 55+: 0.237 → 0.127 (−46%). **Chênh lệch giữa nhóm giảm nhiều nhất và ít nhất chỉ 3 điểm %.**

**3. Mối liên hệ**
Đây là **lát cắt thứ ba** (sau vùng và kênh) cho cùng kết quả "giảm đều tuyệt đối". Ba lát cắt độc lập về bản chất — địa lý, kênh, nhân khẩu — cùng loại trừ giả thuyết cục bộ. Kết hợp với ô ASP‑Volume, bức tranh nhân quả đã khép: **cú sốc tác động lên số lượng khách và tần suất mua, đồng đều trên mọi phân khúc**.

**4. Hệ quả kéo theo**
- **`age_group` vô dụng để giải thích biến động doanh thu** — không mang thông tin phân biệt theo thời gian.
- Nhưng vẫn hữu ích cho **phân bổ ngân sách tĩnh**: 25‑34 và 35‑44 cộng lại chiếm **56.5%** doanh thu ổn định qua mọi năm.

**5. Dự đoán**
Cơ cấu 2023–2024 gần như chắc chắn giữ nguyên (25‑34 ~30%, 35‑44 ~26%). Đây là dự đoán độ tin cậy rất cao nhưng giá trị quyết định thấp.

**6. Giới hạn**
`age_group` là trường tĩnh trong `customers.csv` — **không có ngày sinh**, nên khách không "già đi" qua 10 năm dữ liệu. Điều này tự nó đã đảm bảo cơ cấu ổn định; do đó **không thể** dùng chart này để kết luận về hành vi theo vòng đời khách hàng.

### AOV theo nhóm tuổi
**1. Hiện trạng — đồng đều gần như tuyệt đối**
| Nhóm | 18‑24 | 25‑34 | 35‑44 | 45‑54 | 55+ |
|---|---|---|---|---|---|
| AOV (nghìn VND) | 25.42 | 25.56 | 25.50 | **25.59** | 25.42 |
| Số đơn | 84,591 | 181,311 | 161,865 | 118,026 | 69,101 |
| Số khách | 17,039 | 36,342 | 31,920 | 23,172 | 13,457 |

Chênh lệch cao nhất–thấp nhất: **0.17 nghìn VND = 0.68%**.

**2. Nguyên nhân / diễn giải**
Khác biệt 0.68% trên mẫu 69K–181K đơn mỗi nhóm là **không có ý nghĩa thực tiễn**, dù có thể "có ý nghĩa thống kê" do mẫu quá lớn. Đây là ví dụ tốt cho nguyên tắc: *statistical significance ≠ practical significance*.

Kết luận: **giá trị đơn hàng độc lập với tuổi**. Sự khác biệt giữa các nhóm nằm hoàn toàn ở **số lượng khách** (25‑34 có 36,342 khách vs 55+ có 13,457 khách, gấp 2.7 lần) chứ không ở **hành vi chi tiêu mỗi lần mua**.

**3. Mối liên hệ**
Kết hợp với ô trước (cơ cấu tuổi bất động): doanh thu theo tuổi = **số khách × AOV chung**. Vì AOV giống nhau và cơ cấu số khách không đổi, tỷ trọng doanh thu theo tuổi tất yếu phải bất động — **hai chart này thực chất nói cùng một điều**, chart này giải thích *cơ chế* của chart trước.

**4. Hệ quả kéo theo**
- **Không có cơ sở** cho chiến lược định giá phân biệt theo tuổi hoặc "nhắm nhóm tuổi giá trị cao".
- Nếu muốn tăng doanh thu qua kênh nhân khẩu học, đòn bẩy duy nhất là **số lượng khách**, không phải giá trị mỗi khách.

**5. Dự đoán**
AOV theo tuổi sẽ tiếp tục hội tụ quanh 25.4–25.6 nghìn VND. Bất kỳ chênh lệch nào vượt ~1% trong dữ liệu tương lai sẽ là tín hiệu bất thường đáng điều tra.

**6. Giới hạn**
Cùng vấn đề nhóm khóa như ô AOV promo: `groupby(["order_id","age_group"])` — vì mỗi đơn thuộc đúng 1 khách nên ở đây **không** xảy ra tách đôi đơn, chỉ tiêu này đáng tin hơn. Tuy nhiên nó vẫn là AOV **gộp toàn kỳ**, chưa tách theo năm.

### RFM Segmentation (9 nhóm)
**1. Hiện trạng — phân bổ giá trị cực kỳ lệch**
| Segment | Số khách | % khách | Monetary (tỷ) | % giá trị | Recency TB (ngày) | Freq TB | Giá trị/khách |
|---|---|---|---|---|---|---|---|
| **Champions** | 22,575 | 25.6% | **8.950** | **62.9%** | 274 | 15.88 | **396.4k** |
| Loyal Customers | 16,974 | 19.3% | 2.884 | 20.3% | 787 | 7.02 | 169.9k |
| At Risk | 7,989 | 9.1% | 0.646 | 4.5% | **2,010** | 3.90 | 80.9k |
| Can't Lose Them | 2,251 | 2.6% | 0.492 | 3.5% | 1,783 | 8.61 | **218.6k** |
| **Lost** | **21,682** | **24.6%** | 0.459 | **3.2%** | **2,563** | 1.26 | **21.2k** |
| Hibernating | 3,327 | 3.8% | 0.270 | 1.9% | 2,399 | 1.60 | 81.0k |
| Promising | 5,375 | 6.1% | 0.205 | 1.4% | 1,105 | 1.48 | 38.2k |
| New Customers | 4,865 | 5.5% | 0.203 | 1.4% | 359 | 1.51 | 41.8k |
| Need Attention | 3,085 | 3.5% | 0.125 | 0.9% | 689 | 3.65 | 40.5k |

Tổng **88,123 khách / 14.234 tỷ VND** (Monetary = `payments.payment_value`, đơn không hủy).

**2. Phân tích cấu trúc**
- **Champions vs Lost gần bằng nhau về SỐ LƯỢNG** (22,575 vs 21,682 — chênh 4%) nhưng chênh **19.5 lần** về giá trị (62.9% vs 3.2%) và **18.7 lần** giá trị/khách (396.4k vs 21.2k). Gần **1/4 tệp khách hàng đã mất gần hết giá trị thương mại**.
- Champions + Loyal = 44.9% khách nhưng nắm **83.1%** giá trị → tuân theo phân bố Pareto rõ rệt (thậm chí gắt hơn quy tắc 80/20).
- Phân bố `frequency` toàn tệp: trung vị **4 đơn**, trung bình 6.67, tối đa 100; **25.72% khách chỉ mua đúng 1 lần**.
- Phân bố `recency`: trung vị **1,018 ngày (~2.8 năm)**, tối đa 3,832 ngày. Với `SNAPSHOT_DATE = 2022‑12‑31`, **hơn nửa tệp khách đã không mua gì trong gần 3 năm**.

**3. Mối liên hệ**
- Recency trung vị ~2.8 năm là hệ quả trực tiếp của cú sụp 2019 và việc mất nguồn khách mới (ô khách mới/khách cũ): tệp khách bị "đóng băng" ở quá khứ.
- Nhóm "New Customers" chỉ 4,865 khách (5.5%) — quá nhỏ so với "Lost" 21,682 → **tốc độ nạp mới thua xa tốc độ rơi rụng**, khớp với số khách mua lần đầu chỉ còn 1,322 vào 2022.

**4. Hệ quả kéo theo**
- Nhóm mục tiêu win‑back ở Phần 4 (At Risk + Can't Lose Them = 10,240 khách, 11.6%) có recency **1,783–2,010 ngày (~5 năm)**. Ở khoảng cách này, thuật ngữ "At Risk" (sắp rời bỏ) là **sai lệch** — họ đã rời bỏ từ lâu. Xác suất win‑back thực tế nên được giả định **thấp hơn nhiều** so với nhóm vừa rời 3–6 tháng.
- Rủi ro tập trung: 62.9% giá trị nằm ở Champions với recency TB 274 ngày (~9 tháng) — nhóm này cũng đang trượt dần khỏi trạng thái "gần đây".

**5. Dự đoán**
Nếu không có acquisition mới và tần suất mua giữ nguyên, dòng chảy tự nhiên là Champions → Loyal → At Risk → Lost. Với recency TB Champions đã 274 ngày, một phần nhóm này sẽ **rơi khỏi Champions trong 1–2 năm tới**, kéo tỷ trọng "Lost" vượt 30%.

**6. Giới hạn**
- Chấm điểm R/F/M dùng `qcut` trên **rank**, tức luôn chia tệp thành 5 phần bằng nhau → **các segment là tương đối, không tuyệt đối**. Nếu toàn bộ tệp cùng xấu đi, vẫn luôn có 20% được gán điểm 5. Không thể so sánh phân khúc này giữa 2 kỳ khác nhau.
- Monetary lấy từ `payment_value` (đã trừ chiết khấu), **khác** với `line_revenue` (gross) dùng ở các chart khác — nên tổng 14.234 tỷ ở đây không so trực tiếp được với 15.689 tỷ gross ở waterfall.

### ️ Phân tích chi tiết — Cohort Retention: PHÁT HIỆN LỖI DỮ LIỆU NGHIÊM TRỌNG
**1. Hiện trạng**
Đường retention **phẳng gần như tuyệt đối**: M0 3.03%, M1 3.01%, M3 2.94%, M6 3.00%, M9 3.02%, M12 2.92%. Biên độ dao động cả 12 tháng chỉ **0.14 điểm %**.

Đây là bất thường: mọi đường cong retention thực tế đều **giảm mạnh ở M1–M3 rồi phẳng dần**. Một đường phẳng ngay từ M0 là dấu hiệu chỉ tiêu **không đo đúng thứ nó tưởng đang đo**.

**2. Nguyên nhân — truy ra bằng dữ liệu, không suy đoán**

**Bằng chứng 1 — retention quan sát ≈ tỷ lệ nền ngẫu nhiên:**
Số khách khác nhau phát sinh đơn mỗi tháng trung bình **4,265**, trên tổng **121,930** khách trong `customers.csv` → tỷ lệ nền = **3.50%**. Giá trị "retention" quan sát được là **2.89–3.03%**. Hai con số gần như trùng nhau → **đường cong này chỉ đang đo xác suất một khách bất kỳ mua hàng trong một tháng bất kỳ**, hoàn toàn không phụ thuộc vào việc khách đó thuộc cohort nào.

**Bằng chứng 2 — `signup_date` không liên quan tới hành vi mua:**
- **80,623 / 90,246 khách (89.3%)** có đơn hàng **TRƯỚC** ngày đăng ký của chính mình.
- Độ trễ trung vị từ signup tới đơn đầu tiên: **−1,839 ngày** (mua trước khi đăng ký ~5 năm).

**Bằng chứng 3 — hai chuỗi đi ngược chiều nhau:**
| Năm | 2012 | 2014 | 2016 | 2018 | 2020 | 2022 |
|---|---|---|---|---|---|---|
| Số khách **signup** | 957 | 5,034 | 9,202 | 13,011 | 17,211 | **21,103** ⬆️ |
| Số khách **mua lần đầu** | 22,068 | 13,293 | 6,392 | 3,717 | 1,500 | **1,322** ⬇️ |

Signup tăng đều 22 lần trong khi khách mua lần đầu giảm 17 lần. Nếu `signup_date` phản ánh việc bắt đầu quan hệ khách hàng, hai chuỗi này không thể ngược chiều.

**Kết luận: `signup_date` là trường được gán gần như độc lập với hành vi mua** (rất có thể là ngày tạo bản ghi trong bộ sinh dữ liệu). Do đó **toàn bộ phân tích cohort dựa trên nó là vô nghĩa** — cohort không phải là "nhóm khách bắt đầu cùng thời điểm".

**3. Mối liên hệ**
- Kích thước cohort tăng đều 83 (2012‑07) → **1,883 (2022‑12)** phản ánh đúng chuỗi signup, tức mẫu số phình to trong khi tử số (khách thực mua) không tăng → ép tỷ lệ về mức nền.
- **31,684 khách (26.0%)** trong `customers.csv` chưa từng có bất kỳ đơn hàng nào — bằng chứng thêm rằng danh sách khách và danh sách người mua là hai tập khác nhau đáng kể.

**4. Hệ quả kéo theo**
-  **Không được** dùng con số "retention ~3%" để đánh giá sức khỏe khách hàng hay so sánh với benchmark ngành. Nó không phải retention.
-  Chỉ tiêu thay thế đáng tin: **tỷ lệ doanh thu từ khách cũ** (66.1% → 96.4%) và **số đơn/khách/năm** (2.03 → 1.46) — cả hai đều tính từ `order_date`, không dùng `signup_date`.
- Có một tín hiệu vẫn còn giá trị: retention M1 tính theo năm cohort giảm rõ rệt — 2016: **4.74%** → 2019: 2.45% → 2022: **2.11%**. Vì cùng dùng một chỉ tiêu bị lỗi, so sánh **tương đối giữa các năm** vẫn phản ánh việc tần suất mua giảm ~55%.

**5. Dự đoán**
Nếu bổ sung được trường thời điểm bắt đầu đáng tin (hoặc định nghĩa cohort theo **tháng có đơn đầu tiên** thay vì signup), đường cong sẽ có hình decay thật và mức M1 kỳ vọng **cao hơn 3%** đáng kể.

**6.  ĐÃ XỬ LÝ Ở TẦNG dbt (2026-08-10) — xem chart + phân tích ngay bên dưới**

Notebook này **giữ nguyên** cách tính gốc ở trên để đối chiếu số với báo cáo phase cũ (không tự sửa). Lỗi đã được xử lý ở tầng lakehouse bằng cách **thêm model song song**, không sửa đè:

| Model dbt | Định nghĩa cohort | Dùng khi nào |
|---|---|---|
| `iceberg.staging.int_cohort` | tháng `signup_date` | ️ CHỈ đối chiếu lịch sử / regression phase cũ |
| **`iceberg.staging.int_cohort_first_order`** | tháng **đơn hàng đầu tiên** (non-cancelled) |  Phân tích / BI / ra quyết định |

Chart + phân tích chi tiết đường cong retention THẬT (query trực tiếp qua Trino, không hardcode số) → xem cell ngay dưới đây.

### Retention THẬT (đơn đầu tiên) vs retention lỗi (signup_date), query trực tiếp qua Trino
**1. Hiện trạng — hai đường cong lệch hẳn nhau, không chỉ lệch mức mà lệch cả hình dạng**
Đường `int_cohort_first_order` (tím, đậm): **M0 = 100%** → M1 **6.10%** → giảm dần M2 5.60% → M3 5.50% → M4 5.50% → M5 5.40% → chạm đáy **M6 = 5.30%** → hồi M7 5.50% → M8 6.00% → M9 6.20% → M10 6.20% → M11 6.40% → **M12 = 6.40%**. Hình dạng đúng chữ **"nụ cười"**: giảm đơn điệu 6 tháng đầu rồi đảo chiều hồi phục đối xứng gần bằng đỉnh cũ.
Đường `int_cohort` (xám, nét đứt — model cũ dùng `signup_date`) gần như **một đường thẳng nằm ngang quanh 2.9–3.0%** suốt 12 tháng, không có bất kỳ điểm uốn nào. Khoảng cách giữa hai đường: **M1 gấp 2.03 lần, M6 gấp 1.77 lần, M12 gấp 2.21 lần** — chênh lệch không cố định mà co giãn theo đúng hình "nụ cười" của đường thật.

**2. Nguyên nhân**
Hai model dùng cùng công thức tổng hợp (`SUM(n_active)*100.0/SUM(cohort_size)`) và cùng bảng nguồn `stg_orders` cho phần tử số — khác nhau duy nhất ở **định nghĩa `cohort_month`**. `int_cohort_first_order` neo cohort vào chính hành vi mua (tháng đơn đầu tiên) nên tại M0 tử số = mẫu số tuyệt đối → 100% là hệ quả toán học của định nghĩa, không phải phát hiện nghiệp vụ. `int_cohort` neo vào `signup_date` — một trường đã chứng minh (mục 2 ở phân tích phía trên) không liên quan hành vi mua (89.3% khách mua trước khi "đăng ký") — nên tại M0 xác suất một khách bất kỳ phát sinh đơn đúng tháng signup của họ chỉ là xác suất nền ngẫu nhiên (~3%), không hội tụ về 100%.
Hình "nụ cười" của đường thật nhiều khả năng phản ánh **chu kỳ mua lặp lại theo mùa của hàng thời trang** — khớp hướng với biên độ mùa vụ **2.75 lần** giữa tháng cao/thấp điểm đã đo ở Phần 1 (cell "Hình dạng mùa vụ 10 năm chồng nhau"). Khách mua lần đầu ở một mùa cụ thể có xu hướng quay lại đúng dịp tương ứng của năm sau (M12) hơn là giữa chừng (M4–M6) — tương tự việc mua sắm thời trang theo mùa/dịp thay vì đều đặn hàng tháng.

**3. Mối liên hệ**
- Nối với phát hiện `% doanh thu khách cũ` tăng từ 66.1% → 96.4% qua các năm (mục 4 ở phân tích phía trên, dùng `order_date` — không lỗi): dòng doanh thu ngày càng phụ thuộc khách cũ **dù tần suất quay lại theo cohort chỉ 5.3–6.4%** — nghĩa là tổng doanh thu khách cũ lớn chủ yếu do **tích lũy nhiều cohort qua 10 năm** cộng dồn, không phải từng cohort riêng lẻ retention cao.
- Nối với Phần 1 (mùa vụ 2.75 lần) và Phần 2 (Q1 — ASP vs Volume): cả ba cùng chỉ về đặc tính ngành thời trang mua theo mùa/dịp, không phải mua định kỳ đều đặn kiểu FMCG.
- Nối với RFM (Phần 3, cell trước cell này): nhóm `Can't Lose Them`/`At Risk` — nếu đúng giả thuyết "mua theo mùa/năm", thời điểm win-back hiệu quả nhất nên rơi vào **trước mốc 1 năm kể từ đơn đầu (quanh M9–M11)**, không phải ngay sau M1.

**4. Hệ quả kéo theo**
- Kết luận cũ "retention chỉ ~3%, phẳng tuyệt đối" (dựa trên `int_cohort`) là **đánh giá thấp** thực trạng ở mọi mốc — số thật cao gấp 1.77–2.21 lần. Nếu từng dùng con số cũ để quyết định ngân sách CRM/win-back, ngân sách đó bị định giá dựa trên tín hiệu sai.
- Retention thật (5.3–6.4%) vẫn **thấp so với benchmark ngành thời trang online phổ biến (thường 20–40% ở M1)** — đây là vấn đề kinh doanh thật, không phải lỗi đo lường. Không nên diễn giải "đã tìm ra số đúng, mọi thứ ổn" — số đúng vẫn xấu, chỉ là xấu theo cách khác con số cũ.
- ️ **Cập nhật (xem cell kiểm định ngay sau đây)**: khuyến nghị ban đầu "win-back nhắm giai đoạn M4–M5" dựa trên offset trung bình đã được kiểm định lại và **KHÔNG đúng chỗ nhắm** — đáy là hiệu ứng mùa vụ theo THÁNG LỊCH (khoảng Tháng 11–Tháng 1), không phải theo offset kể từ lần mua đầu. Xem kết luận đầy đủ + bằng chứng ở cell/markdown ngay sau.

**5. Dự đoán**
- Nếu hình "nụ cười" thật sự là hiệu ứng chu kỳ mùa/năm (không phải trùng hợp), mở rộng trục sang M13–M24 (cần dbt bỏ giới hạn `month_offset <= 12` hiện tại) sẽ thấy **đáy thứ hai quanh M18** rồi hồi lại quanh **M24** — lặp lại đúng biên độ M6/M12 hiện tại. Đây là dự đoán **kiểm chứng được**: chỉ cần sửa 1 dòng filter trong `int_cohort_first_order`/query notebook, không cần model mới.
- Cách kiểm định chặt hơn giả thuyết "mùa vụ" thay vì "thuần túy vòng đời khách hàng": tách `cohort_month` theo tháng bắt đầu (ví dụ cohort bắt đầu tháng 3 vs tháng 9) rồi so đáy/đỉnh của từng nhóm — nếu đáy luôn rơi đúng offset +6 bất kể tháng bắt đầu (hiệu ứng vòng đời/tenure) thay vì rơi đúng một **tháng lịch cụ thể** bất kể cohort (hiệu ứng mùa lịch thuần túy), sẽ phân biệt được hai giả thuyết. Chưa làm ở đây.

**6. Giới hạn**
- **Right-censoring nhẹ nhưng có thật**: mẫu số (`cohort_size` cộng dồn) giảm dần theo offset — M0 = 88,123 khách nhưng M12 chỉ còn 86,795 khách "đủ điều kiện" (cohort đủ già để quan sát tới M12), tức **1,328 khách (1.5%) bị loại khỏi điểm M12** vì cohort của họ còn quá trẻ. Ảnh hưởng nhỏ (1.5%) nhưng có nghĩa là điểm M12 hơi thiên về các cohort **cũ hơn** (2012–2021) so với điểm M1 (gồm cả cohort 2022).
- **`month_offset` trộn lẫn "tenure" (số tháng kể từ lần mua đầu) với "tháng lịch"** — vì mỗi cohort bắt đầu ở một tháng lịch khác nhau, đường trung bình cộng dồn ở mục 5 chưa tách được hiệu ứng mùa lịch thuần túy khỏi hiệu ứng vòng đời khách hàng. Diễn giải "nụ cười = mùa vụ" ở mục 2 là **giả thuyết có cơ sở gián tiếp** (khớp hướng với biên độ mùa vụ Phần 1), **chưa phải bằng chứng nhân quả trực tiếp** — cần phép tách ở mục 5 mới kết luận chắc.
- Cả hai đường đều là **trung bình weighted toàn kỳ 2012–2022** — có thể che khuất khác biệt theo năm (đã ghi nhận ở mục 4 phân tích phía trên: retention M1 theo năm cohort giảm từ 4.74% (2016) xuống 2.11% (2022) khi tính trên model cũ; chưa recompute xu hướng theo năm cho model `int_cohort_first_order` ở đây).

### Kiểm định giả thuyết "nụ cười = mùa vụ" (nợ để lại ở mục 5/6 phía trên) — KẾT LUẬN: MÙA VỤ, không phải vòng đời
**1. Hiện trạng — 2 phép đo cho 2 câu trả lời trái ngược nhau**
Tách 126 cohort thành 12 nhóm theo **tháng bắt đầu** (10–11 cohort/nhóm, đủ mẫu), tính đường cong retention riêng từng nhóm, tìm điểm đáy (M1–M12) của mỗi nhóm:
- **`trough_offset`** (đáy rơi vào offset thứ mấy): trải từ **1 đến 10**, độ lệch chuẩn **3,06 tháng** — hoàn toàn KHÔNG hội tụ về một con số cố định (bác bỏ "đáy luôn ở tenure +6").
- **`trough_calendar_month`** (đáy rơi vào tháng dương lịch nào, quy đổi từ offset): **10/12 nhóm (83%) đáy đúng THÁNG 1**, độ lệch tròn (circular std) chỉ ~28° (**dưới 1 tháng**) — hội tụ rất chặt.

**2. Nguyên nhân**
Khi cohort bắt đầu Tháng 12 → chỉ cần offset 1 là chạm Tháng 1; cohort bắt đầu Tháng 3 → phải đi offset 10 mới chạm Tháng 1 năm sau. Offset khác nhau hoàn toàn nhưng đều **hội tụ về đúng 1 tháng dương lịch** — đây chính xác là chữ ký của hiệu ứng **MÙA VỤ (calendar)**, không phải hiệu ứng **VÒNG ĐỜI (tenure)**. Nếu là vòng đời thật, offset đáy phải giống nhau bất kể tháng bắt đầu — dữ liệu cho kết quả ngược lại.

Khớp trực tiếp với "Hình dạng mùa vụ 10 năm chồng nhau" đã đo ở Phần 1: **Tháng 11 (4,83%)/Tháng 12 (4,71%)/Tháng 1 (5,11%)** là 3 tháng thấp điểm nhất năm. Khách hàng đơn giản là **không quay lại mua trong giai đoạn thấp điểm cuối năm–đầu năm sau**, bất kể họ mới mua lần đầu được bao lâu.

**3. Mối liên hệ — giải thích luôn vì sao đường cong TRUNG BÌNH TOÀN KỲ (mục 1 phía trên) lại có hình "nụ cười" nông ở M6 thay vì đáy sắc nhọn**
Đường trung bình weighted mọi cohort (không tách tháng bắt đầu) **gộp 12 đáy sắc nhọn nằm ở 12 offset khác nhau** (1 đến 10) lại với nhau. Phép cộng dồn này "trải mỏng" (smear) các đáy riêng lẻ ra thành 1 vùng trũng nông ở khoảng giữa (quanh M5–M6) — đây là **ảo ảnh gộp (pooling artifact) của phép trung bình**, KHÔNG phải bằng chứng cho 1 hiệu ứng vòng đời thật ở tháng thứ 6. Đường "nụ cười" ở mục 1 vẫn đúng về mặt SỐ LIỆU, chỉ SAI về mặt DIỄN GIẢI nguyên nhân — đã sửa ở đây.

**4. Hệ quả kéo theo — SỬA khuyến nghị hành động đã ghi trước đó**
Ở mục 4 phía trên (phân tích đường cong trung bình) có ghi: *"Đáy M6 gợi ý cửa sổ can thiệp: win-back nhắm đúng giai đoạn M4–M5"* — khuyến nghị này **dựa trên offset trung bình, giờ xác nhận là sai chỗ nhắm**. Khuyến nghị đúng: win-back/CRM nên nhắm theo **THÁNG LỊCH** (chủ động outreach khoảng Tháng 10–11, TRƯỚC khi bước vào vùng thấp điểm Tháng 11–Tháng 1), áp dụng đồng loạt cho MỌI khách bất kể họ thuộc offset/cohort nào — không phải chờ đúng "tháng thứ 4–5 kể từ lần mua đầu" của riêng từng khách.

**5. Dự đoán**
Nếu giả thuyết mùa vụ đúng, năm sau (dữ liệu ngoài phạm vi 2012–2022) đáy retention theo tháng lịch vẫn sẽ rơi vào khoảng Tháng 11–Tháng 1 bất kể phân bố cohort mới ra sao — đây là dự đoán **kiểm chứng được** trực tiếp, khác hẳn dự đoán "đáy ở tenure M6" (đã bác bỏ).

**6. Giới hạn**
- 2 nhóm bắt đầu Tháng 1–2 KHÔNG rơi đúng Tháng 1 (đáy thật ở Tháng 10–11 của chính nhóm đó) — 10/12 không phải 12/12. Có thể do mẫu ít hơn (10 cohort thay vì 11) hoặc có 1 đáy phụ khác ngoài Tháng 1; **chưa điều tra thêm**, không đủ để bác bỏ kết luận chung (83% đồng thuận + circular std rất chặt là bằng chứng mạnh) nhưng cũng không nên coi là 100%.
- Mỗi nhóm tháng chỉ có 10–11 cohort — đủ để thấy pattern rõ nhưng KHÔNG đủ để ước lượng khoảng tin cậy chính thức (cần bootstrap nếu muốn con số p-value nghiêm ngặt hơn, chưa làm ở đây).
---

## Phần D — Đề xuất hành động

_Notebook: `notebooks/02d_eda_de_xuat.ipynb`_

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

## Hình dung Dashboard — yêu cầu rút ra từ EDA

Mục này không phải spec kỹ thuật (chưa phải việc của EDA) — là bản phác thảo NHU CẦU dashboard dựa trên phát hiện thật, đối chiếu với 6 mart dbt đã có (`mart_revenue_daily`, `mart_customer_segments`, `mart_channel_perf`, `mart_cohort_retention`) để biết cái nào dựng được NGAY và cái nào còn thiếu mart nguồn.

### Trang 1 — Tổng quan doanh thu (Revenue Overview)

Câu hỏi trả lời: doanh thu đang ở đâu so với lịch sử, xu hướng gần đây thế nào.

| Thành phần | Nguồn dữ liệu | Sẵn sàng |
|---|---|---|
| Line chart Revenue/COGS/MA30 theo ngày, có mốc break | `mart_revenue_daily` (đã có `revenue_ma30`, `revenue_yoy_pct`, `revenue_rank_desc`) | Có sẵn |
| Heatmap năm × tháng | `mart_revenue_daily` (group by `year`/`month` có sẵn) | Có sẵn |
| Card so sánh cùng kỳ (YoY) | `mart_revenue_daily.revenue_yoy_pct` | Có sẵn |
| Cảnh báo mùa vụ (T8 năm lẻ margin âm) | CHƯA có cột "năm chẵn/lẻ" hay cờ promo trong mart | **Thiếu** — cần thêm cột hoặc mart phụ (xem Trang 3) |

### Trang 2 — Doanh thu theo lát cắt (Category / Region / Channel)

| Thành phần | Nguồn dữ liệu | Sẵn sàng |
|---|---|---|
| Trend category/region/channel theo năm | `mart_channel_perf` (đúng grain long-format `dimension_type`) | Có sẵn |
| AOV có/không promo | `mart_channel_perf` (`dimension_type='promo'`) | Có sẵn |
| Region × Category cross (2 chiều đồng thời) | KHÔNG có — `mart_channel_perf` chỉ 1 chiều/lần (`dimension_type`) | **Thiếu** — cần mart mới hoặc pivot ở BI tool |

### Trang 3 — Chẩn đoán nguyên nhân (Diagnostic) — ĐÃ ĐÓNG (2026-08-10)

~~Đây là nhóm phát hiện có giá trị cao nhất phiên này... hoàn toàn chưa có mart nào expose~~ → **ĐÃ LÀM.** 2 mart mới (`dbt_datathon/models/marts/mart_revenue_diagnostic_yearly.sql`, `mart_promo_margin_diagnostic.sql`) + 1 intermediate dùng chung (`int_diagnostic_line_items.sql`). Verify đối chiếu Trino vs số notebook đã công bố khớp tuyệt đối (gross/cancelled/discount, repeat share, ASP-volume 2018→2019, below-cost promo/category). Chi tiết: PROCESS.md log 2026-08-10 "Mart chẩn đoán nguyên nhân".

| Thành phần | Nguồn dữ liệu | Sẵn sàng |
|---|---|---|
| ASP vs Volume theo năm (index 2018=100) | `mart_revenue_diagnostic_yearly` (`asp`, `qty`, `n_orders`, `n_active_cust`) | **Có sẵn** |
| Waterfall Gross → Net (hủy đơn/chiết khấu/hoàn tiền) | `mart_revenue_diagnostic_yearly` (`gross_booked`/`cancelled_loss`/`discount_loss`/`refund_loss`/`net_revenue`) | **Có sẵn** |
| % dòng bán dưới giá vốn theo category/promo/tháng | `mart_promo_margin_diagnostic` (grain year×month×category×has_promo) | **Có sẵn** |
| Cờ "năm chẵn/lẻ" + lịch khuyến mãi | `mart_promo_margin_diagnostic.is_odd_year` (kết hợp `month`+`has_promo`) | **Có sẵn** |

Phát hiện phụ khi build: `refund_loss` tổng mart (0.487 tỷ) thấp hơn số notebook gốc từng công bố (0.511 tỷ) — notebook gốc tính `refund_loss` KHÔNG lọc năm (khác mọi cột khác đều lọc 2013-2022), mart sửa đúng sự không nhất quán đó (2.115/39.939 dòng `returns.csv` thuộc đơn năm 2012 bị loại đúng). Số mart đáng tin hơn số notebook cũ ở điểm này.

### Trang 4 — Khách hàng (Customer / RFM / Cohort)

| Thành phần | Nguồn dữ liệu | Sẵn sàng |
|---|---|---|
| RFM segment overview (9 nhóm, %khách, %giá trị) | `mart_customer_segments` | Có sẵn |
| Cohort retention curve (đường cong tổng) | `mart_cohort_retention` (build hôm nay, dùng `int_cohort_first_order` — retention ĐÚNG) | Có sẵn |
| Cohort retention TÁCH THEO NĂM (so sánh cohort 2016 vs 2022) | `int_cohort_first_order` (intermediate, query được qua Trino, chưa "expose" mart riêng) | **Một phần** — có dữ liệu nhưng chưa có mart tiện dùng cho BI tool thông thường (thường chỉ đọc mart, không đọc intermediate) |
| Cohort tách theo tháng bắt đầu (kiểm định mùa vụ) | Không có mart — tính trong notebook | **Thiếu**, ưu tiên thấp (đây là phân tích 1 lần để kiểm định giả thuyết, không phải nhu cầu theo dõi liên tục) |
| Demographics theo tuổi | Không có mart — `li` join | **Thiếu**, nhưng ưu tiên thấp (đã kết luận tuổi KHÔNG phân biệt hành vi — dashboard theo dõi liên tục ít giá trị) |

### Trang 5 — Đề xuất & kịch bản (Prescriptive / What-if)

Khác biệt về bản chất: đây là tính toán CÓ GIẢ ĐỊNH (`PRICE_EFFECT_SHARE=0.6`, `uplift_scenario=5/10/15%`) — **không nên** là mart tĩnh (giả định thay đổi thì mart phải build lại). Phù hợp hơn với 1 trong 2 hướng:
- BI tool có tính năng "what-if slider" (Power BI/Tableau parameter) — build sẵn mart RAW (chưa áp giả định: margin theo category/region thật, danh sách khách At Risk/Can't Lose Them kèm AOV) rồi để dashboard tự nhân giả định.
- Giữ như hiện tại: notebook/script chạy theo yêu cầu, không cần dashboard real-time cho phần này (đúng bản chất "đề xuất", không phải "theo dõi vận hành").

### Tổng kết ưu tiên nếu triển khai

| Ưu tiên | Việc | Lý do |
|---|---|---|
| ~~1~~ ĐÃ XONG | ~~Mart chẩn đoán (Trang 3)~~ | Xong 2026-08-10 — `mart_revenue_diagnostic_yearly` + `mart_promo_margin_diagnostic` |
| 1 (mới) | Mart cohort theo năm (Trang 4) | Có sẵn dữ liệu nguồn (`int_cohort_first_order`), chỉ cần thêm 1 view/mart nhẹ |
| 3 | Region × Category cross (Trang 2) | Nhu cầu cụ thể (đã dùng ở đề xuất 3), nhưng độ lớn tác động đã đo thấp (0.038 tỷ) — không khẩn |
| Không cần mart | Trang 5 (What-if) | Bản chất động, mart tĩnh không phù hợp |

Đây là **phác thảo yêu cầu, không phải commitment triển khai** — quyết có làm dashboard/mart mới nào ở trên là việc của PO, ngoài phạm vi EDA.
