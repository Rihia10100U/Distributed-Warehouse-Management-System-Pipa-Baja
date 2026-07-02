# Entity Relationship & Use Case Diagram — DWMS Pipa Baja

```mermaid
erDiagram
    %% ========================
    %% PLANT 1 — Gudang Semarang
    %% ========================
    plant1_raw_material {
        VARCHAR_50 kode_barcode_rm PK
        VARCHAR_100 jenis_material
        DECIMAL_10_2 berat_ton
        VARCHAR_10 lokasi_rm_sloc
        VARCHAR_20 status
    }

    plant1_work_in_progress {
        VARCHAR_50 no_seri_barcode PK
        VARCHAR_100 jenis_pipa
        VARCHAR_20 status
    }

    plant1_finish_good {
        VARCHAR_50 no_seri_barcode PK
        VARCHAR_100 jenis_pipa
        VARCHAR_10 id_rak_sloc
        VARCHAR_20 status
    }

    %% ========================
    %% PLANT 2 — Gudang Surabaya
    %% ========================
    plant2_raw_material {
        VARCHAR_50 kode_barcode_rm PK
        VARCHAR_100 jenis_material
        DECIMAL_10_2 berat_ton
        VARCHAR_10 lokasi_rm_sloc
        VARCHAR_20 status
    }

    plant2_work_in_progress {
        VARCHAR_50 no_seri_barcode PK
        VARCHAR_100 jenis_pipa
        VARCHAR_20 status
    }

    plant2_finish_good {
        VARCHAR_50 no_seri_barcode PK
        VARCHAR_100 jenis_pipa
        VARCHAR_10 id_rak_sloc
        VARCHAR_20 status
    }

    %% ========================
    %% HUB — FDW Foreign Tables
    %% ========================
    hub_foreign_rm_gudang1 {
        VARCHAR_50 kode_barcode_rm
        VARCHAR_100 jenis_material
        DECIMAL_10_2 berat_ton
        VARCHAR_10 lokasi_rm_sloc
        VARCHAR_20 status
    }

    hub_foreign_rm_gudang2 {
        VARCHAR_50 kode_barcode_rm
        VARCHAR_100 jenis_material
        DECIMAL_10_2 berat_ton
        VARCHAR_10 lokasi_rm_sloc
        VARCHAR_20 status
    }

    hub_foreign_wip_gudang1 {
        VARCHAR_50 no_seri_barcode
        VARCHAR_100 jenis_pipa
        VARCHAR_20 status
    }

    hub_foreign_wip_gudang2 {
        VARCHAR_50 no_seri_barcode
        VARCHAR_100 jenis_pipa
        VARCHAR_20 status
    }

    hub_foreign_fg_gudang1 {
        VARCHAR_50 no_seri_barcode
        VARCHAR_100 jenis_pipa
        VARCHAR_10 id_rak_sloc
        VARCHAR_20 status
    }

    hub_foreign_fg_gudang2 {
        VARCHAR_50 no_seri_barcode
        VARCHAR_100 jenis_pipa
        VARCHAR_10 id_rak_sloc
        VARCHAR_20 status
    }

    %% ========================
    %% HUB — Views
    %% ========================
    hub_view_v_global_raw_material {
        VARCHAR pabrik
        VARCHAR_50 kode_barcode_rm
        VARCHAR_100 jenis_material
        DECIMAL_10_2 berat_ton
        VARCHAR_10 lokasi_rm_sloc
        VARCHAR_20 status
    }

    hub_view_v_global_produksi_wip {
        VARCHAR pabrik
        VARCHAR_50 no_seri_barcode
        VARCHAR_100 jenis_pipa
        VARCHAR_20 status
    }

    hub_view_v_global_finish_good {
        VARCHAR pabrik
        VARCHAR_50 no_seri_barcode
        VARCHAR_100 jenis_pipa
        VARCHAR_10 id_rak_sloc
        VARCHAR_20 status
    }

    %% ========================
    %% RELATIONSHIPS (LOGICAL FLOW)
    %% ========================
    plant1_raw_material ||--o{ plant1_work_in_progress : "bahan_baku_ke_produksi"
    plant1_work_in_progress ||--o{ plant1_finish_good : "produksi_ke_finish"

    plant2_raw_material ||--o{ plant2_work_in_progress : "bahan_baku_ke_produksi"
    plant2_work_in_progress ||--o{ plant2_finish_good : "produksi_ke_finish"

    %% FDW Mappings
    plant1_raw_material ||--|| hub_foreign_rm_gudang1 : "fdw_map"
    plant1_work_in_progress ||--|| hub_foreign_wip_gudang1 : "fdw_map"
    plant1_finish_good ||--|| hub_foreign_fg_gudang1 : "fdw_map"

    plant2_raw_material ||--|| hub_foreign_rm_gudang2 : "fdw_map"
    plant2_work_in_progress ||--|| hub_foreign_wip_gudang2 : "fdw_map"
    plant2_finish_good ||--|| hub_foreign_fg_gudang2 : "fdw_map"

    %% View Compositions
    hub_foreign_rm_gudang1 ||--|| hub_view_v_global_raw_material : "union_all"
    hub_foreign_rm_gudang2 ||--|| hub_view_v_global_raw_material : "union_all"

    hub_foreign_wip_gudang1 ||--|| hub_view_v_global_produksi_wip : "union_all"
    hub_foreign_wip_gudang2 ||--|| hub_view_v_global_produksi_wip : "union_all"

    hub_foreign_fg_gudang1 ||--|| hub_view_v_global_finish_good : "union_all"
    hub_foreign_fg_gudang2 ||--|| hub_view_v_global_finish_good : "union_all"
```

