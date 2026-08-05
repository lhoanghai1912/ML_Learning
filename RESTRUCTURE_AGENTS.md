# WORK ORDERS — Restructure Lakehouse (D1=C full infra)

Nhánh: `chore/restructure-lakehouse`. Gốc: `/Users/lhoanghai_/Documents/Study/Dự án datathon2026/`.
Mỗi prompt TỰ CHỨA. Phát theo milestone (phụ thuộc bên dưới).

## Sequencing (phụ thuộc)

```
M0 pm  (scaffold + tooling)        ─┐
M1 de  (move data + config)         ├─ M0 xong mới chạy M1..M7
M2 de  (infra docker THẬT)          │   M2 ⇐ M1
M3 de+da (dbt trên Trino/Iceberg)   │   M3 ⇐ M2
M4 de+ds (port src/datathon)        │   M4 ⇐ M1
M5 tester (tests + CI)              │   M5 ⇐ M4
M6 da+ds (notebooks)                │   M6 ⇐ M4
M7 ba  (data/README dictionary)     ┘   M7 ⇐ M1
```

Song song được: sau M1 → {M4, M7} chạy song song. Sau M2 → M3. Sau M4 → {M5, M6}.

---

## M0 — pm — Scaffold + tooling

> Bạn là DATA ENGINEER/PM. Gốc dự án tuyệt đối: `/Users/lhoanghai_/Documents/Study/Dự án datathon2026/`. Nhánh `chore/restructure-lakehouse`.
> Nhiệm vụ: dựng khung cây thư mục target + tooling. KHÔNG move data, KHÔNG port code (milestone khác lo).
> Việc:
> 1. Tạo folder rỗng kèm `.gitkeep`: `infra/{spark,iceberg,trino,minio,cloudbeaver}`, `jobs`, `src/datathon`, `dbt_datathon/models/{staging,intermediate,marts}`, `dbt_datathon/tests`, `notebooks`, `tests`, `data/raw`, `data/sample`, `.github/workflows`.
> 2. `git mv EDA_Insight docs/analysis` ; `git mv "tài liệu" docs/brief` ; `git mv orchestrator_prompt.md docs/` ; `git mv PROGRESS.md docs/`. (giữ nguyên nội dung, chỉ đổi path)
> 3. `src/datathon/__init__.py` (rỗng, package importable).
> 4. `pyproject.toml`: name=datathon, python>=3.9, deps từ `requirements.txt` (pandas, matplotlib, openpyxl, lunardate, scikit-learn, scipy, statsmodels, xgboost, lightgbm, nbconvert, nbclient, notebook) + thêm `dbt-trino` (**pin version**), `pyiceberg`, `boto3`, `psycopg2-binary` (Postgres catalog), `trino`, `pytest`, `ruff`, `structlog` (JSON log). Optional group `obs`: `openlineage-python`. Build backend hatchling, package = `src/datathon`.
> 5. `uv`: nếu cài được `pip install uv` thì `uv lock` → `uv.lock`. Không được thì `pip freeze > requirements.lock` và ghi chú trong README.
> 6. `Makefile` target: `setup` (uv sync / pip install), `lint` (ruff), `test` (pytest), `up` (docker compose up -d), `down`, `ingest` (jobs/ingest_csv_to_iceberg.py), `dbt` (dbt run), `forecast` (src submission), `sample` (sinh data/sample).
> 7. `LICENSE` = MIT (holder: Team Datathon 2026). `.env.example` biến: `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_ENDPOINT`, `S3_BUCKET`, `TRINO_HOST`, `TRINO_PORT`, `ICEBERG_WAREHOUSE`, `DATA_RAW_PATH`. KHÔNG để giá trị thật, chỉ placeholder.
> 8. `README.md`: rewrite mô tả cây mới + cách chạy (`make setup && make up && make ingest && make dbt && make forecast`). Giữ tóm tắt đề bài A/B từ README cũ.
> 9. Cập nhật `.gitignore`: thêm `data/raw/*.csv`, `!data/raw/.gitkeep`, `.env`, `dbt_datathon/target/`, `dbt_datathon/dbt_packages/`, `*.duckdb`.
> Ràng buộc: không xóa file nào của `EDA_Insight` (chỉ move). Chạy `python -c "import sys; sys.path.insert(0,'src'); import datathon"` OK.
> Trả về: cây thư mục mới, list file tạo, uv hay requirements.lock, vấn đề path.

