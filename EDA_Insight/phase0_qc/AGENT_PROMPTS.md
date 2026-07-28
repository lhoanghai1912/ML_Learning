# Phase 0 QC — Prompt dispatch (4 window song song)

Mỗi block dưới = 1 prompt copy-paste vào **1 window Claude Code riêng**. Chạy đồng thời được — handoff dependency qua file marker trong `EDA_Insight/phase0_qc/_status/`.

**Quy ước chung (mọi window):**
- Repo: `/Users/lhoanghai_/Documents/Study/Dự án datathon2026`
- Data raw: `<repo>/data/*.csv` (14 bảng). Output QC: `<repo>/EDA_Insight/phase0_qc/`
- Đọc `qc_sprint_plan.md` trước khi làm. KHÔNG sửa file của agent khác.
- Xong 1 task → ghi marker `_status/qcNN.done` — **BẮT BUỘC đúng format: `qc` thường + 2 chữ số + `.done`** (QC0.1→`qc01.done`, QC0.6→`qc06.done`, QC0.10→`qc10.done`). KHÔNG dùng `QC0.1.done`. Poll-loop downstream match đúng tên này. Nội dung: timestamp + đường dẫn artifact.
- Task blocked → **poll** marker upstream bằng bash until-loop, không tự bịa số.
- Schema 14 bảng đã có trong `qc_sprint_plan.md` — dùng, không re-discover.

Thứ tự khởi động: **DE chạy trước** (nhả 0.2, 0.3, 0.4). DA/DS bắt đầu ngay phần không phụ thuộc, tự chờ marker cho phần phụ thuộc. TESTER chạy cuối.

---

## 🪟 WINDOW 1 — Agent @de (structural)

```
Bạn là @de (data engineer) trong team Datathon 2026. Repo: /Users/lhoanghai_/Documents/Study/Dự án datathon2026.
Đọc EDA_Insight/phase0_qc/qc_sprint_plan.md. Bạn sở hữu QC0.1, QC0.2, QC0.3, QC0.4 — chạy TUẦN TỰ trong window này.
Data: <repo>/data/*.csv (14 bảng). Output: <repo>/EDA_Insight/phase0_qc/de/. Dùng python3 + pandas.

Nhiệm vụ:
QC0.1 Snapshot/inventory — 14 bảng: rows, cols, bytes, encoding, delimiter, sha256. Ghi de/qc01_inventory.csv.
QC0.2 Schema & format — mỗi cột: dtype thực/kỳ vọng, parse date OK?, enum values các cột phân loại (order_status, payment_method, device_type, order_source, gender, age_group, acquisition_channel, region, promo_type, stackable_flag, *_flag). Flag cột parse fail/dtype lệch. Ghi de/qc02_schema.csv + de/qc02_enums.md.
QC0.3 Grain & candidate key — mỗi bảng: grain 1 câu + test COUNT(*)==COUNT(DISTINCT key). Đặc biệt verify: geography.zip unique hay zip+district; order_items grain (order_id+product_id có trùng?); payments 1:1 orders; inventory snapshot_date+product_id. Ghi de/qc03_keys.csv (bảng|grain|key|pass|violations).
QC0.4 Referential integrity — đếm orphan mọi FK edge: orders.customer_id→customers, orders.zip→geography, customers.zip→geography, order_items.order_id→orders, order_items.product_id→products, order_items.promo_id→promotions, order_items.promo_id_2→promotions, payments.order_id→orders, shipments.order_id→orders, returns.order_id→orders, returns.product_id→products, reviews.{order_id,product_id,customer_id}→*, inventory.product_id→products. Ghi de/qc04_ri.csv (edge|child_rows|orphans|orphan_pct|severity).

Sau MỖI task: ghi marker EDA_Insight/phase0_qc/_status/qcNN.done — ĐÚNG format `qc`+2 chữ số thường: qc01.done, qc02.done, qc03.done, qc04.done (KHÔNG viết QC0.1.done). QC0.4 phụ thuộc key hợp lệ QC0.3 — chỉ chạy sau khi qc03 xong.
Nguyên tắc: KHÔNG sửa data. Số vi phạm phải kèm ví dụ. Phân biệt lỗi-data vs hiện-tượng-nghiệp-vụ. Xong 4 task → tóm tắt severity cao nhất cho PM.
```

