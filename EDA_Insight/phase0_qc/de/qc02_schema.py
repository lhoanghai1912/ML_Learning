# -*- coding: utf-8 -*-
# QC0.2 - Schema & format (@de)
# Moi cot: dtype thuc te vs ky vong, parse date OK?, enum values cho cot phan loai,
# flag cot parse fail / dtype lech.
# CHI DOC - khong sua data.

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA = ROOT / "data"
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)

# kieu ky vong: int / float / str / date
EXPECTED = {
    "customers": {
        "customer_id": "int", "zip": "int", "city": "str",
        "signup_date": "date", "gender": "str", "age_group": "str",
        "acquisition_channel": "str",
    },
    "geography": {
        "zip": "int", "city": "str", "region": "str", "district": "str",
    },
    "products": {
        "product_id": "int", "product_name": "str", "category": "str",
        "segment": "str", "size": "str", "color": "str",
        "price": "float", "cogs": "float",
    },
    "promotions": {
        "promo_id": "str", "promo_name": "str", "promo_type": "str",
        "discount_value": "float", "start_date": "date", "end_date": "date",
        "applicable_category": "str", "promo_channel": "str",
        "stackable_flag": "int", "min_order_value": "int",
    },
    "orders": {
        "order_id": "int", "order_date": "date", "customer_id": "int",
        "zip": "int", "order_status": "str", "payment_method": "str",
        "device_type": "str", "order_source": "str",
    },
    "order_items": {
        "order_id": "int", "product_id": "int", "quantity": "int",
        "unit_price": "float", "discount_amount": "float",
        "promo_id": "str", "promo_id_2": "str",
    },
    "payments": {
        "order_id": "int", "payment_method": "str",
        "payment_value": "float", "installments": "int",
    },
    "shipments": {
        "order_id": "int", "ship_date": "date",
        "delivery_date": "date", "shipping_fee": "float",
    },
    "returns": {
        "return_id": "str", "order_id": "int", "product_id": "int",
        "return_date": "date", "return_reason": "str",
        "return_quantity": "int", "refund_amount": "float",
    },
    "reviews": {
        "review_id": "str", "order_id": "int", "product_id": "int",
        "customer_id": "int", "review_date": "date", "rating": "int",
        "review_title": "str",
    },
    "inventory": {
        "snapshot_date": "date", "product_id": "int",
        "stock_on_hand": "int", "units_received": "int",
        "units_sold": "int", "stockout_days": "int",
        "days_of_supply": "float", "fill_rate": "float",
        "stockout_flag": "int", "overstock_flag": "int",
        "reorder_flag": "int", "sell_through_rate": "float",
        "product_name": "str", "category": "str", "segment": "str",
        "year": "int", "month": "int",
    },
    "web_traffic": {
        "date": "date", "sessions": "int", "unique_visitors": "int",
        "page_views": "int", "bounce_rate": "float",
        "avg_session_duration_sec": "float", "traffic_source": "str",
    },
    "sales": {"Date": "date", "Revenue": "float", "COGS": "float"},
    "sample_submission": {"Date": "date", "Revenue": "float", "COGS": "float"},
}

# cot enum trong diem theo de bai
ENUM_COLS = [
    "order_status", "payment_method", "device_type", "order_source",
    "gender", "age_group", "acquisition_channel", "region", "promo_type",
    "stackable_flag", "stockout_flag", "overstock_flag", "reorder_flag",
]
ENUM_MAX_SHOW = 40  # neu > se ghi "high-cardinality, khong liet ke het"


