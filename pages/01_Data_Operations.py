from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

from ruleset.etl_process import (
    LogiTrackETL,
    get_default_db_url,
)
from ruleset.generate_data import DEFAULT_DIRTY_RATES, DEFAULT_END_DATE, DEFAULT_START_DATE, RAW_DIR, generate_dataset
from utils.ui import hero, load_css, metric_card, scroll_table, status_badge

load_css()


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


def list_raw_files() -> list[Path]:
    if not RAW_DIR.exists():
        return []
    return sorted(RAW_DIR.glob("*.csv"), key=lambda path: path.stat().st_mtime, reverse=True)


def get_selected_raw_file() -> Path | None:
    return validate_raw_file(st.session_state.get("selected_raw_input"))


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


def dirty_mask(df: pd.DataFrame) -> pd.Series:
    checks = []
    if "Customer_Phone" in df:
        checks.append(df["Customer_Phone"].isna() | df["Customer_Phone"].astype(str).str.strip().eq(""))
    if "Dest_ZIP" in df:
        checks.append(df["Dest_ZIP"].isna() | df["Dest_ZIP"].astype(str).str.strip().eq(""))
    if "Weight_Kg" in df:
        checks.append(pd.to_numeric(df["Weight_Kg"], errors="coerce").lt(0))
    if "Shipping_Cost" in df:
        checks.append(pd.to_numeric(df["Shipping_Cost"], errors="coerce").lt(0))
    if "Nomor_Resi" in df:
        checks.append(df["Nomor_Resi"].duplicated(keep=False))
    if not checks:
        return pd.Series(False, index=df.index)
    mask = checks[0]
    for check in checks[1:]:
        mask = mask | check
    return mask


def preview_generated_file(path: str | Path | None) -> None:
    valid_path = validate_raw_file(path)
    if not valid_path:
        return
    try:
        df = pd.read_csv(valid_path, nrows=150)
        mask = dirty_mask(df)
        st.markdown("#### Latest Raw Preview")
        st.caption(f"{valid_path.name} - preview 150 rows")
        styled = df.head(60).style.apply(
            lambda row: ["background-color: #FEF9C3" if bool(mask.loc[row.name]) else "" for _ in row],
            axis=1,
        )
        st.dataframe(styled, width="stretch", hide_index=True)
        st.caption(f"Highlighted rows indicate dirty candidates in the preview: {int(mask.sum()):,} rows.")
    except Exception as exc:
        st.warning(f"Preview tidak bisa dibuka: {exc}")


engine = get_engine()

hero(
    "Data Operations",
    "Generate batch raw harian, jalankan ETL, pantau archive file, dan audit proses menuju PostgreSQL star schema.",
    "Daily Batch Ingestion",
)

with st.sidebar:
    st.header("Batch Controls")
    num_rows = st.number_input("Jumlah baris raw", min_value=1_000, max_value=100_000, value=15_000, step=1_000)
    start_date = st.date_input("Tanggal awal data", value=DEFAULT_START_DATE)
    end_date = st.date_input("Tanggal akhir data", value=DEFAULT_END_DATE)
    seed_text = st.text_input("Seed opsional", value="", help="Isi angka agar data dummy bisa direproduksi.")
    inject_dirty = st.checkbox("Sisipkan dirty data untuk demo cleaning", value=True)
    st.divider()
    st.header("Dirty Profile")
    dirty_rates = {
        "missing_phone": st.slider("Nomor telepon kosong", 0.0, 10.0, DEFAULT_DIRTY_RATES["missing_phone"] * 100, 0.1) / 100,
        "missing_zip": st.slider("Kode pos kosong", 0.0, 10.0, DEFAULT_DIRTY_RATES["missing_zip"] * 100, 0.1) / 100,
        "negative_weight": st.slider("Berat negatif", 0.0, 5.0, DEFAULT_DIRTY_RATES["negative_weight"] * 100, 0.1) / 100,
        "negative_cost": st.slider("Biaya negatif", 0.0, 5.0, DEFAULT_DIRTY_RATES["negative_cost"] * 100, 0.1) / 100,
        "messy_branch": st.slider("Teks cabang berantakan", 0.0, 5.0, DEFAULT_DIRTY_RATES["messy_branch"] * 100, 0.1) / 100,
        "duplicate_rows": st.slider("Duplikasi data", 0.0, 5.0, DEFAULT_DIRTY_RATES["duplicate_rows"] * 100, 0.1) / 100,
    }

    st.divider()
    st.header("Raw File")
    selected_sidebar_file = get_selected_raw_file()
    if selected_sidebar_file:
        st.success(f"Input dipilih: {selected_sidebar_file.name}")
    else:
        st.info("Belum ada input ETL. Generate batch atau pilih raw CSV.")

raw_files = list_raw_files()
target_file = get_selected_raw_file()
run_disabled = target_file is None
estimated_dirty = sum(int(num_rows * rate) for rate in dirty_rates.values()) if inject_dirty else 0

left, right = st.columns(2)

