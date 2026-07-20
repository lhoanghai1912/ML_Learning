# Diagnostic revenue — kết hợp orders + order_items + products + customers +
# geography + promotions + returns + payments để trả lời "vì sao" đằng sau
# 6 chart Descriptive đã có (eda_training_charts.py, phase1_descriptive/).
# Output: EDA_Insight/output/phase2/07..14_*.png + in số liệu ra console.
# Chạy: python EDA_Insight/phase2_diagnostic/revenue_diagnostic.py (sau khi activate .venv)

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

HERE = Path(__file__).resolve().parent           # EDA_Insight/phase2_diagnostic/
DATA = HERE.parent.parent / "data"                # dữ liệu gốc: <project root>/data
OUT = HERE.parent / "output" / "phase2"           # chart: EDA_Insight/output/phase2/
OUT.mkdir(parents=True, exist_ok=True)

C_REV, C_COGS, C_GRAY, C_ACCENT = "#A32D2D", "#185FA5", "#888780", "#534AB7"
PALETTE = ["#185FA5", "#A32D2D", "#3B6D11", "#BA7517", "#534AB7", "#993556"]

plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "grid.linestyle": ":"})

print("Đang load & join dữ liệu...")
orders = pd.read_csv(DATA / "orders.csv", parse_dates=["order_date"])
items = pd.read_csv(DATA / "order_items.csv")
products = pd.read_csv(DATA / "products.csv", usecols=["product_id", "category", "cogs", "price"])
customers = pd.read_csv(DATA / "customers.csv", usecols=["customer_id", "acquisition_channel", "signup_date"])
geography = pd.read_csv(DATA / "geography.csv", usecols=["zip", "region"])
promotions = pd.read_csv(DATA / "promotions.csv",
                          usecols=["promo_id", "promo_type", "promo_channel", "discount_value",
                                   "start_date", "end_date"],
                          parse_dates=["start_date", "end_date"])
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
li["month"] = li["order_date"].dt.month
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

# =================================================================
# PHẦN MỞ RỘNG — Giai đoạn 2 chính thức (2026-07-20, DA)
# Trả lời 5 câu hỏi Diagnostic bắt buộc (xem PROGRESS.md #2 + đề bài task):
#   Q1 (15-16) vì sao 2019-2021 sụt mạnh — tách giá/khối lượng/promo
#   Q2 (17-18) cơ chế lỗ gộp — unit_price vs catalog cost, đối chiếu promo
#   Q3 (19)    margin category/region — kiểm soát biến nhiễu mix
#   Q4 (20)    marketing channel (order_source) — revenue+margin theo năm
#   Q5 (21)    Tết x cường độ khuyến mãi
# Export CSV vào phase2_diagnostic/data/ (trước đây để trống có chủ đích — xem DATA_LINEAGE.md).
# Chart mới đánh số tiếp 29-35 (không đè 07-14 đã có).
# =================================================================
DATA_OUT = HERE / "data"
DATA_OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------
# 15. Q1 — VÌ SAO 2019-2021 SỤT MẠNH? Tách ASP (giá) vs qty/orders/khách (khối lượng)
# ---------------------------------------------------------------
yr_kpi = li.groupby("year").agg(revenue=("line_revenue", "sum"), qty=("quantity", "sum")).reset_index()
yr_kpi["ASP"] = yr_kpi["revenue"] / yr_kpi["qty"]

ord_all = orders.assign(year=orders["order_date"].dt.year)
ord_all = ord_all[ord_all["year"].between(2013, 2022)]
n_orders = ord_all.groupby("year")["order_id"].nunique().rename("n_orders")
n_active_cust = ord_all.groupby("year")["customer_id"].nunique().rename("n_active_cust")
yr_kpi = yr_kpi.merge(n_orders, on="year").merge(n_active_cust, on="year")
yr_kpi["AOV"] = yr_kpi["revenue"] / yr_kpi["n_orders"]
yr_kpi.to_csv(DATA_OUT / "yearly_kpi_decompose.csv", index=False)

