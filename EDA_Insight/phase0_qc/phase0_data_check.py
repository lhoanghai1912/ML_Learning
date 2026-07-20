# Phase 0 — Kiểm tra dữ liệu trước khi phân tích
# Mục tiêu:
#   1. Tìm công thức đúng của Revenue/COGS trong sales.csv (tái dựng từ order_items)
#   2. Kiểm tra grain của web_traffic
#   3. Kiểm tra duplicate trong order_items
#   4. Xem 382 ngày lỗ gộp rơi vào thời điểm nào
# Chạy: python3 phase0_data_check.py

import pandas as pd
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

print("Đang load dữ liệu...")
orders = pd.read_csv(DATA / "orders.csv", parse_dates=["order_date"],
                     usecols=["order_id", "order_date", "order_status"])
items = pd.read_csv(DATA / "order_items.csv")
products = pd.read_csv(DATA / "products.csv", usecols=["product_id", "cogs"])
sales = pd.read_csv(DATA / "sales.csv", parse_dates=["Date"])

# ---------------------------------------------------------------
# 1. TÁI DỰNG REVENUE THEO NGÀY, THỬ TỪNG ĐỊNH NGHĨA
# ---------------------------------------------------------------
items["line_revenue"] = items["quantity"] * items["unit_price"] - items["discount_amount"]
items["line_revenue_gross"] = items["quantity"] * items["unit_price"]
items = items.merge(products, on="product_id", how="left")
items["line_cogs"] = items["quantity"] * items["cogs"]

df = items.merge(orders, on="order_id", how="left")

sales_idx = sales.set_index("Date")["Revenue"]

def test_definition(name, mask, col="line_revenue"):
    daily = df.loc[mask].groupby("order_date")[col].sum()
    joined = pd.concat([sales_idx, daily], axis=1, keys=["sales", "rebuilt"]).dropna()
    diff_pct = ((joined["rebuilt"] - joined["sales"]).abs() / joined["sales"]).mean() * 100
    print(f"  {name:<55} sai lệch TB: {diff_pct:8.3f}%")
    return diff_pct

print("\n=== 1. Định nghĩa Revenue nào khớp sales.csv? ===")
all_true = pd.Series(True, index=df.index)
candidates = {
    "Tất cả đơn (net = qty*price - discount)": (all_true, "line_revenue"),
    "Tất cả đơn (gross = qty*price)": (all_true, "line_revenue_gross"),
    "Bỏ cancelled": (df["order_status"] != "cancelled", "line_revenue"),
    "Bỏ cancelled + returned": (~df["order_status"].isin(["cancelled", "returned"]), "line_revenue"),
    "Chỉ delivered": (df["order_status"] == "delivered", "line_revenue"),
    "Chỉ delivered + returned + shipped": (df["order_status"].isin(["delivered", "returned", "shipped"]), "line_revenue"),
}
results = {}
for name, (mask, col) in candidates.items():
    results[name] = test_definition(name, mask, col)
best = min(results, key=results.get)
print(f"\n  >>> Khớp nhất: {best} (sai lệch {results[best]:.3f}%)")

print("\n=== 1b. COGS tái dựng (định nghĩa khớp nhất ở trên) ===")
mask, _ = candidates[best]
daily_cogs = df.loc[mask].groupby("order_date")["line_cogs"].sum()
joined = pd.concat([sales.set_index("Date")["COGS"], daily_cogs], axis=1,
                   keys=["sales", "rebuilt"]).dropna()
diff = ((joined["rebuilt"] - joined["sales"]).abs() / joined["sales"]).mean() * 100
print(f"  Sai lệch COGS trung bình: {diff:.3f}%")

# ---------------------------------------------------------------
# 2. WEB_TRAFFIC GRAIN
# ---------------------------------------------------------------
print("\n=== 2. web_traffic: 1 dòng/ngày hay ngày×nguồn? ===")
wt = pd.read_csv(DATA / "web_traffic.csv", parse_dates=["date"])
per_day = wt.groupby("date").size()
print(f"  Số dòng/ngày: min={per_day.min()}, max={per_day.max()}")
print(f"  Khoảng ngày: {wt['date'].min().date()} → {wt['date'].max().date()}")
print(f"  Số nguồn traffic xuất hiện: {wt['traffic_source'].nunique()}")

# ---------------------------------------------------------------
# 3. DUPLICATE TRONG ORDER_ITEMS
# ---------------------------------------------------------------
print("\n=== 3. order_items có dòng trùng (order_id, product_id)? ===")
dup = items.duplicated(subset=["order_id", "product_id"]).sum()
print(f"  Số dòng trùng khóa: {dup}")
n_items_per_order = items.groupby("order_id").size()
print(f"  Sản phẩm/đơn: min={n_items_per_order.min()}, max={n_items_per_order.max()}, "
      f"TB={n_items_per_order.mean():.2f}")

# ---------------------------------------------------------------
# 4. NGÀY LỖ GỘP RƠI VÀO ĐÂU?
# ---------------------------------------------------------------
print("\n=== 4. Ngày COGS > Revenue phân bố thế nào? ===")
sales["loss"] = sales["COGS"] > sales["Revenue"]
print(f"  Tổng: {sales['loss'].sum()}/{len(sales)} ngày")
print("\n  Theo năm:")
print(sales.groupby(sales["Date"].dt.year)["loss"].sum().to_string())
print("\n  Theo tháng (cộng 11 năm):")
print(sales.groupby(sales["Date"].dt.month)["loss"].sum().to_string())

print("\nXong Phase 0.")
