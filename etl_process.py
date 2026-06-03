from __future__ import annotations

import argparse
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL
from dotenv import load_dotenv

# Load file .env project agar konfigurasi lokal tidak kalah oleh environment global.
load_dotenv(override=True)

SCRIPT_DIR = Path(__file__).resolve().parent

# Gunakan os.getenv dengan fallback default agar anti-error
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASS = os.getenv('DB_PASS', 'admin123')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'logitrack_dw')


def _build_default_db_url() -> str:
    explicit_url = os.getenv("LOGITRACK_DB_URL")
    if explicit_url:
        return explicit_url

    return URL.create(
        "postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
    ).render_as_string(hide_password=False)


DEFAULT_DB_URL = _build_default_db_url()
DEFAULT_SCHEMA_PATH = SCRIPT_DIR / "schema.sql"
DEFAULT_RAW_DIR = SCRIPT_DIR / "raw"
DEFAULT_PROCESSED_DIR = SCRIPT_DIR / "processed"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "Nomor_Resi", "Shipping_Date", "Branch_Code", "Branch_Name", "Branch_City",
    "Branch_Province", "Service_Type", "Service_Name", "SLA_Days", "Receiver_Address",
    "Dest_District", "Dest_City", "Dest_Province", "Dest_ZIP", "Item_Name",
    "Item_Category", "Weight_Kg", "Fragile_Status", "Origin_City", "Transit_Point",
    "Destination_City_Code", "Customer_Name", "Customer_Type", "Customer_Phone",
    "Shipping_Status", "Shipping_Cost", "Shipping_Duration", "Is_Late",
    "Delay_Reason_Category", "Delay_Description",
]

SLA_BY_SERVICE_TYPE = {"REG": 3, "EXP": 1, "ECO": 6, "SME": 0}
LATE_STATUSES = {"Delayed", "Failed", "Returned To Sender", "Returned to Sender"}
WAREHOUSE_TABLES = [
    "fact_shipping", "dim_time", "dim_service", "dim_destination", "dim_status",
    "dim_reason", "dim_branch", "dim_item", "dim_route", "dim_customer",
]

ProgressCallback = Callable[[str], None]


def get_default_db_url() -> str:
    return DEFAULT_DB_URL


