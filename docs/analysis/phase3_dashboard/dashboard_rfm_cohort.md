# Dashboard A — RFM Segmentation, Cohort Retention, Demographics & Churn Risk

**Giai đoạn 3 — Vin Datathon 2026.** Mở rộng từ `customer_demographics.py` (section 22-28) và
`customer_demographics.md`. Tất cả script chỉ **đọc** `data/`, chạy lại được từ đầu bằng
`.venv/bin/python EDA_Insight/phase3_dashboard/customer_demographics.py`. Chart: `EDA_Insight/output/phase3/22..28_*.png`.
Data trung gian xuất ra: `phase3_dashboard/data/rfm_customer_segments.csv`,
`cohort_retention_matrix.csv`, `churn_risk_scores.csv` — xem `EDA_Insight/DATA_LINEAGE.md`.

*Reorganize 2026-07-20: di chuyển vào `EDA_Insight/phase3_dashboard/`, chart sang
`EDA_Insight/output/phase3/`. Nội dung/số liệu bên dưới giữ nguyên, chỉ path thay đổi.*

**Ngày viết:** 2026-07-20. **Người mới học data đọc được** — mỗi khái niệm (RFM, cohort, churn
risk, logistic) có giải thích ngắn trước khi vào số.

---

## 0. Dữ liệu dùng chung (áp cho toàn bộ báo cáo)

- Bảng: `orders`, `payments`, `customers`, `geography` (KHÔNG dùng `sales.csv` — đó là gross demand
  cho model forecast, không phải giá trị khách hàng thật, theo Phase 0 QC W1).
- **Non-cancelled orders** = `orders.order_status != 'cancelled'` (giữ delivered/returned/shipped/
  paid/created — đúng yêu cầu đề bài, không tự ý loại thêm).
- **Monetary = `payments.payment_value`** (net thực thu từng đơn, QC xác nhận khớp 100% — mục I1
  phase0_qc_report.md), KHÔNG dùng `sales.Revenue` (gross, kể cả đơn cancelled).
- **Snapshot date** (mốc tính Recency) = `orders.order_date.max()` = **2022-12-31** (ngày cuối dữ liệu).
- **Mẫu:** 88,123 khách có ≥1 đơn không-cancelled (= mẫu RFM). Khác với 90,246 khách có ≥1 đơn
  **bất kỳ** trạng thái (định nghĩa "khách từng mua hàng thực" trong scope Phase 0) — chênh **2,123
  khách chỉ toàn đơn cancelled**, bị loại khỏi RFM vì họ chưa từng thực sự nhận/thanh toán đơn nào.
  Tổng CRM vẫn là 121,930 khách — mọi % trong báo cáo đều ghi rõ đang chia trên mẫu nào.
- **238 khách pre-launch** (`signup_date < 2012-07-04`, phát hiện ở Phase 0 W8): tách riêng khỏi
  cohort chính theo đúng yêu cầu đề bài (khác khuyến nghị "gộp" ở QC W8 — ưu tiên yêu cầu mới nhất),
  báo cáo số liệu riêng ở mục 2.

---

## 1. RFM Segmentation

### RFM là gì? (giải thích nhanh)
RFM là 3 chỉ số đo "sức khoẻ" quan hệ với từng khách hàng:
- **Recency (R)** — bao lâu rồi khách chưa mua? (ít ngày = tốt)
- **Frequency (F)** — khách mua bao nhiêu đơn? (nhiều = tốt)
- **Monetary (M)** — khách đã chi bao nhiêu tiền? (nhiều = tốt)

Mỗi khách được chấm điểm 1-5 cho từng chỉ số (so với toàn bộ khách khác, dùng ngũ phân vị —
quintile), rồi gộp 3 điểm lại thành một **segment** có tên gọi (Champions, At Risk, Lost...) để dễ
ra quyết định marketing/CSKH.

### Câu hỏi & giả thuyết
Khách hàng nào đang mang lại giá trị, khách nào đang có nguy cơ mất, và nên ưu tiên hành động cho
nhóm nào trước? Giả thuyết: giá trị khách hàng phân phối lệch mạnh (Pareto) — thiểu số khách tạo
phần lớn doanh thu.

### Dữ liệu dùng
88,123 khách (mẫu RFM, xem mục 0). R/F/M tính trên đơn không-cancelled, Monetary = `payment_value`.
Điểm 1-5 dùng `pd.qcut` trên rank (tránh lỗi trùng bin do nhiều khách có cùng frequency).

