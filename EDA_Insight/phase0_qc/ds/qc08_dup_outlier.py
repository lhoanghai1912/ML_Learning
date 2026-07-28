"""
QC0.8 - Duplicate & outlier check
Owner: @ds. Dep: QC0.3 (grain/key, done).
KHONG sua data - chi doc va bao cao.

Output: EDA_Insight/phase0_qc/ds/qc08_dup_outlier.csv
Marker: EDA_Insight/phase0_qc/_status/qc08.done
"""
import pandas as pd
import numpy as np
import os

ROOT = "/Users/lhoanghai_/Documents/Study/Dự án datathon2026"
DATA = os.path.join(ROOT, "data")
OUT_DIR = os.path.join(ROOT, "EDA_Insight/phase0_qc/ds")
STATUS_DIR = os.path.join(ROOT, "EDA_Insight/phase0_qc/_status")

rows = []  # list of dict -> final csv


def add(check_type, table, col_or_key, method, count, total, rate, detail, classification):
    rows.append({
        "check_type": check_type,       # dup_fullrow | dup_key | outlier | invalid_value
        "table": table,
        "col_or_key": col_or_key,
        "method": method,               # exact | IQR | zscore | rule
        "count": count,
        "total_rows": total,
        "rate_pct": round(rate, 4) if total else 0,
        "detail": detail,
        "classification": classification,  # outlier_that | loi_nhap | hop_le_nghiep_vu | can_xem_lai
    })


# ---------------------------------------------------------------
# 1) FULL-ROW DUPLICATE - tat ca 14 bang
# ---------------------------------------------------------------
tables = {
    "customers": "customer_id",
    "products": "product_id",
    "geography": "zip",
    "orders": "order_id",
    "payments": "order_id",
    "order_items": ["order_id", "product_id"],
    "shipments": "order_id",
    "reviews": "review_id",
    "returns": "return_id",
    "promotions": "promo_id",
    "inventory": ["snapshot_date", "product_id"],
    "web_traffic": "date",
    "sales": "Date",
    "sample_submission": "Date",
}

dfs = {}
for t in tables:
    dfs[t] = pd.read_csv(os.path.join(DATA, f"{t}.csv"))

for t, df in dfs.items():
    n = len(df)
    dup_full = df.duplicated(keep="first").sum()
    add("dup_fullrow", t, "ALL_COLS", "exact", int(dup_full), n,
        dup_full / n * 100 if n else 0,
        f"{dup_full} dong trung toan bo cot (giu ban dau, dem ban lap)",
        "loi_nhap" if dup_full > 0 else "hop_le_nghiep_vu")

# ---------------------------------------------------------------
# 2) DUP THEO CANDIDATE KEY - trong tam order_items (order_id+product_id)
# ---------------------------------------------------------------
for t, key in tables.items():
    df = dfs[t]
    n = len(df)
    keycols = key if isinstance(key, list) else [key]
    dup_key_mask = df.duplicated(subset=keycols, keep=False)
    n_dup_rows = dup_key_mask.sum()
    n_groups = df[dup_key_mask].drop_duplicates(subset=keycols).shape[0] if n_dup_rows else 0

    classification = "hop_le_nghiep_vu"
    detail = f"{n_groups} nhom key trung ({n_dup_rows} dong lien quan)"

    if t == "order_items" and n_dup_rows > 0:
        # check xem cac dong trung key co khac unit_price/quantity/discount khong
        # (=> line item hop le, khac lan mua) hay giong het cac cot con lai (=> loi nhap/dup that)
        dup_groups = df[dup_key_mask].groupby(keycols)
        identical_rest = 0
        differ_rest = 0
        rest_cols = [c for c in df.columns if c not in keycols]
        for _, g in dup_groups:
            if g[rest_cols].drop_duplicates().shape[0] == 1:
                identical_rest += 1
            else:
                differ_rest += 1
        detail = (f"{n_groups} nhom (order_id,product_id) trung: "
                  f"{differ_rest} nhom KHAC nhau o unit_price/quantity/discount (>=1 lan mua khac nhau, "
                  f"hop le - line item that), {identical_rest} nhom GIONG HET cac cot con lai "
                  f"(nghi ban ghi trung/loi nhap)")
        classification = "can_xem_lai" if identical_rest > 0 else "hop_le_nghiep_vu"

    if t == "returns" and n_dup_rows > 0:
        detail += " (nhieu lan tra hang cho cung 1 SKU/don - can xem co hop ly khong, vd tra 1 phan nhieu lan)"
        classification = "can_xem_lai"

    add("dup_key", t, "+".join(keycols), "exact", int(n_dup_rows), n,
        n_dup_rows / n * 100 if n else 0, detail, classification)


# ---------------------------------------------------------------
# 3) OUTLIER: IQR + z-score, + gia tri am/0 vo ly
# ---------------------------------------------------------------
def iqr_outlier(series):
    s = series.dropna()
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    mask = (s < lo) | (s > hi)
    return mask.sum(), lo, hi


def zscore_outlier(series, thresh=3):
    s = series.dropna()
    mu, sd = s.mean(), s.std()
    if sd == 0 or pd.isna(sd):
        return 0, None
    z = (s - mu) / sd
    mask = z.abs() > thresh
    return mask.sum(), thresh