base = yr_kpi.set_index("year")
r18, r19 = base.loc[2018], base.loc[2019]
d_revenue = (r19["revenue"] / r18["revenue"] - 1) * 100
d_asp = (r19["ASP"] / r18["ASP"] - 1) * 100
d_qty = (r19["qty"] / r18["qty"] - 1) * 100
d_orders = (r19["n_orders"] / r18["n_orders"] - 1) * 100
d_cust = (r19["n_active_cust"] / r18["n_active_cust"] - 1) * 100
d_aov = (r19["AOV"] / r18["AOV"] - 1) * 100

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
idx = base.index
ax1.plot(idx, base["revenue"] / 1e9, "o-", color=C_REV, lw=2, label="Revenue (tỷ)")
ax1.axvline(2019, color=C_GRAY, ls="--", lw=1)
ax1.set_ylabel("Revenue (tỷ VND)"); ax1.set_title("Revenue theo năm — break 2019")
ax1b = ax1.twinx()
ax1b.plot(idx, base["ASP"], "s--", color=C_ACCENT, lw=1.6, label="ASP (giá bán TB/đơn vị)")
ax1b.set_ylabel("ASP (VND/đơn vị)", color=C_ACCENT)
l1, lb1 = ax1.get_legend_handles_labels(); l2, lb2 = ax1b.get_legend_handles_labels()
ax1.legend(l1 + l2, lb1 + lb2, frameon=False, loc="upper right", fontsize=9)

idx100 = base / base.loc[2018] * 100
for col, c, lbl in [("qty", C_COGS, "Số lượng bán (qty)"), ("n_orders", C_REV, "Số đơn"),
                     ("n_active_cust", C_ACCENT, "Khách active"), ("ASP", "#3B6D11", "ASP")]:
    ax2.plot(idx, idx100[col], "o-", color=c, lw=1.8, label=lbl)
ax2.axhline(100, color=C_GRAY, ls=":", lw=1)
ax2.axvline(2019, color=C_GRAY, ls="--", lw=1)
ax2.set_ylabel("Index (2018 = 100)"); ax2.set_title("Volume rơi mạnh, ASP KHÔNG giảm (index 2018=100)")
ax2.legend(frameon=False, fontsize=9)
fig.tight_layout(); fig.savefig(OUT / "29_yearly_price_volume_decompose.png", dpi=110); plt.close(fig)

print("=== 15. Q1 — Decompose YoY 2018→2019 ===")
print(f"  Revenue {d_revenue:+.1f}% | ASP {d_asp:+.1f}% | Qty {d_qty:+.1f}% | "
      f"Số đơn {d_orders:+.1f}% | Khách active {d_cust:+.1f}% | AOV {d_aov:+.1f}%")
print("  -> ASP KHÔNG giảm (thậm chí tăng nhẹ); sụt giảm gần như toàn bộ đến từ khối lượng"
      " (qty/số đơn) rơi ~40%, khách active rơi ~28%.\n")

# ---------------------------------------------------------------
# 16. Q1(c) — CƯỜNG ĐỘ KHUYẾN MÃI THEO NĂM (join order_items + promotions qua promo_id, FK sạch 100%)
# ---------------------------------------------------------------
li["has_promo"] = li["promo_id"].notna()
promo_line_rev = li.loc[li["has_promo"]].groupby("year")["line_revenue"].sum()
total_rev_yr = li.groupby("year")["line_revenue"].sum()
avg_discount_active = li.loc[li["has_promo"]].groupby("year")["discount_value"].mean()

promo_rev = pd.DataFrame({
    "pct_revenue_with_promo": (promo_line_rev / total_rev_yr * 100),
    "pct_lineitems_with_promo": li.groupby("year")["has_promo"].mean() * 100,
    "avg_discount_value_active_pct": avg_discount_active,
})
active_counts = {}
for y in range(2013, 2023):
    y_start, y_end = pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y}-12-31")
    active_counts[y] = int(((promotions["start_date"] <= y_end) & (promotions["end_date"] >= y_start)).sum())
