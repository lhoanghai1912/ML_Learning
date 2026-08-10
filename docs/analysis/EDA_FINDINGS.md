# EDA Findings — Vin Datathon 2026

Tài liệu tổng (index) — tóm tắt + dashboard requirements. Phân tích chi tiết từng chart tách theo đúng 4 notebook, đọc ở 4 file riêng (mỗi file = 1 giai đoạn, khớp 1-1 với notebook tương ứng):

| Giai đoạn | Notebook | Phân tích chi tiết |
|---|---|---|
| A — Thời vụ & biến động theo thời gian | `notebooks/02a_eda_thoi_vu.ipynb` | [`eda_findings_thoi_vu.md`](./eda_findings_thoi_vu.md) |
| B — Chẩn đoán nguyên nhân | `notebooks/02b_eda_nguyen_nhan.ipynb` | [`eda_findings_nguyen_nhan.md`](./eda_findings_nguyen_nhan.md) |
| C — Phân khúc khách hàng | `notebooks/02c_eda_khach_hang.ipynb` | [`eda_findings_khach_hang.md`](./eda_findings_khach_hang.md) |
| D — Đề xuất hành động | `notebooks/02d_eda_de_xuat.ipynb` | [`eda_findings_de_xuat.md`](./eda_findings_de_xuat.md) |

Nguồn dữ liệu: 14 bảng raw CSV (`data/raw/`), `sales` qua Trino mart `mart_revenue_daily`. Coverage 2012-07-04 → 2022-12-31 (2012 chỉ nửa năm, không so YoY 2013). Mọi số verify được lại bằng cách chạy code cell tương ứng trong notebook.

## Tóm tắt — 10 phát hiện chính

1. **Đỉnh doanh thu thật là 2016** (2.105 tỷ VND/năm), không phải 2018. Suy giảm bắt đầu **Quý 4/2018** (YoY tháng 10 -23.6%, tháng 11 -32.7%), không phải đột ngột 01/01/2019. 2022 mới hồi phục 63% mức đỉnh, chưa về lại quỹ đạo cũ.
2. **Nguyên nhân sụt giảm 2018→2019: 100% do khối lượng, không phải giá.** ASP tăng nhẹ +2.4% trong khi Revenue -38.6%; Qty -40%, số đơn/khách active -28%. Đồng đều trên mọi vùng/kênh/nhóm tuổi — cú sốc hệ thống, không phải 1 phân khúc cụ thể.
3. **Gốc rễ dài hạn: khách mới cạn dần từ 2013** — 5-6 năm TRƯỚC khi doanh thu sụt. Doanh nghiệp sống bằng tệp khách cũ tích lũy tới khi cạn (% doanh thu khách cũ: 66.1%→96.4%, 2013→2022).
4. **Chu kỳ khuyến mãi "Urban Blowout" (`fixed`, năm LẺ, Tháng 8) là nguyên nhân trực tiếp margin âm định kỳ** — 99.65% dòng hàng liên quan bán dưới giá vốn, giá bán chỉ 59.6% giá vốn. T8 năm chẵn margin +19.9%, năm lẻ -34.5%.
5. **Hiệu ứng Tết phần lớn là nhiễu trộn với mùa vụ** — top 5 ngày doanh thu cao nhất TOÀN KỲ đều rơi cuối T5-đầu T6 (mùa cao điểm), không phải ngày Tết nào. Mùa cao điểm thật: T4-T6; thấp điểm: T11-T1 (ngược mùa mua sắm cuối năm phương Tây).
6. **Giá trị khách hàng cực lệch (Pareto gắt)**: Champions 25.6% khách nắm 62.9% giá trị. Lost 24.6% khách (gần bằng Champions về số lượng) chỉ còn 3.2% giá trị.
7. **Bug dữ liệu nghiêm trọng đã phát hiện + fix**: `customers.signup_date` không phản ánh quan hệ mua bán thật (89.3% khách có đơn TRƯỚC ngày signup). Cohort retention tính trên trường này chỉ là base rate ngẫu nhiên (~3%), KHÔNG PHẢI retention thật. Đã fix ở tầng dbt (model song song `int_cohort_first_order`) — retention thật cao gấp ~2 lần số cũ.
8. **Đáy retention là hiệu ứng MÙA VỤ, không phải vòng đời khách hàng** — 10/12 nhóm cohort (83%) có đáy retention rơi đúng Tháng 1 dương lịch dù offset kể từ ngày mua đầu trải rộng 1-10 tháng tùy tháng bắt đầu.
9. **3 đề xuất định lượng, độ lớn chênh nhau rất xa**: floor-pricing (+0.462 tỷ VND) lớn hơn win-back (~0.033 tỷ) và đồng bộ pricing vùng (0.038 tỷ) khoảng 12-14 lần. Ưu tiên floor-pricing (sửa 5 chương trình khuyến mãi `fixed`) trước.
10. **Model forecast (Phần B) học đúng hướng** (dự báo đi ngang theo mức 2022, không ngoại suy tăng) nhưng có rủi ro cụ thể đã định lượng: T8/2023 (năm lẻ, đúng chu kỳ Urban Blowout) khả năng bị over-forecast vì `lag_365` tra về T8/2022 (năm chẵn, bình thường).

