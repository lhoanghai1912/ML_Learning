# Analysis: Phần A — 11 năm doanh thu: chuyện gì đã xảy ra, vì sao, ai đang tạo ra giá trị, và nên làm gì?

- **Vai trò:** Data Analyst — deliverable D4 (Phase 10), mục con của `final_report.md`.
- **Ngày viết:** 2026-07-27.
- **Phạm vi:** Tài liệu này **CHỈ tổng hợp lại** số liệu đã chốt ở Phase 0-4 (đều ✅ done trong `PROGRESS.md`) thành 1 câu chuyện liền mạch cho người đọc kinh doanh — **KHÔNG tính toán/phân tích số liệu mới**. Mọi số trong bài đều truy được về đúng file/mục nguồn.
- **Nguồn:** `PROGRESS.md`; `phase1_descriptive/descriptive_summary.md`; `phase2_diagnostic/diagnostic_summary.md`; `phase3_dashboard/dashboard_rfm_cohort.md`; `phase4_prescriptive/prescriptive_analysis.md` + `ba_action_spec.md`; chart `EDA_Insight/output/phase1..4/`.

**Tóm tắt nhanh (cho người bận):** Doanh thu gãy cấu trúc năm 2019 (giảm 38,6%) và chưa từng hồi phục về mức đỉnh cũ. Nguyên nhân là **sụp khối lượng giao dịch** (ít đơn, ít khách), **không phải do giảm giá**. Khuyến mãi lại là thủ phạm trực tiếp gây 382 ngày bán lỗ gộp. 25,6% khách hàng (Champions) tạo ra 62,9% giá trị — nhưng dữ liệu hành vi khách quay lại theo cohort lại phẳng bất thường, nghi vấn đặc tính dữ liệu mô phỏng. Bốn đề xuất hành động đều có số cụ thể, lớn nhất là đặt giá sàn = giá vốn (+0,462 tỷ VND margin/10 năm) — và rõ ràng: **không giảm giá, không tăng khuyến mãi** để "cứu" doanh thu.

---

## Câu hỏi & giả thuyết

Bốn câu hỏi lớn, xâu chuỗi theo đúng trình tự điều tra đã làm ở Phase 1-4:

1. **Descriptive — Chuyện gì đã xảy ra?** Doanh thu/lợi nhuận 11 năm (2012-2022) biến động ra sao — có xu hướng dài hạn không, mùa vụ/Tết lặp lại thế nào, category/region nào đang gánh doanh thu?
2. **Diagnostic — Vì sao?** Cú sụt năm 2019 đến từ đâu — giá bán, khối lượng, đổi mix sản phẩm hay khuyến mãi? Cơ chế nào khiến gần 1/5 số dòng hàng bán dưới giá vốn?
3. **Dashboard — Ai đang tạo ra giá trị?** Khách hàng nào quan trọng nhất (RFM), có quay lại mua theo thời gian không (cohort), vùng nào chất lượng khách tốt nhất?
4. **Prescriptive — Nên làm gì?** Với những gì đã biết, hành động định lượng nào nên ưu tiên để bảo toàn/tăng margin và giữ khách?

**Giả thuyết ban đầu** (đã kiểm chứng bằng số ở Phase 1-4, không mặc định đúng — xem kết quả xác nhận/bác bỏ trong từng tầng bên dưới): có 1 cú sụt cấu trúc quanh 2019; mùa vụ ổn định qua các năm; Tết tạo pattern giống nhau mỗi năm; break 2019 do giảm giá kích cầu; giá trị khách hàng phân phối lệch (Pareto); khách hàng có xu hướng giảm hoạt động dần theo tuổi quan hệ (decay curve).

---

## Dữ liệu dùng

