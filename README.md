# JNE Logistics Data Warehouse

An end-to-end logistics data warehouse project for simulating shipment operations, processing raw delivery transactions through an ETL pipeline, and presenting managerial analytics through an interactive Streamlit dashboard.

The application is designed for a Data Warehouse final project. It separates the workflow into synthetic data generation, ETL processing, PostgreSQL warehouse storage, audit logging, and executive delivery performance analytics.

## Key Features

- **Synthetic logistics data generation** for daily shipment batches, including configurable date ranges, row counts, random seeds, and optional dirty data injection.
- **ETL pipeline** that extracts raw CSV files, cleans and normalizes shipment records, loads PostgreSQL dimension and fact tables, and archives processed files.
- **PostgreSQL star schema** with `fact_shipping` and supporting dimensions for time, branch, service, destination, item, route, customer, status, and delay reason.
- **ETL audit trail** through run-level and step-level logs, including row counts, duration, status, source file, clean output, and error messages.
- **Interactive Streamlit dashboard** for monitoring SLA performance, revenue, branch performance, route bottlenecks, destination risk, customer segments, item categories, and root causes of delay.
- **Decision Support System (DSS)** with rule-based risk scoring, KPI alerts, executive insights, and prioritized operational areas.

## Tech Stack

- **Python**: Streamlit, pandas, NumPy, Faker
- **Visualization**: Plotly
- **Database**: PostgreSQL
- **ORM / Database Access**: SQLAlchemy, psycopg2
- **Containerization**: Docker Compose
- **Database Viewer**: Adminer

## Project Structure

```text
.
|-- app.py                          # Streamlit application entry point
|-- docker-compose.yml              # PostgreSQL and Adminer services
|-- requirements.txt                # Python dependencies
|-- schema.sql                      # Warehouse schema and ETL log tables
|-- dataset/
|   |-- baseline/                   # Static baseline dataset for repeatable demos
|   `-- dynamic/
|       |-- raw/                    # Generated raw CSV files waiting for ETL
|       `-- processed/              # Archived raw and clean files after ETL
|-- pages/
|   |-- 01_Data_Operations.py       # Data generation, ETL execution, and audit summary
|   |-- 02_Analytics.py             # Executive logistics analytics dashboard
|   |-- 03_Data_Warehouse_Detail.py # Star schema exploration and table previews
|   `-- 04_ETL_Audit_Log.py         # ETL run and step history
|-- ruleset/
|   |-- generate_data.py            # Synthetic logistics data generator
|   |-- etl_process.py              # ETL pipeline implementation
|   `-- dss.py                      # DSS scoring, KPI alerting, and insights
`-- utils/
    |-- dataset_naming.py           # Batch file naming helpers
    |-- queries.py                  # Reusable analytics SQL queries
    `-- ui.py                       # Shared Streamlit UI components and styling
```

## Data Warehouse Schema

The warehouse uses a star schema centered on `fact_shipping`.

| Table | Purpose |
| --- | --- |
| `fact_shipping` | Shipment transaction facts, including tracking number, duration, cost, and late status. |
| `dim_time` | Date, day, month, quarter, year, and weekend attributes. |
| `dim_branch` | Origin branch details. |
| `dim_service` | Service type, service name, and SLA days. |
| `dim_destination` | Receiver destination details. |
| `dim_item` | Item category, weight, and fragile status. |
| `dim_route` | Origin, transit point, and destination route code. |
| `dim_customer` | Customer name, type, and phone number. |
| `dim_status` | Shipment status values. |
| `dim_reason` | Delay reason category and description. |
| `etl_run_log` | ETL run metadata and final status. |
| `etl_step_log` | Step-by-step ETL execution history. |


## Dataset Workflow

The project separates static and dynamic data sources:

- `dataset/baseline/` contains a static CSV dataset for repeatable demos and validation.
- `dataset/dynamic/raw/` stores newly generated raw CSV batches waiting for ETL.
- `dataset/dynamic/processed/` stores processed raw files and exported clean CSV files after a successful ETL run.

Generated raw files follow this naming pattern:

```text
raw_nasional_logistics_data_YYYYMMDD_batch001.csv
```

After a successful ETL run, the raw file is moved into `dataset/dynamic/processed/` with a `done_` prefix. This prevents the same batch from being processed twice.

## Notes

- The ETL pipeline performs a full warehouse refresh by default.
- The Streamlit UI only enables ETL execution when a valid raw CSV exists in `dataset/dynamic/raw/`.
- The database schema is reset-safe for development because `schema.sql` rebuilds the warehouse tables before loading data.
- The dashboard depends on successful warehouse loading. If analytics pages are empty, generate a batch and run the ETL pipeline first.
