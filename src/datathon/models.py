"""Model forecast Revenue + COGS 548 ngày (tree-based + ensemble seasonal-naive).

Port từ code phase cũ (nhánh `feat/phase8-model`, chưa merge `main` lúc nhánh
restructure tạo — xem `.process_status/M4b.md` mục "Nguồn port"):
    `EDA_Insight/phase8_model/build_model.py`

GIỮ NGUYÊN thuật toán/hyperparameter/SEED — không tự đổi.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np
import pandas as pd

# LightGBM sklearn wrapper phát UserWarning "X does not have valid feature
# names..." mỗi lần predict(numpy) sau khi fit(numpy) — bug vô hại của thư
# viện (không liên quan đúng/sai kết quả). Tắt để log không phình to khi
# `recursive_forecast` gọi predict() hàng trăm lần/target (548 ngày x nhiều
# fold backtest).
warnings.filterwarnings("ignore", category=UserWarning)
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
import xgboost as xgb
import lightgbm as lgb

from datathon.features import (
    CALENDAR_FEATURES,
    FEATURE_COLS,
    TARGETS,
    build_static_lag_features,
    recursive_forecast,
    seasonal_naive_chain,
)

SEED = 42
np.random.seed(SEED)

# Cấu hình sản xuất — kết quả CHỌN qua rolling-origin backtest gốc (Phase 8:
# `main_548d` fold, xem `docs/analysis/.../phase8_model/data/final_choice.txt`
# port trong `.process_status/M4b.md`). Ghim ở đây để `fit_all()` không phải
# chạy lại backtest tốn kém (4 model x nhiều fold) mỗi lần forecast — ĐÂY LÀ
# cấu hình đã backtest, KHÔNG PHẢI hyperparameter tự chọn mới. Muốn tái tạo
# lựa chọn này từ đầu: `datathon.backtest.select_best_config()`.
FINAL_CONFIG: dict[str, dict] = {
    "Revenue": {"tree_model": "LightGBM", "use_ensemble": True, "use_quarter": False},
    "COGS": {"tree_model": "LightGBM", "use_ensemble": True, "use_quarter": False},
}


def make_model_factories() -> dict[str, object]:
    """4 model tree ứng viên — hyperparameter GHIM nguyên từ Phase 8."""
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


def _clone(estimator: object) -> object:
    return estimator.__class__(**estimator.get_params())


@dataclass
class TargetForecaster:
    """fit()/predict() forecast 1 target (Revenue hoặc COGS).

    fit(train): train tree model (global hoặc per-quarter) trên `train`.
    predict(calendar_df): forecast đệ quy (xem `features.recursive_forecast`)
    + (tùy chọn) ensemble 0.5*tree + 0.5*seasonal-naive B1, clip >= 0.
    """

    target: str
    tree_model: str
    use_ensemble: bool
    use_quarter: bool
    _predict_fn: Optional[Callable[[pd.DataFrame], np.ndarray]] = field(default=None, repr=False)
    _hist: Optional[pd.Series] = field(default=None, repr=False)
    _feature_importance: Optional[pd.Series] = field(default=None, repr=False)

    def fit(self, train: pd.DataFrame) -> "TargetForecaster":
        """train: DataFrame có cột Date + CALENDAR_FEATURES + self.target (xem
        `features.load_train_features()` hoặc 1 lát train_fit của backtest)."""
        hist = train.set_index("Date")[self.target].sort_index()
        lag = build_static_lag_features(hist, pd.DatetimeIndex(train["Date"]))
        X = pd.concat([train.set_index("Date")[CALENDAR_FEATURES], lag], axis=1)
        y = train.set_index("Date")[self.target]

        factories = make_model_factories()
        if self.tree_model not in factories:
            raise ValueError(f"tree_model không hợp lệ: {self.tree_model} (chọn 1 trong {list(factories)})")
        ctor = factories[self.tree_model]

        if self.use_quarter:
            models = {}
            imps = []
            for q in (1, 2, 3, 4):
                mask = X["quarter"] == q
                m = _clone(ctor)
                m.fit(X.loc[mask, FEATURE_COLS].to_numpy(), y.loc[mask].to_numpy())
                models[q] = m
                imps.append(m.feature_importances_)
            self._feature_importance = pd.Series(np.mean(imps, axis=0), index=FEATURE_COLS)

            def predict_fn(Xrow: pd.DataFrame, _models: dict = models) -> np.ndarray:
                q = int(Xrow["quarter"].iloc[0])
                return _models[q].predict(Xrow.to_numpy())
        else:
            model = _clone(ctor)
            model.fit(X[FEATURE_COLS].to_numpy(), y.to_numpy())
            self._feature_importance = pd.Series(model.feature_importances_, index=FEATURE_COLS)

            def predict_fn(Xrow: pd.DataFrame, _m: object = model) -> np.ndarray:
                return _m.predict(Xrow.to_numpy())

        self._predict_fn = predict_fn
        self._hist = hist
        return self

    def predict(self, calendar_df: pd.DataFrame) -> np.ndarray:
        """calendar_df: DataFrame có cột Date + CALENDAR_FEATURES (KHÔNG cột
        target — đây là horizon cần dự báo). Trả mảng dự đoán, clip >= 0."""
        if self._predict_fn is None or self._hist is None:
            raise RuntimeError("TargetForecaster chưa fit(). Gọi .fit(train) trước .predict().")
        tree_fc = recursive_forecast(self._predict_fn, self._hist, calendar_df[["Date"] + CALENDAR_FEATURES])
        if self.use_ensemble:
            b1_fc = seasonal_naive_chain(self._hist, pd.DatetimeIndex(calendar_df["Date"]))
            final = 0.5 * tree_fc + 0.5 * b1_fc
        else:
            final = tree_fc
        return np.clip(final, 0.0, None)

    @property
    def feature_importance(self) -> pd.Series:
        if self._feature_importance is None:
            raise RuntimeError("TargetForecaster chưa fit().")
        return self._feature_importance


def fit_all(
    train: pd.DataFrame, config_map: dict[str, dict] = FINAL_CONFIG
) -> dict[str, TargetForecaster]:
    """fit 1 TargetForecaster cho mỗi target trong `config_map` (mặc định
    `FINAL_CONFIG`, cấu hình sản xuất đã backtest)."""
    forecasters: dict[str, TargetForecaster] = {}
    for target in TARGETS:
        cfg = config_map[target]
        forecasters[target] = TargetForecaster(target=target, **cfg).fit(train)
    return forecasters


def predict_all(
    forecasters: dict[str, TargetForecaster], forecast_calendar: pd.DataFrame
) -> pd.DataFrame:
    """Dự báo mọi target trong `forecasters` trên cùng 1 lịch (`forecast_calendar`).
    Trả DataFrame cột Date + 1 cột / target."""
    out: dict[str, object] = {"Date": forecast_calendar["Date"].reset_index(drop=True)}
    for target, fc in forecasters.items():
        out[target] = fc.predict(forecast_calendar)
    return pd.DataFrame(out)
