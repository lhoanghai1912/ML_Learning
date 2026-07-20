# Phase 0 — Báo cáo QC toàn diện Data Quality & Schema (Vin Datathon 2026)

- **Ngày chạy:** 2026-07-20 · Python 3.9.6 · pandas 2.3.3 (venv dự án)
- **Script tái lập:** `EDA_Insight/phase0_qc/phase0_full_qc.py` — chạy bằng `.venv/bin/python`, ~3.5s, exit 0, **chỉ đọc** `data/`
- **Phạm vi:** 14 bảng CSV + đối chiếu `tài liệu/data_dictionary.xlsx`
- **Kỳ vọng thời gian:** lịch sử 2012-07-04 → 2022-12-31; forecast 2023-01-01 → 2024-07-01 (548 ngày)

---

## 1. BẢNG TỔNG HỢP VẤN ĐỀ THEO MỨC NGHIÊM TRỌNG

**Tổng: 18 vấn đề — 0 BLOCKER, 10 WARNING, 8 INFO.** Không có vấn đề nào chặn tiến độ; dữ liệu đủ sạch để vào EDA/model ngay, nhưng 10 WARNING dưới đây phải được xử lý CÓ CHỦ ĐÍCH (đặc biệt W1, W2 — ảnh hưởng trực tiếp cả Phần A lẫn Phần B).

| # | Mức | Bảng | Vấn đề (số liệu cụ thể) | Ảnh hưởng | Khuyến nghị |
|---|-----|------|------------------------|-----------|-------------|
| W1 | **WARNING** | sales ↔ order_items | **Định nghĩa target:** `sales.Revenue` = **GROSS** (`qty × unit_price`) của **TẤT CẢ đơn, kể cả cancelled**, KHÔNG trừ discount/refund (MAPE tái dựng **0.000%**). `sales.COGS` = `qty × cogs` catalog cùng mask (MAPE **0.000%**). Net-bỏ-cancelled thấp hơn target 13.4–23.8% | A + B | Phần B forecast đúng định nghĩa gross. Phần A phải ghi rõ dashboard dùng gross demand hay net revenue — thống nhất toàn team để không chênh số |
| W2 | **WARNING** | order_items | **133,052/714,669 dòng hàng (18.62%) bán dưới giá vốn** (`unit_price < cogs` catalog) — nguồn gốc trực tiếp của 382 ngày lỗ gộp | A + B | Không "sửa" dữ liệu; forecast COGS **độc lập** với Revenue; dashboard margin phân tách theo mùa sale |
| W3 | **WARNING** | sales | **382/3,833 ngày (9.97%) có COGS > Revenue** (lỗ gộp). Theo tháng (cộng 11 năm): T8=155, T12=122, T11=55, T7=33; theo năm nhiều nhất: 2021=74, 2015=55, 2022=51 | A + B | Không áp ràng buộc COGS < Revenue khi forecast; chú thích trong dashboard margin |
| W4 | **WARNING** | web_traffic | **Grain thực tế = 1 dòng/ngày toàn site** (min=max=1 dòng/ngày), TRÁI với dictionary ("date + traffic_source"). `traffic_source` chỉ là nhãn của ngày (organic_search 1090 ngày, paid_search 784…) | A (marketing) | KHÔNG sum sessions theo traffic_source như phân rã đầy đủ; phân tích kênh dùng `orders.order_source` |
| W5 | **WARNING** | web_traffic | Chỉ có từ **2013-01-01** — thiếu **181 ngày đầu** (2012-07-04 → 2012-12-31) so với sales/orders | B (feature) | Model dùng traffic phải mask/bỏ giai đoạn 2012 khi train |
| W6 | **WARNING** | inventory | **Panel không cân:** chỉ 1,624/2,412 SP xuất hiện; mỗi SP trung bình ~37/126 tháng (min=1, median=27, max=126); 60,247 dòng vs 204,624 nếu đủ | A (vận hành) | Không suy diễn "tồn = 0" cho tháng vắng mặt; không dùng làm feature forecast bắt buộc |
| W7 | **WARNING** | order_items | 16 dòng trùng cặp `(order_id, product_id)` nhưng **không phải bản ghi lặp** — là 2 line item hợp lệ (khác unit_price/quantity, 0% cặp cùng giá). Grain thật = "dòng hàng" | A + B | **KHÔNG xóa** (xóa sẽ lệch đối chiếu sales.csv 0.000%). Join returns/reviews theo cặp phải aggregate order_items trước, tránh fan-out |
| W8 | **WARNING** | customers | **238 khách có signup_date trước 2012-07-04** (sớm nhất 2012-01-17), trước cả ngày mở bán | A (cohort) | Gộp vào cohort 2012-H2 hoặc loại — quyết định thống nhất trước khi chạy cohort |
| W9 | **WARNING** | returns | 1 dòng `return_quantity` > quantity đã mua; 1 dòng `refund_amount` > gross dòng hàng | A (nhỏ) | Cắt trần theo dòng hàng gốc khi tính net-sau-trả-hàng |
| W10 | **WARNING** | promotions | `applicable_category` thiếu 40/50 (80%) — theo dictionary nghĩa là "áp dụng mọi category" | A (marketing) | Impute nhãn `all_categories` thay vì để NaN |
| I1 | INFO | payments | `payment_value` = net (`qty×price − discount`) khớp **100.00%** đơn (median chênh 0.00), **kể cả đơn cancelled/created cũng có payment** | A | Không coi là tiền thực thu; phân tích dòng tiền phải lọc `order_status` |
| I2 | INFO | sample_submission | File mẫu **đã có sẵn giá trị** Revenue/COGS (placeholder, vd 2023-01-01 = 2,665,507.2) | B | Bài nộp phải **ghi đè toàn bộ** 2 cột; giữ format Date `YYYY-MM-DD` |
| I3 | INFO | shipments | `shipping_fee` 0–32 (median 1.73) — quá nhỏ so với giá trị đơn (nghìn–trăm nghìn) → khác đơn vị tiền tệ | A | Không cộng vào doanh thu; chỉ so sánh tương đối |
| I4 | INFO | shipments | 564 đơn delivered/returned/shipped (524/29/11) **không có bản ghi shipment** (~0.1%) | A | Chấp nhận sai lệch nhỏ khi phân tích fulfillment |
| I5 | INFO | products / customers | 814/2,412 SP chưa từng bán; 31,684/121,930 khách chưa từng đặt đơn | A | Chú ý mẫu số khi tính conversion/coverage |
| I6 | INFO | products | 240 `product_name` trùng giữa các SKU khác nhau | A | Luôn dùng `product_id` làm khóa |
| I7 | INFO | sales, sample_submission | Naming PascalCase (`Date/Revenue/COGS`) vs snake_case các bảng khác | Pipeline | Chuẩn hoá ở lớp staging; giữ nguyên khi nộp |
| I8 | INFO | web_traffic | `bounce_rate` 0.0032–0.0058 — phi thực tế (mô phỏng) | A | Chỉ dùng biến động tương đối |

