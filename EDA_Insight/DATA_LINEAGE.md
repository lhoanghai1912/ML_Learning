# Data Lineage — EDA_Insight (Vin Datathon 2026)

Tài liệu này trả lời 1 câu hỏi duy nhất cho người mới đọc code lần đầu: **"file data này ở đâu ra, nó
đã bị biến đổi thế nào từ dữ liệu gốc, và ai/bước nào dùng nó tiếp theo?"**

Cập nhật: 2026-07-20, sau khi tổ chức lại `EDA_Insight/` theo từng phase (`phase0_qc/`,
`phase1_descriptive/`, `phase2_diagnostic/`, `phase3_dashboard/`, `output/phase{0,1,2,3}/`).

---

## 0. Nguyên tắc đọc bảng dưới

- **`data/` gốc** (`/Dự án datathon2026/data/`) là **read-only tuyệt đối** — không script nào trong
  `EDA_Insight/` được phép ghi/sửa vào đây, chỉ đọc.
- Mỗi phase chỉ đọc **raw `data/`** hoặc **data đã export ở phase trước** — không phase nào tính lại từ
  đầu một con số mà phase trước đã chốt (tránh 2 nguồn sự thật khác nhau cho cùng 1 số liệu).
- Cột **"Gross hay Net"** là khái niệm quan trọng nhất xuyên suốt toàn bộ pipeline (chốt ở Phase 0 W1):
  - **gross_revenue** = `quantity × unit_price`, tính trên **TẤT CẢ đơn kể cả `cancelled`**, KHÔNG trừ
    `discount_amount`. Đây là công thức tái dựng khớp `sales.csv` (target chính thức Phần B) gần tuyệt
    đối (MAPE ~0.000%). Dùng cho **forecast Phần B**.
  - **net_revenue** = `quantity × unit_price − discount_amount`, **loại bỏ đơn `cancelled`**. Đây là
    "doanh thu thật" theo nghĩa kinh doanh. Dùng cho **phân tích/báo cáo kinh doanh** (Phase 1 mục 2.6,
    Phase 2 waterfall, Phase 3 RFM Monetary).
  - Gap giữa 2 định nghĩa ~13-19% (tuỳ có trừ thêm `returns.refund_amount` hay không) — **không phải lỗi
    dữ liệu**, là 2 mục đích khác nhau. Mọi file dưới đây đều ghi rõ đang dùng gross hay net.

## 1. Sơ đồ luồng tổng quát