### Findings (Descriptive)

| Segment | Số khách | % khách | Tổng Monetary (tỷ VND) | % Monetary | Monetary TB/khách (VND) | Recency TB (ngày) | Frequency TB |
|---|---:|---:|---:|---:|---:|---:|---:|
| Champions | 22,575 | 25.6% | 8.95 | **62.9%** | 396,438 | 274 | 15.88 |
| Loyal Customers | 16,974 | 19.3% | 2.88 | 20.3% | 169,914 | 787 | 7.02 |
| Lost | 21,682 | 24.6% | 0.46 | 3.2% | 21,158 | 2,563 | 1.26 |
| At Risk | 7,989 | 9.1% | 0.65 | 4.5% | 80,882 | 2,010 | 3.90 |
| Can't Lose Them | 2,251 | 2.6% | 0.49 | 3.5% | 218,601 | 1,783 | 8.61 |
| Hibernating | 3,327 | 3.8% | 0.27 | 1.9% | 81,035 | 2,399 | 1.60 |
| Promising | 5,375 | 6.1% | 0.21 | 1.4% | 38,217 | 1,105 | 1.48 |
| New Customers | 4,865 | 5.5% | 0.20 | 1.4% | 41,793 | 359 | 1.51 |
| Need Attention | 3,085 | 3.5% | 0.12 | 0.9% | 40,454 | 689 | 3.65 |

Tổng Monetary toàn mẫu ≈ **14.23 tỷ VND**. Chart: `../output/phase3/22_rfm_segment_summary.png`,
`../output/phase3/23_rfm_scatter.png`.

### Diagnostic — tại sao phân phối lệch vậy?
- **25.6% khách (Champions) tạo 62.9% giá trị** — Pareto rõ rệt, đúng với hầu hết mô hình bán lẻ
  lặp lại nhiều đơn. Đây là nhóm định nghĩa "core business", không phải nhóm mới cần tăng trưởng.
- **Lost chiếm tới 24.6% số khách nhưng chỉ 3.2% giá trị** — phần lớn trong số này gần như chưa bao
  giờ là khách trung thành (Frequency TB chỉ 1.26 đơn) → khả năng cứu lại thấp, không nên đầu tư
  nhiều ngân sách retention cho nhóm này.
- **Can't Lose Them (2,251 khách) có Monetary/khách 218,601 VND — cao thứ 2 sau Champions**, từng
  mua trung bình 8.61 đơn (gần bằng Loyal Customers) nhưng đã im lặng trung bình 1,783 ngày (~4.9
  năm) — đây là nhóm "đã từng rất tốt, đang mất dần", giá trị cứu lại/khách cao nhất trong các
  nhóm rủi ro → ưu tiên can thiệp hàng đầu (xem Prescriptive).

### Hạn chế
- Điểm R/F/M dùng **quintile tương đối** (so khách với nhau), KHÔNG phải ngưỡng tuyệt đối — một
  khách "Lost" theo RFM chỉ có nghĩa là thuộc 20% tệ nhất trong dữ liệu này, không chắc đã thực sự
  "bỏ đi" theo nghĩa tuyệt đối (xem đối chiếu ở mục 4 — 74% khách thực ra đã >365 ngày không mua).
- Rule gán tên segment (Champions/At Risk/...) là quy tắc phổ biến trong ngành nhưng do nhóm tự
  chọn ngưỡng (r≥4, f≥4...) — có thể điều chỉnh theo mục tiêu kinh doanh thực tế.
- Dữ liệu mô phỏng 11 năm — Recency trung bình toàn mẫu **1,282 ngày** (median 1,018 ngày, ~2.8
  năm) rất cao vì cửa sổ quan sát dài; so sánh segment PHẢI đặt trong ngữ cảnh cửa sổ 11 năm này,
  không so trực tiếp với chuẩn ngành thông thường (cửa sổ 1-2 năm).

---

## 2. Cohort Retention

### Cohort là gì? (giải thích nhanh)
Một **cohort** là nhóm khách hàng đăng ký (signup) trong cùng một tháng. **Retention theo cohort**
đo % khách của cohort đó còn quay lại mua hàng ở tháng thứ 1, 3, 6, 12... kể từ khi signup. Đây là
cách chuẩn để trả lời: "khách mới có gắn bó lâu dài không, và mất bao lâu để họ rời đi?"

