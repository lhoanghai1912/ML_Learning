# Data Dictionary — `data/raw/`

> Nguồn sự thật cho 14 bảng raw + `sample_submission.csv`. Cột/dtype dưới đây đọc **trực tiếp từ
> CSV thật** trên đĩa (`data/raw/*.csv`, cùng path `src/datathon/config.RAW_TABLES` trỏ tới) —
> không lấy từ trí nhớ, không bịa. Cách verify: xem mục "Verify" cuối file.
>
> Bổ sung ngữ cảnh nghiệp vụ (gross/net, grain thật, cảnh báo DQ) tham chiếu từ tài liệu đã có sẵn
> trong repo — `README.md` (root) và `docs/analysis/DATA_LINEAGE.md` +
> `docs/analysis/phase0_qc/phase0_qc_report.md` (QC toàn diện, chạy 2026-07-20, đối chiếu gốc với
> `docs/brief/data_dictionary.xlsx` + `docs/brief/Đề bài1.docx`). File `.xlsx`/`.docx` là binary,
> không đọc trực tiếp được trong session này (không có tool giải nén/parse Office) — nếu cần đối
> chiếu lại từng cột với dictionary gốc, mở thủ công 2 file đó.

## 0. Cách lấy data raw (BẮT BUỘC đọc — clone mới KHÔNG có data)

Từ milestone M1 (`ee63d2b`), `data/raw/*.csv` đã `git rm --cached` — file **còn trên đĩa máy cũ**
nhưng **không còn trong git**. Clone repo mới ở máy khác sẽ có thư mục `data/raw/` rỗng (chỉ có
`.gitkeep`).

- **Nguồn tải chính thức (PO cấp 2026-08-07):**
  <https://drive.google.com/drive/folders/1nLtCvUsczAQ9QB-hbBDh5_w6v-joRBaX>

  > ⚠ **Folder KHÔNG public — cần được cấp quyền truy cập trước.** Đã probe bằng
  > `curl -sL` (2026-08-07): HTTP 200 nhưng nội dung trả về là trang
  > `<title>Google Drive: Sign-in</title>` → Drive đang ở chế độ hạn chế, người ngoài mở link sẽ
  > thấy "Request access". Muốn clone-and-run được thì PO phải đổi share thành
  > *"Anyone with the link → Viewer"*, hoặc add email từng người vào folder.
  >
  > ⚠ **Nội dung folder CHƯA verify được từ repo** — session không có quyền truy cập nên **chưa**
  > xác nhận folder chứa đủ 14 CSV, chưa đối chiếu checksum với bản đang có trên đĩa
  > (`data/raw/`, 126MB, 14 file). Ai tải về lần đầu: chạy mục "Verify" bên dưới trước khi tin số.
  >
  > Ghi chú link: link PO gửi có tiền tố `/u/2/` (chỉ số tài khoản Google của PO, không dùng được
  > cho người khác) — đã chuẩn hoá bỏ `/u/2/` khi ghi vào đây.
- Sau khi có nguồn: tải đủ **14 file CSV**, đặt đúng tên vào `data/raw/` (tên phải khớp
  `src/datathon/config.RAW_TABLES`, không đổi tên):
  `customers.csv, geography.csv, inventory.csv, order_items.csv, orders.csv, payments.csv,
  products.csv, promotions.csv, returns.csv, reviews.csv, sales.csv, sample_submission.csv,
  shipments.csv, web_traffic.csv`.
- Có thể override thư mục bằng env `DATA_RAW_PATH` (xem `src/datathon/config.py`) nếu không muốn
  đặt ở `data/raw/` mặc định.
