# Vin Datathon 2026

Dự án phân tích dữ liệu + dự báo cho cuộc thi Vin Datathon 2026. Bộ dữ liệu mô phỏng một sàn thương mại điện tử Việt Nam, trải dài 11 năm (04/07/2012 – 31/12/2022), gồm 15 bảng (đơn hàng, khách hàng, sản phẩm, thanh toán, khuyến mãi, tồn kho, traffic web...).

Team: Hải, Hoàng, Đăng.

## Đề bài

Xem chi tiết tại [`tài liệu/Đề bài1.docx`](tài liệu/Đề bài1.docx) và data dictionary tại [`tài liệu/data_dictionary.xlsx`](tài liệu/data_dictionary.xlsx). Tóm tắt:

- **Phần A — Dashboard & Analysis**: phân tích revenue/profit, RFM segmentation, cohort retention, marketing channels. Mỗi mảng đi đủ 4 tầng **Descriptive → Diagnostic → Predictive → Prescriptive**, chốt bằng đề xuất hành động định lượng.
- **Phần B — Forecast**: dự báo **Revenue** và **COGS** cho 548 ngày kế tiếp (01/01/2023 – 01/07/2024), nộp theo format `data/sample_submission.csv`.
- **Liên kết A→B**: insight từ Phần A (xu hướng doanh thu, mùa vụ, margin theo quý) được dùng làm giả định thiết kế model cho Phần B.

### Điểm dữ liệu cần lưu ý

- `sales.csv` chứa `Revenue`/`COGS` là số liệu **GROSS** — bao gồm cả đơn đã hủy, chưa trừ giảm giá. Đây là số phải dùng khi đối chiếu với target dự báo Phần B (đề bài dựa trên `sales.csv`).
- `net_revenue` (loại đơn hủy, trừ giảm giá) chỉ dùng cho phân tích góc nhìn kinh doanh ở Phần A — **không** dùng để đối chiếu forecast. Chênh lệch gross vs net ~13-24% tùy giai đoạn.
- `payments.payment_value` là giá trị tiền mặt thực nhận theo đơn (khớp 100%), dùng làm Monetary trong RFM.

## Cấu trúc thư mục

```
.
├── data/                       # Dữ liệu gốc — CHỈ ĐỌC, không sửa
├── tài liệu/                   # Đề bài + data dictionary
├── EDA_Insight/                # Toàn bộ phân tích, chia theo phase
│   ├── phase0_qc/              # QC schema & chất lượng dữ liệu
│   ├── phase1_descriptive/     # Trend, CAGR, mùa vụ, hiệu ứng Tết
│   ├── phase2_diagnostic/      # Vì sao revenue/margin biến động
│   ├── phase3_dashboard/       # RFM, cohort retention, demographics
│   ├── output/phaseN/          # Chart theo từng phase
│   └── DATA_LINEAGE.md         # Truy vết data thô → data trung gian qua từng phase
├── orchestrator_prompt.md      # Vai trò & quy trình điều phối agent con
├── PROGRESS.md                 # Trạng thái từng giai đoạn (nguồn sự thật duy nhất)
├── requirements.txt
└── .venv/                      # (không commit) môi trường Python local
```

Mỗi phase có `data/` riêng chứa CSV trung gian do phase đó tạo ra (VD: data đã làm sạch, đã tổng hợp) — không sửa trực tiếp lên `data/` gốc. Lineage đầy đủ (bảng nào từ bảng nào, transform gì) ghi ở [`EDA_Insight/DATA_LINEAGE.md`](EDA_Insight/DATA_LINEAGE.md).

## Quy trình làm việc (agent-driven)

Dự án dùng Claude Code với các "agent vai trò" (de/da/ds/ba/pm/tester) chạy từng phase theo bảng phụ thuộc trong [`orchestrator_prompt.md`](orchestrator_prompt.md). Trạng thái hiện tại của từng giai đoạn — done/pending, file output, phát hiện chính — luôn được cập nhật ở [`PROGRESS.md`](PROGRESS.md). Đọc file đó trước để biết dự án đang ở đâu.

## Cài đặt & chạy local

Yêu cầu: Python 3 (khuyến nghị dùng venv riêng).

```sh
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Thư viện hiện tại: `pandas`, `matplotlib`, `openpyxl`, `lunardate`. Notebook/script trong `EDA_Insight/phaseN_*/` chạy độc lập bằng `.venv/bin/python`, đọc dữ liệu trực tiếp từ `data/` (đường dẫn tương đối tới gốc dự án).

> Lưu ý: môi trường hiện chưa có `nbconvert`/`nbclient` (không chạy notebook qua Jupyter kernel thật được, phải verify bằng cách gộp code cell rồi `exec()`) và chưa có `sklearn`/`scipy`/`statsmodels` (cần bổ sung trước khi làm model ở Phần B).

## Đồng bộ nhiều máy

Repo đã cấu hình `.gitignore` bỏ qua `.venv/`, `.DS_Store`, cache Python và thư mục worktree của Claude Code. Khi clone máy mới: tạo lại venv theo hướng dẫn trên, `data/` đã có sẵn trong repo nên không cần tải riêng.
