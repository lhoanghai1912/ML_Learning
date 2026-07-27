# Model Report — Giai đoạn 8: Dự báo Revenue + COGS 548 ngày (tree-based + ensemble)

- **Vai trò:** DS, xây model vượt mốc baseline GĐ7 (B1 seasonal naive), forecast 548 ngày (2023-01-01 → 2024-07-01).
- **Script tái lập:** `EDA_Insight/phase8_model/build_model.py` — chỉ đọc `features_train.csv`, `features_forecast.csv`, `data/sample_submission.csv`. Seed cố định (`SEED=42`). Chạy: `.venv/bin/python EDA_Insight/phase8_model/build_model.py` (~1-2 phút).
- Revenue và COGS **train độc lập** (đúng chốt GĐ5) — không dùng target này để dự đoán target kia.

---

## 1. Problem framing & baseline

**Bài toán:** dự đoán *gross demand* (Revenue, COGS) mỗi ngày cho 548 ngày tương lai, chưa có ground-truth thật. Mốc đánh giá là holdout nội bộ 548 ngày cuối của dữ liệu train (2021-07-02 → 2022-12-31), mô phỏng đúng độ dài + độ mới của horizon thật.

**Baseline phải vượt (GĐ7):** B1 — seasonal naive (ŷ(t) = giá trị cùng ngày năm trước).

| Target | WAPE baseline | MAPE baseline |
|---|---:|---:|
| Revenue | 25.18% | 27.48% |
| COGS | 23.09% | 24.08% |

B1 thắng áp đảo B2 (month-mean) và B3/B3b (linear) ở GĐ7 vì linear model ngoại suy `trend_index` toàn cục bị lệch bias +29-39% (chi tiết `phase7_baseline/baseline_report.md` mục 4.4). **Kết luận GĐ8 phải giải quyết:** không dùng ngoại suy tuyến tính; tận dụng lag mùa vụ (giống B1) nhưng học thêm được cấu trúc phi tuyến/tương tác mà B1 (chỉ nhìn đúng 1 năm trước) bỏ lỡ.

---

## 2. Data & split

- Nguồn: `EDA_Insight/phase6_features/data/features_train.csv` (3,833 ngày, 2012-07-04 → 2022-12-31, có target) và `features_forecast.csv` (548 ngày, không target).
- **Rolling-origin backtest — 5 fold** (không chỉ 1 holdout, theo khuyến nghị GĐ7 mục 5.2/6.3):

| Fold | Holdout | Train_fit kết thúc | Vai trò |
|---|---|---|---|
| `main_548d` | 2021-07-02 → 2022-12-31 | 2021-07-01 | **Fold chính thức** — đúng mốc phải vượt GĐ7 |
| `rolling_1` | 2020-01-01 → 2021-07-01 | 2019-12-31 | Kiểm tra ổn định |
| `rolling_2` | 2018-07-02 → 2019-12-31 | 2018-07-01 | Straddle đúng giai đoạn break 2019 (khó nhất) |
| `rolling_3` | 2016-12-31 → 2018-07-01 | 2016-12-30 | Kiểm tra ổn định |
| `rolling_4` | 2015-07-02 → 2016-12-30 | 2015-07-01 | Kiểm tra ổn định, train_fit ngắn nhất còn đủ dữ liệu (>1000 ngày) |

- Mỗi fold: `train_fit` chỉ chứa dữ liệu **trước** holdout — không leakage. Model production cuối cùng fit trên **toàn bộ** `features_train.csv` (2012-2022) rồi forecast 548 ngày thật — hợp lệ vì không có ngày nào của 2023-2024 bị lộ vào train.
- Model chọn thắng dựa theo **WAPE fold `main_548d`** (đúng mốc chính thức đề bài yêu cầu), các fold `rolling_*` dùng để đánh giá độ ổn định, không dùng làm tiêu chí chọn chính (lý do: `rolling_2` trùng đúng giai đoạn sốc cấu trúc 2019, không đại diện tốt cho horizon thật 2023-2024 gần `main_548d` hơn nhiều).

---

## 3. Features

