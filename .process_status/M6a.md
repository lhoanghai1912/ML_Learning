# M6a — da — notebooks/01_data_quality.ipynb + notebooks/02_eda.ipynb

Status: ✅ done (chờ PO verify + gộp vào PROCESS.md)
Ownership: CHỈ `notebooks/01_data_quality.ipynb`, `notebooks/02_eda.ipynb`. KHÔNG đụng
`notebooks/03_forecasting_colab.ipynb` (M6b), KHÔNG đụng `docs/analysis/` (giữ nguyên archive cũ),
KHÔNG đụng `PROCESS.md`.

## Việc đã làm

1. Đọc `PROCESS.md` trước — xác nhận M4a (`b3b85cf`) + M4b (`f4036f9`) = ✅, M3a/M3b vẫn `⬜
   pending` tại thời điểm làm → quyết định notebook 02 đọc **raw CSV qua config** (không có mart
   dbt), ghi rõ TODO nối mart trong markdown đầu notebook.
2. `pip install --upgrade pip && pip install -e . --no-deps` trong `.venv` (hatchling hỗ trợ PEP
   660 với pip mới) để `import datathon` chạy thẳng trong notebook, không cần `sys.path.insert`
   thủ công. Đăng ký kernel Jupyter riêng `datathon-venv` trỏ đúng `.venv/bin/python` (absolute
   path, tránh lệ thuộc `PATH` lúc `nbconvert` chạy) — không sửa gì trong repo, chỉ local venv
   state (không commit).
3. `notebooks/01_data_quality.ipynb` (17 code cell) — port `docs/analysis/phase0_qc/` (giữ nguyên
   file cũ, không xoá): gọi **10/10 hàm DQ thật** trong `datathon.quality` (M4a, `b3b85cf`) trên
   14 bảng raw CSV đọc qua `datathon.config`/`datathon.ingestion.load_raw`: `inventory,
   validate_schema, keys, check_ri, completeness, business_rules, time_coverage, dup_outlier,
   reconcile, write_dq_log` — gọi RỜI từng hàm (để show chi tiết từng chiều) + đối chiếu lại bằng
   `quality.run_all()` (đúng entrypoint M2/M5 dùng) ở cuối. Demo thêm `ingestion.ingest_table()`
   để show chiều 3 (`keys`) chuyển FAIL→PASS sau khi có surrogate `order_item_line_id`.
4. `notebooks/02_eda.ipynb` (25 code cell) — port `docs/analysis/phase1_descriptive/`,
   `phase2_diagnostic/`, `phase3_dashboard/`, `phase4_prescriptive/` (giữ nguyên file `.py`/`.ipynb`
   cũ, không xoá) thành 4 phần trong 1 notebook, đọc qua `datathon.config`/`load_raw` (không
   hardcode path):
   - **Descriptive**: 6 chart (daily+MA30, monthly margin, heatmap năm×tháng, mùa vụ 10 năm chồng,
     day-of-week, hiệu ứng Tết ±30 ngày qua `lunardate`) ⇐ `eda_training_charts.py`/`tet_effect.py`.
   - **Diagnostic**: join `order_items+orders+products+customers+geography+promotions`, sanity
     check khớp `sales.csv`, category/region share, khách mới vs repeat, waterfall gross→net,
     channel trend, promo AOV, Q1 (decompose ASP vs volume break 2019), Q2 (cơ chế bán dưới giá
     vốn gắn với promo) ⇐ `revenue_diagnostic.py`.
   - **Dashboard**: revenue theo tuổi, AOV theo tuổi, RFM segmentation (Champions/Loyal/At
     Risk/...), cohort retention theo tháng signup (loại 238 khách pre-launch) ⇐
     `customer_demographics.py` (bỏ phần logistic-regression churn — ngoài phạm vi 4 phần
     descriptive/diagnostic/dashboard/prescriptive, ghi rõ trong "Hạn chế").
   - **Prescriptive**: 3 đề xuất định lượng — floor price (loại bán dưới giá vốn), win-back theo
     RFM segment (kịch bản uplift), nhân rộng pricing practice vùng margin tốt nhất ⇐
     `prescriptive_analysis.py`.
5. Sửa 1 lỗi phát sinh khi port (không có trong bản gốc vì bản gốc dùng `usecols` giới hạn cột):
   `customers` (load full qua `load_raw`, có sẵn cột `zip`) merge với `li` (đã có `zip` từ
   `orders`) → pandas tự suffix `zip_x/zip_y` → vỡ merge `geography` bước sau. Fix: `customers.drop(
   columns=["zip"])` trước khi merge vào `li`; đơn giản hoá cell cohort retention (bỏ self-merge
   `customers_zip` thừa vì `customers` gốc đã có `zip`).
6. Execute END-TO-END cả 2 notebook bằng `jupyter nbconvert --execute --inplace` (kernel
   `datathon-venv`), output THẬT giữ nguyên trong file (không xoá trước khi nộp).

## Lệnh verify đã chạy + kết quả thật

