# DWMS Pipa Baja — Uji Coba postgres_fdw

Panduan untuk mengetes Foreign Data Wrapper (FDW) yang menghubungkan database Plant 1 (Semarang), Plant 2 (Surabaya), dan Hub Pusat.

## Prasyarat

```powershell
docker-compose up -d
```

Semua container harus berstatus `Up`:

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## 1. Cek Data di Masing-Masing Plant

### Plant 1 (Semarang)

```powershell
docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "SELECT * FROM raw_material.lokasi_rm;"
docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "SELECT * FROM produksi.work_in_progress;"
docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "SELECT * FROM finish_good.lokasi_rak;"
```

### Plant 2 (Surabaya)

```powershell
docker exec pg-plant2 psql -U admin -d db_gudang_2 -c "SELECT * FROM raw_material.lokasi_rm;"
docker exec pg-plant2 psql -U admin -d db_gudang_2 -c "SELECT * FROM produksi.work_in_progress;"
docker exec pg-plant2 psql -U admin -d db_gudang_2 -c "SELECT * FROM finish_good.lokasi_rak;"
```

## 2. Cek FDW di Hub Pusat

```powershell
docker exec pg-hub psql -U admin -d db_hub_pusat -c "\dx"
```
Pastikan `postgres_fdw` terdaftar.

```powershell
docker exec pg-hub psql -U admin -d db_hub_pusat -c "\des+"
docker exec pg-hub psql -U admin -d db_hub_pusat -c "\det+"
```
Cek foreign server dan foreign table sudah ada.

## 3. Cek View Agregat

```powershell
docker exec pg-hub psql -U admin -d db_hub_pusat -c "SELECT * FROM v_global_raw_material;"
docker exec pg-hub psql -U admin -d db_hub_pusat -c "SELECT * FROM v_global_produksi_wip;"
docker exec pg-hub psql -U admin -d db_hub_pusat -c "SELECT * FROM v_global_finish_good;"
```

### Hasil yang Diharapkan

| View | Baris | Detail |
|------|-------|--------|
| `v_global_raw_material` | **6** | 3 Plant 1 + 3 Plant 2 |
| `v_global_produksi_wip` | **5** | 3 Plant 1 + 2 Plant 2 |
| `v_global_finish_good` | **5** | 3 Plant 1 + 2 Plant 2 |

## 4. Tes Propagasi Data

Tambah data baru di Plant 1, lalu cek apakah muncul otomatis di Hub:

```powershell
docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "INSERT INTO raw_material.lokasi_rm VALUES ('RM-P1-099', 'Test Coil', 10.0, 'SLOC-T1', 'Tersedia');"

docker exec pg-hub psql -U admin -d db_hub_pusat -c "SELECT * FROM v_global_raw_material WHERE kode_barcode_rm = 'RM-P1-099';"
```
Data harus langsung muncul (real-time, tanpa delay).

Bersihkan data uji:

```powershell
docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "DELETE FROM raw_material.lokasi_rm WHERE kode_barcode_rm = 'RM-P1-099';"
```

## 5. Tes Simulasi Gangguan

```powershell
docker stop pg-plant1
docker exec pg-hub psql -U admin -d db_hub_pusat -c "SELECT * FROM v_global_raw_material;"
```
Query akan gagal atau error saat menjangkau foreign table plant1 — bukti FDW mencoba koneksi ke remote.

```powershell
docker start pg-plant1
```

## 6. Tes Koneksi Eksternal via Nginx Gateway

```powershell
psql -h localhost -p 5430 -U admin -d db_hub_pusat -c "SELECT * FROM v_global_raw_material;"
psql -h localhost -p 5431 -U admin -d db_gudang_1 -c "SELECT * FROM raw_material.lokasi_rm;"
psql -h localhost -p 5432 -U admin -d db_gudang_2 -c "SELECT * FROM raw_material.lokasi_rm;"
```

## 7. Tes Dashboard

Buka `http://localhost:8501` di browser.

- Tab **Raw Material** — harus menampilkan 6 baris dari kedua plant
- Tab **Produksi / WIP** — harus 5 baris
- Tab **Finish Good** — harus 5 baris
- Klik tombol **Segarkan** — cache Redis dihapus, data di-reload dari hub

