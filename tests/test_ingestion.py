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

2026-08-10 — vá 5 gap coverage từ audit độc lập
(`.process_status/tester_verify_test_ingestion_2026-08-10.md`). Thêm 4 nhóm class nữa cho các
hàm phụ trợ NẰM NGOÀI "4 phần cốt lõi" khai ở trên nhưng được `ingest_table` dùng bên trong
(trước bản vá: dùng gián tiếp qua 32 test cũ nhưng KHÔNG có test nào tự assert riêng):

    - `load_raw`                   — nhánh lỗi `FileNotFoundError` (G3).
    - `add_metadata_columns`       — đủ 5 cột metadata bắt buộc, đúng tên/giá trị/kiểu (G1 —
                                       Medium, contract cứng "DE HARDENING STANDARD").
    - `_row_checksum`              — nội dung cột `_checksum`: deterministic + xử lý NaN (G2).
    - `build_order_items_line_id`  — nhánh lỗi `ValueError` khi thiếu `_source_row_number` (G4).

Đồng thời pin lại đúng trạng thái/số dòng quarantine ĐO THẬT trên `data/sample`
(`test_runs_clean_on_every_sample_table`, `test_order_items_gets_unique_surrogate_key_column`
trong `TestIngestTable`) thay vì chấp nhận lỏng `status in ("OK", "QUARANTINED")` (G5).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
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
# 3. load_raw — nhánh lỗi FileNotFoundError chưa từng được test (G3)
# ---------------------------------------------------------------------------


