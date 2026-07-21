# Feature Spec — Giai đoạn 6b (DS, chạy độc lập)

- **Vai trò:** DS, chốt "hợp đồng" định nghĩa feature + sàng lọc tương quan, để đối chiếu với ma trận feature de sinh ra (`build_features.py`, `features_train.csv`, `features_forecast.csv`).
- **Script tái lập:** `EDA_Insight/phase6_features/screen_features.py` — chỉ đọc `data/sales.csv`, ~vài giây, không đọc bất kỳ file nào của de.
- **Chưa train model.** Đây chỉ là mô tả/tương quan để sàng lọc trước Giai đoạn 7.
- **File output của mục này** (tất cả nằm trong `EDA_Insight/phase6_features/`):
  - `data/feature_target_correlation.csv` — tương quan mỗi feature với Revenue/COGS.
  - `data/redundancy_correlation_matrix.csv` — tương quan chéo giữa các feature (month/quarter/sin-cos/trend...).
  - `data/tet_dates_ds_check.csv` — Tết 2011-2025 tự tính bằng `lunardate`, độc lập với `tet_dates.csv` gốc và `tet_dates_extended.csv` của de (dùng để đối chiếu chéo, KHÔNG thay thế).
  - `EDA_Insight/output/phase6/screen_feature_target_corr_heatmap.png` — heatmap Pearson r.

---

## 1. Bảng định nghĩa feature (hợp đồng đối chiếu)

Range tính: toàn bộ `sales.csv` — 3,833 ngày, 2012-07-04 → 2022-12-31 (train). Forecast 548 ngày (2023-01-01 → 2024-07-01) dùng cùng công thức, không cần dữ liệu tương lai nào khác ngoài lịch.

| Feature | Công thức chính xác | Nguồn giả định | Nhóm | Diễn giải (người mới học) |
|---|---|---|---|---|
| `year` | `Date.year` | Nhiệm vụ 4 #6 (model_assumptions) | Bắt buộc (thận trọng, xem mục 5) | Năm dương lịch của ngày quan sát. |
| `month` | `Date.month` (1-12) | G2 + Nhiệm vụ 4 #2 | Bắt buộc | Tháng, dùng bắt mùa vụ lượng (đỉnh T4-6, đáy T11-12). |
| `quarter` | `Date.quarter` (1-4) | Nhiệm vụ 4 #7 | Thử nghiệm (khả năng dư thừa) | Quý — hàm phái sinh trực tiếp của tháng. |
| `day_of_week` | `Date.weekday()`, **0 = Thứ Hai** | Nhiệm vụ 4 #5 | Bắt buộc | Thứ trong tuần, đỉnh Thứ Tư/đáy Thứ Bảy (Phase 1). |
| `day_of_month` | `Date.day` (1-31) | Không có trong G1-G5 gốc — DS tự thêm để kiểm tra hiệu ứng ngày lương/đầu-cuối tháng | Thử nghiệm | Ngày trong tháng. |
| `month_sin` | `sin(2π·month/12)` | Hệ quả kỹ thuật của G2 (mã hoá cyclical cho `month`) | Bắt buộc (đi kèm `month_cos`) | Mã hoá tháng dạng vòng tròn để Tháng 12 và Tháng 1 "gần nhau" thay vì cách xa 11 đơn vị. |
| `month_cos` | `cos(2π·month/12)` | nt | Bắt buộc (đi kèm `month_sin`) | nt |
| `dow_sin` | `sin(2π·day_of_week/7)` | Hệ quả kỹ thuật của Nhiệm vụ 4 #5 | Thử nghiệm | Mã hoá thứ trong tuần dạng vòng tròn. |
| `dow_cos` | `cos(2π·day_of_week/7)` | nt | Thử nghiệm | nt |
| `is_post_2019` | 1 nếu `Date ≥ 2019-01-01`, else 0 | G1 (Nhiệm vụ 2), Nhiệm vụ 4 #1 | Bắt buộc, ưu tiên cao nhất | Cờ đánh dấu giai đoạn sau khi Revenue rơi -38.6% (structural break, không phải nhiễu). |
| `is_post_2019_transition` | 1 nếu `2019-01-01 ≤ Date ≤ 2021-12-31`, else 0 | G1 | Bắt buộc (bổ sung, thử nghiệm mức 2) | Cờ riêng giai đoạn giảm sâu nhất (CAGR -12%/năm), tách khỏi giai đoạn phục hồi 2022+. |
| `days_from_tet` | Số ngày có dấu tới mồng 1 Tết ÂM LỊCH gần nhất (âm = trước Tết, dương = sau); tính bằng `lunardate` | G3, Nhiệm vụ 4 #3 | Bắt buộc, ưu tiên cao | Khoảng cách tới Tết — Tết ảnh hưởng doanh thu nhưng biên độ đổi mỗi năm nên để model tự học qua biến liên tục này. |
| `is_low_margin_season` | 1 nếu `month ∈ {7,8,9,11,12}`, else 0 | G2, G4, Nhiệm vụ 4 #4 | Bắt buộc cho COGS, tuỳ chọn cho Revenue | Cờ mùa margin thấp (promo giảm giá sâu, chênh 266 lần dòng bán dưới giá vốn), là proxy hợp lệ (lịch, không phải promo thật) thay cho biến promo tương lai (leakage nếu dùng trực tiếp). |
| `trend_index` | `(Date − 2012-07-04).days` | Nhiệm vụ 4 #6 | Bắt buộc (thận trọng, xem mục 5) | Số ngày kể từ ngày đầu dữ liệu — bắt xu hướng dài hạn liên tục thay vì rời rạc theo năm. |
| `is_vn_holiday` | 1 nếu (tháng,ngày) ∈ {(4,30),(5,1),(9,2),(12,25)}, else 0 | Nhiệm vụ 4 #8 (chưa có bằng chứng định lượng riêng, cần Giai đoạn 6 tự kiểm tra) | Thử nghiệm | Cờ lễ VN 30/4-1/5, Quốc khánh 2/9, Giáng sinh — CHƯA verify tín hiệu, xem mục 4 kết quả tương quan. |

