# Vin Datathon 2026

Dự án phân tích dữ liệu + dự báo cho cuộc thi Vin Datathon 2026. Bộ dữ liệu mô phỏng một sàn thương mại điện tử Việt Nam, trải dài 11 năm (04/07/2012 – 31/12/2022), gồm 15 bảng (đơn hàng, khách hàng, sản phẩm, thanh toán, khuyến mãi, tồn kho, traffic web...).

Team: Hải, Hoàng, Đăng.

## Đề bài

Xem chi tiết tại [`docs/brief/Đề bài1.docx`](docs/brief/Đề%20bài1.docx) và data dictionary tại [`docs/brief/data_dictionary.xlsx`](docs/brief/data_dictionary.xlsx). Tóm tắt:

- **Phần A — Dashboard & Analysis**: phân tích revenue/profit, RFM segmentation, cohort retention, marketing channels. Mỗi mảng đi đủ 4 tầng **Descriptive → Diagnostic → Predictive → Prescriptive**, chốt bằng đề xuất hành động định lượng.
- **Phần B — Forecast**: dự báo **Revenue** và **COGS** cho 548 ngày kế tiếp (01/01/2023 – 01/07/2024), nộp theo format `data/raw/sample_submission.csv`.
- **Liên kết A→B**: insight từ Phần A (xu hướng doanh thu, mùa vụ, margin theo quý) được dùng làm giả định thiết kế model cho Phần B.

### Điểm dữ liệu cần lưu ý

- `sales.csv` chứa `Revenue`/`COGS` là số liệu **GROSS** — bao gồm cả đơn đã hủy, chưa trừ giảm giá. Đây là số phải dùng khi đối chiếu với target dự báo Phần B (đề bài dựa trên `sales.csv`).
- `net_revenue` (loại đơn hủy, trừ giảm giá) chỉ dùng cho phân tích góc nhìn kinh doanh ở Phần A — **không** dùng để đối chiếu forecast. Chênh lệch gross vs net ~13-24% tùy giai đoạn.
- `payments.payment_value` là giá trị tiền mặt thực nhận theo đơn (khớp 100%), dùng làm Monetary trong RFM.

## Cấu trúc thư mục (lakehouse layout)

```
.
├── data/
│   ├── raw/                     # CSV gốc — gitignored, xem data/README.md để lấy data
│   └── sample/                  # Sample nhỏ (head N dòng) commit được, dùng cho CI/test
├── infra/                       # Config hạ tầng: spark, iceberg, trino, minio, cloudbeaver
├── jobs/                        # Batch job: ingest CSV → Iceberg, compaction, expire snapshots
├── src/datathon/                # Package Python chính (config, schema, quality, features, models, backtest, submission)
├── dbt_datathon/                # dbt project trên Trino/Iceberg (staging/intermediate/marts)
├── notebooks/                   # 3 notebook chuẩn hoá: data_quality, eda, forecasting_colab
├── tests/                       # pytest — schema, no-leakage, backtest, submission format
├── docs/
│   ├── analysis/                # (cũ EDA_Insight/) toàn bộ phân tích 11 phase, giữ nguyên nội dung
│   ├── brief/                   # (cũ tài liệu/) đề bài + data dictionary gốc
│   ├── orchestrator_prompt.md   # vai trò & quy trình điều phối agent con
│   └── PROGRESS.md              # trạng thái từng giai đoạn phân tích (nguồn sự thật duy nhất)
├── .github/workflows/           # CI (lint + pytest trên data/sample)
├── docker-compose.yml           # Spark + Iceberg + Trino + MinIO + Postgres + CloudBeaver (M2)
├── pyproject.toml               # deps + build (hatchling), package = src/datathon
├── uv.lock                      # lockfile (uv)
├── Makefile
├── LICENSE
└── .env.example
```

`docs/analysis` (cũ `EDA_Insight/`) giữ đầy đủ 11 phase, mỗi phase có `data/` riêng chứa CSV trung gian do phase đó tạo ra — không sửa trực tiếp lên `data/raw/` gốc. Lineage đầy đủ ghi ở [`docs/analysis/DATA_LINEAGE.md`](docs/analysis/DATA_LINEAGE.md).

## Cài đặt & chạy

Yêu cầu: Python >= 3.9, Docker (cho infra lakehouse thật).

```sh
make setup      # uv sync (hoặc pip install -e . nếu chưa có uv)
make up          # docker compose up -d (Spark + Iceberg + Trino + MinIO + Postgres + CloudBeaver)
make ingest      # nạp data/raw/*.csv vào Iceberg (MERGE, idempotent)
make dbt         # dbt run trên Trino/Iceberg
make forecast    # sinh submission.csv (Phần B)
make sample      # sinh data/sample/*.csv từ data/raw (cho CI/test)
make lint        # ruff check
make test        # pytest
```

Dependency quản lý bằng [`uv`](https://github.com/astral-sh/uv) (`uv.lock`). Nếu môi trường không cài được `uv`, cài package bằng `pip install -e .` và tự dựng lockfile qua `pip freeze > requirements.lock`.

## Quy trình làm việc (agent-driven)

Dự án dùng Claude Code với các "agent vai trò" (de/da/ds/ba/pm/tester) chạy từng phase/milestone theo bảng phụ thuộc trong [`docs/orchestrator_prompt.md`](docs/orchestrator_prompt.md) (phase phân tích cũ) và [`RESTRUCTURE_AGENTS.md`](RESTRUCTURE_AGENTS.md) (milestone tái cấu trúc lakehouse M0–M7). Trạng thái hiện tại luôn cập nhật ở [`docs/PROGRESS.md`](docs/PROGRESS.md) (phân tích) và [`PROCESS.md`](PROCESS.md) (restructure). Đọc file tương ứng trước để biết dự án đang ở đâu.

## Đồng bộ nhiều máy

`data/raw/*.csv` đã gitignore (xem [`data/README.md`](data/README.md) cách lấy data thật); `.env` cũng gitignore — copy từ `.env.example` và điền giá trị thật, không commit. Khi clone máy mới: `make setup`, tải data vào `data/raw/`, rồi `make up && make ingest`.
