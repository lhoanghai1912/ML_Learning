{{ config(contract={'enforced': true}) }}

-- Nguồn: iceberg.raw.geography. phase0_qc: 0 null, zip là mã định danh (không tính toán số học).

select
    cast(zip as varchar) as zip,
    cast(city as varchar) as city,
    cast(region as varchar) as region,
    cast(district as varchar) as district
from {{ source('raw', 'geography') }}
