# PROJECT RULES — Vin Datathon 2026 (Lakehouse Restructure)

> File này Claude Code tự nạp mỗi session. OVERRIDE trí nhớ session. Đọc trước khi làm bất cứ gì.

## RULE 0 — PROCESS.md LÀ NGUỒN SỰ THẬT DUY NHẤT

- **LUÔN đọc `PROCESS.md` ĐẦU TIÊN** mỗi session/mỗi lần tiếp tục việc — KHÔNG dựa vào ngữ cảnh session (session có thể bị clear/mất token).
- **LUÔN cập nhật `PROCESS.md` NGAY sau khi xong 1 đơn vị việc** (không đợi cuối). Ghi: status, commit hash, file output, DoD tự check, ghi chú/blocker.
- Trạng thái, phụ thuộc, việc kế tiếp → LẤY TỪ `PROCESS.md`, không tự nhớ.
- Trước khi bắt đầu milestone: kiểm cột "Phụ thuộc" trong `PROCESS.md` = ✅ mới chạy. Chưa → dừng, báo.
- Chỉ sửa row milestone CỦA MÌNH. Không đụng row người khác.

## File điều phối (đọc theo thứ tự)

1. `PROCESS.md` — trạng thái + việc kế (nguồn sự thật).
2. `RESTRUCTURE_AGENTS.md` — chi tiết từng milestone M0–M7 + "DE HARDENING STANDARD" + "DATA QUALITY CHECK STANDARD" (10 chiều).
3. `RESTRUCTURE_PLAN.md` — vision, RICE, quyết định (D1=C, D2=A, D3).

## Bối cảnh dự án (cố định)

- E-commerce VN mô phỏng, 11 năm (2012–2022), 14 bảng raw + sample_submission.
- Phần A: dashboard/analysis. Phần B: forecast Revenue+COGS 548 ngày.
- Restructure: EDA-notebook → lakehouse (Spark+Iceberg+Trino+MinIO+Postgres+dbt), D1=C.
- Nhánh làm việc: `chore/restructure-lakehouse`. Việc cũ 11 phase archive ở `docs/analysis/`.

## Ràng buộc bắt buộc

- KHÔNG sửa data raw (`data/raw/` chỉ đọc).
- KHÔNG commit secret / key. Chỉ `.env` (gitignored) + `.env.example` placeholder.
- KHÔNG rewrite git history. KHÔNG push nếu user không yêu cầu. KHÔNG commit thẳng main.
- Conventional commits (`feat/fix/chore/refactor/docs`).
- Ingest: MERGE/append (không createOrReplace) + metadata cols + quarantine (không drop im).
- 10 chiều DQ + gate hardening (RESTRUCTURE_AGENTS.md) = điều kiện merge.
- REGRESSION: forecast_548 mới phải khớp committed baseline; số mart khớp phase cũ.
- Verify chạy được TRƯỚC khi ghi ✅ vào PROCESS.md.

## Vai trò agent

de (engineer/infra/ingest/dbt-staging) · da (analysis/marts/notebook) · ds (model/features/forecast) · ba (docs/data dictionary) · pm (scaffold/tooling/điều phối) · tester (tests/CI/QC).

## Khi mất ngữ cảnh / session mới

1. Đọc `PROCESS.md` → xác định milestone đang ở đâu, cái gì ✅/🟡/❌.
2. Đọc mục milestone tương ứng trong `RESTRUCTURE_AGENTS.md`.
3. Tiếp tục từ đó. KHÔNG làm lại việc đã ✅. KHÔNG đoán từ trí nhớ.
