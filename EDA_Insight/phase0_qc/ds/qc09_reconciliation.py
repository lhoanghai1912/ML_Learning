"""
QC0.9 - Cross-table reconciliation
Owner: @ds. Dep: QC0.4 (RI) + QC0.6 (business-rule) + QC0.8 (dup/outlier) - phai xong het.
KHONG sua data - chi doc va doi chieu.

Output: EDA_Insight/phase0_qc/ds/qc09_reconciliation.csv
Cot: cap | gia_tri_A | gia_tri_B | pct_lech | ket_luan
Marker: EDA_Insight/phase0_qc/_status/qc09.done
"""
import pandas as pd
import numpy as np
import os

ROOT = "/Users/lhoanghai_/Documents/Study/Dự án datathon2026"
DATA = os.path.join(ROOT, "data")
OUT_DIR = os.path.join(ROOT, "EDA_Insight/phase0_qc/ds")
STATUS_DIR = os.path.join(ROOT, "EDA_Insight/phase0_qc/_status")

rows = []


def add(cap, a_label, a_val, b_label, b_val, note_extra=""):
    if a_val == 0 and b_val == 0:
        pct = 0.0
    else:
        pct = abs(a_val - b_val) / max(abs(a_val), abs(b_val), 1e-9) * 100
    if pct < 0.5:
        ketluan = "khop"
    elif pct < 20:
        ketluan = "lech-co-giai-thich"
    else:
        ketluan = "lech-bat-thuong"
    rows.append({
        "cap": cap,
        "gia_tri_A": f"{a_label}={a_val:,.2f}",
        "gia_tri_B": f"{b_label}={b_val:,.2f}",
        "pct_lech": round(pct, 4),
        "ket_luan": ketluan,
        "ghi_chu": note_extra,
    })


print("Loading tables...")
orders = pd.read_csv(os.path.join(DATA, "orders.csv"), parse_dates=["order_date"])
order_items = pd.read_csv(os.path.join(DATA, "order_items.csv"))
products = pd.read_csv(os.path.join(DATA, "products.csv"))
payments = pd.read_csv(os.path.join(DATA, "payments.csv"))
shipments = pd.read_csv(os.path.join(DATA, "shipments.csv"))
returns = pd.read_csv(os.path.join(DATA, "returns.csv"))
reviews = pd.read_csv(os.path.join(DATA, "reviews.csv"))
sales = pd.read_csv(os.path.join(DATA, "sales.csv"), parse_dates=["Date"])

# join order_items <- orders (order_date, order_status) va <- products (cogs)
oi = order_items.merge(orders[["order_id", "order_date", "order_status"]], on="order_id", how="left")
oi = oi.merge(products[["product_id", "cogs"]], on="product_id", how="left")
oi["gross_line"] = oi["unit_price"] * oi["quantity"]
oi["cogs_line"] = oi["cogs"] * oi["quantity"]
oi["net_line"] = oi["gross_line"] - oi["discount_amount"]

# ---------------------------------------------------------------
# 1) sales.Revenue/COGS vs aggregate GROSS tu order_items (ky vong ~0.0000%)
# ---------------------------------------------------------------
sales_rev_total = sales["Revenue"].sum()
sales_cogs_total = sales["COGS"].sum()
oi_gross_total = oi["gross_line"].sum()
oi_cogs_total = oi["cogs_line"].sum()

add("sales.Revenue (total) vs SUM(order_items gross=unit_price*qty)",
    "sales.Revenue", sales_rev_total, "order_items.gross", oi_gross_total,
    "tong toan bo lich su, khong loc status")

add("sales.COGS (total) vs SUM(order_items qty*products.cogs)",
    "sales.COGS", sales_cogs_total, "order_items.cogs", oi_cogs_total,
    "tong toan bo lich su, khong loc status")

# doi chieu theo ngay (mismatch date coverage giua sales va orders se lam ro nguyen nhan lech neu co)
oi_daily_gross = oi.groupby(oi["order_date"].dt.date)["gross_line"].sum()
sales_daily = sales.set_index(sales["Date"].dt.date)["Revenue"]
common_days = oi_daily_gross.index.intersection(sales_daily.index)
add("So ngay trung giua sales.Date va orders.order_date",
    "sales.Date distinct", sales["Date"].nunique(), "orders.order_date distinct", orders["order_date"].nunique(),
    f"so ngay giao nhau={len(common_days)}; neu lech span thi gross theo NGAY se khong khop dai han")

# ---------------------------------------------------------------
# 2) sales gross vs net (loai cancelled + discount) -> ky vong gap ~13.37%
# ---------------------------------------------------------------
oi_net_excl_cancel = oi.loc[oi["order_status"] != "cancelled", "net_line"].sum()
gap_pct = (oi_gross_total - oi_net_excl_cancel) / oi_gross_total * 100
rows.append({
    "cap": "sales gross vs net (loai cancelled + tru discount)",
    "gia_tri_A": f"gross_all={oi_gross_total:,.2f}",
    "gia_tri_B": f"net_excl_cancelled={oi_net_excl_cancel:,.2f}",
    "pct_lech": round(gap_pct, 4),
    "ket_luan": "khop-voi-ky-vong-13.37%" if abs(gap_pct - 13.37) < 2 else "lech-so-voi-ky-vong-13.37%",
    "ghi_chu": f"gap thuc te={gap_pct:.2f}% (ky vong ~13.37%)",
})

