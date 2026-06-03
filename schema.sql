-- ================================================================
-- JNE Logistics Data Warehouse - PostgreSQL Star Schema
-- Versi reset-safe untuk development/tugas.
--
-- Kenapa ada DROP TABLE?
-- Agar error akibat schema lama/partial seperti:
-- "column time_id referenced in foreign key constraint does not exist"
-- hilang, karena seluruh tabel lama dibangun ulang dari nol.
-- ================================================================

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

CREATE TABLE dim_time (
    time_id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    day INT NOT NULL,
    month INT NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    day_name VARCHAR(20),
    month_name VARCHAR(20),
    is_weekend BOOLEAN DEFAULT FALSE
);

CREATE TABLE dim_service (
    service_id BIGSERIAL PRIMARY KEY,
    service_type VARCHAR(50) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    sla_days INT NOT NULL,
    CONSTRAINT uq_dim_service UNIQUE (service_type, service_name, sla_days)
);

CREATE TABLE dim_destination (
    destination_id BIGSERIAL PRIMARY KEY,
    receiver_address TEXT NOT NULL,
    district VARCHAR(100),
    city VARCHAR(100),
    province VARCHAR(100),
    zip_code VARCHAR(20),
    CONSTRAINT uq_dim_destination UNIQUE (receiver_address, district, city, province, zip_code)
);

CREATE TABLE dim_status (
    status_id BIGSERIAL PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE dim_reason (
    reason_id BIGSERIAL PRIMARY KEY,
    reason_category VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE dim_branch (
    branch_id BIGSERIAL PRIMARY KEY,
    branch_code VARCHAR(20) NOT NULL UNIQUE,
    branch_name VARCHAR(100) NOT NULL,
    city VARCHAR(100),
    region_province VARCHAR(100)
);

CREATE TABLE dim_item (
    item_id BIGSERIAL PRIMARY KEY,
    item_name VARCHAR(200) NOT NULL,
    item_category VARCHAR(100),
    weight_kg NUMERIC(10, 2),
    fragile_status BOOLEAN,
    CONSTRAINT uq_dim_item UNIQUE (item_name, item_category, weight_kg, fragile_status)
);

CREATE TABLE dim_route (
    route_id BIGSERIAL PRIMARY KEY,
    origin_city VARCHAR(100) NOT NULL,
    transit_point VARCHAR(100) NOT NULL,
    destination_city_code VARCHAR(20) NOT NULL,
    CONSTRAINT uq_dim_route UNIQUE (origin_city, transit_point, destination_city_code)
);

CREATE TABLE dim_customer (
    customer_id BIGSERIAL PRIMARY KEY,
    customer_name VARCHAR(200) NOT NULL,
    customer_type VARCHAR(50),
    phone_number VARCHAR(50),
    CONSTRAINT uq_dim_customer UNIQUE (customer_name, customer_type, phone_number)
);

CREATE TABLE fact_shipping (
    shipping_fact_id BIGSERIAL PRIMARY KEY,
    time_id BIGINT NOT NULL,
    branch_id BIGINT NOT NULL,
    service_id BIGINT NOT NULL,
    destination_id BIGINT NOT NULL,
    item_id BIGINT NOT NULL,
    route_id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    status_id BIGINT NOT NULL,
    reason_id BIGINT NOT NULL,
    nomor_resi VARCHAR(50) NOT NULL UNIQUE,
    shipping_duration INT,
    shipping_cost NUMERIC(15, 2),
    is_late INT NOT NULL DEFAULT 0 CHECK (is_late IN (0, 1)),
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fact_time FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
    CONSTRAINT fk_fact_branch FOREIGN KEY (branch_id) REFERENCES dim_branch(branch_id),
    CONSTRAINT fk_fact_service FOREIGN KEY (service_id) REFERENCES dim_service(service_id),
    CONSTRAINT fk_fact_destination FOREIGN KEY (destination_id) REFERENCES dim_destination(destination_id),
    CONSTRAINT fk_fact_item FOREIGN KEY (item_id) REFERENCES dim_item(item_id),
    CONSTRAINT fk_fact_route FOREIGN KEY (route_id) REFERENCES dim_route(route_id),
    CONSTRAINT fk_fact_customer FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
    CONSTRAINT fk_fact_status FOREIGN KEY (status_id) REFERENCES dim_status(status_id),
    CONSTRAINT fk_fact_reason FOREIGN KEY (reason_id) REFERENCES dim_reason(reason_id)
);

-- Metadata ETL 
CREATE TABLE etl_run_log (
    run_id BIGSERIAL PRIMARY KEY,
    source_file TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'RUNNING',
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    rows_extracted INT DEFAULT 0,
    rows_after_cleaning INT DEFAULT 0,
    rows_loaded INT DEFAULT 0,
    clean_csv TEXT,
    error_message TEXT
);

CREATE TABLE etl_step_log (
    step_log_id BIGSERIAL PRIMARY KEY,
    run_id BIGINT REFERENCES etl_run_log(run_id) ON DELETE CASCADE,
    step_name VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds NUMERIC(12, 3),
    rows_processed INT,
    message TEXT
);

CREATE INDEX idx_fact_shipping_time_id ON fact_shipping(time_id);
CREATE INDEX idx_fact_shipping_branch_id ON fact_shipping(branch_id);
CREATE INDEX idx_fact_shipping_service_id ON fact_shipping(service_id);
CREATE INDEX idx_fact_shipping_status_id ON fact_shipping(status_id);
CREATE INDEX idx_fact_shipping_is_late ON fact_shipping(is_late);
CREATE INDEX idx_etl_run_log_started_at ON etl_run_log(started_at DESC);
CREATE INDEX idx_etl_step_log_run_id ON etl_step_log(run_id);
