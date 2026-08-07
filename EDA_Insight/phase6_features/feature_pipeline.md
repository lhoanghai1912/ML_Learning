# Feature Pipeline — Giai đoạn 6a (de), ma trận feature thuần lịch

- Vai trò: de. Chạy độc lập với session ds (không đụng `feature_spec.md`,
  `feature_target_correlation.csv`, `output/phase6/screen_*`).
- Script: `EDA_Insight/phase6_features/build_features.py`
- Chạy lại: `.venv/bin/python EDA_Insight/phase6_features/build_features.py`
  (chỉ đọc `data/`, chỉ ghi `EDA_Insight/phase6_features/data/` +
  `EDA_Insight/output/phase6/qc_*.png`, ~2-3s, exit 0)
- CHƯA train model (Giai đoạn 7) — đây chỉ là feature matrix.

---

## 1. Pipeline (5 bước, đúng thứ tự script chạy)

1. **`build_tet_dates_extended()`** — dùng `lunardate` tính mồng 1 Tết dương lịch
   2012-2025 (`LunarDate(year,1,1).to_solar_date()`). Đối chiếu 2013-2022 với
   `phase1_descriptive/data/tet_dates.csv` (chỉ đọc) — nếu lệch 1 năm bất kỳ,
   script `sys.exit(1)`, KHÔNG ghi đè file. Kết quả: khớp 100% (10/10 năm).
   Lưu `data/tet_dates_extended.csv`.
2. **`compute_days_from_tet()`** — vector hoá bằng `np.searchsorted` trên mảng
   Tết đã sort: với mỗi ngày, tìm Tết liền trước/liền sau, chọn Tết có
   `|khoảng cách|` nhỏ hơn, trả về khoảng cách CÓ DẤU (âm = trước Tết, dương =
   sau Tết).
3. **`build_calendar_features(dates, tet_dates)`** — hàm DUY NHẤT, dùng chung
   cho cả train và forecast (đảm bảo 2 tập cùng công thức, không lệch định
   nghĩa, không leakage — hàm chỉ nhận `dates` + bảng Tết, không đọc target).
   Sinh đủ 17 cột feature GHIM theo brief (xem bảng mục 2).
4. **`build_train()`** — đọc `data/sales.csv` (3,833 dòng, 2012-07-04 →
   2022-12-31), gọi `build_calendar_features`, thêm `is_partial_year_2012`,
   join `Revenue`/`COGS` NGUYÊN TRẠNG từ `sales.csv` (không tính lại, không
   sửa) → `data/features_train.csv`.
5. **`build_forecast()`** — đọc `data/sample_submission.csv` (548 dòng,
   2023-01-01 → 2024-07-01), gọi CÙNG `build_calendar_features`, KHÔNG join
   target → `data/features_forecast.csv`.

Sau đó hàm `qc()` (mục 5 dưới) chạy tự động cuối script, in log ra stdout +
xuất 1 chart.

---

## 2. Định nghĩa 17 cột feature (đúng GHIM, không tự đổi)

| Cột | Công thức | Ghi chú |
|---|---|---|
| `year` | `dt.year` | int |
| `month` | `dt.month` | 1-12 |
| `quarter` | `dt.quarter` | 1-4 |
| `day_of_week` | `dt.dayofweek` | 0=Thứ Hai … 6=Chủ Nhật |
| `day_of_month` | `dt.day` | 1-31 |
| `month_sin`/`month_cos` | `sin/cos(2π·month/12)` | cyclical |
| `dow_sin`/`dow_cos` | `sin/cos(2π·day_of_week/7)` | cyclical |
| `is_post_2019` | 1 nếu date ≥ 2019-01-01 | dummy break (G1) |
| `is_post_2019_transition` | 1 nếu 2019-01-01 ≤ date ≤ 2021-12-31 | (G1) |
| `days_from_tet` | (date − Tết gần nhất).days, có dấu | (G3), mở rộng 2012-2025 |
| `is_low_margin_season` | 1 nếu month ∈ {7,8,9,11,12} | (G2/G4) |
| `trend_index` | (date − 2012-07-04).days | neo cố định, train/forecast cùng thang |
| `is_holiday_302_305` | 1 nếu 30/4 hoặc 1/5 | chưa kiểm chứng định lượng |
| `is_holiday_qk` | 1 nếu 2/9 | chưa kiểm chứng định lượng |
| `is_christmas` | 1 nếu 25/12 | chưa kiểm chứng định lượng |