- Verify sau khi đặt file: `python3 -c "import sys; sys.path.insert(0,'src'); from datathon.config import RAW_TABLES; import pandas as pd; print(pd.read_csv(RAW_TABLES['sales']).shape)"` → kỳ vọng `(3833, 3)`.
- `data/sample/` — **ĐÃ CÓ** (M5, commit `fe4b455`): 14 CSV, tổng **640K**, commit vào git, dùng cho
  CI/pytest. Sinh lại bằng `make sample`. Không nhầm với `data/raw/` (full data 126MB, gitignored,
  không commit). **Hệ quả:** clone sạch **không có** `data/raw/` vẫn chạy được `make test`
  (pytest trên sample), nhưng **không** chạy được `make forecast` (cần full raw từ Drive ở trên).

## 1. Tổng quan phạm vi

- **14 bảng raw** (+ `sample_submission.csv` tính chung vào 14 theo `RAW_TABLES`, đúng scope M1/M7).
- **Lịch sử (Phần A + target Phần B):** `2012-07-04 → 2022-12-31` — xác nhận thật từ `sales.csv`
  (dòng đầu `2012-07-04`, dòng cuối `2022-12-31`, 3,833 dòng = 1 dòng/ngày, không thiếu ngày).
- **`web_traffic.csv` bắt đầu muộn hơn:** `2013-01-01 → 2022-12-31` (3,652 dòng) — **thiếu 181 ngày
  đầu** (2012-07-04 → 2012-12-31) so với sales/orders. Không dùng traffic làm feature bắt buộc cho
  giai đoạn 2012.
- **`sample_submission.csv` = template Phần B:** `2023-01-01 → 2024-07-01`, **548 dòng** (đúng số
  ngày cần forecast). File đã có sẵn giá trị `Revenue`/`COGS` — đây là **placeholder**, bài nộp
  phải **ghi đè toàn bộ** 2 cột, giữ nguyên format `Date` (`YYYY-MM-DD`).

## 2. Business fact bắt buộc đọc trước khi phân tích/model

- **`sales.csv` (`Revenue`, `COGS`) = GROSS** — tính trên **tất cả đơn kể cả `cancelled`**, KHÔNG
  trừ `discount_amount`/`refund_amount`. Đây là số **target chính thức Phần B** (đề bài dựa trên
  `sales.csv`, đối chiếu nộp bài dùng số này). Rebuild từ `order_items × orders × products`
  (`quantity × unit_price` giữ nguyên cancelled) khớp `sales.csv` với **MAPE 0.000%**.
- **`net_revenue`** (loại đơn `cancelled`, trừ `discount_amount`) **KHÔNG có sẵn thành cột trong CSV
  raw nào** — là số **tính lại** từ `order_items`/`orders`, chỉ dùng cho phân tích góc nhìn kinh
  doanh **Phần A** (RFM Monetary tham khảo, waterfall margin, dashboard). **Không** dùng để đối
  chiếu forecast Phần B. Gap gross vs net ~13–24% tùy giai đoạn.
- **`payments.payment_value`** = tiền thực thu theo đơn (`qty×price − discount`, khớp 100% công
  thức, kể cả đơn `cancelled` vẫn có payment ghi nhận — không suy diễn là dòng tiền thật, phải lọc
  `order_status` trước khi dùng). Đây là cột dùng làm **Monetary trong RFM** (Phần A).
- **COGS có thể > Revenue theo ngày** (382/3,833 ngày = 9.97%, "lỗ gộp") — do bán dưới giá vốn khi
  chạy promo (18.62% dòng `order_items`). Đây **không phải lỗi dữ liệu** — không áp ràng buộc
  `COGS < Revenue` khi forecast.

## 3. Sơ đồ quan hệ (FK) tổng quát

```
customers (PK customer_id) ──┐
geography (PK zip)     ──────┼──< orders (PK order_id, FK customer_id, FK zip)
                              │        │
products (PK product_id) ────┤        ├──1:1── payments (FK order_id)
promotions (PK promo_id) ────┤        ├──0:1── shipments (FK order_id)
                              │        ├──<   order_items (FK order_id, FK product_id, FK promo_id/promo_id_2 nullable)
                              │        ├──<   returns (FK order_id, FK product_id)
                              │        └──<   reviews (FK order_id, FK product_id, FK customer_id)
                              │
                              └──< inventory (FK product_id, grain product_id × snapshot_date)

sales (grain Date)            — bảng tổng hợp độc lập, KHÔNG có FK — rebuild khớp
                                 order_items×orders×products (gross), MAPE 0.000%
web_traffic (grain date)      — bảng tổng hợp độc lập, KHÔNG có FK, không join được xuống order-level
sample_submission (grain Date)— template output Phần B, không phải bảng nghiệp vụ
```

