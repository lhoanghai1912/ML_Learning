"""Feature engineering cho forecast Revenue + COGS 548 ngày (Phần B).

Port từ code phase cũ (nhánh `feat/phase8-model`, chưa merge vào `main` lúc
nhánh restructure được tạo — xem `.process_status/M4b.md` mục "Nguồn port"):
    - `EDA_Insight/phase6_features/build_features.py`  (calendar features, Tết)
    - `EDA_Insight/phase8_model/build_model.py`          (lag features + forecast đệ quy)

GIỮ NGUYÊN công thức — không tự đổi. Đọc data qua `datathon.config` (RAW_TABLES),
KHÔNG hardcode path CSV khác.

No-leakage (bắt buộc đọc trước khi sửa file này):
    - Feature lịch (calendar) tại ngày d chỉ dùng thành phần CHÍNH ngày d
      (dow/month/quarter/sin-cos/…) hoặc hằng số neo cố định `TREND_ANCHOR`
      — không đọc target hay dữ liệu tương lai.
    - `days_from_tet` tính từ bảng ngày Tết (âm lịch, tính trước bằng công
      thức lịch, không phụ thuộc dữ liệu bán hàng) — không leak.
    - Feature lag (`lag_365`, `lag_365_smooth7`) tại ngày d chỉ tra cứu lịch
      sử quanh d-365 (±LAG_TOL/SMOOTH_WINDOW) — luôn nhỏ hơn d, không bao giờ
      tra cứu ngày >= d.
    - `build_static_lag_features` (dùng xây X cho TRAIN/train_fit của 1 fold):
      tra từ `hist` = actual đã biết tại thời điểm build; mọi lookup đều lùi
      365 ngày nên an toàn dù `hist` có thể chứa dữ liệu "tương lai" của biến
      khác trong bộ nhớ (ta không bao giờ tra cứu ngày >= d).
    - `recursive_forecast` (dùng cho forecast 548 ngày > 365 ngày lag): lag
      tại ngày d tra từ `hist` gồm actual quá khứ + dự đoán CHÍNH MODEL NÀY đã
      sinh cho ngày < d (chain tuần tự) — KHÔNG BAO GIỜ đọc actual/dự đoán của
      ngày >= d. Đây là lý do bắt buộc phải đệ quy thay vì vector hoá.
"""
from __future__ import annotations

from typing import Callable, Iterable

import numpy as np
import pandas as pd
from lunardate import LunarDate

from datathon import config

TARGETS: list[str] = ["Revenue", "COGS"]

TREND_ANCHOR = pd.Timestamp("2012-07-04")  # neo cố định trend_index=0 (ngày đầu sales.csv)

LAG_DAYS = 365
LAG_TOL = 3
SMOOTH_WINDOW = 3  # lag_365_smooth7 = mean [lag-3 .. lag+3] (7 điểm)

CALENDAR_FEATURES: list[str] = [
    "month", "quarter", "day_of_week", "day_of_month",
    "month_sin", "month_cos", "dow_sin", "dow_cos",
    "is_post_2019", "is_post_2019_transition",
    "days_from_tet", "is_low_margin_season", "trend_index",
    "is_holiday_302_305", "is_holiday_qk", "is_christmas",
]
LAG_FEATURES: list[str] = ["lag_365", "lag_365_smooth7"]
FEATURE_COLS: list[str] = CALENDAR_FEATURES + LAG_FEATURES


# =========================================================================
# Tết (âm lịch) — tính trước bằng công thức lịch, KHÔNG phụ thuộc data bán hàng
# =========================================================================

def build_tet_dates(years: Iterable[int]) -> pd.DataFrame:
    """Ngày Tết dương lịch cho mỗi năm trong `years`, tính bằng lunardate."""
    rows = [
        {"year": y, "tet_date": pd.Timestamp(LunarDate(y, 1, 1).to_solar_date())}
        for y in years
    ]
    return pd.DataFrame(rows)


def _tet_dates_for(dates: pd.Series) -> pd.Series:
    """Bảng Tết đủ phủ `dates` ± 1 năm (đảm bảo luôn có Tết liền trước/liền
    sau mọi ngày trong `dates` để tra "gần nhất" không bị lệch biên)."""
    d = pd.to_datetime(dates)
    y_min, y_max = int(d.dt.year.min()), int(d.dt.year.max())
    return build_tet_dates(range(y_min - 1, y_max + 2))["tet_date"]


