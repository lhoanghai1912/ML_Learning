# Doanh thu + thói quen khách hàng theo khu vực (region) và độ tuổi (age_group)
# Kết hợp order_items + orders + products + customers + geography.
# Công thức revenue = gross (qty*unit_price, tất cả trạng thái đơn) — khớp sales.csv
# 0.000% sai lệch, đã xác nhận ở phase0_qc/phase0_data_check.py + phase2_diagnostic/revenue_diagnostic.py.
# Output: EDA_Insight/output/phase3/15..28_*.png
# Chạy: python EDA_Insight/phase3_dashboard/customer_demographics.py (sau khi activate .venv)

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

HERE = Path(__file__).resolve().parent           # EDA_Insight/phase3_dashboard/
DATA = HERE.parent.parent / "data"                # dữ liệu gốc: <project root>/data
OUT = HERE.parent / "output" / "phase3"           # chart: EDA_Insight/output/phase3/
OUT.mkdir(parents=True, exist_ok=True)
EXPORT = HERE / "data"                            # data trung gian Phase 3
EXPORT.mkdir(exist_ok=True)

C_REV, C_COGS, C_GRAY, C_ACCENT = "#A32D2D", "#185FA5", "#888780", "#534AB7"
PALETTE = ["#185FA5", "#A32D2D", "#3B6D11", "#BA7517", "#534AB7", "#993556"]
AGE_ORDER = ["18-24", "25-34", "35-44", "45-54", "55+"]

plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "grid.linestyle": ":"})

print("Đang load & join dữ liệu...")
orders = pd.read_csv(DATA / "orders.csv", parse_dates=["order_date"])
items = pd.read_csv(DATA / "order_items.csv")
products = pd.read_csv(DATA / "products.csv", usecols=["product_id", "category", "cogs"])
customers = pd.read_csv(DATA / "customers.csv",
                        usecols=["customer_id", "age_group", "gender", "signup_date"])
geography = pd.read_csv(DATA / "geography.csv", usecols=["zip", "region"])

li = (items
      .merge(orders, on="order_id", how="left")
      .merge(products, on="product_id", how="left")
      .merge(customers, on="customer_id", how="left")
      .merge(geography, on="zip", how="left"))

li["line_revenue"] = li["quantity"] * li["unit_price"]
li["year"] = li["order_date"].dt.year
li = li[li["year"].between(2013, 2022)].copy()
li["age_group"] = pd.Categorical(li["age_group"], categories=AGE_ORDER, ordered=True)

print(f"{len(li):,} dòng sau join | {li['customer_id'].nunique():,} khách "
      f"| age_group null: {li['age_group'].isna().sum()}\n")

# ---------------------------------------------------------------
# 15. REVENUE THEO ĐỘ TUỔI QUA CÁC NĂM
# ---------------------------------------------------------------
age_yr = li.groupby(["year", "age_group"], observed=True)["line_revenue"].sum().unstack()
age_share = age_yr.div(age_yr.sum(axis=1), axis=0) * 100

fig, ax = plt.subplots(figsize=(11, 5.5))
bottom = np.zeros(len(age_share))
for i, ag in enumerate(AGE_ORDER):
    ax.bar(age_share.index, age_share[ag], bottom=bottom, label=ag,
           color=PALETTE[i % len(PALETTE)], width=0.65)
    bottom += age_share[ag].values
ax.set_ylabel("% doanh thu trong năm")
ax.set_title("Tỷ trọng doanh thu theo nhóm tuổi qua các năm")
ax.legend(frameon=False, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.08))
fig.tight_layout(); fig.savefig(OUT / "15_age_share.png", dpi=110); plt.close(fig)

print("=== 15. Tỷ trọng theo tuổi ===")
print(f"  2013: {age_share.loc[2013].round(1).to_dict()}")
print(f"  2022: {age_share.loc[2022].round(1).to_dict()}\n")

# ---------------------------------------------------------------
# 16. HEATMAP REVENUE: ĐỘ TUỔI x KHU VỰC (toàn kỳ 2013-2022)
# ---------------------------------------------------------------
cross = li.pivot_table(index="age_group", columns="region", values="line_revenue",
                       aggfunc="sum", observed=True).reindex(AGE_ORDER) / 1e9

