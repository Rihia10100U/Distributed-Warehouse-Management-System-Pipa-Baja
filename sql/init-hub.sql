-- Hub Pusat — FDW Setup for Plant 1 (Semarang) & Plant 2 (Surabaya)
CREATE EXTENSION IF NOT EXISTS postgres_fdw;

-- Foreign Servers
CREATE SERVER fdw_plant1
    FOREIGN DATA WRAPPER postgres_fdw
    OPTIONS (host 'pg-plant1', port '5432', dbname 'db_gudang_1');

CREATE SERVER fdw_plant2
    FOREIGN DATA WRAPPER postgres_fdw
    OPTIONS (host 'pg-plant2', port '5432', dbname 'db_gudang_2');

-- User Mappings
CREATE USER MAPPING FOR admin
    SERVER fdw_plant1
    OPTIONS (user 'admin', password 'secretpassword');

CREATE USER MAPPING FOR admin
    SERVER fdw_plant2
    OPTIONS (user 'admin', password 'secretpassword');

-- Local schemas for each plant's foreign tables
CREATE SCHEMA IF NOT EXISTS plant1;
CREATE SCHEMA IF NOT EXISTS plant2;

-- Import all tables from Plant 1
IMPORT FOREIGN SCHEMA raw_material FROM SERVER fdw_plant1 INTO plant1;
IMPORT FOREIGN SCHEMA produksi    FROM SERVER fdw_plant1 INTO plant1;
IMPORT FOREIGN SCHEMA finish_good FROM SERVER fdw_plant1 INTO plant1;

-- Import all tables from Plant 2
IMPORT FOREIGN SCHEMA raw_material FROM SERVER fdw_plant2 INTO plant2;
IMPORT FOREIGN SCHEMA produksi    FROM SERVER fdw_plant2 INTO plant2;
IMPORT FOREIGN SCHEMA finish_good FROM SERVER fdw_plant2 INTO plant2;

-- Global views (used by dashboard)
CREATE VIEW v_global_raw_material AS
SELECT 'Gudang / Plant 1' AS pabrik, kode_barcode_rm, jenis_material, berat_ton, lokasi_rm_sloc, status
FROM plant1.lokasi_rm
UNION ALL
SELECT 'Gudang / Plant 2' AS pabrik, kode_barcode_rm, jenis_material, berat_ton, lokasi_rm_sloc, status
FROM plant2.lokasi_rm;

CREATE VIEW v_global_produksi_wip AS
SELECT 'Gudang / Plant 1' AS pabrik, no_seri_barcode, jenis_pipa, status
FROM plant1.work_in_progress
UNION ALL
SELECT 'Gudang / Plant 2' AS pabrik, no_seri_barcode, jenis_pipa, status
FROM plant2.work_in_progress;

CREATE VIEW v_global_finish_good AS
SELECT 'Gudang / Plant 1' AS pabrik, no_seri_barcode, jenis_pipa, id_rak_sloc, status
FROM plant1.lokasi_rak
UNION ALL
SELECT 'Gudang / Plant 2' AS pabrik, no_seri_barcode, jenis_pipa, id_rak_sloc, status
FROM plant2.lokasi_rak;
