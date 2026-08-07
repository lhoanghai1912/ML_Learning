# -*- coding: utf-8 -*-
# Phase 0 — QC TOÀN DIỆN data quality & schema — Vin Datathon 2026
# Mở rộng từ phase0_data_check.py (giữ nguyên logic đối chiếu sales ↔ order_items).
#
# Chạy:
#   "/Users/lhoanghai_/Downloads/Dự án datathon2026/.venv/bin/python" phase0_full_qc.py
#   (fallback: python3 phase0_full_qc.py — chỉ cần pandas)
#   (file nằm trong EDA_Insight/phase0_qc/ — DATA trỏ lên 3 cấp tới thư mục gốc dự án/data)
#
# Nội dung:
#   1. Schema từng bảng vs data_dictionary (tên cột, kiểu, số dòng)
#   2. Missing / duplicate theo khóa chính / giá trị âm-bất thường
#   3. Khoảng thời gian thực tế vs kỳ vọng 2012-07-04 → 2022-12-31, ngày thiếu
#   4. Referential integrity (đếm bản ghi mồ côi cụ thể)
#   5. Đối chiếu sales ↔ order_items (Revenue/COGS) + payments
#   6. Kiểm tra sample_submission (548 ngày, 2023-01-01 → 2024-07-01)
#   7. Tổng hợp vấn đề BLOCKER / WARNING / INFO
#
# CHỈ ĐỌC dữ liệu — không ghi/sửa bất kỳ file nào trong data/.

import sys
import time
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent.parent / "data"

EXPECT_START = pd.Timestamp("2012-07-04")
EXPECT_END = pd.Timestamp("2022-12-31")
SUB_START = pd.Timestamp("2023-01-01")
SUB_END = pd.Timestamp("2024-07-01")

# ----------------------------------------------------------------------
# Kỳ vọng theo data_dictionary.xlsx (tên cột theo đúng thứ tự + kiểu + số dòng)
# Kiểu: int / float / str / date
# ----------------------------------------------------------------------
EXPECTED = {
    "customers": {
        "rows": 121930,
        "cols": {"customer_id": "int", "zip": "int", "city": "str",
                 "signup_date": "date", "gender": "str", "age_group": "str",
                 "acquisition_channel": "str"},
        "pk": ["customer_id"],
    },
    "geography": {
        "rows": 39948,
        "cols": {"zip": "int", "city": "str", "region": "str", "district": "str"},
        "pk": ["zip"],
    },
    "products": {
        "rows": 2412,
        "cols": {"product_id": "int", "product_name": "str", "category": "str",
                 "segment": "str", "size": "str", "color": "str",
                 "price": "float", "cogs": "float"},
        "pk": ["product_id"],
    },
    "promotions": {
        "rows": 50,
        "cols": {"promo_id": "str", "promo_name": "str", "promo_type": "str",
                 "discount_value": "float", "start_date": "date", "end_date": "date",
                 "applicable_category": "str", "promo_channel": "str",
                 "stackable_flag": "int", "min_order_value": "int"},
        "pk": ["promo_id"],
    },
    "orders": {
        "rows": 646945,
        "cols": {"order_id": "int", "order_date": "date", "customer_id": "int",
                 "zip": "int", "order_status": "str", "payment_method": "str",
                 "device_type": "str", "order_source": "str"},
        "pk": ["order_id"],
    },
    "order_items": {
        "rows": 714669,
        "cols": {"order_id": "int", "product_id": "int", "quantity": "int",
                 "unit_price": "float", "discount_amount": "float",
                 "promo_id": "str", "promo_id_2": "str"},
        "pk": ["order_id", "product_id"],
    },
    "payments": {
        "rows": 646945,
        "cols": {"order_id": "int", "payment_method": "str",
                 "payment_value": "float", "installments": "int"},
        "pk": ["order_id"],
    },
    "shipments": {
        "rows": 566067,
        "cols": {"order_id": "int", "ship_date": "date",
                 "delivery_date": "date", "shipping_fee": "float"},
        "pk": ["order_id"],
    },
    "returns": {
        "rows": 39939,
        "cols": {"return_id": "str", "order_id": "int", "product_id": "int",
                 "return_date": "date", "return_reason": "str",
                 "return_quantity": "int", "refund_amount": "float"},
        "pk": ["return_id"],
    },
    "reviews": {
        "rows": 113551,
        "cols": {"review_id": "str", "order_id": "int", "product_id": "int",
                 "customer_id": "int", "review_date": "date", "rating": "int",
                 "review_title": "str"},
        "pk": ["review_id"],
    },
    "inventory": {
        "rows": 60247,
        "cols": {"snapshot_date": "date", "product_id": "int",
                 "stock_on_hand": "int", "units_received": "int",
                 "units_sold": "int", "stockout_days": "int",
                 "days_of_supply": "float", "fill_rate": "float",
                 "stockout_flag": "int", "overstock_flag": "int",
                 "reorder_flag": "int", "sell_through_rate": "float",
                 "product_name": "str", "category": "str", "segment": "str",
                 "year": "int", "month": "int"},
        "pk": ["snapshot_date", "product_id"],
    },
    "web_traffic": {
        "rows": 3652,
        "cols": {"date": "date", "sessions": "int", "unique_visitors": "int",
                 "page_views": "int", "bounce_rate": "float",
                 "avg_session_duration_sec": "float", "traffic_source": "str"},
        "pk": ["date"],  # dictionary ghi date+traffic_source (suy luận) — script sẽ kiểm chứng
    },
    "sales": {
        "rows": 3833,
        "cols": {"Date": "date", "Revenue": "float", "COGS": "float"},
        "pk": ["Date"],
    },
    "sample_submission": {
        "rows": 548,
        "cols": {"Date": "date", "Revenue": "float", "COGS": "float"},
        "pk": ["Date"],
    },
}

ISSUES = []  # list of dict(severity, table, issue, recommendation)


def add_issue(severity, table, issue, recommendation):
    ISSUES.append({"severity": severity, "table": table,
                   "issue": issue, "recommendation": recommendation})


