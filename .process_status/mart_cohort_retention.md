# Report — mart_cohort_retention (expose int_cohort_first_order lên mart)

Ngày: 2026-08-10. Nhánh: `chore/restructure-lakehouse`. Việc con song song (1 trong 3), scope
CHỈ 2 file: `dbt_datathon/models/marts/mart_cohort_retention.sql` (mới) +
`dbt_datathon/models/schema.yml` (thêm entry, không đụng entry khác).

## 1. Thiết kế grain đã chọn + lý do

Đọc 2 mart tiền lệ trước khi quyết:
- `mart_revenue_daily`: giữ NGUYÊN grain nguồn (1 dòng/ngày, từ `int_daily_revenue`), chỉ thêm
  cột enrichment (YoY, rank, year/month/day_of_week).
- `mart_customer_segments`: AGGREGATE lên grain thô hơn — từ customer-grain `int_rfm` lên
  segment-grain (9 dòng), group by segment, docstring ghi rõ "muốn chi tiết dùng int_rfm trực
  tiếp".

Chọn cách 2 (aggregate), áp cho cohort: `int_cohort_first_order` grain gốc là
`(cohort_month, month_offset)` (~126 cohort_month × nhiều offset = hàng nghìn dòng thô). Yêu cầu
chính của việc này là "đường cong retention trung bình theo month_offset, weighted theo
cohort_size" — đúng bản chất một phép AGGREGATE (group by month_offset, sum cohort_size/n_active
rồi chia), không phải enrichment giữ nguyên grain.

**Quyết định**: `mart_cohort_retention` grain = **1 dòng/month_offset** (126 dòng, offset
0..125). KHÔNG giữ breakdown theo `cohort_month` trong mart này — lý do:
1. Yêu cầu gốc ghi "tối thiểu phải có" đường cong tổng; đây chính là mục tiêu chính, không phải
   mục tiêu phụ.
2. Đúng tiền lệ `mart_customer_segments`: model intermediate (`int_cohort_first_order`) đã sẵn
   grain chi tiết, vẫn query được thẳng qua Trino khi cần breakdown — không cần nhân đôi dữ liệu
   trong mart.
3. Grain đơn giản → `month_offset` là khóa tự nhiên, test `not_null`+`unique` rõ ràng, không có
   NULL đặc biệt kiểu "dòng tổng" (đã cân nhắc và loại phương án UNION ALL thêm 1 dòng
   `cohort_month = NULL` đại diện tổng — phức tạp hoá test không cần thiết vì đằng nào bản thân
   mart NÀY đã là "dòng tổng" cho mỗi offset, không cần thêm 1 tầng nữa).
4. Thoả đúng yêu cầu "BI query đường cong tổng bằng 1 SELECT đơn giản không cần GROUP BY phức
   tạp": `select month_offset, retention_pct from mart_cohort_retention order by month_offset`.

Cột output: `month_offset` (PK), `n_cohorts_observed` (số cohort_month có mặt ở offset đó — đo độ
tin cậy điểm dữ liệu), `earliest_cohort_month`/`latest_cohort_month` (cohort nào đóng góp),
`total_cohort_size` (mẫu số), `total_active` (tử số), `retention_pct` = weighted retention
(`sum(n_active)*100/sum(cohort_size)` — tương đương trung bình cộng `retention_pct` từng cohort
weighted theo `cohort_size`, đúng công thức yêu cầu).

Nguồn dữ liệu ghi rõ trong docstring `.sql` + `description` schema.yml: **`int_cohort_first_order`
— KHÔNG PHẢI `int_cohort`** (model cũ, cohort theo `signup_date`, retention sai/phẳng 3.4-3.6%,
đã cảnh báo ở chính model đó). Không đụng, không sửa 2 file `.sql` intermediate theo đúng ràng
buộc.

## 2. Verify build pass — KHÔNG phá baseline

- **Baseline TRƯỚC khi sửa gì** (tự chạy xác nhận, không tin số cũ trong PROCESS.md suông):
  `cd dbt_datathon && ../.venv/bin/dbt build` → `PASS=120 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=121`
  — khớp đúng số PROCESS.md ghi (commit `f2ac8b3`).
- **Sau khi thêm `mart_cohort_retention.sql` + entry schema.yml**:
  `PASS=126 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=127` — đúng +6 (1 model mới + 5 test: `not_null`
  trên `month_offset`/`n_cohorts_observed`/`total_cohort_size`/`total_active` + `unique` trên
  `month_offset`). 0 model/test cũ nào đổi trạng thái.