**Không đưa vào khung feature (đã loại ở Giai đoạn 5, nhắc lại để không tái phạm):**
- Feature hành vi khách hàng lặp lại (rolling active customers, CLV, cohort/RFM theo thời gian) — Nhiệm vụ 3, retention phẳng, khả năng cao do cơ chế sinh dữ liệu random-independent.
- Cường độ promotion tương lai (đếm promo đang chạy từ `promotions.csv`) — G4, leakage rõ ràng vì 548 ngày forecast không có `promotions` tương lai thật.
- `region` làm trục phân rã chính — G5, biến thiên margin theo vùng chỉ ~1pp, target là tổng toàn quốc.

---

## 2. Phân tích dư thừa (redundancy)

Ma trận tương quan chéo (Spearman, `redundancy_correlation_matrix.csv`):

| | month | quarter | month_sin | month_cos | day_of_month | trend_index | year | is_post_2019 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| month | 1.000 | 0.971 | -0.756 | 0.207 | 0.011 | 0.023 | -0.069 | -0.033 |
| quarter | 0.971 | 1.000 | -0.776 | 0.204 | 0.013 | 0.019 | -0.070 | -0.033 |
| trend_index | 0.023 | 0.019 | -0.001 | 0.002 | 0.006 | 1.000 | 0.996 | 0.841 |
| year | -0.069 | -0.070 | 0.068 | -0.015 | -0.003 | 0.996 | 1.000 | 0.845 |
| is_post_2019 | -0.033 | -0.033 | 0.032 | -0.007 | -0.001 | 0.841 | 0.845 | 1.000 |

**Kết luận:**

