"""
QC0.10 -- Audit doc lap (KHONG tin so cu tu de/da/ds).
Tu chay lai 5 finding severity cao nhat tu QC0.1-0.9, doi chieu voi so da bao cao.
Chay: python3 qc10_independent_audit.py (tu thu muc phase0_qc/tester, hoac repo root)
"""
import pandas as pd
import os

# tim repo root (co thu muc data/)
here = os.path.dirname(os.path.abspath(__file__))
root = here
while root != "/" and not os.path.isdir(os.path.join(root, "data")):
    root = os.path.dirname(root)
DATA = os.path.join(root, "data")
print(f"DATA dir: {DATA}")

orders = pd.read_csv(os.path.join(DATA, "orders.csv"))
order_items = pd.read_csv(os.path.join(DATA, "order_items.csv"))
products = pd.read_csv(os.path.join(DATA, "products.csv"))
payments = pd.read_csv(os.path.join(DATA, "payments.csv"))
returns = pd.read_csv(os.path.join(DATA, "returns.csv"))
shipments = pd.read_csv(os.path.join(DATA, "shipments.csv"))
inventory = pd.read_csv(os.path.join(DATA, "inventory.csv"))

results = []

def log(check, reported, recomputed, match):
    results.append((check, reported, recomputed, match))
    print(f"[{ 'MATCH' if match else 'MISMATCH' }] {check}\n  reported={reported}\n  recomputed={recomputed}\n")

# ---------------------------------------------------------------
# FINDING 1 (critical candidate) — returns.refund_amount > payments.payment_value
# Reported (QC0.6 / QC0.9): 3430 dong vi pham / 39939 = 8.588097%
# ---------------------------------------------------------------
r = returns.merge(payments[["order_id", "payment_value"]], on="order_id", how="left")
viol1 = r[r["refund_amount"] > r["payment_value"]]
n1 = len(viol1)
rate1 = n1 / len(returns) * 100
log(
    "returns.refund_amount > payments.payment_value (per return row)",
    "3430 / 39939 = 8.588097%",
    f"{n1} / {len(returns)} = {rate1:.6f}%",
    n1 == 3430,
)
# ratio bound check (reported: min=1.000, median=1.097, max=1.250)
ratio = (viol1["refund_amount"] / viol1["payment_value"])
print(f"  ratio refund/payment (vi pham): min={ratio.min():.3f} median={ratio.median():.3f} max={ratio.max():.3f}")

# ---------------------------------------------------------------
# FINDING 2 (business phenomenon, rate lon nhat) — order_items.unit_price < products.cogs
# Reported (QC0.6): 133052 / 714669 = 18.61729%
# ---------------------------------------------------------------
oi = order_items.merge(products[["product_id", "cogs"]], on="product_id", how="left")
viol2 = oi[oi["unit_price"] < oi["cogs"]]
n2 = len(viol2)
rate2 = n2 / len(order_items) * 100
log(
    "order_items.unit_price < products.cogs (ban duoi gia von, line-item level)",
    "133052 / 714669 = 18.61729%",
    f"{n2} / {len(order_items)} = {rate2:.5f}%",
    n2 == 133052,
)

# ---------------------------------------------------------------
# FINDING 3 (loi-data candidate) — order_status in {delivered,shipped,returned} nhung KHONG co shipment record
# Reported (QC0.6/QC0.9): 564 / 566631 = 0.099536%
# ---------------------------------------------------------------
ship_ids = set(shipments["order_id"].unique())
sub = orders[orders["order_status"].isin(["delivered", "shipped", "returned"])]
viol3 = sub[~sub["order_id"].isin(ship_ids)]
n3 = len(viol3)
rate3 = n3 / len(sub) * 100
log(
    "order_status in {delivered,shipped,returned} nhung KHONG co ban ghi shipments",
    "564 / 566631 = 0.099536%",
    f"{n3} / {len(sub)} = {rate3:.6f}%",
    n3 == 564,
)
if n3 > 0:
    print("  status breakdown vi pham:", viol3["order_status"].value_counts().to_dict())
    print("  order_date range vi pham:", viol3["order_date"].min(), "->", viol3["order_date"].max())

# ---------------------------------------------------------------
# FINDING 4 (grain FAIL) — order_items (order_id,product_id) khong phai key duy nhat
# Reported (QC0.3/QC0.8): 16 nhom trung, 32 dong vi pham (dup_key count=32 trong QC0.8)
# ---------------------------------------------------------------
grp = order_items.groupby(["order_id", "product_id"]).size()
dup_groups = grp[grp > 1]
n_groups = len(dup_groups)
n_rows_involved = dup_groups.sum()
log(
    "order_items grain: (order_id,product_id) nhom trung",
    "16 nhom trung / 32 dong lien quan",
    f"{n_groups} nhom trung / {n_rows_involved} dong lien quan",
    (n_groups == 16) and (n_rows_involved == 32),
)
# xac nhan khong co full-row duplicate trong cac nhom nay
sample_key = dup_groups.index[0]
sample_rows = order_items[
    (order_items["order_id"] == sample_key[0]) & (order_items["product_id"] == sample_key[1])
]
print(f"  vi du nhom trung dau tien {sample_key}:\n{sample_rows.to_string(index=False)}")
full_dup_within_groups = 0
for (oid, pid), _ in dup_groups.items():
    rows = order_items[(order_items["order_id"] == oid) & (order_items["product_id"] == pid)]
    if rows.duplicated(keep=False).any():
        full_dup_within_groups += 1
print(f"  so nhom co full-row-duplicate THAT SU (rui ro loi nhap): {full_dup_within_groups} / {n_groups}")

# ---------------------------------------------------------------
# FINDING 5 (data phenomenon / dead column) — inventory.reorder_flag = 100% gia tri 0
# Reported (QC0.2): distinct=1, gia tri 0 chiem 100.00% (60247/60247)
# ---------------------------------------------------------------
vc = inventory["reorder_flag"].value_counts()
n_distinct = inventory["reorder_flag"].nunique()
pct_zero = (inventory["reorder_flag"] == 0).mean() * 100
log(
    "inventory.reorder_flag — cot chet (100% = 0)",
    "distinct=1, 0 chiem 100.00% (60247/60247)",
    f"distinct={n_distinct}, 0 chiem {pct_zero:.2f}% ({(inventory['reorder_flag']==0).sum()}/{len(inventory)})",
    (n_distinct == 1) and (pct_zero == 100.0),
)

# ---------------------------------------------------------------
# Tong ket
# ---------------------------------------------------------------
print("\n" + "=" * 70)
print("TONG KET AUDIT DOC LAP")
print("=" * 70)
all_match = True
for check, reported, recomputed, match in results:
    status = "MATCH" if match else "MISMATCH"
    if not match:
        all_match = False
    print(f"- [{status}] {check}")
print(f"\nKET LUAN: {'TAT CA 5 FINDING KHOP VOI SO DA BAO CAO' if all_match else 'CO MISMATCH -- CAN DIEU TRA THEM'}")
