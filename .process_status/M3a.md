# M3a — de — báo cáo (dbt staging trên Trino/Iceberg)

Status: ✅ done (chờ PO verify + gộp vào PROCESS.md)
Ownership: `dbt_datathon/{dbt_project.yml,packages.yml,profiles.yml,package-lock.yml,models/staging/*,models/schema.yml}`.
Ngoại lệ được user cho phép chạm (nêu rõ trong task item 1): `pyproject.toml` (chỉ dòng pin
`dbt-trino`/`dbt-core`) + `uv.lock` hệ quả trực tiếp của pin đó. KHÔNG đụng `Makefile`,
`.process_status/M6a.md`/`M6b.md`, `data/sample/*`, `tests/*` (WIP của M5/M6a/M6b chạy song
song cùng lúc trong cùng working tree — thấy qua `git status`, không phải của mình, không add).

## Tóm tắt

dbt project chạy THẬT trên Trino/Iceberg (container M2 đang sống, không giả lập). 14
`stg_*.sql` clean 14 bảng raw, contract enforced 100%, `dbt build` = **74/74 PASS** (14 view
model + 60 data test), `dbt source freshness` = **14/14 PASS**. Row count `stg_*` khớp 100%
`raw.*` (đối chiếu Trino trực tiếp). Contract enforcement đã **verify bắt lỗi thật** (cố ý sửa
sai kiểu → build fail đúng như kỳ vọng, revert lại xanh).

## Việc đã làm

1. **Pin version** (`pyproject.toml`): `dbt-trino==1.8.0` (M0) → **`dbt-trino==1.10.3`** +
   thêm mới **`dbt-core==1.10.22`** (trước đây dbt-core không được pin tường minh, chỉ là
   transitive dep). Lý do đổi — bug thật tìm được lúc verify: `dbt-trino==1.8.0` khai
   `Requires-Dist: dbt-core >=1.8.0` (không chặn trên) → `uv lock`/`pip install` tự chọn
   dbt-core **1.12.0** (mới nhất tại thời điểm chạy), lệch xa dbt-core mà `dbt-trino 1.8.0`
   thực sự được test cùng (~1.8.x, adapter test với Trino 445). Mixing 1.8.0-adapter với
   1.12-core là rủi ro tương thích không kiểm soát được. Fix: bump `dbt-trino` lên bản mới
   nhất cùng dòng minor với `dbt-core` mới nhất khả dụng (1.10.x) + PIN CỨNG cả hai để
   `uv lock`/`pip install` không tự trôi version nữa. Đã chạy `uv lock` lại (uv có sẵn ở
   `~/Library/Python/3.9/bin/uv`, không phải cài mới) — resolve sạch, `uv.lock` cập nhật
   259 packages (trước đó do dbt-core không pin, lock cũ thực ra đã âm thầm kéo dbt-core
   1.12.0 — xác nhận đúng bug trên bằng bằng chứng từ chính `uv lock` output).
   `trino` python client (dùng bởi M2 `jobs/_lakehouse.py`) — không đổi version (0.338.0),
   dbt-trino 1.10.3 khai `trino~=0.331` (PEP440 compatible-release trên version 2-segment =
   `>=0.331, ==0.*` → 0.338.0 vẫn thoả, verify bằng `pip install` thật không hạ cấp gói).
2. `dbt_datathon/dbt_project.yml`: profile `datathon_lakehouse`, `models.staging.+materialized:
   view` (staging = view nhẹ, không vật lý hoá — an toàn/idempotent tự nhiên vì chỉ là SELECT
   định nghĩa lại, không ghi dữ liệu). KHÔNG cấu hình `intermediate:`/`marts:` — để trống cho
   M3b.
3. `dbt_datathon/packages.yml`: `dbt-labs/dbt_utils` `[">=1.3.0", "<2.0.0"]` → `dbt deps` resolve
   **1.4.1**, ghi `package-lock.yml` (đã commit — lockfile chuẩn dbt, giống vai trò `uv.lock`).
