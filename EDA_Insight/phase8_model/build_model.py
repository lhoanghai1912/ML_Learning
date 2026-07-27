"""
Giai đoạn 8 — Model dự báo Revenue + COGS 548 ngày (tree-based + ensemble).

CHỈ ĐỌC:
  - EDA_Insight/phase6_features/data/features_train.csv    (3,833 ngày, có target)
  - EDA_Insight/phase6_features/data/features_forecast.csv (548 ngày, không target)
  - data/sample_submission.csv (đối chiếu format cột)

GHI:
  - EDA_Insight/phase8_model/data/*.csv
  - EDA_Insight/output/phase8/*.png

KHÔNG sửa data gốc, KHÔNG sửa output GĐ6/GĐ7. Revenue/COGS train độc lập.
Seed cố định (SEED=42). Chạy: .venv/bin/python EDA_Insight/phase8_model/build_model.py
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

# LightGBM sklearn wrapper (v4.6.0) phát UserWarning "X does not have valid
# feature names..." mỗi lần predict(numpy) sau khi fit(numpy) — bug vô hại của
# thư viện (không liên quan tới đúng/sai kết quả), tắt để log không phình to
# và tránh overhead I/O khi gọi predict hàng chục nghìn lần (recursive forecast).
warnings.filterwarnings("ignore", category=UserWarning)
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import xgboost as xgb
import lightgbm as lgb

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42
np.random.seed(SEED)

ROOT = Path(__file__).resolve().parents[2]
F6_DIR = ROOT / "EDA_Insight" / "phase6_features" / "data"
OUT_DATA = Path(__file__).resolve().parent / "data"
OUT_CHART = ROOT / "EDA_Insight" / "output" / "phase8"
OUT_DATA.mkdir(parents=True, exist_ok=True)
OUT_CHART.mkdir(parents=True, exist_ok=True)

TARGETS = ["Revenue", "COGS"]
LAG_DAYS = 365
LAG_TOL = 3
SMOOTH_WINDOW = 3  # lag_365_smooth7 = mean of [lag-3 .. lag+3] (7 điểm)

# Feature lịch + lag thuần (KHÔNG hành vi khách hàng, KHÔNG promo tương lai —
# theo ràng buộc đề bài / GĐ5). `year` bị bỏ để giảm đa cộng tuyến với
# `trend_index` (đồng nhất quyết định GĐ7 mục 2), nhưng với tree ít quan trọng.
CALENDAR_FEATURES = [
    "month", "quarter", "day_of_week", "day_of_month",
    "month_sin", "month_cos", "dow_sin", "dow_cos",
    "is_post_2019", "is_post_2019_transition",
    "days_from_tet", "is_low_margin_season", "trend_index",
    "is_holiday_302_305", "is_holiday_qk", "is_christmas",
]
LAG_FEATURES = ["lag_365", "lag_365_smooth7"]
FEATURE_COLS = CALENDAR_FEATURES + LAG_FEATURES

MAIN_HOLDOUT_END = pd.Timestamp("2022-12-31")
HOLDOUT_LEN = 548
MIN_TRAIN_DAYS = 1000  # rolling-origin: dừng khi train_fit ngắn hơn ~2.7 năm


# =========================================================================
# Metric + lag helpers
# =========================================================================

def calc_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    err = y_true - y_pred
    n_zero = int((np.abs(y_true) < 1e-9).sum())
    mape = np.mean(np.abs(err) / np.abs(y_true)) * 100 if n_zero == 0 else np.nan
    wape = np.sum(np.abs(err)) / np.sum(np.abs(y_true)) * 100
    rmse = np.sqrt(np.mean(err ** 2))
    mae = np.mean(np.abs(err))
    return {"MAPE": mape, "WAPE": wape, "RMSE": rmse, "MAE": mae, "n_zero_actual": n_zero}


def lookup_lag(hist: pd.Series, d: pd.Timestamp, lag: int = LAG_DAYS, tol: int = LAG_TOL) -> float:
    lag_date = d - pd.Timedelta(days=lag)
    if lag_date in hist.index:
        return float(hist.loc[lag_date])
    for delta in range(1, tol + 1):
        for cand in (lag_date - pd.Timedelta(days=delta), lag_date + pd.Timedelta(days=delta)):
            if cand in hist.index:
                return float(hist.loc[cand])
    return float(hist.mean())


def lookup_lag_smooth(hist: pd.Series, d: pd.Timestamp, lag: int = LAG_DAYS, window: int = SMOOTH_WINDOW) -> float:
    lag_date = d - pd.Timedelta(days=lag)
    vals = []
    for k in range(-window, window + 1):
        cand = lag_date + pd.Timedelta(days=k)
        if cand in hist.index:
            vals.append(float(hist.loc[cand]))
    if not vals:
        return float(hist.mean())
    return float(np.mean(vals))


def build_static_lag_features(hist: pd.Series, dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Xây lag_365 / lag_365_smooth7 KHÔNG chain — dùng khi xây feature cho tập
    TRAIN (mọi ngày d trong dates, d-365 luôn < d nên không leak, an toàn dù
    hist chứa dữ liệu về sau vì ta không bao giờ tra cứu >= d)."""
    lags, smooths = [], []
    for d in dates:
        lags.append(lookup_lag(hist, d))
        smooths.append(lookup_lag_smooth(hist, d))
    return pd.DataFrame({"lag_365": lags, "lag_365_smooth7": smooths}, index=dates)


