# Tester — vá 5 gap coverage `tests/test_ingestion.py` (audit `2026-08-10`)

Vai trò: tester, QA. Nhiệm vụ: vá đúng 5 gap (G1–G5) mà phiên audit độc lập trước ghi nợ trong
`.process_status/tester_verify_test_ingestion_2026-08-10.md` (dòng log PROCESS.md tương ứng:
"2026-08-10: tester audit độc lập `tests/test_ingestion.py` (commit `2a06c33`)").

**Phạm vi tuân thủ đúng ràng buộc được giao**: CHỈ sửa `tests/test_ingestion.py`. KHÔNG đụng
`src/datathon/ingestion.py`, `tests/conftest.py`, `tests/test_schema.py`, `PROCESS.md`, hay bất
kỳ file nào khác — xác nhận bằng `git diff --stat` ở mục 7.

Môi trường: `.venv/bin/python` = Python 3.9.6, pytest 8.4.2, ruff (bản cài trong `.venv`), macOS
darwin. Baseline TRƯỚC khi sửa (verify lại, không tin số cũ suông): `pytest
tests/test_ingestion.py -q` = 32 passed; `pytest -q` toàn repo = 85 passed.

---

## 1. Tóm tắt thay đổi — map đúng 5 gap → test mới

| Gap | Mức độ | Hàm target | Class mới/sửa | Số test thêm |
|---|---|---|---|---|
| G1 | Medium | `add_metadata_columns()` | `TestAddMetadataColumns` (mới) | 9 |
| G2 | Low-Medium | `_row_checksum()` / cột `_checksum` | `TestRowChecksum` (mới) | 8 |
| G3 | Low | `load_raw()` nhánh `FileNotFoundError` | `TestLoadRaw` (mới) | 2 |
| G4 | Low | `build_order_items_line_id()` nhánh `raise ValueError` | `TestBuildOrderItemsLineId` (mới) | 2 |
| G5 | Low | Assert lỏng 2 test trong `TestIngestTable` | Sửa tại chỗ (không thêm class) | 0 (2 test sửa, không thêm) |

Tổng: **32 → 53 test** trong `tests/test_ingestion.py` (+21, đúng bằng 9+8+2+2, G5 không thêm
test mới — chỉ pin lại assert của 2 test đã có).