- **`month` vs `quarter`: dư thừa gần như hoàn toàn (r=0.971).** `quarter = ceil(month/3)` — hàm phái sinh trực tiếp, không mang thêm thông tin. **Khuyến nghị: chỉ giữ 1 trong 2.** Nếu model tree-based (RF/GBM) thì `month` chi tiết hơn, nên ưu tiên `month`, bỏ `quarter`. Nếu cần feature thô cho linear model dễ diễn giải theo quý thì có thể giữ `quarter` thay `month`, không giữ cả hai.
- **`month` vs `month_sin`/`month_cos`: KHÔNG dư thừa theo nghĩa xấu — bổ sung cho nhau.** Correlation Pearson chỉ đo quan hệ tuyến tính; `month` dạng số nguyên có lỗi cấu trúc (Tháng 12 và Tháng 1 cách nhau 11 đơn vị dù liền kề mùa vụ), trong khi `month_sin`/`month_cos` mã hoá đúng tính chu kỳ (Tháng 12 gần Tháng 1). Với model tuyến tính, **nên dùng `month_sin`+`month_cos` thay `month` thô**; với model tree-based, `month` thô vẫn dùng tốt (tree chia ngưỡng, không cần liên tục chu kỳ) — có thể giữ cả hai loại làm 2 nhóm feature thử nghiệm song song, không mâu thuẫn.
- **`day_of_month` có giá trị thật, không phải nhiễu:** kiểm tra trung bình Revenue theo từng ngày (1-31) cho thấy pattern rõ — thấp nhất ngày 4-6 (~2.7-2.9 triệu), tăng dần, cao nhất ngày 30-31 (~7.3-7.6 triệu) và ngày 1 cũng cao (~6.3 triệu). Giống hiệu ứng "đầu/cuối tháng" (lương, chi tiêu dồn cuối tháng) — **corr với `Date` ordinal (trend) chỉ 0.006, không phải do leak thời gian**, là pattern within-month thật. **Khuyến nghị: giữ `day_of_month` làm feature thử nghiệm**, nhưng lưu ý ngày 29-31 chỉ xuất hiện ở một số tháng trong năm (tháng 2 không có ngày 29-31 hầu hết năm, tháng 4/6/9/11 không có ngày 31) → mẫu số nhỏ hơn cho các ngày cuối tháng, dễ nhiễu hơn so với ngày 1-28.
- **`trend_index` vs `year` vs `is_post_2019`: đa cộng tuyến rất cao** (`trend_index`~`year` r=0.996, cả hai ~`is_post_2019` r=0.84). Đây là rủi ro thật cho model tuyến tính (hệ số không ổn định, dấu có thể đảo khi thêm/bớt 1 feature) — xem mục 5.

---

## 3. Validate `days_from_tet`

Trích script (đầy đủ trong log chạy `screen_features.py`):

**Quanh Tết 2019 (2019-02-05, trong range train):**

| Date | days_from_tet |
|---|---:|
| 2019-01-28 | -8 |
| 2019-02-04 | -1 |
| 2019-02-05 | 0 |
| 2019-02-06 | +1 |
| 2019-02-12 | +7 |

→ Dấu đúng: âm trước Tết, 0 đúng ngày Tết, dương sau Tết.

**Quanh Tết 2023 (2023-01-22) và Tết 2024 (2024-02-10) — ngoài range train, minh hoạ công thức tự tính cho 548 ngày forecast (không lấy từ `sales.csv`):**

| Date | days_from_tet | | Date | days_from_tet |
|---|---:|---|---|---:|
| 2023-01-21 | -1 | | 2024-02-09 | -1 |
| 2023-01-22 | 0 | | 2024-02-10 | 0 |
| 2023-01-23 | +1 | | 2024-02-11 | +1 |

→ Công thức áp dụng được cho cả horizon forecast, không cần dữ liệu tương lai nào khác ngoài lịch Tết (đã tự tính bằng `lunardate` tới 2025, đủ phủ hết 548 ngày).

**Liên tục qua ranh giới năm dương lịch (2019-12-25 → 2020-01-05, giữa Tết 2019 04-02-05 và Tết 2020 25-01-2020):**

| Date | days_from_tet |
|---|---:|
| 2019-12-31 | -25 |
| 2020-01-01 | -24 |
| 2020-01-05 | -20 |

→ Không có bước nhảy/reset ở mốc 01-01 — feature tính đúng theo Tết ÂM LỊCH gần nhất (so cả Tết năm trước lẫn Tết năm sau, lấy khoảng cách tuyệt đối nhỏ nhất), không bug reset về Tết dương lịch năm mới.

---

## 4. Sàng lọc tương quan feature-target

