import html as _html
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

from ruleset.etl_process import get_default_db_url
from utils.ui import hero, load_css, metric_card, scroll_table, status_badge


load_css()


@st.cache_resource
def get_engine():
    return create_engine(get_default_db_url(), pool_pre_ping=True)


def load_run_logs(engine) -> pd.DataFrame:
    return pd.read_sql(
        text(
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
            LIMIT 30
            """
        ),
        engine,
    )


def load_step_logs(engine, run_id: int) -> pd.DataFrame:
    return pd.read_sql(
        text(
            """
            SELECT
                step_name,
                status,
                duration_seconds,
                rows_processed,
                message
            FROM etl_step_log
            WHERE run_id = :run_id
            ORDER BY step_log_id
            """
        ),
        engine,
        params={"run_id": run_id},
    )


engine = get_engine()

hero(
    "ETL Audit Log",
    "Timeline eksekusi pipeline untuk memantau status, durasi, jumlah baris, archive raw file, dan error message.",
    "Operational Audit",
)

try:
    run_logs = load_run_logs(engine)
except Exception as exc:
    st.markdown(
        '<div class="empty-state">Audit log belum tersedia. Jalankan ETL Pipeline terlebih dahulu.</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Detail error"):
        st.exception(exc)
    st.stop()

if run_logs.empty:
    st.markdown('<div class="empty-state">Belum ada riwayat ETL.</div>', unsafe_allow_html=True)
    st.stop()

success_count = int((run_logs["status"].str.upper() == "SUCCESS").sum())
failed_count = int((run_logs["status"].str.upper() == "FAILED").sum())
total_loaded = int(run_logs["rows_loaded"].fillna(0).sum())

# ── Summary metrics ──
cols = st.columns(4)
with cols[0]:
    metric_card("Total Runs", f"{len(run_logs):,}", "latest 30", "indigo")
with cols[1]:
    metric_card("Successful", f"{success_count:,}", "completed", "green")
with cols[2]:
    metric_card("Failed", f"{failed_count:,}", "error runs", "red" if failed_count > 0 else "gray")
with cols[3]:
    metric_card("Rows Loaded", f"{total_loaded:,}", "total processed", "yellow" if failed_count else "green")

# ── Section header ──
st.markdown(
    """
    <div class="section-divider">
        <div class="section-divider-icon">📋</div>
        <div class="section-divider-text">
            <div class="section-divider-title">Run History</div>
            <div class="section-divider-sub">Detail setiap eksekusi pipeline ETL beserta step log</div>
        </div>
        <div class="section-divider-line"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

for row in run_logs.itertuples(index=False):
    source_name = Path(str(row.source_file)).name if row.source_file else "-"
    status_text = str(row.status or "UNKNOWN").upper()
    status_icon = "✅" if status_text == "SUCCESS" else "❌" if status_text == "FAILED" else "⏳"
    status_html = status_badge(row.status)

    with st.expander(f"{status_icon} Run #{row.run_id} — {source_name}"):
        st.markdown(status_html, unsafe_allow_html=True)

        meta_cols = st.columns(4)
        with meta_cols[0]:
            metric_card("Extracted", f"{int(row.rows_extracted or 0):,}", "raw rows", "indigo")
        with meta_cols[1]:
            metric_card("Cleaned", f"{int(row.rows_after_cleaning or 0):,}", "after transform", "yellow")
        with meta_cols[2]:
            metric_card("Loaded", f"{int(row.rows_loaded or 0):,}", "warehouse rows", "green")
        with meta_cols[3]:
            duration = ""
            if row.started_at is not None and row.ended_at is not None:
                duration_seconds = (pd.to_datetime(row.ended_at) - pd.to_datetime(row.started_at)).total_seconds()
                duration = f"{duration_seconds:.1f}s"
            metric_card("Duration", duration or "-", "elapsed", "gray")

        # Pipeline progress bar
        extracted = int(row.rows_extracted or 0)
        cleaned = int(row.rows_after_cleaning or 0)
        loaded = int(row.rows_loaded or 0)
        if extracted > 0:
            clean_pct = min(100, int(cleaned / extracted * 100))
            load_pct = min(100, int(loaded / extracted * 100))
            st.markdown(
                f"""
                <div style="margin:10px 0 8px;">
                    <div style="display:flex; justify-content:space-between; font-size:11px; color:#94A3B8; font-weight:700; margin-bottom:6px;">
                        <span>Extract → Clean: {clean_pct}%</span>
                        <span>Clean → Load: {load_pct}%</span>
                    </div>
                    <div style="height:6px; background:rgba(148,163,184,.12); border-radius:999px; overflow:hidden; display:flex;">
                        <div style="width:{load_pct}%; background:linear-gradient(90deg, #4F46E5, #22C55E); border-radius:999px; transition: width .5s ease;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        steps = load_step_logs(engine, int(row.run_id))
        if not steps.empty:
            steps_display = steps.copy()
            steps_display["status"] = steps_display["status"].map(status_badge)
            st.write(scroll_table(steps_display.to_html(escape=False, index=False)), unsafe_allow_html=True)

        if row.error_message:
            st.error(row.error_message)
