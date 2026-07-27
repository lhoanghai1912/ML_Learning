# Phase 10 — Story A→B, Báo cáo cuối & Phân việc

Chủ trì: PM. Trạng thái: 🔄 in-progress (mở 2026-07-27, ngay sau khi Phase 9 GATE = GO).
Đầu vào: toàn bộ Phase 0–9 (xem `PROGRESS.md` — nguồn sự thật). Bản nộp Phần B đã sẵn sàng.

---

## 1. Mục tiêu

Gộp 10 phase kỹ thuật thành **1 câu chuyện business mạch lạc A→B** + báo cáo cuối + slide thi, và **nộp Phần B**. Không thêm phân tích/model mới — chỉ tổng hợp, kể chuyện, kiểm tra lần cuối.

## 2. Deliverable

| # | Deliverable | File/định dạng | Người chốt |
|---|---|---|---|
| D1 | Bản nộp Phần B | `phase9_validation/forecast_548_SUBMIT_crlf.csv` (đã sẵn, CRLF) | Hải |
| D2 | Báo cáo cuối (business, A→B) | `phase10_report/final_report.md` | Hải (gộp) |
| D3 | Slide thuyết trình | `phase10_report/slides.*` | Đăng |
| D4 | Câu chuyện Phần A (Descriptive→Prescriptive) | mục trong D2 + slide | Đăng |
| D5 | Câu chuyện Phần B (model→validation→rủi ro) | mục trong D2 + slide | Hoàng |

## 3. Story A→B — bộ khung (spine để kể, số lấy từ PROGRESS)

**A. Chuyện gì đã xảy ra (Descriptive):** doanh thu gãy cấu trúc 2019 (−38.6%), lợi nhuận giảm nhanh gấp 3 doanh thu. Streetwear = 79.9% doanh thu nhưng margin không cao nhất. Tết KHÔNG đồng nhất qua năm.

**A. Vì sao (Diagnostic):** break 2019 = **sụp khối lượng** (qty −40%, khách −28%), KHÔNG phải giá (ASP +2.4%)/mix/promo. Promo gây 47.9% dòng bán dưới giá vốn → 382 ngày lỗ gộp. ⚠️ Nguyên nhân gốc "vì sao khách rời đi" NẰM NGOÀI data giao dịch (đã loại trừ giá/mix/promo/kênh/vùng) — nói thẳng giới hạn.

**A. Ai giá trị nhất (Dashboard):** Pareto 25.6% khách (Champions) = 62.9% giá trị. West nhỏ nhất nhưng chất lượng khách tốt nhất. 🔴 Cohort retention PHẲNG ~3–6% → data khách sinh random, **không có hành vi quay lại thật**.

**A. Nên làm gì (Prescriptive):** (1) Floor price=cogs → margin +2.36pp, +0.462 tỷ VND/10 năm (quick win lớn nhất). (2) Win-back Champions/At-Risk (nhỏ, cần A/B test). (3) Nhân rộng pricing West (bài học vận hành). (4) KHÔNG giảm giá/tăng promo — đã chứng minh không phải vấn đề giá.

**🔗 Cầu nối A→B (mấu chốt — chấm điểm liên kết):** phát hiện cohort phẳng ở A ⇒ feature hành vi khách VÔ NGHĨA cho forecast ⇒ Phần B **chỉ dùng feature thuần lịch**. Target = **gross demand** (đối chứng MAPE 0.000% vs `sales.csv`). Mùa vụ/Tết/break-2019 từ A ⇒ thành feature `days_from_tet`, `is_post_2019`, `month`... 5 giả định G1–G5.

**B. Dự báo thế nào (Model):** baseline B1 seasonal naive thắng bất ngờ (WAPE 25.18/23.09) ⇒ chốt hướng lag mùa vụ. Model cuối = **LightGBM global + ensemble 50/50 với B1**, thêm `lag_365`. Vượt mốc: **Revenue 22.71%, COGS 19.79%**.

**B. Tin được không (Validation):** QA tính lại độc lập khớp, không leakage, byte-identical. Bản nộp fix CRLF sẵn. ⚠️ Rủi ro trung thực: leaf-cap `trend_index` (under-forecast nếu nền bật tăng vượt lịch sử); không có ground-truth 2023-24; sốc cấu trúc kiểu 2019 thì mọi model chịu.

## 4. Phân việc (ĐỀ XUẤT — team confirm/đổi)

