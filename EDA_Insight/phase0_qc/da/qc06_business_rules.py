"""
QC0.6 -- Business-rule validity -- @da
Dep: QC0.2 (enum/schema cua @de), QC0.4 (FK promo sach, 0 orphan).
Kiem tra 14 luat nghiep vu. KHONG sua data. Moi luat ghi: rule | violations | rate | example | loai.
Output: da/qc06_business_rules.csv
"""
import pandas as pd
import numpy as np
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(REPO, "data")
OUT = os.path.dirname(os.path.abspath(__file__))

results = []


def add(rule, checked_rows, violations, example, loai, ghi_chu=""):
    rate = round(100 * violations / checked_rows, 6) if checked_rows else None
    results.append({
        "rule": rule,
        "checked_rows": checked_rows,
        "violations": violations,
        "rate_pct": rate,
        "example": example,
        "loai": loai,
        "ghi_chu": ghi_chu,
    })


def fmt_example(df, cols, n=2):
    if len(df) == 0:
        return ""
    return df[cols].head(n).to_dict("records")


# ---------------------------------------------------------------- load ----
orders = pd.read_csv(os.path.join(DATA, "orders.csv"), parse_dates=["order_date"])
order_items = pd.read_csv(os.path.join(DATA, "order_items.csv"))
products = pd.read_csv(os.path.join(DATA, "products.csv"))
payments = pd.read_csv(os.path.join(DATA, "payments.csv"))
promotions = pd.read_csv(os.path.join(DATA, "promotions.csv"), parse_dates=["start_date", "end_date"])
returns = pd.read_csv(os.path.join(DATA, "returns.csv"), parse_dates=["return_date"])
reviews = pd.read_csv(os.path.join(DATA, "reviews.csv"), parse_dates=["review_date"])
shipments = pd.read_csv(os.path.join(DATA, "shipments.csv"), parse_dates=["ship_date", "delivery_date"])
inventory = pd.read_csv(os.path.join(DATA, "inventory.csv"))

# =====================================================================
# 1. order_items.unit_price >= products.cogs
# =====================================================================
oi_cogs = order_items.merge(products[["product_id", "cogs"]], on="product_id", how="left")
mask = oi_cogs["unit_price"] < oi_cogs["cogs"]
viol = oi_cogs[mask]
add(
    "order_items.unit_price >= products.cogs",
    len(oi_cogs), int(mask.sum()),
    fmt_example(viol, ["order_id", "product_id", "unit_price", "cogs"]),
    "hien-tuong-nghiep-vu",
    f"Ban duoi gia von — hien tuong THAT (da biet ~382/3833 ngay = 9.97% lo gop o cap do daily-aggregate theo sprint plan). "
    f"O cap do dong hang (line-item), rate cao hon nhieu: {int(mask.sum())}/{len(oi_cogs)} dong ({round(100*mask.sum()/len(oi_cogs),4)}%) co unit_price<cogs. "
    f"Chenh lech 2 rate (9.97% ngay vs 18.6% dong hang) HOP LY vi 1 ngay co nhieu dong hang, chi can vai dong lai bu duoc cac dong lo -> ngay van net-lai duong; "
    f"khong mau thuan, chi la khac granularity. Khong sua — day la du lieu phan anh chien luoc gia/khuyen mai sau, giu nguyen cho model."
)

# =====================================================================
# 2. discount_amount trong [0, unit_price*quantity]
# =====================================================================
line_total = order_items["unit_price"] * order_items["quantity"]
neg_disc = order_items["discount_amount"] < 0
over_disc = order_items["discount_amount"] > line_total
viol_mask = neg_disc | over_disc
viol = order_items[viol_mask].copy()
viol["line_total"] = line_total[viol_mask]
add(
    "discount_amount in [0, unit_price*quantity]",
    len(order_items), int(viol_mask.sum()),
    fmt_example(viol, ["order_id", "product_id", "unit_price", "quantity", "discount_amount", "line_total"]),
    "loi-data" if viol_mask.sum() > 0 else "khong-vi-pham",
    f"neg(<0)={int(neg_disc.sum())}, vuot line_total={int(over_disc.sum())}"
)

