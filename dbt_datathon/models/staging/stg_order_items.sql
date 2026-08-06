{{ config(contract={'enforced': true}) }}

-- Nguồn: iceberg.raw.order_items. phase0_qc W7: 16 dòng trùng cặp (order_id, product_id) là 2
-- line item hợp lệ (khác unit_price/quantity, 0% cặp cùng giá) — grain thật = "dòng hàng",
-- KHÔNG dedup (dedup sẽ lệch đối chiếu sales.csv 0.000%, xem phase0_qc_report.md mục 6).
-- `line_number` = raw `_source_row_number` (M2) đổi tên cho lớp sạch — AN TOÀN làm phần khóa
-- grain vì CSV nguồn tĩnh: cùng file -> cùng thứ tự dòng -> cùng giá trị mọi lần ingest lại.
-- KHÔNG dùng ROW_NUMBER() tính lại ở đây (không đảm bảo thứ tự qua các lần chạy SQL khác nhau).

select
    cast(order_id as bigint) as order_id,
    cast(product_id as bigint) as product_id,
    cast(_source_row_number as bigint) as line_number,
    cast(quantity as bigint) as quantity,
    cast(unit_price as double) as unit_price,
    cast(discount_amount as double) as discount_amount,
    cast(promo_id as varchar) as promo_id,
    cast(promo_id_2 as varchar) as promo_id_2
from {{ source('raw', 'order_items') }}
