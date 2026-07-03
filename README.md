# DWMS Pipa Baja — Uji Coba Sistem Database Terdistribusi

Panduan uji coba konsep distributed database pada sistem yang menghubungkan Plant 1 (Semarang), Plant 2 (Surabaya), dan Hub Pusat menggunakan PostgreSQL FDW.

## Prasyarat

```powershell
docker compose up -d
```

Semua container harus berstatus `Up`:

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}"
```

---

## A. Fragmentasi Horizontal (Horizontal Fragmentation)

**Teori:** Tabel global dipecah secara horizontal — baris tertentu disimpan di plant tertentu berdasarkan lokasi.

Uji: Setiap plant hanya punya data wilayahnya sendiri.

```powershell
docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "SELECT * FROM raw_material.lokasi_rm;"
docker exec pg-plant2 psql -U admin -d db_gudang_2 -c "SELECT * FROM raw_material.lokasi_rm;"
```

| Plant | Baris | Prefix ID |
|-------|-------|-----------|
| Plant 1 (Semarang) | 3 | `RM-P1-*` |
| Plant 2 (Surabaya) | 3 | `RM-P2-*` |

Tidak ada tumpang tindih — setiap baris hanya berada di satu plant (disjoint fragmentation).

---

## B. Otonomi Lokal (Local Autonomy)

**Teori:** Setiap node DB dapat beroperasi secara independen tanpa ketergantungan ke node lain.

### B.1 Plant beroperasi sendiri

Plant 1 dapat melakukan CRUD tanpa perlu plant lain atau hub:

```powershell
docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "INSERT INTO raw_material.lokasi_rm VALUES ('RM-P1-099', 'Test Otonomi', 10.0, 'SLOC-T1', 'Tersedia');"
docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "SELECT * FROM raw_material.lokasi_rm WHERE kode_barcode_rm = 'RM-P1-099';"
docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "DELETE FROM raw_material.lokasi_rm WHERE kode_barcode_rm = 'RM-P1-099';"
```

### B.2 Plant tidak bisa saling akses

Plant 1 **tidak bisa** melihat data Plant 2 (tidak ada FDW dari plant ke plant):

```powershell
docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "SELECT * FROM plant2.lokasi_rm;"
docker exec pg-plant2 psql -U admin -d db_gudang_2 -c "SELECT * FROM plant1.lokasi_rm;"
```

Keduanya akan error — `schema "plant2"` / `schema "plant1"` tidak ada.

### B.3 Masing-masing plant punya data berbeda

Jumlah baris antar plant tidak harus sama:

```powershell
docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "SELECT count(*) AS total_rm FROM raw_material.lokasi_rm;"
docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "SELECT count(*) AS total_wip FROM produksi.work_in_progress;"
docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "SELECT count(*) AS total_fg FROM finish_good.lokasi_rak;"

