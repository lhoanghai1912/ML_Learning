# Phase 4 — Prescriptive: 4 đề xuất định lượng
# Đọc: data/{order_items,orders,products}.csv (raw, chỉ đọc)
#      + phase2_diagnostic/data/category_region_margin_controlled.csv
#      + phase3_dashboard/data/{rfm_customer_segments,churn_risk_scores}.csv
# Xuất: phase4_prescriptive/data/*.csv + output/phase4/36..38_*.png
# Chạy: .venv/bin/python EDA_Insight/phase4_prescriptive/prescriptive_analysis.py

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

HERE = Path(__file__).resolve().parent                  # EDA_Insight/phase4_prescriptive/
ROOT = HERE.parent.parent                                # project root
DATA = ROOT / "data"                                      # raw data (chỉ đọc)
P2 = HERE.parent / "phase2_diagnostic" / "data"
P3 = HERE.parent / "phase3_dashboard" / "data"
OUT_DATA = HERE / "data"
OUT_CHART = HERE.parent / "output" / "phase4"
OUT_DATA.mkdir(parents=True, exist_ok=True)
OUT_CHART.mkdir(parents=True, exist_ok=True)

PALETTE = ["#185FA5", "#A32D2D", "#3B6D11", "#BA7517", "#534AB7", "#993556"]
plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "grid.linestyle": ":"})

print("=" * 70)
print("ĐỀ XUẤT 1 — FLOOR PRICE CHO PROMOTION")
print("=" * 70)

items = pd.read_csv(DATA / "order_items.csv")
orders = pd.read_csv(DATA / "orders.csv", parse_dates=["order_date"], usecols=["order_id", "order_date", "zip"])
products = pd.read_csv(DATA / "products.csv", usecols=["product_id", "category", "cogs", "price"])

li = (items.merge(orders, on="order_id", how="left")
           .merge(products, on="product_id", how="left"))

li["line_revenue"] = li["quantity"] * li["unit_price"]
li["line_cogs"] = li["quantity"] * li["cogs"]
# Floor price = max(unit_price, cogs) — không bán dưới giá vốn ở bất kỳ dòng nào
li["unit_price_floor"] = np.maximum(li["unit_price"], li["cogs"])
li["line_revenue_floor"] = li["quantity"] * li["unit_price_floor"]

n_total = len(li)
n_below = (li["unit_price"] < li["cogs"]).sum()
print(f"Tổng số dòng order_items (toàn bộ lịch sử): {n_total:,}")
print(f"Số dòng bán dưới giá vốn: {n_below:,} ({n_below/n_total*100:.2f}%)")

rev_actual = li["line_revenue"].sum()
cogs_actual = li["line_cogs"].sum()
margin_actual_pct = (1 - cogs_actual / rev_actual) * 100
margin_actual_vnd = rev_actual - cogs_actual

rev_floor = li["line_revenue_floor"].sum()
cogs_floor = cogs_actual  # COGS catalog không đổi, chỉ giá bán đổi
margin_floor_pct = (1 - cogs_floor / rev_floor) * 100
margin_floor_vnd = rev_floor - cogs_floor

margin_gain_vnd = margin_floor_vnd - margin_actual_vnd
margin_gain_pp = margin_floor_pct - margin_actual_pct

print(f"\nRevenue thực tế (gross, toàn lịch sử): {rev_actual/1e9:.3f} tỷ VND")
print(f"COGS thực tế: {cogs_actual/1e9:.3f} tỷ VND")
print(f"Gross margin thực tế: {margin_actual_pct:.2f}% ({margin_actual_vnd/1e9:.3f} tỷ VND)")
print(f"\nNếu áp floor price = cogs (loại bỏ hoàn toàn bán dưới giá vốn):")
print(f"Revenue giả định: {rev_floor/1e9:.3f} tỷ VND (+{(rev_floor-rev_actual)/1e9:.3f} tỷ)")
print(f"Gross margin giả định: {margin_floor_pct:.2f}% ({margin_floor_vnd/1e9:.3f} tỷ VND)")
print(f"=> Margin tăng thêm: +{margin_gain_pp:.2f} điểm % , +{margin_gain_vnd/1e9:.3f} tỷ VND")