| Tầng | Nguồn chính | Khoảng thời gian | Phạm vi/lọc |
|---|---|---|---|
| Descriptive (Phase 1) | `sales.csv` (Date, Revenue, COGS); `order_items+products+orders+geography` | 2012-07-04 → 2022-12-31 (3.833 ngày); CAGR loại năm 2012 (chỉ nửa năm) | **gross_revenue** — toàn bộ đơn kể cả `cancelled`, không trừ discount (khớp `sales.csv`, sai lệch build lại từ order_items ~0,0000%) |
| Diagnostic (Phase 2) | `order_items+orders+products+customers+geography+promotions` (join theo FK, sạch 100%) | 2013-01-01 → 2022-12-31 (loại nửa năm 2012 lẻ) | Vẫn dùng **gross** xuyên suốt — đúng định nghĩa khớp target Phần B |
| Dashboard (Phase 3) | `orders+payments+customers+geography` (KHÔNG dùng `sales.csv`) | Snapshot Recency = 2022-12-31; cohort 126 tháng (2012-07 → 2022-12) | Non-cancelled orders; **Monetary = `payments.payment_value`** (net thực thu); mẫu RFM 88.123 khách (có ≥1 đơn non-cancelled), cohort 121.692 khách (loại 238 khách pre-launch) |
| Prescriptive (Phase 4) | `floor_price_simulation_*`, `winback_scenario_by_segment`, `west_margin_replication_*` (đều re-dùng số Phase 1-3, không tính lại) | Toàn kỳ lịch sử 2013-2022 | Đây là **mô phỏng "nếu áp dụng chính sách từ đầu"**, không phải dự báo tương lai |

Toàn bộ số liệu bên dưới lấy nguyên trạng từ 4 file summary trên — không suy diễn thêm số mới.

---

## Findings

### Tầng 1 — Chuyện gì đã xảy ra (Descriptive)

#### 1.1. Doanh thu gãy cấu trúc năm 2019

| Năm | Doanh thu (tỷ VND) | Ghi chú |
|---|---:|---|
| 2013 | 1,66 | |
| 2014 | 1,87 | |
| 2015 | 1,89 | |
| 2016 | 2,10 | đỉnh |
| 2017 | 1,91 | |
| 2018 | 1,85 | |
| **2019** | **1,14** | **rơi 38,6% so với 2018** |
| 2020 | 1,05 | |
| 2021 | 1,04 | đáy |
| 2022 | 1,17 | +12,15% YoY — năm đầu phục hồi rõ |

CAGR toàn kỳ 2013-2022: **-3,80%/năm** doanh thu, **-2,71%/năm** lợi nhuận gộp — nhưng không đều: tăng trưởng 2013-2015 (+6,79%/năm), chững lại 2016-2018 (-6,24%/năm doanh thu, profit giảm chậm hơn -2,52%/năm), rồi **giảm sâu nhất 2019-2021** — doanh thu -4,21%/năm nhưng **lợi nhuận gộp giảm -12,00%/năm, nhanh gấp ~3 lần doanh thu** → margin bị bào mòn thêm chứ không chỉ co quy mô.

*Chart: `../output/phase1/01_daily_ma30.png` (đường doanh thu trung bình động 30 ngày, thấy rõ điểm gãy), `../output/phase1/02_monthly_margin.png`, `../output/phase1/03_heatmap_year_month.png` (heatmap năm×tháng — sáng dần rõ rệt từ 2019).*
*Nguồn: `descriptive_summary.md` mục 2.1.*

#### 1.2. Mùa vụ ổn định, nhưng Tết KHÔNG đồng nhất qua các năm

Mùa vụ theo tháng lặp lại khá ổn định qua 10 năm: đỉnh tháng 4-6 (~12,5-13,0% doanh thu năm/tháng), đáy tháng 11-12 (~4,7-4,8%/tháng) — chênh nhau ~2,7 lần. Riêng tháng 8 có độ lệch chuẩn cao nhất (±2,15 điểm %, nghi do "Mid-Year Sale" chạy năm có năm không). Theo ngày trong tuần: đỉnh thứ Tư, đáy thứ Bảy, chênh 19,8% — khách mua tập trung giữa tuần, khác retail truyền thống.

Ngược lại, **hiệu ứng Tết Nguyên Đán không giống nhau giữa các năm** — biên độ dao động rất khác biệt:

