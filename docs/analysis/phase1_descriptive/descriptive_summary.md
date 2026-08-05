# Analysis: EDA Descriptive — Trend, Seasonality, Tết, Category/Region (Giai đoạn 1)

- **Ngày chạy:** 2026-07-20 · `.venv/bin/python` (Python 3.9.6, pandas 2.3.3)
- **Kế thừa:** Phase 0 QC (`../phase0_qc/phase0_qc_report.md`) — 0 blocker, 3 điểm bắt buộc tuân thủ đã áp dụng xuyên suốt (xem mục 0)
- **Code nguồn số liệu trong báo cáo này:** `EDA_khoi_dong.ipynb` (mục 4 mới), `EDA_quan_sat.ipynb` (mục 1-9, mục 7-9 mới), `tet_effect.py` (mục 5 mới) — tất cả nằm trong `EDA_Insight/phase1_descriptive/` (đã reorganize theo phase 2026-07-20, xem `EDA_Insight/DATA_LINEAGE.md`). Data trung gian xuất ra nằm ở `phase1_descriptive/data/`, chart ở `EDA_Insight/output/phase1/`.

---

## 0. Câu hỏi & giả thuyết

Giai đoạn 1 (Descriptive) trả lời 5 câu hỏi mô tả, kèm chẩn đoán sơ bộ (why ở mức nông — đào sâu để Giai đoạn 2):
1. Doanh thu/lợi nhuận gộp 11 năm tăng hay giảm? Tốc độ bao nhiêu, có đều không?
2. Mùa vụ lặp lại thế nào theo tháng, theo ngày trong tuần, qua các năm?
3. Tết Nguyên Đán ảnh hưởng doanh thu ra sao, có giống nhau mỗi năm không?
4. Category nào, region nào đang gánh doanh thu — margin có đồng đều không?
5. "Doanh thu" trong `sales.csv` (gross) khác gì với doanh thu thực nhận (net) — lệch bao nhiêu?

**Giả thuyết ban đầu** (sẽ kiểm chứng bằng số, không mặc định đúng):
- H1: có 1 cú sụt cấu trúc quanh 2019 làm giảm quy mô lâu dài.
- H2: mùa vụ tháng ổn định qua các năm (hình dạng giữ nguyên dù biên độ đổi).
- H3: Tết luôn tạo ra 1 pattern giảm-trước/tăng-sau giống nhau mỗi năm.
- H4: 1-2 category/region đang gánh phần lớn doanh thu và có margin khác biệt rõ.

## 1. Dữ liệu dùng

| Nguồn | Khoảng thời gian | Lọc | Ghi chú định nghĩa metric |
|---|---|---|---|
| `sales.csv` (Date, Revenue, COGS) | 2012-07-04 → 2022-12-31 (3.833 ngày, đủ, 0 thiếu) | Không lọc — dùng nguyên trạng | **gross_revenue** = tất cả đơn kể `cancelled`, không trừ discount (khớp order_items 100.000% theo QC) |
| `order_items` + `products` + `orders` + `geography` | join theo `product_id`/`order_id`/`zip`, cùng khoảng thời gian | Mục 4 QC section 7-9 dùng TOÀN kỳ (kể cả nửa năm 2012); mục CAGR loại 2012 (chỉ có nửa năm) | gross cho category/region (đối chiếu sanity check với sales.csv: sai lệch TB **0.0000%**); net cho mục 9 (loại `cancelled`, trừ `discount_amount`) |

**Vì sao dùng gross làm chuẩn cho category/region?** Vì Phase 0 đã chứng minh `gross_revenue` xây lại từ `order_items` khớp `sales.csv` gần tuyệt đối (sai số ~1e-9, do làm tròn số thực) — decompose theo chiều nào (category/region/tháng) cũng tin cậy 100%. Ngược lại nếu build net_revenue rồi so sánh sẽ luôn lệch so với target Phần B — đây là lý do QC W1 yêu cầu tách rõ 2 khái niệm.

---

## 2. Findings

### 2.1. Trend 11 năm — CAGR toàn kỳ & theo giai đoạn

**CAGR (Compound Annual Growth Rate)** = tốc độ tăng trưởng kép/năm, giả định tăng/giảm đều mỗi năm từ điểm đầu đến điểm cuối. Công thức: `(giá trị cuối / giá trị đầu)^(1/số năm) − 1`. Tính trên `gross_revenue` và `gross_profit = gross_revenue − COGS`, loại năm 2012 (chỉ có nửa năm, gộp vào sẽ méo số).

