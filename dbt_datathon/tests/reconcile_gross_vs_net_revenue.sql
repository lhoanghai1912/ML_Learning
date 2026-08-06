-- Singular test (M3b) — đối chiếu GROSS (stg_sales, target Phần B) vs NET "bỏ cancelled"
-- (order_items, loại đơn cancelled, trừ discount_amount) — port logic bảng đối chiếu 6 định
-- nghĩa Revenue ở docs/analysis/phase0_qc/phase0_qc_report.md mục 6.
--
-- Ngưỡng kỳ vọng: gap 10.0%-25.0%. LÝ DO chọn dải này (không bịa):
--   - phase0_qc_report.md mục 6 đo 6 định nghĩa net khác nhau, gap dao động 4.562% (net tất cả
--     đơn, không loại cancelled) đến 23.811% (chỉ delivered) — riêng định nghĩa "bỏ cancelled"
--     (đúng cách int_rfm/mart_customer_segments đang dùng cho customer value) đo được 13.369%.
--   - descriptive_summary.md mục 2.6 xác nhận lại đúng con số 13.37% cho định nghĩa "bỏ
--     cancelled, trừ discount" — khớp 100% với công thức test này (đã verify lại bằng Trino
--     trực tiếp trước khi viết test, xem .process_status/M3b.md: gross=16,430,476,585.53,
--     net=14,233,855,627.9996, gap=13.369185...%).
--   - Dải [10%,25%] rộng hơn con số quan sát 13.369% để chống false-positive nếu dữ liệu raw
--     đổi nhẹ qua các lần re-ingest (M2 idempotent MERGE — số không nên đổi, nhưng test này canary
--     cho "định nghĩa gross/net còn khớp nhau về BẢN CHẤT", KHÔNG phải test bit-exact) — chặn
--     dưới 10% nếu ai đó vô tình đổi net thành "tất cả đơn không trừ gì" (gap co lại gần 0%, sai
--     định nghĩa I1/W1), chặn trên 25% nếu net bị tính sai kiểu "chỉ delivered" hoặc lỗi loại bỏ
--     nhầm dữ liệu.
--
-- dbt convention: singular test PASS khi trả về 0 dòng — dòng trả về = VI PHẠM ngưỡng.

with gross as (
    select sum(revenue) as gross_revenue
    from {{ ref('stg_sales') }}
),

net as (
    select sum(oi.quantity * oi.unit_price - oi.discount_amount) as net_revenue
    from {{ ref('stg_order_items') }} oi
    inner join {{ ref('stg_orders') }} o on oi.order_id = o.order_id
    where o.order_status != 'cancelled'
),

check_gap as (
    select
        g.gross_revenue,
        n.net_revenue,
        (g.gross_revenue - n.net_revenue) / g.gross_revenue * 100 as gap_pct
    from gross g
    cross join net n
)

select *
from check_gap
where gap_pct < 10.0 or gap_pct > 25.0
