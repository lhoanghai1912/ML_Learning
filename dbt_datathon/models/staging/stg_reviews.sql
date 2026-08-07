{{ config(contract={'enforced': true}) }}

-- Nguồn: iceberg.raw.reviews. phase0_qc: 0 trùng (order_id, product_id); rating trong [1..5];
-- customer_id luôn khớp người đặt đơn.

select
    cast(review_id as varchar) as review_id,
    cast(order_id as bigint) as order_id,
    cast(product_id as bigint) as product_id,
    cast(customer_id as bigint) as customer_id,
    cast(review_date as date) as review_date,
    cast(rating as bigint) as rating,
    cast(review_title as varchar) as review_title
from {{ source('raw', 'reviews') }}