> **Không có BLOCKER.** Các mục từng nghi ngờ là blocker đều đã kiểm chứng đạt: sales đủ 3,833 ngày liên tục không gãy; sample_submission đúng khung; referential integrity 15/15 quan hệ = 0 bản ghi mồ côi.

---

## 2. SCHEMA vs DATA DICTIONARY (từng bảng)

**Kết luận: 14/14 bảng khớp 100% tên cột, thứ tự cột, kiểu dữ liệu và số dòng với data_dictionary.xlsx. Không có cột lệch tên/lệch kiểu.**

| Bảng | Số dòng (thực tế = dictionary) | PK | Khớp cột/kiểu | Ghi chú |
|------|-------------------------------:|----|:---:|---------|
| customers | 121,930 | customer_id | ✔ | id không liên tục (max 157,563 > số dòng) — bình thường |
| geography | 39,948 | zip | ✔ | zip là mã định danh, không tính toán số học |
| products | 2,412 | product_id | ✔ | 0 SKU có cogs > price ở catalog |
| promotions | 50 | promo_id | ✔ | `applicable_category` null 80% (chủ đích) |
| orders | 646,945 | order_id | ✔ | status: delivered 516,716 / cancelled 59,462 / returned 36,142 / shipped 13,773 / paid 13,577 / created 7,275 |
| order_items | 714,669 | dòng hàng (không phải order_id+product_id thuần) | ✔ | promo_id null 61.34%, promo_id_2 null 99.97% (chủ đích) |
| payments | 646,945 | order_id | ✔ | 1-1 với orders |
| shipments | 566,067 | order_id | ✔ | thiếu 80,878 đơn (chủ yếu cancelled/paid/created — hợp lý) |
| returns | 39,939 | return_id | ✔ | 100% khớp dòng hàng gốc theo (order_id, product_id) |
| reviews | 113,551 | review_id | ✔ | 0 trùng (order_id, product_id); customer luôn = người đặt đơn |
| inventory | 60,247 | snapshot_date + product_id | ✔ | snapshot luôn cuối tháng; đủ 126/126 tháng |
| web_traffic | 3,652 | **date** (không phải date+source như dictionary — xem W4) | ✔ cột/kiểu | duy nhất 1 điểm dictionary SAI về grain |
| sales | 3,833 | Date | ✔ | |
| sample_submission | 548 | Date | ✔ | |