| Giai đoạn | n (năm) | CAGR revenue | CAGR gross_profit | Diễn giải |
|---|---|---:|---:|---|
| **2013 → 2022 (toàn kỳ)** | 9 | **-3.80%/năm** | **-2.71%/năm** | Âm toàn kỳ, nhưng KHÔNG đều — có 1 giai đoạn tăng rồi 1 giai đoạn giảm sâu (xem dưới) |
| 2013-2015 | 2 | +6.79%/năm | +8.36%/năm | Giai đoạn tăng trưởng khởi đầu |
| 2016-2018 | 2 | -6.24%/năm | -2.52%/năm | Bắt đầu suy giảm, profit giảm chậm hơn revenue |
| 2019-2021 | 2 | -4.21%/năm | **-12.00%/năm** | Giảm sâu nhất — profit giảm nhanh gấp 3 lần revenue → margin bị bào mòn thêm, không chỉ do co quy mô |
| 2021 → 2022 (YoY) | 1 | **+12.15%** | — | Năm đầu tiên phục hồi rõ sau đáy |

Doanh thu theo năm (tỷ VND): 2013=1,66 · 2014=1,87 · 2015=1,89 · 2016=2,10 (đỉnh) · 2017=1,91 · 2018=1,85 · **2019=1,14 (rơi 38,6% so 2018)** · 2020=1,05 · 2021=1,04 (đáy) · 2022=1,17.

**Kết luận sơ bộ (H1 — xác nhận):** có "structural break" rõ tại 2019 (annotate sẵn ở chart mục 1 `EDA_quan_sat.ipynb`) — doanh thu rơi ~38,6% chỉ trong 1 năm và không hồi phục về mức 2016-2018 suốt 3 năm sau đó. Đây là câu hỏi quan trọng nhất để Giai đoạn 2 điều tra "vì sao" (không phải do mùa vụ — vì hình dạng mùa vụ trong năm vẫn giữ nguyên qua break, chỉ biên độ bị nén, xem 2.2).

### 2.2. Seasonality

**Theo tháng (tỷ trọng % doanh thu cả năm, trung bình ± độ lệch chuẩn qua 10 năm 2013-2022):**

| Tháng | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| % ± std | 5.11±0.58 | 6.32±0.53 | 9.95±1.01 | 12.5±0.64 | **12.95±0.74** (đỉnh) | 12.18±1.27 | 9.17±0.62 | 8.62±**2.15** | 7.2±0.55 | 6.47±0.53 | 4.83±0.55 | **4.71±0.74** (đáy) |

- Đỉnh mùa vụ: tháng 4-6 (~12,5-13% doanh thu năm/tháng — gần gấp 2,7 lần tháng thấp nhất).
- Đáy: tháng 11-12 (~4,7-4,8%/tháng).
- Tháng 8 có độ lệch chuẩn cao nhất (±2,15 điểm %) — biến động thất thường giữa các năm, nhiều khả năng do "mùa sale giữa năm" (Mid-Year Sale) diễn ra năm có năm không (khớp giả thuyết trong `EDA_quan_sat.ipynb` mục 4).
- **Kết luận (H2 — xác nhận phần lớn):** hình dạng mùa vụ theo tháng lặp lại ổn định qua 10 năm (10 đường tỷ trọng gần trùng nhau, xem chart mục 4), TRỪ tháng 8 — không nên coi mùa vụ là "cố định tuyệt đối" khi forecast.

**Theo ngày trong tuần:** đỉnh thứ Tư, đáy thứ Bảy, chênh lệch cao nhất/thấp nhất = **19,8%**. Khách đặt hàng tập trung giữa tuần, không phải cuối tuần — hành vi mua sắm online khác retail truyền thống (thường cuối tuần đông hơn).

**So sánh giữa các năm (heatmap năm × tháng):** đậm nhất (doanh thu tuyệt đối cao nhất) rơi vào 2016-2018, sáng dần (giảm) rõ từ 2019 — khớp với CAGR âm giai đoạn 2019-2021 ở mục 2.1. Hình dạng mùa vụ trong năm giữ nguyên nhưng "biên độ" (quy mô tuyệt đối) bị nén lại sau break 2019.

### 2.3. Hiệu ứng Tết Nguyên Đán

**Số liệu tổng hợp (trung bình 10 cái Tết 2013-2022, gộp theo triệu VND/ngày):**

