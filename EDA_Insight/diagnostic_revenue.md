# Diagnostic Revenue — kết hợp orders + order_items + products + customers + geography + promotions + returns

Tầng **Diagnostic** (tại sao xảy ra?) tiếp nối 6 chart Descriptive đã có (`eda_training_charts.py`, `tet_effect.py`). Script: `revenue_diagnostic.py` — join `order_items` (grain sản phẩm/đơn) với 6 bảng còn lại, sanity check khớp `sales.csv` 0.000% sai lệch. Chart lưu tại `output/07..14_*.png`.

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

*Tạo ngày 17/07/2026 — script: `EDA_Insight/revenue_diagnostic.py`.*
