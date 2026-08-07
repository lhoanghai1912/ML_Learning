"""M5 — test_schema.py

1. `datathon.schema.validate_schema` bắt sai dtype/enum (synthetic — biết trước đáp án đúng).
2. Smoke 10 chiều DQ (`datathon.quality`) trên `data/sample`, gọi HÀM THẬT (không mock):
   grain/key unique (chiều 3), RI orphan (chiều 4), completeness ngưỡng (chiều 5),
   dup (chiều 8), reconciliation lệch (chiều 9).

Mọi assertion đối chiếu số liệu ĐÃ CHẠY THẬT (không giả định/không `assert True`).
"""

from __future__ import annotations

import pandas as pd
import pytest

from datathon import ingestion, quality
from datathon import schema as schema_mod

# ---------------------------------------------------------------------------
# 1. schema.validate_schema — dtype / enum
# ---------------------------------------------------------------------------


def test_validate_schema_passes_on_clean_row() -> None:
    df = pd.DataFrame(
        [
            {
                "customer_id": 1,
                "zip": 15201,
                "city": "Hai Phong",
                "signup_date": "2021-12-30",
                "gender": "Female",
                "age_group": "35-44",
                "acquisition_channel": "social_media",
            }
        ]
    )
    result = schema_mod.validate_schema(df, "customers")
    assert result.ok is True
    assert result.missing_columns == []
    assert result.dtype_mismatch == {}
    assert result.enum_violations == {}
    assert result.n_invalid_rows == 0
    assert bool(result.row_valid_mask.iloc[0]) is True


def test_validate_schema_catches_bad_dtype() -> None:
    """customer_id không ép được sang int -> dtype_mismatch, dòng bị đánh invalid."""
    df = pd.DataFrame(
        [
            {  # dòng sạch
                "customer_id": 1, "zip": 15201, "city": "Hai Phong",
                "signup_date": "2021-12-30", "gender": "Female",
                "age_group": "35-44", "acquisition_channel": "social_media",
            },
            {  # dòng lỗi dtype: customer_id không phải số
                "customer_id": "not_a_number", "zip": 15201, "city": "Hai Phong",
                "signup_date": "2021-12-30", "gender": "Female",
                "age_group": "35-44", "acquisition_channel": "social_media",
            },
        ]
    )
    result = schema_mod.validate_schema(df, "customers")
    assert result.dtype_mismatch == {"customer_id": 1}
    assert result.n_invalid_rows == 1
    assert list(result.row_valid_mask) == [True, False]


def test_validate_schema_catches_bad_enum() -> None:
    """gender ngoài enum {'Female','Male','Non-binary'} -> enum_violations, dòng invalid."""
    df = pd.DataFrame(
        [
            {
                "customer_id": 1, "zip": 15201, "city": "Hai Phong",
                "signup_date": "2021-12-30", "gender": "alien",
                "age_group": "35-44", "acquisition_channel": "social_media",
            }
        ]
    )
    result = schema_mod.validate_schema(df, "customers")
    assert result.enum_violations == {"gender": 1}
    assert result.n_invalid_rows == 1
    assert bool(result.row_valid_mask.iloc[0]) is False


def test_validate_schema_catches_missing_column() -> None:
    df = pd.DataFrame([{"customer_id": 1, "zip": 15201}])  # thiếu 5 cột bắt buộc
    result = schema_mod.validate_schema(df, "customers")
    assert result.ok is False
    assert set(result.missing_columns) == {
        "city", "signup_date", "gender", "age_group", "acquisition_channel",
    }


def test_validate_schema_flags_unexpected_column_but_allows_metadata() -> None:
    df = pd.DataFrame(
        [
            {
                "customer_id": 1, "zip": 15201, "city": "Hai Phong",
                "signup_date": "2021-12-30", "gender": "Female",
                "age_group": "35-44", "acquisition_channel": "social_media",
                "totally_unknown_col": "x",
                "_ingested_at": "2026-01-01T00:00:00+00:00",  # metadata -> KHÔNG flag
            }
        ]
    )
    result = schema_mod.validate_schema(df, "customers")
    assert result.unexpected_columns == ["totally_unknown_col"]


def test_validate_schema_unknown_table_raises() -> None:
    with pytest.raises(KeyError):
        schema_mod.get_schema("khong_ton_tai")


# ---------------------------------------------------------------------------
# 2. Smoke 10 chiều DQ trên data/sample — quality.py (M4a), hàm thật
# ---------------------------------------------------------------------------


def test_dq_inventory_dimension1_row_count_matches_actual_file(
    all_sample_tables: dict[str, pd.DataFrame], sample_dir
) -> None:
    """Chiều 1 — 14/14 bảng có mặt, row_count khớp CSV thật đọc độc lập."""
    results = quality.inventory(all_sample_tables)
    tables_seen = {r.table for r in results}
    assert tables_seen == set(schema_mod.ALL_TABLES)
    row_count_by_table = {
        r.table: r.value for r in results if r.metric == "row_count"
    }
    for table, df in all_sample_tables.items():
        raw_len = len(pd.read_csv(sample_dir / f"{table}.csv"))
        assert row_count_by_table[table] == raw_len == len(df)
    assert all(r.status == "PASS" for r in results), [r for r in results if r.status != "PASS"]


