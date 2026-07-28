# Datathon 2026 — Báo cáo cuối: Từ 11 năm dữ liệu bán hàng đến dự báo 548 ngày

- **Nhóm:** (điền tên nhóm). **Ngày:** 2026-07-28. **Deliverable:** D2 (Phase 10).
- **Cấu trúc:** Phần A (Descriptive → Diagnostic → Dashboard → Prescriptive) → **Cầu nối A→B** → Phần B (Baseline → Model → Validation → Rủi ro).
- **Nguyên tắc:** tài liệu này **tổng hợp** kết quả đã chốt ở Phase 0–9 (đều ✅ trong `PROGRESS.md`), KHÔNG tạo phân tích/số liệu mới. Mọi số truy được về đúng file/mục nguồn (liệt kê cuối bài).

---

## Executive summary (đọc trước khi vào chi tiết)

**Chuyện gì đã xảy ra:** Doanh thu gãy cấu trúc năm 2019 (−38,6%), chưa từng hồi phục về đỉnh cũ; lợi nhuận gộp giai đoạn 2019–2021 giảm nhanh gấp ~3 lần doanh thu.

**Vì sao:** Cú sụt là **sụp khối lượng giao dịch** (qty −40%, khách active −28%), **KHÔNG phải giảm giá** (ASP/AOV còn +2,4%/+2,7%), không phải mix/promo/kênh/vùng. Khuyến mãi lại là thủ phạm trực tiếp gây 382 ngày bán lỗ gộp (47,9% dòng có promo bán dưới giá vốn). Nguyên nhân *gốc* vì sao khách rời đi **nằm ngoài dữ liệu giao dịch** — nói thẳng, không suy đoán.

**Ai tạo giá trị:** 25,6% khách (Champions) = 62,9% giá trị. West nhỏ nhất nhưng chất lượng khách tốt nhất. **Cohort retention phẳng ~3–6%** → dữ liệu khách sinh ngẫu nhiên, không có hành vi quay lại thật.

**Nên làm gì:** (1) Floor price = giá vốn → **+0,462 tỷ VND margin/10 năm** (quick-win lớn nhất); (2) win-back Can't Lose Them → At Risk; (3) nhân rộng pricing West; (4) **KHÔNG giảm giá/tăng promo** — sai nguyên nhân.

**Cầu nối:** cohort phẳng ⇒ feature hành vi vô nghĩa ⇒ Phần B **chỉ dùng feature thuần lịch**; target = **gross demand** (khớp `sales.csv` MAPE 0.000%); mùa vụ/Tết/break-2019 hoá thành feature.

**Dự báo:** baseline seasonal-naive thắng bất ngờ ⇒ chốt hướng lag mùa vụ. Model cuối = **LightGBM global + ensemble 50/50 với B1**. **Vượt mốc cả 2 target: Revenue WAPE 22,71% (mốc 25,18%), COGS WAPE 19,79% (mốc 23,09%).**

**Tin được không:** QA kiểm định độc lập — số khớp, không leakage, file nộp tái lập byte-identical. **3 rủi ro trung thực:** chặn-trần trend (under-forecast nếu 2023–24 bật tăng vượt lịch sử); chưa có ground-truth 2023–24; sốc cấu trúc kiểu 2019 thì mọi model chịu chung.

