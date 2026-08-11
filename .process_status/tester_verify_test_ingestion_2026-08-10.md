# Tester independent verify — `tests/test_ingestion.py` (commit `2a06c33`)

Vai trò: tester, QA độc lập. KHÔNG sửa `tests/test_ingestion.py` / `src/datathon/ingestion.py`.
Không tin self-report của phiên viết code — mọi kết luận dưới đây là PO/tester **tự chạy lại**.

Môi trường: `.venv/bin/python` = Python 3.9.6, pytest 8.4.2, macOS darwin. Không cài
`pytest-randomly` (`ModuleNotFoundError: No module named 'pytest_randomly'`) → thứ tự collect
là **cố định theo tên file alphabet** (`test_backtest → test_features_no_leakage →
test_ingestion → test_schema → test_submission`), không có yếu tố random giữa các lần chạy.

---

## 1. Đọc `tests/test_ingestion.py` (258 dòng) trước khi chạy

4 nhóm test, khớp 4 phần cốt lõi của `src/datathon/ingestion.py`:

| Class | Số test | Hàm/đối tượng target |
|---|---|---|
| `TestIngestResult` | 3 | `IngestResult` (dataclass) |
| `TestSplitValidQuarantine` | 4 | `split_valid_quarantine` |
| `TestMergeUpsert` | 5 | `merge_upsert` |
| `TestIngestTable` | 20 (14 parametrize + 6) | `ingest_table` (gọi gián tiếp `load_raw`, `add_metadata_columns`, `build_order_items_line_id`) |

Tổng 3+4+5+20 = **32**, khớp con số PROCESS.md khai.

---

## 2. Output pytest thật — `tests/test_ingestion.py -v` (dán nguyên văn)

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Users/lhoanghai_/Documents/Study/Dự án datathon2026/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/lhoanghai_/Documents/Study/Dự án datathon2026
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 32 items

