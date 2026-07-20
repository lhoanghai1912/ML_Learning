# Doanh thu + thói quen khách hàng theo khu vực & độ tuổi

Kết hợp `order_items` + `orders` + `products` + `customers` + `geography`. Revenue = gross (khớp `sales.csv` 0.000%, xem `../phase2_diagnostic/diagnostic_revenue.md`). Script: `customer_demographics.py` · Notebook: `EDA_demographics.ipynb` · Chart: `../output/phase3/15..21_*.png`.

*Reorganize 2026-07-20: di chuyển vào `EDA_Insight/phase3_dashboard/` — xem `EDA_Insight/DATA_LINEAGE.md`.*

## Tóm tắt 1 dòng

**Độ tuổi không ảnh hưởng gì đến hành vi mua (AOV, tần suất, category đều phẳng). Khu vực thì có — khách West chi tiêu/người cao hơn Central 62%, dù dân số khách ít nhất.**

## 1–5. Theo độ tuổi — mọi thứ đều phẳng

| Chỉ số | 18-24 | 25-34 | 35-44 | 45-54 | 55+ |
|---|---|---|---|---|---|
| % doanh thu 2022 | 13.5 | 30.1 | 26.4 | 19.1 | 10.9 |
| AOV (nghìn VND) | 25.42 | 25.56 | 25.50 | 25.59 | 25.42 |
| Tần suất (đơn/khách) | 7.07 | 7.11 | 7.21 | 7.22 | 7.27 |
| Streetwear % | 80.0 | 80.4 | 79.9 | 80.2 | 80.2 |
| Revenue/khách (triệu) | 0.126 | 0.128 | 0.129 | 0.130 | 0.131 |

Chênh lệch lớn nhất giữa các nhóm tuổi trên bất kỳ chỉ số nào đều dưới ~4%. Kết luận: **age_group không mang tín hiệu hành vi** trong bộ dữ liệu này — % doanh thu theo tuổi khác nhau (13.5% vs 30.1%) đơn thuần vì SỐ KHÁCH mỗi nhóm khác nhau (25-34 đông nhất: 26,802 khách), không phải vì nhóm đó chi tiêu khác nhóm khác.

## 6. Giới tính — cũng phẳng

Revenue theo giới tính tỷ lệ đúng theo số khách (Female 59,640 · Male 57,457 · Non-binary 4,833). AOV (25.49 / 25.52 / 25.74 nghìn) và tần suất (7.17 / 7.18 / 6.98 đơn/khách) gần như bằng nhau. Không có tín hiệu hành vi theo giới tính.

## 7. Khu vực — điểm khác biệt DUY NHẤT, và dễ đọc sai nhất

| Region | Số khách | Revenue tổng (tỷ, 2013-22) | Revenue/khách (triệu) |
|---|---|---|---|
| East | 44,721 | ~7.28 | 0.163 |
| Central | 30,784 | ~4.72 | 0.154 |
| West | 14,741 | ~3.68 | **0.249** |

Nhìn cột "Revenue tổng" → tưởng East quan trọng nhất, West kém nhất. Nhìn cột "Revenue/khách" → **ngược lại**: khách West chi tiêu cao hơn Central 62%, cao hơn East 53%. Đúng ở MỌI nhóm tuổi (không phải do lệch cơ cấu tuổi giữa các vùng — đã kiểm tra chéo age×region).

**Đây là bẫy Simpson's paradox kinh điển**: tổng bị chi phối bởi quy mô dân số, per-capita mới phản ánh đúng chất lượng khách hàng từng vùng.

## Prescriptive

- Không dùng `age_group` hay `gender` làm biến phân khúc/feature — dữ liệu không ủng hộ, sẽ chỉ thêm nhiễu cho model Phần B hoặc RFM.
- Nếu cân nhắc ngân sách mở rộng theo vùng: **West đáng ưu tiên đầu tư/khách hơn**, dù quy mô hiện tại nhỏ nhất — ngược với kết luận nếu chỉ nhìn bảng xếp hạng doanh thu tổng.
- Bất kỳ chart "theo vùng" nào trong dashboard cuối cùng nên đi kèm bản per-capita, tránh đội ngũ chấm bài hiểu lầm y như bẫy ở trên.

*Tạo ngày 17/07/2026.*

---

