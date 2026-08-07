# Model Assumptions — Giai đoạn 5 (chốt giả định A → B, Vin Datathon 2026)

- **Ngày viết:** 2026-07-21 · `.venv/bin/python` (Python 3.9.6, pandas 2.3.3 — **không có sklearn/scipy/statsmodels**, xem cảnh báo cuối file)
- **Vai trò:** DS, bản lề Phần A (Dashboard/Analysis) → Phần B (Forecast Revenue + COGS, 548 ngày 2023-01-01 → 2024-07-01)
- **Script tái lập:** `EDA_Insight/phase5_model_assumptions/verify_target_and_cohort.py` — chỉ đọc `data/`, ~10s, exit 0
- **Input đã đọc:** `phase0_qc_report.md`, `descriptive_summary.md`, `diagnostic_summary.md`, `dashboard_rfm_cohort.md`, `data/sample_submission.csv`
- **Giai đoạn 5 KHÔNG implement model/feature thật** — chỉ chốt giả định bằng văn bản + verify bằng số.

---

## Nhiệm vụ 1 — Xác nhận target chính xác

**Câu hỏi:** target Phần B (`sales.Revenue`, `sales.COGS`) có đúng là gross demand (tất cả đơn kể cả cancelled, không trừ discount) như Phase 0 QC đã nêu không?

**Cách verify (độc lập, tự tính lại từ `order_items` + `orders` + `products`, không đọc lại số Phase 0):**
- `gross_revenue_line = quantity × unit_price`, `gross_cogs_line = quantity × cogs` (catalog), group theo `order_date`, **giữ nguyên toàn bộ đơn kể cả `cancelled`**, không trừ `discount_amount`.

**Kết quả (3,833/3,833 ngày đối chiếu):**

| Chỉ số | Giá trị |
|---|---:|
| MAPE Revenue (sales.csv vs rebuild gross) | **0.000000%** |
| MAPE COGS (sales.csv vs rebuild gross) | **0.000000%** |
| Max lệch Revenue / COGS 1 ngày | 0.000000% / 0.000001% (sai số làm tròn float) |
| MAPE nếu dùng NET (loại cancelled, trừ discount) — đối chứng | **13.903%** |

Đối chiếu cụ thể (5 ngày đầu + 5 ngày random seed=42, đơn vị VND):

| Date | Revenue (sales.csv) | gross_revenue (rebuild) | COGS (sales.csv) | gross_cogs (rebuild) |
|---|---:|---:|---:|---:|
| 2012-07-04 | 5,123,547.94 | 5,123,547.94 | 3,982,991.19 | 3,982,991.19 |
| 2018-11-19 | 2,171,786.90 | 2,171,786.90 | 1,822,847.47 | 1,822,847.47 |
| 2019-01-13 | 3,354,624.45 | 3,354,624.45 | 2,671,314.89 | 2,671,314.89 |
| 2022-02-28 | 6,007,208.86 | 6,007,208.86 | 4,942,844.92 | 4,942,844.92 |

Full 3,833 dòng: `EDA_Insight/phase5_model_assumptions/data/target_reconcile_sample.csv`.

**Kết luận:** xác nhận lại 100% kết luận Phase 0 W1 bằng phép tính độc lập — `sales.Revenue`/`sales.COGS` = **gross demand toàn bộ đơn (kể cancelled), không trừ discount**. Đây LÀ đúng định nghĩa target Phần B, KHÔNG phải net_revenue. Đối chứng bằng bản NET lệch tới 13.9% càng khẳng định không được nhầm 2 khái niệm khi build feature ở Giai đoạn 6 (feature nào tính từ `order_items` phải dùng đúng công thức gross, không lọc `cancelled`).

---

## Nhiệm vụ 2 — Giả định cho model Phần B

Mỗi giả định: **insight nguồn** → **giả định rút ra** → **áp dụng vào model**.

### G1. Structural break 2019 — model hoá bằng dummy/indicator giai đoạn, KHÔNG chia train riêng biệt hoàn toàn

