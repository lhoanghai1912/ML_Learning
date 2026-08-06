{{ config(contract={'enforced': true}) }}

-- Nguồn: iceberg.raw.shipments. phase0_qc I3: shipping_fee (0-32, median 1.73) khác đơn vị tiền
-- tệ so với giá trị đơn -- KHÔNG cộng vào doanh thu ở downstream, chỉ so sánh tương đối.

select
    cast(order_id as bigint) as order_id,
    cast(ship_date as date) as ship_date,
    cast(delivery_date as date) as delivery_date,
    cast(shipping_fee as double) as shipping_fee
from {{ source('raw', 'shipments') }}