## 8. RFM, Cohort, Churn risk (mở rộng Giai đoạn 3)

> Phần này bổ sung script `customer_demographics.py` section 22-28 (chart `../output/phase3/22..28_*.png`). Giải thích khái niệm + số liệu đầy đủ nằm ở `dashboard_rfm_cohort.md` — đây chỉ là bảng tóm tắt tham chiếu nhanh.

**Mẫu:** 88,123 khách có ≥1 đơn không-cancelled (khác 90,246 khách có ≥1 đơn bất kỳ — 2,123 khách chỉ toàn đơn cancelled bị loại khỏi RFM). Recency tính tới 2022-12-31. Monetary = `payment_value` (net, đã QC khớp 100%).

### RFM segment

| Segment | Số khách | % khách | Tổng Monetary (tỷ VND) | % Monetary | Monetary TB/khách (VND) | Recency TB (ngày) |
|---|---:|---:|---:|---:|---:|---:|
| Champions | 22,575 | 25.6% | 8.95 | 62.9% | 396,438 | 274 |
| Loyal Customers | 16,974 | 19.3% | 2.88 | 20.3% | 169,914 | 787 |
| Lost | 21,682 | 24.6% | 0.46 | 3.2% | 21,158 | 2,563 |
| At Risk | 7,989 | 9.1% | 0.65 | 4.5% | 80,882 | 2,010 |
| Can't Lose Them | 2,251 | 2.6% | 0.49 | 3.5% | 218,601 | 1,783 |
| Hibernating | 3,327 | 3.8% | 0.27 | 1.9% | 81,035 | 2,399 |
| Promising | 5,375 | 6.1% | 0.21 | 1.4% | 38,217 | 1,105 |
| New Customers | 4,865 | 5.5% | 0.20 | 1.4% | 41,793 | 359 |
| Need Attention | 3,085 | 3.5% | 0.12 | 0.9% | 40,454 | 689 |

Tổng Monetary toàn mẫu RFM ≈ **14.23 tỷ VND**. Champions chỉ 25.6% số khách nhưng chiếm **62.9%** giá trị — Pareto rõ rệt.

### Cohort retention (loại 238 khách pre-launch)

Retention trung bình toàn kỳ theo tháng kể từ cohort: **M1 ≈ 3.0% · M3 ≈ 2.9% · M6 ≈ 3.0% · M12 ≈ 2.9%** — gần như phẳng, không có decay theo tuổi cohort (xem diễn giải ở `dashboard_rfm_cohort.md`). 238 khách pre-launch: 171 (71.8%) từng mua, tổng 28.7 triệu VND, hành vi không khác biệt đáng kể so với mẫu chung.

### RFM × Region

| Region | % Champions | % Lost |
|---|---:|---:|
| Central | 22.7% | 27.9% |
| East | 24.1% | 23.4% |
| West | **36.1%** | 21.4% |

Khớp với phát hiện per-capita ở mục 7: West vừa chi tiêu/khách cao nhất vừa có tỷ trọng Champions cao nhất.

### Churn risk (rule-based, ngưỡng tuyệt đối) + logistic validation

| Tier | Số khách | Tổng Monetary (tỷ VND) |
|---|---:|---:|
| Đã rời bỏ (>365 ngày) | 65,071 | 6.95 |
| An toàn | 10,819 | 3.71 |
| Rủi ro cao | 11,762 | 3.29 |
| Rủi ro trung bình | 471 | 0.28 |

Logistic regression thủ công (numpy, không có sklearn/scipy trong venv), time-split cutoff 2022-06-30: Accuracy 0.877, Precision 0.884, Recall 0.990, **AUC 0.773**. Baseline "đoán tất cả churn" đã đạt Accuracy ~0.874 (do churn rate thực tế 87.4%) — model chỉ nhỉnh hơn baseline một chút về accuracy nhưng AUC 0.773 cho thấy khả năng **xếp hạng** rủi ro thực sự hữu ích (dùng để ưu tiên, không dùng ngưỡng 0.5 cứng). Hệ số chuẩn hoá: recency_days +0.211, frequency −0.330, log(monetary) −0.630, trend_180d +0.025 (gần 0, khả năng nhiễu do cộng tuyến với recency).

Chi tiết đầy đủ, diễn giải 4 cấp và đề xuất hành động: xem `dashboard_rfm_cohort.md`.