```
.venv/bin/jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=datathon-venv \
  --ExecutePreprocessor.timeout=900 \
  notebooks/01_data_quality.ipynb
-> [NbConvertApp] Writing 96825 bytes to notebooks/01_data_quality.ipynb   (0 lỗi)

.venv/bin/jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=datathon-venv \
  --ExecutePreprocessor.timeout=1200 \
  notebooks/02_eda.ipynb
-> [NbConvertApp] Writing 1589229 bytes to notebooks/02_eda.ipynb          (0 lỗi, ~28s tổng)
```

Kiểm tra lại bằng `nbformat` (đếm `output_type == "error"` trên toàn bộ cell code):

```
notebooks/01_data_quality.ipynb code cells: 17 errors: 0
notebooks/02_eda.ipynb          code cells: 25 errors: 0
```

## Số liệu thật đọc được từ output (bằng chứng KHÔNG bịa)

- Notebook 01 — `run_all()`: **PASS 177 / WARN 21 / FAIL 1** trên 199 dòng log (khớp
  `.process_status/M4a.md`). FAIL duy nhất = `order_items` thiếu surrogate khi đọc raw thô (đúng
  thiết kế, biến mất sau `ingest_table`). Reconcile chiều 9: `sales<->order_items` MAPE
  Revenue/COGS = **0.000%** (định nghĩa `gross_all_orders`, ngưỡng 1.0%, PASS); `sales<->payments`
  MAPE 5.168% (diagnostic, ngưỡng 10%, PASS, không gate).
- Notebook 02 — sanity check diagnostic: rebuilt `line_revenue` vs `sales.csv` lệch **0.000%**
  (677,662 dòng sau join, 89,063 khách 2013-2022). Break 2018→2019: Revenue -38.6%, ASP +2.4%
  (không giảm), Qty -40.0%, Số đơn -40.2%, Khách active -28.0% → sụt giảm do khối lượng, không do
  giá. Bán dưới giá vốn: 47.86% dòng có promo vs 0.18% dòng không promo. Waterfall gross→net:
  15.69 tỷ → 13.05 tỷ (83.2%). Cohort retention M1/M3/M6/M12 ≈ 2.9-3.0% (retention rơi mạnh sau
  tháng đầu, điển hình first-purchase drop-off). Floor price: margin 13.80% → 16.15% giả định
  (+0.462 tỷ VND). Đầy đủ trong output notebook, không tóm tắt lại số khác.

## DoD tự check

- [x] `notebooks/01_data_quality.ipynb` gọi **10/10 hàm DQ thật** trong `datathon.quality` (M4a),
      không hardcode path (qua `datathon.config`).
- [x] `notebooks/02_eda.ipynb` gồm đủ 4 phần descriptive/diagnostic/dashboard/prescriptive, đọc
      qua `datathon.config`/`load_raw`; TODO nối mart dbt ghi rõ (M3a/M3b chưa xong).
- [x] Execute từ đầu tới cuối KHÔNG lỗi (`nbconvert --execute`, verify lại bằng `nbformat` đếm
      error output = 0/0).
- [x] Output thật còn nguyên trong file (không `--clear-output` trước khi nộp).
- [x] KHÔNG xoá notebook/script cũ trong `docs/analysis/` (còn nguyên 100%).
- [x] KHÔNG đụng `notebooks/03_forecasting_colab.ipynb` (M6b sở hữu).
- [x] KHÔNG commit `PROCESS.md`.

## Ghi chú / blocker cho PO

- KHÔNG có blocker chặn merge. 2 lưu ý:
  1. `docs/dq_log/` là output RUNTIME của `quality.write_dq_log()` khi chạy notebook 01 (batch_id
     mới mỗi lần chạy) — đã xoá sau khi verify (không phải file nguồn, không commit).
  2. Đã `pip install -e .` (editable) + đăng ký kernel `datathon-venv` trong `.venv` local để
     notebook chạy `import datathon` sạch — thay đổi này CHỈ ở local venv/site-packages
     (`.venv/`, `~/Library/Jupyter/kernels/`), KHÔNG sửa file nào trong repo, KHÔNG commit. Agent
     khác/PO tái chạy notebook cần tự làm bước này 1 lần (`pip install -e . --no-deps` trong
     `.venv` sau `uv sync`/`make setup`) hoặc dùng cách `sys.path.insert` cũ nếu không muốn cài
     editable — cân nhắc thêm bước này vào `make setup`/README nếu muốn tester (M5) chạy lại dễ.
  3. Working tree lúc làm việc có file uncommitted của agent khác chạy song song (M3a: `dbt_datathon/*`,
     `pyproject.toml` sửa `dbt-core`/`dbt-trino` version, `Makefile` sửa target `sample`; M5:
     `data/sample/*`, `tests/*`) — KHÔNG đụng, không `git add`, chỉ `git add
     notebooks/01_data_quality.ipynb notebooks/02_eda.ipynb`.

## Commit

- `git add notebooks/01_data_quality.ipynb notebooks/02_eda.ipynb` — conventional commit
  `feat(analysis): consolidate phase0-4 into 01_data_quality + 02_eda notebooks (M6a)`.
- Không `git add -A`, không đụng `PROCESS.md`, không đụng file của M3a/M5/M6b.
