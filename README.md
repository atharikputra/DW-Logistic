# JNE Logistics Data Warehouse

Project tugas akhir Data Warehouse untuk simulasi performa pengiriman logistik. Aplikasi ini memisahkan workflow menjadi data generation, ETL operations, database warehouse PostgreSQL, dan delivery analytics untuk kebutuhan manajerial.

## Struktur Utama

- `generate_data.py`: membuat raw CSV dummy ke folder `raw/`.
- `etl_process.py`: ETL core dari raw CSV ke PostgreSQL star schema.
- `pages/etl_operations.py`: halaman Streamlit untuk generate raw data, run ETL, dan audit log.
- `pages/delivery_analytics.py`: dashboard manajerial untuk SLA, cabang, rute, destinasi, customer, item, dan root cause delay.
- `utils/queries.py`: query analytics agar halaman visual tidak bercampur dengan SQL.
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
Port     : 5432
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

1. Buka halaman `ETL Operations`.
2. Set jumlah data, rentang tanggal, seed opsional, dan opsi dirty data.
3. Klik `Generate Raw Data`.
4. Klik `Run ETL Pipeline`.
5. Buka halaman `Delivery Analytics`.
6. Gunakan filter day/week/month, tanggal, cabang, layanan, destinasi, customer type, dan kategori barang.

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

Catatan: di Adminer, `Server` pakai `db` karena Adminer dan PostgreSQL berjalan di network Docker yang sama. Untuk aplikasi Python/Streamlit, host tetap `127.0.0.1` dari `.env`.

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

File raw yang berhasil diproses ETL akan dipindahkan ke folder `processed/`. Halaman `ETL Operations` hanya menjalankan ETL jika ada raw CSV valid di folder `raw/`, sehingga file lama yang sudah selesai tidak diproses dua kali.