# =====================================================================
# 3. quantity > 0
# =====================================================================
mask = order_items["quantity"] <= 0
viol = order_items[mask]
add(
    "order_items.quantity > 0",
    len(order_items), int(mask.sum()),
    fmt_example(viol, ["order_id", "product_id", "quantity"]),
    "loi-data" if mask.sum() > 0 else "khong-vi-pham",
)

# =====================================================================
# 4. order_date trong [promo.start_date, promo.end_date] khi co promo_id
# =====================================================================
def check_promo_window(promo_col):
    sub = order_items[order_items[promo_col].notna()][["order_id", "product_id", promo_col]].copy()
    sub = sub.merge(orders[["order_id", "order_date"]], on="order_id", how="left")
    sub = sub.merge(
        promotions[["promo_id", "start_date", "end_date"]].rename(columns={"promo_id": promo_col}),
        on=promo_col, how="left"
    )
    out_of_window = (sub["order_date"] < sub["start_date"]) | (sub["order_date"] > sub["end_date"])
    viol = sub[out_of_window]
    add(
        f"order_date in [promo.start,end] khi co {promo_col}",
        len(sub), int(out_of_window.sum()),
        fmt_example(viol, ["order_id", promo_col, "order_date", "start_date", "end_date"]),
        "loi-data" if out_of_window.sum() > 0 else "khong-vi-pham",
        f"So dong co {promo_col} (khong null): {len(sub)}"
    )

check_promo_window("promo_id")
check_promo_window("promo_id_2")

# =====================================================================
# 5. returns.return_quantity <= qty da dat (SUM quantity theo order_id+product_id trong order_items)
# =====================================================================
ordered_qty = order_items.groupby(["order_id", "product_id"])["quantity"].sum().reset_index()
ordered_qty.columns = ["order_id", "product_id", "ordered_qty"]
ret_chk = returns.merge(ordered_qty, on=["order_id", "product_id"], how="left")
no_match = ret_chk["ordered_qty"].isna()
over_qty = (~no_match) & (ret_chk["return_quantity"] > ret_chk["ordered_qty"])
viol = ret_chk[over_qty]
add(
    "returns.return_quantity <= qty da dat (order_items)",
    len(ret_chk), int(over_qty.sum()),
    fmt_example(viol, ["return_id", "order_id", "product_id", "return_quantity", "ordered_qty"]),
    "loi-data" if over_qty.sum() > 0 else "khong-vi-pham",
    f"return khong khop duoc voi order_items (order_id,product_id) nao: {int(no_match.sum())} dong (cho vao muc rieng, khong tinh la vi pham qty)"
)
# muc rieng: return khong match duoc order_items — de rieng vi day la van de khac (kha nang match ket hop nhieu line item cung SKU)
add(
    "returns match voi order_items theo (order_id,product_id)",
    len(ret_chk), int(no_match.sum()),
    fmt_example(ret_chk[no_match], ["return_id", "order_id", "product_id"]),
    "can-xem-xet" if no_match.sum() > 0 else "khong-vi-pham",
    "RI returns.order_id/product_id da PASS o QC0.4 (0 orphan voi orders/products rieng le); ospomo o day la KHONG tim thay dung CAP (order_id,product_id) trong order_items — khac voi orphan FK don le."
)

# =====================================================================
# 6. refund_amount trong [0, payments.payment_value]
# =====================================================================
ref_chk = returns.merge(payments[["order_id", "payment_value"]], on="order_id", how="left")
neg_ref = ref_chk["refund_amount"] < 0
over_ref = ref_chk["refund_amount"] > ref_chk["payment_value"]
viol_mask = neg_ref | over_ref
viol = ref_chk[viol_mask].copy()