**Feature lịch thuần (không hành vi khách hàng, không promo tương lai — đúng ràng buộc GĐ5):**
`month, quarter, day_of_week, day_of_month, month_sin, month_cos, dow_sin, dow_cos, is_post_2019, is_post_2019_transition, days_from_tet, is_low_margin_season, trend_index, is_holiday_302_305, is_holiday_qk, is_christmas`.

**Feature lag mới thêm (khuyến nghị mạnh nhất GĐ7 mục 5.2 #2):**
- `lag_365`: giá trị thật (hoặc dự đoán chain, nếu vượt quá 365 ngày horizon) tại đúng ngày cùng kỳ năm trước, có fallback ±3 ngày rồi tới trung bình toàn lịch sử — logic giống hệt B1.
- `lag_365_smooth7`: trung bình 7 ngày quanh mốc lag_365 (±3 ngày) — làm mượt nhiễu ngày lẻ, cho model 1 tín hiệu "mức nền mùa vụ năm trước" ổn định hơn giá trị đơn lẻ.

**Cơ chế forecast tuần tự (recursive, quan trọng để hiểu rủi ro):** horizon 548 ngày > 365 ngày lag, nên 365 ngày đầu horizon dùng `lag_365` từ **actual thật** (dữ liệu train), nhưng ~183 ngày cuối horizon (khoảng từ 2024 trở đi) phải dùng `lag_365` từ **giá trị model tự dự đoán trước đó** (chain), không phải actual — giống hệt cách B1 xử lý ở GĐ7, không phải leakage nhưng có rủi ro cộng dồn sai số (nêu ở mục 6).

**Đã thử nhưng KHÔNG dùng:** feature hành vi khách lặp lại (CLV, retention...), cường độ promo tương lai — loại theo đúng ràng buộc GĐ5/đề bài.

---

## 4. Model + lý do chọn

**Candidate đã test (rolling-origin, cả 2 target):** RandomForest, GradientBoosting (sklearn), XGBoost, LightGBM — đều tree-based, không ngoại suy tuyến tính (đúng khuyến nghị GĐ7). Sau đó test thêm 2 biến thể trên model tree thắng: (a) Ensemble 50/50 với B1 seasonal naive, (b) model huấn luyện riêng theo quý (Q1-Q4).

**Kết quả chọn model — fold `main_548d` (WAPE %):**

| Model | Revenue | COGS |
|---|---:|---:|
| B1 seasonal naive (baseline) | 25.18 | 23.09 |
| RandomForest | 25.13 | 21.31 |
| GradientBoosting | 25.09 | 20.92 |
| XGBoost | 24.63 | 22.34 |
| **LightGBM** | **23.22** | **20.05** |
| LightGBM per-quarter | 24.42 | 22.70 |
| **Ensemble (LightGBM + B1, 50/50)** | **22.71** | **19.79** |

→ **LightGBM thắng trong nhóm tree đơn** (thấp nhất cả 2 target). **Ensemble (LightGBM + B1 trung bình 50/50) thắng cuối cùng** — cải thiện thêm so với LightGBM đơn (Revenue 23.22%→22.71%, COGS 20.05%→19.79%).

**Tại sao ensemble giúp:** LightGBM học được tương tác phi tuyến (month × trend × days_from_tet...) mà B1 không có, nhưng B1 vẫn nắm bắt được biến động ngày-qua-ngày thật của đúng 1 năm trước rất tốt cho các spike đột biến (VD spike Revenue >1×10⁷ giữa 2022, xem chart mục 5) mà LightGBM có xu hướng làm mượt bớt vì học từ nhiều năm gộp lại. Trung bình 2 model có xu hướng khác nhau (1 "quá mượt", 1 "quá theo sát 1 năm") giúp giảm sai số ở cả 2 kiểu lỗi — khớp đúng khuyến nghị GĐ7 mục 5.2 #5 ("ensemble seasonal-naive + tree-based chặn rủi ro đuôi chuỗi").

**Tại sao KHÔNG dùng per-quarter:** model riêng theo quý (mỗi submodel chỉ ~950 ngày dữ liệu thay vì ~3,285) tệ hơn model global trên fold `main_548d` (Revenue 24.42% vs 23.22%, COGS 22.70% vs 20.05%) — mất dữ liệu do chia nhỏ (variance tăng) không được bù lại đủ bởi lợi ích "chuyên biệt hoá theo quý". `quarter` vẫn có mặt như 1 feature trong model global (tree tự học tương tác nếu có ích) — feature importance cho thấy `quarter` gần như **0 importance** (dư thừa hoàn toàn với `month`, đúng phát hiện GĐ6 mục 2), xác nhận thêm bằng chứng lý do per-quarter không giúp: margin/mùa vụ theo quý đã được `month`/`month_sin`/`month_cos` bắt trọn.

**Cấu hình cuối cùng — GIỐNG cho cả 2 target:** LightGBM (global, không chia quý) + Ensemble 50/50 với B1 seasonal naive, production fit trên toàn bộ 2012-2022.

---

## 5. Kết quả (bảng metric, so baseline)

**Holdout chính thức 548 ngày (2021-07-02 → 2022-12-31) — model cuối cùng vs baseline:**

| Target | Metric | B1 baseline (GĐ7) | Model cuối (GĐ8) | Cải thiện |
|---|---|---:|---:|---:|
| Revenue | WAPE | 25.18% | **22.71%** | -2.47 điểm % (-9.8% tương đối) |
| Revenue | MAPE | 27.48% | 26.19% | -1.29 điểm % |
| Revenue | RMSE | 1,022,856 | 945,528 | thấp hơn |
| Revenue | MAE | 724,009 | 653,010 | thấp hơn |
| COGS | WAPE | 23.09% | **19.79%** | -3.30 điểm % (-14.3% tương đối) |
| COGS | MAPE | 24.08% | 21.30% | -2.78 điểm % |
| COGS | RMSE | 830,134 | 726,071 | thấp hơn |
| COGS | MAE | 601,980 | 515,752 | thấp hơn |

**→ VƯỢT MỐC rõ ràng cả 2 target, trên đúng metric chính (WAPE) và cả 3 metric phụ (MAPE/RMSE/MAE).**

**Ổn định qua rolling-origin (avg WAPE 4 fold lịch sử, không tính fold main):**

| Target | B1 (avg) | LightGBM (avg) | Ensemble (avg) | GradientBoosting (avg, tốt nhất về ổn định) |
|---|---:|---:|---:|---:|
| Revenue | 32.39% | 32.81% | 30.53% | 31.57% |
| COGS | 30.78% | 30.45% | 28.43% | **24.05%** |

Chart: `output/phase8/08_backtest_wape_by_fold.png` — mọi model (kể cả B1) đều tệ hẳn ở fold `rolling_2` (2018-07 → 2019-12, đúng giai đoạn sốc cấu trúc break 2019) — đây là **giới hạn của dữ liệu, không phải lỗi model cụ thể nào** (khớp phát hiện GĐ7). Đáng chú ý: `GradientBoosting` ổn định hơn qua các fold cũ (đặc biệt COGS), nhưng KHÔNG được chọn vì tiêu chí chính thức là fold `main_548d` — ghi nhận đây là 1 trade-off cần GĐ9 cân nhắc lại (xem mục 7).

**Feature quan trọng nhất (LightGBM, `data/feature_importance.csv`, chart `08_feature_importance.png`):**

1. `trend_index` — quan trọng nhất cả 2 target (khác linear model, tree không ngoại suy tuyến tính mà chia leaf theo ngưỡng, tránh được bias GĐ7 mục 4.4).
2. `days_from_tet` — mạnh thứ 2, xác nhận hiệu ứng Tết.
3. `day_of_month` — mạnh thứ 3, xác nhận pattern đầu/cuối tháng (GĐ6).
4. `lag_365` và `lag_365_smooth7` — mạnh thứ 4-5, xác nhận khuyến nghị GĐ7 "thêm lag làm feature" đúng hướng.
5. `quarter`, `is_holiday_qk`, `is_christmas` — **~0 importance**, xác nhận dư thừa/nhiễu (khớp cảnh báo GĐ6 mục 2, GĐ6 mục 4-5).

Chart actual-vs-predicted holdout (`08_holdout_actual_vs_pred_final.png`): model cuối bám sát actual rất tốt kể cả ở đỉnh nhọn đột biến (spike Revenue >1.1×10⁷ giữa 2022) — khác hẳn B3 linear GĐ7 (luôn lệch hệ thống lên trên, xem GĐ7 mục 4.4).

---

## 6. Hạn chế & rủi ro (leakage, drift, bias)

1. **Không leakage được xác nhận:** mọi feature (lịch + `lag_365`) chỉ dùng thông tin ≤ ngày t-1 tại thời điểm dự đoán ngày t; train_fit luôn cắt trước holdout ở mọi fold; production fit dùng toàn bộ train 2012-2022 — hợp lệ vì horizon 2023-2024 không có ground-truth nào bị lộ.
2. **Rủi ro cộng dồn sai số (compounding error) ở phần đuôi horizon:** 365 ngày đầu forecast dùng `lag_365` từ actual thật, nhưng ~183 ngày cuối (khoảng nửa đầu 2024) phải dùng `lag_365` từ **giá trị model tự dự đoán** trước đó (chain) — nếu model sai sớm, sai số có thể lan sang các ngày sau. Backtest đã đánh giá đúng cơ chế chain này (không phải đánh giá lạc quan), nhưng CHƯA tách riêng đo WAPE ngày 1-365 vs 366-548 của horizon để định lượng mức độ suy giảm — khuyến nghị GĐ9 làm rõ.
3. **Ensemble tính hậu-nghiệm (post-hoc), không phải chain chung:** LightGBM-chain và B1-chain được tính **độc lập** rồi mới lấy trung bình — nghĩa là lag input của mỗi nhánh KHÔNG dùng giá trị ensemble cuối cùng, chỉ dùng giá trị chain riêng của chính nó. Đây là xấp xỉ hợp lý cho phạm vi GĐ8 nhưng khác 1 ensemble "đệ quy thật" (dùng chính giá trị blend làm lag cho bước sau) — rủi ro nhỏ, cần lưu ý khi diễn giải.
4. **Không có ground-truth 2023-2024:** mọi con số WAPE/MAPE trong báo cáo này đến từ holdout nội bộ (2012-2022) — độ tin cậy khi áp dụng cho horizon thật phụ thuộc giả định "cơ chế sinh dữ liệu 2023-2024 tương tự 2012-2022", CHƯA được kiểm chứng (đúng cảnh báo GĐ7 mục 6.4 về rủi ro ngoại suy giai đoạn phục hồi 2022).
5. **Fold `rolling_2` (break 2019) cho thấy MỌI model (kể cả B1) đều kém (WAPE 44-63%)** — nếu 2023-2024 xảy ra 1 cú sốc cấu trúc tương tự (không có bằng chứng nào trong dữ liệu hiện tại xác nhận hay phủ nhận), model này (và mọi model khác train trên 2012-2022) đều có rủi ro tương tự — đây là giới hạn cấu trúc của bài toán, không riêng gì model GĐ8.
6. **Chỉ 5 fold rolling-origin** (giới hạn bởi độ dài dữ liệu 10.5 năm / 548 ngày mỗi fold) — bằng chứng ổn định chưa thật nhiều, đặc biệt chỉ có 1 fold "hậu-break" (`main_548d`, `rolling_1`) so với 1 fold "giữa-break" và 2 fold "tiền-break".
7. **Không tune hyperparameter** (dùng cấu hình mặc định hợp lý, seed cố định) — có thể còn dư địa cải thiện nhưng cũng có rủi ro overfit nếu tune quá tay trên dữ liệu ít (3,833 ngày).
8. **`GradientBoosting` ổn định hơn qua lịch sử nhưng không được chọn** (chỉ so trên fold main theo đúng tiêu chí đề bài) — nếu ưu tiên robustness dài hạn hơn là khớp đúng mốc GĐ7, đây là lựa chọn thay thế đáng cân nhắc (xem mục 7).

---

## 7. Bước tiếp theo (khuyến nghị cho GĐ9)

1. **Validate format nộp:** đối chiếu `data/forecast_548.csv` với `sample_submission.csv` — số cột, tên cột, số dòng (548, đã tự-assert trong script), kiểu số (2 chữ số thập phân), không NaN/âm (đã tự-assert). Nên kiểm tra thêm encoding/line-ending nếu hệ thống chấm bài nhạy cảm.
2. **SHAP** cho LightGBM (Revenue + COGS) để hiểu chiều tác động (không chỉ độ lớn importance dạng split-count như hiện tại) — đặc biệt xem `trend_index` và `lag_365` tương tác thế nào ở vùng ngoại suy (trend_index forecast > max train).
3. **Tách riêng đo WAPE ngày 1-365 vs 366-548** của holdout main để định lượng rủi ro cộng dồn sai số nêu ở mục 6.2 — nếu suy giảm mạnh, cân nhắc dùng lag_182 (nửa năm) bổ sung hoặc horizon ngắn hơn cho phần đuôi.
4. **Cân nhắc lại GradientBoosting làm phương án dự phòng** (ổn định hơn qua rolling fold, đặc biệt COGS) nếu ưu tiên robustness thay vì chỉ khớp đúng mốc `main_548d`.
5. **Thử ensemble weight khác 50/50** (VD tối ưu trọng số trên validation riêng, hoặc trọng số giảm dần theo khoảng cách ngày dự đoán) thay vì cố định.
6. **Kế hoạch retrain/monitor drift:** khi có actual 2023 thật (dù một phần), nên retrain lại theo lịch (VD mỗi quý) và theo dõi WAPE rolling trên dữ liệu mới để phát hiện sớm nếu cơ chế sinh dữ liệu đổi khác so với 2012-2022.

---

### Cập nhật GĐ9 (đã thực hiện — `phase9_validation/validation_report.md`)

Các khuyến nghị #2, #3, #4, #5 ở trên đã được kiểm tại GĐ9, **KHÔNG đổi model/weight → giữ nguyên `forecast_548.csv`**:

- **#2 SHAP:** chiều tác động khớp GĐ6 (`lag_365` +, `trend_index` −, `days_from_tet` +, `day_of_month` +); `quarter`/`is_holiday_qk`/`is_christmas` mean|SHAP|=0 xác nhận lại. **Phát hiện mới:** `trend_index` ở vùng ngoại suy (100% ngày forecast > max train) bị **tree chặn phẳng ở leaf cuối** → đóng góp hằng số cho toàn forecast; rủi ro under-forecast nếu 2023–2024 tăng nền vượt lịch sử (đưa vào §6 hạn chế).
- **#3 Horizon:** đuôi (366–548, lag chain) KHÔNG suy giảm — còn tốt hơn đầu (Rev −3.74, COGS −0.84 điểm) → rủi ro §6.2 không hiện thực hóa; **không cần lag_182**.
- **#4/#5 Robustness + weight:** Ensemble 50/50 thắng main + no-break cả 2 target; grid weight 0.30–0.70 cho argmin đúng tại 0.5 (validation) → **giữ 50/50**. GradientBoosting chỉ hơn ở fold break `rolling_2` → giữ làm fallback nếu drift báo sốc cấu trúc.

---

## 8. Danh sách file output

- `build_model.py` — script tái lập đầy đủ.
- `data/backtest_metrics.csv` — metric mọi fold × mọi model (kể cả B1, ensemble, per-quarter).
- `data/holdout_predictions.csv` — actual + dự đoán (B1, tree thắng, ensemble) trên fold `main_548d`.
- `data/feature_importance.csv` — importance LightGBM, 2 target.
- `data/forecast_548.csv` — **bản nộp cuối cùng**, đúng format `Date,Revenue,COGS`, 548 dòng, không NaN, không âm.
- `data/final_choice.txt` — cấu hình model cuối cùng mỗi target.
- `output/phase8/08_backtest_wape_by_fold.png` — WAPE mọi model qua 5 fold.
- `output/phase8/08_holdout_actual_vs_pred_final.png` — actual vs predicted model cuối, holdout main.
- `output/phase8/08_feature_importance.png` — feature importance 2 target.
- `output/phase8/08_forecast_548_final.png` — forecast 548 ngày thật, model cuối cùng.
