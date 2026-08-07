"""Pytest bootstrap cho M5 — toàn bộ test suite chạy trên `data/sample`
(KHÔNG cần docker/Spark/data raw thật, tổng <1MB — xem `tests/tools/generate_sample.py`).

QUAN TRỌNG: `datathon.config` đọc biến môi trường `DATA_RAW_PATH` MỘT LẦN lúc import
module (`Path(__file__)` + `os.environ.get(...)` ở top-level). Vì vậy phải set env
TRƯỚC bất kỳ `import datathon...` nào — kể cả import gián tiếp qua plugin pytest khác.
File này chạy sớm nhất (pytest luôn nạp `conftest.py` trước khi collect test module),
nên đây là điểm set duy nhất, đúng chỗ.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"

# Ép toàn bộ suite đọc data/sample (không phụ thuộc .env / máy chạy có data thật hay không).
os.environ["DATA_RAW_PATH"] = str(SAMPLE_DIR)

_SRC = str(PROJECT_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pandas as pd
import pytest

from datathon import schema as schema_mod
from datathon.config import DATA_RAW, RAW_TABLES
from datathon.ingestion import load_raw


def pytest_configure(config: pytest.Config) -> None:
    """Fail-fast rõ ràng nếu ai đó lỡ trỏ nhầm sang data/raw (test sẽ chạy chậm/khác
    hành vi mong đợi) — không âm thầm chạy sai bộ data."""
    assert DATA_RAW == SAMPLE_DIR, (
        f"datathon.config.DATA_RAW = {DATA_RAW}, kỳ vọng {SAMPLE_DIR} "
        "(conftest.py set DATA_RAW_PATH nhưng datathon đã bị import trước đó?)"
    )


@pytest.fixture(scope="session")
def sample_dir() -> Path:
    return SAMPLE_DIR


@pytest.fixture(scope="session")
def all_sample_tables() -> dict[str, pd.DataFrame]:
    """Load đủ 14 bảng `data/sample/*.csv` qua `ingestion.load_raw` (parse date theo
    schema contract thật — giống hệt pipeline production dùng)."""
    return {name: load_raw(name) for name in schema_mod.ALL_TABLES}


@pytest.fixture()
def raw_tables_paths() -> dict[str, Path]:
    return RAW_TABLES
