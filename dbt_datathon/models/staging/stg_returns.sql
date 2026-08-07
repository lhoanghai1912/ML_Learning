{{ config(contract={'enforced': true}) }}

-- Nguồn: iceberg.raw.returns. phase0_qc W9: 1 dòng return_quantity > quantity gốc, 1 dòng
-- refund_amount > gross dòng hàng gốc — giữ nguyên (không tự sửa), cắt trần thuộc mart/M3b.

select
    cast(return_id as varchar) as return_id,
    cast(order_id as bigint) as order_id,
    cast(product_id as bigint) as product_id,
    cast(return_date as date) as return_date,
    cast(return_reason as varchar) as return_reason,
    cast(return_quantity as bigint) as return_quantity,
    cast(refund_amount as double) as refund_amount
from {{ source('raw', 'returns') }}