### Câu hỏi & giả thuyết
Khách hàng có xu hướng giảm hoạt động dần theo thời gian kể từ khi đăng ký (decay curve) như hầu
hết mô hình e-commerce thực tế không?

### Dữ liệu dùng
121,692 khách (đã loại 238 khách pre-launch), 126 cohort tháng (2012-07 → 2022-12), "active" = có
≥1 đơn không-cancelled trong tháng offset đó. Mẫu số mỗi cohort = tổng số khách signup tháng đó
(không chỉ khách từng mua) — đúng chuẩn retention (đo cả khách chưa từng mua vẫn tính vào mẫu số).

### Findings (Descriptive)
Retention trung bình toàn kỳ (weighted theo số khách, chỉ tính cohort đã đủ thời gian quan sát đến
offset đó): **M1 ≈ 3.0% · M3 ≈ 2.9% · M6 ≈ 3.0% · M12 ≈ 2.9%**.

Chart: `../output/phase3/24_cohort_retention_heatmap.png` (đầy đủ 126 cohort × offset 0-15 tháng),
`../output/phase3/25_cohort_retention_curve.png` (đường trung bình, dễ đọc hơn).

**238 khách pre-launch:** 171 khách (71.8%) từng có đơn không-cancelled, tổng Monetary 28.7 triệu
VND, Frequency TB 6.68 đơn/khách — gần như KHÔNG khác biệt so với Frequency TB toàn mẫu RFM (6.67
đơn/khách). Kết luận: nhóm 238 khách này không phải segment đặc biệt về hành vi, chỉ là lỗi/nhiễu
dữ liệu signup_date — tách khỏi cohort chính là quyết định đúng nhưng không cần xử lý gì thêm về
mặt phân tích hành vi.

### Diagnostic — vì sao đường retention gần như PHẲNG, không giảm dần?
Đây là phát hiện quan trọng nhất của phần cohort: retention **không hề giảm dần theo tuổi cohort**
như một sản phẩm/thị trường thực thường thấy (decay curve điển hình: cao ở M1 rồi giảm dần). Ở đây
M1 (3.0%) ≈ M12 (2.9%) — chênh lệch nằm trong biên độ nhiễu tự nhiên (dao động 2.9-3.4% qua các
offset, xem `../output/phase3/25_cohort_retention_curve.png`).

**Diễn giải (correlation, không phải nhân quả đã kiểm chứng bằng thực nghiệm A/B):** khả năng cao
nhất là cơ chế sinh dữ liệu mô phỏng gán xác suất mua hàng gần như **hằng số theo tháng** cho mỗi
khách (không phụ thuộc "tuổi" quan hệ với shop), khác với hành vi khách hàng thực tế thường gắn bó
mạnh nhất ngay sau khi đăng ký rồi giảm dần. Điều này khớp với `avg_frequency` toàn mẫu RFM chỉ
6.67 đơn trải trên tối đa 126 tháng lịch sử → xác suất mua bất kỳ tháng nào ~3% là hợp lý về mặt số
học nếu hành vi ngẫu nhiên đều theo thời gian.

### Hạn chế
- Đây là dữ liệu **mô phỏng** — kết luận "không có decay theo cohort" chỉ đúng cho bộ dữ liệu này,
  KHÔNG được suy diễn rằng shop thật cũng vậy.
- Heatmap 126 hàng khó đọc trực quan ở kích thước nhỏ — nên xem file gốc phóng to, hoặc dùng chart
  đường (`25_cohort_retention_curve.png`) làm tóm tắt chính.
- Retention offset lớn (>12 tháng) có ít cohort đủ điều kiện quan sát hơn (cohort gần cuối kỳ dữ
  liệu chưa đủ thời gian trôi qua) — đã loại đúng bằng điều kiện `cohort_month + offset <= tháng
  cuối dữ liệu`, không có bias nội suy.

---

## 3. Demographics × RFM

### Câu hỏi & giả thuyết
Vùng/nhóm nhân khẩu nào tập trung nhiều khách giá trị cao (Champions) hơn — có khớp với phát hiện
per-capita ở `customer_demographics.md` mục 7 (West chi tiêu/khách cao hơn Central 62%) không?