# Theo category
cat_g = li.groupby("category").agg(
    revenue=("line_revenue", "sum"),
    cogs=("line_cogs", "sum"),
    revenue_floor=("line_revenue_floor", "sum"),
).reset_index()
cat_g["margin_pct_actual"] = (1 - cat_g["cogs"] / cat_g["revenue"]) * 100
cat_g["margin_pct_floor"] = (1 - cat_g["cogs"] / cat_g["revenue_floor"]) * 100
cat_g["margin_gain_vnd"] = (cat_g["revenue_floor"] - cat_g["cogs"]) - (cat_g["revenue"] - cat_g["cogs"])
cat_g["margin_gain_pp"] = cat_g["margin_pct_floor"] - cat_g["margin_pct_actual"]
cat_g = cat_g.sort_values("margin_gain_vnd", ascending=False)
print("\nTheo category (tỷ VND margin tăng thêm):")
print(cat_g[["category", "margin_gain_vnd", "margin_gain_pp"]].assign(
    margin_gain_vnd=lambda d: (d["margin_gain_vnd"]/1e9).round(3)).to_string(index=False))

summary1 = pd.DataFrame([{
    "metric": "toàn_shop",
    "revenue_actual_vnd": rev_actual, "cogs_actual_vnd": cogs_actual,
    "margin_pct_actual": margin_actual_pct, "margin_vnd_actual": margin_actual_vnd,
    "revenue_floor_vnd": rev_floor, "margin_pct_floor": margin_floor_pct,
    "margin_vnd_floor": margin_floor_vnd,
    "margin_gain_vnd": margin_gain_vnd, "margin_gain_pp": margin_gain_pp,
    "n_lines_total": n_total, "n_lines_below_cost": n_below,
}])
summary1.to_csv(OUT_DATA / "floor_price_simulation_overall.csv", index=False)
cat_g.to_csv(OUT_DATA / "floor_price_simulation_by_category.csv", index=False)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].bar(["Thực tế", "Floor price"], [margin_actual_pct, margin_floor_pct],
            color=[PALETTE[1], PALETTE[0]], width=0.5)
axes[0].set_ylabel("Gross margin (%)")
axes[0].set_title("Margin toàn shop: thực tế vs floor price")
for i, v in enumerate([margin_actual_pct, margin_floor_pct]):
    axes[0].text(i, v + 0.1, f"{v:.2f}%", ha="center")

axes[1].barh(cat_g["category"], cat_g["margin_gain_vnd"] / 1e9, color=PALETTE[2])
axes[1].set_xlabel("Margin tăng thêm (tỷ VND)")
axes[1].set_title("Margin tăng thêm theo category (floor price)")
fig.tight_layout()
fig.savefig(OUT_CHART / "36_floor_price_margin_before_after.png", dpi=110)
plt.close(fig)

print("\n" + "=" * 70)
print("ĐỀ XUẤT 2 — WIN-BACK THEO RFM SEGMENT")
print("=" * 70)

rfm = pd.read_csv(P3 / "rfm_customer_segments.csv")
churn = pd.read_csv(P3 / "churn_risk_scores.csv")

target_segments = ["Can't Lose Them", "At Risk"]
uplift_scenarios = [0.05, 0.10, 0.15]  # X điểm % tăng tỷ lệ giữ chân (kịch bản, KHÔNG phải dự báo)

rows = []
for seg in target_segments:
    sub = rfm[rfm["segment"] == seg]
    n_cust = len(sub)
    total_monetary = sub["monetary"].sum()
    total_frequency = sub["frequency"].sum()
    avg_monetary = sub["monetary"].mean()
    aov = total_monetary / total_frequency  # giá trị trung bình 1 đơn hàng lịch sử của khách trong segment
    for x in uplift_scenarios:
        n_retained = n_cust * x
        revenue_potential = n_retained * aov
        rows.append({
            "segment": seg, "n_customers": n_cust,
            "avg_monetary_vnd": avg_monetary, "avg_order_value_vnd": aov,
            "uplift_scenario_pct": x * 100,
            "n_customers_retained_est": n_retained,
            "revenue_potential_vnd": revenue_potential,
        })
    print(f"\nSegment: {seg}")
    print(f"  Số khách: {n_cust:,} | Monetary TB/khách: {avg_monetary:,.0f} VND | AOV TB: {aov:,.0f} VND")
    for x in uplift_scenarios:
        n_retained = n_cust * x
        revenue_potential = n_retained * aov
        print(f"  Kịch bản +{x*100:.0f}pp retention -> ~{n_retained:.0f} khách quay lại "
              f"-> +{revenue_potential/1e6:,.1f} triệu VND (1 đơn/khách)")

winback = pd.DataFrame(rows)
winback.to_csv(OUT_DATA / "winback_scenario_by_segment.csv", index=False)

fig, ax = plt.subplots(figsize=(9, 5.5))
width = 0.25
x_pos = np.arange(len(target_segments))
for i, x in enumerate(uplift_scenarios):
    vals = [winback[(winback.segment == s) & (winback.uplift_scenario_pct == x*100)]["revenue_potential_vnd"].values[0] / 1e6
            for s in target_segments]
    ax.bar(x_pos + i*width, vals, width=width, label=f"+{x*100:.0f}pp retention", color=PALETTE[i])
