# Phần A — Thời vụ & biến động theo thời gian

_Phần của [`EDA_FINDINGS.md`](./EDA_FINDINGS.md) — tóm tắt + dashboard đọc ở đó, đây là bản phân tích chi tiết đầy đủ của riêng phần này._


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

