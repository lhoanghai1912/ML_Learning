# Phần C — Phân khúc khách hàng

_Phần của [`EDA_FINDINGS.md`](./EDA_FINDINGS.md) — tóm tắt + dashboard đọc ở đó, đây là bản phân tích chi tiết đầy đủ của riêng phần này._


### Tỷ trọng doanh thu theo nhóm tuổi
**1. Hiện trạng — ổn định đến mức gần như là hằng số**
| Nhóm tuổi | 2013 | 2022 | Biên độ 10 năm | Dao động max−min |
|---|---|---|---|---|
| 25‑34 | 29.58% | 30.12% | 29.37 – 30.12 | **0.74 điểm %** |
| 35‑44 | 26.33% | 26.42% | 25.96 – 26.46 | **0.50 điểm %** |
| 45‑54 | 19.39% | 19.10% | 18.90 – 19.61 | 0.71 điểm % |
| 18‑24 | 13.34% | 13.50% | 13.34 – 14.13 | 0.79 điểm % |
| 55+ | 11.35% | 10.86% | 10.86 – 11.45 | 0.59 điểm % |

Không nhóm nào dịch chuyển quá **0.8 điểm %** trong cả thập kỷ, kể cả xuyên qua cú sụp 2019.

**2. Nguyên nhân / ý nghĩa**
Cơ cấu tuổi bất động khi doanh thu giảm một nửa có nghĩa: **mọi nhóm tuổi mất doanh thu theo cùng một tỷ lệ**. Kiểm chứng bằng giá trị tuyệt đối (2016 → 2022): 25‑34: 0.619 → 0.352 tỷ (−43%); 35‑44: 0.553 → 0.309 (−44%); 45‑54: 0.413 → 0.223 (−46%); 18‑24: 0.283 → 0.158 (−44%); 55+: 0.237 → 0.127 (−46%). **Chênh lệch giữa nhóm giảm nhiều nhất và ít nhất chỉ 3 điểm %.**

**3. Mối liên hệ**
Đây là **lát cắt thứ ba** (sau vùng và kênh) cho cùng kết quả "giảm đều tuyệt đối". Ba lát cắt độc lập về bản chất — địa lý, kênh, nhân khẩu — cùng loại trừ giả thuyết cục bộ. Kết hợp với ô ASP‑Volume, bức tranh nhân quả đã khép: **cú sốc tác động lên số lượng khách và tần suất mua, đồng đều trên mọi phân khúc**.

**4. Hệ quả kéo theo**
- **`age_group` vô dụng để giải thích biến động doanh thu** — không mang thông tin phân biệt theo thời gian.
- Nhưng vẫn hữu ích cho **phân bổ ngân sách tĩnh**: 25‑34 và 35‑44 cộng lại chiếm **56.5%** doanh thu ổn định qua mọi năm.

**5. Dự đoán**
Cơ cấu 2023–2024 gần như chắc chắn giữ nguyên (25‑34 ~30%, 35‑44 ~26%). Đây là dự đoán độ tin cậy rất cao nhưng giá trị quyết định thấp.

**6. Giới hạn**
`age_group` là trường tĩnh trong `customers.csv` — **không có ngày sinh**, nên khách không "già đi" qua 10 năm dữ liệu. Điều này tự nó đã đảm bảo cơ cấu ổn định; do đó **không thể** dùng chart này để kết luận về hành vi theo vòng đời khách hàng.

### AOV theo nhóm tuổi
**1. Hiện trạng — đồng đều gần như tuyệt đối**
| Nhóm | 18‑24 | 25‑34 | 35‑44 | 45‑54 | 55+ |
|---|---|---|---|---|---|
| AOV (nghìn VND) | 25.42 | 25.56 | 25.50 | **25.59** | 25.42 |
| Số đơn | 84,591 | 181,311 | 161,865 | 118,026 | 69,101 |
| Số khách | 17,039 | 36,342 | 31,920 | 23,172 | 13,457 |

Chênh lệch cao nhất–thấp nhất: **0.17 nghìn VND = 0.68%**.

**2. Nguyên nhân / diễn giải**
Khác biệt 0.68% trên mẫu 69K–181K đơn mỗi nhóm là **không có ý nghĩa thực tiễn**, dù có thể "có ý nghĩa thống kê" do mẫu quá lớn. Đây là ví dụ tốt cho nguyên tắc: *statistical significance ≠ practical significance*.

