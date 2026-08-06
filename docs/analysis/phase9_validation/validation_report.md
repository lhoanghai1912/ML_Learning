# Validation Report — Giai đoạn 9

Kiểm định độc lập model GĐ8 (LightGBM global + Ensemble 50/50 với B1 seasonal naive, dự báo Revenue + COGS 548 ngày). Report này gộp 2 phần:

- **T9.1 + T9.2 + T9.6-gate (QA/tester, độc lập)** — format bản nộp, leakage, reproducibility, metric vs baseline tự tính lại. Script `t91_format_check.py`. Kết luận: **GO có điều kiện** (xem §T9.1, §T9.2 và §Kết luận cuối bên dưới).
- **T9.3–T9.5 (DS)** — explainability (SHAP) + robustness. Script `explain_robustness.py`, seed cố định `SEED=42`, tự tái lập model GĐ8 (import trực tiếp `build_model.py`, không tin số report cũ). Ràng buộc GĐ5 giữ nguyên: chỉ feature lịch + lag, không hành vi khách/promo tương lai. Không leakage.

Chạy DS: `.venv/bin/python EDA_Insight/phase9_validation/explain_robustness.py` (~2–3 phút).
Chạy QA: `.venv/bin/python EDA_Insight/phase9_validation/t91_format_check.py` + `.venv/bin/python EDA_Insight/phase8_model/build_model.py` (rerun ~6 phút, diff bản committed).

---

## T9.1 — Format bản nộp (QA, độc lập) — 14 PASS / 1 FAIL

So `phase8_model/data/forecast_548.csv` với `data/sample_submission.csv`. Mọi số tự chạy.

| # | Tiêu chí | Kết quả | Bằng chứng |
|---|---|:--:|---|
| 1 | Encoding = UTF-8 | PASS | decode utf-8 strict OK |
| 2 | **Line-ending khớp sample** | **FAIL** | sample=**CRLF** (549), submit=**LF** (0 CRLF) |
| 3 | Tên+thứ tự cột == sample | PASS | `[Date,Revenue,COGS]` |
| 4 | Cột đúng `[Date,Revenue,COGS]` | PASS | — |
| 5 | Số dòng == 548 | PASS | 548 |
| 6 | Số dòng == sample | PASS | 548==548 |
| 7 | Date parse `YYYY-MM-DD` | PASS | 0 lỗi |
| 8 | Range 2023-01-01→2024-07-01 | PASS | min/max khớp, n=548 |
| 9 | Không trùng ngày | PASS | dup=0 |
| 10 | Không thiếu ngày (liên tục) | PASS | missing=0 |
| 11 | Thứ tự ngày == sample | PASS | elementwise equal |
| 12 | 0 NaN | PASS | nan=0 |
| 13 | 0 giá trị âm | PASS | neg=0/0 |
| 14 | ≤2 chữ số thập phân | PASS | submit dp-dist `{1:114,2:982}` max=2; sample cũng drop trailing zero `{1:109,2:987}` — cùng style |
| 15 | Revenue/COGS numeric | PASS | — |

**FAIL #2 — Line-ending (BLOCKER mức thấp, phải sửa trước nộp).** Severity Low–Medium / Priority High (fix free). sample CRLF, submit LF; hệ chấm nhạy line-ending có thể lỗi parse (không tự verify được độ nhạy judge → sửa cho chắc).
Fix lossless (nội dung y hệt): bản CRLF sẵn tại `EDA_Insight/phase9_validation/forecast_548_SUBMIT_crlf.csv`, hoặc:
```bash
.venv/bin/python -c "p='EDA_Insight/phase8_model/data/forecast_548.csv'; d=open(p,'rb').read().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'); open(p,'wb').write(d)"
```
*Ghi chú tiêu chí #14:* check gắt "đúng 2 ký tự lẻ" ban đầu FAIL 114 dòng là **báo động giả** — sample tự nó drop trailing zero; yêu cầu thực = làm tròn ≤2 số lẻ, submit đạt.

---

## T9.2 — Leakage + Reproducibility (QA, chạy lại seed=42)

### Reproducibility — diff bản committed sau rerun sạch

| Output | Byte-identical? | Chi tiết |
|---|:--:|---|
| **`forecast_548.csv` (BẢN NỘP)** | **PASS** | sha256 khớp `080c8bb4…78d36b` (2 lần chạy độc lập trùng) |
| `holdout_predictions.csv` | PASS | max abs diff = 0.0 |
| `final_choice.txt` | PASS | Rev & COGS: LightGBM + ensemble, no per-quarter |
| `backtest_metrics.csv` | FAIL (cosmetic) | 3/72 dòng lệch, **chỉ RandomForest** |

