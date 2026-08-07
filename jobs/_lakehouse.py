"""jobs/_lakehouse.py — helper dùng chung cho ingest/compact/expire (M2, ownership `jobs/*`).

KHÔNG import từ `src/datathon/*` (M4a/M4b chạy song song, tránh race/phụ thuộc chéo milestone).
Tự chứa: đọc `.env`, cấu hình bảng raw, kết nối Trino + pyiceberg REST catalog, logging JSON,
checksum, batch id, audit helpers.

Kiến trúc ghi dữ liệu (đã verify thật bằng docker thật, không suy đoán — xem .process_status/M2.md):
    1. Đọc CSV -> pandas (dtype=str, giữ nguyên fidelity) -> ép kiểu theo TABLE_SCHEMAS.
    2. Thêm 5 cột metadata (_ingested_at/_source_file/_source_row_number/_checksum/_batch_id).
    3. Tách quarantine (thiếu natural key / lỗi ép kiểu ngày-số bắt buộc) -> bảng
       `iceberg.raw._quarantine_<table>` (KHÔNG drop im).
    4. Ghi batch hợp lệ vào bảng staging `iceberg.raw._stage_<table>` qua pyiceberg
       (`overwrite()` — CHỈ staging, bảng scratch/landing buffer, KHÔNG phải bảng raw đích;
       rule "không createOrReplace" áp dụng cho bảng raw đích, không áp dụng staging buffer).
    5. MERGE INTO bảng raw đích (`iceberg.raw.<table>`) USING staging theo natural key qua Trino
       SQL — đây là bước idempotent thật sự (chạy lại không nhân đôi row đích).
    6. Ghi 1 dòng `iceberg.ops.ingest_audit` mỗi bảng mỗi lần chạy.
"""

from __future__ import annotations

import hashlib
import os
import sys
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

# ---------------------------------------------------------------------------
# .env loader (không thêm dependency python-dotenv — chỉ được sửa file trong jobs/*)
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_dotenv(path: Path | None = None) -> None:
    """Parse `.env` đơn giản (KEY=VALUE, bỏ comment/blank). Không override env đã set sẵn
    (process env luôn thắng — cho phép override lúc chạy: `FOO=bar python jobs/...`)."""
    env_path = path or (PROJECT_ROOT / ".env")
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_dotenv()


def env(name: str, default: str | None = None, required: bool = False) -> str:
    val = os.environ.get(name, default)
    if required and not val:
        raise RuntimeError(f"Missing required env var: {name} (xem .env.example)")
    return val or ""


# ---------------------------------------------------------------------------
# Logging (structured JSON — không log dữ liệu nhạy cảm: không log secret/giá trị row thô)
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(sys.stdout),
)


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)


# ---------------------------------------------------------------------------
# Batch id / checksum
# ---------------------------------------------------------------------------


def new_batch_id() -> str:
    return f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{uuid.uuid4().hex[:8]}"


