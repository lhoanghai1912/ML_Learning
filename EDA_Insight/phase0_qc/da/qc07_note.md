# QC0.7 — Time coverage — note

Nguồn: `data/*.csv` (raw, không sửa). Script: `qc07_timecoverage.py`. Kết quả chi tiết: `qc07_timecoverage.csv`.

## 1. Bảng theo bảng

| Bảng | Cột ngày | Min | Max | Span | Missing | Ghi chú |
|---|---|---|---|---:|---:|---|
| sales | Date | 2012-07-04 | 2022-12-31 | 3.833d | **0** | Daily series đầy đủ, khớp 100% span (COUNT rows = COUNT days trong range) |
| orders | order_date | 2012-07-04 | 2022-12-31 | 3.833d | **0** | 646.945 đơn trải trên đúng 3.833 ngày distinct — **khớp tuyệt đối min/max/số-ngày-distinct với `sales`** → `sales` gần như chắc chắn là daily aggregate của `orders` |
| web_traffic | date | 2013-01-01 | 2022-12-31 | 3.652d | **0** | Daily series đầy đủ *trong phạm vi của nó* — không có ngày trống bên trong |
| inventory | snapshot_date | 2012-07-31 | 2022-12-31 | 126 tháng | **0** | Panel THÁNG (cuối tháng), không phải daily. 126 tháng liên tục Jul-2012→Dec-2022, không hụt tháng nào |
| promotions | start_date / end_date | 2013-01-31 / 2022-12-31 | 2022-11-18 / … | — | N/A | Chỉ 50 chương trình (event list), KHÔNG phải daily series → "missing days" vô nghĩa ở đây, xem mục 4 |
| reviews | review_date | 2012-07-10 | 2022-12-31 | 3.827d | 2 | 2 ngày không có review nào: `2012-07-11`, `2021-02-22` — số lượng nhỏ, nhiều khả năng là ngày thực sự **0 review phát sinh** (113.551 review / 3.833 ngày kinh doanh ≈ 30/ngày, xác suất 1 ngày = 0 là thấp nhưng không phải bằng chứng lỗi hệ thống rõ ràng vì chỉ 2/3.827 ngày ~0.05%) |
| returns | return_date | 2012-07-11 | 2022-12-31 | 3.826d | 20 | 20 ngày không có return nào (0.5% số ngày) — tương tự, return là sự kiện hiếm hơn (39.939 return / 3.833 ngày ≈ 10/ngày), rải rác nhiều năm khác nhau (2019, 2020×5, 2021, …) không tập trung 1 khối → nhiều khả năng là **biến động tự nhiên** (ngày ít đơn/ngày lễ), không phải lỗi ETL |
| shipments | ship_date | 2012-07-04 | 2022-12-29 | 3.831d | **0** | |
| shipments | delivery_date | 2012-07-06 | 2022-12-31 | 3.831d | **0** | |
| sample_submission | Date | 2023-01-01 | 2024-07-01 | 548d | **0** | Horizon forecast liên tục, không hụt ngày |

## 2. Giải thích lệch span `web_traffic` (3.652d) vs `sales` (3.833d) = 181 ngày

- `sales`/`orders`: bắt đầu **2012-07-04**.
- `web_traffic`: bắt đầu **2013-01-01**.
- Số ngày từ 2012-07-04 → 2012-12-31 (inclusive) = **181 ngày** — khớp CHÍNH XÁC với chênh lệch 3.833 − 3.652 = 181.
- Cả 2 bảng cùng kết thúc **2022-12-31**.

**Kết luận:** đây KHÔNG phải hiện tượng ngày bị rớt rải rác (đã xác nhận `missing_units=0` cho cả 2 bảng — bên trong phạm vi của mình mỗi bảng đều liền mạch). Đây là **một khối liên tục 181 ngày không có dữ liệu** ở đầu chuỗi `web_traffic` — hệ thống tracking web analytics (sessions/page_views/bounce_rate…) chỉ bắt đầu thu thập từ **2013-01-01**, trong khi doanh nghiệp đã bán hàng (có `orders`/`sales`) từ **2012-07-04**, tức **web_traffic tracking được triển khai TRỄ HƠN ~6 tháng so với ngày mở bán**. Đây là **giới hạn dữ liệu nguồn (data availability), không phải lỗi data quality** — không có gì để "fix", chỉ cần **document**: mọi model dùng `web_traffic` làm feature sẽ thiếu no-data cho 2012-07-04→2012-12-31, cần xử lý (loại bỏ giai đoạn đó khỏi training window có dùng web feature, hoặc impute có ghi chú rõ).

