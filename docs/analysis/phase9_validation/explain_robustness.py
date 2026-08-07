"""
Giai đoạn 9 — Explainability (SHAP) + Robustness cho model GĐ8.

Tự tái lập model GĐ8 (LightGBM global + ensemble 50/50 B1), KHÔNG tin số report cũ:
  T9.3  SHAP LightGBM cả 2 target — CHIỀU tác động + vùng ngoại suy trend_index (leaf-cap).
  T9.4  Suy giảm theo horizon: WAPE/MAPE ngày 1-365 vs 366-548 trên holdout main_548d.
        Nếu đuôi tệ rõ (>+5 điểm WAPE) -> thử lag_182 bổ sung.
  T9.5  Re-check robustness (GB vs LGB vs Ensemble qua 5 fold) + tối ưu weight ensemble
        trên VALIDATION (rolling folds, KHÔNG fit trên fold main -> tránh overfit chọn model).

CHỈ ĐỌC:
  - EDA_Insight/phase6_features/data/features_train.csv    (3,833 ngày, có target)
  - EDA_Insight/phase6_features/data/features_forecast.csv (548 ngày, không target)
  - EDA_Insight/phase8_model/data/backtest_metrics.csv     (bảng metric GĐ8)
GHI:
  - EDA_Insight/phase9_validation/data/*.csv
  - EDA_Insight/output/phase9/*.png
  - (điều kiện) forecast_548_v2.csv chỉ khi weight tối ưu ĐỔI so 50/50 và tốt hơn rõ.

Seed cố định (kế thừa SEED=42 từ build_model). Không leakage: chỉ feature lịch + lag.
Chạy: .venv/bin/python EDA_Insight/phase9_validation/explain_robustness.py  (~2-3 phút)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import shap

ROOT = Path(__file__).resolve().parents[2]
P8_DIR = ROOT / "EDA_Insight" / "phase8_model"
sys.path.insert(0, str(P8_DIR))

# Tái sử dụng NGUYÊN VẸN logic GĐ8 (không copy-drift): factories, chain, lag, folds, metric.
from build_model import (  # noqa: E402
    SEED, TARGETS, CALENDAR_FEATURES, LAG_FEATURES, FEATURE_COLS,
    LAG_DAYS, LAG_TOL, SMOOTH_WINDOW,
    calc_metrics, lookup_lag, lookup_lag_smooth,
    build_static_lag_features, seasonal_naive_chain,
    recursive_tree_forecast, make_models, build_rolling_folds,
)

np.random.seed(SEED)

F6_DIR = ROOT / "EDA_Insight" / "phase6_features" / "data"
OUT_DATA = Path(__file__).resolve().parent / "data"
OUT_CHART = ROOT / "EDA_Insight" / "output" / "phase9"
OUT_DATA.mkdir(parents=True, exist_ok=True)
OUT_CHART.mkdir(parents=True, exist_ok=True)

WEIGHT_GRID = [round(0.30 + 0.05 * k, 2) for k in range(9)]  # 0.30 .. 0.70 (trọng số cho TREE)
TAIL_WAPE_TRIGGER = 5.0  # điểm % — ngưỡng "đuôi tệ rõ" để kích hoạt thử lag_182


# =========================================================================
# Helpers dùng chung
# =========================================================================

def fit_lgbm_full(train_full: pd.DataFrame, target: str):
    """Fit LightGBM production trên TOÀN BỘ train (đúng cấu hình cuối GĐ8)."""
    hist = train_full.set_index("Date")[target].sort_index()
    lag_full = build_static_lag_features(hist, pd.DatetimeIndex(train_full["Date"]))
    X_full = pd.concat([train_full.set_index("Date")[CALENDAR_FEATURES], lag_full], axis=1)[FEATURE_COLS]
    y_full = train_full.set_index("Date")[target]
    model = make_models()["LightGBM"]
    model = model.__class__(**model.get_params())
    model.fit(X_full.to_numpy(), y_full.to_numpy())
    return model, X_full, y_full, hist


def capture_forecast_features(model, hist: pd.Series, calendar_df: pd.DataFrame) -> pd.DataFrame:
    """Chạy chain đệ quy GĐ8 nhưng GHI LẠI ma trận feature thực tế mỗi bước
    (để SHAP đúng trên vùng ngoại suy). Trả DataFrame FEATURE_COLS theo Date."""
    h = hist.copy()
    cal = calendar_df.sort_values("Date").reset_index(drop=True)
    rows = []
    for _, r in cal.iterrows():
        d = r["Date"]
        feat = {c: r[c] for c in CALENDAR_FEATURES}
        feat["lag_365"] = lookup_lag(h, d)
        feat["lag_365_smooth7"] = lookup_lag_smooth(h, d)
        X = pd.DataFrame([feat])[FEATURE_COLS]
        yhat = max(float(model.predict(X.to_numpy())[0]), 0.0)
        h.loc[d] = yhat
        feat["Date"] = d
        rows.append(feat)
    return pd.DataFrame(rows).set_index("Date")[FEATURE_COLS]


# =========================================================================
# T9.3 — SHAP
# =========================================================================

def run_shap(train_full: pd.DataFrame, forecast_df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "=" * 78 + "\nT9.3 — SHAP explainability (LightGBM, cả 2 target)\n" + "=" * 78)
    trend_max_train = int(train_full["trend_index"].max())
    print(f"[ngoại suy] trend_index train: 0..{trend_max_train} | forecast: "
          f"{int(forecast_df['trend_index'].min())}..{int(forecast_df['trend_index'].max())} "
          f"-> 100% ngày forecast có trend_index > max train ({trend_max_train}).")

    shap_summary_rows = []
    key_feats = ["trend_index", "lag_365", "days_from_tet", "day_of_month"]
    zero_feats = ["quarter", "is_holiday_qk", "is_christmas"]

    fig_bee, axes_bee = plt.subplots(1, 2, figsize=(15, 7))
    fig_sweep, axes_sweep = plt.subplots(1, 2, figsize=(15, 6))

    for ti, target in enumerate(TARGETS):
        model, X_full, y_full, hist = fit_lgbm_full(train_full, target)
        explainer = shap.TreeExplainer(model)
        sv_train = explainer.shap_values(X_full.to_numpy())  # (n, n_feat)

        # feature forecast thực tế (recursive lag) -> SHAP vùng ngoại suy
        Xf = capture_forecast_features(model, hist, forecast_df[["Date"] + CALENDAR_FEATURES])
        sv_fc = explainer.shap_values(Xf.to_numpy())

        mean_abs = np.abs(sv_train).mean(axis=0)
        order = np.argsort(mean_abs)[::-1]

        # chiều tác động: dấu corr(feature_value, shap_value)
        for fi, feat in enumerate(FEATURE_COLS):
            fv = X_full[feat].to_numpy()
            sv = sv_train[:, fi]
            if np.std(fv) < 1e-12 or np.std(sv) < 1e-12:
                corr = 0.0
            else:
                corr = float(np.corrcoef(fv, sv)[0, 1])
            shap_summary_rows.append({
                "target": target, "feature": feat,
                "mean_abs_shap": float(mean_abs[fi]),
                "dir_corr": corr,
                "direction": "+" if corr > 0.05 else ("-" if corr < -0.05 else "~0"),
                "mean_abs_shap_forecast": float(np.abs(sv_fc[:, fi]).mean()),
                "std_shap_forecast": float(np.std(sv_fc[:, fi])),
            })

        # ---- beeswarm ----
        plt.sca(axes_bee[ti])
        shap.summary_plot(sv_train, X_full, feature_names=FEATURE_COLS, show=False,
                          plot_size=None, max_display=12, sort=True)
        axes_bee[ti].set_title(f"{target}: SHAP beeswarm (LightGBM, train)")

        # ---- sweep trend_index chứng minh leaf-cap ----
        base = X_full.median(numeric_only=True)
        sweep_trend = np.arange(0, int(forecast_df["trend_index"].max()) + 1, 10)
        Xs = pd.DataFrame([base] * len(sweep_trend))
        Xs["trend_index"] = sweep_trend
        yhat_sweep = model.predict(Xs[FEATURE_COLS].to_numpy())
        ax = axes_sweep[ti]
        ax.plot(sweep_trend, yhat_sweep, color="steelblue", lw=1.4)
        ax.axvline(trend_max_train, color="red", ls="--", lw=1,
                   label=f"max train trend={trend_max_train}")
        ax.set_title(f"{target}: prediction vs trend_index (feature khác = median)")
        ax.set_xlabel("trend_index"); ax.set_ylabel(f"pred {target}")
        ax.legend(fontsize=8)
        # đo mức "phẳng" của đuôi ngoại suy
        tail_mask = sweep_trend > trend_max_train
        tail_vals = yhat_sweep[tail_mask]
        flat = float(tail_vals.max() - tail_vals.min()) if tail_mask.sum() else 0.0
        in_vals = yhat_sweep[~tail_mask]
        in_range = float(in_vals.max() - in_vals.min())
        print(f"\n[{target}] TOP feature theo mean|SHAP|:")
        for j in order[:6]:
            print(f"    {FEATURE_COLS[j]:<22} mean|shap|={mean_abs[j]:.0f}")
        print(f"[{target}] chiều tác động (corr value<->shap):")
        for feat in key_feats:
            row = [r for r in shap_summary_rows if r["target"] == target and r["feature"] == feat][0]
            print(f"    {feat:<16} dir={row['direction']}  corr={row['dir_corr']:+.2f}")
        print(f"[{target}] ~0 importance check:")
        for feat in zero_feats:
            row = [r for r in shap_summary_rows if r["target"] == target and r["feature"] == feat][0]
            print(f"    {feat:<16} mean|shap|={row['mean_abs_shap']:.1f}")
        print(f"[{target}] LEAF-CAP: dao động pred trong đuôi ngoại suy (trend>{trend_max_train}) "
              f"= {flat:.0f}  vs  biên độ trong-range = {in_range:.0f}  "
              f"-> {'CHẶN PHẲNG (capped)' if flat < 0.02 * max(in_range,1) else 'còn biến thiên'}")

    fig_bee.tight_layout(); fig_bee.savefig(OUT_CHART / "09_shap_beeswarm.png", dpi=120); plt.close(fig_bee)
    fig_sweep.tight_layout(); fig_sweep.savefig(OUT_CHART / "09_trend_leafcap_sweep.png", dpi=120); plt.close(fig_sweep)

    ss = pd.DataFrame(shap_summary_rows)
    ss.to_csv(OUT_DATA / "shap_summary.csv", index=False)

    # bar mean|SHAP| 2 panel
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, target in zip(axes, TARGETS):
        sub = ss[ss["target"] == target].sort_values("mean_abs_shap")
        colors = ["crimson" if d == "-" else ("teal" if d == "+" else "grey") for d in sub["direction"]]
        ax.barh(sub["feature"], sub["mean_abs_shap"], color=colors)
        ax.set_title(f"{target}: mean|SHAP| (teal=+, đỏ=-, xám=~0)")
        ax.set_xlabel("mean|SHAP|")
    fig.tight_layout(); fig.savefig(OUT_CHART / "09_shap_bar_signed.png", dpi=120); plt.close(fig)
    return ss


# =========================================================================
# Tái tạo preds mọi fold (LightGBM chain + B1 chain) — cho T9.4 + T9.5
# =========================================================================

def regen_fold_preds(train_full: pd.DataFrame, folds: list) -> dict:
    """Trả store[target][fold_label] = {actual, tree(LightGBM chain), b1(chain), dates}."""
    store = {t: {} for t in TARGETS}
    for target in TARGETS:
        for f in folds:
            train_fit = train_full[train_full["Date"] <= f["train_fit_end"]].copy()
            holdout = train_full[(train_full["Date"] >= f["holdout_start"]) &
                                 (train_full["Date"] <= f["holdout_end"])].copy()
            hist_fit = train_fit.set_index("Date")[target].sort_index()
            lag_train = build_static_lag_features(hist_fit, pd.DatetimeIndex(train_fit["Date"]))
            X_train = pd.concat([train_fit.set_index("Date")[CALENDAR_FEATURES], lag_train], axis=1)[FEATURE_COLS]
            y_train = train_fit.set_index("Date")[target]
            model = make_models()["LightGBM"]
            model = model.__class__(**model.get_params())
            model.fit(X_train.to_numpy(), y_train.to_numpy())
            tree_p = recursive_tree_forecast(lambda X, m=model: m.predict(X.to_numpy()),
                                             hist_fit, holdout[["Date"] + CALENDAR_FEATURES])
            b1_p = seasonal_naive_chain(hist_fit, pd.DatetimeIndex(holdout["Date"]))
            store[target][f["label"]] = {
                "actual": holdout[target].to_numpy(),
                "tree": np.clip(tree_p, 0, None),
                "b1": np.clip(b1_p, 0, None),
                "dates": holdout["Date"].to_numpy(),
            }
            print(f"  [regen] {target} {f['label']}: n={len(b1_p)}")
    return store


# =========================================================================
# T9.4 — suy giảm theo horizon
# =========================================================================

def run_horizon(store: dict, train_full: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    print("\n" + "=" * 78 + "\nT9.4 — Suy giảm theo horizon (holdout main_548d)\n" + "=" * 78)
    rows = []
    tail_bad = {}
    for target in TARGETS:
        s = store[target]["main_548d"]
        a, tree, b1 = s["actual"], s["tree"], s["b1"]
        ens = 0.5 * tree + 0.5 * b1
        n = len(a)
        seg = {"day_1_365 (lag=actual)": slice(0, 365),
               "day_366_548 (lag=chain/self-pred)": slice(365, n),
               "full_548": slice(0, n)}
        for name, sl in seg.items():
            for mdl, pred in [("B1", b1), ("LightGBM", tree), ("Ensemble_50_50", ens)]:
                m = calc_metrics(a[sl], pred[sl])
                rows.append({"target": target, "segment": name, "model": mdl,
                             "n": (sl.stop or n) - sl.start, "WAPE": m["WAPE"], "MAPE": m["MAPE"]})
        w_head = calc_metrics(a[0:365], ens[0:365])["WAPE"]
        w_tail = calc_metrics(a[365:n], ens[365:n])["WAPE"]
        delta = w_tail - w_head
        tail_bad[target] = delta > TAIL_WAPE_TRIGGER
        print(f"[{target}] Ensemble WAPE  đầu(1-365)={w_head:.2f}%  đuôi(366-{n})={w_tail:.2f}%  "
              f"Δ(đuôi-đầu)={delta:+.2f} điểm -> "
              f"{'ĐUÔI TỆ RÕ (>+5) — kích hoạt thử lag_182' if tail_bad[target] else 'đuôi KHÔNG suy giảm rõ'}")
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DATA / "horizon_degradation.csv", index=False)
    return df, tail_bad


def test_lag182_main(train_full: pd.DataFrame, folds: list) -> pd.DataFrame:
    """Thử thêm lag_182 vào feature set, đo lại đuôi (366-548) trên fold main.
    lag_182 chain: 182<365 nên tra cứu self-pred từ ~ngày 183 (compounding sớm hơn)."""
    print("\n[lag_182] Test bổ sung lag_182 trên fold main (chỉ chạy khi đuôi tệ rõ)...")
    f0 = folds[0]
    rows = []
    FEATS_182 = FEATURE_COLS + ["lag_182"]
    for target in TARGETS:
        train_fit = train_full[train_full["Date"] <= f0["train_fit_end"]].copy()
        holdout = train_full[(train_full["Date"] >= f0["holdout_start"]) &
                             (train_full["Date"] <= f0["holdout_end"])].copy()
        hist_fit = train_fit.set_index("Date")[target].sort_index()

        def lag182(hist, d):
            return lookup_lag(hist, d, lag=182, tol=LAG_TOL)

        lag365_tr = build_static_lag_features(hist_fit, pd.DatetimeIndex(train_fit["Date"]))
        lag182_tr = pd.Series([lag182(hist_fit, d) for d in train_fit["Date"]],
                              index=pd.DatetimeIndex(train_fit["Date"]), name="lag_182")
        X_train = pd.concat([train_fit.set_index("Date")[CALENDAR_FEATURES], lag365_tr, lag182_tr], axis=1)[FEATS_182]
        y_train = train_fit.set_index("Date")[target]
        model = make_models()["LightGBM"]
        model = model.__class__(**model.get_params())
        model.fit(X_train.to_numpy(), y_train.to_numpy())

        # chain có lag_182
        h = hist_fit.copy()
        cal = holdout[["Date"] + CALENDAR_FEATURES].sort_values("Date").reset_index(drop=True)
        preds = np.empty(len(cal))
        for i, r in cal.iterrows():
            d = r["Date"]
            feat = {c: r[c] for c in CALENDAR_FEATURES}
            feat["lag_365"] = lookup_lag(h, d)
            feat["lag_365_smooth7"] = lookup_lag_smooth(h, d)
            feat["lag_182"] = lag182(h, d)
            X = pd.DataFrame([feat])[FEATS_182]
            yhat = max(float(model.predict(X.to_numpy())[0]), 0.0)
            preds[i] = yhat
            h.loc[d] = yhat
        preds = pd.Series(preds, index=cal["Date"]).reindex(holdout["Date"]).to_numpy()
        b1 = seasonal_naive_chain(hist_fit, pd.DatetimeIndex(holdout["Date"]))
        ens = 0.5 * np.clip(preds, 0, None) + 0.5 * b1
        a = holdout[target].to_numpy(); n = len(a)
        for name, sl in [("day_1_365", slice(0, 365)), ("day_366_548", slice(365, n)), ("full_548", slice(0, n))]:
            m = calc_metrics(a[sl], ens[sl])
            rows.append({"target": target, "variant": "Ensemble_+lag182", "segment": name, "WAPE": m["WAPE"]})
        w_tail = calc_metrics(a[365:n], ens[365:n])["WAPE"]
        print(f"[lag_182] {target}: đuôi(366-548) WAPE với +lag182 = {w_tail:.2f}%")
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DATA / "lag182_tail_test.csv", index=False)
    return df


# =========================================================================
# T9.5 — robustness + weight tuning
# =========================================================================

def run_robustness(store: dict, folds: list) -> tuple[pd.DataFrame, dict]:
    print("\n" + "=" * 78 + "\nT9.5 — Robustness (5 fold) + tối ưu weight ensemble\n" + "=" * 78)
    bt = pd.read_csv(P8_DIR / "data" / "backtest_metrics.csv")
    fold_order = [f["label"] for f in folds]
    rolling = [l for l in fold_order if l != "main_548d"]  # validation-only cho chọn weight

    # ---- bảng GB vs LGB vs Ensemble(50/50) qua 5 fold (từ backtest GĐ8) ----
    print("\n[bảng robustness — WAPE % theo fold]")
    robust_rows = []
    for target in TARGETS:
        for mdl, key in [("GradientBoosting", "GradientBoosting"),
                         ("LightGBM", "LightGBM"),
                         ("Ensemble_LGB_B1_50/50", "Ensemble_LightGBM_B1")]:
            sub = bt[(bt.target == target) & (bt.model == key)].set_index("fold")["WAPE"]
            per = {fl: round(float(sub.get(fl, np.nan)), 2) for fl in fold_order}
            roll_avg = float(np.mean([per[fl] for fl in rolling]))
            roll_avg_nobreak = float(np.mean([per[fl] for fl in rolling if fl != "rolling_2"]))
            row = {"target": target, "model": mdl, **per,
                   "avg_rolling": round(roll_avg, 2),
                   "avg_rolling_no_break": round(roll_avg_nobreak, 2)}
            robust_rows.append(row)
            print(f"  {target:<8} {mdl:<24} " +
                  " ".join(f"{fl}={per[fl]:.1f}" for fl in fold_order) +
                  f" | avgRoll={roll_avg:.2f} avgRoll(no break)={roll_avg_nobreak:.2f}")
    robust_df = pd.DataFrame(robust_rows)
    robust_df.to_csv(OUT_DATA / "robustness_table.csv", index=False)

    # ---- grid weight: chọn trên rolling folds (KHÔNG dùng main) ----
    print("\n[weight tuning] grid (trọng số TREE) — chọn theo avg WAPE rolling folds (validation), "
          "main chỉ để BÁO CÁO:")
    weight_rows = []
    chosen = {}
    for target in TARGETS:
        best = None
        for w in WEIGHT_GRID:
            per = {}
            for fl in fold_order:
                s = store[target][fl]
                ens = w * s["tree"] + (1 - w) * s["b1"]
                per[fl] = calc_metrics(s["actual"], ens)["WAPE"]
            roll_avg = float(np.mean([per[fl] for fl in rolling]))
            roll_avg_nobreak = float(np.mean([per[fl] for fl in rolling if fl != "rolling_2"]))
            weight_rows.append({"target": target, "w_tree": w, "main_548d": per["main_548d"],
                                "avg_rolling": roll_avg, "avg_rolling_no_break": roll_avg_nobreak})
            # tiêu chí chọn = avg rolling (không nhìn main -> tránh overfit chọn model)
            if best is None or roll_avg < best[1]:
                best = (w, roll_avg, per["main_548d"], roll_avg_nobreak)
        w05_main = [r for r in weight_rows if r["target"] == target and r["w_tree"] == 0.5][0]["main_548d"]
        w05_roll = [r for r in weight_rows if r["target"] == target and r["w_tree"] == 0.5][0]["avg_rolling"]
        chosen[target] = {"w_best_by_rolling": best[0], "roll_wape": best[1],
                          "main_wape_at_best": best[2], "w05_main": w05_main, "w05_roll": w05_roll}
        print(f"  [{target}] w*(theo rolling)={best[0]}  avgRoll={best[1]:.2f}  main@w*={best[2]:.2f}  "
              f"|| w=0.5: avgRoll={w05_roll:.2f} main={w05_main:.2f}")
    pd.DataFrame(weight_rows).to_csv(OUT_DATA / "weight_grid.csv", index=False)
    return robust_df, chosen


def main():
    train_full = pd.read_csv(F6_DIR / "features_train.csv", parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
    forecast_df = pd.read_csv(F6_DIR / "features_forecast.csv", parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
    folds = build_rolling_folds(train_full)
    print(f"[load] train {train_full.shape} | forecast {forecast_df.shape} | folds={[f['label'] for f in folds]}")

    ss = run_shap(train_full, forecast_df)

    print("\n[regen] tái tạo LightGBM-chain + B1-chain mọi fold (cho T9.4/T9.5)...")
    store = regen_fold_preds(train_full, folds)

    horizon_df, tail_bad = run_horizon(store, train_full)
    lag182_df = None
    if any(tail_bad.values()):
        lag182_df = test_lag182_main(train_full, folds)

    robust_df, chosen = run_robustness(store, folds)

    # -------- quyết định weight/model + (điều kiện) re-forecast --------
    print("\n" + "=" * 78 + "\nQUYẾT ĐỊNH weight / model\n" + "=" * 78)
    changed = {}
    for target in TARGETS:
        c = chosen[target]
        # đổi weight chỉ khi: w* != 0.5 VÀ tốt hơn trên CẢ rolling lẫn main (bằng chứng nhất quán)
        better_roll = c["roll_wape"] < c["w05_roll"] - 1e-6
        better_main = c["main_wape_at_best"] < c["w05_main"] - 1e-6
        do_change = (c["w_best_by_rolling"] != 0.5) and better_roll and better_main
        changed[target] = c["w_best_by_rolling"] if do_change else 0.5
        print(f"[{target}] w*={c['w_best_by_rolling']} betterRoll={better_roll} betterMain={better_main} "
              f"-> {'ĐỔI sang w='+str(c['w_best_by_rolling']) if do_change else 'GIỮ 50/50'}")

    any_change = any(w != 0.5 for w in changed.values())
    if any_change:
        print("\n[RE-FORECAST] weight đổi -> sinh forecast_548_v2.csv + báo tester chạy lại T9.1.")
        out = {"Date": forecast_df["Date"].dt.strftime("%Y-%m-%d")}
        for target in TARGETS:
            model, _, _, hist = fit_lgbm_full(train_full, target)
            tree_fc = recursive_tree_forecast(lambda X, m=model: m.predict(X.to_numpy()),
                                              hist, forecast_df[["Date"] + CALENDAR_FEATURES])
            b1_fc = seasonal_naive_chain(hist, pd.DatetimeIndex(forecast_df["Date"]))
            w = changed[target]
            fc = np.clip(w * tree_fc + (1 - w) * b1_fc, 0, None)
            out[target] = np.round(fc, 2)
        pd.DataFrame(out).to_csv(OUT_DATA / "forecast_548_v2.csv", index=False)
        print("  -> ĐÃ GHI forecast_548_v2.csv (weight:", changed, ")")
    else:
        print("\n[RE-FORECAST] KHÔNG đổi weight/model -> giữ nguyên bản nộp GĐ8 (forecast_548.csv). "
              "Tester KHÔNG cần chạy lại T9.1.")

    print("\nHoàn tất GĐ9. Output:")
    for p in sorted(OUT_DATA.glob("*")):
        print(" -", p)
    for p in sorted(OUT_CHART.glob("09_*.png")):
        print(" -", p)


if __name__ == "__main__":
    main()
