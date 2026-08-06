{{
    config(
        materialized='incremental',
        unique_key='customer_id',
        incremental_strategy='merge',
        on_schema_change='sync_all_columns'
    )
}}

-- Grain: 1 dòng/customer_id — CHỈ khách có >=1 đơn KHÔNG-cancelled ("mẫu RFM", kỳ vọng 88,123
-- khách, khớp dashboard_rfm_cohort.md mục 0). Nguồn: {{ ref('stg_orders') }} + {{ ref('stg_payments') }}.
-- Port: docs/analysis/phase3_dashboard/customer_demographics.py mục RFM SEGMENTATION (dòng 219-281).
--
-- Định nghĩa (khớp source Python):
--   Recency  = số ngày từ đơn KHÔNG-cancelled gần nhất tới SNAPSHOT_DATE = max(order_date) TOÀN
--              BỘ đơn (mọi trạng thái — khớp `orders["order_date"].max()` trong script gốc, KHÔNG
--              phải max trên riêng đơn không-cancelled).
--   Frequency = số đơn KHÔNG-cancelled (distinct order_id).
--   Monetary  = tổng stg_payments.payment_value (net thực thu/đơn, phase0_qc I1) trên đơn
--              KHÔNG-cancelled.
--
-- R/F/M score — KHÁC BIỆT ĐÃ BIẾT với source Python (ghi rõ, không lệch câm):
--   Python gốc dùng `rank(method='first')` rồi `pandas.qcut` (ngũ phân vị theo NỘI SUY TUYẾN
--   TÍNH trên rank) để chia 5 nhóm. Trino không có hàm tương đương trực tiếp — dùng `ntile(5)`
--   (chuẩn ngành cho RFM quintile scoring trên SQL, chia nhóm gần-bằng-nhau theo thứ tự, KHÔNG
--   nội suy). `rank(method='first')` phá ties theo THỨ TỰ XUẤT HIỆN trong DataFrame — vì
--   `groupby("customer_id")` mặc định sort=True, thứ tự đó CHÍNH LÀ customer_id tăng dần -> bắt
--   buộc `order by ..., customer_id asc` làm tie-break phụ trong `ntile()` dưới đây, nếu không
--   (thử THẬT, xem .process_status/M3b.md) NTILE phá ties theo thứ tự vật lý bất định của Trino,
--   lệch Champions tới 22,614 vs kỳ vọng 22,575 (39 khách, KHÔNG chấp nhận được). Sau khi thêm
--   tie-break customer_id: VERIFY THẬT bằng script Python đối chiếu 2 thuật toán trên đúng dữ
--   liệu orders.csv/payments.csv — lệch còn 4/88,123 khách (0.0045%), đúng ở ranh giới ngũ phân
--   vị do khác thuật toán nội suy (không phải bug) — segment "Champions" khớp TUYỆT ĐỐI 22,575
--   khách, các segment còn lại lệch tối đa ±2 khách so với dashboard_rfm_cohort.md.

with snapshot as (
    select max(order_date) as snapshot_date
    from {{ ref('stg_orders') }}
),

non_cancel as (
    select
        o.customer_id,
        o.order_id,
        o.order_date,
        p.payment_value
    from {{ ref('stg_orders') }} o
    left join {{ ref('stg_payments') }} p on o.order_id = p.order_id
    where o.order_status != 'cancelled'
),

agg as (
    select
        customer_id,
        max(order_date) as last_order_date,
        count(distinct order_id) as frequency,
        sum(payment_value) as monetary
    from non_cancel
    group by customer_id
),

with_recency as (
    select
        a.customer_id,
        a.last_order_date,
        a.frequency,
        a.monetary,
        date_diff('day', a.last_order_date, s.snapshot_date) as recency_days
    from agg a
    cross join snapshot s
),

scored as (
    select
        customer_id,
        last_order_date,
        recency_days,
        frequency,
        monetary,
        -- recency: ngày CÀNG NHỎ càng tốt -> đảo ngược ntile (nhóm 1 = recency nhỏ nhất = điểm 5)
        -- tie-break phụ = customer_id asc (khớp pandas rank(method='first'), xem lý do ở trên)
        6 - ntile(5) over (order by recency_days asc, customer_id asc) as r_score,
        -- frequency/monetary: giá trị CÀNG LỚN càng tốt -> ntile tăng dần = điểm tăng dần
        ntile(5) over (order by frequency asc, customer_id asc) as f_score,
        ntile(5) over (order by monetary asc, customer_id asc) as m_score
    from with_recency
)

select
    customer_id,
    last_order_date,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    -- Port NGUYÊN THỨ TỰ if/elif của rfm_segment() (customer_demographics.py dòng 260-278) —
    -- thứ tự CASE WHEN dưới đây PHẢI giữ đúng thứ tự vì các điều kiện chồng lấn nhau.
    case
        when r_score >= 4 and f_score >= 4 and m_score >= 4 then 'Champions'
        when r_score >= 3 and f_score >= 3 and m_score >= 3 then 'Loyal Customers'
        when r_score >= 4 and f_score <= 2 then 'New Customers'
        when r_score = 3 and f_score <= 2 then 'Promising'
        when r_score <= 2 and f_score >= 4 and m_score >= 4 then 'Can''t Lose Them'
        when r_score <= 2 and f_score >= 3 then 'At Risk'
        when r_score <= 2 and f_score <= 2 and m_score >= 3 then 'Hibernating'
        when r_score <= 2 and f_score <= 2 then 'Lost'
        else 'Need Attention'
    end as segment
from scored