def seasonal_naive_chain(hist: pd.Series, dates: pd.DatetimeIndex) -> np.ndarray:
    """B1 seasonal naive — giống hệt logic GĐ7, dùng làm 1 nhánh ensemble."""
    h = hist.copy()
    preds = {}
    for d in sorted(dates):
        val = lookup_lag(h, d)
        preds[d] = val
        h.loc[d] = val
    return pd.Series(preds).reindex(dates).to_numpy()


def recursive_tree_forecast(predict_fn, hist: pd.Series, calendar_df: pd.DataFrame) -> np.ndarray:
    """Dự báo tuần tự ngày-qua-ngày: lag_365/lag_365_smooth7 tra cứu từ `hist`
    (actual + dự đoán trước đó của CHÍNH model này, không phải actual tương
    lai) — cần thiết vì horizon 548 > 365 ngày."""
    h = hist.copy()
    cal_sorted = calendar_df.sort_values("Date").reset_index(drop=True)
    preds = np.empty(len(cal_sorted))
    for i, row in cal_sorted.iterrows():
        d = row["Date"]
        lag_val = lookup_lag(h, d)
        smooth_val = lookup_lag_smooth(h, d)
        feat = {c: row[c] for c in CALENDAR_FEATURES}
        feat["lag_365"] = lag_val
        feat["lag_365_smooth7"] = smooth_val
        X = pd.DataFrame([feat])[FEATURE_COLS]
        yhat = float(predict_fn(X)[0])
        yhat = max(yhat, 0.0)
        preds[i] = yhat
        h.loc[d] = yhat
    # trả về theo đúng thứ tự calendar_df gốc (đầu vào có thể không sort)
    out = pd.Series(preds, index=cal_sorted["Date"]).reindex(calendar_df["Date"]).to_numpy()
    return out


# =========================================================================
# Model factories (seed cố định)
# =========================================================================

def make_models() -> dict:
    return {
        "RandomForest": RandomForestRegressor(
            n_estimators=400, max_depth=8, min_samples_leaf=5,
            random_state=SEED, n_jobs=-1),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=300, max_depth=3, learning_rate=0.05, random_state=SEED),
        "XGBoost": xgb.XGBRegressor(
            n_estimators=400, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, random_state=SEED,
            tree_method="hist", n_jobs=-1, verbosity=0),
        "LightGBM": lgb.LGBMRegressor(
            n_estimators=400, num_leaves=31, learning_rate=0.05,
            random_state=SEED, n_jobs=-1, verbosity=-1),
    }


# =========================================================================
# Rolling-origin folds
# =========================================================================

