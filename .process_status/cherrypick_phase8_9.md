# Cherry-pick phase8_model + phase9_validation — REPORT

Agent: pm/ba. Nợ #2 (PROCESS.md nhật ký 2026-08-06 "QUYẾT ĐỊNH tiến độ RICE").
Ownership: `docs/analysis/phase8_model/*`, `docs/analysis/phase9_validation/*`
+ ngoại lệ 1 cell `notebooks/03_forecasting_colab.ipynb` (id `ac4a7e19`).

**Status: ❌ BLOCKED — chưa làm được, KHÔNG tự nhận ✅.**

## Chặn ở đâu

Session agent này chỉ có tool: Read, Edit, Write, Glob, Grep. Không có
Bash/shell. Việc bắt buộc cần shell, không làm được:

- Bước 1 (copy nguồn): cần `git show feat/phase8-model:<path>` — Read tool
  chỉ đọc file thật trên đĩa, không đọc được blob ở branch/commit khác.
- Bước 3 (verify): cần `jupyter nbconvert --execute --inplace` — không chạy
  được, không có shell.

Đã thử tìm đường vòng, không có:
- `docs/analysis/phase8_model`, `docs/analysis/phase9_validation`: Glob xác
  nhận **0 file** — đúng như PROCESS.md mô tả, chưa ai copy trước.
- Tìm worktree khác trên máy có thể chứa sẵn `feat/phase8-model` đã checkout
  (`.git/worktrees/angry-roentgen-9f92d9`): trỏ tới
  `/Users/lhoanghai_/Downloads/Dự án datathon2026/.claude/worktrees/...` —
  thư mục **không còn tồn tại** (worktree cũ đã dọn), không dùng được.
- Không có cách nào khác đọc nội dung blob ở branch khác mà không có shell.

## Đã làm được (không cần shell, đọc-only)

1. Đọc `PROCESS.md` — xác nhận đúng nợ #2, đúng danh sách file nguồn.
2. `Glob docs/analysis/phase8_model/**` + `phase9_validation/**` → 0 file
   (xác nhận đích trống, chưa trùng lặp việc ai đã làm).
3. Đọc `notebooks/03_forecasting_colab.ipynb` toàn bộ phần liên quan (cell
   `8c3759e0` markdown giải thích, cell `ac4a7e19` code đọc baseline, cell
   `4f73d83c` regression assert, mục 9.6 + mục 10 cuối notebook cũng nhắc
   nợ này) — xác định CHÍNH XÁC 1 cell cần sửa: **`ac4a7e19`**.
4. Soạn sẵn lệnh + nội dung sửa (bên dưới) — sẵn sàng chạy ngay khi có shell,
   không cần điều tra lại.

## Việc cần PO làm (1 trong 2)

- **(a) Cấp Bash tool cho session này** → chạy tiếp ngay theo kế hoạch dưới.
- **(b) PO tự chạy** các lệnh dưới (hoặc giao agent có Bash) — report này đủ
  chi tiết để chạy thẳng không cần suy nghĩ lại.

## Kế hoạch sẵn (chạy khi có shell)

### Bước 1 — liệt kê + copy nguyên file (không cherry-pick commit)

```bash
cd "/Users/lhoanghai_/Documents/Study/Dự án datathon2026"

# liệt kê đúng danh sách file + blob SHA (dùng verify byte-identical sau)
git ls-tree -r feat/phase8-model -- EDA_Insight/phase8_model EDA_Insight/phase9_validation \
  > /tmp/phase89_filelist.txt
cat /tmp/phase89_filelist.txt

mkdir -p docs/analysis/phase8_model/data
mkdir -p docs/analysis/phase9_validation/committed_baseline
mkdir -p docs/analysis/phase9_validation/data

# copy TỪNG file bằng git show (không dùng git checkout/cherry-pick — không
# kéo diff thừa của nhánh kia), path đích = path nguồn bỏ prefix EDA_Insight/
git ls-tree -r --name-only feat/phase8-model \
  -- EDA_Insight/phase8_model EDA_Insight/phase9_validation | while read -r f; do
  dst="docs/analysis/${f#EDA_Insight/}"
  mkdir -p "$(dirname "$dst")"
  git show "feat/phase8-model:$f" > "$dst"
  echo "copied: $f -> $dst"
done
```

### Verify byte-identical (so blob SHA, không suy đoán)

```bash
git ls-tree -r --name-only feat/phase8-model \
  -- EDA_Insight/phase8_model EDA_Insight/phase9_validation | while read -r f; do
  dst="docs/analysis/${f#EDA_Insight/}"
  src_sha=$(git ls-tree feat/phase8-model "$f" | awk '{print $3}')
  dst_sha=$(git hash-object "$dst")
  [ "$src_sha" = "$dst_sha" ] && echo "OK   $dst" || echo "DIFF $dst  src=$src_sha dst=$dst_sha"
done
```

Tất cả phải in `OK` — có `DIFF` thì dừng, báo lại (đừng tiếp bước 2).