### Dữ liệu dùng
88,123 khách RFM join `customers.zip` → `geography.region` (referential integrity 100%, theo QC).
age_group/gender **không dùng** làm biến phân khúc (đã kết luận "phẳng" ở mục 1-6 của
`customer_demographics.md`, không lặp lại ở đây).

### Findings (Descriptive) + Diagnostic

| Region | % Champions | % Lost |
|---|---:|---:|
| Central | 22.7% | 27.9% |
| East | 24.1% | 23.4% |
| West | **36.1%** | 21.4% |

Chart: `../output/phase3/26_rfm_region_heatmap.png`.

**West có tỷ trọng Champions cao nhất (36.1% vs Central 22.7%, East 24.1%) và tỷ trọng Lost thấp
nhất (21.4%)** — khớp hoàn toàn với phát hiện per-capita đã có (`customer_demographics.md` mục 7:
West chi tiêu/khách cao hơn Central 62%, cao hơn East 53%). Hai phương pháp độc lập (RFM segment và
per-capita revenue) cùng chỉ ra một kết luận → tăng độ tin cậy: **chất lượng khách ở West thực sự
tốt hơn**, không phải trùng hợp thống kê từ một cách tính.

### Hạn chế
- Vẫn là **correlation**: dữ liệu không có biến giải thích "tại sao" (marketing spend theo vùng,
  đối thủ cạnh tranh, thu nhập vùng...) để khẳng định nguyên nhân.
- West có quy mô khách nhỏ nhất (đã nêu ở mục 7 `customer_demographics.md`) — cỡ mẫu nhỏ hơn có thể
  khiến % dao động lớn hơn khi thêm/bớt vài trăm khách; không phải bằng chứng thống kê có kiểm định.

---

## 4. Predictive — Churn Risk

### Churn risk là gì? (giải thích nhanh)
Dự đoán khách nào **sắp ngừng mua** để can thiệp SỚM (voucher, email, gọi điện) trước khi họ rời
hẳn — hiệu quả hơn nhiều so với cố "cứu" khách đã mất từ lâu. Ở đây dùng 2 cách tiếp cận song song:
(1) **rule-based** — quy tắc đơn giản dễ giải thích cho vận hành; (2) **logistic regression** — mô
hình thống kê để kiểm chứng/xếp hạng độ tin cậy của rule.

### Câu hỏi & giả thuyết
Khách nào có nguy cơ churn cao dựa trên Recency + xu hướng Frequency gần đây, và mô hình đơn giản
có dự đoán được không?

### Dữ liệu dùng
88,123 khách RFM. Rule-based dùng Recency (ngày) + trend = (số đơn 180 ngày gần nhất) − (số đơn 180
ngày trước đó nữa). Logistic dùng **time-split** để tránh rò rỉ dữ liệu (data leakage): cutoff
2022-06-30, feature tính đến cutoff, nhãn "churned" = không mua gì trong 6 tháng SAU cutoff (dữ
liệu tương lai với thời điểm tính feature — đúng chuẩn validate mô hình dự đoán).

> **Giới hạn môi trường:** venv dự án không có `sklearn`/`scipy`/`statsmodels` → logistic regression
> viết tay bằng `numpy` (gradient descent, chuẩn hoá feature, L2 regularization nhẹ), AUC tính tay
> bằng công thức Mann-Whitney U (không cần scipy). Đây là bản **đơn giản, không phải mô hình sản
> xuất** — đủ để kiểm chứng rule-based, chưa nên dùng để tự động hoá quyết định.

### Findings — Rule-based (Descriptive)

| Tier | Ngưỡng | Số khách | Tổng Monetary (tỷ VND) |
|---|---|---:|---:|
| Đã rời bỏ | Recency > 365 ngày | 65,071 | 6.95 |
| Rủi ro cao | Recency > 180 ngày VÀ trend ≤ 0 | 11,762 | 3.29 |
| Rủi ro trung bình | Recency > 90 ngày VÀ trend < 0 | 471 | 0.28 |
| An toàn | còn lại | 10,819 | 3.71 |

Chart: `../output/phase3/27_churn_risk_summary.png`.

