# Analysis: Vì sao doanh thu/lợi nhuận sụt mạnh 2019-2021? (Giai đoạn 2 — Diagnostic)

- **Ngày chạy:** 2026-07-20 · `.venv/bin/python` (Python 3.9.6, pandas 2.3.3)
- **Kế thừa:** Phase 0 QC (0 blocker, 3 điểm bắt buộc gross/net/COGS>Revenue — xem mục 0) + Phase 1
  Descriptive (structural break 2019 phát hiện, Tết không đồng nhất, Streetwear/Casual margin thấp).
- **Code nguồn số liệu:** `revenue_diagnostic.py` mục 15-21 (mở rộng từ bản sơ bộ mục 1-14),
  `EDA_diagnostic.ipynb` mục 9-15. Data trung gian: `phase2_diagnostic/data/*.csv` (8 file, mới).
  Chart: `EDA_Insight/output/phase2/29..35_*.png` (không đè 07-14 đã có).
- **Người mới học data đọc được** — mỗi phần có số liệu cụ thể + diễn giải bằng lời trước khi kết luận.

---

## 0. Câu hỏi & giả thuyết

Giai đoạn 1 (Descriptive) để lại 5 câu hỏi "vì sao" chưa trả lời (xem `descriptive_summary.md` mục 4).
Giai đoạn 2 trả lời từng câu bằng số liệu, có kiểm soát biến nhiễu khi cần:

1. **Vì sao 2019-2021 sụt mạnh** (revenue -38,6% chỉ trong 2019, profit giảm nhanh gấp 3 lần revenue)?
   Do (a) giá bán giảm, (b) số đơn/khách giảm, hay (c) đổi mix category/cường độ promotion?
2. **Cơ chế 382 ngày lỗ gộp** (18,6% dòng order_items bán dưới giá vốn — QC W2/W3) hoạt động thế nào?
   Có phải do khuyến mãi, có tập trung ở Casual/Streetwear (2 category margin thấp nhất/tỷ trọng lớn
   nhất) không?
3. **Margin category/region khác nhau do đâu** — do cơ cấu sản phẩm (mix) khác nhau giữa vùng, hay do
   giá/discount thực sự khác nhau?
4. **Marketing channel** (`order_source`) có liên quan gì đến break 2019 không?
5. **Tết** có tương quan với cường độ khuyến mãi đúng dịp không (thay vì coi Tết là hệ số cố định — đã
   bác bỏ ở Phase 1)?

**Giả thuyết ban đầu** (kiểm chứng bằng số, không mặc định đúng):
- H1: break 2019 do giảm giá bán để kích cầu trong bối cảnh khó khăn.
- H2: bán dưới giá vốn là lỗi định giá ngẫu nhiên, không liên quan khuyến mãi.
- H3: region margin cao (West) chủ yếu do bán được giá tốt hơn (không phải do mix sản phẩm).
- H4: 1 kênh marketing cụ thể suy yếu gây ra break 2019.
- H5: Tết có tương quan rõ với khuyến mãi chạy đúng dịp.

*(Spoiler: H1, H2, H4 đều bị bác bỏ bằng số liệu; H3 đúng một phần; H5 chỉ đúng yếu/không chắc chắn — xem chi tiết bên dưới.)*

## 1. Dữ liệu dùng

| Nguồn | Khoảng thời gian | Lọc | Định nghĩa metric |
|---|---|---|---|
| `order_items` + `orders` + `products` + `customers` + `geography` + `promotions` (join theo `product_id`/`order_id`/`customer_id`/`zip`/`promo_id` — tất cả FK sạch 100% theo QC) | 2013-01-01 → 2022-12-31 (loại nửa năm 2012 lẻ, đồng bộ Phase 1/2 sơ bộ) | Không lọc order_status — dùng **gross** (kể cả cancelled), đúng định nghĩa khớp `sales.csv` (sanity check: sai lệch **0.000%**) | `line_revenue = quantity × unit_price`, `line_cogs = quantity × cogs` (catalog) |
| `promotions.csv` (`start_date`, `end_date`, `discount_value`) | 2013-01-31 → 2022-12-31 (50 promo) | Không lọc | Đối chiếu ngày chạy promo với ngày giao dịch/ngày quanh Tết |
| `phase1_descriptive/data/{tet_dates,tet_yearly_stats}.csv` | 2013-2022 (10 cái Tết) | Đọc lại nguyên trạng, không tính lại | `dip_pct`/`pre_week_pct` = % lệch baseline riêng từng năm (đã chốt ở Phase 1) |