**Đã đóng (2026-08-10)**: mart chẩn đoán nguyên nhân (gap RICE #1 nêu ở mục Dashboard dưới) — `mart_revenue_diagnostic_yearly` + `mart_promo_margin_diagnostic`, xem chi tiết PROCESS.md.

---

## Hình dung Dashboard — yêu cầu rút ra từ EDA

Mục này không phải spec kỹ thuật (chưa phải việc của EDA) — là bản phác thảo NHU CẦU dashboard dựa trên phát hiện thật, đối chiếu với 6 mart dbt đã có (`mart_revenue_daily`, `mart_customer_segments`, `mart_channel_perf`, `mart_cohort_retention`) để biết cái nào dựng được NGAY và cái nào còn thiếu mart nguồn.

### Trang 1 — Tổng quan doanh thu (Revenue Overview)

Câu hỏi trả lời: doanh thu đang ở đâu so với lịch sử, xu hướng gần đây thế nào.

| Thành phần | Nguồn dữ liệu | Sẵn sàng |
|---|---|---|
| Line chart Revenue/COGS/MA30 theo ngày, có mốc break | `mart_revenue_daily` (đã có `revenue_ma30`, `revenue_yoy_pct`, `revenue_rank_desc`) | Có sẵn |
| Heatmap năm × tháng | `mart_revenue_daily` (group by `year`/`month` có sẵn) | Có sẵn |
| Card so sánh cùng kỳ (YoY) | `mart_revenue_daily.revenue_yoy_pct` | Có sẵn |
| Cảnh báo mùa vụ (T8 năm lẻ margin âm) | CHƯA có cột "năm chẵn/lẻ" hay cờ promo trong mart | **Thiếu** — cần thêm cột hoặc mart phụ (xem Trang 3) |

### Trang 2 — Doanh thu theo lát cắt (Category / Region / Channel)

| Thành phần | Nguồn dữ liệu | Sẵn sàng |
|---|---|---|
| Trend category/region/channel theo năm | `mart_channel_perf` (đúng grain long-format `dimension_type`) | Có sẵn |
| AOV có/không promo | `mart_channel_perf` (`dimension_type='promo'`) | Có sẵn |
| Region × Category cross (2 chiều đồng thời) | KHÔNG có — `mart_channel_perf` chỉ 1 chiều/lần (`dimension_type`) | **Thiếu** — cần mart mới hoặc pivot ở BI tool |

### Trang 3 — Chẩn đoán nguyên nhân (Diagnostic) — ĐÃ ĐÓNG (2026-08-10)

~~Đây là nhóm phát hiện có giá trị cao nhất phiên này... hoàn toàn chưa có mart nào expose~~ → **ĐÃ LÀM.** 2 mart mới (`dbt_datathon/models/marts/mart_revenue_diagnostic_yearly.sql`, `mart_promo_margin_diagnostic.sql`) + 1 intermediate dùng chung (`int_diagnostic_line_items.sql`). Verify đối chiếu Trino vs số notebook đã công bố khớp tuyệt đối (gross/cancelled/discount, repeat share, ASP-volume 2018→2019, below-cost promo/category). Chi tiết: PROCESS.md log 2026-08-10 "Mart chẩn đoán nguyên nhân".

| Thành phần | Nguồn dữ liệu | Sẵn sàng |
|---|---|---|
| ASP vs Volume theo năm (index 2018=100) | `mart_revenue_diagnostic_yearly` (`asp`, `qty`, `n_orders`, `n_active_cust`) | **Có sẵn** |
| Waterfall Gross → Net (hủy đơn/chiết khấu/hoàn tiền) | `mart_revenue_diagnostic_yearly` (`gross_booked`/`cancelled_loss`/`discount_loss`/`refund_loss`/`net_revenue`) | **Có sẵn** |
| % dòng bán dưới giá vốn theo category/promo/tháng | `mart_promo_margin_diagnostic` (grain year×month×category×has_promo) | **Có sẵn** |
| Cờ "năm chẵn/lẻ" + lịch khuyến mãi | `mart_promo_margin_diagnostic.is_odd_year` (kết hợp `month`+`has_promo`) | **Có sẵn** |

Phát hiện phụ khi build: `refund_loss` tổng mart (0.487 tỷ) thấp hơn số notebook gốc từng công bố (0.511 tỷ) — notebook gốc tính `refund_loss` KHÔNG lọc năm (khác mọi cột khác đều lọc 2013-2022), mart sửa đúng sự không nhất quán đó (2.115/39.939 dòng `returns.csv` thuộc đơn năm 2012 bị loại đúng). Số mart đáng tin hơn số notebook cũ ở điểm này.

### Trang 4 — Khách hàng (Customer / RFM / Cohort)

| Thành phần | Nguồn dữ liệu | Sẵn sàng |
|---|---|---|
| RFM segment overview (9 nhóm, %khách, %giá trị) | `mart_customer_segments` | Có sẵn |
| Cohort retention curve (đường cong tổng) | `mart_cohort_retention` (build hôm nay, dùng `int_cohort_first_order` — retention ĐÚNG) | Có sẵn |
| Cohort retention TÁCH THEO NĂM (so sánh cohort 2016 vs 2022) | `int_cohort_first_order` (intermediate, query được qua Trino, chưa "expose" mart riêng) | **Một phần** — có dữ liệu nhưng chưa có mart tiện dùng cho BI tool thông thường (thường chỉ đọc mart, không đọc intermediate) |
| Cohort tách theo tháng bắt đầu (kiểm định mùa vụ) | Không có mart — tính trong notebook | **Thiếu**, ưu tiên thấp (đây là phân tích 1 lần để kiểm định giả thuyết, không phải nhu cầu theo dõi liên tục) |
| Demographics theo tuổi | Không có mart — `li` join | **Thiếu**, nhưng ưu tiên thấp (đã kết luận tuổi KHÔNG phân biệt hành vi — dashboard theo dõi liên tục ít giá trị) |

### Trang 5 — Đề xuất & kịch bản (Prescriptive / What-if)

Khác biệt về bản chất: đây là tính toán CÓ GIẢ ĐỊNH (`PRICE_EFFECT_SHARE=0.6`, `uplift_scenario=5/10/15%`) — **không nên** là mart tĩnh (giả định thay đổi thì mart phải build lại). Phù hợp hơn với 1 trong 2 hướng:
- BI tool có tính năng "what-if slider" (Power BI/Tableau parameter) — build sẵn mart RAW (chưa áp giả định: margin theo category/region thật, danh sách khách At Risk/Can't Lose Them kèm AOV) rồi để dashboard tự nhân giả định.
- Giữ như hiện tại: notebook/script chạy theo yêu cầu, không cần dashboard real-time cho phần này (đúng bản chất "đề xuất", không phải "theo dõi vận hành").

### Tổng kết ưu tiên nếu triển khai

| Ưu tiên | Việc | Lý do |
|---|---|---|
| ~~1~~ ĐÃ XONG | ~~Mart chẩn đoán (Trang 3)~~ | Xong 2026-08-10 — `mart_revenue_diagnostic_yearly` + `mart_promo_margin_diagnostic` |
| 1 (mới) | Mart cohort theo năm (Trang 4) | Có sẵn dữ liệu nguồn (`int_cohort_first_order`), chỉ cần thêm 1 view/mart nhẹ |
| 3 | Region × Category cross (Trang 2) | Nhu cầu cụ thể (đã dùng ở đề xuất 3), nhưng độ lớn tác động đã đo thấp (0.038 tỷ) — không khẩn |
| Không cần mart | Trang 5 (What-if) | Bản chất động, mart tĩnh không phù hợp |

Đây là **phác thảo yêu cầu, không phải commitment triển khai** — quyết có làm dashboard/mart mới nào ở trên là việc của PO, ngoài phạm vi EDA.
