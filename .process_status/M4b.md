# M4b (ds) — features/models/backtest/submission — REPORT

Status: ✅ done (chờ PO gộp + cập nhật PROCESS.md)
Agent: ds. Phụ thuộc: M1 (✅ ee63d2b). Song song với M2/M4a/M7 — chỉ đụng 4 file ownership.

## File tạo

- `src/datathon/features.py` — calendar + Tết + lag features, load train/forecast qua `config.RAW_TABLES`.
- `src/datathon/models.py` — `TargetForecaster` (fit/predict), `FINAL_CONFIG`, `fit_all`/`predict_all`.
- `src/datathon/backtest.py` — `build_rolling_folds`, `calc_metrics`, `run_backtest`, `select_best_config`.
- `src/datathon/submission.py` — `build_submission`, `validate_submission`, `write_submission`.

## Nguồn port (⚠ quan trọng — đọc trước khi review)

`RESTRUCTURE_AGENTS.md` mục M4 chỉ định nguồn `docs/analysis/phase8_model/*` và
`docs/analysis/phase9_validation/*`. **2 thư mục này KHÔNG tồn tại trên nhánh
`chore/restructure-lakehouse`** (và cả `main`) — `chore/restructure-lakehouse`
được tạo từ `main` tại commit `d2f0d44`, TRƯỚC khi Phase 8/9 được làm (nhánh
`feat/phase8-model` có thêm các commit Phase 8/9 nhưng CHƯA merge vào `main`).

Xác nhận (read-only, không checkout/merge):
- `git merge-base main feat/phase8-model` == `git merge-base chore/restructure-lakehouse feat/phase8-model`
  == `d2f0d44` (branch điểm re re từ trước Phase 8).
- `docs/analysis/` (nhánh hiện tại) dừng ở `phase7_baseline` (khớp `ls`), không có phase8/9.

→ Đã port trực tiếp từ nội dung 3 file trên nhánh `feat/phase8-model` (đọc bằng
`git show feat/phase8-model:<path>`, KHÔNG checkout/switch nhánh, KHÔNG sửa gì
ở branch đó):
- `EDA_Insight/phase6_features/build_features.py` (đã có sẵn ở
  `docs/analysis/phase6_features/build_features.py` nhánh hiện tại, dùng để
  đối chiếu — xem mục Verify) → nguồn `features.build_calendar_features`.
- `EDA_Insight/phase8_model/build_model.py` (chỉ có ở `feat/phase8-model`) →
  nguồn `features.py` (lag/recursive), `models.py`, `backtest.py`.
- `EDA_Insight/phase9_validation/t91_format_check.py` (chỉ có ở
  `feat/phase8-model`) → nguồn `submission.py` (`validate_submission`).
- `EDA_Insight/phase9_validation/committed_baseline/{forecast_548.committed.csv,
  backtest_metrics.committed.csv}` (chỉ có ở `feat/phase8-model`) → baseline
  regression (mục Verify).
- `EDA_Insight/phase8_model/data/final_choice.txt` → `models.FINAL_CONFIG`
  (Revenue: LightGBM/ensemble=True/quarter=False; COGS: giống hệt).

**Không sửa data raw, không đụng nhánh `feat/phase8-model`** (chỉ đọc qua `git show`).
Nếu PO muốn nguồn nằm hẳn trong `docs/analysis` của nhánh restructure, cần 1
việc riêng (merge/cherry-pick phase8/9 vào `docs/analysis` — NGOÀI scope M4b,
báo PO quyết định).

## Kiến trúc / quyết định

- `features.py` không phụ thuộc file CSV trung gian cũ
  (`docs/analysis/phase6_features/data/*.csv`) — tính lại calendar/lag feature
  trực tiếp từ `sales.csv` + `sample_submission.csv` qua `config.RAW_TABLES`
  (đúng "1 nguồn path" của M1, portable sang lakehouse sau này).
- `models.FINAL_CONFIG` ghim cấu hình sản xuất đã backtest xong ở Phase 8
  (LightGBM + ensemble B1, không per-quarter, cho cả Revenue/COGS) — **không
  phải hyperparameter tự chọn mới**, lấy nguyên từ `final_choice.txt` committed.
  `backtest.select_best_config()` implement ĐẦY ĐỦ logic tái tạo lựa chọn này
  từ đầu (4 model tree x rolling fold + so ensemble + so per-quarter) nếu cần
  audit lại — KHÔNG chạy trong `fit_all()` mặc định (tốn, ~20+ fit/target).

## No-leakage — cách tránh future info

- Calendar feature (month/dow/sin-cos/is_post_2019/…): chỉ hàm số của CHÍNH
  ngày d hoặc hằng số neo cố định `TREND_ANCHOR` — 0 phụ thuộc target.
- `days_from_tet`: bảng Tết tính trước bằng công thức âm lịch (`lunardate`),
  không phụ thuộc dữ liệu bán hàng.
- Lag feature (`lag_365`, `lag_365_smooth7`) luôn tra `d - 365 (±tolerance)`
  — luôn < d.