---

## M1 — de — Move data + config (⚠ path fragile)

> Gốc: `/Users/lhoanghai_/Documents/Study/Dự án datathon2026/`. Nhánh restructure. M0 đã xong.
> Nhiệm vụ: dời 14 CSV raw về `data/raw/`, gỡ khỏi git tracking, gom mọi path vào 1 config.
> Việc:
> 1. `git mv data/*.csv data/raw/` (14 file: customers, geography, inventory, order_items, orders, payments, products, promotions, returns, reviews, sales, sample_submission, shipments, web_traffic). `touch data/raw/.gitkeep`.
> 2. `git rm --cached data/raw/*.csv` (GIỮ file trên đĩa, bỏ tracking). KHÔNG rewrite history.
> 3. `src/datathon/config.py`: định nghĩa `PROJECT_ROOT`, `DATA_RAW`, `DATA_SAMPLE`, `RAW_TABLES` (dict tên→path), đọc `DATA_RAW_PATH` từ env fallback `data/raw`. 1 nguồn path duy nhất.
> 4. Grep toàn repo tìm hardcode `data/` path trong `docs/analysis/**/*.py` — KHÔNG sửa file analysis cũ (đã archive, để nguyên). Chỉ đảm bảo `config.py` là chuẩn cho code MỚI.
> Ràng buộc: verify `python -c "import sys;sys.path.insert(0,'src');from datathon.config import RAW_TABLES;import pandas as pd;print(pd.read_csv(RAW_TABLES['sales']).shape)"` chạy OK TRƯỚC khi báo done.
> ⚠ Cảnh báo: `git rm --cached` không xóa file đĩa nhưng lần commit sau CSV biến khỏi repo — người clone mới KHÔNG có data. `data/README.md` (M7) phải ghi cách lấy data.
> Trả về: list file move, shape sales.csv đọc qua config, xác nhận đĩa còn CSV.

---

## DE HARDENING STANDARD (BẮT BUỘC — áp dụng M2, M3)

Tuân thủ mục 27 "Cải tiến lakehouse". Vi phạm = fail gate.

**Ingestion:**
- KHÔNG dùng `createOrReplace`. Dùng incremental **append / MERGE** theo natural key + `_source_updated_at`.
- Mỗi bảng raw thêm cột metadata: `_ingested_at` (utc now), `_source_file`, `_source_row_number`, `_checksum` (hash cả row), `_batch_id` (1 batch/lần chạy).
- **Schema contract** khai báo rõ (dtype + not_null + enum) trong `datathon.schema`. Schema evolution CHỈ theo **allowlist** (thêm cột được duyệt trước) — KHÔNG bật auto-merge-schema tùy ý.
- Record lỗi (sai schema/RI) → ghi bảng **quarantine** `iceberg.raw._quarantine_<table>` kèm lý do. TUYỆT ĐỐI không drop im lặng.

**Iceberg:**
- **Hidden partitioning** cho bảng lớn theo ngày: `months(date)` cho `orders`, `payments`, `sales` daily; tránh partition quá nhỏ (không partition theo day nếu volume thấp).
- Job bảo trì theo lịch: `rewrite_data_files` (compaction), `rewrite_manifests`, `expire_snapshots`. Kiểm soát **small-file problem** + snapshot retention (giữ N ngày, ghi rõ N).

**Catalog:**
- Metadata catalog production = **PostgreSQL** (JDBC catalog), KHÔNG SQLite. Thêm service `postgres` trong compose.

