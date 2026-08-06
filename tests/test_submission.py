"""M5 — test_submission.py

`build_submission()`/`validate_submission()` (datathon.submission) trên `data/sample`:
đúng cột, đúng 548 dòng ngày, không NaN, không âm — VÀ chứng minh `validate_submission` thật
sự BẮT được lỗi khi format sai (không phải hàm luôn PASS)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from datathon.submission import (
    EXPECTED_ROWS,
    SUBMISSION_COLUMNS,
    build_submission,
    validate_submission,
)


@pytest.fixture(scope="module")
def sample_submission_df(sample_dir: Path) -> pd.DataFrame:
    """1 lần build cho cả module (fit LightGBM x2 target trên data/sample — ~10-15s)."""
    return build_submission()


# ---------------------------------------------------------------------------
# 1. build_submission() trên data/sample — format thật đúng sample_submission.csv
# ---------------------------------------------------------------------------


def test_build_submission_has_correct_columns(sample_submission_df: pd.DataFrame) -> None:
    assert list(sample_submission_df.columns) == SUBMISSION_COLUMNS == ["Date", "Revenue", "COGS"]


def test_build_submission_has_exactly_548_rows(sample_submission_df: pd.DataFrame) -> None:
    assert len(sample_submission_df) == EXPECTED_ROWS == 548


def test_build_submission_dates_match_sample_submission_csv_exactly(
    sample_submission_df: pd.DataFrame, sample_dir: Path
) -> None:
    sample = pd.read_csv(sample_dir / "sample_submission.csv")
    assert list(sample_submission_df["Date"]) == list(sample["Date"])
    assert not sample_submission_df["Date"].duplicated().any()


def test_build_submission_no_nan(sample_submission_df: pd.DataFrame) -> None:
    assert int(sample_submission_df[["Revenue", "COGS"]].isna().sum().sum()) == 0


def test_build_submission_no_negative_values(sample_submission_df: pd.DataFrame) -> None:
    assert (pd.to_numeric(sample_submission_df["Revenue"]) >= 0).all()
    assert (pd.to_numeric(sample_submission_df["COGS"]) >= 0).all()


def test_build_submission_passes_own_validator(sample_submission_df: pd.DataFrame) -> None:
    results = validate_submission(sample_submission_df)  # không raise = PASS
    assert all(ok for _name, ok, _detail in results)
    assert len(results) == 8  # 8 check port từ t91_format_check.py


# ---------------------------------------------------------------------------
# 2. validate_submission() — chứng minh BẮT ĐƯỢC lỗi thật (không phải luôn PASS/mock rỗng)
# ---------------------------------------------------------------------------


def _valid_sub(sample_dir: Path) -> pd.DataFrame:
    sample = pd.read_csv(sample_dir / "sample_submission.csv")
    return pd.DataFrame({
        "Date": sample["Date"],
        "Revenue": np.round(np.linspace(1000.0, 2000.0, len(sample)), 2),
        "COGS": np.round(np.linspace(800.0, 1600.0, len(sample)), 2),
    })


def test_validate_submission_catches_negative_value(sample_dir: Path) -> None:
    sub = _valid_sub(sample_dir)
    sub.loc[0, "Revenue"] = -5.0
    with pytest.raises(AssertionError, match="0 negative values"):
        validate_submission(sub, sample_path=sample_dir / "sample_submission.csv")


def test_validate_submission_catches_wrong_row_count(sample_dir: Path) -> None:
    sub = _valid_sub(sample_dir).iloc[:-1]  # thiếu 1 dòng -> 547
    with pytest.raises(AssertionError, match="row count == 548"):
        validate_submission(sub, sample_path=sample_dir / "sample_submission.csv")


def test_validate_submission_catches_nan(sample_dir: Path) -> None:
    sub = _valid_sub(sample_dir)
    sub.loc[3, "COGS"] = float("nan")
    with pytest.raises(AssertionError, match="0 NaN Revenue"):
        validate_submission(sub, sample_path=sample_dir / "sample_submission.csv")


def test_validate_submission_catches_duplicate_date(sample_dir: Path) -> None:
    sub = _valid_sub(sample_dir)
    sub.loc[1, "Date"] = sub.loc[0, "Date"]
    with pytest.raises(AssertionError, match="no duplicate dates"):
        validate_submission(sub, sample_path=sample_dir / "sample_submission.csv")


def test_validate_submission_wrong_columns_raises_keyerror_KNOWN_LIMITATION(sample_dir: Path) -> None:
    """KNOWN LIMITATION (phát hiện thật, KHÔNG PHẢI bug do M5 gây ra — báo PO/M4, M5 KHÔNG được
    sửa `src/datathon/*`): khi cột sai (thiếu/đổi tên `Revenue`/`COGS`), `validate_submission()`
    KHÔNG dừng sớm ở check "columns == [...]" (chỉ set `ok=False` rồi chạy tiếp) — dòng sau đó
    `sub[["Revenue", "COGS"]]` (check NaN) access thẳng cột đã đổi tên -> văng `KeyError` THẬT
    từ pandas, KHÔNG phải `AssertionError("submission format FAIL: ...")` như API tài liệu hoá
    (docstring: "FAIL bất kỳ check nào -> raise AssertionError"). Test này CHARACTERIZE hành vi
    HIỆN TẠI (pass = đúng như observe thật, xem `.process_status/M5.md`)."""
    sub = _valid_sub(sample_dir).rename(columns={"COGS": "Cost"})
    with pytest.raises(KeyError):
        validate_submission(sub, sample_path=sample_dir / "sample_submission.csv")


@pytest.mark.xfail(
    strict=True,
    reason=(
        "KNOWN LIMITATION đã báo PO/M4 (.process_status/M5.md): validate_submission() nên raise "
        "AssertionError('submission format FAIL: ...') rõ ràng cho cột sai, giống mọi check khác "
        "(negative/NaN/row-count/...), thay vì để lộ KeyError thô từ pandas. Nếu M4 sửa xong, "
        "test này sẽ tự PASS -> lúc đó xoá marker xfail + xoá test _KNOWN_LIMITATION ở trên."
    ),
)
def test_validate_submission_catches_wrong_columns_with_clean_assertion_error(sample_dir: Path) -> None:
    sub = _valid_sub(sample_dir).rename(columns={"COGS": "Cost"})
    with pytest.raises(AssertionError, match=r"columns == \[Date,Revenue,COGS\]"):
        validate_submission(sub, sample_path=sample_dir / "sample_submission.csv")


def test_validate_submission_catches_unparseable_date(sample_dir: Path) -> None:
    sub = _valid_sub(sample_dir)
    sub.loc[0, "Date"] = "not-a-date"
    with pytest.raises(AssertionError, match="all Date parse"):
        validate_submission(sub, sample_path=sample_dir / "sample_submission.csv")


def test_validate_submission_catches_date_order_mismatch(sample_dir: Path) -> None:
    sub = _valid_sub(sample_dir)
    sub["Date"] = sub["Date"].iloc[::-1].reset_index(drop=True)  # đảo ngược thứ tự ngày
    with pytest.raises(AssertionError, match="date order == sample"):
        validate_submission(sub, sample_path=sample_dir / "sample_submission.csv")


def test_validate_submission_accepts_valid_submission(sample_dir: Path) -> None:
    sub = _valid_sub(sample_dir)
    results = validate_submission(sub, sample_path=sample_dir / "sample_submission.csv")
    assert all(ok for _name, ok, _detail in results)