```
data/ (raw, 14 bảng CSV, READ-ONLY)
   │
   ▼
Phase 0 — QC (phase0_qc/)                     [KHÔNG xuất data — chỉ xuất report]
   │  phase0_data_check.py, phase0_full_qc.py → phase0_qc_report.md
   │  Chốt: công thức gross_revenue khớp sales.csv, 382 ngày lỗ gộp, referential integrity,
   │  16 dòng trùng khoá hợp lệ, snapshot date, v.v. → LÀM NỀN TẢNG cho mọi phép biến đổi ở dưới.
   ▼
Phase 1 — Descriptive (phase1_descriptive/)   [xuất data/*.csv — clean/reconcile]
   │  tet_effect.py            → data/tet_dates.csv, data/tet_yearly_stats.csv
   │  EDA_quan_sat.ipynb mục 7-9 → data/category_region_decompose.csv, data/daily_revenue_gross_net.csv
   ▼
Phase 2 — Diagnostic (phase2_diagnostic/)     [xuất data/*.csv — 2026-07-20, chính thức]
   │  revenue_diagnostic.py, EDA_diagnostic.ipynb → data/{yearly_kpi_decompose,
   │    promo_intensity_by_year,monthly_unit_price_ratio,category_below_cost_rate,
   │    category_region_margin_controlled,region_margin_mix_decomposition,
   │    channel_revenue_margin_by_year,tet_promo_overlap}.csv
   │  Chốt: break 2019 do khối lượng sụp (không phải giá/mix/promo); promo là cơ chế
   │  trực tiếp gây bán dưới giá vốn; region margin ~40% do mix, ~60% do giá thật.
   ▼
Phase 3 — Dashboard A: RFM/Cohort/Churn (phase3_dashboard/)  [xuất data/*.csv — feature-engineered]
   │  customer_demographics.py → data/rfm_customer_segments.csv, data/cohort_retention_matrix.csv,
   │                              data/churn_risk_scores.csv
   ▼
Phase 4 — Prescriptive (phase4_prescriptive/)  [xuất data/*.csv — 2026-07-21, chính thức]
   │  prescriptive_analysis.py → data/{floor_price_simulation_overall,floor_price_simulation_by_category,
   │    winback_scenario_by_segment,west_margin_replication_by_category_region,
   │    west_margin_replication_summary}.csv
   │  Chốt: floor price = cogs loại bỏ bán dưới giá vốn → margin toàn shop +2,36pp (+0,462 tỷ VND
   │    toàn kỳ 10 năm, cận trên lý thuyết, giả định không co giãn cầu); win-back Can't Lose Them/At
   │    Risk là kịch bản minh hoạ (+5/10/15pp retention, cần A/B test thật để xác nhận); nhân rộng
   │    pricing West chỉ +38 triệu VND/10 năm (margin +0,24pp — giá trị chính là định hướng vận hành,
   │    không phải đòn bẩy tài chính lớn); KHÔNG đề xuất giảm giá/tăng khuyến mãi (Phase 2 đã chứng
   │    minh break 2019 là vấn đề khối lượng, không phải giá).
   ▼
Phase 5 — Chốt giả định A→B (phase5_model_assumptions/)  [xuất data/*.csv — verify độc lập]
   │  verify_target_and_cohort.py → data/target_reconcile_sample.csv (3,833 dòng, đối chiếu
   │    sales.csv vs rebuild gross từ order_items — MAPE 0.000000%),
   │    data/cohort_retention_by_first_order.csv (13 dòng, verify độc lập retention phẳng bằng
   │    cohort = tháng đơn hàng đầu tiên, KHÔNG dùng lại signup_date của Phase 3)
   │  Chốt: target = gross demand xác nhận lại; retention phẳng ~5-6% mọi offset (xác nhận độc
   │    lập phát hiện Phase 3, khả năng cao do cơ chế sinh dữ liệu độc lập theo thời gian) → loại
   │    bỏ feature hành vi khách hàng lặp lại khỏi khung feature Giai đoạn 6; chốt 5 giả định
   │    model (break 2019 = dummy indicator, mùa vụ margin thấp T7-9/T11-12 cho COGS, days_from_tet
   │    liên tục, không dùng promo tương lai, region không làm trục chính) — xem
   │    `phase5_model_assumptions/model_assumptions.md`.
   ▼
Phase 6-10 (chưa tới) — Feature engineering thuần lịch, baseline model, model theo quý +
   ensemble, validation, báo cáo cuối — sẽ ĐỌC LẠI các file data/*.csv ở Phase 1/3/5 làm input,
   không tính lại từ raw.
```

## 2. Raw data (`/Dự án datathon2026/data/`, chỉ đọc)

| Bảng | Grain | Vai trò trong pipeline |
|---|---|---|
| `sales.csv` | 1 dòng/ngày (`Date, Revenue, COGS`) | **Target chính thức Phần B** — Revenue/COGS đã xác nhận = gross (Phase 0). `sample_submission.csv` yêu cầu ghi đè đúng 2 cột này cho 548 ngày 2023-2024. |
| `orders.csv` | 1 dòng/đơn | `order_status`, `order_date`, `customer_id`, `zip`, `order_source` — trục lọc cancelled/non-cancelled dùng khắp mọi phase. |
| `order_items.csv` | 1 dòng/sản phẩm-trong-đơn | Nguồn tái dựng `gross_revenue`/`net_revenue` theo mọi chiều (ngày/category/region/tuổi...). |
| `products.csv` | 1 dòng/SKU | `category`, `cogs`, `price` catalog. |
| `customers.csv` | 1 dòng/khách | `signup_date` (cohort), `age_group`/`gender` (đã kết luận "phẳng", không dùng làm feature), `zip`. |
| `geography.csv` | 1 dòng/zip | `zip → region` (referential integrity 100%, theo QC). |
| `payments.csv` | 1 dòng/đơn | `payment_value` = net thực thu/đơn (khớp 100% công thức `qty×price − discount`) — dùng làm Monetary ở RFM. |
| `promotions.csv`, `returns.csv` | 1 dòng/promo, 1 dòng/return | Dùng ở Phase 2 (waterfall, promo effect) — chưa persist CSV riêng. |