**Security/ops:**
- 0 commit MinIO key. `.env.example` placeholder + đọc runtime từ `.env`/secret store. Bỏ mọi default credential.
- Mỗi service: `healthcheck` + resource limit (`mem_limit`/`cpus`).
- **Observability**: structured logs (JSON) cho jobs; tối thiểu **audit table** `iceberg.ops.ingest_audit` (batch_id, table, rows_in, rows_quarantined, ts, status). Nếu kịp: OpenLineage (Marquez) + Prometheus/Grafana.

---

## DATA QUALITY CHECK STANDARD (10 chiều — BẮT BUỘC)

Khung DQ đầy đủ. Nguồn có sẵn: `docs/analysis/phase0_qc/` (qc01–qc10, đã verify). Port lại, KHÔNG làm lại thuật toán. Mỗi chiều gắn 4 chỗ: `quality.py` (M4) · dbt test (M3) · quarantine trigger (M2) · pytest (M5).

| # | Chiều | Check gì | Nguồn port | Đích | Fail → |
|---|---|---|---|---|---|
| 1 | Snapshot/inventory | 14 bảng có mặt, số dòng, dung lượng, cột, checksum batch | `phase0_qc/de/qc01_inventory.py` | `quality.inventory()` + `ops.ingest_audit` | log + fail nếu thiếu bảng |
| 2 | Schema & format | dtype đúng, enum hợp lệ, format ngày/tiền, encoding | `de/qc02_schema.py` | `schema.validate_schema()` + dbt **contract** | quarantine row sai dtype/enum |
| 3 | Grain & candidate key | grain 1 dòng/khóa; candidate key unique; `order_items` line ID ổn định | `de/qc03_keys.py` | dbt `unique`/`dbt_utils.unique_combination` + `test_schema.py` | fail build |
| 4 | Referential integrity | FK con→cha tồn tại (orders→customers, order_items→orders...) | `de/qc04_ri.py` | dbt `relationships` + `quality.check_ri()` | quarantine orphan row |
| 5 | Completeness | null rate cột bắt buộc, cột trống, % missing theo bảng | `da/qc05_completeness.py` | dbt `not_null` + `quality.completeness()` | warn ngưỡng / fail cột khóa |
| 6 | Business-rule validity | rule nghiệp vụ: revenue≥0, cogs≥0, qty>0, date trong biên, status ∈ enum, gross≥net | `da/qc06_business_rules.py` | dbt singular test + `quality.business_rules()` | quarantine vi phạm |
| 7 | Time coverage | phủ ngày 2012→2022 liên tục, gap ngày, spike/hụt theo tháng | `da/qc07_timecoverage.py` | dbt source **freshness** + `quality.time_coverage()` | warn gap |
| 8 | Duplicate & outlier | trùng full-row/khóa; outlier giá/qty (IQR/z-score) | `ds/qc08_dup_outlier.py` | `quality.dup_outlier()` + `test_schema.py` | dup→quarantine; outlier→flag |
| 9 | Cross-table reconciliation | đối chiếu liên bảng: sales gross vs orders sum; payments vs orders; gross vs net ~13–24% | `ds/qc09_reconciliation.py` | dbt singular test + `quality.reconcile()` | fail nếu lệch > ngưỡng |
| 10 | Data-quality log | tổng hợp 1–9 thành log versioned (bảng+CSV), severity, trend theo batch | `phase0_qc/data_quality_log.{csv,md}` + `tester/qc10_independent_audit.py` | `quality.write_dq_log()` → `ops.dq_log` + `docs/` | báo cáo, gate CONDITIONAL/PASS/FAIL |

Nguyên tắc: chiều 2/4/6/8 sai → **quarantine** (không drop). Chiều 1/3/9 sai khóa → **fail hard**. 5/7 → **warn theo ngưỡng** ghi rõ. Mọi kết quả ghi `ops.dq_log` (batch_id, dimension, table, metric, threshold, status).

---

## M2 — de — Infra docker THẬT (Spark + Iceberg + Trino + MinIO + Postgres + CloudBeaver)

