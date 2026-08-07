# RESTRUCTURE PLAN — Datathon 2026 → Lakehouse Layout

Owner: PO. Trạng thái: **APPROVED** — nhánh `chore/restructure-lakehouse` (từ main).

**Quyết định user (2026-08-05):**
- **D1 = C** — Full lakehouse chạy thật (docker-compose Spark + Iceberg + Trino + MinIO + CloudBeaver + dbt). Effort ~2 tuần. Docker OK (v29.6.1). ⚠ `uv` CHƯA cài.
- **D2 = A** — Archive `EDA_Insight/` → `docs/analysis/`, port insight sang dbt marts dần.
- **D3** — `git rm --cached` CSV + gitignore + sample nhỏ. KHÔNG rewrite history. Làm trên nhánh mới.

RICE cập nhật cho D1=C: **WS8 (infra) nâng lên P1**, effort E=8 (không còn scaffold). Xem work order chi tiết ở `RESTRUCTURE_AGENTS.md`.

---

## 1. Vision & mục tiêu

Chuyển repo từ **EDA-notebook** (organic, 11 phase xong) sang **cấu trúc lakehouse chuẩn production** (target struct: Spark + Iceberg + Trino + MinIO + dbt + uv + docker + CI).

Success metrics (đo được):

| Metric | Baseline | Target |
|---|---|---|
| File cây khớp target struct | 0% | 100% node có mặt |
| Notebook/script chạy lại được sau move (0 broken path) | ? | 100% |
| Analysis 11 phase cũ bảo toàn (0 file mất) | 100% | 100% |
| Repo size (git) | ~150MB CSV commit | < 20MB (raw gitignored + sample nhỏ) |
| CI xanh trên push | không có CI | ci.yml pass |
| `make setup && make test` chạy 1 lệnh | không | pass |

Giả định (không có số thật):
- G1: mục tiêu contest = giữ được kết quả forecast Phần B, KHÔNG thi hạ tầng. Nên infra là "nice-to-have", analysis là "must".
- G2: chưa có Docker/Spark/Trino cài trên máy. Build full infra = nhiều ngày.

---

## 2. DECISIONS NEEDED (chốt trước khi làm)

**D1 — Độ sâu infra.** Target có Spark/Iceberg/Trino/MinIO/CloudBeaver/dbt. 3 lựa chọn:
- **A. Scaffold-only** (khuyến nghị): tạo folder + file mẫu/README cho infra, KHÔNG dựng cluster thật. Giữ pipeline pandas hiện tại chạy. Rẻ, nhanh, không mất việc cũ.
- **B. dbt + DuckDB/Postgres**: dựng dbt thật chạy local nhẹ (không cần Spark). Trung bình.
- **C. Full lakehouse**: docker-compose Spark+Iceberg+Trino+MinIO chạy thật. Đắt, rủi ro cao, nhiều ngày.

**D2 — Số phận `EDA_Insight/` (11 phase).** Target không có chỗ cho nó. Chọn:
- **A. Archive** → gom vào `notebooks/` + `docs/analysis/`, port insight sang dbt marts dần. (khuyến nghị)
- **B. Rewrite** phase 5–9 thành `src/datathon/*.py` chuẩn, bỏ notebook cũ. Đắt, rủi ro mất logic đã verify.

**D3 — Data 150MB CSV đang commit.** Target: `data/raw/` gitignored + `sample/` nhỏ. Nghĩa là:
- gỡ CSV khỏi git tracking, thêm vào .gitignore, tạo `data/sample/` (vài nghìn dòng) cho CI.
- Trade-off: **repo nhẹ + chuẩn** vs **mất tiện "clone là có data"**. Cần `data/README.md` ghi cách tải data thật.
- ⚠ Gỡ file khỏi git history (nếu muốn nhẹ thật) = rewrite history, phá clone người khác. Mặc định: chỉ `git rm --cached` (giữ history), không rewrite.

> Khuyến nghị PO: **D1=A, D2=A, D3=git rm --cached + sample**. Rẻ, giữ trọn việc cũ, khớp struct 100% mặt cây thư mục. Nâng cấp B/C để sprint sau.

---

## 3. Gap analysis — Current → Target mapping

