#!/usr/bin/env python3
"""jobs/ingest_csv_to_iceberg.py — Ingest 14 CSV raw -> Iceberg (MERGE theo natural key,
idempotent — KHÔNG createOrReplace trên bảng raw đích).

Chạy: `python jobs/ingest_csv_to_iceberg.py [--tables sales,orders] [--only-quarantine-check]`
Cần: docker compose up (postgres, minio, mc, iceberg-rest, trino) healthy; `.env` đã điền.

Xem `jobs/_lakehouse.py` (docstring đầu file) cho kiến trúc chi tiết + bằng chứng đã verify thật.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import _lakehouse as lh

from datathon.config import RAW_TABLES

log = lh.get_logger("ingest")

_ARROW_TYPE = {
    "int64": pa.int64(),
    "double": pa.float64(),
    "date": pa.date32(),
    "string": pa.string(),
    "timestamp": pa.timestamp("us"),
}


def _to_int_or_none(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return int(v)


def _to_float_or_none(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return float(v)


def _to_date_or_none(v):
    if v is None or pd.isna(v):
        return None
    return v.date() if hasattr(v, "date") else v


def _to_str_or_none(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return str(v)


def build_arrow_array(series: pd.Series, ctype: str):
    if ctype == "int64":
        return pa.array([_to_int_or_none(v) for v in series], type=pa.int64())
    if ctype == "double":
        return pa.array([_to_float_or_none(v) for v in series], type=pa.float64())
    if ctype == "date":
        return pa.array([_to_date_or_none(v) for v in series], type=pa.date32())
    if ctype == "timestamp":
        return pa.array(series.tolist(), type=pa.timestamp("us"))
    return pa.array([_to_str_or_none(v) for v in series], type=pa.string())


def read_and_cast(table: str, path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Đọc CSV -> ép kiểu theo TABLE_SPECS. Trả (good_df, quarantine_df).
    good_df: cột gốc đã ép kiểu (python-native trong object dtype khi cần) + _source_row_number.
    quarantine_df: cột gốc dạng string + _reason (lý do quarantine, có thể ghép nhiều lỗi)."""
    spec = lh.TABLE_SPECS[table]
    col_names = [c for c, _ in spec.columns]

    raw = pd.read_csv(
        path,
        dtype=str,
        keep_default_na=True,
        na_values=["", "NA", "NaN", "nan", "null", "NULL"],
    )
    raw.columns = [c.strip().lower() for c in raw.columns]

    missing_cols = [c for c in col_names if c not in raw.columns]
    if missing_cols:
        raise RuntimeError(f"{table}: thiếu cột {missing_cols} trong {path} (schema contract lệch)")

    raw = raw[col_names].reset_index(drop=True)
    raw.insert(0, "_source_row_number", range(1, len(raw) + 1))

    checksums = raw[col_names].apply(lambda r: lh.checksum_row(r.tolist()), axis=1)

    bad_mask = pd.Series(False, index=raw.index)
    reasons = pd.Series("", index=raw.index)

    key_cols = [c for c in spec.natural_key if c != "_source_row_number"]
    for kc in key_cols:
        null_key = raw[kc].isna()
        if null_key.any():
            reasons = reasons.mask(null_key, reasons + f"null_key:{kc};")
            bad_mask |= null_key

    typed = raw.copy()
    for col, ctype in spec.columns:
        if ctype == "int64" or ctype == "double":
            coerced = pd.to_numeric(typed[col], errors="coerce")
            fail = coerced.isna() & typed[col].notna()
            typed[col] = coerced
        elif ctype == "date":
            coerced = pd.to_datetime(typed[col], errors="coerce")
            fail = coerced.isna() & typed[col].notna()
            typed[col] = coerced
        else:
            fail = pd.Series(False, index=typed.index)
        if fail.any():
            reasons = reasons.mask(fail, reasons + f"bad_{ctype}:{col};")
            bad_mask |= fail

    typed["_checksum"] = checksums
    typed["_reason"] = reasons

    good = typed.loc[~bad_mask].drop(columns=["_reason"]).copy()
    quarantine = raw.loc[bad_mask].copy()
    quarantine["_reason"] = reasons.loc[bad_mask]
    quarantine["_checksum"] = checksums.loc[bad_mask]
    return good, quarantine


