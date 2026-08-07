{{ config(materialized='table') }}

-- Grain: 1 dòng/ngày. Nguồn: {{ ref('int_daily_revenue') }} — mart phục vụ dashboard doanh thu
-- Phần A (port docs/analysis/phase1_descriptive/eda_training_charts.py, xem chi tiết công thức ở
-- int_daily_revenue.sql). Thêm so với intermediate:
--   - revenue_yoy_pct: so cùng NGÀY LỊCH năm trước (date_add('year', -1, date), KHÔNG offset cố
--     định 365 ngày để tránh lệch năm nhuận — 29/2 không có ngày tương ứng năm không nhuận sẽ NULL,
--     đúng hành vi, không suy diễn).
--   - revenue_rank_desc: hạng ngày theo doanh thu cao nhất (đối chiếu "Top 5 ngày doanh thu cao
--     nhất" in ra ở cuối eda_training_charts.py).
--   - year/month/day_of_week: cột tiện dụng cho filter dashboard (KHÔNG đổi grain, vẫn 1 dòng/ngày).

with base as (
    select * from {{ ref('int_daily_revenue') }}
),

with_yoy as (
    select
        b.*,
        py.revenue as revenue_prior_year,
        case
            when py.revenue is not null and py.revenue != 0
            then (b.revenue - py.revenue) / py.revenue * 100
            else null
        end as revenue_yoy_pct
    from base b
    left join base py on py.date = date_add('year', -1, b.date)
)

select
    date,
    revenue,
    cogs,
    gross_profit,
    margin_pct,
    revenue_ma30,
    cogs_ma30,
    month_start,
    monthly_revenue,
    monthly_cogs,
    monthly_margin_pct,
    revenue_prior_year,
    revenue_yoy_pct,
    year(date) as year,
    month(date) as month,
    day_of_week(date) as day_of_week,
    rank() over (order by revenue desc) as revenue_rank_desc
from with_yoy
