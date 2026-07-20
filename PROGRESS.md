# PROGRESS — Vin Datathon 2026

Cập nhật lần cuối: 2026-07-20

**Cấu trúc thư mục** (sau reorg): mỗi phase 1 folder riêng trong `EDA_Insight/` — `phase0_qc/`, `phase1_descriptive/` (kèm `data/` chứa CSV trung gian), `phase2_diagnostic/`, `phase3_dashboard/` (kèm `data/`). Chart tách theo `output/phase0-3/`. Lineage đầy đủ ghi ở `EDA_Insight/DATA_LINEAGE.md`.

| # | Giai đoạn | Agent | Trạng thái | File output | Ghi chú |
|---|---|---|---|---|---|
| 0 | Data quality & schema QC | de | ✅ done | `EDA_Insight/phase0_qc/phase0_full_qc.py`, `phase0_qc_report.md` | 0 BLOCKER, 10 WARNING, 8 INFO. Key: sales.Revenue=gross kể cả cancelled (lệch net ~24%); 18.6% dòng bán dưới giá vốn → 382 ngày lỗ gộp; web_traffic chỉ 1 dòng/ngày toàn site (không dùng traffic_source phân kênh) |
| 1 | EDA Descriptive (trend, CAGR, seasonality, Tết) | da | ✅ done | `EDA_Insight/phase1_descriptive/descriptive_summary.md` + notebook + `data/{tet_yearly_stats,daily_revenue_gross_net,category_region_decompose}.csv` | Structural break 2019 (revenue -38.6%, profit giảm nhanh gấp 3 revenue). Tết KHÔNG đồng nhất qua năm (bác giả thuyết ban đầu). Streetwear 79.9% doanh thu nhưng margin không cao nhất. ⚠️ Notebook cell mới CHƯA chạy trong Jupyter thật (venv thiếu nbconvert, chỉ verify bằng exec()) — cần mở Jupyter Run All trước khi trình bày |
| 2 | Diagnostic (revenue giảm, margin, COGS) | da | ✅ done | `EDA_Insight/phase2_diagnostic/diagnostic_summary.md` + `diagnostic_revenue.md` (mục 9-15) + `data/{yearly_kpi_decompose,promo_intensity_by_year,monthly_unit_price_ratio,category_below_cost_rate,category_region_margin_controlled,region_margin_mix_decomposition,channel_revenue_margin_by_year,tet_promo_overlap}.csv` | Break 2019 = khối lượng sụp (qty -40%, khách -28%), KHÔNG phải giá (ASP +2.4%)/mix/promo. Promo gây 47.9% dòng bán dưới giá vốn (vs 0.18% không promo) — cơ chế trực tiếp 382 ngày lỗ gộp. West margin cao ~40% do mix, ~60% do giá thật. Tết x promo: corr yếu (+0.65, n=10) |
| 3 | Dashboard A: RFM, cohort, marketing, demographics | da | ✅ done | `EDA_Insight/phase3_dashboard/dashboard_rfm_cohort.md` + `customer_demographics.py/.md` + `data/{rfm_customer_segments,cohort_retention_matrix,churn_risk_scores}.csv` | Pareto: 25.6% khách (Champions) = 62.9% giá trị. Cohort retention PHẲNG ~3% mọi tháng (nghi ngờ đặc tính data mô phỏng — DS phải xác nhận ở Phase 5). West region nhỏ nhất nhưng chất lượng khách tốt nhất. ⚠️ Logistic regression viết tay bằng numpy (venv thiếu sklearn/scipy) |
| 4 | Prescriptive: đề xuất hành động định lượng | ba + da | ⬜ pending | — | Chờ 2, 3 |
| 5 | Chốt giả định model (A → B) | ds + ba | ⬜ pending | — | Chờ 2 |
| 6 | Feature engineering thuần lịch | de + ds | ⬜ pending | — | Chờ 5 |
| 7 | Baseline models | ds | ⬜ pending | — | Chờ 6 |
| 8 | Model theo quý + ensemble, forecast 548 ngày | ds | ⬜ pending | — | Chờ 7 |
| 9 | Validation + explainability + check submission | tester + ds | ⬜ pending | — | Chờ 8 |
| 10 | Story A→B, báo cáo, phân việc Hải/Hoàng/Đăng | pm | ⬜ pending | — | Xuyên suốt |
