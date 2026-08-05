#!/usr/bin/env python3
"""jobs/compact_iceberg.py — Bảo trì Iceberg: rewrite_data_files (compaction) + rewrite_manifests.

Dùng Trino `ALTER TABLE ... EXECUTE optimize` (= rewrite_data_files, bin-pack file nhỏ) và
`ALTER TABLE ... EXECUTE optimize_manifests` (= rewrite_manifests) — đã verify chạy thật OK trên
Trino 470 + iceberg REST catalog (xem `.process_status/M2.md`). Không dùng Spark vì Trino SQL đã
đủ, đơn giản hơn, không cần thêm dependency pyspark (pyproject không có pyspark).

Chạy: `python jobs/compact_iceberg.py [--tables sales,orders] [--file-size-threshold 100MB]`
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import _lakehouse as lh

log = lh.get_logger("compact")


def compact_table(cur, table: str, file_size_threshold: str) -> None:
    log.info("compact_start", table=table)
    lh.trino_execute(
        cur,
        f'ALTER TABLE iceberg.raw."{table}" EXECUTE optimize(file_size_threshold => \'{file_size_threshold}\')',
    )
    lh.trino_execute(cur, f'ALTER TABLE iceberg.raw."{table}" EXECUTE optimize_manifests')
    log.info("compact_done", table=table)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables", default="", help="CSV tên bảng, rỗng = tất cả bảng trong TABLE_SPECS")
    parser.add_argument(
        "--file-size-threshold",
        default="128MB",
        help="File nhỏ hơn ngưỡng này mới bị rewrite (tránh compact lại file đã đủ lớn)",
    )
    args = parser.parse_args()

    tables = [t.strip() for t in args.tables.split(",") if t.strip()] or list(lh.TABLE_SPECS.keys())

    conn = lh.get_trino_conn()
    cur = conn.cursor()
    try:
        for table in tables:
            try:
                compact_table(cur, table, args.file_size_threshold)
            except Exception as exc:  # noqa: BLE001 — log lỗi từng bảng, tiếp tục bảng khác
                log.error("compact_failed", table=table, error=str(exc)[:500])
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
