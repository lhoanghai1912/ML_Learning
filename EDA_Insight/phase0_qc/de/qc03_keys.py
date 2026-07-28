# -*- coding: utf-8 -*-
# QC0.3 - Grain & candidate key (@de)
# Moi bang: grain 1 cau + test COUNT(*) == COUNT(DISTINCT key).
# Trong tam: geography.zip unique?; order_items grain (trung order_id+product_id?);
# payments 1:1 orders; inventory snapshot_date+product_id.
# CHI DOC - khong sua data.

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA = ROOT / "data"
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)


def load(name):
    return pd.read_csv(DATA / "{}.csv".format(name), low_memory=False)


def key_test(df, key_cols):
    n = len(df)
    n_distinct = df.drop_duplicates(subset=key_cols).shape[0]
    violations = n - n_distinct
    return n, n_distinct, violations


rows_out = []


def add(table, grain, key, n, n_distinct, violations, example_note=""):
    passed = "PASS" if violations == 0 else "FAIL"
    rows_out.append({
        "table": table, "grain": grain, "key": key,
        "rows": n, "distinct_key": n_distinct,
        "violations": violations, "pass": passed, "note": example_note,
    })
    print("[{:<18}] key={:<28} rows={:>9,} distinct={:>9,} violations={:>7,} -> {}".format(
        table, key, n, n_distinct, violations, passed))
    if example_note:
        print("    note: {}".format(example_note))


print("QC0.3 Grain & candidate key\n")

# --- customers: grain 1 dong/khach hang ---
cus = load("customers")
n, nd, v = key_test(cus, ["customer_id"])
add("customers", "1 dong / 1 khach hang (customer_id)", "customer_id", n, nd, v)

# --- products: grain 1 dong/SKU ---
prod = load("products")
n, nd, v = key_test(prod, ["product_id"])
add("products", "1 dong / 1 SKU (product_id)", "product_id", n, nd, v)

# --- geography: zip unique hay zip+district? ---
geo = load("geography")
n, nd_zip, v_zip = key_test(geo, ["zip"])
n2, nd_zd, v_zd = key_test(geo, ["zip", "district"])
note_geo = "zip DUY NHAT ({} dong = {} zip distinct). zip+district cung PASS nhung thua vi zip da unique.".format(n, nd_zip) \
    if v_zip == 0 else \
    "zip KHONG unique ({} dong, {} zip distinct, {} vi pham). Grain thuc te la zip+district ({} vi pham).".format(
        n, nd_zip, v_zip, v_zd)
add("geography", "1 dong / 1 zip (candidate)", "zip", n, nd_zip, v_zip, note_geo)
add("geography", "kiem tra thay the: 1 dong / (zip, district)", "zip+district", n2, nd_zd, v_zd)

# --- orders: grain 1 dong/don hang ---
orders = load("orders")
n, nd, v = key_test(orders, ["order_id"])
add("orders", "1 dong / 1 don hang (order_id)", "order_id", n, nd, v)

# --- payments: grain 1 dong/don hang, ky vong 1:1 voi orders ---
pay = load("payments")
n, nd, v = key_test(pay, ["order_id"])
order_ids = set(orders["order_id"])
pay_ids = set(pay["order_id"])
extra_pay = pay_ids - order_ids
missing_pay = order_ids - pay_ids
note_pay = "So sanh voi orders: {} order_id trong payments nhung KHONG co trong orders (RI); {} don orders KHONG co payment.".format(
    len(extra_pay), len(missing_pay))
add("payments", "1 dong / 1 don hang, ky vong 1:1 voi orders (order_id)", "order_id", n, nd, v, note_pay)
print("    1:1 voi orders: {}".format(
    "PASS (COUNT bang nhau va key unique 2 phia)" if (len(orders) == len(pay) and v == 0 and not extra_pay and not missing_pay)
    else "XEM CHI TIET RI (QC0.4)"))

# --- order_items: grain that su la gi? ---
items = load("order_items")
n, nd_pair, v_pair = key_test(items, ["order_id", "product_id"])
dup_mask = items.duplicated(subset=["order_id", "product_id"], keep=False)
dup_rows = items[dup_mask].sort_values(["order_id", "product_id"])
if v_pair > 0:
    # kiem tra cac dong trung (order_id,product_id) co phai IDENTICAL toan bo cot khong,
    # hay khac o unit_price/quantity/promo (=> line item hop le, khac nhau)
    full_dup = items.duplicated(keep=False)
    n_full_dup_rows = int(full_dup.sum())
    diffs = dup_rows.groupby(["order_id", "product_id"]).agg(
        n_unit_price=("unit_price", "nunique"),
        n_quantity=("quantity", "nunique"),
    )
    all_identical_groups = ((diffs["n_unit_price"] == 1) & (diffs["n_quantity"] == 1)).sum()
    total_dup_groups = len(diffs)
    example = dup_rows.head(4).to_dict("records")
    grain_desc = ("(order_id,product_id) KHONG phai key duy nhat: {} dong vi pham tren {} nhom trung. "
                  "{} bang dong TRUNG TOAN BO cac cot (full-row duplicate); "
                  "{} nhom (order_id,product_id) trung nhung KHAC unit_price/quantity "
                  "(la 2 line item hop le cung SKU, VD mua nhieu lan / gia khac nhau trong cung don). "
                  "GRAIN THAT: 1 dong = 1 dong hang (line item), KHONG phai 1 dong = 1 SKU/don. "
                  "Vi du 2 dong dau trung key: {}").format(
        v_pair, total_dup_groups, n_full_dup_rows,
        total_dup_groups - all_identical_groups, example[:2])