Ký hiệu: `──<` = 1-N (1 dòng cha, nhiều dòng con), `──1:1` = 1-1 cùng grain, `──0:1` = 0 hoặc 1 (không
phải order nào cũng có).

## 4. Chi tiết từng bảng (14 bảng, cột/dtype đọc thật từ CSV)

### 4.1 `customers.csv` — 121,930 dòng, grain 1 dòng/khách

| Cột | Dtype quan sát | Ý nghĩa / ghi chú |
|---|---|---|
| `customer_id` | int64 | **PK** |
| `zip` | int64 | FK → `geography.zip` |
| `city` | object (string) | denormalized, trùng `geography.city` theo zip |
| `signup_date` | date (`YYYY-MM-DD`) | dùng cohort; **238 khách có `signup_date` < 2012-07-04** (sớm nhất 2012-01-17), trước cả ngày mở bán — cần quyết định gộp cohort 2012-H2 hay loại trước khi phân tích cohort |
| `gender` | object (enum) | `Female/Male/Non-binary` quan sát được |
| `age_group` | object (enum) | dạng bucket (`18-24`, `25-34`, `35-44`, `45-54`, ...) |
| `acquisition_channel` | object (enum) | `social_media/email_campaign/organic_search/referral/paid_search/direct` quan sát được |

### 4.2 `geography.csv` — 39,948 dòng, grain 1 dòng/zip

| Cột | Dtype quan sát | Ý nghĩa / ghi chú |
|---|---|---|
| `zip` | int64 | **PK** |
| `city` | object (string) | |
| `region` | object (enum) | chỉ 3 giá trị: `East/Central/West` (verify: 39,948/39,948 dòng khớp 1 trong 3, không lệch) |
| `district` | object (string) | dạng `District #N` |

### 4.3 `inventory.csv` — 60,247 dòng, grain 1 dòng/(`product_id` × `snapshot_date`, tháng)

| Cột | Dtype quan sát | Ý nghĩa / ghi chú |
|---|---|---|
| `snapshot_date` | date | cuối tháng (`YYYY-MM-30/31`) |
| `product_id` | int64 | FK → `products.product_id` |
| `stock_on_hand` | int64 | |
| `units_received` | int64 | |
| `units_sold` | int64 | |
| `stockout_days` | int64 | |
| `days_of_supply` | float64 | |
| `fill_rate` | float64 | tỷ lệ 0–1 |
| `stockout_flag` | int64 (0/1 bool) | |
| `overstock_flag` | int64 (0/1 bool) | |
| `reorder_flag` | int64 (0/1 bool) | |
| `sell_through_rate` | float64 | tỷ lệ 0–1 |
| `product_name` | object (string) | denormalized từ `products` |
| `category` | object (string) | denormalized từ `products` |
| `segment` | object (string) | denormalized từ `products` |
| `year` | int64 | derived từ `snapshot_date` |
| `month` | int64 | derived từ `snapshot_date` |

⚠ **Panel không cân**: chỉ 1,624/2,412 SP xuất hiện; mỗi SP trung bình ~37/126 tháng (min=1,
median=27, max=126) — **không suy diễn "tồn = 0"** cho tháng SP vắng mặt; không bắt buộc dùng làm
feature forecast.

### 4.4 `order_items.csv` — 714,669 dòng, grain 1 dòng/line item trong đơn

