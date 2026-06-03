from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

from etl_process import LogiTrackETL, find_latest_raw_csv, get_default_db_url
from generate_data import DEFAULT_END_DATE, DEFAULT_START_DATE, RAW_DIR, generate_dataset

st.set_page_config(page_title="ETL Operations", layout="wide")


@st.cache_resource
def get_engine():
    return create_engine(get_default_db_url(), pool_pre_ping=True)


def validate_raw_file(candidate: str | Path | None) -> Path | None:
    if candidate is None:
        return None
    path = Path(candidate)
    if not path.exists():
        return None
    if path.suffix.lower() != ".csv":
        return None
    if path.parent.resolve() != RAW_DIR.resolve():
        return None
    return path.resolve()


def get_next_raw_file() -> Path | None:
    session_file = validate_raw_file(st.session_state.get("latest_file"))
    if session_file:
        return session_file
    latest_file = find_latest_raw_csv(raw_dir=RAW_DIR)
    return validate_raw_file(latest_file)


def read_etl_logs(engine):
    run_logs = pd.read_sql(
        """
        SELECT
            run_id,
            source_file,
            status,
            started_at,
            ended_at,
            rows_extracted,
            rows_after_cleaning,
            rows_loaded,
            error_message
        FROM etl_run_log
        ORDER BY run_id DESC
        LIMIT 10
        """,
        engine,
    )
    step_logs = pd.read_sql(
        """
        SELECT
            step_name,
            status,
            duration_seconds,
            rows_processed,
            message
        FROM etl_step_log
        ORDER BY step_log_id DESC
        LIMIT 20
        """,
        engine,
    )
    return run_logs, step_logs


def warehouse_counts(engine) -> dict[str, int]:
    tables = [
        "fact_shipping",
        "dim_time",
        "dim_branch",
        "dim_service",
        "dim_destination",
        "dim_item",
        "dim_route",
        "dim_customer",
    ]
    counts = {}
    with engine.connect() as conn:
        for table in tables:
            try:
                counts[table] = int(conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0)
            except Exception:
                counts[table] = 0
    return counts


engine = get_engine()

st.title("ETL Operations")
st.caption("Simulasi raw data, eksekusi ETL, dan audit pipeline menuju PostgreSQL data warehouse.")

with st.sidebar:
    st.header("Data Generation")
    num_rows = st.number_input("Jumlah baris raw", min_value=1_000, max_value=100_000, value=15_000, step=1_000)
    start_date = st.date_input("Tanggal awal", value=DEFAULT_START_DATE)
    end_date = st.date_input("Tanggal akhir", value=DEFAULT_END_DATE)
    seed_text = st.text_input("Seed opsional", value="", help="Isi angka agar data dummy bisa direproduksi.")
    inject_dirty = st.checkbox("Sisipkan dirty data untuk demo cleaning", value=True)

    st.divider()
    st.header("Raw File")
    next_file = get_next_raw_file()
    if next_file:
        st.success(f"Siap diproses: {next_file.name}")
    else:
        st.info("Tidak ada raw CSV aktif di folder raw.")

left, right = st.columns([1, 1])

with left:
    st.subheader("1. Generate Raw Data")
    st.write("Membuat data transaksi dummy yang masih mentah, termasuk variasi musiman, rute, layanan, risiko keterlambatan, dan dirty data terkontrol.")

    if st.button("Generate Raw Data", width="stretch"):
        if end_date < start_date:
            st.error("Tanggal akhir tidak boleh lebih awal dari tanggal awal.")
        else:
            seed = int(seed_text) if seed_text.strip().isdigit() else None
            with st.status("Membuat raw data...", expanded=True) as status:
                file_path = generate_dataset(
                    num_rows=int(num_rows),
                    start_date=start_date,
                    end_date=end_date,
                    seed=seed,
                    inject_dirty=inject_dirty,
                )
                st.session_state["latest_file"] = file_path
                status.update(label="Raw data berhasil dibuat.", state="complete", expanded=False)
            st.success(f"File baru: {Path(file_path).name}")
            st.rerun()

with right:
    st.subheader("2. Run ETL Pipeline")
    st.write("Memindahkan data dari raw CSV ke star schema. Tombol ini hanya aktif bila ada file raw yang valid dan belum diproses.")

    target_file = get_next_raw_file()
    run_disabled = target_file is None
    if st.button("Run ETL Pipeline", width="stretch", type="primary", disabled=run_disabled):
        if target_file is None:
            st.error("Tidak ada raw CSV valid. Generate raw data baru terlebih dahulu.")
        else:
            with st.status("Menjalankan Extract, Transform, Load...", expanded=True) as status:
                logs: list[str] = []

                def ui_callback(message: str) -> None:
                    logs.append(message)
                    st.write(message)

                try:
                    etl = LogiTrackETL(file_path=target_file, progress_callback=ui_callback)
                    result = etl.run_full_pipeline()
                    st.session_state.pop("latest_file", None)
                    st.cache_data.clear()
                    status.update(label="Pipeline ETL berhasil.", state="complete", expanded=False)
                    st.success(
                        f"Loaded {result['metrics']['rows_loaded']:,} shipment rows ke data warehouse."
                    )
                except Exception as exc:
                    status.update(label="Pipeline ETL gagal.", state="error", expanded=True)
                    st.error(str(exc))
                    with st.expander("Detail error"):
                        st.exception(exc)

if run_disabled:
    st.info("Run ETL akan aktif setelah ada file raw baru di folder raw. File yang sudah sukses diproses dipindahkan ke folder processed agar tidak diproses dua kali.")

st.divider()

st.subheader("Pipeline Audit")

try:
    counts = warehouse_counts(engine)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Fact Rows", f"{counts.get('fact_shipping', 0):,}")
    m2.metric("Dates", f"{counts.get('dim_time', 0):,}")
    m3.metric("Branches", f"{counts.get('dim_branch', 0):,}")
    m4.metric("Destinations", f"{counts.get('dim_destination', 0):,}")

    run_logs, step_logs = read_etl_logs(engine)
    tab_runs, tab_steps = st.tabs(["Run History", "Step Detail"])
    with tab_runs:
        st.dataframe(run_logs, width="stretch", hide_index=True)
    with tab_steps:
        st.dataframe(step_logs, width="stretch", hide_index=True)
except Exception as exc:
    st.info("Log belum tersedia. Jalankan pipeline untuk pertama kali.")
    with st.expander("Detail koneksi/log"):
        st.exception(exc)