| Vùng thời gian (so với mồng 1) | Revenue TB (triệu/ngày) |
|---|---:|
| Cả năm trung bình | 4,29 |
| Đáy trước Tết (-30..-15 ngày) | 2,60 |
| Tuần trước Tết (-7..-1) | 2,94 |
| Mồng 1 ±3 ngày | 3,30 |
| Tuần sau Tết (+1..+7) | 3,34 |
| Hồi phục (+15..+30) | 3,83 |

→ Trong cửa sổ ±30 ngày quanh Tết, doanh thu **thấp nhất ở vùng -30..-15 ngày** (2,60 triệu/ngày), sau đó tăng dần, đạt 3,83 triệu/ngày ở vùng hồi phục +15..+30 — cao hơn đáy khoảng **+47%** (không phải "gấp đôi" như ghi chú cũ trong notebook — số liệu thực tế thấp hơn, đã sửa lại cách diễn đạt cho chính xác).

**Số liệu MỚI — định lượng theo từng năm (baseline riêng từng năm, xem `data/tet_yearly_stats.csv`):**

| Năm | Baseline (triệu/ngày) | Tuần trước Tết | Quanh mồng 1 | Tuần sau Tết | Hồi phục +15..30 |
|---|---:|---:|---:|---:|---:|
| 2013 | 4,54 | -34,1% | -27,2% | -23,7% | -18,3% |
| 2014 | 5,13 | -35,5% | -27,2% | -45,8% | -8,8% |
| 2015 | 5,18 | -19,9% | -14,4% | +18,0% | -4,9% |
| 2016 | 5,75 | -36,1% | -31,8% | -27,0% | -25,2% |
| 2017 | 5,24 | -42,2% | -9,8% | -21,3% | -10,0% |
| 2018 | 5,07 | -35,0% | -22,4% | -21,3% | -16,5% |
| 2019 | 3,11 | -3,6% | **-39,8%** | -25,6% | +2,9% |
| 2020 | 2,88 | -47,4% | -29,0% | -18,1% | -16,8% |
| 2021 | 2,86 | -44,4% | -24,8% | -16,9% | -14,0% |
| 2022 | 3,20 | -10,4% | -11,3% | -46,3% | **+13,6%** |

**Đọc số:** so với baseline (Revenue TB) của CHÍNH năm đó, mọi vùng quanh Tết đều **thấp hơn trung bình năm** (trung bình 10 năm: tuần trước Tết -30,9%, quanh mồng 1 -23,8%, tuần sau -22,8%, hồi phục -9,8%). Điều này không mâu thuẫn với "đáy → hồi phục" ở bảng tổng hợp phía trên — vì tháng 1-2 (quanh Tết) vốn dĩ là mùa thấp điểm trong năm (xem mục 2.2: tháng 1 chỉ chiếm 5,11%, tháng 2 chiếm 6,32% doanh thu năm — thấp hơn nhiều so tháng 4-6). Tết làm vùng thấp điểm này thấp thêm nữa, rồi phục hồi dần nhưng vẫn chưa vượt baseline năm cho tới hết cửa sổ ±30 ngày.

**Kết luận (H3 — BÁC BỎ, không giống nhau mỗi năm):** biên độ dao động quanh Tết KHÁC NHAU rất nhiều giữa các năm — tuần trước Tết dao động từ -3,6% (2019) đến -47,4% (2020); dip quanh mồng 1 từ -9,8% (2017) đến -39,8% (2019). Không có 1 pattern cố định để áp cứng vào model — cần feature `days_from_tet` (biến liên tục) thay vì hệ số cố định theo mùa.

### 2.4. Decompose theo category

*(gross_revenue, toàn kỳ 2012-2022, join `order_items`+`products` — sanity check khớp `sales.csv`: sai lệch TB **0,0000%**)*

| Category | % doanh thu | Margin % (gross_profit/gross_revenue) |
|---|---:|---:|
| Streetwear | **79,92%** | 13,24% |
| Outdoor | 15,18% | **16,37%** (cao nhất) |
| Casual | 2,80% | **11,75%** (thấp nhất) |
| GenZ | 2,09% | 19,13% (margin cao nhất, doanh thu nhỏ nhất) |

**Đọc số:** Streetwear gánh gần 80% doanh thu nhưng margin không cao nhất — GenZ và Outdoor margin tốt hơn dù tỷ trọng nhỏ. Đây là tín hiệu (chưa phải kết luận nhân quả) để Giai đoạn 2 kiểm tra: category Casual (margin thấp nhất 11,75%) có phải nơi tập trung nhiều dòng bán dưới giá vốn (W2 — 18,6% dòng order_items) hay không.

### 2.5. Decompose theo region