| Cột | Dtype quan sát | Ý nghĩa / ghi chú |
|---|---|---|
| `order_id` | int64 | FK → `orders.order_id` (N dòng/1 đơn) |
| `product_id` | int64 | FK → `products.product_id` |
| `quantity` | int64 | |
| `unit_price` | float64 | giá bán thật dòng này (có dynamic pricing, dao động ~0.46–1.10× giá catalog `products.price`) |
| `discount_amount` | float64 | |
| `promo_id` | object (string, nullable) | FK → `promotions.promo_id`; **null 61.34%** (438,353 dòng) — null có nghĩa "không áp promo", không phải thiếu dữ liệu |
| `promo_id_2` | object (string, nullable) | FK → `promotions.promo_id`; **null 99.97%** (714,463 dòng) — promo thứ 2 hiếm khi áp dụng |

⚠ **Không phải natural key `(order_id, product_id)` duy nhất** — 16 dòng trùng cặp này nhưng là 2
line item hợp lệ (khác `unit_price`/`quantity`, 0% cặp cùng giá). **Grain thật = "dòng hàng"**
(cần surrogate row id nếu cần key ổn định, ví dụ dùng ở dbt incremental `unique_key`). **KHÔNG xóa**
dòng trùng cặp — xóa sẽ lệch đối chiếu `sales.csv` (hiện khớp 0.000% MAPE). Join `returns`/`reviews`
theo `(order_id, product_id)` phải aggregate `order_items` trước để tránh fan-out.
**18.62% dòng (133,052/714,669) có `unit_price < cogs` catalog** — bán dưới giá vốn (nguồn gốc 382
ngày lỗ gộp ở `sales.csv`), không phải lỗi dữ liệu.

### 4.5 `orders.csv` — 646,945 dòng, grain 1 dòng/đơn

| Cột | Dtype quan sát | Ý nghĩa / ghi chú |
|---|---|---|
| `order_id` | int64 | **PK** |
| `order_date` | date | 2012-07-04 → 2022-12-31 |
| `customer_id` | int64 | FK → `customers.customer_id` |
| `zip` | int64 | FK → `geography.zip` |
| `order_status` | object (enum) | quan sát được: `delivered/returned/cancelled/shipped` (không xác nhận đủ 100% enum, tham khảo `docs/brief/data_dictionary.xlsx` nếu cần đầy đủ) — trục lọc cancelled/non-cancelled dùng khắp mọi phân tích |
| `payment_method` | object (enum) | `credit_card/cod/paypal` quan sát được |
| `device_type` | object (enum) | `desktop/mobile/tablet` quan sát được |
| `order_source` | object (enum) | `paid_search/direct/referral/organic_search/email_campaign` quan sát được — dùng cho phân tích kênh marketing (không dùng `web_traffic.traffic_source`, xem 4.14) |

### 4.6 `payments.csv` — 646,945 dòng, grain 1 dòng/đơn (1:1 với `orders`, cùng số dòng)

| Cột | Dtype quan sát | Ý nghĩa / ghi chú |
|---|---|---|
| `order_id` | int64 | FK → `orders.order_id`, 1:1 |
| `payment_method` | object (enum) | trùng lặp thông tin với `orders.payment_method` |
| `payment_value` | float64 | = **Monetary cho RFM** (Phần A). Khớp 100% công thức `qty×price − discount`. Có payment kể cả đơn `cancelled` — phải lọc `order_status` trước khi coi là dòng tiền thực thu |
| `installments` | int64 | số kỳ trả góp |

### 4.7 `products.csv` — 2,412 dòng, grain 1 dòng/SKU

| Cột | Dtype quan sát | Ý nghĩa / ghi chú |
|---|---|---|
| `product_id` | int64 | **PK** |
| `product_name` | object (string) | |
| `category` | object (string) | vd `Streetwear` |
| `segment` | object (string) | vd `Everyday` |
| `size` | object (enum) | `S/M/L/XL` quan sát được |
| `color` | object (string) | |
| `price` | float64 | giá catalog (không phải giá bán thật — xem `order_items.unit_price`) |
| `cogs` | float64 | giá vốn catalog, dùng đối chiếu `unit_price < cogs` |

