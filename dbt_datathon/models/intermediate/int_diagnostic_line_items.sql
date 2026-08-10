{{
    config(
        materialized='incremental',
        unique_key='diagnostic_line_id',
        incremental_strategy='merge',
        on_schema_change='sync_all_columns'
    )
}}

-- Grain: 1 dòng/(order_id, product_id, line_number) — cùng grain stg_order_items, JOIN thêm
-- orders/products/geography để có category/region/order_status/promo_id. Nguồn dùng chung cho
-- mart_revenue_diagnostic_yearly + mart_promo_margin_diagnostic — tránh viết lại join 3 bảng 2
-- lần. Port `li` build trong notebooks/02b_eda_nguyen_nhan.ipynb (đã verify sanity check trong
-- notebook: line_revenue rebuilt khớp sales.csv 0.000% MAPE).
--
-- Lọc year(order_date) BETWEEN 2013 AND 2022 — khớp đúng phạm vi notebook gốc (loại nửa năm 2012
-- lẻ, không đủ 1 năm để so YoY).
--
-- line_revenue/line_cogs = GROSS (quantity * unit_price / cogs, TRƯỚC chiết khấu) — chiết khấu
-- tính riêng ở mart_revenue_diagnostic_yearly qua discount_amount, KHÔNG trừ 2 lần ở đây.

with li as (
    select
        oi.order_id,
        oi.product_id,
        oi.line_number,
        oi.quantity,
        oi.unit_price,
        oi.discount_amount,
        oi.promo_id,
        o.order_date,
        o.order_status,
        o.customer_id,
        pr.category,
        pr.cogs as unit_cogs,
        g.region,
        year(o.order_date) as year,
        month(o.order_date) as month,
        (oi.promo_id is not null) as has_promo,
        (oi.quantity * oi.unit_price) as line_revenue,
        (oi.quantity * pr.cogs) as line_cogs,
        (oi.unit_price < pr.cogs) as below_cost
    from {{ ref('stg_order_items') }} oi
    inner join {{ ref('stg_orders') }} o on oi.order_id = o.order_id
    left join {{ ref('stg_products') }} pr on oi.product_id = pr.product_id
    left join {{ ref('stg_geography') }} g on o.zip = g.zip
    where year(o.order_date) between 2013 and 2022
)

select
    cast(order_id as varchar) || '|' || cast(product_id as varchar) || '|' || cast(line_number as varchar)
        as diagnostic_line_id,
    order_id,
    product_id,
    line_number,
    quantity,
    unit_price,
    discount_amount,
    promo_id,
    order_date,
    order_status,
    customer_id,
    category,
    unit_cogs,
    region,
    year,
    month,
    has_promo,
    line_revenue,
    line_cogs,
    below_cost
from li
