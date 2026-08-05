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
| M2 | de | M1 | ⬜ | | docker-compose.yml, infra/*, jobs/* | up healthy; ingest MERGE idempotent; audit row | ⟂ M4a/M4b/M7 |
| M3a | de | M2 | ⬜ | | dbt_project.yml, packages.yml, models/staging/*, schema.yml(sources+freshness+contract) | dbt build staging xanh | |
| M3b | da | **M3a** | ⬜ | | models/intermediate/*, models/marts/*, mart tests, exposures | mart build xanh; regression==phase1 | cần staging M3a |
| M4a | de | M1 | ⬜ | | src/datathon/{schema,ingestion,quality}.py | import OK; 10 chiều DQ đủ | ⟂ M4b |
| M4b | ds | M1 | ⬜ | | src/datathon/{features,models,backtest,submission}.py | import OK; regression forecast==baseline | ⟂ M4a |
| M5 | tester | M4a+M4b | ⬜ | | tests/*, ci.yml, data/sample | pytest xanh; CI pass; sample<1MB | ⟂ M6a/M6b |
| M6a | da | M4a+M4b | ⬜ | | notebooks/01_data_quality.ipynb, 02_eda.ipynb | execute sạch | ⟂ M6b/M5 |
| M6b | ds | M4a+M4b | ⬜ | | notebooks/03_forecasting_colab.ipynb | execute sạch (+Colab) | ⟂ M6a/M5 |
| M7 | ba | M1 | ⬜ | | data/README.md | 14 bảng tài liệu hóa | ⟂ M2/M4 |

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
- (PO ghi tiếp mỗi lần duyệt...)

---

## Blocker log

| Ngày | M | Ai | Vấn đề | Trạng thái |
|---|---|---|---|---|
| | | | | |
