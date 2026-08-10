{{ config(materialized='table') }}

-- Grain: 1 dòng/month_offset (AGGREGATE lên grain thô hơn nguồn — theo tiền lệ
-- `mart_customer_segments`, aggregate customer-grain `int_rfm` lên segment-grain). Nguồn:
-- {{ ref('int_cohort_first_order') }} (grain gốc 1 dòng/(cohort_month, month_offset)) —
-- KHÔNG PHẢI {{ ref('int_cohort') }} (model đó cohort theo signup_date, retention SAI — xem
-- cảnh báo trong file .sql/description của chính model đó, PROCESS.md log 2026-08-10).
--
-- Đây là "đường cong retention trung bình" gộp TẤT CẢ cohort lại theo month_offset, WEIGHTED
-- theo cohort_size (không phải trung bình cộng đơn giản của các retention_pct riêng lẻ):
--   retention_pct = sum(n_active) * 100 / sum(cohort_size)   -- across mọi cohort_month có mặt
--                                                                ở offset đó ("đủ điều kiện quan
--                                                                sát", xem int_cohort_first_order)
-- Tương đương sum(cohort_size_i * retention_pct_i) / sum(cohort_size_i) — cohort đông khách đóng
-- góp nhiều hơn vào đường cong tổng, đúng ý nghĩa "trung bình weighted".
--
-- Muốn xem breakdown CHI TIẾT theo từng cohort_month (vd vẽ nhiều đường cong so sánh theo năm)
-- → query thẳng {{ ref('int_cohort_first_order') }} qua Trino (không mất thông tin, dbt
-- intermediate vẫn query được dù không "expose" chính thức — cùng cách mart_customer_segments
-- trỏ người dùng chi tiết về int_rfm).
--
-- BI query đường cong tổng: `select month_offset, retention_pct from mart_cohort_retention
-- order by month_offset` — 1 SELECT đơn giản, KHÔNG cần GROUP BY (đã gộp sẵn ở mart).
--
-- Verify qua Trino trực tiếp (2026-08-10, khớp tuyệt đối số đã công bố khi thêm
-- int_cohort_first_order, PROCESS.md log 2026-08-10): M0=100.0%, M1=6.10%, M6=5.30% (đáy),
-- M12=6.40% (hồi phục, hình "nụ cười") — mẫu 88,123 khách (khớp count(*) từ int_rfm).

with base as (
    select * from {{ ref('int_cohort_first_order') }}
),

agg as (
    select
        month_offset,
        count(distinct cohort_month) as n_cohorts_observed,
        min(cohort_month) as earliest_cohort_month,
        max(cohort_month) as latest_cohort_month,
        sum(cohort_size) as total_cohort_size,
        sum(n_active) as total_active
    from base
    group by month_offset
)

select
    month_offset,
    n_cohorts_observed,
    earliest_cohort_month,
    latest_cohort_month,
    total_cohort_size,
    total_active,
    case
        when total_cohort_size > 0
        then total_active * 100.0 / total_cohort_size
        else null
    end as retention_pct
from agg
order by month_offset