4 class mới được chèn giữa `TestSplitValidQuarantine` (nhóm cốt lõi #2 cũ) và `TestMergeUpsert`
(nhóm cốt lõi #3 cũ) — đổi tên comment đánh số từ 4 nhóm (1–4) thành 8 nhóm (1–8) cho khớp thứ tự
thật trong file (`1 IngestResult → 2 split_valid_quarantine → 3 load_raw[MỚI] → 4
add_metadata_columns[MỚI] → 5 _row_checksum[MỚI] → 6 build_order_items_line_id[MỚI] → 7
merge_upsert → 8 ingest_table`), thay vì chèn kiểu "2b/2c" — giữ đúng convention đánh số tuần tự
đã có trong file, không phải hack cho nhanh. 4 nhóm gốc (`IngestResult`, `split_valid_quarantine`,
`merge_upsert`, `ingest_table`) giữ NGUYÊN nội dung — chỉ đổi số thứ tự trong comment + G5 (2 dòng
assert trong `ingest_table`), không xoá/viết lại test nào đã xanh.

---

## 2. Chi tiết từng gap — cái gì đổi, vì sao chọn cách đó

### G1 — `add_metadata_columns()`: 5 cột metadata bắt buộc (Medium)

**Trước**: 0 test tự assert tên/giá trị/kiểu 5 cột `_ingested_at`/`_source_file`/
`_source_row_number`/`_checksum`/`_batch_id` — dùng gián tiếp qua 32 test cũ nhưng không ai kiểm.

**Sau**: `TestAddMetadataColumns` (9 test) — đủ tên cột, giá trị đúng tham số truyền vào
(`_source_file`, `_batch_id`), `_source_row_number` đúng 0-based tuần tự theo thứ tự dòng,
`_ingested_at` là timestamp UTC-aware ISO, nằm trong khoảng `[before_call, after_call]` đo thật
(không giả định), dùng CHUNG 1 giá trị cho mọi dòng trong 1 lần gọi (`nunique()==1`), `_checksum`
đúng hình dạng chuỗi hex 64 ký tự, business columns giữ nguyên không đổi, không mutate df gốc,
trả object mới (không cùng reference).

**Vì sao hardcode `REQUIRED_METADATA_COLUMNS` thay vì import `schema.METADATA_COLUMNS`**: cân
nhắc dùng lại hằng số có sẵn trong `schema.py` (DRY hơn), nhưng chọn hardcode trực tiếp 5 tên cột
trong test — lý do: nếu dùng lại `schema.METADATA_COLUMNS` để so sánh, một lỗi ĐỒNG THỜI ở cả
`schema.py` VÀ `ingestion.py` (vd ai đó xoá `_batch_id` khỏi cả 2 nơi cùng lúc khi refactor) sẽ
không bị bắt — test sẽ so sánh 2 nguồn cùng sai với nhau và vẫn xanh. Hardcode theo đúng literal
đã ghi trong `RESTRUCTURE_AGENTS.md` "DE HARDENING STANDARD" (nguồn sự thật ngoài code) biến test
thành 1 "chốt hợp đồng" độc lập với cả 2 file kia.

### G2 — `_row_checksum()` / cột `_checksum`: deterministic + xử lý NaN (Low-Medium)

**Trước**: 0 test đọc/assert nội dung cột `_checksum` trong toàn repo.

**Sau**: `TestRowChecksum` (8 test) — cùng nội dung → cùng checksum; khác nội dung → khác
checksum; khớp đúng sha256 tính TAY độc lập (không gọi lại `_row_checksum` để so sánh — tránh bug
tự che bug) theo đúng docstring hàm (payload nối bằng `"|"`); NaN → chuỗi rỗng trong payload
(không phải chữ `"nan"` literal); output đúng hình dạng hex 64 ký tự; 1 test wiring (checksum của
`add_metadata_columns` khớp gọi `_row_checksum` trực tiếp trên business columns — bắt lỗi nếu ai
đó lỡ đổi cột/axis truyền vào `.apply()`); 1 test checksum ĐỘC LẬP với `_batch_id`/`_source_file`
(đúng mục đích "phát hiện thay đổi khi MERGE lại" — 2 lần ingest cùng nội dung nhưng khác batch
phải ra cùng checksum); 1 test NaN không crash qua đường gọi thật `add_metadata_columns`.

**Phát hiện khi thiết kế test (không phải bug, ghi nhận vì hữu ích)**: dựng `pd.Series({"a": 1,
"b": float("nan")})` KHÔNG ép `dtype` làm pandas tự đổi `1` (int) thành `1.0` (float) — vì Series
chỉ có 2 giá trị số (int + NaN) nên pandas chọn 1 dtype số chung (float64) cho toàn bộ Series. Đã
verify riêng bằng script trước khi viết test (xem mục 5) rồi CHỌN CÁCH ép `dtype="object"` tường
minh khi dựng row test tay, để cô lập đúng logic của `_row_checksum` (join + NaN + hash) khỏi hiệu
ứng suy kiểu này của pandas. Đây là hiệu ứng của CÁCH TEST TỰ DỰNG DỮ LIỆU, không phải hành vi của
hàm `_row_checksum`/`add_metadata_columns` — xem mục 4 "Điều tra thêm" để biết vì sao nó KHÔNG xảy
ra trên dữ liệu 14 bảng thật.

### G3 — `load_raw()`: nhánh `FileNotFoundError` (Low)

**Trước**: 0 test chạm nhánh này trong toàn repo (chỉ có nhánh `KeyError` được cover qua
`ingest_table("khong_ton_tai")`).

**Sau**: `TestLoadRaw` (2 test) — dùng đúng pattern `monkeypatch.setitem(ingestion.RAW_TABLES,
...)` đã có sẵn trong file (2 test cũ ở `TestIngestTable` cũng dùng cách này), trỏ 1 bảng sang
path `tmp_path` KHÔNG tồn tại thật trên đĩa (`assert not ghost_path.exists()` làm tiền đề, không
giả định suông) → verify `FileNotFoundError` raise đúng + message chứa tên bảng VÀ path (debug
được, không phải message chung chung).

### G4 — `build_order_items_line_id()`: nhánh `raise ValueError` (Low)

**Trước**: 0 test gọi hàm này mà KHÔNG đi qua `add_metadata_columns()` trước (mọi lời gọi thật
trong `ingest_table` luôn có `_source_row_number` sẵn).

**Sau**: `TestBuildOrderItemsLineId` (2 test) — 1 test dựng DataFrame CỐ Ý thiếu
`_source_row_number`, verify `ValueError` raise đúng + message chứa tên cột thiếu; 1 test đối
chứng happy-path (cùng DataFrame, chỉ thêm đúng 1 cột `_source_row_number`) để cô lập đúng NGUYÊN
NHÂN raise, không phải do dữ liệu khác sai.

### G5 — pin đúng trạng thái/số dòng quarantine (Low)

**Trước**: `assert result.status in ("OK", "QUARANTINED")` — chấp nhận cả 2 trạng thái.

**Sau**: chạy `ingest_table()` THẬT cho đủ 14 bảng `data/sample` TRƯỚC khi sửa assert (lệnh +
output thật ở mục 6) → tất cả đều `status="OK"`, `rows_quarantined=0`. Pin cứng
`assert result.status == "OK"` + `assert result.rows_quarantined == 0` cho
`test_runs_clean_on_every_sample_table` (parametrize 14 bảng) và
`test_order_items_gets_unique_surrogate_key_column` (thêm `assert len(valid) == 2193` — đúng số
dòng dữ liệu thật của `data/sample/order_items.csv`, đo được từ `wc -l` trừ 1 dòng header).

---

## 3. Verify — `pytest tests/test_ingestion.py -v`

Trước khi sửa (baseline, chạy lại để xác nhận, không tin số cũ suông):

```
$ .venv/bin/python -m pytest tests/test_ingestion.py -q
32 passed in 0.32s
```

Sau khi vá (dán đủ danh sách 53 test, không cắt bớt):

```
collected 53 items

tests/test_ingestion.py::TestIngestResult::test_construction_and_fields PASSED [  1%]
tests/test_ingestion.py::TestIngestResult::test_quarantine_reasons_defaults_to_empty_dict PASSED [  3%]
tests/test_ingestion.py::TestIngestResult::test_default_dict_not_shared_between_instances PASSED [  5%]
tests/test_ingestion.py::TestSplitValidQuarantine::test_all_valid_rows_quarantine_empty_no_reason_column PASSED [  7%]
tests/test_ingestion.py::TestSplitValidQuarantine::test_dtype_violation_row_quarantined_with_reason_tagged PASSED [  9%]
tests/test_ingestion.py::TestSplitValidQuarantine::test_enum_violation_row_quarantined_with_reason_tagged PASSED [ 11%]
tests/test_ingestion.py::TestSplitValidQuarantine::test_does_not_mutate_input_dataframe PASSED [ 13%]
tests/test_ingestion.py::TestLoadRaw::test_missing_file_on_disk_raises_file_not_found_error PASSED [ 15%]
tests/test_ingestion.py::TestLoadRaw::test_error_message_names_missing_table_and_path PASSED [ 16%]
tests/test_ingestion.py::TestAddMetadataColumns::test_adds_all_five_required_metadata_columns PASSED [ 18%]
tests/test_ingestion.py::TestAddMetadataColumns::test_original_business_columns_preserved_unchanged PASSED [ 20%]
tests/test_ingestion.py::TestAddMetadataColumns::test_source_file_column_equals_argument_for_every_row PASSED [ 22%]
tests/test_ingestion.py::TestAddMetadataColumns::test_batch_id_column_equals_argument_for_every_row PASSED [ 24%]
tests/test_ingestion.py::TestAddMetadataColumns::test_source_row_number_is_zero_based_sequential_in_row_order PASSED [ 26%]
tests/test_ingestion.py::TestAddMetadataColumns::test_ingested_at_is_timezone_aware_utc_iso_timestamp_close_to_now PASSED [ 28%]
tests/test_ingestion.py::TestAddMetadataColumns::test_checksum_column_is_64_char_hex_string_on_every_row PASSED [ 30%]
tests/test_ingestion.py::TestAddMetadataColumns::test_does_not_mutate_input_dataframe PASSED [ 32%]
tests/test_ingestion.py::TestAddMetadataColumns::test_returns_new_dataframe_object_not_same_reference PASSED [ 33%]
tests/test_ingestion.py::TestRowChecksum::test_same_content_produces_same_checksum_deterministic PASSED [ 35%]
tests/test_ingestion.py::TestRowChecksum::test_different_content_produces_different_checksum PASSED [ 37%]
tests/test_ingestion.py::TestRowChecksum::test_matches_manually_computed_sha256_of_pipe_joined_values PASSED [ 39%]
tests/test_ingestion.py::TestRowChecksum::test_nan_value_becomes_empty_string_in_payload_not_literal_nan_text PASSED [ 41%]
tests/test_ingestion.py::TestRowChecksum::test_output_is_64_char_lowercase_hex_sha256_digest PASSED [ 43%]
tests/test_ingestion.py::TestRowChecksum::test_add_metadata_columns_checksum_matches_independent_row_checksum_call PASSED [ 45%]
tests/test_ingestion.py::TestRowChecksum::test_add_metadata_columns_checksum_independent_of_batch_id_and_source_file PASSED [ 47%]
tests/test_ingestion.py::TestRowChecksum::test_add_metadata_columns_handles_nan_in_business_column_without_crashing PASSED [ 49%]
tests/test_ingestion.py::TestBuildOrderItemsLineId::test_missing_source_row_number_column_raises_value_error PASSED [ 50%]
tests/test_ingestion.py::TestBuildOrderItemsLineId::test_succeeds_once_source_row_number_column_present PASSED [ 52%]
tests/test_ingestion.py::TestMergeUpsert::test_no_existing_dedupes_last_row_per_key_in_given_order PASSED [ 54%]
tests/test_ingestion.py::TestMergeUpsert::test_existing_plus_incoming_keeps_newest_by_updated_at PASSED [ 56%]
tests/test_ingestion.py::TestMergeUpsert::test_incoming_wins_tie_break_on_equal_timestamp PASSED [ 58%]
tests/test_ingestion.py::TestMergeUpsert::test_calling_twice_with_same_incoming_is_idempotent PASSED [ 60%]
tests/test_ingestion.py::TestMergeUpsert::test_unrelated_existing_rows_survive_unchanged PASSED [ 62%]
tests/test_ingestion.py::TestIngestTable::test_bad_table_name_raises_keyerror PASSED [ 64%]
tests/test_ingestion.py::TestIngestTable::test_reuses_given_batch_id PASSED [ 66%]
tests/test_ingestion.py::TestIngestTable::test_generates_batch_id_when_not_given PASSED [ 67%]
tests/test_ingestion.py::TestIngestTable::test_order_items_gets_unique_surrogate_key_column PASSED [ 69%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[customers] PASSED [ 71%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[geography] PASSED [ 73%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[products] PASSED [ 75%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[promotions] PASSED [ 77%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[orders] PASSED [ 79%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[order_items] PASSED [ 81%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[payments] PASSED [ 83%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[shipments] PASSED [ 84%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[returns] PASSED [ 86%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[reviews] PASSED [ 88%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[inventory] PASSED [ 90%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[web_traffic] PASSED [ 92%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[sales] PASSED [ 94%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[sample_submission] PASSED [ 96%]
tests/test_ingestion.py::TestIngestTable::test_quarantines_real_enum_violation_not_silently_dropped PASSED [ 98%]
tests/test_ingestion.py::TestIngestTable::test_missing_required_column_triggers_failed_status PASSED [100%]

53 passed in 0.33s
```

**Kết luận mục 3: PASS.** 32 → 53 test (+21, khớp đúng tổng 9+8+2+2 test mới từ G1-G4; G5 không
thêm test, chỉ pin lại assert). 0 fail/error/skip.

---

## 4. Verify — `pytest -q` toàn bộ suite

Trước: 85 passed. Sau:

```
$ .venv/bin/python -m pytest -q
........................................................................ [ 67%]
.................................................................... [100%]
=============================== warnings summary ===============================
tests/test_submission.py: 1096 warnings
  .../sklearn/utils/validation.py:2739: UserWarning: X does not have valid feature names...
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
106 passed, 1096 warnings in 24.25s
```

**Kết luận mục 4: PASS.** 85 → 106 (+21, đúng bằng số test mới thêm — không phá test nào đang
xanh, không có test nào biến mất). 1096 warning đều pre-existing từ `test_submission.py`/sklearn,
không liên quan thay đổi này. **Chạy lại LẦN 2 liên tiếp** để loại flaky: **106 passed** lần nữa,
cùng warning count, thời gian tương đương (24.15s) — không flaky.

**Điều tra thêm (do có thêm 2 test monkeypatch `RAW_TABLES` mới trong `TestLoadRaw`, tương tự
pattern rủi ro rò rỉ mà audit trước đã kiểm cho 2 test cũ)** — đảo thứ tự file
`test_schema.py`↔`test_ingestion.py` cả 2 chiều:

```
$ .venv/bin/python -m pytest tests/test_schema.py tests/test_ingestion.py -q
70 passed in 0.38s
$ .venv/bin/python -m pytest tests/test_ingestion.py tests/test_schema.py -q
70 passed in 0.38s
```

17 (`test_schema.py`) + 53 (`test_ingestion.py`) = 70 — khớp cả 2 chiều, không rò rỉ monkeypatch
sang `test_schema.py` (dùng `RAW_TABLES` thật qua fixture `raw_tables_paths`/`all_sample_tables`
session-scope trong `conftest.py`).

---

## 5. Verify — `ruff check tests/test_ingestion.py`

Lần chạy đầu tiên (SAU khi viết xong 21 test mới, TRƯỚC khi sửa lint) phát hiện 2 lỗi thật:

```
$ .venv/bin/python -m ruff check tests/test_ingestion.py
UP012 [*] Unnecessary call to `encode` as UTF-8
   --> tests/test_ingestion.py:283:35
        expected = hashlib.sha256("1|hanoi|2.5".encode("utf-8")).hexdigest()
UP012 [*] Unnecessary call to `encode` as UTF-8
   --> tests/test_ingestion.py:288:35
        expected = hashlib.sha256("1||x".encode("utf-8")).hexdigest()
Found 2 errors.
```

Cả 2 đều do tôi tự viết (`test_matches_manually_computed_sha256_of_pipe_joined_values`,
`test_nan_value_becomes_empty_string_in_payload_not_literal_nan_text`) — gọi `.encode("utf-8")`
trên 1 chuỗi LITERAL (ruff gợi ý viết thẳng bytes-literal `b"..."` thay vì mã hoá lúc chạy). Sửa
đúng theo gợi ý ruff (`hashlib.sha256(b"1|hanoi|2.5")`, `hashlib.sha256(b"1||x")`) — hành vi giống
hệt, chỉ gọn hơn. Chạy lại:

```
$ .venv/bin/python -m ruff check tests/test_ingestion.py
All checks passed!
$ .venv/bin/python -m ruff check tests/
All checks passed!
```

**Kết luận mục 5: PASS** (sau 1 vòng tự sửa lint). 0 lỗi trên `tests/test_ingestion.py` và trên
toàn bộ `tests/` (kiểm rộng hơn yêu cầu để chắc chắn không văng lỗi sang import dùng chung). Đã
chạy lại `pytest tests/test_ingestion.py -v` (53 passed) sau khi sửa lint để xác nhận đổi cú pháp
không đổi hành vi test.

---

## 6. G5 — số quarantine thật từng bảng `data/sample`, đo TRƯỚC khi viết assert

Lệnh chạy (dùng đúng `ingest_table()` thật, set `DATA_RAW_PATH` trỏ `data/sample` giống hệt
`conftest.py`), chạy TRƯỚC khi sửa 2 test G5:

```
$ DATA_RAW_PATH="$(pwd)/data/sample" .venv/bin/python -c "
from datathon import schema as schema_mod
from datathon import ingestion
for table in schema_mod.ALL_TABLES:
    valid, bad, result = ingestion.ingest_table(table)
    print(f'{table:20s} status={result.status:12s} rows_in={result.rows_in:6d} rows_valid={result.rows_valid:6d} rows_quarantined={result.rows_quarantined:6d}')
"

customers            status=OK           rows_in=  1923 rows_valid=  1923 rows_quarantined=     0
geography            status=OK           rows_in=  1713 rows_valid=  1713 rows_quarantined=     0
products             status=OK           rows_in=   311 rows_valid=   311 rows_quarantined=     0
promotions           status=OK           rows_in=    50 rows_valid=    50 rows_quarantined=     0
orders               status=OK           rows_in=  2000 rows_valid=  2000 rows_quarantined=     0
order_items          status=OK           rows_in=  2193 rows_valid=  2193 rows_quarantined=     0
payments             status=OK           rows_in=  2000 rows_valid=  2000 rows_quarantined=     0
shipments            status=OK           rows_in=  1754 rows_valid=  1754 rows_quarantined=     0
returns              status=OK           rows_in=   123 rows_valid=   123 rows_quarantined=     0
reviews              status=OK           rows_in=   365 rows_valid=   365 rows_quarantined=     0
inventory            status=OK           rows_in=   250 rows_valid=   250 rows_quarantined=     0
web_traffic           status=OK           rows_in=   300 rows_valid=   300 rows_quarantined=     0
sales                status=OK           rows_in=   300 rows_valid=   300 rows_quarantined=     0
sample_submission    status=OK           rows_in=   548 rows_valid=   548 rows_quarantined=     0
```

**14/14 bảng: `status=OK`, `rows_quarantined=0`.** Đối chiếu `rows_in` với `wc -l data/sample/*.csv
| trừ 1 dòng header` — khớp (vd `order_items.csv` 2194 dòng file = 2193 dòng dữ liệu +1 header,
đúng `rows_in=2193`). Số này dùng để pin cứng `test_runs_clean_on_every_sample_table` (14 test
parametrize) + `test_order_items_gets_unique_surrogate_key_column` (thêm `len(valid) == 2193`).

Không có bảng nào trong `data/sample` phát sinh dtype/enum violation — hợp lý vì `data/sample` là
tập con lấy mẫu (không phải toàn bộ `data/raw`, xem `tests/tools/generate_sample.py`), không đại
diện cho việc "sample luôn sạch tuyệt đối trong mọi trường hợp" mà chỉ phản ánh ĐÚNG trạng thái
của file `data/sample/*.csv` HIỆN TẠI — đúng tinh thần "pin số đo được, không suy đoán" của gap G5.

---

## 7. Verify phạm vi sửa — CHỈ đúng 1 file nguồn + 1 file report

```
$ git status --short
 M PROCESS.md                                                   <- đã modified TỪ TRƯỚC session này (không phải tôi sửa)
 M tests/test_ingestion.py
?? .process_status/tester_patch_ingestion_gaps_2026-08-10.md
?? .process_status/tester_verify_test_ingestion_2026-08-10.md   <- report audit gốc, đã có sẵn

$ git diff --stat -- tests/test_ingestion.py
 tests/test_ingestion.py | 270 ++++++++++++++++++++++++++++++++++++++++++++++--
 1 file changed, 263 insertions(+), 7 deletions(-)

$ git diff --stat -- src/
(rỗng — 0 thay đổi trong src/)
```

`PROCESS.md` modified từ TRƯỚC khi bắt đầu phiên này (đúng trạng thái git ban đầu được cấp, không
phải tôi tạo ra) — **không đụng, không commit theo đúng yêu cầu**. `src/datathon/ingestion.py`
**0 thay đổi** — xác nhận đúng ràng buộc "CHỈ sửa tests/test_ingestion.py".

---

## 8. Bug thật trong `ingestion.py`? — KHÔNG tìm thấy

Trong lúc viết 21 test mới cho G1–G4, mọi hành vi quan sát được đều khớp ĐÚNG docstring + logic
đọc trong `ingestion.py` — không phát hiện sai lệch nào giữa "code làm gì" và "code NÊN làm gì"
theo `RESTRUCTURE_AGENTS.md`/docstring module. Cụ thể đã soi kỹ (không chỉ chạy xanh là kết luận):

- `add_metadata_columns`: 5 cột đúng tên, đúng giá trị, không mutate input, trả object mới — đúng
  100% docstring.
- `_row_checksum`: payload nối `"|"`, NaN → rỗng, sha256 hex — đúng 100% docstring + code đọc
  được.
- `load_raw`: `FileNotFoundError` đúng message có tên bảng + path.
- `build_order_items_line_id`: `ValueError` đúng message có tên cột thiếu.

**1 phát hiện PHỤ (KHÔNG phải bug, chỉ là quan sát về cách dựng dữ liệu test) — đã điều tra kỹ
thêm để không bỏ sót rủi ro thật**: khi tự dựng `pd.Series({"a": 1, "b": float("nan")})` (không ép
`dtype`) để test tay, pandas tự đổi `1` (int) thành `1.0` (float) do quy tắc suy kiểu chung của
Series khi TOÀN BỘ giá trị đều là số (int/NaN). Câu hỏi đặt ra: **hiệu ứng này có xảy ra trên dữ
liệu 14 bảng thật không** (qua đường gọi thật `df[business_cols].apply(_row_checksum, axis=1)`
trong `add_metadata_columns`)? Đã verify bằng 3 script độc lập (không suy đoán):

1. Bảng có ít nhất 1 cột string (12/14 bảng: `customers`, `geography`, `products`, `promotions`,
   `orders`, `order_items`, `payments`, `returns`, `reviews`, `inventory`, `web_traffic`, + cột
   string luôn hiện diện) — cột string ép cả row về `dtype=object`, giữ nguyên int. **An toàn.**
2. Bảng KHÔNG có cột string nhưng có cột ngày (`shipments`: `order_id` int + `ship_date`/
   `delivery_date` datetime64 + `shipping_fee` float) — verify thật: `datetime64` cũng ép cả row
   về `dtype=object` (không có supertype số chung giữa `int64`+`datetime64`), giữ nguyên
   `order_id` là `int`, kể cả khi `delivery_date` là `NaT`. **An toàn.**
3. 2 bảng còn lại KHÔNG có cột string, có cột ngày nhưng KHÔNG có cột int nào (`sales`,
   `sample_submission`: chỉ `Date`+`Revenue`+`COGS`, đều float/date) — không có cột int nào để bị
   "mất" thành float, và verify thêm: `Date` (Timestamp) vẫn giữ nguyên dạng đọc được
   (`"2020-01-01 00:00:00"`), không bị ép thành số epoch. **An toàn.**

**Kết luận**: hiệu ứng suy kiểu của pandas là CÓ THẬT (verify được) nhưng **không áp dụng cho bất
kỳ bảng nào trong 14 bảng schema thật của dự án** — mọi bảng đều có ít nhất 1 cột string hoặc cột
ngày "neo" `dtype=object` cho cả dòng khi trích xuất qua `.apply(axis=1)`. Không phải bug, không
cần sửa `ingestion.py`, không cần thêm test riêng cho rủi ro này (đã loại trừ bằng chứng, không
phải bỏ qua vì lười). Ghi lại đầy đủ ở đây để ai đó sau này thêm bảng mới CHỈ TOÀN cột số (không
string, không date) sẽ biết cần re-check lại giả định này.

---

## 9. Gap còn lại / ngoài phạm vi 5 gap được giao

- `new_batch_id()` — audit gốc (mục 5.3 report cũ) từng ghi chú "Nhẹ: không test format/độ dài
  chuỗi hex trả về" nhưng **KHÔNG nằm trong danh sách 5 gap G1–G5** được giao vá lần này — cố tình
  KHÔNG thêm test cho hàm này, giữ đúng phạm vi được giao, tránh scope creep.
- 2 test characterize cũ (nợ #1, đã đóng theo log PROCESS.md `2026-08-10`
  `lookup_lag`/`validate_submission`) không liên quan file này, không đụng tới.
- Không phát sinh gap coverage MỚI nào từ chính 21 test vừa thêm (mỗi hàm target của G1–G4 đều đã
  cover đủ nhánh chính + nhánh lỗi được yêu cầu).

---

## Tổng kết PASS/FAIL

| Mục | Kết quả |
|---|---|
| 5 gap (G1–G5) đều đã vá, đúng phạm vi assert được yêu cầu | **PASS** |
| `pytest tests/test_ingestion.py -v`: 32 → 53 passed | **PASS** |
| `pytest -q` toàn repo: 85 → 106 passed, không phá test cũ, không flaky (2 lần chạy) | **PASS** |
| `ruff check tests/test_ingestion.py`: 0 lỗi (sau 1 vòng tự sửa 2 lỗi UP012) | **PASS** |
| G5: số liệu quarantine đo THẬT trước khi viết assert cứng | **PASS** (14/14 bảng OK, 0 quarantine) |
| Phạm vi sửa: CHỈ `tests/test_ingestion.py` + report, `src/` 0 thay đổi | **PASS** |
| Bug thật trong `ingestion.py`? | **KHÔNG có** — 1 quan sát phụ (pandas dtype suy kiểu khi tự dựng test data) đã điều tra, xác nhận KHÔNG áp dụng cho 14 bảng thật, không phải bug |

File này không sửa `src/datathon/ingestion.py`, không sửa `tests/conftest.py`/`test_schema.py`,
không sửa `PROCESS.md` — đúng phạm vi được giao.