> Giả định vai: Hải = lead (PM + tổng hợp), Đăng = phụ trách Phần A/analyst, Hoàng = phụ trách Phần B/model. **Confirm lại nếu sai.**

| ID | Task | Owner | Est | Dep | AC (điều kiện hoàn thành) |
|---|---|---|---|---|---|
| T10.1 | Viết câu chuyện Phần A (D4): 4 tầng + 4 đề xuất định lượng, chèn chart `output/phase1-4` | Đăng | 1.5d | P4 | Kể liền mạch what→why→who→action, mỗi đề xuất có con số + giả định |
| T10.2 | Viết câu chuyện Phần B (D5): baseline→model→validation→rủi ro, chèn chart `output/phase7-9` | Hoàng | 1.5d | P9 | Nêu rõ WAPE vượt mốc + 3 rủi ro trung thực + vì sao ensemble |
| T10.3 | Viết cầu nối A→B (mục 3, phần 🔗) — mấu chốt chấm điểm | Hải | 0.5d | T10.1, T10.2 | Chỉ rõ insight A NÀO → quyết định model B NÀO (cohort phẳng→calendar-only; target=gross) |
| T10.4 | Gộp `final_report.md` (D2): A + bridge + B, thống nhất số/giọng | Hải | 1d | T10.1-3 | 1 tài liệu, số khớp PROGRESS, không mâu thuẫn giữa các mục |
| T10.5 | Slide thi (D3): rút gọn từ D2, ≤15 slide, ưu tiên bridge + kết quả | Đăng | 1d | T10.4 | Có slide bridge A→B + slide WAPE + slide rủi ro |
| T10.6 | Nộp Phần B (D1): xác nhận nộp đúng `forecast_548_SUBMIT_crlf.csv`, check lại format lần cuối trên cổng nộp | Hải | 0.5d | P9 | Cổng nhận file, đúng 548 dòng, không lỗi parse |
| T10.7 | Dry-run thuyết trình + Q&A, rà số liệu lần cuối | cả 3 | 0.5d | T10.4, T10.5 | Mỗi người trả lời rõ phần mình, không vấp số |

Đường găng: (T10.1 ∥ T10.2) → T10.3 → T10.4 → T10.5 → T10.7. ~4 ngày lịch. T10.6 (nộp) làm được NGAY, không chờ báo cáo.

## 5. Checklist nộp Phần B (làm trước, gỡ rủi ro sớm)

- [x] 548 dòng, range 2023-01-01→2024-07-01, không thiếu/trùng ngày (P9 T9.1)
- [x] Cột `Date,Revenue,COGS` đúng thứ tự, 0 NaN, 0 âm, ≤2 số lẻ (P9 T9.1)
- [x] Line-ending CRLF khớp sample → dùng `forecast_548_SUBMIT_crlf.csv` (P9 fix)
- [ ] **Nộp thử lên cổng sớm** để lộ lỗi format ẩn (T10.6) — ưu tiên
- [ ] Xác nhận đề cho nộp lại/ghi đè hay 1 lần duy nhất

## 6. Rủi ro Phase 10

| Rủi ro | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Cổng nộp lỗi format ẩn (encoding/CRLF/tên file) | trung bình | **rất cao** | T10.6 nộp thử SỚM, không đợi phút chót |
| Bridge A→B kể yếu → mất điểm liên kết (tiêu chí lõi đề bài) | trung bình | cao | Hải viết riêng T10.3, review kỹ, đưa lên đầu slide |
| Số liệu 3 người lệch nhau khi gộp | trung bình | trung bình | T10.4 dùng PROGRESS làm nguồn số duy nhất |
| Bị hỏi rủi ro model, trả lời lảng | thấp | trung bình | T10.2 chuẩn bị sẵn: leaf-cap, no ground-truth, break-2019 |
| **Deadline chưa biết** | — | không đánh giá được | **PM cần team xác nhận ngày nộp NGAY** |

---

## Ghi chú PM

- Không có deadline datathon trong repo → chưa chốt được on-track. Cần xác nhận để xếp lịch T10.*.
- Bản nộp Phần B đã sẵn sàng kỹ thuật — nộp thử được ngay hôm nay, tách khỏi tiến độ viết báo cáo.
- Notebook phase1-7 còn 10 file modified unstaged (rerun output) + NOTEBOOKS.md — việc riêng, gộp commit "docs" sau, không chặn Phase 10.