| Năm | Tuần trước Tết | Quanh mồng 1 | Ghi chú |
|---|---:|---:|---|
| 2017 | -42,2% | -9,8% | dip quanh mồng 1 nhẹ nhất |
| **2019** | -3,6% | **-39,8%** | tuần trước nhẹ nhất nhưng dip mồng 1 sâu nhất — bất thường, trùng năm break |
| **2020** | **-47,4%** | -29,0% | tuần trước sâu nhất |
| 2022 | -10,4% | -11,3% | hồi phục tốt nhất (+13,6% ở vùng +15..30 ngày) |

→ Bác bỏ giả thuyết "Tết có pattern cố định mỗi năm". Không nên áp 1 hệ số Tết cứng khi dự báo — cần biến liên tục theo khoảng cách tới Tết.

*Chart: `../output/phase1/04_seasonal_shape.png`, `../output/phase1/05_day_of_week.png`, `../output/phase1/06_tet_effect.png`.*
*Nguồn: `descriptive_summary.md` mục 2.2-2.3.*

#### 1.3. Streetwear gánh gần 80% doanh thu nhưng margin không cao nhất

| Category | % doanh thu | Margin % |
|---|---:|---:|
| **Streetwear** | **79,92%** | 13,24% |
| Outdoor | 15,18% | 16,37% |
| Casual | 2,80% | 11,75% (thấp nhất) |
| GenZ | 2,09% | 19,13% (cao nhất, doanh thu nhỏ nhất) |

| Region | % doanh thu | Margin % |
|---|---:|---:|
| East | 46,48% | 13,64% |
| Central | 30,08% | 13,47% |
| West | 23,44% (nhỏ nhất) | 14,53% (cao nhất) |

Category là trục phân hoá margin mạnh hơn nhiều so với region (11,75-19,13pp vs 13,47-14,53pp). Đối chiếu thêm: gross_revenue toàn 11 năm ≈ 16,43 tỷ VND (khớp `sales.csv`, dùng cho model Phần B) vs net_revenue ≈ 14,23 tỷ VND (đã loại cancelled + discount) — gap 13,37%, hai định nghĩa phục vụ 2 mục đích khác nhau, không phải lỗi dữ liệu.

*Chart: `../output/phase1/22_category_decompose.png`, `../output/phase1/23_region_decompose.png`, `../output/phase1/24_gross_vs_net_reconcile.png`.*
*Nguồn: `descriptive_summary.md` mục 2.4-2.6.*

---

### Tầng 2 — Vì sao (Diagnostic)

#### 2.1. Break 2019 = sụp KHỐI LƯỢNG, KHÔNG phải giá/mix/promo

| Chỉ số | 2018 | 2019 | YoY |
|---|---:|---:|---:|
| Revenue | 1,85 tỷ | 1,14 tỷ | **-38,6%** |
| ASP (giá bán TB/đơn vị) | — | — | **+2,4%** |
| Số lượng bán (qty) | 337.646 | 202.653 | **-40,0%** |
| Số đơn | 69.510 | 41.601 | **-40,2%** |
| Khách active | 37.922 | 27.312 | **-28,0%** |
| AOV (giá trị đơn TB) | — | — | **+2,7%** |

Nếu công ty giảm giá kích cầu, ASP phải giảm còn qty tăng bù lại — **thực tế ngược lại hoàn toàn**: ASP/AOV tăng nhẹ, trong khi qty/đơn/khách active rơi 28-40%. Kiểm tra thêm 2 nghi vấn khác: (a) cường độ khuyến mãi 2019 chỉ 38,4% doanh thu có promo — đúng nhịp "năm lẻ" bình thường (năm lẻ luôn cao hơn năm chẵn ~8-10pp do có thêm 2 promo cố định), không bất thường; (b) mix category cũng chỉ dịch chuyển dần qua 10 năm, không có bước nhảy tại 2019. Kênh marketing cũng không phải nguyên nhân: cả 6 kênh (`order_source`) rơi đồng đều **37,3%-41,0%** (chênh chỉ 3,7 điểm %) — vấn đề hệ thống/toàn platform, không phải 1 kênh cụ thể suy yếu.