### Diagnostic — đối chiếu với RFM segment (mục 1)
**Phát hiện quan trọng:** RFM segment "Lost" chỉ có 21,682 khách (24.6% mẫu) nhưng churn-risk rule
(ngưỡng TUYỆT ĐỐI 365 ngày) cho thấy **65,071 khách (73.8% mẫu) đã hơn 1 năm không mua gì** — gấp 3
lần con số "Lost" theo RFM. Lý do: RFM dùng ngũ phân vị (quintile) — "Lost" LUÔN LUÔN là ~20-25% tệ
nhất bất kể mức độ tệ tuyệt đối là bao nhiêu, còn churn-risk dùng ngưỡng cố định 365 ngày nên phản
ánh đúng mức độ nghiêm trọng thực tế. **Bài học: không nên chỉ nhìn RFM segment để đánh giá quy mô
vấn đề churn — phải đối chiếu với ngưỡng tuyệt đối.**

### Findings — Logistic regression validation (Predictive, có kiểm chứng out-of-time)
- Tập validate: 87,589 khách có đơn ≤ 2022-06-30; churn rate thực tế 6 tháng sau = **87.4%** (đa số
  khách không mua lại trong 6 tháng bất kỳ — nhất quán với Recency trung bình rất cao ở mục 1).
- Train 70,071 / Test 17,518 khách (80/20, random_seed=42).
- **Accuracy 0.877, Precision 0.884, Recall 0.990, AUC 0.773.**
- Hệ số chuẩn hoá: `recency_days +0.211` (Recency cao → tăng nguy cơ churn — hợp lý), `frequency
  −0.330` (mua nhiều lần trong quá khứ → giảm nguy cơ — hợp lý), `log(monetary) −0.630` (chi tiêu
  nhiều → giảm nguy cơ, hệ số mạnh nhất), `trend_180d +0.025` (gần 0 — không có ý nghĩa rõ ràng,
  khả năng cộng tuyến với recency_days vì cả hai đều phản ánh hoạt động gần đây).
- Calibration curve (`../output/phase3/28_logistic_validation.png`) bám sát đường chéo lý tưởng → xác suất dự
  đoán đáng tin cậy để **xếp hạng** mức độ rủi ro, không chỉ để phân loại nhị phân.

### Hạn chế (phải đọc trước khi dùng)
- **Accuracy 0.877 chỉ nhỉnh hơn baseline "đoán tất cả đều churn" (~0.874, vì churn rate nền đã
  87.4%)** — do dữ liệu mất cân bằng nặng. Accuracy KHÔNG phải chỉ số nên nhìn ở đây; **AUC 0.773**
  (đáng tin — model xếp hạng đúng thứ tự rủi ro tốt hơn ngẫu nhiên đáng kể, ngẫu nhiên = 0.5) mới là
  chỉ số phản ánh giá trị thực của mô hình.
- Mô hình logistic chỉ tuyến tính, 4 feature đơn giản — chưa thử interaction terms, chưa so sánh với
  mô hình khác (tree-based...), chưa có sklearn nên chưa cross-validate nhiều fold.
- Ngưỡng rule-based (90/180/365 ngày) chọn theo kinh nghiệm phổ biến ngành, **chưa tối ưu hoá bằng
  dữ liệu** (vd. chưa tìm ngưỡng tối ưu hoá F1/lợi nhuận kỳ vọng) — nên tinh chỉnh ở Giai đoạn 5 nếu
  triển khai thật.
- Nhãn "churned" dựa trên cửa sổ 6 tháng cố định — khách hàng có chu kỳ mua thưa (VD 8-9 tháng/lần)
  có thể bị gắn nhãn sai "churned" dù vẫn còn hoạt động về sau.

---

## 5. Prescriptive — Đề xuất hành động định lượng

> Tất cả số liệu dưới đây lấy trực tiếp từ script `customer_demographics.py`, không suy diễn thêm.

**1. Bảo vệ Champions (22,575 khách, 62.9% giá trị = 8.95 tỷ VND) bằng chương trình VIP/loyalty,
KHÔNG chạy khuyến mãi đại trà cho nhóm này.** Recency TB chỉ 274 ngày — vẫn đang hoạt động tốt, rủi
ro chính là bị đối thủ lôi kéo chứ không phải churn tự nhiên. Đề xuất: ngân sách retention ưu tiên
giữ chân (free shipping tier cao, early access sản phẩm mới) thay vì giảm giá — tránh "đốt tiền"
giảm giá cho khách vốn đã trung thành.