## 3. Bảng lineage chi tiết — từng file data trung gian

### Phase 1 — Descriptive (`phase1_descriptive/data/`)

| File | Nguồn gốc (bảng raw) | Phép biến đổi | Tạo bởi | Dùng tiếp ở đâu |
|---|---|---|---|---|
| `tet_dates.csv` | Không đọc `data/` — sinh từ thư viện `lunardate` (mồng 1 âm lịch → dương lịch, 2012-2024) | Tính trực tiếp `LunarDate(year, 1, 1).toSolarDate()` cho từng năm | `tet_effect.py` | Feature lịch âm `days_from_tet` cho Phase 6 (feature engineering thuần lịch) và mọi chart "hiệu ứng Tết". |
| `tet_yearly_stats.csv` | `sales.csv` (`Date, Revenue`) + `tet_dates.csv` | Với mỗi năm 2013-2022: lấy baseline = Revenue TB **của chính năm đó**; tính % lệch baseline cho 4 band (`pre_week`, `dip`, `post_week`, `recovery`) trong cửa sổ ±30 ngày quanh mồng 1. KHÔNG lọc cancelled (dùng nguyên `sales.csv` = gross). | `tet_effect.py` | `descriptive_summary.md` mục 2.3 (bác bỏ giả thuyết "Tết đồng nhất mỗi năm" H3); input cho Phase 6 khi engineer feature Tết theo năm thay vì hệ số cố định. |
| `category_region_decompose.csv` | `order_items` + `products` (category, cogs) + `orders` (zip, order_status) + `geography` (region) | Join full outer theo `product_id`/`zip`; `gross_revenue = qty×unit_price`, `gross_cogs = qty×cogs`; **KHÔNG loại `cancelled`** (gross, toàn kỳ 2012-2022, khớp sanity check với `sales.csv` sai lệch 0.0000%); group theo `category` rồi theo `region`, gộp lại 1 file với cột `dimension` (category/region) + `dim_value`. | `EDA_quan_sat.ipynb` mục 7-8 (export thêm ở mục 7b) | `diagnostic_revenue.md` (Phase 2, đối chiếu xu hướng category theo năm); Phase 4 (ưu tiên ngân sách category/region theo margin); Phase 6 (feature category-mix nếu cần). |
| `daily_revenue_gross_net.csv` | `sales.csv` (`Date, Revenue, COGS` = gross có sẵn) + `order_items`+`orders` (tính `net_revenue` = loại `cancelled`, trừ `discount_amount`, group theo ngày) | `gross_revenue`/`COGS` lấy **trực tiếp** từ `sales.csv` (không tính lại — đã xác nhận = gross ở Phase 0); `net_revenue` tính từ `order_items` theo đúng công thức net đã chốt, group theo `order_date`, join vào theo `Date`. Ngày không có đơn non-cancelled → `net_revenue = 0`. | `EDA_quan_sat.ipynb` mục 9 (export thêm ở mục 9b) | Đối chiếu gross vs net theo ngày cho bất kỳ phase nào cần "doanh thu thật" thay vì gross demand; input tham khảo cho Phase 2 waterfall (đối chiếu số ngày/tháng cụ thể thay vì chỉ tổng toàn kỳ). |

### Phase 2 — Diagnostic (`phase2_diagnostic/data/`)

