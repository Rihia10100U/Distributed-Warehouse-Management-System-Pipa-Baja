-- Plant 1: Gudang 1 (Semarang)
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
('RM-P1-001', 'Hot Rolled Coil 3mm', 25.50, 'SLOC-A1', 'Tersedia'),
('RM-P1-002', 'Cold Rolled Coil 2mm', 18.20, 'SLOC-A2', 'Tersedia'),
('RM-P1-003', 'Galvalume Coil 0.8mm', 30.00, 'SLOC-A3', 'Tersedia');

CREATE SCHEMA IF NOT EXISTS produksi;
CREATE TABLE produksi.work_in_progress (
    no_seri_barcode VARCHAR(50) PRIMARY KEY,
    jenis_pipa VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Dalam Proses'
);

INSERT INTO produksi.work_in_progress VALUES
('WIP-P1-001', 'Pipa 4 inch SCH40', 'Dalam Proses'),
('WIP-P1-002', 'Pipa 6 inch SCH80', 'Dalam Proses'),
('WIP-P1-003', 'Pipa 3 inch SCH40', 'Dalam Proses');

CREATE SCHEMA IF NOT EXISTS finish_good;
CREATE TABLE finish_good.lokasi_rak (
    no_seri_barcode VARCHAR(50) PRIMARY KEY,
    jenis_pipa VARCHAR(100) NOT NULL,
    id_rak_sloc VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Siap Jual'
);

INSERT INTO finish_good.lokasi_rak VALUES
('FG-P1-001', 'Pipa 4 inch SCH40', 'RAK-B1', 'Siap Jual'),
('FG-P1-002', 'Pipa 6 inch SCH80', 'RAK-B2', 'Siap Jual'),
('FG-P1-003', 'Pipa 2 inch SCH40', 'RAK-B3', 'Siap Jual');
