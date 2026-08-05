"""10 chiều Data Quality — port từ `docs/analysis/phase0_qc/phase0_full_qc.py` (đã verify thủ công,
xem `phase0_qc_report.md`). KHÔNG làm lại thuật toán, chỉ tổ chức lại thành hàm tái dùng được.

Chuẩn: RESTRUCTURE_AGENTS.md mục "DATA QUALITY CHECK STANDARD (10 chiều)".

    #  Hàm                Chiều                          Severity (action khi sai)
    1  inventory           Snapshot/inventory             HARD_FAIL
    2  validate_schema     Schema & format                QUARANTINE
    3  keys                Grain & candidate key           HARD_FAIL
    4  check_ri            Referential integrity          QUARANTINE
    5  completeness        Completeness                   WARN
    6  business_rules      Business-rule validity         QUARANTINE
    7  time_coverage       Time coverage                  WARN
    8  dup_outlier         Duplicate & outlier            QUARANTINE (dup) / FLAG (outlier)
    9  reconcile           Cross-table reconciliation     HARD_FAIL
    10 write_dq_log        Data-quality log                INFO (tổng hợp, ghi log)

Mỗi hàm trả `list[DQResult]` — KHÔNG raise để dừng pipeline; caller (job M2 / test M5) tự quyết
định hành động (quarantine/fail/warn) dựa vào `.severity` + `.status`. `run_all()` gộp cả 10 chiều
+ ghi log + trả gate tổng.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from datathon import schema as schema_mod
from datathon.config import PROJECT_ROOT
from datathon.ingestion import load_raw, new_batch_id

# Log versioned theo batch — thay `ops.dq_log` Postgres thật (chưa có tới khi M2 dựng infra).
# Cùng schema cột, M2 chỉ cần INSERT INTO ops.dq_log SELECT * FROM CSV này.
DQ_LOG_DIR: Path = PROJECT_ROOT / "docs" / "dq_log"

SEVERITY_BY_DIMENSION: dict[int, str] = {
    1: "HARD_FAIL",
    2: "QUARANTINE",
    3: "HARD_FAIL",
    4: "QUARANTINE",
    5: "WARN",
    6: "QUARANTINE",
    7: "WARN",
    8: "QUARANTINE",
    9: "HARD_FAIL",
    10: "INFO",
}

DIMENSION_NAME: dict[int, str] = {
    1: "inventory",
    2: "validate_schema",
    3: "keys",
    4: "check_ri",
    5: "completeness",
    6: "business_rules",
    7: "time_coverage",
    8: "dup_outlier",
    9: "reconcile",
    10: "write_dq_log",
}


@dataclass
class DQResult:
    """1 dòng kết quả DQ — map trực tiếp sang `ops.dq_log` (batch_id, dimension, table, metric,
    threshold, status)."""

    dimension: int
    name: str
    table: str
    metric: str
    value: float | int | str
    threshold: float | int | str | None
    status: str  # "PASS" | "WARN" | "FAIL"
    severity: str  # "HARD_FAIL" | "QUARANTINE" | "WARN" | "INFO" — hành động khi status != PASS
    detail: str
    batch_id: str


def _result(
    dimension: int, table: str, metric: str, value, threshold, status: str, detail: str, batch_id: str
) -> DQResult:
    return DQResult(
        dimension=dimension,
        name=DIMENSION_NAME[dimension],
        table=table,
        metric=metric,
        value=value,
        threshold=threshold,
        status=status,
        severity=SEVERITY_BY_DIMENSION[dimension],
        detail=detail,
        batch_id=batch_id,
    )


def _load_all(tables: dict[str, pd.DataFrame] | None) -> dict[str, pd.DataFrame]:
    """Load toàn bộ 14 bảng qua `ingestion.load_raw` nếu caller không tự truyền `tables` sẵn có
    (tránh đọc CSV lặp lại giữa các chiều khi gọi từ `run_all`)."""
    if tables is not None:
        return tables
    loaded: dict[str, pd.DataFrame] = {}
    for name in schema_mod.ALL_TABLES:
        try:
            loaded[name] = load_raw(name)
        except FileNotFoundError:
            continue
    return loaded


# ----------------------------------------------------------------------
# 1 — Snapshot / inventory
# ----------------------------------------------------------------------
def inventory(
    tables: dict[str, pd.DataFrame] | None = None, batch_id: str | None = None
) -> list[DQResult]:
    """Chiều 1 — 14 bảng có mặt, số dòng, số cột. Nguồn: phase0_full_qc.py PHẦN 1.
    Thiếu bảng -> FAIL cứng (dừng pipeline, không đoán mò tiếp)."""
    batch_id = batch_id or new_batch_id()
    loaded = _load_all(tables)
    results: list[DQResult] = []
    for table in schema_mod.ALL_TABLES:
        if table not in loaded:
            results.append(
                _result(1, table, "table_present", 0, 1, "FAIL",
                        f"Thiếu bảng '{table}' — không đọc được raw CSV.", batch_id)
            )
            continue
        df = loaded[table]
        results.append(
            _result(1, table, "row_count", len(df), None, "PASS" if len(df) > 0 else "FAIL",
                    f"{len(df):,} dòng, {len(df.columns)} cột.", batch_id)
        )
    return results


# ----------------------------------------------------------------------
# 2 — Schema & format
# ----------------------------------------------------------------------
def validate_schema(df: pd.DataFrame, table: str, batch_id: str | None = None) -> list[DQResult]:
    """Chiều 2 — dtype đúng, enum hợp lệ. Delegate `schema.validate_schema`.
    Sai -> QUARANTINE dòng vi phạm (không drop); thiếu cột hẳn -> FAIL (bảng không dùng được)."""
    batch_id = batch_id or new_batch_id()
    v = schema_mod.validate_schema(df, table)
    results: list[DQResult] = []
    if v.missing_columns:
        results.append(_result(2, table, "missing_columns", len(v.missing_columns), 0, "FAIL",
                                f"Thiếu cột: {v.missing_columns}", batch_id))
    if v.unexpected_columns:
        results.append(_result(2, table, "unexpected_columns", len(v.unexpected_columns), 0, "WARN",
                                f"Cột lạ ngoài allowlist: {v.unexpected_columns}", batch_id))
    for col, n in v.dtype_mismatch.items():
        results.append(_result(2, table, f"dtype_mismatch:{col}", n, 0, "FAIL",
                                f"{n} dòng ép kiểu thất bại ở cột '{col}'.", batch_id))
    for col, n in v.enum_violations.items():
        results.append(_result(2, table, f"enum_violation:{col}", n, 0, "FAIL",
                                f"{n} dòng giá trị ngoài enum ở cột '{col}'.", batch_id))
    if not results:
        results.append(_result(2, table, "schema_ok", v.n_rows, v.n_rows, "PASS",
                                "Không có lỗi dtype/enum/cột.", batch_id))
    return results


# ----------------------------------------------------------------------
# 3 — Grain & candidate key
# ----------------------------------------------------------------------
def keys(df: pd.DataFrame, table: str, batch_id: str | None = None) -> list[DQResult]:
    """Chiều 3 — grain 1 dòng/khóa; `order_items` cần surrogate line id ổn định (grain tự nhiên
    KHÔNG unique, đã biết trước — không coi là lỗi, nhưng vẫn phải có key thay thế unique).
    Sai -> FAIL cứng."""
    batch_id = batch_id or new_batch_id()
    ts = schema_mod.get_schema(table)
    grain = list(ts.grain)
    results: list[DQResult] = []

    missing_grain_cols = [c for c in grain if c not in df.columns]
    if missing_grain_cols:
        results.append(_result(3, table, "grain_columns_missing", len(missing_grain_cols), 0, "FAIL",
                                f"Thiếu cột grain {missing_grain_cols}.", batch_id))
        return results

    dup = int(df.duplicated(subset=grain).sum())
    if ts.grain_unique:
        results.append(_result(3, table, f"dup_grain:{grain}", dup, 0, "PASS" if dup == 0 else "FAIL",
                                f"{dup} dòng trùng grain {grain}.", batch_id))
    else:
        results.append(
            _result(3, table, f"dup_grain_natural:{grain}", dup, None, "PASS",
                    f"{dup} dòng trùng grain tự nhiên {grain} — KHÔNG phải lỗi (dòng hàng hợp lệ, "
                    "khác giá/số lượng); cần surrogate key riêng để unique.", batch_id)
        )
        surrogate = schema_mod.ORDER_ITEMS_SURROGATE_KEY
        if surrogate in df.columns:
            dup_sur = int(df.duplicated(subset=[surrogate]).sum())
            results.append(
                _result(3, table, f"dup_surrogate:{surrogate}", dup_sur, 0,
                        "PASS" if dup_sur == 0 else "FAIL",
                        f"{dup_sur} dòng trùng surrogate key '{surrogate}'.", batch_id)
            )
        else:
            results.append(
                _result(3, table, "surrogate_missing", 1, 0, "FAIL",
                        f"Thiếu cột surrogate '{surrogate}' — chưa build line id ổn định "
                        "(gọi ingestion.build_order_items_line_id trước).", batch_id)
            )
    return results


# ----------------------------------------------------------------------
# 4 — Referential integrity
# ----------------------------------------------------------------------
def check_ri(
    tables: dict[str, pd.DataFrame] | None = None, batch_id: str | None = None
) -> list[DQResult]:
    """Chiều 4 — FK con→cha tồn tại. Port `schema.FK_CHECKS` (phase0 PHẦN 4).
    Sai -> QUARANTINE dòng mồ côi (không drop)."""
    batch_id = batch_id or new_batch_id()
    loaded = _load_all(tables)
    results: list[DQResult] = []
    for child, ck, parent, pk_col in schema_mod.FK_CHECKS:
        if child not in loaded or parent not in loaded:
            results.append(_result(4, child, f"ri_skipped:{ck}->{parent}.{pk_col}", 0, 0, "WARN",
                                    f"Thiếu bảng '{child}' hoặc '{parent}' để check RI.", batch_id))
            continue
        cvals = loaded[child][ck].dropna()
        pvals = set(loaded[parent][pk_col].dropna())
        n_orphan = int((~cvals.isin(pvals)).sum())
        pct = (100.0 * n_orphan / len(cvals)) if len(cvals) else 0.0
        results.append(
            _result(4, child, f"ri_orphan:{ck}->{parent}.{pk_col}", n_orphan, 0,
                    "PASS" if n_orphan == 0 else "FAIL",
                    f"{n_orphan:,}/{len(cvals):,} dòng ({pct:.3f}%) có {ck} không tồn tại "
                    f"trong {parent}.{pk_col}.", batch_id)
        )
    return results


# ----------------------------------------------------------------------
# 5 — Completeness
# ----------------------------------------------------------------------
def completeness(
    df: pd.DataFrame, table: str, batch_id: str | None = None, warn_threshold: float = 0.0
) -> list[DQResult]:
    """Chiều 5 — null rate cột bắt buộc (`schema.required`, đã loại 2 ngoại lệ null hợp lệ).
    Sai -> WARN theo ngưỡng (KHÔNG fail hard, KHÔNG quarantine — theo nguyên tắc "5/7→warn")."""
    batch_id = batch_id or new_batch_id()
    ts = schema_mod.get_schema(table)
    n = len(df)
    results: list[DQResult] = []
    for col in ts.required:
        if col not in df.columns:
            results.append(_result(5, table, f"missing_required_col:{col}", 1, 0, "WARN",
                                    f"Cột bắt buộc '{col}' không có trong data.", batch_id))
            continue
        n_null = int(df[col].isna().sum())
        rate = (n_null / n) if n else 0.0
        status = "PASS" if rate <= warn_threshold else "WARN"
        results.append(
            _result(5, table, f"null_rate:{col}", round(rate, 6), warn_threshold, status,
                    f"{n_null:,}/{n:,} ({rate:.2%}) null ở cột bắt buộc '{col}'.", batch_id)
        )
    return results


# ----------------------------------------------------------------------
# 6 — Business-rule validity
# ----------------------------------------------------------------------
def business_rules(
    tables: dict[str, pd.DataFrame] | None = None,
    batch_id: str | None = None,
    expect_start: str = "2012-07-04",
    expect_end: str = "2022-12-31",
) -> list[DQResult]:
    """Chiều 6 — revenue>=0, cogs>=0, qty>0, date trong biên, status ∈ enum, gross>=net.
    Port phase0 PHẦN 2 (giá trị bất thường theo domain). Sai -> QUARANTINE dòng vi phạm."""
    batch_id = batch_id or new_batch_id()
    loaded = _load_all(tables)
    results: list[DQResult] = []
    start, end = pd.Timestamp(expect_start), pd.Timestamp(expect_end)

    if "sales" in loaded:
        sales = loaded["sales"]
        n_rev_neg = int((sales["Revenue"] < 0).sum())
        n_cogs_neg = int((sales["COGS"] < 0).sum())
        results.append(_result(6, "sales", "revenue_negative", n_rev_neg, 0,
                                "PASS" if n_rev_neg == 0 else "FAIL",
                                f"{n_rev_neg} dòng Revenue < 0 (rule: revenue>=0).", batch_id))
        results.append(_result(6, "sales", "cogs_negative", n_cogs_neg, 0,
                                "PASS" if n_cogs_neg == 0 else "FAIL",
                                f"{n_cogs_neg} dòng COGS < 0 (rule: cogs>=0).", batch_id))

    if "order_items" in loaded:
        items = loaded["order_items"]
        n_qty_bad = int((items["quantity"] <= 0).sum())
        gross = items["quantity"] * items["unit_price"]
        n_gross_lt_net = int((items["discount_amount"] > gross).sum())
        results.append(_result(6, "order_items", "quantity_not_positive", n_qty_bad, 0,
                                "PASS" if n_qty_bad == 0 else "FAIL",
                                f"{n_qty_bad} dòng quantity <= 0 (rule: qty>0).", batch_id))
        results.append(_result(6, "order_items", "gross_lt_net", n_gross_lt_net, 0,
                                "PASS" if n_gross_lt_net == 0 else "FAIL",
                                f"{n_gross_lt_net} dòng discount_amount > gross "
                                "(rule: gross>=net).", batch_id))

    if "orders" in loaded:
        orders = loaded["orders"]
        ts = schema_mod.get_schema("orders")
        n_status_bad = int(
            (~orders["order_status"].astype("string").isin(ts.enums["order_status"])).sum()
        )
        n_date_oob = int((~orders["order_date"].between(start, end)).sum())
        results.append(_result(6, "orders", "status_enum_violation", n_status_bad, 0,
                                "PASS" if n_status_bad == 0 else "FAIL",
                                f"{n_status_bad} dòng order_status ngoài enum "
                                "(rule: status ∈ enum).", batch_id))
        results.append(_result(6, "orders", "order_date_out_of_bounds", n_date_oob, 0,
                                "PASS" if n_date_oob == 0 else "FAIL",
                                f"{n_date_oob} dòng order_date ngoài "
                                f"[{expect_start}, {expect_end}] (rule: date trong biên).", batch_id))
    return results


# ----------------------------------------------------------------------
# 7 — Time coverage
# ----------------------------------------------------------------------
def time_coverage(
    df: pd.DataFrame,
    table: str,
    date_col: str,
    batch_id: str | None = None,
    expect_start: str = "2012-07-04",
    expect_end: str = "2022-12-31",
) -> list[DQResult]:
    """Chiều 7 — phủ ngày liên tục trong biên kỳ vọng, đếm ngày thiếu (`missing_days`,
    port phase0 PHẦN 3). Sai -> WARN (theo nguyên tắc "5/7→warn", không hard fail)."""
    batch_id = batch_id or new_batch_id()
    s = df[date_col].dropna() if date_col in df.columns else pd.Series([], dtype="datetime64[ns]")
    if s.empty:
        return [_result(7, table, f"missing_days:{date_col}", 0, None, "WARN",
                         f"Không có giá trị hợp lệ ở cột ngày '{date_col}'.", batch_id)]
    start = max(s.min(), pd.Timestamp(expect_start))
    end = min(s.max(), pd.Timestamp(expect_end))
    full = pd.date_range(start, end, freq="D")
    have = pd.DatetimeIndex(s.unique())
    missing = full.difference(have)
    status = "PASS" if len(missing) == 0 else "WARN"
    sample = ", ".join(d.strftime("%Y-%m-%d") for d in missing[:5])
    detail = f"{len(missing)} ngày thiếu trong [{start.date()}, {end.date()}]"
    if len(missing):
        detail += f" (vd: {sample}{'...' if len(missing) > 5 else ''})"
    return [_result(7, table, f"missing_days:{date_col}", len(missing), 0, status, detail + ".", batch_id)]


# ----------------------------------------------------------------------
# 8 — Duplicate & outlier
# ----------------------------------------------------------------------
def dup_outlier(
    df: pd.DataFrame,
    table: str,
    batch_id: str | None = None,
    numeric_cols: list[str] | None = None,
    iqr_k: float = 3.0,
) -> list[DQResult]:
    """Chiều 8 — trùng FULL-ROW (business columns, loại cột `_metadata`) -> QUARANTINE.
    Outlier IQR trên cột numeric -> FLAG (không quarantine, chỉ đánh dấu)."""
    batch_id = batch_id or new_batch_id()
    business_cols = [c for c in df.columns if not str(c).startswith("_")]
    n_dup = int(df.duplicated(subset=business_cols).sum())
    results: list[DQResult] = [
        _result(8, table, "duplicate_full_row", n_dup, 0, "PASS" if n_dup == 0 else "FAIL",
                f"{n_dup} dòng trùng toàn bộ business columns.", batch_id)
    ]

    if numeric_cols is None:
        ts = schema_mod.get_schema(table)
        numeric_cols = [c for c, k in ts.columns.items() if k in ("int", "float") and c in df.columns]

    for col in numeric_cols:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if series.empty:
            continue
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lo, hi = q1 - iqr_k * iqr, q3 + iqr_k * iqr
        n_out = int(((series < lo) | (series > hi)).sum())
        if n_out:
            results.append(
                _result(8, table, f"outlier_iqr:{col}", n_out, None, "WARN",
                        f"{n_out} dòng ngoài [{lo:.2f}, {hi:.2f}] (IQR x{iqr_k}) ở cột '{col}' "
                        "— FLAG, không quarantine.", batch_id)
            )
    return results


# ----------------------------------------------------------------------
# 9 — Cross-table reconciliation
# ----------------------------------------------------------------------
def reconcile(
    tables: dict[str, pd.DataFrame] | None = None,
    batch_id: str | None = None,
    mape_threshold: float = 1.0,
    payments_mape_threshold: float = 10.0,
) -> list[DQResult]:
    """Chiều 9 — sales vs order_items (chọn định nghĩa khớp nhất) là check CHÍNH THỨC (target
    definition, port nguyên `thr=1.0` từ phase0 PHẦN 5) -> lệch > `mape_threshold` FAIL cứng.
    payments vs orders CHỈ diagnostic bổ sung (phase0 gốc chỉ print MAPE, không gate) — payment
    ghi theo payment date/khác timing với order_date nên MAPE ngày tự nhiên cao hơn; lệch >
    `payments_mape_threshold` chỉ WARN, KHÔNG kéo gate tổng xuống FAIL."""
    batch_id = batch_id or new_batch_id()
    loaded = _load_all(tables)
    required = {"sales", "order_items", "orders", "products", "payments"}
    if not required.issubset(loaded):
        missing = required - set(loaded)
        return [_result(9, "sales<->order_items", "reconcile_skipped", 0, None, "WARN",
                         f"Thiếu bảng {sorted(missing)} — bỏ qua reconcile.", batch_id)]

    sales_rev = loaded["sales"].set_index("Date")["Revenue"]
    sales_cogs = loaded["sales"].set_index("Date")["COGS"]

    items = loaded["order_items"].copy()
    items["line_revenue"] = items["quantity"] * items["unit_price"] - items["discount_amount"]
    items["line_gross"] = items["quantity"] * items["unit_price"]
    items = items.merge(loaded["products"][["product_id", "cogs"]], on="product_id", how="left")
    items["line_cogs"] = items["quantity"] * items["cogs"]
    df = items.merge(
        loaded["orders"][["order_id", "order_date", "order_status"]], on="order_id", how="left"
    )

    def _mape(mask: pd.Series, col: str, target: pd.Series) -> float:
        daily = df.loc[mask].groupby("order_date")[col].sum()
        joined = pd.concat([target, daily], axis=1, keys=["sales", "rebuilt"]).dropna()
        if joined.empty:
            return float("nan")
        return float(((joined["rebuilt"] - joined["sales"]).abs() / joined["sales"]).mean() * 100)

    all_true = pd.Series(True, index=df.index)
    candidates = {
        "net_all_orders": (all_true, "line_revenue"),
        "gross_all_orders": (all_true, "line_gross"),
        "net_delivered_only": (df["order_status"] == "delivered", "line_revenue"),
    }
    mapes = {name: _mape(mask, col, sales_rev) for name, (mask, col) in candidates.items()}
    best_name = min(mapes, key=lambda k: (math.isnan(mapes[k]), mapes[k]))
    best_mape = mapes[best_name]
    best_mask, _ = candidates[best_name]

    results: list[DQResult] = [
        _result(9, "sales<->order_items", f"revenue_mape:{best_name}", round(best_mape, 4),
                mape_threshold, "PASS" if best_mape <= mape_threshold else "FAIL",
                f"Định nghĩa khớp nhất '{best_name}': MAPE ngày Revenue {best_mape:.3f}%.", batch_id)
    ]

    mape_cogs = _mape(best_mask, "line_cogs", sales_cogs)
    results.append(
        _result(9, "sales<->order_items", f"cogs_mape:{best_name}", round(mape_cogs, 4),
                mape_threshold, "PASS" if mape_cogs <= mape_threshold else "FAIL",
                f"COGS tái dựng (mask '{best_name}'): MAPE ngày {mape_cogs:.3f}%.", batch_id)
    )

    pay_daily = (
        loaded["payments"]
        .merge(loaded["orders"][["order_id", "order_date"]], on="order_id", how="left")
        .groupby("order_date")["payment_value"].sum()
    )
    joined_pay = pd.concat([sales_rev, pay_daily], axis=1, keys=["sales", "payments"]).dropna()
    mape_pay = (
        float(((joined_pay["payments"] - joined_pay["sales"]).abs() / joined_pay["sales"]).mean() * 100)
        if not joined_pay.empty else float("nan")
    )
    results.append(
        _result(9, "sales<->payments", "revenue_mape", round(mape_pay, 4), payments_mape_threshold,
                "PASS" if mape_pay <= payments_mape_threshold else "WARN",
                f"payments.payment_value theo ngày vs sales.Revenue: MAPE {mape_pay:.3f}% "
                "(diagnostic — payment date khác order_date, KHÔNG dùng làm gate chính thức).",
                batch_id)
    )
    return results


# ----------------------------------------------------------------------
# 10 — Data-quality log
# ----------------------------------------------------------------------
def write_dq_log(
    results: list[DQResult], batch_id: str | None = None, out_dir: Path | None = None
) -> pd.DataFrame:
    """Chiều 10 — gộp 1-9 thành log versioned. Ghi `docs/dq_log/dq_log_<batch_id>.csv` (immutable,
    versioned theo batch) + `docs/dq_log/dq_log_latest.csv` (snapshot mới nhất).

    Thay cho `ops.dq_log` Postgres thật (chưa có tới khi M2 dựng infra) — CÙNG schema cột, M2 chỉ
    cần INSERT INTO ops.dq_log SELECT * FROM CSV này, không đổi format.
    """
    out_dir = out_dir or DQ_LOG_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "batch_id": r.batch_id,
            "dimension": r.dimension,
            "dimension_name": r.name,
            "table": r.table,
            "metric": r.metric,
            "value": r.value,
            "threshold": r.threshold,
            "status": r.status,
            "severity": r.severity,
            "detail": r.detail,
            "logged_at": datetime.now(timezone.utc).isoformat(),
        }
        for r in results
    ]
    log_df = pd.DataFrame(rows)
    bid = batch_id or (results[0].batch_id if results else new_batch_id())
    log_df.to_csv(out_dir / f"dq_log_{bid}.csv", index=False)
    log_df.to_csv(out_dir / "dq_log_latest.csv", index=False)
    return log_df


def gate_status(results: list[DQResult]) -> str:
    """PASS / CONDITIONAL / FAIL tổng hợp — FAIL nếu có FAIL ở dimension HARD_FAIL (1/3/9),
    CONDITIONAL nếu có FAIL/WARN ở dimension khác, ngược lại PASS."""
    if any(r.status == "FAIL" and r.severity == "HARD_FAIL" for r in results):
        return "FAIL"
    if any(r.status in ("FAIL", "WARN") for r in results):
        return "CONDITIONAL"
    return "PASS"


def run_all(
    tables: dict[str, pd.DataFrame] | None = None, batch_id: str | None = None
) -> tuple[pd.DataFrame, str]:
    """Chạy đủ 10 chiều DQ trên toàn bộ bảng raw, ghi dq_log, trả (log_df, gate_status)."""
    batch_id = batch_id or new_batch_id()
    loaded = _load_all(tables)
    results: list[DQResult] = []

    results += inventory(loaded, batch_id)
    for table, df in loaded.items():
        results += validate_schema(df, table, batch_id)
        results += keys(df, table, batch_id)
    results += check_ri(loaded, batch_id)
    for table, df in loaded.items():
        results += completeness(df, table, batch_id)
    results += business_rules(loaded, batch_id)

    date_cols_by_table = {
        "orders": "order_date", "sales": "Date", "web_traffic": "date",
        "shipments": "ship_date", "returns": "return_date", "reviews": "review_date",
        "inventory": "snapshot_date", "customers": "signup_date",
    }
    for table, col in date_cols_by_table.items():
        if table in loaded and col in loaded[table].columns:
            results += time_coverage(loaded[table], table, col, batch_id)

    for table, df in loaded.items():
        results += dup_outlier(df, table, batch_id)
    results += reconcile(loaded, batch_id)

    log_df = write_dq_log(results, batch_id)
    return log_df, gate_status(results)