def build_rolling_folds(train_full: pd.DataFrame) -> list[dict]:
    min_date = train_full["Date"].min()
    max_date = train_full["Date"].max()
    folds = []
    holdout_end = max_date
    idx = 0
    while True:
        holdout_start = holdout_end - pd.Timedelta(days=HOLDOUT_LEN - 1)
        train_fit_end = holdout_start - pd.Timedelta(days=1)
        train_fit_len = (train_fit_end - min_date).days + 1
        if train_fit_len < MIN_TRAIN_DAYS or holdout_start < min_date:
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


def main():
    train_full = pd.read_csv(F6_DIR / "features_train.csv", parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
    forecast_df = pd.read_csv(F6_DIR / "features_forecast.csv", parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
    sample_sub = pd.read_csv(ROOT / "data" / "sample_submission.csv")
    assert set(forecast_df["Date"].dt.strftime("%Y-%m-%d")) == set(sample_sub["Date"]), "forecast dates lệch sample_submission"
    print(f"[load] train_full: {train_full.shape}, forecast: {forecast_df.shape}")

    folds = build_rolling_folds(train_full)
    print(f"[rolling-origin] {len(folds)} folds:")
    for f in folds:
        print(f"  {f['label']}: holdout {f['holdout_start'].date()} -> {f['holdout_end'].date()}, "
              f"train_fit kết thúc {f['train_fit_end'].date()}")

    model_factories = make_models()

    backtest_rows = []          # metric mỗi fold x target x model (single-tree + B1)
    main_holdout_pred_rows = []  # chi tiết fold main để chart + report
    best_model_name = {}        # target -> tên model tree thắng (global)
    best_use_ensemble = {}      # target -> True/False dùng ensemble(tree+B1)
    best_use_quarter = {}       # target -> True/False dùng quarter-specific
    feature_importance_rows = []

    for target in TARGETS:
        print(f"\n==== Target: {target} ====")
        hist_full_actual = train_full.set_index("Date")[target].sort_index()

        # lưu prediction từng model từng fold để chọn model thắng + build ensemble
        fold_model_preds = {}   # (fold_label) -> {model_name: preds_array}
        fold_b1_preds = {}
        fold_actuals = {}

        for f in folds:
            train_fit = train_full[train_full["Date"] <= f["train_fit_end"]].copy()
            holdout = train_full[(train_full["Date"] >= f["holdout_start"]) & (train_full["Date"] <= f["holdout_end"])].copy()
            hist_fit = train_fit.set_index("Date")[target].sort_index()

            # ---- feature X cho train_fit (lag tra cứu tĩnh, không leak) ----
            lag_train = build_static_lag_features(hist_fit, pd.DatetimeIndex(train_fit["Date"]))
            X_train = pd.concat([
                train_fit.set_index("Date")[CALENDAR_FEATURES],
                lag_train
            ], axis=1)[FEATURE_COLS]
            y_train = train_fit.set_index("Date")[target]

            # ---- B1 seasonal naive (chain) trên holdout ----
            b1_pred = seasonal_naive_chain(hist_fit, pd.DatetimeIndex(holdout["Date"]))
            fold_b1_preds[f["label"]] = b1_pred
            fold_actuals[f["label"]] = holdout[target].to_numpy()

            m_b1 = calc_metrics(holdout[target].to_numpy(), b1_pred)
            backtest_rows.append({"fold": f["label"], "target": target, "model": "B1_seasonal_naive", **m_b1})

            fold_model_preds[f["label"]] = {}
            for name, ctor in model_factories.items():
                model = ctor.__class__(**ctor.get_params()) if hasattr(ctor, "get_params") else ctor
                model.fit(X_train.to_numpy(), y_train.to_numpy())
                preds = recursive_tree_forecast(lambda X, m=model: m.predict(X.to_numpy()), hist_fit, holdout[["Date"] + CALENDAR_FEATURES])
                fold_model_preds[f["label"]][name] = preds
                m = calc_metrics(holdout[target].to_numpy(), preds)
                backtest_rows.append({"fold": f["label"], "target": target, "model": name, **m})
                print(f"  [{f['label']}] {name}: WAPE={m['WAPE']:.2f}%  MAPE={m['MAPE']:.2f}%")

        # ---------------- chọn model tree thắng theo WAPE trung bình các fold ----------------
        bt_df = pd.DataFrame(backtest_rows)
        bt_target = bt_df[bt_df["target"] == target]
        avg_wape = bt_target.groupby("model")["WAPE"].mean().sort_values()
        main_wape = bt_target[bt_target["fold"] == "main_548d"].set_index("model")["WAPE"]
        print(f"\n[{target}] avg WAPE tất cả fold:\n{avg_wape.round(2)}")
        print(f"[{target}] WAPE fold main (chính thức so baseline):\n{main_wape.round(2)}")

        # Tiêu chí chọn: WAPE fold main (holdout chính thức phải vượt mốc GĐ7) —
        # rolling-origin dùng để BÁO CÁO độ ổn định, không dùng làm tiêu chí chọn
        # chính vì các fold cũ (VD rolling_2 trùng đúng giai đoạn break 2019) khó
        # so sánh công bằng với horizon thật 2023-2024 (gần main fold hơn nhiều).
        tree_models_only = [n for n in avg_wape.index if n != "B1_seasonal_naive"]
        winner_tree = main_wape[tree_models_only].idxmin()
        best_model_name[target] = winner_tree
        print(f"[{target}] --> tree model thắng (WAPE fold main): {winner_tree} "
              f"(avg mọi fold để tham khảo ổn định: {avg_wape[tree_models_only].round(2).to_dict()})")

        # ---------------- test ensemble (0.5*tree_thắng + 0.5*B1) trên mọi fold ----------------
        ens_metrics = []
        for f in folds:
            lbl = f["label"]
            tree_p = fold_model_preds[lbl][winner_tree]
            b1_p = fold_b1_preds[lbl]
            ens_p = 0.5 * tree_p + 0.5 * b1_p
            m = calc_metrics(fold_actuals[lbl], ens_p)
            ens_metrics.append(m["WAPE"])
            backtest_rows.append({"fold": lbl, "target": target, "model": f"Ensemble_{winner_tree}_B1", **m})
        ens_avg = float(np.mean(ens_metrics))
        ens_main = ens_metrics[0]
        tree_avg = avg_wape[winner_tree]
        tree_main = main_wape[winner_tree]
        b1_avg = avg_wape["B1_seasonal_naive"]
        b1_main = main_wape["B1_seasonal_naive"]
        use_ensemble = ens_main < tree_main
        best_use_ensemble[target] = use_ensemble
        print(f"[{target}] Ensemble(tree+B1) avg WAPE={ens_avg:.2f}% (main={ens_main:.2f}%) "
              f"vs tree avg={tree_avg:.2f}% (main={tree_main:.2f}%) vs B1 avg={b1_avg:.2f}% (main={b1_main:.2f}%) "
              f"-> {'DÙNG ENSEMBLE' if use_ensemble else 'DÙNG TREE ĐƠN'}")

        # ---------------- test quarter-specific tree thay cho global ----------------
        quarter_metrics_main = None
        quarter_metrics_all = []
        for f in folds:
            train_fit = train_full[train_full["Date"] <= f["train_fit_end"]].copy()
            holdout = train_full[(train_full["Date"] >= f["holdout_start"]) & (train_full["Date"] <= f["holdout_end"])].copy()
            hist_fit = train_fit.set_index("Date")[target].sort_index()
            lag_train = build_static_lag_features(hist_fit, pd.DatetimeIndex(train_fit["Date"]))
            X_train_full = pd.concat([train_fit.set_index("Date")[CALENDAR_FEATURES], lag_train], axis=1)
            y_train_full = train_fit.set_index("Date")[target]

            q_models = {}
            for q in [1, 2, 3, 4]:
                mask = X_train_full["quarter"] == q
                ctor = model_factories[winner_tree]
                m_q = ctor.__class__(**ctor.get_params())
                m_q.fit(X_train_full.loc[mask, FEATURE_COLS].to_numpy(), y_train_full.loc[mask].to_numpy())
                q_models[q] = m_q

            def predict_fn_q(X, models=q_models):
                q = int(X["quarter"].iloc[0])
                return models[q].predict(X.to_numpy())

            preds_q = recursive_tree_forecast(predict_fn_q, hist_fit, holdout[["Date"] + CALENDAR_FEATURES])
            m = calc_metrics(holdout[target].to_numpy(), preds_q)
            quarter_metrics_all.append(m["WAPE"])
            if f["label"] == "main_548d":
                quarter_metrics_main = m["WAPE"]
            backtest_rows.append({"fold": f["label"], "target": target, "model": f"{winner_tree}_per_quarter", **m})

        quarter_avg = float(np.mean(quarter_metrics_all))
        use_quarter = quarter_metrics_main < tree_main
        best_use_quarter[target] = use_quarter
        print(f"[{target}] {winner_tree} per-quarter avg WAPE={quarter_avg:.2f}% (main={quarter_metrics_main:.2f}%) "
              f"vs global avg={tree_avg:.2f}% (main={tree_main:.2f}%) -> "
              f"{'DÙNG PER-QUARTER' if use_quarter else 'DÙNG GLOBAL'}")

        # ---------------- lưu chi tiết fold main để chart/so sánh ----------------
        lbl = "main_548d"
        holdout_main = train_full[(train_full["Date"] >= folds[0]["holdout_start"]) & (train_full["Date"] <= folds[0]["holdout_end"])]
        for i, d in enumerate(holdout_main["Date"]):
            main_holdout_pred_rows.append({
                "Date": d.strftime("%Y-%m-%d"), "target": target,
                "actual": fold_actuals[lbl][i],
                "B1_seasonal_naive": fold_b1_preds[lbl][i],
                winner_tree: fold_model_preds[lbl][winner_tree][i],
                f"Ensemble_{winner_tree}_B1": 0.5 * fold_model_preds[lbl][winner_tree][i] + 0.5 * fold_b1_preds[lbl][i],
            })

    # =====================================================================
    # FINAL: chọn cấu hình per target, fit production trên FULL train, forecast
    # =====================================================================
    final_choice = {}
    forecast_out = {}
    holdout_final_pred = {}

    for target in TARGETS:
        winner_tree = best_model_name[target]
        use_ensemble = best_use_ensemble[target]
        use_quarter = best_use_quarter[target]
        final_choice[target] = {
            "tree_model": winner_tree, "use_ensemble": use_ensemble, "use_quarter": use_quarter,
        }
        print(f"\n[FINAL {target}] tree={winner_tree}, ensemble={use_ensemble}, per_quarter={use_quarter}")

        hist_full_actual = train_full.set_index("Date")[target].sort_index()
        lag_full = build_static_lag_features(hist_full_actual, pd.DatetimeIndex(train_full["Date"]))
        X_full = pd.concat([train_full.set_index("Date")[CALENDAR_FEATURES], lag_full], axis=1)
        y_full = train_full.set_index("Date")[target]

        ctor = model_factories[winner_tree]

        if use_quarter:
            q_models = {}
            for q in [1, 2, 3, 4]:
                mask = X_full["quarter"] == q
                m_q = ctor.__class__(**ctor.get_params())
                m_q.fit(X_full.loc[mask, FEATURE_COLS].to_numpy(), y_full.loc[mask].to_numpy())
                q_models[q] = m_q

            def predict_fn_final(X, models=q_models):
                q = int(X["quarter"].iloc[0])
                return models[q].predict(X.to_numpy())

            imp = np.mean([q_models[q].feature_importances_ for q in [1, 2, 3, 4]], axis=0)
        else:
            model_final = ctor.__class__(**ctor.get_params())
            model_final.fit(X_full[FEATURE_COLS].to_numpy(), y_full.to_numpy())
            predict_fn_final = lambda X, m=model_final: m.predict(X.to_numpy())
            imp = model_final.feature_importances_

        for feat_name, val in zip(FEATURE_COLS, imp):
            feature_importance_rows.append({"target": target, "feature": feat_name, "importance": val})

        # forecast 548 ngày thật (production, dùng full train làm history)
        tree_fc = recursive_tree_forecast(predict_fn_final, hist_full_actual, forecast_df[["Date"] + CALENDAR_FEATURES])

        if use_ensemble:
            b1_fc = seasonal_naive_chain(hist_full_actual, pd.DatetimeIndex(forecast_df["Date"]))
            final_fc = 0.5 * tree_fc + 0.5 * b1_fc
        else:
            final_fc = tree_fc
        final_fc = np.clip(final_fc, 0, None)
        forecast_out[target] = final_fc

        # holdout main dùng CHÍNH cấu hình cuối (để so sánh công bằng, đã tính ở vòng trên
        # nhưng fold main chưa áp per-quarter nếu use_quarter=True và tree đã lưu global ở trên
        # -> tính lại đúng cấu hình final cho holdout main)
        f0 = folds[0]
        train_fit0 = train_full[train_full["Date"] <= f0["train_fit_end"]].copy()
        holdout0 = train_full[(train_full["Date"] >= f0["holdout_start"]) & (train_full["Date"] <= f0["holdout_end"])].copy()
        hist_fit0 = train_fit0.set_index("Date")[target].sort_index()
        lag_train0 = build_static_lag_features(hist_fit0, pd.DatetimeIndex(train_fit0["Date"]))
        X_train0 = pd.concat([train_fit0.set_index("Date")[CALENDAR_FEATURES], lag_train0], axis=1)
        y_train0 = train_fit0.set_index("Date")[target]

        if use_quarter:
            q_models0 = {}
            for q in [1, 2, 3, 4]:
                mask = X_train0["quarter"] == q
                m_q = ctor.__class__(**ctor.get_params())
                m_q.fit(X_train0.loc[mask, FEATURE_COLS].to_numpy(), y_train0.loc[mask].to_numpy())
                q_models0[q] = m_q
            predict_fn0 = lambda X, models=q_models0: models[int(X["quarter"].iloc[0])].predict(X.to_numpy())
        else:
            model0 = ctor.__class__(**ctor.get_params())
            model0.fit(X_train0[FEATURE_COLS].to_numpy(), y_train0.to_numpy())
            predict_fn0 = lambda X, m=model0: m.predict(X.to_numpy())

        tree_hold0 = recursive_tree_forecast(predict_fn0, hist_fit0, holdout0[["Date"] + CALENDAR_FEATURES])
        if use_ensemble:
            b1_hold0 = seasonal_naive_chain(hist_fit0, pd.DatetimeIndex(holdout0["Date"]))
            final_hold0 = 0.5 * tree_hold0 + 0.5 * b1_hold0
        else:
            final_hold0 = tree_hold0
        final_hold0 = np.clip(final_hold0, 0, None)
        holdout_final_pred[target] = {"Date": holdout0["Date"].to_numpy(), "actual": holdout0[target].to_numpy(), "pred": final_hold0}

        m_final = calc_metrics(holdout0[target].to_numpy(), final_hold0)
        print(f"[FINAL {target}] holdout main (548d) — WAPE={m_final['WAPE']:.2f}%  MAPE={m_final['MAPE']:.2f}%  "
              f"RMSE={m_final['RMSE']:.0f}  MAE={m_final['MAE']:.0f}")
        backtest_rows.append({"fold": "main_548d", "target": target, "model": "FINAL_CHOSEN", **m_final})

    # =====================================================================
    # SAVE outputs
    # =====================================================================
    bt_df = pd.DataFrame(backtest_rows)
    bt_df.to_csv(OUT_DATA / "backtest_metrics.csv", index=False)

    fi_df = pd.DataFrame(feature_importance_rows)
    fi_df.to_csv(OUT_DATA / "feature_importance.csv", index=False)

    hp_df = pd.DataFrame(main_holdout_pred_rows)
    hp_df.to_csv(OUT_DATA / "holdout_predictions.csv", index=False)

    forecast_csv = pd.DataFrame({
        "Date": forecast_df["Date"].dt.strftime("%Y-%m-%d"),
        "Revenue": np.round(forecast_out["Revenue"], 2),
        "COGS": np.round(forecast_out["COGS"], 2),
    })
    assert forecast_csv.shape[0] == 548
    assert forecast_csv[["Revenue", "COGS"]].isna().sum().sum() == 0
    assert (forecast_csv["Revenue"] >= 0).all() and (forecast_csv["COGS"] >= 0).all()
    forecast_csv.to_csv(OUT_DATA / "forecast_548.csv", index=False)

    with open(OUT_DATA / "final_choice.txt", "w") as fpt:
        for target, cfg in final_choice.items():
            fpt.write(f"{target}: tree_model={cfg['tree_model']} use_ensemble={cfg['use_ensemble']} "
                      f"use_quarter={cfg['use_quarter']}\n")

    # =====================================================================
    # CHARTS
    # =====================================================================

    # Chart 1: backtest WAPE theo fold, mỗi model (2 panel target)
    main_models_order = None
    fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=False)
    for ax, target in zip(axes, TARGETS):
        sub = bt_df[(bt_df["target"] == target) & (bt_df["model"] != "FINAL_CHOSEN")]
        pivot = sub.pivot_table(index="fold", columns="model", values="WAPE")
        fold_order = [f["label"] for f in folds]
        pivot = pivot.reindex(fold_order)
        for col in pivot.columns:
            ax.plot(pivot.index, pivot[col], marker="o", label=col, linewidth=1.2)
        ax.set_title(f"{target}: WAPE (%) rolling-origin backtest — {len(folds)} fold (fold trái = cũ nhất, phải = main)")
        ax.set_ylabel("WAPE %")
        ax.legend(fontsize=7, ncol=2)
        ax.tick_params(axis='x', labelrotation=15)
    fig.tight_layout()
    fig.savefig(OUT_CHART / "08_backtest_wape_by_fold.png", dpi=120)
    plt.close(fig)

    # Chart 2: actual vs predicted (final chosen) trên holdout main
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    for ax, target in zip(axes, TARGETS):
        d = holdout_final_pred[target]
        ax.plot(d["Date"], d["actual"], label="Actual", color="black", linewidth=1.1)
        ax.plot(d["Date"], d["pred"], label=f"Model cuối cùng ({final_choice[target]['tree_model']}"
                                             f"{'+Ensemble B1' if final_choice[target]['use_ensemble'] else ''}"
                                             f"{'/perQ' if final_choice[target]['use_quarter'] else ''})",
                color="darkorange", linewidth=1.0, alpha=0.85)
        ax.set_title(f"{target}: Actual vs Predicted (model cuối) — holdout main 548 ngày")
        ax.set_ylabel(target)
        ax.legend(fontsize=8)
    axes[-1].set_xlabel("Date")
    fig.tight_layout()
    fig.savefig(OUT_CHART / "08_holdout_actual_vs_pred_final.png", dpi=120)
    plt.close(fig)

    # Chart 3: feature importance (2 panel)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, target in zip(axes, TARGETS):
        sub = fi_df[fi_df["target"] == target].sort_values("importance", ascending=True)
        ax.barh(sub["feature"], sub["importance"], color="teal")
        ax.set_title(f"{target}: Feature importance ({final_choice[target]['tree_model']})")
        ax.set_xlabel("Importance")
    fig.tight_layout()
    fig.savefig(OUT_CHART / "08_feature_importance.png", dpi=120)
    plt.close(fig)

    # Chart 4: forecast 548 ngày cuối cùng
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    for ax, target in zip(axes, TARGETS):
        ax.plot(forecast_df["Date"], forecast_out[target], color="steelblue", linewidth=1.0)
        ax.set_title(f"{target}: Forecast 548 ngày (2023-01-01 → 2024-07-01) — model cuối cùng")
        ax.set_ylabel(target)
    axes[-1].set_xlabel("Date")
    fig.tight_layout()
    fig.savefig(OUT_CHART / "08_forecast_548_final.png", dpi=120)
    plt.close(fig)

    print("\nHoàn tất Giai đoạn 8. File output:")
    for p in sorted(OUT_DATA.glob("*")):
        print(f" - {p}")
    for p in sorted(OUT_CHART.glob("08_*.png")):
        print(f" - {p}")


if __name__ == "__main__":
    main()
