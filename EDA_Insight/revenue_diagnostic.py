# Diagnostic revenue — kết hợp orders + order_items + products + customers +
# geography + promotions + returns + payments để trả lời "vì sao" đằng sau
# 6 chart Descriptive đã có (eda_training_charts.py).
# Output: EDA_Insight/output/07..14_*.png + in số liệu ra console.
# Chạy: python EDA_Insight/revenue_diagnostic.py (sau khi activate .venv)

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
OUT = HERE / "output"
OUT.mkdir(exist_ok=True)

C_REV, C_COGS, C_GRAY, C_ACCENT = "#A32D2D", "#185FA5", "#888780", "#534AB7"
PALETTE = ["#185FA5", "#A32D2D", "#3B6D11", "#BA7517", "#534AB7", "#993556"]

plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "grid.linestyle": ":"})

print("Đang load & join dữ liệu...")
orders = pd.read_csv(DATA / "orders.csv", parse_dates=["order_date"])
items = pd.read_csv(DATA / "order_items.csv")
products = pd.read_csv(DATA / "products.csv", usecols=["product_id", "category", "cogs"])
customers = pd.read_csv(DATA / "customers.csv", usecols=["customer_id", "acquisition_channel", "signup_date"])
geography = pd.read_csv(DATA / "geography.csv", usecols=["zip", "region"])
promotions = pd.read_csv(DATA / "promotions.csv", usecols=["promo_id", "promo_type", "promo_channel"])
returns = pd.read_csv(DATA / "returns.csv", usecols=["order_id", "refund_amount"])
sales = pd.read_csv(DATA / "sales.csv", parse_dates=["Date"])

# ---------------------------------------------------------------
# JOIN GỐC: order_items (grain = 1 dòng/sản phẩm/đơn) + mọi chiều liên quan
# ---------------------------------------------------------------
li = (items
      .merge(orders, on="order_id", how="left")
      .merge(products, on="product_id", how="left")
      .merge(customers, on="customer_id", how="left")
      .merge(geography, on="zip", how="left")
      .merge(promotions, on="promo_id", how="left"))

li["line_revenue"] = li["quantity"] * li["unit_price"]
li["line_cogs"] = li["quantity"] * li["cogs"]
li["year"] = li["order_date"].dt.year
li = li[li["year"].between(2013, 2022)].copy()  # bỏ nửa năm 2012 lẻ, đồng bộ các chart trước

# sanity check với sales.csv (Phase 0 đã xác nhận công thức)
chk = li.groupby(li["order_date"])["line_revenue"].sum()
diff = ((chk.reindex(sales.set_index("Date")["Revenue"].index) - sales.set_index("Date")["Revenue"]).abs()
        / sales.set_index("Date")["Revenue"]).mean() * 100
print(f"Sanity check — sai lệch rebuilt vs sales.csv: {diff:.3f}% (kỳ vọng ~0%)\n")

# ---------------------------------------------------------------
# 07. REVENUE THEO CATEGORY — tỷ trọng đổi qua các năm
# ---------------------------------------------------------------
cat_yr = li.groupby(["year", "category"])["line_revenue"].sum().unstack()
cat_share = cat_yr.div(cat_yr.sum(axis=1), axis=0) * 100

fig, ax = plt.subplots(figsize=(11, 5.5))
bottom = np.zeros(len(cat_share))
for i, cat in enumerate(cat_share.columns):
    ax.bar(cat_share.index, cat_share[cat], bottom=bottom, label=cat,
           color=PALETTE[i % len(PALETTE)], width=0.65)
    bottom += cat_share[cat].values
ax.set_ylabel("% doanh thu trong năm")
ax.set_title("Tỷ trọng doanh thu theo category qua các năm")
ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.08))
fig.tight_layout(); fig.savefig(OUT / "07_category_share.png", dpi=110); plt.close(fig)

print("=== 07. Category ===")
print(f"  2013: {cat_share.loc[2013].round(1).to_dict()}")
print(f"  2022: {cat_share.loc[2022].round(1).to_dict()}\n")

# ---------------------------------------------------------------
# 08. REVENUE THEO REGION
# ---------------------------------------------------------------
reg_yr = li.groupby(["year", "region"])["line_revenue"].sum().unstack() / 1e9

fig, ax = plt.subplots(figsize=(11, 5))
for i, reg in enumerate(reg_yr.columns):
    ax.plot(reg_yr.index, reg_yr[reg], "o-", color=PALETTE[i % len(PALETTE)], lw=2, label=reg)
ax.set_ylabel("Revenue (tỷ/năm)")
ax.set_title("Doanh thu theo vùng (region) qua các năm")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(OUT / "08_region_trend.png", dpi=110); plt.close(fig)

print("=== 08. Region (tỷ VND, 2022) ===")
print(f"  {reg_yr.loc[2022].round(1).to_dict()}\n")

