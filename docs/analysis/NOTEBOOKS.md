# Notebooks — bản kèm chart INLINE cho từng script .py

Nhiệm vụ TOOLING (de): mỗi script phân tích `.py` có 1 notebook `.ipynb` tương ứng (cùng thư mục, cùng
basename), chạy ĐÚNG code gốc nhưng chart hiện INLINE ngay dưới cell. Đây là đóng gói lại phần đã có —
**KHÔNG phân tích mới, KHÔNG sửa logic/số liệu**. Cả 9 notebook đã chạy thật (`jupyter nbconvert --execute
--inplace`), output đã bake vào file, 0 cell lỗi.

## Cách chạy lại (nếu cần re-bake output)

```sh
.venv/bin/jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 <notebook.ipynb>
```

## Xử lý chung áp dụng cho cả 9 notebook

1. **Setup cell đầu tiên** (sau cell markdown tiêu đề): `%matplotlib inline` + `os.chdir(<gốc dự án
   tuyệt đối>)` + gán `__file__ = "<đường dẫn tuyệt đối tới chính file .py gốc>"`. Lý do cần `__file__`:
   hầu hết script dùng `Path(__file__).resolve().parent` để định vị thư mục — notebook không có biến
   `__file__` mặc định nên phải gán tay, nếu không mọi đường dẫn tương đối (đọc `data/`, ghi
   `output/phaseN/`) sẽ vỡ. Sau khi gán, code gốc chạy đúng y hệt như khi gọi `python script.py`.
2. **Backend `matplotlib.use("Agg")`**: các script gốc set cứng backend Agg (không hiển thị được). Trong
   bản notebook, dòng này bị bỏ qua (comment lại) để `%matplotlib inline` (đã set ở cell đầu) thắng — chỉ
   thay đổi trong **bản sao ở notebook**, KHÔNG đụng file `.py` gốc.
3. **Hiện chart inline**: mọi `plt.close(fig)`/`plt.close()` (dùng để dọn figure khi chạy script ngoài
   Jupyter, tránh rò bộ nhớ) được chèn thêm `plt.show()` ngay trước — figure hiện ra trong output cell rồi
   mới đóng. `plt.savefig(...)` giữ nguyên 100% nên file chart trong `output/phaseN/` không đổi nội dung
   (đã verify `git status` — không phát sinh diff nào ngoài 9 file `.ipynb` mới).
4. **Tách cell theo mốc logic**: dùng đúng các khối comment phân đoạn đã có sẵn trong code gốc (dạng
   `# ---...---` / `# ===...===` bọc quanh 1 dòng tiêu đề, VD `# 1. TOÀN CHUỖI...`) làm ranh giới —
   mỗi khối thành 1 cell markdown (tiêu đề) + 1-2 cell code. Với 2 script bọc logic trong `def main():`
   (`screen_features.py`, `build_baselines.py`), nội dung `main()` được "unwrap" thành nhiều cell tuần tự
   bằng `textwrap.dedent` (bỏ 1 cấp thụt lề) — thứ tự câu lệnh và toàn bộ logic bên trong giữ nguyên
   100%, chỉ khác chỗ code đó nằm ở cell nào. Với `build_features.py`, khối `if __name__ == "__main__":`
   cuối file cũng unwrap tương tự (ghi chú: Jupyter luôn có `__name__ == "__main__"` nên khối đó vốn tự
   chạy được kể cả khi giữ nguyên `if`, việc tách chỉ để hiện thành cell riêng cho dễ đọc).
5. **KHÔNG sửa nội dung tính toán nào** — mọi phép biến đổi dữ liệu, công thức, tham số giữ đúng 100% so
   với `.py` gốc.

## Bảng đối chiếu