- **Insight nguồn:** `descriptive_summary.md` mục 2.1 (Revenue rơi -38.6% năm 2019, không hồi phục 3 năm) + `diagnostic_summary.md` mục 2.1 và mục "Đề xuất Giai đoạn 5" #5 (break do khối lượng sụp — ít đơn/khách active 28-40%, KHÔNG phải giá; ASP/AOV còn tăng nhẹ +2.4%/+2.7%) + mục "Đề xuất" #5 gợi ý "chia train trước/sau 2019 hoặc dùng biến indicator".
- **Giả định rút ra:** break 2019 là thay đổi cấu trúc thật (structural, không phải nhiễu ngẫu nhiên), phải model hoá tường minh — không để 1 model trend tuyến tính xuyên suốt 2013-2022 tự "trung bình hoá" qua break.
- **Phương án ưu tiên (1 trong 2, chọn dummy/indicator thay vì tách train riêng biệt):**
  - **Ưu tiên: biến `is_post_2019` (indicator nhị phân, =1 từ 2019-01-01 trở đi) + có thể thêm `is_post_2019_transition` (=1 riêng cho 2019-2021, giai đoạn giảm sâu nhất theo CAGR -12%/năm profit) làm feature, GIỮ NGUYÊN toàn bộ 2013-2022 làm 1 tập train.**
  - **Lý do chọn dummy thay vì chia 2 tập train riêng:** (a) nếu chỉ train trên giai đoạn sau 2019 (2019-2022, chỉ 4 năm) thì mất hết thông tin seasonality/Tết đã kiểm chứng ổn định qua 10 năm (Phase 1 mục 2.2 — hình dạng mùa vụ tháng lặp lại, chỉ biên độ đổi) — 4 năm không đủ để ước lượng mùa vụ ổn định, đặc biệt các năm 2020-2021 lại là đáy tuyệt đối, dễ overfit vào giai đoạn xấu nhất; (b) dummy cho phép model học chung shape mùa vụ/Tết từ toàn bộ 10 năm trong khi vẫn tách được "mức nền" (level) khác nhau giữa 2 giai đoạn.
  - **Rủi ro cần lưu ý ở Giai đoạn 7-8:** nếu dùng model tuyến tính/additive (kiểu decompose trend+seasonal), indicator chỉ dịch level — cần thêm interaction `is_post_2019 × month` nếu biên độ mùa vụ cũng đổi khác (Phase 1 xác nhận: "biên độ bị nén lại sau break", tức không chỉ level mà cả amplitude đổi) — Giai đoạn 6 nên cân nhắc feature `is_post_2019 × seasonal_month_pct` hoặc để model tree-based tự học interaction.
  - 2022 là năm phục hồi đầu tiên (+12.15% YoY) — forecast 548 ngày (2023-2024) nối tiếp ngay sau 2022, nên xu hướng gần nhất (2021-2022) có trọng số quan trọng hơn giai đoạn 2013-2018 — Giai đoạn 7 nên cân nhắc weighted training (trọng số cao hơn cho quan sát gần) thay vì trọng số đều.

### G2. Feature mùa vụ tháng (flag margin thấp T7-9, T11-12) — đưa vào CẢ Revenue LẪN COGS, nhưng vai trò khác nhau