*(gross_revenue, toàn kỳ, join `order_items`+`orders`+`geography`)*

| Region | % doanh thu | Margin % |
|---|---:|---:|
| East | 46,48% | 13,64% |
| Central | 30,08% | 13,47% |
| West | 23,44% (nhỏ nhất) | **14,53%** (cao nhất) |

**Đọc số:** chênh lệch margin giữa 3 region khá nhỏ (13,47-14,53 điểm %) so với chênh lệch giữa category (11,75-19,13 điểm %) → **category là trục phân hoá margin mạnh hơn region** ở mức descriptive này.

### 2.6. Gross vs Net revenue — đối chiếu

- **gross_revenue** (tất cả đơn kể cancelled, không trừ discount, join từ `order_items`): tổng 11 năm ≈ **16,43 tỷ VND** — khớp `sales.csv` (dùng cho forecast Phần B).
- **net_revenue** (loại đơn `cancelled`, trừ `discount_amount`, view kinh doanh): tổng 11 năm ≈ **14,23 tỷ VND**.
- **Gap = 13,37%** — đến từ 2 nguồn cộng dồn: (1) đơn `cancelled` (~9,2% tổng số đơn theo QC) vẫn được tính vào gross dù công ty không thu tiền; (2) `discount_amount` bị trừ khi tính net. Đây KHÔNG phải lỗi dữ liệu — là 2 định nghĩa metric phục vụ 2 mục đích khác nhau: **gross cho model Phần B (khớp target chính xác), net cho báo cáo kinh doanh thực tế**. Xem chart tháng đối chiếu 2 đường trong `EDA_quan_sat.ipynb` mục 9.

---

## 3. Hạn chế của phân tích

1. CAGR theo giai đoạn 2-3 năm rất nhạy với năm chọn làm điểm đầu/cuối (chỉ 2 điểm dữ liệu mỗi giai đoạn) — không phải hồi quy xu hướng đầy đủ; dùng để mô tả hướng đi, không dùng để ngoại suy chính xác.
2. Hiệu ứng Tết tính trên band trung bình (7 ngày/dải) — chưa kiểm định thống kê (t-test/CI) có ý nghĩa hay chỉ là nhiễu ngẫu nhiên; để Giai đoạn 2 làm sâu hơn nếu cần.
3. Category/region decompose là **descriptive** (số liệu + margin), CHƯA kiểm soát biến nhiễu (vd: region margin cao có thể do cơ cấu category khác nhau giữa các vùng, chưa tách bạch) — không kết luận nhân quả.
4. `net_revenue` ở mục 2.6 CHƯA trừ `returns.refund_amount` (chỉ trừ cancelled + discount) — nếu trừ thêm hoàn tiền, gap thực tế sẽ lớn hơn 13,37% (đội `revenue_diagnostic.py` đã tính waterfall đầy đủ 4 bước, xem `diagnostic_revenue.md` — không lặp lại ở đây để tránh trùng phạm vi Phase 2).
5. Cả 5 mục dùng dữ liệu lịch sử 2012-2022 — không có nghĩa pattern sẽ lặp lại y hệt cho 548 ngày dự báo 2023-2024 (đặc biệt sau cú break 2019, chưa rõ 2022 là bắt đầu chu kỳ mới hay dao động ngắn hạn).

## 4. Đề xuất cho Giai đoạn 2 (Diagnostic)

