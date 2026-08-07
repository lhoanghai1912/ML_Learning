"""Ingestion helpers — load raw CSV theo `config`, gắn metadata, MERGE/append theo natural key,
tách quarantine. KHÔNG bao giờ `dropna`/xóa dòng lỗi im lặng — luôn trả về để caller quarantine.

Phạm vi M4a: KHÔNG có Spark/Iceberg chạy ở đây. Các hàm thuần pandas trong file này là logic
dùng chung — job Iceberg thật (M2, `jobs/ingest_csv_to_iceberg.py`) gọi lại đúng các hàm này
(`load_raw`, `add_metadata_columns`, `merge_upsert`) khi ghi Spark/Iceberg, để tránh viết 2 lần
2 định nghĩa MERGE khác nhau.

Quy tắc bắt buộc (DE HARDENING STANDARD, RESTRUCTURE_AGENTS.md):
    - KHÔNG createOrReplace — chỉ append/MERGE theo natural key + cột updated_at.
    - 5 cột metadata bắt buộc: _ingested_at, _source_file, _source_row_number, _checksum, _batch_id.
    - Record lỗi schema -> quarantine (bảng riêng), KHÔNG drop.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pandas as pd

from datathon import schema as schema_mod
from datathon.config import RAW_TABLES


def new_batch_id() -> str:
    """1 batch_id / lần chạy ingest. Dùng chung cho mọi bảng trong cùng batch nếu truyền vào."""
    return uuid.uuid4().hex


def _row_checksum(row: pd.Series) -> str:
    """Hash toàn bộ giá trị business columns của 1 dòng — phát hiện thay đổi khi MERGE lại."""
    payload = "|".join("" if pd.isna(v) else str(v) for v in row)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_raw(table: str) -> pd.DataFrame:
    """Đọc 1 bảng raw qua `config.RAW_TABLES`, parse cột ngày theo schema contract.

    KHÔNG gắn metadata (dùng `add_metadata_columns` riêng) — giữ hàm này thuần "đọc".
    """
    if table not in RAW_TABLES:
        raise KeyError(
            f"Bảng '{table}' không có trong config.RAW_TABLES. Bảng hợp lệ: {tuple(RAW_TABLES)}"
        )
    path = RAW_TABLES[table]
    if not path.exists():
        raise FileNotFoundError(f"Không thấy file raw cho bảng '{table}': {path}")
    df = pd.read_csv(path, low_memory=False)
    ts = schema_mod.get_schema(table)
    for col in ts.date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="%Y-%m-%d", errors="coerce")
    return df


def add_metadata_columns(df: pd.DataFrame, *, source_file: str, batch_id: str) -> pd.DataFrame:
    """Gắn 5 cột metadata bắt buộc. Trả DataFrame MỚI — không sửa `df` gốc (tránh side-effect)."""
    out = df.copy()
    out["_ingested_at"] = datetime.now(timezone.utc).isoformat()
    out["_source_file"] = source_file
    # 0-based, tính trên thứ tự dòng của df ĐANG XỬ LÝ (đúng vì CSV nguồn cố định thứ tự dòng
    # giữa các lần chạy — không sort/shuffle trước khi gọi hàm này).
    out["_source_row_number"] = range(len(out))
    business_cols = [c for c in df.columns if not str(c).startswith("_")]
    out["_checksum"] = df[business_cols].apply(_row_checksum, axis=1)
    out["_batch_id"] = batch_id
    return out


def build_order_items_line_id(df: pd.DataFrame) -> pd.Series:
    """Surrogate line ID ổn định cho `order_items`.

    (order_id, product_id) KHÔNG unique tự nhiên (16 cặp trùng — 2 dòng hàng hợp lệ khác giá/số
    lượng, xem `schema.py` docstring). Dùng (order_id, product_id, _source_row_number) làm khóa
    surrogate: ỔN ĐỊNH giữa các lần chạy vì file CSV nguồn không đổi thứ tự dòng — KHÔNG dùng
    `row_number()` tính lại sau filter/sort (sẽ đổi giá trị, phá MERGE incremental).
    """
    if "_source_row_number" not in df.columns:
        raise ValueError(
            "Cần gọi add_metadata_columns() trước build_order_items_line_id() "
            "(thiếu cột _source_row_number)."
        )
    raw_key = (
        df["order_id"].astype(str)
        + "|" + df["product_id"].astype(str)
        + "|" + df["_source_row_number"].astype(str)
    )
    return raw_key.map(lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest())


def split_valid_quarantine(
    df: pd.DataFrame, validation: schema_mod.SchemaValidationResult
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tách dòng hợp lệ / quarantine theo `SchemaValidationResult.row_valid_mask`.

    KHÔNG drop — bảng quarantine giữ NGUYÊN dòng lỗi kèm lý do, để soi lại/backfill sau.
    """
    valid = df.loc[validation.row_valid_mask].copy()
    bad = df.loc[~validation.row_valid_mask].copy()
    if len(bad):
        reasons = []
        if validation.dtype_mismatch:
            reasons.append("dtype_mismatch:" + ",".join(validation.dtype_mismatch))
        if validation.enum_violations:
            reasons.append("enum_violation:" + ",".join(validation.enum_violations))
        bad["_dq_reason"] = "; ".join(reasons) if reasons else "schema_violation"
    return valid, bad


