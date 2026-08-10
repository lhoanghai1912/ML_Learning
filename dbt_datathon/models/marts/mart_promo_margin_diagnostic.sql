{{ config(materialized='table') }}

-- Grain: 1 dòng/(year, month, category, has_promo). Trang "Chẩn đoán nguyên nhân" — port "Tỷ lệ
-- bán dưới giá vốn theo category" (notebooks/02b_eda_nguyen_nhan.ipynb) VÀ mở khóa cờ mùa vụ
-- chưa có mart nào trước đây (chương trình khuyến mãi "Urban Blowout" chỉ chạy năm LẺ, tháng 8 —
-- xem docs/analysis/EDA_FINDINGS.md Phần A "Doanh thu tháng & biên lãi gộp"/Phần B "Q2").
--
-- Grain cố ý mịn (year x month x category x has_promo, tối đa 10x12x4x2=960 dòng) thay vì bake
-- sẵn từng lát cắt riêng (kiểu mart_channel_perf) — để BI tool tự pivot theo category HOẶC promo
-- HOẶC tháng HOẶC năm-chẵn/lẻ (mod(year,2)) mà không cần thêm mart nào nữa.
--
-- KHÔNG gồm AOV promo/không-promo — đã có sẵn ở {{ ref('mart_channel_perf') }}
-- (dimension_type='promo'), không làm lại 2 lần.

with li as (
    select * from {{ ref('int_diagnostic_line_items') }}
)

select
    year,
    month,
    category,
    has_promo,
    mod(year, 2) = 1 as is_odd_year,
    count(*) as n_lines,
    sum(case when below_cost then 1 else 0 end) as n_below_cost,
    sum(case when below_cost then 1 else 0 end) * 100.0 / nullif(count(*), 0) as pct_below_cost,
    sum(line_revenue) as revenue,
    sum(line_cogs) as cogs,
    (sum(line_revenue) - sum(line_cogs)) * 100.0 / nullif(sum(line_revenue), 0) as margin_pct
from li
group by year, month, category, has_promo
order by year, month, category, has_promo
