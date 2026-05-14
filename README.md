# JNE Logistics Data Warehouse - ETL Otomatis

Folder ini berisi versi revisi yang sudah dibuat lebih dinamis dan nyambung antar-file:

- `generate_db.py` membuat CSV raw dengan nama timestamp dinamis di `data/raw/`.
- `etl_process.py` membaca CSV terbaru/terpilih, membersihkan data, membuat schema PostgreSQL, mengisi 9 dimensi + 1 fact table, dan mencatat proses ETL ke tabel log.
- `app.py` menjalankan generate + ETL langsung dari dashboard Streamlit dan menampilkan hasil proses ETL.
- `schema.sql` berisi star schema PostgreSQL yang bisa dilihat di DBeaver.

## 1. Install package

```bash
pip install -r requirements.txt
```

## 2. Siapkan PostgreSQL

Buat database bernama `logitrack_dw`. Default koneksi yang dipakai kode:

```text
Host     : localhost
Port     : 5432
Database : logitrack_dw
User     : admin
Password : admin123
Schema   : public
```

Jika user/password berbeda, ubah `PostgreSQL DB URL` di sidebar dashboard atau set environment variable:

```bash
set LOGITRACK_DB_URL=postgresql://user:password@localhost:5432/logitrack_dw
```

## 3. Jalankan dashboard

```bash
streamlit run app.py
```

Lalu klik tombol **Generate + ETL** di sidebar.

## 4. Lihat di DBeaver

Refresh database `logitrack_dw` → schema `public`. Tabel yang akan muncul:

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

## Catatan penting

Mode default ETL adalah **full refresh**, jadi setiap run akan mengosongkan ulang tabel fact dan dimension agar data tidak dobel. Riwayat proses ETL tetap disimpan di `etl_run_log` dan `etl_step_log`.


## Fix error `column "time_id" referenced in foreign key constraint does not exist`

Error ini biasanya terjadi karena database PostgreSQL/DBeaver masih menyimpan tabel lama atau tabel `fact_shipping` sempat dibuat tidak lengkap. Versi `schema.sql` terbaru sudah bersifat reset-safe: semua tabel DW lama akan di-drop lalu dibuat ulang dengan kolom FK lengkap (`time_id`, `branch_id`, `service_id`, dan seterusnya).

Jika error masih muncul, jalankan manual di DBeaver sebelum menjalankan Streamlit:

```sql
DROP TABLE IF EXISTS etl_step_log CASCADE;
DROP TABLE IF EXISTS etl_run_log CASCADE;
DROP TABLE IF EXISTS fact_shipping CASCADE;
DROP TABLE IF EXISTS dim_time CASCADE;
DROP TABLE IF EXISTS dim_service CASCADE;
DROP TABLE IF EXISTS dim_destination CASCADE;
DROP TABLE IF EXISTS dim_status CASCADE;
DROP TABLE IF EXISTS dim_reason CASCADE;
DROP TABLE IF EXISTS dim_branch CASCADE;
DROP TABLE IF EXISTS dim_item CASCADE;
DROP TABLE IF EXISTS dim_route CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
```

Setelah itu klik ulang tombol **Generate + ETL** di dashboard.