docker exec pg-plant2 psql -U admin -d db_gudang_2 -c "SELECT count(*) AS total_rm FROM raw_material.lokasi_rm;"
docker exec pg-plant2 psql -U admin -d db_gudang_2 -c "SELECT count(*) AS total_wip FROM produksi.work_in_progress;"
docker exec pg-plant2 psql -U admin -d db_gudang_2 -c "SELECT count(*) AS total_fg FROM finish_good.lokasi_rak;"
```

| Tabel | Plant 1 | Plant 2 |
|-------|---------|---------|
| raw_material.lokasi_rm | 3 | 3 |
| produksi.work_in_progress | 3 | 2 |
| finish_good.lokasi_rak | 3 | 2 |

---

## C. Foreign Data Wrapper (FDW)

**Teori:** FDW adalah jembatan yang memungkinkan hub membaca data dari plant tanpa menyalin data.

### C.1 Cek komponen FDW

```powershell
docker exec pg-hub psql -U admin -d db_hub_pusat -c "\dx"
```
Pastikan `postgres_fdw` terdaftar.

```powershell
docker exec pg-hub psql -U admin -d db_hub_pusat -c "\des+"
docker exec pg-hub psql -U admin -d db_hub_pusat -c "\det+ *.*"
docker exec pg-hub psql -U admin -d db_hub_pusat -c "\dn+"
```

| Komponen | Jumlah | Detail |
|----------|--------|--------|
| Foreign Server | 2 | `fdw_plant1` → `pg-plant1:5432/db_gudang_1`, `fdw_plant2` → `pg-plant2:5432/db_gudang_2` |
| Foreign Table | 6 | 3 tabel per plant (lokasi_rm, work_in_progress, lokasi_rak) di schema `plant1`/`plant2` |
| User Mapping | 2 | `admin` → kedua server |

### C.2 FDW bersifat read-only dari hub

Coba tulis data via foreign table dari hub:

```powershell
docker exec pg-hub psql -U admin -d db_hub_pusat -c "INSERT INTO plant1.lokasi_rm VALUES ('RM-P1-XXX', 'Hack', 1.0, 'SLOC-X', 'Tersedia');"
```

Akan error — `cannot insert into foreign table` karena tanpa `INSERT` privilege di mapping.

---

## D. Transparansi Fragmentasi (Fragmentation Transparency)

**Teori:** Pengguna melihat data sebagai satu tabel utuh, tidak sadar data tersebar.

### D.1 View menggabungkan fragment

```powershell
docker exec pg-hub psql -U admin -d db_hub_pusat -c "SELECT * FROM v_global_raw_material;"
docker exec pg-hub psql -U admin -d db_hub_pusat -c "SELECT * FROM v_global_produksi_wip;"
docker exec pg-hub psql -U admin -d db_hub_pusat -c "SELECT * FROM v_global_finish_good;"
```

| View | Baris | Detail |
|------|-------|--------|
| `v_global_raw_material` | **6** | 3 Plant 1 + 3 Plant 2 |
| `v_global_produksi_wip` | **5** | 3 Plant 1 + 2 Plant 2 |
| `v_global_finish_good` | **5** | 3 Plant 1 + 2 Plant 2 |

Kolom `pabrik` memberi tahu asal data, tapi struktur tabel seragam — pengguna bisa `WHERE` atau `GROUP BY` tanpa peduli fragmentasi.

### D.2 Query agregasi lintas plant

```powershell
docker exec pg-hub psql -U admin -d db_hub_pusat -c "SELECT pabrik, COUNT(*) AS total FROM v_global_raw_material GROUP BY pabrik;"
docker exec pg-hub psql -U admin -d db_hub_pusat -c "SELECT pabrik, SUM(berat_ton) AS total_berat FROM v_global_raw_material GROUP BY pabrik;"
```

---

## E. Propagasi Data Real-Time (FDW vs Replikasi)

**Teori:** FDW membaca langsung dari sumber (real-time), berbeda dengan replikasi yang butuh sinkronisasi.

```powershell
docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "INSERT INTO raw_material.lokasi_rm VALUES ('RM-P1-099', 'Real-Time Test', 10.0, 'SLOC-T1', 'Tersedia');"

docker exec pg-hub psql -U admin -d db_hub_pusat -c "SELECT * FROM v_global_raw_material WHERE kode_barcode_rm = 'RM-P1-099';"
```

Data langsung muncul tanpa delay — **berbeda dengan replikasi** yang punya lag.

```powershell
docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "DELETE FROM raw_material.lokasi_rm WHERE kode_barcode_rm = 'RM-P1-099';"
```

---

## F. Ketahanan (Resilience / Fault Tolerance)

**Teori:** Kegagalan satu node tidak menghentikan seluruh sistem.

### F.1 Plant mati, plant lain tetap jalan

```powershell
docker stop pg-plant1