def create_target_table_ddl(table: str) -> str:
    spec = lh.TABLE_SPECS[table]
    cols = list(spec.columns) + list(lh.METADATA_COLUMNS)
    col_defs = ",\n    ".join(f'"{c}" {lh.trino_type(t)}' for c, t in cols)
    partition_col = spec.date_partition_col
    if partition_col is None and spec.partition_fallback_ingested_at:
        partition_clause = ", partitioning = ARRAY['month(_ingested_at)']"
    elif partition_col is not None:
        partition_clause = f", partitioning = ARRAY['month({partition_col})']"
    else:
        partition_clause = ""
    return (
        f'CREATE TABLE IF NOT EXISTS iceberg.raw."{table}" (\n    {col_defs}\n) '
        f"WITH (format = 'PARQUET'{partition_clause})"
    )


def create_quarantine_table_ddl(table: str) -> str:
    spec = lh.TABLE_SPECS[table]
    cols = [(c, "string") for c, _ in spec.columns]  # quarantine giữ nguyên string gốc
    cols += [("_reason", "string")] + list(lh.METADATA_COLUMNS)  # _checksum đã có trong METADATA_COLUMNS
    col_defs = ",\n    ".join(f'"{c}" {lh.trino_type(t)}' for c, t in cols)
    return (
        f'CREATE TABLE IF NOT EXISTS iceberg.raw."_quarantine_{table}" (\n    {col_defs}\n) '
        "WITH (format = 'PARQUET')"
    )


def to_arrow_for_stage(df: pd.DataFrame, table: str, batch_id: str, source_file: str, ingested_at) -> pa.Table:
    spec = lh.TABLE_SPECS[table]
    arrays, names = [], []
    for col, ctype in spec.columns:
        arrays.append(build_arrow_array(df[col], ctype))
        names.append(col)
    n = len(df)
    arrays += [
        pa.array([ingested_at] * n, type=pa.timestamp("us")),
        pa.array([source_file] * n, type=pa.string()),
        build_arrow_array(df["_source_row_number"], "int64"),
        build_arrow_array(df["_checksum"], "string"),
        pa.array([batch_id] * n, type=pa.string()),
    ]
    names += [c for c, _ in lh.METADATA_COLUMNS]
    return pa.Table.from_arrays(arrays, names=names)


def to_arrow_for_quarantine(df: pd.DataFrame, table: str, batch_id: str, source_file: str, ingested_at) -> pa.Table:
    spec = lh.TABLE_SPECS[table]
    arrays, names = [], []
    for col, _ in spec.columns:
        arrays.append(build_arrow_array(df[col], "string"))
        names.append(col)
    arrays += [build_arrow_array(df["_reason"], "string")]
    names += ["_reason"]
    n = len(df)
    arrays += [
        pa.array([ingested_at] * n, type=pa.timestamp("us")),
        pa.array([source_file] * n, type=pa.string()),
        build_arrow_array(df["_source_row_number"], "int64"),
        build_arrow_array(df["_checksum"], "string"),
        pa.array([batch_id] * n, type=pa.string()),
    ]
    names += [c for c, _ in lh.METADATA_COLUMNS]
    return pa.Table.from_arrays(arrays, names=names)


def merge_sql(table: str) -> str:
    spec = lh.TABLE_SPECS[table]
    all_cols = [c for c, _ in spec.columns] + [c for c, _ in lh.METADATA_COLUMNS]
    key_cols = list(spec.natural_key)
    # "=" thường (không phải IS NOT DISTINCT FROM) — AN TOÀN vì key_cols đã bị lọc null ra
    # quarantine từ trước (read_and_cast), và bench thật cho thấy IS NOT DISTINCT FROM ép Trino
    # dùng nested-loop join thay vì hash-join -> chậm O(n^2) (121930 dòng ~ chạy >3 phút; đổi
    # sang "=" xong tức thì). Xem .process_status/M2.md phần perf.
    on_clause = " AND ".join(f't."{k}" = s."{k}"' for k in key_cols)
    update_cols = [c for c in all_cols if c not in key_cols]
    update_set = ", ".join(f'"{c}" = s."{c}"' for c in update_cols)
    insert_cols = ", ".join(f'"{c}"' for c in all_cols)
    insert_vals = ", ".join(f's."{c}"' for c in all_cols)
    return (
        f'MERGE INTO iceberg.raw."{table}" t USING iceberg.raw."_stage_{table}" s\n'
        f"ON {on_clause}\n"
        # Chỉ UPDATE khi nội dung dòng thật sự đổi (_checksum khác) — tránh rewrite toàn bộ
        # data file khi chạy lại với dữ liệu KHÔNG đổi (COW rewrite rất chậm nếu update mọi
        # dòng dù giá trị y hệt). Đây chính là phần làm MERGE idempotent-và-rẻ.
        f'WHEN MATCHED AND t."_checksum" != s."_checksum" THEN UPDATE SET {update_set}\n'
        f"WHEN NOT MATCHED THEN INSERT ({insert_cols}) VALUES ({insert_vals})"
    )


