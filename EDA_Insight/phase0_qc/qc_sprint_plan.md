# Phase 0 QC — Sprint plan & phân việc (10 dimension DQ)

Chủ trì: PM. Sprint: QC-refresh. Scope: **14 bảng raw** trong `/data`. Mục tiêu: chạy 10 kiểm tra data-quality chuẩn, ra 1 **DQ log** tổng hợp có severity + action.

## Bảng nguồn (inventory nhanh — chốt ở QC0.1)

| Bảng | Rows | Candidate key (giả định — verify QC0.3) |
|---|---:|---|
| customers | 121.930 | `customer_id` |
| products | 2.412 | `product_id` |
| geography | 39.948 | `zip` (nghi ko unique → `zip+district`) |
| orders | 646.945 | `order_id` |
| payments | 646.945 | `order_id` (1:1 với orders?) |
| order_items | 714.669 | `order_id+product_id` (nghi có dòng trùng) |
| shipments | 566.067 | `order_id` (< orders → 80.878 đơn ko ship) |
| reviews | 113.551 | `review_id` |
| returns | 39.939 | `return_id` |
| promotions | 49 | `promo_id` |
| inventory | 60.247 | `snapshot_date+product_id` |
| web_traffic | 3.652 | `date` |
| sales | 3.833 | `Date` |
| sample_submission | 548 | `Date` (horizon 2023-01-01→2024-07-01) |

Roles agent: **@de** (kỹ thuật cấu trúc) · **@da** (nghĩa/nghiệp vụ) · **@ds** (số/thống kê) · **@tester** (audit + log). PM điều phối.

---

## Task board — 10 task

### QC0.1 — Snapshot/Inventory · @de · 0.25d · dep: — · blocked: no
Chụp trạng thái 14 bảng: đường dẫn, kích thước, mã hoá, delimiter, số dòng, số cột, sha256 mỗi file (khoá version data).
**AC:** bảng inventory 14 dòng (file/rows/cols/bytes/encoding/sep/sha256); ghi rõ file thừa/thiếu so đề bài.

### QC0.2 — Schema & format · @de · 0.5d · dep: QC0.1 · blocked: no
Với mỗi cột: dtype thực tế vs kỳ vọng; parse `*_date`/`Date`/`snapshot_date` (format thống nhất?); numeric có ký tự lạ/nghìn-phân-cách; enum-column liệt kê giá trị phân biệt.
**Cột trọng điểm:** `order_status`, `payment_method`, `device_type`, `order_source`, `gender`, `age_group`, `acquisition_channel`, `region`, `promo_type`, `stackable_flag`, các `*_flag` inventory.
**AC:** bảng cột×(dtype thực/kỳ vọng/parse OK?/enum values); flag mọi cột parse fail hoặc dtype lệch.

### QC0.3 — Grain & candidate key · @de · 0.5d · dep: QC0.2 · blocked: no
Xác định grain từng bảng + test key: `COUNT(*)==COUNT(DISTINCT key)`. Đặc biệt: `geography.zip` unique hay `zip+district`; `order_items` grain (1 dòng/SKU/đơn hay cho phép trùng); `payments` 1:1 với `orders`; `inventory` `snapshot_date+product_id`.
**AC:** mỗi bảng ghi rõ grain 1 câu + key PASS/FAIL kèm số dòng vi phạm.

### QC0.4 — Referential integrity · @de · 0.75d · dep: QC0.3 · blocked: **YES** (chờ key hợp lệ ở QC0.3)
Kiểm mọi FK edge, đếm orphan (child ko match parent):
- `orders.customer_id→customers` · `orders.zip→geography` · `customers.zip→geography`
- `order_items.order_id→orders` · `order_items.product_id→products` · `order_items.promo_id/promo_id_2→promotions`
- `payments.order_id→orders` · `shipments.order_id→orders` · `returns.order_id→orders` · `returns.product_id→products`
- `reviews.{order_id,product_id,customer_id}→*` · `inventory.product_id→products`
**AC:** ma trận edge×(child rows/orphan count/orphan %); mỗi orphan >0 ghi severity + nghi nguyên nhân.

### QC0.5 — Completeness (null/blank) · @da · 0.5d · dep: QC0.2 · blocked: no
% null/blank/sentinel (`NA`,`-1`,`0` bất thường) mỗi cột. Trọng điểm: `shipments.delivery_date` (đang giao?), `order_items.promo_id_2` (nghi phần lớn null → OK), `reviews.rating/review_title`, `returns.return_reason`, `customers.age_group/gender`.
**AC:** bảng cột×null% sort giảm; phân loại null "hợp lệ nghiệp vụ" vs "thiếu bất thường".

### QC0.6 — Business-rule validity · @da · 1d · dep: QC0.2, QC0.4 · blocked: **YES** (cần enum QC0.2 + FK promo QC0.4)
Kiểm luật nghiệp vụ:
- `order_items.unit_price >= products.cogs`? (đã biết 382 ngày lỗ gộp — đo lại rate)
- `discount_amount <= unit_price*quantity`; `discount_amount >= 0`; `quantity > 0`
- `order_date` nằm trong `[promo.start_date, promo.end_date]` khi có `promo_id`
- `returns.return_quantity <=` qty đã đặt; `refund_amount <= payments.payment_value`; `refund_amount >= 0`
- `reviews.rating ∈ [1,5]`; `review_date >= order_date`
- `payments.installments >= 1`; `payment_value >= 0`
- tỷ lệ 0–1: `bounce_rate`, `fill_rate`, `sell_through_rate`
- date logic: `delivery_date >= ship_date >= order_date`; `end_date >= start_date`
**AC:** mỗi luật ghi rate vi phạm + ví dụ; tách "lỗi data" vs "hiện tượng nghiệp vụ thật" (vd bán dưới giá vốn).