Theo `PROGRESS.md`, Giai đoạn 2 (Diagnostic) đã chuyển từ "pending" sang **chính thức hoàn thành**
2026-07-20 — mở rộng `revenue_diagnostic.py` (mục 15-21) + `EDA_diagnostic.ipynb`, trả lời 5 câu hỏi
bắt buộc (break 2019, cơ chế lỗ gộp, margin category/region có kiểm soát mix, marketing channel, Tết
x promo). Chart mới: `output/phase2/29..35_*.png` (không đè 07-14 đã có ở bản sơ bộ). Toàn bộ dùng
**gross** (`line_revenue = quantity × unit_price`, không loại cancelled — khớp `sales.csv` 0.000%,
đồng bộ Phase 1), trừ mục margin dùng `line_cogs = quantity × cogs` catalog.

| File | Nguồn gốc (bảng raw) | Phép biến đổi | Tạo bởi | Dùng tiếp ở đâu |
|---|---|---|---|---|
| `yearly_kpi_decompose.csv` | `order_items+orders+products` (`li`), lọc năm 2013-2022 | Theo năm: `revenue`, `qty`, `ASP=revenue/qty`, `n_orders`, `n_active_cust`, `AOV=revenue/n_orders` | `revenue_diagnostic.py` mục 15 | Trả lời Q1 (break 2019 do khối lượng, không do giá) — input Phase 5 khi chốt giả định feature "volume-driven, không phải price-driven". |
| `promo_intensity_by_year.csv` | `order_items` (`promo_id`) + `promotions`, join theo `promo_id` (FK sạch 100% theo QC) | Theo năm: `% doanh thu có promo`, `% dòng hàng có promo`, `avg_discount_value` dòng có promo, `n_promo_active_overlap` (đếm promo có khoảng ngày chồng lấn năm đó) | `revenue_diagnostic.py` mục 16 | Loại giả thuyết "đổi cường độ promo gây break 2019" — input Phase 4 (ngân sách promo theo mùa, không theo "sửa lỗi 2019"). |
| `monthly_unit_price_ratio.csv` | `order_items+products` (`unit_price`, `price` catalog, `cogs`) | Theo tháng (gộp 2013-2022): `mean/median price_ratio = unit_price/price`, `% dòng dưới giá vốn` (`unit_price<cogs`), tách riêng theo có/không `promo_id`, `promo_active_days_sum_alltime` (tổng ngày promo chồng lấn tháng đó, cộng dồn mọi năm/mọi promo) | `revenue_diagnostic.py` mục 17 | Chứng minh cơ chế 382 ngày lỗ gộp (QC W2/W3) = do promo, không phải lỗi giá; input Phase 6 (feature "promo season flag" theo tháng thay vì biến promo tương lai không có). |
| `category_below_cost_rate.csv` | `order_items+products` | Theo category: `n_lines`, `% dòng dưới giá vốn`, `revenue_below_cost`, `% doanh thu đến từ dòng dưới giá vốn` | `revenue_diagnostic.py` mục 18 | Xác nhận Casual/Streetwear bị "cắn" giá vốn nhiều nhất — input Phase 4 (review giá sàn 2 category này trước mùa sale). |
| `category_region_margin_controlled.csv` | `order_items+products+orders+geography` | Cross-tab `region × category`: `revenue`, `cogs`, `margin_pct`, `share_in_region_pct` (tỷ trọng category trong doanh thu vùng đó) | `revenue_diagnostic.py` mục 19 | Bảng chi tiết nền cho `region_margin_mix_decomposition.csv` — dùng khi cần soi margin 1 category cụ thể theo từng vùng. |
| `region_margin_mix_decomposition.csv` | Tính từ `category_region_margin_controlled` + trọng số category toàn quốc (`nat_w`) | `actual_margin_pct` (margin thật của vùng) vs `mix_adjusted_margin_pct` (áp trọng số category toàn quốc lên margin riêng từng category của vùng đó) vs `mix_effect_pp` (chênh lệch = phần margin do mix) | `revenue_diagnostic.py` mục 19 | Kết luận: margin West cao ~40% do mix (nhiều Outdoor), ~60% do giá/discount thật tốt hơn — input Phase 4 khi nhân rộng bài học West sang vùng khác (không chỉ đổi mix sản phẩm). |
| `channel_revenue_margin_by_year.csv` | `order_items+orders` (`order_source`) | Theo năm × `order_source`: `revenue`, `cogs`, `margin_pct` | `revenue_diagnostic.py` mục 20 | Xác nhận break 2019 đồng đều mọi kênh (không phải 1 kênh yếu đi) — input Phase 4 (không cắt ngân sách 1 kênh cụ thể để "sửa" break 2019). |
| `tet_promo_overlap.csv` | `promotions` (`start_date/end_date`) + `phase1_descriptive/data/{tet_dates,tet_yearly_stats}.csv` | Với mỗi năm: đếm `n_promo_overlap_tet` (promo có khoảng ngày chồng lấn cửa sổ ±30 ngày quanh mồng 1), liệt kê `promo_ids_overlap`, join với `dip_pct`/`pre_week_pct` đã tính sẵn ở Phase 1 | `revenue_diagnostic.py` mục 21 | `corr(n_promo_overlap_tet, dip_pct)=+0.65` (n=10, yếu/gợi ý) — input Phase 6 khi cân nhắc feature Tết có tương tác với lịch promo hay để độc lập (`days_from_tet` thuần lịch, theo khuyến nghị Phase 1). |

