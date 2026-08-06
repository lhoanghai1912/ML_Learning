{{ config(contract={'enforced': true}) }}

-- Nguồn: iceberg.raw.sample_submission. phase0_qc I2: file mẫu có sẵn giá trị placeholder cho
-- revenue/cogs -- bài nộp (Phần B) phải ghi đè toàn bộ 2 cột, không dùng giá trị ở đây làm căn cứ.

select
    cast(date as date) as date,
    cast(revenue as double) as revenue,
    cast(cogs as double) as cogs
from {{ source('raw', 'sample_submission') }}