with left:
    selected_option = str(target_file) if target_file else None
    raw_options = [None] + [str(path.resolve()) for path in raw_files]
    selected_index = raw_options.index(selected_option) if selected_option in raw_options else 0
    st.markdown(
        f"""
        <div class="operation-panel generate">
            <div class="operation-head">
                <div>
                    <div class="operation-kicker">Generate</div>
                    <div class="operation-title">Raw Daily Batch</div>
                    <div class="operation-copy">Membuat CSV raw baru sebagai simulasi transaksi operasional harian.</div>
                </div>
                <div class="operation-step">01</div>
            </div>
            <div class="operation-meta-grid">
                <div class="operation-meta">
                    <div class="operation-meta-label">Rows</div>
                    <div class="operation-meta-value">{int(num_rows):,}</div>
                    <div class="operation-meta-note">raw volume</div>
                </div>
                <div class="operation-meta">
                    <div class="operation-meta-label">Dirty</div>
                    <div class="operation-meta-value">{estimated_dirty:,}</div>
                    <div class="operation-meta-note">estimated</div>
                </div>
                <div class="operation-meta">
                    <div class="operation-meta-label">Window</div>
                    <div class="operation-meta-value">{start_date:%b}-{end_date:%b}</div>
                    <div class="operation-meta-note">{start_date:%Y}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chosen_raw = st.selectbox(
        "Input raw untuk ETL",
        options=raw_options,
        index=selected_index,
        format_func=lambda value: "Belum memilih raw input" if value is None else Path(value).name,
    )
    if chosen_raw is None:
        st.session_state.pop("selected_raw_input", None)
        target_file = None
        run_disabled = True
    else:
        st.session_state["selected_raw_input"] = chosen_raw
        target_file = validate_raw_file(chosen_raw)
        run_disabled = target_file is None

    if st.button("Generate Daily Batch", width="stretch"):
        if end_date < start_date:
            st.error("Tanggal akhir tidak boleh lebih awal dari tanggal awal.")
        else:
            seed = int(seed_text) if seed_text.strip().isdigit() else None
            with st.status("Generating operational raw batch...", expanded=True) as status:
                st.write("Sampling branch, service, destination, customer, item, SLA, cost, and delay risk.")
                file_path = generate_dataset(
                    num_rows=int(num_rows),
                    start_date=start_date,
                    end_date=end_date,
                    seed=seed,
                    inject_dirty=inject_dirty,
                    dirty_rates=dirty_rates if inject_dirty else None,
                )
                st.session_state["selected_raw_input"] = file_path
                st.session_state["latest_generated_file"] = file_path
                status.update(label="Raw data berhasil dibuat.", state="complete", expanded=False)
            st.toast(f"Generated {Path(file_path).name}")
            st.rerun()

with right:
    raw_status = "Ready" if target_file else "No Input"
    raw_status_note = "selected" if target_file else "choose first"
    st.markdown(
        f"""
        <div class="operation-panel etl">
            <div class="operation-head">
                <div>
                    <div class="operation-kicker">Pipeline</div>
                    <div class="operation-title">Run ETL Pipeline</div>
                    <div class="operation-copy">Memproses raw CSV aktif, membersihkan data, lalu load ke PostgreSQL star schema.</div>
                </div>
                <div class="operation-step">02</div>
            </div>
            <div class="operation-meta-grid">
                <div class="operation-meta">
                    <div class="operation-meta-label">Raw Status</div>
                    <div class="operation-meta-value">{raw_status}</div>
                    <div class="operation-meta-note">{raw_status_note}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
                    st.session_state.pop("selected_raw_input", None)
                    st.cache_data.clear()
                    status.update(label="Pipeline ETL berhasil.", state="complete", expanded=False)
                    st.toast(f"Loaded {result['metrics']['rows_loaded']:,} shipment rows to warehouse.")
                    summary_cols = st.columns(3)
                    with summary_cols[0]:
                        metric_card("Extracted", f"{result['metrics']['rows_extracted']:,}", "raw rows", "indigo")
                    with summary_cols[1]:
                        metric_card("Cleaned", f"{result['metrics']['rows_after_cleaning']:,}", "after cleaning", "yellow")
                    with summary_cols[2]:
                        metric_card("Loaded", f"{result['metrics']['rows_loaded']:,}", "fact rows", "green")
                except Exception as exc:
                    status.update(label="Pipeline ETL gagal.", state="error", expanded=True)
                    st.error(str(exc))
                    with st.expander("Detail error"):
                        st.exception(exc)


if run_disabled:
    st.info("Run ETL akan aktif setelah kamu generate batch baru atau memilih raw CSV dari dataset/dynamic/raw.")

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

preview_generated_file(st.session_state.get("latest_generated_file") or st.session_state.get("selected_raw_input"))

st.divider()

st.subheader("Warehouse Snapshot & Pipeline Audit")

try:
    counts = warehouse_counts(engine)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        metric_card("Fact Rows", f"{counts.get('fact_shipping', 0):,}", "warehouse", "indigo")
    with m2:
        metric_card("Dates", f"{counts.get('dim_time', 0):,}", "dim_time", "gray")
    with m3:
        metric_card("Branches", f"{counts.get('dim_branch', 0):,}", "dim_branch", "green")
    with m4:
        metric_card("Destinations", f"{counts.get('dim_destination', 0):,}", "dim_destination", "yellow")

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    run_logs, step_logs = read_etl_logs(engine)
    tab_runs, tab_steps = st.tabs(["Run History", "Step Detail"])
    with tab_runs:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if run_logs.empty:
            st.markdown('<div class="empty-state">Belum ada run ETL.</div>', unsafe_allow_html=True)
        else:
            display_runs = run_logs.copy()
            display_runs["status"] = display_runs["status"].map(status_badge)
            display_runs["source_file"] = display_runs["source_file"].astype(str).map(lambda value: Path(value).name)
            st.write(scroll_table(display_runs.to_html(escape=False, index=False)), unsafe_allow_html=True)
    with tab_steps:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.dataframe(step_logs, width="stretch", hide_index=True)
except Exception as exc:
    st.info("Log belum tersedia. Jalankan pipeline untuk pertama kali.")
    with st.expander("Detail koneksi/log"):
        st.exception(exc)