### Phase 3 — Dashboard A: RFM/Cohort/Demographics/Churn (`phase3_dashboard/data/`)

| File | Nguồn gốc (bảng raw) | Phép biến đổi | Tạo bởi | Dùng tiếp ở đâu |
|---|---|---|---|---|
| `rfm_customer_segments.csv` | `orders` (loại `cancelled`) + `payments.payment_value` | **Mẫu**: 88,123 khách có ≥1 đơn **non-cancelled** (khác 90,246 khách có ≥1 đơn bất kỳ trạng thái — 2,123 khách chỉ toàn đơn cancelled bị loại). `recency_days` = số ngày từ đơn gần nhất tới snapshot `2022-12-31`; `frequency` = số đơn non-cancelled; `monetary` = tổng `payment_value` (net thực thu/đơn, đã QC khớp 100%). R/F/M chấm điểm 1-5 bằng `qcut` trên rank (ngũ phân vị); `segment` gán theo rule (Champions/Loyal/Lost/At Risk/...). | `customer_demographics.py` (mục RFM Segmentation) | Input trực tiếp cho `churn_risk_scores.csv` (cùng phase); Phase 4 (đề xuất ngân sách theo segment); Phase 5 (DS xác nhận lại ngưỡng RFM trước khi đưa vào production); CLV modeling nếu làm ở Phase 6+. |
| `cohort_retention_matrix.csv` | `customers.signup_date` (loại 238 khách pre-launch `signup_date < 2012-07-04`) + `orders` (non-cancelled) | Cohort = tháng `signup_date`. Với mỗi cohort, tính % khách còn active (≥1 đơn non-cancelled) ở tháng offset 0-15 kể từ signup; mẫu số = **toàn bộ khách signup tháng đó** (kể cả chưa từng mua) — đúng chuẩn retention. 126 cohort tháng (2012-07 → 2022-12) × 16 cột offset. | `customer_demographics.py` (mục Cohort Retention) | Phase 5 — DS phải xác nhận lại phát hiện "retention PHẲNG ~3% mọi offset" (nghi ngờ đặc tính mô phỏng) trước khi giả định decay curve kiểu BG/NBD trong model CLV. |
| `churn_risk_scores.csv` | `rfm_customer_segments.csv` (tier rule-based, toàn mẫu 88,123 khách) + logistic regression numpy thủ công (time-split, cutoff `2022-06-30`) | Cột `churn_tier`: rule tuyệt đối theo `recency_days` (>365 = "Đã rời bỏ", >180 & trend≤0 = "Rủi ro cao", ...). Cột `p_churn_logistic`: xác suất từ model logistic huấn luyện trên 87,589 khách có đơn ≤ cutoff (train 70,071/test 17,518, AUC 0.773) — áp dụng cho **toàn bộ** 87,589 khách trong `hist_agg`, không chỉ tập test; khách chỉ có đơn SAU cutoff (~535 khách, phần chênh giữa 88,123 và 87,589) để **NaN** ở cột này (không suy diễn/bịa số). Cột `used_in_logistic_test_set` đánh dấu 17,518 khách dùng để tính Accuracy/Precision/Recall/AUC ở báo cáo — phân biệt với phần còn lại (in-sample, dùng để train). | `customer_demographics.py` (mục Churn Risk + Logistic regression) | Phase 4 (target list ưu tiên campaign win-back theo tier); Phase 5 (DS thay bằng sklearn logistic chuẩn + tối ưu ngưỡng rule theo F1/lợi nhuận kỳ vọng, có `class_weight` cho mất cân bằng 87.4% churn). |