def compute_days_from_tet(dates: pd.Series, tet_dates: pd.Series) -> np.ndarray:
    """Số ngày có dấu tới Tết GẦN NHẤT (âm=trước Tết, dương=sau Tết), liên tục
    qua ranh giới năm dương lịch (vectorized bằng searchsorted)."""
    tet_sorted = np.sort(tet_dates.values.astype("datetime64[D]"))
    d = pd.to_datetime(dates).values.astype("datetime64[D]")

    idx_right = np.searchsorted(tet_sorted, d, side="left")
    idx_right_c = np.clip(idx_right, 0, len(tet_sorted) - 1)
    idx_left_c = np.clip(idx_right - 1, 0, len(tet_sorted) - 1)

    delta_right = (d - tet_sorted[idx_right_c]).astype("timedelta64[D]").astype(int)
    delta_left = (d - tet_sorted[idx_left_c]).astype("timedelta64[D]").astype(int)

    pick_left = np.abs(delta_left) <= np.abs(delta_right)
    return np.where(pick_left, delta_left, delta_right)


# =========================================================================
# Calendar features (dùng chung cho train + forecast — không leakage)
# =========================================================================

def build_calendar_features(dates: pd.Series, tet_dates: pd.Series) -> pd.DataFrame:
    """Ma trận feature lịch cho `dates`. Mỗi hàng chỉ dùng thông tin của
    CHÍNH ngày đó (lịch dương/âm, hằng số neo) — an toàn dùng cho cả ngày
    tương lai (forecast) vì không tra cứu target."""
    d = pd.Series(pd.to_datetime(dates)).reset_index(drop=True)
    f = pd.DataFrame({"Date": d})

    f["month"] = d.dt.month
    f["quarter"] = d.dt.quarter
    f["day_of_week"] = d.dt.dayofweek  # 0 = Thứ Hai
    f["day_of_month"] = d.dt.day

    f["month_sin"] = np.sin(2 * np.pi * f["month"] / 12)
    f["month_cos"] = np.cos(2 * np.pi * f["month"] / 12)
    f["dow_sin"] = np.sin(2 * np.pi * f["day_of_week"] / 7)
    f["dow_cos"] = np.cos(2 * np.pi * f["day_of_week"] / 7)

    f["is_post_2019"] = (d >= pd.Timestamp("2019-01-01")).astype(int)
    f["is_post_2019_transition"] = (
        (d >= pd.Timestamp("2019-01-01")) & (d <= pd.Timestamp("2021-12-31"))
    ).astype(int)

    f["days_from_tet"] = compute_days_from_tet(d, tet_dates)

    f["is_low_margin_season"] = f["month"].isin([7, 8, 9, 11, 12]).astype(int)

    f["trend_index"] = (d - TREND_ANCHOR).dt.days

    month_day = d.dt.strftime("%m-%d")
    f["is_holiday_302_305"] = month_day.isin(["04-30", "05-01"]).astype(int)
    f["is_holiday_qk"] = (month_day == "09-02").astype(int)
    f["is_christmas"] = (month_day == "12-25").astype(int)

    return f


# =========================================================================
# Lag features (365 ngày) — chỉ tra cứu quá khứ, KHÔNG dùng future info
# =========================================================================

def lookup_lag(hist: pd.Series, d: pd.Timestamp, lag: int = LAG_DAYS, tol: int = LAG_TOL) -> float:
    """Giá trị `hist` tại d-lag (±tol nếu thiếu đúng ngày); fallback mean(hist)
    nếu vùng lân cận cũng thiếu. `hist` chỉ chứa dữ liệu tính tới < d."""
    lag_date = d - pd.Timedelta(days=lag)
    if lag_date in hist.index:
        return float(hist.loc[lag_date])
    for delta in range(1, tol + 1):
        for cand in (lag_date - pd.Timedelta(days=delta), lag_date + pd.Timedelta(days=delta)):
            if cand in hist.index:
                return float(hist.loc[cand])
    return float(hist.mean())


def lookup_lag_smooth(
    hist: pd.Series, d: pd.Timestamp, lag: int = LAG_DAYS, window: int = SMOOTH_WINDOW
) -> float:
    """Trung bình `hist` quanh d-lag (±window) — làm mượt nhiễu 1 ngày lẻ."""
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
    """Lag feature cho tập TRAIN (mọi ngày d trong `dates` tra cứu tĩnh, không
    chain). An toàn: với mọi d, lookup luôn ở d-365(±tol) < d."""
    lags, smooths = [], []
    for d in dates:
        lags.append(lookup_lag(hist, d))
        smooths.append(lookup_lag_smooth(hist, d))
    return pd.DataFrame({"lag_365": lags, "lag_365_smooth7": smooths}, index=dates)


