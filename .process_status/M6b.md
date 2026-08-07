# M6b (ds) — notebooks/03_forecasting_colab.ipynb — REPORT

Status: ✅ done (chờ PO gộp + cập nhật PROCESS.md)
Agent: ds. Phụ thuộc: M4a (✅ b3b85cf) + M4b (✅ f4036f9). Song song với M3a/M5/M6a —
chỉ đụng `notebooks/03_forecasting_colab.ipynb`.

## File tạo

- `notebooks/03_forecasting_colab.ipynb` (31 cells) — commit `604cb48`.

## Nội dung (port từ đâu)

Gộp `docs/analysis/phase7_baseline/` (baseline B1/B2/B3/B3b) + Phase 8/9
(`feat/phase8-model`, LightGBM+ensemble+SHAP/robustness — 2 phase này CHƯA có
trong `docs/analysis` nhánh này, xem `.process_status/M4b.md` mục "Nguồn port")
thành 1 luồng: **load feature → baseline B1 (5-fold backtest) → model LightGBM
+ ensemble (5-fold backtest) → so sánh/feature importance → submission →
REGRESSION CHECK**.

**Toàn bộ thuật toán gọi qua module M4b thật** — notebook KHÔNG viết lại công
thức nào:
- `datathon.features`: `load_train_features`, `load_forecast_features`,
  `seasonal_naive_chain` (baseline B1), `TARGETS`.
- `datathon.models`: `FINAL_CONFIG`, `fit_all` (feature importance).
- `datathon.backtest`: `build_rolling_folds`, `calc_metrics`, `run_backtest`.
- `datathon.submission`: `build_submission`, `validate_submission`.

Phần "viết mới" trong notebook chỉ là: lọc DataFrame theo fold (`train[train.Date
<= ...]`, giống hệt logic filter công khai trong `backtest._split_fold` nhưng gọi
trực tiếp trên `train`/`folds` public để B1 không cần fit model), gộp bảng
kết quả (`pd.concat`/`pivot`), vẽ chart (`matplotlib`), và regression check
(`git show` + so `diff`) — không đụng công thức forecast/feature/model nào.

## Chạy trên Colab

- Cell 1 (bootstrap): detect `google.colab`, nếu Colab → `git clone --branch
  chore/restructure-lakehouse https://github.com/lhoanghai1912/ML_Learning.git`
  vào `/content/`, `cd` vào đó; nếu local → tự dò lên cha tới khi thấy
  `pyproject.toml`. Thêm `src/` vào `sys.path` (không cần cài package).
- Cell 2 (deps): `pip install` **subset** dependencies từ `pyproject.toml` —
  chỉ phần notebook forecast này thật sự import (`pandas, numpy, matplotlib,
  lunardate, scikit-learn, scipy, xgboost, lightgbm`) — KHÔNG cài cả stack hạ
  tầng Spark/Trino/dbt/MinIO/Postgres (không dùng ở đây, nặng/chậm trên Colab).
- Data: đọc 100% qua `datathon.config.RAW_TABLES` (0 hardcode path máy local).
  Nếu Colab thiếu `data/raw`: tự mount Google Drive (biến `COLAB_DRIVE_DATA_DIR`
  chỉnh theo user) hoặc fallback `google.colab.files.upload()`, set
  `DATA_RAW_PATH` + `importlib.reload(config)`. Local: đã có `data/raw/*.csv`
  sẵn trên máy → pass ngay (đúng thực tế đã verify — xem mục Verify).
- ⚠ Chưa test thật trên Colab (không có môi trường Colab trong session này) —
  bootstrap logic đã review kỹ (clone/pip/mount đúng API chuẩn), nhưng PO/tester
  nên chạy thật 1 lần trên Colab để xác nhận trước khi coi M6b "Colab-verified".

## Execute — bằng chứng thật

```
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=python3 --ExecutePreprocessor.timeout=900 \
  notebooks/03_forecasting_colab.ipynb
```

- Exit code 0. `[NbConvertApp] Writing 306076 bytes...`. Elapsed ~2m39s (venv
  local, CPU, không Spark/docker).
- Quét lại toàn bộ 31 cell qua `nbformat`: **0 output type `error`**.
- 3 chart PNG render thật (WAPE by fold ×2 target, feature importance ×2
  target, forecast 548 overlay) — `image/png` output có mặt trong file.