**Diff backtest = nhiễu ULP:** 3 dòng lệch đều RandomForest (rolling_1, rolling_3 — fold phụ), max **rel diff 3.2e-16** (1 ULP float64). LightGBM / Ensemble / FINAL_CHOSEN / B1 / GradientBoosting / XGBoost: lệch **0.0 tuyệt đối**. Nguyên nhân: `RandomForest(n_jobs=-1)` cộng float đa luồng không cố định thứ tự (`random_state=42` đã fix cây). **Không ảnh hưởng bản nộp** (byte-identical) hay quyết định chọn model. Fix để log byte-identical 100%: RF `n_jobs=1` hoặc round metric trước khi ghi. Không chặn nộp.

### Audit leakage (đọc `build_model.py`)

| Kiểm tra | KQ | Dòng |
|---|:--:|---|
| Mọi fold: train_fit cắt TRƯỚC holdout (không chồng) | PASS | 188, 236–237 (`train_fit_end=holdout_start−1`) |
| Feature train chỉ dùng `hist_fit` (không full history) | PASS | 241 |
| lag_365 chỉ dùng ≤ t−1 (`d−365`; tol/smooth ≤ `d−362`) | PASS | 86–106 |
| Holdout/forecast recursive chain, không đọc actual tương lai | PASS | 131–152, 260, 401 |
| Production fit không lộ ngày 2023–2024 vào train | PASS | 371–401 (train ≤2022-12-31) |
| Revenue/COGS train độc lập | PASS | vòng `for target` riêng |

→ **Không phát hiện leakage.** Chain đuôi horizon hợp lệ (đã backtest đúng cơ chế), không phải leak.

### T9.6-gate — Metric độc lập vs baseline (QA tự tính WAPE, không dùng calc_metrics ds)

Tính lại từ `holdout_predictions.csv`, holdout chính 548 ngày, công thức QA riêng:

| Target | Model | WAPE | MAPE | Vượt mốc GĐ7? |
|---|---|---:|---:|:--:|
| Revenue | B1 (mốc 25.18) | **25.18** | 27.48 | — (khớp GĐ7) |
| Revenue | Ensemble FINAL | **22.71** | 26.19 | **PASS** (−2.47đ) |
| COGS | B1 (mốc 23.09) | **23.09** | 24.08 | — (khớp GĐ7) |
| COGS | Ensemble FINAL | **19.79** | 21.30 | **PASS** (−3.30đ) |

B1 tự tính = 25.18/23.09 **khớp chính xác** baseline_report GĐ7 → công thức QA đồng nhất, mốc tái lập. Final vượt WAPE cả 2 target. n_zero_actual=0 → MAPE hợp lệ. **Mọi số model_report tái lập được, không bịa.**

---

## T9.3 — SHAP explainability (LightGBM, cả 2 target)

TreeExplainer trên LightGBM production (fit toàn bộ train 2012–2022). Chart: `output/phase9/09_shap_beeswarm.png`, `09_shap_bar_signed.png`, `09_trend_leafcap_sweep.png`. Số liệu: `data/shap_summary.csv`.

### Chiều tác động (không chỉ độ lớn) — dấu corr(feature value ↔ SHAP)

| Feature | Chiều | corr (Rev / COGS) | Diễn giải business |
|---|:--:|---:|---|
| `lag_365` | **+ (thuận, rất mạnh)** | +0.95 / +0.95 | Cùng kỳ năm trước cao → dự báo cao. Đây là "mức nền mùa vụ" — tín hiệu mạnh nhất, đúng bản chất B1. |
| `trend_index` | **− (NGƯỢC chiều)** | −0.63 / −0.63 | trend cao = giai đoạn gần đây (post-2019) → SHAP âm → kéo dự báo **xuống**. Khớp GĐ6 (corr trend↔Revenue = −0.296): mức nền/ngày các năm gần đây thấp hơn giai đoạn 2013–2018. Tree học đúng dấu này, mạnh hơn tuyến tính. |
| `days_from_tet` | **+ (thuận)** | +0.58 / +0.55 | Âm = trước Tết, dương = sau Tết. SHAP dương khi xa Tết về sau → quanh/trước Tết doanh thu **thấp** (đóng cửa), sau Tết phục hồi. Khớp GĐ6 (corr +0.367). |
| `day_of_month` | **+ (thuận)** | +0.46 / +0.45 | Cuối tháng → dự báo cao hơn. Khớp pattern đầu/cuối tháng GĐ6. |

