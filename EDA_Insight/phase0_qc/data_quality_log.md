# QC0.10 — Data Quality Log & GATE Phase 0

Owner: @tester · Nguồn: gộp toàn bộ artifact QC0.1–0.9 (`de/`, `da/`, `ds/`) · Log đầy đủ: [`data_quality_log.csv`](./data_quality_log.csv) (30 dòng, mỗi dòng = 1 finding hoặc 1 nhóm finding đồng chất) · Script audit độc lập: [`tester/qc10_independent_audit.py`](./tester/qc10_independent_audit.py).

---

## 1. Tóm tắt điều hành

- Quét **14 bảng raw**, **91 cột**, 10 dimension QC (schema, grain/key, referential integrity, completeness, business-rule, time coverage, duplicate, outlier, reconciliation, audit).
- **30 finding** ghi nhận trong log. Phân bố severity:

| Severity | Số finding | % |
|---|---:|---:|
| critical | 2 | 6.7% |
| high | 3 | 10.0% |
| med | 4 | 13.3% |
| low | 12 | 40.0% |
| none (PASS/informational) | 9 | 30.0% |

- Phân loại: **21 hiện-tượng-nghiệp-vụ hoặc PASS** (không phải lỗi, chỉ cần document/accept) vs **4 lỗi-data thật sự** cần fix (2 critical + 2 high, cùng gốc là 2 root-cause độc lập — xem mục 3).
- **Không phát hiện** vấn đề ở: schema/dtype (0 parse fail/91 cột), full-row duplicate (0/14 bảng), referential integrity (0 orphan/12 cạnh FK), phần lớn business-rule (7/8 luật 0 vi phạm), time alignment tổng thể (sales↔orders↔web_traffic↔sample_submission đều giải thích được, sample_submission xác nhận không leakage).

## 2. 4 lỗi-data cần xử lý (2 root-cause)

| Root cause | Finding liên quan | Rate | Severity |
|---|---|---:|---|
| **A. Hoàn tiền vượt số tiền đã thu** (`refund_amount > payments.payment_value`) | QC0.6-02 (mức dòng return: 3.430/39.939 = 8.59%), QC0.6-03 (mức đơn hàng, tổng hợp: 3.640/36.062 = 10.09%) | 8.6–10.1% | **critical** |
| **B. Đơn hàng đã giao/ship/trả nhưng thiếu bản ghi shipment** (`order_status∈{delivered,shipped,returned}` nhưng không có dòng trong `shipments`) | QC0.6-04 = QC0.9-03 (cùng 1 hiện tượng nhìn từ 2 hướng: business-rule và reconciliation) | 564/566.631 = 0.0995% | **high** |

**Ghi chú quan trọng — root cause B:** toàn bộ 564 dòng vi phạm rơi vào `order_date` 2022-12-22 → 2022-12-31 (10 ngày cuối lịch sử). Đây không phải lỗi rải rác ngẫu nhiên mà tập trung 100% ở đuôi dữ liệu → nghi **ETL cắt/late-arriving data ở batch cuối**, không phải lỗi hệ thống toàn kỳ.

**Root cause A** có pattern đáng ngờ: tỷ lệ `refund/payment` bị chặn trên ở ~1.25x (min=1.000, median=1.097, max=1.250) — không phải nhiễu ngẫu nhiên vô hạn, nên nghi là lỗi phát sinh dữ liệu có chủ đích (tương tự pattern "382 ngày lỗ gộp" đã biết trong sprint plan), không giải thích được bằng `shipping_fee` hay business rule rõ ràng.

## 3. Audit độc lập — 5 finding severity cao nhất (tự chạy lại, không tin số cũ)

Đã tự viết script pandas độc lập, đọc trực tiếp `data/*.csv`, tính lại từ đầu (không copy số từ CSV của de/da/ds), rồi so khớp:

| # | Finding | Số đã báo cáo | Số tự tính lại | Kết quả |
|---|---|---|---|---|
| 1 | `refund_amount > payment_value` (dòng return) | 3.430/39.939 = 8.5881% | 3.430/39.939 = 8.5881% | ✅ khớp |
| 2 | `unit_price < products.cogs` (line-item) | 133.052/714.669 = 18.6173% | 133.052/714.669 = 18.6173% | ✅ khớp |
| 3 | `order_status` thiếu bản ghi shipment | 564/566.631 = 0.0996% | 564/566.631 = 0.0996% | ✅ khớp |
| 4 | `order_items` grain — nhóm trùng (order_id,product_id) | 16 nhóm / 32 dòng | 16 nhóm / 32 dòng | ✅ khớp (đã xác nhận thêm: 0/16 nhóm là full-row-duplicate thật) |
| 5 | `inventory.reorder_flag` — cột chết 100%=0 | distinct=1, 100% | distinct=1, 100% (60.247/60.247) | ✅ khớp |

