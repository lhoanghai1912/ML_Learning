"""Sinh + validate forecast 548 ngày (Revenue, COGS) đúng format `sample_submission.csv`.

Port từ code phase cũ (nhánh `feat/phase8-model`, xem `.process_status/M4b.md`
mục "Nguồn port"):
    - `EDA_Insight/phase8_model/build_model.py`        (block SAVE forecast_548.csv)
    - `EDA_Insight/phase9_validation/t91_format_check.py` (check format độc lập)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from datathon import config
from datathon.features import load_forecast_features, load_train_features
from datathon.models import FINAL_CONFIG, fit_all, predict_all

SUBMISSION_COLUMNS: list[str] = ["Date", "Revenue", "COGS"]
EXPECTED_ROWS = 548


def build_submission(config_map: dict[str, dict] | None = None) -> pd.DataFrame:
    """Fit `models.FINAL_CONFIG` (hoặc `config_map` truyền vào) trên FULL
    train (`features.load_train_features()`), forecast 548 ngày
    (`features.load_forecast_features()`). Trả DataFrame đúng cột/format
    `sample_submission.csv`, đã validate cứng (raise nếu sai)."""
    train = load_train_features()
    forecast_cal = load_forecast_features()
    forecasters = fit_all(train, config_map or FINAL_CONFIG)
    pred = predict_all(forecasters, forecast_cal)

    out = pd.DataFrame({
        "Date": pred["Date"].dt.strftime("%Y-%m-%d"),
        "Revenue": pred["Revenue"].round(2),
        "COGS": pred["COGS"].round(2),
    })
    validate_submission(out)
    return out


def validate_submission(sub: pd.DataFrame, sample_path: Path | None = None) -> list[tuple[str, bool, str]]:
    """Đối chiếu format với `sample_submission.csv` (port rút gọn từ
    `t91_format_check.py`). Check "cứng" (cột/số dòng/ngày/NaN/âm) — FAIL bất
    kỳ check nào -> raise AssertionError (không âm thầm bỏ qua). Trả list
    (tên check, pass?, chi tiết) để caller log thêm nếu cần."""
    sample = pd.read_csv(sample_path or config.RAW_TABLES["sample_submission"])
    results: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        results.append((name, bool(ok), detail))

    check("columns == [Date,Revenue,COGS]", list(sub.columns) == SUBMISSION_COLUMNS, f"got {list(sub.columns)}")
    check("row count == 548", len(sub) == EXPECTED_ROWS, f"rows={len(sub)}")
    check("row count == sample", len(sub) == len(sample), f"sub={len(sub)} sample={len(sample)}")

    dates = pd.to_datetime(sub["Date"], format="%Y-%m-%d", errors="coerce")
    check("all Date parse YYYY-MM-DD", int(dates.isna().sum()) == 0, f"unparseable={int(dates.isna().sum())}")
    check("no duplicate dates", int(sub["Date"].duplicated().sum()) == 0, "")

    sample_dates = pd.to_datetime(sample["Date"], format="%Y-%m-%d", errors="coerce")
    check("date order == sample", bool(dates.equals(sample_dates)), "elementwise date equality")

    n_nan = int(sub[["Revenue", "COGS"]].isna().sum().sum())
    check("0 NaN Revenue/COGS", n_nan == 0, f"nan={n_nan}")

    neg = int((pd.to_numeric(sub["Revenue"], errors="coerce") < 0).sum() +
               (pd.to_numeric(sub["COGS"], errors="coerce") < 0).sum())
    check("0 negative values", neg == 0, f"neg={neg}")

    failed = [r for r in results if not r[1]]
    if failed:
        raise AssertionError(f"submission format FAIL: {failed}")
    return results


def write_submission(out_path: Path | None = None) -> Path:
    """Sinh submission + ghi CSV. Mặc định `<PROJECT_ROOT>/submission.csv`."""
    sub = build_submission()
    out_path = out_path or (config.PROJECT_ROOT / "submission.csv")
    sub.to_csv(out_path, index=False)
    return out_path


if __name__ == "__main__":
    path = write_submission()
    print(f"submission.csv ghi tại: {path}")
