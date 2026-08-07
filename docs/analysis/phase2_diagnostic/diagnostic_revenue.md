# Diagnostic Revenue — kết hợp orders + order_items + products + customers + geography + promotions + returns

Tầng **Diagnostic** (tại sao xảy ra?) tiếp nối 6 chart Descriptive đã có (`../phase1_descriptive/eda_training_charts.py`, `../phase1_descriptive/tet_effect.py`). Script: `revenue_diagnostic.py` (mở rộng: notebook `EDA_diagnostic.ipynb` cùng thư mục) — join `order_items` (grain sản phẩm/đơn) với 6 bảng còn lại, sanity check khớp `sales.csv` 0.000% sai lệch. Chart lưu tại `../output/phase2/07..14_*.png`.

*Reorganize 2026-07-20: di chuyển vào `EDA_Insight/phase2_diagnostic/`, chart sang `EDA_Insight/output/phase2/` — xem `EDA_Insight/DATA_LINEAGE.md`. `phase2_diagnostic/data/` hiện để trống, chờ Phase 2 chính thức chạy đầy đủ (xem `PROGRESS.md`, trạng thái Giai đoạn 2 vẫn "pending" — nội dung ở đây là bản sơ bộ, số liệu đã verify khớp báo cáo nhưng CHƯA phải deliverable chính thức của Giai đoạn 2).*

## 1. Category — Streetwear ngày càng lấn át (`07_category_share.png`)

| | Casual | GenZ | Outdoor | Streetwear |
|---|---|---|---|---|
| 2013 | 1.8% | 1.6% | 19.8% | 76.8% |
| 2022 | 4.6% | 2.5% | 9.0% | **83.8%** |

Outdoor mất hơn nửa tỷ trọng (19.8%→9.0%) trong 10 năm, Streetwear hút hết phần đó. Danh mục ngày càng lệ thuộc 1 category duy nhất — rủi ro tập trung.

**Prescriptive gợi ý:** trước khi tăng ngân sách marketing đều cho cả 4 category, ưu tiên Streetwear (đang thắng) và đánh giá lại có nên duy trì Outdoor hay tái định vị.

## 2. Region — East dẫn đầu nhưng cả 3 vùng cùng chung nhịp suy giảm (`08_region_trend.png`)

2022 (tỷ VND): East 0.5 · Central 0.4 · West 0.2. Không vùng nào tách khỏi xu hướng chung (break 2019 xảy ra đồng loạt) → nguyên nhân sụt giảm là hệ thống (platform-wide), không phải vấn đề riêng 1 khu vực.

## 3. Khách mới vs khách cũ (`09_new_vs_repeat.png`)

Tỷ trọng doanh thu từ "khách cũ" (đơn không phải lần mua đầu tiên của khách): 2013 66.1% → 2018 94.7% → 2022 96.4%.

Lưu ý đọc đúng: đây là tỷ trọng theo **tenure tích lũy** (pool khách càng lớn theo thời gian thì đơn "không phải lần đầu" càng chiếm đa số), **không phải** bằng chứng lòng trung thành — vì tần suất mua trung bình toàn kỳ chỉ 1.83 đơn/khách (đã chốt ở Phase 0). Điểm đáng chú ý hơn: nhìn tổng chiều cao cột, doanh thu từ khách MỚI (lát đỏ) gần như biến mất sau 2019 (từ ~0.3–0.5 tỷ/năm xuống dưới 0.1 tỷ) — khớp và làm rõ thêm câu chuyện break 2019 đã biết (khách active giảm 28%, tần suất mua giảm).

## 4. Waterfall: Gross booked → Net thực thu (`10_waterfall_net_revenue.png`)

| Bước | Tỷ VND | % của Gross |
|---|---|---|
| Gross booked (= Revenue trong sales.csv) | 15.69 | 100% |
| − Hủy đơn (cancelled) | −1.45 | 9.2% |
| − Chiết khấu (discount) | −0.68 | 4.3% |
| − Hoàn tiền (returns) | −0.51 | 3.3% |
| **= Net thực thu** | **13.05** | **83.2%** |

"Revenue" trong sales.csv là số ghi nhận gộp (đã xác nhận ở Phase 0), **không phải** tiền thực về. 16.8% hao hụt, đòn bẩy lớn nhất là **hủy đơn** (gấp đôi discount, gấp gần 3 lần refund).