## Pipeline Flow

```mermaid
flowchart LR
    subgraph Plant1["🏭 Plant 1 — Semarang"]
        RM1["raw_material.lokasi_rm"] --> WIP1["produksi.work_in_progress"] --> FG1["finish_good.lokasi_rak"]
    end

    subgraph Plant2["🏭 Plant 2 — Surabaya"]
        RM2["raw_material.lokasi_rm"] --> WIP2["produksi.work_in_progress"] --> FG2["finish_good.lokasi_rak"]
    end

    subgraph Hub["🗄️ Hub Pusat (postgres_fdw)"]
        direction TB
        vRM["v_global_raw_material"]
        vWIP["v_global_produksi_wip"]
        vFG["v_global_finish_good"]
    end

    RM1 -->|FDW| vRM
    RM2 -->|FDW| vRM
    WIP1 -->|FDW| vWIP
    WIP2 -->|FDW| vWIP
    FG1 -->|FDW| vFG
    FG2 -->|FDW| vFG

    subgraph Dashboard["📊 Streamlit Dashboard"]
        D["Dashboard PPIC"]
    end

    vRM -->|SQL Query| D
    vWIP -->|SQL Query| D
    vFG -->|SQL Query| D
```

## Use Case Diagram

```mermaid
flowchart TB
    %% Actors
    PPIC["👤 PPIC Staff"]
    Op1["👤 Operator Gudang 1\n(Semarang)"]
    Op2["👤 Operator Gudang 2\n(Surabaya)"]
    Admin["👤 Admin Pusat"]
    System["⚙️ Sistem"]

    %% Use Cases
    UC1("(Melihat Stok\nBahan Baku)")
    UC2("(Melihat Produksi\nBerjalan / WIP)")
    UC3("(Melihat Barang\nJadi / Finish Good)")
    UC4("(Menyegarkan\nSeluruh Data)")
    UC5("(Mencatat Penerimaan\nBahan Baku)")
    UC6("(Mencatat Produksi\nPipa)")
    UC7("(Mencatat Barang\nJadi ke Rak)")
    UC8("(Mengakses Data\nTeragregasi Hub)")
    UC9("(Mengagregasi Data\nvia postgres_fdw)")
    UC10("(Menyimpan Cache\nHasil Query)")
    UC11("(Menampilkan Grafik\nSebaran Pipa)")

    %% Relationship: PPIC Staff
    PPIC --> UC1
    PPIC --> UC2
    PPIC --> UC3
    PPIC --> UC4
    UC2 -.->|extend| UC11

    %% Relationship: Operator Gudang
    Op1 --> UC5
    Op1 --> UC6
    Op1 --> UC7

    Op2 --> UC5
    Op2 --> UC6
    Op2 --> UC7

    %% Relationship: Admin Pusat
    Admin --> UC8

    %% Relationship: System
    System --> UC9
    System --> UC10
    UC9 -.->|include| UC8

    %% Boundary boxes
    subgraph Gudang["🏭 Gudang 1 & 2"]
        UC5
        UC6
        UC7
    end

    subgraph Dashboard["📊 Dashboard PPIC"]
        UC1
        UC2
        UC3
        UC4
        UC11
    end

    subgraph Hub["🗄️ Hub Pusat"]
        UC8
        UC9
    end

    subgraph Cache["⚡ Redis Cache"]
        UC10
    end
```

## Activity Diagrams

### 1. Alur Monitoring Dashboard oleh PPIC Staff