1. **Ưu tiên 1 — Điều tra "vì sao" giai đoạn 2019-2021:** doanh thu rơi 38,6% năm 2019 và profit giảm nhanh gấp 3 lần revenue (-12%/năm) — kiểm tra: giá bán trung bình có giảm không, số đơn có giảm không, hay do promotion/mix category thay đổi. Join `promotions` + `order_items` theo `promo_id` (đã sạch 100% theo QC).
2. **Đào sâu margin theo category:** category Casual (margin 11,75% — thấp nhất) và Streetwear (79,9% doanh thu, margin chỉ 13,24%) — kiểm tra tỷ lệ dòng bán dưới giá vốn (W2: 18,6% toàn hệ thống) có tập trung ở 2 category này không, và có trùng với 382 ngày lỗ gộp (T7-8, T11-12) không.
3. **Cơ chế COGS > giá bán:** dùng phân phối `unit_price/price` catalog theo tháng (đã có sẵn hướng dẫn ở `phase0_qc_report.md` mục Giai đoạn 2, khuyến nghị #5) để chứng minh cơ chế giảm giá sâu gây lỗ gộp, đối chiếu với promotion đang chạy.
4. **Tết:** vì biến động quá khác nhau giữa các năm (H3 bác bỏ), nên thử tương quan với biến khác (vd: `promotions` có promo nào rơi đúng dịp Tết một số năm không) thay vì coi Tết là hệ số cố định.
5. **Region:** chênh lệch margin nhỏ giữa 3 vùng — có thể không phải trục ưu tiên cho Phase 2/3 bằng category; nên dồn effort vào category + giai đoạn 2019 trước.

---

## Tổng kết

**File đã sửa (mở rộng, giữ nguyên nội dung cũ):**
- `EDA_khoi_dong.ipynb` — thêm mục 4 "CAGR toàn kỳ & theo giai đoạn" (2 cell code/markdown mới + 1 markdown diễn giải).
- `EDA_quan_sat.ipynb` — thêm mục 7 (category), 8 (region), 9 (gross vs net) — 9 cell mới, chèn trước mục "Chốt feature" (giữ mục đó làm cell cuối).
- `tet_effect.py` — thêm section 5 "Định lượng theo từng năm", sinh thêm file `data/tet_yearly_stats.csv`.

**File mới tạo:**
- `descriptive_summary.md` (file này).
- `data/tet_dates.csv`, `data/tet_yearly_stats.csv` (10 dòng, 2013-2022) — từ `tet_effect.py`.
- Chart mới trong `../output/phase1/`: `22_category_decompose.png`, `23_region_decompose.png`, `24_gross_vs_net_reconcile.png`.

**Cập nhật 2026-07-20 (reorganize theo phase + data lineage):**
- Toàn bộ code/report Phase 1 gom vào `EDA_Insight/phase1_descriptive/`, data trung gian vào `phase1_descriptive/data/`, chart vào `EDA_Insight/output/phase1/` — xem `EDA_Insight/DATA_LINEAGE.md` cho bảng luồng dữ liệu đầy đủ.
- Thêm 2 export MỚI (số liệu lấy nguyên từ code đã có ở mục 2.4-2.6, không tính lại): `data/category_region_decompose.csv` (7 dòng: 4 category + 3 region, cột `dimension`/`dim_value`/`gross_revenue`/`gross_cogs`/`gross_profit`/`margin_pct`/`share_pct`) và `data/daily_revenue_gross_net.csv` (3.833 dòng, cột `Date`/`gross_revenue`/`net_revenue`/`COGS`) — thêm ở `EDA_quan_sat.ipynb` mục 7b và 9b.
- Đã verify lại toàn bộ số liệu sau khi move (exec lại 2 notebook + 2 script bằng `.venv/bin/python`) — khớp 100% với số liệu đã chốt trong báo cáo này (CAGR, seasonality, Tết theo năm, category/region margin, gross/net gap).

**Phát hiện đáng chú ý nhất:**
1. Structural break 2019 — doanh thu rơi 38,6%, profit giảm nhanh hơn revenue trong 2019-2021 (margin bị bào mòn thêm) — CHƯA rõ nguyên nhân, ưu tiên số 1 cho Giai đoạn 2.
2. Hiệu ứng Tết KHÔNG đồng nhất giữa các năm (biên độ dao động rất khác nhau) — bác bỏ giả thuyết ban đầu H3.
3. Streetwear gánh ~80% doanh thu nhưng margin không cao nhất; category nhỏ hơn (GenZ, Outdoor) margin tốt hơn — cơ hội cần điều tra thêm, không kết luận vội.
4. Gross vs net gap 13,37% (chưa tính returns) — nhắc lại: mọi chart/báo cáo PHẢI ghi rõ đang dùng gross hay net để tránh trộn số liệu (đúng yêu cầu QC W1).

**Giới hạn kỹ thuật khi thực hiện:** venv dự án (`.venv/bin/python`) không có `nbconvert`/`nbclient` nên KHÔNG thể "chạy" 2 notebook qua Jupyter kernel thật để bake output vào file. Đã verify bằng cách nối toàn bộ source các code-cell theo đúng thứ tự và `exec()` bằng `.venv/bin/python` — chạy sạch, không lỗi, số liệu in ra khớp với số liệu trong báo cáo này. Cell mới trong 2 notebook hiện ở trạng thái **chưa chạy** (`execution_count: null`, không có output) — cần mở bằng VS Code/Jupyter, chọn kernel `.venv`, bấm Run All để bake output/chart vào notebook trước khi nộp/trình bày.

**Khuyến nghị cho Giai đoạn 2:** xem mục 4 phía trên (5 điểm, ưu tiên #1 là điều tra break 2019).
