{{
    config(
        materialized='incremental',
        unique_key='date',
        incremental_strategy='merge',
        on_schema_change='sync_all_columns'
    )
}}

-- Grain: 1 dòng/ngày (2012-07-04 .. 2022-12-31, 3.833 ngày liên tục — khớp stg_sales).
-- Nguồn: {{ ref('stg_sales') }} (GROSS toàn bộ đơn kể cả cancelled, target Phần B — phase0_qc W1).
-- Port: docs/analysis/phase1_descriptive/eda_training_charts.py mục 1 (daily + MA30 30 ngày) và
-- mục 2 (doanh thu tháng + margin %).
--
-- Vì sao "incremental" nhưng SELECT luôn FULL stg_sales (không filter is_incremental())?
-- MA30/monthly margin là window function cần TOÀN BỘ chuỗi ngày liền mạch phía trước để tính
-- đúng cho MỌI dòng (kể cả dòng cũ nếu logic đổi) — nếu chỉ quét batch mới sẽ thiếu 29 ngày lookback
-- và làm sai MA30 của các ngày đầu batch. Dữ liệu nguồn tĩnh (2012-2022, lịch sử cố định) và nhỏ
-- (3.833 dòng) nên full recompute mỗi lần chạy rẻ (< 1s). MERGE theo unique_key=date vẫn đảm bảo
-- idempotent thật (dán log verify 2 lần chạy trong .process_status/M3b.md) — đây là lựa chọn CÓ
-- CHỦ ĐÍCH, không phải thiếu incremental filter do quên.

with daily as (
    select
        date,
        revenue,
        cogs,
        revenue - cogs as gross_profit,
        case when revenue != 0 then (revenue - cogs) / revenue * 100 else null end as margin_pct
    from {{ ref('stg_sales') }}
),

with_ma as (
    select
        date,
        revenue,
        cogs,
        gross_profit,
        margin_pct,
        avg(revenue) over (order by date rows between 29 preceding and current row) as revenue_ma30,
        avg(cogs) over (order by date rows between 29 preceding and current row) as cogs_ma30
    from daily
),

monthly as (
    select
        date_trunc('month', date) as month_start,
        sum(revenue) as monthly_revenue,
        sum(cogs) as monthly_cogs
    from daily
    group by date_trunc('month', date)
)

select
    d.date,
    d.revenue,
    d.cogs,
    d.gross_profit,
    d.margin_pct,
    d.revenue_ma30,
    d.cogs_ma30,
    date_trunc('month', d.date) as month_start,
    m.monthly_revenue,
    m.monthly_cogs,
    case
        when m.monthly_revenue != 0
        then (m.monthly_revenue - m.monthly_cogs) / m.monthly_revenue * 100
        else null
    end as monthly_margin_pct
from with_ma d
inner join monthly m on date_trunc('month', d.date) = m.month_start