```mermaid
flowchart TB
    Start((Mulai)) --> Buka["Buka Dashboard\nStreamlit :8501"]
    Buka --> PilihTab{"Pilih Segmen"}
    PilihTab -->|Tab 1| RM["Akses Segmen\nRaw Material"]
    PilihTab -->|Tab 2| WIP["Akses Segmen\nProduksi / WIP"]
    PilihTab -->|Tab 3| FG["Akses Segmen\nFinish Good"]

    subgraph CacheCheck["Cek & Query Data"]
        direction TB
        CekCache{"Cache Redis\nada ?"}
        CekCache -->|Ya| AmbilCache["Ambil dari Redis\n(JSON → DataFrame)"]
        CekCache -->|Tidak| QueryHub["Query ke pg-hub\nvia psycopg2"]
        QueryHub --> SimpanCache["Simpan ke Redis\nTTL 60 detik"]
    end

    RM --> CekCache
    WIP --> CekCache
    FG --> CekCache
    AmbilCache --> Tampil["Tampilkan Dataframe\n& Grafik"]
    SimpanCache --> Tampil

    Tampil --> Refresh{"User klik\nSegarkan ?"}
    Refresh -->|Ya| Invalidate["Invalidate Cache\nhapus 3 key Redis"]
    Invalidate --> Reload["st.rerun()"]
    Reload --> PilihTab
    Refresh -->|Tidak| Selesai((Selesai))
```

### 2. Alur Pencatatan Data oleh Operator Gudang (via Scanner)

```mermaid
flowchart TB
    Start((Mulai)) --> Scan["Operator scan\nbarcode material/pipa"]
    Scan --> PilihGudang{"Scannerterkoneksi ke\nport nginx ?"}
    PilihGudang -->|Port 5431| Nginx1["nginx-gateway:5431\nTCP stream"]
    PilihGudang -->|Port 5432| Nginx2["nginx-gateway:5432\nTCP stream"]
    Nginx1 --> Route1["Proxy ke\npg-plant1:5432"]
    Nginx2 --> Route2["Proxy ke\npg-plant2:5432"]

    subgraph PlantDB["Write ke Database Plant"]
        direction TB
        Tentukan{"Tipe Data"}
        Tentukan -->|Bahan Baku| InsertRM["INSERT INTO\nraw_material.lokasi_rm"]
        Tentukan -->|Produksi| InsertWIP["INSERT INTO\nproduksi.work_in_progress"]
        Tentukan -->|Barang Jadi| InsertFG["INSERT INTO\nfinish_good.lokasi_rak"]
    end

    Route1 --> Tentukan
    Route2 --> Tentukan
    InsertRM --> Sukses["Data tersimpan\n✅"]
    InsertWIP --> Sukses
    InsertFG --> Sukses
    Sukses --> Notif["Dashboard akan membaca\nvia FDW di refresh\nberikutnya"]
    Notif --> Selesai((Selesai))
```

### 3. Alur Agregasi Data via postgres_fdw

```mermaid
flowchart TB
    Start((Mulai)) --> InitHub["pg-hub menjalankan\ninit-hub.sql"]
    InitHub --> CekPlant{"pg-plant1 & pg-plant2\nsudah siap ?"}
    CekPlant -->|Belum| Retry["PostgreSQL retry\notomatis saat restart"]
    Retry --> CekPlant
    CekPlant -->|Ya| Ext["CREATE EXTENSION\npostgres_fdw"]
    Ext --> Server["CREATE SERVER\nserver_gudang1 & 2"]
    Server --> Mapping["CREATE USER MAPPING\nadmin → admin"]
    Mapping --> Foreign["CREATE FOREIGN TABLE\n6 foreign tables\n(3 skema × 2 plant)"]
    Foreign --> View["CREATE OR REPLACE VIEW\n3 global views\n(UNION ALL)"]
    View --> Siap["Hub Pusat siap\nmelayani query"]
    Siap --> Dashboard["Dashboard query 3 views\nvia get_connection()"]
    Dashboard --> ReturnData["Return data\ntanpa mengetahui\nsumber plant"]
    ReturnData --> Selesai((Selesai))
```

### 4. Alur Siklus Produksi End-to-End

```mermaid
flowchart TB
    Start((Mulai)) --> BahanBaku["Bahan baku coil\nditerima gudang"]
    BahanBaku --> CatatRM["Operator catat ke\nraw_material.lokasi_rm"]
    CatatRM --> Proses["Material masuk\nlantai produksi"]
    Proses --> CatatWIP["Operator catat ke\nproduksi.work_in_progress"]
    CatatWIP --> Produksi["Pipa diproduksi\nsesuai jenis"]
    Produksi --> QC{"Quality Control\nlulus ?"}
    QC -->|Tidak| Rework["Rework /\nDibatalkan"]
    Rework --> Selesai1((Selesai))
    QC -->|Ya| Jadi["Pipa jadi siap\ndisimpan di rak"]
    Jadi --> CatatFG["Operator catat ke\nfinish_good.lokasi_rak"]
    CatatFG --> SiapJual["Status: Siap Jual\nsiap diangkut"]
    SiapJual --> Dashboard["Dashboard PPIC\nmenampilkan data\n3 segmen terintegrasi"]
    Dashboard --> Selesai2((Selesai))
```
