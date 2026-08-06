"""T9.1 — Independent submission-format check.
QA gate. Recompute everything, trust nothing from ds report.
Run: .venv/bin/python EDA_Insight/phase9_validation/t91_format_check.py
"""
import sys
import pandas as pd

ROOT = "/Users/lhoanghai_/Documents/Study/Dự án datathon2026"
SAMPLE = f"{ROOT}/data/sample_submission.csv"
SUBMIT = f"{ROOT}/EDA_Insight/phase8_model/data/forecast_548.csv"

results = []  # (criterion, pass/fail, detail)


def check(name, ok, detail):
    results.append((name, "PASS" if ok else "FAIL", detail))


# ---- read raw bytes first (encoding + line ending) ----
with open(SAMPLE, "rb") as f:
    raw_sample = f.read()
with open(SUBMIT, "rb") as f:
    raw_submit = f.read()

# encoding: try strict utf-8 decode
try:
    raw_submit.decode("utf-8")
    submit_utf8 = True
except UnicodeDecodeError:
    submit_utf8 = False
try:
    raw_sample.decode("utf-8")
    sample_utf8 = True
except UnicodeDecodeError:
    sample_utf8 = False
check("Encoding submit = UTF-8", submit_utf8,
      f"submit utf8={submit_utf8}; sample utf8={sample_utf8}")

# line ending
sample_crlf = raw_sample.count(b"\r\n")
submit_crlf = raw_submit.count(b"\r\n")
sample_lf_only = raw_sample.count(b"\n") - sample_crlf
submit_lf_only = raw_submit.count(b"\n") - submit_crlf
sample_le = "CRLF" if sample_crlf > 0 and sample_lf_only == 0 else ("LF" if sample_crlf == 0 else "MIXED")
submit_le = "CRLF" if submit_crlf > 0 and submit_lf_only == 0 else ("LF" if submit_crlf == 0 else "MIXED")
check("Line-ending matches sample", sample_le == submit_le,
      f"sample={sample_le} (crlf={sample_crlf}), submit={submit_le} (crlf={submit_crlf})")

# ---- parse ----
sample = pd.read_csv(SAMPLE)
sub = pd.read_csv(SUBMIT, dtype={"Date": str})

# column names + order
cols_ok = list(sub.columns) == list(sample.columns)
check("Column names+order == sample", cols_ok,
      f"sample={list(sample.columns)}, submit={list(sub.columns)}")

# expected exact
exp_cols = ["Date", "Revenue", "COGS"]
check("Columns exactly [Date,Revenue,COGS]", list(sub.columns) == exp_cols,
      f"got {list(sub.columns)}")

# row count
check("Row count == 548", len(sub) == 548, f"rows={len(sub)}")
check("Row count == sample", len(sub) == len(sample), f"submit={len(sub)} sample={len(sample)}")

# date range continuous, no dup, no missing
dates = pd.to_datetime(sub["Date"], format="%Y-%m-%d", errors="coerce")
n_bad_fmt = dates.isna().sum()
check("All Date parse as YYYY-MM-DD", n_bad_fmt == 0, f"unparseable={n_bad_fmt}")

expected = pd.date_range("2023-01-01", "2024-07-01", freq="D")
check("Date range 2023-01-01..2024-07-01", len(expected) == 548 and
      dates.min() == expected.min() and dates.max() == expected.max(),
      f"min={dates.min()} max={dates.max()} n_expected={len(expected)}")

dup = sub["Date"].duplicated().sum()
check("No duplicate dates", dup == 0, f"dup={dup}")

missing = sorted(set(expected) - set(dates.dropna()))
check("No missing days (continuous)", len(missing) == 0,
      f"missing={len(missing)}" + ("" if not missing else f" first={missing[0]}"))

# same date set/order as sample
sample_dates = pd.to_datetime(sample["Date"], format="%Y-%m-%d", errors="coerce")
check("Date order == sample", dates.equals(sample_dates), "elementwise date equality")

# NaN
n_nan = int(sub[["Revenue", "COGS"]].isna().sum().sum())
check("0 NaN in Revenue/COGS", n_nan == 0, f"nan={n_nan}")

# negative
neg_rev = int((pd.to_numeric(sub["Revenue"], errors="coerce") < 0).sum())
neg_cogs = int((pd.to_numeric(sub["COGS"], errors="coerce") < 0).sum())
check("0 negative values", neg_rev == 0 and neg_cogs == 0, f"neg_rev={neg_rev} neg_cogs={neg_cogs}")

# Decimal precision — real rule = rounded to <=2 decimals (matches sample:
# sample itself drops trailing zeros, e.g. '1136463.0'). Gate = no token >2 dp.
def dec_dist(path):
    dist = {}
    over2 = 0
    with open(path, "r", encoding="utf-8", newline="") as f:
        next(f)
        for line in f:
            for tok in line.rstrip("\r\n").split(",")[1:]:
                fl = len(tok.split(".")[1]) if "." in tok else 0
                dist[fl] = dist.get(fl, 0) + 1
                if fl > 2:
                    over2 += 1
    return dict(sorted(dist.items())), over2

sub_dist, sub_over2 = dec_dist(SUBMIT)
smp_dist, _ = dec_dist(SAMPLE)
check("No value >2 decimals (rounded)", sub_over2 == 0,
      f"submit dp-dist={sub_dist} over2={sub_over2}; sample dp-dist={smp_dist} "
      f"(both drop trailing zeros — same style)")

# numeric parse
num_ok = pd.to_numeric(sub["Revenue"], errors="coerce").notna().all() and \
         pd.to_numeric(sub["COGS"], errors="coerce").notna().all()
check("Revenue/COGS all numeric", num_ok, "")

# ---- print table ----
print("\n" + "=" * 78)
print("T9.1 — SUBMISSION FORMAT CHECK (independent)")
print("=" * 78)
w = max(len(r[0]) for r in results)
n_fail = 0
for name, verdict, detail in results:
    mark = "OK " if verdict == "PASS" else ">>>"
    if verdict == "FAIL":
        n_fail += 1
    print(f"{mark} [{verdict}] {name.ljust(w)} | {detail}")
print("=" * 78)
print(f"TOTAL: {len(results)-n_fail} PASS / {n_fail} FAIL")
if n_fail:
    print("RESULT: BLOCKER — at least one FAIL. See '>>>' rows.")
else:
    print("RESULT: T9.1 GO (format).")
print("=" * 78)

# quick value sanity (not a gate, informational)
print("\n[info] submit value summary:")
print(sub[["Revenue", "COGS"]].astype(float).describe().loc[["min", "max", "mean"]].round(2).to_string())
print(f"[info] rows with COGS>Revenue: {int((sub['COGS'].astype(float)>sub['Revenue'].astype(float)).sum())} (no constraint required per GĐ5)")

sys.exit(1 if n_fail else 0)