## 3. Xác nhận `sample_submission` KHÔNG chồng lịch sử

- Lịch sử (`sales`/`orders`) kết thúc: **2022-12-31**.
- Forecast horizon (`sample_submission`) bắt đầu: **2023-01-01**.
- 2023-01-01 = ngày kế tiếp ngay sau 2022-12-31 (gap = 0 ngày, không overlap, không hở).
- Horizon: 2023-01-01 → 2024-07-01, đúng **548 ngày** liên tục, không thiếu ngày nào (missing_units=0).

**Kết luận:** xác nhận **sample_submission KHÔNG chồng lấn dữ liệu lịch sử** — nối tiếp liền mạch (seamless hand-off), đúng thiết kế 1 bài toán forecast out-of-sample thuần túy. An toàn để dùng toàn bộ lịch sử 2012-07-04→2022-12-31 làm train, không rò rỉ (leakage) nhãn tương lai.

## 4. `promotions` — không phải daily series

`promotions` chỉ có 50 dòng = 50 chương trình khuyến mãi (mỗi dòng 1 campaign với `start_date`/`end_date` riêng), KHÔNG phải 1 dòng/ngày. Do đó khái niệm "missing days" của bảng này vô nghĩa (99% "ngày trống" chỉ vì hầu hết ngày trong 10 năm không nằm trong campaign nào — đúng bản chất, không phải lỗi). Điều đáng kiểm ở đây là:
- `start_date` range: 2013-01-31 → 2022-11-18 (50 distinct start dates).
- `end_date` range: 2013-03-01 → 2022-12-31 (50 distinct end dates).
- Cả 2 nằm gọn trong phạm vi `sales`/`orders` (2012-07-04→2022-12-31) → **không có campaign nào rơi ra ngoài lịch sử bán hàng** (hợp lý).
- Business-rule `end_date >= start_date` per-row → thuộc QC0.6, không lặp lại ở đây.

## 5. Alignment tổng thể giữa các bảng

| Cặp | Nhận xét |
|---|---|
| sales vs orders | Khớp tuyệt đối min/max/số ngày → `sales` = daily rollup của `orders` |
| web_traffic vs sales/orders | Lệch 181 ngày đầu (web_traffic bắt đầu trễ) — đã giải thích mục 2 |
| shipments (ship/delivery) vs orders | Min ship_date = min order_date (2012-07-04) hợp lý; max ship_date (2022-12-29) < max order_date (2022-12-31) — hợp lý vì đơn cuối kỳ chưa kịp ship (không phải gap dữ liệu, là độ trễ vận hành tự nhiên cuối chuỗi) |
| reviews/returns vs orders | Nằm trong phạm vi orders, có review/return sau ngày order cuối 1-2 hôm là hợp lý (độ trễ đánh giá/trả hàng) |
| inventory (monthly) vs sales (daily) | Cùng năm bắt đầu/kết thúc (2012-07 → 2022-12), granularity khác (tháng vs ngày) — cần resample khi join |
| sample_submission vs lịch sử | Không chồng lấn — xem mục 3 |

## Hạn chế phân tích
- "Missing days" ở đây tính theo **calendar day có mặt ít nhất 1 dòng dữ liệu** (union theo ngày), KHÔNG kiểm tra volume/completeness NỘI DUNG trong ngày đó (vd 1 đơn hàng duy nhất trong ngày vẫn tính là "có dữ liệu ngày đó") — kiểm tra volume bất thường theo ngày thuộc QC0.8 (outlier, @ds).
- 2 ngày reviews=0 và 20 ngày returns=0 chưa được đối chiếu với ngày lễ/Tết hay biến cố cụ thể (vd Tet effect đã có trong `phase1_descriptive/tet_effect.ipynb`) — có thể liên hệ chéo nếu cần điều tra sâu hơn, nhưng không nằm trong scope QC0.7.
