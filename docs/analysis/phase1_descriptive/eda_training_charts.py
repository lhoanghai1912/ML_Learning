# EDA dữ liệu training (sales.csv) — 6 biểu đồ quan sát trước khi build model
# Output: EDA_Insight/output/phase1/*.png
# Chạy: python EDA_Insight/phase1_descriptive/eda_training_charts.py (sau khi activate .venv)

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lunardate import LunarDate
from pathlib import Path

HERE = Path(__file__).resolve().parent           # EDA_Insight/phase1_descriptive/
OUT = HERE.parent / "output" / "phase1"          # EDA_Insight/output/phase1/
OUT.mkdir(parents=True, exist_ok=True)

C_REV = "#A32D2D"   # đỏ — Revenue, cố định mọi chart
C_COGS = "#185FA5"  # xanh — COGS
C_GRAY = "#888780"  # xám — nền/ngữ cảnh
C_ACCENT = "#534AB7"

plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "grid.linestyle": ":"})

sales = pd.read_csv(HERE.parent.parent / "data" / "sales.csv", parse_dates=["Date"])
sales["margin_pct"] = (sales["Revenue"] - sales["COGS"]) / sales["Revenue"] * 100

# ---------------------------------------------------------------
# 1. TOÀN CHUỖI: daily + MA30 + mốc break 2019
# ---------------------------------------------------------------
sales["MA30"] = sales["Revenue"].rolling(30).mean()
fig, ax = plt.subplots(figsize=(13, 4.5))
ax.plot(sales["Date"], sales["Revenue"] / 1e6, color=C_GRAY, alpha=0.35, lw=0.5)
ax.plot(sales["Date"], sales["MA30"] / 1e6, color=C_REV, lw=2, label="Revenue MA30")
ax.axvline(pd.Timestamp("2019-01-01"), color=C_GRAY, ls="--", lw=1.5)
ax.annotate("break 2019", xy=(pd.Timestamp("2019-01-15"), 16), color=C_GRAY)
ax.set_ylabel("Triệu VND/ngày")
ax.set_title("Revenue theo ngày 2012–2022 (xám = từng ngày, đỏ = trung bình trượt 30 ngày)")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(OUT / "01_daily_ma30.png", dpi=110); plt.close(fig)

# ---------------------------------------------------------------
# 2. THÁNG: revenue + margin% (2 panel, KHÔNG dual-axis)
# ---------------------------------------------------------------
monthly = sales.set_index("Date").resample("ME")[["Revenue", "COGS"]].sum()
monthly["margin_pct"] = (monthly["Revenue"] - monthly["COGS"]) / monthly["Revenue"] * 100
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 6.5), sharex=True)
ax1.plot(monthly.index, monthly["Revenue"] / 1e9, color=C_REV, lw=1.8)
ax1.set_ylabel("Revenue (tỷ/tháng)")
ax1.set_title("Doanh thu tháng và biên lãi gộp — gai margin âm rơi vào mùa sale")
ax2.fill_between(monthly.index, monthly["margin_pct"], 0,
                 where=monthly["margin_pct"] >= 0, color=C_COGS, alpha=0.45)
ax2.fill_between(monthly.index, monthly["margin_pct"], 0,
                 where=monthly["margin_pct"] < 0, color=C_REV, alpha=0.55)
ax2.axhline(0, color=C_GRAY, lw=1)
ax2.set_ylabel("Gross margin %")
fig.tight_layout(); fig.savefig(OUT / "02_monthly_margin.png", dpi=110); plt.close(fig)

# ---------------------------------------------------------------
# 3. HEATMAP năm × tháng (sequential 1 hue)
# ---------------------------------------------------------------
hm = sales.pivot_table(index=sales["Date"].dt.year, columns=sales["Date"].dt.month,
                       values="Revenue", aggfunc="sum") / 1e9
fig, ax = plt.subplots(figsize=(11, 5))
im = ax.imshow(hm.values, cmap="Blues", aspect="auto")
ax.set_xticks(range(12), [f"T{m}" for m in range(1, 13)])
ax.set_yticks(range(len(hm.index)), hm.index)
ax.grid(False)
fig.colorbar(im, label="Revenue (tỷ)")
ax.set_title("Heatmap doanh thu năm × tháng — đỉnh giữa năm, đáy cuối năm, tối dần từ 2019")
fig.tight_layout(); fig.savefig(OUT / "03_heatmap_year_month.png", dpi=110); plt.close(fig)

