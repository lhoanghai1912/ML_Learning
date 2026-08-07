# infra/cloudbeaver — Preset Trino connection

CloudBeaver Community (`dbeaver/cloudbeaver:26.1.4`) không có driver Trino built-in sẵn và định
dạng file auto-provisioning (`data-sources.json`/`product.conf` trong `workspace/GlobalConfiguration`)
phụ thuộc UUID sinh lúc chạy — mount tĩnh dễ bị ignore hoặc conflict giữa các lần `docker compose up`
khác nhau. Quyết định: KHÔNG mount provisioning JSON tự chế (rủi ro cao, khó verify offline);
document setup thủ công 1 lần (2 phút) ở đây, đơn giản, chắc ăn hơn.

## Setup lần đầu (sau `docker compose up -d`, cloudbeaver healthy)

1. Mở `http://localhost:${CLOUDBEAVER_PORT:-8978}` → wizard tạo admin account (chỉ hỏi 1 lần,
   lưu trong volume `cloudbeaver_data`).
2. New Connection → driver **Trino** (CloudBeaver có sẵn driver Trino trong danh sách driver
   community, tự tải khi chọn lần đầu — cần mạng lúc đó).
3. Connection settings:
   - Host: `trino` (nếu CloudBeaver và Trino cùng network compose) hoặc `localhost` (nếu chọn
     driver JDBC nối từ máy host ra port publish `8080`).
   - Port: `8080`
   - Catalog: `iceberg` (tuỳ chọn, có thể để trống rồi gõ `iceberg.raw.<table>` trong query).
   - Authentication: None (Trino dev, không bật auth trong compose này).
4. Test Connection → Finish.

## Query mẫu kiểm tra sau ingest

```sql
SHOW SCHEMAS FROM iceberg;
SELECT count(*) FROM iceberg.raw.sales;
SELECT * FROM iceberg.ops.ingest_audit ORDER BY finished_at DESC LIMIT 20;
```
