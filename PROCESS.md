# PROCESS — Restructure Lakehouse (D1=C)

Nhánh: `chore/restructure-lakehouse`. Nguồn sự thật DUY NHẤT cho restructure.
Chi tiết việc: `RESTRUCTURE_AGENTS.md`. Kế hoạch: `RESTRUCTURE_PLAN.md`.

**Luật cập nhật:** mỗi agent chạy xong milestone của mình → tự sửa row tương ứng bảng dưới (status, commit, file output, DoD, ghi chú). KHÔNG sửa row người khác. PO đọc bảng này để duyệt + phát milestone kế.

Status: ⬜ pending · 🟡 running · ✅ done · ❌ blocked

---

## Bảng milestone

| M | Agent | Phụ thuộc | Status | Commit | File output chính | DoD tự check | Ghi chú / blocker |
|---|---|---|---|---|---|---|---|
| M0 | pm | — | ✅ | 79e32f7 | scaffold tree, pyproject.toml, uv.lock, Makefile, README.md, LICENSE, .env.example, .gitignore, docs/{analysis,brief,orchestrator_prompt.md,PROGRESS.md} | tree khớp target 100% node; `import datathon` OK (verify qua `python3 -c "import sys;sys.path.insert(0,'src');import datathon"`); docs/analysis 128/128 file, docs/brief 2/2 file (0 mất) | uv cài được (`pip install uv` OK) → `uv lock` thành công, 270 packages, `uv.lock` 8047 dòng. Không cần fallback requirements.lock. Không move data, không port code (đúng scope M0). |
| M1 | de | M0 | ✅ | ee63d2b | data/raw/*.csv (14, untracked), src/datathon/config.py, data/raw/.gitkeep | đọc sales qua config OK (shape (3833,3)); `git rm --cached` xong, đĩa còn 14 CSV; RAW_TABLES 1 nguồn path | 6 file docs/analysis còn hardcode `data/` path — archive cũ, KHÔNG sửa (đúng scope). ⚠ commit sau sẽ làm CSV biến khỏi repo, clone mới không có data — M7 phải ghi cách lấy. |
| M2 | de | M1 | ✅ | a57f7ed (+e470cd4) | docker-compose.yml, infra/*, jobs/* | **PO LIVE-VERIFY** (container up thật, query Trino trực tiếp): count khớp CSV 100%; PO tự re-ingest promotions 50→50 idempotent; audit SUCCESS; quarantine=3; hidden partition month(order_date) v2; catalog Postgres iceberg_tables; 0 secret; version pinned | spark gap ĐÓNG ở e470cd4 (iceberg-aws-bundle, pyspark đọc REST catalog OK). Trino MERGE ON dùng `=` (null key đã lọc quarantine). Report .process_status/M2.md |
| M3a | de | M2 | ✅ | d1271d9 | dbt_project.yml, packages.yml, models/staging/* (14), schema.yml(sources+freshness+contract) | dbt build 74/74 PASS (14 view+60 test); source freshness 14/14 PASS; contract enforcement verify THẬT (test âm: sai kiểu→fail, revert→xanh); row count stg_*=raw.* 100% khớp | pin dbt-trino==1.10.3+dbt-core==1.10.22 (bug: 1.8.0 kéo core 1.12.0 lệch). Report .process_status/M3a.md |
| M3b | da | M3a | ✅ | e537485 | models/intermediate/{int_daily_revenue,int_rfm,int_cohort}.sql, models/marts/{mart_revenue_daily,mart_customer_segments,mart_channel_perf}.sql, tests/reconcile_gross_vs_net_revenue.sql, schema.yml(append) | dbt build 114/114 PASS (20 model+94 test) 4 lần liên tiếp không flaky; source freshness 14/14; incremental idempotent (Trino count không đổi, 0 trùng khóa); 0 đụng staging | RFM Champions khớp tuyệt đối, 4/9 segment lệch ±2/88,123 (ntile vs qcut, đã giải thích). PO tự recompute độc lập gross/net/RFM/cohort qua Trino khớp 100%. Report .process_status/M3b.md |
| M4a | de | M1 | ✅ | b3b85cf | src/datathon/{schema,ingestion,quality}.py | import OK; 10/10 hàm DQ đủ; run_all 14 bảng; sales↔order_items MAPE 0.000%; order_items surrogate line_id | severity map đúng (1/3/9=fail,2/4/6/8=quar,5/7=warn). Report .process_status/M4a.md |
| M4b | ds | M1 | ✅ | f4036f9 | src/datathon/{features,models,backtest,submission}.py | import OK; **REGRESSION forecast_548 BYTE-IDENTICAL baseline (PO verify thật)**; backtest metric khớp; no-leakage (đệ quy 548) | ⚠ nguồn port từ nhánh feat/phase8-model (phase8/9 CHƯA có ở docs/analysis nhánh này) — PO cân nhắc cherry-pick để audit lâu dài. Report .process_status/M4b.md |
| M5 | tester | M4a+M4b | ✅ | fe4b455 | tests/{conftest,test_schema,test_features_no_leakage,test_backtest,test_submission}.py, .github/workflows/ci.yml, data/sample (14 CSV) | pytest **52 passed, 1 xfailed**; sample 640K<1MB deterministic (shasum khớp 2 lần chạy); CI push/PR không cần docker | 2 finding tech-debt báo M4 (không tự sửa src): (1) `lookup_lag` fallback `hist.mean()` look-ahead nhẹ ~9.4% dòng train đầu (2012-2013); (2) `validate_submission` lộ `KeyError` thô thay vì `AssertionError` khi cột sai. Report .process_status/M5.md |
| M6a | da | M4a+M4b | ✅ | 64933e9 | notebooks/01_data_quality.ipynb, 02_eda.ipynb | execute sạch (0/17 + 0/25 cell error); DQ 177 PASS/21 WARN/1 FAIL(expected)/reconcile MAPE 0.000%; EDA sanity lệch 0.000% | đọc raw CSV qua config (M3a mart chưa xong lúc chạy) — TODO nối mart ghi rõ trong notebook. Report .process_status/M6a.md |
| M6b | ds | M4a+M4b | ✅ | 604cb48 | notebooks/03_forecasting_colab.ipynb | execute sạch (0/31 cell error, Colab-ready bootstrap); model vượt baseline B1 (Revenue -9.8%, COGS -14.3%); REGRESSION forecast_548 byte-identical (max diff=0.0) | ⚠ Colab bootstrap CHƯA test trên Colab thật (chỉ local); regression phụ thuộc `git show f4bc6a4` từ feat/phase8-model — nếu nhánh đó mất, cell fail (không phải model sai). Report .process_status/M6b.md |
| M8 | po | M0–M7 | 🟡 | 8999f1d | Makefile (fix `uv`/`pip`/`python` trần), .gitignore, data/README.md, PROCESS.md | AC1/AC2/AC3/AC4/AC7/AC8 PASS (xem log 2026-08-07 trước). **AC5 PASS**: PR #1 mở `chore/restructure-lakehouse` → `main` (https://github.com/lhoanghai1912/ML_Learning/pull/1), 32 commit, `gh` CLI cài+login xong | ❌ **CÒN LẠI: merge PR #1 vào main** (chờ review/PO bấm merge trên GitHub — merge strategy đã chốt = **merge commit**, KHÔNG squash/rebase khi bấm) |
| M7 | ba | M1 | ✅ | 3347521 (+2026-08-07 update) | data/README.md | 14 bảng tài liệu hóa (302 dòng); cột thật + grain/PK/FK; business fact GROSS/net/Monetary; coverage 2012–2022 | TODO "Cách lấy data" **đã điền** (PO cấp link Drive 2026-08-07). ⚠ folder KHÔNG public (probe → trang Sign-in) + chưa verify nội dung 14 CSV/checksum. Report .process_status/M7.md |

**Song song an toàn** (⟂ = disjoint file, chạy cùng lúc OK):
- Sau M1: `{M2, M4a, M4b, M7}` — 4 session riêng, khác file hoàn toàn.
- Sau M2: `M3a` → rồi `M3b` (tuần tự — marts cần staging).
- Sau M4a+M4b: `{M5, M6a, M6b}`.

## Protocol chạy SONG SONG (bắt buộc khi ⟂)

1. Mỗi sub-agent 1 session riêng, CHỈ đụng file trong ownership của mình (cột "File output"). CẤM sửa file ngoài ownership.
2. Commit CHỈ file của mình: `git add <own paths>` — KHÔNG `git add -A` / `git add .`.
3. **KHÔNG commit PROCESS.md** khi song song (tránh race). Thay: ghi report `.process_status/<M>.md` (file tạo, verify, blocker).
4. Xong → báo PO. **PO gộp**: đọc `.process_status/*.md`, verify tích hợp (import chung, regression, dbt build tổng) → PO tự cập nhật + commit các row PROCESS.md.
5. 2 sub-agent lỡ đụng cùng file → DỪNG, báo PO (ownership sai).

> Milestone 1-agent (M0/M1/M2/M7): agent tự cập nhật + commit row PROCESS.md của mình (không race).

---

## PO review checklist (chạy sau mỗi milestone)

- [ ] Status row = ✅ và có commit hash.
- [ ] File output chính tồn tại thật (không chỉ khai báo).
- [ ] DoD milestone đạt (xem "Gate hardening" + "10 chiều DQ" trong RESTRUCTURE_AGENTS.md).
- [ ] Không phá milestone trước (regression).
- [ ] Không leak secret / không commit key.
- [ ] Greenlight milestone kế theo cột "Phụ thuộc".

---

## Nhật ký PO / quyết định

- 2026-08-05: nhánh tạo từ main. D1=C, D2=A, D3=git rm --cached. Phase8 WIP parked trong stash.
- 2026-08-05: **M0 GATE = PASS** (verify PO). Tree khớp target, import OK, docs 128+2 preserved, data chưa move (đúng scope). Greenlight **M1** (de, single). Sau M1 → phát song song {M2, M4a, M4b, M7}.
- 2026-08-05: **M1 GATE = PASS** (verify PO). commit ee63d2b. 14 CSV ở data/raw/ (đĩa còn, git index=0, .gitignore chặn re-add). config.py đọc sales OK (3833,3), RAW_TABLES 14 bảng all exist, 1 nguồn path. No history rewrite. Sửa placeholder PENDING_COMMIT→ee63d2b. **Greenlight WAVE SONG SONG {M2, M4a, M4b, M7}** — 4 session riêng, disjoint file, KHÔNG commit PROCESS.md (ghi .process_status/<M>.md), PO gộp.
- 2026-08-05: **WAVE {M2,M4a,M4b,M7} GATE = PASS** (verify PO thật, không tin self-report). Bằng chứng PO tự chạy:
  - Ownership disjoint 100% (git show per-commit: M2=infra/jobs/compose/.env.example, M4a=schema/ingestion/quality, M4b=features/models/backtest/submission, M7=data/README.md — 0 chồng chéo).
  - Import tổng 8 module `src/datathon` cùng lúc OK (qua .venv; bare python3 fail do thiếu venv, KHÔNG phải bug; lunardate/lightgbm declared pyproject:15/20).
  - M4a: 10/10 hàm DQ present. M4b: **forecast_548 PO tự sinh = BYTE-IDENTICAL committed baseline** (diff -q khớp, 548 dòng). REGRESSION PASS.
  - M2: 0 hardcoded secret (git grep committed files), .env không tracked. M7: README 302 dòng, mục nguồn data=TODO.
  - PO gộp: commit M7 deliverable 3347521 + reports 2e496db (M7 agent để deliverable uncommitted, PO commit thay).
  - **2 việc PO còn nợ**: (1) cấp nguồn tải data raw → điền data/README.md mục 0 (M7 TODO). (2) quyết cherry-pick phase8/9 từ feat/phase8-model vào docs/analysis để M4b audit lâu dài (khuyến nghị: có, tránh mất nguồn nếu nhánh bị xoá).
  - **Greenlight kế**: M3a (de, dbt staging — cần M2 ✅, đã ✅) → xong mới M3b. Song song được: {M5, M6a, M6b} cần M4a+M4b (✅) — có thể phát NGAY cùng M3a. Đề xuất phát: M3a + {M5, M6a, M6b} = 4 session (M3a/M5 disjoint; M6a/M6b disjoint notebook).
- 2026-08-06: **M2 RE-CHECK = PASS (PO LIVE-VERIFY, không chỉ đọc report)**. Container đang chạy → PO query Trino trực tiếp: 6 service healthy; count sales/promo/order_items/orders khớp CSV 100%; PO TỰ re-ingest promotions 50→50 (MERGE idempotent, không nhân đôi); ops.ingest_audit SUCCESS; raw._quarantine_promotions=3; SHOW CREATE orders = month(order_date) v2; Postgres có iceberg_tables+iceberg_namespace_properties (không SQLite); 0 secret hardcode; version pinned. **Spark gap ĐÓNG** commit e470cd4 (de tự bổ iceberg-aws-bundle, pyspark đọc REST catalog verify OK). M2 hết gap.
- 2026-08-06: **Phát WAVE kế = {M3a, M5, M6a, M6b}** (4 session song song, disjoint file). Dependency đủ: M3a cần M2(✅); M5/M6a/M6b cần M4a+M4b(✅). M3b (marts) ĐỢI M3a xong (tuần tự). Ownership: M3a=dbt_datathon/{project,packages,models/staging,schema.yml sources}; M5=tests/*+.github/workflows/ci.yml+data/sample; M6a=notebooks/01+02; M6b=notebooks/03. KHÔNG commit PROCESS.md khi song song → .process_status/<M>.md, PO gộp.
- 2026-08-06: **WAVE {M3a,M5,M6a,M6b} GATE = PASS** (verify PO qua `git show --stat` từng commit + đọc report, không tin self-report suông). Ownership disjoint 100% xác nhận (M3a=dbt_datathon/+pyproject/uv.lock; M5=tests/+ci.yml+data/sample+Makefile 1 dòng; M6a=notebooks/01+02; M6b=notebooks/03 — 0 chồng chéo). Bằng chứng: M3a dbt build 74/74 PASS + contract test âm thật; M5 pytest 52 passed/1 xfailed + sample deterministic; M6a/M6b execute 0 lỗi qua nbformat count, DQ/EDA/forecast số liệu khớp M4a/M4b report cũ. Commit 4 row PROCESS.md + gitignore bổ sung `dbt_datathon/logs/`+`dbt_datathon/.user.yml` (theo đề xuất M3a report, tránh agent sau lỡ add rác).
  - **Greenlight M3b** (da, `models/intermediate/*`+`models/marts/*`, cần M3a ✅ — đã đủ điều kiện).
  - **2 việc nợ mới** (không chặn merge, track tech debt): (1) M4 sửa `lookup_lag` fallback mean look-ahead nhẹ + `validate_submission` KeyError thô (M5 finding). (2) Cherry-pick `phase8_model/`+`phase9_validation/` từ `feat/phase8-model` vào `docs/analysis` — M6b regression check đang phụ thuộc commit rời `f4bc6a4`, rủi ro mất nguồn đối chiếu nếu nhánh đó bị xoá (nhắc lại từ M4b, giờ thêm M6b phụ thuộc trực tiếp).
  - Việc nợ cũ vẫn còn: cấp nguồn tải data raw cho `data/README.md` (M7 TODO).
- 2026-08-06: **QUYẾT ĐỊNH tiến độ (RICE) — chạy M3b ngay, lịch 3 nợ song song không chặn**:
  - **M3b = P0, chạy ngay**: Reach=100% (mọi output A/B phụ thuộc mart cuối cùng), Impact=cao (đóng nốt bảng restructure, mở đường notebook 01/02 nối mart thay raw — đang là TODO của M6a), Confidence=cao (staging 14 bảng xanh, spec sẵn RESTRUCTURE_AGENTS.md), Effort=trung bình → RICE cao nhất còn lại. **Greenlight chạy da, single session** (không song song — không có milestone nào khác đang mở).
  - **Nợ #2 (cherry-pick phase8_model/phase9_validation) = ưu tiên nhì, làm TRƯỚC/song song M3b**: rủi ro mất nguồn đối chiếu regression tăng dần theo thời gian (nhánh `feat/phase8-model` có thể bị dọn/xoá bất cứ lúc nào, ngoài kiểm soát của PROCESS này) — effort thấp (copy/cherry-pick 2 thư mục vào `docs/analysis`), impact cao nếu xảy ra (M4b + M6b cả 2 đang phụ thuộc commit rời `f4bc6a4`). Giao **pm/ba**, disjoint file với M3b (`docs/analysis/phase8_model/`, `docs/analysis/phase9_validation/` — không đụng `dbt_datathon/`) → **có thể chạy CÙNG LÚC với M3b**.
  - **Nợ #1 (lookup_lag fallback mean + validate_submission KeyError) = P2, sau M3b**: effort thấp nhưng đụng `src/datathon/features.py`+`submission.py` (M4a/M4b sở hữu) — sửa xong phải chạy lại REGRESSION forecast_548 (rủi ro đổi số nếu fix đụng đường tính lag) + tests M5 đã có sẵn characterize (phải update/xoá `xfail` tương ứng). KHÔNG chặn M3b (khác file hoàn toàn), nhưng **không chạy song song với M3b/nợ#2** để tránh 3 luồng cùng lúc khó verify — xếp lịch SAU khi M3b xanh.
  - **Nợ #3 (nguồn tải data raw) = action item của PO**, không phải agent — chưa có nguồn thật để điền, giữ TODO, không chặn merge nào.
- 2026-08-06: **Nợ#2 ĐÓNG** (session ba báo ❌ BLOCKED trung thực — thiếu Bash tool trong session được cấp, không tự nhận vơ ✅; PO tự chạy tiếp theo phương án (b) ba đề xuất, dùng đúng kế hoạch/lệnh ba đã soạn sẵn không cần điều tra lại):
  - Copy 18 file `phase8_model/`+`phase9_validation/` từ `feat/phase8-model` → `docs/analysis/` — verify byte-identical qua `git hash-object` (18/18 OK, không suy đoán). Commit `5ef126e`.
  - Sửa cell `ac4a7e19` (`notebooks/03_forecasting_colab.ipynb`) bỏ fallback `git show f4bc6a4:...` → đọc thẳng path local, `assert` fail rõ nếu thiếu file. PO tự quyết + sửa luôn 3 chỗ text lỗi thời ba hỏi (mục 8 markdown, mục 9.6, mục 10 "PO nợ") — chỉ text mô tả, không đụng thuật toán, rủi ro thấp. Re-run `nbconvert --execute` full: 0/18 code cell lỗi, REGRESSION vẫn PASS byte-identical (max diff=0.0, khớp số cũ khi còn đọc qua git show). Commit `8bcb7fd`.
  - `.process_status/cherrypick_phase8_9.md` giữ nguyên làm bằng chứng lịch sử (không sửa lại thành ✅ giả — ba đúng là KHÔNG làm được phần thực thi, PO làm tiếp phần đó, minh bạch ai làm gì).
  - Rủi ro mất nguồn đối chiếu regression (M4b, M6b) **đã đóng** — hết phụ thuộc commit rời trên nhánh `feat/phase8-model`.
  - **Bài học điều phối**: session ba/pm không có Bash tool cho task cần shell (git show blob nhánh khác, nbconvert execute) — lần phát agent kế cần xác nhận trước session có tool phù hợp việc giao, tránh phát nhầm phải PO tự làm lại.
  - Còn lại: **Nợ #1** (lookup_lag/validate_submission, P2 sau M3b) + **Nợ #3** (nguồn data raw, PO action item) — chưa đổi.
- 2026-08-06: **M3b GATE = PASS (PO LIVE-VERIFY qua Trino trực tiếp, không tin self-report)**. Commit `e537485`. Bằng chứng PO tự chạy độc lập:
  - `SHOW TABLES iceberg.staging` = đúng 20 bảng (14 stg + 3 int + 3 mart).
  - PO tự chạy `dbt build` lại (lần 4 tính cả report) = PASS=114/114, 0 error, không flaky. `dbt source freshness` = 14/14 PASS.
  - Row count `int_daily_revenue/int_rfm/int_cohort` = 3833/88123/8001 — PO tự query khớp tuyệt đối report. PO build thêm 1 lần nữa, count KHÔNG đổi → idempotent xác nhận độc lập.
  - RFM 9 segment, cohort M1/M3/M6/M12 (3.0/2.9/3.0/2.9%), gross/net/gap (16.43 tỷ/14.23 tỷ/13.369%) — PO tự `GROUP BY`/recompute qua Trino, khớp tuyệt đối số report.
  - `git diff --stat` xác nhận `models/staging/*` = 0 thay đổi, `schema.yml` chỉ 214 dòng thêm/0 xoá — M3a không bị đụng.
  - **M3 (dbt) HOÀN TẤT hoàn toàn** (M3a+M3b) — hết gap tầng dbt.
  - **Việc kế cho M6a** (không chặn, TODO có sẵn trong `notebooks/02_eda.ipynb`): đổi cell đọc raw CSV → đọc mart qua Trino (`exposure notebook_02_eda` đã khai 4 model). Chưa greenlight session mới — để tuỳ PO lên lịch.
  - **8/8 milestone chính (M0-M7, tính M3=M3a+M3b) ✅.** Chỉ còn nợ #1 (P2) + nợ #3 (PO action item) + việc tuỳ chọn M6a nối mart.
- 2026-08-06: **CHECKPOINT — tạm dừng, tiếp tục sau.** Trạng thái tại điểm dừng (đọc mục này trước nếu mất ngữ cảnh):
  - Restructure lakehouse: **8/8 milestone chính ✅** (M0,M1,M2,M3a,M3b,M4a,M4b,M5,M6a,M6b,M7 — không còn milestone bảng nào ⬜).
  - HEAD hiện tại = `10f8295`. Không có việc đang dang dở nửa chừng (mọi commit đã verify PASS trước khi ghi).
  - **Việc còn treo, chưa làm — thứ tự ưu tiên gợi ý khi tiếp tục:**
    1. `CLAUDE.md` (file `/Users/lhoanghai_/Documents/Study/Dự án datathon2026/CLAUDE.md`) đang **modified, CHƯA commit** (rule "phân tích chi tiết mọi nội dung tạo ra" thêm ngày 2026-08-06) — `git diff CLAUDE.md` để xem lại, quyết commit hay bỏ.
    2. **Nợ #1** (P2): `src/datathon/features.py` (`lookup_lag`/`lookup_lag_smooth` fallback `hist.mean()` look-ahead nhẹ ~9.4% dòng train đầu) + `src/datathon/submission.py` (`validate_submission` lộ `KeyError` thô thay vì `AssertionError`) — giao M4 (de/ds), sửa xong PHẢI re-run REGRESSION forecast_548 (so byte-identical `docs/analysis/phase9_validation/committed_baseline/` nay đã có local, không cần `git show` nữa) + update test M5 (`tests/test_features_no_leakage.py`, `tests/test_submission.py` — xoá/update `xfail` tương ứng).
    3. **Nợ #3**: PO cấp nguồn tải data raw thật → điền `data/README.md` mục 0 (còn TODO từ M7, `.process_status/M7.md`).
    4. **Tuỳ chọn, không nợ**: M6a đổi `notebooks/02_eda.ipynb` từ đọc raw CSV sang đọc mart qua Trino (`exposure notebook_02_eda` đã khai sẵn 4 model trong `schema.yml` từ M3b) — TODO note sẵn trong notebook mục 0, không chặn gì.
  - **Không có milestone nào ⬜ pending trong bảng — restructure coi như xong phần khung.** Việc còn lại thuần là tech-debt/polish, làm khi có thời gian, không khẩn cấp.
- 2026-08-07: **PO AUDIT sau checkpoint — phát hiện 6 gap gate-level chưa ai ghi + đóng 2 gap.** Bằng chứng PO tự chạy trong phiên, không tin PROCESS.md cũ:
  - ✅ **DoD "Demo" (RESTRUCTURE_PLAN mục 7) LẦN ĐẦU verify qua ĐÚNG entrypoint chính thức**: `PYTHONPATH=src python -m datathon.submission` (= `make forecast`) EXIT=0, sinh `submission.csv` 549 dòng (548+header), `diff -q` với `docs/analysis/phase9_validation/committed_baseline/forecast_548.committed.csv` = **BYTE-IDENTICAL**. Trước đây regression chỉ verify qua script/notebook rời — nay chuỗi `config→features→models→submission` đã xác nhận qua đường demo thật.
  - ✅ Infra còn sống: 6/6 container healthy (up 45h) — trino, spark-iceberg, iceberg-rest, postgres, minio, cloudbeaver.
  - ✅ **G1 (nhánh chưa push) = ĐÓNG.** Lần check đầu phiên: `@{upstream}` = *"no upstream configured"*, `git branch -a` không có remote ref → 28 commit chỉ nằm local (rủi ro mất trắng). User push trong lúc phiên chạy; re-check sau `git fetch`: `origin/chore/restructure-lakehouse` = `d9379f6` = local HEAD, ahead/behind = **0/0**. Rủi ro mất-trắng đã hết.
  - ✅ **Nợ #3 (nguồn data raw) = ĐÓNG (nội dung đã verify).** PO cấp link Drive `1nLtCvUsczAQ9QB-hbBDh5_w6v-joRBaX` + tải bản thật về `~/Downloads/Dự án datathon2026`. Đã điền `data/README.md` mục 0 (chuẩn hoá bỏ tiền tố `/u/2/` — chỉ số tài khoản riêng của PO, người khác dùng không được). Bằng chứng verify PO tự chạy:
    - **14/14 CSV BYTE-IDENTICAL** với `data/raw/` đang dùng — `shasum -a 256 *.csv | sort` 2 bên, `diff` = rỗng. Data trên Drive = đúng data mọi kết quả repo đang dựa vào.
    - `tài liệu/data_dictionary.xlsx` checksum **khớp** `docs/brief/`.
    - ⚠→✅ `tài liệu/Đề bài1.docx` **khác byte** (Drive 439,557B mtime Jul 16 vs repo 266,318B mtime Jul 15) — thoạt nhìn giống "đề bài bản mới", **rủi ro cao nếu đúng**. PO đào sâu: giải nén cả 2 docx, trích text từ `word/document.xml`, strip tag → cả 2 đúng **3007 ký tự / 18 dòng, `diff` = 0 dòng khác**. Kết luận: **nội dung chữ GIỐNG HỆT**, khác byte do Google Docs re-export (nhúng font `NotoSansSymbols*.ttf`, `customXml`→`customXML`, bỏ `endnotes/footnotes`). **KHÔNG phải đề bài sửa đổi — không cần làm lại phân tích nào.** (Bài học: byte-diff trên file Office KHÔNG đủ kết luận nội dung đổi; phải trích text so.)
    - `EDA_Insight/{Hải,Hoàng,Đăng}/` trên Drive = 3 thư mục **RỖNG** — việc thật đã archive ở `docs/analysis/` (D2=A). Không có gì phải cứu.
    - `data/README.md` bổ sung bảng mapping Drive→repo (Drive để CSV **phẳng** ở `data/`, repo cần `data/raw/` — bê nguyên là sai chỗ) + lệnh copy + lệnh verify checksum.
    - 🟡 **Còn 1 ask**: folder Drive vẫn **không public** (probe `curl -sL` → `<title>Google Drive: Sign-in</title>`, người ngoài thấy "Request access"). Không chặn PO (PO có quyền), nhưng chặn người mới clone. → đổi share "Anyone with the link → Viewer" hoặc add email từng người.
  - ✅ Sửa luôn text lỗi thời trong `data/README.md`: mục `data/sample/` ghi "chưa tồn tại tại thời điểm M7" — sai từ khi M5 (`fe4b455`) tạo 14 CSV/640K. Đã sửa + ghi rõ hệ quả: clone sạch chạy được `make test` (sample) nhưng KHÔNG chạy được `make forecast` (cần full raw).
  - ❌ **G2 CÒN MỞ — chưa merge, chưa xác nhận PR.** `origin/main` = `d2f0d44`, so với nhánh = **0 ahead / 28 behind**. Success criteria PLAN mục 8 yêu cầu *"PR review pass"* → chưa đạt. Không kiểm được PR: **`gh` CLI chưa cài trên máy** (`command not found: gh`) → cần cài `gh` hoặc PO tự xác nhận trạng thái PR trên web.
  - 🟡 **G3 — metric `Repo size < 20MB` = MISS, ghi nhận chính thức.** Thực tế `.git` = **101MB** (`du -sh .git`). Nguyên nhân: D3 chốt chỉ `git rm --cached`, KHÔNG rewrite history → CSV cũ còn trong history. **Quyết định: WON'T FIX** (RICE 0.17 — rewrite history phá mọi clone + làm chết hash tham chiếu trong PROCESS.md, đổi lấy ~80MB không đáng). Bảng metric mục 1 `RESTRUCTURE_PLAN.md` phải đọc kèm ghi chú này, đừng coi là đạt hết.
  - 🟡 **G4 — `submission.csv` KHÔNG bị gitignore.** `git check-ignore -v submission.csv` = 0 match → ai lỡ `git add -A` sau `make forecast` là commit nhầm artifact 18KB. Chưa sửa (chờ gộp vào batch cleanup).
  - 🟢 **G5 — rác git**: worktree `prunable` trỏ `~/Downloads/Dự án datathon2026/.claude/worktrees/angry-roentgen-9f92d9` (path repo khác) + nhánh local thừa `claude/angry-roentgen-9f92d9`. Chưa dọn.
  - 🟢 **G6 — `CLAUDE.md` vẫn modified chưa commit** (rule "phân tích chi tiết", +6 dòng). Chưa quyết.
  - **Backlog RICE sau audit**: (A) mở public Drive = P0 blocked-on-PO · (B) cleanup G4/G5/G6 = RICE 30 · (C) M8 merge main = RICE 27 · (D) nợ #1 lookup_lag = RICE 2.8 · (E) M6a nối mart = RICE 1.6 · (F) rewrite history = 0.17 WON'T DO.
  - **Trade-off chốt**: merge M8 TRƯỚC, sửa nợ #1 ở PR riêng v1.1 — vì fix `lookup_lag` có thể đổi số forecast → phá regression byte-identical; trộn vào PR release sẽ không phân biệt được số đổi do fix hay do restructure.
  - **Chưa quyết (chờ PO)**: merge strategy — merge commit (giữ 28 commit, PROCESS.md tham chiếu hash cụ thể nên KHUYẾN NGHỊ) vs squash (log sạch nhưng mọi hash trong PROCESS.md thành hash chết).
- 2026-08-07: **PO CHỐT 3 quyết định + BATCH CLEANUP G4/G5/G6 xong.**
  - **Quyết định 1 — nguồn data**: PO cung cấp thêm bản đã tải sẵn `~/Downloads/Dự án datathon2026/` (chính là folder Drive giải nén). Ghi vào `data/README.md` kèm cảnh báo **machine-local, chỉ đúng máy PO** — máy khác vẫn phải tải từ link Drive. Verify không có chỗ nào hardcode: `git grep -n "Downloads" -- src/ jobs/ tests/ dbt_datathon/` = **0 hit**, code luôn đọc qua `src/datathon/config.py` (override `DATA_RAW_PATH`). Không mở public Drive → giữ nguyên ghi chú rủi ro cho người clone mới, PO chấp nhận.
  - **Quyết định 2 — merge strategy = MERGE COMMIT** (PO confirm, đúng khuyến nghị PO đề xuất). Lý do giữ: PROCESS.md tham chiếu ~10 hash cụ thể (`ee63d2b`, `a57f7ed`, `e470cd4`, `d1271d9`, `e537485`, `f4036f9`, `fe4b455`, `604cb48`, `64933e9`, `3347521`, `5ef126e`, `8bcb7fd`) — squash biến toàn bộ thành hash chết, mất khả năng audit từng gate. Đổi lại log `main` dài hơn: chấp nhận.
  - **Quyết định 3 — batch cleanup = CHẠY.** Kết quả:
    - **G4 ĐÓNG**: thêm `submission.csv` vào `.gitignore` (kèm comment: artifact của `make forecast`, bản chuẩn đối chiếu nằm ở `docs/analysis/phase9_validation/committed_baseline/`). Verify thật: `touch submission.csv && git check-ignore -v submission.csv` → match `.gitignore:24`. Hết rủi ro `git add -A` commit nhầm artifact.
    - **G5 ĐÓNG**: `git worktree prune -v` gỡ `angry-roentgen-9f92d9` (*"gitdir file points to non-existent location"* — path `~/Downloads/.../.claude/` đã bị bản tải Drive ghi đè, xác nhận `ls` = No such file). Xoá nhánh thừa `claude/angry-roentgen-9f92d9`. **An toàn có kiểm chứng TRƯỚC khi xoá**: `git log claude/angry-roentgen-9f92d9 --not main chore/restructure-lakehouse origin/main` = **rỗng** → 0 commit độc nhất; dùng `git branch -d` (safe) chứ không `-D` (force), git chấp nhận xoá `(was 8e1200c)`. Không mất việc.
    - **G6 ĐÓNG**: commit `CLAUDE.md` (rule "PHÂN TÍCH CHI TIẾT MỌI NỘI DUNG TẠO RA", +6 dòng) — rule đã áp dụng thực tế từ 2026-08-06, giờ mới vào git.
  - **Còn lại đúng 2 việc**: (a) **M8 merge vào main** (`origin/main` 28 behind — chờ mở PR, `gh` CLI chưa cài nên PO không tự kiểm/mở PR bằng CLI được). (b) **Nợ #1** `lookup_lag`/`validate_submission` — P2, làm ở PR riêng v1.1 SAU merge, để nếu số forecast đổi thì biết chắc do fix chứ không do restructure.
- 2026-08-07: **M8 SMOKE TEST CLONE SẠCH — bắt được BUG THẬT, DoD "Reproducible" trước đó là KHAI KHỐNG.**
  - **Cách làm**: `git clone --branch chore/restructure-lakehouse <repo> /tmp/smoke_m8` (clone thật, không phải chạy tại chỗ) → clone đúng như người mới: `data/raw/` chỉ có `.gitkeep`, `data/sample/` có đủ 14 file.
  - 🔴 **BUG PHÁT HIỆN — `make setup` CHẾT trên clone sạch**: `/bin/sh: pip: command not found` → `make: *** [setup] Error 127`. Chẩn đoán bằng lệnh, không đoán: máy có `python3`+`pip3` (`/opt/homebrew/bin`) nhưng **KHÔNG có `uv`, KHÔNG có `pip`, KHÔNG có `python`**. Makefile M0 viết `uv sync` else `pip install -e .` → uv mất (M0 từng cài, nay không còn), fallback `pip` trần cũng không tồn tại trên macOS/Homebrew hiện đại. **Hệ quả nghiêm trọng**: DoD `RESTRUCTURE_PLAN` mục 7 *"Reproducible: `make setup && make test` chạy từ clone sạch"* được đánh ✅ từ M0/M5 nhưng **CHƯA AI CHẠY THẬT TỪ CLONE SẠCH** — nếu merge thẳng, người clone đầu tiên sẽ dính lỗi ngay lệnh đầu. Cùng lớp lỗi còn ở `ingest`/`forecast`/`sample` (dùng `python` trần — **cũng không tồn tại**) và `dbt` (console script trần, `cd dbt_datathon` xong mất luôn venv).
  - ✅ **FIX Makefile** (19+/7-): thêm `PY := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)` và `DBT` tương tự dùng `$(CURDIR)` (chịu được `cd dbt_datathon`); `setup` khi không có uv thì `python3 -m venv .venv` + `pip install -e .` **trong venv** (tránh luôn lỗi PEP 668 externally-managed nếu cài thẳng vào Homebrew python); mọi target bỏ sạch `python`/`pip` trần.
  - ✅ **AC1 PASS (verify thật sau fix)**: `make setup && make test` trên clone sạch → `>> uv not found -> python3 -m venv .venv + pip install -e .`, `Python 3.14.6`, **`52 passed, 1 xfailed in 53.21s`** — khớp tuyệt đối baseline M5, dù chạy trên Python 3.14 + toàn bộ dependency bản mới nhất (không phải `.venv` cũ đã pin sẵn). Tín hiệu mạnh hơn dự kiến: code không phụ thuộc phiên bản lib đóng băng.
  - ✅ **AC2 PASS**: làm ĐÚNG hướng dẫn vừa viết trong `data/README.md` — `cp "~/Downloads/Dự án datathon2026/data/"*.csv data/raw/` (14 file, 126MB) → `make forecast` EXIT=0 → `diff` với `committed_baseline/forecast_548.committed.csv` = **BYTE-IDENTICAL**. Chứng minh 2 thứ cùng lúc: (1) chuỗi tái lập clone→setup→data→forecast chạy được trên môi trường trắng; (2) hướng dẫn README viết đúng, không phải lý thuyết.
  - ✅ **AC3 PASS**: sau `make forecast`, `git status --short` trong clone chỉ hiện file đang sửa — `submission.csv` **không lọt** (gitignore G4 hoạt động thật).
  - **Bài học điều phối (quan trọng)**: milestone tự đánh ✅ DoD "chạy từ clone sạch" mà **không ai thực sự clone** → lỗi ẩn 2 tuần, chỉ lộ ở gate release. Từ nay DoD có chữ "clone sạch" bắt buộc kèm bằng chứng `git clone` ra thư mục khác + output lệnh.
  - **Trạng thái M8**: AC1,2,3,4,7,8 PASS. **Còn AC5 (mở PR) + merge** — chờ PO cấp phép push (branch hiện 4 commit ahead origin) và cài `gh` hoặc tự mở PR trên web.
- 2026-08-07: **AC5 ĐÓNG — PR #1 mở.** Push commit `8999f1d` lên origin. Cài `gh` CLI (`brew install gh`, v2.97.0) + login web (`gh auth login`, account `lhoanghai1912`, scopes gist/read:org/repo/workflow) — xác nhận `gh auth status` = logged in. Tạo PR `chore/restructure-lakehouse` → `main`: https://github.com/lhoanghai1912/ML_Learning/pull/1 (32 commit, 271 file thay đổi, +42060/-2960779 — phần lớn xoá do CSV cũ/artifact không còn track). **Còn lại đúng 1 việc: bấm merge PR trên GitHub** (merge strategy đã chốt = merge commit, không squash — PROCESS.md tham chiếu hash cụ thể từng gate).
- (PO ghi tiếp mỗi lần duyệt...)

---

## Blocker log

| Ngày | M | Ai | Vấn đề | Trạng thái |
|---|---|---|---|---|
| | | | | |