@dataclass
class IngestResult:
    """Tương ứng 1 dòng `ops.ingest_audit` (M2 ghi thật vào Postgres/Iceberg; ở M4a chỉ trả object
    để job M2 / test dùng lại, tránh định nghĩa audit record 2 lần)."""

    table: str
    batch_id: str
    rows_in: int
    rows_valid: int
    rows_quarantined: int
    ts: str
    status: str  # "OK" | "QUARANTINED" | "FAILED"
    quarantine_reasons: dict[str, int] = field(default_factory=dict)


def ingest_table(table: str, batch_id: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame, IngestResult]:
    """Load + gắn metadata + validate schema (chiều 2) + tách quarantine cho 1 bảng.

    Trả (valid_df, quarantine_df, IngestResult). KHÔNG ghi Iceberg thật — job M2 gọi hàm này rồi
    tự MERGE INTO Iceberg + ghi `ops.ingest_audit`/`raw._quarantine_<table>`.
    """
    batch_id = batch_id or new_batch_id()
    df = load_raw(table)
    df = add_metadata_columns(df, source_file=str(RAW_TABLES[table]), batch_id=batch_id)
    if table == "order_items":
        df[schema_mod.ORDER_ITEMS_SURROGATE_KEY] = build_order_items_line_id(df)

    validation = schema_mod.validate_schema(df, table)
    valid, bad = split_valid_quarantine(df, validation)

    if not validation.ok:
        status = "FAILED"  # thiếu cột kỳ vọng — lỗi cấu trúc, không dùng được bảng
    elif len(bad):
        status = "QUARANTINED"
    else:
        status = "OK"

    result = IngestResult(
        table=table,
        batch_id=batch_id,
        rows_in=len(df),
        rows_valid=len(valid),
        rows_quarantined=len(bad),
        ts=datetime.now(timezone.utc).isoformat(),
        status=status,
        quarantine_reasons={"schema_violation": len(bad)} if len(bad) else {},
    )
    return valid, bad, result


def merge_upsert(
    existing: pd.DataFrame | None,
    incoming: pd.DataFrame,
    natural_key: list[str],
    updated_at_col: str = "_ingested_at",
) -> pd.DataFrame:
    """Mô phỏng `MERGE INTO ... ON natural_key` ở tầng pandas (KHÔNG createOrReplace).

    Idempotent: gọi 2 lần với CÙNG `incoming` -> kết quả không đổi (không nhân đôi dòng) —
    dòng trùng `natural_key` giữ bản ghi có `updated_at_col` MỚI NHẤT (tie-break: `incoming`
    luôn thắng `existing` cùng timestamp, vì nối sau + `keep="last"`).

    natural_key PHẢI unique thật trên `incoming` (vd `order_id`, hoặc
    `schema.ORDER_ITEMS_SURROGATE_KEY` cho order_items — KHÔNG dùng (order_id, product_id) trần).
    """
    if existing is None or existing.empty:
        return incoming.drop_duplicates(subset=natural_key, keep="last").reset_index(drop=True)
    combined = pd.concat([existing, incoming], ignore_index=True)
    combined = combined.sort_values(updated_at_col, kind="stable")
    combined = combined.drop_duplicates(subset=natural_key, keep="last")
    return combined.reset_index(drop=True)