- **Insight nguồn:** `phase0_qc_report.md` W3 (382/3,833 ngày lỗ gộp, dồn T8=155, T12=122, T11=55, T7=33 ngày) + `diagnostic_summary.md` mục 2.2 (promo là cơ chế trực tiếp: 47.86% dòng CÓ promo bán dưới giá vốn vs 0.18% dòng KHÔNG có promo — chênh 266 lần; tỷ lệ dưới giá vốn cao nhất T12=47.3%, T9=34.9%, T7=31.9%, T8=29.2%, khớp lịch `Year-End Sale` T11→T1, `Fall Launch` T8→T10, `Urban Blowout` T7→T9) + `descriptive_summary.md` mục 2.2 (T4-6 là đỉnh doanh thu 12.5-13%/tháng, T11-12 là đáy 4.7-4.8%/tháng — 2 hiện tượng KHÁC NHAU: đỉnh/đáy doanh thu theo lượng bán vs mùa margin thấp theo giá).
- **Giả định rút ra:** có 2 mùa vụ chồng lấn nhưng khác cơ chế — (a) mùa vụ LƯỢNG (Revenue cao T4-6, thấp T11-12) và (b) mùa vụ MARGIN (COGS/Revenue ratio xấu đi T7-9 & T11-12 do promo giảm giá sâu). Không nên gộp chung 1 flag.
- **Áp dụng vào model:**
  - **Revenue model:** dùng flag/feature mùa vụ LƯỢNG — ví dụ `month` (categorical/cyclical sin-cos) hoặc `revenue_seasonal_index_by_month` (đã có sẵn ở Phase 1 — tỷ trọng % theo tháng, bảng mục 2.2) làm feature chính, PHẢN ÁNH ĐỈNH T4-6/ĐÁY T11-12.
  - **COGS model:** ngoài feature mùa vụ lượng (COGS cũng biến động theo lượng bán), THÊM riêng flag `is_low_margin_season` (=1 cho T7, T8, T9, T11, T12 — dựa đúng bằng chứng cơ chế promo đã chứng minh, không phải suy đoán) để model học COGS/Revenue ratio tăng lên đúng các tháng này — feature này áp cho COGS mạnh hơn Revenue vì cơ chế (bán dưới giá vốn) tác động trực tiếp đến COGS/Revenue ratio chứ không phải khối lượng bán.
  - Vì Revenue và COGS forecast **độc lập** (theo khuyến nghị W2/W3 QC — không ràng buộc COGS < Revenue), 2 model có thể dùng chung khung feature lịch nhưng trọng số/tầm quan trọng của `is_low_margin_season` nên khác nhau — đây là quyết định để Giai đoạn 7-8 tune, Giai đoạn 5 chỉ chốt là PHẢI có mặt feature này ở cả 2 model.

### G3. `days_from_tet` liên tục — chốt dùng, KHÔNG dùng hệ số Tết cố định

- **Insight nguồn:** `descriptive_summary.md` mục 2.3 (H3 BÁC BỎ — biên độ dip quanh Tết dao động -3.6% (2019) đến -47.4% (2020), không có 1 pattern cố định) + `diagnostic_summary.md` mục 2.5 (Q5 — tương quan Tết×promo yếu, `corr=+0.646` nhưng n=10 quá nhỏ để tin cậy, "KHÔNG đủ để kết luận nhân quả") + mục "Đề xuất Giai đoạn 5" #3 (giữ nguyên khuyến nghị `days_from_tet` độc lập).
- **Giả định rút ra:** không có hệ số Tết đơn nhất áp được cho mọi năm — phải để model tự học pattern từ khoảng cách liên tục tới Tết, và KHÔNG giả định tương tác chặt với promo (vì n=10 năm không đủ mẫu).
- **Áp dụng vào model:** feature `days_from_tet` = số ngày (có dấu, âm nếu trước Tết, dương nếu sau) từ ngày quan sát đến mồng 1 Tết gần nhất — tính bằng `lunardate` (đã có sẵn cách làm ở `phase1_descriptive/data/tet_dates.csv`, cần mở rộng tới 2023-2024 cho 548 ngày forecast — việc của Giai đoạn 6). KHÔNG dùng feature `is_tet_promo` (tương tác Tết-promo) vì bằng chứng chưa đủ mạnh.

### G4. KHÔNG dùng "cường độ promotion tương lai" làm feature trực tiếp

- **Insight nguồn:** `phase0_qc_report.md` mục 12 (horizon 548 ngày không có promo tương lai thật, phải dùng lịch mùa vụ thay thế) + `diagnostic_summary.md` mục "Đề xuất Giai đoạn 5" #2 (nhắc lại rõ ràng, không dùng biến promo intensity tương lai).
- **Giả định rút ra:** đây là **leakage risk rõ ràng nếu vi phạm** — data 548 ngày dự báo (2023-01-01 → 2024-07-01) không có bảng `promotions` tương lai thật; nếu Giai đoạn 6 vô tình dùng biến đếm số promo đang chạy (tính từ `promotions.csv` lịch sử) làm feature train nhưng lúc predict lại phải "đoán" promo tương lai (không biết) → hoặc leak (nếu dùng data test) hoặc feature vô nghĩa (nếu để 0/NaN toàn horizon).
- **Áp dụng vào model:** thay bằng feature thuần lịch (đã proxy hoá qua G2 — flag `is_low_margin_season` dựa trên tháng, không dựa trên promo_id cụ thể). Đây là feature suy ra TỪ bằng chứng cơ chế promo (đã chứng minh ở G2), nhưng bản thân feature là lịch (tháng), không phải biến promo trực tiếp — nên dùng được cho cả 548 ngày forecast mà không cần biết trước công ty sẽ chạy promo gì.

