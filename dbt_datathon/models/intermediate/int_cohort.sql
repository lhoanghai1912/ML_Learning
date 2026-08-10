{{
    config(
        materialized='incremental',
        unique_key=['cohort_month', 'month_offset'],
        incremental_strategy='merge',
        on_schema_change='sync_all_columns'
    )
}}

-- ⚠️⚠️ CẢNH BÁO CHẤT LƯỢNG DỮ LIỆU (thêm 2026-08-10) — ĐỌC TRƯỚC KHI DÙNG SỐ CỦA MODEL NÀY ⚠️⚠️
-- `signup_date` KHÔNG phản ánh thời điểm khách bắt đầu quan hệ mua bán, nên cohort dựng trên nó
-- KHÔNG phải cohort thật và `retention_pct` ở đây KHÔNG phải retention. Bằng chứng tự chạy trên
-- tầng staging (chi tiết: PROCESS.md log 2026-08-10, notebooks/02_eda.ipynb mục Cohort):
--   1) 80,623/90,246 khách có đơn (89.3%) có đơn hàng TRƯỚC ngày signup của chính mình.
--   2) Khách signup TĂNG 957 (2012) -> 21,103 (2022); khách có đơn ĐẦU TIÊN GIẢM 22,068 -> 1,322.
--   3) retention_pct phẳng 3.4-3.6% ở MỌI month_offset 0..12 = trùng khít "base rate" 3.50%
--      (~4,265 khách khác nhau có đơn mỗi tháng / 121,930 khách) -> chỉ đang đo xác suất một khách
--      BẤT KỲ mua trong một tháng BẤT KỲ, không phụ thuộc cohort.
-- MODEL NÀY GIỮ NGUYÊN CÓ CHỦ ĐÍCH: là bản đối chiếu REGRESSION với phase cũ
-- (dashboard_rfm_cohort.md), sửa đè sẽ phá gate M3b đã verify. => Phân tích/BI/ra quyết định phải
-- dùng model `int_cohort_first_order` (cohort theo tháng đơn hàng ĐẦU TIÊN). Model này chỉ
-- dùng cho mục đích đối chiếu lịch sử.
--
-- Grain: 1 dòng/(cohort_month, month_offset). Nguồn: {{ ref('stg_customers') }} (cohort theo
-- tháng signup_date) + {{ ref('stg_orders') }} KHÔNG-cancelled (activity).
-- Port: docs/analysis/phase3_dashboard/customer_demographics.py mục COHORT RETENTION
-- (dòng 325-368). 238 khách pre-launch (signup_date < 2012-07-04 = SHOP_OPEN, phase0_qc W8)
-- LOẠI khỏi cohort chính — đúng quyết định đề bài (khác khuyến nghị "gộp" của QC).
--
-- month_offset chỉ sinh trong khoảng "quan sát được" — cohort_month + offset <= tháng đơn
-- không-cancelled MỚI NHẤT toàn hệ thống (đúng logic "eligible" trong Python gốc, dòng 373-374:
-- `eligible = cohort_sizes.index[cohort_sizes.index + off <= max_month]`). Với offset trong dải
-- này mà KHÔNG có khách nào active, n_active=0/retention_pct=0 (KHÔNG phải NULL) — khác 1 chi
-- tiết kỹ thuật vô hại so với `active.unstack()` gốc (pivot thưa tạo NaN cho ô không xuất hiện
-- trong groupby): Python gốc khi tính `avg_retention` cũng `.fillna(0)` những ô này trước khi
-- cộng dồn (dòng 377) — tức NaN và 0 ở đây LÀ CÙNG Ý NGHĨA "0 khách active", quyết định trả về 0
-- tường minh ở lớp intermediate giúp mart/BI cộng dồn thẳng không cần fillna lại.

with cohort_customers as (
    select
        customer_id,
        signup_date,
        date_trunc('month', signup_date) as cohort_month
    from {{ ref('stg_customers') }}
    where signup_date >= date('2012-07-04')
),

cohort_sizes as (
    select
        cohort_month,
        count(distinct customer_id) as cohort_size
    from cohort_customers
    group by cohort_month
),

non_cancel_orders as (
    select
        customer_id,
        order_id,
        date_trunc('month', order_date) as order_month
    from {{ ref('stg_orders') }}
    where order_status != 'cancelled'
),

max_month as (
    select max(order_month) as max_order_month
    from non_cancel_orders
),

cohort_offsets as (
    select
        cs.cohort_month,
        cs.cohort_size,
        t.month_offset
    from cohort_sizes cs
    cross join max_month mm
    cross join unnest(
        sequence(0, date_diff('month', cs.cohort_month, mm.max_order_month))
    ) as t (month_offset)
),

activity as (
    select
        cc.cohort_month,
        date_diff('month', cc.cohort_month, nco.order_month) as month_offset,
        nco.customer_id
    from non_cancel_orders nco
    inner join cohort_customers cc on nco.customer_id = cc.customer_id
    where date_diff('month', cc.cohort_month, nco.order_month) >= 0
),

active_counts as (
    select
        cohort_month,
        month_offset,
        count(distinct customer_id) as n_active
    from activity
    group by cohort_month, month_offset
)

select
    co.cohort_month,
    co.month_offset,
    co.cohort_size,
    coalesce(ac.n_active, 0) as n_active,
    case
        when co.cohort_size > 0
        then coalesce(ac.n_active, 0) * 100.0 / co.cohort_size
        else null
    end as retention_pct
from cohort_offsets co
left join active_counts ac
    on co.cohort_month = ac.cohort_month
    and co.month_offset = ac.month_offset