def find_latest_raw_csv(raw_dir: str | Path = DEFAULT_RAW_DIR) -> Optional[Path]:
    raw_dir = Path(raw_dir)
    candidates = sorted(raw_dir.glob("raw_nasional_logistics_data_*.csv"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0].resolve() if candidates else None


class LogiTrackETL:
    def __init__(
        self,
        file_path: str | Path,
        db_url: str = DEFAULT_DB_URL,
        schema_path: str | Path = DEFAULT_SCHEMA_PATH,
        processed_dir: str | Path = DEFAULT_PROCESSED_DIR,
        refresh_warehouse: bool = True,
        chunksize: int = 5_000,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        self.file_path = Path(file_path).resolve()
        self.db_url = db_url
        self.schema_path = Path(schema_path).resolve()
        self.processed_dir = Path(processed_dir).resolve()
        self.refresh_warehouse = refresh_warehouse
        self.chunksize = chunksize
        self.progress_callback = progress_callback

        self.engine: Engine = create_engine(db_url, pool_pre_ping=True)
        self.df: pd.DataFrame = pd.DataFrame()
        self.clean_csv_path: Optional[Path] = None
        self.run_id: Optional[int] = None
        self.steps: list[dict[str, object]] = []
        self.metrics: dict[str, int] = {
            "rows_extracted": 0,
            "rows_after_cleaning": 0,
            "rows_loaded": 0,
        }

    # ------------------------------------------------------------------
    # Utility & logging
    # ------------------------------------------------------------------
    def _emit(self, message: str) -> None:
        logger.info(message)
        if self.progress_callback:
            self.progress_callback(message)

    def _execute_sql_file(self, sql_path: Path) -> None:
        if not sql_path.exists():
            raise FileNotFoundError(f"schema.sql tidak ditemukan: {sql_path}")
        sql = sql_path.read_text(encoding="utf-8")
        with self.engine.begin() as conn:
            conn.exec_driver_sql(sql)

    def ensure_schema(self) -> None:
        self._emit("Memastikan schema PostgreSQL tersedia...")
        self._execute_sql_file(self.schema_path)

    def reset_warehouse_tables(self) -> None:
        joined_tables = ", ".join(WAREHOUSE_TABLES)
        self._emit("Melakukan full refresh Data Warehouse: TRUNCATE fact dan dimension tables...")
        with self.engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {joined_tables} RESTART IDENTITY CASCADE"))

    def _create_run_log(self) -> int:
        with self.engine.begin() as conn:
            run_id = conn.execute(
                text(
                    """
                    INSERT INTO etl_run_log (source_file, status)
                    VALUES (:source_file, 'RUNNING')
                    RETURNING run_id
                    """
                ),
                {"source_file": str(self.file_path)},
            ).scalar_one()
        return int(run_id)

    def _update_run_log(self, status: str, error_message: Optional[str] = None) -> None:
        if self.run_id is None:
            return
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE etl_run_log
                    SET status = :status,
                        ended_at = CURRENT_TIMESTAMP,
                        rows_extracted = :rows_extracted,
                        rows_after_cleaning = :rows_after_cleaning,
                        rows_loaded = :rows_loaded,
                        clean_csv = :clean_csv,
                        error_message = :error_message
                    WHERE run_id = :run_id
                    """
                ),
                {
                    "status": status,
                    "rows_extracted": self.metrics["rows_extracted"],
                    "rows_after_cleaning": self.metrics["rows_after_cleaning"],
                    "rows_loaded": self.metrics["rows_loaded"],
                    "clean_csv": str(self.clean_csv_path) if self.clean_csv_path else None,
                    "error_message": error_message,
                    "run_id": self.run_id,
                },
            )

    def _insert_step_log(
        self,
        step_name: str,
        status: str,
        started_at_sql: str,
        duration_seconds: float,
        rows_processed: Optional[int],
        message: str,
    ) -> None:
        if self.run_id is None:
            return
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO etl_step_log
                        (run_id, step_name, status, started_at, ended_at, duration_seconds, rows_processed, message)
                    VALUES
                        (:run_id, :step_name, :status, CAST(:started_at AS TIMESTAMP), CURRENT_TIMESTAMP,
                         :duration_seconds, :rows_processed, :message)
                    """
                ),
                {
                    "run_id": self.run_id,
                    "step_name": step_name,
                    "status": status,
                    "started_at": started_at_sql,
                    "duration_seconds": round(duration_seconds, 3),
                    "rows_processed": rows_processed,
                    "message": message,
                },
            )

    def _run_step(self, step_name: str, func: Callable[[], Optional[int]]) -> Optional[int]:
        self._emit(f"Mulai step: {step_name}")
        started_at_sql = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        start = time.perf_counter()
        try:
            rows = func()
            duration = time.perf_counter() - start
            message = f"{step_name} selesai dalam {duration:.2f} detik"
            self._insert_step_log(step_name, "SUCCESS", started_at_sql, duration, rows, message)
            self.steps.append(
                {
                    "step": step_name,
                    "status": "SUCCESS",
                    "duration_seconds": round(duration, 3),
                    "rows_processed": rows,
                    "message": message,
                }
            )
            self._emit(message)
            return rows
        except Exception as exc:
            duration = time.perf_counter() - start
            message = f"{step_name} gagal: {exc}"
            self._insert_step_log(step_name, "FAILED", started_at_sql, duration, None, message)
            self.steps.append(
                {
                    "step": step_name,
                    "status": "FAILED",
                    "duration_seconds": round(duration, 3),
                    "rows_processed": None,
                    "message": message,
                }
            )
            self._emit(message)
            raise

    # ------------------------------------------------------------------
    # Extract
    # ------------------------------------------------------------------
    def extract(self) -> int:
        if not self.file_path.exists():
            raise FileNotFoundError(f"File CSV tidak ditemukan: {self.file_path}")
        self.df = pd.read_csv(self.file_path)
        missing = [col for col in REQUIRED_COLUMNS if col not in self.df.columns]
        if missing:
            raise ValueError(f"Kolom wajib hilang dari CSV: {missing}")
        self.metrics["rows_extracted"] = len(self.df)
        return len(self.df)

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_text(series: pd.Series) -> pd.Series:
        return series.fillna("Unknown").astype(str).str.strip().str.replace(r"\s+", " ", regex=True).str.title()

    @staticmethod
    def _safe_zip(series: pd.Series) -> pd.Series:
        return (
            series.fillna("00000")
            .astype(str)
            .str.replace(r"\D", "", regex=True)
            .replace("", "00000")
            .str[-5:]
            .str.zfill(5)
        )

    def _fix_weight(self) -> None:
        self.df["Weight_Kg"] = pd.to_numeric(self.df["Weight_Kg"], errors="coerce")
        valid_weight = self.df["Weight_Kg"].between(0.1, 100)
        median_weight = self.df.loc[valid_weight, "Weight_Kg"].median()
        if pd.isna(median_weight):
            median_weight = 1.0
        self.df.loc[~valid_weight, "Weight_Kg"] = round(float(median_weight), 2)
        self.df["Weight_Kg"] = self.df["Weight_Kg"].round(2)

    def _fix_cost(self) -> None:
        self.df["Shipping_Cost"] = pd.to_numeric(self.df["Shipping_Cost"], errors="coerce")
        valid_cost = self.df["Shipping_Cost"] > 0
        median_cost = self.df.loc[valid_cost, "Shipping_Cost"].median()
        if pd.isna(median_cost):
            median_cost = 25_000
        self.df.loc[~valid_cost, "Shipping_Cost"] = median_cost
        self.df["Shipping_Cost"] = self.df["Shipping_Cost"].round(2)

    def transform(self) -> int:
        df_before = len(self.df)

        self.df["Nomor_Resi"] = self.df["Nomor_Resi"].astype(str).str.strip().str.upper()
        self.df = self.df.dropna(subset=["Nomor_Resi", "Shipping_Date"])
        self.df = self.df[self.df["Nomor_Resi"].ne("")]
        self.df = self.df.drop_duplicates(subset=["Nomor_Resi"], keep="first")

        self.df["Shipping_Date"] = pd.to_datetime(self.df["Shipping_Date"], errors="coerce")
        self.df = self.df.dropna(subset=["Shipping_Date"])

        text_columns = [
            "Branch_Name", "Branch_City", "Branch_Province", "Service_Name",
            "Receiver_Address", "Dest_District", "Dest_City", "Dest_Province",
            "Item_Name", "Item_Category", "Origin_City", "Destination_City_Code",
            "Customer_Name", "Customer_Type", "Shipping_Status",
        ]
        for col in text_columns:
            self.df[col] = self._normalize_text(self.df[col])

        self.df["Branch_Code"] = self.df["Branch_Code"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
        self.df["Service_Type"] = self.df["Service_Type"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
        self.df["Transit_Point"] = self.df["Transit_Point"].fillna("Direct").astype(str).str.strip().str.upper().replace({"NAN": "DIRECT", "NONE": "DIRECT", "": "DIRECT"})
        self.df["Customer_Phone"] = self.df["Customer_Phone"].fillna("Unknown").astype(str).str.strip()
        self.df["Dest_ZIP"] = self._safe_zip(self.df["Dest_ZIP"])

        self.df["Delay_Reason_Category"] = self._normalize_text(self.df["Delay_Reason_Category"]).replace(
            {"Nan": "No Delay", "None": "No Delay", "Unknown": "No Delay"}
        )
        self.df["Delay_Description"] = self.df["Delay_Description"].fillna("No delay").astype(str).str.strip().replace({"nan": "No delay", "None": "No delay", "": "No delay"})

        self.df["Fragile_Status"] = self.df["Fragile_Status"].astype(str).str.lower().isin(["true", "1", "yes", "y"])
        self._fix_weight()
        self._fix_cost()

        self.df["SLA_Days"] = self.df["Service_Type"].map(SLA_BY_SERVICE_TYPE)
        self.df["SLA_Days"] = self.df["SLA_Days"].fillna(pd.to_numeric(self.df["SLA_Days"], errors="coerce")).fillna(3).astype(int)
        self.df["Shipping_Duration"] = pd.to_numeric(self.df["Shipping_Duration"], errors="coerce").fillna(self.df["SLA_Days"])
        self.df["Shipping_Duration"] = self.df["Shipping_Duration"].clip(lower=0).round().astype(int)

        self.df["Is_Late"] = np.where(
            self.df["Shipping_Status"].isin(LATE_STATUSES) | (self.df["Shipping_Duration"] > self.df["SLA_Days"]),
            1, 0,
        ).astype(int)
        self.df.loc[self.df["Is_Late"].eq(0), ["Delay_Reason_Category", "Delay_Description"]] = ["No Delay", "No delay"]

        self.df["date"] = self.df["Shipping_Date"].dt.date
        self.df["day"] = self.df["Shipping_Date"].dt.day
        self.df["month"] = self.df["Shipping_Date"].dt.month
        self.df["year"] = self.df["Shipping_Date"].dt.year
        self.df["quarter"] = self.df["Shipping_Date"].dt.quarter
        self.df["day_name"] = self.df["Shipping_Date"].dt.day_name()
        self.df["month_name"] = self.df["Shipping_Date"].dt.month_name()
        self.df["is_weekend"] = self.df["Shipping_Date"].dt.dayofweek.isin([5, 6])

        self.metrics["rows_after_cleaning"] = len(self.df)
        self._emit(f"Cleaning selesai: {df_before:,} baris awal -> {len(self.df):,} baris bersih")
        return len(self.df)

    # ------------------------------------------------------------------
    # Load dimensions & fact
    # ------------------------------------------------------------------
    def _to_sql_append(self, df: pd.DataFrame, table_name: str) -> None:
        df.to_sql(table_name, self.engine, if_exists="append", index=False, chunksize=self.chunksize, method="multi")

    def load_dimensions(self) -> int:
        total_rows = 0

        dim_time = self.df[["date", "day", "month", "year", "quarter", "day_name", "month_name", "is_weekend"]].drop_duplicates("date")
        self._to_sql_append(dim_time, "dim_time")
        total_rows += len(dim_time)

        dim_service = self.df[["Service_Type", "Service_Name", "SLA_Days"]].drop_duplicates()
        dim_service = dim_service.rename(columns={"Service_Type": "service_type", "Service_Name": "service_name", "SLA_Days": "sla_days"})
        self._to_sql_append(dim_service, "dim_service")
        total_rows += len(dim_service)

        dim_destination = self.df[["Receiver_Address", "Dest_District", "Dest_City", "Dest_Province", "Dest_ZIP"]].drop_duplicates()
        dim_destination = dim_destination.rename(
            columns={
                "Receiver_Address": "receiver_address", "Dest_District": "district",
                "Dest_City": "city", "Dest_Province": "province", "Dest_ZIP": "zip_code",
            }
        )
        self._to_sql_append(dim_destination, "dim_destination")
        total_rows += len(dim_destination)

        dim_status = pd.DataFrame({"status_name": sorted(self.df["Shipping_Status"].dropna().unique())})
        self._to_sql_append(dim_status, "dim_status")
        total_rows += len(dim_status)

        dim_reason = (
            self.df[["Delay_Reason_Category", "Delay_Description"]]
            .rename(columns={"Delay_Reason_Category": "reason_category", "Delay_Description": "description"})
            .sort_values(["reason_category", "description"])
            .drop_duplicates(subset=["reason_category"], keep="first")
        )
        self._to_sql_append(dim_reason, "dim_reason")
        total_rows += len(dim_reason)

        dim_branch = self.df[["Branch_Code", "Branch_Name", "Branch_City", "Branch_Province"]].drop_duplicates("Branch_Code")
        dim_branch = dim_branch.rename(
            columns={
                "Branch_Code": "branch_code", "Branch_Name": "branch_name",
                "Branch_City": "city", "Branch_Province": "region_province",
            }
        )
        self._to_sql_append(dim_branch, "dim_branch")
        total_rows += len(dim_branch)

        dim_item = self.df[["Item_Name", "Item_Category", "Weight_Kg", "Fragile_Status"]].drop_duplicates()
        dim_item = dim_item.rename(
            columns={"Item_Name": "item_name", "Item_Category": "item_category", "Weight_Kg": "weight_kg", "Fragile_Status": "fragile_status"}
        )
        self._to_sql_append(dim_item, "dim_item")
        total_rows += len(dim_item)

        dim_route = self.df[["Origin_City", "Transit_Point", "Destination_City_Code"]].drop_duplicates()
        dim_route = dim_route.rename(
            columns={"Origin_City": "origin_city", "Transit_Point": "transit_point", "Destination_City_Code": "destination_city_code"}
        )
        self._to_sql_append(dim_route, "dim_route")
        total_rows += len(dim_route)

        dim_customer = self.df[["Customer_Name", "Customer_Type", "Customer_Phone"]].drop_duplicates()
        dim_customer = dim_customer.rename(
            columns={"Customer_Name": "customer_name", "Customer_Type": "customer_type", "Customer_Phone": "phone_number"}
        )
        self._to_sql_append(dim_customer, "dim_customer")
        total_rows += len(dim_customer)

        return total_rows

    def _read_map(self, query: str, key_cols: list[str], id_col: str) -> dict[object, int]:
        map_df = pd.read_sql(query, self.engine)
        if len(key_cols) == 1:
            return dict(zip(map_df[key_cols[0]], map_df[id_col]))
        keys = list(map(tuple, map_df[key_cols].to_numpy()))
        return dict(zip(keys, map_df[id_col]))

    def load_fact(self) -> int:
        time_map = self._read_map("SELECT time_id, date FROM dim_time", ["date"], "time_id")
        time_map = {pd.to_datetime(k).date(): v for k, v in time_map.items()}

        branch_map = self._read_map("SELECT branch_id, branch_code FROM dim_branch", ["branch_code"], "branch_id")
        service_map = self._read_map("SELECT service_id, service_type, service_name, sla_days FROM dim_service", ["service_type", "service_name", "sla_days"], "service_id")
        destination_map = self._read_map(
            "SELECT destination_id, receiver_address, district, city, province, zip_code FROM dim_destination",
            ["receiver_address", "district", "city", "province", "zip_code"], "destination_id",
        )
        status_map = self._read_map("SELECT status_id, status_name FROM dim_status", ["status_name"], "status_id")
        reason_map = self._read_map("SELECT reason_id, reason_category FROM dim_reason", ["reason_category"], "reason_id")
        item_map = self._read_map(
            "SELECT item_id, item_name, item_category, weight_kg::float AS weight_kg, fragile_status FROM dim_item",
            ["item_name", "item_category", "weight_kg", "fragile_status"], "item_id",
        )
        route_map = self._read_map(
            "SELECT route_id, origin_city, transit_point, destination_city_code FROM dim_route",
            ["origin_city", "transit_point", "destination_city_code"], "route_id",
        )
        customer_map = self._read_map(
            "SELECT customer_id, customer_name, customer_type, phone_number FROM dim_customer",
            ["customer_name", "customer_type", "phone_number"], "customer_id",
        )

        fact = self.df.copy()
        fact["time_id"] = fact["date"].map(time_map)
        fact["branch_id"] = fact["Branch_Code"].map(branch_map)
        fact["service_id"] = list(
            map(lambda row: service_map.get((row.Service_Type, row.Service_Name, int(row.SLA_Days))), fact.itertuples(index=False))
        )
        fact["destination_id"] = list(
            map(
                lambda row: destination_map.get((row.Receiver_Address, row.Dest_District, row.Dest_City, row.Dest_Province, row.Dest_ZIP)),
                fact.itertuples(index=False),
            )
        )
        fact["status_id"] = fact["Shipping_Status"].map(status_map)
        fact["reason_id"] = fact["Delay_Reason_Category"].map(reason_map)
        fact["item_id"] = list(
            map(
                lambda row: item_map.get((row.Item_Name, row.Item_Category, float(row.Weight_Kg), bool(row.Fragile_Status))),
                fact.itertuples(index=False),
            )
        )
        fact["route_id"] = list(
            map(
                lambda row: route_map.get((row.Origin_City, row.Transit_Point, row.Destination_City_Code)),
                fact.itertuples(index=False),
            )
        )
        fact["customer_id"] = list(
            map(
                lambda row: customer_map.get((row.Customer_Name, row.Customer_Type, row.Customer_Phone)),
                fact.itertuples(index=False),
            )
        )

        final_fact = fact[
            [
                "time_id", "branch_id", "service_id", "destination_id", "item_id", 
                "route_id", "customer_id", "status_id", "reason_id", "Nomor_Resi", 
                "Shipping_Duration", "Shipping_Cost", "Is_Late",
            ]
        ].rename(
            columns={
                "Nomor_Resi": "nomor_resi",
                "Shipping_Duration": "shipping_duration",
                "Shipping_Cost": "shipping_cost",
                "Is_Late": "is_late",
            }
        )

        mandatory_fk = ["time_id", "branch_id", "service_id", "destination_id", "item_id", "route_id", "customer_id", "status_id", "reason_id"]
        missing_fk_rows = int(final_fact[mandatory_fk].isna().any(axis=1).sum())
        if missing_fk_rows:
            self._emit(f"Warning: {missing_fk_rows:,} baris fact dibuang karena FK tidak termapping.")
        final_fact = final_fact.dropna(subset=mandatory_fk)
        final_fact[mandatory_fk] = final_fact[mandatory_fk].astype(int)
        final_fact["is_late"] = final_fact["is_late"].astype(int)

        self._to_sql_append(final_fact, "fact_shipping")
        self.metrics["rows_loaded"] = len(final_fact)
        return len(final_fact)

    def export_clean_csv(self) -> int:
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        self.clean_csv_path = self.processed_dir / f"logistics_clean_final_{timestamp}.csv"
        self.df.to_csv(self.clean_csv_path, index=False)
        return len(self.df)

    def run_full_pipeline(self) -> dict[str, object]:
        pipeline_started = time.perf_counter()
        self.ensure_schema()
        self.run_id = self._create_run_log()

        try:
            if self.refresh_warehouse:
                self._run_step("Reset Warehouse Tables", self.reset_warehouse_tables)
            self._run_step("Extract Raw CSV", self.extract)
            self._run_step("Transform & Clean Data", self.transform)
            self._run_step("Load Dimension Tables", self.load_dimensions)
            self._run_step("Load Fact Table", self.load_fact)
            self._run_step("Export Clean CSV", self.export_clean_csv)
            self._update_run_log("SUCCESS")
            duration = time.perf_counter() - pipeline_started
            
            # --- FITUR BARU: Memindahkan file mentah ke folder processed ---
            filename = self.file_path.name
            self.processed_dir.mkdir(parents=True, exist_ok=True)
            processed_raw_path = self.processed_dir / f"done_{filename}"
            shutil.move(str(self.file_path), str(processed_raw_path))
            self._emit(f"File raw mentah otomatis dipindahkan ke: {processed_raw_path}")
            # ---------------------------------------------------------------

            self._emit("ETL PROCESS COMPLETE. Data Warehouse siap digunakan di dashboard dan Adminer.")
            return {
                "run_id": self.run_id,
                "status": "SUCCESS",
                "source_file": str(self.file_path),
                "clean_csv": str(self.clean_csv_path) if self.clean_csv_path else None,
                "duration_seconds": round(duration, 3),
                "metrics": self.metrics.copy(),
                "steps": self.steps,
            }
        except Exception as exc:
            self._update_run_log("FAILED", str(exc))
            raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ETL pipeline from raw CSV into PostgreSQL data warehouse.")
    parser.add_argument("--file", default=None, help="Path CSV raw. Jika kosong, ETL mengambil CSV terbaru di data/raw.")
    parser.add_argument("--db-url", default=DEFAULT_DB_URL, help="PostgreSQL URL.")
    parser.add_argument("--append", action="store_true", help="Append data tanpa TRUNCATE warehouse. Default: full refresh.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    csv_file = Path(args.file).resolve() if args.file else find_latest_raw_csv()
    if csv_file is None:
        raise FileNotFoundError("Tidak ada raw_nasional_logistics_data_*.csv di folder raw.")
    etl = LogiTrackETL(file_path=csv_file, db_url=args.db_url, refresh_warehouse=not args.append)
    result = etl.run_full_pipeline()
    print(result)