fig, ax = plt.subplots(figsize=(7.5, 6))
im = ax.imshow(cross.values, cmap="Blues", aspect="auto")
ax.set_xticks(range(len(cross.columns)), cross.columns)
ax.set_yticks(range(len(cross.index)), cross.index)
for i in range(cross.shape[0]):
    for j in range(cross.shape[1]):
        v = cross.values[i, j]
        color = "white" if v > cross.values.max() * 0.6 else "#2c2c2a"
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", color=color, fontsize=10)
ax.grid(False)
fig.colorbar(im, label="Revenue (tỷ VND)")
ax.set_title("Doanh thu: độ tuổi × khu vực (tỷ VND, 2013–2022)")
fig.tight_layout(); fig.savefig(OUT / "16_age_region_heatmap.png", dpi=110); plt.close(fig)

print("=== 16. Độ tuổi x khu vực (tỷ VND) ===")
print(cross.round(2).to_string(), "\n")

# ---------------------------------------------------------------
# 17. AOV THEO ĐỘ TUỔI — "thói quen" chi tiêu mỗi đơn
# ---------------------------------------------------------------
order_val = li.groupby(["order_id", "age_group"], observed=True)["line_revenue"].sum().reset_index()
aov_age = order_val.groupby("age_group", observed=True)["line_revenue"].mean().reindex(AGE_ORDER)

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(aov_age.index, aov_age.values / 1e3, color=C_ACCENT, width=0.55)
for i, v in enumerate(aov_age.values / 1e3):
    ax.text(i, v, f"{v:.1f}k", ha="center", va="bottom", fontsize=10)
ax.set_ylabel("Giá trị đơn TB (nghìn VND)")
ax.set_title("AOV theo nhóm tuổi")
fig.tight_layout(); fig.savefig(OUT / "17_aov_by_age.png", dpi=110); plt.close(fig)

print("=== 17. AOV theo tuổi (nghìn VND) ===")
print(f"  {(aov_age/1e3).round(2).to_dict()}\n")

# ---------------------------------------------------------------
# 18. TẦN SUẤT MUA (đơn/khách) THEO ĐỘ TUỔI
# ---------------------------------------------------------------
cust_age = customers.set_index("customer_id")["age_group"]
orders_per_cust = orders.groupby("customer_id").size().rename("n_orders")
freq = orders_per_cust.to_frame().join(cust_age).dropna()
freq_age = freq.groupby("age_group", observed=True)["n_orders"].mean().reindex(AGE_ORDER)
n_cust_age = freq.groupby("age_group", observed=True).size().reindex(AGE_ORDER)

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(freq_age.index, freq_age.values, color=C_COGS, width=0.55)
for i, v in enumerate(freq_age.values):
    ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=10)
ax.set_ylabel("Số đơn TB / khách")
ax.set_title("Tần suất mua theo nhóm tuổi")
fig.tight_layout(); fig.savefig(OUT / "18_order_freq_by_age.png", dpi=110); plt.close(fig)

print("=== 18. Tần suất mua theo tuổi ===")
print(f"  đơn/khách: {freq_age.round(2).to_dict()}")
print(f"  số khách/nhóm: {n_cust_age.to_dict()}\n")

# ---------------------------------------------------------------
# 19. CATEGORY ƯA THÍCH THEO ĐỘ TUỔI (tỷ trọng trong từng nhóm tuổi)
# ---------------------------------------------------------------
cat_age = li.pivot_table(index="age_group", columns="category", values="line_revenue",
                         aggfunc="sum", observed=True).reindex(AGE_ORDER)
cat_age_share = cat_age.div(cat_age.sum(axis=1), axis=0) * 100

fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(cat_age_share.values, cmap="Oranges", aspect="auto")
ax.set_xticks(range(len(cat_age_share.columns)), cat_age_share.columns)
ax.set_yticks(range(len(cat_age_share.index)), cat_age_share.index)
for i in range(cat_age_share.shape[0]):
    for j in range(cat_age_share.shape[1]):
        v = cat_age_share.values[i, j]
        color = "white" if v > 50 else "#2c2c2a"
        ax.text(j, i, f"{v:.1f}%", ha="center", va="center", color=color, fontsize=10)
ax.grid(False)
fig.colorbar(im, label="% doanh thu trong nhóm tuổi")
ax.set_title("Category ưa thích theo nhóm tuổi (% trong từng hàng)")
fig.tight_layout(); fig.savefig(OUT / "19_category_by_age.png", dpi=110); plt.close(fig)

print("=== 19. Category theo tuổi (% mỗi hàng) ===")
print(cat_age_share.round(1).to_string(), "\n")

# ---------------------------------------------------------------
# 20. GIỚI TÍNH — revenue + AOV + tần suất
# ---------------------------------------------------------------
gender_rev = li.groupby("gender")["line_revenue"].sum() / 1e9
order_val_g = li.groupby(["order_id", "gender"])["line_revenue"].sum().reset_index()
aov_gender = order_val_g.groupby("gender")["line_revenue"].mean()
cust_gender = customers.set_index("customer_id")["gender"]
freq_g = orders_per_cust.to_frame().join(cust_gender).dropna().groupby("gender")["n_orders"].mean()

fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
axes[0].bar(gender_rev.index, gender_rev.values, color=PALETTE[:3], width=0.55)
axes[0].set_ylabel("Revenue (tỷ VND)"); axes[0].set_title("Doanh thu theo giới tính")
axes[1].bar(aov_gender.index, aov_gender.values / 1e3, color=PALETTE[:3], width=0.55)
axes[1].set_ylabel("AOV (nghìn VND)"); axes[1].set_title("AOV theo giới tính")
axes[2].bar(freq_g.index, freq_g.values, color=PALETTE[:3], width=0.55)
axes[2].set_ylabel("Đơn TB/khách"); axes[2].set_title("Tần suất mua theo giới tính")
fig.tight_layout(); fig.savefig(OUT / "20_gender_summary.png", dpi=110); plt.close(fig)

print("=== 20. Giới tính ===")
print(f"  Revenue (tỷ): {gender_rev.round(2).to_dict()}")
print(f"  AOV (nghìn): {(aov_gender/1e3).round(2).to_dict()}")
print(f"  Tần suất (đơn/khách): {freq_g.round(2).to_dict()}\n")

# ---------------------------------------------------------------
# 21. REVENUE / KHÁCH (per-capita) — tách ảnh hưởng số lượng khỏi hành vi thật
#     Chart 15/16 là TỔNG, dễ đọc nhầm: khu vực ít khách trông "kém" dù mỗi
#     khách ở đó chi nhiều hơn. Đây là chart đối chiếu bắt buộc phải xem cùng.
# ---------------------------------------------------------------
cust_rev = li.groupby("customer_id")["line_revenue"].sum().rename("total_rev")
cust_dim = customers.set_index("customer_id")[["age_group", "gender"]].join(
    orders[["customer_id", "zip"]].drop_duplicates("customer_id").set_index("customer_id")
).join(geography.set_index("zip")["region"], on="zip")
percap = cust_dim.join(cust_rev).fillna({"total_rev": 0})

percap_region = percap.groupby("region")["total_rev"].mean() / 1e6
percap_age = percap.groupby("age_group", observed=True)["total_rev"].mean().reindex(AGE_ORDER) / 1e6
n_region = percap["region"].value_counts()

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
bars0 = axes[0].bar(percap_region.index, percap_region.values, color=PALETTE[:3], width=0.55)
for i, (reg, v) in enumerate(percap_region.items()):
    axes[0].text(i, v, f"{v:.3f}tr\n({n_region[reg]:,} khách)", ha="center", va="bottom", fontsize=9)
axes[0].set_ylabel("Revenue TB / khách (triệu VND)")
axes[0].set_title("Per-capita theo khu vực — KHÔNG phẳng")

axes[1].bar(percap_age.index, percap_age.values, color=C_GRAY, width=0.55)
for i, v in enumerate(percap_age.values):
    axes[1].text(i, v, f"{v:.3f}tr", ha="center", va="bottom", fontsize=9)
axes[1].set_ylabel("Revenue TB / khách (triệu VND)")
axes[1].set_title("Per-capita theo tuổi — gần như phẳng")
axes[1].set_ylim(0, percap_region.max() * 1.15)
axes[0].set_ylim(0, percap_region.max() * 1.15)
fig.tight_layout(); fig.savefig(OUT / "21_revenue_per_customer.png", dpi=110); plt.close(fig)

print("=== 21. Revenue/khách (triệu VND) — per-capita ===")
print(f"  Theo region: {percap_region.round(4).to_dict()}")
print(f"  Theo tuổi  : {percap_age.round(4).to_dict()}")
print(f"  West cao hơn Central: {(percap_region['West']/percap_region['Central']-1)*100:.1f}%\n")

print(f"Đã lưu 7 chart (15-21) vào {OUT}")

# ================================================================
# RFM SEGMENTATION — Recency / Frequency / Monetary
# Recency  = số ngày từ đơn KHÔNG-cancelled gần nhất tới ngày cuối dữ liệu
# Frequency = số đơn không-cancelled
# Monetary  = tổng payment_value (net thực thu, QC khớp 100% net/đơn — I1)
# trên đơn không-cancelled (loại cancelled, giữ delivered/returned/shipped/paid/created)
# ================================================================
print("Đang tính RFM...")
payments = pd.read_csv(DATA / "payments.csv", usecols=["order_id", "payment_value"])
customers_zip = pd.read_csv(DATA / "customers.csv", usecols=["customer_id", "zip"])