Beeswarm xác nhận trực quan: `lag_365` điểm đỏ (giá trị cao) nằm bên phải (SHAP dương); `trend_index` điểm đỏ (recent) dồn bên trái (SHAP âm).

### trend_index ở vùng ngoại suy — tree CÓ chặn ở leaf cuối không? → **CÓ, chặn phẳng tuyệt đối**

- **100% (548/548) ngày forecast có `trend_index` > max train** (train 0→3832, forecast 3833→4380). Đây là ngoại suy hoàn toàn ngoài range huấn luyện.
- Sweep `trend_index` (giữ feature khác = median): trong range train pred biến thiên ~2.1M (Rev) / 1.6M (COGS); **ngoài range (trend > 3832) dao động = 0** → đường dự báo **nằm ngang tuyệt đối** (Rev ≈ 2.65M, COGS ≈ 2.87M = giá trị leaf phải-cùng).
- **Kết luận:** tree KHÔNG ngoại suy tuyến tính (tránh được bias +29–39% của linear GĐ7 mục 4.4) — nhưng cái giá là `trend_index` đóng góp một **hằng số cố định** cho toàn bộ 548 ngày forecast. Mọi biến thiên trong forecast đến từ `lag_365` + calendar, KHÔNG từ trend.
- **Rủi ro business kèm theo (nêu rõ):** nếu mức nền thật 2023–2024 **tăng vượt** đỉnh 2022, model **không thể** bắt được (bị cap) → sẽ **under-forecast** phần tăng trưởng thật ngoài lịch sử. Ngược lại nếu tiếp tục đi ngang/giảm thì cap là an toàn. Cap lấy đúng giá trị leaf của giai đoạn gần nhất (mức nền recent, thấp) — thiên về thận trọng.

### Xác nhận feature ~0 importance (khớp GĐ6/GĐ8)

`quarter`, `is_holiday_qk`, `is_christmas`: **mean|SHAP| = 0.0 tuyệt đối** cả 2 target. Xác nhận độc lập bằng SHAP (không chỉ split-count như GĐ8) — 3 feature này dư thừa hoàn toàn (quarter ⊂ month; hai cờ lễ là nhiễu cỡ mẫu nhỏ). An toàn để loại nếu muốn gọn model; giữ lại cũng vô hại (tree không dùng).

---

## T9.4 — Suy giảm theo horizon (holdout main_548d)

Tách metric theo 2 chế độ lag của cơ chế chain (rủi ro §6.2): ngày 1–365 dùng `lag_365` từ **actual thật**; ngày 366–548 dùng `lag_365` từ **giá trị model tự dự đoán** (chain). Số liệu: `data/horizon_degradation.csv`.

| Target | Model | WAPE 1–365 (lag actual) | WAPE 366–548 (lag chain) | Δ đuôi−đầu |
|---|---|---:|---:|---:|
| Revenue | B1 | 26.45% | 22.21% | −4.24 |
| Revenue | LightGBM | 23.50% | 22.55% | −0.95 |
| Revenue | **Ensemble 50/50** | 23.83% | **20.09%** | **−3.74** |
| COGS | B1 | 23.13% | 23.00% | −0.13 |
| COGS | LightGBM | 19.58% | 21.19% | +1.61 |
| COGS | **Ensemble 50/50** | 20.03% | **19.20%** | **−0.84** |

**Kết luận:** rủi ro cộng dồn sai số phần đuôi §6.2 **KHÔNG hiện thực hóa** trên holdout — đuôi ensemble còn **tốt hơn** đầu (Rev −3.74, COGS −0.84 điểm). LightGBM đơn có compounding nhẹ ở COGS (+1.61 điểm) nhưng nhánh B1 neo lại → ensemble triệt tiêu. Đây là bằng chứng thực nghiệm cho vai trò "chặn rủi ro đuôi chuỗi" của ensemble.

**→ KHÔNG cần thêm `lag_182`** (điều kiện kích hoạt Δ>+5 điểm không đạt cho bất kỳ target nào → giữ model gọn, không thêm biến làm compounding sớm hơn từ ngày ~183).