# ---------------------------------------------------------------
# 3) COUNT(orders)==COUNT(payments), verify 1:1
# ---------------------------------------------------------------
n_orders = len(orders)
n_payments = len(payments)
add("COUNT(orders) vs COUNT(payments)", "orders", n_orders, "payments", n_payments,
    "verify 1:1 tong so dong")

# verify moi order co dung 1 payment (khong phai chi count bang nhau ngau nhien)
pay_per_order = payments.groupby("order_id").size()
n_orders_with_multi_pay = (pay_per_order > 1).sum()
n_orders_no_pay = orders["order_id"].nunique() - orders["order_id"].isin(payments["order_id"]).sum()
rows.append({
    "cap": "orders 1:1 payments (per order_id, khong chi count tong)",
    "gia_tri_A": f"order co >1 payment={n_orders_with_multi_pay}",
    "gia_tri_B": f"order khong co payment={n_orders_no_pay}",
    "pct_lech": round((n_orders_with_multi_pay + n_orders_no_pay) / n_orders * 100, 4),
    "ket_luan": "khop" if (n_orders_with_multi_pay == 0 and n_orders_no_pay == 0) else "lech-bat-thuong",
    "ghi_chu": "count tong bang nhau chua chac 1:1 that su - can kiem tra per-order_id",
})

# ---------------------------------------------------------------
# 4) orders - shipments = 80.878 -> khop don cancelled/chua ship?
# ---------------------------------------------------------------
n_shipments = len(shipments)
diff_orders_shipments = n_orders - n_shipments
add("COUNT(orders) - COUNT(shipments)", "orders", n_orders, "shipments", n_shipments,
    f"hieu so={diff_orders_shipments:,} (ky vong tham chieu 80,878)")

orders_no_ship = orders[~orders["order_id"].isin(shipments["order_id"])]
status_no_ship = orders_no_ship["order_status"].value_counts()
n_no_ship_cancelled_or_early = status_no_ship.get("cancelled", 0) + status_no_ship.get("created", 0) + status_no_ship.get("paid", 0)
rows.append({
    "cap": "don KHONG co shipment vs status (cancelled/created/paid = chua giao van)",
    "gia_tri_A": f"orders_no_shipment={len(orders_no_ship):,}",
    "gia_tri_B": f"status cancelled+created+paid={n_no_ship_cancelled_or_early:,} | breakdown={status_no_ship.to_dict()}",
    "pct_lech": round(abs(len(orders_no_ship) - n_no_ship_cancelled_or_early) / len(orders_no_ship) * 100, 4) if len(orders_no_ship) else 0,
    "ket_luan": "khop" if n_no_ship_cancelled_or_early == len(orders_no_ship) else "lech-co-giai-thich",
    "ghi_chu": "kiem tra 80.878 don khong co shipment co phai toan bo la cancelled/created/paid (chua toi buoc ship) khong",
})

# nguoc lai: cac don co status shipped/delivered/returned nhung LAI khong co shipment record (bat thuong)
should_have_ship = orders[orders["order_status"].isin(["shipped", "delivered", "returned"])]
missing_ship_but_should = should_have_ship[~should_have_ship["order_id"].isin(shipments["order_id"])]
rows.append({
    "cap": "don status shipped/delivered/returned nhung KHONG co shipment record",
    "gia_tri_A": f"so don nay={len(missing_ship_but_should):,}",
    "gia_tri_B": f"tong don shipped/delivered/returned={len(should_have_ship):,}",
    "pct_lech": round(len(missing_ship_but_should) / len(should_have_ship) * 100, 4) if len(should_have_ship) else 0,
    "ket_luan": "khop" if len(missing_ship_but_should) == 0 else "lech-bat-thuong",
    "ghi_chu": "neu >0: don da giao/tra hang nhung thieu ban ghi shipment - nghi thieu du lieu",
})

# ---------------------------------------------------------------
# 5) SUM(payments.payment_value) vs SUM(order_items net); SUM(returns.refund_amount) <= payments
# ---------------------------------------------------------------
payments_total = payments["payment_value"].sum()
oi_net_all = oi["net_line"].sum()  # net toan bo (khong loai cancelled) - doi chieu voi payment thuc thu
add("SUM(payments.payment_value) vs SUM(order_items net = gross-discount, tat ca status)",
    "payments_total", payments_total, "order_items_net_total", oi_net_all,
    "neu payment thu tren TOAN BO don (ke ca sau nay huy) thi so sanh voi net toan bo hop ly hon net-excl-cancelled")

add("SUM(payments.payment_value) vs SUM(order_items net, LOAI cancelled)",
    "payments_total", payments_total, "order_items_net_excl_cancelled", oi_net_excl_cancel,
    "neu payment CHI thu tren don khong huy thi cap nay hop ly hon")