**Vì sao dùng gross xuyên suốt Giai đoạn 2 (trừ chỗ nói rõ net)?** Toàn bộ câu hỏi 1-5 đều là câu hỏi
"vì sao target Phần B (sales.Revenue/COGS) biến động" — nên phải dùng đúng định nghĩa gross khớp target
(0.000% sai lệch theo QC) để không lẫn 2 khái niệm. Phần "net thực thu" (đã trừ cancelled + discount +
returns.refund_amount) đã có sẵn ở waterfall 4 bước (mục 4 `diagnostic_revenue.md`, bản sơ bộ trước đó
— Net = 13.05 tỷ, 83.2% gross) — Giai đoạn 2 mở rộng này **không tính lại** con số đó, chỉ tham chiếu.

---

## 2. Findings & Diagnostic

### 2.1. Vì sao 2019-2021 sụt mạnh? — KHÔNG phải giá, mà là khối lượng

Decompose revenue = qty × ASP (giá bán bình quân/đơn vị), đo song song số đơn và khách active:

| Chỉ số | 2018 | 2019 | YoY 2018→2019 |
|---|---:|---:|---:|
| Revenue | 1,85 tỷ | 1,14 tỷ | **-38,6%** |
| ASP (giá bán TB/đơn vị) | — | — | **+2,4%** |
| Số lượng bán (qty) | 337.646 | 202.653 | **-40,0%** |
| Số đơn | 69.510 | 41.601 | **-40,2%** |
| Khách active | 37.922 | 27.312 | **-28,0%** |
| AOV (giá trị đơn TB) | — | — | **+2,7%** |

**Đọc số:** nếu công ty giảm giá để kích cầu, ta sẽ thấy ASP giảm còn qty tăng bù lại — hoàn toàn
NGƯỢC LẠI với những gì quan sát được. ASP và AOV đều **tăng nhẹ**, trong khi số lượng bán, số đơn, và
khách active đều rơi mạnh (28-40%). → **Bác bỏ H1 (giảm giá bán).** Nguyên nhân là **sụp đổ về phía cầu**
(ít khách mua hơn, ít đơn hơn), không phải chiến lược giá của shop.

**Kiểm tra (c) — mix category/cường độ promotion có đổi khác tại 2019 không?**

Join `order_items` + `promotions` theo `promo_id` (FK sạch 100%, 0 bản ghi mồ côi theo QC):

| Năm | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | **2019** | 2020 | 2021 | 2022 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| % doanh thu có promo | 39,9 | 30,8 | 39,4 | 29,5 | 38,4 | 29,4 | **38,4** | 32,0 | 38,9 | 32,0 |

