#!/bin/sh
# infra/minio/init.sh — init bucket + policy cho lakehouse (chạy 1 lần bởi service `mc` trong compose).
# Idempotent: mc mb --ignore-existing, mc anonymous set không lỗi nếu chạy lại.
set -eu

: "${MINIO_ROOT_USER:?MINIO_ROOT_USER not set}"
: "${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD not set}"
: "${S3_BUCKET:?S3_BUCKET not set}"

mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

# Bucket chứa warehouse Iceberg (raw + ops namespace data files).
mc mb --ignore-existing "local/${S3_BUCKET}"

# Private bucket (không public) — lakehouse nội bộ, không expose anonymous read/write.
mc anonymous set none "local/${S3_BUCKET}" || true

# Versioning tắt (Iceberg tự quản lý snapshot/versioning ở tầng metadata, không cần S3 versioning
# cho warehouse — bật thêm sẽ tốn storage vô ích với schema hiện tại).
echo "MinIO init done: bucket=${S3_BUCKET}"
