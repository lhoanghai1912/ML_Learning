{{ config(contract={'enforced': true}) }}

-- Nguồn: iceberg.raw.payments. phase0_qc I1: payment_value = net (qty*price - discount), khớp
-- 100% đơn kể cả cancelled/created -> KHÔNG coi là tiền thực thu; lọc order_status khi phân tích
-- dòng tiền (việc của mart/M3b, không xử lý ở staging).

select
    cast(order_id as bigint) as order_id,
    cast(payment_method as varchar) as payment_method,
    cast(payment_value as double) as payment_value,
    cast(installments as bigint) as installments
from {{ source('raw', 'payments') }}
