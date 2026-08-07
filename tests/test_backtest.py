"""M5 — test_backtest.py

1. `calc_metrics` (WAPE/MAPE/RMSE/MAE) tính đúng — đối chiếu công thức tính tay trên fixture nhỏ.
2. `build_rolling_folds` / `_split_fold` — fold train/test KHÔNG overlap (rolling-origin theo
   thời gian, `train_fit_end = holdout_start - 1 ngày`).
3. `run_backtest` end-to-end (fit model THẬT trên fixture nhỏ) — WAPE trả ra khớp tính tay lại
   từ actual/predict của chính fold đó.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from datathon.backtest import (
    HOLDOUT_LEN,
    MIN_TRAIN_DAYS,
    _split_fold,
    build_rolling_folds,
    calc_metrics,
    run_backtest,
)
from datathon.features import build_calendar_features, build_tet_dates

# ---------------------------------------------------------------------------
# 1. calc_metrics — công thức tính tay
# ---------------------------------------------------------------------------


def test_calc_metrics_wape_matches_hand_computed_formula() -> None:
    y_true = np.array([100.0, 200.0, 300.0, 50.0])
    y_pred = np.array([110.0, 190.0, 330.0, 40.0])

    err = y_true - y_pred
    expected_wape = float(np.sum(np.abs(err)) / np.sum(np.abs(y_true)) * 100)
    expected_mape = float(np.mean(np.abs(err) / np.abs(y_true)) * 100)
    expected_rmse = float(np.sqrt(np.mean(err ** 2)))
    expected_mae = float(np.mean(np.abs(err)))

    m = calc_metrics(y_true, y_pred)

    assert m["WAPE"] == pytest.approx(expected_wape)
    assert m["MAPE"] == pytest.approx(expected_mape)
    assert m["RMSE"] == pytest.approx(expected_rmse)
    assert m["MAE"] == pytest.approx(expected_mae)
    assert m["n_zero_actual"] == 0

    # Đối chiếu 1 con số tính tay hoàn toàn độc lập (không dùng lại công thức numpy ở trên) —
    # |10|+|10|+|30|+|10| = 60 ; |100|+|200|+|300|+|50| = 650 ; WAPE = 60/650*100
    assert m["WAPE"] == pytest.approx(60.0 / 650.0 * 100.0)


def test_calc_metrics_perfect_prediction_is_zero() -> None:
    y = np.array([10.0, 20.0, 30.0])
    m = calc_metrics(y, y)
    assert m["WAPE"] == pytest.approx(0.0)
    assert m["MAPE"] == pytest.approx(0.0)
    assert m["RMSE"] == pytest.approx(0.0)
    assert m["MAE"] == pytest.approx(0.0)


def test_calc_metrics_mape_nan_when_any_actual_is_zero() -> None:
    y_true = np.array([0.0, 100.0])
    y_pred = np.array([5.0, 90.0])
    m = calc_metrics(y_true, y_pred)
    assert m["n_zero_actual"] == 1
    assert np.isnan(m["MAPE"])  # MAPE không định nghĩa được khi actual=0 -> đúng phải NaN
    # WAPE vẫn tính được (denominator = sum|actual| != 0 vì có phần tử 100)
    expected_wape = (5.0 + 10.0) / (0.0 + 100.0) * 100.0
    assert m["WAPE"] == pytest.approx(expected_wape)


# ---------------------------------------------------------------------------
# 2. build_rolling_folds / _split_fold — train/test KHÔNG overlap
# ---------------------------------------------------------------------------


def _synthetic_train_full(n_days: int = 260) -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=n_days, freq="D")
    tet = build_tet_dates(range(2019, 2022))["tet_date"]
    feat = build_calendar_features(dates, tet)
    rng = np.random.default_rng(1)
    feat["Revenue"] = 1000 + 2 * np.arange(len(feat)) + rng.normal(0, 5, len(feat))
    return feat


def test_build_rolling_folds_train_fit_end_is_exactly_holdout_start_minus_1_day() -> None:
    train_full = _synthetic_train_full(n_days=260)
    folds = build_rolling_folds(train_full, holdout_len=30, min_train_days=100)

    assert len(folds) >= 2, "cần >=2 fold để kiểm rolling-origin thật sự lùi về quá khứ"
    for f in folds:
        assert f["train_fit_end"] == f["holdout_start"] - pd.Timedelta(days=1)
        assert f["holdout_start"] <= f["holdout_end"]


def test_build_rolling_folds_no_overlap_between_train_and_holdout_via_real_split_fn() -> None:
    """Dùng ĐÚNG hàm `_split_fold` mà `run_backtest` gọi thật — không tự suy luận lại logic."""
    train_full = _synthetic_train_full(n_days=260)
    folds = build_rolling_folds(train_full, holdout_len=30, min_train_days=100)

    for f in folds:
        train_fit, holdout = _split_fold(train_full, f)
        assert len(train_fit) > 0 and len(holdout) > 0
        assert train_fit["Date"].max() < holdout["Date"].min(), (
            f"fold {f['label']}: train_fit và holdout OVERLAP thời gian -> leakage"
        )
        # không overlap tập hợp ngày (chặt hơn so sánh max/min, phòng ca không liên tục)
        assert set(train_fit["Date"]).isdisjoint(set(holdout["Date"]))


def test_build_rolling_folds_successive_holdouts_do_not_overlap() -> None:
    """Rolling-origin: fold sau lùi về quá khứ, holdout của fold N+1 phải hoàn toàn TRƯỚC
    holdout của fold N (không chồng lấn 2 lần đánh giá)."""
    train_full = _synthetic_train_full(n_days=400)
    folds = build_rolling_folds(train_full, holdout_len=30, min_train_days=100)
    assert len(folds) >= 3

    for prev, nxt in zip(folds, folds[1:]):
        assert nxt["holdout_end"] < prev["holdout_start"], (
            f"{nxt['label']} holdout_end={nxt['holdout_end']} KHÔNG < "
            f"{prev['label']} holdout_start={prev['holdout_start']} -> overlap giữa các fold"
        )


def test_build_rolling_folds_first_fold_is_main_548d_with_default_constants() -> None:
    """Xác nhận default `HOLDOUT_LEN=548`/`MIN_TRAIN_DAYS=1000` đúng như production dùng
    (fold 0 luôn label 'main_548d', đúng 548 ngày holdout cuối chuỗi)."""
    train_full = _synthetic_train_full(n_days=HOLDOUT_LEN + MIN_TRAIN_DAYS + 50)
    folds = build_rolling_folds(train_full)  # dùng default HOLDOUT_LEN/MIN_TRAIN_DAYS thật
    assert folds[0]["label"] == "main_548d"
    assert (folds[0]["holdout_end"] - folds[0]["holdout_start"]).days + 1 == HOLDOUT_LEN
    assert folds[0]["holdout_end"] == train_full["Date"].max()


def test_build_rolling_folds_stops_when_train_too_short() -> None:
    """min_train_days chặn đúng — không sinh fold nào nếu data ngắn hơn holdout+min_train."""
    train_full = _synthetic_train_full(n_days=50)
    folds = build_rolling_folds(train_full, holdout_len=30, min_train_days=100)
    assert folds == []


# ---------------------------------------------------------------------------
# 3. run_backtest end-to-end — fit THẬT (model nhanh), WAPE khớp tính tay lại
# ---------------------------------------------------------------------------


def test_run_backtest_wape_matches_manual_recompute_from_returned_predictions() -> None:
    """Chạy `run_backtest` thật (RandomForest — nhanh nhất trong 4 model) trên fixture nhỏ,
    rồi tự fit lại 1 lần nữa THỦ CÔNG (dùng `_split_fold` + `TargetForecaster` trực tiếp, KHÔNG
    gọi lại `run_backtest`) để đối chiếu WAPE — chứng minh `run_backtest` không âm thầm tính
    khác với pipeline thật."""
    from datathon.features import CALENDAR_FEATURES
    from datathon.models import TargetForecaster

    train_full = _synthetic_train_full(n_days=200)
    fold = {
        "fold": 0, "label": "tiny",
        "holdout_start": train_full["Date"].iloc[150],
        "holdout_end": train_full["Date"].iloc[159],
        "train_fit_end": train_full["Date"].iloc[149],
    }

    result = run_backtest(
        train_full, target="Revenue", tree_model="RandomForest",
        use_ensemble=False, use_quarter=False, folds=[fold],
    )
    assert len(result) == 1
    assert result.loc[0, "fold"] == "tiny"
    assert result.loc[0, "target"] == "Revenue"
    assert np.isfinite(result.loc[0, "WAPE"])
    assert result.loc[0, "WAPE"] >= 0.0

    # đối chiếu độc lập: tự fit lại đúng logic run_backtest dùng (SEED cố định trong models.py
    # -> RandomForest deterministic -> phải ra WAPE giống hệt).
    train_fit, holdout = _split_fold(train_full, fold)
    fc = TargetForecaster(
        target="Revenue", tree_model="RandomForest", use_ensemble=False, use_quarter=False
    ).fit(train_fit)
    preds = fc.predict(holdout[["Date"] + CALENDAR_FEATURES])
    manual_metrics = calc_metrics(holdout["Revenue"].to_numpy(), preds)

    assert result.loc[0, "WAPE"] == pytest.approx(manual_metrics["WAPE"])
    assert result.loc[0, "RMSE"] == pytest.approx(manual_metrics["RMSE"])


def test_run_backtest_train_and_holdout_do_not_overlap_for_real_fold_used() -> None:
    """Fold dùng bởi `run_backtest` ở test trên — xác nhận lại KHÔNG overlap qua chính
    `_split_fold` (đủ nhanh, không cần fit model)."""
    train_full = _synthetic_train_full(n_days=200)
    fold = {
        "fold": 0, "label": "tiny",
        "holdout_start": train_full["Date"].iloc[150],
        "holdout_end": train_full["Date"].iloc[159],
        "train_fit_end": train_full["Date"].iloc[149],
    }
    train_fit, holdout = _split_fold(train_full, fold)
    assert set(train_fit["Date"]).isdisjoint(set(holdout["Date"]))
    assert len(train_fit) == 150
    assert len(holdout) == 10
