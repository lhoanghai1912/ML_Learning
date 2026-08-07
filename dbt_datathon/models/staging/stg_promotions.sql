{{ config(contract={'enforced': true}) }}

-- Nguồn: iceberg.raw.promotions. phase0_qc W10: applicable_category thiếu 40/50 (80%) — theo
-- data dictionary nghĩa là "áp dụng mọi category" -> impute 'all_categories' thay vì để NULL
-- (khuyến nghị explicit của phase0_qc_report.md mục 8.2, áp dụng đúng ở lớp staging).

select
    cast(promo_id as varchar) as promo_id,
    cast(promo_name as varchar) as promo_name,
    cast(promo_type as varchar) as promo_type,
    cast(discount_value as double) as discount_value,
    cast(start_date as date) as start_date,
    cast(end_date as date) as end_date,
    coalesce(cast(applicable_category as varchar), 'all_categories') as applicable_category,
    cast(promo_channel as varchar) as promo_channel,
    cast(stackable_flag as bigint) as stackable_flag,
    cast(min_order_value as double) as min_order_value
from {{ source('raw', 'promotions') }}