**Caveat trung thực:** đuôi holdout main = **H2/2022** (giai đoạn phục hồi ổn định). Đuôi forecast thật = **H1/2024**, regime có thể khác → không thể loại trừ hoàn toàn compounding trên horizon thật. Bằng chứng hiện có ủng hộ model đủ mạnh, nhưng monitor drift khi có actual 2023 (xem §retrain GĐ8 mục 7.6).

---

## T9.5 — Robustness (5 fold) + weight ensemble

### Bảng WAPE % — GradientBoosting vs LightGBM vs Ensemble 50/50 qua CẢ 5 fold

Số liệu: `data/robustness_table.csv` (lấy từ backtest GĐ8, đối chiếu khớp).

| Target | Model | main_548d | roll_1 | roll_2 (break) | roll_3 | roll_4 | avg_roll | avg_roll (no break) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Revenue | GradientBoosting | 25.1 | 21.1 | 44.6 | 27.0 | 33.5 | 31.57 | 27.23 |
| Revenue | LightGBM | 23.2 | 22.1 | 63.2 | 25.5 | 20.4 | 32.80 | 22.68 |
| Revenue | **Ensemble 50/50** | **22.7** | 20.4 | 58.3 | 24.1 | 19.2 | 30.53 | **21.26** |
| COGS | GradientBoosting | 20.9 | 22.1 | **31.2** | 20.6 | 22.2 | **24.05** | 21.66 |
| COGS | LightGBM | 20.1 | 25.0 | 57.4 | 21.0 | 18.4 | 30.45 | 21.47 |
| COGS | **Ensemble 50/50** | **19.8** | 21.1 | 54.6 | 20.8 | 17.3 | 28.43 | **19.71** |

**Đọc bảng:**
- Trên **fold main** (mốc chính thức) và **avg các fold no-break**: **Ensemble thắng cả 2 target** (Rev 22.7/21.26, COGS 19.8/19.71 — thấp nhất mỗi cột).
- **GradientBoosting** chỉ thắng ở **`avg_roll` COGS (24.05)** — nhưng lợi thế này **hoàn toàn đến từ fold break `rolling_2`** (GB 31.2 vs Ensemble 54.6). Loại fold break ra, GB thua Ensemble ở mọi target.
- `rolling_2` (2018-07→2019-12, đúng sốc cấu trúc break 2019) làm **mọi** model tệ 44–63% — giới hạn dữ liệu, không phải lỗi model.

### Tối ưu weight ensemble (grid 0.30–0.70 trọng số tree, chọn trên VALIDATION)

Chọn theo **avg WAPE các fold rolling** (validation) — **KHÔNG nhìn fold main** để tránh overfit chọn model. Số liệu: `data/weight_grid.csv`.

| Target | w*(argmin avg_roll) | avg_roll@w* | main@w* | So w=0.5 |
|---|:--:|---:|---:|---|
| Revenue | **0.50** | 30.53 | 22.71 | trùng — 0.5 là argmin |
| COGS | **0.50** | 28.43 | 19.79 | trùng — 0.5 là argmin |

- **w=0.5 chính là argmin trên validation cho CẢ 2 target** → 50/50 là lựa chọn nguyên tắc theo đúng tiêu chí đăng ký trước.
- Nghiêng nhiều-tree hơn (w≈0.6) chỉ tốt hơn ≤0.2 điểm trên main/no-break, **nhưng làm tệ fold break** (B1 đỡ tệ hơn tree ở break, cần B1 nhiều hơn) → đánh đổi robustness lấy lợi ích trong-nhiễu. **Từ chối.**

### CHỐT

| Hạng mục | Quyết định | Lý do (số liệu) |
|---|---|---|
| Model | **GIỮ Ensemble LightGBM + B1** | Thắng main + no-break cả 2 target; GB chỉ hơn nhờ 1 fold break không đại diện horizon post-break 2023–2024. |
| Weight | **GIỮ 50/50** | Là argmin validation cả 2 target; lệch weight chỉ đổi ≤0.2 điểm mà mất robustness break. |
| Re-forecast | **KHÔNG** | Không đổi model/weight → `forecast_548.csv` GĐ8 giữ nguyên. **Tester KHÔNG cần chạy lại T9.1.** |

**GradientBoosting = phương án dự phòng có ghi nhận:** nếu có tín hiệu sốc cấu trúc trong 2023–2024 (hiện KHÔNG có bằng chứng), GB robust hơn hẳn ở regime break (COGS: 31.2 vs 54.6). Giữ sẵn làm fallback nếu monitor drift báo động.

