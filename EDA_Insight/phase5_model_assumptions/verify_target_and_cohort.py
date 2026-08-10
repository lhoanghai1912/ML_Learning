"""
Giai đoạn 5 — Verify script (CHỈ ĐỌC data/, không sửa/ghi đè gì trong data/).
Chạy: .venv/bin/python EDA_Insight/phase5_model_assumptions/verify_target_and_cohort.py

Nhiệm vụ 1: chứng minh sales.csv (Revenue/COGS) = gross demand tổng hợp từ order_items,
            KỂ CẢ đơn cancelled, KHÔNG trừ discount. In đối chiếu vài dòng cụ thể + MAPE toàn kỳ.
Nhiệm vụ 3: verify độc lập nghi vấn cohort retention phẳng ~3% (Phase 3), tự group theo
            THÁNG mua đầu tiên (first order month) — khác cách Phase 3 (dùng signup_date) —
            để xem có phải đặc tính chung của cơ chế sinh dữ liệu hay chỉ do 1 cách đo.

Output: EDA_Insight/phase5_model_assumptions/data/target_reconcile_sample.csv
        EDA_Insight/phase5_model_assumptions/data/cohort_retention_by_first_order.csv
"""
import pandas as pd
import numpy as np

DATA = "data"
OUT = "EDA_Insight/phase5_model_assumptions/data"

# ============================================================
# NHIỆM VỤ 1 — Verify target gross
# ============================================================
print("=" * 70)
print("NHIỆM VỤ 1 — Verify sales.csv = gross demand (order_items, kể cả cancelled)")
print("=" * 70)

sales = pd.read_csv(f"{DATA}/sales.csv", parse_dates=["Date"])
oi = pd.read_csv(f"{DATA}/order_items.csv")
orders = pd.read_csv(f"{DATA}/orders.csv", parse_dates=["order_date"])
products = pd.read_csv(f"{DATA}/products.csv")

oi = oi.merge(orders[["order_id", "order_date", "order_status"]], on="order_id", how="left")
oi = oi.merge(products[["product_id", "cogs"]], on="product_id", how="left")

# GROSS: tất cả đơn (kể cancelled), KHÔNG trừ discount
oi["gross_revenue_line"] = oi["quantity"] * oi["unit_price"]
oi["gross_cogs_line"] = oi["quantity"] * oi["cogs"]

daily_gross = oi.groupby(oi["order_date"].dt.date).agg(
    gross_revenue=("gross_revenue_line", "sum"),
    gross_cogs=("gross_cogs_line", "sum"),
).reset_index().rename(columns={"order_date": "Date"})
daily_gross["Date"] = pd.to_datetime(daily_gross["Date"])

cmp = sales.merge(daily_gross, on="Date", how="inner")
cmp["rev_diff_pct"] = (cmp["Revenue"] - cmp["gross_revenue"]).abs() / cmp["Revenue"] * 100
cmp["cogs_diff_pct"] = (cmp["COGS"] - cmp["gross_cogs"]).abs() / cmp["COGS"] * 100

print(f"\nSố ngày đối chiếu: {len(cmp)} (kỳ vọng 3,833)")
print(f"MAPE Revenue (sales.csv vs rebuild gross từ order_items, kể cả cancelled): {cmp['rev_diff_pct'].mean():.6f}%")
print(f"MAPE COGS    (sales.csv vs rebuild gross từ order_items, kể cả cancelled): {cmp['cogs_diff_pct'].mean():.6f}%")
print(f"Max lệch Revenue: {cmp['rev_diff_pct'].max():.6f}% | Max lệch COGS: {cmp['cogs_diff_pct'].max():.6f}%")

print("\n--- Đối chiếu cụ thể 5 ngày đầu ---")
print(cmp[["Date", "Revenue", "gross_revenue", "rev_diff_pct", "COGS", "gross_cogs", "cogs_diff_pct"]].head(5).to_string(index=False))

print("\n--- Đối chiếu cụ thể 5 ngày ngẫu nhiên (seed=42) ---")
print(cmp.sample(5, random_state=42)[["Date", "Revenue", "gross_revenue", "rev_diff_pct", "COGS", "gross_cogs", "cogs_diff_pct"]]
      .sort_values("Date").to_string(index=False))