- **Train** (`build_static_lag_features`): tra tĩnh vào `hist` (actual đã biết
  tới ngày build) — an toàn vì offset luôn lùi 365 ngày.
- **Forecast 548 ngày** (`recursive_forecast`, `models.TargetForecaster.predict`):
  548 > 365 nên nửa sau horizon cần lag rơi vào chính vùng đang dự báo → đệ
  quy ngày-qua-ngày, `hist` chỉ được cập nhật bằng dự đoán CHÍNH MODEL NÀY
  vừa sinh cho ngày < d, KHÔNG BAO GIỜ đọc actual/dự đoán ngày >= d.
- `backtest.py`: split THEO THỜI GIAN — mỗi fold `train_fit_end = holdout_start - 1 ngày`
  (không overlap), fit lại từ đầu trên `train_fit` mỗi fold (không rò rỉ giữa
  các fold/tương lai).

## Verify

1. Import: `python3 -c "import sys;sys.path.insert(0,'src');import datathon.features,datathon.models,datathon.backtest,datathon.submission"` → **OK**.
2. **features.py khớp output cũ**: so `load_train_features()`/`load_forecast_features()`
   với `docs/analysis/phase6_features/data/features_{train,forecast}.csv` (file
   có sẵn, nhánh hiện tại) trên toàn bộ `CALENDAR_FEATURES` (16 cột) →
   **max abs diff = 0** (float sin/cos lệch ~1e-17, epsilon dấu phẩy động).
3. **REGRESSION forecast_548** (`submission.build_submission()`, full train
   3833 ngày, model LightGBM production + ensemble B1) vs
   `feat/phase8-model:.../committed_baseline/forecast_548.committed.csv`:
   **`diff` byte-for-byte IDENTICAL** (548 dòng, cả Revenue lẫn COGS,
   `max abs diff = 0.0`, `n_diff>0.01 = 0`). Runtime ~10s (không cần docker/GPU).
4. **backtest.py khớp baseline**: `run_backtest(train, "Revenue", "LightGBM",
   use_ensemble=True, use_quarter=False, folds=[main_548d])` → MAPE/WAPE/RMSE/MAE
   khớp `backtest_metrics.committed.csv` dòng `main_548d,Revenue,Ensemble_LightGBM_B1`
   tới nhiều chữ số thập phân (WAPE 22.711511511781737 cả 2 phía).
   `build_rolling_folds()` sinh đúng 5 fold (`main_548d` + `rolling_1..4`),
   khớp range fold gốc.
5. **submission.validate_submission**: test bắt lỗi THẬT (không `assert True`)
   — case cột âm (`Revenue=-5`) → FAIL đúng `'0 negative values'`; case thiếu
   1 dòng (547) → FAIL đúng `'row count == 548'`. Case hợp lệ → PASS.

Kết luận: **REGRESSION PASS — khớp baseline 100% (sai số 0)**.

## Hạn chế / rủi ro

- `FINAL_CONFIG` ghim cứng (không auto re-derive mỗi lần) — nếu sau này thêm
  data mới (retrain), cần chủ động chạy `backtest.select_best_config()` rồi
  cập nhật `FINAL_CONFIG` (không tự động, tránh đổi hyperparameter ngoài ý
  muốn giữa các lần forecast).
- `select_best_config()` viết đủ, ĐÃ KIỂM 1 fold/1 config khớp số — CHƯA chạy
  full (4 model x 5 fold x 2 target, ước lượng vài phút) trong lần verify này
  vì không cần thiết cho gate regression (forecast_548 đã khớp 100% dùng
  FINAL_CONFIG có sẵn). Nếu PO muốn full audit, chạy:
  `backtest.select_best_config(load_train_features(), "Revenue")` / `"COGS"`.
- Nguồn phase8/9 nằm ở nhánh `feat/phase8-model` chưa merge — nếu nhánh đó bị
  xoá/rewrite sau này, mất khả năng tái audit nguồn gốc. Đề xuất PO: merge
  hoặc cherry-pick phase8/9 vào `docs/analysis` của `main` (việc riêng, ngoài
  scope M4b).
- `recursive_forecast` gọi `predict_fn` 548 lần/target tuần tự (Python loop,
  không vector hoá) — bắt buộc do đệ quy chống leak, nhưng chậm hơn batch
  predict. Chấp nhận được ở quy mô 548-742 ngày (~10s/lần chạy đo thực tế).

## DoD tự check

- [x] import OK.
- [x] regression forecast_548 == baseline (100%, sai số 0).
- [x] backtest metric khớp baseline.
- [x] no-leakage nêu rõ cách tránh (mục trên).
- [x] 0 hardcode path CSV khác `config.RAW_TABLES` (chỉ `config.PROJECT_ROOT` cho output submission.csv mặc định).
- [x] type hint đầy đủ trên hàm public.
- [x] không đụng `schema.py/ingestion.py/quality.py` (M4a), không đụng `config.py` (M1), không sửa data raw.