---

## Cập nhật hạn chế & rủi ro (bổ sung cho §6 model_report GĐ8)

1. **§6.2 (compounding đuôi) — GIẢM MỨC:** đo thực nghiệm cho thấy đuôi holdout không suy giảm (còn tốt hơn). Nhưng đuôi holdout (H2/2022) ≠ đuôi forecast (H1/2024) → vẫn cần monitor.
2. **Leaf-cap trend_index (MỚI, từ T9.3):** toàn bộ 548 ngày forecast nhận đóng góp `trend_index` = hằng số (leaf recent, thấp). Model **không bắt được tăng trưởng thật vượt lịch sử** → thiên hướng under-forecast nếu 2023–2024 bật tăng nền. Rủi ro một chiều, cần nêu khi trình bày.
3. **§6.6 (chỉ 5 fold, 1 fold break):** không đổi — bằng chứng robustness vẫn hạn chế bởi độ dài dữ liệu.

---

## Kết luận T9.6 (phần DS)

- Explainability: model diễn giải được, chiều tác động hợp lý, khớp phát hiện GĐ6. Không phát hiện feature "ma"/leakage; 3 feature ~0 xác nhận lại.
- Robustness: cấu hình cuối (Ensemble 50/50) là lựa chọn tốt nhất trên tiêu chí đăng ký trước; weight tuning không cải thiện đáng kể.
- **Không đổi bản nộp cuối** (`forecast_548.csv` GĐ8).

---

## Kết luận T9.6 (gộp) — Bảng PASS/FAIL + GO/NO-GO

| Hạng mục | KQ |
|---|:--:|
| T9.1 Format (13 tiêu chí lõi) | PASS |
| T9.1 Line-ending khớp sample | **FAIL → phải sửa CRLF** |
| T9.2 `forecast_548.csv` byte-identical | PASS |
| T9.2 `backtest_metrics.csv` byte-identical | FAIL (nhiễu ULP, RF, vô hại) |
| T9.2 Leakage audit | PASS |
| T9.6 Vượt baseline Revenue WAPE | PASS (22.71 < 25.18) |
| T9.6 Vượt baseline COGS WAPE | PASS (19.79 < 23.09) |
| T9.6 B1 baseline tái lập khớp GĐ7 | PASS |
| T9.3–T9.5 (DS) Explainability + Robustness | PASS (không leakage, cấu hình tối ưu) |

### QUYẾT ĐỊNH: **GO CÓ ĐIỀU KIỆN**

**Điều kiện bắt buộc trước nộp (1 việc):**
1. **Sửa line-ending → CRLF** cho khớp sample. Nộp `forecast_548_SUBMIT_crlf.csv` (byte-identical nội dung, chỉ khác line-ending) hoặc chạy lệnh fix in-place ở §T9.1.

**Không chặn nộp (ghi nhận / xử lý sau):**
- `backtest_metrics` nhiễu ULP trên RandomForest → set RF `n_jobs=1` nếu cần log byte-identical 100%.
- Rủi ro nền không sửa được ở GĐ8 (đã nêu §6 model_report + §T9.3/T9.4 trên): không có ground-truth 2023–24; leaf-cap `trend_index` → thiên under-forecast nếu nền bật tăng; fold break 2019 mọi model đều kém.

**Sau khi áp fix #1 → bản nộp đủ điều kiện GO.**

---

## File output GĐ9

- `explain_robustness.py` — script tái lập (import `build_model.py`).
- `data/shap_summary.csv` — mean|SHAP| + chiều tác động mọi feature, 2 target.
- `data/horizon_degradation.csv` — WAPE/MAPE đầu vs đuôi horizon.
- `data/robustness_table.csv` — GB vs LGB vs Ensemble qua 5 fold.
- `data/weight_grid.csv` — grid weight 0.30–0.70.
- `output/phase9/09_shap_beeswarm.png`, `09_shap_bar_signed.png`, `09_trend_leafcap_sweep.png`.
- *(không sinh `forecast_548_v2.csv` — không đổi weight/model.)*

**QA (T9.1/T9.2):**
- `t91_format_check.py` — script check format độc lập (tái lập).
- `forecast_548_SUBMIT_crlf.csv` — **bản nộp đã fix CRLF** (nội dung byte-identical forecast_548).
- `committed_baseline/*.committed.csv` — snapshot output committed để diff sau rerun.
- `rerun1_stdout.log` — log chạy lại `build_model.py`.