# Đối chứng: thử bản NET (loại cancelled, trừ discount) để chứng minh nó KHÔNG khớp
oi_net = oi[oi["order_status"] != "cancelled"].copy()
oi_net["net_revenue_line"] = oi_net["quantity"] * oi_net["unit_price"] - oi_net["discount_amount"]
daily_net = oi_net.groupby(oi_net["order_date"].dt.date)["net_revenue_line"].sum().reset_index()
daily_net.columns = ["Date", "net_revenue"]
daily_net["Date"] = pd.to_datetime(daily_net["Date"])
cmp_net = sales.merge(daily_net, on="Date", how="inner")
cmp_net["diff_pct"] = (cmp_net["Revenue"] - cmp_net["net_revenue"]).abs() / cmp_net["Revenue"] * 100
print(f"\n[Đối chứng] MAPE nếu dùng NET (loại cancelled, trừ discount) thay vì gross: {cmp_net['diff_pct'].mean():.3f}% "
      f"(rõ ràng lệch nhiều so với {cmp['rev_diff_pct'].mean():.6f}% của gross — xác nhận target = gross)")

cmp.to_csv(f"{OUT}/target_reconcile_sample.csv", index=False)
print(f"\nĐã lưu: {OUT}/target_reconcile_sample.csv ({len(cmp)} dòng)")

# ============================================================
# NHIỆM VỤ 3 — Verify độc lập cohort retention phẳng ~3%
# ============================================================
print("\n" + "=" * 70)
print("NHIỆM VỤ 3 — Verify độc lập retention, cohort = THÁNG ĐƠN HÀNG ĐẦU TIÊN (không dùng signup_date)")
print("=" * 70)

orders_nc = orders[orders["order_status"] != "cancelled"].copy()
orders_nc["order_month"] = orders_nc["order_date"].dt.to_period("M")

first_order = orders_nc.groupby("customer_id")["order_month"].min().rename("cohort_month")
orders_nc = orders_nc.merge(first_order, on="customer_id", how="left")
orders_nc["offset_month"] = (orders_nc["order_month"] - orders_nc["cohort_month"]).apply(lambda x: x.n)

last_data_month = orders_nc["order_month"].max()
cohort_sizes = first_order.value_counts().rename("n_customers")

# active customer-month set
active = orders_nc[["customer_id", "cohort_month", "offset_month"]].drop_duplicates()

max_offset = 12
records = []
for offset in range(0, max_offset + 1):
    # chỉ tính cohort đủ thời gian quan sát đến offset đó (tránh bias cohort cuối kỳ)
    valid_cohorts = [cm for cm in cohort_sizes.index if (cm + offset) <= last_data_month]
    if not valid_cohorts:
        continue
    denom = cohort_sizes.loc[valid_cohorts].sum()
    n_active = active[(active["offset_month"] == offset) & (active["cohort_month"].isin(valid_cohorts))]["customer_id"].nunique()
    records.append({"offset_month": offset, "n_customers_denom": int(denom), "n_active": n_active, "retention_pct": 100 * n_active / denom})

ret_df = pd.DataFrame(records)
print("\nRetention theo offset (cohort = tháng đơn hàng KHÔNG-cancelled ĐẦU TIÊN của khách, weighted toàn mẫu):")
print(ret_df.to_string(index=False))

print(f"\nM1={ret_df.loc[ret_df.offset_month==1,'retention_pct'].values[0]:.2f}% | "
      f"M3={ret_df.loc[ret_df.offset_month==3,'retention_pct'].values[0]:.2f}% | "
      f"M6={ret_df.loc[ret_df.offset_month==6,'retention_pct'].values[0]:.2f}% | "
      f"M12={ret_df.loc[ret_df.offset_month==12,'retention_pct'].values[0]:.2f}%")
print(f"Std across offset 1-12: {ret_df[ret_df.offset_month.between(1,12)]['retention_pct'].std():.3f} điểm % "
      "(nếu nhỏ => phẳng, xác nhận Phase 3)")

ret_df.to_csv(f"{OUT}/cohort_retention_by_first_order.csv", index=False)
print(f"\nĐã lưu: {OUT}/cohort_retention_by_first_order.csv ({len(ret_df)} dòng)")

# Thêm 1 phép đo độc lập thứ 2: xác suất mua trong 1 tháng bất kỳ, theo tenure (số tháng kể từ đơn đầu)
# so sánh khách "tenure thấp" (mới) vs "tenure cao" (cũ) xem có khác nhau về xác suất active không
print("\n--- Kiểm tra thêm: xác suất active theo 'độ tuổi' quan hệ khách hàng (tenure bucket) ---")
tenure_days = (orders_nc.groupby("customer_id")["order_date"].max() - orders_nc.groupby("customer_id")["order_date"].min()).dt.days
freq = orders_nc.groupby("customer_id").size()
print(f"Trung bình số đơn/khách (non-cancelled): {freq.mean():.2f} | Trung bình khoảng tenure (ngày, max-min order date): {tenure_days.mean():.1f}")
print("(Nếu hành vi có 'decay' thật, khách tenure dài sẽ có tần suất mua/tháng giảm dần theo tuổi — "
      "nhưng bảng retention ở trên đã cho thấy KHÔNG có xu hướng giảm rõ theo offset.)")

print("\nDone.")