SNAPSHOT_DATE = orders["order_date"].max()          # 2022-12-31 — ngày cuối dữ liệu
SHOP_OPEN = pd.Timestamp("2012-07-04")               # ngày mở bán thực tế (W8)

non_cancel = orders[orders["order_status"] != "cancelled"].merge(
    payments, on="order_id", how="left")

rfm = non_cancel.groupby("customer_id").agg(
    last_order=("order_date", "max"),
    frequency=("order_id", "nunique"),
    monetary=("payment_value", "sum"),
).reset_index()
rfm["recency_days"] = (SNAPSHOT_DATE - rfm["last_order"]).dt.days

n_any_order = orders["customer_id"].nunique()
n_noncancel_order = rfm["customer_id"].nunique()
print(f"  Khách có >=1 đơn (mọi trạng thái): {n_any_order:,}")
print(f"  Khách có >=1 đơn KHÔNG-cancelled (= mẫu RFM): {n_noncancel_order:,} "
      f"(chênh {n_any_order - n_noncancel_order:,} khách chỉ toàn đơn cancelled -> loại khỏi RFM)\n")


def qscore(s, labels):
    ranks = s.rank(method="first")
    return pd.qcut(ranks, 5, labels=labels).astype(int)


rfm["R_score"] = qscore(rfm["recency_days"], [5, 4, 3, 2, 1])   # recency nhỏ = tốt = điểm cao
rfm["F_score"] = qscore(rfm["frequency"], [1, 2, 3, 4, 5])
rfm["M_score"] = qscore(rfm["monetary"], [1, 2, 3, 4, 5])


def rfm_segment(row):
    r, f, m = row["R_score"], row["F_score"], row["M_score"]
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3 and m >= 3:
        return "Loyal Customers"
    if r >= 4 and f <= 2:
        return "New Customers"
    if r == 3 and f <= 2:
        return "Promising"
    if r <= 2 and f >= 4 and m >= 4:
        return "Can't Lose Them"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r <= 2 and f <= 2 and m >= 3:
        return "Hibernating"
    if r <= 2 and f <= 2:
        return "Lost"
    return "Need Attention"


rfm["segment"] = rfm.apply(rfm_segment, axis=1)

seg_summary = (rfm.groupby("segment")
               .agg(n_customers=("customer_id", "count"),
                    total_monetary=("monetary", "sum"),
                    avg_recency=("recency_days", "mean"),
                    avg_frequency=("frequency", "mean"))
               .sort_values("total_monetary", ascending=False))
seg_summary["pct_customers"] = seg_summary["n_customers"] / seg_summary["n_customers"].sum() * 100
seg_summary["pct_monetary"] = seg_summary["total_monetary"] / seg_summary["total_monetary"].sum() * 100

print("=== 22. RFM segment summary ===")
print(seg_summary.round(2).to_string(), "\n")

fig, axes = plt.subplots(1, 2, figsize=(13, 6))
order_idx = seg_summary.index
axes[0].barh(order_idx, seg_summary["n_customers"], color=PALETTE[0])
axes[0].invert_yaxis()
axes[0].set_xlabel("Số khách hàng")
axes[0].set_title("RFM: số khách theo segment")
for i, v in enumerate(seg_summary["n_customers"]):
    axes[0].text(v, i, f" {v:,}", va="center", fontsize=9)

axes[1].barh(order_idx, seg_summary["total_monetary"] / 1e9, color=PALETTE[1])
axes[1].invert_yaxis()
axes[1].set_xlabel("Tổng Monetary (tỷ VND)")
axes[1].set_title("RFM: tổng giá trị theo segment")
for i, v in enumerate(seg_summary["total_monetary"] / 1e9):
    axes[1].text(v, i, f" {v:.2f}", va="center", fontsize=9)
fig.tight_layout(); fig.savefig(OUT / "22_rfm_segment_summary.png", dpi=110); plt.close(fig)

fig, ax = plt.subplots(figsize=(10, 7))
for i, seg in enumerate(order_idx):
    sub = rfm[rfm["segment"] == seg]
    ax.scatter(sub["recency_days"], sub["frequency"],
               s=np.clip(sub["monetary"] / 2000, 3, 120),
               alpha=0.25, color=PALETTE[i % len(PALETTE)], label=seg, edgecolors="none")
ax.set_xlabel("Recency (ngày kể từ đơn gần nhất)")
ax.set_ylabel("Frequency (số đơn)")
ax.set_title("RFM scatter: Recency vs Frequency (kích thước điểm = Monetary)")
ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper right")
fig.tight_layout(); fig.savefig(OUT / "23_rfm_scatter.png", dpi=110); plt.close(fig)


