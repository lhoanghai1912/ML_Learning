# Cầu nối A → B: Insight nào của Phần A quyết định thiết kế model Phần B

- **Vai trò:** PM (T10.3) — deliverable trọng tâm chấm điểm *tính liên kết* của đề bài. Nhúng vào giữa `final_report.md` (sau Phần A, trước Phần B).
- **Phạm vi:** KHÔNG tạo số mới. Chỉ chỉ rõ **mối nhân quả**: mỗi phát hiện đã chốt ở Phần A (Phase 1–5) dẫn thẳng tới **quyết định thiết kế nào** ở Phần B (Phase 6–9). Số đã truy nguồn trong Phần A/B tương ứng.
- **Luận điểm 1 câu:** Phần B không chọn feature/target/model theo cảm tính — **từng lựa chọn đều là hệ quả trực tiếp của một phát hiện định lượng ở Phần A.**

---

## Bảng ánh xạ Insight A → Quyết định B (đọc nhanh)

| # | Phát hiện Phần A (nguồn) | Quyết định Phần B (nguồn) | Cơ chế nhân quả |
|---|---|---|---|
| L1 | **Cohort retention phẳng ~3–6%**, không giảm theo tuổi quan hệ (A Tầng 3.2; Phase 3 + xác nhận Phase 5) | **Bỏ toàn bộ feature hành vi khách; chỉ dùng feature thuần lịch** (B mục 0.1; Phase 6) | Data khách sinh ngẫu nhiên độc lập theo thời gian ⇒ CLV/khách-active/tần suất mua lặp = nhiễu, "chạy được" nhưng vô nghĩa dự báo ⇒ loại từ gốc |
| L2 | **Target khớp `sales.csv` = gross demand** (kể cả đơn huỷ), MAPE 0.000%; net lệch 13,9% (A Tầng 1.3 gap gross/net 13,37%; Phase 5) | **Target = gross demand**, Revenue & COGS train độc lập (B mục 0.2) | Chốt đúng mục tiêu ngay từ đầu ⇒ tránh cả Phần B build nhầm net revenue |
| L3 | **Tết KHÔNG cố định qua các năm** (dip mồng 1 dao động −9,8%→−39,8%) (A Tầng 1.2; Phase 1) | Dùng **biến liên tục `days_from_tet`**, KHÔNG áp 1 hệ số Tết cứng (B mục 0.1, 3.1) | Pattern Tết đổi mỗi năm ⇒ hệ số cố định sai ⇒ để model học theo khoảng cách tới Tết. `days_from_tet` = feature mạnh #2 |
| L4 | **Break cấu trúc 2019** = sụp khối lượng, nền doanh thu 2019–2022 thấp hẳn 2013–2018 (A Tầng 1.1 + 2.1; Phase 1–2) | Feature **`is_post_2019`** + **`trend_index`**; và **bỏ model tuyến tính, chuyển sang cây** (B mục 2, 3) | 1 hệ số trend tuyến tính không khớp nổi 2 pha trái chiều ⇒ B3 linear bias +29–39%, ra cả doanh thu âm ⇒ model cây học phi tuyến quanh mốc 2019 |
| L5 | **Mùa vụ theo tháng ổn định** (đỉnh T4–6, đáy T11–12); quý trùng lặp tháng | `month`/`month_sin`/`month_cos`; **loại `quarter`** (corr 0.97 với month, importance ~0) (B mục 0.1, 3.2) | Mùa vụ tháng lặp lại được ⇒ mã hoá cyclical; quý dư thừa ⇒ chia model theo quý còn *tệ hơn* |
| L6 | **Nguyên nhân gốc khách rời NẰM NGOÀI data giao dịch** (đã loại giá/mix/promo/kênh/vùng) (A Tầng 2.5; Phase 2) | Chấp nhận **không có feature ngoại sinh**; nêu thẳng **rủi ro sốc cấu trúc** (B rủi ro 3) | Không có biến giải thích "vì sao 2019" ⇒ không model được cú sốc tương tự ⇒ trung thực: mọi model chịu chung nếu 2023–24 lặp lại sốc |
| L7 | **KHÔNG giảm giá/tăng promo** — vấn đề là khối lượng, không phải giá (A Tầng 4; Phase 4) | Forecast giả định **chính sách giá/promo không đổi**; nêu rõ nếu công ty đổi promo sau báo cáo thì forecast lệch (B rủi ro 2; A Hạn chế #8) | Prescriptive A và Forecast B nhất quán 1 thế giới quan: nền cầu do khách, không do đòn bẩy giá |

---

## Diễn giải mạch nhân quả (kể liền, không rời rạc)

**Điểm xoay số 1 — vì sao Phần B *không giống* một bài forecast e-commerce thông thường (L1).** Bài toán cho dữ liệu khách hàng đầy đủ, phản xạ tự nhiên là đắp feature hành vi: CLV, số khách active lăn theo tháng, tần suất mua lại. Phần A **chặn đứng** hướng đó bằng một con số: đường cohort retention gần như phẳng tuyệt đối ~3–6% từ tháng 1 tới tháng 12 sau khi mua (độ lệch chuẩn 0,4 điểm %), trong khi khách thật luôn có decay-curve dốc xuống. Hai phép đo độc lập (Phase 3 theo `signup_date`, Phase 5 theo tháng đơn đầu) khác mẫu số nhưng **cùng kết luận**: hành vi quay lại là ngẫu nhiên, không có tín hiệu. Hệ quả cứng cho B: mọi feature "khách cũ quay lại" bị loại **trước khi build**, Phase 6 chỉ giữ 17 feature thuần lịch. Đây là link đắt giá nhất — nó biến một bài "panel hành vi" thành một bài "chuỗi thời gian thuần mùa vụ".

**Điểm xoay số 2 — chốt đúng target trước khi tốn công (L2).** Phase 5 đối chứng: cột đề bài trùng khít tổng hợp gross từ `sales.csv` (kể cả đơn huỷ), MAPE 0.000%; phương án net (loại huỷ) lệch 13,9% — đúng bằng gap gross/net 13,37% mà Phần A đã đo độc lập ở Tầng 1.3. Nếu bỏ qua bước này, cả Phần B có nguy cơ tối ưu nhầm net revenue rồi thua mốc oan. Chốt gross demand + train Revenue/COGS độc lập là quyết định phòng ngừa, không phải kỹ thuật hoa mỹ.

**Điểm xoay số 3 — phát hiện mô tả của A trở thành feature định lượng của B (L3, L4, L5).** Ba pattern lịch sử A đo được không nằm im trong báo cáo mà **hoá thành cột dữ liệu**: Tết-không-cố-định ⇒ `days_from_tet` (feature mạnh #2, SHAP dương); break-2019 ⇒ `is_post_2019` + `trend_index` (feature mạnh #1, nhưng SHAP **âm** — đúng chiều "càng gần đây nền càng thấp" mà A phát hiện); mùa vụ-tháng-ổn định ⇒ mã hoá cyclical `month_sin/cos`, đồng thời loại `quarter` vì A cho thấy quý chỉ là bản thô của tháng. Chính break-2019 cũng là lý do B **bỏ linear chọn cây**: một đường thẳng đơn hệ số không thể vừa dốc lên 2013–2018 vừa đi ngang 2019–2022, nên B3 linear ngoại suy lệch +29–39% và cho 4 ngày doanh thu âm — bằng chứng số cho việc chuyển hướng.

**Điểm xoay số 4 — giới hạn của A trở thành sự trung thực của B (L6, L7).** A tuyên bố thẳng: đã loại giá/mix/promo/kênh/vùng nhưng *vì sao* khách rời 2019 nằm ngoài data giao dịch. B không giả vờ vá lỗ hổng đó bằng feature ngoại sinh bịa ra — thay vào đó ghi nhận **rủi ro 3**: nếu 2023–24 có sốc cấu trúc kiểu 2019, mọi model đều chịu chung (fold `rolling_2` xác nhận: mọi model kể cả B1 đều tệ hẳn). Và vì Prescriptive A khuyến nghị **không giảm giá/tăng promo**, forecast B nhất quán giả định chính sách giá không đổi — nếu công ty đổi promo sau khi đọc báo cáo, forecast sẽ lệch (nêu rõ ở cả A Hạn chế #8 lẫn B rủi ro 2).

---

## Vì sao link này đáng điểm (chốt)

Không có bước nào ở Phần B là "mặc định chọn model mạnh nhất". Feature (`days_from_tet`, `is_post_2019`, `trend_index`, cyclical month, loại `quarter`), target (gross demand), lẫn *class* model (cây thay vì tuyến tính) — **tất cả đều lần ngược được về một phát hiện định lượng cụ thể ở Phần A**. Kết quả cuối (Revenue WAPE 22,71% vượt mốc 25,18%; COGS 19,79% vượt 23,09%) là sản phẩm của chuỗi quyết định có căn cứ này, không phải may mắn tinh chỉnh tham số.
