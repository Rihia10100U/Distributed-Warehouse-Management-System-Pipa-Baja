# DWMS Pipa Baja — Agent Guide

## Stack
- **Orchestration**: Docker Compose, 5 containers on `dwms_integrated_network`
- **Databases**: 3× PostgreSQL 15 (plant1, plant2, hub), linked via `postgres_fdw`
- **Cache**: Redis 7-alpine (`redis-cache`), dashboard query caching TTL 60s
- **Gateway**: Nginx alpine — Layer 4 TCP stream proxy (NOT HTTP) routing ports 5430-5432 → internal PG
- **Dashboard**: Streamlit 1.32 + pandas 2.2 + psycopg2-binary 2.9 + redis-py 5.2 on python:3.10-slim

## Architecture
- External ports → nginx-gateway (TCP stream) → PostgreSQL: 5430 → pg-hub, 5431 → pg-plant1, 5432 → pg-plant2
- Dashboard connects directly to `pg-hub:5432` (Docker internal), NOT via nginx
- Dashboard `get_connection()` hardcodes `admin/secretpassword`

## Critical: `init-hub.sql` is empty (0 bytes)
`sql/init-hub.sql` contains **no FDW setup** — no `CREATE SERVER`, `CREATE USER MAPPING`, `CREATE FOREIGN TABLE`, or `CREATE VIEW`. The hub PG container will start with only the `db_hub_pusat` database and no FDW infrastructure. To make the system functional, either populate this file with the FDW DDL, or exec into pg-hub and run the setup manually. The existing mount at `/docker-entrypoint-initdb.d/init.sql` is correct but the file has no content.

## Startup order
```
pg-plant1 ─┐
            ├──→ pg-hub ──→ nginx-gateway (also waits for redis-cache)
pg-plant2 ─┘                → ppic-dashboard (waits for pg-hub only)
redis-cache (no deps)
```
Init SQL only runs on **first DB creation**. To re-run: `docker-compose down -v && docker-compose up -d`.

## Database schemas (per plant DB)
| Schema | Table | Purpose |
|--------|-------|---------|
| `raw_material` | `lokasi_rm` | Coil raw material inventory |
| `produksi` | `work_in_progress` | Pipes in production |
| `finish_good` | `lokasi_rak` | Finished pipes in rack storage |

Each `init-plant*.sql` creates all 3 schemas + tables + seed data. Plant 1 (Semarang): 3 rows each. Plant 2 (Surabaya): 3 RM + 2 WIP + 2 FG.

## Dashboard queries exactly 3 hub views (when FDW is set up)
- `v_global_raw_material` — columns: `pabrik, kode_barcode_rm, jenis_material, berat_ton, lokasi_rm_sloc, status`
- `v_global_produksi_wip` — columns: `pabrik, no_seri_barcode, jenis_pipa, status`
- `v_global_finish_good` — columns: `pabrik, no_seri_barcode, jenis_pipa, id_rak_sloc, status`
Each view would UNION both plants with `'Gudang / Plant X'` AS pabrik.

## Streamlit pitfalls
- `st.bar_chart` y-axis must be numeric. GroupBy+count before charting (see `app.py:89`, `app.py:108-109`). String columns crash at runtime.
- `st.bar_chart(color='#dd5500')` valid hex override; `color='pabrik'` maps a column.
- Redis cache keys: `cache:raw_material`, `cache:produksi_wip`, `cache:finish_good`. `invalidate_cache()` clears all 3 on refresh.
- `get_redis()` silently returns `None` on failure — no crash if Redis down, falls back to direct DB queries.

## No tests, no CI, no lint/typecheck
Zero test files, CI workflows, or lint/format config. Only command: `docker-compose up -d` / `docker-compose down`. Per-container log access via `docker logs <container>`.
