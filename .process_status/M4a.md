# M4a — de — schema.py / ingestion.py / quality.py

Status: DONE (chưa gộp PROCESS.md — PO tự cập nhật theo protocol song song).

## File tạo (đúng ownership, không đụng file khác)
- `src/datathon/schema.py`
- `src/datathon/ingestion.py`
- `src/datathon/quality.py`

## Nguồn port
- `docs/analysis/phase0_qc/phase0_full_qc.py` (dict `EXPECTED`, `FK_CHECKS`, PHẦN 1-5) — đã verify
  lại enum/dup trực tiếp trên `data/raw/*.csv` (không suy đoán), khớp báo cáo `phase0_qc_report.md`.

## Nội dung

### schema.py
- `TableSchema` dataclass: dtype (int/float/str/date), `required` (not-null, đã loại 2 ngoại lệ
  null hợp lệ: `order_items.promo_id/promo_id_2`, `promotions.applicable_category`), `grain`,
  `grain_unique`, `enums` (lấy từ data thật), `allowed_extra_columns` (allowlist evolution — mặc
  định 5 cột metadata).
- 14 `SCHEMAS` đủ (customers…sample_submission).
- `order_items`: `grain_unique=False` (16 cặp (order_id,product_id) trùng — dòng hàng hợp lệ, đã
  verify không phải lỗi). Cần surrogate `order_item_line_id` (build ở `ingestion.py`).
- `validate_schema(df, table)` -> `SchemaValidationResult` (missing/unexpected columns, dtype
  mismatch, enum violations, row_valid_mask bool) — KHÔNG check null (thuộc chiều 5 riêng).
- `FK_CHECKS`: 15 cặp FK port nguyên từ phase0.

### ingestion.py
- `load_raw(table)` — đọc qua `config.RAW_TABLES`, parse date theo schema.
- `add_metadata_columns()` — gắn đủ 5 cột: `_ingested_at/_source_file/_source_row_number/
  _checksum/_batch_id`.
- `build_order_items_line_id()` — surrogate SHA256(order_id|product_id|_source_row_number), ổn
  định vì CSV nguồn không đổi thứ tự dòng.
- `split_valid_quarantine()` — tách theo `row_valid_mask`, KHÔNG drop, gắn `_dq_reason`.
- `ingest_table(table)` -> (valid_df, quarantine_df, `IngestResult`) — pure pandas, KHÔNG ghi
  Iceberg thật (M2 gọi lại các hàm này khi ghi Spark/Iceberg, tránh 2 định nghĩa MERGE).
- `merge_upsert(existing, incoming, natural_key, updated_at_col)` — mô phỏng `MERGE INTO`, verify
  idempotent (test dưới).

### quality.py
- 10 hàm đúng tên theo AGENTS.md: `inventory / validate_schema / keys / check_ri / completeness /
  business_rules / time_coverage / dup_outlier / reconcile / write_dq_log`.
- `DQResult` dataclass + `SEVERITY_BY_DIMENSION` (1/3/9=HARD_FAIL, 2/4/6/8=QUARANTINE, 5/7=WARN,
  10=INFO) — đúng fail-rule trong work order.
- `reconcile()`: check chính thức (thr=1.0%, port nguyên phase0) = sales↔order_items (định nghĩa
  khớp nhất tự động chọn theo MAPE nhỏ nhất). payments↔sales chỉ diagnostic (threshold 10%, WARN
  only, KHÔNG kéo gate — phase0 gốc cũng chỉ print MAPE này, không gate).
- `run_all()` — chạy đủ 10 chiều trên 14 bảng, ghi `docs/dq_log/dq_log_<batch_id>.csv` +
  `dq_log_latest.csv` (thay `ops.dq_log` Postgres tạm thời tới khi M2 dựng infra — cùng schema
  cột, M2 chỉ cần INSERT INTO ops.dq_log SELECT * FROM CSV).

## Verify đã chạy

```
python3 -c "import sys;sys.path.insert(0,'src');import datathon.schema,datathon.ingestion,datathon.quality"
-> import OK
```

- Đủ 10 hàm DQ: `inventory, validate_schema, keys, check_ri, completeness, business_rules,
  time_coverage, dup_outlier, reconcile, write_dq_log` (list qua `DIMENSION_NAME`).
- Chạy 1 chiều trên CSV thật qua config: `quality.completeness(load_raw('sales'), 'sales')` ->
  PASS cả 3 cột (Date/Revenue/COGS null_rate 0%).
- Chạy **toàn bộ 10 chiều** trên **14 bảng thật** (`quality.run_all()`, 3.1s, 199 dòng log):
  - PASS 177, WARN 21, FAIL 1 (raw chưa qua ingest -> `order_items` thiếu surrogate, ĐÚNG THIẾT
    KẾ — chiều 3 phát hiện đúng, cần gọi `ingest_table` trước).
  - `sales<->order_items` reconcile: MAPE Revenue = COGS = **0.000%** (định nghĩa `gross_all_orders`
    khớp tuyệt đối — đúng kết luận phase0 gốc).
- Test riêng full pipeline `ingest_table('order_items')` -> `keys()` PASS cả 2 check (dup grain tự
  nhiên 16 dòng = INFO không lỗi; dup surrogate = 0). `merge_upsert()` gọi 2 lần: 714,669 ->
  714,669 dòng (idempotent, không nhân đôi).
- Test artifact (`docs/dq_log/*.csv` sinh lúc verify) đã xóa trước commit — không phải file giao
  nộp của M4a (job M2 thật sẽ tự sinh log khi chạy ingest).

## Blocker / ghi chú cho PO
- KHÔNG có blocker. KHÔNG đụng `features.py/models.py/backtest.py/submission.py` (M4b) hay
  `config.py` (M1).
- Phát hiện lúc song song: M4b + M7 đã có file chưa commit trong working tree
  (`src/datathon/{backtest,features,models,submission}.py`, `data/README.md`,
  `.process_status/M7.md`) — KHÔNG đụng, để nguyên cho chủ sở hữu tự commit.
- `docs/dq_log/` là output RUNTIME của `quality.write_dq_log()`, không phải file source — đã thêm
  info này để PO cân nhắc gitignore nếu muốn (chưa tự ý sửa `.gitignore`, ngoài ownership M4a).