def now_utc() -> datetime:
    """Naive UTC datetime (khớp Iceberg/Trino TIMESTAMP(6) không timezone)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def sql_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")


def checksum_row(values: Iterable[Any]) -> str:
    """sha256 của toàn bộ giá trị 1 dòng (theo thứ tự cột gốc) — dùng để phát hiện thay đổi
    nội dung dòng giữa các lần ingest, KHÔNG dùng làm khóa merge (trừ khi bảng không có
    natural key nào khác, xem order_items)."""
    joined = "\x1f".join("" if v is None else str(v) for v in values)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Table schema (cột raw sau khi lowercase + kiểu dữ liệu landing layer).
# Nguồn: đọc header thật `data/raw/*.csv` (xem .process_status/M2.md). Đây là contract TỐI
# THIỂU của M2 (landing); `src/datathon/schema.py` (M4a) là contract đầy đủ/authoritative cho
# 10-chiều DQ — 2 file độc lập, không import chéo (tránh race song song).
# ---------------------------------------------------------------------------

# type: "int64" | "double" | "date" | "string"
ColumnSpec = tuple  # (name, type)


@dataclass(frozen=True)
class TableSpec:
    columns: tuple  # tuple[ColumnSpec, ...] theo đúng thứ tự cột raw (đã lowercase)
    natural_key: tuple  # cột (đã lowercase, có thể gồm _source_row_number) làm khóa MERGE
    date_partition_col: str | None  # cột date để hidden-partition months(<col>); None = bỏ qua
    partition_fallback_ingested_at: bool = False  # bảng thiếu cột date -> partition theo _ingested_at


TABLE_SPECS: dict[str, TableSpec] = {
    "customers": TableSpec(
        columns=(
            ("customer_id", "int64"),
            ("zip", "string"),
            ("city", "string"),
            ("signup_date", "date"),
            ("gender", "string"),
            ("age_group", "string"),
            ("acquisition_channel", "string"),
        ),
        natural_key=("customer_id",),
        date_partition_col=None,
    ),
    "geography": TableSpec(
        columns=(
            ("zip", "string"),
            ("city", "string"),
            ("region", "string"),
            ("district", "string"),
        ),
        natural_key=("zip",),
        date_partition_col=None,
    ),
    "inventory": TableSpec(
        columns=(
            ("snapshot_date", "date"),
            ("product_id", "int64"),
            ("stock_on_hand", "int64"),
            ("units_received", "int64"),
            ("units_sold", "int64"),
            ("stockout_days", "int64"),
            ("days_of_supply", "double"),
            ("fill_rate", "double"),
            ("stockout_flag", "int64"),
            ("overstock_flag", "int64"),
            ("reorder_flag", "int64"),
            ("sell_through_rate", "double"),
            ("product_name", "string"),
            ("category", "string"),
            ("segment", "string"),
            ("year", "int64"),
            ("month", "int64"),
        ),
        natural_key=("snapshot_date", "product_id"),
        date_partition_col=None,  # 60247 dòng — dưới ngưỡng, tránh partition quá nhỏ
    ),
    "order_items": TableSpec(
        columns=(
            ("order_id", "int64"),
            ("product_id", "int64"),
            ("quantity", "int64"),
            ("unit_price", "double"),
            ("discount_amount", "double"),
            ("promo_id", "string"),
            ("promo_id_2", "string"),
        ),
        # ⚠ order_items KHÔNG có line-id tự nhiên. Dùng _source_row_number làm tie-breaker —
        # AN TOÀN ở raw layer vì CSV nguồn là file tĩnh: cùng file -> cùng thứ tự dòng -> cùng
        # _source_row_number ở MỌI lần ingest lại (khác với row_number() tính lại trên 1 SQL
        # query không đảm bảo thứ tự — đó là điều RESTRUCTURE_AGENTS.md cảnh báo cho M3
        # intermediate, không áp dụng ở đây). M3 intermediate vẫn phải tự tạo surrogate key
        # nghiệp vụ riêng theo đúng chỉ dẫn của nó.
        natural_key=("order_id", "product_id", "_source_row_number"),
        date_partition_col=None,
    ),
    "orders": TableSpec(
        columns=(
            ("order_id", "int64"),
            ("order_date", "date"),
            ("customer_id", "int64"),
            ("zip", "string"),
            ("order_status", "string"),
            ("payment_method", "string"),
            ("device_type", "string"),
            ("order_source", "string"),
        ),
        natural_key=("order_id",),
        date_partition_col="order_date",
    ),
    "payments": TableSpec(
        columns=(
            ("order_id", "int64"),
            ("payment_method", "string"),
            ("payment_value", "double"),
            ("installments", "int64"),
        ),
        natural_key=("order_id",),
        # ⚠ payments KHÔNG có cột date riêng (raw không có, không tự bịa để giữ nguyên raw).
        # Hidden-partition theo tháng _ingested_at thay thế — join lấy order_date thật ở M3 staging.
        date_partition_col=None,
        partition_fallback_ingested_at=True,
    ),
    "products": TableSpec(
        columns=(
            ("product_id", "int64"),
            ("product_name", "string"),
            ("category", "string"),
            ("segment", "string"),
            ("size", "string"),
            ("color", "string"),
            ("price", "double"),
            ("cogs", "double"),
        ),
        natural_key=("product_id",),
        date_partition_col=None,
    ),
    "promotions": TableSpec(
        columns=(
            ("promo_id", "string"),
            ("promo_name", "string"),
            ("promo_type", "string"),
            ("discount_value", "double"),
            ("start_date", "date"),
            ("end_date", "date"),
            ("applicable_category", "string"),
            ("promo_channel", "string"),
            ("stackable_flag", "int64"),
            ("min_order_value", "double"),
        ),
        natural_key=("promo_id",),
        date_partition_col=None,  # 49 dòng — quá nhỏ
    ),
    "returns": TableSpec(
        columns=(
            ("return_id", "string"),
            ("order_id", "int64"),
            ("product_id", "int64"),
            ("return_date", "date"),
            ("return_reason", "string"),
            ("return_quantity", "int64"),
            ("refund_amount", "double"),
        ),
        natural_key=("return_id",),
        date_partition_col=None,  # 39939 dòng — dưới ngưỡng
    ),
    "reviews": TableSpec(
        columns=(
            ("review_id", "string"),
            ("order_id", "int64"),
            ("product_id", "int64"),
            ("customer_id", "int64"),
            ("review_date", "date"),
            ("rating", "int64"),
            ("review_title", "string"),
        ),
        natural_key=("review_id",),
        date_partition_col="review_date",
    ),
    "sales": TableSpec(
        columns=(
            ("date", "date"),
            ("revenue", "double"),
            ("cogs", "double"),
        ),
        natural_key=("date",),
        date_partition_col="date",
    ),
    "sample_submission": TableSpec(
        columns=(
            ("date", "date"),
            ("revenue", "double"),
            ("cogs", "double"),
        ),
        natural_key=("date",),
        date_partition_col=None,  # template 548 dòng, không phải fact lớn
    ),
    "shipments": TableSpec(
        columns=(
            ("order_id", "int64"),
            ("ship_date", "date"),
            ("delivery_date", "date"),
            ("shipping_fee", "double"),
        ),
        natural_key=("order_id",),
        date_partition_col="ship_date",
    ),
    "web_traffic": TableSpec(
        columns=(
            ("date", "date"),
            ("sessions", "int64"),
            ("unique_visitors", "int64"),
            ("page_views", "int64"),
            ("bounce_rate", "double"),
            ("avg_session_duration_sec", "double"),
            ("traffic_source", "string"),
        ),
        natural_key=("date",),
        date_partition_col=None,  # 3652 dòng — nhỏ
    ),
}

METADATA_COLUMNS: tuple = (
    ("_ingested_at", "timestamp"),
    ("_source_file", "string"),
    ("_source_row_number", "int64"),
    ("_checksum", "string"),
    ("_batch_id", "string"),
)

_TRINO_TYPE = {
    "int64": "BIGINT",
    "double": "DOUBLE",
    "date": "DATE",
    "string": "VARCHAR",
    "timestamp": "TIMESTAMP(6)",
}


def trino_type(t: str) -> str:
    return _TRINO_TYPE[t]


# ---------------------------------------------------------------------------
# Connections
# ---------------------------------------------------------------------------


def get_trino_conn():
    import trino

    return trino.dbapi.connect(
        host=env("TRINO_HOST", "localhost"),
        port=int(env("TRINO_PORT", "8080")),
        user="datathon_ingest",
        catalog="iceberg",
        schema="raw",
    )


def get_pyiceberg_catalog():
    from pyiceberg.catalog import load_catalog

    return load_catalog(
        "iceberg",
        **{
            "type": "rest",
            "uri": env("ICEBERG_REST_URI", "http://localhost:8181"),
            "s3.endpoint": env("MINIO_ENDPOINT", "http://localhost:9000"),
            "s3.access-key-id": env("MINIO_ROOT_USER", required=True),
            "s3.secret-access-key": env("MINIO_ROOT_PASSWORD", required=True),
            "s3.region": env("AWS_REGION", "us-east-1"),
            "s3.force-virtual-addressing": "false",
        },
    )


def trino_execute(cur, sql: str) -> None:
    cur.execute(sql)
    cur.fetchall()


def ensure_namespaces(cur) -> None:
    trino_execute(cur, "CREATE SCHEMA IF NOT EXISTS iceberg.raw")
    trino_execute(cur, "CREATE SCHEMA IF NOT EXISTS iceberg.ops")


AUDIT_DDL = """
CREATE TABLE IF NOT EXISTS iceberg.ops.ingest_audit (
    batch_id varchar,
    table_name varchar,
    rows_in bigint,
    rows_ingested bigint,
    rows_quarantined bigint,
    started_at timestamp(6),
    finished_at timestamp(6),
    status varchar,
    source_file varchar,
    message varchar
) WITH (format = 'PARQUET')
"""


def ensure_audit_table(cur) -> None:
    trino_execute(cur, AUDIT_DDL)


def write_audit_row(
    cur,
    *,
    batch_id: str,
    table_name: str,
    rows_in: int,
    rows_ingested: int,
    rows_quarantined: int,
    started_at: datetime,
    finished_at: datetime,
    status: str,
    source_file: str,
    message: str = "",
) -> None:
    sql = (
        "INSERT INTO iceberg.ops.ingest_audit "
        "(batch_id, table_name, rows_in, rows_ingested, rows_quarantined, started_at, "
        "finished_at, status, source_file, message) VALUES ("
        f"'{batch_id}', '{table_name}', {rows_in}, {rows_ingested}, {rows_quarantined}, "
        f"TIMESTAMP '{sql_timestamp(started_at)}', TIMESTAMP '{sql_timestamp(finished_at)}', "
        f"'{status}', '{_sql_escape(source_file)}', '{_sql_escape(message)}')"
    )
    trino_execute(cur, sql)


def _sql_escape(s: str) -> str:
    return (s or "").replace("'", "''")
