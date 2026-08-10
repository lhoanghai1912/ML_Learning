# Audit — Temporal/Cross-table Consistency (2026-08-10)

Phạm vi: AUDIT THUẦN, không sửa code/data/PROCESS.md. Đọc `src/datathon/quality.py` + `RESTRUCTURE_AGENTS.md` mục "DATA QUALITY CHECK STANDARD (10 chiều)" + chạy query thật (pandas, qua `config.RAW_TABLES`, `.venv/bin/python`) trên toàn bộ `data/raw/*.csv`.

Bối cảnh: notebook `02_eda.ipynb` phát hiện `stg_customers.signup_date` sai — 89,3% khách có đơn TRƯỚC ngày signup, làm `int_cohort` cho ra "retention" giả 3,4–3,6% (= base rate). Đã fix bằng model song song `int_cohort_first_order` (commit `f2ac8b3`), KHÔNG sửa `int_cohort`. Câu hỏi đặt ra: (1) DQ framework 10 chiều có bắt được lỗi này không — nếu không, gap ở đâu, đề xuất gì; (2) còn landmine tương tự chỗ nào khác trong 14 bảng không.

---

## Việc 1 — DQ framework 10 chiều có bắt được lỗi `signup_date` không?

### Kết luận: KHÔNG bắt được. Đây là gap thật của framework hiện tại (đã đọc hết `quality.py`, không suy đoán).

Đi qua từng chiều 1 lượt, đối chiếu code thật trong `quality.py`:

| # | Hàm | Check gì (đọc code thật) | Có bắt được lỗi này không? | Vì sao |
|---|---|---|---|---|
| 1 | `inventory` | 14 bảng có mặt, row count > 0 | ❌ | Chỉ đếm dòng, không đọc nội dung cột |
| 2 | `validate_schema` | dtype/enum/cột thiếu-thừa | ❌ | `signup_date` đúng kiểu `date`, không sai dtype/enum — lỗi là *ngữ nghĩa*, không phải *định dạng* |
| 3 | `keys` | grain 1 dòng/khóa unique | ❌ | `customer_id` vẫn unique trong `customers`, không liên quan |
| 4 | `check_ri` | FK con→cha **tồn tại** (`orders.customer_id ∈ customers.customer_id`) | ❌ | Đây đúng là chiều "gần nhất" nhưng **chỉ check tồn tại (existence), không check thứ tự thời gian (temporal ordering)** của quan hệ đó. 100% `orders.customer_id` tồn tại trong `customers` (verify lại ở Việc 2 — 646.945/646.945 khớp), nên `check_ri` báo PASS tuyệt đối dù quan hệ đó về mặt thời gian vô lý |
| 5 | `completeness` | null rate cột bắt buộc | ❌ | `signup_date` không null (0% — đây là dữ liệu SAI giá trị, không phải THIẾU giá trị) |
| 6 | `business_rules` | revenue≥0, cogs≥0, qty>0, **date trong biên**, status∈enum, gross≥net | ❌ | "Date trong biên" hiện chỉ implement cho `orders.order_date` so với `[2012-07-04, 2022-12-31]` (biên toàn cục) — KHÔNG có rule nào so `signup_date` với `order_date` (2 cột khác bảng, cần join). Toàn bộ hàm hiện tại là single-table row-level rule, kể cả khi `loaded` có sẵn nhiều bảng |
| 7 | `time_coverage` | phủ ngày liên tục trong biên kỳ vọng | ❌ | Có chạy `time_coverage(customers, "customers", "signup_date")` (khai trong `date_cols_by_table` của `run_all`) nhưng chỉ đo **gap ngày thiếu trong chính cột đó** — không so với bảng khác. Cột `signup_date` tự nó phủ ngày liên tục bình thường, không có gap |
| 8 | `dup_outlier` | trùng full-row; outlier IQR trên cột numeric | ❌ | `signup_date` là kiểu date, không nằm trong `numeric_cols` (`int`/`float`) → không bao giờ được đưa vào IQR check |
| 9 | `reconcile` | đối chiếu SUM revenue/cogs giữa `sales` và `order_items` rebuilt, payments vs orders | ❌ | Reconcile hiện tại chỉ đối chiếu **giá trị tiền** (Revenue/COGS), không đối chiếu **ngày tháng** giữa 2 bảng. Tổng tiền vẫn khớp 100% (MAPE 0.000%) dù `signup_date` sai — 2 vấn đề độc lập nhau |
| 10 | `write_dq_log` | tổng hợp 1–9 | ❌ | Không tự sinh check mới, chỉ ghi lại kết quả 1–9 — 1–9 đã không bắt được thì 10 cũng không có gì để ghi |