### Phase 4 — Prescriptive (`phase4_prescriptive/data/`)

Mô phỏng lịch sử ("nếu áp dụng sớm hơn thì...") cho 3/4 đề xuất định lượng — đề xuất thứ 4
(acquisition/retention) không xuất CSV vì không có dữ liệu chi phí marketing để ước tính số tuyệt đối,
chỉ nêu định hướng chiến lược (xem `prescriptive_analysis.md` mục 4).

| File | Nguồn gốc (bảng raw) | Phép biến đổi | Tạo bởi | Dùng tiếp ở đâu |
|---|---|---|---|---|
| `floor_price_simulation_overall.csv` | `order_items+orders+products` (gross, toàn bộ 714,669 dòng lịch sử, không lọc năm/trạng thái đơn) | `unit_price_floor = max(unit_price, cogs)`; so sánh `revenue`/`margin_pct` thực tế vs giả định floor price (COGS catalog không đổi) | `prescriptive_analysis.py` (Đề xuất 1) | Nền cho khuyến nghị "đặt giá sàn = cogs khi chạy promo" — margin toàn shop +2.36pp nếu áp dụng, giả định không co giãn cầu (nêu rõ ở mục Rủi ro). |
| `floor_price_simulation_by_category.csv` | Như trên, group theo `category` | Margin tăng thêm (VNĐ, điểm %) theo từng category | `prescriptive_analysis.py` (Đề xuất 1) | Xác nhận Streetwear đóng góp phần lớn margin tăng thêm (do tỷ trọng doanh thu, không phải % tăng/dòng cao nhất) — ưu tiên review floor price category này trước. |
| `winback_scenario_by_segment.csv` | `phase3_dashboard/data/rfm_customer_segments.csv` (không tính lại từ raw) | Với segment "Can't Lose Them"/"At Risk": `AOV = tổng monetary/tổng frequency`; kịch bản `+5/10/15 điểm % retention` → `doanh thu tiềm năng = n_khách × X% × AOV` | `prescriptive_analysis.py` (Đề xuất 2) | Target list ưu tiên ngân sách win-back — con số là KỊCH BẢN minh hoạ, cần thiết kế A/B test thật trước khi scale (theo khuyến nghị `dashboard_rfm_cohort.md`). |
| `west_margin_replication_by_category_region.csv` | `phase2_diagnostic/data/category_region_margin_controlled.csv` (không tính lại từ raw) | Với mỗi category ở Central/East: `gap_pp = margin(West) − margin(vùng)` (chặn ≥0); `target_margin = margin(vùng) + 60%×gap_pp` (hệ số 60% lấy từ `region_margin_mix_decomposition.csv` Phase 2); `margin tăng thêm = cogs_cũ − cogs_mới` | `prescriptive_analysis.py` (Đề xuất 3) | Chi tiết từng category — dùng khi cần biết category nào đáng ưu tiên nhân rộng pricing West trước (Outdoor, Streetwear có gap dương lớn nhất). |
| `west_margin_replication_summary.csv` | Tổng hợp từ file trên + `category_region_margin_controlled.csv` | Margin toàn shop (3 vùng gộp) trước/sau kịch bản 60% | `prescriptive_analysis.py` (Đề xuất 3) | Kết luận: +38 triệu VND/10 năm (margin +0.24pp) — con số nhỏ, giá trị chính là định hướng vận hành. |

Chart mới: `EDA_Insight/output/phase4/36_floor_price_margin_before_after.png`,
`37_winback_revenue_scenario.png`, `38_west_margin_replication_uplift.png`.

### Phase 5 — Chốt giả định A→B (`phase5_model_assumptions/data/`)

