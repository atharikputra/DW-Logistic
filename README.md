# JNE Logistics Data Warehouse

Project tugas akhir Data Warehouse untuk simulasi performa pengiriman logistik. Aplikasi ini memisahkan workflow menjadi data generation, ETL operations, database warehouse PostgreSQL, dan delivery analytics untuk kebutuhan manajerial.

## Struktur Utama

- `dataset/baseline/`: dataset statis sebagai baseline/acuan demo dan validasi.
- `dataset/dynamic/raw/`: raw CSV dinamis hasil generate harian yang siap diproses ETL.
- `dataset/dynamic/processed/`: arsip raw dan clean CSV setelah ETL selesai.
- `generate_data.py`: membuat raw CSV dummy ke folder `dataset/dynamic/raw/`.
- `etl_process.py`: ETL core dari raw CSV ke PostgreSQL star schema.
- `pages/01_Data_Operations.py`: halaman Streamlit untuk generate raw data, run ETL, dan ringkasan audit.
- `pages/02_Analytics.py`: dashboard manajerial untuk SLA, cabang, rute, destinasi, customer, item, dan root cause delay.
- `pages/03_Data_Warehouse_Detail.py`: halaman eksplorasi star schema dan preview tabel warehouse.
- `pages/04_ETL_Audit_Log.py`: halaman timeline run ETL dan detail step pipeline.
- `utils/queries.py`: query analytics agar halaman visual tidak bercampur dengan SQL.
- `utils/ui.py`: helper custom CSS dan komponen visual reusable.
- `schema.sql`: definisi fact table, dimension table, dan ETL log.
- `docker-compose.yml`: menjalankan PostgreSQL dan Adminer.

## 1. Setup Project

Kalau baru clone:

```powershell
git clone "https://github.com/atharikputra/DW-Logistic"
cd "DW-Logistic"
```

Kalau sudah ada folder project:

```powershell
cd "C:\AIDAN\SEM 6\DATWEAR\DW-Logistic"
```

Buat dan aktifkan virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Kalau PowerShell menolak aktivasi:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2. Setup Environment

Copy file contoh environment:

```powershell
Copy-Item .env.example .env
```

Default koneksi aplikasi ke PostgreSQL:

```text
Host     : 127.0.0.1
Port     : 5433
Database : logitrack_dw
User     : admin
Password : admin123
```

## 3. Jalankan PostgreSQL Dan Adminer

```powershell
docker compose up -d
```

Cek container:

```powershell
docker ps
```

Harus muncul container:

- `LogiTrack_DW`: PostgreSQL database.
- `LogiTrack_Adminer`: web database viewer.

## 4. Jalankan Streamlit

```powershell
streamlit run app.py
```

Alur demo yang disarankan:

1. Buka halaman `Data Operations`.
2. Set jumlah data, rentang tanggal, seed opsional, dan opsi dirty data.
3. Klik `Generate Raw Data` untuk mensimulasikan batch data operasional harian baru.
4. Klik `Run ETL Pipeline`.
5. Buka halaman `Data Warehouse Detail` atau `ETL Audit Log` untuk memeriksa hasil load dan riwayat pipeline.
6. Buka halaman `Analytics`.
7. Gunakan filter day/week/month, tanggal, cabang, layanan, destinasi, customer type, dan kategori barang.

## 5. Cek Database Lewat Adminer

Buka browser:

```text
http://localhost:8080
```

Login Adminer:

```text
System   : PostgreSQL
Server   : db
Username : admin
Password : admin123
Database : logitrack_dw
```

Catatan: di Adminer, `Server` pakai `db` karena Adminer dan PostgreSQL berjalan di network Docker yang sama. Untuk aplikasi Python/Streamlit, host tetap `127.0.0.1` dari `.env` dan port host memakai `5433` agar tidak bentrok dengan PostgreSQL lokal.

Tabel utama yang bisa dicek:

- `fact_shipping`
- `dim_time`
- `dim_branch`
- `dim_service`
- `dim_destination`
- `dim_item`
- `dim_route`
- `dim_customer`
- `dim_status`
- `dim_reason`
- `etl_run_log`
- `etl_step_log`

Query cepat di Adminer:

```sql
SELECT COUNT(*) FROM fact_shipping;

SELECT *
FROM etl_run_log
ORDER BY run_id DESC;
```

## Catatan Workflow

Project ini membedakan dua jenis dataset:

- **Data dinamis**: berada di `dataset/dynamic/raw/`. File ini dibuat oleh generator untuk mensimulasikan data operasional harian yang bisa berubah dari waktu ke waktu. Format namanya `raw_nasional_logistics_data_YYYYMMDD_batch001.csv`, lalu batch berikutnya pada tanggal yang sama menjadi `batch002`, `batch003`, dan seterusnya.
- **Baseline statis**: berada di `dataset/baseline/`. File ini tidak berubah otomatis dan hanya dipakai sebagai acuan demo ulang atau pembanding bila butuh hasil yang konsisten.

File raw dinamis yang berhasil diproses ETL akan dipindahkan ke folder `dataset/dynamic/processed/`. Halaman `Data Operations` hanya menjalankan ETL jika ada raw CSV valid di folder `dataset/dynamic/raw/`, sehingga file lama yang sudah selesai tidak diproses dua kali.
