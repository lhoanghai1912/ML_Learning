# BA Action Spec — Giai đoạn 4 (Prescriptive) + Giai đoạn 5 (Model Assumptions)
## Vin Datathon 2026 — Input cho Giai đoạn 10 (pm)

Ngày viết: 2026-07-21 · Vai trò: BA · Không tính lại số — mọi số trích từ `phase4_prescriptive/prescriptive_analysis.md` và `phase5_model_assumptions/model_assumptions.md` (đối chiếu thêm `phase2_diagnostic/diagnostic_summary.md`, `phase3_dashboard/dashboard_rfm_cohort.md`, `phase3_dashboard/customer_demographics.md`).

---

## Phần 1 — Tóm tắt điều hành

**Câu chuyện xuyên suốt A→B:** Break 2019 (Revenue −38,6%) là do **khối lượng giao dịch sụp đổ** (số đơn/khách active giảm 28-40%), **không phải do giá** (ASP +2,4%, AOV +2,7% — cả hai còn tăng) — *diagnostic_summary.md mục 2.1, Kết luận Q1*. Vì vậy đề xuất hành động (Phần A) **không đi theo hướng giảm giá thêm**, mà tập trung **bảo toàn margin đã có** (floor price, nhân rộng cách định giá West) và **acquisition/retention có mục tiêu** (ưu tiên vùng West, bảo vệ Champions) — *prescriptive_analysis.md Đề xuất 1-4*. Model dự báo (Phần B) đi đúng mạch này: mã hoá break 2019 bằng biến chỉ báo giai đoạn (không giả định giá là driver), dùng feature lịch (tháng/Tết) thay vì feature giá/khuyến mãi tương lai (không có thật, sẽ leak), và **bỏ hẳn feature hành vi khách hàng lặp lại** vì phát hiện retention phẳng bất thường (nghi ngờ dữ liệu mô phỏng random) — *model_assumptions.md G1-G4, Nhiệm vụ 3*.

**Top 3 hành động ưu tiên cao nhất:**
1. **A1 — Áp floor price = giá vốn**: chặn hoàn toàn bán dưới giá vốn, quick-win margin lớn nhất, dễ triển khai nhất trong 4 đề xuất.
2. **A7 — Bảo vệ Champions (loyalty/VIP)** trước khi mở rộng khách mới: Champions tạo 62,9% giá trị (8,95 tỷ VND), giữ rẻ hơn tìm khách mới tương đương.
3. **G4/Nhiệm vụ 3 sign-off (Phần 3)** — chốt ngay: KHÔNG dùng feature promo tương lai (leakage) và KHÔNG dùng feature hành vi khách lặp lại (retention phẳng, nghi dữ liệu random) — chặn sai hướng trước khi Giai đoạn 6 bắt đầu code.

---

## Phần 2 — Backlog hành động đã ưu tiên

### A1 — Floor price = giá vốn cho mọi promotion