def test_dq_keys_dimension3_grain_unique_tables_pass(
    all_sample_tables: dict[str, pd.DataFrame],
) -> None:
    """Chiều 3 — bảng grain_unique=True (customers/geography/products/orders) không trùng khóa
    trên sample thật (sample được sinh referential-consistent, xem tests/tools/generate_sample.py)."""
    for table in ("customers", "geography", "products", "orders"):
        results = quality.keys(all_sample_tables[table], table)
        assert len(results) == 1
        assert results[0].status == "PASS", results[0].detail
        assert results[0].value == 0


def test_dq_keys_dimension3_order_items_natural_key_not_unique_but_surrogate_is() -> None:
    """Chiều 3 — order_items: grain tự nhiên (order_id, product_id) CÓ THỂ trùng (2 dòng hàng
    hợp lệ khác giá/số lượng, đúng thiết kế — KHÔNG phải lỗi), nhưng surrogate line id PHẢI
    unique. Test synthetic — biết trước có đúng 1 cặp trùng để kiểm cả 2 nhánh."""
    df = pd.DataFrame(
        [
            {"order_id": 1, "product_id": 100, "quantity": 1, "unit_price": 10.0,
             "discount_amount": 0.0, "promo_id": None, "promo_id_2": None},
            {"order_id": 1, "product_id": 100, "quantity": 2, "unit_price": 9.0,
             "discount_amount": 0.0, "promo_id": None, "promo_id_2": None},  # trùng grain tự nhiên
            {"order_id": 2, "product_id": 200, "quantity": 1, "unit_price": 5.0,
             "discount_amount": 0.0, "promo_id": None, "promo_id_2": None},
        ]
    )
    df = ingestion.add_metadata_columns(df, source_file="synthetic", batch_id="t")
    df[schema_mod.ORDER_ITEMS_SURROGATE_KEY] = ingestion.build_order_items_line_id(df)

    results = quality.keys(df, "order_items")
    by_metric = {r.metric.split(":")[0]: r for r in results}
    assert by_metric["dup_grain_natural"].value == 1  # 1 cặp trùng, PASS (không phải lỗi)
    assert by_metric["dup_grain_natural"].status == "PASS"
    assert by_metric["dup_surrogate"].value == 0
    assert by_metric["dup_surrogate"].status == "PASS"

    # Bug injection thật: nếu surrogate cũng trùng (giả lập lỗi build key) -> phải FAIL.
    df_bad = df.copy()
    df_bad.loc[1, schema_mod.ORDER_ITEMS_SURROGATE_KEY] = df_bad.loc[0, schema_mod.ORDER_ITEMS_SURROGATE_KEY]
    results_bad = quality.keys(df_bad, "order_items")
    by_metric_bad = {r.metric.split(":")[0]: r for r in results_bad}
    assert by_metric_bad["dup_surrogate"].value == 1
    assert by_metric_bad["dup_surrogate"].status == "FAIL"


def test_dq_check_ri_dimension4_detects_real_orphan_in_sample(
    all_sample_tables: dict[str, pd.DataFrame],
) -> None:
    """Chiều 4 — RI orphan THẬT trên sample (không synthetic): `inventory` được sinh bằng
    head-N ĐỘC LẬP (cố ý, xem generate_sample.py) nên có product_id KHÔNG nằm trong
    `products` sample (đã lọc theo order_items/returns/reviews) -> phải bắt được orphan > 0.
    Ngược lại orders->customers/geography (được sinh referential-consistent) phải sạch (0 orphan)."""
    results = quality.check_ri(all_sample_tables)
    by_key = {(r.table, r.metric): r for r in results}

    inv_orphan = by_key[("inventory", "ri_orphan:product_id->products.product_id")]
    assert inv_orphan.value > 0
    assert inv_orphan.status == "FAIL"

    orders_cust = by_key[("orders", "ri_orphan:customer_id->customers.customer_id")]
    assert orders_cust.value == 0
    assert orders_cust.status == "PASS"

    orders_geo = by_key[("orders", "ri_orphan:zip->geography.zip")]
    assert orders_geo.value == 0
    assert orders_geo.status == "PASS"

    items_orders = by_key[("order_items", "ri_orphan:order_id->orders.order_id")]
    assert items_orders.value == 0
    assert items_orders.status == "PASS"


def test_dq_check_ri_dimension4_synthetic_orphan_detected() -> None:
    """Bug injection trực tiếp qua `quality.check_ri()` THẬT: 1 order_id ở `order_items`
    KHÔNG tồn tại ở bảng cha `orders` -> phải bắt đúng 1 orphan, status FAIL."""
    order_items = pd.DataFrame({
        "order_id": [1, 2, 999999], "product_id": [10, 10, 10],
    })
    orders = pd.DataFrame({"order_id": [1, 2]})
    tables = {"order_items": order_items, "orders": orders}

    results = quality.check_ri(tables)
    r = next(
        x for x in results
        if x.table == "order_items" and x.metric == "ri_orphan:order_id->orders.order_id"
    )
    assert r.value == 1
    assert r.status == "FAIL"
    assert r.severity == "QUARANTINE"