Tính trên toàn bộ range train (3,833 ngày). File đầy đủ: `data/feature_target_correlation.csv`.

| Feature | Pearson r (Revenue) | Pearson r (COGS) | Spearman r (Revenue) | Đọc số |
|---|---:|---:|---:|---|
| `is_post_2019` | **-0.380** | -0.374 | -0.428 | Mạnh nhất trong nhóm binary — khớp G1. |
| `month_cos` | **-0.498** | -0.503 | -0.524 | Mạnh nhất toàn bộ — khớp mùa vụ tháng. |
| `days_from_tet` | 0.367 | 0.346 | 0.381 | Mạnh — khớp G3 (dương vì Tết ở đầu năm, xa Tết dần thì trend năm thường phục hồi trong cùng năm, đọc kèm month, không đọc riêng lẻ theo nghĩa nhân quả). |
| `trend_index` | -0.296 | -0.284 | -0.359 | Trung bình — nhưng đa cộng tuyến với `year`/`is_post_2019` (mục 2). |
| `year` | -0.278 | -0.270 | -0.341 | Trung bình — cùng trục với `trend_index`. |
| `day_of_month` | 0.256 | 0.265 | 0.292 | Trung bình — xác nhận pattern đầu/cuối tháng ở mục 2 là thật, không phải nhiễu. |
| `is_post_2019_transition` | -0.322 | -0.317 | -0.369 | Trung bình-mạnh, thấp hơn `is_post_2019` một chút — hợp lý vì chỉ phủ 3/4 năm giai đoạn sau break. |
| `quarter` | -0.214 | -0.174 | -0.248 | Yếu-trung bình, gần trùng `month` (mục 2) — dư thừa. |
| `month` | (không tính trực tiếp theo Pearson tuyến tính vì phi tuyến chu kỳ — xem `month_sin`/`month_cos`) | | | |
| `month_sin` | 0.183 | 0.133 | 0.216 | Yếu-trung bình. |
| `is_low_margin_season` | -0.228 | -0.146 | -0.235 | **Đúng như G2 dự đoán: tác động mạnh hơn lên Revenue (lượng bán) trong dữ liệu thô này** — nhưng lưu ý bảng chỉ đo tương quan tuyến tính với target thô (chưa kiểm soát trend/break); vai trò thật của feature này (COGS/Revenue RATIO, không phải mức COGS/Revenue tuyệt đối) cần đánh giá lại ở Giai đoạn 7 bằng residual sau khi trừ trend+month, không chỉ đọc corr thô. |
| `dow_sin` | 0.098 | 0.098 | 0.085 | Yếu, có ý nghĩa thống kê (p<0.001) nhờ n lớn (3,833) nhưng magnitude nhỏ. |
| `day_of_week` | -0.067 | -0.067 | -0.074 | Yếu, có ý nghĩa thống kê nhưng magnitude nhỏ nhất trong nhóm liên tục. |
| `dow_cos` | 0.0003 (p=0.99) | -0.0015 (p=0.93) | 0.054 (p<0.001) | **Yếu nhất, Pearson không có ý nghĩa thống kê với Revenue** — do `dow_cos` gần như đối xứng quanh giữa tuần, cần dùng cùng `dow_sin` (không nên dùng riêng lẻ). |
| `is_vn_holiday` | 0.082 | 0.078 | 0.035 (p=0.033, yếu) | Group mean diff **dương** (+2.07 triệu Revenue ngày lễ vs ngày thường) — ngược hướng "ngày lễ nên trầm lắng hơn"; khả năng cao là confound theo tháng (2/9 rơi tháng 9 — mùa thấp, nhưng 30/4-1/5 và 25/12 lại rơi các tháng khác) và cỡ mẫu nhỏ (chỉ 4 ngày/năm × 11 năm ≈ 44 quan sát) — **CHƯA đủ bằng chứng để kết luận, cần Giai đoạn 7 kiểm tra residual sau khi kiểm soát tháng/Tết**, không nên tin số liệu thô này như một hiệu ứng nhân quả.

**Feature tín hiệu mạnh (ưu tiên train trước):** `month_cos`/`month_sin`, `is_post_2019`, `days_from_tet`, `is_post_2019_transition`.

