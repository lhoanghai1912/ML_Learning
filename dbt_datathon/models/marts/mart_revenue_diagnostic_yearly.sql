{{ config(materialized='table') }}

-- Grain: 1 dòng/year (2013-2022, 10 dòng). Trang "Chẩn đoán nguyên nhân" — gap lớn nhất chỉ ra ở
-- docs/analysis/EDA_FINDINGS.md mục "Hình dung Dashboard". Port 3 chart trong
-- notebooks/02b_eda_nguyen_nhan.ipynb: "Doanh thu khách mới vs khách cũ", "Waterfall Gross->Net",
-- "Q1 ASP vs Volume".
--
-- Nguồn: {{ ref('int_diagnostic_line_items') }} (revenue/qty/cancelled/discount/new-repeat) +
-- {{ ref('stg_orders') }} TRỰC TIẾP cho n_orders/n_active_cust — KHÔNG suy từ line-item join, vì
-- inner join order_items có thể thiếu order_id nếu đơn không có dòng hàng nào (khớp đúng cách
-- notebook gốc tính "ord_all" riêng từ `orders`, không suy ra từ `li`).
--
-- refund_loss theo năm: notebook gốc CHỈ tính refund_loss TOÀN KỲ (returns["refund_amount"].sum(),
-- KHÔNG lọc/join năm nào) — mart này MỞ RỘNG có chủ đích thành theo năm (cần join returns->orders
-- lấy order_date mới có year), lọc year(order_date) BETWEEN 2013 AND 2022 để NHẤT QUÁN với mọi
-- cột khác trong mart (gross_booked/cancelled_loss/discount_loss đều lọc đúng khung này qua `li`).
--
-- PHÁT HIỆN khi verify (2026-08-10, không suy đoán — đối chiếu Trino vs pandas độc lập): tổng
-- refund_loss mart (0.487 tỷ) THẤP HƠN số notebook gốc công bố (0.511 tỷ) — chênh 0.024 tỷ vì
-- 2,115 dòng returns.csv (trong tổng 39,939) thuộc đơn hàng đặt năm 2012 (ngoài khung 2013-2022).
-- Đây KHÔNG phải bug ở mart — notebook gốc tính refund_loss KHÔNG NHẤT QUÁN với chính nó (mọi số
-- khác trong cùng chart đều lọc 2013-2022 qua `li`, riêng refund lấy nguyên `returns.csv` không
-- lọc gì). Mart này CHỦ ĐỘNG SỬA sự không nhất quán đó — số ở đây đúng hơn số notebook gốc, không
-- phải khớp kém hơn. Xem PROCESS.md log 2026-08-10 mục "mart chẩn đoán nguyên nhân" để đọc đầy đủ.

with li as (
    select * from {{ ref('int_diagnostic_line_items') }}
),

first_order as (
    -- Khớp đúng notebook: first_order tính trên TOÀN BỘ orders (không lọc năm 2013-2022) — khách
    -- mua lần đầu 2012 vẫn tính đúng là "khách cũ" nếu quay lại 2013+.
    select customer_id, min(order_date) as first_order_date
    from {{ ref('stg_orders') }}
    group by customer_id
),

li_tagged as (
    select
        li.*,
        (li.order_date = fo.first_order_date) as is_new_customer_order
    from li
    left join first_order fo on li.customer_id = fo.customer_id
),

revenue_agg as (
    select
        year,
        sum(line_revenue) as gross_booked,
        sum(case when is_new_customer_order then line_revenue else 0 end) as revenue_new,
        sum(case when not is_new_customer_order then line_revenue else 0 end) as revenue_repeat,
        sum(case when order_status = 'cancelled' then line_revenue else 0 end) as cancelled_loss,
        sum(case when order_status != 'cancelled' then discount_amount else 0 end) as discount_loss,
        sum(quantity) as qty
    from li_tagged
    group by year
),

orders_agg as (
    select
        year(order_date) as year,
        count(distinct order_id) as n_orders,
        count(distinct customer_id) as n_active_cust
    from {{ ref('stg_orders') }}
    where year(order_date) between 2013 and 2022
    group by year(order_date)
),

returns_agg as (
    select
        year(o.order_date) as year,
        sum(r.refund_amount) as refund_loss
    from {{ ref('stg_returns') }} r
    inner join {{ ref('stg_orders') }} o on r.order_id = o.order_id
    where year(o.order_date) between 2013 and 2022
    group by year(o.order_date)
)

select
    r.year,
    r.gross_booked,
    r.revenue_new,
    r.revenue_repeat,
    r.revenue_repeat * 100.0 / nullif(r.gross_booked, 0) as pct_revenue_repeat,
    r.cancelled_loss,
    r.discount_loss,
    coalesce(ret.refund_loss, 0) as refund_loss,
    r.gross_booked - r.cancelled_loss - r.discount_loss - coalesce(ret.refund_loss, 0) as net_revenue,
    r.qty,
    o.n_orders,
    o.n_active_cust,
    r.gross_booked / nullif(r.qty, 0) as asp,
    r.gross_booked / nullif(o.n_orders, 0) as aov
from revenue_agg r
inner join orders_agg o on r.year = o.year
left join returns_agg ret on r.year = ret.year
order by r.year
