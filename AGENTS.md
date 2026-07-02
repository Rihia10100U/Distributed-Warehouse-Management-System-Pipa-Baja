# DWMS Pipa Baja — Agent Guide

## Stack
- **Orchestration**: Docker Compose, 5 containers on `dwms_integrated_network`
- **Databases**: 3× PostgreSQL 15 (plant1, plant2, hub), linked via `postgres_fdw`
- **Cache**: Redis 7-alpine (`redis-cache`), accessed by dashboard for query result caching (TTL 60s)
- **Gateway**: Nginx alpine — Layer 4 TCP stream proxy (NOT HTTP) routing ports 5430-5432 → internal PG instances
- **Dashboard**: Streamlit 1.32 + pandas 2.2 + psycopg2-binary 2.9 + redis-py 5.2 on python:3.10-slim

## Architecture
```
External Ports → nginx-gateway (TCP stream) → PostgreSQL
  5430 → pg-hub:5432
  5431 → pg-plant1:5432
  5432 → pg-plant2:5432

Dashboard → pg-hub:5432 (direct internal Docker network, NOT via nginx)
```

## Startup order (derived from depends_on in docker-compose.yml)
```
pg-plant1 ─┐
            ├──→ pg-hub ──→ nginx-gateway (also waits for redis-cache)
pg-plant2 ─┘                → ppic-dashboard (waits for pg-hub only)
redis-cache (no deps, starts freely)
```
FDW init (`init-hub.sql`) may fail if plant DBs aren't ready yet. PostgreSQL retries the init script automatically on restart.

## Database schemas (each plant DB)

| Schema | Table | Purpose |
|--------|-------|---------|
| `raw_material` | `lokasi_rm` | Coil raw material inventory |
| `produksi` | `work_in_progress` | Pipes in production |
| `finish_good` | `lokasi_rak` | Finished pipes in rack storage |

Each `init-plant*.sql` creates all 3 schemas+tables with seed data. Hub FDW foreign tables reference these by `schema_name.table_name`.

## Hub views (queried by dashboard)

Dashboard queries exactly 3 views — all other views are unused:
- `v_global_raw_material` — columns: `pabrik, kode_barcode_rm, jenis_material, berat_ton, lokasi_rm_sloc, status`
- `v_global_produksi_wip` — columns: `pabrik, no_seri_barcode, jenis_pipa, status`
- `v_global_finish_good` — columns: `pabrik, no_seri_barcode, jenis_pipa, id_rak_sloc, status`

Each view UNIONs both plants with a hardcoded `'Gudang / Plant X'` AS pabrik.

## Init SQL constraints

Each PG container mounts its init SQL as a single file:
- `./sql/init-plant1.sql` → `/docker-entrypoint-initdb.d/init.sql` in `pg-plant1`
- `./sql/init-plant2.sql` → `/docker-entrypoint-initdb.d/init.sql` in `pg-plant2`
- `./sql/init-hub.sql` → `/docker-entrypoint-initdb.d/init.sql` in `pg-hub`

Only runs on first DB creation. To re-run: `docker-compose down -v && docker-compose up`.

## Streamlit dashboard pitfalls

- `st.bar_chart` **y-axis must be numeric**. GroupBy+count before charting. String columns crash at runtime.
- `st.bar_chart(color='#dd5500')` is valid (hex string override); `color='pabrik'` maps a column.
- Dashboard connects to `pg-hub:5432` (Docker internal), **not** to the nginx gateway.
- `get_connection()` is the only DB connection function — hardcoded `admin/secretpassword`.
- Redis caching (`redis-cache:6379`): each query result is cached with TTL 60s. Keys: `cache:raw_material`, `cache:produksi_wip`, `cache:finish_good`. `invalidate_cache()` clears all 3 on refresh.
- `get_redis()` silently returns `None` on failure — no crash if Redis is down, just falls back to direct DB queries.

## No tests, no CI, no lint/typecheck

This project has zero test files, zero CI workflows, zero lint/format/typecheck config. No commands exist beyond `docker-compose up`/`down`.