# ================================================================
# COHORT RETENTION — cohort theo THÁNG signup_date
# 238 khách signup trước ngày mở bán (2012-07-04, W8) TÁCH riêng khỏi
# cohort chính (không tính vào heatmap/curve), báo cáo riêng bên dưới.
# ================================================================
print("Đang tính cohort retention...")
customers_full = customers.merge(customers_zip, on="customer_id", how="left")
customers_full["signup_date"] = pd.to_datetime(customers_full["signup_date"])
is_pre_launch = customers_full["signup_date"] < SHOP_OPEN
pre_launch = customers_full[is_pre_launch].copy()
cohort_customers = customers_full[~is_pre_launch].copy()
cohort_customers["cohort_month"] = cohort_customers["signup_date"].dt.to_period("M")

orders_nc = non_cancel[["customer_id", "order_date"]].copy()
orders_nc["order_month"] = orders_nc["order_date"].dt.to_period("M")

merged = orders_nc.merge(cohort_customers[["customer_id", "cohort_month"]],
                          on="customer_id", how="inner")
merged["month_offset"] = ((merged["order_month"].dt.year - merged["cohort_month"].dt.year) * 12
                           + (merged["order_month"].dt.month - merged["cohort_month"].dt.month))
merged = merged[merged["month_offset"] >= 0]

cohort_sizes = cohort_customers.groupby("cohort_month")["customer_id"].nunique()
active = merged.groupby(["cohort_month", "month_offset"])["customer_id"].nunique().unstack()
retention_pct = active.divide(cohort_sizes, axis=0) * 100

MAX_OFFSET = 15
retention_pct_clip = retention_pct.reindex(columns=range(0, MAX_OFFSET + 1))

print(f"  Cohort chính (loại {len(pre_launch)} khách pre-launch): {len(cohort_customers):,} khách, "
      f"{cohort_sizes.shape[0]} cohort tháng ({cohort_sizes.index.min()} -> {cohort_sizes.index.max()})")

n_rows = retention_pct_clip.shape[0]
fig, ax = plt.subplots(figsize=(9, max(6, n_rows * 0.13)))
im = ax.imshow(retention_pct_clip.values, cmap="Blues", aspect="auto", vmin=0, vmax=100)
ax.set_xticks(range(retention_pct_clip.shape[1]), retention_pct_clip.columns)
ax.set_yticks(range(n_rows), [str(p) for p in retention_pct_clip.index])
ax.tick_params(axis="y", labelsize=6)
ax.set_xlabel("Tháng kể từ cohort (month offset)")
ax.set_ylabel("Cohort (tháng signup)")
ax.set_title(f"Cohort retention theo tháng (%) -- {n_rows} cohort, loại {len(pre_launch)} khách pre-launch")
ax.grid(False)
fig.colorbar(im, label="% còn hoạt động", shrink=0.5)
fig.tight_layout(); fig.savefig(OUT / "24_cohort_retention_heatmap.png", dpi=120); plt.close(fig)

max_month = orders_nc["order_month"].max()
offsets = range(0, 13)
avg_retention = {}
for off in offsets:
    eligible = cohort_sizes.index[cohort_sizes.index + off <= max_month]
    denom = cohort_sizes.loc[eligible].sum()
    if off in active.columns:
        numer = active.reindex(index=eligible, columns=[off]).fillna(0).sum().iloc[0]
    else:
        numer = 0
    avg_retention[off] = numer / denom * 100 if denom > 0 else np.nan
avg_retention = pd.Series(avg_retention)

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.plot(avg_retention.index, avg_retention.values, marker="o", color=C_ACCENT)
for m in [1, 3, 6, 12]:
    if m in avg_retention.index:
        ax.annotate(f"M{m}: {avg_retention[m]:.1f}%", (m, avg_retention[m]),
                    textcoords="offset points", xytext=(0, 8), fontsize=9, ha="center")
ax.set_xlabel("Tháng kể từ cohort (month offset)")
ax.set_ylabel("% cohort còn hoạt động (trung bình toàn kỳ, weighted)")
ax.set_title("Đường cong retention trung bình (loại 238 khách pre-launch)")
fig.tight_layout(); fig.savefig(OUT / "25_cohort_retention_curve.png", dpi=110); plt.close(fig)

print("=== 24-25. Cohort retention ===")
milestone = {f"M{k}": round(v, 1) for k, v in avg_retention.items() if k in [1, 3, 6, 12]}
print(f"  Retention mốc (trung bình toàn kỳ): {milestone}")