**Prescriptive gợi ý:** giảm tỷ lệ hủy đơn (9.2%) là lever mạnh nhất để tăng net revenue — mạnh hơn tối ưu discount hay giảm return.

## 5. Kênh order_source (`11_channel_trend.png`)

Toàn bộ 6 kênh (organic_search, paid_search, social_media, email_campaign, referral, direct) đều gãy cùng lúc năm 2019 — organic_search 0.51→0.32 tỷ, paid_search 0.40→0.25 tỷ. Xác nhận thêm: break 2019 là vấn đề hệ thống/retention, **không phải** 1 kênh marketing cụ thể suy yếu.

## 6. LTV theo acquisition_channel (`12_ltv_by_channel.png`)

Revenue trung bình/khách trọn đời gần như **bằng nhau** giữa mọi kênh: 0.17–0.18 triệu VND, chênh lệch kênh cao nhất vs thấp nhất chỉ ~6%.

**Đọc kết quả:** acquisition_channel không phải yếu tố phân hoá chất lượng khách trong dữ liệu này. Prescriptive: nên tối ưu theo **chi phí acquisition** (kênh nào rẻ hơn) thay vì kỳ vọng "kênh này mang khách xịn hơn kênh kia" — vì dữ liệu không ủng hộ giả định đó.

## 7. Payment method (`13_payment_method_share.png`)

Cơ cấu gần như đứng yên suốt 10 năm: credit_card ~55%, paypal ~15%, cod ~15%, apple_pay ~10%, bank_transfer ~5% (2013 và 2022 lệch nhau <0.5 điểm %). Không có dịch chuyển sang thanh toán số — khác với kỳ vọng thông thường về e-commerce trưởng thành dần. Feature này gần như hằng số, không đáng đưa vào model Phần B.

## 8. Hiệu ứng khuyến mãi (`14_promo_effect.png`)

- AOV đơn **không** có promo: 27,945 VND — AOV đơn **có** promo: 21,896 VND (**thấp hơn 21.6%**).
- Ngược trực giác: promo thường kỳ vọng đẩy giá trị giỏ hàng lên, ở đây lại thấp hơn.
- Doanh thu theo loại: promo dạng "percentage" áp đảo "fixed" (5.06 tỷ vs 0.38 tỷ) — nhưng cũng vì có 45 promo percentage so với chỉ 5 promo fixed trong `promotions.csv`, không hẳn phản ánh loại nào hiệu quả hơn trên cùng 1 đơn vị promo.

**Prescriptive gợi ý:** cần điều tra thêm (không nằm trong scope diagnostic này) — có thể promo đang bị dùng cho hàng thanh lý/giá thấp thay vì kích cầu giỏ hàng lớn. Đáng để Phần A module RFM/Predictive đào sâu trước khi kết luận promo "không hiệu quả".

## Giới hạn / lưu ý phương pháp

- Toàn bộ số liệu lọc năm 2013–2022 (bỏ nửa cuối 2012), đồng bộ với các chart Descriptive trước.
- "Revenue" = gross (đã xác nhận Phase 0); waterfall ở mục 4 là lớp bổ sung để thấy phần thực thu.
- LTV (mục 6) tính trên toàn bộ lịch sử trong data (2012–2022), không phải LTV dự phóng.
- promo_id_2 luôn null (0% điền) — không có đơn nào stack 2 promo dù `stackable_flag` tồn tại trong `promotions.csv`; đã bỏ qua promo_id_2.

*Tạo ngày 17/07/2026 — script: `EDA_Insight/phase2_diagnostic/revenue_diagnostic.py`.*

---

# PHẦN MỞ RỘNG — Giai đoạn 2 chính thức (2026-07-20)

Từ đây là nội dung Giai đoạn 2 (Diagnostic) **chính thức**, trả lời đủ 5 câu hỏi bắt buộc theo đề bài/PROGRESS.md, kế thừa toàn bộ mục 1-8 phía trên (không tính lại, chỉ mở rộng `revenue_diagnostic.py` — mục 15-21 mới). Chart mới: `../output/phase2/29..35_*.png`. Data trung gian export vào `phase2_diagnostic/data/` (8 file CSV, trước đây để trống có chủ đích — nay đã hết pending).