def kind_of(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return "int"
    if pd.api.types.is_float_dtype(dtype):
        return "float"
    if pd.api.types.is_bool_dtype(dtype):
        return "bool"
    return "str"


rows_out = []
enum_md_lines = ["# QC0.2 — Enum values cac cot phan loai\n",
                  "CHI DOC. Cot khong ton tai o bang do bi bo qua.\n"]

print("QC0.2 Schema & format")
for table, cols_spec in EXPECTED.items():
    path = DATA / "{}.csv".format(table)
    df = pd.read_csv(path, low_memory=False)
    n = len(df)
    print("\n[{}] {:,} dong, {} cot".format(table, n, len(df.columns)))

    extra_cols = [c for c in df.columns if c not in cols_spec]
    missing_cols = [c for c in cols_spec if c not in df.columns]
    if missing_cols:
        print("  THIEU cot vs ky vong:", missing_cols)
    if extra_cols:
        print("  Cot ngoai ky vong (ghi nhan, khong loi):", extra_cols)

    for col, exp_kind in cols_spec.items():
        if col not in df.columns:
            rows_out.append({
                "table": table, "column": col, "dtype_actual": "MISSING",
                "dtype_expected": exp_kind, "parse_ok": "N/A",
                "parse_fail_count": "", "flag": "COT_THIEU",
            })
            continue
        s = df[col]
        if exp_kind == "date":
            raw_nonnull = s.notna().sum()
            parsed = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
            fail = raw_nonnull - parsed.notna().sum()
            parse_ok = "OK" if fail == 0 else "FAIL"
            flag = "" if fail == 0 else "PARSE_FAIL({})".format(fail)
            rows_out.append({
                "table": table, "column": col, "dtype_actual": str(s.dtype),
                "dtype_expected": exp_kind, "parse_ok": parse_ok,
                "parse_fail_count": int(fail), "flag": flag,
            })
            if fail:
                print("  [PARSE FAIL] {}: {} gia tri khong parse duoc thanh date (format ky vong YYYY-MM-DD)".format(col, fail))
            continue

        act_kind = kind_of(s.dtype)
        # int thuong doc thanh float do co NaN -> khong tinh la lech neu du lieu la so nguyen
        dtype_note = ""
        flag = ""
        if exp_kind == "int" and act_kind == "float":
            non_na = s.dropna()
            is_whole = ((non_na % 1) == 0).all() if len(non_na) else True
            if s.isna().any() and is_whole:
                dtype_note = "float do co NaN, gia tri van la so nguyen"
            elif not is_whole:
                dtype_note = "co gia tri thap phan thuc su — LECH KIEU"
                flag = "DTYPE_LECH"
        elif exp_kind != act_kind and not (exp_kind == "str" and act_kind in ("int", "float")):
            dtype_note = "LECH kieu ky vong {} vs thuc te {}".format(exp_kind, act_kind)
            flag = "DTYPE_LECH"
        elif exp_kind == "str" and act_kind in ("int", "float"):
            dtype_note = "cot ky vong str nhung doc ra {} (vd ma dinh danh dang so)".format(act_kind)

        # so ky tu la / dau phan cach nghin cho cot numeric (kiem tra qua ban raw string)
        rows_out.append({
            "table": table, "column": col, "dtype_actual": str(s.dtype),
            "dtype_expected": exp_kind, "parse_ok": "OK",
            "parse_fail_count": 0, "flag": flag if flag else dtype_note,
        })
        if flag:
            print("  [DTYPE LECH] {}: ky vong={} thuc te={} ({})".format(col, exp_kind, act_kind, dtype_note))

    # enum values cho cot trong diem co trong bang nay
    for col in ENUM_COLS:
        if col not in df.columns:
            continue
        vc = df[col].value_counts(dropna=False)
        n_uniq = df[col].nunique(dropna=True)
        n_null = df[col].isna().sum()
        enum_md_lines.append("\n## {}.{}".format(table, col))
        enum_md_lines.append("- distinct: {} | null: {} ({:.3f}%)".format(n_uniq, n_null, 100.0 * n_null / n))
        if n_uniq <= ENUM_MAX_SHOW:
            for val, cnt in vc.items():
                val_disp = "NaN" if pd.isna(val) else val
                enum_md_lines.append("  - `{}`: {:,} ({:.2f}%)".format(val_disp, cnt, 100.0 * cnt / n))
        else:
            enum_md_lines.append("  - high-cardinality ({} gia tri), khong liet ke het. Top 10:".format(n_uniq))
            for val, cnt in vc.head(10).items():
                enum_md_lines.append("    - `{}`: {:,}".format(val, cnt))
        print("  enum {:<22} distinct={:<4} null={}".format(col, n_uniq, n_null))

schema_df = pd.DataFrame(rows_out, columns=[
    "table", "column", "dtype_actual", "dtype_expected", "parse_ok",
    "parse_fail_count", "flag",
])
schema_out = OUT / "qc02_schema.csv"
schema_df.to_csv(schema_out, index=False)

enums_out = OUT / "qc02_enums.md"
enums_out.write_text("\n".join(enum_md_lines) + "\n", encoding="utf-8")

# tom tat flag
flags = schema_df[schema_df["flag"].astype(str).str.len() > 0]
flags = flags[flags["flag"].str.contains("PARSE_FAIL|DTYPE_LECH|COT_THIEU", regex=True, na=False)]
print("\n--- TOM TAT: cot bi flag (parse fail / dtype lech / cot thieu) ---")
if len(flags) == 0:
    print("(khong co)")
else:
    print(flags[["table", "column", "flag"]].to_string(index=False))

print("\nGhi:", schema_out)
print("Ghi:", enums_out)