## 3. MISSING / DUPLICATES / GIÁ TRỊ BẤT THƯỜNG

- **Missing:** chỉ 3 cột có null, tất cả đều "null có nghĩa": `order_items.promo_id` 438,353 (61.34%), `order_items.promo_id_2` 714,463 (99.97%), `promotions.applicable_category` 40 (80%). **11/14 bảng không thiếu bất kỳ giá trị nào.**
- **Duplicates:** 0 trùng PK ở mọi bảng, 0 trùng cả dòng — ngoại lệ duy nhất: 16 dòng order_items trùng cặp (order_id, product_id) nhưng là line item hợp lệ (W7).
- **Giá trị âm/bất thường:** 0 giá trị âm ở toàn bộ cột tiền/số lượng (price, cogs, unit_price, discount, payment_value, shipping_fee, refund, quantity, stock...). 0 dòng discount > gross. 0 rating ngoài [1..5]. 0 `ship_date < order_date`, 0 `delivery_date < ship_date` (lead time 2–7 ngày, median 4), 0 `return_date/review_date < order_date`. Chỉ 2 dòng returns bất thường (W9).
- **Logic nghiệp vụ:** `unit_price`/giá catalog dao động 0.462–1.104 (median 0.982) → có dynamic pricing giảm tới ~54%; 18.62% dòng bán dưới giá vốn (W2).

## 4. KHOẢNG THỜI GIAN vs KỲ VỌNG 2012-07-04 → 2022-12-31

| Bảng.cột | Min → Max | Ngày distinct | Gãy chuỗi? |
|----------|-----------|--------------:|-----------|
| sales.Date | 2012-07-04 → 2022-12-31 | 3,833 | **0 ngày thiếu — chuỗi target hoàn hảo** |
| orders.order_date | 2012-07-04 → 2022-12-31 | 3,833 | 0 ngày thiếu |
| web_traffic.date | **2013-01-01** → 2022-12-31 | 3,652 | 0 ngày thiếu trong khoảng, nhưng **thiếu 181 ngày đầu** (W5) |
| customers.signup_date | **2012-01-17** → 2022-12-31 | 3,941 | 238 khách signup trước mở bán (W8) |
| shipments.ship_date | 2012-07-04 → 2022-12-29 | 3,831 | hợp lý (đuôi lệch do lead time) |
| shipments.delivery_date | 2012-07-06 → 2022-12-31 | 3,831 | hợp lý |
| returns.return_date | 2012-07-11 → 2022-12-31 | 3,806 | hợp lý (trễ sau mua) |
| reviews.review_date | 2012-07-10 → 2022-12-31 | 3,825 | hợp lý |
| inventory.snapshot_date | 2012-07-31 → 2022-12-31 | 126 tháng | **đủ 126/126 tháng cuối tháng** |
| promotions.start/end | 2013-01-31 → 2022-12-31 | 50 | không có promo năm 2012 |
| Khoảng cách sales cuối → submission đầu | 2022-12-31 → 2023-01-01 | 1 ngày | liền mạch, không gãy |

## 5. REFERENTIAL INTEGRITY — 15/15 quan hệ SẠCH (0 bản ghi mồ côi)

```
order_items.order_id   → orders     : 0/714,669   payments.order_id  → orders   : 0/646,945
order_items.product_id → products   : 0/714,669   shipments.order_id → orders   : 0/566,067
orders.customer_id     → customers  : 0/646,945   returns.order_id   → orders   : 0/39,939
orders.zip             → geography  : 0/646,945   returns.product_id → products : 0/39,939
customers.zip          → geography  : 0/121,930   reviews.order_id/product_id/customer_id : 0/113,551
inventory.product_id   → products   : 0/60,247    order_items.promo_id / promo_id_2 → promotions : 0/276,316 và 0/206
```

Coverage (không phải lỗi): 0 đơn thiếu payment, 0 đơn thiếu order_items; 80,878 đơn không có shipment (đúng logic status, trừ 564 đơn — I4).

## 6. ĐỐI CHIẾU SALES ↔ ORDER_ITEMS ↔ PAYMENTS (phát hiện quan trọng nhất)

| Định nghĩa Revenue thử nghiệm | MAPE theo ngày | Lệch tổng 11 năm |
|-------------------------------|---------------:|-----------------:|
| **Tất cả đơn, GROSS = qty × unit_price** | **0.000%** | **+0.000%** |
| Tất cả đơn, net (− discount) | 5.168% | −4.562% |
| Bỏ cancelled, net | 13.903% | −13.369% |
| Bỏ cancelled + returned, net | 19.150% | −18.640% |
| Chỉ delivered, net | 24.500% | −23.811% |
| delivered + returned + shipped, net | 17.149% | −16.488% |