## 9. Vì sao 2019-2021 sụt mạnh? — tách giá vs khối lượng (`29_yearly_price_volume_decompose.png`)

| Chỉ số | 2018 | 2019 | YoY |
|---|---:|---:|---:|
| Revenue | 1.85 tỷ | 1.14 tỷ | **-38.6%** |
| ASP (giá bán TB/đơn vị) | — | — | **+2.4%** |
| Số lượng bán (qty) | 337,646 | 202,653 | **-40.0%** |
| Số đơn | 69,510 | 41,601 | **-40.2%** |
| Khách active | 37,922 | 27,312 | **-28.0%** |
| AOV | — | — | **+2.7%** |

**Kết luận rõ ràng — KHÔNG mơ hồ:** break 2019 **không phải** do giảm giá bán (ASP thực ra tăng nhẹ +2.4%, AOV cũng tăng +2.7%) — mà do **khối lượng giao dịch sụp đổ**: ít đơn hơn 40%, ít khách mua hơn 28%. Đây là vấn đề **retention/acquisition**, không phải vấn đề **pricing**.

## 10. Cường độ khuyến mãi theo năm — có đổi khác tại 2019 không? (`30_promo_intensity_by_year.png`)

Join `order_items` + `promotions` theo `promo_id` (FK sạch 100% theo QC, 0 bản ghi mồ côi):

| Năm | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | **2019** | 2020 | 2021 | 2022 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| % doanh thu có promo | 39.9 | 30.8 | 39.4 | 29.5 | 38.4 | 29.4 | **38.4** | 32.0 | 38.9 | 32.0 |

Cường độ promo dao động theo **chu kỳ lẻ/chẵn năm** (năm lẻ có thêm "Rural Special"/"Urban Blowout" nên cao hơn ~8-10pp) — **2019 nằm đúng nhịp năm lẻ bình thường (38.4%), không có bất thường**. → **Loại bỏ giả thuyết (c) "đổi mix/cường độ promotion gây break 2019"** — mix category cũng gần như không đổi quanh 2019 (Streetwear 80-83%, Outdoor 11-15%, xem lại mục 1). Nguyên nhân break phải nằm ở phía cầu (khách/đơn), không phải phía cung (giá, promo, mix sản phẩm).

## 11. Cơ chế lỗ gộp — chứng minh bằng số (`31_unit_price_ratio_by_month.png`)

QC (W2/W3) phát hiện 18.6% dòng order_items bán dưới giá vốn → 382 ngày lỗ gộp, dồn T7-8/T11-12. Chứng minh cơ chế:

| | % dòng bán dưới giá vốn |
|---|---:|
| Dòng hàng **CÓ** promo (`promo_id` not null) | **47.86%** |
| Dòng hàng **KHÔNG** promo | **0.18%** |

Chênh lệch ~266 lần — **bằng chứng trực tiếp: khuyến mãi là cơ chế gây bán dưới giá vốn**, gần như không xảy ra ngoài promo. Theo tháng, tỷ lệ dưới giá vốn cao nhất: T12 (47.3%), T9 (34.9%), T7 (31.9%), T8 (29.2%) — trùng khớp promo `Year-End Sale` (T11-T1, giảm 20%), `Fall Launch` (T8-10, giảm 10%), `Urban Blowout` (T7-9, giảm cứng 50 nghìn VND/đơn vị, chỉ áp Streetwear) chạy đúng các tháng này. `unit_price/catalog price` trung bình rơi xuống 0.80-0.88 các tháng T7-8, T12 — xác nhận giảm giá sâu (không phải lỗi nhập liệu).

## 12. Bán dưới giá vốn có tập trung Casual/Streetwear? (`32_below_cost_rate_by_category.png`)

| Category | % dòng bán dưới giá vốn | % doanh thu category đến từ dòng dưới giá vốn |
|---|---:|---:|
| **Casual** | **22.30%** | 17.93% |
| **Streetwear** | **21.36%** | 18.00% |
| Outdoor | 18.10% | 17.20% |
| GenZ | 9.83% | 10.78% |