**2. Ưu tiên win-back "Can't Lose Them" trước — 2,251 khách, giá trị lịch sử 492 triệu VND, Monetary
TB/khách 218,601 VND (cao thứ 2 toàn bộ segment), từng mua TB 8.61 đơn nhưng đã im lặng TB 1,783
ngày.** Đây là nhóm ROI/khách cao nhất trong các nhóm rủi ro — nếu chỉ có ngân sách cho MỘT chiến
dịch win-back, chọn nhóm này trước. Đề xuất: gọi điện/email cá nhân hoá + voucher giá trị cao (vd.
15-20% một đơn), không cần giảm giá sâu đại trà.

**3. Rủi ro cao (11,762 khách, 3.29 tỷ VND) — dồn ngân sách vào top 20% giá trị nhất trong tier
(2,352 khách) vì nhóm này đã chiếm 46.9% giá trị của cả tier (1.54/3.29 tỷ VND).** Chạy campaign
reactivation (email + voucher) cho 2,352 khách này trước, phần còn lại (9,410 khách, giá trị thấp
hơn) dùng kênh chi phí thấp hơn (email tự động, không gọi điện). **Giả định thận trọng** (chưa có
số đo A/B thật): nếu tỷ lệ reactivation đạt 10-15% (benchmark phổ biến ngành cho email win-back,
KHÔNG phải số đo từ dữ liệu này) → ước tính giữ lại được ~235-353 khách, tương đương ~154-231 triệu
VND giá trị lịch sử được bảo toàn một phần. **Cần A/B test thật để xác nhận trước khi scale** (xem
mục Giai đoạn 4).

**4. "Đã rời bỏ" (65,071 khách, 6.95 tỷ VND) — KHÔNG chạy campaign đại trà (chi phí không hiệu
quả), chỉ target top 10% giá trị nhất (6,507 khách, đã chiếm 39.8% giá trị của cả nhóm = 2.76 tỷ
VND).** Phần còn lại (58,564 khách, giá trị TB thấp) nên loại khỏi ngân sách retention chủ động — ưu
tiên ngân sách cho mục 2-3 có ROI/khách cao hơn nhiều.

**5. Region: tăng ngân sách acquisition cho West.** West chỉ 14,741 khách (nhỏ nhất 3 vùng) nhưng
per-capita cao nhất (0.249 triệu VND/khách, cao hơn Central 62%) VÀ tỷ trọng Champions cao nhất
(36.1% vs Central 22.7%) — hai phương pháp độc lập cùng xác nhận chất lượng khách West tốt hơn.
Đề xuất: dịch chuyển một phần ngân sách acquisition từ Central/East sang West, kỳ vọng CLV/khách
mới cao hơn (dựa trên hành vi khách hiện tại — **chưa kiểm chứng bằng thử nghiệm thực tế**, xem hạn
chế mục 3).

---

## Tổng kết

### Kết quả đạt được
- Mở rộng thành công `customer_demographics.py` (thêm section 22-28, ~360 dòng) và
  `customer_demographics.md` (thêm mục 8) — script chạy lại từ đầu không lỗi (~7s), chỉ đọc `data/`.
- Tạo mới `dashboard_rfm_cohort.md` (file này) — báo cáo đầy đủ 4 cấp Descriptive → Diagnostic →
  Predictive → Prescriptive cho RFM, Cohort, Demographics×RFM, Churn risk.
- 7 chart mới: `../output/phase3/22_rfm_segment_summary.png`, `23_rfm_scatter.png`,
  `24_cohort_retention_heatmap.png`, `25_cohort_retention_curve.png`, `26_rfm_region_heatmap.png`,
  `27_churn_risk_summary.png`, `28_logistic_validation.png`.

### File đã tạo/sửa
| File | Thay đổi |
|---|---|
| `EDA_Insight/phase3_dashboard/customer_demographics.py` | Sửa — thêm section 22-28 (nối tiếp, không đổi code cũ); 2026-07-20 thêm export 3 CSV data trung gian |
| `EDA_Insight/phase3_dashboard/customer_demographics.md` | Sửa — thêm mục 8 (tóm tắt tham chiếu nhanh) |
| `EDA_Insight/phase3_dashboard/dashboard_rfm_cohort.md` | Mới — báo cáo đầy đủ (file này) |
| `EDA_Insight/output/phase3/22..28_*.png` | Mới — 7 chart |
| `EDA_Insight/phase3_dashboard/data/rfm_customer_segments.csv`, `cohort_retention_matrix.csv`, `churn_risk_scores.csv` | Mới (2026-07-20) — xem `EDA_Insight/DATA_LINEAGE.md` |