| Script `.py` | Notebook | Có chart? (số ảnh) | Số cell (code) | Ghi chú xử lý |
|---|---|---|---|---|
| `phase1_descriptive/eda_training_charts.py` | `eda_training_charts.ipynb` | Có (6: `01`–`06`) | 18 (9 code) | Chuẩn — tách theo 6 mục `# N. TIÊU ĐỀ` có sẵn + mục "SỐ LIỆU KÈM PHÂN TÍCH". |
| `phase1_descriptive/tet_effect.py` | `tet_effect.ipynb` | Có (1: `tet_effect.png`) | 14 (7 code) | Chuẩn — tách theo 5 mục (bảng Tết, offset, thống kê, chart, định lượng theo năm). Ghi đè `tet_dates.csv`/`tet_yearly_stats.csv` với nội dung y hệt (đã verify không có diff). |
| `phase2_diagnostic/revenue_diagnostic.py` | `revenue_diagnostic.ipynb` | Có (15: `07`–`14`, `29`–`35`) | 38 (19 code) | Chuẩn — 15 khối `# N. TIÊU ĐỀ` tách thành 15 cặp markdown/code. |
| `phase3_dashboard/customer_demographics.py` | `customer_demographics.ipynb` | Có (14: `15`–`28`) | 30 (15 code) | Chuẩn — 7 khối `# N. TIÊU ĐỀ` (chart 15-21) + 6 khối lớn `# ===...===` (RFM, cohort, RFM×region, churn, logistic, export) — mỗi khối RFM/cohort/logistic có 2 chart cùng 1 cell (không có ranh giới comment riêng giữa 2 chart trong cùng khối ở bản gốc). |
| `phase4_prescriptive/prescriptive_analysis.py` | `prescriptive_analysis.ipynb` | Có (3: `36`–`38`) | 12 (6 code) | Script gốc không dùng comment `# ---` để phân đoạn — tách thủ công theo 3 khối `print("="*70)` (ĐỀ XUẤT 1/2/3) đã có sẵn trong code. |
| `phase5_model_assumptions/verify_target_and_cohort.py` | `verify_target_and_cohort.ipynb` | **Không** — chỉ in số liệu + xuất 2 CSV | 8 (4 code) | Không có `matplotlib`/`plt` trong script gốc → không cần xử lý backend/inline. Tách theo 2 khối `# ===...===` (NHIỆM VỤ 1, NHIỆM VỤ 3). |
| `phase6_features/build_features.py` | `build_features.ipynb` | Có (1: `qc_month_dow_distribution.png`) | 18 (9 code) | 6 hàm (`build_tet_dates_extended`, `compute_days_from_tet`, `build_calendar_features`, `build_train`, `build_forecast`, `qc`) mỗi hàm 1 cell theo đúng khối comment có sẵn; khối `if __name__ == "__main__":` cuối file unwrap thành 1 cell riêng (dedent, không đổi logic). |
| `phase6_features/screen_features.py` | `screen_features.ipynb` | Có (1: `screen_feature_target_corr_heatmap.png`) | 20 (10 code) | Script bọc gần hết logic trong `def main():`, có `try/import matplotlib` cục bộ ở giữa hàm — đã bỏ 2 dòng `import matplotlib`/`matplotlib.use("Agg")` cục bộ đó trong bản notebook (giữ `import matplotlib.pyplot as plt`), phần còn lại của `main()` unwrap bằng `textwrap.dedent` thành 6 cell tuần tự (load data, validate Tết, sàng lọc tương quan, chart, redundancy, hoàn tất). |
| `phase7_baseline/build_baselines.py` | `build_baselines.ipynb` | Có (5: `07_train_fit_vs_actual`, `07_holdout_actual_vs_pred`, `07_forecast_baselines_overlay`, `07_b3_residuals_holdout`, `07_metric_bar_comparison`) | 28 (14 code) | Toàn bộ pipeline nằm trong `def main():` — unwrap bằng `textwrap.dedent` thành 9 cell (helper functions giữ nguyên 1 cell riêng, không unwrap; load+split, fit 4 baseline theo vòng lặp `for target in TARGETS` giữ nguyên 1 cell vì không tách được vòng lặp mà không đổi cấu trúc, lưu metrics, xuất forecast, chọn best, 5 chart tách riêng theo 5 khối `# --- Chart N: ... ---` có sẵn). |

## Verify đã chạy thật, 0 lỗi

Đã quét toàn bộ 9 file `.ipynb` bằng `nbformat` — không cell nào có `output_type == "error"`; đếm được
đúng số ảnh `image/png` trong output khớp bảng trên (46 ảnh tổng cộng, cộng thêm 0 ảnh của
`verify_target_and_cohort.ipynb`). `git status` sau khi chạy xong không phát sinh thay đổi ở bất kỳ file
nào ngoài 9 `.ipynb` mới (các `plt.savefig(...)` ghi đè đúng nội dung y hệt bản cũ, các CSV export cũng
tính lại ra đúng số cũ — không có phân tích mới, không có số liệu mới).