**Nguyên nhân gốc (root cause của gap):** 10 chiều hiện có được thiết kế theo 2 nhóm — (a) check **trong 1 bảng** (schema/grain/completeness/business_rules-đơn/dup_outlier/time_coverage), (b) check **liên bảng nhưng chỉ trên GIÁ TRỊ SỐ** (`check_ri` = tồn tại khóa, `reconcile` = khớp tổng tiền). Không có chiều nào check **liên bảng trên GIÁ TRỊ NGÀY** (temporal ordering qua join, kiểu "cột ngày ở bảng con phải xảy ra sau cột ngày tương ứng ở bảng cha"). Đây đúng là loại lỗi user mô tả: "cross-table temporal consistency" — **không có trong 10 chiều chuẩn của `RESTRUCTURE_AGENTS.md` lẫn implementation `quality.py`.**

### Đề xuất cụ thể (CHỈ đề xuất bằng văn bản — không sửa `quality.py`)

**Tên hàm:** `cross_table_temporal_consistency`

**Vị trí:** hàm mới độc lập, gọi trong `run_all()` sau `check_ri` (vì logic tương tự — cùng cần `loaded` nhiều bảng — nhưng KHÔNG gộp vào `check_ri` vì bản chất khác: RI đo *existence*, cái này đo *ordering*).

**Vì sao KHÔNG nên gắn vào dimension 6 (`business_rules`, severity=QUARANTINE hiện có sẵn):** đã cân nhắc gắn vào đây trước (cùng nhóm "business rule"), nhưng severity QUARANTINE của dimension 6 giả định hành động "loại dòng vi phạm ra khỏi luồng chính, đưa vào `_quarantine_<table>`". Với lỗi này KHÔNG áp dụng được — vi phạm chiếm **89,3% số khách hàng** (Việc 2 xác nhận lại số này), quarantine gần hết bảng `customers` sẽ phá vỡ mọi model/mart downstream dùng `customers` (không phải 1 nhóm dòng lỗi nhỏ cá biệt như orphan FK thường thấy). Vấn đề ở đây là **1 CỘT không đáng tin, không phải 1 nhóm DÒNG sai** → hành động đúng là WARN + gắn cờ ở cấp cột (đúng nguyên tắc "5/7 → warn ngưỡng" của chuẩn hiện có, không phải "2/4/6/8 → quarantine").

**Đề xuất: thêm CHIỀU MỚI #11 (ngoài 10 chiều chuẩn hiện có — cần PO duyệt mở rộng chuẩn), severity = `WARN`.**

Logic (map đúng convention `_result()` đang dùng trong file):

```python
# ----------------------------------------------------------------------
# 11 (đề xuất) — Cross-table temporal consistency
# ----------------------------------------------------------------------
def cross_table_temporal_consistency(
    tables: dict[str, pd.DataFrame] | None = None,
    batch_id: str | None = None,
    warn_threshold: float = 0.02,  # 2% — số dòng orders-shipments-returns-reviews-promotions
                                    # đã đo thật (Việc 2) đều = 0.0000%, nên ngưỡng 2% đủ chặt để
                                    # bắt lỗi hệ thống (89.3%) mà vẫn tha cho nhiễu nhỏ hợp lý
) -> list[DQResult]:
    """Chiều 11 (đề xuất) — cột ngày ở bảng 'quan hệ' (vd signup_date) phải xảy ra TRƯỚC (hoặc
    cùng) cột ngày ở bảng 'sự kiện phát sinh từ quan hệ đó' (vd order_date), theo GRAIN ĐÚNG của
    quan hệ (join key), KHÔNG áp cho toàn cục. Sai -> WARN theo ngưỡng (không quarantine — vi phạm
    thường ở mức CỘT không đáng tin, không phải DÒNG cá biệt; quarantine sẽ xoá phần lớn bảng)."""
    batch_id = batch_id or new_batch_id()
    loaded = _load_all(tables)
    results: list[DQResult] = []

    if "customers" in loaded and "orders" in loaded:
        cust = loaded["customers"][["customer_id", "signup_date"]]
        first_order = (
            loaded["orders"].groupby("customer_id")["order_date"].min().rename("first_order_date")
        )
        joined = cust.merge(first_order, on="customer_id", how="inner")
        n = len(joined)
        n_viol = int((joined["first_order_date"] < joined["signup_date"]).sum())
        pct = n_viol / n if n else 0.0
        results.append(
            _result(11, "customers<->orders", "signup_after_first_order", round(pct, 6),
                    warn_threshold, "PASS" if pct <= warn_threshold else "WARN",
                    f"{n_viol:,}/{n:,} ({pct:.2%}) khách có signup_date SAU ngày đơn đầu tiên "
                    "— cột signup_date không đáng tin làm mốc quan hệ khách hàng.", batch_id)
        )
    return results
```