Cường độ promo dao động theo **chu kỳ năm lẻ/năm chẵn** (năm lẻ có thêm 2 promo "Rural Special"/"Urban
Blowout" nên cao hơn ~8-10 điểm %) — **2019 nằm đúng nhịp năm lẻ bình thường, không có gì bất thường.**
Mix category (Streetwear 80-84%, Outdoor 9-20%) cũng chỉ dịch chuyển DẦN qua 10 năm, không có bước nhảy
tại 2019 (xem `07_category_share.png` — bản sơ bộ). → **Bác bỏ giả thuyết (c).**

**Kết luận Q1:** break 2019 đến từ **khối lượng giao dịch sụp đổ** (ít đơn, ít khách active), KHÔNG phải
giá bán, KHÔNG phải mix category, KHÔNG phải cường độ khuyến mãi. Đây là vấn đề **retention/acquisition**
— khớp với phát hiện ở bản sơ bộ trước đó (mục 3 `diagnostic_revenue.md`: doanh thu từ khách MỚI gần như
biến mất sau 2019). *Chart: `29_yearly_price_volume_decompose.png`, `30_promo_intensity_by_year.png`.*

### 2.2. Cơ chế 382 ngày lỗ gộp — khuyến mãi là nguyên nhân trực tiếp

So sánh tỷ lệ dòng hàng bán dưới giá vốn (`unit_price < cogs` catalog) giữa dòng CÓ và KHÔNG có promo:

| | % dòng bán dưới giá vốn |
|---|---:|
| Dòng hàng **CÓ** promo (`promo_id` khác null) | **47,86%** |
| Dòng hàng **KHÔNG** có promo | **0,18%** |

Chênh lệch **~266 lần** — đây là bằng chứng trực tiếp, không phải suy diễn: gần như TOÀN BỘ hiện tượng
bán dưới giá vốn xảy ra khi có khuyến mãi đang chạy. **Bác bỏ H2** (không phải lỗi định giá ngẫu nhiên).

Theo tháng, tỷ lệ dưới giá vốn cao nhất: **T12 (47,3%)**, T9 (34,9%), T7 (31,9%), T8 (29,2%) — trùng
khớp lịch chạy `Year-End Sale` (T11→T1, giảm 20%), `Fall Launch` (T8→T10, giảm 10%), `Urban Blowout`
(T7→T9, giảm cứng 50 nghìn VND/đơn vị, chỉ áp riêng Streetwear). `unit_price/catalog price` trung bình
rơi xuống 0,80-0,88 các tháng T7-8 và T12 — xác nhận đây là giảm giá sâu có chủ đích, không phải lỗi
nhập liệu. Kết quả này khớp và làm rõ thêm phát hiện QC (382 ngày lỗ gộp dồn T7-8, T11-12).

**Có tập trung ở Casual/Streetwear không?**

| Category | % dòng bán dưới giá vốn | % doanh thu category đến từ dòng dưới giá vốn |
|---|---:|---:|
| **Casual** (margin thấp nhất, 11,75% — Phase 1) | **22,30%** | 17,93% |
| **Streetwear** (79,9% doanh thu, margin 13,24%) | **21,36%** | 18,00% |
| Outdoor | 18,10% | 17,20% |
| GenZ (margin cao nhất) | 9,83% | 10,78% |

**Đúng — xác nhận giả thuyết Phase 1:** Casual và Streetwear đúng là 2 category có tỷ lệ dòng bán dưới
giá vốn cao nhất. Vì Streetwear chiếm ~80% tổng doanh thu, chỉ riêng 21,36% dòng dưới giá vốn của
category này đã đủ kéo margin toàn shop xuống — đây là **cơ chế định lượng** giải thích tại sao
"Streetwear gánh doanh thu nhưng margin không cao nhất" (Phase 1 mục 2.4).

**Kết luận Q2:** promotion (đặc biệt `Urban Blowout` giảm giá cứng, `Year-End Sale`/`Fall Launch` giảm
% sâu) là cơ chế trực tiếp gây bán dưới giá vốn, tập trung mạnh nhất ở Casual/Streetwear và các tháng
T7-9, T11-12. *Chart: `31_unit_price_ratio_by_month.png`, `32_below_cost_rate_by_category.png`.*

### 2.3. Margin category/region — bao nhiêu do mix, bao nhiêu do giá thật?

Phase 1 đã mô tả: margin theo region East 13,64% / Central 13,47% / West 14,53% (chênh lệch nhỏ, ~1pp).
Câu hỏi: West cao hơn vì **bán nhiều sản phẩm margin cao hơn** (mix khác), hay vì **giá/discount thực sự
tốt hơn** trong cùng 1 category?

**Phương pháp kiểm soát biến nhiễu:** tính "margin mix-adjusted" — áp trọng số category **toàn quốc**
(Streetwear 80,1%, Outdoor 14,9%, Casual 2,9%, GenZ 2,1%) lên margin riêng từng category của TỪNG
vùng, rồi so với margin thực tế của vùng đó.

| Region | Margin thực tế | Margin mix-adjusted | Chênh lệch do mix (pp) |
|---|---:|---:|---:|
| East | 13,31% | 13,38% | -0,07 |
| Central | 13,15% | 13,24% | -0,10 |
| **West** | **14,20%** | **13,86%** | **+0,35** |

**Đọc số:** khoảng cách margin thực tế West − Central = 14,20% − 13,15% = **1,06pp**. Nếu loại bỏ hiệu
ứng mix (giả định West có cùng cơ cấu category toàn quốc), khoảng cách chỉ còn 13,86% − 13,24% =
**0,61pp**. Tức là:
- **~40% chênh lệch margin West-Central đến từ mix category** — West bán tỷ trọng Outdoor cao hơn hẳn
  (25,8% doanh thu West là Outdoor, so với ~11,5% ở Central/East); Outdoor có margin toàn quốc 16,01%,
  cao hơn Streetwear 12,92%.
- **~60% còn lại đến từ giá/discount thực sự tốt hơn TRONG CÙNG category** — VD Outdoor riêng ở West
  margin 16,74% (cao hơn Outdoor toàn quốc 16,01%); Streetwear ở West margin 13,28% (cao hơn Streetwear
  toàn quốc 12,92%).

**Kết luận Q3 (H3 đúng một phần):** cả 2 yếu tố cùng đóng góp vào margin cao hơn của West — không thể
quy hết cho "cơ cấu sản phẩm may mắn". West thực sự bán giá/discount tốt hơn ở cùng category, không chỉ
là ảo giác thống kê từ mix. *Chart: `33_category_region_margin_controlled.png`.*

### 2.4. Marketing channel — không liên quan đến break 2019

| Kênh (`order_source`) | Sụt revenue 2018→2019 |
|---|---:|
| email_campaign | -41,0% |
| social_media | -39,9% |
| referral | -39,1% |
| organic_search | -37,7% |
| direct | -37,4% |
| paid_search | -37,3% |

Chênh lệch giữa kênh rơi mạnh nhất/nhẹ nhất chỉ **3,7 điểm %** — cực kỳ đồng đều. Margin theo kênh cũng
dao động cùng biên độ theo năm (9-17%), không kênh nào tách khỏi xu hướng chung. **Bác bỏ H4.**

**Kết luận Q4:** break 2019 là vấn đề **hệ thống/toàn platform**, không phải 1 kênh marketing cụ thể suy
yếu — nhất quán với phát hiện độc lập ở mục 2.1 (khối lượng, không phải giá) và bản sơ bộ trước đó (mục
2, 5: region và channel đều gãy đồng loạt). *Chart: `34_channel_revenue_margin_trend.png`.*

### 2.5. Tết x cường độ khuyến mãi — tương quan yếu, mẫu quá nhỏ để kết luận

Đối chiếu số promo (`promotions.csv`) trùng cửa sổ ±30 ngày quanh mồng 1 Tết mỗi năm với `dip_pct`
(mức lệch baseline quanh mồng 1, đã tính sẵn ở `tet_yearly_stats.csv` — Phase 1):

| Năm | Số promo trùng Tết | Promo chính | dip_pct | pre_week_pct |
|---|---:|---|---:|---:|
| 2013 | 1 | Rural Special 2013 | -27,2% | -34,1% |
| 2015 | 2 | Spring Sale 2015; Rural Special 2015 | -14,4% | -19,9% |
| 2016 | 0 | — | -31,8% | -36,1% |
| 2017 | 2 | Year-End Sale 2016; Rural Special 2017 | -9,8% | -42,2% |
| **2019** | 1 | Rural Special 2019 | **-39,8%** (sâu nhất) | **-3,6%** (nhẹ nhất) |
| 2022 | 1 | Year-End Sale 2021 | -11,3% | -10,4% |

*(bảng đầy đủ 10 năm trong `tet_promo_overlap.csv`)*

- `corr(n_promo_overlap_tet, dip_pct) = +0,646` (n=10) — có promo chạy quanh Tết đi cùng dip **nhẹ hơn**
  (promo có thể bù đắp một phần sụt giảm mùa thấp điểm).
- `corr(n_promo_overlap_tet, pre_week_pct) = +0,065` — gần như KHÔNG liên hệ với tuần ngay trước Tết.

**Đọc số cẩn thận:** với n=10 năm, hệ số tương quan 0,65 dao động rất mạnh chỉ với 1-2 điểm dữ liệu đổi
khác — **KHÔNG đủ để kết luận nhân quả**. 2019 là ca đặc biệt: chỉ 1 promo nhưng dip sâu nhất (-39,8%)
trong khi pre-week lại nhẹ nhất (-3,6%) — nhiều khả năng đây là ảnh hưởng lan từ break 2019 tổng thể
(mục 2.1) hơn là do bản thân promo quanh Tết năm đó.

**Kết luận Q5 (H5 không được ủng hộ rõ ràng):** tương quan Tết-promo tồn tại nhưng yếu và mẫu quá nhỏ.
Giữ nguyên khuyến nghị Phase 1: dùng `days_from_tet` (biến liên tục theo từng năm) thay vì hệ số Tết cố
định hoặc giả định tương tác chặt với promo. *Chart: `35_tet_promo_overlap.png`.*

---

## 3. Hạn chế của phân tích

1. **CAGR/decompose theo năm dùng 2 điểm đầu-cuối** (2018 vs 2019) — nhạy với năm chọn, không phải hồi
   quy xu hướng đầy đủ; dùng để mô tả hướng đi (khối lượng vs giá), không ngoại suy chính xác.
2. **Q3 (mix-adjustment) là phương pháp thống kê mô tả, chưa có kiểm định ý nghĩa thống kê** (t-test/CI
   cho chênh lệch margin 0,61pp còn lại sau khi loại mix) — kết luận "60% do giá thật" là ước lượng
   điểm, chưa có khoảng tin cậy.
3. **Q5 (Tết x promo) mẫu chỉ 10 năm** — hệ số tương quan 0,646 không ổn định, dễ đổi dấu/độ lớn nếu
   thêm/bớt 1-2 năm; không dùng làm căn cứ quyết định ngân sách promo dịp Tết.
4. **Chưa xác định được NGUYÊN NHÂN GỐC (root cause) của việc mất khách/mất đơn tại 2019** — đã loại trừ
   được giá, mix, promo, và 1 kênh cụ thể, nhưng dữ liệu hiện có KHÔNG có biến giải thích bên ngoài
   (marketing spend theo thời gian, sự kiện cạnh tranh, thay đổi chính sách vận hành/logistics, tình
   hình kinh tế vĩ mô...) để xác định TẠI SAO khách rời đi/không quay lại. Đây là giới hạn cứng của
   bộ dữ liệu mô phỏng, không phải thiếu sót phân tích.
5. Toàn bộ phân tích dùng dữ liệu lịch sử 2013-2022 — không đảm bảo pattern (VD tương quan Tết-promo,
   cơ chế lỗ gộp theo mùa) sẽ lặp lại y hệt cho 548 ngày dự báo 2023-2024, đặc biệt nếu công ty thay đổi
   chính sách promo sau khi đọc báo cáo này.

## 4. Đề xuất

### Cho Giai đoạn 4 (Prescriptive — phối hợp BA + DA)
1. **Đưa "khối lượng, không phải giá" làm khung diễn giải chính cho mọi đề xuất phục hồi doanh thu** —
   không đề xuất giảm giá/tăng khuyến mãi để "cứu" doanh thu (đã chứng minh giá không phải vấn đề); ưu
   tiên đề xuất tăng khách active/số đơn (acquisition, win-back — phối hợp với `dashboard_rfm_cohort.md`
   mục 5: Champions, Can't Lose Them).
2. **Review giá sàn (floor price) khi chạy promo, đặc biệt `Urban Blowout` (Streetwear, giảm cứng) và
   `Year-End Sale`/`Fall Launch` (giảm % sâu, T7-9 & T11-12)** — 47,9% dòng có promo bán dưới giá vốn là
   con số rất cao, cần đặt ngưỡng giảm giá tối đa theo category (ưu tiên Casual, Streetwear) thay vì áp
   1 mức % cố định cho mọi category.
3. **Nhân rộng bài học West cần tách rõ 2 phần:** ~40% do mix sản phẩm (có thể nhân rộng bằng cách đẩy
   Outdoor ở vùng khác) và ~60% do giá/discount thực thi tốt hơn (cần tìm hiểu vận hành/pricing ở West
   cụ thể là gì trước khi áp dụng nơi khác — dữ liệu hiện tại không giải thích được "tại sao").
4. **Không cắt ngân sách 1 kênh marketing cụ thể để "sửa" break 2019** — vì mọi kênh gãy đồng đều, cắt
   giảm 1 kênh sẽ không khắc phục nguyên nhân gốc (mất khách trên diện rộng).
5. **Thiết kế thêm 1 khảo sát/thu thập dữ liệu ngoài** (nếu có thể) về nguyên nhân mất khách 2019 — vì
   đây là giới hạn cứng của bộ dữ liệu (mục 3.4), Prescriptive khó đưa giải pháp trúng đích nếu chỉ dựa
   vào dữ liệu giao dịch nội bộ.

### Cho Giai đoạn 5 (chốt giả định A→B — phối hợp DS + BA)
1. **Giả định "volume-driven, không phải price-driven" nên đưa vào feature engineering (Giai đoạn 6):**
   model forecast Phần B nên ưu tiên feature phản ánh khối lượng/xu hướng khách (nếu có thể suy ra từ
   lịch sử, VD trend khách active) hơn là feature giá — vì giá không phải driver của biến động lịch sử.
2. **KHÔNG dùng biến "cường độ promotion tương lai" làm feature trực tiếp cho 548 ngày forecast** (đã
   khuyến nghị ở QC #12) — nhưng NÊN dùng **lịch mùa vụ theo tháng** (T7-9, T11-12) như 1 flag "mùa có
   khả năng margin thấp" cho COGS/Revenue model, dựa trên bằng chứng cơ chế đã chứng minh ở mục 2.2 (không
   phải suy đoán).
3. **KHÔNG giả định mối quan hệ Tết-promo chặt chẽ** khi engineer feature — dùng `days_from_tet` độc lập
   theo khuyến nghị Phase 1, vì tương quan ở mục 2.5 quá yếu (n=10) để tin cậy.
4. **Region không nên là trục ưu tiên chính cho model** (đồng nhất với khuyến nghị Phase 1 mục 5) — margin
   chênh lệch vùng nhỏ và đã giải thích được phần lớn bằng mix + hiệu ứng giá cục bộ, ít giá trị thêm cho
   forecast tổng Revenue/COGS toàn quốc.
5. **Break 2019 nên được model hoá như 1 structural break rõ ràng** (không cố gắng fit 1 đường trend
   xuyên suốt 2013-2022) — DS cân nhắc chia dữ liệu train theo giai đoạn (trước/sau 2019) hoặc dùng biến
   chỉ báo (indicator/dummy) cho giai đoạn 2019-2021, vì nguyên nhân là thay đổi cấu trúc về phía cầu chứ
   không phải nhiễu ngẫu nhiên.

---

## Tổng kết

### File đã tạo/sửa
| File | Thay đổi |
|---|---|
| `EDA_Insight/phase2_diagnostic/revenue_diagnostic.py` | Sửa — thêm mục 15-21 (~360 dòng), giữ nguyên mục 1-14 cũ; sửa 2 dòng load `products`/`promotions` để thêm cột `price`/`discount_value`/`start_date`/`end_date`; thêm `li["month"]` |
| `EDA_Insight/phase2_diagnostic/EDA_diagnostic.ipynb` | Sửa — thêm 7 cặp markdown+code (mục 9-15), cập nhật cell load data đồng bộ, cập nhật bảng "Chốt insight" cuối notebook (7 dòng mới) |
| `EDA_Insight/phase2_diagnostic/diagnostic_revenue.md` | Sửa — thêm phần "PHẦN MỞ RỘNG — Giai đoạn 2 chính thức" (mục 9-15 + bảng chốt 5 câu hỏi), giữ nguyên mục 1-8 cũ |
| `EDA_Insight/phase2_diagnostic/diagnostic_summary.md` | **Mới** — báo cáo này |
| `EDA_Insight/DATA_LINEAGE.md` | Sửa — cập nhật sơ đồ luồng Phase 2, thay bảng "RỖNG có chủ đích" bằng bảng lineage đầy đủ 8 file, sửa ghi chú mục 4.3 |
| `PROGRESS.md` | Sửa — Phase 2 chuyển ⬜ pending → ✅ done |
| `EDA_Insight/phase2_diagnostic/data/*.csv` (8 file) | Mới — xem bảng dưới |
| `EDA_Insight/output/phase2/29..35_*.png` (7 chart) | Mới — không đè 07-14 đã có |

**8 file CSV mới (`phase2_diagnostic/data/`):** `yearly_kpi_decompose.csv`, `promo_intensity_by_year.csv`,
`monthly_unit_price_ratio.csv`, `category_below_cost_rate.csv`, `category_region_margin_controlled.csv`,
`region_margin_mix_decomposition.csv`, `channel_revenue_margin_by_year.csv`, `tet_promo_overlap.csv`
(chi tiết nguồn gốc/phép biến đổi từng file: `EDA_Insight/DATA_LINEAGE.md` mục "Phase 2").

### Đã tìm ra nguyên nhân break 2019 chưa?
**Có, ở mức "nhân tố nào KHÔNG phải nguyên nhân" đã rất rõ ràng và chắc chắn** (đã loại trừ bằng số liệu
cụ thể, chênh lệch lớn, nhất quán across nhiều phép đo độc lập):
- **KHÔNG** phải giá bán giảm (ASP +2,4%, AOV +2,7% — thậm chí tăng).
- **KHÔNG** phải đổi mix category hay cường độ khuyến mãi (2019 đúng nhịp năm lẻ bình thường).
- **KHÔNG** phải 1 kênh marketing cụ thể suy yếu (cả 6 kênh rơi đồng đều 37-41%).
- **KHÔNG** phải 1 vùng địa lý cụ thể (theo bản sơ bộ trước — cả 3 region gãy đồng loạt).

**CÒN NGHI VẤN — chưa xác định được nguyên nhân GỐC (root cause) thực sự:** mọi bằng chứng đều chỉ về
"khối lượng giao dịch sụp đổ trên diện rộng" (ít đơn hơn 40%, ít khách active hơn 28%, khách mới gần như
biến mất theo bản sơ bộ trước), nhưng dữ liệu giao dịch nội bộ (order_items, orders, promotions...)
**không chứa biến nào giải thích TẠI SAO** khách ngừng mua/không quay lại — có thể là thay đổi chính
sách vận hành, sự kiện cạnh tranh, thay đổi kinh tế vĩ mô, hoặc đơn thuần là đặc tính của dữ liệu mô
phỏng (tương tự phát hiện "cohort retention phẳng" ở Phase 3 — nghi ngờ cơ chế sinh dữ liệu). **Kết luận
mức phân tích Diagnostic dừng ở đây: "sụp đổ nhu cầu toàn diện, nguyên nhân gốc ngoài phạm vi dữ liệu
hiện có."**

### Phát hiện quan trọng nhất (theo thứ tự ưu tiên đọc)
1. **Break 2019 = khối lượng, không phải giá** — ASP/AOV còn tăng nhẹ trong khi qty/đơn/khách active rơi
   28-40%. Đây là phát hiện định hướng quan trọng nhất cho Prescriptive: đừng giảm giá để "cứu" doanh thu.
2. **Khuyến mãi là cơ chế trực tiếp gây bán dưới giá vốn** — 47,9% dòng có promo bán dưới giá vốn vs 0,18%
   dòng không promo (chênh 266 lần), dồn đúng T7-9 và T11-12 (khớp tuyệt đối lịch promo).
3. **Casual và Streetwear đúng là 2 category bị "cắn" giá vốn nhiều nhất** (22,3% và 21,4% dòng dưới giá
   vốn) — xác nhận trực tiếp giả thuyết margin thấp của Phase 1.
4. **Region margin cao (West) chỉ ~40% do mix sản phẩm, ~60% do giá/discount thực sự tốt hơn** — không
   thể chỉ đổ cho "cơ cấu sản phẩm may mắn" khi đề xuất nhân rộng.
5. **Tương quan Tết-promo yếu và mẫu quá nhỏ (n=10)** — không đủ cơ sở để model hoá tương tác này.

### Giới hạn kỹ thuật khi thực hiện
- venv dự án không có `nbconvert`/`nbclient` (giống Phase 1/3) — không "chạy" notebook qua Jupyter kernel
  thật. Đã verify bằng cách nối toàn bộ source code-cell theo đúng thứ tự và `exec()` bằng
  `.venv/bin/python` (thêm `matplotlib.use("Agg")` để tránh treo do backend GUI `macosx` mặc định) — chạy
  sạch, exit 0, số liệu in ra khớp 100% với báo cáo này và với `revenue_diagnostic.py`. Cell mới trong
  notebook ở trạng thái **chưa bake output** (`execution_count: null`) — cần mở bằng Jupyter/VS Code,
  chọn kernel `.venv`, bấm Run All trước khi trình bày.
- `revenue_diagnostic.py` chạy lại từ đầu bằng `.venv/bin/python EDA_Insight/phase2_diagnostic/revenue_diagnostic.py`
  — ~15-20s, exit 0, chỉ đọc `data/` (không ghi/sửa gì trong đó), 15 chart (07-14 + 29-35) + 8 CSV.

**Khuyến nghị tiếp theo:** xem mục 4 phía trên (Giai đoạn 4 và 5, mỗi bên 4-5 điểm cụ thể).