**Xác nhận giả thuyết Phase 1:** Casual (margin thấp nhất 11.75% — Phase 1) và Streetwear (79.9% doanh thu, margin 13.24%) đúng là 2 category có tỷ lệ dòng bán dưới giá vốn cao nhất. Vì Streetwear chiếm ~80% doanh thu, tỷ lệ 21.36% dòng dưới giá vốn của riêng category này đã đủ kéo margin toàn shop xuống — đây là **nguyên nhân định lượng** của "Streetwear gánh doanh thu nhưng margin không cao nhất" (phát hiện Phase 1 mục 2.4).

## 13. Margin category/region — kiểm soát biến nhiễu mix (`33_category_region_margin_controlled.png`)

Region margin actual (Phase 1): East 13.64%, Central 13.47%, West 14.53%. Câu hỏi: West cao hơn do **mix category khác** (bán nhiều sản phẩm margin cao hơn) hay do **giá/discount thực sự tốt hơn**?

Phương pháp: tính "margin mix-adjusted" — áp trọng số category **toàn quốc** (Streetwear 80.1%, Outdoor 14.9%, Casual 2.9%, GenZ 2.1%) lên margin riêng từng category của TỪNG region, so với margin thực tế của region đó.

| Region | Margin thực tế | Margin mix-adjusted | Chênh lệch do mix (pp) |
|---|---:|---:|---:|
| East | 13.31% | 13.38% | -0.07 |
| Central | 13.15% | 13.24% | -0.10 |
| **West** | **14.20%** | **13.86%** | **+0.35** |

**Đọc số:** khoảng cách margin thực tế giữa West và Central là 14.20% − 13.15% = 1.06pp. Nếu loại bỏ hiệu ứng mix (giả định West có cùng cơ cấu category toàn quốc), khoảng cách còn 13.86% − 13.24% = 0.61pp. Tức là: **~40% chênh lệch margin West-Central đến từ mix category** (West bán tỷ trọng Outdoor cao hơn hẳn — 25.8% doanh thu West là Outdoor, so với ~11.5% ở Central/East — margin Outdoor 16.0% cao hơn Streetwear 12.9%), **~60% còn lại đến từ giá/discount thực sự tốt hơn trong CÙNG category** (VD Outdoor riêng ở West margin 16.74% > Outdoor toàn quốc 16.01%; Streetwear ở West margin 13.28% > Streetwear toàn quốc 12.92%). → Kết luận: **cả 2 yếu tố cùng đóng góp**, không thể quy hết cho "cơ cấu sản phẩm" — West thực sự bán giá/discount tốt hơn, không chỉ là ảo giác thống kê từ mix.

## 14. Marketing channel (`order_source`) — revenue & margin theo năm (`34_channel_revenue_margin_trend.png`)

| Kênh | Sụt 2018→2019 |
|---|---:|
| email_campaign | -41.0% |
| social_media | -39.9% |
| referral | -39.1% |
| organic_search | -37.7% |
| direct | -37.4% |
| paid_search | -37.3% |

Chênh lệch giữa kênh rơi mạnh nhất/nhẹ nhất chỉ **3.7pp** — cực kỳ đồng đều. Margin theo kênh cũng dao động cùng biên độ theo năm (9-17%), không kênh nào tách xu hướng. **Xác nhận thêm (không phải phát hiện mới): break 2019 là vấn đề hệ thống/retention toàn platform, không phải 1 kênh marketing cụ thể suy yếu** — khớp hoàn toàn với phát hiện gốc ở mục 5 phía trên, nay có thêm lát cắt margin.

## 15. Tết x cường độ khuyến mãi (`35_tet_promo_overlap.png`)

Đối chiếu số promo (`promotions.csv`) trùng cửa sổ ±30 ngày quanh mồng 1 Tết mỗi năm với `dip_pct`/`pre_week_pct` đã tính ở `tet_yearly_stats.csv` (Phase 1):

