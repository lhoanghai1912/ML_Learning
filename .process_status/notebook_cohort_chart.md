# Report — notebooks/02_eda.ipynb: thêm chart + phân tích retention thật (int_cohort_first_order)

Ngày: 2026-08-10. Nhánh: `chore/restructure-lakehouse`. Commit: `b365bed`. Scope: CHỈ `notebooks/02_eda.ipynb`.

## Bối cảnh

Log PROCESS.md 2026-08-10 ("Nợ signup_date ở tầng dbt — ĐÓNG") thêm model dbt
`int_cohort_first_order` (cohort theo tháng đơn hàng đầu tiên, không dùng
`signup_date`) verify retention thật: M0=100%, M1=6.10%, M6=5.30% (đáy),
M12=6.40% ("nụ cười"). Notebook mục 6 cohort đã được cập nhật **mô tả tĩnh**
(bảng số viết tay) nhưng chưa có code cell thật query + vẽ chart. Việc này bổ
sung phần còn thiếu đó.

## Cell nào thêm (số thứ tự sau khi chạy xong, 0-indexed)

Notebook trước: 62 cell. Sau: 64 cell (thêm đúng 2, không xoá cell nào).

- **Cell 50** (markdown, mục 6 cũ "✅ ĐÃ XỬ LÝ Ở TẦNG dbt") — **SỬA có chủ đích**
  (rút gọn): bỏ đoạn bảng số + "3 điểm rút ra" mô tả tĩnh (giờ dư thừa vì có
  chart thật ngay dưới), **giữ nguyên** bảng định nghĩa 2 model
  (`int_cohort` vs `int_cohort_first_order`) làm điểm neo. Mục 1–5 phía trên
  (hiện trạng/nguyên nhân/mối liên hệ/hệ quả/dự đoán của phát hiện lỗi
  `signup_date`) **không đụng**.
- **Cell 51 (CODE — MỚI)**: query Trino 2 model —
  `SELECT month_offset, SUM(n_active)*100.0/SUM(cohort_size) AS retention_pct
  FROM int_cohort_first_order|int_cohort WHERE month_offset BETWEEN 0 AND 12
  GROUP BY month_offset ORDER BY month_offset` (đúng công thức đã verify,
  đủ 13 điểm M0–M12, không hardcode). Dùng lại `_trino_conn` đã mở ở cell 3
  (đúng pattern kết nối notebook đang dùng — không tạo cách kết nối mới).
  Vẽ 2 đường chồng nhau: `int_cohort_first_order` (màu `C_ACCENT`, nét liền,
  đậm) vs `int_cohort` (màu `C_GRAY`, nét đứt) — đúng bảng màu/style đã set ở
  cell 1 đầu notebook (`C_REV/C_COGS/C_GRAY/C_ACCENT`, `plt.rcParams` chung).
  Có `assert` sanity (đủ 13 điểm, M0=100%).
