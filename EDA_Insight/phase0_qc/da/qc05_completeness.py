"""
QC0.5 -- Completeness (null/blank/sentinel) -- @da
Scan 14 bang raw trong data/*.csv. Voi moi cot: dem null (NaN), blank string
("", chi whitespace), sentinel text ("NA","N/A","null","none","unknown","-","?")
va sentinel so -1. Khong sua data, chi doc va bao cao.
Output: da/qc05_completeness.csv
"""
import pandas as pd
import numpy as np
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(REPO, "data")
OUT = os.path.dirname(os.path.abspath(__file__))

TABLES = [
    "customers", "products", "geography", "orders", "payments", "order_items",
    "shipments", "reviews", "returns", "promotions", "inventory",
    "web_traffic", "sales", "sample_submission",
]

SENTINEL_TEXT = {"na", "n/a", "null", "none", "unknown", "-", "?", "nan", ""}

# Business classification rules — cot nao null la hop le nghiep vu, ghi ly do.
# key = (table, column) -> giai thich
BUSINESS_NULL_OK = {
    ("order_items", "promo_id_2"): "Khuyen mai thu 2 (stackable) hiem gap -> phan lon NULL hop le (theo QC0.4: 714,463/714,669 = 99.97% null, KHONG tinh la orphan/loi).",
    ("order_items", "promo_id"): "Don khong ap dung khuyen mai -> NULL hop le (theo QC0.4: 438,353/714,669 = 61.34% null).",
    ("promotions", "applicable_category"): "NULL = chuong trinh khuyen mai ap dung TOAN BO danh muc (vd 'Spring Sale', 'Year-End Sale' theo tung nam) — khong phai loi. 5 dong co gia tri (Streetwear/Outdoor) la promo gioi han 1 danh muc. Nen doi ten/dung sentinel ro rang hon (vd 'ALL') de tranh nham voi thieu du lieu, nhung ban chat la hop le nghiep vu.",
}

# Cot da kiem tra thuc te CO 0% null (kha nang gia dinh ban dau trong sprint plan sai)
# — ghi lai de tranh nham lan, khong bao gio duoc gan hop_le_nghiep_vu vi khong co null de phan loai.
VERIFIED_ZERO_NULL_NOTE = {
    ("shipments", "delivery_date"): "THUC TE: 0% null (566,067/566,067 co delivery_date). Gia dinh ban dau trong sprint plan ('dang giao?') SAI cho cot nay — moi shipment record da co ngay giao. Khoang trong that su la o CAP DO BANG: orders (646,945) - shipments (566,067) = 80,878 don KHONG co shipment record nao (xem QC0.3/QC0.9), khong phai delivery_date bi null trong shipments.",
    ("reviews", "review_title"): "THUC TE: 0% null (113,551/113,551 co title). Khong co truong hop rating co nhung title trong nhu gia dinh.",
    ("returns", "return_reason"): "THUC TE: 0% null (39,939/39,939 co ly do). Khong thieu du lieu o cot nay.",
}


def classify(table, col, null_pct, distinct_vals_sample):
    key = (table, col)
    if null_pct == 0:
        note = VERIFIED_ZERO_NULL_NOTE.get(key, "")
        return "khong_co_null", note
    if key in BUSINESS_NULL_OK:
        return "hop_le_nghiep_vu", BUSINESS_NULL_OK[key]
    # id / khoa / gia / so luong / ngay cot goc -> null bat thuong
    critical_markers = ("_id", "date", "price", "value", "amount", "quantity",
                         "rating", "status", "method", "zip")
    if any(m in col.lower() for m in critical_markers):
        return "thieu_bat_thuong", f"Cot co ve la truong loi/khoa/gia tri cot loi ({col}); null > 0 nen kiem tra nguyen nhan."
    return "can_xem_xet", "Chua co quy tac nghiep vu ro rang — can @da/domain xac nhan."


def scan_table(table):
    path = os.path.join(DATA, f"{table}.csv")
    df = pd.read_csv(path, low_memory=False)
    n = len(df)
    rows = []
    for col in df.columns:
        s = df[col]
        n_null = int(s.isna().sum())
        is_text = s.dtype == object
        n_blank = 0
        n_sentinel_text = 0
        sample_vals = []
        if is_text:
            non_null = s.dropna().astype(str)
            stripped = non_null.str.strip()
            n_blank = int((stripped == "").sum())
            lowered = stripped.str.lower()
            n_sentinel_text = int(lowered.isin(SENTINEL_TEXT - {""}).sum())
        n_sentinel_neg1 = 0
        if not is_text:
            try:
                n_sentinel_neg1 = int((s.dropna() == -1).sum())
            except TypeError:
                n_sentinel_neg1 = 0
        total_missing = n_null + n_blank + n_sentinel_text
        pct_null = round(100 * n_null / n, 4) if n else 0
        pct_blank = round(100 * n_blank / n, 4) if n else 0
        pct_sentinel_text = round(100 * n_sentinel_text / n, 4) if n else 0
        pct_sentinel_neg1 = round(100 * n_sentinel_neg1 / n, 4) if n else 0
        pct_total_missing = round(100 * total_missing / n, 4) if n else 0

        classification, note = classify(table, col, pct_null, sample_vals)

        rows.append({
            "table": table,
            "column": col,
            "rows": n,
            "null_count": n_null,
            "null_pct": pct_null,
            "blank_count": n_blank,
            "blank_pct": pct_blank,
            "sentinel_text_count": n_sentinel_text,
            "sentinel_text_pct": pct_sentinel_text,
            "sentinel_neg1_count": n_sentinel_neg1,
            "sentinel_neg1_pct": pct_sentinel_neg1,
            "total_missing_pct": pct_total_missing,
            "classification": classification,
            "note": note,
        })
    return rows


def main():
    all_rows = []
    for t in TABLES:
        try:
            all_rows.extend(scan_table(t))
        except Exception as e:
            all_rows.append({
                "table": t, "column": "__ERROR__", "rows": None,
                "null_count": None, "null_pct": None, "blank_count": None,
                "blank_pct": None, "sentinel_text_count": None,
                "sentinel_text_pct": None, "sentinel_neg1_count": None,
                "sentinel_neg1_pct": None, "total_missing_pct": None,
                "classification": "ERROR", "note": str(e),
            })

    out_df = pd.DataFrame(all_rows)
    out_df = out_df.sort_values("total_missing_pct", ascending=False, na_position="last")
    out_path = os.path.join(OUT, "qc05_completeness.csv")
    out_df.to_csv(out_path, index=False)
    print(f"Wrote {out_path} — {len(out_df)} rows (table x column)")

    # In nhanh top 20 cot missing nhieu nhat
    print("\nTop 20 cot theo total_missing_pct:")
    print(out_df[["table", "column", "null_pct", "total_missing_pct", "classification"]].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