# ---------------------------------------------------------------
# 4. MÙA VỤ CÓ BỀN VỮNG? — tỷ trọng từng tháng trong năm, 10 năm chồng lên nhau
# ---------------------------------------------------------------
yr = sales[sales["Date"].dt.year.between(2013, 2022)].copy()
yr["year"], yr["month"] = yr["Date"].dt.year, yr["Date"].dt.month
share = (yr.groupby(["year", "month"])["Revenue"].sum()
         / yr.groupby("year")["Revenue"].sum()).unstack() * 100
fig, ax = plt.subplots(figsize=(11, 5))
for y in share.index:
    ax.plot(share.columns, share.loc[y], color=C_GRAY, alpha=0.35, lw=1)
ax.plot(share.columns, share.mean(), color=C_ACCENT, lw=2.5, marker="o",
        label="Trung bình 10 năm")
ax.set_xticks(range(1, 13), [f"T{m}" for m in range(1, 13)])
ax.set_ylabel("% doanh thu cả năm")
ax.set_title("Hình dạng mùa vụ 10 năm chồng lên nhau (xám = từng năm) — có lặp lại không?")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(OUT / "04_seasonal_shape.png", dpi=110); plt.close(fig)

# ---------------------------------------------------------------
# 5. THỨ TRONG TUẦN
# ---------------------------------------------------------------
dow = sales.groupby(sales["Date"].dt.dayofweek)["Revenue"].mean() / 1e6
labels = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(labels, dow.values, color=C_COGS, width=0.62)
for i, v in enumerate(dow.values):
    ax.text(i, v + 0.05, f"{v:.2f}", ha="center", fontsize=10, color="#444441")
ax.set_ylabel("Revenue TB (triệu/ngày)")
ax.set_title("Doanh thu trung bình theo thứ trong tuần")
fig.tight_layout(); fig.savefig(OUT / "05_day_of_week.png", dpi=110); plt.close(fig)

# ---------------------------------------------------------------
# 6. HIỆU ỨNG TẾT ±30 NGÀY
# ---------------------------------------------------------------
tet_dates = [pd.Timestamp(LunarDate(y, 1, 1).to_solar_date()) for y in range(2013, 2023)]
frames = []
for t in tet_dates:
    w = sales[(sales["Date"] >= t - pd.Timedelta(days=30)) &
              (sales["Date"] <= t + pd.Timedelta(days=30))].copy()
    w["offset"] = (w["Date"] - t).dt.days
    frames.append(w)
avg = pd.concat(frames).groupby("offset")[["Revenue", "COGS"]].mean() / 1e6
fig, ax = plt.subplots(figsize=(12, 4.5))
ax.axvspan(-7, 0, color="#FAC775", alpha=0.25, label="Tuần trước Tết")
ax.axvspan(0, 7, color="#B5D4F4", alpha=0.35, label="Tuần sau Tết")
ax.axvline(0, color="#BA7517", ls="--", lw=1.6)
ax.plot(avg.index, avg["Revenue"], "o-", color=C_REV, ms=3.5, lw=1.6, label="Revenue")
ax.plot(avg.index, avg["COGS"], "o-", color=C_COGS, ms=3.5, lw=1.6, label="COGS")
ax.set_xlabel("Số ngày cách Tết (0 = mồng 1)")
ax.set_ylabel("TB (triệu VND)")
ax.set_title("Hiệu ứng Tết: trung bình 10 cái Tết 2013–2022")
ax.legend(frameon=False, ncol=2)
fig.tight_layout(); fig.savefig(OUT / "06_tet_effect.png", dpi=110); plt.close(fig)

# ---------------------------------------------------------------
# SỐ LIỆU KÈM PHÂN TÍCH
# ---------------------------------------------------------------
print("=== Số liệu đọc kèm chart ===")
print(f"Corr(Revenue, COGS) theo ngày: {sales['Revenue'].corr(sales['COGS']):.4f}")
print(f"Tỷ lệ COGS/Revenue: TB {(sales['COGS']/sales['Revenue']).mean():.3f}, "
      f"độ lệch chuẩn {(sales['COGS']/sales['Revenue']).std():.3f}")
print(f"\nDoW (triệu): {dict(zip(labels, dow.round(2)))}")
print(f"Chênh cao nhất vs thấp nhất trong tuần: "
      f"{(dow.max()/dow.min()-1)*100:.1f}%")
print("\nTỷ trọng tháng (TB % ± std qua 10 năm):")
for m in range(1, 13):
    print(f"  T{m:<2}: {share[m].mean():5.2f}% ± {share[m].std():.2f}")
top5 = sales.nlargest(5, "Revenue")[["Date", "Revenue"]]
print("\nTop 5 ngày doanh thu cao nhất:")
for _, r in top5.iterrows():
    print(f"  {r['Date'].date()}  {r['Revenue']/1e6:6.1f} triệu")
print(f"\nĐã lưu 6 chart vào {OUT}")
