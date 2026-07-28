"""
QC0.7 -- Time coverage -- @da
Doc range min/max + so ngay thieu (calendar-day gap) cho moi bang co truong thoi gian.
Output: da/qc07_timecoverage.csv + da/qc07_note.md
KHONG sua data.
"""
import pandas as pd
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(REPO, "data")
OUT = os.path.dirname(os.path.abspath(__file__))

# (table, date_col, is_daily_series) -- is_daily_series=False cho bang su kien roi rac
# (promotions: 50 chuong trinh, khong phai 1 dong/ngay) hoac panel thang (inventory).
SPECS = [
    ("sales", "Date", "daily"),
    ("orders", "order_date", "daily_multi"),      # nhieu don/ngay, kiem tra distinct-day coverage
    ("web_traffic", "date", "daily"),
    ("inventory", "snapshot_date", "monthly"),
    ("promotions", "start_date", "event"),
    ("promotions", "end_date", "event"),
    ("reviews", "review_date", "daily_multi"),
    ("returns", "return_date", "daily_multi"),
    ("shipments", "ship_date", "daily_multi"),
    ("shipments", "delivery_date", "daily_multi"),
    ("sample_submission", "Date", "daily"),
]


def load_dates(table, col):
    df = pd.read_csv(os.path.join(DATA, f"{table}.csv"))
    return pd.to_datetime(df[col])


def analyze(table, col, kind):
    dates = load_dates(table, col).dropna()
    n_rows = len(dates)
    dmin, dmax = dates.min(), dates.max()

    if kind == "monthly":
        full_range = pd.date_range(dmin, dmax, freq="ME")
        distinct = dates.dt.normalize().nunique()
        span_units = len(full_range)
        missing_units = span_units - distinct
        unit = "months"
    elif kind == "event":
        span_units = (dmax - dmin).days + 1
        distinct = dates.nunique()
        missing_units = None  # khong ap dung — day la danh sach su kien, khong phai daily series
        unit = "days(span, KHONG phai daily series)"
    else:
        full_range = pd.date_range(dmin, dmax, freq="D")
        span_units = len(full_range)
        distinct = dates.dt.normalize().nunique()
        missing_units = span_units - distinct
        unit = "days"

    missing_list = []
    if kind in ("daily", "daily_multi") and missing_units and 0 < missing_units:
        present = set(dates.dt.normalize().unique())
        missing_list = sorted(d.strftime("%Y-%m-%d") for d in full_range if d not in present)

    return {
        "table": table,
        "date_col": col,
        "kind": kind,
        "n_rows": n_rows,
        "date_min": dmin.strftime("%Y-%m-%d"),
        "date_max": dmax.strftime("%Y-%m-%d"),
        "span_units": span_units,
        "unit": unit,
        "distinct_units_with_data": distinct,
        "missing_units": missing_units if missing_units is not None else "N/A (event list)",
        "missing_sample": "; ".join(missing_list[:10]) + (f" ... (+{len(missing_list)-10} more)" if len(missing_list) > 10 else ""),
    }


def main():
    rows = [analyze(t, c, k) for t, c, k in SPECS]
    df = pd.DataFrame(rows)
    out_path = os.path.join(OUT, "qc07_timecoverage.csv")
    df.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")
    print(df[["table", "date_col", "date_min", "date_max", "span_units", "missing_units"]].to_string(index=False))


if __name__ == "__main__":
    main()