- **`sales.Revenue` ≡ gross demand toàn bộ đơn (kể cả cancelled), `sales.COGS` ≡ qty × cogs catalog — cả hai khớp 0.000%.** → Có thể decompose target theo category/region/product từ order_items một cách tuyệt đối tin cậy, và mọi phân tích driver cho forecast phải theo định nghĩa gross này.
- `payment_value` = net từng đơn chính xác 100% (kể cả đơn cancelled) → payments là bảng dẫn xuất, không phải cash thực thu.

## 7. SAMPLE_SUBMISSION — HỢP LỆ

- Cột `[Date, Revenue, COGS]`, kiểu `datetime / float64 / float64` — đúng format.
- **Đúng 548 dòng**, 2023-01-01 → 2024-07-01, **0 ngày thiếu, 0 trùng, 0 NaN** — liền mạch với ngày cuối của sales (2022-12-31).
- Lưu ý I2: file mẫu đã chứa giá trị placeholder — phải ghi đè toàn bộ khi nộp.

---

## 8. KHUYẾN NGHỊ CHO GIAI ĐOẠN 1–3

### Giai đoạn 1 — EDA descriptive
1. **Chốt "từ điển metric" trước khi vẽ bất kỳ chart nào** (hệ quả W1): định nghĩa song song `gross_revenue` (khớp sales.csv, dùng cho forecast) và `net_revenue` (qty×price − discount, bỏ cancelled, dùng cho business view). Mọi notebook/chart ghi rõ đang dùng metric nào.
2. Xây 1 lớp staging chung (script/notebook load duy nhất): chuẩn hoá tên cột PascalCase → snake_case (I7), parse ngày, impute `applicable_category='all_categories'` (W10), KHÔNG xóa 16 line item trùng cặp (W7).
3. Phân rã revenue theo category/region/tháng từ order_items — an toàn vì khớp target 0.000%.
4. Mùa vụ: kiểm chứng đỉnh sale T7-T8 và T11-T12 (nơi tập trung 365/382 ngày lỗ gộp) — đây là "câu chuyện" chính của descriptive.

### Giai đoạn 2 — EDA diagnostic
5. Lỗ gộp (W2, W3): chứng minh cơ chế `unit_price giảm sâu < cogs` trong mùa sale bằng phân phối ratio unit_price/price theo tháng; đối chiếu với promotions đang chạy (đủ FK sạch để join promo_id).
6. Marketing theo kênh: dùng `orders.order_source` + `customers.acquisition_channel`; **không** dùng `web_traffic.traffic_source` làm phân rã kênh (W4). web_traffic chỉ dùng làm chỉ số tổng lưu lượng ngày từ 2013.
7. Returns/cancelled: tỷ lệ cancelled 9.2%, returned 5.6% — phân tích theo lý do/size (returns join sạch 100% về dòng hàng gốc).

### Giai đoạn 3 — Dashboard RFM / cohort / demographics
8. RFM: tính trên đơn **không-cancelled** với net value; dùng customer_id từ orders (reviews đã xác nhận nhất quán 100%). Mẫu số: 90,246 khách từng mua / 121,930 tổng CRM (I5).
9. Cohort: cohort theo `signup_date` (chuẩn CRM) — quyết định trước cách xử lý 238 khách signup trước 2012-07-04 (W8: khuyến nghị gộp vào cohort 2012-H2); có thể so sánh với cohort theo first_order_date.
10. Demographics: gender/age_group/region đầy đủ 0 null, join geography sạch 100% — dùng thoải mái; zip xử lý như mã định danh.

### Cho model forecast (Phần B)
11. Target = `sales.csv` nguyên trạng (3,833 ngày liên tục, 0 thiếu). Forecast Revenue và COGS như 2 chuỗi liên quan nhưng **không ràng buộc COGS < Revenue** (W3).
12. Feature ngoài (traffic, promo) phải xử lý cửa sổ thiếu: traffic từ 2013 (W5), promo từ 2013; horizon 548 ngày không có promo tương lai → dùng lịch mùa vụ (Tết, T7-T8, T11-T12) thay vì biến promo trực tiếp.
13. Nộp bài: ghi đè đủ 548 dòng đúng thứ tự Date của sample_submission, giữ nguyên header `Date,Revenue,COGS` (I2).

---
*Tái lập toàn bộ số liệu: `cd "EDA_Insight/phase0_qc" && "../../.venv/bin/python" phase0_full_qc.py` (fallback `python3` nếu venv lỗi — chỉ cần pandas).*
