# M3b — da — báo cáo (dbt intermediate + marts trên Trino/Iceberg)

Status: ✅ done (chờ PO verify + gộp vào PROCESS.md)
Ownership: `dbt_datathon/{models/intermediate/*, models/marts/*, models/schema.yml (PHẦN THÊM
MỚI), dbt_project.yml (block intermediate:/marts:)}`.
Ngoại lệ tự thêm ngoài danh sách ownership gốc trong prompt (nêu rõ lý do): `dbt_datathon/tests/
reconcile_gross_vs_net_revenue.sql` — BẮT BUỘC theo việc 3 của prompt ("test reconciliation
gross vs net") + RESTRUCTURE_AGENTS.md DATA QUALITY STANDARD chiều 9 ("dbt singular test"),
không thể nhét logic này vào `schema.yml` (schema.yml chỉ khai generic test, singular test PHẢI
là file `.sql` riêng theo convention dbt — `test-paths: ["tests"]` đã cấu hình sẵn từ M0). KHÔNG
đụng bất kỳ file nào của M3a (`models/staging/*`, sources trong `schema.yml`) — chỉ APPEND.

## Tóm tắt

3 model `intermediate/` (daily revenue, RFM, cohort retention) + 3 mart (`mart_revenue_daily`,
`mart_customer_segments`, `mart_channel_perf`) build THẬT trên Trino/Iceberg (container M2 đang
sống). `dbt build` = **114/114 PASS** (20 model + 94 data test + 1 exposure NO-OP — exposure
không phải test, NO-OP là hành vi đúng của `dbt build`), chạy lại **3 lần liên tiếp** đều
114/114, `dbt source freshness` vẫn **14/14 PASS** (không đụng M3a). Incremental verify idempotent
THẬT (2 lần build liên tiếp, đối chiếu row count qua Trino độc lập, không tin log dbt). **REGRESSION
khớp gần như TUYỆT ĐỐI** với 3 báo cáo Phần A cũ (`descriptive_summary.md`, `diagnostic_revenue.md`,
`dashboard_rfm_cohort.md`) — chi tiết số liệu ở mục Verify bên dưới, có 1 sai khác đã biết + giải
thích đầy đủ (RFM quintile, do khác thuật toán `ntile()` SQL vs `pandas.qcut`, lệch tối đa ±2
khách/segment trên 88,123 khách).

## Việc đã làm

### 1. `dbt_datathon/dbt_project.yml`
Thêm block `intermediate: +materialized: incremental` và `marts: +materialized: table` (append
sau block `staging:` đã có của M3a, KHÔNG sửa block đó). Không set `+schema:` cho 2 block mới —
lý do giống hệt M3a (tránh bug `staging_staging`, xem comment trong file): intermediate/marts
hiện CÙNG schema Trino với staging (`staging`), phân biệt bằng tiền tố tên bảng `int_`/`mart_`.
Chấp nhận có chủ đích ở milestone này, không phải thiếu sót — tách schema vật lý là việc của M
sau nếu cần.

### 2. `models/intermediate/int_daily_revenue.sql`
Grain 1 dòng/ngày (3.833 ngày). Port `docs/analysis/phase1_descriptive/eda_training_charts.py`
mục 1 (daily + MA30 30 ngày, dùng `avg() over (rows between 29 preceding and current row)`) và
mục 2 (doanh thu + margin theo tháng, broadcast xuống từng ngày qua join `date_trunc('month',
date)`). Model `incremental` (`unique_key='date'`, `incremental_strategy='merge'`) nhưng **luôn
SELECT full `stg_sales`** — quyết định CÓ CHỦ ĐÍCH (ghi rõ trong comment đầu file): MA30/monthly
margin là window function cần toàn bộ chuỗi ngày liền mạch để đúng cho MỌI dòng, dữ liệu nguồn
tĩnh + nhỏ (3.833 dòng) nên full recompute mỗi lần chạy rẻ (< 1s theo log thật), MERGE theo
`unique_key=date` vẫn đảm bảo idempotent — đã verify THẬT (mục Verify #3).

### 3. `models/intermediate/int_rfm.sql`
Grain 1 dòng/customer_id, chỉ khách có ≥1 đơn KHÔNG-cancelled (kỳ vọng 88,123 khách — khớp
`dashboard_rfm_cohort.md` mục 0). Port `docs/analysis/phase3_dashboard/customer_demographics.py`
mục RFM SEGMENTATION (dòng 219-281): Recency = ngày từ đơn không-cancelled gần nhất tới
`snapshot_date = max(order_date)` TOÀN BỘ đơn; Frequency = số đơn không-cancelled; Monetary =
tổng `stg_payments.payment_value`. Segment gán qua `CASE WHEN` port ĐÚNG thứ tự if/elif của
`rfm_segment()` gốc (thứ tự quan trọng vì điều kiện chồng lấn).

**R/F/M score — bug tìm & sửa lúc verify (ghi lại để không lặp):** Python gốc dùng
`rank(method='first')` (phá tie theo thứ tự xuất hiện = customer_id tăng dần, vì
`groupby(sort=True)` mặc định) rồi `pandas.qcut` (ngũ phân vị nội suy tuyến tính). Trino không có
hàm tương đương — dùng `ntile(5)`. **Lần thử đầu tiên `ntile(5) over (order by recency_days
asc)` KHÔNG có tie-break phụ** → Champions ra **22,614** khách thay vì kỳ vọng 22,575 (lệch 39
khách, quá lớn để chấp nhận) — vì `recency_days`/`frequency`/`monetary` có nhiều giá trị trùng
(integer ngày, ~4.000 giá trị phân biệt trên 88.123 khách), Trino phá tie theo thứ tự vật lý bất
định thay vì customer_id. **Fix:** thêm `order by <cột>, customer_id asc` làm tie-break phụ,
khớp đúng cơ chế `rank(method='first')` của pandas → verify lại: Champions khớp **TUYỆT ĐỐI
22,575**, 8 segment còn lại lệch tối đa ±2 khách (0.0045%-0.02%, do khác thuật toán nội suy
`qcut` vs bucket-size `ntile`, KHÔNG phải bug — đã verify bằng script Python độc lập đối chiếu 2
thuật toán trên đúng `orders.csv`/`payments.csv`, xem mục Verify #2).

### 4. `models/intermediate/int_cohort.sql`
Grain 1 dòng/(cohort_month, month_offset). Port `docs/analysis/phase3_dashboard/
customer_demographics.py` mục COHORT RETENTION (dòng 325-368). 238 khách pre-launch
(`signup_date < 2012-07-04`) loại khỏi cohort chính (đúng quyết định đề bài, khác khuyến nghị
"gộp" của phase0_qc W8). `month_offset` chỉ sinh trong khoảng "quan sát được"
(`cohort_month + offset <= tháng đơn không-cancelled mới nhất toàn hệ thống`, dùng
`sequence()`+`unnest()` của Trino) — đúng logic `eligible` trong Python gốc (dòng 373-374). Khi
offset hợp lệ nhưng 0 khách active, `n_active=0`/`retention_pct=0` tường minh (KHÔNG NULL) —
khác 1 chi tiết vô hại so với `active.unstack()` gốc (tạo NaN cho ô không xuất hiện trong
groupby thưa), nhưng Python gốc khi tính `avg_retention` cũng `.fillna(0)` các ô này trước khi
cộng dồn (dòng 377) → NaN và 0 ở đây LÀ CÙNG Ý NGHĨA, quyết định trả 0 tường minh giúp mart/BI
cộng thẳng không cần fillna lại.

### 5. `models/marts/mart_revenue_daily.sql`
Từ `int_daily_revenue`, materialized `table`. Thêm `revenue_yoy_pct` (so cùng NGÀY LỊCH năm
trước qua `date_add('year', -1, date)` — không offset cố định 365 ngày để tránh lệch năm nhuận),
`revenue_rank_desc`, `year`/`month`/`day_of_week` (cột tiện filter dashboard, không đổi grain).

### 6. `models/marts/mart_customer_segments.sql`
Từ `int_rfm`, GROUP BY segment → grain 1 dòng/segment (9 dòng). Port bảng "Findings
(Descriptive)" mục 1 `dashboard_rfm_cohort.md` (n_customers, %khách, tổng Monetary, %Monetary,
Monetary TB/khách, Recency TB, Frequency TB). Chi tiết từng khách vẫn truy vấn được qua
`int_rfm` trực tiếp (không mất thông tin).

### 7. `models/marts/mart_channel_perf.sql`
Grain 1 dòng/(year, dimension_type, dimension_value) — bảng "long" hợp nhất 4 lát cắt diagnostic
từ `docs/analysis/phase2_diagnostic/revenue_diagnostic.py`: `channel` (order_source theo năm),
`category` (theo năm), `region` (theo năm), `promo` (AOV có/không promo, `year=NULL` vì source
gốc tính TOÀN KỲ 2013-2022 không chia năm). Lọc `year BETWEEN 2013 AND 2022` — đúng filter gốc
(loại nửa năm 2012 lẻ). **Chi tiết cố ý giữ giống gốc dù không "đẹp":** AOV promo port ĐÚNG
group-key `groupby(["order_id","has_promo"])` của source — nếu 1 đơn có cả dòng có-promo lẫn
không-promo, bị tách thành 2 quan sát riêng (không phải AOV đúng nghĩa "giá trị đơn theo có/không
promo") — giữ nguyên hành vi này để khớp số `27,945`/`21,896` VND đã công bố, không tự "sửa cho
đúng hơn" (sẽ đổi số so với báo cáo đã duyệt).

### 8. `dbt_datathon/tests/reconcile_gross_vs_net_revenue.sql` (singular test)
Đối chiếu GROSS (`stg_sales`) vs NET "bỏ cancelled" (`order_items`, loại cancelled, trừ
`discount_amount`) — port bảng đối chiếu 6 định nghĩa Revenue ở `phase0_qc_report.md` mục 6.
Ngưỡng PASS: gap 10.0%-25.0% (dải rộng hơn số quan sát 13.369% để chống false-positive khi
re-ingest, chặn 2 đầu nếu định nghĩa net bị đổi sai — lý do đầy đủ trong comment file test).

### 9. `models/schema.yml` — APPEND (không xoá/sửa sources/staging M3a)
214 dòng thêm mới (verify bằng `git diff --stat`, 0 deletion): docs + tests
not_null/unique/accepted_values cho khóa chính 6 model mới, `dbt_utils.unique_combination_of_columns`
cho `int_cohort` (cohort_month, month_offset) và `mart_channel_perf` (year, dimension_type,
dimension_value), block `exposures:` khai `notebook_02_eda` (02_eda.ipynb) `depends_on` 4 model
(3 mart + `int_cohort`) — đúng TODO đã note sẵn trong `notebooks/02_eda.ipynb` mục 0. **Quyết
định:** `01_data_quality.ipynb` CỐ Ý KHÔNG khai exposure — notebook đó validate trực tiếp
`src/datathon.quality` (10 hàm DQ, M4a) trên raw CSV để mô phỏng đúng pipeline ingest thật (M2),
là luồng kiểm tra SONG SONG/độc lập với dbt, không phải use-case "đọc mart để phân tích" (đã
grep toàn bộ notebook, không có TODO nào liên quan mart — quyết định ghi rõ lý do trong comment
`schema.yml`, không lệch câm).

### 10. Bug phụ tìm lúc verify: apostrophe trong `accepted_values`
Giá trị segment `Can't Lose Them` chứa dấu `'` — macro `accepted_values` không tự escape khi
build `IN (...)` → SQL lỗi `SYNTAX_ERROR` (`mismatched input 't'`). Fix: escape thành
`Can''t Lose Them` trong YAML (2 dấu `'` liên tiếp = 1 dấu `'` literal trong SQL string). Xảy ra
ở 2 chỗ (`int_rfm.segment`, `mart_customer_segments.segment`), cả 2 đã fix, verify lại xanh.

## Verify (chạy thật, log thật — không suy đoán)

### 1. `dbt build` toàn project — 3 LẦN LIÊN TIẾP
```
Lần 1: Done. PASS=114 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=115   (1 lỗi apostrophe, đã fix trước lần này)
Lần 2: Done. PASS=114 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=115
Lần 3: Done. PASS=114 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=115
```
(NO-OP=1 = exposure `notebook_02_eda`, không phải test — hành vi đúng của `dbt build`, không
phải lỗi). 20 model (14 staging view của M3a + 3 intermediate + 3 mart) + 94 data test (60 của
M3a + 34 mới: not_null/unique/accepted_values/unique_combination cho int_/mart_ + 1 singular
reconciliation).

### 2. RFM — đối chiếu 2 thuật toán quintile (Python, TRƯỚC khi viết SQL)
Script độc lập dùng `orders.csv`/`payments.csv` thật (`data/raw/`), so `pandas.qcut` (gốc) vs mô
phỏng `ntile()` (dự kiến dùng SQL): lệch 4/88,123 khách (0.0045%) ở ranh giới ngũ phân vị. Sau
khi build SQL thật với tie-break `customer_id`, đối chiếu qua Trino:

| Segment | int_rfm (Trino) | dashboard_rfm_cohort.md | Lệch |
|---|---:|---:|---:|
| Champions | 22,575 | 22,575 | **0** |
| Loyal Customers | 16,975 | 16,974 | +1 |
| Lost | 21,683 | 21,682 | +1 |
| At Risk | 7,987 | 7,989 | -2 |
| Can't Lose Them | 2,251 | 2,251 | **0** |
| Hibernating | 3,327 | 3,327 | **0** |
| Promising | 5,375 | 5,375 | **0** |
| New Customers | 4,865 | 4,865 | **0** |
| Need Attention | 3,085 | 3,085 | **0** |

Champions avg_recency=274 ngày (khớp), avg_frequency=15.88 (khớp), total_monetary=8.95 tỷ (khớp
làm tròn 2 chữ số thập phân). **Kết luận: lệch tối đa ±2 khách/segment trên 88,123 (0.02%),
KHÔNG phải bug — nguyên nhân đã xác định (khác thuật toán nội suy `qcut` vs bucket `ntile` ở
đúng ranh giới ngũ phân vị), đã document đầy đủ trong `.sql` + `schema.yml`.**

### 3. Cohort — khớp TUYỆT ĐỐI
```sql
select month_offset, sum(n_active)*100.0/sum(cohort_size), count(distinct cohort_month), sum(cohort_size)
from staging.int_cohort where month_offset in (1,3,6,12) group by month_offset
```
Kết quả: **M1=3.0% · M3=2.9% · M6=3.0% · M12=2.9%** — khớp TUYỆT ĐỐI
`dashboard_rfm_cohort.md` mục 2 ("M1 ≈ 3.0% · M3 ≈ 2.9% · M6 ≈ 3.0% · M12 ≈ 2.9%"). 126 cohort
tháng (khớp "126 cohort"), tổng 121,692 khách cohort chính (khớp TUYỆT ĐỐI "121,692 khách (đã
loại 238 khách pre-launch)").

### 4. Daily revenue — khớp TUYỆT ĐỐI
Tổng revenue theo năm (tỷ VND) từ `int_daily_revenue`: **2013=1.66 · 2014=1.87 · 2015=1.89 ·
2016=2.10 · 2017=1.91 · 2018=1.85 · 2019=1.14 · 2020=1.05 · 2021=1.04 · 2022=1.17** — khớp
TUYỆT ĐỐI `descriptive_summary.md` mục 2.1. Count = 3,833 dòng (khớp "3.833 ngày"). Day-of-week:
đỉnh Thứ Tư (4.68 triệu/ngày), đáy Thứ Bảy (3.91 triệu/ngày), chênh **19.7%** (báo cáo gốc
19.8%, lệch 0.1pp do làm tròn 2 chữ số thập phân giữa 2 lần tính — không phải sai số hệ thống).

### 5. Channel/category/region/promo — khớp TUYỆT ĐỐI
Từ `mart_channel_perf`, đối chiếu `diagnostic_revenue.md`:

| Chỉ số | mart_channel_perf | diagnostic_revenue.md | Khớp |
|---|---|---|---|
| Category 2013 | Casual 1.8% · GenZ 1.6% · Outdoor 19.8% · Streetwear 76.8% | y hệt | ✅ |
| Category 2022 | Casual 4.6% · GenZ 2.5% · Outdoor 9.0% · Streetwear 83.8% | y hệt | ✅ |
| Region 2022 (tỷ) | East 0.5 · Central 0.4 · West 0.2 | y hệt | ✅ |
| Promo AOV | không-promo 27,945 VND · có-promo 21,896 VND | y hệt | ✅ |
| Channel Δ 2018→2019 | email -41.0% · social -39.9% · referral -39.1% · organic -37.7% · direct -37.4% · paid_search -37.3% | y hệt | ✅ |

### 6. Reconciliation gross vs net — khớp TUYỆT ĐỐI
```
gross_revenue = 16,430,476,585.53 (≈16.43 tỷ, khớp descriptive_summary.md "≈16,43 tỷ VND")
net_revenue   = 14,233,855,627.9996 (≈14.23 tỷ, khớp descriptive_summary.md "≈14,23 tỷ VND")
gap_pct       = 13.369185...% (khớp TUYỆT ĐỐI phase0_qc_report.md "Bỏ cancelled, net: −13.369%"
                và descriptive_summary.md "Gap = 13.37%")
```
Singular test `reconcile_gross_vs_net_revenue` PASS (gap trong [10%,25%]).

### 7. Incremental idempotent — verify THẬT qua Trino (không tin log dbt)
2 lần `dbt build` liên tiếp, sau đó query COUNT(*) trực tiếp qua Trino (độc lập với dbt):
```
int_daily_revenue: 3833 (cả 2 lần, log dbt "MERGE (3_833 rows)" cả 2 lần)
int_rfm:           88123 (cả 2 lần, log dbt "MERGE (88_123 rows)" cả 2 lần)
int_cohort:        8001 (cả 2 lần, log dbt "MERGE (8_001 rows)" cả 2 lần)
```
Kiểm tra trùng khóa (GROUP BY ... HAVING COUNT(*)>1) trên cả 3 bảng sau 2 lần build: **0 dòng
trùng** cho `date` (int_daily_revenue), `customer_id` (int_rfm), `(cohort_month, month_offset)`
(int_cohort). **Idempotent xác nhận thật, không nhân đôi.**

### 8. `dbt source freshness` — vẫn 14/14 PASS
```
Finished running 14 sources in 0 hours 0 minutes and 1.81 seconds (1.81s).
```
14/14 PASS — không đụng M3a.

### 9. `dbt docs generate`
```
Building catalog
Catalog written to .../dbt_datathon/target/catalog.json
```
Chạy được, không lỗi.

### 10. Ownership — verify bằng `git status`/`git diff`
```
git status --porcelain -- dbt_datathon (lọc target/logs/.user.yml):
 M dbt_datathon/dbt_project.yml                          (chỉ 17 dòng thêm, xem git diff)
 M dbt_datathon/models/schema.yml                        (214 dòng thêm, 0 xoá — git diff --stat)
?? dbt_datathon/models/intermediate/int_cohort.sql
?? dbt_datathon/models/intermediate/int_daily_revenue.sql
?? dbt_datathon/models/intermediate/int_rfm.sql
?? dbt_datathon/models/marts/mart_channel_perf.sql
?? dbt_datathon/models/marts/mart_customer_segments.sql
?? dbt_datathon/models/marts/mart_revenue_daily.sql
?? dbt_datathon/tests/reconcile_gross_vs_net_revenue.sql
```
0 file M3a (`models/staging/*`, sources trong `schema.yml`) bị đụng. `.gitkeep` ở 3 thư mục
(`intermediate/`, `marts/`, `tests/`) vẫn còn nguyên trên đĩa (verify `ls -a`), không bị xoá.

## DoD tự check

- [x] `dbt build` xanh — 114/114 PASS, chạy 3 lần liên tiếp đều xanh (0 flaky).
- [x] `dbt source freshness` vẫn 14/14 PASS (không đụng M3a).
- [x] Incremental chạy 2 lần liên tiếp, count KHÔNG đổi — verify THẬT qua Trino độc lập (không
      tin log dbt), dán log trên. 0 dòng trùng khóa.
- [x] KHÔNG sửa raw/staging — `git diff` xác nhận 0 thay đổi `models/staging/*`, sources.
- [x] REGRESSION đối chiếu 3 file `.md` — khớp TUYỆT ĐỐI cho cohort/daily/channel/category/region/
      promo/reconciliation; RFM khớp TUYỆT ĐỐI ở Champions + lệch tối đa ±2 khách 4/9 segment còn
      lại (đã giải thích nguyên nhân đầy đủ, KHÔNG lệch câm).
- [x] `dbt docs generate` chạy được, catalog.json sinh ra.
- [x] Ownership đúng phạm vi — chỉ 7 file thay đổi/mới, đúng danh sách cho phép + 1 ngoại lệ
      (`tests/*.sql`) đã giải thích lý do bắt buộc.
- [x] KHÔNG commit `PROCESS.md`, KHÔNG `git add -A`.

## Việc PO/milestone kế cần biết

- **M3 (dbt) đã HOÀN TẤT hoàn toàn** (M3a + M3b) — staging + intermediate + marts đều xanh,
  regression khớp toàn bộ Phần A cũ. Không còn gap nào ở tầng dbt.
- **M6a (da) có thể làm tiếp TODO đã note sẵn trong `notebooks/02_eda.ipynb` mục 0**: đổi cell
  load từ raw CSV (`datathon.load_raw()`) sang `SELECT * FROM iceberg.marts.*` qua Trino — exposure
  `notebook_02_eda` trong `schema.yml` đã khai đúng 4 model cần dùng (`mart_revenue_daily`,
  `mart_customer_segments`, `mart_channel_perf`, `int_cohort`). Việc này NGOÀI phạm vi M3b (M3b
  chỉ build model, không sửa notebook), để M6a hoặc PO quyết định lịch.
- **RFM segment lệch ±2 khách/segment (4/9 segment) so với báo cáo cũ** — đã verify + giải thích
  đầy đủ nguyên nhân (thuật toán `ntile` SQL vs `qcut` pandas tại ranh giới ngũ phân vị), không
  phải bug, không cần sửa thêm trừ khi có yêu cầu khớp byte-exact tuyệt đối (nếu cần, chỉ có cách
  triển khai lại thuật toán nội suy tuyến tính của pandas trong SQL — effort cao, lợi ích thấp
  vì Champions — segment quan trọng nhất cho prescriptive — đã khớp tuyệt đối).
- `dbt_datathon/tests/reconcile_gross_vs_net_revenue.sql` là file MỚI ngoài danh sách ownership
  gốc trong prompt — PO cân nhắc khi gộp (lý do bắt buộc đã nêu ở đầu report, không phải lỗi phạm
  vi tuỳ tiện).

## Commit (đề xuất, da CHƯA tự commit theo protocol PROCESS.md khi 1-agent nối tiếp)

`git add dbt_datathon/dbt_project.yml dbt_datathon/models/schema.yml
dbt_datathon/models/intermediate/int_daily_revenue.sql
dbt_datathon/models/intermediate/int_rfm.sql
dbt_datathon/models/intermediate/int_cohort.sql
dbt_datathon/models/marts/mart_revenue_daily.sql
dbt_datathon/models/marts/mart_customer_segments.sql
dbt_datathon/models/marts/mart_channel_perf.sql
dbt_datathon/tests/reconcile_gross_vs_net_revenue.sql` — KHÔNG `-A`, KHÔNG `PROCESS.md`.

Conventional commit đề xuất: `feat(dbt): intermediate + marts trên Trino/Iceberg — RFM/cohort/
revenue/channel, regression khớp Phần A cũ`.