Ghi chú: 814/2,412 SP chưa từng xuất hiện trong `order_items` (chưa từng bán) — chú ý mẫu số khi
tính coverage/conversion theo sản phẩm.

### 4.8 `promotions.csv` — 50 dòng, grain 1 dòng/chương trình khuyến mãi

| Cột | Dtype quan sát | Ý nghĩa / ghi chú |
|---|---|---|
| `promo_id` | object (string) | **PK**, format `PROMO-00NN` (0001–0050 quan sát được) |
| `promo_name` | object (string) | |
| `promo_type` | object (enum) | `percentage/fixed` quan sát được |
| `discount_value` | float64 | |
| `start_date` | date | |
| `end_date` | date | |
| `applicable_category` | object (string, nullable) | **null 80% (40/50 dòng)** — theo dictionary gốc nghĩa là "áp dụng mọi category" (nên impute nhãn `all_categories` thay vì để trống khi phân tích, KHÔNG tự sửa file raw) |
| `promo_channel` | object (enum) | `email/online/in_store/all_channels` quan sát được |
| `stackable_flag` | int64 (0/1 bool) | |
| `min_order_value` | float64 | 0 nghĩa là không ràng buộc đơn tối thiểu |

### 4.9 `returns.csv` — 39,939 dòng, grain 1 dòng/lượt trả hàng

| Cột | Dtype quan sát | Ý nghĩa / ghi chú |
|---|---|---|
| `return_id` | object (string) | **PK**, format `RET-0NNNNN` |
| `order_id` | int64 | FK → `orders.order_id` |
| `product_id` | int64 | FK → `products.product_id` |
| `return_date` | date | |
| `return_reason` | object (enum) | `late_delivery/wrong_size/defective/...` quan sát được |
| `return_quantity` | int64 | |
| `refund_amount` | float64 | |

Ghi chú DQ: 1 dòng `return_quantity` > số lượng đã mua thật; 1 dòng `refund_amount` > gross dòng
hàng gốc — cắt trần theo dòng hàng gốc khi tính net-sau-trả-hàng, không dùng thẳng nếu cần số chính
xác tuyệt đối.

### 4.10 `reviews.csv` — 113,551 dòng, grain 1 dòng/lượt đánh giá

| Cột | Dtype quan sát | Ý nghĩa / ghi chú |
|---|---|---|
| `review_id` | object (string) | **PK**, format `REV-000NNNN` |
| `order_id` | int64 | FK → `orders.order_id` |
| `product_id` | int64 | FK → `products.product_id` |
| `customer_id` | int64 | FK → `customers.customer_id` |
| `review_date` | date | |
| `rating` | int64 | 1–5 |
| `review_title` | object (string) | text ngắn, vd "Highly recommend" |

### 4.11 `sales.csv` — 3,833 dòng, grain 1 dòng/ngày (`2012-07-04 → 2022-12-31`)

| Cột | Dtype quan sát | Ý nghĩa / ghi chú |
|---|---|---|
| `Date` | date | **PK** — 1 dòng/ngày, không thiếu ngày |
| `Revenue` | float64 | **GROSS** — xem mục 2. Target chính thức Phần B |
| `COGS` | float64 | **GROSS** — cùng mask với Revenue (kể cả cancelled) |

Không có FK — bảng tổng hợp độc lập, nhưng rebuild được 100% từ `order_items × orders × products`
(MAPE 0.000%, xem `docs/analysis/phase5_model_assumptions/`).

### 4.12 `sample_submission.csv` — 548 dòng, grain 1 dòng/ngày (`2023-01-01 → 2024-07-01`)

| Cột | Dtype quan sát | Ý nghĩa / ghi chú |
|---|---|---|
| `Date` | date | **PK**, format `YYYY-MM-DD` |
| `Revenue` | float64 | **placeholder** — bài nộp phải ghi đè toàn bộ, không giữ giá trị mẫu |
| `COGS` | float64 | **placeholder** — như trên |