# ---------------------------------------------------------------
# 09. KHÁCH MỚI vs KHÁCH CŨ (repeat) — nối với câu chuyện break 2019
# ---------------------------------------------------------------
first_order = orders.groupby("customer_id")["order_date"].min().rename("first_order_date")
li2 = li.merge(first_order, on="customer_id", how="left")
li2["cust_type"] = np.where(li2["order_date"] == li2["first_order_date"], "Khách mới", "Khách cũ (repeat)")
nr_yr = li2.groupby(["year", "cust_type"])["line_revenue"].sum().unstack() / 1e9

fig, ax = plt.subplots(figsize=(11, 5))
ax.bar(nr_yr.index, nr_yr["Khách cũ (repeat)"], color=C_COGS, label="Khách cũ (repeat)", width=0.6)
ax.bar(nr_yr.index, nr_yr["Khách mới"], bottom=nr_yr["Khách cũ (repeat)"], color=C_REV, label="Khách mới", width=0.6)
ax.set_ylabel("Revenue (tỷ/năm)")
ax.set_title("Doanh thu: khách mới vs khách cũ qua các năm")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(OUT / "09_new_vs_repeat.png", dpi=110); plt.close(fig)

repeat_share = (nr_yr["Khách cũ (repeat)"] / nr_yr.sum(axis=1) * 100)
print("=== 09. Tỷ trọng revenue từ khách cũ (repeat) theo năm ===")
print(f"  2013: {repeat_share.loc[2013]:.1f}%  |  2018: {repeat_share.loc[2018]:.1f}%  |  "
      f"2019: {repeat_share.loc[2019]:.1f}%  |  2022: {repeat_share.loc[2022]:.1f}%\n")

# ---------------------------------------------------------------
# 10. WATERFALL — Gross booked -> Net thực thu
# ---------------------------------------------------------------
gross = li["line_revenue"].sum()
cancelled_loss = li.loc[li["order_status"] == "cancelled", "line_revenue"].sum()
after_cancel = gross - cancelled_loss
discount_loss = li.loc[li["order_status"] != "cancelled", "discount_amount"].sum()
after_discount = after_cancel - discount_loss
refund_loss = returns["refund_amount"].sum()
net_final = after_discount - refund_loss

stages = ["Gross\nbooked", "- Hủy đơn\n(cancelled)", "- Chiết khấu\n(discount)", "- Hoàn tiền\n(returns)", "Net\nthực thu"]
values = [gross, -cancelled_loss, -discount_loss, -refund_loss, net_final]
cum = [gross, after_cancel, after_discount, net_final, net_final]
starts = [0, after_cancel, after_discount, net_final, 0]

fig, ax = plt.subplots(figsize=(11, 5.5))
colors = [C_GRAY, C_REV, C_REV, C_REV, C_ACCENT]
bar_bottoms = [0, after_cancel, after_discount, net_final, 0]
bar_heights = [gross, cancelled_loss, discount_loss, refund_loss, net_final]
for i, (s, h, c) in enumerate(zip(bar_bottoms, bar_heights, colors)):
    ax.bar(i, h, bottom=s, color=c, width=0.55)
    label = f"{(values[i] if i not in (0,4) else cum[i])/1e9:+.2f} tỷ" if i not in (0, 4) else f"{cum[i]/1e9:.2f} tỷ"
    ax.text(i, s + h + gross * 0.01, label, ha="center", fontsize=10, color="#444441")
ax.set_xticks(range(5), stages)
ax.set_ylabel("VND (tỷ)")
ax.set_title(f"Từ doanh thu ghi nhận (gross) đến thực thu ròng — 2013–2022 (hao hụt {(1-net_final/gross)*100:.1f}%)")
fig.tight_layout(); fig.savefig(OUT / "10_waterfall_net_revenue.png", dpi=110); plt.close(fig)

print("=== 10. Waterfall Gross -> Net (toàn kỳ 2013-2022, tỷ VND) ===")
print(f"  Gross booked      : {gross/1e9:8.2f}")
print(f"  - Hủy đơn         : {-cancelled_loss/1e9:8.2f}  ({cancelled_loss/gross*100:.1f}%)")
print(f"  - Chiết khấu      : {-discount_loss/1e9:8.2f}  ({discount_loss/gross*100:.1f}%)")
print(f"  - Hoàn tiền       : {-refund_loss/1e9:8.2f}  ({refund_loss/gross*100:.1f}%)")
print(f"  = Net thực thu    : {net_final/1e9:8.2f}  ({net_final/gross*100:.1f}% của gross)\n")

# ---------------------------------------------------------------
# 11. REVENUE THEO KÊNH (order_source) QUA CÁC NĂM
# ---------------------------------------------------------------
src_yr = li.groupby(["year", "order_source"])["line_revenue"].sum().unstack() / 1e9