## Kết quả thật (dán từ output notebook, KHÔNG hardcode lại số cũ)

**Data:** `train` (3833, 19) 2012-07-04→2022-12-31; `forecast` (548, 17)
2023-01-01→2024-07-01. 0 NaN target.

**Baseline B1 (seasonal-naive), fold `main_548d`:** WAPE Revenue **25.180843%**,
COGS **23.092958%** — khớp `docs/analysis/phase7_baseline/baseline_report.md`.

**Model (LightGBM + ensemble B1, `FINAL_CONFIG`), fold `main_548d`:** WAPE
Revenue **22.711512%**, COGS **19.785127%** — backtest 5 fold × 2 target chạy
thật (~101.5s), khớp số M4b report (22.711511511781737).

**So baseline (mốc phải vượt):**

| Target | B1 WAPE | Model WAPE | Cải thiện tuyệt đối | Cải thiện tương đối |
|---|---:|---:|---:|---:|
| Revenue | 25.18% | 22.71% | -2.47 điểm % | -9.8% |
| COGS | 23.09% | 19.79% | -3.31 điểm % | -14.3% |

→ Model **VƯỢT** baseline B1 cả 2 target trên fold chính thức (assert trong
notebook `improve_pts > 0` — PASS thật, không phải comment).

**Submission (`submission.build_submission()`, elapsed 28.1s):** shape
(548, 3), 8/8 check `validate_submission` PASS (cột, số dòng, format ngày,
0 trùng, 0 NaN, 0 âm).

## REGRESSION CHECK — số liệu thật

Nguồn baseline: `docs/analysis/phase9_validation/committed_baseline/forecast_548.committed.csv`
CHƯA tồn tại trên nhánh này → notebook fallback `git show
f4bc6a4:EDA_Insight/phase9_validation/committed_baseline/forecast_548.committed.csv`
(commit cố định trên `feat/phase8-model`, đúng nguồn M4b đã dùng verify).

```
max abs diff (Revenue+COGS, VND) = 0.0
n_diff > 0.01               = 0
n_diff > 0 (bất kỳ sai lệch) = 0

REGRESSION PASS - forecast_548 khớp committed baseline BYTE-IDENTICAL (max abs diff = 0.0, 548 dòng).
```

**Kết luận: REGRESSION PASS, khớp 100% (sai số 0)** — nhất quán với M4b
(`f4036f9`, đã verify byte-identical trước đó).

## Ràng buộc đã tuân thủ

- KHÔNG xóa notebook cũ trong `docs/analysis/` (chỉ đọc, không sửa/xoá).
- KHÔNG đụng `notebooks/01*`, `notebooks/02*` (M6a sở hữu) — `git status`
  xác nhận chỉ `notebooks/03_forecasting_colab.ipynb` thay đổi trong ownership
  của mình; các file khác đang thay đổi song song bởi M3a/M5 không đụng tới.
- Commit CHỈ `notebooks/03_forecasting_colab.ipynb` (`git add` tường minh,
  không `-A`/`.`) — commit `604cb48`.
- KHÔNG commit `PROCESS.md` (đúng protocol chạy song song) — ghi report này
  thay thế, PO gộp.
- Đọc data qua `datathon.config`, 0 hardcode path CSV máy local.

## Rủi ro / ghi chú cho PO

1. Bootstrap Colab (clone + mount Drive + upload) **chưa test trên Colab thật**
   (chỉ verify local) — nên chạy thử 1 lần trên Colab trước khi tuyên bố
   "Colab-verified" hoàn toàn.
2. REGRESSION CHECK phụ thuộc `git show <commit f4bc6a4>` — nếu object đó bị
   gc sau khi `feat/phase8-model` (kể cả remote) bị xoá, cell regression sẽ FAIL
   vì MẤT NGUỒN ĐỐI CHIẾU (không phải model sai). Khuyến nghị PO cherry-pick
   `phase8_model/` + `phase9_validation/` vào `docs/analysis` nhánh này (đã nêu
   ở M4b, nhắc lại ở đây vì notebook phụ thuộc trực tiếp).
3. `lightgbm` không pin version trong `pyproject.toml` — notebook chạy trên máy
   khác lý thuyết có thể lệch version LightGBM → rủi ro sai khác số học cực nhỏ
   dù cùng SEED=42 (chưa quan sát thấy trên máy chạy report này).