Không phải bảng nghiệp vụ — là **template format** cho output Phần B (548 ngày forecast).

### 4.13 `shipments.csv` — 566,067 dòng, grain 1 dòng/đơn có phát sinh vận đơn (0..1 với `orders`)

| Cột | Dtype quan sát | Ý nghĩa / ghi chú |
|---|---|---|
| `order_id` | int64 | FK → `orders.order_id`, không phải 1:1 (646,945 đơn nhưng chỉ 566,067 có shipment — đơn cancelled/chưa ship không có dòng) |
| `ship_date` | date | |
| `delivery_date` | date | |
| `shipping_fee` | float64 | biên độ 0–32 (median ~1.7) — **khác đơn vị tiền tệ** so với giá trị đơn hàng (nghìn–trăm nghìn); KHÔNG cộng vào doanh thu, chỉ so sánh tương đối |

Ghi chú DQ: 564 đơn `delivered/returned/shipped` (524/29/11) không có bản ghi shipment tương ứng
(~0.1%) — chấp nhận sai lệch nhỏ khi phân tích fulfillment.

### 4.14 `web_traffic.csv` — 3,652 dòng, grain 1 dòng/ngày toàn site (`2013-01-01 → 2022-12-31`)

| Cột | Dtype quan sát | Ý nghĩa / ghi chú |
|---|---|---|
| `date` | date | **PK** — thiếu 181 ngày đầu (2012-07-04→2012-12-31) so với sales/orders |
| `sessions` | int64 | |
| `unique_visitors` | int64 | |
| `page_views` | int64 | |
| `bounce_rate` | float64 | tỷ lệ 0–1 |
| `avg_session_duration_sec` | float64 | |
| `traffic_source` | object (enum) | `organic_search/direct/email_campaign/paid_search` quan sát được — **chỉ là nhãn của cả ngày** (grain thật = 1 dòng/ngày toàn site, KHÔNG phải 1 dòng/ngày×nguồn dù tên cột gợi ý vậy). **Không sum sessions theo `traffic_source`** coi là phân rã đầy đủ kênh — phân tích kênh marketing dùng `orders.order_source` thay thế |

Không có FK tới bảng khác — bảng tổng hợp độc lập, không join được xuống order-level.

## 5. Verify đã chạy (bằng chứng KHÔNG bịa cột)

Đọc trực tiếp 14 file tại đúng path `src/datathon/config.RAW_TABLES` trỏ tới (`data/raw/<tên>.csv`,
1 nguồn path duy nhất, không hardcode nơi khác). Không có tool Bash/Python trong session này để chạy
`pandas.read_csv` trực tiếp — dùng Read tool đọc header + vài dòng đầu/cuối từng file (13/14 file đọc
cả đầu lẫn cuối để xác nhận coverage ngày; `sample_submission` đọc đủ đầu/cuối), và Grep đếm số dòng
(`^` match mỗi dòng) để lấy row count thật. Ví dụ cột đọc được (nguyên văn, không sửa):

- `customers.csv`: `customer_id,zip,city,signup_date,gender,age_group,acquisition_channel`
- `order_items.csv`: `order_id,product_id,quantity,unit_price,discount_amount,promo_id,promo_id_2`
- `sales.csv`: `Date,Revenue,COGS`
- `payments.csv`: `order_id,payment_method,payment_value,installments`
- `web_traffic.csv`: `date,sessions,unique_visitors,page_views,bounce_rate,avg_session_duration_sec,traffic_source`

Toàn bộ 14/14 bảng đã đọc header thật + verify row count qua Grep — số dòng ghi trong mục 4 là số
liệu thật (không phải giả định), khớp chéo với các con số đã chốt trước đó trong
`docs/analysis/phase0_qc/phase0_qc_report.md` (vd 714,669 dòng `order_items`, 3,833 dòng `sales`,
2,412 SP `products`) — không phát hiện lệch số.
