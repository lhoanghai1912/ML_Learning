{{ config(materialized='table') }}

-- Grain: 1 dòng/(year, dimension_type, dimension_value) — bảng "long"/tidy hợp nhất 4 lát cắt
-- diagnostic đã port từ docs/analysis/phase2_diagnostic/revenue_diagnostic.py:
--   dimension_type='channel'  -> order_source theo năm (mục 11, `11_channel_trend.png`)
--   dimension_type='category' -> category theo năm (mục 1/07, `07_category_share.png`)
--   dimension_type='region'   -> region theo năm (mục 2/08, `08_region_trend.png`)
--   dimension_type='promo'    -> AOV có/không promo, year=NULL (TOÀN KỲ 2013-2022, khớp cách
--                                tính gốc KHÔNG chia theo năm ở mục 8/14 `14_promo_effect.png`)
-- revenue/cogs/margin_pct/share_pct chỉ có giá trị ở 3 dimension_type đầu; aov/n_orders chỉ có ở
-- 'promo' — cột dùng chung 1 bảng nên NULL chéo nhau có chủ đích (KHÔNG lệch câm, ghi rõ ở đây).
-- Lọc year BETWEEN 2013-2022 (loại nửa năm 2012 lẻ) — ĐÚNG filter gốc trong revenue_diagnostic.py
-- dòng 46/53: `li[li["year"].between(2013, 2022)]`, đồng bộ mọi chart Diagnostic.
-- line_revenue = quantity * unit_price (GROSS, khớp sales.csv theo phase0_qc — dùng cho
-- channel/category/region); AOV mục promo dùng CÙNG line_revenue (khớp đúng cách tính gốc
-- `li["line_revenue"]`, KHÔNG trừ discount — xem revenue_diagnostic.py dòng 214-215).
-- AOV promo port ĐÚNG group-key gốc `groupby(["order_id","has_promo"])` (dòng 214): nếu 1 đơn có
-- CẢ dòng có-promo lẫn KHÔNG-promo, source gốc tách thành 2 "order_value" riêng (tổng dòng
-- promo/không-promo của CÙNG order_id) rồi mới average theo has_promo — KHÔNG phải AOV đúng
-- nghĩa "giá trị đơn theo có/không promo" (đơn mixed bị đếm 2 lần, 1 lần mỗi phía) — giữ nguyên
-- hành vi này để khớp số 27,945 / 21,896 VND đã công bố ở diagnostic_revenue.md mục 8, KHÔNG tự
-- sửa lại logic cho "đúng" hơn (sẽ đổi số so với báo cáo đã duyệt).

with li as (
    select
        oi.order_id,
        oi.product_id,
        oi.quantity * oi.unit_price as line_revenue,
        oi.quantity * pr.cogs as line_cogs,
        (oi.promo_id is not null) as has_promo,
        o.order_date,
        year(o.order_date) as year,
        o.order_source,
        pr.category,
        g.region
    from {{ ref('stg_order_items') }} oi
    inner join {{ ref('stg_orders') }} o on oi.order_id = o.order_id
    left join {{ ref('stg_products') }} pr on oi.product_id = pr.product_id
    left join {{ ref('stg_geography') }} g on o.zip = g.zip
    where year(o.order_date) between 2013 and 2022
),

channel_trend as (
    select
        year,
        'channel' as dimension_type,
        order_source as dimension_value,
        sum(line_revenue) as revenue,
        sum(line_cogs) as cogs,
        (sum(line_revenue) - sum(line_cogs)) / nullif(sum(line_revenue), 0) * 100 as margin_pct,
        sum(line_revenue) * 100.0 / sum(sum(line_revenue)) over (partition by year) as share_pct,
        cast(null as double) as aov,
        cast(null as bigint) as n_orders
    from li
    group by year, order_source
),

category_share as (
    select
        year,
        'category' as dimension_type,
        category as dimension_value,
        sum(line_revenue) as revenue,
        sum(line_cogs) as cogs,
        (sum(line_revenue) - sum(line_cogs)) / nullif(sum(line_revenue), 0) * 100 as margin_pct,
        sum(line_revenue) * 100.0 / sum(sum(line_revenue)) over (partition by year) as share_pct,
        cast(null as double) as aov,
        cast(null as bigint) as n_orders
    from li
    group by year, category
),

region_share as (
    select
        year,
        'region' as dimension_type,
        region as dimension_value,
        sum(line_revenue) as revenue,
        sum(line_cogs) as cogs,
        (sum(line_revenue) - sum(line_cogs)) / nullif(sum(line_revenue), 0) * 100 as margin_pct,
        sum(line_revenue) * 100.0 / sum(sum(line_revenue)) over (partition by year) as share_pct,
        cast(null as double) as aov,
        cast(null as bigint) as n_orders
    from li
    group by year, region
),

order_promo as (
    select
        order_id,
        has_promo,
        sum(line_revenue) as order_value
    from li
    group by order_id, has_promo
),

promo_aov as (
    select
        cast(null as bigint) as year,
        'promo' as dimension_type,
        case when has_promo then 'with_promo' else 'without_promo' end as dimension_value,
        cast(null as double) as revenue,
        cast(null as double) as cogs,
        cast(null as double) as margin_pct,
        cast(null as double) as share_pct,
        avg(order_value) as aov,
        count(*) as n_orders
    from order_promo
    group by has_promo
)

select * from channel_trend
union all
select * from category_share
union all
select * from region_share
union all
select * from promo_aov