| File | Nguồn gốc (bảng raw) | Phép biến đổi | Tạo bởi | Dùng tiếp ở đâu |
|---|---|---|---|---|
| `target_reconcile_sample.csv` | `sales.csv` + `order_items+orders+products` | Rebuild `gross_revenue_line = quantity×unit_price`, `gross_cogs_line = quantity×cogs` (catalog), group theo `order_date`, **giữ nguyên cancelled, không trừ discount**, join với `sales.csv` theo `Date`, tính `%` lệch tuyệt đối từng ngày. 3,833 dòng, MAPE 0.000000%. | `verify_target_and_cohort.py` (Nhiệm vụ 1) | Xác nhận độc lập lại kết luận Phase 0 W1 (target = gross demand) — căn cứ số cho `model_assumptions.md`. |
| `cohort_retention_by_first_order.csv` | `orders` (non-cancelled) — cohort = **tháng đơn hàng KHÔNG-cancelled ĐẦU TIÊN** của khách (khác Phase 3 dùng `signup_date`) | Với mỗi offset 0-12 tháng: mẫu số = tổng khách của các cohort đủ thời gian quan sát tới offset đó; % active = có ≥1 đơn non-cancelled đúng offset đó. 13 dòng. | `verify_target_and_cohort.py` (Nhiệm vụ 3) | Verify độc lập phát hiện "retention phẳng" của Phase 3 bằng cách đo khác (first-order thay vì signup) — cùng kết luận: PHẲNG (std 0.40pp qua offset 1-12), không có decay → chốt loại bỏ feature hành vi khách hàng lặp lại khỏi khung feature Giai đoạn 6, xem `model_assumptions.md` Nhiệm vụ 3. |

Chart mới: `EDA_Insight/output/phase5/36_cohort_retention_by_first_order_verify.png`.

### Phase 6 — Feature engineering thuần lịch (`phase6_features/data/`)

**Phần de (Giai đoạn 6a) — ma trận feature train/forecast.** Chạy độc lập với phần ds cùng phase
(ds phụ trách `feature_spec.md`, `feature_target_correlation.csv`, `output/phase6/screen_*` — không
liệt kê ở đây, ds tự cập nhật phần của mình). Script: `build_features.py`, chi tiết đầy đủ ở
`phase6_features/feature_pipeline.md`.

| File | Nguồn gốc (bảng raw/phase trước) | Phép biến đổi | Tạo bởi | Dùng tiếp ở đâu |
|---|---|---|---|---|
| `tet_dates_extended.csv` | Không đọc `data/` — sinh từ `lunardate`, đối chiếu với `phase1_descriptive/data/tet_dates.csv` (chỉ đọc, không ghi đè) | Mồng 1 Tết dương lịch 2012-2025 (mở rộng 2 năm so với Phase 1, thêm 2023-2025 cho horizon forecast); dừng script nếu lệch 2013-2022 so với Phase 1 (đã kiểm: khớp 100%) | `build_features.py` bước 1 | Input tính `days_from_tet` cho cả `features_train.csv` và `features_forecast.csv`. |
| `features_train.csv` | `data/sales.csv` (gross, `Date,Revenue,COGS`) + `tet_dates_extended.csv` | 1 dòng/ngày (2012-07-04 → 2022-12-31, 3,833 dòng), 17 cột feature GHIM thuần lịch (`year`, `month`, `quarter`, `day_of_week`, `day_of_month`, `month_sin/cos`, `dow_sin/cos`, `is_post_2019`, `is_post_2019_transition`, `days_from_tet`, `is_low_margin_season`, `trend_index` neo `2012-07-04=0`, `is_holiday_302_305`, `is_holiday_qk`, `is_christmas`) + `is_partial_year_2012` + join nguyên trạng `Revenue`/`COGS` (gross, KHÔNG tính lại) từ `sales.csv`. KHÔNG có feature hành vi khách/promo tương lai/region (chốt Phase 5 G4/G5/Nhiệm vụ 3). | `build_features.py` bước 4 | Input train Giai đoạn 7 (baseline model Revenue/COGS độc lập). |
| `features_forecast.csv` | `data/sample_submission.csv` (`Date`) + `tet_dates_extended.csv` | Đúng 548 dòng (2023-01-01 → 2024-07-01, tập ngày khớp 100% `sample_submission.csv`), CÙNG hàm `build_calendar_features()` như train (không leakage, không lệch định nghĩa), CHỈ feature, KHÔNG có `Revenue`/`COGS`. | `build_features.py` bước 5 | Input predict Giai đoạn 9 (sinh forecast 548 ngày, đối chiếu format `sample_submission.csv`). |