Và bổ sung `SEVERITY_BY_DIMENSION[11] = "WARN"`, `DIMENSION_NAME[11] = "cross_table_temporal_consistency"`, gọi trong `run_all()`.

**Nếu PO muốn tổng quát hoá** (không chỉ riêng cặp signup/order) có thể tham số hoá thành list cặp `(bảng_cha, cột_ngày_cha, khoá_join, bảng_con, cột_ngày_con)` và loop — Việc 2 dưới đây cho thấy 5/6 cặp còn lại đều PASS 0.0000% nên hiện tại chỉ 1 cặp thật sự cần bắt, nhưng thiết kế tổng quát sẽ tự động phủ luôn nếu sau này phát sinh thêm bảng/quan hệ mới.

**Việc bắt buộc sau khi PO duyệt và có ai sửa `quality.py` thật:** chạy lại toàn bộ M4a DoD (import OK, `run_all()` 14 bảng, MAPE, severity map đúng) — đúng ràng buộc CLAUDE.md, KHÔNG tự làm trong audit này.

---

## Việc 2 — Rà landmine tương tự ở các cặp ngày-tháng khác

Đọc `config.RAW_TABLES` (14 bảng), liệt kê mọi cột ngày và join key nối được:

| Bảng | Cột ngày | Join key nối bảng khác |
|---|---|---|
| `customers` | `signup_date` | `customer_id` → `orders` |
| `orders` | `order_date` | `order_id` → `shipments`, `returns`, `reviews`, `order_items` |
| `shipments` | `ship_date`, `delivery_date` | `order_id` → `orders` |
| `returns` | `return_date` | `order_id` → `orders` |
| `reviews` | `review_date` | `order_id` → `orders`, `customer_id` → `customers` |
| `promotions` | `start_date`, `end_date` | `promo_id` → `order_items.promo_id`/`promo_id_2` |
| `inventory` | `snapshot_date` | không có FK tới bảng có ngày khác (chỉ `product_id`) |
| `web_traffic` | `date` | không có khoá join tới bảng nào (không có `customer_id`/`order_id`) |
| `payments` | **KHÔNG CÓ cột ngày** | — |

→ **6 cặp kiểm được** bằng join thật (`order_id`/`customer_id`/`promo_id`) + 1 cặp **không kiểm được** (payments thiếu cột ngày, ghi nhận riêng). `inventory`/`web_traffic` không có khoá nối tới bảng sự kiện nào khác nên không tạo được cặp temporal cross-table — bỏ qua, không phải landmine, chỉ là giới hạn cấu trúc.

### Query & kết quả thật (chạy `.venv/bin/python`, đọc qua `config.RAW_TABLES`, không suy đoán)

Script dùng chung:
```python
import sys; sys.path.insert(0, 'src')
from datathon.config import RAW_TABLES
import pandas as pd

def load(name, date_cols=None):
    df = pd.read_csv(RAW_TABLES[name], low_memory=False)
    if date_cols:
        for c in date_cols:
            df[c] = pd.to_datetime(df[c], errors='coerce')
    return df

def report(name, merged, before_col, after_col):
    n_total = merged[[before_col, after_col]].dropna().shape[0]
    viol = (merged[before_col] > merged[after_col]) & merged[before_col].notna() & merged[after_col].notna()
    n_viol = int(viol.sum())
    pct = 100 * n_viol / n_total if n_total else float('nan')
    print(f'{name}: {n_viol:,}/{n_total:,} ({pct:.4f}%)')
```

Shape 14 bảng đã load (đúng `config.RAW_TABLES`, không phải file khác):
```
orders      (646945, 8)
shipments   (566067, 4)
returns     (39939, 7)
reviews     (113551, 7)
customers   (121930, 7)
promotions  (50, 10)
payments    (646945, 4)   <- KHÔNG có cột ngày
order_items (714669, 7)
```