Kết luận: **giá trị đơn hàng độc lập với tuổi**. Sự khác biệt giữa các nhóm nằm hoàn toàn ở **số lượng khách** (25‑34 có 36,342 khách vs 55+ có 13,457 khách, gấp 2.7 lần) chứ không ở **hành vi chi tiêu mỗi lần mua**.

**3. Mối liên hệ**
Kết hợp với ô trước (cơ cấu tuổi bất động): doanh thu theo tuổi = **số khách × AOV chung**. Vì AOV giống nhau và cơ cấu số khách không đổi, tỷ trọng doanh thu theo tuổi tất yếu phải bất động — **hai chart này thực chất nói cùng một điều**, chart này giải thích *cơ chế* của chart trước.

**4. Hệ quả kéo theo**
- **Không có cơ sở** cho chiến lược định giá phân biệt theo tuổi hoặc "nhắm nhóm tuổi giá trị cao".
- Nếu muốn tăng doanh thu qua kênh nhân khẩu học, đòn bẩy duy nhất là **số lượng khách**, không phải giá trị mỗi khách.

**5. Dự đoán**
AOV theo tuổi sẽ tiếp tục hội tụ quanh 25.4–25.6 nghìn VND. Bất kỳ chênh lệch nào vượt ~1% trong dữ liệu tương lai sẽ là tín hiệu bất thường đáng điều tra.

**6. Giới hạn**
Cùng vấn đề nhóm khóa như ô AOV promo: `groupby(["order_id","age_group"])` — vì mỗi đơn thuộc đúng 1 khách nên ở đây **không** xảy ra tách đôi đơn, chỉ tiêu này đáng tin hơn. Tuy nhiên nó vẫn là AOV **gộp toàn kỳ**, chưa tách theo năm.

### RFM Segmentation (9 nhóm)
**1. Hiện trạng — phân bổ giá trị cực kỳ lệch**
| Segment | Số khách | % khách | Monetary (tỷ) | % giá trị | Recency TB (ngày) | Freq TB | Giá trị/khách |
|---|---|---|---|---|---|---|---|
| **Champions** | 22,575 | 25.6% | **8.950** | **62.9%** | 274 | 15.88 | **396.4k** |
| Loyal Customers | 16,974 | 19.3% | 2.884 | 20.3% | 787 | 7.02 | 169.9k |
| At Risk | 7,989 | 9.1% | 0.646 | 4.5% | **2,010** | 3.90 | 80.9k |
| Can't Lose Them | 2,251 | 2.6% | 0.492 | 3.5% | 1,783 | 8.61 | **218.6k** |
| **Lost** | **21,682** | **24.6%** | 0.459 | **3.2%** | **2,563** | 1.26 | **21.2k** |
| Hibernating | 3,327 | 3.8% | 0.270 | 1.9% | 2,399 | 1.60 | 81.0k |
| Promising | 5,375 | 6.1% | 0.205 | 1.4% | 1,105 | 1.48 | 38.2k |
| New Customers | 4,865 | 5.5% | 0.203 | 1.4% | 359 | 1.51 | 41.8k |
| Need Attention | 3,085 | 3.5% | 0.125 | 0.9% | 689 | 3.65 | 40.5k |

Tổng **88,123 khách / 14.234 tỷ VND** (Monetary = `payments.payment_value`, đơn không hủy).

**2. Phân tích cấu trúc**
- **Champions vs Lost gần bằng nhau về SỐ LƯỢNG** (22,575 vs 21,682 — chênh 4%) nhưng chênh **19.5 lần** về giá trị (62.9% vs 3.2%) và **18.7 lần** giá trị/khách (396.4k vs 21.2k). Gần **1/4 tệp khách hàng đã mất gần hết giá trị thương mại**.
- Champions + Loyal = 44.9% khách nhưng nắm **83.1%** giá trị → tuân theo phân bố Pareto rõ rệt (thậm chí gắt hơn quy tắc 80/20).
- Phân bố `frequency` toàn tệp: trung vị **4 đơn**, trung bình 6.67, tối đa 100; **25.72% khách chỉ mua đúng 1 lần**.
- Phân bố `recency`: trung vị **1,018 ngày (~2.8 năm)**, tối đa 3,832 ngày. Với `SNAPSHOT_DATE = 2022‑12‑31`, **hơn nửa tệp khách đã không mua gì trong gần 3 năm**.