docker exec pg-plant2 psql -U admin -d db_gudang_2 -c "SELECT * FROM raw_material.lokasi_rm;"
```

Plant 2 tetap normal — tidak terpengaruh Plant 1 mati.

### F.2 Plant mati, hub tetap bisa akses plant lain

```powershell
docker exec pg-hub psql -U admin -d db_hub_pusat -c "SELECT * FROM v_global_raw_material;"
```

Query berhasil — data Plant 2 tetap tampil. Data Plant 1 gagal di-fetch (error partial).

### F.3 Hub mati, plant tetap jalan

```powershell
docker stop pg-hub

docker exec pg-plant1 psql -U admin -d db_gudang_1 -c "SELECT * FROM raw_material.lokasi_rm;"
docker exec pg-plant2 psql -U admin -d db_gudang_2 -c "INSERT INTO raw_material.lokasi_rm VALUES ('RM-P2-099', 'Hub Down Test', 5.0, 'SLOC-T2', 'Tersedia');"
```

Kedua plant tetap berfungsi penuh — hub hanya konsumen data.

```powershell
docker start pg-hub
docker start pg-plant1

docker exec pg-plant2 psql -U admin -d db_gudang_2 -c "DELETE FROM raw_material.lokasi_rm WHERE kode_barcode_rm = 'RM-P2-099';"
```

---

## G. Redis Caching

**Teori:** Cache mereduksi beban query ke DB dengan menyimpan hasil query untuk sementara.

### G.1 Akses dashboard

Buka `http://localhost:8501` di browser.
- Tab **Raw Material** — menampilkan 6 baris dari kedua plant
- Tab **Produksi / WIP** — 5 baris
- Tab **Finish Good** — 5 baris

### G.2 Cek key cache di Redis

```powershell
docker exec redis-cache redis-cli KEYS "cache:*"
docker exec redis-cache redis-cli GET "cache:raw_material"
```

### G.3 Cache fallback jika Redis mati

```powershell
docker stop redis-cache
```

Buka dashboard — tetap berfungsi (langsung query ke hub, tanpa cache).  
Tidak crash karena kode dashboard handle `get_redis()` return `None`.

```powershell
docker start redis-cache
```

### G.4 Invalidasi cache

Klik tombol **Segarkan** di dashboard — semua key `cache:*` dihapus, data di-reload.

---

## H. Koneksi Eksternal via Nginx Gateway

**Teori:** Nginx sebagai TCP stream proxy — layer 4, bukan HTTP.

```powershell
psql -h localhost -p 5430 -U admin -d db_hub_pusat -c "SELECT * FROM v_global_raw_material;"
psql -h localhost -p 5431 -U admin -d db_gudang_1 -c "SELECT * FROM raw_material.lokasi_rm;"
psql -h localhost -p 5432 -U admin -d db_gudang_2 -c "SELECT * FROM raw_material.lokasi_rm;"
```

| Port Eksternal | Tujuan Internal |
|----------------|----------------|
| 5430 | pg-hub:5432 |
| 5431 | pg-plant1:5432 |
| 5432 | pg-plant2:5432 |

---

## I. Ringkasan Konsep

| Konsep | Implementasi di Sistem Ini |
|--------|---------------------------|
| **Fragmentasi Horizontal** | Data dibagi per plant — prefix ID `P1`/`P2` |
| **Otonomi Lokal** | Setiap plant independen, tidak bisa lihat plant lain |
| **FDW (Federated DB)** | Hub membaca data dari plant via foreign table |
| **Transparansi Fragmentasi** | View `v_global_*` menyembunyikan distribusi data |
| **Bukan Replikasi** | Tidak ada duplikasi data, FDW baca langsung (real-time) |
| **Fault Tolerance** | Satu plant mati tidak menghentikan plant lain |
| **Caching** | Redis mereduksi beban query (TTL 60 detik, fallback aman) |
| **Gateway** | Nginx TCP stream memetakan port eksternal ke internal |

## Referensi

- ERD & diagram alur: [`ERD.md`](ERD.md)
- Konfigurasi agent & arsitektur: [`AGENTS.md`](AGENTS.md)
