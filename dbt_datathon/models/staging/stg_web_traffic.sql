{{ config(contract={'enforced': true}) }}

-- Nguồn: iceberg.raw.web_traffic. phase0_qc W4: grain thực tế = 1 dòng/ngày toàn site (TRÁI
-- data dictionary "date + traffic_source") -- traffic_source chỉ là nhãn của ngày, KHÔNG sum
-- theo traffic_source. W5: chỉ có từ 2013-01-01 (thiếu 181 ngày đầu 2012), giữ nguyên window.

select
    cast(date as date) as date,
    cast(sessions as bigint) as sessions,
    cast(unique_visitors as bigint) as unique_visitors,
    cast(page_views as bigint) as page_views,
    cast(bounce_rate as double) as bounce_rate,
    cast(avg_session_duration_sec as double) as avg_session_duration_sec,
    cast(traffic_source as varchar) as traffic_source
from {{ source('raw', 'web_traffic') }}