**3. Mối liên hệ**
- Recency trung vị ~2.8 năm là hệ quả trực tiếp của cú sụp 2019 và việc mất nguồn khách mới (ô khách mới/khách cũ): tệp khách bị "đóng băng" ở quá khứ.
- Nhóm "New Customers" chỉ 4,865 khách (5.5%) — quá nhỏ so với "Lost" 21,682 → **tốc độ nạp mới thua xa tốc độ rơi rụng**, khớp với số khách mua lần đầu chỉ còn 1,322 vào 2022.

**4. Hệ quả kéo theo**
- Nhóm mục tiêu win‑back ở Phần 4 (At Risk + Can't Lose Them = 10,240 khách, 11.6%) có recency **1,783–2,010 ngày (~5 năm)**. Ở khoảng cách này, thuật ngữ "At Risk" (sắp rời bỏ) là **sai lệch** — họ đã rời bỏ từ lâu. Xác suất win‑back thực tế nên được giả định **thấp hơn nhiều** so với nhóm vừa rời 3–6 tháng.
- Rủi ro tập trung: 62.9% giá trị nằm ở Champions với recency TB 274 ngày (~9 tháng) — nhóm này cũng đang trượt dần khỏi trạng thái "gần đây".

**5. Dự đoán**
Nếu không có acquisition mới và tần suất mua giữ nguyên, dòng chảy tự nhiên là Champions → Loyal → At Risk → Lost. Với recency TB Champions đã 274 ngày, một phần nhóm này sẽ **rơi khỏi Champions trong 1–2 năm tới**, kéo tỷ trọng "Lost" vượt 30%.

**6. Giới hạn**
- Chấm điểm R/F/M dùng `qcut` trên **rank**, tức luôn chia tệp thành 5 phần bằng nhau → **các segment là tương đối, không tuyệt đối**. Nếu toàn bộ tệp cùng xấu đi, vẫn luôn có 20% được gán điểm 5. Không thể so sánh phân khúc này giữa 2 kỳ khác nhau.
- Monetary lấy từ `payment_value` (đã trừ chiết khấu), **khác** với `line_revenue` (gross) dùng ở các chart khác — nên tổng 14.234 tỷ ở đây không so trực tiếp được với 15.689 tỷ gross ở waterfall.

### ️ Phân tích chi tiết — Cohort Retention: PHÁT HIỆN LỖI DỮ LIỆU NGHIÊM TRỌNG
**1. Hiện trạng**
Đường retention **phẳng gần như tuyệt đối**: M0 3.03%, M1 3.01%, M3 2.94%, M6 3.00%, M9 3.02%, M12 2.92%. Biên độ dao động cả 12 tháng chỉ **0.14 điểm %**.

Đây là bất thường: mọi đường cong retention thực tế đều **giảm mạnh ở M1–M3 rồi phẳng dần**. Một đường phẳng ngay từ M0 là dấu hiệu chỉ tiêu **không đo đúng thứ nó tưởng đang đo**.

**2. Nguyên nhân — truy ra bằng dữ liệu, không suy đoán**

**Bằng chứng 1 — retention quan sát ≈ tỷ lệ nền ngẫu nhiên:**
Số khách khác nhau phát sinh đơn mỗi tháng trung bình **4,265**, trên tổng **121,930** khách trong `customers.csv` → tỷ lệ nền = **3.50%**. Giá trị "retention" quan sát được là **2.89–3.03%**. Hai con số gần như trùng nhau → **đường cong này chỉ đang đo xác suất một khách bất kỳ mua hàng trong một tháng bất kỳ**, hoàn toàn không phụ thuộc vào việc khách đó thuộc cohort nào.

**Bằng chứng 2 — `signup_date` không liên quan tới hành vi mua:**
- **80,623 / 90,246 khách (89.3%)** có đơn hàng **TRƯỚC** ngày đăng ký của chính mình.
- Độ trễ trung vị từ signup tới đơn đầu tiên: **−1,839 ngày** (mua trước khi đăng ký ~5 năm).

**Bằng chứng 3 — hai chuỗi đi ngược chiều nhau:**
| Năm | 2012 | 2014 | 2016 | 2018 | 2020 | 2022 |
|---|---|---|---|---|---|---|
| Số khách **signup** | 957 | 5,034 | 9,202 | 13,011 | 17,211 | **21,103** ⬆️ |
| Số khách **mua lần đầu** | 22,068 | 13,293 | 6,392 | 3,717 | 1,500 | **1,322** ⬇️ |

Signup tăng đều 22 lần trong khi khách mua lần đầu giảm 17 lần. Nếu `signup_date` phản ánh việc bắt đầu quan hệ khách hàng, hai chuỗi này không thể ngược chiều.

**Kết luận: `signup_date` là trường được gán gần như độc lập với hành vi mua** (rất có thể là ngày tạo bản ghi trong bộ sinh dữ liệu). Do đó **toàn bộ phân tích cohort dựa trên nó là vô nghĩa** — cohort không phải là "nhóm khách bắt đầu cùng thời điểm".

**3. Mối liên hệ**
- Kích thước cohort tăng đều 83 (2012‑07) → **1,883 (2022‑12)** phản ánh đúng chuỗi signup, tức mẫu số phình to trong khi tử số (khách thực mua) không tăng → ép tỷ lệ về mức nền.
- **31,684 khách (26.0%)** trong `customers.csv` chưa từng có bất kỳ đơn hàng nào — bằng chứng thêm rằng danh sách khách và danh sách người mua là hai tập khác nhau đáng kể.

**4. Hệ quả kéo theo**
-  **Không được** dùng con số "retention ~3%" để đánh giá sức khỏe khách hàng hay so sánh với benchmark ngành. Nó không phải retention.
-  Chỉ tiêu thay thế đáng tin: **tỷ lệ doanh thu từ khách cũ** (66.1% → 96.4%) và **số đơn/khách/năm** (2.03 → 1.46) — cả hai đều tính từ `order_date`, không dùng `signup_date`.
- Có một tín hiệu vẫn còn giá trị: retention M1 tính theo năm cohort giảm rõ rệt — 2016: **4.74%** → 2019: 2.45% → 2022: **2.11%**. Vì cùng dùng một chỉ tiêu bị lỗi, so sánh **tương đối giữa các năm** vẫn phản ánh việc tần suất mua giảm ~55%.

**5. Dự đoán**
Nếu bổ sung được trường thời điểm bắt đầu đáng tin (hoặc định nghĩa cohort theo **tháng có đơn đầu tiên** thay vì signup), đường cong sẽ có hình decay thật và mức M1 kỳ vọng **cao hơn 3%** đáng kể.

**6.  ĐÃ XỬ LÝ Ở TẦNG dbt (2026-08-10) — xem chart + phân tích ngay bên dưới**

Notebook này **giữ nguyên** cách tính gốc ở trên để đối chiếu số với báo cáo phase cũ (không tự sửa). Lỗi đã được xử lý ở tầng lakehouse bằng cách **thêm model song song**, không sửa đè:

| Model dbt | Định nghĩa cohort | Dùng khi nào |
|---|---|---|
| `iceberg.staging.int_cohort` | tháng `signup_date` | ️ CHỈ đối chiếu lịch sử / regression phase cũ |
| **`iceberg.staging.int_cohort_first_order`** | tháng **đơn hàng đầu tiên** (non-cancelled) |  Phân tích / BI / ra quyết định |

Chart + phân tích chi tiết đường cong retention THẬT (query trực tiếp qua Trino, không hardcode số) → xem cell ngay dưới đây.

### Retention THẬT (đơn đầu tiên) vs retention lỗi (signup_date), query trực tiếp qua Trino
**1. Hiện trạng — hai đường cong lệch hẳn nhau, không chỉ lệch mức mà lệch cả hình dạng**
Đường `int_cohort_first_order` (tím, đậm): **M0 = 100%** → M1 **6.10%** → giảm dần M2 5.60% → M3 5.50% → M4 5.50% → M5 5.40% → chạm đáy **M6 = 5.30%** → hồi M7 5.50% → M8 6.00% → M9 6.20% → M10 6.20% → M11 6.40% → **M12 = 6.40%**. Hình dạng đúng chữ **"nụ cười"**: giảm đơn điệu 6 tháng đầu rồi đảo chiều hồi phục đối xứng gần bằng đỉnh cũ.
Đường `int_cohort` (xám, nét đứt — model cũ dùng `signup_date`) gần như **một đường thẳng nằm ngang quanh 2.9–3.0%** suốt 12 tháng, không có bất kỳ điểm uốn nào. Khoảng cách giữa hai đường: **M1 gấp 2.03 lần, M6 gấp 1.77 lần, M12 gấp 2.21 lần** — chênh lệch không cố định mà co giãn theo đúng hình "nụ cười" của đường thật.

**2. Nguyên nhân**
Hai model dùng cùng công thức tổng hợp (`SUM(n_active)*100.0/SUM(cohort_size)`) và cùng bảng nguồn `stg_orders` cho phần tử số — khác nhau duy nhất ở **định nghĩa `cohort_month`**. `int_cohort_first_order` neo cohort vào chính hành vi mua (tháng đơn đầu tiên) nên tại M0 tử số = mẫu số tuyệt đối → 100% là hệ quả toán học của định nghĩa, không phải phát hiện nghiệp vụ. `int_cohort` neo vào `signup_date` — một trường đã chứng minh (mục 2 ở phân tích phía trên) không liên quan hành vi mua (89.3% khách mua trước khi "đăng ký") — nên tại M0 xác suất một khách bất kỳ phát sinh đơn đúng tháng signup của họ chỉ là xác suất nền ngẫu nhiên (~3%), không hội tụ về 100%.
Hình "nụ cười" của đường thật nhiều khả năng phản ánh **chu kỳ mua lặp lại theo mùa của hàng thời trang** — khớp hướng với biên độ mùa vụ **2.75 lần** giữa tháng cao/thấp điểm đã đo ở Phần 1 (cell "Hình dạng mùa vụ 10 năm chồng nhau"). Khách mua lần đầu ở một mùa cụ thể có xu hướng quay lại đúng dịp tương ứng của năm sau (M12) hơn là giữa chừng (M4–M6) — tương tự việc mua sắm thời trang theo mùa/dịp thay vì đều đặn hàng tháng.

**3. Mối liên hệ**
- Nối với phát hiện `% doanh thu khách cũ` tăng từ 66.1% → 96.4% qua các năm (mục 4 ở phân tích phía trên, dùng `order_date` — không lỗi): dòng doanh thu ngày càng phụ thuộc khách cũ **dù tần suất quay lại theo cohort chỉ 5.3–6.4%** — nghĩa là tổng doanh thu khách cũ lớn chủ yếu do **tích lũy nhiều cohort qua 10 năm** cộng dồn, không phải từng cohort riêng lẻ retention cao.
- Nối với Phần 1 (mùa vụ 2.75 lần) và Phần 2 (Q1 — ASP vs Volume): cả ba cùng chỉ về đặc tính ngành thời trang mua theo mùa/dịp, không phải mua định kỳ đều đặn kiểu FMCG.
- Nối với RFM (Phần 3, cell trước cell này): nhóm `Can't Lose Them`/`At Risk` — nếu đúng giả thuyết "mua theo mùa/năm", thời điểm win-back hiệu quả nhất nên rơi vào **trước mốc 1 năm kể từ đơn đầu (quanh M9–M11)**, không phải ngay sau M1.

**4. Hệ quả kéo theo**
- Kết luận cũ "retention chỉ ~3%, phẳng tuyệt đối" (dựa trên `int_cohort`) là **đánh giá thấp** thực trạng ở mọi mốc — số thật cao gấp 1.77–2.21 lần. Nếu từng dùng con số cũ để quyết định ngân sách CRM/win-back, ngân sách đó bị định giá dựa trên tín hiệu sai.
- Retention thật (5.3–6.4%) vẫn **thấp so với benchmark ngành thời trang online phổ biến (thường 20–40% ở M1)** — đây là vấn đề kinh doanh thật, không phải lỗi đo lường. Không nên diễn giải "đã tìm ra số đúng, mọi thứ ổn" — số đúng vẫn xấu, chỉ là xấu theo cách khác con số cũ.
- ️ **Cập nhật (xem cell kiểm định ngay sau đây)**: khuyến nghị ban đầu "win-back nhắm giai đoạn M4–M5" dựa trên offset trung bình đã được kiểm định lại và **KHÔNG đúng chỗ nhắm** — đáy là hiệu ứng mùa vụ theo THÁNG LỊCH (khoảng Tháng 11–Tháng 1), không phải theo offset kể từ lần mua đầu. Xem kết luận đầy đủ + bằng chứng ở cell/markdown ngay sau.

**5. Dự đoán**
- Nếu hình "nụ cười" thật sự là hiệu ứng chu kỳ mùa/năm (không phải trùng hợp), mở rộng trục sang M13–M24 (cần dbt bỏ giới hạn `month_offset <= 12` hiện tại) sẽ thấy **đáy thứ hai quanh M18** rồi hồi lại quanh **M24** — lặp lại đúng biên độ M6/M12 hiện tại. Đây là dự đoán **kiểm chứng được**: chỉ cần sửa 1 dòng filter trong `int_cohort_first_order`/query notebook, không cần model mới.
- Cách kiểm định chặt hơn giả thuyết "mùa vụ" thay vì "thuần túy vòng đời khách hàng": tách `cohort_month` theo tháng bắt đầu (ví dụ cohort bắt đầu tháng 3 vs tháng 9) rồi so đáy/đỉnh của từng nhóm — nếu đáy luôn rơi đúng offset +6 bất kể tháng bắt đầu (hiệu ứng vòng đời/tenure) thay vì rơi đúng một **tháng lịch cụ thể** bất kể cohort (hiệu ứng mùa lịch thuần túy), sẽ phân biệt được hai giả thuyết. Chưa làm ở đây.

**6. Giới hạn**
- **Right-censoring nhẹ nhưng có thật**: mẫu số (`cohort_size` cộng dồn) giảm dần theo offset — M0 = 88,123 khách nhưng M12 chỉ còn 86,795 khách "đủ điều kiện" (cohort đủ già để quan sát tới M12), tức **1,328 khách (1.5%) bị loại khỏi điểm M12** vì cohort của họ còn quá trẻ. Ảnh hưởng nhỏ (1.5%) nhưng có nghĩa là điểm M12 hơi thiên về các cohort **cũ hơn** (2012–2021) so với điểm M1 (gồm cả cohort 2022).
- **`month_offset` trộn lẫn "tenure" (số tháng kể từ lần mua đầu) với "tháng lịch"** — vì mỗi cohort bắt đầu ở một tháng lịch khác nhau, đường trung bình cộng dồn ở mục 5 chưa tách được hiệu ứng mùa lịch thuần túy khỏi hiệu ứng vòng đời khách hàng. Diễn giải "nụ cười = mùa vụ" ở mục 2 là **giả thuyết có cơ sở gián tiếp** (khớp hướng với biên độ mùa vụ Phần 1), **chưa phải bằng chứng nhân quả trực tiếp** — cần phép tách ở mục 5 mới kết luận chắc.
- Cả hai đường đều là **trung bình weighted toàn kỳ 2012–2022** — có thể che khuất khác biệt theo năm (đã ghi nhận ở mục 4 phân tích phía trên: retention M1 theo năm cohort giảm từ 4.74% (2016) xuống 2.11% (2022) khi tính trên model cũ; chưa recompute xu hướng theo năm cho model `int_cohort_first_order` ở đây).

### Kiểm định giả thuyết "nụ cười = mùa vụ" (nợ để lại ở mục 5/6 phía trên) — KẾT LUẬN: MÙA VỤ, không phải vòng đời
**1. Hiện trạng — 2 phép đo cho 2 câu trả lời trái ngược nhau**
Tách 126 cohort thành 12 nhóm theo **tháng bắt đầu** (10–11 cohort/nhóm, đủ mẫu), tính đường cong retention riêng từng nhóm, tìm điểm đáy (M1–M12) của mỗi nhóm:
- **`trough_offset`** (đáy rơi vào offset thứ mấy): trải từ **1 đến 10**, độ lệch chuẩn **3,06 tháng** — hoàn toàn KHÔNG hội tụ về một con số cố định (bác bỏ "đáy luôn ở tenure +6").
- **`trough_calendar_month`** (đáy rơi vào tháng dương lịch nào, quy đổi từ offset): **10/12 nhóm (83%) đáy đúng THÁNG 1**, độ lệch tròn (circular std) chỉ ~28° (**dưới 1 tháng**) — hội tụ rất chặt.

**2. Nguyên nhân**
Khi cohort bắt đầu Tháng 12 → chỉ cần offset 1 là chạm Tháng 1; cohort bắt đầu Tháng 3 → phải đi offset 10 mới chạm Tháng 1 năm sau. Offset khác nhau hoàn toàn nhưng đều **hội tụ về đúng 1 tháng dương lịch** — đây chính xác là chữ ký của hiệu ứng **MÙA VỤ (calendar)**, không phải hiệu ứng **VÒNG ĐỜI (tenure)**. Nếu là vòng đời thật, offset đáy phải giống nhau bất kể tháng bắt đầu — dữ liệu cho kết quả ngược lại.

Khớp trực tiếp với "Hình dạng mùa vụ 10 năm chồng nhau" đã đo ở Phần 1: **Tháng 11 (4,83%)/Tháng 12 (4,71%)/Tháng 1 (5,11%)** là 3 tháng thấp điểm nhất năm. Khách hàng đơn giản là **không quay lại mua trong giai đoạn thấp điểm cuối năm–đầu năm sau**, bất kể họ mới mua lần đầu được bao lâu.

**3. Mối liên hệ — giải thích luôn vì sao đường cong TRUNG BÌNH TOÀN KỲ (mục 1 phía trên) lại có hình "nụ cười" nông ở M6 thay vì đáy sắc nhọn**
Đường trung bình weighted mọi cohort (không tách tháng bắt đầu) **gộp 12 đáy sắc nhọn nằm ở 12 offset khác nhau** (1 đến 10) lại với nhau. Phép cộng dồn này "trải mỏng" (smear) các đáy riêng lẻ ra thành 1 vùng trũng nông ở khoảng giữa (quanh M5–M6) — đây là **ảo ảnh gộp (pooling artifact) của phép trung bình**, KHÔNG phải bằng chứng cho 1 hiệu ứng vòng đời thật ở tháng thứ 6. Đường "nụ cười" ở mục 1 vẫn đúng về mặt SỐ LIỆU, chỉ SAI về mặt DIỄN GIẢI nguyên nhân — đã sửa ở đây.

**4. Hệ quả kéo theo — SỬA khuyến nghị hành động đã ghi trước đó**
Ở mục 4 phía trên (phân tích đường cong trung bình) có ghi: *"Đáy M6 gợi ý cửa sổ can thiệp: win-back nhắm đúng giai đoạn M4–M5"* — khuyến nghị này **dựa trên offset trung bình, giờ xác nhận là sai chỗ nhắm**. Khuyến nghị đúng: win-back/CRM nên nhắm theo **THÁNG LỊCH** (chủ động outreach khoảng Tháng 10–11, TRƯỚC khi bước vào vùng thấp điểm Tháng 11–Tháng 1), áp dụng đồng loạt cho MỌI khách bất kể họ thuộc offset/cohort nào — không phải chờ đúng "tháng thứ 4–5 kể từ lần mua đầu" của riêng từng khách.

**5. Dự đoán**
Nếu giả thuyết mùa vụ đúng, năm sau (dữ liệu ngoài phạm vi 2012–2022) đáy retention theo tháng lịch vẫn sẽ rơi vào khoảng Tháng 11–Tháng 1 bất kể phân bố cohort mới ra sao — đây là dự đoán **kiểm chứng được** trực tiếp, khác hẳn dự đoán "đáy ở tenure M6" (đã bác bỏ).

**6. Giới hạn**
- 2 nhóm bắt đầu Tháng 1–2 KHÔNG rơi đúng Tháng 1 (đáy thật ở Tháng 10–11 của chính nhóm đó) — 10/12 không phải 12/12. Có thể do mẫu ít hơn (10 cohort thay vì 11) hoặc có 1 đáy phụ khác ngoài Tháng 1; **chưa điều tra thêm**, không đủ để bác bỏ kết luận chung (83% đồng thuận + circular std rất chặt là bằng chứng mạnh) nhưng cũng không nên coi là 100%.
- Mỗi nhóm tháng chỉ có 10–11 cohort — đủ để thấy pattern rõ nhưng KHÔNG đủ để ước lượng khoảng tin cậy chính thức (cần bootstrap nếu muốn con số p-value nghiêm ngặt hơn, chưa làm ở đây).
---

