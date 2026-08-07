"""Schema contract cho 14 bảng raw — dtype, cột bắt buộc, enum, grain/candidate key.

Nguồn: `docs/analysis/phase0_qc/phase0_full_qc.py` (dict `EXPECTED` + `FK_CHECKS`), đã verify
qua QC thủ công (phase0_qc_report.md) + đối chiếu lại trực tiếp trên `data/raw/*.csv`
(xem giá trị enum, số dòng trùng khóa). KHÔNG bịa dtype/enum mới — chỉ port lại.

Vai trò:
    - Contract dùng bởi `quality.validate_schema()` (M4a), dbt model contract (M3a — port riêng
      trong dbt_datathon, không đụng ở đây), và job ingest Iceberg (M2) để quyết định quarantine.
    - Schema evolution CHỈ theo allowlist `allowed_extra_columns`. Mặc định mọi bảng cho phép thêm
      5 cột metadata ingest (`METADATA_COLUMNS`). Muốn thêm cột NGHIỆP VỤ mới phải sửa
      `TableSchema.columns` tường minh trong file này — KHÔNG tự động merge schema lạ.

Đặc thù đã biết (giữ nguyên, không "sửa" dữ liệu):
    - `order_items`: (order_id, product_id) KHÔNG unique (714669 dòng, 16 cặp trùng khóa) — đây
      là 2 dòng hàng hợp lệ của cùng SP trong 1 đơn (khác unit_price/quantity), KHÔNG phải lỗi.
      Grain thật = "dòng hàng". `grain_unique=False`; cần surrogate `order_item_line_id`
      (xem `datathon.ingestion.build_order_items_line_id`) làm khóa MERGE/unique thật sự.
    - `order_items.promo_id`, `order_items.promo_id_2`, `promotions.applicable_category`:
      NULL hợp lệ theo thiết kế (không phải thiếu dữ liệu) — loại khỏi `required`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

# 5 cột metadata ingestion (M2 job Iceberg / M4a ingestion.py) — luôn được phép có mặt,
# KHÔNG tính là "cột thừa" khi validate.
METADATA_COLUMNS: tuple[str, ...] = (
    "_ingested_at",
    "_source_file",
    "_source_row_number",
    "_checksum",
    "_batch_id",
)

# surrogate key riêng cho order_items — cũng luôn cho phép có mặt (do ingestion.py sinh ra).
ORDER_ITEMS_SURROGATE_KEY = "order_item_line_id"


@dataclass(frozen=True)
class TableSchema:
    """Contract 1 bảng raw.

    columns: cột -> kiểu kỳ vọng, 1 trong {"int", "float", "str", "date"}.
    required: cột KHÔNG được null (subset `columns`, xem docstring module — 2 ngoại lệ đã loại).
    grain: cột định nghĩa "1 dòng nghiệp vụ" (candidate key theo data dictionary).
    grain_unique: True nếu `grain` thật sự unique trên data thật (đã verify). False -> cần
        surrogate key khác để MERGE/unique (xem `order_items`).
    enums: cột -> tập giá trị hợp lệ (đã lấy từ data thật, không suy đoán).
    date_cols: cột kiểu date — suy tự động từ `columns` nếu không set tay.
    allowed_extra_columns: allowlist evolution — cột được phép xuất hiện thêm ngoài `columns`.
    """

    name: str
    columns: dict[str, str]
    required: tuple[str, ...]
    grain: tuple[str, ...]
    grain_unique: bool = True
    enums: dict[str, tuple[str, ...]] = field(default_factory=dict)
    date_cols: tuple[str, ...] = field(default_factory=tuple)
    allowed_extra_columns: tuple[str, ...] = METADATA_COLUMNS

    def __post_init__(self) -> None:
        if not self.date_cols:
            object.__setattr__(
                self,
                "date_cols",
                tuple(c for c, k in self.columns.items() if k == "date"),
            )


SCHEMAS: dict[str, TableSchema] = {
    "customers": TableSchema(
        name="customers",
        columns={
            "customer_id": "int",
            "zip": "int",
            "city": "str",
            "signup_date": "date",
            "gender": "str",
            "age_group": "str",
            "acquisition_channel": "str",
        },
        required=(
            "customer_id", "zip", "city", "signup_date",
            "gender", "age_group", "acquisition_channel",
        ),
        grain=("customer_id",),
        enums={
            "gender": ("Female", "Male", "Non-binary"),
            "age_group": ("18-24", "25-34", "35-44", "45-54", "55+"),
            "acquisition_channel": (
                "direct", "email_campaign", "organic_search",
                "paid_search", "referral", "social_media",
            ),
        },
    ),
    "geography": TableSchema(
        name="geography",
        columns={"zip": "int", "city": "str", "region": "str", "district": "str"},
        required=("zip", "city", "region", "district"),
        grain=("zip",),
    ),
    "products": TableSchema(
        name="products",
        columns={
            "product_id": "int", "product_name": "str", "category": "str",
            "segment": "str", "size": "str", "color": "str",
            "price": "float", "cogs": "float",
        },
        required=(
            "product_id", "product_name", "category", "segment",
            "size", "color", "price", "cogs",
        ),
        grain=("product_id",),
        enums={
            "category": ("Casual", "GenZ", "Outdoor", "Streetwear"),
            "segment": (
                "Activewear", "All-weather", "Balanced", "Everyday",
                "Performance", "Premium", "Standard", "Trendy",
            ),
        },
    ),
    "promotions": TableSchema(
        name="promotions",
        columns={
            "promo_id": "str", "promo_name": "str", "promo_type": "str",
            "discount_value": "float", "start_date": "date", "end_date": "date",
            "applicable_category": "str", "promo_channel": "str",
            "stackable_flag": "int", "min_order_value": "int",
        },
        required=(
            "promo_id", "promo_name", "promo_type", "discount_value",
            "start_date", "end_date", "promo_channel",
            "stackable_flag", "min_order_value",
        ),  # applicable_category NULL hợp lệ (40 dòng) — loại khỏi required
        grain=("promo_id",),
        enums={
            "promo_type": ("fixed", "percentage"),
            "promo_channel": ("all_channels", "email", "in_store", "online", "social_media"),
        },
    ),
    "orders": TableSchema(
        name="orders",
        columns={
            "order_id": "int", "order_date": "date", "customer_id": "int",
            "zip": "int", "order_status": "str", "payment_method": "str",
            "device_type": "str", "order_source": "str",
        },
        required=(
            "order_id", "order_date", "customer_id", "zip", "order_status",
            "payment_method", "device_type", "order_source",
        ),
        grain=("order_id",),
        enums={
            "order_status": (
                "cancelled", "created", "delivered", "paid", "returned", "shipped",
            ),
            "payment_method": ("apple_pay", "bank_transfer", "cod", "credit_card", "paypal"),
            "device_type": ("desktop", "mobile", "tablet"),
            "order_source": (
                "direct", "email_campaign", "organic_search",
                "paid_search", "referral", "social_media",
            ),
        },
    ),
    "order_items": TableSchema(
        name="order_items",
        columns={
            "order_id": "int", "product_id": "int", "quantity": "int",
            "unit_price": "float", "discount_amount": "float",
            "promo_id": "str", "promo_id_2": "str",
        },
        required=("order_id", "product_id", "quantity", "unit_price", "discount_amount"),
        grain=("order_id", "product_id"),
        grain_unique=False,  # 16 cặp trùng — dòng hàng hợp lệ, xem docstring module
        allowed_extra_columns=METADATA_COLUMNS + (ORDER_ITEMS_SURROGATE_KEY,),
    ),
    "payments": TableSchema(
        name="payments",
        columns={
            "order_id": "int", "payment_method": "str",
            "payment_value": "float", "installments": "int",
        },
        required=("order_id", "payment_method", "payment_value", "installments"),
        grain=("order_id",),
        enums={
            "payment_method": ("apple_pay", "bank_transfer", "cod", "credit_card", "paypal"),
        },
    ),
    "shipments": TableSchema(
        name="shipments",
        columns={
            "order_id": "int", "ship_date": "date",
            "delivery_date": "date", "shipping_fee": "float",
        },
        required=("order_id", "ship_date", "delivery_date", "shipping_fee"),
        grain=("order_id",),
    ),
    "returns": TableSchema(
        name="returns",
        columns={
            "return_id": "str", "order_id": "int", "product_id": "int",
            "return_date": "date", "return_reason": "str",
            "return_quantity": "int", "refund_amount": "float",
        },
        required=(
            "return_id", "order_id", "product_id", "return_date",
            "return_reason", "return_quantity", "refund_amount",
        ),
        grain=("return_id",),
        enums={
            "return_reason": (
                "changed_mind", "defective", "late_delivery",
                "not_as_described", "wrong_size",
            ),
        },
    ),
    "reviews": TableSchema(
        name="reviews",
        columns={
            "review_id": "str", "order_id": "int", "product_id": "int",
            "customer_id": "int", "review_date": "date", "rating": "int",
            "review_title": "str",
        },
        required=(
            "review_id", "order_id", "product_id", "customer_id",
            "review_date", "rating", "review_title",
        ),
        grain=("review_id",),
        enums={"rating": ("1", "2", "3", "4", "5")},  # so sánh dạng str sau ép kiểu ở validate
    ),
    "inventory": TableSchema(
        name="inventory",
        columns={
            "snapshot_date": "date", "product_id": "int",
            "stock_on_hand": "int", "units_received": "int",
            "units_sold": "int", "stockout_days": "int",
            "days_of_supply": "float", "fill_rate": "float",
            "stockout_flag": "int", "overstock_flag": "int",
            "reorder_flag": "int", "sell_through_rate": "float",
            "product_name": "str", "category": "str", "segment": "str",
            "year": "int", "month": "int",
        },
        required=(
            "snapshot_date", "product_id", "stock_on_hand", "units_received",
            "units_sold", "stockout_days", "days_of_supply", "fill_rate",
            "stockout_flag", "overstock_flag", "reorder_flag",
            "sell_through_rate", "product_name", "category", "segment",
            "year", "month",
        ),
        grain=("snapshot_date", "product_id"),
        enums={
            "stockout_flag": ("0", "1"),
            "overstock_flag": ("0", "1"),
            "reorder_flag": ("0", "1"),
        },
    ),
    "web_traffic": TableSchema(
        name="web_traffic",
        columns={
            "date": "date", "sessions": "int", "unique_visitors": "int",
            "page_views": "int", "bounce_rate": "float",
            "avg_session_duration_sec": "float", "traffic_source": "str",
        },
        required=(
            "date", "sessions", "unique_visitors", "page_views",
            "bounce_rate", "avg_session_duration_sec", "traffic_source",
        ),
        # Grain THẬT là 1 dòng/ngày toàn site (đã verify per_day.max()==1), KHÔNG phải
        # date+traffic_source như data_dictionary gợi ý — traffic_source chỉ là nhãn.
        grain=("date",),
        enums={
            "traffic_source": (
                "direct", "email_campaign", "organic_search",
                "paid_search", "referral", "social_media",
            ),
        },
    ),
    "sales": TableSchema(
        name="sales",
        columns={"Date": "date", "Revenue": "float", "COGS": "float"},
        required=("Date", "Revenue", "COGS"),
        grain=("Date",),
    ),
    "sample_submission": TableSchema(
        name="sample_submission",
        columns={"Date": "date", "Revenue": "float", "COGS": "float"},
        required=("Date", "Revenue", "COGS"),
        grain=("Date",),
    ),
}

ALL_TABLES: tuple[str, ...] = tuple(SCHEMAS.keys())


def get_schema(table: str) -> TableSchema:
    """Trả TableSchema của bảng. Lỗi rõ ràng nếu tên bảng không có contract."""
    try:
        return SCHEMAS[table]
    except KeyError as exc:
        raise KeyError(
            f"Bảng '{table}' không có schema contract. Bảng hợp lệ: {ALL_TABLES}"
        ) from exc


@dataclass
class SchemaValidationResult:
    """Kết quả validate 1 bảng — dùng bởi quality.py (chiều 2) và ingestion.py (quarantine)."""

    table: str
    ok: bool  # False nếu thiếu cột kỳ vọng (lỗi cấu trúc, không dùng được bảng)
    missing_columns: list[str]
    unexpected_columns: list[str]  # cột lạ, không nằm trong allowlist
    dtype_mismatch: dict[str, int]  # cột -> số dòng ép kiểu thất bại
    enum_violations: dict[str, int]  # cột -> số dòng giá trị ngoài enum
    row_valid_mask: pd.Series  # bool theo index df gốc — True = dòng qua hết check dtype/enum
    n_rows: int
    n_invalid_rows: int


def validate_schema(df: pd.DataFrame, table: str) -> SchemaValidationResult:
    """Chiều 2 — Schema & format: dtype đúng, enum hợp lệ, format ngày.

    KHÔNG sửa `df` (trả mask để caller tự tách quarantine, xem `ingestion.split_valid_quarantine`).
    Không check `required` (null) ở đây — thuộc chiều 5 (`quality.completeness`).
    """
    ts = get_schema(table)
    missing_columns = [c for c in ts.columns if c not in df.columns]
    known_extra = set(ts.columns) | set(ts.allowed_extra_columns)
    unexpected_columns = [c for c in df.columns if c not in known_extra]

    mask = pd.Series(True, index=df.index)
    dtype_mismatch: dict[str, int] = {}
    enum_violations: dict[str, int] = {}

    for col, kind in ts.columns.items():
        if col not in df.columns:
            continue
        series = df[col]
        if kind in ("int", "float"):
            coerced = pd.to_numeric(series, errors="coerce")
            bad = coerced.isna() & series.notna()
        elif kind == "date":
            coerced = pd.to_datetime(series, format="%Y-%m-%d", errors="coerce")
            bad = coerced.isna() & series.notna()
        else:
            bad = pd.Series(False, index=df.index)  # str: không ép kiểu, chỉ check enum bên dưới
        n_bad = int(bad.sum())
        if n_bad:
            dtype_mismatch[col] = n_bad
            mask &= ~bad

        if col in ts.enums:
            valid_values = set(ts.enums[col])
            as_str = series.astype("string")
            bad_enum = series.notna() & ~as_str.isin(valid_values)
            n_bad_enum = int(bad_enum.sum())
            if n_bad_enum:
                enum_violations[col] = n_bad_enum
                mask &= ~bad_enum

    n_invalid = int((~mask).sum())
    return SchemaValidationResult(
        table=table,
        ok=len(missing_columns) == 0,
        missing_columns=missing_columns,
        unexpected_columns=unexpected_columns,
        dtype_mismatch=dtype_mismatch,
        enum_violations=enum_violations,
        row_valid_mask=mask,
        n_rows=len(df),
        n_invalid_rows=n_invalid,
    )


# Referential integrity — port nguyên từ phase0_full_qc.py FK_CHECKS.
# (child_table, child_col, parent_table, parent_col)
FK_CHECKS: tuple[tuple[str, str, str, str], ...] = (
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
)