**→ Kết luận: đây là vấn đề khối lượng giao dịch (retention/acquisition), KHÔNG phải giá bán, mix, hay khuyến mãi.**

*Chart: `../output/phase2/29_yearly_price_volume_decompose.png`, `../output/phase2/30_promo_intensity_by_year.png`, `../output/phase2/34_channel_revenue_margin_trend.png`.*
*Nguồn: `diagnostic_summary.md` mục 2.1, 2.4.*

#### 2.2. Khuyến mãi → 47,9% dòng bán dưới giá vốn → 382 ngày lỗ gộp

| | % dòng bán dưới giá vốn |
|---|---:|
| Dòng hàng **CÓ** promo | **47,9%** |
| Dòng hàng **KHÔNG** promo | **0,18%** |

Chênh lệch ~266 lần — bằng chứng trực tiếp: gần như toàn bộ hiện tượng bán dưới giá vốn xảy ra khi có khuyến mãi chạy. Đây chính là cơ chế tạo ra **382 ngày bán lỗ gộp** (18,6% tổng dòng `order_items` toàn hệ thống bán dưới giá vốn — phát hiện gốc từ Phase 0 QC, được Phase 2 giải thích cơ chế). Tập trung rõ theo tháng: T12 (47,3%), T9 (34,9%), T7 (31,9%), T8 (29,2%) — trùng khớp lịch chạy `Year-End Sale` (T11→T1), `Fall Launch` (T8→T10), `Urban Blowout` (T7→T9, giảm cứng). Tập trung theo category: **Casual 22,3%** dòng dưới giá vốn, **Streetwear 21,4%** (nhưng vì chiếm ~80% doanh thu nên kéo margin toàn shop mạnh nhất), Outdoor 18,1%, GenZ 9,8%.

*Chart: `../output/phase2/31_unit_price_ratio_by_month.png`, `../output/phase2/32_below_cost_rate_by_category.png`.*
*Nguồn: `diagnostic_summary.md` mục 2.2.*

#### 2.3. Margin West cao hơn: ~40% do mix sản phẩm, ~60% do giá thật

Kiểm soát biến nhiễu bằng "margin mix-adjusted" (áp trọng số category toàn quốc lên margin từng vùng):

| Region | Margin thực tế | Margin mix-adjusted | Chênh lệch do mix (pp) |
|---|---:|---:|---:|
| East | 13,31% | 13,38% | -0,07 |
| Central | 13,15% | 13,24% | -0,10 |
| **West** | **14,20%** | **13,86%** | **+0,35** |

Khoảng cách margin thực tế West-Central = 1,06pp; sau khi loại hiệu ứng mix chỉ còn 0,61pp → **~40% chênh lệch đến từ mix sản phẩm** (West bán Outdoor nhiều hơn hẳn), **~60% còn lại đến từ giá/discount thực sự tốt hơn trong CÙNG category**. Không thể quy hết cho "may mắn về cơ cấu sản phẩm".

*Chart: `../output/phase2/33_category_region_margin_controlled.png`.*
*Nguồn: `diagnostic_summary.md` mục 2.3.*

#### 2.4. Tết × khuyến mãi: tương quan yếu, mẫu quá nhỏ

`corr(số promo trùng Tết, mức dip)` = +0,646 nhưng n=10 năm — không đủ để kết luận nhân quả; với tuần trước Tết, tương quan gần như 0 (+0,065). Giữ khuyến nghị dùng biến liên tục `days_from_tet`, không giả định tương tác Tết-promo.

*Chart: `../output/phase2/35_tet_promo_overlap.png`.*
*Nguồn: `diagnostic_summary.md` mục 2.5.*

#### 2.5. Nói thẳng: nguyên nhân gốc khách rời đi NẰM NGOÀI dữ liệu giao dịch

