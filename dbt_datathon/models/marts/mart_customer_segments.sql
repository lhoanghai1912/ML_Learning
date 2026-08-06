{{ config(materialized='table') }}

-- Grain: 1 dòng/segment (9 segment RFM). Nguồn: {{ ref('int_rfm') }} (grain gốc 1 dòng/customer).
-- Port bảng "Findings (Descriptive)" mục 1 dashboard_rfm_cohort.md — số liệu khách hàng chi tiết
-- theo segment (n_customers, % khách, tổng Monetary, % Monetary, Monetary TB/khách, Recency TB,
-- Frequency TB). Đây LÀ mart tổng hợp cho dashboard/BI — muốn xem chi tiết từng khách hàng dùng
-- {{ ref('int_rfm') }} trực tiếp (grain customer, KHÔNG mất thông tin, dbt intermediate vẫn query
-- được qua Trino dù không "expose" chính thức).

with rfm as (
    select * from {{ ref('int_rfm') }}
),

seg as (
    select
        segment,
        count(*) as n_customers,
        sum(monetary) as total_monetary,
        avg(recency_days) as avg_recency_days,
        avg(frequency) as avg_frequency
    from rfm
    group by segment
),

totals as (
    select
        sum(n_customers) as total_customers,
        sum(total_monetary) as total_monetary_all
    from seg
)

select
    s.segment,
    s.n_customers,
    s.n_customers * 100.0 / t.total_customers as pct_customers,
    s.total_monetary,
    s.total_monetary * 100.0 / t.total_monetary_all as pct_monetary,
    s.total_monetary / s.n_customers as monetary_per_customer,
    s.avg_recency_days,
    s.avg_frequency
from seg s
cross join totals t
order by s.total_monetary desc
