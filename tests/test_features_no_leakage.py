"""M5 — test_features_no_leakage.py (QUAN TRỌNG NHẤT)

Mục tiêu: chứng minh feature/forecast tại ngày d KHÔNG BAO GIỜ dùng dữ liệu (actual hay dự
đoán) của ngày >= d. Dùng 2 kỹ thuật ĐỘC LẬP, cả 2 đều assert THẬT (không `assert True`):

  A. "Poison differential" — chèn giá trị tương lai cực đoan (sentinel 1e12) vào `hist` tại
     đúng những ngày nằm trong horizon đang dự báo, rồi so sánh output CÓ poison vs KHÔNG có
     poison. Nếu 2 kết quả khác nhau (hoặc sentinel lọt ra output) => hàm đã đọc tương lai =>
     test FAIL thật (không phải giả định).
  B. "Invariant spy" — monkeypatch `lookup_lag`/`lookup_lag_smooth` (đúng hàm nội bộ
     `recursive_forecast`/`seasonal_naive_chain` gọi) để assert bất biến
     `max(hist_đang_có.index) < ngày_đang_dự_báo` tại MỌI lần gọi trong 1 lần chạy thật —
     bắt lỗi leakage ngay tại nguồn, không chỉ suy luận từ output cuối.

Cả 2 kỹ thuật chạy trên hàm THẬT trong `datathon.features` (không viết lại thuật toán).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import datathon.features as features_mod
from datathon.features import (
    CALENDAR_FEATURES,
    build_calendar_features,
    build_static_lag_features,
    build_tet_dates,
    lookup_lag,
    lookup_lag_smooth,
    recursive_forecast,
    seasonal_naive_chain,
)

POISON = 1e12


def _tet_for_years(start_year: int, end_year: int) -> pd.Series:
    return build_tet_dates(range(start_year, end_year + 1))["tet_date"]


# ---------------------------------------------------------------------------
# 0. lookup_lag / lookup_lag_smooth — nhắm đúng offset d-365, không phải "hôm nay"/tương lai
# ---------------------------------------------------------------------------


def test_lookup_lag_targets_365_days_before_not_today_or_future() -> None:
    base = pd.Timestamp("2021-01-01")
    d = base + pd.Timedelta(days=365)
    hist = pd.Series({
        base: 111.0,                              # ĐÚNG: d - 365
        base + pd.Timedelta(days=200): 222.0,      # gần d hơn nhưng SAI offset (ngoài tol=3)
        d: 999999.0,                               # giá trị "hôm nay" của d — không được đọc
        d + pd.Timedelta(days=10): -1.0,            # tương lai của d — không được đọc
    })
    assert lookup_lag(hist, d) == pytest.approx(111.0)


def test_lookup_lag_smooth_window_stays_before_current_day() -> None:
    base = pd.Timestamp("2021-01-01")
    d = base + pd.Timedelta(days=365)
    # window quanh base (SMOOTH_WINDOW=3): base-3..base+3, tất cả đều < d.
    hist = pd.Series({base + pd.Timedelta(days=k): 10.0 + k for k in range(-3, 4)})
    hist.loc[d] = POISON  # nếu hàm lỡ đọc luôn "hôm nay" của d, trung bình sẽ méo hẳn
    val = lookup_lag_smooth(hist, d)
    expected = float(np.mean([10.0 + k for k in range(-3, 4)]))
    assert val == pytest.approx(expected)
    assert val < POISON / 2  # sentinel không lọt vào kết quả


# ---------------------------------------------------------------------------
# A. Poison differential — recursive_forecast / seasonal_naive_chain / build_static_lag_features
# ---------------------------------------------------------------------------


def _make_hist_and_horizon() -> tuple[pd.Series, pd.DataFrame, pd.DatetimeIndex]:
    """400 ngày hist (quá khứ) + 400 ngày horizon kế tiếp (>LAG_DAYS=365 nên horizon nửa sau
    phải tra lag vào chính vùng đang dự báo — đúng điểm rủi ro leakage nếu đệ quy sai)."""
    hist_dates = pd.date_range("2018-01-01", periods=400, freq="D")
    rng = np.random.default_rng(7)
    hist_vals = 1000 + 5 * np.arange(len(hist_dates)) + rng.normal(0, 15, len(hist_dates))
    hist = pd.Series(hist_vals, index=hist_dates)

    horizon_dates = pd.date_range(hist_dates[-1] + pd.Timedelta(days=1), periods=400, freq="D")
    tet = _tet_for_years(2017, 2021)
    calendar_df = build_calendar_features(horizon_dates, tet)
    return hist, calendar_df, horizon_dates


def test_recursive_forecast_ignores_future_poison_in_hist() -> None:
    hist, calendar_df, horizon_dates = _make_hist_and_horizon()

    def predict_fn(X: pd.DataFrame) -> np.ndarray:
        # model giả định — dùng chính lag feature (deterministic, không random) để output
        # phụ thuộc trực tiếp giá trị được recursive_forecast tra ra cho hist.
        return (0.5 * X["lag_365"] + 0.5 * X["lag_365_smooth7"]).to_numpy()

    clean_out = recursive_forecast(predict_fn, hist, calendar_df)

    poisoned_hist = hist.copy()
    poison_series = pd.Series(POISON, index=horizon_dates)  # "biết trước" toàn bộ tương lai
    poisoned_hist = pd.concat([poisoned_hist, poison_series])

    poisoned_out = recursive_forecast(predict_fn, poisoned_hist, calendar_df)

    assert np.allclose(clean_out, poisoned_out), (
        "recursive_forecast() cho kết quả KHÁC khi hist chứa dữ liệu tương lai -> LEAKAGE THẬT"
    )
    assert not np.any(np.isclose(poisoned_out, POISON, rtol=0, atol=1e3)), (
        "sentinel tương lai lọt thẳng ra output -> LEAKAGE THẬT"
    )


def test_seasonal_naive_chain_ignores_future_poison_in_hist() -> None:
    hist, _calendar_df, horizon_dates = _make_hist_and_horizon()

    clean_out = seasonal_naive_chain(hist, horizon_dates)

    poisoned_hist = pd.concat([hist.copy(), pd.Series(POISON, index=horizon_dates)])
    poisoned_out = seasonal_naive_chain(poisoned_hist, horizon_dates)

    assert np.allclose(clean_out, poisoned_out), (
        "seasonal_naive_chain() bị ảnh hưởng bởi dữ liệu tương lai trong hist -> LEAKAGE THẬT"
    )
    assert not np.any(np.isclose(poisoned_out, POISON, rtol=0, atol=1e3))


def test_build_static_lag_features_ignores_future_poison_in_hist_in_support_zone() -> None:
    """TRAIN dùng `build_static_lag_features` — hist thường == toàn bộ target train. Nếu ai đó
    lỡ truyền `hist` có lẫn dữ liệu SAU `dates` cần build (vd nối nhầm dữ liệu holdout vào train
    hist), kết quả PHẢI không đổi so với hist chỉ chứa đúng lịch sử tới hết `dates` — ÍT NHẤT
    với những ngày `d` đã có đủ window lag thật (`d-365±tol` tồn tại trong hist gốc, "in-support
    zone"). Xem `test_lookup_lag_fallback_mean_is_a_known_look_ahead_limitation` cho vùng KHÔNG
    có window (fallback `hist.mean()`) — đó là 1 giới hạn THẬT đã phát hiện, tách riêng để không
    lẫn với test này."""
    dates = pd.date_range("2019-01-01", periods=500, freq="D")
    rng = np.random.default_rng(3)
    hist = pd.Series(500 + 3 * np.arange(len(dates)) + rng.normal(0, 10, len(dates)), index=dates)

    # in-support: d sao cho d-365(±tol=3) chắc chắn nằm trong hist gốc (hist bắt đầu dates[0]),
    # tức d >= dates[0] + 365 + 3. Cắt dư an toàn (buffer +5 ngày).
    in_support = dates[dates >= dates[0] + pd.Timedelta(days=373)]
    assert len(in_support) > 0

    clean = build_static_lag_features(hist, pd.DatetimeIndex(in_support))

    future_dates = pd.date_range(dates[-1] + pd.Timedelta(days=1), periods=50, freq="D")
    poisoned_hist = pd.concat([hist, pd.Series(POISON, index=future_dates)])
    poisoned = build_static_lag_features(poisoned_hist, pd.DatetimeIndex(in_support))

    pd.testing.assert_frame_equal(clean, poisoned)
    assert not (poisoned == POISON).any().any()


def test_lookup_lag_fallback_mean_is_a_known_look_ahead_limitation() -> None:
    """KNOWN LIMITATION (phát hiện thật khi viết test này, KHÔNG PHẢI bug do M5 gây ra — báo
    PO/M4 để cân nhắc, M5 KHÔNG được sửa `src/datathon/*`):

    `lookup_lag`/`lookup_lag_smooth` khi KHÔNG tìm thấy `d-365(±tol)` trong `hist` sẽ fallback
    `hist.mean()` — trung bình trên TOÀN BỘ `hist` truyền vào, KHÔNG giới hạn `< d`. Trong
    `TargetForecaster.fit()`, `hist` = toàn bộ cột target của `train` (không cắt theo từng
    dòng) -> với các dòng TRAIN đầu tiên (thiếu đúng 365 ngày lịch sử phía trước), `lag_365`
    của dòng đó = trung bình target CẢ CHUỖI (bao gồm dữ liệu SAU ngày đó) -> look-ahead nhẹ.

    Đo thật trên `sales.csv` production (2012-07-04 .. 2022-12-31, 3833 ngày, `Revenue`):
    362/3833 dòng (~9.4%, đúng 2012-07-04 .. 2013-07-01) rơi vào fallback này (xem
    `.process_status/M5.md`). Test này CHARACTERIZE hành vi hiện tại (pass = đúng như observe),
    KHÔNG phải xác nhận đây là chấp nhận được — mục đích: nếu sau này M4 sửa/khác đi, test đỏ
    sẽ báo ngay (regression-lock), và giữ bằng chứng cụ thể cho PO quyết định."""
    dates = pd.date_range("2019-01-01", periods=500, freq="D")
    rng = np.random.default_rng(3)
    hist = pd.Series(500 + 3 * np.arange(len(dates)) + rng.normal(0, 10, len(dates)), index=dates)

    d = dates[0]  # ngày đầu tiên — chắc chắn KHÔNG có window d-365 (hist không phủ trước đó)
    lag_date = d - pd.Timedelta(days=365)
    assert lag_date not in hist.index  # tiền đề: đúng là rơi vào fallback

    value_clean = lookup_lag(hist, d)
    assert value_clean == pytest.approx(hist.mean())  # fallback = mean toàn hist (đúng hiện trạng)

    future_dates = pd.date_range(dates[-1] + pd.Timedelta(days=1), periods=50, freq="D")
    poisoned_hist = pd.concat([hist, pd.Series(POISON, index=future_dates)])
    value_poisoned = lookup_lag(poisoned_hist, d)

    # ĐÂY LÀ ĐIỂM MẤU CHỐT: giá trị lag của ngày ĐẦU TIÊN thay đổi khi hist có thêm dữ liệu
    # tương lai xa (sau toàn bộ `dates`) -> fallback mean() thật sự phụ thuộc tương lai.
    assert value_poisoned != pytest.approx(value_clean), (
        "Nếu assertion này FAIL (2 giá trị bằng nhau) nghĩa là hành vi đã đổi/được vá — "
        "cập nhật lại test + báo PO, KHÔNG tự sửa src/datathon."
    )


# ---------------------------------------------------------------------------
# B. Invariant spy — assert trực tiếp bất biến "chỉ đọc index < ngày đang dự báo"
# ---------------------------------------------------------------------------


def test_recursive_forecast_never_reads_hist_index_ge_current_day(monkeypatch: pytest.MonkeyPatch) -> None:
    hist, calendar_df, horizon_dates = _make_hist_and_horizon()

    orig_lag = features_mod.lookup_lag
    orig_smooth = features_mod.lookup_lag_smooth
    n_calls = {"lag": 0, "smooth": 0}

    def spy_lag(h: pd.Series, d: pd.Timestamp, *a, **kw):
        n_calls["lag"] += 1
        assert len(h) == 0 or h.index.max() < d, f"lookup_lag đọc hist >= {d} -> LEAKAGE"
        return orig_lag(h, d, *a, **kw)

    def spy_smooth(h: pd.Series, d: pd.Timestamp, *a, **kw):
        n_calls["smooth"] += 1
        assert len(h) == 0 or h.index.max() < d, f"lookup_lag_smooth đọc hist >= {d} -> LEAKAGE"
        return orig_smooth(h, d, *a, **kw)

    monkeypatch.setattr(features_mod, "lookup_lag", spy_lag)
    monkeypatch.setattr(features_mod, "lookup_lag_smooth", spy_smooth)

    def predict_fn(X: pd.DataFrame) -> np.ndarray:
        return (0.5 * X["lag_365"] + 0.5 * X["lag_365_smooth7"]).to_numpy()

    out = recursive_forecast(predict_fn, hist, calendar_df)

    # đảm bảo spy THỰC SỰ được gọi đúng số lần kỳ vọng (1 lần/ngày horizon) — không phải test
    # "chạy qua nhưng chẳng kiểm gì" (spy 0 lần vẫn "pass" nếu không assert số lần gọi).
    assert n_calls["lag"] == len(horizon_dates)
    assert n_calls["smooth"] == len(horizon_dates)
    assert len(out) == len(horizon_dates)
    assert np.all(np.isfinite(out))


def test_seasonal_naive_chain_never_reads_hist_index_ge_current_day(monkeypatch: pytest.MonkeyPatch) -> None:
    hist, _calendar_df, horizon_dates = _make_hist_and_horizon()
    orig_lag = features_mod.lookup_lag
    n_calls = 0

    def spy_lag(h: pd.Series, d: pd.Timestamp, *a, **kw):
        nonlocal n_calls
        n_calls += 1
        assert h.index.max() < d, f"lookup_lag (trong seasonal_naive_chain) đọc hist >= {d} -> LEAKAGE"
        return orig_lag(h, d, *a, **kw)

    monkeypatch.setattr(features_mod, "lookup_lag", spy_lag)
    out = seasonal_naive_chain(hist, horizon_dates)

    assert n_calls == len(horizon_dates)
    assert len(out) == len(horizon_dates)


# ---------------------------------------------------------------------------
# C. Calendar features: hàm số THUẦN của chính ngày đó — không leak giữa các dòng cùng batch
# ---------------------------------------------------------------------------


def test_calendar_features_are_row_independent_no_cross_row_leakage() -> None:
    """build_calendar_features(dates) không được đổi giá trị 1 ngày khi ta thêm/bớt các ngày
    KHÁC trong cùng batch — mỗi dòng CHỈ phụ thuộc chính ngày của nó."""
    all_dates = pd.date_range("2020-01-01", periods=60, freq="D")
    tet = _tet_for_years(2019, 2021)

    full = build_calendar_features(all_dates, tet)
    subset_dates = all_dates[[5, 20, 40]]  # không liên tục, xáo thứ tự batch
    subset = build_calendar_features(subset_dates, tet)

    full_by_date = full.set_index("Date")
    subset_by_date = subset.set_index("Date")
    for d in subset_dates:
        pd.testing.assert_series_equal(
            full_by_date.loc[d, CALENDAR_FEATURES],
            subset_by_date.loc[d, CALENDAR_FEATURES],
            check_names=False,
        )


def test_calendar_features_have_no_target_columns() -> None:
    """Bất biến cấu trúc: calendar feature builder KHÔNG có tham số/target nào khác ngoài
    `dates`+`tet_dates` — không thể vô tình nhận Revenue/COGS làm input."""
    import inspect

    sig = inspect.signature(build_calendar_features)
    assert list(sig.parameters) == ["dates", "tet_dates"]
    out = build_calendar_features(
        pd.date_range("2020-01-01", periods=3, freq="D"), _tet_for_years(2019, 2021)
    )
    assert "Revenue" not in out.columns
    assert "COGS" not in out.columns


# ---------------------------------------------------------------------------
# D. Tích hợp thật: TargetForecaster (fit+predict) qua horizon > LAG_DAYS — full pipeline M4b
# ---------------------------------------------------------------------------


def test_target_forecaster_predict_never_reads_future_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fit thật (RandomForest, model nhanh nhất trong 4 ứng viên) trên train tổng hợp nhỏ,
    predict horizon 400 ngày (> LAG_DAYS=365, chain đệ quy chắc chắn kích hoạt), đồng thời gắn
    invariant-spy — nếu `TargetForecaster.predict()` (M4b) đổi cách gọi `recursive_forecast`
    theo hướng leak, test này phải FAIL thật."""
    from datathon.models import TargetForecaster

    train_dates = pd.date_range("2018-01-01", periods=420, freq="D")
    tet = _tet_for_years(2017, 2020)
    train = build_calendar_features(train_dates, tet)
    rng = np.random.default_rng(11)
    train["Revenue"] = 1000 + 4 * np.arange(len(train)) + rng.normal(0, 25, len(train))

    fc = TargetForecaster(
        target="Revenue", tree_model="RandomForest", use_ensemble=False, use_quarter=False
    ).fit(train)

    horizon_dates = pd.date_range(train_dates[-1] + pd.Timedelta(days=1), periods=400, freq="D")
    horizon_tet = _tet_for_years(2017, 2021)
    calendar_df = build_calendar_features(horizon_dates, horizon_tet)

    orig_lag = features_mod.lookup_lag
    orig_smooth = features_mod.lookup_lag_smooth
    violations: list[str] = []

    def spy_lag(h, d, *a, **kw):
        if len(h) and h.index.max() >= d:
            violations.append(f"lookup_lag @ {d}")
        return orig_lag(h, d, *a, **kw)

    def spy_smooth(h, d, *a, **kw):
        if len(h) and h.index.max() >= d:
            violations.append(f"lookup_lag_smooth @ {d}")
        return orig_smooth(h, d, *a, **kw)

    monkeypatch.setattr(features_mod, "lookup_lag", spy_lag)
    monkeypatch.setattr(features_mod, "lookup_lag_smooth", spy_smooth)

    preds = fc.predict(calendar_df[["Date"] + CALENDAR_FEATURES])

    assert violations == [], f"TargetForecaster.predict() leak thật: {violations[:5]}"
    assert len(preds) == len(horizon_dates)
    assert np.all(np.isfinite(preds))
    assert np.all(preds >= 0.0)  # models.py clip >= 0