ax.set_xticks(x_pos + width)
ax.set_xticklabels(target_segments)
ax.set_ylabel("Doanh thu tiềm năng (triệu VND)")
ax.set_title("Win-back scenario: doanh thu tiềm năng theo segment (kịch bản, không phải dự báo)")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(OUT_CHART / "37_winback_revenue_scenario.png", dpi=110)
plt.close(fig)

print("\n" + "=" * 70)
print("ĐỀ XUẤT 3 — NHÂN RỘNG PRICING PRACTICE CỦA WEST")
print("=" * 70)

crm = pd.read_csv(P2 / "category_region_margin_controlled.csv")
PRICE_EFFECT_SHARE = 0.60  # ~60% chênh lệch margin West là do giá thật tốt hơn (Phase 2 mục 2.3)

west = crm[crm.region == "West"].set_index("category")["margin_pct"]

rows3 = []
for reg in ["Central", "East"]:
    sub = crm[crm.region == reg].copy()
    sub["west_margin_pct"] = sub["category"].map(west)
    sub["gap_pp"] = sub["west_margin_pct"] - sub["margin_pct"]
    sub["gap_pp_positive"] = sub["gap_pp"].clip(lower=0)  # chỉ tính khi West thực sự tốt hơn
    sub["target_margin_pct"] = sub["margin_pct"] + PRICE_EFFECT_SHARE * sub["gap_pp_positive"]
    sub["cogs_new"] = sub["revenue"] * (1 - sub["target_margin_pct"] / 100)
    sub["margin_gain_vnd"] = sub["cogs"] - sub["cogs_new"]
    rows3.append(sub)

west_repl = pd.concat(rows3, ignore_index=True)
west_repl.to_csv(OUT_DATA / "west_margin_replication_by_category_region.csv", index=False)

total_gain = west_repl["margin_gain_vnd"].sum()
total_revenue_all = crm["revenue"].sum()
total_cogs_all = crm["cogs"].sum()
margin_pct_before = (1 - total_cogs_all / total_revenue_all) * 100
total_cogs_after = total_cogs_all - total_gain
margin_pct_after = (1 - total_cogs_after / total_revenue_all) * 100

print(f"Tổng revenue (Central+East+West, theo category_region_margin_controlled): {total_revenue_all/1e9:.3f} tỷ VND")
print(f"Margin toàn shop hiện tại: {margin_pct_before:.2f}%")
print(f"\nGiả định: Central/East đạt {PRICE_EFFECT_SHARE*100:.0f}% khoảng cách margin so với West trong CÙNG category")
print(west_repl[["region", "category", "margin_pct", "west_margin_pct", "gap_pp", "target_margin_pct", "margin_gain_vnd"]]
      .assign(margin_gain_vnd=lambda d: (d["margin_gain_vnd"]/1e9).round(4)).to_string(index=False))
print(f"\n=> Tổng margin tăng thêm: +{total_gain/1e9:.3f} tỷ VND")
print(f"=> Margin toàn shop mới: {margin_pct_after:.2f}% (+{margin_pct_after-margin_pct_before:.2f} điểm %)")

summary3 = pd.DataFrame([{
    "total_revenue_vnd": total_revenue_all, "margin_pct_before": margin_pct_before,
    "margin_pct_after": margin_pct_after, "margin_gain_pp": margin_pct_after - margin_pct_before,
    "margin_gain_vnd": total_gain, "price_effect_share_assumed": PRICE_EFFECT_SHARE,
}])
summary3.to_csv(OUT_DATA / "west_margin_replication_summary.csv", index=False)

fig, ax = plt.subplots(figsize=(9, 5.5))
cats = west_repl["category"].unique()
x_pos = np.arange(len(cats))
width = 0.35
for i, reg in enumerate(["Central", "East"]):
    vals = [west_repl[(west_repl.category == c) & (west_repl.region == reg)]["margin_gain_vnd"].values[0] / 1e9
            for c in cats]
    ax.bar(x_pos + i*width, vals, width=width, label=reg, color=PALETTE[i])
ax.set_xticks(x_pos + width/2)
ax.set_xticklabels(cats)
ax.set_ylabel("Margin tăng thêm (tỷ VND)")
ax.set_title(f"Margin tăng thêm nếu Central/East đạt {PRICE_EFFECT_SHARE*100:.0f}% gap margin so với West (theo category)")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(OUT_CHART / "38_west_margin_replication_uplift.png", dpi=110)
plt.close(fig)

print("\nHoàn tất Phase 4. CSV: phase4_prescriptive/data/*.csv | Chart: output/phase4/36-38_*.png")