### G5. Region — KHÔNG ưu tiên làm trục chính cho model Revenue/COGS tổng toàn quốc (ĐỒNG Ý với khuyến nghị Phase 1/2)

- **Insight nguồn:** `descriptive_summary.md` mục 2.5 (chênh lệch margin 3 region chỉ 13.47-14.53%, ~1pp, nhỏ hơn nhiều so với chênh lệch category 11.75-19.13%, ~7.4pp) + `diagnostic_summary.md` mục 2.3 (Q3 — margin West cao hơn Central 1.06pp, trong đó chỉ ~40% do mix category, ~60% do giá/discount thực thi tốt hơn — nhưng đây là phát hiện ở mức KHÁCH HÀNG, không phải ở mức tổng Revenue/COGS toàn quốc theo ngày) + mục "Đề xuất Giai đoạn 5" #4 (khuyến nghị rõ region không nên là trục ưu tiên chính cho forecast tổng).
- **Giả định rút ra + xác nhận bằng số:** **ĐỒNG Ý** không ưu tiên region làm trục chính, vì 2 lý do định lượng:
  1. Target Phần B là **Revenue/COGS TỔNG TOÀN QUỐC theo ngày** (`sales.csv` không có cột region) — muốn dùng region làm feature phải tự phân rã `order_items`→region rồi cộng lại, thêm 1 bước gián tiếp không cần thiết khi mục tiêu cuối cùng là tổng.
  2. Chênh lệch margin giữa vùng chỉ ~1pp (rất nhỏ so với chênh lệch category ~7.4pp hay chênh lệch trước/sau break 2019 là -38.6%) — đóng góp biến thiên của region vào tổng Revenue/COGS toàn quốc theo ngày gần như không đáng kể so với biến thiên do mùa vụ/break/Tết.
- **Áp dụng vào model:** KHÔNG đưa `region` làm feature phân rã cho model Revenue/COGS tổng ở Giai đoạn 7-8. Region chỉ có giá trị nếu sau này có yêu cầu forecast tách theo vùng (ngoài phạm vi đề bài hiện tại — sample_submission chỉ có `Date, Revenue, COGS` tổng).

---

## Nhiệm vụ 3 — Verify độc lập nghi vấn cohort retention phẳng ~3%

**Phương pháp verify (độc lập với Phase 3 — Phase 3 dùng `signup_date` làm cohort; ở đây dùng THÁNG ĐƠN HÀNG KHÔNG-CANCELLED ĐẦU TIÊN của khách làm cohort, không đọc lại `cohort_retention_matrix.csv`):**

| Offset (tháng) | Mẫu số (khách) | Số khách active | Retention % |
|---:|---:|---:|---:|
| 1 | 88,043 | 5,407 | 6.14% |
| 3 | 87,936 | 4,862 | 5.53% |
| 6 | 87,589 | 4,625 | 5.28% |
| 9 | 87,092 | 5,394 | 6.19% |
| 12 | 86,795 | 5,544 | 6.39% |

Std retention qua offset 1-12: **0.40 điểm %** — dao động rất nhỏ, KHÔNG có xu hướng giảm dần theo tuổi cohort. Chart: `EDA_Insight/output/phase5/36_cohort_retention_by_first_order_verify.png`. Data đầy đủ: `EDA_Insight/phase5_model_assumptions/data/cohort_retention_by_first_order.csv`.

**Đọc số:** mức retention tuyệt đối ở đây (~5.3-6.4%) khác con số Phase 3 (~2.9-3.4%) — hợp lý vì khác định nghĩa mẫu số: Phase 3 lấy mẫu số = TOÀN BỘ khách signup (kể cả khách chưa từng mua lần nào), còn cách verify này lấy mẫu số = khách ĐÃ có ít nhất 1 đơn (nên tỷ lệ nền cao hơn tự nhiên). Nhưng **kết luận cấu trúc thì giống hệt nhau ở cả 2 cách đo độc lập: đường retention gần như PHẲNG, không có decay curve theo tuổi quan hệ khách hàng.**

