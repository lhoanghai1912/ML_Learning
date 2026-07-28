# -*- coding: utf-8 -*-
# QC0.1 — Snapshot/Inventory (@de)
# Chup trang thai 14 bang raw: rows, cols, bytes, encoding, delimiter, sha256.
# CHI DOC — khong sua data.

import csv
import hashlib
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA = ROOT / "data"
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)

EXPECTED_TABLES = [
    "customers", "products", "geography", "orders", "payments",
    "order_items", "shipments", "reviews", "returns", "promotions",
    "inventory", "web_traffic", "sales", "sample_submission",
]

ENCODINGS_TRY = ["utf-8", "utf-8-sig", "latin1", "cp1258"]


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_encoding(path):
    for enc in ENCODINGS_TRY:
        try:
            with open(path, "r", encoding=enc) as f:
                f.read()
            return enc
        except UnicodeDecodeError:
            continue
    return "unknown(binary?)"


def detect_delimiter(path, encoding):
    with open(path, "r", encoding=encoding, errors="replace") as f:
        sample = f.read(8192)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
        return dialect.delimiter
    except csv.Error:
        return ","  # fallback mac dinh


def count_rows_cols(path, encoding, delimiter):
    with open(path, "r", encoding=encoding, errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        header = next(reader)
        n_cols = len(header)
        n_rows = sum(1 for _ in reader)
    return n_rows, n_cols, header


files_on_disk = {p.stem for p in DATA.glob("*.csv")}
missing_vs_spec = [t for t in EXPECTED_TABLES if t not in files_on_disk]
extra_vs_spec = [t for t in files_on_disk if t not in EXPECTED_TABLES]

rows_out = []
print("QC0.1 Snapshot/Inventory — data dir:", DATA)
for name in EXPECTED_TABLES:
    path = DATA / "{}.csv".format(name)
    if not path.exists():
        rows_out.append({
            "table": name, "path": str(path), "rows": "", "cols": "",
            "bytes": "", "encoding": "", "delimiter": "", "sha256": "",
            "note": "FILE THIEU",
        })
        print("[{}] THIEU FILE".format(name))
        continue
    size_bytes = path.stat().st_size
    enc = detect_encoding(path)
    delim = detect_delimiter(path, enc if enc != "unknown(binary?)" else "utf-8")
    n_rows, n_cols, header = count_rows_cols(path, enc if enc != "unknown(binary?)" else "utf-8", delim)
    digest = sha256_of(path)
    rows_out.append({
        "table": name,
        "path": str(path.relative_to(ROOT)),
        "rows": n_rows,
        "cols": n_cols,
        "bytes": size_bytes,
        "encoding": enc,
        "delimiter": "TAB" if delim == "\t" else delim,
        "sha256": digest,
        "note": "",
    })
    print("[{:<18}] rows={:>9,} cols={:>3} bytes={:>10,} enc={:<10} sep='{}' sha256={}".format(
        name, n_rows, n_cols, size_bytes, enc, delim, digest[:12] + "..."))

df_out = pd.DataFrame(rows_out, columns=[
    "table", "path", "rows", "cols", "bytes", "encoding", "delimiter", "sha256", "note",
])
out_path = OUT / "qc01_inventory.csv"
df_out.to_csv(out_path, index=False)

print("\n--- So voi de bai (14 bang ky vong) ---")
print("File thua ngoai spec:", extra_vs_spec if extra_vs_spec else "(khong co)")
print("File thieu so spec  :", missing_vs_spec if missing_vs_spec else "(khong co)")
print("\nGhi:", out_path)