tests/test_ingestion.py::TestIngestResult::test_construction_and_fields PASSED [  3%]
tests/test_ingestion.py::TestIngestResult::test_quarantine_reasons_defaults_to_empty_dict PASSED [  6%]
tests/test_ingestion.py::TestIngestResult::test_default_dict_not_shared_between_instances PASSED [  9%]
tests/test_ingestion.py::TestSplitValidQuarantine::test_all_valid_rows_quarantine_empty_no_reason_column PASSED [ 12%]
tests/test_ingestion.py::TestSplitValidQuarantine::test_dtype_violation_row_quarantined_with_reason_tagged PASSED [ 15%]
tests/test_ingestion.py::TestSplitValidQuarantine::test_enum_violation_row_quarantined_with_reason_tagged PASSED [ 18%]
tests/test_ingestion.py::TestSplitValidQuarantine::test_does_not_mutate_input_dataframe PASSED [ 21%]
tests/test_ingestion.py::TestMergeUpsert::test_no_existing_dedupes_last_row_per_key_in_given_order PASSED [ 25%]
tests/test_ingestion.py::TestMergeUpsert::test_existing_plus_incoming_keeps_newest_by_updated_at PASSED [ 28%]
tests/test_ingestion.py::TestMergeUpsert::test_incoming_wins_tie_break_on_equal_timestamp PASSED [ 31%]
tests/test_ingestion.py::TestMergeUpsert::test_calling_twice_with_same_incoming_is_idempotent PASSED [ 34%]
tests/test_ingestion.py::TestMergeUpsert::test_unrelated_existing_rows_survive_unchanged PASSED [ 37%]
tests/test_ingestion.py::TestIngestTable::test_bad_table_name_raises_keyerror PASSED [ 40%]
tests/test_ingestion.py::TestIngestTable::test_reuses_given_batch_id PASSED [ 43%]
tests/test_ingestion.py::TestIngestTable::test_generates_batch_id_when_not_given PASSED [ 46%]
tests/test_ingestion.py::TestIngestTable::test_order_items_gets_unique_surrogate_key_column PASSED [ 50%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[customers] PASSED [ 53%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[geography] PASSED [ 56%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[products] PASSED [ 59%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[promotions] PASSED [ 62%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[orders] PASSED [ 65%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[order_items] PASSED [ 68%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[payments] PASSED [ 71%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[shipments] PASSED [ 75%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[returns] PASSED [ 78%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[reviews] PASSED [ 81%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[inventory] PASSED [ 84%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[web_traffic] PASSED [ 87%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[sales] PASSED [ 90%]
tests/test_ingestion.py::TestIngestTable::test_runs_clean_on_every_sample_table[sample_submission] PASSED [ 93%]
tests/test_ingestion.py::TestIngestTable::test_quarantines_real_enum_violation_not_silently_dropped PASSED [ 96%]
tests/test_ingestion.py::TestIngestTable::test_missing_required_column_triggers_failed_status PASSED [100%]

============================== 32 passed in 0.31s ==============================
```

**Kết luận mục 2: PASS.** Đúng 32 test, đúng 32 PASSED, không skip/xfail/error. Khớp claim
PROCESS.md.

---

## 3. Full suite — `pytest -q` (dán nguyên văn)

```
........................................................................ [ 84%]
.............                                                            [100%]
=============================== warnings summary ===============================
tests/test_submission.py: 1096 warnings
  /Users/lhoanghai_/Documents/Study/Dự án datathon2026/.venv/lib/python3.9/site-packages/sklearn/utils/validation.py:2739: UserWarning: X does not have valid feature names, but LGBMRegressor was fitted with feature names
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
85 passed, 1096 warnings in 25.42s
```

**Kết luận mục 3: PASS.** Tổng **85 passed**, khớp tuyệt đối PROCESS.md log 2026-08-10
("Verify: pytest tests/test_ingestion.py -v = 32/32 passed. Full suite pytest -q = 85 passed
(53 cũ + 32 mới, không phá gì)"). 53 + 32 = 85 — số cũ khớp. 0 fail, 0 error. 1096 warning đều
từ `test_submission.py`/sklearn (`LGBMRegressor` feature-name mismatch — pre-existing, không
liên quan `test_ingestion.py`).

---

## 4. `ruff check tests/` (dán nguyên văn)

```
All checks passed!
```

**Kết luận mục 4: PASS.** 0 lỗi lint trên toàn bộ `tests/`.

---

## 5. Đánh giá CHẤT LƯỢNG test (không chỉ "chạy xanh là xong")

### 5.1. Test PASS nhưng assert lỏng / vô nghĩa?

Không có test kiểu `assert True` hay tautology. Nhưng có **2 chỗ assert lỏng có chủ đích**,
cần ghi nhận rõ (không phải bug, nhưng là giới hạn của coverage):

- `test_runs_clean_on_every_sample_table` (parametrize 14 bảng) và
  `test_order_items_gets_unique_surrogate_key_column` đều dùng
  `assert result.status in ("OK", "QUARANTINED")` — chấp nhận **cả 2** trạng thái, không pin
  cứng trạng thái/số dòng quarantine kỳ vọng cho từng bảng sample cụ thể. Đây là smoke test
  "không crash, không FAILED" hơn là test hành vi chính xác. Docstring tự thừa nhận mục đích
  ("DoD kiểu run_all 14 bảng"), nên đây là **thiết kế có chủ đích, chấp nhận được cho mục đích
  smoke**, nhưng KHÔNG thay thế được 1 test pin đúng số quarantine/table nếu cần audit chặt
  hơn sau này.

Các test còn lại (32 - 2 = 30) đều assert cụ thể, đo được (giá trị đếm dòng, giá trị cột, message
lỗi con, `is_unique`, so sánh dict/DataFrame) — không lỏng.

### 5.2. Monkeypatch `RAW_TABLES` có rò rỉ sang test khác không?

**Kết luận: KHÔNG rò rỉ. Có bằng chứng thật, không suy đoán:**

- Không có plugin random-order cài (`pytest_randomly` không tồn tại trong `.venv`) → không thể
  test "2 chiều ngẫu nhiên" qua plugin như đề bài gợi ý. Thay vào đó tự đảo thứ tự file thủ công
  bằng 2 lệnh:
  - `pytest tests/test_schema.py tests/test_ingestion.py -v` → **49 passed**
  - `pytest tests/test_ingestion.py tests/test_schema.py -v` (thứ tự ngược) → **49 passed**
  Cả 2 chiều đều xanh, không lỗi khác nhau. `test_schema.py` (qua `conftest.py`) dùng
  `add_metadata_columns`/`build_order_items_line_id` thật và fixture `raw_tables_paths` trỏ
  thẳng `RAW_TABLES` — nếu monkeypatch rò `RAW_TABLES["customers"]`/`["geography"]` sang path
  tmp giả, các test này sẽ crash (file tmp đã bị pytest dọn hoặc dữ liệu sai) — không xảy ra.
- Chạy `pytest tests/ -p no:randomly -v` **2 lần liên tiếp** (đúng yêu cầu đề bài, dù plugin
  không tồn tại nên `-p no:randomly` là no-op vô hại) → cả 2 lần **85 passed, 1096 warnings**,
  thời gian 24.36s/23.85s — không flaky.
- Verify trực tiếp cơ chế `pytest.MonkeyPatch` (độc lập với file test, tự viết script kiểm 1 lần
  nữa cho chắc, không tin lời pytest docs suông):
  ```
  before = dict(ingestion.RAW_TABLES)
  mp = pytest.MonkeyPatch(); mp.setitem(ingestion.RAW_TABLES, 'customers', 'FAKE_PATH.csv')
  # during patch: FAKE_PATH.csv
  mp.undo()
  # leak? False
  # restored value: /Users/lhoanghai_/.../data/raw/customers.csv
  ```
  Xác nhận `monkeypatch` (function-scoped fixture) tự `undo()` đúng cơ chế pytest chuẩn, dict
  gốc phục hồi nguyên vẹn sau khi test kết thúc.
- Ghi chú thêm: trong chính `tests/test_ingestion.py`, 2 test dùng `monkeypatch.setitem`
  (`test_quarantines_real_enum_violation_not_silently_dropped`,
  `test_missing_required_column_triggers_failed_status`) nằm **SAU CÙNG** trong class
  `TestIngestTable` (cả 14 test `test_runs_clean_on_every_sample_table[customers|geography]`
  đã chạy xong TRƯỚC đó) — nên dù có giả thuyết rò rỉ, cũng không tự-che-giấu được trong nội bộ
  file này; rủi ro thật (nếu có) chỉ lộ ở file chạy SAU (`test_schema.py`), và đã verify sạch ở
  trên.

### 5.3. Coverage — hàm/nhánh nào của `src/datathon/ingestion.py` CHƯA có test?

`grep "^def " src/datathon/ingestion.py` cho 8 hàm top-level (+ 1 dataclass `IngestResult`
không tính bằng `def`):

| Hàm | Test trực tiếp trong `test_ingestion.py`? | Test gián tiếp qua hàm khác? | Gap |
|---|---|---|---|
| `new_batch_id()` | Không | Có — `ingest_table(batch_id=None)` 2 lần, assert 2 batch_id khác nhau | Nhẹ: không test format/độ dài chuỗi hex trả về |
| `_row_checksum()` (private) | Không | Không — cột `_checksum` sinh ra trong mọi lần `ingest_table` nhưng **KHÔNG có test nào đọc/assert cột `_checksum`** | **Có** — 0% coverage về nội dung/tính đúng đắn |
| `load_raw()` | Không | Có (rộng) — fixture `all_sample_tables` (session-scope, `conftest.py`) gọi `load_raw` cho **14/14 bảng**, dùng ở `test_schema.py`; nhánh `KeyError` gián tiếp qua `ingest_table("khong_ton_tai")` | **Có 1 nhánh trắng**: `FileNotFoundError` (path tồn tại trong `RAW_TABLES` nhưng file không tồn tại trên đĩa) — **0 test nào trong toàn repo chạm nhánh này** |
| `add_metadata_columns()` | Không trực tiếp | Có — dùng trong mọi `ingest_table(...)` (32 lần chạy) và trực tiếp ở `test_schema.py:163` | **Có gap thật**: không có test nào assert **5 cột metadata bắt buộc** (`_ingested_at`, `_source_file`, `_source_row_number`, `_checksum`, `_batch_id`) tồn tại đúng tên/đúng giá trị — đây là yêu cầu cứng ghi ngay trong docstring module ("5 cột metadata bắt buộc") và trong `RESTRUCTURE_AGENTS.md` (DE HARDENING STANDARD), nhưng **không có test nào enforce trực tiếp**. Cũng không có test "không mutate df gốc" cho hàm này (khác `split_valid_quarantine` đã có) |
| `build_order_items_line_id()` | Không trực tiếp | Có — qua `ingest_table("order_items")` (chỉ check `is_unique`) và `test_schema.py:164` (dùng để dựng surrogate cho test khác) | **Có gap**: nhánh `raise ValueError(...)` khi thiếu `_source_row_number` — **0 test nào trong toàn repo gọi hàm này KHÔNG qua `add_metadata_columns` trước** → nhánh raise chưa từng chạy |
| `split_valid_quarantine()` | Có, đầy đủ (4 test) | — | Không gap đáng kể |
| `IngestResult` (dataclass) | Có, đầy đủ (3 test, kể cả bẫy mutable-default) | — | Không gap |
| `ingest_table()` | Có, đầy đủ (6 test + 14 parametrize) | — | Nhẹ: 2 assert lỏng đã nêu ở 5.1 |
| `merge_upsert()` | Có, đầy đủ (5 test, cả idempotent + tie-break) | — | Không gap đáng kể |

---

## 6. Danh sách gap, xếp mức độ nghiêm trọng

| # | Gap | Mức độ | Vì sao |
|---|---|---|---|
| G1 | `add_metadata_columns()` — không có test nào assert 5 cột metadata bắt buộc (tên cột, `_batch_id` đúng giá trị truyền vào, `_source_row_number` đúng range 0-based, `_source_file` đúng path) tồn tại/đúng | **Medium** | Đây là contract cứng của dự án (docstring module + DE HARDENING STANDARD), có audit trail thật (M2 dùng đúng hàm này để ghi Iceberg) — nếu ai sửa hàm làm mất 1 cột metadata, **không test nào của `test_ingestion.py` sẽ đỏ báo ngay**, phải chờ lộ ra ở tầng Spark/Trino xa hơn |
| G2 | `_row_checksum()` — 0 test trực tiếp lẫn gián tiếp đọc giá trị cột `_checksum` | **Low-Medium** | Hàm dùng để "phát hiện thay đổi khi MERGE lại" (theo docstring) — hiện không có test nào xác nhận 2 dòng cùng nội dung ra cùng checksum, khác nội dung ra khác checksum, hay dòng có NaN không crash |
| G3 | `load_raw()` — nhánh `FileNotFoundError` chưa từng được test | **Low** | Nhánh lỗi hợp lý (path khai trong config nhưng file bị xoá/chưa tải) — ít khi xảy ra trong CI (data/sample luôn có sẵn) nhưng vẫn là code path chưa verify |
| G4 | `build_order_items_line_id()` — nhánh `raise ValueError` (thiếu `_source_row_number`) chưa từng được test | **Low** | Best-practice: hàm helper nội bộ, lời gọi thực tế luôn đi sau `add_metadata_columns` nên rủi ro thực tế thấp, nhưng vẫn là dead code path về mặt coverage |
| G5 | `test_runs_clean_on_every_sample_table` / `test_order_items_gets_unique_surrogate_key_column` assert lỏng `status in ("OK","QUARANTINED")` | **Low** | Có chủ đích (smoke test), chấp nhận được, nhưng nếu muốn chặt hơn nên pin đúng trạng thái/số dòng quarantine kỳ vọng theo từng bảng `data/sample` |

**Không phát hiện gap nghiêm trọng (High/Critical)** — 4 hàm core nhất theo đúng scope module
docstring (`IngestResult`, `split_valid_quarantine`, `merge_upsert`, `ingest_table`) đều được
test đầy đủ, có chủ đích rõ ràng, assert cụ thể đo được. Monkeypatch không rò rỉ (verify độc lập
3 cách: đảo thứ tự file 2 chiều, chạy lại 2 lần liên tiếp, script kiểm cơ chế `MonkeyPatch.undo()`
riêng). Gap thật (G1, G2) nằm ở 2 hàm phụ trợ (`add_metadata_columns`, `_row_checksum`) — vốn nằm
NGOÀI 4 mục tiêu chính đã khai trong docstring của `test_ingestion.py` ("Cover 4 phần cốt lõi"),
nên không phải lỗi sai lời hứa, mà là scope chưa mở rộng tới.

---

## Tổng kết PASS/FAIL

| Mục | Kết quả |
|---|---|
| 2. `pytest tests/test_ingestion.py -v` = 32/32 PASSED | **PASS** |
| 3. `pytest -q` full suite = 85 passed, không đổi so PROCESS.md | **PASS** |
| 4. `ruff check tests/` = 0 lỗi | **PASS** |
| 5a. Assert lỏng/vô nghĩa | 2 chỗ có chủ đích, chấp nhận được (không phải bug) |
| 5b. Monkeypatch rò rỉ `RAW_TABLES` | **KHÔNG rò rỉ** (verify 3 cách độc lập) |
| 5c. Coverage đủ 4 mục tiêu core đã khai | **Đủ**; 2 hàm phụ trợ ngoài scope khai báo có gap (G1 Medium, G2 Low-Medium) |

File này không sửa `tests/test_ingestion.py`, không sửa `src/datathon/ingestion.py`, không sửa
`PROCESS.md`, không commit gì — thuần audit/verify theo yêu cầu.