| Target node | Nguồn hiện có | Hành động |
|---|---|---|
| `README.md` | có (cập nhật) | rewrite mô tả cấu trúc mới |
| `LICENSE` | ❌ | tạo (MIT?) |
| `.env.example` | ❌ | tạo (biến MinIO/Trino/paths) |
| `.gitignore` | có | thêm `data/raw/*`, giữ .venv |
| `Makefile` | ❌ | tạo target: setup/lint/test/eda/forecast |
| `pyproject.toml` | ❌ | tạo từ `requirements.txt` |
| `uv.lock` | ❌ (dùng pip) | `uv lock` hoặc `requirements.lock` |
| `docker-compose.yml` | ❌ | scaffold (D1) |
| `data/raw/.gitkeep` | `data/*.csv` | move CSV → raw/, gitignore, .gitkeep |
| `data/sample/` | ❌ | sinh sample nhỏ từ raw |
| `data/README.md` | `tài liệu/data_dictionary.xlsx` | viết data dictionary md |
| `infra/{spark,iceberg,trino,minio,cloudbeaver}` | ❌ | scaffold (D1) |
| `src/datathon/config.py` | rải rác path trong script | gom config path |
| `src/datathon/ingestion.py` | phase0 loaders | trích từ phase0 |
| `src/datathon/schema.py` | `phase0_qc/de/qc02_schema.py` | port |
| `src/datathon/quality.py` | `phase0_qc/*` (qc01–10) | port |
| `src/datathon/features.py` | `phase6_features/screen_features.py` | port |
| `src/datathon/backtest.py` | `phase9_validation/*`, `phase8` backtest | port |
| `src/datathon/models.py` | `phase8_model/build_model.py` | port |
| `src/datathon/submission.py` | `phase9_validation/t91_format_check.py`, submission csv | port |
| `jobs/*` | ❌ | scaffold (D1) |
| `dbt_datathon/*` | ❌ | scaffold (D1/D2) |
| `notebooks/01_data_quality.ipynb` | phase0 notebooks | consolidate |
| `notebooks/02_eda.ipynb` | phase1–4 notebooks | consolidate |
| `notebooks/03_forecasting_colab.ipynb` | phase7–8 notebooks | consolidate |
| `tests/test_schema.py` | `qc02_schema.py` | viết pytest |
| `tests/test_features_no_leakage.py` | phase6 leakage check | viết pytest |
| `tests/test_backtest.py` | phase9 | viết pytest |
| `tests/test_submission.py` | `t91_format_check.py` | viết pytest |
| `.github/workflows/ci.yml` | ❌ | tạo (lint+pytest+sample) |
| **KEEP (ngoài struct)**: `PROGRESS.md`, `orchestrator_prompt.md`, `tài liệu/`, `EDA_Insight/` | → `docs/` | move theo D2 |

---

## 4. RICE — ưu tiên workstream

Reach (bao nhiêu phần dự án hưởng, 1–10) × Impact (0.25/0.5/1/2/3) × Confidence (%) ÷ Effort (người-ngày).

| # | Workstream | R | I | C | E | RICE | Ưu tiên |
|---|---|---|---|---|---|---|---|
| WS1 | Scaffold cây thư mục + move CSV→raw + .gitignore + .gitkeep | 10 | 3 | 90% | 1 | **27.0** | P0 |
| WS2 | pyproject.toml + uv.lock + Makefile + LICENSE + .env.example | 9 | 2 | 90% | 1 | **16.2** | P0 |
| WS3 | Port `src/datathon/*` từ phase code (config/schema/quality/features/models/backtest/submission) | 8 | 3 | 70% | 3 | **5.6** | P1 |
| WS4 | tests/ pytest + CI ci.yml | 7 | 2 | 80% | 2 | **5.6** | P1 |
| WS5 | data/README.md (data dictionary) + data/sample sinh nhỏ | 6 | 2 | 90% | 1 | **10.8** | P1 |
| WS6 | Consolidate notebooks 01/02/03 từ phase cũ | 6 | 1 | 70% | 2 | **2.1** | P2 |
| WS7 | dbt_datathon scaffold (staging/intermediate/marts/tests) | 5 | 1 | 60% | 3 | **1.0** | P2 |
| WS8 | infra scaffold (spark/iceberg/trino/minio/cloudbeaver + docker-compose + jobs) | 4 | 0.5 | 50% | 4 | **0.25** | P3 |

Thứ tự làm: **WS1 → WS2 → (WS3, WS5 song song) → WS4 → WS6 → WS7 → WS8**.

---

## 5. Chia việc theo agent (de/da/ds/ba/pm/tester)

