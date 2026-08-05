# infra/iceberg — Catalog config

Catalog production = **PostgreSQL JDBC catalog** (KHÔNG SQLite), expose qua 1 **REST catalog
server** (`tabulario/iceberg-rest:1.6.0`, service `iceberg-rest` trong `docker-compose.yml`).
Trino và Spark cùng nối vào REST catalog này → 1 nguồn sự thật duy nhất cho metadata/snapshot
(không mỗi engine tự giữ 1 catalog riêng).

```
Trino (iceberg.catalog.type=rest) ─┐
                                     ├─→ iceberg-rest (RESTCatalogServer, JdbcCatalog) ─→ Postgres (metadata: iceberg_tables, iceberg_namespace_properties)
Spark (catalog-impl=RESTCatalog) ──┘                                                  └─→ MinIO/S3 (data files, warehouse=s3a://<bucket>/warehouse)
pyiceberg (jobs/*.py, catalog type "rest") ─┘
```

## Property mapping (env → Iceberg catalog properties)

Image `tabulario/iceberg-rest` map env var `CATALOG_<KEY>` → catalog property (đã verify thật
bằng `docker image inspect` + chạy thử container thật, không đoán):

| Env var (compose) | Iceberg catalog property | Giá trị dự án |
|---|---|---|
| `CATALOG_CATALOG__IMPL` | `catalog-impl` | `org.apache.iceberg.jdbc.JdbcCatalog` |
| `CATALOG_URI` | `uri` | `jdbc:postgresql://postgres:5432/${POSTGRES_DB}` |
| `CATALOG_JDBC_USER` | `jdbc.user` | `${POSTGRES_USER}` |
| `CATALOG_JDBC_PASSWORD` | `jdbc.password` | `${POSTGRES_PASSWORD}` |
| `CATALOG_WAREHOUSE` | `warehouse` | `${ICEBERG_WAREHOUSE}` (vd `s3a://datathon/warehouse`) |
| `CATALOG_IO__IMPL` | `io-impl` | `org.apache.iceberg.aws.s3.S3FileIO` |
| `CATALOG_S3_ENDPOINT` | `s3.endpoint` | `http://minio:9000` |
| `CATALOG_S3_PATH__STYLE__ACCESS` | `s3.path-style-access` | `true` |

Quy tắc: `_` đơn → `.`, `__` đôi → `-`. Double-underscore = ký tự `-` literal trong tên property
(vd `CATALOG_IO__IMPL` → `io-impl`, KHÔNG phải `io.impl`).

Xác nhận đã test thật (không suy đoán): container start OK, log in ra đúng property map, tạo
namespace `raw` qua `POST /v1/namespaces` → Postgres có bảng `iceberg_tables` +
`iceberg_namespace_properties`. (Xem `.process_status/M2.md` phần verify.)

## Namespace

- `iceberg.raw.*` — bảng raw 14 nguồn + `_quarantine_<table>`.
- `iceberg.ops.*` — `ingest_audit` (M2), `dq_log` (M4a, chưa tạo ở milestone này).

## Retention / maintenance

Xem `jobs/compact_iceberg.py` (rewrite_data_files + rewrite_manifests, chạy qua Trino
`ALTER TABLE ... EXECUTE optimize`) và `jobs/expire_snapshots.py` (retention mặc định
`SNAPSHOT_RETENTION_DAYS=7`, override qua `.env`).
