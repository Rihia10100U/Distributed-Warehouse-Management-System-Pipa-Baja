-- Plant 2: Gudang 2 (Surabaya)
-- Skema: Raw Material, Produksi WIP, Finish Good

CREATE SCHEMA IF NOT EXISTS raw_material;
CREATE TABLE raw_material.lokasi_rm (
    kode_barcode_rm VARCHAR(50) PRIMARY KEY,
    jenis_material VARCHAR(100) NOT NULL,
    berat_ton DECIMAL(10,2) NOT NULL,
    lokasi_rm_sloc VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Tersedia'
);

INSERT INTO raw_material.lokasi_rm VALUES
('RM-P2-001', 'Hot Rolled Coil 4mm', 22.00, 'SLOC-C1', 'Tersedia'),
('RM-P2-002', 'Cold Rolled Coil 1.5mm', 15.75, 'SLOC-C2', 'Tersedia'),
('RM-P2-003', 'Stainless Coil 2mm', 12.50, 'SLOC-C3', 'Tersedia');

CREATE SCHEMA IF NOT EXISTS produksi;
CREATE TABLE produksi.work_in_progress (
    no_seri_barcode VARCHAR(50) PRIMARY KEY,
    jenis_pipa VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Dalam Proses'
);

INSERT INTO produksi.work_in_progress VALUES
('WIP-P2-001', 'Pipa 8 inch SCH40', 'Dalam Proses'),
('WIP-P2-002', 'Pipa 4 inch SCH80', 'Dalam Proses');

CREATE SCHEMA IF NOT EXISTS finish_good;
CREATE TABLE finish_good.lokasi_rak (
    no_seri_barcode VARCHAR(50) PRIMARY KEY,
    jenis_pipa VARCHAR(100) NOT NULL,
    id_rak_sloc VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Siap Jual'
);

INSERT INTO finish_good.lokasi_rak VALUES
('FG-P2-001', 'Pipa 8 inch SCH40', 'RAK-D1', 'Siap Jual'),
('FG-P2-002', 'Pipa 4 inch SCH80', 'RAK-D2', 'Siap Jual');