**Feature tín hiệu yếu/chưa chắc (cần thêm kiểm tra ở Giai đoạn 7, không loại ngay):** `is_vn_holiday` (mẫu nhỏ, dấu ngược trực giác), `dow_cos` (không có ý nghĩa thống kê riêng lẻ), `day_of_week`/`dow_sin` (magnitude nhỏ nhưng vẫn có ý nghĩa thống kê, giữ lại vì bằng chứng Phase 1 mạnh hơn — corr thô ở đây không phản ánh hết vì hiệu ứng thứ trong tuần có thể bị lấn át bởi mùa vụ tháng/Tết có biên độ lớn hơn nhiều).

---

## 5. Khuyến nghị Giai đoạn 7

**Thứ tự ưu tiên feature nên thử trước (dựa số liệu mục 4, không suy đoán):**

1. `is_post_2019` (r mạnh nhất nhóm binary, khớp G1 — bắt buộc).
2. `month_sin` + `month_cos` (r mạnh nhất toàn bộ, mã hoá đúng chu kỳ — bắt buộc).
3. `days_from_tet` (r mạnh thứ 3, khớp G3 — bắt buộc).
4. `is_post_2019_transition` (bổ sung cho #1, tách giai đoạn giảm sâu nhất).
5. `is_low_margin_season` — bắt buộc riêng cho COGS (theo G2), với Revenue cân nhắc thêm nhưng đọc lại bằng residual, không chỉ corr thô.
6. `day_of_month` — thêm vào baseline thứ 2 sau khi có baseline calendar cơ bản chạy được, vì pattern có thật (mục 2) dù không nằm trong khung Nhiệm vụ 4 gốc.
7. `day_of_week`/`dow_sin`/`dow_cos` — giữ theo Phase 1, nhưng bỏ `dow_cos` riêng lẻ nếu cần rút gọn (không có ý nghĩa thống kê một mình).
8. `trend_index` HOẶC `year` — chỉ chọn 1 (xem cảnh báo đa cộng tuyến dưới), thử nghiệm sau baseline calendar cơ bản.
9. `is_vn_holiday` — thử nghiệm cuối cùng, mẫu nhỏ (~44 ngày lễ/11 năm), dấu ngược trực giác trong bảng thô — cần Giai đoạn 7 kiểm tra kỹ bằng residual trước khi quyết định giữ/bỏ, KHÔNG default giữ chỉ vì "có vẻ hợp lý".
10. `quarter` — bỏ nếu đã có `month`/`month_sin`/`month_cos` (dư thừa, mục 2).

**Có nên loại 2012 (nửa năm) không?**

**Có, cân nhắc nghiêm túc loại hoặc gắn cờ riêng** — lý do định lượng:
- 2012 chỉ có 181 ngày (04/07 → 31/12), nghĩa là **thiếu hoàn toàn 6 tháng đầu năm (T1-T6)**, đúng giai đoạn Revenue thường đỉnh (T4-6, theo Phase 1 mục 2.2).
- Kiểm tra Revenue trung bình theo năm: 2012 = 4.10 triệu/ngày — **thấp hơn mọi năm pre-break khác (2013-2018 dao động 4.54-5.75 triệu)**, dù về nguyên tắc 2012 nên nằm cùng nhóm "tăng trưởng" pre-break. Chênh lệch này nhiều khả năng là do thiếu tháng cao điểm, không phải do 2012 thực sự yếu hơn — **nếu đưa `year`/`trend_index` vào model tuyến tính, điểm dữ liệu 2012 sẽ kéo lệch coefficient năm/trend** vì nó là 1 outlier về "coverage" chứ không phải outlier về hành vi.
- **Khuyến nghị cụ thể:** (a) nếu dùng model tree-based, giữ nguyên 2012, tree không bị ảnh hưởng nhiều vì chia theo ngưỡng cục bộ; (b) nếu dùng model tuyến tính có `year`/`trend_index`, nên loại 181 ngày 2012 khỏi train hoặc thêm 1 cờ `is_partial_year` để model không hiểu lầm đây là mức nền thật của năm 2012; (c) tuyệt đối không dùng 2012 để ước lượng seasonality theo tháng (vì chỉ có H2, sẽ làm lệch ước lượng đỉnh T4-6 nếu vô tình gộp).

**Cờ lễ VN (`is_vn_holiday`) có đáng giữ không?**

Dựa số liệu mục 4: **corr yếu (Pearson 0.082/0.078), Spearman còn yếu hơn và p-value biên (0.033/0.014), group mean diff dương ngược trực giác (ngày lễ lại có Revenue trung bình CAO hơn 2.07 triệu so với ngày thường, thay vì thấp hơn vì công ty đóng cửa/khách ít mua)**. Đây gần chắc là confound (lễ trùng vào ngày có promo/cuối tuần/mùa cao điểm khác nhau tuỳ năm) chứ không phải hiệu ứng lễ thật, và cỡ mẫu quá nhỏ (~44 quan sát/11 năm) để tin. **Khuyến nghị: KHÔNG đưa vào baseline đầu tiên; nếu muốn giữ, phải test residual (sau khi trừ month + is_post_2019 + days_from_tet) ở Giai đoạn 7 trước khi quyết định, không default giữ.**

**Rủi ro đa cộng tuyến `trend_index` / `year` / `is_post_2019`:**

Xác nhận bằng số (mục 2): `trend_index`~`year` r=0.996 (gần như 1 biến), cả hai ~`is_post_2019` r≈0.84. Đây là đa cộng tuyến nghiêm trọng cho mọi model tuyến tính (OLS/Ridge/Lasso yếu) — hệ số ước lượng sẽ không ổn định, dấu có thể sai trực giác dù model vẫn fit tốt tổng thể (R² không bị ảnh hưởng nhiều nhưng interpretability mất). **Khuyến nghị:**
- Model tuyến tính: chỉ chọn **1 trong 2** của {`trend_index`, `year`} cộng với `is_post_2019` (không dùng cả 3), hoặc dùng Ridge để giảm phương sai hệ số.
- Model tree-based (RF/GBM): đa cộng tuyến ít ảnh hưởng tới độ chính xác dự báo nhưng vẫn làm feature importance bị "chia sẻ" giữa 2-3 biến giống nhau, khó đọc importance — nếu cần interpretability, cân nhắc chỉ giữ `is_post_2019` + `trend_index`, bỏ `year` thô.
- Đây thuần là quan sát thống kê (correlation), CHƯA chạy VIF hay model thật — Giai đoạn 7 nên xác nhận lại bằng VIF nếu dùng linear model.

---

## Hạn chế & rủi ro (nêu ngay, không suy đoán quá mức)

1. Toàn bộ mục 4 là **tương quan tuyến tính/hạng (Pearson/Spearman) trên target THÔ**, chưa kiểm soát các feature khác cùng lúc (không phải partial correlation, không phải feature importance từ model thật) — thứ tự "mạnh/yếu" ở đây là gợi ý sàng lọc ban đầu, KHÔNG phải kết quả cuối cùng về feature importance sau khi train model thật ở Giai đoạn 7.
2. `is_low_margin_season` corr thô với Revenue (-0.228) mạnh hơn với COGS (-0.146) — **ngược với kỳ vọng G2** (kỳ vọng feature này ảnh hưởng COGS/Revenue ratio mạnh hơn). Đây KHÔNG phải bằng chứng G2 sai — corr thô đo mức tuyệt đối, không đo ratio; cần Giai đoạn 7 tính lại trên `COGS/Revenue` ratio hoặc residual mới đánh giá đúng.
3. `is_vn_holiday` và `dow_cos` có dấu hiệu nhiễu/confound rõ trong dữ liệu này — đã nêu cảnh báo cụ thể ở mục 4-5, không tự ý loại hẳn (để Giai đoạn 7 quyết định bằng residual test).
4. Script này KHÔNG đọc file của de — nếu `feature_target_correlation.csv`/định nghĩa ở đây lệch với ma trận de sinh ra, cần đối chiếu thủ công 2 file `feature_spec.md` (DS) và `feature_pipeline.md` (de) trước khi Giai đoạn 7 bắt đầu.
