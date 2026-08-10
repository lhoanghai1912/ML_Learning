"""test_ingestion.py — `datathon.ingestion`, phần chưa được test trực tiếp trước đây
(`tests/test_schema.py`/`conftest.py` chỉ dùng gián tiếp `load_raw`/`add_metadata_columns` qua
fixture, không tự assert). Cover 4 phần cốt lõi:

    - `IngestResult`             — dataclass, field mặc định.
    - `split_valid_quarantine`   — tách dòng hợp lệ/lỗi theo `SchemaValidationResult`, gắn `_dq_reason`.
    - `merge_upsert`             — mô phỏng MERGE INTO idempotent theo natural key (bất biến nhấn
                                     mạnh xuyên suốt M2/M3b — verify ở tầng pandas trước khi tin
                                     hành vi tương tự trên Trino/Iceberg thật).
    - `ingest_table`             — tích hợp load+metadata+validate+quarantine trên `data/sample`
                                     THẬT (14 bảng) + 1 CSV lỗi tự tạo (không suy đoán trạng thái
                                     QUARANTINED/FAILED, tạo dữ liệu vi phạm thật rồi assert).

Style theo `tests/test_schema.py`: hàm thật, không mock (`unittest.mock`) — chỉ dùng
`monkeypatch.setitem` để trỏ 1 bảng sang CSV lỗi tự tạo trong `tmp_path`, không đụng
`data/sample` gốc.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from datathon import ingestion
from datathon import schema as schema_mod

# ---------------------------------------------------------------------------
# 1. IngestResult — dataclass
# ---------------------------------------------------------------------------


class TestIngestResult:
    def test_construction_and_fields(self) -> None:
        r = ingestion.IngestResult(
            table="customers",
            batch_id="abc123",
            rows_in=10,
            rows_valid=9,
            rows_quarantined=1,
            ts="2026-01-01T00:00:00+00:00",
            status="QUARANTINED",
            quarantine_reasons={"schema_violation": 1},
        )
        assert r.table == "customers"
        assert r.status == "QUARANTINED"
        assert r.rows_valid + r.rows_quarantined == r.rows_in
        assert r.quarantine_reasons == {"schema_violation": 1}

    def test_quarantine_reasons_defaults_to_empty_dict(self) -> None:
        r = ingestion.IngestResult(
            table="geography", batch_id="x", rows_in=5, rows_valid=5,
            rows_quarantined=0, ts="2026-01-01T00:00:00+00:00", status="OK",
        )
        assert r.quarantine_reasons == {}

    def test_default_dict_not_shared_between_instances(self) -> None:
        """`field(default_factory=dict)` — bẫy kinh điển nếu lỡ dùng `= {}` (mutable default
        dùng chung mọi instance). Verify đúng factory, không phải giả định suông."""
        r1 = ingestion.IngestResult("a", "b1", 1, 1, 0, "t", "OK")
        r2 = ingestion.IngestResult("a", "b2", 1, 1, 0, "t", "OK")
        r1.quarantine_reasons["x"] = 1
        assert r2.quarantine_reasons == {}


# ---------------------------------------------------------------------------
# 2. split_valid_quarantine
# ---------------------------------------------------------------------------


def _geo_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


class TestSplitValidQuarantine:
    def test_all_valid_rows_quarantine_empty_no_reason_column(self) -> None:
        df = _geo_df([{"zip": 1, "city": "Hai Phong", "region": "North", "district": "D1"}])
        validation = schema_mod.validate_schema(df, "geography")
        valid, bad = ingestion.split_valid_quarantine(df, validation)

        assert len(valid) == 1
        assert len(bad) == 0
        assert "_dq_reason" not in bad.columns  # cột chỉ gắn khi len(bad) > 0, xem .sql/.py

    def test_dtype_violation_row_quarantined_with_reason_tagged(self) -> None:
        df = _geo_df([
            {"zip": 1, "city": "A", "region": "North", "district": "D1"},
            {"zip": "khong-phai-so", "city": "B", "region": "North", "district": "D2"},
        ])
        validation = schema_mod.validate_schema(df, "geography")
        valid, bad = ingestion.split_valid_quarantine(df, validation)

        assert len(valid) == 1 and len(bad) == 1
        assert valid["city"].iloc[0] == "A"
        assert bad["city"].iloc[0] == "B"
        assert "dtype_mismatch:zip" in bad["_dq_reason"].iloc[0]

    def test_enum_violation_row_quarantined_with_reason_tagged(self) -> None:
        df = pd.DataFrame([
            {"customer_id": 1, "zip": 1, "city": "A", "signup_date": "2020-01-01",
             "gender": "Female", "age_group": "25-34", "acquisition_channel": "direct"},
            {"customer_id": 2, "zip": 2, "city": "B", "signup_date": "2020-01-02",
             "gender": "Alien", "age_group": "25-34", "acquisition_channel": "direct"},
        ])
        validation = schema_mod.validate_schema(df, "customers")
        valid, bad = ingestion.split_valid_quarantine(df, validation)

        assert len(valid) == 1 and len(bad) == 1
        assert bad["customer_id"].iloc[0] == 2
        assert "enum_violation:gender" in bad["_dq_reason"].iloc[0]

    def test_does_not_mutate_input_dataframe(self) -> None:
        df = _geo_df([{"zip": 1, "city": "A", "region": "North", "district": "D1"}])
        cols_before = list(df.columns)
        validation = schema_mod.validate_schema(df, "geography")
        ingestion.split_valid_quarantine(df, validation)
        assert list(df.columns) == cols_before  # không lòi thêm _dq_reason vào df gốc


# ---------------------------------------------------------------------------
# 3. merge_upsert — idempotent MERGE theo natural key
# ---------------------------------------------------------------------------


class TestMergeUpsert:
    def test_no_existing_dedupes_last_row_per_key_in_given_order(self) -> None:
        """existing=None: dedup theo THỨ TỰ dòng trong `incoming` (docstring — không tự sort theo
        updated_at ở nhánh này), verify đúng hành vi thật chứ không suy đoán."""
        incoming = pd.DataFrame([
            {"k": 1, "v": "old", "_ingested_at": "2026-01-01T00:00:00Z"},
            {"k": 2, "v": "c", "_ingested_at": "2026-01-01T00:00:00Z"},
            {"k": 1, "v": "new", "_ingested_at": "2026-01-02T00:00:00Z"},
        ])
        out = ingestion.merge_upsert(None, incoming, natural_key=["k"])
        assert len(out) == 2
        assert out.set_index("k").loc[1, "v"] == "new"

    def test_existing_plus_incoming_keeps_newest_by_updated_at(self) -> None:
        existing = pd.DataFrame([{"k": 1, "v": "old", "_ingested_at": "2026-01-01T00:00:00Z"}])
        incoming = pd.DataFrame([{"k": 1, "v": "new", "_ingested_at": "2026-01-02T00:00:00Z"}])
        out = ingestion.merge_upsert(existing, incoming, natural_key=["k"])
        assert len(out) == 1
        assert out["v"].iloc[0] == "new"

    def test_incoming_wins_tie_break_on_equal_timestamp(self) -> None:
        """Docstring: "incoming luôn thắng existing cùng timestamp" — verify đúng thật, không
        tin lời docstring suông."""
        existing = pd.DataFrame([{"k": 1, "v": "existing_val", "_ingested_at": "2026-01-01T00:00:00Z"}])
        incoming = pd.DataFrame([{"k": 1, "v": "incoming_val", "_ingested_at": "2026-01-01T00:00:00Z"}])
        out = ingestion.merge_upsert(existing, incoming, natural_key=["k"])
        assert len(out) == 1
        assert out["v"].iloc[0] == "incoming_val"

    def test_calling_twice_with_same_incoming_is_idempotent(self) -> None:
        """Đúng bất biến MERGE idempotent nhấn mạnh xuyên suốt PROCESS.md (M2 re-ingest
        promotions 50->50, M3b build lại không đổi count) — verify ở tầng pandas."""
        incoming = pd.DataFrame([
            {"k": 1, "v": "a", "_ingested_at": "2026-01-01T00:00:00Z"},
            {"k": 2, "v": "b", "_ingested_at": "2026-01-01T00:00:00Z"},
        ])
        first = ingestion.merge_upsert(None, incoming, natural_key=["k"])
        second = ingestion.merge_upsert(first, incoming, natural_key=["k"])

        assert len(first) == len(second) == 2
        pd.testing.assert_frame_equal(
            first.sort_values("k").reset_index(drop=True),
            second.sort_values("k").reset_index(drop=True),
        )

    def test_unrelated_existing_rows_survive_unchanged(self) -> None:
        existing = pd.DataFrame([
            {"k": 1, "v": "keep_me", "_ingested_at": "2026-01-01T00:00:00Z"},
        ])
        incoming = pd.DataFrame([
            {"k": 2, "v": "new_row", "_ingested_at": "2026-01-05T00:00:00Z"},
        ])
        out = ingestion.merge_upsert(existing, incoming, natural_key=["k"])
        assert len(out) == 2
        assert out.set_index("k").loc[1, "v"] == "keep_me"
        assert out.set_index("k").loc[2, "v"] == "new_row"


# ---------------------------------------------------------------------------
# 4. ingest_table — tích hợp, chạy trên data/sample THẬT + 1 CSV lỗi tự tạo
# ---------------------------------------------------------------------------


class TestIngestTable:
    def test_bad_table_name_raises_keyerror(self) -> None:
        with pytest.raises(KeyError):
            ingestion.ingest_table("khong_ton_tai")

    def test_reuses_given_batch_id(self) -> None:
        _, _, result = ingestion.ingest_table("customers", batch_id="fixed-batch-xyz")
        assert result.batch_id == "fixed-batch-xyz"

    def test_generates_batch_id_when_not_given(self) -> None:
        _, _, result = ingestion.ingest_table("geography")
        assert result.batch_id  # non-empty
        _, _, result2 = ingestion.ingest_table("geography")
        assert result.batch_id != result2.batch_id  # 2 lần gọi khác batch_id (uuid4)

    def test_order_items_gets_unique_surrogate_key_column(self) -> None:
        valid, _bad, result = ingestion.ingest_table("order_items")
        assert schema_mod.ORDER_ITEMS_SURROGATE_KEY in valid.columns
        assert valid[schema_mod.ORDER_ITEMS_SURROGATE_KEY].is_unique
        assert result.status in ("OK", "QUARANTINED")

    @pytest.mark.parametrize("table", list(schema_mod.ALL_TABLES))
    def test_runs_clean_on_every_sample_table(self, table: str) -> None:
        """DoD kiểu M4a ("run_all 14 bảng") nhưng cho đúng `ingest_table` — trước đây chưa ai
        loop qua cả 14 bảng gọi hàm này, chỉ có `quality.run_all` loop DQ (khác hàm)."""
        valid, bad, result = ingestion.ingest_table(table)
        assert result.status in ("OK", "QUARANTINED"), (
            f"{table}: status={result.status} (FAILED nghĩa là thiếu cột — sample hỏng?)"
        )
        assert result.rows_in == len(valid) + len(bad)
        assert result.rows_valid == len(valid)
        assert result.rows_quarantined == len(bad)

    def test_quarantines_real_enum_violation_not_silently_dropped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Tạo 1 CSV customers CÓ THẬT 1 dòng vi phạm enum (gender) — verify ingest_table()
        tách đúng quarantine, KHÔNG drop im (đúng rule DE HARDENING bắt buộc). Không suy đoán
        trạng thái QUARANTINED — dựng dữ liệu lỗi thật rồi chạy hàm thật."""
        bad_csv = tmp_path / "customers.csv"
        pd.DataFrame([
            {"customer_id": 1, "zip": 10001, "city": "Hanoi", "signup_date": "2020-01-01",
             "gender": "Female", "age_group": "25-34", "acquisition_channel": "direct"},
            {"customer_id": 2, "zip": 10002, "city": "Hue", "signup_date": "2020-01-02",
             "gender": "Alien", "age_group": "25-34", "acquisition_channel": "direct"},
        ]).to_csv(bad_csv, index=False)
        monkeypatch.setitem(ingestion.RAW_TABLES, "customers", bad_csv)

        _valid, bad, result = ingestion.ingest_table("customers")

        assert result.status == "QUARANTINED"
        assert result.rows_in == 2
        assert result.rows_valid == 1
        assert result.rows_quarantined == 1
        assert bad["customer_id"].iloc[0] == 2
        assert "enum_violation:gender" in bad["_dq_reason"].iloc[0]
        assert result.quarantine_reasons == {"schema_violation": 1}

    def test_missing_required_column_triggers_failed_status(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Thiếu cột bắt buộc (region/district) -> lỗi CẤU TRÚC, không dùng được bảng ->
        status FAILED (khác QUARANTINED — bảng vẫn đọc được, chỉ 1 số dòng lỗi)."""
        bad_csv = tmp_path / "geography.csv"
        pd.DataFrame([{"zip": 1, "city": "Hanoi"}]).to_csv(bad_csv, index=False)
        monkeypatch.setitem(ingestion.RAW_TABLES, "geography", bad_csv)

        _valid, _bad, result = ingestion.ingest_table("geography")

        assert result.status == "FAILED"