fig, ax = plt.subplots(figsize=(11, 5))
for i, src in enumerate(src_yr.columns):
    ax.plot(src_yr.index, src_yr[src], "o-", color=PALETTE[i % len(PALETTE)], lw=1.8, label=src)
ax.set_ylabel("Revenue (tỷ/năm)")
ax.set_title("Doanh thu theo kênh đặt hàng (order_source) qua các năm")
ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.1))
fig.tight_layout(); fig.savefig(OUT / "11_channel_trend.png", dpi=110); plt.close(fig)

print("=== 11. Kênh order_source (tỷ VND, 2022) ===")
print(f"  {src_yr.loc[2022].round(1).to_dict()}\n")

# ---------------------------------------------------------------
# 12. GIÁ TRỊ KHÁCH HÀNG THEO ACQUISITION_CHANNEL (kênh nào "câu" khách xịn)
# ---------------------------------------------------------------
cust_rev = li.groupby("customer_id")["line_revenue"].sum().rename("total_revenue")
cust_ch = customers.set_index("customer_id")["acquisition_channel"]
ltv = cust_rev.to_frame().join(cust_ch).groupby("acquisition_channel")["total_revenue"].mean().sort_values() / 1e6

fig, ax = plt.subplots(figsize=(9, 5))
ax.barh(ltv.index, ltv.values, color=C_ACCENT)
for i, v in enumerate(ltv.values):
    ax.text(v, i, f"  {v:.2f} tr", va="center", fontsize=10, color="#444441")
ax.set_xlabel("Revenue trung bình / khách (triệu VND, trọn đời trong data)")
ax.set_title("Giá trị khách hàng theo kênh acquisition — kênh nào mang khách chất lượng?")
fig.tight_layout(); fig.savefig(OUT / "12_ltv_by_channel.png", dpi=110); plt.close(fig)

print("=== 12. LTV theo acquisition_channel (triệu VND/khách) ===")
print(f"  {ltv.round(2).to_dict()}\n")

# ---------------------------------------------------------------
# 13. REVENUE THEO PAYMENT_METHOD QUA CÁC NĂM (tỷ trọng)
# ---------------------------------------------------------------
pay_yr = li.groupby(["year", "payment_method"])["line_revenue"].sum().unstack()
pay_share = pay_yr.div(pay_yr.sum(axis=1), axis=0) * 100

fig, ax = plt.subplots(figsize=(11, 5.5))
bottom = np.zeros(len(pay_share))
for i, pm in enumerate(pay_share.columns):
    ax.bar(pay_share.index, pay_share[pm], bottom=bottom, label=pm,
           color=PALETTE[i % len(PALETTE)], width=0.65)
    bottom += pay_share[pm].values
ax.set_ylabel("% doanh thu trong năm")
ax.set_title("Tỷ trọng doanh thu theo phương thức thanh toán qua các năm")
ax.legend(frameon=False, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.08))
fig.tight_layout(); fig.savefig(OUT / "13_payment_method_share.png", dpi=110); plt.close(fig)

print("=== 13. Payment method ===")
print(f"  2013: {pay_share.loc[2013].round(1).to_dict()}")
print(f"  2022: {pay_share.loc[2022].round(1).to_dict()}\n")

# ---------------------------------------------------------------
# 14. KHUYẾN MÃI: AOV promo vs non-promo + revenue theo promo_type
# ---------------------------------------------------------------
li["has_promo"] = li["promo_id"].notna()
order_val = li.groupby(["order_id", "has_promo"])["line_revenue"].sum().reset_index()
aov = order_val.groupby("has_promo")["line_revenue"].mean()

promo_type_rev = li[li["has_promo"]].groupby("promo_type")["line_revenue"].sum() / 1e9

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
ax1.bar(["Không promo", "Có promo"], aov.values / 1e3, color=[C_GRAY, C_ACCENT], width=0.5)
for i, v in enumerate(aov.values / 1e3):
    ax1.text(i, v, f"{v:.1f}k", ha="center", va="bottom", fontsize=10)
ax1.set_ylabel("Giá trị đơn TB (nghìn VND)")
ax1.set_title("AOV: đơn có promo vs không promo")

ax2.bar(promo_type_rev.index, promo_type_rev.values, color=[C_REV, C_COGS], width=0.5)
ax2.set_ylabel("Revenue (tỷ)")
ax2.set_title("Doanh thu theo loại khuyến mãi")
fig.tight_layout(); fig.savefig(OUT / "14_promo_effect.png", dpi=110); plt.close(fig)

print("=== 14. Khuyến mãi ===")
print(f"  AOV không promo: {aov[False]:,.0f} VND | AOV có promo: {aov[True]:,.0f} VND "
      f"(chênh {(aov[True]/aov[False]-1)*100:+.1f}%)")
print(f"  Revenue theo promo_type (tỷ): {promo_type_rev.round(2).to_dict()}\n")

print(f"Đã lưu 8 chart (07-14) vào {OUT}")