**Kết luận audit: 5/5 khớp 100%** với số de/da/ds đã báo cáo → độ tin cậy pipeline QC0.1–0.9 cao, không phát hiện sai số tính toán trong các artifact nguồn.

## 4. Đối chiếu impact với model đang dùng (Phase 6–8)

Đã kiểm tra `phase6_features/build_features.py`: pipeline feature/model hiện tại **chỉ đọc `sales.csv` + `sample_submission.csv`** (daily aggregate), **không** đọc trực tiếp `orders/order_items/returns/shipments/web_traffic/inventory` raw. Do đó:
- 2 root-cause lỗi-data (A, B) ở trên **chưa ảnh hưởng** số liệu forecast Phase 8 hiện tại (vì raw `returns`/`shipments` không phải input trực tiếp).
- Nhưng **bắt buộc phải xử lý trước khi**: (a) mở rộng feature set dùng raw `returns`/`shipments`/`web_traffic`, (b) dùng cho báo cáo tài chính/logistics KPI riêng ngoài forecast doanh thu.

## 5. GATE Phase 0

# GATE: **CONDITIONAL PASS**

Data đủ chất lượng để tiếp tục dùng cho forecast doanh thu (Phase 6–9 hiện tại, dựa trên `sales.csv` aggregate — không bị ảnh hưởng bởi 2 lỗi-data phát hiện). Không FAIL vì: 0 lỗi schema/RI/full-duplicate, lỗi-data phát hiện có phạm vi hẹp (≤10.1%) và có root-cause rõ ràng, không lan toàn bộ dataset.

### Điều kiện bắt buộc trước khi dùng raw tables cho phạm vi rộng hơn forecast hiện tại:

1. **[critical]** Điều tra nguồn gốc 3.430 dòng return (mức đơn: 3.640) có `refund_amount > payment_value`. Nếu không tìm được business rule giải thích (vd phí ẩn, làm tròn, hoàn kèm phí ship) → cap `refund_amount` tại `payment_value` hoặc loại trừ khỏi mọi SUM dùng cho báo cáo/feature tài chính. **Owner đề xuất: @da + @de.**
2. **[high]** Điều tra 564 đơn `delivered/shipped/returned` thiếu bản ghi `shipments`, tập trung 100% ở 2022-12-22→2022-12-31. Xác nhận có phải ETL cắt batch cuối không; nếu đúng, bổ sung dữ liệu hoặc loại 10 ngày này khỏi mọi phân tích logistics/fulfillment-rate. **Owner đề xuất: @de.**
3. **[med]** Loại `inventory.reorder_flag` khỏi mọi feature set (cột chết, 100%=0, vô nghĩa).
4. **[med]** Khi dùng `web_traffic` làm feature xuyên suốt lịch sử: xử lý rõ khoảng trống 181 ngày đầu (2012-07-04→2012-12-31) — loại giai đoạn đó khỏi train hoặc impute có ghi chú, không được coi là "0 traffic thật".
5. Giữ nguyên (không sửa) hiện tượng bán dưới giá vốn (18.6% dòng hàng, `unit_price<cogs`) — đã xác nhận là business phenomenon thật (chiến lược giá/khuyến mãi sâu), KHÔNG phải lỗi, KHÔNG được "sửa" số liệu này.

### Không cần hành động thêm (accept as-is)
QC0.2-01, QC0.4-01, QC0.5-01/02/03, QC0.6-05, QC0.7-02/03/04, QC0.8-01/03/04/05/06/07, QC0.9-01/02/04/05, và các finding "hiện-tượng-nghiệp-vụ" mức low/med khác trong `data_quality_log.csv` — đã document đầy đủ lý do, không cần fix.

---
Báo PM: **GATE Phase 0 = CONDITIONAL PASS**, 2 điều kiện critical/high (mục 5.1, 5.2) cần @de/@da xử lý trước khi mở rộng feature set ngoài `sales.csv`. Model Phase 8 hiện tại không bị chặn.