# Dieu tra sau ban chat vi pham refund>payment_value: ty le refund/payment,
# co phai do return-nhieu-lan-cung-don (aggregation issue) hay la lech that su.
n_returns_per_order_for_viol = returns.groupby("order_id").size().reindex(viol["order_id"]).fillna(0).values
n_single_return_order = int((n_returns_per_order_for_viol == 1).sum())
n_multi_return_order = int((n_returns_per_order_for_viol > 1).sum())
ratio = (viol["refund_amount"] / viol["payment_value"]) if len(viol) else pd.Series(dtype=float)
ratio_stats = f"ratio refund/payment: min={ratio.min():.3f}, median={ratio.median():.3f}, max={ratio.max():.3f}" if len(ratio) else ""

add(
    "refund_amount in [0, payments.payment_value]",
    len(ref_chk), int(viol_mask.sum()),
    fmt_example(viol, ["return_id", "order_id", "refund_amount", "payment_value"]),
    "loi-data" if viol_mask.sum() > 0 else "khong-vi-pham",
    f"neg={int(neg_ref.sum())}, refund>payment_value={int(over_ref.sum())}. "
    f"Da dieu tra: {n_single_return_order}/{int(viol_mask.sum())} vi pham la don CHI CO 1 return (khong phai do cong don nhieu return trung order_id — vay khong the giai thich bang aggregation), "
    f"{n_multi_return_order} don co >1 return. {ratio_stats}. "
    f"Ty le refund/payment bi CHAN TREN o ~1.25x, khong random vo han -> nghi la NHIEU/ANOMALY duoc CO Y dua vao du lieu (giong pattern '382 ngay lo gop' da biet), "
    f"KHONG giai thich duoc bang shipping_fee hay logic nghiep vu ro rang -> xep loai-data, can @tester dieu tra sau o QC0.9/QC0.10."
)

# check tong hop theo order_id (tong refund cua toan bo return trong 1 don vs payment_value don do)
ref_sum = returns.groupby("order_id")["refund_amount"].sum().reset_index()
ref_sum = ref_sum.merge(payments[["order_id", "payment_value"]], on="order_id", how="left")
over_sum = ref_sum["refund_amount"] > ref_sum["payment_value"]
add(
    "SUM(refund_amount) theo order_id <= payment_value (tong hop)",
    len(ref_sum), int(over_sum.sum()),
    fmt_example(ref_sum[over_sum], ["order_id", "refund_amount", "payment_value"]),
    "loi-data" if over_sum.sum() > 0 else "khong-vi-pham",
    "Kiem tra o muc DON (cong don nhieu return cung order_id) — chinh xac hon kiem tra tung dong return rieng le o muc [6]."
)

# =====================================================================
# 7. reviews.rating in [1,5]
# =====================================================================
mask = ~reviews["rating"].between(1, 5)
viol = reviews[mask]
add(
    "reviews.rating in [1,5]",
    len(reviews), int(mask.sum()),
    fmt_example(viol, ["review_id", "order_id", "rating"]),
    "loi-data" if mask.sum() > 0 else "khong-vi-pham",
)

# =====================================================================
# 8. reviews.review_date >= order_date
# =====================================================================
rev_chk = reviews.merge(orders[["order_id", "order_date"]], on="order_id", how="left")
mask = rev_chk["review_date"] < rev_chk["order_date"]
viol = rev_chk[mask]
add(
    "reviews.review_date >= orders.order_date",
    len(rev_chk), int(mask.sum()),
    fmt_example(viol, ["review_id", "order_id", "review_date", "order_date"]),
    "loi-data" if mask.sum() > 0 else "khong-vi-pham",
)

# =====================================================================
# 9. payments.installments >= 1
# =====================================================================
mask = payments["installments"] < 1
viol = payments[mask]
add(
    "payments.installments >= 1",
    len(payments), int(mask.sum()),
    fmt_example(viol, ["order_id", "installments"]),
    "loi-data" if mask.sum() > 0 else "khong-vi-pham",
)

# =====================================================================
# 10. payments.payment_value >= 0
# =====================================================================
mask = payments["payment_value"] < 0
viol = payments[mask]
add(
    "payments.payment_value >= 0",
    len(payments), int(mask.sum()),
    fmt_example(viol, ["order_id", "payment_value"]),
    "loi-data" if mask.sum() > 0 else "khong-vi-pham",
)

