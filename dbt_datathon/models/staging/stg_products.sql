{{ config(contract={'enforced': true}) }}

-- Nguồn: iceberg.raw.products. phase0_qc: 0 SKU cogs>price ở catalog; 240 product_name trùng
-- giữa các SKU khác nhau (I6) -> luôn dùng product_id làm khóa, KHÔNG dùng product_name.

select
    cast(product_id as bigint) as product_id,
    cast(product_name as varchar) as product_name,
    cast(category as varchar) as category,
    cast(segment as varchar) as segment,
    cast(size as varchar) as size,
    cast(color as varchar) as color,
    cast(price as double) as price,
    cast(cogs as double) as cogs
from {{ source('raw', 'products') }}
