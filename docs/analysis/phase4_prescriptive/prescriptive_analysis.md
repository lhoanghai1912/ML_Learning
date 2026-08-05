# Prescriptive Analysis — 4 đề xuất định lượng (Giai đoạn 4)

**Ngày chạy:** 2026-07-21 · `.venv/bin/python` (pandas, không sklearn/scipy/statsmodels).
**Kế thừa:** `phase2_diagnostic/diagnostic_summary.md` (break 2019 do khối lượng, không phải giá;
promo gây bán dưới giá vốn; West margin ~40% mix/60% giá thật) + `phase3_dashboard/dashboard_rfm_cohort.md`
(Pareto Champions, Can't Lose Them ROI/khách cao nhất trong nhóm rủi ro) + `customer_demographics.md`
(West nhỏ nhất nhưng chất lượng khách tốt nhất).
**Code nguồn số liệu:** `prescriptive_analysis.py`. Data trung gian mới: `phase4_prescriptive/data/*.csv`
(5 file). Chart: `EDA_Insight/output/phase4/36..38_*.png`.
**Người mới học data đọc được** — mỗi đề xuất: vấn đề (số cũ) → hành động → công thức + giả định ước
tính tác động → rủi ro/giới hạn của chính ước tính đó.

---

## Đề xuất 1 — Floor price cho promotion

### Vấn đề (số liệu Phase 2)
`category_below_cost_rate.csv` + `monthly_unit_price_ratio.csv`: 47,9% dòng order_items **có** promo
bán dưới giá vốn (vs 0,18% dòng không promo — chênh 266 lần). Tập trung T7-9 (`Urban Blowout`,
`Fall Launch`) và T11-12 (`Year-End Sale`); nặng nhất ở Casual (22,3% dòng dưới giá vốn) và
Streetwear (21,4% dòng, nhưng chiếm ~80% doanh thu nên kéo margin toàn shop mạnh nhất).

### Hành động đề xuất
Đặt **giá sàn (floor price) = giá vốn (`cogs`) theo từng SKU**, áp dụng khi tính giá bán sau khuyến
mãi — không cho `unit_price` xuống dưới `cogs` ở BẤT KỲ dòng hàng nào, kể cả khi promo giảm % sâu
hay giảm cứng (`Urban Blowout`). Ưu tiên review trước 2 category Casual, Streetwear và 2 giai đoạn
T7-9, T11-12.

### Ước tính tác động (mô phỏng lịch sử — "nếu áp floor price từ đầu")

**Công thức:** với mỗi dòng `order_items`, `unit_price_floor = max(unit_price, cogs)`. Giữ nguyên
`quantity` (giả định không đổi — xem rủi ro bên dưới). `line_revenue_floor = quantity × unit_price_floor`.
COGS không đổi (catalog cố định) → margin tăng thêm (VNĐ) = doanh thu tăng thêm.

Tính trên **toàn bộ 714.669 dòng `order_items` lịch sử** (không lọc năm, không lọc trạng thái đơn — gross,
khớp định nghĩa `sales.csv` theo Phase 0/2):

| Chỉ số | Thực tế | Nếu áp floor price | Chênh lệch |
|---|---:|---:|---:|
| Số dòng bán dưới giá vốn | 133.052 (18,62%) | 0 | −133.052 |
| Revenue (gross, toàn kỳ) | 16,430 tỷ VND | 16,892 tỷ VND | **+0,462 tỷ VND** |
| COGS | 14,163 tỷ VND | 14,163 tỷ VND | 0 (không đổi) |
| Gross margin % | 13,80% | 16,15% | **+2,36 điểm %** |
| Gross margin (VNĐ) | 2,267 tỷ VND | 2,729 tỷ VND | **+0,462 tỷ VND** |

Theo category, phần margin tăng thêm dồn chủ yếu ở Streetwear (do chiếm ~80% doanh thu, dù % tăng/dòng
không phải cao nhất):

| Category | Margin tăng thêm (tỷ VND) | Margin tăng thêm (điểm %) |
|---|---:|---:|
| Streetwear | 0,409 | +2,62pp |
| Outdoor | 0,041 | +1,35pp |
| Casual | 0,008 | +1,55pp |
| GenZ | 0,003 | +0,81pp |

Chart: `36_floor_price_margin_before_after.png`. Data: `data/floor_price_simulation_overall.csv`,
`data/floor_price_simulation_by_category.csv`.

### Rủi ro/giới hạn của ước tính này
- **Giả định KHÔNG có co giãn cầu theo giá (no demand elasticity)** — mô phỏng giữ nguyên `quantity`
  bán ra dù giá tăng. Thực tế nâng giá sàn có thể làm giảm số lượng bán (đặc biệt các dòng bị "cắn"
  giá vốn nặng nhất là do promo giảm giá sâu cố ý kích cầu) → +0,462 tỷ VND là **cận trên lý thuyết**,
  con số thật khi triển khai sẽ thấp hơn.
- +0,462 tỷ VND là tính trên **toàn bộ 10 năm lịch sử** (2013-2022), không phải/năm — trung bình
  ~46 triệu VND/năm, một con số nhỏ so với margin toàn shop hằng năm (margin toàn kỳ 2,267 tỷ/10 năm
  ≈ 227 triệu/năm) nhưng **tỷ trọng tăng tương đối lớn (+17% margin thực tế toàn kỳ)**.
  → Đây là biện pháp bảo toàn margin đã có, KHÔNG phải nguồn tăng trưởng doanh thu — phù hợp bổ sung
  cho, không thay thế, hướng acquisition/retention (Đề xuất 4).
- Chỉ mô phỏng ở mức dòng hàng — không tính lại hiệu ứng thứ cấp (VD promo giảm giá sâu vẫn có thể là
  công cụ thu hút khách mới hiệu quả dù bán dưới giá vốn — dữ liệu hiện tại không đo được ROI marketing
  của việc "lỗ có chủ đích" này).

---

## Đề xuất 2 — Win-back/retention theo RFM segment

### Vấn đề (số liệu Phase 3)
`rfm_customer_segments.csv`: "Can't Lose Them" (2.251 khách, Monetary TB/khách 218.601 VND — cao thứ 2
toàn bộ segment, từng mua TB 8,61 đơn) đã im lặng TB 1.783 ngày — ROI/khách cao nhất trong các nhóm rủi
ro. "At Risk" (7.989 khách, Monetary TB/khách 80.882 VND, im lặng TB 2.010 ngày) — quy mô lớn hơn nhưng
giá trị/khách thấp hơn.

### Hành động đề xuất
Ưu tiên ngân sách win-back cá nhân hoá (gọi điện/email + voucher) cho "Can't Lose Them" trước, sau đó
"At Risk" — theo đúng khuyến nghị `dashboard_rfm_cohort.md` mục 5.2.

### Ước tính tác động (KỊCH BẢN, không phải dự báo)

**Công thức:** `AOV segment = tổng Monetary segment / tổng Frequency segment` (giá trị trung bình 1 đơn
hàng lịch sử của khách trong segment — dùng làm proxy doanh thu cho **1 đơn quay lại**, KHÔNG dùng toàn
bộ Monetary trung bình vì đó là tổng nhiều năm lịch sử, gán hết cho 1 lần quay lại sẽ phóng đại). Với
mỗi kịch bản tăng tỷ lệ giữ chân +X điểm % (X = 5/10/15, **là giả định minh hoạ, không suy ra từ dữ
liệu thật — cần A/B test để xác nhận**):

`Doanh thu tiềm năng = (Số khách segment × X%) × AOV segment`

| Segment | Số khách | Monetary TB/khách | AOV TB/đơn | +5pp | +10pp | +15pp |
|---|---:|---:|---:|---:|---:|---:|
| Can't Lose Them | 2.251 | 218.601 VND | 25.393 VND | +2,9 triệu VND | +5,7 triệu VND | +8,6 triệu VND |
| At Risk | 7.989 | 80.882 VND | 20.756 VND | +8,3 triệu VND | +16,6 triệu VND | +24,9 triệu VND |

Chart: `37_winback_revenue_scenario.png`. Data: `data/winback_scenario_by_segment.csv`.

### Rủi ro/giới hạn của ước tính này
- **Đây là ước tính kịch bản (scenario), không phải dự báo** — tỷ lệ +5/10/15pp không lấy từ A/B test
  thật, chỉ là mốc minh hoạ để thấy độ lớn tương đối giữa 2 segment.
- Con số tuyệt đối **rất nhỏ** (vài triệu VND) vì công thức chỉ tính 1 đơn quay lại/khách — nếu khách
  quay lại và duy trì mua nhiều đơn tiếp theo (giống hành vi trước khi rời), giá trị thực tế sẽ cao hơn
  nhiều lần con số này; nhưng dữ liệu hiện tại không có cách nào ước lượng "sẽ mua lại bao nhiêu đơn"
  mà không suy đoán — nên cố tình chọn công thức bảo thủ (1 đơn) thay vì phóng đại bằng cả Monetary.
- Không có chi phí campaign (voucher, nhân sự gọi điện, email) để tính ROI ròng — con số trên là
  **doanh thu tiềm năng gộp**, chưa trừ chi phí thực hiện.
- Nhóm "Can't Lose Them" giá trị/khách cao hơn nhưng quy mô nhỏ hơn 3,5 lần "At Risk" → nếu ngân sách
  giới hạn cho 1 chiến dịch, "Can't Lose Them" có ROI/khách tốt hơn nhưng "At Risk" có tổng tiềm năng
  lớn hơn (8,3-24,9 triệu vs 2,9-8,6 triệu) — cần cân đối theo ngân sách thực tế, không chỉ nhìn 1 chỉ
  số.

---

## Đề xuất 3 — Nhân rộng pricing practice của West

### Vấn đề (số liệu Phase 2)
`region_margin_mix_decomposition.csv`: margin West 14,20% vs Central 13,15%/East 13,31% — Phase 2 đã
tách: ~40% chênh lệch do mix sản phẩm (West bán nhiều Outdoor hơn), **~60% do giá/discount thực sự tốt
hơn trong CÙNG category** (`category_region_margin_controlled.csv`).

### Hành động đề xuất
Tìm hiểu vận hành pricing/discount thực tế ở West (dữ liệu giao dịch không giải thích được "tại sao",
cần khảo sát/phỏng vấn vận hành) và áp dụng thử nghiệm sang Central/East, ưu tiên category có gap lớn
nhất (Outdoor, Streetwear).

### Ước tính tác động (mô phỏng lịch sử — kịch bản 60%)

**Công thức:** với mỗi category ở Central/East, `gap_pp = margin_pct(West, category) − margin_pct(vùng, category)`
(chỉ tính khi gap dương — nơi West thực sự tốt hơn). `target_margin = margin_pct(vùng) + 60% × gap_pp`
(giả định theo Phase 2: chỉ 60% chênh lệch margin có thể nhân rộng bằng "giá thật tốt hơn", 40% còn lại
là do mix sản phẩm — không đạt được chỉ bằng thay đổi giá). `cogs_mới = revenue × (1 − target_margin/100)`,
`margin tăng thêm = cogs_cũ − cogs_mới`.

| Region | Category | Margin hiện tại | Margin West | Gap | Target margin | Margin tăng thêm |
|---|---|---:|---:|---:|---:|---:|
| Central | Casual | 11,59% | 11,78% | +0,19pp | 11,71% | 0,1 triệu VND |
| Central | GenZ | 19,95% | 18,28% | −1,67pp (West thấp hơn) | 19,95% (giữ nguyên) | 0 |
| Central | Outdoor | 15,72% | 16,74% | +1,03pp | 16,33% | 3,4 triệu VND |
| Central | Streetwear | 12,67% | 13,28% | +0,61pp | 13,03% | 14,6 triệu VND |
| East | Casual | 11,31% | 11,78% | +0,47pp | 11,60% | 0,5 triệu VND |
| East | GenZ | 18,83% | 18,28% | −0,55pp (West thấp hơn) | 18,83% (giữ nguyên) | 0 |
| East | Outdoor | 15,37% | 16,74% | +1,37pp | 16,19% | 6,9 triệu VND |
| East | Streetwear | 12,93% | 13,28% | +0,34pp | 13,14% | 12,6 triệu VND |

**Tổng margin tăng thêm: +0,038 tỷ VND (38 triệu VND)** trên tổng revenue 15,689 tỷ VND (Central+East+West
gộp, theo `category_region_margin_controlled.csv`). Margin toàn shop (3 vùng): 13,47% → 13,71%
(**+0,24 điểm %**).

Chart: `38_west_margin_replication_uplift.png`. Data: `data/west_margin_replication_by_category_region.csv`,
`data/west_margin_replication_summary.csv`.

### Rủi ro/giới hạn của ước tính này
- **Hệ số 60% lấy từ Phase 2 là ước lượng điểm ở CẤP VÙNG (mix-adjustment toàn vùng), không phải tính
  riêng từng category** — áp dụng lại hệ số này cho gap ở TỪNG category (đã tự nó kiểm soát mix theo
  category) là một giả định đơn giản hoá, có thể không chính xác 100% cho từng category cụ thể (VD
  GenZ ở Central/East margin đã CAO HƠN West — áp dụng máy móc công thức sẽ cho kết quả âm vô lý, nên đã
  chặn gap ở 0 cho các trường hợp này).
- **Con số tuyệt đối rất nhỏ (38 triệu VND/10 năm ≈ 3,8 triệu/năm)** — vì gap margin giữa các vùng vốn
  đã nhỏ (dưới 1,4pp mọi category), quy mô doanh thu Central/East cho phần "còn thiếu" so với West cũng
  không lớn. Đây là bằng chứng số cho thấy: **nhân rộng West không phải đòn bẩy tài chính lớn**, giá trị
  chính của bài học West là ĐỊNH HƯỚNG vận hành pricing (learning), không phải nguồn tăng margin đáng kể.
- Chưa biết "West làm gì khác" về mặt vận hành thực tế (không có dữ liệu discount policy theo vùng) —
  nên con số 38 triệu VND chỉ là **tiềm năng lý thuyết nếu đạt được**, chưa có kế hoạch hành động cụ
  thể để đạt gap đó.

---

## Đề xuất 4 — Định hướng acquisition/retention (KHÔNG giảm giá/tăng khuyến mãi)

### Vì sao không đề xuất giảm giá
Phase 2 đã chứng minh bằng số: break 2019 (revenue −38,6%) đi cùng ASP **+2,4%** và AOV **+2,7%** (tăng,
không giảm), trong khi qty/số đơn/khách active giảm 28-40%. Đây là **vấn đề khối lượng/khách, không
phải giá** — giảm giá thêm/tăng khuyến mãi sẽ KHÔNG giải quyết đúng nguyên nhân, mà còn làm trầm trọng
thêm cơ chế bán dưới giá vốn đã nêu ở Đề xuất 1.

### Định hướng chiến lược (không ước tính số tuyệt đối — không có dữ liệu marketing spend)

1. **Acquisition — ưu tiên vùng West.** West nhỏ nhất về quy mô khách (14.741 khách) nhưng per-capita
   revenue cao hơn Central 62% (`customer_demographics.md` mục 7) VÀ tỷ trọng Champions cao nhất (36,1%
   vs Central 22,7% — `dashboard_rfm_cohort.md` mục 3). Hai phương pháp độc lập cùng xác nhận chất lượng
   khách West tốt hơn → logic: dịch chuyển một phần ngân sách acquisition từ Central/East sang West có
   khả năng mang lại khách mới chất lượng cao hơn trên mỗi đồng chi acquisition — **chưa kiểm chứng bằng
   thử nghiệm thực tế, cần pilot nhỏ trước** (đề xuất gốc: `dashboard_rfm_cohort.md` mục Prescriptive #4).
2. **Retention — bảo vệ Champions trước khi mở rộng khách mới.** Champions (22.575 khách, 62,9% giá trị
   = 8,95 tỷ VND) đang hoạt động tốt (Recency TB 274 ngày) — rủi ro chính là bị đối thủ lôi kéo, không
   phải churn tự nhiên. Logic: chi phí giữ 1 khách Champions luôn thấp hơn chi phí có được 1 khách mới
   tương đương giá trị — ưu tiên chương trình loyalty/VIP (không phải giảm giá đại trà) trước khi dồn
   ngân sách 100% vào tân khách.
3. **Không cắt ngân sách 1 kênh marketing cụ thể để "sửa" break 2019** — cả 6 kênh (`order_source`) rơi
   đồng đều 37-41% (Phase 2 mục 2.4), nên vấn đề là hệ thống/toàn platform, không phải hiệu suất riêng 1
   kênh. Cắt giảm 1 kênh sẽ không khắc phục nguyên nhân gốc.
4. **Root cause thật của sụt khách 2019 vẫn ngoài phạm vi dữ liệu giao dịch nội bộ** (Phase 2 mục 3.4) —
   trước khi cam kết ngân sách acquisition/retention lớn, nên ưu tiên thu thập thêm dữ liệu ngoài (khảo
   sát khách rời đi, benchmark đối thủ, xác nhận có phải do dữ liệu mô phỏng hay không) để tránh đầu tư
   sai hướng dựa trên suy đoán.

---

## Giới hạn phân tích (áp dụng cho cả 4 đề xuất)

1. **Không có dữ liệu chi phí (marketing spend, chi phí vận hành campaign)** — mọi số "doanh thu/margin
   tăng thêm" ở Đề xuất 1-3 đều là **gộp (gross)**, chưa trừ chi phí thực hiện. ROI ròng cần dữ liệu chi
   phí thực tế mới tính được.
2. **Đề xuất 1 và 3 giả định KHÔNG có co giãn cầu theo giá** (nâng giá không làm giảm số lượng bán) — đây
   là giả định lạc quan, các con số nên hiểu là **cận trên lý thuyết**, không phải mức tăng chắc chắn.
3. **Đề xuất 2 dùng tỷ lệ retention giả định (+5/10/15pp), không suy ra từ dữ liệu thật** — cần A/B test
   thật (nhóm treatment nhận voucher/email vs control) để có số liệu tin cậy trước khi scale ngân sách.
4. **Đề xuất 3 áp hệ số 60% (tính ở cấp vùng) xuống cấp category** — đơn giản hoá, có thể không chính
   xác cho từng category riêng lẻ (đã xử lý trường hợp gap âm bằng cách giữ nguyên margin, không suy diễn
   thêm).
5. **Toàn bộ ước tính dùng dữ liệu lịch sử 2013-2022** — không đảm bảo áp dụng y hệt cho 548 ngày dự báo
   2023-2024 (Phần B), đặc biệt nếu công ty đổi chính sách promo/pricing sau khi đọc báo cáo này.
6. **Con số tuyệt đối ở Đề xuất 2, 3 khá nhỏ so với quy mô doanh thu toàn shop** (16,43 tỷ VND toàn kỳ)
   — không nên kỳ vọng các biện pháp này "cứu" doanh thu ở quy mô break 2019; giá trị chính là bảo toàn
   margin (Đề xuất 1, 3) và tối ưu ROI/khách hiện có (Đề xuất 2), KHÔNG thay thế được nhu cầu giải quyết
   root cause sụt khách 2019 (Đề xuất 4 điểm 4).

---

## Tổng kết

### File đã tạo/sửa
| File | Thay đổi |
|---|---|
| `EDA_Insight/phase4_prescriptive/prescriptive_analysis.py` | Mới — script tính 3 mô phỏng định lượng (Đề xuất 1-3) |
| `EDA_Insight/phase4_prescriptive/prescriptive_analysis.md` | Mới — báo cáo này |
| `EDA_Insight/phase4_prescriptive/data/floor_price_simulation_overall.csv` | Mới — margin toàn shop trước/sau floor price |
| `EDA_Insight/phase4_prescriptive/data/floor_price_simulation_by_category.csv` | Mới — margin tăng thêm theo category |
| `EDA_Insight/phase4_prescriptive/data/winback_scenario_by_segment.csv` | Mới — kịch bản win-back Can't Lose Them/At Risk |
| `EDA_Insight/phase4_prescriptive/data/west_margin_replication_by_category_region.csv` | Mới — chi tiết margin tăng thêm theo region×category |
| `EDA_Insight/phase4_prescriptive/data/west_margin_replication_summary.csv` | Mới — tổng hợp toàn shop |
| `EDA_Insight/output/phase4/36_floor_price_margin_before_after.png` | Mới |
| `EDA_Insight/output/phase4/37_winback_revenue_scenario.png` | Mới |
| `EDA_Insight/output/phase4/38_west_margin_replication_uplift.png` | Mới |
| `EDA_Insight/DATA_LINEAGE.md` | Sửa — thêm mục "Phase 4" |

### Tóm tắt số liệu chính (theo thứ tự đọc)
1. **Floor price:** loại bỏ hoàn toàn bán dưới giá vốn (18,62% dòng lịch sử) → margin toàn shop
   13,80% → 16,15% (+2,36pp), +0,462 tỷ VND margin toàn kỳ 10 năm. Giả định không co giãn cầu — cận
   trên lý thuyết.
2. **Win-back:** Can't Lose Them (2.251 khách) ROI/khách cao nhất nhưng tổng tiềm năng nhỏ (2,9-8,6
   triệu VND theo kịch bản +5/15pp); At Risk (7.989 khách) tổng tiềm năng lớn hơn (8,3-24,9 triệu VND) —
   đều là kịch bản minh hoạ, cần A/B test thật.
3. **Nhân rộng West:** chỉ +38 triệu VND/10 năm (margin toàn shop +0,24pp) — gap margin vùng vốn đã nhỏ,
   giá trị chính là bài học vận hành, không phải đòn bẩy tài chính lớn.
4. **Acquisition/retention:** không ước tính số tuyệt đối (thiếu dữ liệu chi phí marketing) — logic rõ
   ràng: ưu tiên West (acquisition) + Champions (retention), không cắt kênh nào, không giảm giá.

### Khuyến nghị cho Giai đoạn 10 (pm — tổng hợp story A→B)
1. **Câu chuyện chính xuyên suốt A→B: "vấn đề là khối lượng/khách, không phải giá"** — dùng nhất quán từ
   Phase 2 (chẩn đoán) đến Phase 4 (đề xuất) đến Phần B (feature engineering không dùng giá làm driver
   chính) — đây là mạch logic quan trọng nhất cần nêu trong báo cáo cuối.
2. **Xếp 4 đề xuất theo độ lớn tác động ước tính, không theo thứ tự trình bày:** Floor price (Đề xuất 1,
   +0,462 tỷ VND) là biện pháp có tác động định lượng lớn nhất và dễ triển khai nhất (chỉ cần đặt ngưỡng
   giá, không cần dữ liệu ngoài) — nên là đề xuất "quick win" nổi bật nhất trong bài trình bày.
3. **Nêu rõ Đề xuất 2, 3 có con số tuyệt đối nhỏ nhưng giá trị định hướng cao** — tránh để giám khảo hiểu
   nhầm "team đề xuất giải pháp không đáng kể"; nhấn mạnh đây là bảo toàn/tối ưu trên nền tảng hiện có,
   bổ sung cho Đề xuất 1 và 4, không phải giải pháp độc lập "cứu" doanh thu.
4. **Đề xuất 4 (acquisition/retention) là nơi cần nối rõ nhất với Phần B/Predictive** — nếu Giai đoạn 5-9
   xây dựng được feature "khách active"/"cohort mới" cho forecast, nên liên hệ ngược lại đề xuất này
   trong báo cáo cuối để tạo mạch A→B liền mạch (chẩn đoán → đề xuất → mô hình → dự báo).
5. **Mọi số liệu tác động trong Đề xuất 1-3 cần đính kèm rõ giả định** (không co giãn cầu, X% retention
   giả định, hệ số 60% ở cấp vùng) khi trình bày — giám khảo có thể hỏi trực tiếp về các giả định này,
   cần chuẩn bị trả lời "nếu giả định sai thì sao" (đã liệt kê ở mục Giới hạn phân tích).