Đã loại trừ được, bằng số liệu cụ thể và nhất quán: **KHÔNG** phải giá bán giảm (ASP/AOV còn tăng), **KHÔNG** phải đổi mix category hay cường độ khuyến mãi, **KHÔNG** phải 1 kênh marketing cụ thể, **KHÔNG** phải 1 vùng địa lý cụ thể. Nhưng dữ liệu giao dịch nội bộ (`order_items`, `orders`, `promotions`...) **không chứa biến giải thích bên ngoài** (chi tiêu marketing theo thời gian, đối thủ cạnh tranh, thay đổi vận hành/logistics, kinh tế vĩ mô...) để trả lời **tại sao** khách ngừng mua/không quay lại năm 2019. Đây là **giới hạn cứng của bộ dữ liệu hiện có, không phải thiếu sót của phân tích** — cần nói rõ với người đọc thay vì suy đoán thêm.

*Nguồn: `diagnostic_summary.md` mục 3 (Hạn chế #4) và Tổng kết.*

---

### Tầng 3 — Ai đang tạo ra giá trị (Dashboard: RFM & Cohort)

#### 3.1. Pareto rõ rệt: 25,6% khách tạo 62,9% giá trị

| Segment | Số khách | % khách | Tổng Monetary (tỷ VND) | % Monetary | Monetary TB/khách (VND) | Recency TB (ngày) |
|---|---:|---:|---:|---:|---:|---:|
| **Champions** | 22.575 | **25,6%** | 8,95 | **62,9%** | 396.438 | 274 |
| Loyal Customers | 16.974 | 19,3% | 2,88 | 20,3% | 169.914 | 787 |
| Lost | 21.682 | 24,6% | 0,46 | 3,2% | 21.158 | 2.563 |
| At Risk | 7.989 | 9,1% | 0,65 | 4,5% | 80.882 | 2.010 |
| Can't Lose Them | 2.251 | 2,6% | 0,49 | 3,5% | 218.601 | 1.783 |
| Hibernating | 3.327 | 3,8% | 0,27 | 1,9% | 81.035 | 2.399 |
| Promising | 5.375 | 6,1% | 0,21 | 1,4% | 38.217 | 1.105 |
| New Customers | 4.865 | 5,5% | 0,20 | 1,4% | 41.793 | 359 |
| Need Attention | 3.085 | 3,5% | 0,12 | 0,9% | 40.454 | 689 |

Tổng Monetary toàn mẫu RFM (88.123 khách) ≈ 14,23 tỷ VND. **Champions** là "core business" — 62,9% giá trị đến từ 25,6% khách. **Can't Lose Them** (2.251 khách) tuy chỉ 2,6% khách nhưng Monetary/khách 218.601 VND (cao thứ 2 toàn bộ segment) — nhóm "từng rất tốt, đang mất dần", ROI/khách cứu lại cao nhất trong các nhóm rủi ro.

*Chart: `../output/phase3/22_rfm_segment_summary.png`, `../output/phase3/23_rfm_scatter.png`.*
*Nguồn: `dashboard_rfm_cohort.md` mục 1.*

#### 3.2. Cohort retention PHẲNG ~3-6% — data mô phỏng, không có hành vi quay lại thật

Retention trung bình theo tuổi cohort (Phase 3, đo theo `signup_date`, 121.692 khách/126 cohort tháng): **M1 ≈ 3,0% · M3 ≈ 2,9% · M6 ≈ 3,0% · M12 ≈ 2,9%** — gần như không đổi (dao động 2,9-3,4%). PROGRESS.md ghi nhận xác nhận độc lập lần 2 (đo theo tháng đơn hàng đầu tiên, mẫu số khác) cho kết quả cùng cấu trúc phẳng, chỉ khác mức tuyệt đối (~5,3-6,4%) — **hai phép đo độc lập, mẫu số khác nhau, nhưng cùng một kết luận**: đường retention **KHÔNG giảm dần theo tuổi cohort** như mô hình e-commerce thực tế thường thấy (decay curve điển hình: cao ngay sau đăng ký rồi giảm dần).

**Diễn giải (correlation, chưa kiểm chứng bằng thực nghiệm):** khả năng cao là cơ chế sinh dữ liệu mô phỏng gán xác suất mua hàng gần như hằng số theo tháng cho mỗi khách, không phụ thuộc "tuổi" quan hệ với shop — khác hành vi khách hàng thật. **Đây là phát hiện quan trọng nhất của Tầng 3** vì nó dẫn thẳng đến quyết định thiết kế model dự báo ở Phần B (xem câu chuyển tiếp cuối bài).

*Chart: `../output/phase3/24_cohort_retention_heatmap.png`, `../output/phase3/25_cohort_retention_curve.png`.*
*Nguồn: `dashboard_rfm_cohort.md` mục 2; `PROGRESS.md` dòng Phase 3 & Phase 5.*

#### 3.3. West nhỏ nhất nhưng chất lượng khách tốt nhất

| Region | % Champions | % Lost |
|---|---:|---:|
| Central | 22,7% | 27,9% |
| East | 24,1% | 23,4% |
| **West** | **36,1%** | 21,4% (thấp nhất) |

West chỉ 14.741 khách (nhỏ nhất 3 vùng) nhưng per-capita revenue cao hơn Central 62%, cao hơn East 53% (0,249 triệu VND/khách) — hai phương pháp độc lập (RFM segment và per-capita revenue) cùng xác nhận **chất lượng khách West thực sự tốt hơn**, không phải trùng hợp thống kê.

*Chart: `../output/phase3/26_rfm_region_heatmap.png`.*
*Nguồn: `dashboard_rfm_cohort.md` mục 3, mục 5.5 (đối chiếu `customer_demographics.md` mục 7).*

#### 3.4. RFM "Lost" đánh giá thấp mức độ nghiêm trọng thực tế

RFM segment "Lost" chỉ 21.682 khách (24,6% mẫu) — nhưng ngưỡng tuyệt đối (Recency > 365 ngày) cho thấy **65.071 khách (73,8% mẫu, 6,95 tỷ VND giá trị lịch sử) đã hơn 1 năm không mua gì**, gấp 3 lần con số "Lost". Lý do: RFM dùng ngũ phân vị tương đối (luôn ~20-25% tệ nhất bất kể mức độ tệ tuyệt đối), còn churn-risk dùng ngưỡng cố định nên phản ánh đúng quy mô vấn đề hơn.

*Chart: `../output/phase3/27_churn_risk_summary.png`.*
*Nguồn: `dashboard_rfm_cohort.md` mục 4.*

---

### Tầng 4 — Nên làm gì (Prescriptive): 4 đề xuất định lượng

> Nguyên tắc xuyên suốt (từ Tầng 2): **vấn đề là khối lượng/khách, không phải giá** — nên không đề xuất nào theo hướng giảm giá để "cứu" doanh thu.

**Đề xuất 1 — Floor price = giá vốn (quick-win margin lớn nhất)**

Đặt `unit_price_floor = max(unit_price, cogs)` theo từng SKU, không cho bất kỳ dòng hàng nào bán dưới giá vốn dù khuyến mãi giảm sâu thế nào — ưu tiên review Casual/Streetwear và giai đoạn T7-9, T11-12.

Mô phỏng trên toàn bộ 714.669 dòng lịch sử: loại bỏ hoàn toàn 133.052 dòng (18,62%) bán dưới giá vốn → Revenue gross 16,430 tỷ → 16,892 tỷ VND, margin toàn shop **13,80% → 16,15% (+2,36 điểm %)**, tương đương **+0,462 tỷ VND margin toàn kỳ 10 năm** (~46 triệu/năm, riêng Streetwear chiếm +0,409 tỷ nhờ tỷ trọng doanh thu lớn). **Giả định quan trọng: KHÔNG có co giãn cầu theo giá** (giữ nguyên số lượng bán dù giá tăng) — đây là **cận trên lý thuyết**, con số thật khi triển khai sẽ thấp hơn; cần theo dõi `quantity` thực tế sau khi áp dụng.

*Chart: `../output/phase4/36_floor_price_margin_before_after.png`.*

**Đề xuất 2 — Win-back theo RFM: Can't Lose Them trước, At Risk sau**

Ưu tiên ngân sách win-back cá nhân hoá (gọi điện/email + voucher) cho "Can't Lose Them" (2.251 khách, Monetary TB/khách 218.601 VND, im lặng TB 1.783 ngày) trước — ROI/khách cao nhất trong nhóm rủi ro. Sau đó mới đến "At Risk" (7.989 khách, Monetary TB/khách 80.882 VND, im lặng TB 2.010 ngày).

Kịch bản tăng tỷ lệ quay lại +5/10/15pp (dùng AOV/đơn, KHÔNG dùng cả Monetary lịch sử để tránh phóng đại): **Can't Lose Them +2,9 / +5,7 / +8,6 triệu VND**; **At Risk +8,3 / +16,6 / +24,9 triệu VND**. **Giả định quan trọng: đây là kịch bản minh hoạ, tỷ lệ +5/10/15pp KHÔNG suy ra từ dữ liệu thật** (cần A/B test treatment vs control mới có số tin cậy); số liệu trên cũng **chưa trừ chi phí campaign** (voucher, nhân sự).

*Chart: `../output/phase4/37_winback_revenue_scenario.png`.*

**Đề xuất 3 — Nhân rộng cách định giá của West (giá trị chính là bài học vận hành)**

Tìm hiểu vận hành pricing/discount thực tế ở West rồi thử áp dụng sang Central/East, ưu tiên category có gap lớn nhất (Outdoor, Streetwear). Mô phỏng theo hệ số "60% do giá thật" (Tầng 2): **chỉ +38 triệu VND margin/10 năm** (margin toàn shop 3 vùng 13,47% → 13,71%, +0,24pp) — lớn nhất ở Streetwear (Central +14,6 triệu, East +12,6 triệu) và Outdoor (Central +3,4 triệu, East +6,9 triệu); GenZ ở Central/East margin đã cao hơn West nên giữ nguyên, không áp dụng. **Giả định quan trọng: hệ số 60% tính ở cấp vùng, áp máy móc xuống từng category là đơn giản hoá** — con số rất nhỏ, **không phải đòn bẩy tài chính**, giá trị chính là định hướng vận hành (chưa biết "West làm gì khác" cụ thể vì dữ liệu giao dịch không giải thích được).

*Chart: `../output/phase4/38_west_margin_replication_uplift.png`.*

**Đề xuất 4 — KHÔNG giảm giá/tăng khuyến mãi; ưu tiên acquisition West + retention Champions**

Vì Tầng 2 đã chứng minh break 2019 đi cùng ASP/AOV **tăng** chứ không giảm — giảm giá/tăng khuyến mãi thêm sẽ **không** giải quyết đúng nguyên nhân (khối lượng/khách), mà còn làm trầm trọng thêm cơ chế bán dưới giá vốn ở Đề xuất 1. Định hướng chiến lược (không ước tính số $ tuyệt đối vì thiếu dữ liệu chi phí marketing):
- **Acquisition ưu tiên West** — nhỏ nhất về quy mô (14.741 khách) nhưng chất lượng khách tốt nhất (per-capita +62% so Central, 36,1% Champions) — pilot nhỏ trước khi cam kết ngân sách lớn.
- **Retention bảo vệ Champions trước khi mở rộng khách mới** — 22.575 khách, 62,9% giá trị (8,95 tỷ VND), đang hoạt động tốt (Recency TB 274 ngày) — chương trình loyalty/VIP, không giảm giá đại trà.
- **Không cắt ngân sách 1 kênh marketing cụ thể** — cả 6 kênh rơi đồng đều 37-41%, cắt 1 kênh không khắc phục nguyên nhân gốc.

---

## Hạn chế của phân tích

1. **Nguyên nhân gốc khách rời đi/không quay lại năm 2019 KHÔNG xác định được từ dữ liệu giao dịch nội bộ** — đã loại trừ giá, mix, khuyến mãi, kênh, vùng, nhưng không có biến ngoài (chi tiêu marketing, đối thủ cạnh tranh, kinh tế vĩ mô) để trả lời "tại sao". Đây là giới hạn cứng của dữ liệu, không phải thiếu sót phân tích (Tầng 2.5).
2. CAGR/decompose theo giai đoạn dựa trên 2 điểm mốc (năm đầu-cuối) — nhạy với năm chọn, không phải hồi quy xu hướng đầy đủ; chỉ dùng để mô tả hướng đi.
3. Hiệu ứng Tết và tương quan Tết-khuyến mãi tính trên mẫu rất nhỏ (n=10 năm) — hệ số +0,646 không ổn định, không đủ để kết luận nhân quả.
4. Toàn bộ decompose category/region là descriptive/correlational (riêng phần mix-adjustment của West đã kiểm soát biến nhiễu nhưng vẫn là ước lượng điểm, chưa có khoảng tin cậy thống kê).
5. **Cohort retention phẳng là phát hiện correlational trên dữ liệu mô phỏng** — không nên suy diễn sang hành vi khách hàng thật ngoài đời; cần DS xác nhận thêm (đã làm ở Phase 5, xem cầu nối cuối bài).
6. RFM dùng ngũ phân vị tương đối, không phải ngưỡng tuyệt đối — dễ đánh giá thấp mức độ nghiêm trọng (minh hoạ ở mục Lost 24,6% vs 73,8% theo ngưỡng tuyệt đối).
7. Cả 4 đề xuất Prescriptive đều **thiếu dữ liệu chi phí** (marketing spend, vận hành campaign) — mọi số là gộp (gross), chưa phải ROI ròng. Đề xuất 1 và 3 giả định không co giãn cầu (cận trên lý thuyết). Đề xuất 2 dùng tỷ lệ retention minh hoạ, cần A/B test thật trước khi scale ngân sách.
8. Toàn bộ phân tích dùng dữ liệu lịch sử 2012-2022 — không đảm bảo lặp lại y hệt cho 548 ngày dự báo 2023-2024, đặc biệt nếu công ty đổi chính sách promo/pricing sau khi đọc báo cáo này.

---

## Đề xuất

Tóm tắt ưu tiên hành động (số + giả định chi tiết ở Tầng 4):

| # | Đề xuất | Tác động định lượng | Giả định chính |
|---|---|---|---|
| **1** | **Floor price = giá vốn** | **+0,462 tỷ VND margin/10 năm** (13,80%→16,15%, +2,36pp) | KHÔNG co giãn cầu — cận trên lý thuyết |
| 2 | Win-back Can't Lose Them → At Risk | +2,9→+8,6 triệu VND (CLT) / +8,3→+24,9 triệu VND (At Risk), theo kịch bản +5/10/15pp | Tỷ lệ minh hoạ, chưa từ A/B test thật; chưa trừ chi phí |
| 3 | Nhân rộng pricing West | +38 triệu VND/10 năm (margin toàn shop +0,24pp) | Hệ số 60% tính cấp vùng, áp xuống category là đơn giản hoá |
| 4 | **KHÔNG giảm giá/tăng khuyến mãi** — ưu tiên acquisition West + retention Champions | Không định lượng $ (thiếu dữ liệu chi phí marketing) | Break 2019 là vấn đề khối lượng, không phải giá (đã chứng minh ở Tầng 2) |

---

## Chuyển tiếp sang Phần B

Chính phát hiện cohort retention phẳng ~3-6% ở Tầng 3 — không có bằng chứng khách hàng quay lại theo hành vi thật — là lý do Phần B buộc phải bỏ toàn bộ feature dựa trên hành vi khách hàng lặp lại và chuyển sang một hướng tiếp cận khác hẳn để dự báo Revenue/COGS cho 548 ngày tới, được trình bày ngay sau đây.
