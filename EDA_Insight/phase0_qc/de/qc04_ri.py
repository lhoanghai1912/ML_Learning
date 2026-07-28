# -*- coding: utf-8 -*-
# QC0.4 - Referential integrity (@de)
# Dem orphan (child khong match parent) cho moi FK edge.
# Dep: QC0.3 (grain/key da chot) - CHAY SAU QC0.3.
# CHI DOC - khong sua data.

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA = ROOT / "data"
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
STATUS = OUT.parent / "_status"

assert (STATUS / "QC0.3.done").exists(), "QC0.4 phu thuoc QC0.3 - chua thay marker QC0.3.done"


def load(name):
    return pd.read_csv(DATA / "{}.csv".format(name), low_memory=False)


TBL = {n: load(n) for n in [
    "customers", "products", "geography", "orders", "payments",
    "order_items", "shipments", "reviews", "returns", "promotions", "inventory",
]}

EDGES = [
    ("orders", "customer_id", "customers", "customer_id"),
    ("orders", "zip", "geography", "zip"),
    ("customers", "zip", "geography", "zip"),
    ("order_items", "order_id", "orders", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("order_items", "promo_id", "promotions", "promo_id"),
    ("order_items", "promo_id_2", "promotions", "promo_id"),
    ("payments", "order_id", "orders", "order_id"),
    ("shipments", "order_id", "orders", "order_id"),
    ("returns", "order_id", "orders", "order_id"),
    ("returns", "product_id", "products", "product_id"),
    ("reviews", "order_id", "orders", "order_id"),
    ("reviews", "product_id", "products", "product_id"),
    ("reviews", "customer_id", "customers", "customer_id"),
    ("inventory", "product_id", "products", "product_id"),
]

# canh nao NULL FK duoc coi la hop le nghiep vu (khong tinh la orphan)
EXPECTED_NULL_FK = {
    ("order_items", "promo_id"): "phan lon don khong ap dung khuyen mai -> NULL hop le",
    ("order_items", "promo_id_2"): "khuyen mai thu 2 (stackable) hiem -> phan lon NULL hop le",
}

rows_out = []
print("QC0.4 Referential integrity\n")

for child, ck, parent, pk in EDGES:
    cdf = TBL[child]
    pdf = TBL[parent]
    child_rows = len(cdf)
    cvals_all = cdf[ck]
    n_null = cvals_all.isna().sum()
    cvals = cvals_all.dropna()
    pvals = set(pdf[pk].dropna())
    orphan_mask = ~cvals.isin(pvals)
    n_orphan = int(orphan_mask.sum())
    orphan_pct = 100.0 * n_orphan / child_rows if child_rows else 0.0
    orphan_keys_distinct = cvals[orphan_mask].nunique()
    example_ids = cvals[orphan_mask].unique()[:3].tolist()

    is_expected_null = (child, ck) in EXPECTED_NULL_FK
    # severity: critical neu FK bat buoc (order_items->orders/products, payments/shipments/returns/reviews->orders
    # hoac ->customers/products) va orphan>0; cao neu >1%; trung binh neu 0<pct<=1%; thap neu null-only edge co orphan nho
    if n_orphan == 0:
        severity = "none"
    elif orphan_pct > 5:
        severity = "critical"
    elif orphan_pct > 0.1:
        severity = "high"
    elif orphan_pct > 0:
        severity = "medium"
    else:
        severity = "low"

    note = ""
    if is_expected_null:
        note = "{} ({} null, {:.2f}%, KHONG tinh la orphan)".format(
            EXPECTED_NULL_FK[(child, ck)], n_null, 100.0 * n_null / child_rows)

    rows_out.append({
        "edge": "{}.{} -> {}.{}".format(child, ck, parent, pk),
        "child_rows": child_rows,
        "null_fk": int(n_null),
        "orphans": n_orphan,
        "orphan_pct": round(orphan_pct, 4),
        "orphan_keys_distinct": int(orphan_keys_distinct),
        "example_orphan_values": example_ids,
        "severity": severity,
        "note": note,
    })
    print("{:<40} child_rows={:>9,} null={:>7,} orphans={:>7,} ({:>6.3f}%) sev={:<8} vd={}".format(
        "{}.{}->{}.{}".format(child, ck, parent, pk), child_rows, n_null, n_orphan, orphan_pct,
        severity, example_ids if n_orphan else ""))
    if note:
        print("    {}".format(note))

out_df = pd.DataFrame(rows_out, columns=[
    "edge", "child_rows", "null_fk", "orphans", "orphan_pct",
    "orphan_keys_distinct", "example_orphan_values", "severity", "note",
])
out_path = OUT / "qc04_ri.csv"
out_df.to_csv(out_path, index=False)

# --- Coverage phu (khong phai loi - de tester/PM tham khao) ---
print("\n--- Coverage nguoc (INFO, khong phai orphan) ---")
orders = TBL["orders"]
o_ids = set(orders["order_id"])
no_ship = o_ids - set(TBL["shipments"]["order_id"])
no_items = o_ids - set(TBL["order_items"]["order_id"])
print("  orders khong co shipment : {:,} (theo status: {})".format(
    len(no_ship),
    orders[orders["order_id"].isin(no_ship)]["order_status"].value_counts().to_dict()))
print("  orders khong co order_items: {:,}".format(len(no_items)))
if len(no_items):
    print("    -> status cac don nay:", orders[orders["order_id"].isin(no_items)]["order_status"].value_counts().to_dict())

print("\n--- TOM TAT severity ---")
sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}
out_df["_s"] = out_df["severity"].map(sev_order)
print(out_df.sort_values("_s")[["edge", "orphans", "orphan_pct", "severity"]].to_string(index=False))

print("\nGhi:", out_path)