def ingest_table(table: str, tables_to_run: set | None = None) -> dict:
    if tables_to_run and table not in tables_to_run:
        return {}
    path = RAW_TABLES[table]
    if not path.exists():
        raise FileNotFoundError(f"{table}: {path} không tồn tại")

    batch_id = lh.new_batch_id()
    started_at = lh.now_utc()
    log.info("ingest_start", table=table, batch_id=batch_id, source_file=str(path))

    good, quarantine = read_and_cast(table, path)
    ingested_at = lh.now_utc()

    catalog = lh.get_pyiceberg_catalog()
    conn = lh.get_trino_conn()
    cur = conn.cursor()
    lh.ensure_namespaces(cur)
    lh.ensure_audit_table(cur)
    lh.trino_execute(cur, create_target_table_ddl(table))
    lh.trino_execute(cur, create_quarantine_table_ddl(table))

    rows_ingested = 0
    rows_quarantined = 0
    status = "SUCCESS"
    message = ""

    try:
        if len(good) > 0:
            stage_arrow = to_arrow_for_stage(good, table, batch_id, str(path), ingested_at)
            stage_table = catalog.create_table_if_not_exists(
                ("raw", f"_stage_{table}"), schema=stage_arrow.schema
            )
            # Staging = scratch/landing buffer (KHÔNG phải bảng raw đích) -> overwrite hợp lệ,
            # không vi phạm rule "no createOrReplace" (rule đó áp dụng cho bảng raw._<table> đích).
            stage_table.overwrite(stage_arrow)
            lh.trino_execute(cur, merge_sql(table))
            rows_ingested = len(good)

        if len(quarantine) > 0:
            q_arrow = to_arrow_for_quarantine(quarantine, table, batch_id, str(path), ingested_at)
            q_iceberg_table = catalog.load_table(("raw", f"_quarantine_{table}"))
            q_iceberg_table.append(q_arrow)
            rows_quarantined = len(quarantine)
            log.warning(
                "ingest_quarantine",
                table=table,
                batch_id=batch_id,
                rows_quarantined=rows_quarantined,
            )
    except Exception as exc:
        status = "FAILED"
        message = str(exc)[:500]
        raise
    finally:
        finished_at = lh.now_utc()
        lh.write_audit_row(
            cur,
            batch_id=batch_id,
            table_name=table,
            rows_in=len(good) + len(quarantine),
            rows_ingested=rows_ingested,
            rows_quarantined=rows_quarantined,
            started_at=started_at,
            finished_at=finished_at,
            status=status,
            source_file=str(path),
            message=message,
        )
        cur.close()
        conn.close()

    log.info(
        "ingest_done",
        table=table,
        batch_id=batch_id,
        rows_ingested=rows_ingested,
        rows_quarantined=rows_quarantined,
        status=status,
    )
    return {
        "table": table,
        "batch_id": batch_id,
        "rows_ingested": rows_ingested,
        "rows_quarantined": rows_quarantined,
        "status": status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables", default="", help="CSV tên bảng, rỗng = tất cả 14 bảng")
    args = parser.parse_args()

    tables_to_run = {t.strip() for t in args.tables.split(",") if t.strip()} or None
    order = list(lh.TABLE_SPECS.keys())
    results = []
    for table in order:
        if tables_to_run and table not in tables_to_run:
            continue
        results.append(ingest_table(table, tables_to_run))

    log.info("ingest_all_done", n_tables=len(results))
    for r in results:
        print(r)


if __name__ == "__main__":
    main()
