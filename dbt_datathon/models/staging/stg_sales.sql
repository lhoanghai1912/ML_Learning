{{ config(contract={'enforced': true}) }}

-- Nguồn: iceberg.raw.sales. phase0_qc W1: revenue = GROSS (qty*unit_price) TẤT CẢ đơn kể cả
-- cancelled, KHÔNG trừ discount/refund; cogs = qty*cogs catalog cùng mask (MAPE tái dựng
-- 0.000% so với order_items) -- đây LÀ target forecast Phần B, giữ nguyên nghĩa gross, KHÔNG
-- suy diễn lại net ở staging. Header CSV gốc PascalCase (Date/Revenue/COGS, phase0_qc I7) đã
-- được chuẩn hoá snake_case sẵn ở landing M2 -- không cần đổi tên ở đây.

select
    cast(date as date) as date,
    cast(revenue as double) as revenue,
    cast(cogs as double) as cogs
from {{ source('raw', 'sales') }}