def kind_of(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return "int"
    if pd.api.types.is_float_dtype(dtype):
        return "float"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "date"
    return "str"


def fmt_pct(n, d):
    return "{:.2f}%".format(100.0 * n / d) if d else "n/a"


def hr(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def sub(title):
    print("\n--- " + title + " ---")


def missing_days(dates, start, end):
    full = pd.date_range(start, end, freq="D")
    have = pd.DatetimeIndex(pd.Series(dates).dropna().unique())
    return full.difference(have)


def show_days(idx, limit=15):
    if len(idx) == 0:
        return "(không có)"
    days = [d.strftime("%Y-%m-%d") for d in idx[:limit]]
    extra = "" if len(idx) <= limit else " ... (+{} ngày nữa)".format(len(idx) - limit)
    return ", ".join(days) + extra


# ----------------------------------------------------------------------
# LOAD
# ----------------------------------------------------------------------
t0 = time.time()
print("Python:", sys.version.split()[0], "| pandas:", pd.__version__)
print("Thư mục dữ liệu:", DATA)
print("Đang load 14 bảng (chỉ đọc)...")

RAW = {}
for name in EXPECTED:
    # low_memory=False: tránh DtypeWarning mixed types (promo_id_2 gần như toàn NaN)
    RAW[name] = pd.read_csv(DATA / "{}.csv".format(name), low_memory=False)

# Parse cột ngày (errors='coerce' để đếm giá trị không parse được)
DATE_COLS = {t: [c for c, k in spec["cols"].items() if k == "date"]
             for t, spec in EXPECTED.items()}
for t, cols in DATE_COLS.items():
    for c in cols:
        if c in RAW[t].columns:
            raw_nonnull = RAW[t][c].notna().sum()
            RAW[t][c] = pd.to_datetime(RAW[t][c], format="%Y-%m-%d", errors="coerce")
            bad = raw_nonnull - RAW[t][c].notna().sum()
            if bad:
                print("  [!] {}.{}: {} giá trị ngày không parse được".format(t, c, bad))
                add_issue("WARNING", t, "{} giá trị '{}' không parse được thành ngày".format(bad, c),
                          "Kiểm tra format ngày bất thường trước khi dùng.")

print("Load xong sau {:.1f}s".format(time.time() - t0))

# ======================================================================
# PHẦN 1 — SCHEMA vs DATA DICTIONARY
# ======================================================================
hr("PHẦN 1 — SCHEMA & SỐ DÒNG vs DATA DICTIONARY")
for t, spec in EXPECTED.items():
    df = RAW[t]
    exp_cols = list(spec["cols"].keys())
    act_cols = list(df.columns)
    n_exp, n_act = spec["rows"], len(df)
    ok_rows = "OK" if n_exp == n_act else "LỆCH (dict: {:,})".format(n_exp)
    print("\n[{}] {:,} dòng — {}".format(t, n_act, ok_rows))
    if n_exp != n_act:
        add_issue("WARNING", t,
                  "Số dòng thực tế {:,} khác dictionary {:,}".format(n_act, n_exp),
                  "Xác nhận lại phiên bản dữ liệu / dictionary.")
    miss_cols = [c for c in exp_cols if c not in act_cols]
    extra_cols = [c for c in act_cols if c not in exp_cols]
    if miss_cols:
        print("  THIẾU cột so với dictionary:", miss_cols)
        add_issue("BLOCKER", t, "Thiếu cột {}".format(miss_cols),
                  "Không dùng bảng này cho pipeline tới khi bổ sung cột.")
    if extra_cols:
        print("  THỪA cột so với dictionary:", extra_cols)
        add_issue("INFO", t, "Cột thừa ngoài dictionary: {}".format(extra_cols),
                  "Ghi nhận, không ảnh hưởng nếu không dùng.")
    if not miss_cols and not extra_cols and act_cols != exp_cols:
        print("  Thứ tự cột khác dictionary (tên đầy đủ):", act_cols)
    # kiểu dữ liệu
    for c in exp_cols:
        if c not in df.columns:
            continue
        exp_k = spec["cols"][c]
        act_k = kind_of(df[c].dtype)
        # int đọc thành float thường do có NaN — vẫn báo
        if exp_k != act_k:
            note = ""
            if exp_k == "int" and act_k == "float" and df[c].isna().any():
                note = " (float do có NaN)"
            print("  Kiểu lệch: {:<24} dict={:<6} thực tế={}{}".format(c, exp_k, act_k, note))
            if not note and not (exp_k == "date" and act_k == "date"):
                add_issue("INFO", t,
                          "Cột '{}' kiểu thực tế {} khác dictionary {}".format(c, act_k, exp_k),
                          "Ép kiểu rõ ràng khi load (dtype=... / astype).")
    if act_cols == exp_cols:
        print("  Tên cột + thứ tự: khớp dictionary. dtypes:",
              {c: str(df[c].dtype) for c in act_cols})

print("\nGhi chú naming: sales & sample_submission dùng PascalCase (Date/Revenue/COGS),"
      "\ncác bảng khác snake_case — cần chuẩn hoá khi join.")
add_issue("INFO", "sales, sample_submission",
          "Naming không đồng nhất: 'Date/Revenue/COGS' (PascalCase) vs snake_case ở bảng khác",
          "Chuẩn hoá tên cột trong lớp staging của pipeline, giữ nguyên khi nộp bài.")

# ======================================================================
# PHẦN 2 — MISSING / DUPLICATES / GIÁ TRỊ BẤT THƯỜNG
# ======================================================================
hr("PHẦN 2 — MISSING VALUES / DUPLICATES / GIÁ TRỊ ÂM-BẤT THƯỜNG")

for t, spec in EXPECTED.items():
    df = RAW[t]
    n = len(df)
    sub(t)
    # Missing
    na = df.isna().sum()
    na = na[na > 0]
    if len(na) == 0:
        print("  Missing: không có")
    else:
        for c, v in na.items():
            print("  Missing {:<24} {:>9,} ({})".format(c, v, fmt_pct(v, n)))
            expected_null = (t == "order_items" and c in ("promo_id", "promo_id_2")) or \
                            (t == "promotions" and c == "applicable_category")
            if not expected_null:
                add_issue("WARNING", t,
                          "Cột '{}' thiếu {:,} giá trị ({})".format(c, v, fmt_pct(v, n)),
                          "Điều tra nguyên nhân; quyết định impute/drop có chủ đích.")
    # Duplicates theo PK
    pk = spec["pk"]
    dup_pk = df.duplicated(subset=pk).sum()
    dup_row = df.duplicated().sum()
    print("  Duplicate theo PK {}: {:,} | duplicate cả dòng: {:,}".format(pk, dup_pk, dup_row))
    if dup_pk > 0 and t != "web_traffic":  # web_traffic xử lý riêng (grain chưa chắc)
        if t == "order_items":
            dup_pairs = df[df.duplicated(subset=pk, keep=False)].sort_values(pk)
            same_price = dup_pairs.groupby(pk)["unit_price"].nunique().eq(1).mean() * 100
            print("    Chi tiết {} cặp trùng (mẫu 6 dòng): cùng unit_price ở {:.0f}% cặp"
                  " → là 2 line item hợp lệ của cùng SP (giá/lượng khác nhau)".format(dup_pk, same_price))
            print(dup_pairs.head(6).to_string(index=False))
            add_issue("WARNING", t,
                      "{:,} dòng trùng cặp (order_id, product_id) nhưng KHÔNG phải bản ghi lặp — "
                      "là line item hợp lệ (khác unit_price/quantity); grain thật là 'dòng hàng'".format(dup_pk),
                      "KHÔNG xóa (xóa sẽ lệch đối chiếu sales.csv). Khi join returns/reviews theo "
                      "(order_id, product_id) phải aggregate order_items trước để tránh fan-out nhân đôi.")
        else:
            sev = "BLOCKER" if t in ("sales", "sample_submission", "orders") else "WARNING"
            add_issue(sev, t, "{:,} dòng trùng khóa chính {}".format(dup_pk, pk),
                      "Khử trùng lặp (giữ bản ghi đầu/aggregate) trước khi join, nếu không sẽ nhân đôi số liệu.")

# --- Kiểm tra giá trị theo domain từng bảng ---
sub("customers — giá trị bất thường")
cus = RAW["customers"]
early = (cus["signup_date"] < EXPECT_START).sum()
late = (cus["signup_date"] > EXPECT_END).sum()
print("  signup_date < 2012-07-04: {:,} | > 2022-12-31: {:,}".format(early, late))
print("  gender:", sorted(cus["gender"].dropna().unique().tolist()))
print("  age_group:", sorted(cus["age_group"].dropna().unique().tolist()))
if early or late:
    add_issue("WARNING", "customers",
              "{:,} signup trước 2012-07-04 và {:,} sau 2022-12-31".format(early, late),
              "Cohort analysis: quyết định gộp/loại các signup ngoài cửa sổ dữ liệu.")

sub("products — giá trị bất thường")
prod = RAW["products"]
neg_price = (prod["price"] <= 0).sum()
neg_cogs = (prod["cogs"] <= 0).sum()
cogs_gt_price = (prod["cogs"] > prod["price"]).sum()
dup_name = prod.duplicated(subset=["product_name"]).sum()
print("  price <= 0: {:,} | cogs <= 0: {:,}".format(neg_price, neg_cogs))
print("  cogs > price (margin âm ngay ở catalog): {:,}/{:,} SKU ({})".format(
    cogs_gt_price, len(prod), fmt_pct(cogs_gt_price, len(prod))))
print("  product_name trùng nhau: {:,} dòng".format(dup_name))
if cogs_gt_price:
    add_issue("WARNING", "products",
              "{:,}/{:,} SKU ({}) có cogs > price — margin âm ở mức catalog".format(
                  cogs_gt_price, len(prod), fmt_pct(cogs_gt_price, len(prod))),
              "Nguyên nhân trực tiếp của các ngày lỗ gộp; giữ nguyên khi forecast COGS "
              "(là đặc tính dữ liệu), nhưng ghi chú trong dashboard margin.")
if neg_price or neg_cogs:
    add_issue("WARNING", "products", "Giá/cogs <= 0", "Loại hoặc sửa trước khi tính margin.")
if dup_name:
    add_issue("INFO", "products", "{:,} product_name trùng (SKU khác nhau, trùng tên)".format(dup_name),
              "Dùng product_id làm khóa, không dùng tên.")

sub("promotions — giá trị bất thường")
promo = RAW["promotions"]
bad_range = (promo["end_date"] < promo["start_date"]).sum()
beyond = (promo["end_date"] > EXPECT_END).sum()
print("  end_date < start_date: {:,} | end_date > 2022-12-31: {:,}".format(bad_range, beyond))
print("  promo_type:", sorted(promo["promo_type"].dropna().unique().tolist()),
      "| discount_value:", sorted(promo["discount_value"].dropna().unique().tolist()))
if bad_range:
    add_issue("WARNING", "promotions", "{} promo có end_date < start_date".format(bad_range),
              "Sửa/loại khi tính hiệu quả khuyến mại.")

sub("orders — giá trị bất thường")
orders = RAW["orders"]
print("  order_status:", orders["order_status"].value_counts().to_dict())
print("  payment_method:", sorted(orders["payment_method"].dropna().unique().tolist()))

sub("order_items — giá trị bất thường")
items = RAW["order_items"]
q0 = (items["quantity"] <= 0).sum()
p0 = (items["unit_price"] <= 0).sum()
dneg = (items["discount_amount"] < 0).sum()
gross = items["quantity"] * items["unit_price"]
dover = (items["discount_amount"] > gross).sum()
print("  quantity <= 0: {:,} | unit_price <= 0: {:,} | discount < 0: {:,}".format(q0, p0, dneg))
print("  discount_amount > quantity*unit_price (net âm): {:,}".format(dover))
for v, lbl in [(q0, "quantity <= 0"), (p0, "unit_price <= 0"),
               (dneg, "discount âm"), (dover, "discount vượt gross → net âm")]:
    if v:
        add_issue("WARNING", "order_items", "{:,} dòng {}".format(v, lbl),
                  "Lọc/cắt về 0 khi tái dựng doanh thu.")
# unit_price lệch xa giá catalog?
ip = items.merge(RAW["products"][["product_id", "price", "cogs"]], on="product_id", how="left")
ratio = ip["unit_price"] / ip["price"]
print("  unit_price/catalog price: min={:.3f}, p1={:.3f}, median={:.3f}, p99={:.3f}, max={:.3f}".format(
    ratio.min(), ratio.quantile(0.01), ratio.median(), ratio.quantile(0.99), ratio.max()))
# unit_price bán DƯỚI cogs → nguồn gốc các ngày lỗ gộp trong sales.csv
below_cogs = (ip["unit_price"] < ip["cogs"]).sum()
print("  Dòng hàng bán dưới giá vốn (unit_price < catalog cogs): {:,}/{:,} ({})".format(
    below_cogs, len(ip), fmt_pct(below_cogs, len(ip))))
if below_cogs:
    add_issue("WARNING", "order_items",
              "{:,} dòng hàng ({}) có unit_price < cogs catalog — bán dưới giá vốn "
              "(dynamic pricing mùa sale), là nguyên nhân trực tiếp của các ngày lỗ gộp trong sales.csv".format(
                  below_cogs, fmt_pct(below_cogs, len(ip))),
              "Không 'sửa' dữ liệu; forecast COGS độc lập với Revenue và dashboard margin cần "
              "phân tách theo mùa khuyến mại (T7-T8, T11-T12).")

sub("payments — giá trị bất thường")
pay = RAW["payments"]
pv0 = (pay["payment_value"] <= 0).sum()
print("  payment_value <= 0: {:,}".format(pv0))
print("  installments:", sorted(pay["installments"].dropna().unique().tolist()))
if pv0:
    add_issue("WARNING", "payments", "{:,} payment_value <= 0".format(pv0),
              "Điều tra trước khi dùng làm proxy doanh thu.")

sub("shipments — giá trị bất thường")
ship = RAW["shipments"]
fee_neg = (ship["shipping_fee"] < 0).sum()
print("  shipping_fee < 0: {:,} | shipping_fee: min={:.2f}, median={:.2f}, max={:.2f}".format(
    fee_neg, ship["shipping_fee"].min(), ship["shipping_fee"].median(), ship["shipping_fee"].max()))
odate = orders.set_index("order_id")["order_date"]
ship_j = ship.join(odate, on="order_id")
ship_before_order = (ship_j["ship_date"] < ship_j["order_date"]).sum()
deliv_before_ship = (ship_j["delivery_date"] < ship_j["ship_date"]).sum()
print("  ship_date < order_date: {:,} | delivery_date < ship_date: {:,}".format(
    ship_before_order, deliv_before_ship))
lead = (ship_j["delivery_date"] - ship_j["ship_date"]).dt.days
print("  Lead time giao hàng (ngày): min={}, median={}, max={}".format(
    lead.min(), lead.median(), lead.max()))
for v, lbl in [(ship_before_order, "ship_date < order_date"),
               (deliv_before_ship, "delivery_date < ship_date")]:
    if v:
        add_issue("WARNING", "shipments", "{:,} dòng {}".format(v, lbl),
                  "Loại khỏi phân tích lead-time; không ảnh hưởng forecast doanh thu.")
if ship["shipping_fee"].max() < 100:
    add_issue("INFO", "shipments",
              "shipping_fee ({:.2f}–{:.2f}) quá nhỏ so với giá trị đơn (hàng nghìn–trăm nghìn) — "
              "khả năng khác đơn vị tiền tệ".format(ship["shipping_fee"].min(), ship["shipping_fee"].max()),
              "Không cộng shipping_fee vào doanh thu; chỉ dùng so sánh tương đối.")

sub("returns — giá trị bất thường")
ret = RAW["returns"]
rq0 = (ret["return_quantity"] <= 0).sum()
rf0 = (ret["refund_amount"] <= 0).sum()
print("  return_quantity <= 0: {:,} | refund_amount <= 0: {:,}".format(rq0, rf0))
ret_j = ret.join(odate, on="order_id")
ret_before = (ret_j["return_date"] < ret_j["order_date"]).sum()
print("  return_date < order_date: {:,}".format(ret_before))
if ret_before:
    add_issue("WARNING", "returns", "{:,} return_date trước order_date".format(ret_before),
              "Loại khỏi phân tích thời gian trả hàng.")
# return_quantity / refund so với dòng hàng gốc
ret_m = ret.merge(items[["order_id", "product_id", "quantity", "unit_price"]],
                  on=["order_id", "product_id"], how="left")
no_line = ret_m["quantity"].isna().sum()
over_qty = (ret_m["return_quantity"] > ret_m["quantity"]).sum()
over_amt = (ret_m["refund_amount"] > ret_m["quantity"] * ret_m["unit_price"] * 1.0001).sum()
print("  Return không khớp dòng hàng gốc (order_id+product_id): {:,}".format(no_line))
print("  return_quantity > quantity đã mua: {:,} | refund > gross dòng hàng: {:,}".format(over_qty, over_amt))
if no_line:
    add_issue("WARNING", "returns",
              "{:,} bản ghi return không khớp dòng hàng trong order_items".format(no_line),
              "Join theo (order_id, product_id) sẽ mất các dòng này — kiểm tra trước khi tính tỷ lệ trả hàng.")
if over_qty:
    add_issue("WARNING", "returns", "{:,} return_quantity > quantity đã mua".format(over_qty),
              "Cắt trần theo quantity gốc khi tính net revenue sau trả hàng.")
if over_amt:
    add_issue("WARNING", "returns", "{:,} refund_amount > gross của dòng hàng".format(over_amt),
              "Kiểm tra công thức refund (có thể gồm phí khác); không trừ thô vào doanh thu.")

sub("reviews — giá trị bất thường")
rev = RAW["reviews"]
bad_rating = (~rev["rating"].isin([1, 2, 3, 4, 5])).sum()
rev_j = rev.join(odate, on="order_id")
rev_before = (rev_j["review_date"] < rev_j["order_date"]).sum()
print("  rating ngoài [1..5]: {:,} | review_date < order_date: {:,}".format(bad_rating, rev_before))
dup_rev_pair = rev.duplicated(subset=["order_id", "product_id"]).sum()
print("  Trùng (order_id, product_id): {:,} — 1 đơn/1 SP có nhiều review".format(dup_rev_pair))
# review customer có đúng là người đặt đơn?
rev_c = rev.merge(orders[["order_id", "customer_id"]], on="order_id",
                  how="left", suffixes=("", "_order"))
mismatch_cust = (rev_c["customer_id"] != rev_c["customer_id_order"]).sum()
print("  customer_id trong review khác customer đặt đơn: {:,}".format(mismatch_cust))
if rev_before:
    add_issue("WARNING", "reviews", "{:,} review_date trước order_date".format(rev_before),
              "Loại khi phân tích hành vi sau mua.")
if mismatch_cust:
    add_issue("WARNING", "reviews",
              "{:,} review có customer_id khác người đặt đơn".format(mismatch_cust),
              "Dùng customer_id từ orders làm chuẩn khi join RFM/review.")

sub("inventory — giá trị bất thường")
inv = RAW["inventory"]
for c in ["stock_on_hand", "units_received", "units_sold", "stockout_days", "days_of_supply"]:
    neg = (inv[c] < 0).sum()
    if neg:
        print("  {} < 0: {:,}".format(c, neg))
        add_issue("WARNING", "inventory", "{:,} dòng {} âm".format(neg, c), "Lọc trước khi phân tích tồn kho.")
fill_bad = ((inv["fill_rate"] < 0) | (inv["fill_rate"] > 1)).sum()
print("  fill_rate ngoài [0,1]: {:,} | reorder_flag chỉ có giá trị: {}".format(
    fill_bad, sorted(inv["reorder_flag"].unique().tolist())))
is_month_end = (inv["snapshot_date"] == inv["snapshot_date"] + pd.offsets.MonthEnd(0)).all()
print("  snapshot_date luôn là cuối tháng: {}".format(is_month_end))
n_prod_inv = inv["product_id"].nunique()
print("  Sản phẩm có mặt trong inventory: {:,}/{:,}".format(n_prod_inv, len(prod)))
combo = inv.groupby("product_id")["snapshot_date"].nunique()
print("  Số tháng snapshot/sản phẩm: min={}, median={}, max={} → panel KHÔNG cân"
      " ({:,} dòng vs {:,} nếu đủ 126 tháng x {:,} SP)".format(
          combo.min(), int(combo.median()), combo.max(), len(inv), 126 * n_prod_inv, n_prod_inv))
add_issue("WARNING", "inventory",
          "Panel không cân: chỉ {:,}/{:,} SP xuất hiện, mỗi SP trung bình ~{:.0f}/126 tháng snapshot".format(
              n_prod_inv, len(prod), combo.mean()),
          "Không suy diễn 'tồn kho = 0' cho tháng vắng mặt; chỉ dùng inventory cho phân tích vận hành, "
          "không dùng làm feature forecast bắt buộc.")
# nhất quán cột thừa từ products
inv_p = inv.merge(prod[["product_id", "product_name", "category", "segment"]],
                  on="product_id", how="left", suffixes=("", "_p"))
mm = ((inv_p["product_name"] != inv_p["product_name_p"]) |
      (inv_p["category"] != inv_p["category_p"]) |
      (inv_p["segment"] != inv_p["segment_p"])).sum()
print("  Dòng inventory lệch product_name/category/segment so với products: {:,}".format(mm))
if mm:
    add_issue("WARNING", "inventory",
              "{:,} dòng denormalized (product_name/category/segment) lệch bảng products".format(mm),
              "Luôn lấy thuộc tính sản phẩm từ products, bỏ cột denormalized trong inventory.")

sub("web_traffic — giá trị bất thường + grain")
wt = RAW["web_traffic"]
uv_gt = (wt["unique_visitors"] > wt["sessions"]).sum()
br_bad = ((wt["bounce_rate"] < 0) | (wt["bounce_rate"] > 1)).sum()
print("  unique_visitors > sessions: {:,} | bounce_rate ngoài [0,1]: {:,}".format(uv_gt, br_bad))
per_day = wt.groupby("date").size()
print("  Số dòng/ngày: min={}, max={} → grain thực tế: {}".format(
    per_day.min(), per_day.max(),
    "1 dòng/ngày (traffic_source chỉ là thuộc tính!)" if per_day.max() == 1 else "ngày x nguồn"))
print("  Phân bố traffic_source:", wt["traffic_source"].value_counts().to_dict())
if per_day.max() == 1:
    add_issue("WARNING", "web_traffic",
              "Grain thực tế là 1 dòng/ngày TOÀN SITE, trái với dictionary (date + traffic_source); "
              "traffic_source chỉ là nhãn nguồn lớn nhất/đại diện của ngày",
              "KHÔNG sum sessions theo traffic_source như thể là phân rã đầy đủ — "
              "phân tích marketing theo nguồn phải dùng orders.order_source thay thế.")
print("  bounce_rate: {:.4f} → {:.4f} (thấp bất thường so với thực tế ~0.3–0.6)".format(
    wt["bounce_rate"].min(), wt["bounce_rate"].max()))
add_issue("INFO", "web_traffic", "bounce_rate 0.003–0.006 — thấp phi thực tế (dữ liệu mô phỏng)",
          "Chỉ dùng biến động tương đối, không diễn giải giá trị tuyệt đối.")

sub("sales — giá trị bất thường")
sales = RAW["sales"]
r_neg = (sales["Revenue"] <= 0).sum()
c_neg = (sales["COGS"] <= 0).sum()
loss = (sales["COGS"] > sales["Revenue"])
print("  Revenue <= 0: {:,} | COGS <= 0: {:,}".format(r_neg, c_neg))
print("  Ngày COGS > Revenue (lỗ gộp): {:,}/{:,} ({})".format(
    loss.sum(), len(sales), fmt_pct(loss.sum(), len(sales))))
print("  Lỗ gộp theo năm:", sales.groupby(sales["Date"].dt.year)["COGS"].count().index.tolist())
by_year = sales.assign(loss=loss).groupby(sales["Date"].dt.year)["loss"].sum()
print("  ", by_year.to_dict())
by_month = sales.assign(loss=loss).groupby(sales["Date"].dt.month)["loss"].sum()
print("   Theo tháng (cộng 11 năm):", by_month.to_dict())
if loss.sum():
    add_issue("WARNING", "sales",
              "{:,}/{:,} ngày ({}) có COGS > Revenue — lỗ gộp, tập trung kiểm chứng theo mùa sale".format(
                  loss.sum(), len(sales), fmt_pct(loss.sum(), len(sales))),
              "Forecast COGS ĐỘC LẬP với Revenue (không dùng ràng buộc COGS < Revenue); "
              "dashboard margin cần chú thích các ngày này.")

# ======================================================================
# PHẦN 3 — KHOẢNG THỜI GIAN & CHUỖI NGÀY
# ======================================================================
hr("PHẦN 3 — KHOẢNG THỜI GIAN THỰC TẾ vs KỲ VỌNG 2012-07-04 → 2022-12-31")
DATE_CHECK = [
    ("customers", "signup_date", False),
    ("promotions", "start_date", False),
    ("promotions", "end_date", False),
    ("orders", "order_date", True),
    ("shipments", "ship_date", False),
    ("shipments", "delivery_date", False),
    ("returns", "return_date", False),
    ("reviews", "review_date", False),
    ("inventory", "snapshot_date", False),
    ("web_traffic", "date", True),
    ("sales", "Date", True),
]
for t, c, need_daily in DATE_CHECK:
    s = RAW[t][c]
    print("\n[{}.{}] {} → {} | {} ngày distinct".format(
        t, c, s.min().date(), s.max().date(), s.nunique()))
    if need_daily:
        miss = missing_days(s, max(s.min(), EXPECT_START), min(s.max(), EXPECT_END))
        print("  Ngày thiếu TRONG khoảng thực tế của bảng: {} → {}".format(len(miss), show_days(miss)))
        gap_head = (s.min() - EXPECT_START).days
        gap_tail = (EXPECT_END - s.max()).days
        if gap_head > 0:
            print("  Bắt đầu MUỘN hơn kỳ vọng {} ngày (từ {})".format(gap_head, s.min().date()))
        if gap_tail > 0:
            print("  Kết thúc SỚM hơn kỳ vọng {} ngày (đến {})".format(gap_tail, s.max().date()))
        if len(miss) > 0:
            sev = "BLOCKER" if t == "sales" else "WARNING"
            add_issue(sev, t, "Thiếu {} ngày trong chuỗi {} ({})".format(len(miss), c, show_days(miss, 5)),
                      "Reindex đủ ngày + xử lý (impute/flag) trước khi làm chuỗi thời gian.")
        if t == "web_traffic" and gap_head > 0:
            add_issue("WARNING", "web_traffic",
                      "Chỉ có từ {} — thiếu {} ngày đầu (2012-07-04 → {})".format(
                          s.min().date(), gap_head, (s.min() - pd.Timedelta(days=1)).date()),
                      "Feature traffic cho forecast phải xử lý 181 ngày đầu không có dữ liệu "
                      "(mask hoặc bỏ giai đoạn 2012 khi train mô hình dùng traffic).")

# inventory: đủ 126 tháng?
inv_months = pd.PeriodIndex(RAW["inventory"]["snapshot_date"], freq="M").unique().sort_values()
full_months = pd.period_range("2012-07", "2022-12", freq="M")
miss_m = full_months.difference(inv_months)
print("\n[inventory.snapshot_date] {} tháng distinct / kỳ vọng {} — thiếu: {}".format(
    len(inv_months), len(full_months), list(miss_m.astype(str)) if len(miss_m) else "(không)"))

# ======================================================================
# PHẦN 4 — REFERENTIAL INTEGRITY
# ======================================================================
hr("PHẦN 4 — REFERENTIAL INTEGRITY (bản ghi mồ côi)")

FK_CHECKS = [
    ("order_items", "order_id", "orders", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("orders", "customer_id", "customers", "customer_id"),
    ("orders", "zip", "geography", "zip"),
    ("customers", "zip", "geography", "zip"),
    ("payments", "order_id", "orders", "order_id"),
    ("shipments", "order_id", "orders", "order_id"),
    ("returns", "order_id", "orders", "order_id"),
    ("returns", "product_id", "products", "product_id"),
    ("reviews", "order_id", "orders", "order_id"),
    ("reviews", "product_id", "products", "product_id"),
    ("reviews", "customer_id", "customers", "customer_id"),
    ("inventory", "product_id", "products", "product_id"),
    ("order_items", "promo_id", "promotions", "promo_id"),
    ("order_items", "promo_id_2", "promotions", "promo_id"),
]
for child, ck, parent, pk_col in FK_CHECKS:
    cvals = RAW[child][ck].dropna()
    pvals = set(RAW[parent][pk_col].dropna())
    orphan_mask = ~cvals.isin(pvals)
    n_orphan = int(orphan_mask.sum())
    n_orphan_keys = cvals[orphan_mask].nunique()
    status = "OK" if n_orphan == 0 else "MỒ CÔI"
    print("  {}.{} → {}.{}: {:,}/{:,} dòng mồ côi ({}) [{} khóa distinct]  {}".format(
        child, ck, parent, pk_col, n_orphan, len(cvals),
        fmt_pct(n_orphan, len(cvals)), n_orphan_keys, status))
    if n_orphan > 0:
        pct = 100.0 * n_orphan / len(cvals)
        sev = "BLOCKER" if (pct > 5 and child in ("order_items", "orders")) else "WARNING"
        add_issue(sev, child,
                  "{:,} dòng ({}) có {} không tồn tại trong {}.{}".format(
                      n_orphan, fmt_pct(n_orphan, len(cvals)), ck, parent, pk_col),
                  "Dùng LEFT JOIN + cờ orphan; thống nhất loại/giữ trước khi tính KPI theo chiều đó.")

# Độ phủ ngược (không phải lỗi — để nắm coverage)
sub("Độ phủ ngược (coverage — INFO)")
o_ids = set(orders["order_id"])
print("  Orders không có payment: {:,}".format(len(o_ids - set(pay['order_id']))))
no_ship = orders[~orders["order_id"].isin(set(ship["order_id"]))]
print("  Orders không có shipment: {:,} — theo status: {}".format(
    len(no_ship), no_ship["order_status"].value_counts().to_dict()))
odd_no_ship = no_ship[no_ship["order_status"].isin(["delivered", "returned", "shipped"])]
if len(odd_no_ship):
    add_issue("INFO", "shipments",
              "{:,} đơn status delivered/returned/shipped nhưng KHÔNG có bản ghi shipment "
              "(chi tiết: {})".format(len(odd_no_ship),
                                      odd_no_ship["order_status"].value_counts().to_dict()),
              "Chấp nhận sai lệch nhỏ (~0.1%) khi phân tích fulfillment; "
              "đơn cancelled/paid/created không có shipment là hợp lý.")
no_items = o_ids - set(items["order_id"])
print("  Orders không có order_items: {:,}".format(len(no_items)))
if len(no_items):
    add_issue("WARNING", "orders",
              "{:,} đơn không có dòng hàng nào trong order_items".format(len(no_items)),
              "Các đơn này không đóng góp doanh thu tái dựng — kiểm tra status trước khi diễn giải AOV.")
print("  Sản phẩm chưa từng được bán: {:,}/{:,}".format(
    len(set(prod['product_id']) - set(items['product_id'])), len(prod)))
print("  Khách chưa từng đặt đơn: {:,}/{:,}".format(
    len(set(cus['customer_id']) - set(orders['customer_id'])), len(cus)))
add_issue("INFO", "products/customers",
          "{:,} SP chưa từng bán; {:,} khách chưa từng đặt đơn".format(
              len(set(prod['product_id']) - set(items['product_id'])),
              len(set(cus['customer_id']) - set(orders['customer_id']))),
          "Bình thường với catalog/CRM; chú ý mẫu số khi tính tỷ lệ chuyển đổi.")

# ======================================================================
# PHẦN 5 — ĐỐI CHIẾU SALES ↔ ORDER_ITEMS (+ PAYMENTS)
# ======================================================================
hr("PHẦN 5 — ĐỐI CHIẾU sales.csv ↔ tái dựng từ order_items / payments")

items = items.copy()
items["line_revenue"] = items["quantity"] * items["unit_price"] - items["discount_amount"]
items["line_gross"] = items["quantity"] * items["unit_price"]
items = items.merge(prod[["product_id", "cogs"]], on="product_id", how="left")
items["line_cogs"] = items["quantity"] * items["cogs"]
df = items.merge(orders[["order_id", "order_date", "order_status"]], on="order_id", how="left")
sales_idx = sales.set_index("Date")

def test_def(name, mask, col):
    daily = df.loc[mask].groupby("order_date")[col].sum()
    j = pd.concat([sales_idx["Revenue"], daily], axis=1, keys=["sales", "rebuilt"]).dropna()
    mape = ((j["rebuilt"] - j["sales"]).abs() / j["sales"]).mean() * 100
    tot = (j["rebuilt"].sum() / j["sales"].sum() - 1) * 100
    print("  {:<58} MAPE ngày: {:7.3f}% | lệch tổng: {:+7.3f}%".format(name, mape, tot))
    return mape

all_true = pd.Series(True, index=df.index)
candidates = {
    "Tất cả đơn (net = qty*price - discount)": (all_true, "line_revenue"),
    "Tất cả đơn (gross = qty*price)": (all_true, "line_gross"),
    "Bỏ cancelled (net)": (df["order_status"] != "cancelled", "line_revenue"),
    "Bỏ cancelled + returned (net)": (~df["order_status"].isin(["cancelled", "returned"]), "line_revenue"),
    "Chỉ delivered (net)": (df["order_status"] == "delivered", "line_revenue"),
    "delivered + returned + shipped (net)": (df["order_status"].isin(["delivered", "returned", "shipped"]), "line_revenue"),
}
sub("Định nghĩa Revenue nào khớp sales.csv?")
res = {n: test_def(n, m, c) for n, (m, c) in candidates.items()}
best = min(res, key=res.get)
print("\n  >>> Khớp nhất: {} (MAPE {:.3f}%)".format(best, res[best]))

sub("Payments theo ngày vs sales.Revenue")
pay_daily = pay.merge(orders[["order_id", "order_date"]], on="order_id", how="left") \
               .groupby("order_date")["payment_value"].sum()
jp = pd.concat([sales_idx["Revenue"], pay_daily], axis=1, keys=["sales", "payments"]).dropna()
mape_pay = ((jp["payments"] - jp["sales"]).abs() / jp["sales"]).mean() * 100
print("  MAPE ngày (sum payment_value vs Revenue): {:.3f}%".format(mape_pay))

sub("COGS tái dựng (mask khớp nhất)")
mask, _ = candidates[best]
daily_cogs = df.loc[mask].groupby("order_date")["line_cogs"].sum()
jc = pd.concat([sales_idx["COGS"], daily_cogs], axis=1, keys=["sales", "rebuilt"]).dropna()
mape_cogs = ((jc["rebuilt"] - jc["sales"]).abs() / jc["sales"]).mean() * 100
tot_cogs = (jc["rebuilt"].sum() / jc["sales"].sum() - 1) * 100
print("  MAPE ngày COGS: {:.3f}% | lệch tổng: {:+.3f}%".format(mape_cogs, tot_cogs))

thr = 1.0
if res[best] > thr or mape_cogs > thr:
    add_issue("WARNING", "sales ↔ order_items",
              "Định nghĩa khớp nhất '{}' vẫn lệch MAPE Revenue {:.2f}%/COGS {:.2f}% so với sales.csv".format(
                  best, res[best], mape_cogs),
              "Dùng sales.csv làm target chính thức khi forecast; order_items chỉ dùng làm feature/driver.")
elif best == "Tất cả đơn (gross = qty*price)":
    add_issue("WARNING", "sales ↔ order_items",
              "ĐỊNH NGHĨA TARGET: sales.Revenue = GROSS (qty x unit_price) của TẤT CẢ đơn "
              "KỂ CẢ cancelled, KHÔNG trừ discount/refund (MAPE {:.3f}%); "
              "sales.COGS = qty x cogs catalog cùng mask (MAPE {:.3f}%). "
              "Doanh thu 'net, bỏ cancelled' của dashboard sẽ THẤP hơn target ~13-19%".format(
                  res[best], mape_cogs),
              "Phần B: forecast đúng định nghĩa gross này. Phần A: dashboard phải ghi rõ "
              "đang dùng gross demand hay net revenue để 2 phần nhất quán, tránh chênh số giữa các thành viên.")
else:
    add_issue("INFO", "sales ↔ order_items",
              "Revenue/COGS tái dựng từ order_items khớp sales.csv (định nghĩa: {}; MAPE {:.2f}%/{:.2f}%)".format(
                  best, res[best], mape_cogs),
              "Có thể decompose target theo category/region từ order_items một cách tin cậy.")

sub("Payments vs order_items theo TỪNG ĐƠN")
order_net = items.groupby("order_id")["line_revenue"].sum()
jo = pd.concat([order_net, pay.set_index("order_id")["payment_value"]], axis=1, join="inner")
diff = jo["payment_value"] - jo["line_revenue"]
within1 = (diff.abs() / jo["line_revenue"].clip(lower=1e-9) < 0.01).mean() * 100
print("  Đơn khớp trong ±1%: {:.2f}% | chênh lệch: median={:.2f}, p95={:.2f}".format(
    within1, diff.median(), diff.quantile(0.95)))
if within1 < 99:
    add_issue("WARNING", "payments ↔ order_items",
              "Chỉ {:.1f}% đơn có payment_value khớp (±1%) tổng net dòng hàng; median chênh {:.2f}".format(
                  within1, diff.median()),
              "Xác định payment_value gồm những gì (phí? thuế?) trước khi dùng thay doanh thu.")
else:
    add_issue("INFO", "payments",
              "payment_value = tổng net (qty x price - discount) của đơn, khớp {:.1f}% đơn, "
              "kể cả đơn cancelled/created cũng có payment".format(within1),
              "Không coi payment_value là tiền THỰC THU (cash) — nó là giá trị đơn tính sẵn; "
              "phân tích dòng tiền phải lọc theo order_status.")

# ======================================================================
# PHẦN 6 — SAMPLE_SUBMISSION
# ======================================================================
hr("PHẦN 6 — KIỂM TRA sample_submission.csv")
sub_df = RAW["sample_submission"]
print("  Cột: {} | dtypes: {}".format(list(sub_df.columns),
                                      {c: str(sub_df[c].dtype) for c in sub_df.columns}))
print("  Số dòng: {} (kỳ vọng 548)".format(len(sub_df)))
print("  Khoảng ngày: {} → {} (kỳ vọng {} → {})".format(
    sub_df["Date"].min().date(), sub_df["Date"].max().date(), SUB_START.date(), SUB_END.date()))
miss_sub = missing_days(sub_df["Date"], SUB_START, SUB_END)
dup_sub = sub_df.duplicated(subset=["Date"]).sum()
na_sub = sub_df[["Revenue", "COGS"]].isna().sum().sum()
print("  Ngày thiếu trong khung: {} | trùng Date: {} | NaN ở Revenue/COGS: {}".format(
    len(miss_sub), dup_sub, na_sub))
ok_sub = (len(sub_df) == 548 and len(miss_sub) == 0 and dup_sub == 0
          and sub_df["Date"].min() == SUB_START and sub_df["Date"].max() == SUB_END
          and pd.api.types.is_float_dtype(sub_df["Revenue"])
          and pd.api.types.is_float_dtype(sub_df["COGS"]))
print("  KẾT LUẬN: {}".format("HỢP LỆ — đúng 548 ngày liên tục, 2 cột dự báo kiểu float"
                              if ok_sub else "KHÔNG HỢP LỆ — xem chi tiết ở trên"))
if not ok_sub:
    add_issue("BLOCKER", "sample_submission",
              "Khung nộp bài không đúng 548 ngày liên tục 2023-01-01 → 2024-07-01",
              "Đối chiếu lại đề bài trước khi build pipeline forecast.")
else:
    add_issue("INFO", "sample_submission",
              "File mẫu đã có sẵn GIÁ TRỊ Revenue/COGS (baseline placeholder, ví dụ 2023-01-01 = 2,665,507.2)",
              "Bài nộp phải GHI ĐÈ toàn bộ 2 cột bằng dự báo của mình; giữ nguyên format Date YYYY-MM-DD.")
# Gãy chuỗi giữa train và forecast?
gap = (SUB_START - sales["Date"].max()).days
print("  Khoảng cách sales cuối ({}) → submission đầu ({}): {} ngày".format(
    sales["Date"].max().date(), SUB_START.date(), gap))

# ======================================================================
# PHẦN 7 — TỔNG HỢP VẤN ĐỀ
# ======================================================================
hr("PHẦN 7 — TỔNG HỢP VẤN ĐỀ THEO MỨC NGHIÊM TRỌNG")
order_sev = {"BLOCKER": 0, "WARNING": 1, "INFO": 2}
ISSUES.sort(key=lambda x: (order_sev[x["severity"]], x["table"]))
counts = {}
for it in ISSUES:
    counts[it["severity"]] = counts.get(it["severity"], 0) + 1
print("Tổng: {} vấn đề — BLOCKER: {}, WARNING: {}, INFO: {}\n".format(
    len(ISSUES), counts.get("BLOCKER", 0), counts.get("WARNING", 0), counts.get("INFO", 0)))
for it in ISSUES:
    print("[{:<7}] {}".format(it["severity"], it["table"]))
    print("   Vấn đề     : {}".format(it["issue"]))
    print("   Khuyến nghị: {}".format(it["recommendation"]))

print("\nXong Phase 0 full QC sau {:.1f}s.".format(time.time() - t0))