promo_rev["n_promo_active_overlap"] = pd.Series(active_counts)
promo_rev.index.name = "year"
promo_rev.reset_index().to_csv(DATA_OUT / "promo_intensity_by_year.csv", index=False)

fig, ax = plt.subplots(figsize=(11, 5))
colors = [C_ACCENT if y != 2019 else C_REV for y in promo_rev.index]
ax.bar(promo_rev.index, promo_rev["pct_revenue_with_promo"], color=colors, width=0.6)
ax.axvline(2019, color=C_GRAY, ls="--", lw=1)
ax.set_ylabel("% doanh thu đến từ dòng hàng có promo")
ax.set_title("Cường độ khuyến mãi theo năm — dao động chu kỳ lẻ/chẵn (Rural/Urban Special),\nKHÔNG nhảy vọt hay sụt bất thường tại 2019")
fig.tight_layout(); fig.savefig(OUT / "30_promo_intensity_by_year.png", dpi=110); plt.close(fig)

print("=== 16. Q1(c) — Cường độ khuyến mãi theo năm (% doanh thu có promo) ===")
print(promo_rev["pct_revenue_with_promo"].round(1).to_dict())
print(f"  n_promo_active_overlap theo năm: {active_counts}")
print("  -> 2019 (38.4%) nằm đúng nhịp năm lẻ (2013/2015/2017/2019/2021 ~38-40%,"
      " năm chẵn ~30-32%) — mix/cường độ promo KHÔNG phải nguyên nhân break.\n")

# ---------------------------------------------------------------
# 17. Q2 — CƠ CHẾ LỖ GỘP: unit_price/catalog price theo tháng, đối chiếu promotion đang chạy
# ---------------------------------------------------------------
li["below_cost"] = li["unit_price"] < li["cogs"]
li["price_ratio"] = li["unit_price"] / li["price"]

mo = li.groupby("month").agg(
    mean_price_ratio=("price_ratio", "mean"),
    median_price_ratio=("price_ratio", "median"),
    pct_below_cost=("below_cost", "mean"),
).reset_index()
mo["pct_below_cost"] *= 100
bc_by_promo = li.groupby(["month", "has_promo"])["below_cost"].mean().unstack() * 100
mo["pct_below_cost_with_promo"] = mo["month"].map(bc_by_promo[True])
mo["pct_below_cost_without_promo"] = mo["month"].map(bc_by_promo[False])

promo_days_by_month = []
for m in range(1, 13):
    days = sum(len(pd.date_range(p.start_date, p.end_date, freq="D")[pd.date_range(p.start_date, p.end_date, freq="D").month == m])
               for _, p in promotions.iterrows())
    promo_days_by_month.append(days)
mo["promo_active_days_sum_alltime"] = promo_days_by_month
mo.to_csv(DATA_OUT / "monthly_unit_price_ratio.csv", index=False)

overall_bc_promo = li.loc[li["has_promo"], "below_cost"].mean() * 100
overall_bc_nopromo = li.loc[~li["has_promo"], "below_cost"].mean() * 100

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
ax1.bar(mo["month"], mo["pct_below_cost"], color=C_GRAY, width=0.6, label="% dòng bán dưới giá vốn")
ax1b = ax1.twinx()
ax1b.plot(mo["month"], mo["mean_price_ratio"], "o-", color=C_ACCENT, lw=2, label="unit_price/catalog price (TB)")
ax1b.axhline(1.0, color=C_REV, ls=":", lw=1)
ax1.set_xticks(range(1, 13)); ax1.set_xlabel("Tháng"); ax1.set_ylabel("% dòng bán dưới giá vốn")
ax1b.set_ylabel("Tỷ lệ unit_price/catalog price", color=C_ACCENT)
ax1.set_title("Tỷ lệ bán dưới giá vốn theo tháng (dồn T7-9, T11-12)")
l1, lb1 = ax1.get_legend_handles_labels(); l2, lb2 = ax1b.get_legend_handles_labels()
ax1.legend(l1 + l2, lb1 + lb2, frameon=False, fontsize=8, loc="upper center")