else:
    grain_desc = "(order_id,product_id) la key duy nhat, khong co dong trung."
add("order_items", "1 dong = 1 dong hang (line item) trong 1 don, co the >1 dong/SKU/don", "order_id+product_id",
    n, nd_pair, v_pair, grain_desc)
print("    full-row duplicate (moi cot giong het): {:,}".format(int(items.duplicated(keep=False).sum())))

# --- shipments: grain 1 dong/don ---
ship = load("shipments")
n, nd, v = key_test(ship, ["order_id"])
add("shipments", "1 dong / 1 don da ship (order_id, subset cua orders)", "order_id", n, nd, v,
    "orders - shipments = {:,} don chua co ban ghi shipment (co the chua ship/huy).".format(len(orders) - len(ship)))

# --- reviews: grain 1 dong/review ---
rev = load("reviews")
n, nd, v = key_test(rev, ["review_id"])
n2, nd2, v2 = key_test(rev, ["order_id", "product_id"])
add("reviews", "1 dong / 1 review (review_id)", "review_id", n, nd, v)
add("reviews", "kiem tra thay the: 1 review / (order_id,product_id)?", "order_id+product_id", n2, nd2, v2,
    "{} vi pham -> {} don+SKU co nhieu review (vd review lai)".format(
        v2, "PASS neu 0" if v2 == 0 else "co"))

# --- returns: grain 1 dong/return ---
ret = load("returns")
n, nd, v = key_test(ret, ["return_id"])
add("returns", "1 dong / 1 yeu cau tra hang (return_id)", "return_id", n, nd, v)
n2, nd2, v2 = key_test(ret, ["order_id", "product_id"])
add("returns", "kiem tra thay the: 1 return / (order_id,product_id)?", "order_id+product_id", n2, nd2, v2,
    "{} vi pham -> {} nhom (order_id,product_id) co nhieu lan return".format(v2, v2))

# --- promotions: grain 1 dong/promo ---
promo = load("promotions")
n, nd, v = key_test(promo, ["promo_id"])
add("promotions", "1 dong / 1 chuong trinh khuyen mai (promo_id)", "promo_id", n, nd, v)

# --- inventory: grain snapshot_date+product_id ---
inv = load("inventory")
n, nd, v = key_test(inv, ["snapshot_date", "product_id"])
add("inventory", "1 dong / 1 (thang snapshot, SKU) -- panel thang x san pham", "snapshot_date+product_id", n, nd, v,
    "Panel KHONG can: {} SKU distinct trong inventory / {} SKU trong products.".format(
        inv["product_id"].nunique(), prod["product_id"].nunique()))

# --- web_traffic: grain 1 dong/ngay (traffic_source la thuoc tinh, khong phai chieu khoa) ---
wt = load("web_traffic")
n, nd_date, v_date = key_test(wt, ["date"])
per_day = wt.groupby("date").size()
add("web_traffic", "1 dong / 1 ngay TOAN SITE (traffic_source la nhan/thuoc tinh, KHONG phai chieu phan rach)",
    "date", n, nd_date, v_date,
    "So dong/ngay: min={}, max={}. Neu max=1 => date la key that su, du du lieu co cot traffic_source.".format(
        per_day.min(), per_day.max()))

# --- sales / sample_submission: grain 1 dong/ngay ---
sales = load("sales")
n, nd, v = key_test(sales, ["Date"])
add("sales", "1 dong / 1 ngay (Date)", "Date", n, nd, v)

sub_df = load("sample_submission")
n, nd, v = key_test(sub_df, ["Date"])
add("sample_submission", "1 dong / 1 ngay du bao (Date)", "Date", n, nd, v)

# ------------------------------------------------------------------
out_df = pd.DataFrame(rows_out, columns=[
    "table", "grain", "key", "rows", "distinct_key", "violations", "pass", "note",
])
out_path = OUT / "qc03_keys.csv"
out_df.to_csv(out_path, index=False)

fails = out_df[out_df["pass"] == "FAIL"]
print("\n--- TOM TAT: key test FAIL ---")
if len(fails) == 0:
    print("(khong co — tat ca key ung vien pass, tru cac dong 'kiem tra thay the' co the FAIL co chu dich)")
else:
    print(fails[["table", "key", "violations", "note"]].to_string(index=False))

print("\nGhi:", out_path)
