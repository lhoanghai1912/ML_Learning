"""Nguồn path DUY NHẤT cho toàn dự án. Không hardcode path CSV nơi khác.

Env:
    DATA_RAW_PATH: override thư mục raw (fallback "data/raw" tương đối PROJECT_ROOT).
"""

from __future__ import annotations

import os
from pathlib import Path

# src/datathon/config.py -> src/datathon -> src -> PROJECT_ROOT
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

DATA_RAW: Path = Path(
    os.environ.get("DATA_RAW_PATH", str(PROJECT_ROOT / "data" / "raw"))
)
if not DATA_RAW.is_absolute():
    DATA_RAW = PROJECT_ROOT / DATA_RAW

DATA_SAMPLE: Path = PROJECT_ROOT / "data" / "sample"

# tên bảng -> path CSV. 14 bảng raw (không tính sample_submission nếu cần tách riêng
# nhưng theo yêu cầu M1, gộp chung 1 dict cho đủ 14 file trong data/raw/).
RAW_TABLES: dict[str, Path] = {
    "customers": DATA_RAW / "customers.csv",
    "geography": DATA_RAW / "geography.csv",
    "inventory": DATA_RAW / "inventory.csv",
    "order_items": DATA_RAW / "order_items.csv",
    "orders": DATA_RAW / "orders.csv",
    "payments": DATA_RAW / "payments.csv",
    "products": DATA_RAW / "products.csv",
    "promotions": DATA_RAW / "promotions.csv",
    "returns": DATA_RAW / "returns.csv",
    "reviews": DATA_RAW / "reviews.csv",
    "sales": DATA_RAW / "sales.csv",
    "sample_submission": DATA_RAW / "sample_submission.csv",
    "shipments": DATA_RAW / "shipments.csv",
    "web_traffic": DATA_RAW / "web_traffic.csv",
}