# =====================================================================
# 11. ty le 0-1: bounce_rate, fill_rate, sell_through_rate
# =====================================================================
web_traffic = pd.read_csv(os.path.join(DATA, "web_traffic.csv"))
for tbl_name, df_, col in [
    ("web_traffic", web_traffic, "bounce_rate"),
    ("inventory", inventory, "fill_rate"),
    ("inventory", inventory, "sell_through_rate"),
]:
    mask = ~df_[col].between(0, 1)
    viol = df_[mask]
    id_cols = [c for c in ["date", "snapshot_date", "product_id"] if c in df_.columns][:2]
    add(
        f"{tbl_name}.{col} in [0,1]",
        len(df_), int(mask.sum()),
        fmt_example(viol, id_cols + [col]),
        "loi-data" if mask.sum() > 0 else "khong-vi-pham",
    )

# =====================================================================
# 12. date logic: delivery_date >= ship_date >= order_date
# =====================================================================
ship_chk = shipments.merge(orders[["order_id", "order_date"]], on="order_id", how="left")
viol_ship_lt_order = ship_chk["ship_date"] < ship_chk["order_date"]
viol_deliv_lt_ship = ship_chk["delivery_date"] < ship_chk["ship_date"]
add(
    "shipments.ship_date >= orders.order_date",
    len(ship_chk), int(viol_ship_lt_order.sum()),
    fmt_example(ship_chk[viol_ship_lt_order], ["order_id", "order_date", "ship_date"]),
    "loi-data" if viol_ship_lt_order.sum() > 0 else "khong-vi-pham",
)
add(
    "shipments.delivery_date >= ship_date",
    len(ship_chk), int(viol_deliv_lt_ship.sum()),
    fmt_example(ship_chk[viol_deliv_lt_ship], ["order_id", "ship_date", "delivery_date"]),
    "loi-data" if viol_deliv_lt_ship.sum() > 0 else "khong-vi-pham",
)

# 12b. don co status delivered/shipped/returned nhung KHONG co ban ghi shipments
# (phat hien phu tu QC0.4 cua @de -- doi chieu lai o day vi lien quan date-logic/order_status)
status_needs_ship = {"delivered", "shipped", "returned"}
orders_needing_ship = orders[orders["order_status"].isin(status_needs_ship)]
missing_ship = orders_needing_ship[~orders_needing_ship["order_id"].isin(shipments["order_id"])]
add(
    "order_status in {delivered,shipped,returned} => phai co ban ghi shipments",
    len(orders_needing_ship), len(missing_ship),
    fmt_example(missing_ship, ["order_id", "order_date", "order_status"]),
    "loi-data" if len(missing_ship) > 0 else "khong-vi-pham",
    f"Doi chieu lai finding cua @de (QC0.4): {len(missing_ship)} don co status ngu y da/dang ship nhung khong co dong trong shipments. "
    f"Min/max order_date cua nhom nay: {missing_ship['order_date'].min()} -> {missing_ship['order_date'].max()}"
    if len(missing_ship) > 0 else ""
)

# =====================================================================
# 13. promotions: end_date >= start_date
# =====================================================================
mask = promotions["end_date"] < promotions["start_date"]
viol = promotions[mask]
add(
    "promotions.end_date >= start_date",
    len(promotions), int(mask.sum()),
    fmt_example(viol, ["promo_id", "start_date", "end_date"]),
    "loi-data" if mask.sum() > 0 else "khong-vi-pham",
)

# =====================================================================
# Ghi ket qua
# =====================================================================
out_df = pd.DataFrame(results)
out_path = os.path.join(OUT, "qc06_business_rules.csv")
out_df.to_csv(out_path, index=False)
print(f"Wrote {out_path} -- {len(out_df)} rules")
print(out_df[["rule", "checked_rows", "violations", "rate_pct", "loai"]].to_string(index=False))