**Mục lục:**
1. [Phần A — Chuyện gì / vì sao / ai / làm gì](#phần-a)
2. [Cầu nối A→B](#cầu-nối-ab)
3. [Phần B — Dự báo: Model → Validation → Rủi ro](#phần-b)
4. [Kết luận chung & bước tiếp theo](#kết-luận-chung)

---

<a name="phần-a"></a>

# PHẦN A — 11 năm doanh thu: chuyện gì đã xảy ra, vì sao, ai tạo giá trị, nên làm gì

**Nguồn Phần A:** `phase1_descriptive/descriptive_summary.md`; `phase2_diagnostic/diagnostic_summary.md`; `phase3_dashboard/dashboard_rfm_cohort.md`; `phase4_prescriptive/prescriptive_analysis.md` + `ba_action_spec.md`; chart `../output/phase1..4/`.

## Câu hỏi điều tra

1. **Descriptive — Chuyện gì đã xảy ra?** Doanh thu/lợi nhuận 11 năm (2012–2022): xu hướng dài hạn, mùa vụ/Tết, category/region nào gánh doanh thu?
2. **Diagnostic — Vì sao?** Cú sụt 2019 từ đâu — giá, khối lượng, mix, hay promo? Cơ chế nào khiến ~1/5 dòng hàng bán dưới giá vốn?
3. **Dashboard — Ai tạo giá trị?** Khách nào quan trọng nhất (RFM), có quay lại không (cohort), vùng nào chất lượng tốt nhất?
4. **Prescriptive — Nên làm gì?** Hành động định lượng nào ưu tiên để bảo toàn/tăng margin và giữ khách?

## Dữ liệu dùng

| Tầng | Nguồn chính | Khoảng thời gian | Phạm vi/lọc |
|---|---|---|---|
| Descriptive (P1) | `sales.csv`; `order_items+products+orders+geography` | 2012-07-04 → 2022-12-31 (3.833 ngày) | **gross_revenue** (kể cả `cancelled`, không trừ discount; khớp `sales.csv`, lệch build lại ~0,0000%) |
| Diagnostic (P2) | `order_items+orders+products+customers+geography+promotions` | 2013-01-01 → 2022-12-31 | gross xuyên suốt — khớp target Phần B |
| Dashboard (P3) | `orders+payments+customers+geography` (KHÔNG dùng `sales.csv`) | Snapshot Recency 2022-12-31; cohort 126 tháng | Non-cancelled; **Monetary = `payments.payment_value`**; RFM 88.123 khách, cohort 121.692 khách |
| Prescriptive (P4) | `floor_price_simulation_*`, `winback_scenario_by_segment`, `west_margin_replication_*` | Toàn kỳ 2013–2022 | **Mô phỏng "nếu áp chính sách từ đầu"**, không phải dự báo |

---

## Tầng 1 — Chuyện gì đã xảy ra (Descriptive)

### 1.1 Doanh thu gãy cấu trúc năm 2019

| Năm | Doanh thu (tỷ VND) | Ghi chú |
|---|---:|---|
| 2013 | 1,66 | |
| 2014 | 1,87 | |
| 2015 | 1,89 | |
| 2016 | 2,10 | đỉnh |
| 2017 | 1,91 | |
| 2018 | 1,85 | |
| **2019** | **1,14** | **rơi 38,6% so 2018** |
| 2020 | 1,05 | |
| 2021 | 1,04 | đáy |
| 2022 | 1,17 | +12,15% YoY — năm đầu phục hồi rõ |

CAGR 2013–2022: **−3,80%/năm** doanh thu, **−2,71%/năm** lợi nhuận gộp — không đều: tăng 2013–2015 (+6,79%/năm), chững 2016–2018, **giảm sâu nhất 2019–2021** (doanh thu −4,21%/năm nhưng lợi nhuận gộp −12,00%/năm, **nhanh gấp ~3 lần**) → margin bị bào mòn thêm, không chỉ co quy mô.

*Chart: `../output/phase1/01_daily_ma30.png`, `../output/phase1/02_monthly_margin.png`, `../output/phase1/03_heatmap_year_month.png`. Nguồn: `descriptive_summary.md` §2.1.*

### 1.2 Mùa vụ ổn định, nhưng Tết KHÔNG đồng nhất qua các năm

Mùa vụ theo tháng lặp lại ổn định: đỉnh T4–6 (~12,5–13,0%/tháng), đáy T11–12 (~4,7–4,8%/tháng) — chênh ~2,7 lần. T8 lệch chuẩn cao nhất (±2,15 điểm %, nghi "Mid-Year Sale" chạy năm có năm không). Theo ngày: đỉnh thứ Tư, đáy thứ Bảy, chênh 19,8%.

Ngược lại, **hiệu ứng Tết không giống nhau giữa các năm**:

| Năm | Tuần trước Tết | Quanh mồng 1 | Ghi chú |
|---|---:|---:|---|
| 2017 | −42,2% | −9,8% | dip mồng 1 nhẹ nhất |
| **2019** | −3,6% | **−39,8%** | dip mồng 1 sâu nhất — trùng năm break |
| **2020** | **−47,4%** | −29,0% | tuần trước sâu nhất |
| 2022 | −10,4% | −11,3% | hồi phục tốt nhất |

→ **Bác bỏ** giả thuyết "Tết có pattern cố định". Không áp 1 hệ số Tết cứng — cần biến liên tục theo khoảng cách tới Tết. *(→ trở thành feature `days_from_tet` ở Phần B, xem Cầu nối L3.)*

*Chart: `../output/phase1/04_seasonal_shape.png`, `05_day_of_week.png`, `06_tet_effect.png`. Nguồn: `descriptive_summary.md` §2.2–2.3.*

### 1.3 Streetwear gánh gần 80% doanh thu nhưng margin không cao nhất

| Category | % doanh thu | Margin % | | Region | % doanh thu | Margin % |
|---|---:|---:|---|---|---:|---:|
| **Streetwear** | **79,92%** | 13,24% | | East | 46,48% | 13,64% |
| Outdoor | 15,18% | 16,37% | | Central | 30,08% | 13,47% |
| Casual | 2,80% | 11,75% (thấp nhất) | | West | 23,44% (nhỏ nhất) | 14,53% (cao nhất) |
| GenZ | 2,09% | 19,13% (cao nhất) | | | | |

Category phân hoá margin mạnh hơn region nhiều. **gross_revenue 11 năm ≈ 16,43 tỷ VND** (khớp `sales.csv`, dùng cho model Phần B) vs **net ≈ 14,23 tỷ VND** — gap **13,37%**, hai định nghĩa cho 2 mục đích khác nhau, không phải lỗi dữ liệu. *(→ chính là lý do B chốt target = gross demand, xem Cầu nối L2.)*

*Chart: `../output/phase1/22_category_decompose.png`, `23_region_decompose.png`, `24_gross_vs_net_reconcile.png`. Nguồn: `descriptive_summary.md` §2.4–2.6.*

---

## Tầng 2 — Vì sao (Diagnostic)

### 2.1 Break 2019 = sụp KHỐI LƯỢNG, KHÔNG phải giá/mix/promo

| Chỉ số | 2018 | 2019 | YoY |
|---|---:|---:|---:|
| Revenue | 1,85 tỷ | 1,14 tỷ | **−38,6%** |
| ASP | — | — | **+2,4%** |
| Số lượng bán (qty) | 337.646 | 202.653 | **−40,0%** |
| Số đơn | 69.510 | 41.601 | **−40,2%** |
| Khách active | 37.922 | 27.312 | **−28,0%** |
| AOV | — | — | **+2,7%** |

Giảm giá kích cầu thì ASP↓ qty↑ — **thực tế ngược lại**: ASP/AOV tăng nhẹ, qty/đơn/khách rơi 28–40%. Loại thêm: cường độ promo 2019 (38,4% doanh thu) đúng nhịp năm lẻ; mix category không nhảy bậc tại 2019; cả 6 kênh (`order_source`) rơi đồng đều **37,3%–41,0%** (chênh 3,7 điểm %) → vấn đề toàn platform, không phải 1 kênh.

**→ Kết luận: vấn đề khối lượng (retention/acquisition), KHÔNG phải giá, mix, hay promo.**

*Chart: `../output/phase2/29_yearly_price_volume_decompose.png`, `30_promo_intensity_by_year.png`, `34_channel_revenue_margin_trend.png`. Nguồn: `diagnostic_summary.md` §2.1, 2.4.*

### 2.2 Khuyến mãi → 47,9% dòng bán dưới giá vốn → 382 ngày lỗ gộp

| | % dòng bán dưới giá vốn |
|---|---:|
| Dòng **CÓ** promo | **47,9%** |
| Dòng **KHÔNG** promo | **0,18%** |

Chênh ~266 lần — bằng chứng trực tiếp: hiện tượng bán dưới giá vốn gắn với khuyến mãi. Cơ chế tạo **382 ngày bán lỗ gộp** (18,6% tổng dòng `order_items` bán dưới giá vốn — gốc từ Phase 0 QC, Phase 2 giải thích). Tập trung T12 (47,3%), T9 (34,9%), T7 (31,9%), T8 (29,2%) — trùng `Year-End Sale`, `Fall Launch`, `Urban Blowout`. Theo category: Casual 22,3%, Streetwear 21,4% (kéo margin toàn shop mạnh nhất vì ~80% doanh thu), Outdoor 18,1%, GenZ 9,8%.

*Chart: `../output/phase2/31_unit_price_ratio_by_month.png`, `32_below_cost_rate_by_category.png`. Nguồn: `diagnostic_summary.md` §2.2.*

### 2.3 Margin West cao hơn: ~40% do mix, ~60% do giá thật

| Region | Margin thực tế | Margin mix-adjusted | Chênh do mix (pp) |
|---|---:|---:|---:|
| East | 13,31% | 13,38% | −0,07 |
| Central | 13,15% | 13,24% | −0,10 |
| **West** | **14,20%** | **13,86%** | **+0,35** |

Gap West−Central thực tế 1,06pp; sau loại mix còn 0,61pp → **~40% do mix** (West bán Outdoor nhiều hơn), **~60% do giá/discount thật tốt hơn trong cùng category**. Không thể quy hết cho "may mắn cơ cấu".

*Chart: `../output/phase2/33_category_region_margin_controlled.png`. Nguồn: `diagnostic_summary.md` §2.3.*

### 2.4 Tết × khuyến mãi: tương quan yếu, mẫu quá nhỏ

`corr(số promo trùng Tết, mức dip)` = +0,646 nhưng n=10 năm — không đủ kết luận nhân quả; tuần trước Tết corr ~0 (+0,065). Giữ khuyến nghị `days_from_tet` liên tục, không giả định tương tác Tết–promo. *Chart: `../output/phase2/35_tet_promo_overlap.png`. Nguồn: `diagnostic_summary.md` §2.5.*

### 2.5 Nói thẳng: nguyên nhân gốc khách rời đi NẰM NGOÀI dữ liệu giao dịch

Đã loại trừ bằng số nhất quán: **KHÔNG** phải giá (ASP/AOV tăng), **KHÔNG** phải mix/promo, **KHÔNG** phải 1 kênh, **KHÔNG** phải 1 vùng. Nhưng dữ liệu giao dịch nội bộ **không chứa biến ngoại sinh** (marketing spend theo thời gian, đối thủ, vận hành/logistics, vĩ mô) để trả lời **tại sao** khách ngừng mua 2019. Đây là **giới hạn cứng của dữ liệu, không phải thiếu sót phân tích** — nói rõ thay vì suy đoán. *(→ trở thành rủi ro sốc cấu trúc của B, xem Cầu nối L6.)*

*Nguồn: `diagnostic_summary.md` §3 (Hạn chế #4) + Tổng kết.*

---

## Tầng 3 — Ai tạo giá trị (Dashboard: RFM & Cohort)

### 3.1 Pareto rõ rệt: 25,6% khách tạo 62,9% giá trị

| Segment | Số khách | % khách | Monetary (tỷ VND) | % Monetary | Monetary TB/khách | Recency TB (ngày) |
|---|---:|---:|---:|---:|---:|---:|
| **Champions** | 22.575 | **25,6%** | 8,95 | **62,9%** | 396.438 | 274 |
| Loyal Customers | 16.974 | 19,3% | 2,88 | 20,3% | 169.914 | 787 |
| Lost | 21.682 | 24,6% | 0,46 | 3,2% | 21.158 | 2.563 |
| At Risk | 7.989 | 9,1% | 0,65 | 4,5% | 80.882 | 2.010 |
| Can't Lose Them | 2.251 | 2,6% | 0,49 | 3,5% | 218.601 | 1.783 |
| Hibernating | 3.327 | 3,8% | 0,27 | 1,9% | 81.035 | 2.399 |
| Promising | 5.375 | 6,1% | 0,21 | 1,4% | 38.217 | 1.105 |
| New Customers | 4.865 | 5,5% | 0,20 | 1,4% | 41.793 | 359 |
| Need Attention | 3.085 | 3,5% | 0,12 | 0,9% | 40.454 | 689 |

Tổng Monetary mẫu RFM (88.123 khách) ≈ 14,23 tỷ VND. **Champions** = core business (62,9% giá trị/25,6% khách). **Can't Lose Them** (2.251 khách, Monetary/khách 218.601 VND — cao thứ 2) = "từng rất tốt, đang mất dần", ROI cứu lại cao nhất nhóm rủi ro.

*Chart: `../output/phase3/22_rfm_segment_summary.png`, `23_rfm_scatter.png`. Nguồn: `dashboard_rfm_cohort.md` §1.*

### 3.2 Cohort retention PHẲNG ~3–6% — data mô phỏng, không có hành vi quay lại thật

Retention TB theo tuổi cohort (121.692 khách/126 cohort tháng): **M1 ≈ 3,0% · M3 ≈ 2,9% · M6 ≈ 3,0% · M12 ≈ 2,9%** — gần như không đổi (2,9–3,4%). Xác nhận độc lập lần 2 (đo theo tháng đơn đầu, mẫu số khác) cho **cùng cấu trúc phẳng**, chỉ khác mức tuyệt đối (~5,3–6,4%). Đường retention **KHÔNG giảm theo tuổi cohort** như e-commerce thật (decay-curve).

**Diễn giải (correlational):** khả năng cao cơ chế sinh dữ liệu gán xác suất mua gần như hằng số theo tháng, không phụ thuộc tuổi quan hệ. **Đây là phát hiện quan trọng nhất Tầng 3** — dẫn thẳng tới quyết định thiết kế model Phần B *(xem Cầu nối L1)*.

*Chart: `../output/phase3/24_cohort_retention_heatmap.png`, `25_cohort_retention_curve.png`. Nguồn: `dashboard_rfm_cohort.md` §2; `PROGRESS.md` Phase 3 & 5.*

### 3.3 West nhỏ nhất nhưng chất lượng khách tốt nhất

| Region | % Champions | % Lost |
|---|---:|---:|
| Central | 22,7% | 27,9% |
| East | 24,1% | 23,4% |
| **West** | **36,1%** | 21,4% (thấp nhất) |

West chỉ 14.741 khách (nhỏ nhất) nhưng per-capita revenue cao hơn Central 62%, East 53% (0,249 triệu VND/khách) — 2 phương pháp độc lập cùng xác nhận chất lượng khách West tốt hơn. *Chart: `../output/phase3/26_rfm_region_heatmap.png`. Nguồn: `dashboard_rfm_cohort.md` §3, §5.5.*

### 3.4 RFM "Lost" đánh giá thấp mức độ nghiêm trọng thực tế

RFM "Lost" chỉ 21.682 khách (24,6%) — nhưng ngưỡng tuyệt đối (Recency > 365 ngày) cho thấy **65.071 khách (73,8% mẫu, 6,95 tỷ VND lịch sử) đã hơn 1 năm không mua**, gấp 3 lần. RFM dùng ngũ phân vị tương đối (luôn ~20–25% tệ nhất); churn-risk ngưỡng cố định phản ánh đúng quy mô hơn. *Chart: `../output/phase3/27_churn_risk_summary.png`. Nguồn: `dashboard_rfm_cohort.md` §4.*

---

## Tầng 4 — Nên làm gì (Prescriptive): 4 đề xuất định lượng

> Nguyên tắc (từ Tầng 2): **vấn đề là khối lượng/khách, không phải giá** — không đề xuất nào giảm giá để "cứu" doanh thu.

**Đề xuất 1 — Floor price = giá vốn (quick-win margin lớn nhất).** Đặt `unit_price_floor = max(unit_price, cogs)` theo SKU, ưu tiên Casual/Streetwear và T7–9, T11–12. Mô phỏng 714.669 dòng: loại 133.052 dòng (18,62%) bán dưới giá vốn → Revenue gross 16,430 → 16,892 tỷ, margin toàn shop **13,80% → 16,15% (+2,36pp)**, **+0,462 tỷ VND margin/10 năm** (Streetwear +0,409 tỷ). **Giả định: KHÔNG co giãn cầu — cận trên lý thuyết.** *Chart: `../output/phase4/36_floor_price_margin_before_after.png`.*

**Đề xuất 2 — Win-back: Can't Lose Them trước, At Risk sau.** Ưu tiên ngân sách cá nhân hoá cho CLT (2.251 khách, ROI/khách cao nhất) rồi At Risk (7.989 khách). Kịch bản +5/10/15pp (dùng AOV/đơn): **CLT +2,9 / +5,7 / +8,6 triệu VND**; **At Risk +8,3 / +16,6 / +24,9 triệu VND**. **Giả định: tỷ lệ minh hoạ, chưa từ A/B test, chưa trừ chi phí campaign.** *Chart: `../output/phase4/37_winback_revenue_scenario.png`.*

**Đề xuất 3 — Nhân rộng pricing West (giá trị là bài học vận hành).** Áp cách định giá West sang Central/East, ưu tiên Outdoor/Streetwear. Mô phỏng hệ số "60% do giá thật": **+38 triệu VND margin/10 năm** (+0,24pp). **Giả định: hệ số 60% cấp vùng, áp xuống category là đơn giản hoá — không phải đòn bẩy tài chính.** *Chart: `../output/phase4/38_west_margin_replication_uplift.png`.*

**Đề xuất 4 — KHÔNG giảm giá/tăng promo; ưu tiên acquisition West + retention Champions.** Break 2019 đi cùng ASP/AOV **tăng** → giảm giá không giải quyết đúng nguyên nhân, còn làm nặng cơ chế bán dưới giá vốn. Định hướng: acquisition pilot West (chất lượng khách tốt nhất); retention bảo vệ Champions (62,9% giá trị) trước khi mở khách mới; không cắt 1 kênh marketing cụ thể (cả 6 kênh rơi đồng đều). *(→ nhất quán với giả định "chính sách không đổi" của forecast B, xem Cầu nối L7.)*

### Tóm tắt ưu tiên hành động

| # | Đề xuất | Tác động | Giả định chính |
|---|---|---|---|
| **1** | **Floor price = giá vốn** | **+0,462 tỷ VND/10 năm** (+2,36pp) | KHÔNG co giãn cầu (cận trên) |
| 2 | Win-back CLT → At Risk | +2,9→8,6 tr (CLT) / +8,3→24,9 tr (At Risk) | Tỷ lệ minh hoạ, chưa A/B test |
| 3 | Nhân rộng pricing West | +38 tr/10 năm (+0,24pp) | Hệ số 60% cấp vùng |
| 4 | **KHÔNG giảm giá/tăng promo** | Không định lượng $ (thiếu data chi phí) | Break 2019 = khối lượng, không phải giá |

## Hạn chế Phần A

1. Nguyên nhân gốc khách rời 2019 **không xác định được từ data giao dịch** (thiếu biến ngoại sinh) — giới hạn cứng, không phải thiếu sót (Tầng 2.5).
2. CAGR/decompose dựa 2 mốc năm — nhạy năm chọn, chỉ mô tả hướng.
3. Hiệu ứng Tết & tương quan Tết–promo trên n=10 năm — không đủ kết luận nhân quả.
4. Decompose category/region là correlational (mix-adjust West là ước lượng điểm, chưa CI).
5. Cohort phẳng là phát hiện correlational trên data mô phỏng — không suy sang khách thật ngoài đời (đã xác nhận Phase 5).
6. RFM dùng ngũ phân vị tương đối — dễ đánh giá thấp mức nghiêm trọng (Lost 24,6% vs 73,8% ngưỡng tuyệt đối).
7. Cả 4 đề xuất **thiếu data chi phí** — số là gross, chưa phải ROI ròng.
8. Data 2012–2022 không đảm bảo lặp y hệt cho 548 ngày 2023–2024, nhất là nếu công ty đổi promo/pricing sau báo cáo.

---

<a name="cầu-nối-ab"></a>

# CẦU NỐI A → B: Insight nào của Phần A quyết định thiết kế model Phần B

> **Luận điểm:** Phần B không chọn feature/target/model theo cảm tính — **từng lựa chọn là hệ quả trực tiếp của một phát hiện định lượng ở Phần A.**

| # | Phát hiện Phần A | Quyết định Phần B | Cơ chế nhân quả |
|---|---|---|---|
| L1 | **Cohort retention phẳng ~3–6%** (Tầng 3.2) | **Bỏ feature hành vi khách; chỉ dùng feature thuần lịch** (B §0.1) | Data khách ngẫu nhiên ⇒ CLV/khách-active/tần suất mua = nhiễu ⇒ loại từ gốc |
| L2 | **Target = gross demand** khớp `sales.csv` (Tầng 1.3, gap 13,37%) | **Target = gross demand**, Revenue & COGS train độc lập (B §0.2, MAPE 0.000%) | Chốt đúng mục tiêu ⇒ tránh build nhầm net |
| L3 | **Tết KHÔNG cố định** (Tầng 1.2) | Biến liên tục **`days_from_tet`**, không hệ số Tết cứng (B §0.1, 3.1) | Pattern Tết đổi mỗi năm ⇒ để model học theo khoảng cách. `days_from_tet` = feature #2 |
| L4 | **Break 2019** sụp khối lượng, nền thấp hẳn (Tầng 1.1+2.1) | **`is_post_2019`** + **`trend_index`**; **bỏ linear → cây** (B §2, 3) | 1 hệ số trend không khớp 2 pha ⇒ B3 linear bias +29–39%, ra doanh thu âm ⇒ cây học phi tuyến |
| L5 | **Mùa vụ tháng ổn định**; quý trùng tháng (Tầng 1.2) | `month_sin/cos`; **loại `quarter`** (corr 0.97, importance ~0) (B §0.1, 3.2) | Mùa vụ tháng lặp ⇒ cyclical; quý dư thừa ⇒ chia model theo quý *tệ hơn* |
| L6 | **Nguyên nhân gốc NẰM NGOÀI data** (Tầng 2.5) | Chấp nhận không có feature ngoại sinh; nêu thẳng **rủi ro sốc cấu trúc** (B rủi ro 3) | Không có biến giải thích 2019 ⇒ không model được cú sốc ⇒ trung thực |
| L7 | **KHÔNG giảm giá/tăng promo** (Tầng 4) | Forecast giả định **chính sách không đổi** (B rủi ro 2; A Hạn chế #8) | Prescriptive A & Forecast B nhất quán 1 thế giới quan |

**Điểm xoay số 1 (L1) — vì sao B không giống bài forecast e-commerce thường:** phản xạ tự nhiên là đắp feature hành vi (CLV, khách active, tần suất). Phần A chặn đứng bằng con số: cohort phẳng ~3–6% (SD 0,4 điểm %) trong khi khách thật có decay-curve dốc. Hai phép đo độc lập (P3, P5) cùng kết luận: hành vi quay lại là nhiễu. Hệ quả: mọi feature "khách cũ quay lại" bị loại **trước khi build**, Phase 6 chỉ giữ 17 feature thuần lịch. Link đắt giá nhất — biến bài "panel hành vi" thành "chuỗi thời gian thuần mùa vụ".

**Điểm xoay số 2 (L2):** Phase 5 đối chứng target khớp gross `sales.csv` MAPE 0.000%; net lệch 13,9% — đúng gap 13,37% A đo ở Tầng 1.3. Bỏ bước này ⇒ nguy cơ tối ưu nhầm net rồi thua mốc oan.

**Điểm xoay số 3 (L3, L4, L5):** pattern mô tả của A **hoá thành cột dữ liệu** — Tết-không-cố-định ⇒ `days_from_tet` (feature #2, SHAP dương); break-2019 ⇒ `is_post_2019`+`trend_index` (feature #1, SHAP **âm**, đúng chiều "nền gần đây thấp"); mùa vụ-tháng ⇒ `month_sin/cos`, loại `quarter`. Break-2019 cũng là lý do bỏ linear chọn cây: đường thẳng đơn hệ số ngoại suy lệch +29–39% và cho 4 ngày doanh thu âm.

**Điểm xoay số 4 (L6, L7):** giới hạn của A thành sự trung thực của B — không vá lỗ hổng "vì sao 2019" bằng feature ngoại sinh bịa; thay vào đó ghi nhận rủi ro sốc cấu trúc (fold `rolling_2` xác nhận mọi model tệ hẳn). Forecast nhất quán giả định chính sách giá không đổi (A Hạn chế #8, B rủi ro 2).

**Vì sao đáng điểm:** feature, target, lẫn *class* model đều lần ngược được về một phát hiện định lượng của A. Kết quả cuối (Revenue WAPE 22,71% / COGS 19,79%) là sản phẩm của chuỗi quyết định có căn cứ, không phải may mắn tinh chỉnh.

---

<a name="phần-b"></a>

# PHẦN B — Dự báo: Model → Validation → Rủi ro

- **Bài toán:** dự báo **Revenue** và **COGS** hằng ngày cho 548 ngày (2023-01-01 → 2024-07-01), chưa có ground-truth tại thời điểm làm model.
- **Nguồn Phần B:** `phase7_baseline/baseline_report.md`, `phase8_model/model_report.md`, `phase9_validation/validation_report.md`, chart `../output/phase7-9`.
- **Lưu ý xuyên suốt:** horizon thật (2023–2024) chưa có ground-truth ⇒ **mọi WAPE/MAPE trong Phần B đến từ holdout nội bộ (2012–2022)**, không phải đánh giá trên dữ liệu thật của horizon.

## 0. Ràng buộc nối từ Phần A (tóm tắt — chi tiết ở Cầu nối)

- **§0.1 Feature thuần lịch** (L1): cohort phẳng ⇒ loại feature hành vi; Phase 6 giữ 17 feature lịch. Sàng lọc tương quan: `month_cos` (−0.50), `is_post_2019` (−0.38), `days_from_tet` (+0.37) mạnh nhất; `quarter` loại (corr 0.97 với `month`).
- **§0.2 Target = gross demand** (L2): khớp `sales.csv` MAPE 0.000% (net lệch 13,9%). Revenue & COGS train **độc lập** — không suy target này ra target kia.

## 1. Data & thiết kế đánh giá (theo thời gian)

Mọi chia tập tôn trọng thứ tự thời gian — **không bao giờ dùng tương lai dự đoán quá khứ**.

| Tập | Khoảng | Số ngày | Vai trò |
|---|---|---:|---|
| `train_fit` | 2012-07-04 → 2021-07-01 | 3.285 | Fit model, không thấy holdout |
| **Holdout chính (`main_548d`)** | 2021-07-02 → 2022-12-31 | 548 | Mốc đánh giá chính thức |
| `train_full` | 2012-07-04 → 2022-12-31 | 3.833 | Fit model cuối, tạo forecast thật |
| **Forecast thật (bản nộp)** | 2023-01-01 → 2024-07-01 | 548 | Chưa có ground-truth |

Phase 8 nâng lên **rolling-origin backtest 5 fold**: `main_548d` (fold chính thức, chọn model), `rolling_1..4` (đánh giá ổn định). `rolling_2` (2018-07→2019-12) trùng đúng giai đoạn sốc 2019 — khó nhất, không dùng chọn model vì không đại diện horizon thật.

## 2. Bước 1 — Baseline: bất ngờ seasonal naive thắng

4 baseline: **B1 seasonal naive** (copy giá trị đúng ngày năm trước), B2 month-mean, B3 linear (OLS 9 feature lịch), B3b linear + interaction.

| Baseline | Revenue WAPE | COGS WAPE |
|---|---:|---:|
| **B1 seasonal naive** | **25.18%** | **23.09%** |
| B3b linear + interaction | 46.54% | 41.22% |
| B3 linear | 46.97% | 42.28% |
| B2 month-mean | 56.51% | 52.22% |

Model "ngây thơ" nhất **thắng áp đảo** model hồi quy đủ feature (~25% vs ~47%). **Vì sao B3 thua:** `trend_index` chỉ 1 hệ số cho toàn 2013–2022, trong khi doanh thu tăng 2013–2018 rồi giảm/phục hồi chậm sau 2019 — đường thẳng không khớp 2 pha. Ngoại suy lệch **+29%** (holdout TB thật 2.875.239 vs dự đoán 3.712.559), riêng 2022 **+39%**; còn cho **4 ngày Revenue âm** (thấp nhất −231.484). *(→ đúng L4.)*

**Quyết định chốt hướng Phase 8:** giữ tín hiệu lag mùa vụ + thêm khả năng phi tuyến của cây. Cụ thể: (1) thử model cây thay linear; (2) đưa "giá trị cùng kỳ năm trước" thành **feature `lag_365`**; (3) bắt buộc chặn dự báo ở 0.

![Actual vs Predicted 4 baseline](../output/phase7/07_holdout_actual_vs_pred.png)
![So sánh WAPE/MAPE](../output/phase7/07_metric_bar_comparison.png)
![Residual B3 lệch âm hệ thống](../output/phase7/07_b3_residuals_holdout.png)

**Mốc Phase 8 phải vượt (WAPE, holdout chính): Revenue 25.18% · COGS 23.09%.**

## 3. Bước 2 — Model cuối: LightGBM + Ensemble, vượt mốc

### 3.1 Feature
Giữ 17 feature lịch Phase 6 + 2 feature mới theo bài học baseline: `lag_365` (giá trị cùng kỳ năm trước, logic giống B1 nhưng là input cho model) và `lag_365_smooth7` (trung bình 7 ngày quanh mốc). **Cơ chế chain:** 365 ngày đầu dùng `lag_365` thật, ~183 ngày cuối dùng `lag_365` từ giá trị model tự dự đoán — không leakage nhưng có rủi ro lý thuyết cộng dồn sai số (xem rủi ro 1).

### 3.2 Model — WAPE % trên fold `main_548d` (tiêu chí chọn chính thức)

| Model | Revenue | COGS |
|---|---:|---:|
| B1 seasonal naive (mốc GĐ7) | 25.18 | 23.09 |
| RandomForest | 25.13 | 21.31 |
| GradientBoosting | 25.09 | 20.92 |
| XGBoost | 24.63 | 22.34 |
| **LightGBM** | **23.22** | **20.05** |
| LightGBM theo quý | 24.42 | 22.70 |
| **Ensemble (LightGBM + B1, 50/50)** | **22.71** | **19.79** |

LightGBM thắng nhóm model đơn. Chia theo quý *tệ hơn* (mỗi model quý còn ~950 ngày thay vì ~3.285); `quarter` importance ~0 — mùa vụ quý đã được `month` bắt trọn. **Ensemble 50/50 với B1 thắng cuối cùng.**

**Cấu hình cuối (giống nhau 2 target):** LightGBM (global) + Ensemble 50/50 với B1, fit sản xuất trên toàn 2012–2022.

### 3.3 Kết quả so mốc (bảng chính)

| Target | Metric | Mốc B1 | Model cuối | Cải thiện |
|---|---|---:|---:|---:|
| Revenue | **WAPE** | 25.18% | **22.71%** | −2.47 điểm (−9.8% tương đối) |
| Revenue | MAPE | 27.48% | 26.19% | −1.29 điểm |
| Revenue | RMSE | 1.022.856 | 945.528 | thấp hơn |
| Revenue | MAE | 724.009 | 653.010 | thấp hơn |
| COGS | **WAPE** | 23.09% | **19.79%** | −3.30 điểm (−14.3% tương đối) |
| COGS | MAPE | 24.08% | 21.30% | −2.78 điểm |
| COGS | RMSE | 830.134 | 726.071 | thấp hơn |
| COGS | MAE | 601.980 | 515.752 | thấp hơn |

→ **Vượt mốc cả 2 target**, trên WAPE lẫn 3 chỉ số phụ. Diễn giải: WAPE 22.71% = tổng sai số tuyệt đối 548 ngày / tổng doanh thu thật ≈ 22,7% — mỗi 100 đồng doanh thu thật model lệch TB ~22–23 đồng tính trên cả kỳ.

**Feature quan trọng nhất (LightGBM):** `trend_index` (#1, nhưng SHAP **âm** — càng gần đây kéo dự báo xuống, khớp L4), `days_from_tet` (#2, khớp L3), `day_of_month` (#3), `lag_365`/`lag_365_smooth7` (#4–5, khớp bài học baseline); `quarter`/`is_holiday_qk`/`is_christmas` importance ~0 (khớp L5).

![WAPE mọi model qua 5 fold](../output/phase8/08_backtest_wape_by_fold.png)
![Actual vs Predicted model cuối](../output/phase8/08_holdout_actual_vs_pred_final.png)
![Feature importance](../output/phase8/08_feature_importance.png)
![Forecast 548 ngày](../output/phase8/08_forecast_548_final.png)

## 4. Vì sao ensemble thắng — cơ chế, không phải may mắn

Hai model **sai khác kiểu nhau**, trung bình triệt tiêu cả 2 kiểu sai:
- **LightGBM** học tương tác phi tuyến từ *toàn bộ* 10 năm nhưng **làm mượt** spike ngày lẻ.
- **B1** copy nguyên biến động ngày-qua-ngày 1 năm trước → bắt spike tốt (Revenue >1×10⁷ giữa 2022) nhưng không học 9 năm còn lại.

**Bằng chứng thực nghiệm (Phase 9)** — tách WAPE 365 ngày đầu (`lag_365` thật) vs 183 ngày cuối (`lag_365` model tự dự đoán):

| Target | Model | WAPE 1–365 | WAPE 366–548 | Đuôi vs đầu |
|---|---|---:|---:|---:|
| Revenue | LightGBM đơn | 23.50% | 22.55% | −0.95 (đỡ hơn) |
| Revenue | **Ensemble** | 23.83% | **20.09%** | **−3.74 (đỡ hơn hẳn)** |
| COGS | LightGBM đơn | 19.58% | 21.19% | **+1.61 (tệ hơn — cộng dồn)** |
| COGS | **Ensemble** | 20.03% | **19.20%** | **−0.84 (đỡ hơn)** |

LightGBM đơn có dấu hiệu cộng dồn sai số nhẹ ở COGS đuôi (+1.61), nhưng ghép B1 thì ensemble đuôi **tốt hơn đầu** cả 2 target — nhánh B1 "neo" lại, triệt tiêu phần trôi. Bằng chứng số cho vai trò "chặn rủi ro đuôi chuỗi".

## 5. Validation: có tin được số này không?

Phase 9 cho 1 người khác (QA/tester) **kiểm định độc lập**, tự chạy lại từ đầu.

- **Format bản nộp — 14/15 PASS ngay lần đầu:** đúng cột `Date,Revenue,COGS`, 548 dòng, range 2023-01-01→2024-07-01, không thiếu/trùng ngày, 0 NaN, 0 âm, ≤2 số lẻ. **1 FAIL:** line-ending (sample CRLF, file gốc LF) → **đã sửa**: bản nộp = `forecast_548_SUBMIT_crlf.csv`, byte-identical trừ ký tự xuống dòng.
- **Không leakage — 6/6 PASS (đọc trực tiếp code):** fold cắt `train_fit` trước holdout không chồng lấn; feature chỉ dùng ≤ ngày t−1; `lag_365` ≤ t−1; forecast dùng chain; model sản xuất không để lộ 2023–2024; Revenue/COGS độc lập.
- **Tái lập byte-identical:** chạy lại 2 lần độc lập, `forecast_548.csv` khớp sha256 `080c8bb4…78d36b`. `backtest_metrics.csv` lệch 3/72 dòng cỡ 3.2×10⁻¹⁶ (làm tròn đa luồng RandomForest) — không ảnh hưởng file nộp/quyết định.

| Target | Model | WAPE (QA tự tính) | Vượt mốc? |
|---|---|---:|:--:|
| Revenue | B1 (mốc) | 25.18% | khớp GĐ7 |
| Revenue | Ensemble | 22.71% | **PASS** |
| COGS | B1 (mốc) | 23.09% | khớp GĐ7 |
| COGS | Ensemble | 19.79% | **PASS** |

**Giải thích được (SHAP):** `lag_365` dương (mạnh nhất, "mức nền mùa vụ"); `trend_index` **âm** (gần đây kéo xuống, khớp L4); `days_from_tet` dương (khớp L3); `day_of_month` dương. 3 feature importance ~0 (`quarter`/`is_holiday_qk`/`is_christmas`) xác nhận `mean|SHAP|=0` tuyệt đối.

![SHAP beeswarm](../output/phase9/09_shap_beeswarm.png)
![SHAP bar signed](../output/phase9/09_shap_bar_signed.png)

**GATE cuối: GO có điều kiện → điều kiện (CRLF) đã gỡ.** Bản nộp = `forecast_548_SUBMIT_crlf.csv`.

## 6. Ba rủi ro trung thực (không giấu)

**Rủi ro 1 — Model bị "chặn trần" ở `trend_index`, có thể under-forecast nếu 2023–24 tăng vượt lịch sử.** Cây chỉ học ngưỡng đã thấy khi train. 100% 548 ngày forecast có `trend_index` vượt phạm vi train (train đến vị trí 3.832, forecast từ 3.833). Tăng `trend_index` ra ngoài phạm vi → dự báo **đứng yên tuyệt đối**. Nếu 2023–24 đi ngang/giảm giống 2019–2022 thì an toàn; nếu **bật tăng vượt đỉnh 2013–2018**, model **không bắt được**. Rủi ro **một chiều** — chỉ có nguy cơ dự báo thấp, nghiêng về thận trọng.

**Rủi ro 2 — Chưa có số thật 2023–2024 để đối chiếu.** Mọi WAPE/MAPE từ holdout nội bộ 2012–2022. Độ tin cậy phụ thuộc giả định **cơ chế sinh 2023–24 ≈ cơ chế 2012–22** — chưa kiểm chứng được vì chưa có số thật. Giới hạn cố hữu của mọi bài dự báo chưa có ground-truth (khớp A Hạn chế #8).

**Rủi ro 3 — Sốc cấu trúc kiểu 2019 thì mọi model chịu chung.** Fold `rolling_2` (đúng giai đoạn 2019): mọi model kể cả B1 tệ hẳn — Revenue WAPE 44.6% (GB) → 63.2% (LightGBM đơn), COGS 31.2% (GB) → 57.4% (LightGBM đơn); Ensemble 58.3%/54.6%. Giới hạn của **dữ liệu**, không phải model — nếu 2023–24 có biến cố tương tự (không có bằng chứng xác nhận/phủ nhận), mọi model đều rủi ro. *(→ đúng A Tầng 2.5 / L6.)*

**Vì sao vẫn chọn Ensemble thay GradientBoosting** (dù GB robust hơn ở fold sốc): trên fold chính thức `main_548d` và trung bình fold "không sốc", Ensemble thắng cả 2 target; lợi thế "ổn định" của GB gần như hoàn toàn đến từ 1 fold sốc — loại fold đó, GB thua Ensemble mọi target. Chọn theo tiêu chí đăng ký từ đầu (fold main), không đổi tiêu chí sau khi thấy kết quả. **Xử lý:** giữ GradientBoosting làm **phương án dự phòng đã ghi nhận** — chuyển sang nếu có tín hiệu sốc trong data thật.

## 7. Kết luận Phần B & giám sát

**Quyết định cuối:** giữ Ensemble LightGBM + B1 (50/50) — trọng số 50/50 là điểm tối ưu khi dò lưới 0.30–0.70 trên validation (không nhìn fold main) cho **cả 2 target**. `forecast_548.csv` (GĐ8) giữ nguyên; bản nộp `forecast_548_SUBMIT_crlf.csv` (chỉ sửa line-ending).

**Giám sát khi có số thật:** (1) có actual 2023 → so ngay forecast, kiểm rủi ro 1 (under-forecast?) và rủi ro 3 (sốc?); (2) phát hiện sốc/lệch bất thường → cân nhắc chuyển GradientBoosting (fallback) hoặc retrain theo quý; (3) theo dõi WAPE rolling để phát hiện sớm nếu cơ chế 2023–24 khác 2012–22 (rủi ro 2).

---

<a name="kết-luận-chung"></a>

# KẾT LUẬN CHUNG & bước tiếp theo

**Một câu chuyện liền mạch A→B:** dữ liệu 11 năm cho thấy doanh thu gãy cấu trúc 2019 do **sụp khối lượng khách**, không phải giá; khách giá trị tập trung ở Champions nhưng **cohort không có hành vi quay lại thật**. Chính phát hiện đó buộc bài dự báo bỏ mọi feature hành vi, chỉ dùng **feature thuần lịch** trên **target gross demand**, chọn **model cây + ensemble seasonal-naive** — và **vượt mốc cả 2 chỉ tiêu (Revenue WAPE 22,71% / COGS 19,79%)**, đã được QA kiểm định độc lập.

**Giá trị business:** quick-win rõ nhất là **floor price = giá vốn (+0,462 tỷ VND margin/10 năm)**; định hướng chiến lược là **giữ khối lượng/khách (acquisition West + retention Champions), không giảm giá**.

**Trung thực về giới hạn:** nguyên nhân gốc khách rời 2019 nằm ngoài data; forecast chưa có ground-truth 2023–24; model thận trọng (under-forecast) nếu cầu bật tăng vượt lịch sử; sốc cấu trúc kiểu 2019 thì mọi model chịu chung — đã có fallback GradientBoosting + kế hoạch giám sát.

**Bước tiếp theo (Phase 10 còn lại):** nộp Phần B lên cổng (`forecast_548_SUBMIT_crlf.csv`); dựng slide ≤15 (ưu tiên bridge + WAPE + rủi ro); dry-run Q&A.

---

## Nguồn tổng hợp (không có phân tích/số liệu mới)

- `PROGRESS.md` — bảng tiến độ Phase 0–9 (nguồn số duy nhất).
- **Phần A:** `phase1_descriptive/descriptive_summary.md`; `phase2_diagnostic/diagnostic_summary.md`; `phase3_dashboard/dashboard_rfm_cohort.md`; `phase4_prescriptive/prescriptive_analysis.md` + `ba_action_spec.md`; chart `../output/phase1..4/`.
- **Phần B:** `phase7_baseline/baseline_report.md`; `phase8_model/model_report.md`; `phase9_validation/validation_report.md`; chart `../output/phase7..9/`.
- Story gốc: `part_a_story.md`, `part_b_story.md`, `bridge_a_to_b.md`.