pre_launch_ids = set(pre_launch["customer_id"])
rfm_pre = rfm[rfm["customer_id"].isin(pre_launch_ids)]
pct_ever_bought = len(rfm_pre) / len(pre_launch) * 100 if len(pre_launch) else np.nan
print(f"  238 khách pre-launch: {len(rfm_pre)} từng có đơn non-cancelled ({pct_ever_bought:.1f}%), "
      f"tổng monetary {rfm_pre['monetary'].sum()/1e6:.1f} triệu VND, "
      f"avg frequency {rfm_pre['frequency'].mean():.2f} đơn/khách "
      f"(so với toàn mẫu RFM: {rfm['frequency'].mean():.2f} đơn/khách)\n")


# ================================================================
# RFM x DEMOGRAPHICS — segment nào tập trung ở vùng nào
# ================================================================
rfm_geo = rfm.merge(customers_zip, on="customer_id", how="left").merge(geography, on="zip", how="left")
seg_region = pd.crosstab(rfm_geo["segment"], rfm_geo["region"])
seg_region_pct = seg_region.div(seg_region.sum(axis=0), axis=1) * 100   # % trong từng vùng

print("=== 26. RFM segment theo region (% khách trong mỗi vùng) ===")
print(seg_region_pct.round(1).to_string(), "\n")

fig, ax = plt.subplots(figsize=(8, 7))
mat = seg_region_pct.reindex(order_idx)
im = ax.imshow(mat.values, cmap="Purples", aspect="auto")
ax.set_xticks(range(mat.shape[1]), mat.columns)
ax.set_yticks(range(mat.shape[0]), mat.index, fontsize=9)
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        v = mat.values[i, j]
        color = "white" if v > np.nanmax(mat.values) * 0.6 else "#2c2c2a"
        ax.text(j, i, f"{v:.1f}%", ha="center", va="center", color=color, fontsize=9)
ax.grid(False)
ax.set_title("RFM segment theo vùng (% khách trong mỗi vùng)")
fig.colorbar(im, label="% trong vùng")
fig.tight_layout(); fig.savefig(OUT / "26_rfm_region_heatmap.png", dpi=110); plt.close(fig)


# ================================================================
# CHURN RISK — rule-based (Recency + xu hướng Frequency 180 ngày gần nhất)
# ================================================================
print("Đang tính churn risk (rule-based)...")
freq_recent = non_cancel[non_cancel["order_date"] > SNAPSHOT_DATE - pd.Timedelta(days=180)]
freq_prior = non_cancel[(non_cancel["order_date"] <= SNAPSHOT_DATE - pd.Timedelta(days=180)) &
                         (non_cancel["order_date"] > SNAPSHOT_DATE - pd.Timedelta(days=360))]
f_recent = freq_recent.groupby("customer_id").size().rename("f_recent")
f_prior = freq_prior.groupby("customer_id").size().rename("f_prior")

risk = rfm.set_index("customer_id")[["recency_days", "frequency", "monetary"]].join(f_recent).join(f_prior).fillna(0)
risk["trend"] = risk["f_recent"] - risk["f_prior"]


def churn_tier(row):
    if row["recency_days"] > 365:
        return "Da roi bo (>365d)"
    if row["recency_days"] > 180 and row["trend"] <= 0:
        return "Rui ro cao"
    if row["recency_days"] > 90 and row["trend"] < 0:
        return "Rui ro trung binh"
    return "An toan"


risk["churn_tier"] = risk.apply(churn_tier, axis=1)
risk_summary = (risk.groupby("churn_tier")
                 .agg(n_customers=("recency_days", "count"), total_monetary=("monetary", "sum"))
                 .sort_values("total_monetary", ascending=False))

print("=== 27. Churn risk (rule-based) ===")
print(risk_summary.round(0).to_string(), "\n")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].bar(risk_summary.index, risk_summary["n_customers"], color=PALETTE[3])
axes[0].set_ylabel("Số khách"); axes[0].set_title("Churn risk: số khách/tier")
axes[0].tick_params(axis="x", rotation=20)
axes[1].bar(risk_summary.index, risk_summary["total_monetary"] / 1e9, color=PALETTE[4])
axes[1].set_ylabel("Tổng Monetary (tỷ VND)"); axes[1].set_title("Churn risk: giá trị/tier")
axes[1].tick_params(axis="x", rotation=20)
fig.tight_layout(); fig.savefig(OUT / "27_churn_risk_summary.png", dpi=110); plt.close(fig)