Chart QC: `EDA_Insight/output/phase6/qc_month_dow_distribution.png` (so phân bố `month`/`day_of_week`
giữa train và forecast — chênh lệch `month` là do cấu trúc horizon 1.5 năm dương lịch, không phải lỗi,
giải thích chi tiết ở `feature_pipeline.md` mục 4).

## 4. Ghi chú quan trọng khi dùng lại các file trên

1. **Không trộn gross và net khi join/so sánh giữa các file.** `category_region_decompose.csv` và
   `tet_yearly_stats.csv` là **gross** (khớp `sales.csv`, dùng cho Phần B); `rfm_customer_segments.csv`
   và `churn_risk_scores.csv` dùng **Monetary = net** (`payment_value`, loại cancelled, dùng cho phân
   tích khách hàng). `daily_revenue_gross_net.csv` là file DUY NHẤT có cả 2 cột cạnh nhau để đối chiếu.
2. **`daily_revenue_gross_net.csv` CHƯA trừ `returns.refund_amount`** — chỉ loại cancelled + trừ
   discount. Nếu cần net "thực thu cuối cùng" (trừ cả return), dùng số waterfall 4 bước ở Phase 2
   (`diagnostic_revenue.md` mục 4: Net thực thu = 13.05 tỷ, tức 83.2% gross — thấp hơn con số net 2 bước
   ở Phase 1 vì trừ thêm returns).
3. **`phase2_diagnostic/data/` đã hết trống** (2026-07-20) — 8 file CSV liệt kê ở mục 3 phía trên, cùng
   quy ước đặt tên với Phase 1/3 (snake_case). Toàn bộ dùng gross (khớp `sales.csv`), trừ 2 file margin
   dùng thêm `cogs` catalog — không có cột nào lẫn net_revenue trong các file này.
4. **`p_churn_logistic` là NaN cho ~535 khách** (khách chỉ phát sinh đơn sau cutoff 2022-06-30) — đây là
   giới hạn của thiết kế time-split (tránh leakage), không phải lỗi khi export; lọc `notna()` trước khi
   dùng cột này để rank toàn bộ khách theo rủi ro.
5. **Toàn bộ số liệu trong bảng trên đã được verify lại sau khi di chuyển thư mục** (2026-07-20) — chạy
   lại `phase0_data_check.py`, `phase0_full_qc.py`, `tet_effect.py`, `eda_training_charts.py`,
   `revenue_diagnostic.py`, `customer_demographics.py`, và exec() nối các code-cell của cả 4 notebook
   (`EDA_khoi_dong.ipynb`, `EDA_quan_sat.ipynb`, `EDA_diagnostic.ipynb`, `EDA_demographics.ipynb`) bằng
   `.venv/bin/python` — tất cả chạy sạch (exit 0), số liệu khớp 100% với các báo cáo `.md` hiện có.
6. **`phase4_prescriptive/data/` trộn cả gross và net có chủ đích, mỗi file ghi rõ loại đang dùng:**
   `floor_price_simulation_*.csv` dùng **gross** (`order_items` toàn bộ, khớp định nghĩa `sales.csv` —
   đúng scope "toàn bộ order_items lịch sử" theo yêu cầu đề xuất 1); `winback_scenario_by_segment.csv`
   dùng **net** (kế thừa `monetary` = `payment_value` từ `rfm_customer_segments.csv` Phase 3);
   `west_margin_replication_*.csv` dùng **gross + cogs catalog** (kế thừa `category_region_margin_controlled.csv`
   Phase 2). Không cộng dồn số giữa 3 nhóm file này (đơn vị/định nghĩa doanh thu khác nhau).