refund_total = returns["refund_amount"].sum()
rows.append({
    "cap": "SUM(returns.refund_amount) <= SUM(payments.payment_value)",
    "gia_tri_A": f"refund_total={refund_total:,.2f}",
    "gia_tri_B": f"payments_total={payments_total:,.2f}",
    "pct_lech": round(refund_total / payments_total * 100, 4),
    "ket_luan": "khop" if refund_total <= payments_total else "lech-bat-thuong (refund > payment tong the - vo ly)",
    "ghi_chu": "refund/payment ratio - kiem tra muc do hop ly tong quan",
})

# per-order: refund_amount cua 1 return co <= payment_value cua don do khong (rule-level, QC0.6 co the da lam - o day recheck aggregate)
ret_pay = returns.merge(payments[["order_id", "payment_value"]], on="order_id", how="left")
n_refund_over_payment = (ret_pay["refund_amount"] > ret_pay["payment_value"]).sum()
rows.append({
    "cap": "PER-ORDER: refund_amount > payment_value cua chinh don do",
    "gia_tri_A": f"so dong return vi pham={n_refund_over_payment:,}",
    "gia_tri_B": f"tong so dong returns={len(returns):,}",
    "pct_lech": round(n_refund_over_payment / len(returns) * 100, 4),
    "ket_luan": "khop" if n_refund_over_payment == 0 else "lech-bat-thuong",
    "ghi_chu": "vi pham logic hoan tien > da thu - can flag rieng (QC0.6 co the da bat, o day xac nhan lai o muc cross-table)",
})

# ---------------------------------------------------------------
# 6) reviews / returns count vs orders - hop ly?
# ---------------------------------------------------------------
n_reviews = len(reviews)
n_returns = len(returns)
n_order_items = len(order_items)

# Luu y: reviews/returns KHONG ky vong bang orders (review/return la optional, khong phai 1:1)
# => khong dung nguong pct_lech chung, chi bao cao ty le va nhan dinh hop ly hay khong.
rows.append({
    "cap": "COUNT(reviews) vs COUNT(orders) [ty le, khong ky vong bang nhau]",
    "gia_tri_A": f"reviews={n_reviews:,}", "gia_tri_B": f"orders={n_orders:,}",
    "pct_lech": round(n_reviews / n_orders * 100, 4),
    "ket_luan": "khop-hop-ly" if 0 < n_reviews / n_orders <= 1 else "lech-bat-thuong",
    "ghi_chu": f"ty le reviews/orders={n_reviews/n_orders*100:.2f}% - review la optional (khach co the ko review), <=100% la hop ly, khong phai loi doi chieu",
})
rows.append({
    "cap": "COUNT(reviews) vs COUNT(order_items) [ty le, khong ky vong bang nhau]",
    "gia_tri_A": f"reviews={n_reviews:,}", "gia_tri_B": f"order_items={n_order_items:,}",
    "pct_lech": round(n_reviews / n_order_items * 100, 4),
    "ket_luan": "khop-hop-ly" if 0 < n_reviews / n_order_items <= 1 else "lech-bat-thuong",
    "ghi_chu": f"ty le reviews/order_items={n_reviews/n_order_items*100:.2f}% - moi review gan 1 (order_id,product_id) cu the, <=100% hop ly",
})
rows.append({
    "cap": "COUNT(returns) vs COUNT(orders) [ty le, khong ky vong bang nhau]",
    "gia_tri_A": f"returns={n_returns:,}", "gia_tri_B": f"orders={n_orders:,}",
    "pct_lech": round(n_returns / n_orders * 100, 4),
    "ket_luan": "khop-hop-ly" if 0 < n_returns / n_orders <= 1 else "lech-bat-thuong",
    "ghi_chu": f"ty le returns/orders={n_returns/n_orders*100:.2f}%; doi chieu voi order_status=returned ({(orders['order_status']=='returned').sum():,} don) - xem dong duoi",
})

n_status_returned = (orders["order_status"] == "returned").sum()
rows.append({
    "cap": "COUNT(returns distinct order_id) vs COUNT(orders status=returned)",
    "gia_tri_A": f"distinct order_id trong returns={returns['order_id'].nunique():,}",
    "gia_tri_B": f"orders.order_status=returned={n_status_returned:,}",
    "pct_lech": round(abs(returns['order_id'].nunique() - n_status_returned) / max(n_status_returned,1) * 100, 4),
    "ket_luan": "khop" if returns['order_id'].nunique() == n_status_returned else "lech-co-giai-thich",
    "ghi_chu": "ky vong so don co it nhat 1 return ~ so don status=returned (co the lech neu 1 don return roi status khac, hoac return partial khong doi status)",
})

# ---------------------------------------------------------------
# WRITE OUTPUT
# ---------------------------------------------------------------
out_df = pd.DataFrame(rows)
out_path = os.path.join(OUT_DIR, "qc09_reconciliation.csv")
out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
print(f"Wrote {len(out_df)} rows -> {out_path}")

os.makedirs(STATUS_DIR, exist_ok=True)
with open(os.path.join(STATUS_DIR, "qc09.done"), "w") as f:
    f.write("qc09 done\n")
print("Marker qc09.done written")