> Gốc như trên. Docker v29.6.1 sẵn. M1 xong. **ĐỌC "DE HARDENING STANDARD" ở trên — bắt buộc.**
> Nhiệm vụ: docker-compose chạy được lakehouse local, chuẩn hardening.
> Việc:
> 1. `docker-compose.yml` services: `minio` (S3, 9000/9001, creds từ `.env`, KHÔNG default), `mc` (init bucket), `postgres` (Iceberg JDBC catalog metadata — KHÔNG SQLite), `iceberg-rest` (REST catalog backend = postgres, storage = MinIO), `trino` (catalog iceberg → REST + MinIO, **pin version** connector), `spark-iceberg` (iceberg runtime + S3A), `cloudbeaver` (8978). Mỗi service: `healthcheck` + `mem_limit`/`cpus`. Secrets `${VAR}` từ `.env`.
> 2. `infra/minio/` bucket policy + init. `infra/iceberg/` catalog config (postgres JDBC). `infra/trino/` `etc/catalog/iceberg.properties` (pin connector version) + `config.properties` + `jvm.config`. `infra/spark/` `spark-defaults.conf` (iceberg extensions, S3A). `infra/cloudbeaver/` preset Trino.
> 3. `jobs/ingest_csv_to_iceberg.py`: đọc `data/raw/*.csv` (dùng `datathon.config`), namespace `raw`. Ghi Iceberg **MERGE theo natural key** (không createOrReplace). Thêm 5 cột metadata (`_ingested_at/_source_file/_source_row_number/_checksum/_batch_id`). Record sai schema → `raw._quarantine_<table>`. Ghi `ops.ingest_audit`. **Hidden partitioning** `months(date)` cho orders/payments/sales. Idempotent (chạy 2 lần không nhân đôi).
> 4. `jobs/compact_iceberg.py` — `rewrite_data_files` + `rewrite_manifests`. `jobs/expire_snapshots.py` — retention N ngày (ghi rõ). (tùy chọn `jobs/rewrite_manifests.py` riêng nếu tách).
> Ràng buộc: `docker compose up -d` → tất cả healthy. `python jobs/ingest_csv_to_iceberg.py` → `SELECT count(*) FROM iceberg.raw.sales` qua Trino > 0; chạy LẦN 2 count KHÔNG đổi (idempotent MERGE). `ops.ingest_audit` có dòng. Ghi RAM cần (Spark+Postgres nặng). ⚠ Secrets CHỈ `.env` (gitignored), 0 hardcode/default creds trong compose.
> Trả về: services + health, count sales (2 lần), số quarantine, audit row, RAM/thời gian, smoke test.

---

## M3 — de + da — dbt trên Trino/Iceberg

> Gốc như trên. M2 xong (Iceberg raw có data).
> Nhiệm vụ: dbt project chạy thật trên Trino. **Tuân "DE HARDENING STANDARD".**
> Việc:
> 1. `dbt_datathon/dbt_project.yml` (profile trino), `packages.yml` (dbt_utils), profile trỏ Trino từ `.env`. **Pin version** `dbt-trino` + connector tương thích Iceberg syntax.
> 2. `models/staging/`: `stg_*.sql` clean 14 bảng raw (ép kiểu, chuẩn tên cột) — rule làm sạch từ `docs/analysis/phase0_qc`. Khai **model contract** (`config(contract={enforced: true})`) + cột/kiểu rõ.
> 3. `models/intermediate/`: `int_daily_revenue`, `int_rfm`, `int_cohort` — port logic `docs/analysis/phase1..3`. Model **incremental** dùng `unique_key` đúng **grain**. ⚠ `order_items` cần **line ID ổn định** — nếu raw thiếu, tạo surrogate key ổn định (`dbt_utils.generate_surrogate_key` trên khóa tự nhiên bền), KHÔNG dùng row_number đổi theo lần chạy.
> 4. `models/marts/`: `mart_revenue_daily`, `mart_customer_segments`, `mart_channel_perf` — port insight Phần A.
> 5. `models/schema.yml`: `sources` khai **freshness** (loaded_at = `_ingested_at`, warn/error after); `tests` not_null/unique/relationships khóa chính; test reconciliation gross vs net (phase0); **exposures** (dashboard/notebook dùng mart nào); `dbt docs`.
> Ràng buộc: `dbt build` xanh (contract enforced pass). `dbt source freshness` chạy được. Incremental chạy 2 lần không nhân đôi (unique_key đúng). Không sửa raw. Regression: revenue daily tổng == phase1.
> Trả về: `dbt build` + `source freshness` kết quả, model pass/fail, contract/incremental OK, mart khớp/lệch phase cũ.