def outlier_nature(series, lo, hi):
    """Phan biet outlier that (phan phoi lien tuc, gia tri da dang)
    vs loi nhap (gia tri lap/sentinel bat thuong, vd 999999, -1, cluster tai 1 diem).
    Heuristic: ty le distinct/count trong vung outlier cao (>0.5) => lien tuc tu nhien => outlier_that.
    Ty le thap (nhieu ban ghi lap 1-2 gia tri) => nghi loi nhap/sentinel => can_xem_lai.
    """
    s = series.dropna()
    out = s[(s < lo) | (s > hi)]
    if len(out) == 0:
        return "hop_le_nghiep_vu", "khong co outlier"
    ratio = out.nunique() / len(out)
    if ratio > 0.5:
        return "outlier_that", f"gia tri outlier da dang (distinct/count={ratio:.2f}) - phan phoi lien tuc, khong phai sentinel/loi nhap"
    else:
        return "can_xem_lai", f"gia tri outlier lap lai nhieu (distinct/count={ratio:.2f}) - nghi sentinel/loi nhap, can kiem tra"


outlier_targets = [
    ("order_items", "unit_price", True),   # (table, col, negative_illogical?)
    ("order_items", "quantity", True),
    ("order_items", "discount_amount", False),  # 0 hop le (khong giam gia), am moi vo ly
    ("payments", "payment_value", True),
    ("returns", "refund_amount", False),  # 0 nghi, am vo ly - check rieng
    ("products", "price", True),
    ("products", "cogs", True),
    ("web_traffic", "avg_session_duration_sec", True),
    ("web_traffic", "sessions", True),
    ("web_traffic", "page_views", True),
]

for t, col, zero_illogical in outlier_targets:
    df = dfs[t] if t in dfs else pd.read_csv(os.path.join(DATA, f"{t}.csv"))
    n = len(df)
    s = df[col]

    # gia tri am
    n_neg = (s < 0).sum()
    add("invalid_value", t, col, "rule_negative", int(n_neg), n,
        n_neg / n * 100 if n else 0,
        f"{n_neg} dong {col} < 0 (min={s.min()})",
        "loi_nhap" if n_neg > 0 else "hop_le_nghiep_vu")

    # gia tri 0
    n_zero = (s == 0).sum()
    add("invalid_value", t, col, "rule_zero", int(n_zero), n,
        n_zero / n * 100 if n else 0,
        f"{n_zero} dong {col} == 0",
        "loi_nhap" if zero_illogical and n_zero > 0 else "hop_le_nghiep_vu")

    # IQR outlier (tren toan bo, ke ca am - de thay range that)
    n_iqr, lo, hi = iqr_outlier(s)
    nature, nature_note = outlier_nature(s, lo, hi)
    add("outlier", t, col, "IQR_1.5x", int(n_iqr), n,
        n_iqr / n * 100 if n else 0,
        f"nguong IQR=[{lo:.2f},{hi:.2f}]; min={s.min():.2f}; max={s.max():.2f}; {nature_note}",
        nature)

    # z-score outlier
    n_z, thresh = zscore_outlier(s)
    add("outlier", t, col, "zscore_3", int(n_z), n,
        n_z / n * 100 if n else 0,
        f"|z|>3, mean={s.mean():.2f}, std={s.std():.2f}; {nature_note}",
        nature)

# refund_amount rieng: am vo ly, nhung can so voi payments.payment_value (QC0.9 se doi chieu sau)
df_ret = dfs["returns"]
n_ret = len(df_ret)
n_neg_refund = (df_ret["refund_amount"] < 0).sum()
add("invalid_value", "returns", "refund_amount", "rule_negative", int(n_neg_refund), n_ret,
    n_neg_refund / n_ret * 100 if n_ret else 0,
    f"{n_neg_refund} dong refund_amount < 0", "loi_nhap" if n_neg_refund > 0 else "hop_le_nghiep_vu")

# quantity == 0 nghi vo ly (mua 0 san pham khong hop ly)
n_qty0 = (dfs["order_items"]["quantity"] == 0).sum()
add("invalid_value", "order_items", "quantity", "rule_zero_illogical", int(n_qty0), len(dfs["order_items"]),
    n_qty0 / len(dfs["order_items"]) * 100,
    f"{n_qty0} dong quantity==0 (mua 0 san pham - vo ly neu co)",
    "loi_nhap" if n_qty0 > 0 else "hop_le_nghiep_vu")

# products.price < cogs (ban duoi gia von) - "outlier that" da biet, khong phai loi nhap
n_below_cogs = (dfs["products"]["price"] < dfs["products"]["cogs"]).sum()
add("business_outlier", "products", "price_vs_cogs", "rule", int(n_below_cogs), len(dfs["products"]),
    n_below_cogs / len(dfs["products"]) * 100,
    f"{n_below_cogs} SKU co price < cogs (gia ban < gia von - hien tuong nghiep vu, khong phai loi nhap)",
    "hop_le_nghiep_vu")

# discount_amount > unit_price*quantity (giam gia vuot gia tri don hang) - loi nhap tiem nang
oi = dfs["order_items"]
n_disc_over = (oi["discount_amount"] > oi["unit_price"] * oi["quantity"]).sum()
add("invalid_value", "order_items", "discount_amount_vs_line_total", "rule", int(n_disc_over), len(oi),
    n_disc_over / len(oi) * 100,
    f"{n_disc_over} dong discount_amount > unit_price*quantity (giam gia vuot gia tri dong hang)",
    "loi_nhap" if n_disc_over > 0 else "hop_le_nghiep_vu")


# ---------------------------------------------------------------
# WRITE OUTPUT
# ---------------------------------------------------------------
out_df = pd.DataFrame(rows)
out_path = os.path.join(OUT_DIR, "qc08_dup_outlier.csv")
out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
print(f"Wrote {len(out_df)} rows -> {out_path}")

os.makedirs(STATUS_DIR, exist_ok=True)
with open(os.path.join(STATUS_DIR, "qc08.done"), "w") as f:
    f.write("qc08 done\n")
print("Marker qc08.done written")