ax2.bar(mo["month"] - 0.2, mo["pct_below_cost_with_promo"], width=0.4, color=C_ACCENT, label="Dòng CÓ promo")
ax2.bar(mo["month"] + 0.2, mo["pct_below_cost_without_promo"], width=0.4, color=C_GRAY, label="Dòng KHÔNG promo")
ax2.set_xticks(range(1, 13)); ax2.set_xlabel("Tháng"); ax2.set_ylabel("% dòng bán dưới giá vốn")
ax2.set_title(f"Toàn kỳ: có promo {overall_bc_promo:.1f}% dòng dưới giá vốn vs không promo {overall_bc_nopromo:.1f}%")
ax2.legend(frameon=False, fontsize=9)
fig.tight_layout(); fig.savefig(OUT / "31_unit_price_ratio_by_month.png", dpi=110); plt.close(fig)

print("=== 17. Q2 — Cơ chế lỗ gộp: promotion là nguyên nhân trực tiếp ===")
print(f"  % dòng bán dưới giá vốn KHI có promo   : {overall_bc_promo:.2f}%")
print(f"  % dòng bán dưới giá vốn KHI KHÔNG có promo: {overall_bc_nopromo:.2f}%")
top4 = mo.sort_values("pct_below_cost", ascending=False)[["month", "pct_below_cost"]].head(4)
print(f"  4 tháng lỗ nhiều dòng nhất: {top4.to_dict('records')}\n")

# ---------------------------------------------------------------
# 18. Q2 — TỶ LỆ BÁN DƯỚI GIÁ VỐN THEO CATEGORY — có tập trung Casual/Streetwear?
# ---------------------------------------------------------------
total_rev_by_cat = li.groupby("category")["line_revenue"].sum()
bc_cat = li.groupby("category").agg(
    n_lines=("below_cost", "size"),
    pct_lineitems_below_cost=("below_cost", "mean"),
    revenue_below_cost=("line_revenue", lambda s: s[li.loc[s.index, "below_cost"]].sum()),
).reset_index()
bc_cat["pct_lineitems_below_cost"] *= 100
bc_cat["pct_revenue_below_cost"] = bc_cat.apply(
    lambda r: r["revenue_below_cost"] / total_rev_by_cat[r["category"]] * 100, axis=1)
bc_cat = bc_cat.sort_values("pct_lineitems_below_cost", ascending=False)
bc_cat.to_csv(DATA_OUT / "category_below_cost_rate.csv", index=False)

fig, ax = plt.subplots(figsize=(9, 5))
ax.barh(bc_cat["category"], bc_cat["pct_lineitems_below_cost"], color=PALETTE[:len(bc_cat)])
for i, v in enumerate(bc_cat["pct_lineitems_below_cost"]):
    ax.text(v, i, f"  {v:.1f}%", va="center", fontsize=10)
ax.set_xlabel("% dòng hàng bán dưới giá vốn")
ax.set_title("Tỷ lệ bán dưới giá vốn theo category")
fig.tight_layout(); fig.savefig(OUT / "32_below_cost_rate_by_category.png", dpi=110); plt.close(fig)

print("=== 18. Q2 — % dòng bán dưới giá vốn theo category ===")
print(bc_cat[["category", "pct_lineitems_below_cost", "pct_revenue_below_cost"]].round(2).to_string(index=False), "\n")