---

## M4 — de + ds — Port `src/datathon/*`

> Gốc như trên. M1 xong (config có). KHÔNG viết lại thuật toán — trích từ code phase đã verify.
> Nhiệm vụ: 8 module chuẩn, importable, có test được.
> Việc (nguồn → đích):
> - `schema.py` ⇐ `docs/analysis/phase0_qc/de/qc02_schema.py` — dtype/enum 14 bảng, hàm `validate_schema(df, table)`.
> - `ingestion.py` ⇐ phase0 loaders — `load_raw(table)` dùng `config.RAW_TABLES`.
> - `quality.py` ⇐ `phase0_qc/*` qc01–10 — implement ĐỦ **10 chiều DQ** (xem "DATA QUALITY CHECK STANDARD"): `inventory/validate_schema/keys/check_ri/completeness/business_rules/time_coverage/dup_outlier/reconcile/write_dq_log`. Mỗi hàm trả DataFrame report + severity. `write_dq_log()` ghi `ops.dq_log`.
> - `features.py` ⇐ `phase6_features/screen_features.py` — calendar features (dow, month, quarter, Tết, lễ). ⚠ giữ nguyên logic no-leakage.
> - `models.py` ⇐ `phase8_model/build_model.py` — train quý + ensemble, `fit()/predict()`.
> - `backtest.py` ⇐ `phase9_validation/*` + phase8 backtest — WAPE/MAPE, rolling fold.
> - `submission.py` ⇐ `phase9_validation/t91_format_check.py` — build + validate format vs `data/raw/sample_submission.csv`, xuất `submission.csv`.
> Ràng buộc: ds — REGRESSION: `models.py` sinh `forecast_548` PHẢI khớp `docs/analysis/phase9_validation/committed_baseline/forecast_548.committed.csv` (sai số ~0). Không đổi hyperparameter. 0 hardcode path (dùng config). Type hint đầy đủ.
> Trả về: 8 module + kết quả regression forecast (khớp/lệch bao nhiêu).

---

## M5 — tester — tests + CI

> Gốc như trên. M4 xong.
> Nhiệm vụ: pytest thật + GitHub Actions, chạy trên `data/sample` (không cần docker).
> Việc:
> 1. Sinh `data/sample/*.csv` = head N dòng mỗi bảng raw (đủ để test, <1MB tổng). Commit được. Có `make sample` tái tạo.
> 2. `tests/test_schema.py` — assert `validate_schema` bắt sai dtype/enum; cover 10 chiều DQ ở mức smoke (grain/key unique, RI orphan, completeness ngưỡng, dup, reconciliation lệch) trên `data/sample`.
> 3. `tests/test_features_no_leakage.py` — assert feature tại ngày t KHÔNG dùng data > t (leakage guard). Quan trọng nhất.
> 4. `tests/test_backtest.py` — assert WAPE tính đúng trên fixture nhỏ, fold không overlap train/test.
> 5. `tests/test_submission.py` — assert output khớp format `sample_submission.csv` (đúng cột, đúng 548 dòng ngày, không NaN, không âm).
> 6. `.github/workflows/ci.yml`: on push/PR → setup python → install (uv/pip) → ruff lint → pytest trên `data/sample`. KHÔNG chạy docker/Spark trong CI (nặng).
> Ràng buộc: `pytest` xanh local. Test phải assert THẬT (không `assert True`). CI dùng `data/sample`, không cần data thật.
> Trả về: số test pass, ci.yml, xác nhận sample <1MB.