---

## 🪟 WINDOW 2 — Agent @da (semantic/business)

```
Bạn là @da (data analyst) team Datathon 2026. Repo: /Users/lhoanghai_/Documents/Study/Dự án datathon2026.
Đọc EDA_Insight/phase0_qc/qc_sprint_plan.md. Bạn sở hữu QC0.5, QC0.7 (chạy NGAY), QC0.6 (chờ @de).
Data: <repo>/data/*.csv. Output: <repo>/EDA_Insight/phase0_qc/da/. python3 + pandas.

CHẠY NGAY (chỉ cần data raw):
QC0.5 Completeness — % null/blank/sentinel mỗi cột 14 bảng, sort giảm. Phân loại null "hợp lệ nghiệp vụ" (vd shipments.delivery_date đang giao, order_items.promo_id_2) vs "thiếu bất thường". Ghi da/qc05_completeness.csv.
QC0.7 Time coverage — range min/max + missing days mỗi bảng có thời gian: sales, orders.order_date, web_traffic, inventory.snapshot_date, promotions, reviews, returns, shipments, sample_submission. Giải thích lệch span web_traffic(3652d) vs sales(3833d)=181 ngày. Xác nhận sample_submission (548d, 2023-01-01→2024-07-01) KHÔNG chồng lịch sử. Ghi da/qc07_timecoverage.csv + note.md.

CHỜ RỒI CHẠY (blocked): QC0.6 Business-rule cần enum QC0.2 + FK promo QC0.4 của @de.
Trước khi chạy QC0.6, poll marker:
  until [ -f EDA_Insight/phase0_qc/_status/qc04.done ]; do sleep 15; done
QC0.6 luật: order_items.unit_price>=products.cogs (đo rate, đã biết ~382 ngày lỗ gộp); discount_amount trong [0, unit_price*quantity]; quantity>0; order_date trong [promo.start,end] khi có promo_id; returns.return_quantity<=qty đặt; refund_amount trong [0, payment_value]; reviews.rating∈[1,5] & review_date>=order_date; installments>=1; payment_value>=0; tỷ lệ 0-1 (bounce_rate, fill_rate, sell_through_rate); date logic delivery>=ship>=order, promo end>=start. Ghi da/qc06_business_rules.csv (rule|violations|rate|example|loại[lỗi-data/nghiệp-vụ]).

Sau mỗi task ghi marker _status/qcNN.done ĐÚNG format `qc`+2 chữ số thường: qc05.done, qc07.done, qc06.done (KHÔNG viết QC0.5.done). KHÔNG sửa data. Xong 3 task → tóm tắt cho PM.
```

---

## 🪟 WINDOW 3 — Agent @ds (statistical/numeric)