### QC0.7 — Time coverage · @da · 0.5d · dep: QC0.2 · blocked: no
Range min/max + gap ngày mỗi bảng có thời gian: `sales`(2012-07-04→2022-12-31, 3.833d — có ngày thiếu?), `orders.order_date`, `web_traffic`(3.652d — vì sao lệch sales 181d?), `inventory.snapshot_date`, `promotions`, `sample_submission`(548d future). Đối chiếu alignment giữa các bảng.
**AC:** timeline mỗi bảng (start/end/days/missing days); giải thích lệch span web_traffic vs sales; xác nhận forecast horizon ko chồng lịch sử.

### QC0.8 — Duplicate & outlier · @ds · 0.75d · dep: QC0.3 · blocked: no
Dup: full-row duplicate + dup theo key ngoài candidate key (vd cùng `order_id+product_id` nhiều dòng ở order_items). Outlier: IQR/z-score cho `unit_price`, `quantity`, `discount_amount`, `payment_value`, `refund_amount`, `customers.age_group` (nếu numeric), `web_traffic.avg_session_duration_sec`, `products.price/cogs`. Giá trị âm/0 vô lý.
**AC:** bảng dup (loại/count); bảng outlier (cột/method/count/range); phân biệt outlier thật vs lỗi nhập.

### QC0.9 — Cross-table reconciliation · @ds · 1d · dep: QC0.4, QC0.6, QC0.8 · blocked: **YES** (cần RI+rule+dup sạch)
- `sales.Revenue/COGS` vs aggregate gross từ `order_items` (kỳ vọng ~0,0000% — tái xác nhận)
- `sales` gross vs net (loại cancelled + discount) → kỳ vọng gap ~13,37%
- `COUNT(orders)==COUNT(payments)` (646.945==646.945 ✓ verify 1:1)
- `orders - shipments` = 80.878 → khớp đơn cancelled/chưa ship?
- `SUM(payments.payment_value)` vs `SUM(order_items net)`; `SUM(returns.refund_amount)` ≤ payments
- `reviews`/`returns` count vs orders hợp lý
**AC:** mỗi cặp đối chiếu ghi giá trị 2 phía + % lệch + kết luận (khớp/lệch có giải thích/lệch bất thường).

### QC0.10 — Data-quality log · @tester · 0.75d · dep: QC0.1–QC0.9 · blocked: **YES** (gate cuối, gom hết)
Gom mọi phát hiện QC0.1–0.9 thành 1 log chuẩn: `check_id | bảng | cột | dimension | mô tả | count/rate | severity(critical/high/med/low) | phân loại(lỗi data/hiện tượng nghiệp vụ) | action(fix/document/accept) | owner`. Audit độc lập sample lại 3–5 finding nặng nhất.
**AC:** `data_quality_log.csv` + `data_quality_log.md` (tóm tắt điều hành); mỗi critical/high có action rõ; GATE Phase 0: PASS/CONDITIONAL/FAIL.

---

## Đường găng & lịch

```
QC0.1 ▓
  └─QC0.2 ▓▓ ──┬─ QC0.5 ▓▓ (da)
               ├─ QC0.7 ▓▓ (da)
               └─QC0.3 ▓▓ (de) ──┬─ QC0.4 ▓▓▓ (de) ──┐
                                  └─ QC0.8 ▓▓▓ (ds) ──┤
                        QC0.6 ▓▓▓▓ (da, cần QC0.2+0.4)─┤
                                       QC0.9 ▓▓▓▓ (ds)─┤ (cần 0.4+0.6+0.8)
                                                QC0.10 ▓▓▓ (tester, gate)
```
Đường găng: **QC0.1→0.2→0.3→0.4→0.6→0.9→0.10 ≈ 4,25 ngày** (1 luồng). Song song 4 agent ⇒ **~2,5 ngày lịch**.

## Phân việc gọn

| Agent | Task | Tổng est |
|---|---|---:|
| **@de** | QC0.1, 0.2, 0.3, 0.4 | 2,0d |
| **@da** | QC0.5, 0.6, 0.7 | 2,0d |
| **@ds** | QC0.8, 0.9 | 1,75d |
| **@tester** | QC0.10 (gate) | 0,75d |

## Blocker & ETA gỡ

| Task blocked | Chờ | ETA gỡ |
|---|---|---|
| QC0.4 (RI) | key hợp lệ QC0.3 | +0,5d sau QC0.3 xong |
| QC0.6 (business-rule) | enum QC0.2 + FK promo QC0.4 | +0,75d sau QC0.4 |
| QC0.9 (reconciliation) | QC0.4+0.6+0.8 sạch | ngày 3 |
| QC0.10 (DQ log) | tất cả QC0.1–0.9 | ngày cuối, gate |

## Rủi ro

| Rủi ro | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Trùng Phase 0 QC cũ (95ffbd1) → làm lại thừa | cao | trung bình | @de đọc `phase0_qc` cũ trước, chỉ bổ sung dimension thiếu |
| `order_items` grain sai giả định → hỏng RI + reconcile | trung bình | cao | QC0.3 chốt grain TRƯỚC, block QC0.4 đúng thứ tự |
| Lẫn "lỗi data" với "hiện tượng nghiệp vụ" (bán dưới giá vốn) | trung bình | cao | QC0.6 + QC0.10 bắt buộc cột phân loại 2 nhóm |
| Data đổi version giữa chừng | thấp | cao | QC0.1 khoá sha256, mọi task tham chiếu snapshot đó |
