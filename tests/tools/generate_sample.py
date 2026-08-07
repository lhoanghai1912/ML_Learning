"""Sinh `data/sample/*.csv` từ `data/raw/*.csv` cho M5 (tests + CI, không cần docker/Spark).

KHÔNG sửa data/raw (chỉ đọc). Deterministic (head N + filter theo id set) — chạy lại ra
kết quả giống hệt, không random.

Chiến lược (không chỉ "head N" độc lập từng bảng — giữ referential integrity thật giữa các
bảng liên quan, để check_ri()/reconcile() trên sample có ý nghĩa thật):
    1. `orders` = head N_ORDERS dòng đầu (order_id 1..N, liên tục theo dữ liệu gốc).
    2. `order_items/payments/shipments/returns/reviews` = lọc theo order_id thuộc tập trên
       (đọc full CSV rồi filter — các bảng raw không quá lớn để pandas xử lý 1 lần).
    3. `customers` = lọc theo customer_id xuất hiện trong `orders` sample.
    4. `geography` = lọc theo zip xuất hiện trong `orders` + `customers` sample.
    5. `products` = lọc theo product_id xuất hiện trong `order_items/returns/reviews` sample.
    6. `promotions` = copy nguyên (chỉ 50 dòng, ~8KB — giữ đủ để order_items FK promo_id không
       orphan).
    7. `inventory` = head N_INVENTORY dòng ĐỘC LẬP (không filter theo product_id sample) —
       CỐ Ý giữ nguyên "head N thô" để có ca RI-orphan THẬT (không synthetic) cho smoke test
       chiều 4 (nhiều snapshot inventory tham chiếu product_id ngoài tập `products` sample nhỏ).
    8. `sales`, `web_traffic` = head N độc lập (không có FK).
    9. `sample_submission` = copy nguyên (548 dòng, cần đủ để test format submission).

Dùng dtype=str khi đọc để giữ nguyên định dạng số/ngày gốc (không làm tròn/đổi định dạng khi
ghi lại to_csv).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

TESTS_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from datathon.config import DATA_RAW, DATA_SAMPLE

N_ORDERS = 2000
N_INVENTORY = 250
N_SALES = 300
N_WEB_TRAFFIC = 300


def _read(table: str) -> pd.DataFrame:
    return pd.read_csv(DATA_RAW / f"{table}.csv", dtype=str, keep_default_na=True)


def _write(df: pd.DataFrame, table: str) -> None:
    DATA_SAMPLE.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_SAMPLE / f"{table}.csv", index=False)


def main() -> None:
    orders = _read("orders").head(N_ORDERS).copy()
    order_ids = set(orders["order_id"])

    order_items = _read("order_items")
    order_items = order_items[order_items["order_id"].isin(order_ids)].copy()

    payments = _read("payments")
    payments = payments[payments["order_id"].isin(order_ids)].copy()

    shipments = _read("shipments")
    shipments = shipments[shipments["order_id"].isin(order_ids)].copy()

    returns = _read("returns")
    returns = returns[returns["order_id"].isin(order_ids)].copy()

    reviews = _read("reviews")
    reviews = reviews[reviews["order_id"].isin(order_ids)].copy()

    customer_ids = set(orders["customer_id"])
    customers = _read("customers")
    customers = customers[customers["customer_id"].isin(customer_ids)].copy()

    zips = set(orders["zip"]) | set(customers["zip"])
    geography = _read("geography")
    geography = geography[geography["zip"].isin(zips)].copy()

    product_ids = (
        set(order_items["product_id"])
        | set(returns["product_id"])
        | set(reviews["product_id"])
    )
    products = _read("products")
    products = products[products["product_id"].isin(product_ids)].copy()

    promotions = _read("promotions")  # copy nguyên, đã nhỏ

    inventory = _read("inventory").head(N_INVENTORY).copy()  # head thô, cố ý (xem docstring)
    sales = _read("sales").head(N_SALES).copy()
    web_traffic = _read("web_traffic").head(N_WEB_TRAFFIC).copy()
    sample_submission = _read("sample_submission")  # copy nguyên, 548 dòng

    tables = {
        "orders": orders,
        "order_items": order_items,
        "payments": payments,
        "shipments": shipments,
        "returns": returns,
        "reviews": reviews,
        "customers": customers,
        "geography": geography,
        "products": products,
        "promotions": promotions,
        "inventory": inventory,
        "sales": sales,
        "web_traffic": web_traffic,
        "sample_submission": sample_submission,
    }
    for name, df in tables.items():
        _write(df, name)
        print(f"{name}: {len(df)} dòng -> data/sample/{name}.csv")


if __name__ == "__main__":
    main()