---

## M6 — da + ds — Consolidate notebooks

> Gốc như trên. M4 xong.
> Nhiệm vụ: gộp notebook phase cũ thành 3 notebook chuẩn, import `datathon`.
> Việc:
> - `notebooks/01_data_quality.ipynb` ⇐ phase0 — gọi `datathon.quality`.
> - `notebooks/02_eda.ipynb` ⇐ phase1–4 — descriptive/diagnostic/dashboard/prescriptive, gọi mart/`datathon`.
> - `notebooks/03_forecasting_colab.ipynb` ⇐ phase7–8 — features→baseline→model→submission, chạy được cả trên Colab (cell cài deps + mount data).
> Ràng buộc: notebook chạy từ đầu tới cuối không lỗi (execute qua nbclient). Đọc data qua `datathon.config`, không hardcode path. Không xóa notebook cũ trong `docs/analysis`.
> Trả về: 3 notebook + xác nhận execute sạch.

---

## M7 — ba — data/README data dictionary

> Gốc như trên. M1 xong. Nguồn: `docs/brief/data_dictionary.xlsx`, `docs/brief/Đề bài1.docx`.
> Nhiệm vụ: `data/README.md` — data dictionary + cách lấy data thật.
> Việc:
> 1. Đọc `data_dictionary.xlsx` → bảng markdown 14 bảng: tên bảng, cột, kiểu, ý nghĩa, khóa.
> 2. Ghi lưu ý nghiệp vụ quan trọng: `sales.csv` là GROSS (dùng đối chiếu forecast B); `net_revenue` chỉ cho Phần A; `payments.payment_value` = Monetary RFM. (lấy từ README cũ).
> 3. Mục "Cách lấy data": vì raw đã gitignore → ghi rõ nguồn tải + đặt vào `data/raw/`. `data/sample/` là gì.
> Ràng buộc: chỉ tạo `data/README.md`. Số liệu (số dòng/bảng) ghi thật nếu đọc được, không thì ghi "giả định".
> Trả về: data/README.md, số bảng tài liệu hóa.

---

## Definition of Done tổng (gate merge)

- Cây khớp target 100% node.
- `make setup && make up && make ingest && make dbt` chạy hết (D1=C).
- `pytest` + `ci.yml` xanh trên `data/sample`.
- REGRESSION: `forecast_548` mới == committed baseline (sai số ~0).
- `EDA_Insight` cũ còn nguyên trong `docs/analysis` (0 mất file).
- PR review pass.

**Gate hardening (mục 27 — fail thì chặn merge):**
- Ingest **MERGE/append** (không createOrReplace); chạy 2 lần idempotent (count không đổi).
- 5 cột metadata có mặt (`_ingested_at/_source_file/_source_row_number/_checksum/_batch_id`).
- Schema contract + evolution allowlist; record lỗi vào `_quarantine_*` (0 drop im lặng).
- Iceberg hidden partitioning `months(date)` cho bảng lớn; có job compaction + rewrite_manifests + expire_snapshots.
- Catalog = PostgreSQL (không SQLite).
- dbt: contract enforced + source freshness + incremental `unique_key` đúng grain (`order_items` line ID ổn định) + exposures + docs.
- Security: 0 commit key, 0 default cred; mọi service có healthcheck + resource limit.
- Observability: structured log jobs + `ops.ingest_audit` table (tối thiểu); OpenLineage/Prometheus nếu kịp.
- Version pin: `dbt-trino` + Trino Iceberg connector.
- **10 chiều DQ** implement đủ trong `quality.py`; ghi `ops.dq_log`; chiều 2/4/6/8 sai → quarantine, 1/3/9 sai khóa → fail hard, 5/7 → warn ngưỡng.
