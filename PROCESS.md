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
| M3b | da | **M3a ✅** | ⬜ | | models/intermediate/*, models/marts/*, mart tests, exposures | mart build xanh; regression==phase1 | **GREENLIGHT** — staging sẵn sàng, có thể `{{ ref('stg_x') }}` |
| M4a | de | M1 | ✅ | b3b85cf | src/datathon/{schema,ingestion,quality}.py | import OK; 10/10 hàm DQ đủ; run_all 14 bảng; sales↔order_items MAPE 0.000%; order_items surrogate line_id | severity map đúng (1/3/9=fail,2/4/6/8=quar,5/7=warn). Report .process_status/M4a.md |
| M4b | ds | M1 | ✅ | f4036f9 | src/datathon/{features,models,backtest,submission}.py | import OK; **REGRESSION forecast_548 BYTE-IDENTICAL baseline (PO verify thật)**; backtest metric khớp; no-leakage (đệ quy 548) | ⚠ nguồn port từ nhánh feat/phase8-model (phase8/9 CHƯA có ở docs/analysis nhánh này) — PO cân nhắc cherry-pick để audit lâu dài. Report .process_status/M4b.md |
| M5 | tester | M4a+M4b | ✅ | fe4b455 | tests/{conftest,test_schema,test_features_no_leakage,test_backtest,test_submission}.py, .github/workflows/ci.yml, data/sample (14 CSV) | pytest **52 passed, 1 xfailed**; sample 640K<1MB deterministic (shasum khớp 2 lần chạy); CI push/PR không cần docker | 2 finding tech-debt báo M4 (không tự sửa src): (1) `lookup_lag` fallback `hist.mean()` look-ahead nhẹ ~9.4% dòng train đầu (2012-2013); (2) `validate_submission` lộ `KeyError` thô thay vì `AssertionError` khi cột sai. Report .process_status/M5.md |
| M6a | da | M4a+M4b | ✅ | 64933e9 | notebooks/01_data_quality.ipynb, 02_eda.ipynb | execute sạch (0/17 + 0/25 cell error); DQ 177 PASS/21 WARN/1 FAIL(expected)/reconcile MAPE 0.000%; EDA sanity lệch 0.000% | đọc raw CSV qua config (M3a mart chưa xong lúc chạy) — TODO nối mart ghi rõ trong notebook. Report .process_status/M6a.md |
| M6b | ds | M4a+M4b | ✅ | 604cb48 | notebooks/03_forecasting_colab.ipynb | execute sạch (0/31 cell error, Colab-ready bootstrap); model vượt baseline B1 (Revenue -9.8%, COGS -14.3%); REGRESSION forecast_548 byte-identical (max diff=0.0) | ⚠ Colab bootstrap CHƯA test trên Colab thật (chỉ local); regression phụ thuộc `git show f4bc6a4` từ feat/phase8-model — nếu nhánh đó mất, cell fail (không phải model sai). Report .process_status/M6b.md |
| M7 | ba | M1 | ✅ | 3347521 | data/README.md | 14 bảng tài liệu hóa (302 dòng); cột thật + grain/PK/FK; business fact GROSS/net/Monetary; coverage 2012–2022 | ⚠ mục "Cách lấy data" = TODO — **cần PO cấp nguồn tải data raw**. Report .process_status/M7.md |

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
- (PO ghi tiếp mỗi lần duyệt...)

---

## Blocker log

| Ngày | M | Ai | Vấn đề | Trạng thái |
|---|---|---|---|---|
| | | | | |
