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
| M1 | de | M0 | ⬜ | | data→raw/, config.py, .gitkeep | đọc sales qua config OK; git rm --cached | |
| M2 | de | M1 | ⬜ | | docker-compose, infra/*, jobs/* | up healthy; ingest MERGE idempotent; audit row | |
| M3 | de+da | M2 | ⬜ | | dbt_datathon/* | dbt build + freshness xanh; contract enforced | |
| M4 | de+ds | M1 | ⬜ | | src/datathon/*.py (8 module) | import OK; regression forecast==baseline | |
| M5 | tester | M4 | ⬜ | | tests/*, ci.yml, data/sample | pytest xanh; CI pass; sample<1MB | |
| M6 | da+ds | M4 | ⬜ | | notebooks/01,02,03 | execute sạch qua nbclient | |
| M7 | ba | M1 | ⬜ | | data/README.md | 14 bảng tài liệu hóa | |

Song song: sau M1 → {M4, M7}. Sau M2 → M3. Sau M4 → {M5, M6}.

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
- (PO ghi tiếp mỗi lần duyệt...)

---

## Blocker log

| Ngày | M | Ai | Vấn đề | Trạng thái |
|---|---|---|---|---|
| | | | | |