# ---------------------------------------------------------------
# 19. Q3 — MARGIN CATEGORY x REGION: kiểm soát biến nhiễu mix category
# ---------------------------------------------------------------
rc = li.groupby(["region", "category"]).agg(revenue=("line_revenue", "sum"), cogs=("line_cogs", "sum")).reset_index()
rc["margin_pct"] = (rc["revenue"] - rc["cogs"]) / rc["revenue"] * 100
rc["share_in_region_pct"] = rc["revenue"] / rc.groupby("region")["revenue"].transform("sum") * 100
rc.to_csv(DATA_OUT / "category_region_margin_controlled.csv", index=False)

nat_w = li.groupby("category")["line_revenue"].sum()
nat_w = nat_w / nat_w.sum()
region_actual = li.groupby("region").apply(
    lambda g: (g["line_revenue"].sum() - g["line_cogs"].sum()) / g["line_revenue"].sum() * 100,
    include_groups=False)
mix_rows = []
for reg in li["region"].dropna().unique():
    g = li[li["region"] == reg]
    cat_m = g.groupby("category").apply(
        lambda x: (x["line_revenue"].sum() - x["line_cogs"].sum()) / x["line_revenue"].sum() * 100,
        include_groups=False)
    mix_adj = sum(cat_m[c] * nat_w[c] for c in nat_w.index)
    mix_rows.append({"region": reg, "actual_margin_pct": region_actual[reg], "mix_adjusted_margin_pct": mix_adj})
mix_df = pd.DataFrame(mix_rows)
mix_df["mix_effect_pp"] = mix_df["actual_margin_pct"] - mix_df["mix_adjusted_margin_pct"]
mix_df.to_csv(DATA_OUT / "region_margin_mix_decomposition.csv", index=False)

fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(mix_df)); w = 0.35
ax.bar(x - w / 2, mix_df["actual_margin_pct"], w, color=C_REV, label="Margin thực tế")
ax.bar(x + w / 2, mix_df["mix_adjusted_margin_pct"], w, color=C_ACCENT, label="Margin nếu mix category = TB toàn quốc")
ax.set_xticks(x, mix_df["region"])
ax.set_ylabel("Margin %")
ax.set_title("Region margin: bao nhiêu do mix category, bao nhiêu do giá/discount thật?")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(OUT / "33_category_region_margin_controlled.png", dpi=110); plt.close(fig)

print("=== 19. Q3 — Margin region: thực tế vs mix-adjusted (trọng số category toàn quốc) ===")
print(mix_df.round(3).to_string(index=False), "\n")

# ---------------------------------------------------------------
# 20. Q4 — MARKETING CHANNEL (order_source): revenue + margin theo năm
# ---------------------------------------------------------------
ch = li.groupby(["year", "order_source"]).agg(revenue=("line_revenue", "sum"), cogs=("line_cogs", "sum")).reset_index()
ch["margin_pct"] = (ch["revenue"] - ch["cogs"]) / ch["revenue"] * 100
ch.to_csv(DATA_OUT / "channel_revenue_margin_by_year.csv", index=False)

piv_rev = ch.pivot(index="year", columns="order_source", values="revenue") / 1e9
piv_margin = ch.pivot(index="year", columns="order_source", values="margin_pct")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
for i, c in enumerate(piv_rev.columns):
    ax1.plot(piv_rev.index, piv_rev[c], "o-", color=PALETTE[i % len(PALETTE)], lw=1.6, label=c)
ax1.axvline(2019, color=C_GRAY, ls="--", lw=1)
ax1.set_ylabel("Revenue (tỷ)"); ax1.set_title("Revenue theo kênh — mọi kênh gãy cùng lúc 2019")
ax1.legend(frameon=False, fontsize=8, ncol=2)

for i, c in enumerate(piv_margin.columns):
    ax2.plot(piv_margin.index, piv_margin[c], "o-", color=PALETTE[i % len(PALETTE)], lw=1.6, label=c)
ax2.axvline(2019, color=C_GRAY, ls="--", lw=1)
ax2.set_ylabel("Margin %"); ax2.set_title("Margin theo kênh — dao động theo năm, không lệch riêng 1 kênh")
fig.tight_layout(); fig.savefig(OUT / "34_channel_revenue_margin_trend.png", dpi=110); plt.close(fig)