`features_train.csv` có thêm 3 cột: `is_partial_year_2012` (=1 cho năm 2012,
để Giai đoạn 7 tự quyết có loại năm cụt hay không), `Revenue`, `COGS` (target
gross, join nguyên trạng từ `sales.csv`).

**KHÔNG có** feature hành vi khách hàng, promo tương lai, region — đúng chốt
Giai đoạn 5 (G4, G5, Nhiệm vụ 3).

---

## 3. Xác nhận số dòng (bắt buộc)

| File | Số dòng | Đối chiếu |
|---|---:|---|
| `features_train.csv` | **3,833** | = số dòng `data/sales.csv` (2012-07-04 → 2022-12-31), không thiếu/thừa ngày |
| `features_forecast.csv` | **548** | = số dòng `data/sample_submission.csv` (2023-01-01 → 2024-07-01); tập ngày khớp 100% (assert `set(...)==set(...)` trong script) |

Script có `assert` cứng cho cả 2 con số này — nếu sai, script dừng ngay (không
âm thầm ghi file sai).

---

## 4. QC bước 5 (log đầy đủ khi chạy `build_features.py`)

1. **Không trùng/thiếu ngày:** `train` — thiếu 0, trùng 0 (so với
   `date_range` liên tục từ min→max). `forecast` — trùng 0, đúng 548 dòng.
2. **NaN ngoài ý muốn:** cả `features_train.csv` và `features_forecast.csv`
   **không có NaN nào** (in rõ nếu có, ở đây log ra "không có NaN").
3. **`days_from_tet` liên tục qua ranh giới năm** — in cửa sổ ±4 ngày quanh
   mồng 1 Tết 2019 (train), Tết 2023 và Tết 2024 (forecast) — bước nhảy đúng
   `+1`/ngày, đúng logic đổi dấu tại mồng 1 (VD Tết 2019: `...-1,0,1...`).
   Kiểm thêm 2 ranh giới dương lịch 31/12→1/1 (2018/2019 và 2022/2023 — mốc
   nối train→forecast) — cũng liên tục `+1`/ngày, không có lỗi lệch năm khi
   tính Tết gần nhất qua ranh giới.
4. **Bảng so phân bố `month`/`day_of_week` train vs forecast:**
   - `month`: forecast (548 ngày = 1.5 năm dương lịch trọn vẹn theo lịch,
     không phải năm chẵn) có tỷ trọng T1-T6 cao hơn train (~11.3% vs ~8%) và
     T7-T12 thấp hơn (~5.5-5.8% vs ~8.6-8.9%) — **đúng như kỳ vọng, không
     phải lỗi**: 548 ngày = 2023 trọn năm (T1-T12) + nửa đầu 2024 (T1-T6), nên
     T1-T6 xuất hiện 2 lần (2023+2024) còn T7-T12 chỉ 1 lần (2023) → tỷ trọng
     lệch tự nhiên theo cấu trúc horizon, không phải bug feature.
   - `day_of_week`: train và forecast gần như đồng nhất (~14.2-14.4% mỗi
     ngày, do 2 tập đều nhiều năm/nhiều tuần, dow phân bố đều tự nhiên).
   - Chart minh hoạ: `EDA_Insight/output/phase6/qc_month_dow_distribution.png`.

Toàn bộ QC PASS — log cuối script in `"QC PASS"`.

---

## 5. Rủi ro/giới hạn kế thừa từ Giai đoạn 5 (nhắc lại, không lặp phân tích)

- `days_from_tet` không có hệ số Tết cố định (G3) — feature chỉ cấp khoảng
  cách, để Giai đoạn 7 tự học pattern.
- `is_low_margin_season`, `is_holiday_302_305`/`is_holiday_qk`/`is_christmas`
  là feature lịch cố định, phòng ngừa leakage promo tương lai (G2/G4) — 3 cờ
  lễ VN dương lịch **CHƯA kiểm chứng định lượng riêng** (đúng ghi chú trong
  brief), Giai đoạn 7 nên coi là feature phụ, không tự suy diễn mức ảnh hưởng.
- `is_post_2019`/`is_post_2019_transition` chỉ là dummy đơn giản (G1) — rủi ro
  biên độ mùa vụ cũng đổi sau break, Giai đoạn 7-8 có thể cần thêm interaction
  `is_post_2019 × month` (đã nêu ở `model_assumptions.md`).
- 548 ngày forecast nối liền ngay sau train (2023-01-01 tiếp theo
  2022-12-31) — không có gap ngày giữa 2 file, `trend_index` dùng chung 1 neo
  nên liên tục qua ranh giới (train kết thúc `trend_index=3832`, forecast bắt
  đầu `trend_index=3833`).
