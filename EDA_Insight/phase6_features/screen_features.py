"""
Giai đoạn 6b — Sàng lọc feature (DS, chạy độc lập với de).

CHỈ ĐỌC: data/sales.csv
GHI: EDA_Insight/phase6_features/data/*, EDA_Insight/output/phase6/screen_*.png

Script này KHÔNG đọc bất kỳ file nào de sinh ra (build_features.py, features_train.csv,
features_forecast.csv, tet_dates_extended.csv). Toàn bộ feature lịch tự tính lại từ đầu
bằng lunardate, dùng để đối chiếu ("hợp đồng" feature_spec.md) với ma trận feature của de.

Chạy: .venv/bin/python EDA_Insight/phase6_features/screen_features.py
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from lunardate import LunarDate
from scipy import stats

warnings.filterwarnings("ignore", category=DeprecationWarning)

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUT_DATA = Path(__file__).resolve().parent / "data"
OUT_CHART = ROOT / "EDA_Insight" / "output" / "phase6"
OUT_DATA.mkdir(parents=True, exist_ok=True)
OUT_CHART.mkdir(parents=True, exist_ok=True)

TREND_ORIGIN = pd.Timestamp("2012-07-04")  # ngày đầu tiên của sales.csv


# ---------------------------------------------------------------------------
# 1. Tết: tự tính bằng lunardate, KHÔNG đọc tet_dates.csv của phase1 hay de
# ---------------------------------------------------------------------------
def build_tet_dates(years: range) -> pd.DataFrame:
    rows = []
    for y in years:
        d = LunarDate(y, 1, 1).to_solar_date()
        rows.append({"year": y, "tet_date": pd.Timestamp(d)})
    return pd.DataFrame(rows)


def compute_days_from_tet(dates: pd.Series, tet_df: pd.DataFrame) -> pd.Series:
    """Số ngày có dấu tới Tết GẦN NHẤT (âm = trước Tết, dương = sau Tết).

    Với mỗi ngày, xét Tết năm đó và Tết năm liền kề (trước/sau), chọn Tết
    có |khoảng cách| nhỏ nhất -> đảm bảo liên tục qua ranh giới năm dương lịch.
    """
    tet_sorted = tet_df.sort_values("tet_date").reset_index(drop=True)
    tet_dates = tet_sorted["tet_date"].to_numpy()

    result = np.empty(len(dates), dtype="int64")
    dates_arr = pd.to_datetime(dates).to_numpy()
    idx_pos = np.searchsorted(tet_dates, dates_arr, side="left")

    for i, (d, pos) in enumerate(zip(dates_arr, idx_pos)):
        candidates = []
        for j in (pos - 1, pos, pos + 1):
            if 0 <= j < len(tet_dates):
                candidates.append(tet_dates[j])
        diffs = [(d - c) / np.timedelta64(1, "D") for c in candidates]
        best = min(diffs, key=lambda x: abs(x))
        result[i] = int(round(best))
    return pd.Series(result, index=dates.index)


VN_HOLIDAYS_FIXED = [
    (4, 30),
    (5, 1),
    (9, 2),
    (12, 25),
]


def build_features(dates: pd.Series, tet_df: pd.DataFrame) -> pd.DataFrame:
    dt = pd.to_datetime(dates)
    df = pd.DataFrame({"Date": dt})

    df["year"] = dt.dt.year
    df["month"] = dt.dt.month
    df["quarter"] = dt.dt.quarter
    df["day_of_week"] = dt.dt.weekday  # 0 = Thứ Hai
    df["day_of_month"] = dt.dt.day

    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

    df["is_post_2019"] = (dt >= pd.Timestamp("2019-01-01")).astype(int)
    df["is_post_2019_transition"] = (
        (dt >= pd.Timestamp("2019-01-01")) & (dt <= pd.Timestamp("2021-12-31"))
    ).astype(int)

    df["days_from_tet"] = compute_days_from_tet(df["Date"], tet_df)

    df["is_low_margin_season"] = df["month"].isin([7, 8, 9, 11, 12]).astype(int)

    df["trend_index"] = (dt - TREND_ORIGIN).dt.days

    is_holiday = pd.Series(False, index=df.index)
    for m, d in VN_HOLIDAYS_FIXED:
        is_holiday |= (df["month"] == m) & (df["day_of_month"] == d)
    df["is_vn_holiday"] = is_holiday.astype(int)

    return df


# ---------------------------------------------------------------------------
# 2. Load sales.csv (CHỈ ĐỌC), build feature cho đúng range train
# ---------------------------------------------------------------------------
def load_sales() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "sales.csv", parse_dates=["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    return df


def main():
    sales = load_sales()
    print(f"[load] sales.csv: {sales.shape[0]} ngày, {sales['Date'].min().date()} -> {sales['Date'].max().date()}")

    tet_df = build_tet_dates(range(2011, 2026))
    tet_df.to_csv(OUT_DATA / "tet_dates_ds_check.csv", index=False)
    print("\n[Tết tự tính bằng lunardate 2011-2025 — đối chiếu độc lập]")
    print(tet_df.to_string(index=False))

    feat = build_features(sales["Date"], tet_df)
    feat = feat.merge(sales, on="Date", how="left")

    # ---------------- Validate days_from_tet quanh vài mốc Tết ----------------
    print("\n[Validate days_from_tet quanh Tết 2019 (2019-02-05)]")
    mask = (feat["Date"] >= "2019-01-28") & (feat["Date"] <= "2019-02-12")
    print(feat.loc[mask, ["Date", "days_from_tet"]].to_string(index=False))

    print("\n[Validate days_from_tet quanh Tết 2023 (2023-01-22) — NGOÀI range train,"
          " chỉ minh hoạ công thức tự tính, không lấy từ sales.csv]")
    tet_2023_window = pd.date_range("2023-01-15", "2023-01-29")
    tmp = build_features(pd.Series(tet_2023_window), tet_df)
    print(tmp[["Date", "days_from_tet"]].to_string(index=False))

    print("\n[Validate days_from_tet quanh Tết 2024 (2024-02-10) — NGOÀI range train]")
    tet_2024_window = pd.date_range("2024-02-03", "2024-02-17")
    tmp2 = build_features(pd.Series(tet_2024_window), tet_df)
    print(tmp2[["Date", "days_from_tet"]].to_string(index=False))

    print("\n[Validate liên tục qua ranh giới năm dương lịch: 2019-12-25 -> 2020-01-05"
          " (giữa Tết 2019 (02-05) và Tết 2020 (01-25))]")
    mask2 = (feat["Date"] >= "2019-12-25") & (feat["Date"] <= "2020-01-05")
    print(feat.loc[mask2, ["Date", "days_from_tet"]].to_string(index=False))

    # ---------------- Sàng lọc tương quan feature-target ----------------
    numeric_cont = [
        "year", "month", "quarter", "day_of_week", "day_of_month",
        "month_sin", "month_cos", "dow_sin", "dow_cos", "days_from_tet", "trend_index",
    ]
    binary_feats = ["is_post_2019", "is_post_2019_transition", "is_low_margin_season", "is_vn_holiday"]

    rows = []
    for col in numeric_cont:
        for target in ["Revenue", "COGS"]:
            pear_r, pear_p = stats.pearsonr(feat[col], feat[target])
            spear_r, spear_p = stats.spearmanr(feat[col], feat[target])
            rows.append({
                "feature": col, "type": "continuous", "target": target,
                "pearson_r": round(pear_r, 4), "pearson_p": round(pear_p, 6),
                "spearman_r": round(spear_r, 4), "spearman_p": round(spear_p, 6),
                "group_mean_diff": np.nan,
            })

    for col in binary_feats:
        for target in ["Revenue", "COGS"]:
            g1 = feat.loc[feat[col] == 1, target]
            g0 = feat.loc[feat[col] == 0, target]
            pear_r, pear_p = stats.pearsonr(feat[col], feat[target])
            spear_r, spear_p = stats.spearmanr(feat[col], feat[target])
            diff = g1.mean() - g0.mean()
            rows.append({
                "feature": col, "type": "binary", "target": target,
                "pearson_r": round(pear_r, 4), "pearson_p": round(pear_p, 6),
                "spearman_r": round(spear_r, 4), "spearman_p": round(spear_p, 6),
                "group_mean_diff": round(diff, 2),
            })

    corr_df = pd.DataFrame(rows)
    corr_df.to_csv(OUT_DATA / "feature_target_correlation.csv", index=False)
    print("\n[Tương quan feature-target] (Pearson/Spearman, n=%d ngày, range train)" % len(feat))
    print(corr_df.to_string(index=False))

    # ---------------- Chart minh hoạ sàng lọc ----------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        pivot = corr_df.pivot_table(index="feature", columns="target", values="pearson_r")
        pivot = pivot.reindex(numeric_cont + binary_feats)
        fig, ax = plt.subplots(figsize=(6, 8))
        im = ax.imshow(pivot.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns)
        for i in range(pivot.shape[0]):
            for j in range(pivot.shape[1]):
                v = pivot.values[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8)
        fig.colorbar(im, ax=ax, label="Pearson r")
        ax.set_title("Sàng lọc: tương quan feature-target (Pearson)")
        fig.tight_layout()
        fig.savefig(OUT_CHART / "screen_feature_target_corr_heatmap.png", dpi=120)
        plt.close(fig)
        print(f"\n[chart] {OUT_CHART / 'screen_feature_target_corr_heatmap.png'}")
    except ImportError:
        print("\n[chart] matplotlib không có sẵn, bỏ qua bước vẽ chart (không bắt buộc).")

    # ---------------- Phân tích dư thừa (redundancy) ----------------
    print("\n[Redundancy check] tương quan chéo month vs quarter vs month_sin/cos")
    redundancy_cols = ["month", "quarter", "month_sin", "month_cos", "day_of_month", "trend_index", "year", "is_post_2019"]
    red_corr = feat[redundancy_cols].corr(method="spearman").round(3)
    red_corr.to_csv(OUT_DATA / "redundancy_correlation_matrix.csv")
    print(red_corr.to_string())

    print("\nHoàn tất. File output:")
    print(f" - {OUT_DATA / 'feature_target_correlation.csv'}")
    print(f" - {OUT_DATA / 'redundancy_correlation_matrix.csv'}")
    print(f" - {OUT_DATA / 'tet_dates_ds_check.csv'}")


if __name__ == "__main__":
    main()