#### Kết quả từng cặp (100% chạy thật, output paste nguyên văn)

| # | Cặp kiểm | Logic vi phạm | Join rows (2 ngày non-null) | Vi phạm | Tỷ lệ | Verdict |
|---|---|---|---|---|---|---|
| 1 | `orders.order_date` → `shipments.ship_date` | ship TRƯỚC order | 566.067 | **0** | 0.0000% | ✅ sạch |
| 2 | `shipments.ship_date` → `shipments.delivery_date` | delivery TRƯỚC ship | 566.067 | **0** | 0.0000% | ✅ sạch |
| 3 | `orders.order_date` → `shipments.delivery_date` | delivery TRƯỚC order | 566.067 | **0** | 0.0000% | ✅ sạch |
| 4 | `orders.order_date` → `returns.return_date` | return TRƯỚC order | 39.939 | **0** | 0.0000% | ✅ sạch |
| 5 | `orders.order_date` → `reviews.review_date` | review TRƯỚC order | 113.551 | **0** | 0.0000% | ✅ sạch |
| 6 | `promotions.start_date` → `promotions.end_date` | end TRƯỚC start | 50 | **0** | 0.0000% | ✅ sạch |
| 6b | `order_items.promo_id` áp dụng → `order_date` có nằm trong `[promotions.start_date, end_date]` không | order ngoài cửa sổ campaign | 276.316 (promo_id) + 206 (promo_id_2) | **0** | 0.0000% | ✅ sạch |
| 7 | `customers.signup_date` → `orders.order_date` (đối chiếu lại — KHÔNG phải phát hiện mới, đã biết) | order TRƯỚC signup | 646.945 (theo dòng order) | **477.453** | **73.8012%** | 🔴 landmine (đã biết, đã xử lý ở dbt) |
| 7b | Cùng cặp 7, tính theo GRAIN đúng (1 dòng/khách, min(order_date) mỗi khách) | ≥1 đơn trước signup | 90.246 khách | **80.623** | **89.3369%** | 🔴 khớp tuyệt đối số notebook 89,3% |
| 8 | `payments` → `orders.order_date` | N/A | — | — | **N/A** | ⚠️ KHÔNG kiểm được — `payments.csv` không có cột ngày nào (`order_id, payment_method, payment_value, installments`). Ghi nhận là **gap cấu trúc dữ liệu nguồn**, không phải bug logic — đơn giản là không có timestamp thanh toán trong dataset |

Output thật (paste trực tiếp từ lần chạy):
```
--- orders.order_date -> shipments.ship_date (ship should be AFTER order) ---
  join rows with both dates non-null: 566,067
  violation (ship_date < order_date): 0 (0.0000%)

--- shipments.ship_date -> shipments.delivery_date (delivery should be AFTER ship) ---
  join rows with both dates non-null: 566,067
  violation (delivery_date < ship_date): 0 (0.0000%)

--- orders.order_date -> shipments.delivery_date (delivery should be AFTER order) ---
  join rows with both dates non-null: 566,067
  violation (delivery_date < order_date): 0 (0.0000%)

--- orders.order_date -> returns.return_date (return should be AFTER order) ---
  join rows with both dates non-null: 39,939
  violation (return_date < order_date): 0 (0.0000%)

--- orders.order_date -> reviews.review_date (review should be AFTER order) ---
  join rows with both dates non-null: 113,551
  violation (review_date < order_date): 0 (0.0000%)

--- promotions.start_date -> promotions.end_date (end should be AFTER start) ---
  join rows with both dates non-null: 50
  violation (end_date < start_date): 0 (0.0000%)

--- customers.signup_date -> orders.order_date (KNOWN issue, re-confirm) ---
  join rows with both dates non-null: 646,945
  violation (order_date < signup_date): 477,453 (73.8012%)
  gap days (after-before) stats: min=-3832, median=-1468.0, max=-1

order_items rows with promo_id applied: 276,316; both dates resolvable: 276,316
order_date OUTSIDE promo [start,end] window: 0 (0.0000%)

order_items rows with promo_id_2 applied: 206; both dates resolvable: 206
order_date OUTSIDE promo_id_2 [start,end] window: 0 (0.0000%)

customers with >=1 order BEFORE signup: 80,623/90,246 (89.3369%)
```

