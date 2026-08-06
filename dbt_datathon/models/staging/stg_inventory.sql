{{ config(contract={'enforced': true}) }}

-- Nguồn: iceberg.raw.inventory. Grain = (snapshot_date, product_id). phase0_qc W6: panel không
-- cân (chỉ 1,624/2,412 SP xuất hiện) — KHÔNG suy diễn tồn=0 cho SP/tháng vắng mặt, giữ nguyên.

select
    cast(snapshot_date as date) as snapshot_date,
    cast(product_id as bigint) as product_id,
    cast(stock_on_hand as bigint) as stock_on_hand,
    cast(units_received as bigint) as units_received,
    cast(units_sold as bigint) as units_sold,
    cast(stockout_days as bigint) as stockout_days,
    cast(days_of_supply as double) as days_of_supply,
    cast(fill_rate as double) as fill_rate,
    cast(stockout_flag as bigint) as stockout_flag,
    cast(overstock_flag as bigint) as overstock_flag,
    cast(reorder_flag as bigint) as reorder_flag,
    cast(sell_through_rate as double) as sell_through_rate,
    cast(product_name as varchar) as product_name,
    cast(category as varchar) as category,
    cast(segment as varchar) as segment,
    cast(year as bigint) as year,
    cast(month as bigint) as month
from {{ source('raw', 'inventory') }}
