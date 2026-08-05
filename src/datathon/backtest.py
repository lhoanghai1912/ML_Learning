"""Backtest rolling-origin cho model Revenue/COGS — metric WAPE/MAPE/RMSE/MAE.

Port từ code phase cũ (nhánh `feat/phase8-model`, xem `.process_status/M4b.md`
mục "Nguồn port"): `EDA_Insight/phase8_model/build_model.py`
(`calc_metrics`, `build_rolling_folds`, vòng lặp chọn model/ensemble/quarter).

Split THEO THỜI GIAN (rolling-origin, KHÔNG shuffle): mỗi fold, `train_fit`
luôn kết thúc TRƯỚC `holdout` bắt đầu (train_fit_end = holdout_start - 1
ngày) — train và holdout không overlap, train luôn ở quá khứ so với holdout
đang đánh giá → không leakage thời gian.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from datathon.features import CALENDAR_FEATURES, TARGETS, seasonal_naive_chain
from datathon.models import TargetForecaster, make_model_factories

HOLDOUT_LEN = 548
MIN_TRAIN_DAYS = 1000  # rolling-origin dừng khi train_fit ngắn hơn ~2.7 năm


def calc_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    err = y_true - y_pred
    n_zero = int((np.abs(y_true) < 1e-9).sum())
    mape = float(np.mean(np.abs(err) / np.abs(y_true)) * 100) if n_zero == 0 else float("nan")
    wape = float(np.sum(np.abs(err)) / np.sum(np.abs(y_true)) * 100)
    rmse = float(np.sqrt(np.mean(err ** 2)))
    mae = float(np.mean(np.abs(err)))
    return {"MAPE": mape, "WAPE": wape, "RMSE": rmse, "MAE": mae, "n_zero_actual": n_zero}


def build_rolling_folds(
    train_full: pd.DataFrame, holdout_len: int = HOLDOUT_LEN, min_train_days: int = MIN_TRAIN_DAYS
) -> list[dict]:
    """Fold 0 = "main_548d" (548 ngày cuối cùng, holdout chính thức để so
    baseline). Fold sau lùi dần về quá khứ (rolling-origin) tới khi
    train_fit ngắn hơn `min_train_days`."""
    min_date = train_full["Date"].min()
    max_date = train_full["Date"].max()
    folds = []
    holdout_end = max_date
    idx = 0
    while True:
        holdout_start = holdout_end - pd.Timedelta(days=holdout_len - 1)
        train_fit_end = holdout_start - pd.Timedelta(days=1)
        train_fit_len = (train_fit_end - min_date).days + 1
        if train_fit_len < min_train_days or holdout_start < min_date:
            break
        folds.append({
            "fold": idx,
            "label": "main_548d" if idx == 0 else f"rolling_{idx}",
            "holdout_start": holdout_start,
            "holdout_end": holdout_end,
            "train_fit_end": train_fit_end,
        })
        holdout_end = holdout_start - pd.Timedelta(days=1)
        idx += 1
    return folds


def _split_fold(train_full: pd.DataFrame, fold: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_fit = train_full[train_full["Date"] <= fold["train_fit_end"]].copy()
    holdout = train_full[
        (train_full["Date"] >= fold["holdout_start"]) & (train_full["Date"] <= fold["holdout_end"])
    ].copy()
    return train_fit, holdout


def run_backtest(
    train_full: pd.DataFrame,
    target: str,
    tree_model: str,
    use_ensemble: bool,
    use_quarter: bool,
    folds: list[dict] | None = None,
) -> pd.DataFrame:
    """Backtest 1 cấu hình (tree_model/use_ensemble/use_quarter) qua mọi fold
    của `folds` (mặc định `build_rolling_folds(train_full)`). Mỗi fold fit
    lại từ đầu trên `train_fit` (không rò rỉ thông tin fold khác/tương lai).
    Trả DataFrame metric (1 dòng/fold)."""
    if folds is None:
        folds = build_rolling_folds(train_full)
    rows = []
    for f in folds:
        train_fit, holdout = _split_fold(train_full, f)
        fc = TargetForecaster(
            target=target, tree_model=tree_model, use_ensemble=use_ensemble, use_quarter=use_quarter
        ).fit(train_fit)
        preds = fc.predict(holdout[["Date"] + CALENDAR_FEATURES])
        m = calc_metrics(holdout[target].to_numpy(), preds)
        model_label = tree_model + ("+ensembleB1" if use_ensemble else "") + ("+perQ" if use_quarter else "")
        rows.append({"fold": f["label"], "target": target, "model": model_label, **m})
    return pd.DataFrame(rows)


def select_best_config(
    train_full: pd.DataFrame, target: str, folds: list[dict] | None = None
) -> dict:
    """Tái tạo lựa chọn cấu hình sản xuất (`models.FINAL_CONFIG`) từ đầu bằng
    rolling-origin backtest — TỐN KÉM (4 model tree x N fold + quarter check),
    KHÔNG gọi trong `models.fit_all()` mặc định. Tiêu chí (giống Phase 8):
        1) tree thắng = WAPE nhỏ nhất trên fold `main_548d` (holdout chính
           thức) trong 4 model tree ứng viên.
        2) use_ensemble = True nếu ensemble(0.5*tree_thắng + 0.5*B1) có WAPE
           fold main THẤP HƠN tree đơn.
        3) use_quarter = True nếu tree_thắng fit per-quarter có WAPE fold
           main THẤP HƠN tree_thắng global.
    Trả dict {"tree_model", "use_ensemble", "use_quarter", "backtest": DataFrame}.
    """
    if folds is None:
        folds = build_rolling_folds(train_full)
    factories = make_model_factories()

    bt_rows = []
    fold_preds: dict[str, dict[str, np.ndarray]] = {name: {} for name in factories}
    fold_actuals: dict[str, np.ndarray] = {}

    for f in folds:
        train_fit, holdout = _split_fold(train_full, f)
        fold_actuals[f["label"]] = holdout[target].to_numpy()
        for name in factories:
            fc = TargetForecaster(target=target, tree_model=name, use_ensemble=False, use_quarter=False).fit(train_fit)
            preds = fc.predict(holdout[["Date"] + CALENDAR_FEATURES])
            fold_preds[name][f["label"]] = preds
            bt_rows.append({"fold": f["label"], "target": target, "model": name, **calc_metrics(fold_actuals[f["label"]], preds)})

    bt_df = pd.DataFrame(bt_rows)
    main_wape = bt_df[bt_df["fold"] == "main_548d"].set_index("model")["WAPE"]
    winner_tree = str(main_wape.idxmin())

    f0 = folds[0]
    train_fit0, holdout0 = _split_fold(train_full, f0)
    hist_fit0 = train_fit0.set_index("Date")[target].sort_index()

    b1_main_pred = seasonal_naive_chain(hist_fit0, pd.DatetimeIndex(holdout0["Date"]))
    tree_main_pred = fold_preds[winner_tree]["main_548d"]
    ens_main_pred = 0.5 * tree_main_pred + 0.5 * b1_main_pred
    ens_main_wape = calc_metrics(fold_actuals["main_548d"], ens_main_pred)["WAPE"]
    use_ensemble = bool(ens_main_wape < main_wape[winner_tree])
    bt_rows.append({"fold": "main_548d", "target": target, "model": f"Ensemble_{winner_tree}_B1",
                     **calc_metrics(fold_actuals["main_548d"], ens_main_pred)})

    fc_q = TargetForecaster(target=target, tree_model=winner_tree, use_ensemble=False, use_quarter=True).fit(train_fit0)
    preds_q = fc_q.predict(holdout0[["Date"] + CALENDAR_FEATURES])
    m_q = calc_metrics(holdout0[target].to_numpy(), preds_q)
    use_quarter = bool(m_q["WAPE"] < main_wape[winner_tree])
    bt_rows.append({"fold": "main_548d", "target": target, "model": f"{winner_tree}_per_quarter", **m_q})

    return {
        "tree_model": winner_tree,
        "use_ensemble": use_ensemble,
        "use_quarter": use_quarter,
        "backtest": pd.DataFrame(bt_rows),
    }