# ================================================================
# LOGISTIC REGRESSION THỦ CÔNG (numpy, không sklearn/scipy — venv không có)
# Time-split validation: cutoff 2022-06-30, feature tính đến cutoff,
# label = không mua gì trong 6 tháng sau cutoff (tránh leakage).
# ================================================================
print("Đang huấn luyện logistic regression thủ công (numpy, time-split validation)...")
CUTOFF = pd.Timestamp("2022-06-30")
hist = non_cancel[non_cancel["order_date"] <= CUTOFF]
future = non_cancel[non_cancel["order_date"] > CUTOFF]

hist_agg = hist.groupby("customer_id").agg(
    last_order=("order_date", "max"), frequency=("order_id", "nunique"), monetary=("payment_value", "sum"))
hist_agg["recency_days"] = (CUTOFF - hist_agg["last_order"]).dt.days

recent180 = hist[hist["order_date"] > CUTOFF - pd.Timedelta(days=180)].groupby("customer_id").size()
prior180 = hist[(hist["order_date"] <= CUTOFF - pd.Timedelta(days=180)) &
                (hist["order_date"] > CUTOFF - pd.Timedelta(days=360))].groupby("customer_id").size()
hist_agg["trend"] = recent180.reindex(hist_agg.index).fillna(0) - prior180.reindex(hist_agg.index).fillna(0)

future_ids = set(future["customer_id"].unique())
hist_agg["churned"] = (~hist_agg.index.isin(future_ids)).astype(int)

print(f"  Tập validate: {len(hist_agg):,} khách có đơn <= {CUTOFF.date()}, "
      f"churn rate thực tế 6 tháng sau = {hist_agg['churned'].mean()*100:.1f}%")

X_raw = np.column_stack([
    hist_agg["recency_days"].values,
    hist_agg["frequency"].values,
    np.log1p(hist_agg["monetary"].values),
    hist_agg["trend"].values,
]).astype(float)
y = hist_agg["churned"].values.astype(float)

rng = np.random.default_rng(42)
idx = rng.permutation(len(y))
n_train = int(len(y) * 0.8)
train_idx, test_idx = idx[:n_train], idx[n_train:]

mu, sigma = X_raw[train_idx].mean(axis=0), X_raw[train_idx].std(axis=0)
sigma[sigma == 0] = 1
X = (X_raw - mu) / sigma
X_train, X_test = X[train_idx], X[test_idx]
y_train, y_test = y[train_idx], y[test_idx]


def train_logistic(X, y, lr=0.3, n_iter=3000, l2=0.01):
    n, d = X.shape
    w = np.zeros(d); b = 0.0
    for _ in range(n_iter):
        z = X @ w + b
        p = 1 / (1 + np.exp(-z))
        grad_w = X.T @ (p - y) / n + l2 * w / n
        grad_b = np.mean(p - y)
        w -= lr * grad_w
        b -= lr * grad_b
    return w, b


w, b = train_logistic(X_train, y_train)
p_test = 1 / (1 + np.exp(-(X_test @ w + b)))
pred_test = (p_test >= 0.5).astype(int)

tp = ((pred_test == 1) & (y_test == 1)).sum()
fp = ((pred_test == 1) & (y_test == 0)).sum()
fn = ((pred_test == 0) & (y_test == 1)).sum()
tn = ((pred_test == 0) & (y_test == 0)).sum()
accuracy = (tp + tn) / len(y_test)
precision = tp / (tp + fp) if (tp + fp) > 0 else np.nan
recall = tp / (tp + fn) if (tp + fn) > 0 else np.nan
f1 = 2 * precision * recall / (precision + recall) if precision and recall else np.nan

ranks = pd.Series(p_test).rank().values
n_pos = y_test.sum(); n_neg = len(y_test) - n_pos
auc = (ranks[y_test == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg) if n_pos > 0 and n_neg > 0 else np.nan

feat_names = ["recency_days", "frequency", "log(monetary)", "trend_180d"]
print("=== 28. Logistic regression (numpy thủ công, time-split cutoff 2022-06-30) ===")
print(f"  Train {len(train_idx):,} / Test {len(test_idx):,} khách")
print(f"  Accuracy={accuracy:.3f} Precision={precision:.3f} Recall={recall:.3f} F1={f1:.3f} AUC={auc:.3f}")
print(f"  Hệ số chuẩn hoá: {dict(zip(feat_names, np.round(w, 3)))}  bias={b:.3f}\n")

calib_df = pd.DataFrame({"p": p_test, "y": y_test})
calib_df["bin"] = pd.qcut(calib_df["p"], 10, duplicates="drop")
calib = calib_df.groupby("bin", observed=True).agg(mean_pred=("p", "mean"), mean_actual=("y", "mean"), n=("y", "size"))

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].plot(calib["mean_pred"], calib["mean_actual"], marker="o", color=C_ACCENT, label="Model")
axes[0].plot([0, 1], [0, 1], "--", color=C_GRAY, label="Calibration hoàn hảo")
axes[0].set_xlabel("Xác suất churn dự đoán (TB theo decile)")
axes[0].set_ylabel("Tỷ lệ churn thực tế")
axes[0].set_title(f"Calibration curve (AUC={auc:.3f})")
axes[0].legend(frameon=False, fontsize=9)