**Xác nhận:** ĐÚNG, retention phẳng ~5-6% (theo cách đo này) suốt offset 1-12 tháng — không giảm dần. Đây là bằng chứng thứ 2, độc lập với Phase 3, cùng đi đến 1 kết luận.

**Đây có phải dấu hiệu customer/order được random-generate độc lập theo thời gian không?** Có khả năng cao — vì:
- Nếu hành vi khách hàng thật, retention luôn giảm dần theo tuổi (khách mới hào hứng nhất ngay sau lần mua đầu, rồi rơi rụng dần — decay curve điển hình mọi ngành e-commerce thực).
- Ở đây M1 ≈ M12 (chênh trong biên độ nhiễu ~0.4pp) — khớp với giả thuyết mỗi khách có 1 "xác suất mua/tháng" gần như hằng số, không phụ thuộc đã mua bao lâu (memoryless, giống phân phối hình học/Poisson đơn giản) — đúng cơ chế thường gặp khi dữ liệu mô phỏng sinh order độc lập theo thời gian (không có state "quan hệ khách hàng" ảnh hưởng ngược lại xác suất mua tương lai).
- Tần suất mua trung bình toàn mẫu chỉ 6.67 đơn/khách trải trên tenure trung bình 1,715 ngày (~4.7 năm) — khớp về mặt số học với xác suất mua ~5-6%/tháng không đổi.

**Kết luận quan trọng cho Giai đoạn 6:** XÁC NHẬN — nếu retention phẳng đúng là do cơ chế sinh dữ liệu độc lập theo thời gian (không có hành vi quay lại thật), thì **mọi feature dựa trên "hành vi khách hàng lặp lại" (VD: rolling active-customer count, CLV-based forecast, RFM aggregate theo thời gian) đều VÔ NGHĨA cho việc dự báo Revenue/COGS tổng** — vì không có tín hiệu "khách cũ quay lại nhiều/ít hơn theo mùa/theo tuổi" để model học. Giai đoạn 6 nên **ưu tiên tuyệt đối feature thuần lịch** (xem Nhiệm vụ 4) thay vì cố gắng đưa feature hành vi khách hàng vào model forecast tổng.

---

## Nhiệm vụ 4 — Khung feature đề xuất cho Giai đoạn 6 (CHỈ liệt kê + lý do, CHƯA implement)

Ưu tiên theo mức độ bằng chứng từ Phase 1/2 (cao → thấp):

| # | Feature | Bằng chứng | Ưu tiên |
|---|---|---|---|
| 1 | `is_post_2019` (dummy giai đoạn) | Break 2019 -38.6%, xác nhận structural bằng decompose khối lượng (Phase 2 mục 2.1) | **Rất cao** |
| 2 | `month` (1-12, dạng cyclical sin/cos hoặc one-hot) | Seasonality tháng ổn định 10/10 năm, đỉnh T4-6/đáy T11-12 (Phase 1 mục 2.2) | **Rất cao** |
| 3 | `days_from_tet` (liên tục, có dấu) | H3 bác bỏ hệ số cố định nhưng Tết vẫn có ảnh hưởng rõ mỗi năm (Phase 1 mục 2.3) | **Rất cao** |
| 4 | `is_low_margin_season` (flag T7,8,9,11,12) — dùng cho COGS chủ yếu | Cơ chế promo-driven đã chứng minh định lượng, chênh 266 lần (Phase 2 mục 2.2) | **Cao** |
| 5 | `day_of_week` (dow) | Chênh lệch đỉnh/đáy 19.8% giữa các ngày, đỉnh thứ Tư/đáy thứ Bảy (Phase 1 mục 2.2) | **Cao** |
| 6 | `year` / `trend_index` (số năm kể từ 2013, hoặc riêng cho từng giai đoạn) | CAGR khác nhau rõ theo giai đoạn — cần bắt trend nhưng KHÔNG dùng 1 trend tuyến tính xuyên suốt (Phase 1 mục 2.1) | **Cao** |
| 7 | `quarter` | Hệ quả phái sinh của `month`, có thể dư thừa nếu đã có month — cân nhắc chỉ dùng 1 trong 2 | Trung bình |
| 8 | Flag lễ Việt Nam khác (30/4-1/5, Quốc khánh 2/9, Giáng sinh...) | CHƯA có bằng chứng định lượng riêng trong Phase 1/2 (chỉ có Tết được kiểm chứng kỹ) — cần Giai đoạn 6 tự kiểm tra trước khi thêm | Trung bình (cần verify thêm) |
| 9 | `is_month8` riêng biệt (ngoài `is_low_margin_season`) | Tháng 8 có std cao nhất (±2.15pp) — biến động thất thường "Mid-Year Sale" năm có năm không (Phase 1 mục 2.2) | Thấp-Trung bình (tín hiệu nhiễu, không chắc lặp lại 2023-2024) |
| — | **KHÔNG dùng:** feature hành vi khách hàng lặp lại (rolling active customers, CLV, cohort-based) | Nhiệm vụ 3 đã xác nhận retention phẳng — vô nghĩa cho forecast tổng | **Loại bỏ** |
| — | **KHÔNG dùng:** cường độ promotion tương lai | Leakage — không có data thật cho 548 ngày forecast (G4) | **Loại bỏ** |
| — | **KHÔNG dùng:** region làm trục phân rã chính | Đóng góp biến thiên nhỏ (~1pp margin) so với target tổng toàn quốc (G5) | **Loại bỏ khỏi model chính** |

