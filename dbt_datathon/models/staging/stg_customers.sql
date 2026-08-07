{{ config(contract={'enforced': true}) }}

-- Nguồn: iceberg.raw.customers (M2, đã cast kiểu + snake_case tại landing).
-- Làm sạch: chỉ ép kiểu tường minh cho contract, KHÔNG business-rule thêm (phase0_qc: 0 null,
-- 0 trùng PK; 238 khách signup_date < 2012-07-04 — giữ nguyên, quyết định cohort thuộc M3b/da).

select
    cast(customer_id as bigint) as customer_id,
    cast(zip as varchar) as zip,
    cast(city as varchar) as city,
    cast(signup_date as date) as signup_date,
    cast(gender as varchar) as gender,
    cast(age_group as varchar) as age_group,
    cast(acquisition_channel as varchar) as acquisition_channel
from {{ source('raw', 'customers') }}