| | |
|---|---|
| **Vấn đề kinh doanh** | 18,62% dòng `order_items` lịch sử bán dưới giá vốn; riêng dòng CÓ promo tỷ lệ dưới giá vốn 47,9% vs 0,18% dòng KHÔNG promo (chênh 266 lần) — tập trung T7-9 (`Urban Blowout`, `Fall Launch`) và T11-12 (`Year-End Sale`), nặng nhất Casual/Streetwear. *Nguồn: `diagnostic_summary.md` mục 2.2; `prescriptive_analysis.md` Đề xuất 1 phần Vấn đề.* |
| **Hành động đề xuất** | Đội pricing đặt `unit_price_floor = max(unit_price, cogs)` theo từng SKU trong engine tính giá sau khuyến mãi — không cho bất kỳ dòng hàng nào xuống dưới giá vốn, kể cả giảm % sâu hay giảm cứng. Review ưu tiên 2 category Casual/Streetwear, 2 giai đoạn T7-9/T11-12. |
| **Tác động kỳ vọng** | Mô phỏng lịch sử: margin toàn shop 13,80% → 16,15% (+2,36 điểm %), +0,462 tỷ VND margin toàn kỳ 10 năm (~46 triệu/năm). **CẢNH BÁO:** đây là **cận trên lý thuyết** — giả định KHÔNG có co giãn cầu theo giá (giữ nguyên số lượng bán dù giá tăng); thực tế con số sẽ thấp hơn. *Nguồn: `prescriptive_analysis.md` Đề xuất 1, bảng ước tính + mục Rủi ro.* |
| **Công sức ước lượng** | **S** — chỉ cần đặt ngưỡng logic giá, không cần dữ liệu ngoài (đánh giá theo `prescriptive_analysis.md` Khuyến nghị Giai đoạn 10 #2). |
| **Bên phụ trách** | Pricing/promo engineering. |
| **Phụ thuộc/điều kiện tiên quyết** | Cần catalog `cogs` cập nhật đúng theo SKU (đã có sẵn trong data). Không phụ thuộc đề xuất khác. |
| **Tiêu chí chấp nhận** | Sau triển khai: 0% dòng order_items có `unit_price < cogs`; theo dõi margin % hàng tháng có tăng theo hướng mô phỏng không (không kỳ vọng khớp chính xác +2,36pp do giả định elasticity); theo dõi song song `quantity` bán ra có giảm bất thường không (kiểm tra giả định "không co giãn cầu"). |
| **Cần ký duyệt?** | **Có** — duyệt chính sách giá sàn cứng (không có ngoại lệ campaign lớn) trước khi go-live, vì ảnh hưởng trực tiếp khả năng chạy các promo giảm giá sâu hiện tại (`Urban Blowout`...). |
| **Mức ưu tiên** | **P0** — tác động định lượng lớn nhất, effort thấp nhất, không phụ thuộc dữ liệu ngoài. |

### A2 — Win-back pilot: "Can't Lose Them" (RFM segment)

| | |
|---|---|
| **Vấn đề kinh doanh** | 2.251 khách "Can't Lose Them", Monetary TB/khách 218.601 VND (cao thứ 2 toàn bộ segment), im lặng TB 1.783 ngày, từng mua TB 8,61 đơn — ROI/khách cao nhất trong nhóm rủi ro. *Nguồn: `dashboard_rfm_cohort.md` bảng segment mục RFM; `prescriptive_analysis.md` Đề xuất 2 phần Vấn đề.* |
| **Hành động đề xuất** | Marketing chạy campaign win-back cá nhân hoá (gọi điện/email + voucher) cho nhóm này trước, theo đúng khuyến nghị `dashboard_rfm_cohort.md` mục 5.2. |
| **Tác động kỳ vọng** | Kịch bản +5/10/15pp tỷ lệ quay lại: +2,9 / +5,7 / +8,6 triệu VND (1 đơn quay lại/khách, AOV 25.393 VND). **CẢNH BÁO:** đây là **kịch bản minh hoạ, không phải dự báo** — tỷ lệ +5/10/15pp KHÔNG suy ra từ dữ liệu thật, cần A/B test; số chưa trừ chi phí campaign (voucher, nhân sự). *Nguồn: `prescriptive_analysis.md` Đề xuất 2, bảng kịch bản + mục Rủi ro.* |
| **Công sức ước lượng** | **M** — cần thiết kế campaign + cơ chế đo lường (A/B test), không chỉ gửi voucher đại trà. |
| **Bên phụ trách** | Marketing/CRM. |
| **Phụ thuộc/điều kiện tiên quyết** | Cần ngân sách campaign (voucher/nhân sự) — hiện chưa có dữ liệu chi phí để tính ROI ròng; cần thiết kế nhóm treatment/control trước khi chạy đại trà. |
| **Tiêu chí chấp nhận** | Chạy pilot trên 1 phần nhóm "Can't Lose Them" với nhóm control song song; đo tỷ lệ quay lại thực tế (đơn hàng mới trong 30-60-90 ngày sau campaign) so với control; nếu tỷ lệ uplift dương và có ý nghĩa → cho phép scale ngân sách. |
| **Cần ký duyệt?** | **Có** — duyệt ngân sách voucher/campaign + thiết kế A/B test trước khi chạy. |
| **Mức ưu tiên** | **P1** — ROI/khách tốt nhất trong nhóm rủi ro nhưng tổng $ tuyệt đối nhỏ, cần A/B test thật trước khi tin số. |

### A3 — Win-back scale: "At Risk" (sau A2)

| | |
|---|---|
| **Vấn đề kinh doanh** | 7.989 khách "At Risk", Monetary TB/khách 80.882 VND (thấp hơn Can't Lose Them), im lặng TB 2.010 ngày — quy mô lớn hơn Can't Lose Them 3,5 lần. *Nguồn: `dashboard_rfm_cohort.md` bảng segment.* |
| **Hành động đề xuất** | Sau khi có kết quả A/B test từ A2, mở rộng cơ chế win-back tương tự sang "At Risk" nếu ngân sách cho phép — ưu tiên thấp hơn Can't Lose Them do ROI/khách thấp hơn nhưng tổng tiềm năng lớn hơn. |
| **Tác động kỳ vọng** | Kịch bản +5/10/15pp: +8,3 / +16,6 / +24,9 triệu VND. **CẢNH BÁO:** cùng giới hạn như A2 (kịch bản minh hoạ, chưa trừ chi phí). *Nguồn: `prescriptive_analysis.md` Đề xuất 2.* |
| **Công sức ước lượng** | **M** — tái dùng cơ chế A2, quy mô lớn hơn. |
| **Bên phụ trách** | Marketing/CRM. |
| **Phụ thuộc/điều kiện tiên quyết** | **Phụ thuộc A2** — chỉ scale khi có bằng chứng A/B test dương từ Can't Lose Them; cần ngân sách lớn hơn 3,5 lần. |
| **Tiêu chí chấp nhận** | Tương tự A2: đo tỷ lệ quay lại thực tế so với control; quyết định ngân sách dựa trên so sánh ROI/khách 2 nhóm (không chỉ nhìn tổng tiềm năng $). |
| **Cần ký duyệt?** | **Có** — duyệt sau khi có kết quả A2, so sánh phân bổ ngân sách 2 nhóm. |
| **Mức ưu tiên** | **P2** — tuần tự sau A2, chưa nên chạy song song vì cùng nguồn ngân sách win-back. |

### A4 — Khảo sát vận hành pricing West (định tính)

| | |
|---|---|
| **Vấn đề kinh doanh** | Margin West 14,20% vs Central 13,15%/East 13,31%; Phase 2 tách được ~40% chênh lệch do mix sản phẩm, **~60% do giá/discount thực thi tốt hơn trong CÙNG category** — nhưng dữ liệu giao dịch không giải thích được "West làm gì khác". *Nguồn: `diagnostic_summary.md` mục 2.3 (Q3); `prescriptive_analysis.md` Đề xuất 3.* |
| **Hành động đề xuất** | Team pricing/ops phỏng vấn/khảo sát vận hành discount thực tế tại West (không có trong data) — trước khi thử nghiệm nhân rộng. |
| **Tác động kỳ vọng** | Không định lượng trực tiếp — là điều kiện tiên quyết để A5 khả thi. Giá trị là **học được cách vận hành**, không phải số $. |
| **Công sức ước lượng** | **M** — cần thời gian phỏng vấn/khảo sát thực địa, không phải phân tích số liệu. |
| **Bên phụ trách** | Pricing/Ops. |
| **Phụ thuộc/điều kiện tiên quyết** | Không phụ thuộc kỹ thuật, nhưng cần quyền tiếp cận đội vận hành West. |
| **Tiêu chí chấp nhận** | Có tài liệu mô tả cụ thể "West khác gì" (chính sách discount, tần suất, ngưỡng duyệt...) — đủ chi tiết để chuyển thành policy thử nghiệm ở A5. |
| **Cần ký duyệt?** | **Không** cần ký duyệt riêng, nhưng cần được ưu tiên thời gian từ ops. |
| **Mức ưu tiên** | **P2** — tiền đề của A5, giá trị tài chính trực tiếp nhỏ. |

### A5 — Thử nghiệm nhân rộng pricing West sang Central/East

| | |
|---|---|
| **Vấn đề kinh doanh** | (kế thừa A4) Gap margin lớn nhất ở Outdoor và Streetwear tại Central/East so với West. *Nguồn: `prescriptive_analysis.md` Đề xuất 3, bảng chi tiết theo category.* |
| **Hành động đề xuất** | Áp thử chính sách pricing/discount học được từ A4 sang Central/East, ưu tiên category Outdoor, Streetwear. |
| **Tác động kỳ vọng** | Mô phỏng: +38 triệu VND margin/10 năm toàn shop (margin 13,47% → 13,71%, +0,24 điểm %). **CẢNH BÁO:** hệ số 60% (mix vs giá) tính ở CẤP VÙNG, áp máy móc xuống cấp category là đơn giản hoá; con số **rất nhỏ (~3,8 triệu/năm)** — không phải đòn bẩy tài chính lớn, giá trị chính là định hướng. *Nguồn: `prescriptive_analysis.md` Đề xuất 3, bảng kết quả + mục Rủi ro.* |
| **Công sức ước lượng** | **L** — cần thay đổi policy pricing thực tế 2 vùng + đo lường trước/sau, rủi ro vận hành cao hơn A1 (đổi giá trên diện rộng nhiều vùng). |
| **Bên phụ trách** | Pricing. |
| **Phụ thuộc/điều kiện tiên quyết** | **Phụ thuộc A4** — không có tài liệu vận hành cụ thể thì không biết thử nghiệm gì. |
| **Tiêu chí chấp nhận** | Pilot 1 category (Outdoor hoặc Streetwear) tại 1 vùng trong thời gian xác định; so sánh margin % thực tế trước/sau so với mô phỏng +uplift kỳ vọng theo category đó (bảng chi tiết Đề xuất 3). |
| **Cần ký duyệt?** | **Có** — duyệt scope pilot (vùng/category/thời gian) vì thay đổi giá bán thực tế ảnh hưởng khách hàng. |
| **Mức ưu tiên** | **P2** — tác động tài chính nhỏ, effort lớn hơn A1 nhiều, giá trị chính là học tập vận hành. |

### A6 — Pilot dịch chuyển ngân sách acquisition sang vùng West

| | |
|---|---|
| **Vấn đề kinh doanh** | West nhỏ nhất về quy mô khách (14.741 khách) nhưng per-capita revenue cao hơn Central 62% (`customer_demographics.md` mục 7) VÀ tỷ trọng Champions cao nhất (36,1% vs Central 22,7%, East 24,1% — `dashboard_rfm_cohort.md`). Hai phương pháp độc lập cùng xác nhận chất lượng khách West tốt hơn. *Nguồn: `prescriptive_analysis.md` Đề xuất 4 điểm 1.* |
| **Hành động đề xuất** | Marketing chạy pilot nhỏ dịch chuyển 1 phần ngân sách acquisition từ Central/East sang West, đo chất lượng khách mới thu được (không cam kết ngân sách lớn ngay). |
| **Tác động kỳ vọng** | **KHÔNG có số $ ước tính** — thiếu dữ liệu marketing spend. Logic định tính: chi phí/khách chất lượng cao ở West có thể thấp hơn dựa trên 2 bằng chứng độc lập (per-capita revenue, % Champions). *Nguồn: `prescriptive_analysis.md` Đề xuất 4.* |
| **Công sức ước lượng** | **M** — cần thiết kế pilot đo lường (CAC, LTV sớm của khách mới theo vùng), không chỉ tăng ngân sách. |
| **Bên phụ trách** | Marketing. |
| **Phụ thuộc/điều kiện tiên quyết** | Nên chờ kết quả A8 (root-cause research) nếu có thể — tránh đầu tư dựa hoàn toàn trên suy đoán khi chưa hiểu tại sao khách sụt 2019. |
| **Tiêu chí chấp nhận** | Pilot chạy trong khung thời gian xác định (VD 1 quý); đo CAC và giá trị 90 ngày đầu của khách mới West so với Central/East cùng kỳ; quyết định scale dựa trên so sánh này, không dựa trên suy luận ban đầu. |
| **Cần ký duyệt?** | **Có** — duyệt ngân sách pilot + chỉ số đo lường thành công trước khi chạy. |
| **Mức ưu tiên** | **P1** — chưa kiểm chứng bằng thử nghiệm thực tế, cần pilot nhỏ trước khi cam kết lớn. |

### A7 — Chương trình loyalty/VIP bảo vệ Champions

| | |
|---|---|
| **Vấn đề kinh doanh** | Champions (22.575 khách, 25,6% tổng khách) tạo 62,9% giá trị (8,95 tỷ VND), đang hoạt động tốt (Recency TB 274 ngày, Frequency TB 15,88) — rủi ro chính là bị đối thủ lôi kéo, không phải churn tự nhiên. *Nguồn: `dashboard_rfm_cohort.md` bảng segment + mục Prescriptive.* |
| **Hành động đề xuất** | Marketing/CRM thiết kế chương trình loyalty/VIP (không phải giảm giá đại trà) cho Champions, ưu tiên TRƯỚC khi dồn ngân sách vào tân khách. |
| **Tác động kỳ vọng** | **KHÔNG có số $ ước tính** — logic định tính: chi phí giữ 1 khách Champions luôn thấp hơn chi phí có được 1 khách mới giá trị tương đương. *Nguồn: `prescriptive_analysis.md` Đề xuất 4 điểm 2.* |
| **Công sức ước lượng** | **M** — thiết kế chương trình loyalty (tier, quyền lợi) + vận hành liên tục. |
| **Bên phụ trách** | Marketing/CRM. |
| **Phụ thuộc/điều kiện tiên quyết** | Không phụ thuộc kỹ thuật; nên làm song song hoặc trước A6. |
| **Tiêu chí chấp nhận** | Theo dõi Recency/Frequency của nhóm Champions theo quý sau khi có chương trình — không để Recency TB xấu đi so với mức nền 274 ngày; theo dõi tỷ lệ Champions rớt xuống "At Risk"/"Can't Lose Them". |
| **Cần ký duyệt?** | **Có** — duyệt ngân sách/quyền lợi chương trình VIP. |
| **Mức ưu tiên** | **P0** — bảo vệ 62,9% giá trị hiện có, chi phí cơ hội thấp hơn tìm khách mới, nên làm sớm song song A1. |

### A8 — Nghiên cứu root-cause sụt khách 2019 (dữ liệu ngoài)

| | |
|---|---|
| **Vấn đề kinh doanh** | Root cause thật của sụt khách 2019 vẫn ngoài phạm vi dữ liệu giao dịch nội bộ — cả 6 kênh marketing rơi đồng đều 37-41% (không phải lỗi 1 kênh), không giải thích được bằng data hiện có. *Nguồn: `diagnostic_summary.md` mục 2.4, mục 3.4; `prescriptive_analysis.md` Đề xuất 4 điểm 3-4.* |
| **Hành động đề xuất** | Trước khi cam kết ngân sách acquisition/retention lớn (A6/A7 mở rộng), ưu tiên thu thập dữ liệu ngoài: khảo sát khách rời đi, benchmark đối thủ, xác nhận có phải do đặc thù dữ liệu mô phỏng hay không (xem thêm Phần 3 — cảnh báo retention phẳng). |
| **Tác động kỳ vọng** | **KHÔNG định lượng** — đây là nghiên cứu nền, giảm rủi ro đầu tư sai hướng. |
| **Công sức ước lượng** | **M** — thiết kế khảo sát + thu thập benchmark thị trường, không phải phân tích data nội bộ. |
| **Bên phụ trách** | Data team + Marketing/Product. |
| **Phụ thuộc/điều kiện tiên quyết** | Không phụ thuộc kỹ thuật; nên hoàn thành trước khi scale A6. |
| **Tiêu chí chấp nhận** | Có báo cáo tổng hợp nguyên nhân khả dĩ (từ khảo sát/benchmark) — dùng làm căn cứ quyết định ngân sách acquisition/retention quy mô lớn. |
| **Cần ký duyệt?** | **Có** — duyệt phạm vi/ngân sách khảo sát. |
| **Mức ưu tiên** | **P1** — không cấp bách về effort nhưng là điều kiện để tránh rủi ro đầu tư sai ở A6 quy mô lớn. |

### Bảng xếp hạng gọn (Impact × Effort)

| ID | Hành động | Impact (định lượng/định hướng) | Effort | Ưu tiên |
|---|---|---|---|---|
| A1 | Floor price = cogs | Cao (định lượng, +0,462 tỷ/10y, cận trên) | S | **P0** |
| A7 | Loyalty Champions | Cao (định tính, bảo vệ 62,9% giá trị) | M | **P0** |
| A2 | Win-back Can't Lose Them | Trung bình (định lượng nhỏ, ROI/khách cao) | M | **P1** |
| A6 | Acquisition pilot West | Trung bình-Cao (định tính, chưa kiểm chứng) | M | **P1** |
| A8 | Root-cause research 2019 | Trung bình (giảm rủi ro đầu tư sai) | M | **P1** |
| A3 | Win-back At Risk | Trung bình (định lượng nhỏ, quy mô lớn hơn) | M | **P2** |
| A4 | Khảo sát vận hành West | Thấp trực tiếp / Cao gián tiếp (tiền đề A5) | M | **P2** |
| A5 | Rollout pricing West | Thấp (định lượng, +38 triệu/10y) | L | **P2** |

---

## Phần 3 — Business sign-off cho giả định model (Phase 5, G1-G5)

### G1 — Break 2019 = biến chỉ báo giai đoạn (`is_post_2019`), giữ nguyên 1 tập train 2013-2022
- **Quyết định kinh doanh mã hoá:** coi 2019 là **thay đổi cấu trúc vĩnh viễn** (không phải nhiễu tạm thời) — model sẽ học "mức nền" khác nhau trước/sau 2019 nhưng vẫn dùng toàn bộ 10 năm để học hình dạng mùa vụ/Tết.
- **Khuyến nghị BA:** **Đồng ý** — khớp đúng chẩn đoán đã chứng minh (khối lượng sụp, không phải giá); tách train riêng 4 năm (2019-2022) sẽ mất tín hiệu mùa vụ và dễ overfit vào giai đoạn xấu nhất.
- **Rủi ro nếu sai:** nếu break không chỉ đổi "mức nền" mà cả biên độ mùa vụ (đã có dấu hiệu — Phase 1: "biên độ bị nén lại sau break"), model tuyến tính đơn giản có thể thiếu chính xác quanh giai đoạn chuyển tiếp 2019-2021 → **DS/pm** cần biết để cân nhắc thêm interaction `is_post_2019 × month` ở Giai đoạn 7-8.

### G2 — 2 feature mùa vụ tách biệt (mùa LƯỢNG cho Revenue, mùa MARGIN `is_low_margin_season` cho COGS)
- **Quyết định kinh doanh mã hoá:** thừa nhận có 2 hiện tượng mùa vụ khác cơ chế — đỉnh/đáy doanh thu theo lượng bán (T4-6 cao/T11-12 thấp) khác với mùa margin xấu do promo giảm sâu (T7-9, T11-12).
- **Khuyến nghị BA:** **Đồng ý** — bằng chứng cơ chế promo đã chứng minh định lượng rất mạnh (chênh 266 lần).
- **Rủi ro nếu sai:** nếu công ty đổi lịch chạy promo (VD dời `Year-End Sale` sang tháng khác) trong 2023-2024, feature lịch cố định sẽ sai lệch → **Marketing cần báo trước cho data team** nếu có kế hoạch đổi lịch khuyến mãi lớn trước khi Giai đoạn 6 chốt feature.

### G3 — `days_from_tet` liên tục, KHÔNG hệ số Tết cố định, KHÔNG interaction Tết×promo
- **Quyết định kinh doanh mã hoá:** thừa nhận Tết ảnh hưởng doanh thu nhưng **không theo pattern cố định mỗi năm** (biên độ dao động -3,6% đến -47,4%) — để model tự học thay vì áp 1 hệ số cứng.
- **Khuyến nghị BA:** **Đồng ý** — mẫu chỉ 10 năm (n=10) không đủ để khẳng định tương tác Tết-promo, tránh đưa giả định chưa đủ bằng chứng vào model.
- **Rủi ro nếu sai:** nếu Tết 2023/2024 lệch mạnh khỏi phân bố lịch sử (VD do chính sách mới), sai số dự báo quanh Tết có thể lớn hơn các giai đoạn khác — **pm/DS cần lưu ý khi trình bày khoảng tin cậy dự báo quanh Tết.**

### G4 — KHÔNG dùng cường độ promotion tương lai làm feature
- **Quyết định kinh doanh mã hoá:** chấp nhận **không có thông tin thật về promo sẽ chạy trong 548 ngày dự báo** — dùng feature lịch (tháng) làm proxy thay vì biến promo trực tiếp.
- **Khuyến nghị BA:** **Đồng ý, bắt buộc** — đây không phải lựa chọn mà là yêu cầu kỹ thuật để tránh leakage (nếu vi phạm, model sẽ học sai hoặc không chạy được lúc predict).
- **Rủi ro nếu sai:** nếu Giai đoạn 6 vô tình dùng biến đếm promo lịch sử làm feature train, dự báo 2023-2024 sẽ hỏng (không có giá trị thật để điền vào) — **DS cần kiểm tra kỹ ở review code Giai đoạn 6**, không chỉ tin vào văn bản giả định.

### G5 — Region KHÔNG làm trục chính cho model Revenue/COGS tổng
- **Quyết định kinh doanh mã hoá:** chấp nhận bỏ qua khác biệt vùng (~1pp margin) khi dự báo tổng toàn quốc, vì mục tiêu cuối (`sample_submission.csv`) chỉ có `Date, Revenue, COGS` — không tách vùng.
- **Khuyến nghị BA:** **Đồng ý** — khớp đúng phạm vi đề bài, tránh thêm bước phân rã→cộng lại không cần thiết.
- **Rủi ro nếu sai:** nếu sau này đề bài/khách hàng yêu cầu dự báo tách vùng, phải làm lại phân tích riêng — **pm cần biết đây là giới hạn phạm vi có chủ đích, không phải thiếu sót.**

### Phát hiện đặc biệt — Cohort retention phẳng (~2,9-3,4% theo Phase 3, ~5,3-6,4% theo Phase 5, đều KHÔNG giảm dần theo tuổi cohort)
- **Quyết định kinh doanh mã hoá:** loại bỏ hoàn toàn feature dựa trên "hành vi khách hàng lặp lại" (rolling active customers, CLV, cohort-aggregate) khỏi model forecast Revenue/COGS tổng.
- **Khuyến nghị BA:** **Cần bàn thêm** — kỹ thuật thì nên đồng ý loại feature này (bằng chứng 2 phương pháp độc lập cùng kết luận retention phẳng), NHƯNG về mặt trình bày, đây là phát hiện nhạy cảm cần thống nhất cách nói trước với giám khảo.
- **Rủi ro nếu sai:** nếu thực ra có tín hiệu retention thật nhưng bị che bởi cách đo, model bỏ lỡ 1 driver thật — cần biết: **DS + pm** (ảnh hưởng trực tiếp cách kể chuyện A→B).
- **Hệ quả trình bày (quan trọng):** dashboard RFM/cohort ở Phần A (`dashboard_rfm_cohort.md`) **vẫn đúng ở mức mô tả** (Champions/At Risk/Can't Lose Them là phân loại mô tả hợp lệ dựa trên dữ liệu thật đã có) — nhưng **mọi đề xuất dự đoán "khách sẽ quay lại"** (VD ước tính win-back A2/A3 ở Phần 2) phải kèm cảnh báo: các con số $ đó là **kịch bản minh hoạ**, không phải dự báo hành vi thật, vì chưa có bằng chứng khách có xu hướng quay lại theo thời gian.
- **Chuẩn bị câu trả lời giám khảo** nếu bị hỏi "vì sao retention phẳng": xem Phần 5 (danh sách câu hỏi giám khảo).

---

## Phần 4 — Sổ quyết định (Decision Register)

| # | Quyết định cần duyệt | Ai duyệt (vai trò) | Hạn chót gợi ý | Hệ quả nếu chưa quyết |
|---|---|---|---|---|
| D1 | Chính sách floor price = cogs, không ngoại lệ campaign lớn (A1) | Chủ pricing/promo | Trước khi code A1 | A1 không triển khai được, mất quick-win margin lớn nhất |
| D2 | Ngân sách + thiết kế A/B test win-back Can't Lose Them (A2) | Chủ marketing/CRM | Trước khi chạy A2 | Không đo được ROI thật, không thể quyết định scale A3 |
| D3 | Ngân sách mở rộng win-back At Risk (A3) | Chủ marketing/CRM | Sau khi có kết quả A2 | Trì hoãn, có thể bỏ lỡ 8,3-24,9 triệu VND tiềm năng (kịch bản) |
| D4 | Phạm vi khảo sát vận hành pricing West (A4) | Chủ pricing/ops | Song song A1 | A5 không có căn cứ để thiết kế pilot |
| D5 | Phạm vi pilot rollout pricing West sang Central/East (A5) | Chủ pricing | Sau A4 | Không nhân rộng được bài học West, dù nhỏ về $ |
| D6 | Ngân sách + chỉ số đo lường pilot acquisition West (A6) | Chủ marketing/finance | Trước khi chạy A6 | Bỏ lỡ cơ hội acquisition hiệu quả hơn, hoặc đầu tư sai nếu không đo đúng |
| D7 | Ngân sách + quyền lợi chương trình loyalty Champions (A7) | Chủ marketing/CRM | Sớm, song song A1 | Rủi ro mất khách Champions (62,9% giá trị) vào đối thủ |
| D8 | Phạm vi/ngân sách nghiên cứu root-cause 2019 (A8) | Sponsor dự án/stakeholder | Trước khi scale A6 lớn | Ngân sách acquisition/retention lớn dựa trên suy đoán chưa kiểm chứng |
| D9 | Chấp nhận giả định model G1-G5 + xử lý phát hiện retention phẳng (Phần 3) | Data owner/pm | Trước Giai đoạn 6 | Giai đoạn 6 có thể build sai feature (VD dùng feature hành vi khách đã bị loại) |
| D10 | Cài đặt hạ tầng (scikit-learn tối thiểu, cân nhắc statsmodels/xgboost) | Team kỹ thuật | Trước Giai đoạn 7 | Giai đoạn 7-8 không chạy được model chuẩn, phải viết tay numpy (chậm, giới hạn ở ensemble) |

---

## Phần 5 — Cầu nối A→B cho Giai đoạn 10 (pm)

### Mạch logic liền mạch (bullet dùng thẳng cho báo cáo)
- Chẩn đoán (Phase 2): break 2019 (Revenue −38,6%) do **khối lượng** (đơn/khách active giảm 28-40%), KHÔNG phải giá (ASP +2,4%, AOV +2,7% — tăng).
- Đề xuất (Phase 4): 4 hành động đều đi theo hướng **bảo toàn margin** (floor price, nhân rộng West) và **acquisition/retention có mục tiêu** (West, Champions) — **không** giảm giá/tăng khuyến mãi thêm, vì sẽ làm trầm trọng cơ chế bán dưới giá vốn đã chứng minh.
- Model (Phase 5): mã hoá đúng chẩn đoán bằng biến chỉ báo giai đoạn (`is_post_2019`) thay vì giả định 1 trend giá xuyên suốt; dùng feature lịch (tháng, Tết) thay vì feature giá/promo tương lai (không có thật); loại bỏ feature hành vi khách lặp lại do phát hiện retention phẳng (nghi dữ liệu mô phỏng).
- Forecast (Phần B, sắp tới): 548 ngày 2023-2024 kế thừa toàn bộ giả định trên — kết quả forecast nên được đọc cùng khung "khối lượng là driver chính", không phải "giá".

### Hạt giống phân việc (task seed) cho Giai đoạn 6-9 — CHỈ liệt kê đầu việc, KHÔNG phân người
1. **Feature engineering lịch** (Giai đoạn 6): `is_post_2019`, `month` (cyclical), `days_from_tet` (mở rộng `tet_dates.csv` tới 2023-2024), `is_low_margin_season`, `day_of_week`, `year`/`trend_index`. *Phụ thuộc: không.*
2. **Cài đặt/verify hạ tầng ML** (scikit-learn tối thiểu; cân nhắc statsmodels, xgboost/lightgbm). *Phụ thuộc: quyết định D10, phải xong TRƯỚC bước 3.*
3. **Baseline model Revenue và COGS độc lập** (Giai đoạn 7), không ràng buộc COGS < Revenue. *Phụ thuộc: bước 1, 2.*
4. **Kiểm thử xử lý break 2019**: so sánh dummy đơn giản vs dummy + interaction `is_post_2019 × month`. *Phụ thuộc: bước 3.*
5. **Model nâng cao/ensemble theo quý** (Giai đoạn 8), nếu hạ tầng cho phép (Random Forest/GBM/XGBoost). *Phụ thuộc: bước 2, 3.*
6. **Sinh forecast 548 ngày + đối chiếu format `sample_submission.csv`** (Giai đoạn 9). *Phụ thuộc: bước 3 hoặc 5.*
7. **Kiểm chứng bổ sung phát hiện retention phẳng** (nếu có scipy: bootstrap so sánh variance retention sớm/muộn) — củng cố câu trả lời giám khảo. *Phụ thuộc: bước 2 (cần scipy).*
8. **Chuẩn bị nội dung A→B cho báo cáo/slide cuối** (dữ liệu đầu vào cho Giai đoạn 10) — tổng hợp: chẩn đoán → đề xuất → giả định model → kết quả forecast. *Phụ thuộc: bước 6.*

### Câu hỏi giám khảo có thể hỏi + hướng trả lời

| Câu hỏi | Hướng trả lời |
|---|---|
| Vì sao retention phẳng, không giảm dần theo tuổi cohort? | Xác nhận bằng 2 phương pháp độc lập (Phase 3 theo `signup_date` ~2,9-3,4%; Phase 5 theo tháng đơn đầu tiên ~5,3-6,4%) — cả 2 đều phẳng, khớp giả thuyết mỗi khách có xác suất mua/tháng gần như hằng số (memoryless) — dấu hiệu dữ liệu order được sinh độc lập theo thời gian. Đây là suy luận hợp lý từ số liệu, **chưa phải kiểm định thống kê chính thức** (thiếu scipy). Đã xử lý: loại toàn bộ feature hành vi khách lặp lại khỏi model forecast. |
| Con số +0,462 tỷ VND (floor price) có chắc chắn không? | Không — là **cận trên lý thuyết**, giả định không co giãn cầu theo giá. Cần pilot đo `quantity` thực tế sau khi áp floor price trước khi tin số này. |
| Đề xuất win-back (2) và nhân rộng West (3) số nhỏ vậy có đáng làm không? | Có — giá trị chính là **bảo toàn/tối ưu trên nền tảng hiện có** và **định hướng vận hành**, bổ sung cho Đề xuất 1 và 4, không phải giải pháp độc lập "cứu" doanh thu ở quy mô break 2019. |
| Root cause thật của sụt khách 2019 là gì? | Chưa xác định được từ dữ liệu giao dịch nội bộ (đã loại trừ giá, đã loại trừ 1 kênh marketing cụ thể) — nằm ngoài phạm vi data hiện có, đề xuất A8 (khảo sát/benchmark ngoài) để tìm tiếp. |
| Sao không dùng cường độ promotion làm feature dự báo? | Rủi ro leakage rõ ràng — 548 ngày dự báo không có dữ liệu `promotions` tương lai thật. Thay bằng feature lịch (`is_low_margin_season`) suy ra từ bằng chứng cơ chế promo lịch sử nhưng bản thân là biến lịch, dùng được cho cả giai đoạn dự báo. |
| Sao không dùng region làm feature? | Target là Revenue/COGS TỔNG toàn quốc (`sample_submission.csv` không có cột region); biến thiên margin theo vùng chỉ ~1pp, nhỏ hơn nhiều so với category (~7,4pp) và break 2019 (-38,6%) — ngoài phạm vi đề bài hiện tại. |
| Hạ tầng thiếu sklearn/scipy/statsmodels ảnh hưởng gì? | Ảnh hưởng trực tiếp Giai đoạn 7 (linear/ARIMA chuẩn) và Giai đoạn 8 (ensemble) — cần cài trước, hoặc viết tay bằng numpy nếu không kịp (đã có tiền lệ ở Phase 3 với logistic regression tay). |

---

## Phần 6 — Sổ rủi ro & giả định hợp nhất (Risk & Assumption Register)

| # | Rủi ro/giả định | Nguồn | Mức ảnh hưởng | Cách giảm thiểu |
|---|---|---|---|---|
| R1 | Không có giả định co giãn cầu theo giá (A1, A5) — nâng giá không làm giảm số lượng bán | `prescriptive_analysis.md` Giới hạn #2 | Cao — có thể phóng đại tác động margin | Pilot nhỏ, theo dõi `quantity` thực tế sau triển khai |
| R2 | Tỷ lệ retention giả định +5/10/15pp (A2, A3) không lấy từ dữ liệu thật | `prescriptive_analysis.md` Giới hạn #3 | Trung bình — sai lệch phân bổ ngân sách win-back | A/B test thật (treatment vs control) trước khi scale |
| R3 | Hệ số 60% (West, A5) tính ở cấp vùng, áp máy móc xuống cấp category | `prescriptive_analysis.md` Giới hạn #4 | Thấp-Trung bình — sai lệch target margin từng category | Coi là định hướng, không phải mục tiêu chính xác; đã chặn gap âm về 0 |
| R4 | Không có dữ liệu chi phí marketing/vận hành campaign | `prescriptive_analysis.md` Giới hạn #1 | Cao — mọi số $ ở A1-A5 là gross, chưa trừ chi phí | Lấy dữ liệu chi phí thật từ tài chính trước khi cam kết ngân sách |
| R5 | Dữ liệu lịch sử 2013-2022 có thể không lặp lại ở 2023-2024, đặc biệt nếu công ty đổi chính sách promo/pricing sau báo cáo này | `prescriptive_analysis.md` Giới hạn #5; `model_assumptions.md` Hạn chế #3 | Cao — ảnh hưởng cả action A1-A5 lẫn model G2/G4 | Theo dõi actual đầu 2023 vs forecast, retrain/điều chỉnh sớm nếu lệch |
| R6 | Break 2019 model hoá bằng dummy đơn giản có thể không đủ nếu biên độ mùa vụ cũng đổi (không chỉ mức nền) | `model_assumptions.md` G1, Hạn chế #2 | Trung bình | Test thêm interaction `is_post_2019 × month` ở Giai đoạn 7-8 |
| R7 | Tết không có hệ số cố định, mẫu n=10 năm quá nhỏ để kết luận tương tác Tết-promo | `model_assumptions.md` G3 | Trung bình | Giữ `days_from_tet` liên tục, không thêm interaction; theo dõi sai số dự báo quanh Tết 2023/2024 |
| R8 | Retention phẳng — khả năng cao dữ liệu khách/đơn được sinh độc lập theo thời gian, không phải hành vi thật | `model_assumptions.md` Nhiệm vụ 3 | Cao — ảnh hưởng cách trình bày cả Phần A lẫn Phần B | Loại feature hành vi khách khỏi model; cảnh báo rõ khi trình bày kết quả win-back (A2/A3) là kịch bản, không phải dự báo hành vi |
| R9 | Hạ tầng `.venv` thiếu sklearn/scipy/statsmodels | `model_assumptions.md` Cảnh báo hạ tầng | Cao — chặn trực tiếp Giai đoạn 7-8 nếu không xử lý | Cài thư viện trước Giai đoạn 7; dự phòng viết tay numpy nếu không kịp |
| R10 | Root cause sụt khách 2019 chưa xác định (ngoài phạm vi data nội bộ) | `diagnostic_summary.md` mục 3.4; `prescriptive_analysis.md` Đề xuất 4 điểm 4 | Cao — quyết định ngân sách A6/A7 quy mô lớn dựa trên suy đoán nếu bỏ qua | Thực hiện A8 (khảo sát/benchmark ngoài) trước khi scale ngân sách lớn |

**Ghi chú số liệu không mâu thuẫn nhưng khác định nghĩa (cần lưu ý khi trình bày):** retention phẳng có 2 con số tuyệt đối khác nhau — Phase 3 (~2,9-3,4%, mẫu số = toàn bộ khách signup) vs Phase 5 (~5,3-6,4%, mẫu số = khách đã có ≥1 đơn) — **không phải mâu thuẫn**, do khác mẫu số, nhưng **kết luận cấu trúc giống hệt nhau** (đường phẳng, không decay). Đã giải thích rõ tại `model_assumptions.md` Nhiệm vụ 3.