⚠ Lưu ý riêng `forecast_548_SUBMIT_crlf.csv` (CRLF cố ý) — `git show > file`
qua redirect không đổi line ending, verify SHA ở trên tự phát hiện nếu bị đổi.

### Bước 2 — sửa cell `ac4a7e19` (CHỈ cell này)

Nội dung hiện tại (giữ fallback `git show f4bc6a4:...`):

```python
LOCAL_BASELINE = (
    PROJECT_ROOT / "docs" / "analysis" / "phase9_validation" / "committed_baseline"
    / "forecast_548.committed.csv"
)
FALLBACK_REF = "f4bc6a4:EDA_Insight/phase9_validation/committed_baseline/forecast_548.committed.csv"

if LOCAL_BASELINE.exists():
    baseline = pd.read_csv(LOCAL_BASELINE)
    baseline_source = str(LOCAL_BASELINE)
else:
    proc = subprocess.run(
        ["git", "show", FALLBACK_REF], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
    )
    baseline = pd.read_csv(io.StringIO(proc.stdout))
    baseline_source = f"git show {FALLBACK_REF}"

print("Baseline nguon:", baseline_source)
print("Baseline shape:", baseline.shape)
baseline.head(2)
```

Đổi thành (bỏ hẳn `git show`, đọc file local trực tiếp — đúng yêu cầu PO):

```python
LOCAL_BASELINE = (
    PROJECT_ROOT / "docs" / "analysis" / "phase9_validation" / "committed_baseline"
    / "forecast_548.committed.csv"
)
assert LOCAL_BASELINE.exists(), (
    f"Thieu baseline: {LOCAL_BASELINE}. Xem docs/analysis/phase9_validation/ "
    "(cherry-pick tu feat/phase8-model, .process_status/cherrypick_phase8_9.md)."
)
baseline = pd.read_csv(LOCAL_BASELINE)
baseline_source = str(LOCAL_BASELINE)

print("Baseline nguon:", baseline_source)
print("Baseline shape:", baseline.shape)
baseline.head(2)
```

**Chưa apply** — đợi bước 1 xong trước (nếu apply trước, cell fail ngay vì
file local chưa tồn tại, làm gãy notebook đang PASS).

**Nợ hỏi PO** (không tự quyết theo đúng ràng buộc task): sau khi sửa
`ac4a7e19`, các cell/mục sau sẽ NÓI SAI (còn nhắc `git show f4bc6a4` /
"CHƯA có" / "PO nợ cherry-pick") nhưng nằm NGOÀI phạm vi cho phép sửa:
- markdown cell `8c3759e0` (đoạn giải thích ngay trên `ac4a7e19`)
- mục 9.6 (rủi ro "phụ thuộc git show")
- mục 10 cuối notebook, dòng "PO nợ: cherry-pick..."

→ Để nguyên (lỗi thời nhưng không sai kỹ thuật) hay PO duyệt cho sửa nốt 3
chỗ text này trong lần chạy kế? Không tự quyết.

### Bước 3 — re-run verify

```bash
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=python3 --ExecutePreprocessor.timeout=900 \
  notebooks/03_forecasting_colab.ipynb
```

Check: exit code 0, quét `nbformat` toàn bộ cell output type `error` = 0,
cell `ac4a7e19` in `Baseline nguon: docs/analysis/phase9_validation/...`
(KHÔNG còn chữ "git show"), cell `4f73d83c` in `max abs diff = 0.0`.
Dán log thật vào report này, không suy đoán số.

### Bước 4 — dọn + note M4b (theo yêu cầu PO)

- `.process_status/M4b.md` cũng tham chiếu nguồn `feat/phase8-model` tương
  tự — **PO tự quyết** có cập nhật hay để nguyên làm lịch sử (report không
  phải file sống). Không tự sửa.
- Commit riêng: `git add docs/analysis/phase8_model docs/analysis/phase9_validation` +
  `git add notebooks/03_forecasting_colab.ipynb` (2 commit tách, hoặc 1 commit
  gộp nếu PO đồng ý — không `git add -A`).
- KHÔNG commit `PROCESS.md` (đúng protocol) — PO tự cập nhật bảng milestone
  sau khi verify.

## Rủi ro nếu không làm sớm (không đổi so với PROCESS.md đã ghi)

`feat/phase8-model` (commit `f4bc6a4`) có thể bị dọn/xoá bất cứ lúc nào,
ngoài kiểm soát của PROCESS này. M4b (`f4036f9`) + M6b (`604cb48`) đang phụ
thuộc trực tiếp commit rời đó để đối chiếu regression — mất là mất luôn
nguồn đối chiếu (không phải model sai, nhưng không audit lại được).

## Việc còn thiếu / chưa làm (khai rõ, không nhận vơ)

- [ ] Copy 2 thư mục (bước 1) — CHƯA làm, cần shell.
- [ ] Verify byte-identical SHA (bước 1b) — CHƯA làm.
- [ ] Sửa cell `ac4a7e19` (bước 2) — CHƯA apply, chỉ soạn sẵn.
- [ ] Re-run nbconvert + verify regression PASS (bước 3) — CHƯA làm.
- [ ] Commit — CHƯA làm.