axes[1].barh(feat_names, w, color=PALETTE[:4])
axes[1].axvline(0, color="#333", linewidth=0.8)
axes[1].set_xlabel("Hệ số chuẩn hoá (dương = tăng nguy cơ churn)")
axes[1].set_title("Feature importance (logistic)")
fig.tight_layout(); fig.savefig(OUT / "28_logistic_validation.png", dpi=110); plt.close(fig)

print(f"Đã lưu thêm 7 chart (22-28) vào {OUT}")


# ================================================================
# EXPORT — data trung gian cho DATA_LINEAGE.md (dashboard_rfm_cohort.md mục 1, 2, 4)
# KHÔNG tính lại số mới — chỉ export đúng các DataFrame đã tính ở trên.
# ================================================================
print("\nĐang export data trung gian Phase 3...")

# 1. RFM customer segments (mục 1 dashboard_rfm_cohort.md) — toàn bộ 88,123 khách mẫu RFM
rfm_export = rfm[["customer_id", "last_order", "recency_days", "frequency", "monetary",
                   "R_score", "F_score", "M_score", "segment"]].copy()
rfm_export.to_csv(EXPORT / "rfm_customer_segments.csv", index=False)
print(f"  Đã lưu {EXPORT / 'rfm_customer_segments.csv'} ({len(rfm_export):,} khách)")

# 2. Cohort retention matrix (mục 2 dashboard_rfm_cohort.md) — 126 cohort x offset 0-15 tháng,
#    đúng ma trận đã dùng vẽ 24_cohort_retention_heatmap.png (retention_pct_clip)
cohort_export = retention_pct_clip.copy()
cohort_export.index = cohort_export.index.astype(str)
cohort_export.columns = [f"month_{c}" for c in cohort_export.columns]
cohort_export = cohort_export.reset_index().rename(columns={"index": "cohort_month"})
cohort_export.to_csv(EXPORT / "cohort_retention_matrix.csv", index=False)
print(f"  Đã lưu {EXPORT / 'cohort_retention_matrix.csv'} ({len(cohort_export)} cohort, "
      f"offset 0-{MAX_OFFSET} tháng, % còn hoạt động)")

# 3. Churn risk scores (mục 4 dashboard_rfm_cohort.md) — tier rule-based (toàn mẫu RFM, 88,123 khách)
#    + xác suất logistic (chỉ tính được cho khách có >=1 đơn non-cancelled <= cutoff 2022-06-30,
#    tức nằm trong hist_agg = 87,589 khách; khách còn lại để NaN ở cột p_churn_logistic — không suy
#    diễn/bịa số cho phần không tính được). p_churn_logistic dùng lại đúng X (đã chuẩn hoá bằng
#    mu/sigma của tập train) và w/b đã huấn luyện ở mục 28 — áp dụng cho TOÀN bộ hist_agg (không chỉ
#    tập test) để có điểm số cho mọi khách; cột used_in_logistic_test_set đánh dấu khách nào thuộc
#    17,518 khách trong tập test dùng để tính Accuracy/Precision/Recall/AUC ở mục 28 (tránh hiểu nhầm
#    p_churn_logistic là "đã out-of-sample" cho toàn bộ 87,589 khách).
p_all = 1 / (1 + np.exp(-(X @ w + b)))
logistic_scores = pd.Series(p_all, index=hist_agg.index, name="p_churn_logistic")
is_test_row = pd.Series(False, index=hist_agg.index, name="used_in_logistic_test_set")
is_test_row.iloc[test_idx] = True

churn_export = (risk[["churn_tier"]]
                .join(logistic_scores)
                .join(is_test_row)
                .reset_index())
churn_export.to_csv(EXPORT / "churn_risk_scores.csv", index=False)
print(f"  Đã lưu {EXPORT / 'churn_risk_scores.csv'} ({len(churn_export):,} khách, "
      f"{logistic_scores.notna().sum():,} có p_churn_logistic)")

print(f"\nHoàn tất export 3 file data trung gian vào {EXPORT}")