| Năm | Số promo trùng Tết | Promo | dip_pct | pre_week_pct |
|---|---:|---|---:|---:|
| 2013 | 1 | Rural Special 2013 | -27.2% | -34.1% |
| 2014 | 1 | Year-End Sale 2013 | -27.2% | -35.5% |
| 2015 | 2 | Spring Sale 2015; Rural Special 2015 | -14.4% | -19.9% |
| 2016 | 0 | — | -31.8% | -36.1% |
| 2017 | 2 | Year-End Sale 2016; Rural Special 2017 | -9.8% | -42.2% |
| 2018 | 1 | Spring Sale 2018 | -22.4% | -35.0% |
| 2019 | 1 | Rural Special 2019 | **-39.8%** | -3.6% |
| 2020 | 1 | Year-End Sale 2019 | -29.0% | -47.4% |
| 2021 | 1 | Rural Special 2021 | -24.8% | -44.4% |
| 2022 | 1 | Year-End Sale 2021 | -11.3% | -10.4% |

`corr(n_promo_overlap_tet, dip_pct) = +0.646` (n=10) — có promo chạy quanh Tết đi cùng dip **nhẹ hơn** (promo bù đắp một phần sụt giảm mùa thấp điểm); `corr(n_promo_overlap_tet, pre_week_pct) = +0.065` — gần như không liên hệ với tuần ngay trước Tết. **Với n=10 năm, đây chỉ là tương quan gợi ý, KHÔNG đủ mẫu để kết luận nhân quả** — 2019 là ngoại lệ đáng chú ý (chỉ 1 promo nhưng dip sâu nhất -39.8%, trong khi pre-week lại nhẹ nhất -3.6%), cho thấy hiệu ứng Tết bị chi phối bởi nhiều yếu tố khác (đặc biệt là break 2019 tổng thể) hơn là riêng promo.

## Chốt 5 câu hỏi Diagnostic bắt buộc

| # | Câu hỏi | Trả lời (số liệu) | Mức độ chắc chắn |
|---|---|---|---|
| 1 | Vì sao 2019-2021 sụt mạnh? | Khối lượng sụp (qty -40.0%, đơn -40.2%, khách -28.0%), giá bán KHÔNG giảm (ASP +2.4%), mix/promo không đổi bất thường | **Cao** — 3 phép đo độc lập (giá, khối lượng, mix/promo) đều chỉ cùng 1 hướng |
| 2 | Cơ chế lỗ gộp? | Promo gây 47.9% dòng bán dưới giá vốn (vs 0.18% không promo), dồn đúng tháng promo chạy | **Cao** — chênh lệch 266 lần, trùng khớp lịch promo tuyệt đối |
| 3 | Margin category/region do đâu? | Casual/Streetwear bán dưới giá vốn nhiều nhất (khớp margin thấp); West margin cao ~40% do mix, ~60% do giá thật | **Trung bình-cao** — đã kiểm soát biến nhiễu bằng mix-adjustment, nhưng chưa có test thống kê chính thức |
| 4 | Kênh marketing có liên quan break 2019? | Không — mọi kênh rơi đồng đều 37-41% | **Cao** — nhất quán với 3 phát hiện độc lập trước (region, category, channel) |
| 5 | Tết có tương quan promo? | Yếu, chỉ gợi ý (+0.65 với dip, ~0 với pre-week), n=10 quá nhỏ | **Thấp** — không đủ mẫu, cần thêm dữ liệu hoặc phương pháp khác ở Giai đoạn 5 |

**Break 2019 — kết luận cuối cùng của Giai đoạn 2:** đã loại trừ được giá bán, mix category, cường độ promotion, và 1 kênh marketing cụ thể là nguyên nhân. Nguyên nhân còn lại, nhất quán với mọi bằng chứng thu thập được (mục 3 — khách mới gần biến mất sau 2019; mục 9 — orders/khách active rơi cùng biên độ mọi kênh), là **sụp đổ về phía cầu: mất khách mới + khách active giảm trên diện rộng, không phải vấn đề giá/sản phẩm/kênh cụ thể**. Dữ liệu hiện có **không có biến giải thích** (marketing spend, sự kiện cạnh tranh, thay đổi chính sách) để xác định NGUYÊN NHÂN GỐC của việc mất khách — đây là giới hạn cứng của bộ dữ liệu, cần nêu rõ ở Giai đoạn 5 khi chốt giả định cho model.

*Cập nhật 2026-07-20 — mở rộng bởi DA, script: `revenue_diagnostic.py` mục 15-21, notebook: `EDA_diagnostic.ipynb`.*