class TestLoadRaw:
    """`load_raw()` có 2 nhánh lỗi: bảng không khai trong `RAW_TABLES` (`KeyError`, đã cover
    gián tiếp qua `TestIngestTable.test_bad_table_name_raises_keyerror`) và path CÓ khai trong
    `RAW_TABLES` nhưng file không tồn tại trên đĩa (`FileNotFoundError`, G3 — trước bản vá 0 test
    nào trong toàn repo chạm nhánh này)."""

    def test_missing_file_on_disk_raises_file_not_found_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ghost_path = tmp_path / "khong_ton_tai_tren_dia.csv"
        assert not ghost_path.exists()  # tiền đề test phải đúng thật, không giả định suông
        monkeypatch.setitem(ingestion.RAW_TABLES, "customers", ghost_path)

        with pytest.raises(FileNotFoundError, match="customers"):
            ingestion.load_raw("customers")

    def test_error_message_names_missing_table_and_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Message phải đủ thông tin debug (tên bảng + path) — đúng nội dung hàm thật build,
        không suy đoán format chung chung."""
        ghost_path = tmp_path / "geography_khong_ton_tai.csv"
        monkeypatch.setitem(ingestion.RAW_TABLES, "geography", ghost_path)

        with pytest.raises(FileNotFoundError) as exc_info:
            ingestion.load_raw("geography")
        assert "geography" in str(exc_info.value)
        assert str(ghost_path) in str(exc_info.value)


# ---------------------------------------------------------------------------
# 4. add_metadata_columns — 5 cột metadata bắt buộc (G1, contract cứng DE HARDENING STANDARD)
# ---------------------------------------------------------------------------


# Hardcode trực tiếp từ docstring `ingestion.py` + `RESTRUCTURE_AGENTS.md` "DE HARDENING
# STANDARD" — KHÔNG import lại `schema.METADATA_COLUMNS`, để test này là 1 chốt hợp đồng ĐỘC LẬP
# (nếu `schema.py` VÀ `ingestion.py` cùng lỡ sửa/xoá 1 cột, test vẫn phải đỏ thay vì tự che bug).
REQUIRED_METADATA_COLUMNS = (
    "_ingested_at", "_source_file", "_source_row_number", "_checksum", "_batch_id",
)


def _biz_df() -> pd.DataFrame:
    return pd.DataFrame({"a": [10, 20, 30], "b": ["x", "y", "z"]})


class TestAddMetadataColumns:
    """`add_metadata_columns()` — G1: trước bản vá không có test nào assert đủ 5 cột metadata
    bắt buộc tồn tại đúng tên + đúng giá trị/kiểu, dù đây là contract cứng (docstring module +
    `RESTRUCTURE_AGENTS.md` "DE HARDENING STANDARD"). Sửa hỏng 1 cột trước đây sẽ KHÔNG có test
    nào của file này báo đỏ."""

    def test_adds_all_five_required_metadata_columns(self) -> None:
        out = ingestion.add_metadata_columns(_biz_df(), source_file="f.csv", batch_id="b1")
        for col in REQUIRED_METADATA_COLUMNS:
            assert col in out.columns, f"thiếu cột metadata bắt buộc: {col}"

    def test_original_business_columns_preserved_unchanged(self) -> None:
        out = ingestion.add_metadata_columns(_biz_df(), source_file="f.csv", batch_id="b1")
        assert list(out["a"]) == [10, 20, 30]
        assert list(out["b"]) == ["x", "y", "z"]

    def test_source_file_column_equals_argument_for_every_row(self) -> None:
        out = ingestion.add_metadata_columns(
            _biz_df(), source_file="data/raw/customers.csv", batch_id="b1"
        )
        assert (out["_source_file"] == "data/raw/customers.csv").all()

    def test_batch_id_column_equals_argument_for_every_row(self) -> None:
        out = ingestion.add_metadata_columns(_biz_df(), source_file="f.csv", batch_id="batch-xyz-123")
        assert (out["_batch_id"] == "batch-xyz-123").all()

    def test_source_row_number_is_zero_based_sequential_in_row_order(self) -> None:
        out = ingestion.add_metadata_columns(_biz_df(), source_file="f.csv", batch_id="b1")
        assert list(out["_source_row_number"]) == [0, 1, 2]

    def test_ingested_at_is_timezone_aware_utc_iso_timestamp_close_to_now(self) -> None:
        before = datetime.now(timezone.utc)
        out = ingestion.add_metadata_columns(_biz_df(), source_file="f.csv", batch_id="b1")
        after = datetime.now(timezone.utc)

        parsed = datetime.fromisoformat(out["_ingested_at"].iloc[0])
        assert parsed.tzinfo is not None  # aware, không phải naive datetime
        assert before <= parsed <= after
        assert out["_ingested_at"].nunique() == 1  # 1 timestamp dùng chung mọi dòng cùng lần gọi

    def test_checksum_column_is_64_char_hex_string_on_every_row(self) -> None:
        out = ingestion.add_metadata_columns(_biz_df(), source_file="f.csv", batch_id="b1")
        assert out["_checksum"].apply(lambda v: isinstance(v, str) and len(v) == 64).all()

    def test_does_not_mutate_input_dataframe(self) -> None:
        """Docstring hàm: "Trả DataFrame MỚI — không sửa df gốc". Cùng convention với
        `TestSplitValidQuarantine.test_does_not_mutate_input_dataframe` — verify thật, không tin
        docstring suông."""
        df = _biz_df()
        cols_before = list(df.columns)
        ingestion.add_metadata_columns(df, source_file="f.csv", batch_id="b1")
        assert list(df.columns) == cols_before

    def test_returns_new_dataframe_object_not_same_reference(self) -> None:
        df = _biz_df()
        out = ingestion.add_metadata_columns(df, source_file="f.csv", batch_id="b1")
        assert out is not df


# ---------------------------------------------------------------------------
# 5. _row_checksum / cột _checksum — nội dung, deterministic, xử lý NaN (G2)
# ---------------------------------------------------------------------------


class TestRowChecksum:
    """`_row_checksum()` (private, "_"-prefixed — Python không ép private thật, import thẳng
    qua module để test vì không có API public thay thế đọc trực tiếp cột `_checksum`). G2:
    trước bản vá 0 test trong toàn repo đọc/assert nội dung cột này.

    Dựng row test bằng `pd.Series({...}, dtype="object")` (ép `dtype=object` tường minh) thay vì
    để pandas tự suy kiểu — đã verify riêng trước khi viết test này:
    `pd.Series({"a": 1, "b": float("nan")})` (KHÔNG ép dtype) làm pandas tự đổi `1` (int) thành
    `1.0` (float), vì cột còn lại toàn số + NaN buộc cả Series lên chung 1 dtype số. Đây là hành
    vi suy kiểu của pandas khi build Series từ dict tay, KHÔNG phải hành vi của `_row_checksum`
    (khi gọi thật qua `add_metadata_columns` trên DataFrame nhiều cột dtype khác nhau — dtype mỗi
    CỘT được giữ nguyên, đã verify bằng script riêng). Ép `dtype="object"` ở đây kiểm đúng logic
    của `_row_checksum` (join + xử lý NaN + hash) tách biệt khỏi hiệu ứng phụ đó."""

    def test_same_content_produces_same_checksum_deterministic(self) -> None:
        row_a = pd.Series({"a": 1, "b": "hanoi"}, dtype="object")
        row_b = pd.Series({"a": 1, "b": "hanoi"}, dtype="object")
        assert ingestion._row_checksum(row_a) == ingestion._row_checksum(row_b)

    def test_different_content_produces_different_checksum(self) -> None:
        row_a = pd.Series({"a": 1, "b": "hanoi"}, dtype="object")
        row_b = pd.Series({"a": 1, "b": "hue"}, dtype="object")
        assert ingestion._row_checksum(row_a) != ingestion._row_checksum(row_b)

    def test_matches_manually_computed_sha256_of_pipe_joined_values(self) -> None:
        """Tính tay payload+sha256 ĐỘC LẬP với implementation (không gọi lại `_row_checksum` để
        so sánh — tránh bug tự che bug), đúng docstring hàm ("Hash toàn bộ giá trị... payload nối
        bằng '|')."""
        row = pd.Series({"a": 1, "b": "hanoi", "c": 2.5}, dtype="object")
        expected = hashlib.sha256(b"1|hanoi|2.5").hexdigest()
        assert ingestion._row_checksum(row) == expected

    def test_nan_value_becomes_empty_string_in_payload_not_literal_nan_text(self) -> None:
        row = pd.Series({"a": 1, "b": float("nan"), "c": "x"}, dtype="object")
        expected = hashlib.sha256(b"1||x").hexdigest()
        assert ingestion._row_checksum(row) == expected

    def test_output_is_64_char_lowercase_hex_sha256_digest(self) -> None:
        result = ingestion._row_checksum(pd.Series({"a": 1}, dtype="object"))
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_add_metadata_columns_checksum_matches_independent_row_checksum_call(self) -> None:
        """Integration wiring check: cột `_checksum` sinh bởi `add_metadata_columns` phải khớp
        gọi `_row_checksum` trực tiếp trên đúng business columns của df gốc — bắt lỗi wiring
        (vd lỡ hash nhầm cả cột metadata, lỡ đổi axis/thứ tự cột)."""
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        out = ingestion.add_metadata_columns(df, source_file="f.csv", batch_id="b1")
        expected = df.apply(ingestion._row_checksum, axis=1)
        pd.testing.assert_series_equal(
            out["_checksum"].reset_index(drop=True),
            expected.reset_index(drop=True),
            check_names=False,
        )

    def test_add_metadata_columns_checksum_independent_of_batch_id_and_source_file(self) -> None:
        """Đúng mục đích docstring ("phát hiện thay đổi khi MERGE lại"): checksum CHỈ phụ thuộc
        nội dung business columns, KHÔNG được lẫn `_batch_id`/`_source_file` — 2 lần gọi CÙNG nội
        dung business nhưng KHÁC batch_id/source_file phải ra CÙNG checksum."""
        df = pd.DataFrame({"a": [1, 2], "b": ["x", None]})
        out1 = ingestion.add_metadata_columns(df, source_file="f1.csv", batch_id="batch-1")
        out2 = ingestion.add_metadata_columns(df, source_file="f2.csv", batch_id="batch-2")
        pd.testing.assert_series_equal(
            out1["_checksum"].reset_index(drop=True),
            out2["_checksum"].reset_index(drop=True),
            check_names=False,
        )

    def test_add_metadata_columns_handles_nan_in_business_column_without_crashing(self) -> None:
        """NaN trong cột business thật (vd `order_items.promo_id` nullable) không được làm
        `_row_checksum` crash khi chạy qua đường gọi thật `add_metadata_columns`."""
        df = pd.DataFrame({"order_id": [1, 2], "promo_id": [None, "PROMO1"]})
        out = ingestion.add_metadata_columns(df, source_file="f.csv", batch_id="b1")
        assert out["_checksum"].notna().all()
        assert out["_checksum"].apply(lambda v: len(v) == 64).all()
        assert out["_checksum"].iloc[0] != out["_checksum"].iloc[1]  # NaN vs "PROMO1" phải khác


# ---------------------------------------------------------------------------
# 6. build_order_items_line_id — nhánh lỗi ValueError khi thiếu _source_row_number (G4)
# ---------------------------------------------------------------------------


class TestBuildOrderItemsLineId:
    """`build_order_items_line_id()` — G4: nhánh `raise ValueError` khi thiếu cột
    `_source_row_number` (gọi hàm KHÔNG qua `add_metadata_columns()` trước) chưa từng được test;
    lời gọi thật trong `ingest_table` luôn đi sau `add_metadata_columns` nên rủi ro thực tế thấp,
    nhưng vẫn là code path 0% coverage trước bản vá."""

    def test_missing_source_row_number_column_raises_value_error(self) -> None:
        df = pd.DataFrame({"order_id": [1, 2], "product_id": [10, 20]})
        assert "_source_row_number" not in df.columns  # tiền đề test đúng
        with pytest.raises(ValueError, match="_source_row_number"):
            ingestion.build_order_items_line_id(df)

    def test_succeeds_once_source_row_number_column_present(self) -> None:
        """Happy path đối chứng — cô lập đúng NGUYÊN NHÂN raise (thiếu cột đó), không phải do dữ
        liệu khác sai."""
        df = pd.DataFrame({
            "order_id": [1, 2], "product_id": [10, 20], "_source_row_number": [0, 1],
        })
        result = ingestion.build_order_items_line_id(df)
        assert len(result) == 2
        assert result.is_unique


# ---------------------------------------------------------------------------
# 7. merge_upsert — idempotent MERGE theo natural key
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
# 8. ingest_table — tích hợp, chạy trên data/sample THẬT + 1 CSV lỗi tự tạo
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
        """G5 (audit 2026-08-10): pin đúng status/rows_quarantined ĐO THẬT trên
        `data/sample/order_items.csv` (2193 dòng dữ liệu, xem lệnh verify trong report vá gap)
        thay vì chấp nhận lỏng `status in ("OK", "QUARANTINED")`."""
        valid, bad, result = ingestion.ingest_table("order_items")
        assert schema_mod.ORDER_ITEMS_SURROGATE_KEY in valid.columns
        assert valid[schema_mod.ORDER_ITEMS_SURROGATE_KEY].is_unique
        assert result.status == "OK"
        assert result.rows_quarantined == 0
        assert len(bad) == 0
        assert len(valid) == 2193

    @pytest.mark.parametrize("table", list(schema_mod.ALL_TABLES))
    def test_runs_clean_on_every_sample_table(self, table: str) -> None:
        """DoD kiểu M4a ("run_all 14 bảng") nhưng cho đúng `ingest_table` — trước đây chưa ai
        loop qua cả 14 bảng gọi hàm này, chỉ có `quality.run_all` loop DQ (khác hàm).

        G5 (audit 2026-08-10): trước bản vá assert lỏng `status in ("OK", "QUARANTINED")` — chấp
        nhận cả 2 trạng thái, không pin đúng kỳ vọng theo từng bảng. Đã tự chạy `ingest_table`
        thật cho ĐỦ 14 bảng `data/sample` trước khi viết assert cứng (không đoán, xem lệnh verify
        trong report vá gap): CẢ 14/14 bảng đều status=OK, rows_quarantined=0 — 0 dòng nào trong
        `data/sample` vi phạm dtype/enum schema contract. Pin đúng số đo được — nếu sample sau
        này đổi/hỏng khiến 1 bảng bất kỳ phát sinh quarantine, test sẽ đỏ NGAY thay vì im lặng
        chấp nhận qua nhánh `QUARANTINED`."""
        valid, bad, result = ingestion.ingest_table(table)
        assert result.status == "OK", (
            f"{table}: status={result.status} (kỳ vọng OK — data/sample đo thật 14/14 bảng sạch, "
            "0 quarantine; FAILED nghĩa là thiếu cột, QUARANTINED nghĩa là sample vừa phát sinh "
            "dòng lỗi mới, cả 2 đều là regression cần điều tra)"
        )
        assert result.rows_quarantined == 0
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