| Agent | Workstream | Deliverable file |
|---|---|---|
| **pm** | WS1, WS2 | cây thư mục, `Makefile`, `pyproject.toml`, `README.md`, `LICENSE`, `.env.example`, cập nhật `.gitignore`, `PROGRESS.md` |
| **de** | WS1(move CSV), WS3(config/schema/ingestion/quality), WS7, WS8 | `src/datathon/config.py, ingestion.py, schema.py, quality.py`; `jobs/*`; `infra/*`; `dbt_datathon/models/staging`; `docker-compose.yml` |
| **ds** | WS3(features/models/backtest/submission), WS6(nb03) | `src/datathon/features.py, models.py, backtest.py, submission.py`; `notebooks/03_forecasting_colab.ipynb` |
| **da** | WS6(nb01,nb02), WS7(marts) | `notebooks/01_data_quality.ipynb, 02_eda.ipynb`; `dbt_datathon/models/{intermediate,marts}` |
| **ba** | WS5 | `data/README.md` (data dictionary từ xlsx), `.env.example` biến nghiệp vụ |
| **tester** | WS4 | `tests/test_*.py`, `.github/workflows/ci.yml`, `dbt_datathon/tests`, `data/sample/` (verify CI chạy) |

Phụ thuộc: pm(WS1) chặn tất cả. de(WS3 config) chặn ds/da port code. tester(WS4) sau khi src/ có hàm.

---

## 6. Migration steps (thứ tự an toàn, không mất việc)

1. **Branch** `chore/restructure-lakehouse` từ main.
2. pm: tạo scaffold folder rỗng + `.gitkeep` (chưa move gì). Commit 1.
3. pm: `git mv EDA_Insight → docs/analysis/`, `tài liệu → docs/brief/`, giữ nguyên nội dung. Commit 2.
4. de: `git mv data/*.csv → data/raw/`; sửa path trong script (config.py trỏ 1 chỗ). `git rm --cached data/raw/*.csv`; thêm `.gitignore`. Commit 3. ⚠ verify 1 script chạy lại OK trước commit.
5. ba/tester: sinh `data/sample/*.csv` (head N dòng) — CHỖ NÀY được commit. Commit 4.
6. pm: `pyproject.toml`, `Makefile`, `LICENSE`, `.env.example`, README rewrite. Commit 5.
7. de+ds: port `src/datathon/*` (import lại logic phase, không viết lại thuật toán). Commit 6.
8. tester: `tests/*` + `ci.yml` chạy trên `data/sample`. Commit 7.
9. da+ds: consolidate `notebooks/*`. Commit 8.
10. de/da: scaffold `infra/`, `jobs/`, `dbt_datathon/` (D1 quyết mức độ). Commit 9.
11. PR → review → merge.

---

## 7. Definition of Done

- **Dev**: cây thư mục khớp target 100% node; `python -c "import datathon"` OK; 0 hardcode absolute path (dùng `config.py`).
- **QA/tester**: `pytest` xanh trên `data/sample`; `ci.yml` pass trên push; 4 file test tồn tại & assert thật.
- **Data**: `data/raw` gitignored + `.gitkeep`; `data/sample` commit được & nhỏ (<1MB); `data/README.md` có data dictionary 15 bảng.
- **Analysis bảo toàn**: mọi file `EDA_Insight` cũ còn nguyên trong `docs/analysis` (diff = 0 nội dung, chỉ đổi path).
- **Reproducible**: `make setup && make test` chạy từ clone sạch.
- **Demo**: chạy `make forecast` (hoặc script tương đương) ra `submission.csv` khớp format `sample_submission.csv`.

---

## 8. Release plan

- Target date: **giả định** +3 ngày làm việc cho D1=A (scaffold). D1=C thì +2 tuần.
- In scope (v1): WS1–WS6 (struct + move + src port + tests + notebooks).
- Out scope (v1): infra chạy thật (Spark/Trino/MinIO), dbt chạy thật (WS7–8 chỉ scaffold).
- Testing window: sau WS4, chạy CI trên sample 1 ngày trước merge.
- Success criteria: DoD mục 7 đạt hết + PR review pass + forecast Phần B ra số KHÔNG đổi so với `phase9` committed baseline (regression check).

---

## 9. Rủi ro & trade-off (nói thẳng)

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Move data phá path → script chết | Cao | config.py 1 chỗ; verify từng commit; recent commit đã từng fix path → cẩn thận |
| `git rm --cached` không giảm size history | TB | mặc định giữ history; muốn nhẹ thật phải rewrite (phá clone team) — hỏi user |
| Port src/ làm sai logic model đã verify | Cao | regression: forecast_548 mới == committed baseline; không sửa thuật toán khi port |
| Full infra (D1=C) ngốn thời gian, lệch mục tiêu contest | Cao | mặc định scaffold-only |
| EDA_Insight biến mất khỏi struct | TB | archive vào docs/, không xóa |

**Trade-off chốt**: struct này tối ưu cho *kỹ thuật/production*, không cho *tốc độ thi*. Nếu deadline contest gần → làm WS1+WS2+WS5 (P0) cho đẹp cây, hoãn WS3–8. Nếu mục tiêu là portfolio/nộp code đẹp → làm hết.