- **Cell 52 (MARKDOWN — MỚI)**: phân tích 6 mục (Hiện trạng / Nguyên nhân /
  Mối liên hệ / Hệ quả kéo theo / Dự đoán / Giới hạn), viết theo đúng khuôn
  các cell "Phân tích chi tiết" khác trong notebook (đọc mẫu cell 37 "Q2:
  Tỷ lệ bán dưới giá vốn" và cell 50 cũ trước khi viết) — không viết hời hợt,
  có số liệu thật trích từ chính output cell 51 + liên hệ chéo Phần 1
  (mùa vụ 2.75 lần), Phần 3 (RFM/win-back), mục 4 phân tích cũ (% doanh thu
  khách cũ 66.1%→96.4%).

## Verify 0 lỗi

```
.venv/bin/python -m jupyter nbconvert --to notebook --execute --inplace notebooks/02_eda.ipynb
```
→ `Writing 1746398 bytes` — **0/26 code cell lỗi** (script quét toàn bộ
`output_type == "error"` qua nbformat, kết quả `errors=0` trên 26 code cell,
trước là 25, +1 cell mới).

Output thật của cell 51 (chạy qua Trino sống, không hardcode):
```
int_cohort_first_order — retention mốc: {'M0': 100.0, 'M1': 6.1, 'M3': 5.5, 'M6': 5.3, 'M9': 6.2, 'M12': 6.4}
int_cohort (signup, đối chiếu) — retention mốc: {'M0': 3.0, 'M1': 3.0, 'M3': 2.9, 'M6': 3.0, 'M9': 3.0, 'M12': 2.9}
Đáy 'nụ cười': M6 = 5.30%  |  hồi tới M12 = 6.40%
Tỷ lệ retention thật / retention lỗi: M1=2.03x, M6=1.77x, M12=2.21x
```
Khớp tuyệt đối số đã ghi trong PROCESS.md log 2026-08-10 (M1=6.10, M6=5.30 đáy,
M12=6.40; int_cohort M1=3.0/M3=2.9/M6=3.0/M12=2.9).

## Verify diff cell-by-cell (script nbformat, KHÔNG nhìn mắt)

Script: so `git show HEAD~1:notebooks/02_eda.ipynb` (bản trước khi sửa,
tương ứng `HEAD` tại thời điểm bắt đầu việc = commit `f2ac8b3`) với bản sau
khi execute. Map index: cell AFTER < 51 khớp trực tiếp BEFORE cùng index;
cell AFTER ≥ 53 khớp BEFORE index-2 (do chèn 2 cell ở vị trí 51–52); cell
AFTER 51,52 là cell mới, loại khỏi vòng so map 1-1.

Kết quả chạy thật:
```
before: 62 cells | after: 64 cells

Tong so cell source khac (ngoai 2 cell moi them): 1
Tong so cell code output-text khac: 1

--- Chi tiet ---
[UNEXPECTED!] cell BEFORE idx=15/AFTER idx=15: OUTPUT TEXT DOI
    before: [..., ('stream','stdout','Corr...\n'), ('stream','stdout','Top 5...\n')]
    after : [..., ('stream','stdout','Corr...\nTop 5...\n')]
[EXPECTED] cell BEFORE idx=50/AFTER idx=50 (markdown): source DA SUA CO CHU DICH (trim muc 6)

--- Cell moi ---
idx=51 type=code len_source=2340   n_outputs=2 n_errors=0
idx=52 type=markdown len_source=5612

--- Verify sau khi gop stream text (cell idx=15) ---
giong het sau khi gop: True
```

Diễn giải:
- **Đúng 1 cell source đổi ngoài 2 cell mới** = cell 50 markdown — **có chủ
  đích** (rút gọn mục 6 cũ), đúng phạm vi cho phép của yêu cầu.
  Mọi cell code khác (24/24 cell code cũ còn lại) **source giữ nguyên 100%**.
- **1 cell output khác cấu trúc** (idx 15, cell "Corr(Revenue,COGS)...") —
  nbconvert đôi lúc chia 1 lần `print` thành nhiều `stream` chunk khác nhau
  giữa 2 lần chạy (buffering không tất định, không liên quan gì tới thay
  đổi của tôi — cell 15 nằm ở Phần 1, cách xa cell cohort). Verify riêng:
  gộp toàn bộ text của các stream chunk theo đúng thứ tự → **giống hệt
  nhau tuyệt đối** (`giong het sau khi gop: True`). Đây là hiện tượng
  **đã từng gặp và ghi nhận benign** ở lần sửa notebook trước (PROCESS.md
  log 2026-08-10, commit `7318ab9`: "1 cell khác cấu trúc output do nbformat
  chia stream thành 3 chunk thay vì 2 — đã verify text gộp lại giống hệt").
  Không phải regression số liệu.
- **0 cell nào khác** (trong 22 code cell + 27 markdown cell còn lại, kể cả
  mọi cell downstream dùng `sales`/`li`/`orders`... ở Phần 2–4) đổi output
  hay source.

Kết luận verify: **PASS** theo đúng tiêu chí "mọi code cell KHÁC (không phải
cell mới thêm) giữ nguyên source, output/text không đổi" — 1 khác biệt output
duy nhất là chunk-boundary vô hại đã chứng minh bằng script, không phải số
liệu đổi.

## Mô tả chart bằng lời (không có ảnh thật đính kèm, mô tả đủ để hình dung)

Biểu đồ đường (line chart), trục X = "Tháng kể từ cohort (month offset)"
chạy 0→12, trục Y = "% cohort còn hoạt động". Hai đường:

- **Đường tím đậm, nét liền, có marker tròn** (`int_cohort_first_order` —
  retention thật): xuất phát đỉnh **100%** tại M0 (rơi thẳng đứng từ 100
  xuống ~6%, vì M0 là điểm neo định nghĩa), sau đó **giảm dần đều** qua
  M1(6.10%)→M2(5.60%)→M3(5.50%)→M4(5.50%)→M5(5.40%)→**chạm đáy M6(5.30%)**,
  rồi **đảo chiều đi lên** M7(5.50%)→M8(6.00%)→M9(6.20%)→M10(6.20%)→
  M11(6.40%)→M12(6.40%). Hình dạng đúng như tên gọi **"nụ cười"** (chữ U
  nông, gần đối xứng quanh đáy M6). Có 3 nhãn số chú thích trực tiếp trên
  đường tại M1/M6/M12.
- **Đường xám, nét đứt, marker tròn** (`int_cohort` — model cũ theo
  `signup_date`): gần như **thẳng băng ngang** quanh mức 2.9–3.0% suốt từ
  M0 đến M12, không có đáy/đỉnh nào đáng kể (dao động trong biên 0.1 điểm %).
- Vị trí tương đối: đường xám luôn nằm **thấp hơn hẳn** đường tím ở mọi
  điểm (khoảng cách 2.3–3.5 điểm %, tức đường tím cao gấp 1.77–2.21 lần),
  và khoảng cách giữa 2 đường **co giãn theo hình chữ U** của đường tím chứ
  không cố định — trực quan cho thấy 2 model không chỉ lệch mức mà lệch cả
  hình dạng/ý nghĩa. Có legend (góc trên phải, `frameon=False`) ghi rõ tên
  model + chú thích "retention THẬT" / "lỗi, chỉ để đối chiếu".

## Hạn chế / nợ còn lại (không chặn việc này)

- Chưa mở rộng trục sang M13–M24 để kiểm giả thuyết chu kỳ mùa/năm lặp lại
  (đề xuất kiểm chứng đã ghi trong mục "Dự đoán" của markdown cell 52,
  chưa làm).
- Chưa tách retention theo tháng bắt đầu cohort để phân biệt hiệu ứng
  "vòng đời khách" (tenure) khỏi "mùa lịch" (calendar-seasonal) — ghi rõ là
  giả thuyết chưa chứng minh nhân quả trong mục "Giới hạn" của cell 52.
- Notebook giờ phụ thuộc Trino sống ở cả cell 51 (thêm 1 điểm phụ thuộc
  docker nữa, ngoài cell 3 đã có từ M6a) — nhất quán với thực trạng đã ghi
  nhận từ M6a, không phải rủi ro mới.
- Quan sát ngoài phạm vi (KHÔNG đụng): 2 file untracked
  `.process_status/audit_temporal_consistency_2026-08-10.md` và
  `.process_status/mart_cohort_retention.md` đang tồn tại trên working tree
  (không phải do việc này tạo ra, không nằm trong PROCESS.md tại thời điểm
  đọc đầu phiên — có vẻ là sản phẩm của phiên/agent khác chạy song song,
  chưa commit). Không thêm vào staging, không sửa, đúng ràng buộc "CHỈ sửa
  notebooks/02_eda.ipynb".

## Không làm (đúng ràng buộc)

- Không sửa `PROCESS.md`.
- Không push (chỉ commit local `b365bed`, PO push sau khi gộp).
- Không đụng file nào khác ngoài `notebooks/02_eda.ipynb`.