---

## Hạn chế & rủi ro

1. Nhiệm vụ 3 kết luận "khả năng cao là random-generate độc lập theo thời gian" — đây là **suy luận hợp lý từ số liệu, không phải chứng minh toán học chặt (chưa test thống kê chính thức do thiếu scipy)**. Nếu sau này có sklearn/scipy, nên chạy thử 1 kiểm định đơn giản (VD so sánh variance retention giữa nhóm offset sớm/muộn bằng bootstrap) để củng cố thêm.
2. G1 (dummy break 2019) là quyết định của DS dựa trên khuyến nghị có sẵn — Giai đoạn 7-8 khi thực nghiệm có thể phát hiện dummy đơn giản không đủ, cần thêm biến liên tục dạng "khoảng cách tới break" hoặc piecewise trend — đây là điều chỉnh hợp lý ở bước sau, không phải sai giả định ở đây.
3. G2/G4 dựa trên bằng chứng cơ chế promo rất mạnh trong lịch sử — rủi ro là công ty CÓ THỂ thay đổi chính sách promo trong 548 ngày forecast (không dữ liệu nào đảm bảo hành vi 2023-2024 giống 2013-2022) — đã nêu ở hạn chế Phase 1/2, nhắc lại ở đây vì ảnh hưởng trực tiếp đến accuracy model.
4. Toàn bộ giả định G1-G5 áp dụng cho model Revenue/COGS **tổng toàn quốc theo ngày** — nếu phạm vi đề bài mở rộng sau này (VD forecast theo category/region), phải làm lại phân tích riêng, không tái dùng nguyên giả định này.

---

## ⚠️ Cảnh báo hạ tầng

**Môi trường `.venv/bin/python` hiện KHÔNG có `sklearn`, `scipy`, `statsmodels`** — chỉ có `pandas`, `matplotlib`, `openpyxl`, `lunardate`. Đây là hạn chế hạ tầng thật (đã gặp tương tự ở Phase 3 khi phải viết logistic regression tay bằng numpy).

**Ảnh hưởng trực tiếp:**
- **Giai đoạn 7 (baseline model):** nếu dự định dùng linear regression/ARIMA chuẩn (statsmodels) hay Ridge/Lasso (sklearn) sẽ KHÔNG chạy được trong venv hiện tại — phải viết tay bằng numpy (như Phase 3 đã làm cho logistic) hoặc cài thư viện trước.
- **Giai đoạn 8 (model theo quý + ensemble):** ensemble (Random Forest, Gradient Boosting, XGBoost/LightGBM) hoàn toàn phụ thuộc sklearn hoặc thư viện tương đương — KHÔNG có cách viết tay khả thi trong thời gian hạn chế của datathon.

**Khuyến nghị:** cài `scikit-learn` (tối thiểu) trước khi bắt đầu Giai đoạn 7, cân nhắc thêm `statsmodels` (cho ARIMA/SARIMA baseline) và `xgboost`/`lightgbm` nếu muốn ensemble mạnh ở Giai đoạn 8. Giai đoạn 5 CHỈ nêu ra cảnh báo này, KHÔNG tự ý cài đặt.