drop_by_channel = (piv_rev.loc[2019] / piv_rev.loc[2018] - 1) * 100
print("=== 20. Q4 — Sụt giảm revenue 2018→2019 theo kênh (%) ===")
print(drop_by_channel.round(1).to_dict())
print("  -> Tất cả kênh rơi cùng biên độ (~37-41%) cùng lúc -> break 2019 là vấn đề hệ thống,"
      " không phải 1 kênh marketing riêng lẻ suy yếu.\n")

# ---------------------------------------------------------------
# 21. Q5 — TẾT: tương quan biến động doanh thu quanh Tết với cường độ khuyến mãi trùng thời điểm
# ---------------------------------------------------------------
tet_dates = pd.read_csv(HERE.parent / "phase1_descriptive" / "data" / "tet_dates.csv", parse_dates=["tet_date"])
tet_stats = pd.read_csv(HERE.parent / "phase1_descriptive" / "data" / "tet_yearly_stats.csv")

rows = []
for _, r in tet_stats.iterrows():
    y = int(r["year"])
    tdate = tet_dates.loc[tet_dates["year"] == y, "tet_date"].iloc[0]
    win_start, win_end = tdate - pd.Timedelta(days=30), tdate + pd.Timedelta(days=30)
    overlap = promotions[(promotions["start_date"] <= win_end) & (promotions["end_date"] >= win_start)]
    rows.append({
        "year": y, "tet_date": tdate.date().isoformat(),
        "n_promo_overlap_tet": len(overlap),
        "promo_ids_overlap": ";".join(overlap["promo_id"].tolist()),
        "max_discount_pct_overlap": overlap["discount_value"].max() if len(overlap) else 0.0,
        "dip_pct": r["dip_pct"], "pre_week_pct": r["pre_week_pct"],
    })
tet_promo = pd.DataFrame(rows)
tet_promo.to_csv(DATA_OUT / "tet_promo_overlap.csv", index=False)

corr_dip = tet_promo["n_promo_overlap_tet"].corr(tet_promo["dip_pct"])
corr_pre = tet_promo["n_promo_overlap_tet"].corr(tet_promo["pre_week_pct"])

fig, ax = plt.subplots(figsize=(9, 5.5))
sc = ax.scatter(tet_promo["n_promo_overlap_tet"], tet_promo["dip_pct"], c=tet_promo["year"], cmap="viridis", s=90)
for _, r in tet_promo.iterrows():
    ax.annotate(str(int(r["year"])), (r["n_promo_overlap_tet"], r["dip_pct"]), fontsize=8, xytext=(4, 4), textcoords="offset points")
ax.set_xlabel("Số promo trùng cửa sổ ±30 ngày quanh Tết")
ax.set_ylabel("% lệch baseline vùng quanh mồng 1 (dip_pct)")
ax.set_title(f"Tết x Promo: n=10 năm, corr(n_promo, dip_pct)={corr_dip:.2f}")
fig.colorbar(sc, label="Năm")
fig.tight_layout(); fig.savefig(OUT / "35_tet_promo_overlap.png", dpi=110); plt.close(fig)

print("=== 21. Q5 — Tương quan số promo trùng Tết vs biến động doanh thu quanh Tết ===")
print(tet_promo[["year", "n_promo_overlap_tet", "promo_ids_overlap", "dip_pct", "pre_week_pct"]].to_string(index=False))
print(f"  corr(n_promo_overlap_tet, dip_pct) = {corr_dip:.3f} (n=10, mẫu nhỏ — chỉ mang tính gợi ý, KHÔNG kết luận nhân quả)")
print(f"  corr(n_promo_overlap_tet, pre_week_pct) = {corr_pre:.3f}\n")

print(f"Đã lưu 7 chart mới (29-35) vào {OUT}")
print(f"Đã export 8 CSV vào {DATA_OUT}")