**Ghi chú số liệu #7 vs #7b**: 2 cách đo cùng 1 vấn đề, khác grain — #7 đo theo DÒNG ĐƠN HÀNG (73,8% tổng số đơn có order_date < signup_date của khách đặt đơn đó), #7b đo theo DÒNG KHÁCH HÀNG (89,3% khách có ÍT NHẤT 1 đơn trước signup — đúng grain notebook đã dùng, khớp tuyệt đối 89,3% đã công bố trước đó, không lệch). Không mâu thuẫn — cách #7b đúng hơn để mô tả "bao nhiêu KHÁCH bị ảnh hưởng", cách #7 đúng hơn để mô tả "bao nhiêu ĐƠN không dùng được nếu tính theo tenure".

Gap ngày (order − signup, chỉ tính dòng vi phạm): min=−3832 ngày (~10,5 năm), median=−1468 ngày (~4 năm), max=−1 ngày. Độ lệch không phải nhiễu nhỏ 1-2 ngày (kiểu timezone/rounding) — median 4 năm chứng tỏ đây là lỗi sinh dữ liệu mô phỏng (signup_date gán ngẫu nhiên độc lập với lịch sử đơn hàng thật), không phải sai số biên.

---

## Tóm tắt

- **Landmine MỚI tìm thấy trong lần audit này: 0.** 6/6 cặp ngày-tháng khác (order↔shipment, ship↔delivery, order↔return, order↔review, promotion start↔end, promo campaign window↔order date áp dụng) đều **0.0000% vi phạm** — sạch tuyệt đối, không cần sửa gì.
- **Landmine ĐÃ BIẾT (không phải phát hiện mới của audit này, chỉ đối chiếu lại độc lập bằng query riêng)**: `customers.signup_date` vs `orders.order_date` — 89,34% khách (grain đúng) / 73,80% đơn hàng (grain đơn) vi phạm. Số khớp tuyệt đối với notebook đã ghi 2026-08-10 (`f2ac8b3`). Đã có xử lý ở tầng dbt (`int_cohort_first_order`), CHƯA có xử lý ở tầng DQ framework (`quality.py`) — đây chính là gap của Việc 1.
- **1 gap cấu trúc dữ liệu nguồn ghi nhận thêm**: `payments.csv` không có cột ngày → không thể tự động kiểm "payment date vs order_date" bằng bất kỳ công cụ nào (không phải lỗi, chỉ là giới hạn dataset — nếu cần đối chiếu timing thanh toán sau này, phải xin thêm cột từ nguồn dữ liệu, không có cách suy ra từ các bảng hiện có).
- **Mức nghiêm trọng landmine `signup_date`**: cao về mặt PHÂN TÍCH (đã chứng minh làm hỏng hoàn toàn 1 model dbt — `int_cohort`), nhưng **thấp về mặt lan toả** — vì đã rà kỹ, đây là CỘT DUY NHẤT trong toàn bộ 14 bảng mang lỗi loại này (0/6 cặp khác dính). Không có bằng chứng cho thấy đây là lỗi hệ thống lan rộng trong cách sinh dữ liệu mô phỏng, chỉ riêng `signup_date`.
- **Khuyến nghị ưu tiên sửa DQ framework: NÊN, nhưng KHÔNG khẩn cấp.** Lý do nên: gap thật, đã chứng minh gây hậu quả thật (1 model sai âm thầm ~vài ngày cho tới khi phát hiện thủ công qua EDA, không phải qua DQ pipeline tự động — nếu không có buổi phân tích sâu 02_eda.ipynb thì lỗi này có thể tồn tại vô thời hạn mà không ai biết). Lý do không khẩn cấp: (a) chỉ 1/14 bảng, 1 cặp cột dính, đã tìm và vá xong ở tầng downstream (dbt); (b) 6 cặp còn lại đã audit sạch — không có landmine thứ 2 đang chờ; (c) đề xuất ở Việc 1 (chiều 11, severity WARN) có sẵn logic + threshold cụ thể, effort thấp khi PO quyết làm — không cần điều tra thêm gì, chỉ cần code + chạy lại M4a DoD.

**Việc còn treo cho PO quyết (không tự làm trong audit này):**
1. Có duyệt thêm chiều DQ #11 (`cross_table_temporal_consistency`, severity WARN) vào `quality.py` không — nếu có, giao lại cho `de`, sửa xong bắt buộc chạy lại toàn bộ M4a DoD (theo CLAUDE.md).
2. `payments` thiếu cột ngày — chấp nhận giới hạn dataset, hay cần bổ sung nguồn dữ liệu khác (ngoài khả năng audit thuần).