- **1 lỗi gặp giữa chừng, đã sửa**: lần build đầu tiên FAIL compile —
  `'ref' is undefined ... Compilation Error` — do tôi lỡ dùng `{{ ref('int_cohort_first_order') }}`
  (jinja) bên trong field `description` của `schema.yml`. Tiền lệ (`int_cohort`,
  `int_cohort_first_order`, `mart_revenue_daily`...) không dùng jinja `ref()` trong description
  schema.yml, chỉ dùng tên trần trong backtick. Sửa lại đúng convention, build lại PASS ngay
  (jinja `ref()` bên trong COMMENT của file `.sql` vẫn giữ nguyên, đúng pattern
  `mart_revenue_daily.sql`/`mart_customer_segments.sql` — không có vấn đề gì ở đó).
- **Idempotent check nhanh**: chạy lại riêng `dbt build --select mart_cohort_retention` lần 2 →
  `PASS=6 WARN=0 ERROR=0` (model `materialized='table'` = full refresh mỗi lần, tự nhiên
  idempotent — không cần incremental merge check như model khác).

## 3. Verify số khớp Trino (tự query lại, không suy đoán)

Query trực tiếp qua `trino` python package (`.venv/bin/python3`, host=localhost:8080,
catalog=iceberg, schema=staging):

**(a) Trên `int_cohort_first_order` (trước khi viết mart, để chốt design đúng số kỳ vọng)**:
```
month_offset=0:  total_cohort_size=88123  total_active=88123  retention_pct=100.0   n_cohorts=126
month_offset=1:  total_cohort_size=88043  total_active=5407   retention_pct=6.1     n_cohorts=125
month_offset=6:  total_cohort_size=87589  total_active=4625   retention_pct=5.3     n_cohorts=120
month_offset=12: total_cohort_size=86795  total_active=5544   retention_pct=6.4     n_cohorts=114
```

**(b) Trên `mart_cohort_retention` sau khi build** — query thẳng bảng mart vừa tạo:
```
month_offset=0:  n_cohorts_observed=126  total_cohort_size=88123  total_active=88123  retention_pct=100.0
month_offset=1:  n_cohorts_observed=125  total_cohort_size=88043  total_active=5407   retention_pct=6.1
month_offset=6:  n_cohorts_observed=120  total_cohort_size=87589  total_active=4625   retention_pct=5.3
month_offset=12: n_cohorts_observed=114  total_cohort_size=86795  total_active=5544   retention_pct=6.4
```
→ **Khớp tuyệt đối** với số đã verify trước đó (PROCESS.md log 2026-08-10, commit `f2ac8b3`):
M0=100%, M1=6.10%, M6=5.30% (đáy), M12=6.40% (hình "nụ cười"). Cũng khớp `count(*)` = **126
dòng** trong mart = đúng 126 cohort tháng đã biết từ M3b.

**(c) Khoá không trùng lặp** — verify bằng data thật (không chỉ tin test dbt):
`select count(*) from (select month_offset from mart_cohort_retention group by month_offset
having count(*)>1)` → **0**.

## 4. Hạn chế / nợ phát sinh (không chặn)

- Mart chỉ cung cấp đường cong TỔNG. Muốn breakdown theo `cohort_month` riêng (vd so sánh nhiều
  đường cong theo năm cohort) phải query thẳng `int_cohort_first_order` — không có sẵn 1 mart
  BI-ready cho việc đó. Chưa hỏi PO có cần thêm mart 2 (chi tiết) không — để backlog nếu cần.
- Chưa thêm `mart_cohort_retention` vào block `exposures` (`notebook_02_eda`) trong
  `schema.yml` — đúng ràng buộc (chỉ được thêm entry mới, không đụng phần khác của file, và
  notebook hiện chưa có cell query mart này thật). Nếu sau này nối notebook vào mart, cần thêm
  exposure riêng.
- Không re-run REGRESSION toàn diện các mart khác (`mart_revenue_daily`,
  `mart_customer_segments`, `mart_channel_perf`) — không cần vì `dbt build` full đã chạy qua tất
  cả, 0 lỗi, 0 test nào trong số đó đổi trạng thái (số PASS tăng đúng +6, không tăng thêm/giảm ở
  chỗ khác).

## 5. File thay đổi (commit riêng, đúng ràng buộc)

- Mới: `dbt_datathon/models/marts/mart_cohort_retention.sql`
- Sửa (chỉ thêm, +30 dòng, 0 xoá — verify qua `git diff --stat`):
  `dbt_datathon/models/schema.yml`
- KHÔNG đụng `int_cohort.sql`, `int_cohort_first_order.sql`, `PROCESS.md`, hay entry nào khác
  trong `schema.yml`.