### Phát hiện đáng chú ý nhất (theo thứ tự ưu tiên đọc)
1. **Pareto rõ rệt:** 25.6% khách (Champions) tạo 62.9% giá trị (14.23 tỷ VND toàn mẫu RFM).
2. **Cohort retention gần như PHẲNG (~3% mọi offset 1-12 tháng)** — không có decay theo tuổi cohort,
   khác hành vi e-commerce thực tế thường thấy — nghi ngờ đặc tính mô phỏng dữ liệu (xem mục 2 Diagnostic).
3. **RFM "Lost" (24.6% mẫu) đánh giá thấp mức độ nghiêm trọng thực tế** — churn-risk ngưỡng tuyệt
   đối cho thấy 73.8% mẫu (65,071 khách) đã hơn 1 năm không mua — gấp 3 lần.
4. **West region nhỏ nhất về quy mô nhưng chất lượng khách tốt nhất** — xác nhận chéo bằng 2 phương
   pháp độc lập (per-capita revenue từ `customer_demographics.md` mục 7 + % Champions ở đây).
5. Logistic regression AUC 0.773 (xếp hạng tốt) nhưng accuracy gần bằng baseline do mất cân bằng
   87.4% churn — nhắc nhở luôn nhìn AUC/Precision-Recall, không chỉ accuracy, với bài toán churn.

### Khuyến nghị Giai đoạn 4 (Prescriptive tổng hợp — phối hợp BA + DA)
- Gộp 5 đề xuất ở mục 5 vào bức tranh prescriptive tổng thể của Phase B (forecast Revenue/COGS) —
  BA cần đối chiếu ngân sách campaign đề xuất (mục 5.2, 5.3) với mùa vụ thấp điểm/cao điểm đã tìm ở
  Giai đoạn 1-2 (đỉnh sale T7-T8, T11-T12) để KHÔNG chạy win-back trùng thời điểm khuyến mãi lớn
  (tránh nhiễu tín hiệu, tốn ngân sách trùng).
- Đề xuất mục 5.3 và 5.4 (ước tính reactivation 10-15%) **cần thiết kế A/B test thật** trước khi
  scale toàn bộ: nhóm treatment (nhận voucher/email) vs control (không nhận), đo tỷ lệ quay lại mua
  trong 90 ngày — theo đúng khung "A/B test: hypothesis, metric chính, sample size, thời gian chạy"
  mà vai trò DA cần thiết kế ở bước tiếp theo.
- Region reallocation (mục 5.5) nên thử nghiệm quy mô nhỏ trước (vd. tăng 10-15% ngân sách
  acquisition West trong 1 quý), đo CAC và CLV 90 ngày đầu của cohort mới trước khi cam kết ngân
  sách lớn.

### Khuyến nghị Giai đoạn 5 (chốt giả định insight A → model B — phối hợp DS + BA)
- **Giả định cần chốt trước khi đưa churn risk vào production:** ngưỡng rule-based hiện tại
  (90/180/365 ngày) là kinh nghiệm, chưa tối ưu bằng dữ liệu — DS nên thử nhiều ngưỡng, tối ưu theo
  F1 hoặc lợi nhuận kỳ vọng (chi phí campaign vs giá trị khách giữ được), có sklearn/scipy trong môi
  trường production (khác venv EDA hiện tại) để dùng logistic regression chuẩn (regularization path,
  cross-validation, class_weight cho dữ liệu mất cân bằng) thay vì bản numpy thủ công ở đây.
- **Retention phẳng theo cohort (mục 2 Diagnostic) là giả định QUAN TRỌNG cần DS xác nhận lại** khi
  nhận dữ liệu — nếu forecast Phần B hoặc mô hình CLV giả định có "decay curve" theo tuổi khách hàng
  (common trong nhiều mô hình CLV chuẩn, vd BG/NBD), giả định đó **KHÔNG khớp với dữ liệu quan sát
  được ở đây** — cần điều chỉnh mô hình hoặc dùng phương pháp không giả định decay (vd. mô hình xác
  suất mua hằng số theo thời gian).
- Model churn production nên tách riêng theo segment giá trị (Champions/Loyal riêng, Can't Lose
  Them/At Risk riêng) thay vì 1 model chung — vì động lực churn và giá trị can thiệp khác nhau rõ
  rệt giữa các nhóm (mục 5).
