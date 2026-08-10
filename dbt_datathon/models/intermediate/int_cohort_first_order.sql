{{
    config(
        materialized='incremental',
        unique_key=['cohort_month', 'month_offset'],
        incremental_strategy='merge',
        on_schema_change='sync_all_columns'
    )
}}

-- Grain: 1 dòng/(cohort_month, month_offset) — GIỐNG model `int_cohort`.
--
-- VÌ SAO TỒN TẠI MODEL NÀY (đọc trước khi dùng):
-- Model `int_cohort` định nghĩa cohort theo `stg_customers.signup_date`. Điều tra 2026-08-10
-- (xem PROCESS.md + notebooks/02_eda.ipynb mục Cohort) chứng minh trường `signup_date` KHÔNG phản
-- ánh thời điểm khách bắt đầu quan hệ mua bán, bằng chứng tự chạy trên chính tầng staging:
--   1) 80,623 / 90,246 khách có đơn (89.3%) có đơn hàng TRƯỚC ngày signup của chính mình.
--   2) Số khách signup TĂNG đều 957 (2012) -> 21,103 (2022), trong khi số khách có đơn ĐẦU TIÊN
--      GIẢM 22,068 (2012) -> 1,322 (2022) — hai chuỗi ngược chiều, không thể cùng mô tả "khách mới".
--   3) Hệ quả đo được: retention của int_cohort phẳng 3.4-3.6% ở MỌI month_offset 0..12, trùng
--      khít "base rate" = (số khách khác nhau có đơn mỗi tháng ~4,265) / (tổng khách 121,930)
--      = 3.50%. Tức đường cong đó chỉ đang đo xác suất một khách BẤT KỲ mua trong một tháng BẤT
--      KỲ — không phụ thuộc cohort, nên KHÔNG PHẢI retention.
--
-- Model này tính lại cohort theo định nghĩa chuẩn ngành: `cohort_month = tháng của ĐƠN HÀNG ĐẦU
-- TIÊN` (first non-cancelled order), hoàn toàn không dùng `signup_date`. Theo định nghĩa này
-- retention M0 luôn = 100% (mọi khách đều active ở chính tháng vào cohort) — đây là dấu hiệu
-- kiểm tra nhanh model chạy đúng.
--
-- QUAN HỆ VỚI int_cohort: KHÔNG thay thế, KHÔNG sửa đè. `int_cohort` giữ nguyên để bảo toàn
-- REGRESSION đã verify ở M3b (weighted retention M1=3.0/M3=2.9/M6=3.0/M12=2.9%, 126 cohort,
-- 121,692 khách — khớp tuyệt đối phase cũ `dashboard_rfm_cohort.md`). Hai model cùng tồn tại:
--   - int_cohort              -> đối chiếu lịch sử / regression phase cũ. KHÔNG dùng ra quyết định.
--   - int_cohort_first_order  -> con số retention đáng tin để phân tích/BI.
--
-- Mẫu khách: chỉ khách có >=1 đơn KHÔNG-cancelled (giống mẫu RFM của model `int_rfm`, kỳ
-- vọng 88,123 khách) — khách chưa từng mua không có cohort_month nên bị loại theo định nghĩa,
-- KHÔNG phải lọc thêm. Đây cũng là điểm khác bản chất với int_cohort (mẫu số ở đó là toàn bộ
-- khách signup, gồm cả 31,684 khách chưa từng có đơn nào).
--
-- month_offset chỉ sinh trong khoảng "quan sát được" (cohort_month + offset <= tháng đơn
-- không-cancelled mới nhất toàn hệ thống) — GIỮ NGUYÊN quy ước của int_cohort để 2 model so sánh
-- được trực tiếp, tránh cohort trẻ bị tính retention trên khoảng thời gian chưa xảy ra.

with non_cancel_orders as (
    select
        customer_id,
        order_id,
        order_date,
        date_trunc('month', order_date) as order_month
    from {{ ref('stg_orders') }}
    where order_status != 'cancelled'
),

first_order as (
    select
        customer_id,
        date_trunc('month', min(order_date)) as cohort_month
    from non_cancel_orders
    group by customer_id
),

cohort_sizes as (
    select
        cohort_month,
        count(distinct customer_id) as cohort_size
    from first_order
    group by cohort_month
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
        fo.cohort_month,
        date_diff('month', fo.cohort_month, nco.order_month) as month_offset,
        nco.customer_id
    from non_cancel_orders nco
    inner join first_order fo on nco.customer_id = fo.customer_id
    where date_diff('month', fo.cohort_month, nco.order_month) >= 0
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
