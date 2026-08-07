#!/usr/bin/env python3
"""jobs/expire_snapshots.py — Expire Iceberg snapshot cũ theo retention (kiểm soát small-file +
metadata phình to). Retention mặc định `SNAPSHOT_RETENTION_DAYS=7` (đổi qua `.env`).

Dùng Trino `ALTER TABLE ... EXECUTE expire_snapshots(retention_threshold => '<N>d')` — đã verify
chạy thật OK trên Trino 470 (xem `.process_status/M2.md`). Trino ép tối thiểu 7 ngày retention
mặc định (`iceberg.expire-snapshots.min-retention`) — nếu cần retention ngắn hơn cho demo/test,
đổi thêm property đó trong `infra/trino/etc/catalog/iceberg.properties` (KHÔNG đổi ngầm ở đây).

Chạy: `python jobs/expire_snapshots.py [--tables sales,orders] [--retention-days 7]`
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import _lakehouse as lh

log = lh.get_logger("expire_snapshots")


def expire_table(cur, table: str, retention_days: int) -> None:
    log.info("expire_start", table=table, retention_days=retention_days)
    lh.trino_execute(
        cur,
        f'ALTER TABLE iceberg.raw."{table}" EXECUTE expire_snapshots(retention_threshold => \'{retention_days}d\')',
    )
    log.info("expire_done", table=table, retention_days=retention_days)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables", default="", help="CSV tên bảng, rỗng = tất cả bảng trong TABLE_SPECS")
    parser.add_argument(
        "--retention-days",
        type=int,
        default=int(lh.env("SNAPSHOT_RETENTION_DAYS", "7")),
        help="Giữ snapshot trong N ngày gần nhất, expire snapshot cũ hơn",
    )
    args = parser.parse_args()

    tables = [t.strip() for t in args.tables.split(",") if t.strip()] or list(lh.TABLE_SPECS.keys())

    conn = lh.get_trino_conn()
    cur = conn.cursor()
    try:
        for table in tables:
            try:
                expire_table(cur, table, args.retention_days)
            except Exception as exc:  # noqa: BLE001 — log lỗi từng bảng, tiếp tục bảng khác
                log.error("expire_failed", table=table, error=str(exc)[:500])
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