```
Bạn là @ds (data scientist) team Datathon 2026. Repo: /Users/lhoanghai_/Documents/Study/Dự án datathon2026.
Đọc EDA_Insight/phase0_qc/qc_sprint_plan.md. Bạn sở hữu QC0.8 (chờ QC0.3), QC0.9 (chờ 0.4+0.6+0.8).
Data: <repo>/data/*.csv. Output: <repo>/EDA_Insight/phase0_qc/ds/. python3 + pandas + numpy.

QC0.8 Duplicate & outlier — chờ grain của @de:
  until [ -f EDA_Insight/phase0_qc/_status/qc03.done ]; do sleep 15; done
Dup: full-row duplicate + dup theo candidate key (đặc biệt order_items order_id+product_id). Outlier IQR+z-score: unit_price, quantity, discount_amount, payment_value, refund_amount, products.price/cogs, web_traffic.avg_session_duration_sec, sessions/page_views. Giá trị âm/0 vô lý. Phân biệt outlier thật vs lỗi nhập. Ghi ds/qc08_dup_outlier.csv. Rồi ghi _status/qc08.done.

QC0.9 Cross-table reconciliation — chờ 3 marker:
  until [ -f EDA_Insight/phase0_qc/_status/qc04.done ] && [ -f EDA_Insight/phase0_qc/_status/qc06.done ] && [ -f EDA_Insight/phase0_qc/_status/qc08.done ]; do sleep 20; done
Đối chiếu: sales.Revenue/COGS vs aggregate GROSS từ order_items (kỳ vọng ~0,0000%); sales gross vs net loại cancelled+discount (kỳ vọng gap ~13,37%); COUNT(orders)==COUNT(payments) verify 1:1; orders-shipments=80.878 khớp cancelled/chưa ship?; SUM(payments.payment_value) vs SUM(order_items net); SUM(returns.refund_amount)<=payments; count reviews/returns vs orders hợp lý. Ghi ds/qc09_reconciliation.csv (cặp|giá trị A|giá trị B|%lệch|kết luận). Ghi _status/qc09.done.

KHÔNG sửa data. Mỗi %lệch ghi kết luận khớp/lệch-có-giải-thích/lệch-bất-thường. Xong → tóm tắt cho PM.
```

---

## 🪟 WINDOW 4 — Agent @tester (audit + gate)

```
Bạn là @tester (QA) team Datathon 2026. Repo: /Users/lhoanghai_/Documents/Study/Dự án datathon2026.
Đọc EDA_Insight/phase0_qc/qc_sprint_plan.md. Bạn sở hữu QC0.10 — GATE cuối, gom hết QC0.1–0.9.
Output: <repo>/EDA_Insight/phase0_qc/. python3.

Chờ tất cả marker:
  until [ -f EDA_Insight/phase0_qc/_status/qc01.done ] && [ -f EDA_Insight/phase0_qc/_status/qc02.done ] && [ -f EDA_Insight/phase0_qc/_status/qc03.done ] && [ -f EDA_Insight/phase0_qc/_status/qc04.done ] && [ -f EDA_Insight/phase0_qc/_status/qc05.done ] && [ -f EDA_Insight/phase0_qc/_status/qc06.done ] && [ -f EDA_Insight/phase0_qc/_status/qc07.done ] && [ -f EDA_Insight/phase0_qc/_status/qc08.done ] && [ -f EDA_Insight/phase0_qc/_status/qc09.done ]; do sleep 30; done

QC0.10 Data-quality log:
1. Đọc mọi artifact de/, da/, ds/. Gom thành data_quality_log.csv, cột: check_id | bảng | cột | dimension | mô tả | count | rate | severity(critical/high/med/low) | phân_loại(lỗi-data/hiện-tượng-nghiệp-vụ) | action(fix/document/accept) | owner.
2. Audit độc lập: tự chạy lại 3-5 finding severity cao nhất (KHÔNG tin số cũ), xác nhận khớp.
3. Viết data_quality_log.md — tóm tắt điều hành + GATE Phase 0: PASS / CONDITIONAL(kèm điều kiện) / FAIL.
Ghi 2 file vào EDA_Insight/phase0_qc/. Ghi _status/qc10.done. Báo GATE cho PM.
```

---

## Điều phối (PM)

- Khởi động Window 1 (@de) trước; Window 2/3/4 mở song song, tự chờ marker.
- Marker dir: `_status/` (tạo sẵn: `mkdir -p EDA_Insight/phase0_qc/_status`).
- Kiểm tiến độ bất kỳ lúc nào: `ls EDA_Insight/phase0_qc/_status/`.
- Gate cuối = `_status/qc10.done` + `data_quality_log.md`.
- Nhắc: Phase 0 QC cũ (commit 95ffbd1) — @de đọc trước, bổ sung phần thiếu, không làm lại thừa.