def seasonal_naive_chain(hist: pd.Series, dates: pd.DatetimeIndex) -> np.ndarray:
    """Baseline B1 seasonal-naive (chain): dự đoán ngày d = lag_365 tra từ
    `hist` (actual + dự đoán trước đó của CHÍNH baseline này) rồi ghi lại vào
    `hist` cho ngày sau tra — không đọc actual của ngày >= d."""
    h = hist.copy()
    preds: dict[pd.Timestamp, float] = {}
    for d in sorted(dates):
        val = lookup_lag(h, d)
        preds[d] = val
        h.loc[d] = val
    return pd.Series(preds).reindex(dates).to_numpy()


def recursive_forecast(
    predict_fn: Callable[[pd.DataFrame], np.ndarray],
    hist: pd.Series,
    calendar_df: pd.DataFrame,
    feature_cols: list[str] = FEATURE_COLS,
) -> np.ndarray:
    """Dự báo tuần tự ngày-qua-ngày cho horizon > LAG_DAYS (548 > 365): lag tại
    ngày d tra từ `hist` = actual quá khứ + dự đoán CHÍNH model này đã sinh cho
    ngày < d (KHÔNG bao giờ actual/dự đoán ngày >= d) — bắt buộc đệ quy."""
    h = hist.copy()
    cal_sorted = calendar_df.sort_values("Date").reset_index(drop=True)
    calendar_cols = [c for c in feature_cols if c not in ("lag_365", "lag_365_smooth7")]
    preds = np.empty(len(cal_sorted))
    for i, row in cal_sorted.iterrows():
        d = row["Date"]
        lag_val = lookup_lag(h, d)
        smooth_val = lookup_lag_smooth(h, d)
        feat = {c: row[c] for c in calendar_cols}
        feat["lag_365"] = lag_val
        feat["lag_365_smooth7"] = smooth_val
        X = pd.DataFrame([feat])[feature_cols]
        yhat = float(predict_fn(X)[0])
        yhat = max(yhat, 0.0)
        preds[i] = yhat
        h.loc[d] = yhat
    out = pd.Series(preds, index=cal_sorted["Date"]).reindex(calendar_df["Date"]).to_numpy()
    return out


# =========================================================================
# Load features từ raw CSV (qua config.RAW_TABLES — nguồn path duy nhất)
# =========================================================================

def load_train_features() -> pd.DataFrame:
    """Feature train: mọi ngày `sales.csv` (2012-2022) + target Revenue/COGS."""
    sales = pd.read_csv(config.RAW_TABLES["sales"], parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
    assert not sales["Date"].duplicated().any(), "sales.csv có ngày trùng"
    assert sales["Date"].is_monotonic_increasing, "sales.csv không theo thứ tự ngày tăng dần"

    tet_dates = _tet_dates_for(sales["Date"])
    feats = build_calendar_features(sales["Date"], tet_dates)
    train = feats.merge(sales[["Date", "Revenue", "COGS"]], on="Date", how="left")
    assert train["Revenue"].notna().all() and train["COGS"].notna().all(), "target NaN sau khi join"
    assert len(train) == len(sales), "số dòng train khác số dòng sales.csv gốc"
    return train


def load_forecast_features() -> pd.DataFrame:
    """Feature forecast: 548 ngày của `sample_submission.csv` (không có target
    — đây là horizon cần dự báo, KHÔNG dùng để leak vào train)."""
    sub = pd.read_csv(config.RAW_TABLES["sample_submission"], parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
    assert not sub["Date"].duplicated().any(), "sample_submission.csv có ngày trùng"
    assert sub["Date"].is_monotonic_increasing, "sample_submission.csv không theo thứ tự ngày tăng dần"
    assert len(sub) == 548, f"sample_submission.csv không phải 548 dòng, đang là {len(sub)}"

    tet_dates = _tet_dates_for(sub["Date"])
    feats = build_calendar_features(sub["Date"], tet_dates)
    assert len(feats) == 548
    assert set(feats["Date"]) == set(sub["Date"]), "tập ngày forecast KHÔNG khớp sample_submission.csv"
    return feats