4. `dbt_datathon/profiles.yml`: target `trino`, `method: none` (Trino local không bật auth —
   "user" chỉ là nhãn session, không phải secret), `host`/`port` đọc qua
   `env_var('TRINO_HOST'/'TRINO_PORT', default)` — default khớp `.env.example`
   (localhost/8080) nên chạy được cả khi quên export; `.env` KHÔNG tự nạp bởi dbt (dbt không
   đọc `.env`, khác Python job M2 có loader riêng) — invocation chuẩn phải export trước:
   `set -a && source .env && set +a && dbt build --project-dir dbt_datathon --profiles-dir
   dbt_datathon`. `cert: false` khai tường minh (Trino local dùng HTTP, không TLS — tắt cảnh
   báo mặc định của dbt-trino 1.10 một cách CÓ CHỦ ĐÍCH thay vì im lặng).
5. `dbt_datathon/models/staging/stg_*.sql` (14 file) — mỗi model:
   - `config(contract={'enforced': true})`.
   - Ép kiểu tường minh khớp `_TRINO_TYPE` M2 (bigint/double/date/varchar) — 1 nguồn sự thật
     kiểu dữ liệu duy nhất giữa landing (M2) và staging (M3a), verify bằng `DESCRIBE
     iceberg.raw.<table>` thật trước khi viết SQL (không suy đoán từ tài liệu).
   - Rule làm sạch port từ `docs/analysis/phase0_qc/phase0_qc_report.md` (đọc thật, không bịa):
     - **W10** `stg_promotions.applicable_category`: `coalesce(..., 'all_categories')` — verify
       `SELECT count(*) WHERE applicable_category='all_categories'` = **40** (khớp đúng "40/50
       thiếu (80%)" trong báo cáo phase0).
     - **W7** `stg_order_items`: KHÔNG dedup 16 cặp `(order_id, product_id)` trùng (là line item
       hợp lệ khác giá/qty) — giữ nguyên grain dòng hàng.
     - **I7**: header gốc PascalCase (`sales`/`sample_submission`) đã chuẩn hoá snake_case sẵn ở
       M2 landing — verify `DESCRIBE` xác nhận, staging không cần đổi tên lại.
   - `order_items._source_row_number` (metadata M2) đổi tên **`line_number`** ở staging — dùng
     làm phần thứ 3 của grain key `(order_id, product_id, line_number)` vì raw không có line-id
     tự nhiên; AN TOÀN vì CSV nguồn tĩnh (không dùng `ROW_NUMBER()` tính lại — đúng cảnh báo
     RESTRUCTURE_AGENTS.md, việc tạo surrogate key nghiệp vụ chính thức cho intermediate thuộc
     M3b, ở đây chỉ đủ cho test uniqueness staging).
   - Metadata cols (`_ingested_at`,...) **KHÔNG** đưa vào staging output (staging = lớp business
     sạch; freshness đọc trực tiếp từ `source` — không cần staging carry-forward).
6. `dbt_datathon/models/schema.yml`:
   - `sources.raw` 14 bảng, `loaded_at_field: _ingested_at`, `freshness: {warn_after: 3 day,
     error_after: 14 day}` — lý do (ghi trong file + đây): dataset lịch sử tĩnh (2012–2022),
     ingest hiện chạy THỦ CÔNG (chưa có scheduler ở milestone này), nên freshness là canary vận
     hành ("pipeline có bị bỏ quên không") chứ không đo độ trễ nguồn thời gian thực. Ngưỡng theo
     nhịp dev quan sát thật ở M2 (nhiều lần re-ingest/ngày).
   - Contract columns (name + `data_type`) cho cả 14 model, khớp 100% thứ tự/kiểu SELECT.
   - Tests: `not_null`/`unique` cho khoá chính từng bảng; `relationships` cho 15 quan hệ FK
     (khớp đúng danh sách RI sạch trong phase0_qc mục 5); `dbt_utils.unique_combination_of_columns`
     cho 2 bảng grain ghép (`stg_inventory`: snapshot_date+product_id; `stg_order_items`:
     order_id+product_id+line_number); `accepted_values` cho `order_status` (6 giá trị) và
     `rating` (1–5, có `quote: false` — bug thật gặp lúc verify, xem mục Bug bên dưới).
   - Cú pháp test dùng `arguments:` lồng bên trong (chuẩn dbt-core 1.10, thay `to:`/`field:`
     đặt trực tiếp — dbt 1.8 cũ chấp nhận cả hai nhưng 1.10 cảnh báo deprecate, đã sửa hết 19
     chỗ để build sạch tuyệt đối, không còn deprecation warning nào ở lần chạy cuối).

## Bug tìm & sửa lúc verify (ghi lại để không lặp)

1. **dbt-trino 1.8.0 pin lỏng lẻo kéo dbt-core 1.12.0** (mismatch adapter/core) — xem mục 1 ở
   trên. Fix: bump + pin cứng cả hai (1.10.3/1.10.22).
2. **`accepted_values` trên cột `bigint` vs list số nguyên** → Trino lỗi
   `TYPE_MISMATCH ... Cannot find common type between bigint and varchar(1)` (macro mặc định
   quote giá trị thành chuỗi). Fix: `quote: false` trong `arguments` của test
   `accepted_values_stg_reviews_rating`.
3. **[Quan trọng] Schema bị nhân đôi `staging_staging`** — set `+schema: staging` trong
   `dbt_project.yml` **CỘNG THÊM** `schema: staging` mặc định trong `profiles.yml` khiến dbt
   macro mặc định `generate_schema_name` nối `<default_schema>_<custom_schema>` =
   `staging_staging` (hành vi mặc định chuẩn của dbt khi có custom schema ở env không phải
   "prod" — không phải bug của mình, là gotcha kinh điển của dbt). Phát hiện khi query Trino
   trực tiếp thấy `SHOW SCHEMAS FROM iceberg` ra `staging_staging` thay vì `staging`. Fix: bỏ
   `+schema:` khỏi `dbt_project.yml`, chỉ giữ 1 nguồn sự thật (`profiles.yml` default schema).
   Đã `DROP SCHEMA iceberg.staging_staging CASCADE` dọn rác trước khi build lại.
4. **19 deprecation warning `MissingArgumentsPropertyInGenericTestDeprecation`** (không phải
   lỗi, nhưng dọn sạch cho build thật xanh 100%, 0 warning) — dbt-core 1.10 đổi cú pháp generic
   test config sang lồng trong `arguments:`. Sửa hết `relationships`/`accepted_values`/
   `dbt_utils.unique_combination_of_columns` (19 chỗ, đúng số lượng cảnh báo).

## Verify (chạy thật, log thật — không suy đoán)

**1. `dbt debug`** → `Connection test: OK connection ok`, `All checks passed!` (Trino
`localhost:8080`, catalog `iceberg`, schema `staging`).

**2. `dbt deps`** → `Installing dbt-labs/dbt_utils` ... `Installed from version 1.4.1`.

**3. `dbt build` (toàn bộ project — chỉ có staging, intermediate/marts còn rỗng nên tương
đương `--select path:models/staging`)**:
```
Finished running 60 data tests, 14 view models in 0 hours 0 minutes and 7.62 seconds (7.62s).
Completed successfully
Done. PASS=74 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=74
```
14/14 model pass (tất cả view, contract enforced). 60/60 test pass (not_null/unique/
relationships/accepted_values/dbt_utils.unique_combination_of_columns). 0 deprecation warning
ở lần chạy cuối.

**4. `dbt source freshness`**:
```
Finished running 14 sources in 0 hours 0 minutes and 2.14 seconds (2.14s).
```
14/14 `PASS` (mọi bảng raw vừa ingest gần đây trong M2 — trong ngưỡng warn 3 ngày).

**5. Contract enforcement — verify THẬT bắt lỗi (không chỉ khai báo)**: cố ý sửa
`stg_customers.customer_id` yml từ `bigint` → `integer`, chạy `dbt run -s stg_customers`:
```
This model has an enforced contract that failed.
| column_name | definition_type | contract_type | mismatch_reason    |
| customer_id | BIGINT          | INTEGER       | data type mismatch |
Done. PASS=0 WARN=0 ERROR=1 SKIP=0 NO-OP=0 TOTAL=1
```
Revert lại `bigint` → `dbt build` xanh lại 74/74. Xác nhận contract THẬT SỰ enforce, không
phải khai báo suông.

**6. Đối chiếu row count `stg_*` vs `raw.*` qua Trino trực tiếp** (không qua dbt, độc lập):
```
stg_customers    121930   raw_customers    121930   (khớp)
stg_order_items  714669   raw_order_items  714669   (khớp)
stg_sales        3833     raw_sales        3833     (khớp)
stg_promotions_all_categories = 40  (khớp "40/50 thiếu 80%" phase0_qc W10)
```

**7. Secret check**: `grep` giá trị `.env` thật trong toàn bộ file mới tạo → 0 kết quả.
`profiles.yml` chỉ dùng `env_var()`, không hardcode.

## DoD tự check

- [x] `dbt build` xanh — contract enforced pass (74/74, 0 error, 0 warn).
- [x] `dbt source freshness` chạy được — 14/14 PASS, ngưỡng + lý do ghi rõ trong schema.yml.
- [x] Contract enforcement verify THẬT (test âm — sửa sai kiểu → fail đúng, revert → xanh lại).
- [x] Không sửa raw (`iceberg.raw.*` không đụng — chỉ SELECT từ source; namespace ghi ra là
      `staging`, khác hoàn toàn `raw`).
- [x] Rule làm sạch có nguồn trích dẫn cụ thể (`phase0_qc_report.md` W7/W10/I7), không bịa.
- [x] 0 secret trong file mới.
- [x] KHÔNG đụng `models/intermediate`, `models/marts` (còn `.gitkeep`, chưa tạo file nào).
- [x] KHÔNG đụng file của M5/M6a/M6b đang chạy song song trong cùng working tree (Makefile,
      tests/*, data/sample/*, .process_status/M6a.md, M6b.md — thấy qua `git status` nhưng
      không `git add`).
- [x] pyproject.toml/uv.lock: chỉ sửa đúng 1 chỗ (pin dbt-trino/dbt-core) theo đúng phạm vi
      task item 1 cho phép, có lý do bug thật kèm bằng chứng.

## Việc PO/milestone kế cần biết

- **Greenlight M3b** (da, `models/intermediate/*` + `models/marts/*`) — staging đã sẵn sàng,
  14 `stg_*` xanh, có thể `{{ ref('stg_x') }}`. M3b tự thêm block `intermediate:`/`marts:` vào
  `dbt_project.yml` khi bắt đầu (dbt_project.yml là file chung, sequential không race vì M3a đã
  xong trước).
- `dbt_datathon/logs/` và `dbt_datathon/.user.yml` hiện untracked (dbt tự sinh) — CHƯA có trong
  `.gitignore` (chỉ có `target/` + `dbt_packages/`). Không thuộc ownership M3a (`.gitignore` ở
  ngoài `dbt_datathon/`) nên không tự sửa — đề xuất PO/M0 bổ sung 2 dòng
  `dbt_datathon/logs/` + `dbt_datathon/.user.yml` vào `.gitignore` để tránh agent sau lỡ
  `git add` rác.
- `uv.lock` đã regenerate khớp pin mới (259 packages) — verify bằng chính `uv lock` resolve
  sạch; KHÔNG chạy `uv sync --frozen` full vào `.venv` chung (venv đang mix pip-installed
  packages từ session này, tránh xáo trộn môi trường M4a/M4b/M2 đang dùng chung — khuyến nghị
  ai đó chạy `uv sync` sạch 1 lần khi gộp wave, không khẩn cấp vì `.venv` hiện tại đã có đúng
  dbt-trino 1.10.3/dbt-core 1.10.22 cài thủ công khớp lock mới).

## Commit

`git add pyproject.toml uv.lock dbt_datathon/dbt_project.yml dbt_datathon/packages.yml
dbt_datathon/profiles.yml dbt_datathon/package-lock.yml dbt_datathon/models/schema.yml
dbt_datathon/models/staging/*.sql dbt_datathon/models/staging/.gitkeep` (deletion) — KHÔNG
`-A`, KHÔNG `PROCESS.md`, KHÔNG file của M5/M6a/M6b.

Conventional commit: `feat(dbt): staging models trên Trino/Iceberg — contract enforced, 14
bảng, source freshness, dbt-trino/dbt-core pin fix`.