def test_dq_completeness_dimension5_clean_sample_passes(
    all_sample_tables: dict[str, pd.DataFrame],
) -> None:
    """Chiều 5 — sales sample không null ở cột bắt buộc -> toàn bộ PASS (ngưỡng 0%)."""
    results = quality.completeness(all_sample_tables["sales"], "sales")
    assert len(results) == 3
    assert all(r.status == "PASS" for r in results)
    assert all(r.value == 0.0 for r in results)


def test_dq_completeness_dimension5_warns_over_threshold() -> None:
    """Bug injection: 2/4 dòng null ở cột bắt buộc Revenue -> null_rate=0.5 > ngưỡng 0 -> WARN
    (severity dimension 5 = WARN theo SEVERITY_BY_DIMENSION, KHÔNG fail hard)."""
    df = pd.DataFrame({
        "Date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"]),
        "Revenue": [100.0, None, 300.0, None],
        "COGS": [50.0, 60.0, 70.0, 80.0],
    })
    results = quality.completeness(df, "sales")
    by_col = {r.metric: r for r in results}
    rev = by_col["null_rate:Revenue"]
    assert rev.value == pytest.approx(0.5)
    assert rev.status == "WARN"
    assert rev.severity == "WARN"
    cogs = by_col["null_rate:COGS"]
    assert cogs.status == "PASS"


def test_dq_dup_outlier_dimension8_clean_sample_passes(
    all_sample_tables: dict[str, pd.DataFrame],
) -> None:
    """Chiều 8 — sales sample không trùng full-row."""
    results = quality.dup_outlier(all_sample_tables["sales"], "sales")
    dup_result = next(r for r in results if r.metric == "duplicate_full_row")
    assert dup_result.value == 0
    assert dup_result.status == "PASS"


def test_dq_dup_outlier_dimension8_detects_injected_duplicate(
    all_sample_tables: dict[str, pd.DataFrame],
) -> None:
    """Bug injection thật: nhân đôi 1 dòng có sẵn -> duplicate_full_row phải >0 và FAIL."""
    sales = all_sample_tables["sales"]
    dup_df = pd.concat([sales, sales.iloc[[0]]], ignore_index=True)
    results = quality.dup_outlier(dup_df, "sales")
    dup_result = next(r for r in results if r.metric == "duplicate_full_row")
    assert dup_result.value == 1
    assert dup_result.status == "FAIL"
    assert dup_result.severity == "QUARANTINE"


def test_dq_reconcile_dimension9_detects_real_mismatch_on_sample(
    all_sample_tables: dict[str, pd.DataFrame],
) -> None:
    """Chiều 9 — reconcile sales<->order_items trên `data/sample`: sample chỉ chứa 2000 đơn
    hàng đầu (~vài ngày) trong khi `sales` sample trải 300 ngày -> lệch ngày cắt cụt tạo MAPE
    THẬT lớn hơn ngưỡng 1% -> phải FAIL (không phải giả lập — số liệu tính từ sample commit).
    """
    results = quality.reconcile(all_sample_tables)
    revenue_result = next(r for r in results if r.metric.startswith("revenue_mape:"))
    assert revenue_result.table == "sales<->order_items"
    assert revenue_result.threshold == 1.0
    assert revenue_result.value > 1.0
    assert revenue_result.status == "FAIL"
    assert revenue_result.severity == "HARD_FAIL"


def test_dq_reconcile_dimension9_passes_when_perfectly_matched() -> None:
    """Positive control: dựng sales/order_items/orders/products/payments khớp tuyệt đối
    (net_all_orders) -> MAPE phải ~0% -> PASS. Chứng minh reconcile() KHÔNG luôn FAIL bừa."""
    orders = pd.DataFrame({
        "order_id": [1, 2],
        "order_date": pd.to_datetime(["2020-01-01", "2020-01-01"]),
        "order_status": ["delivered", "delivered"],
    })
    order_items = pd.DataFrame({
        "order_id": [1, 2],
        "product_id": [10, 10],
        "quantity": [1, 1],
        "unit_price": [100.0, 50.0],
        "discount_amount": [0.0, 0.0],
    })
    products = pd.DataFrame({"product_id": [10], "cogs": [40.0]})
    sales = pd.DataFrame({
        "Date": pd.to_datetime(["2020-01-01"]),
        "Revenue": [150.0],  # == 100 + 50 (net_all_orders, discount=0)
        "COGS": [80.0],      # == (1*40) + (1*40)
    })
    payments = pd.DataFrame({"order_id": [1, 2], "payment_value": [100.0, 50.0]})

    tables = {
        "sales": sales, "order_items": order_items, "orders": orders,
        "products": products, "payments": payments,
    }
    results = quality.reconcile(tables)
    revenue_result = next(r for r in results if r.metric.startswith("revenue_mape:"))
    assert revenue_result.value == pytest.approx(0.0, abs=1e-6)
    assert revenue_result.status == "PASS"
