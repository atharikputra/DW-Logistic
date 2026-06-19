import html

import streamlit as st
from sqlalchemy import create_engine, text

from ruleset.etl_process import get_default_db_url
from utils.ui import hero, load_css


@st.cache_resource
def get_engine():
    return create_engine(get_default_db_url(), pool_pre_ping=True)


def connection_status() -> tuple[bool, str]:
    try:
        with get_engine().connect() as conn:
            db_name = conn.execute(text("SELECT current_database()")).scalar_one()
        return True, f"Connected to {db_name}"
    except Exception as exc:
        return False, str(exc)


def home_page() -> None:
    load_css()

    hero(
        "Executive Logistics Data Warehouse",
        "Aplikasi simulasi data warehouse untuk mengubah batch transaksi pengiriman harian menjadi insight SLA, revenue, cabang, rute, destinasi, customer, dan root cause delay.",
        "Tugas Akhir Data Warehouse",
    )

    # ── Quick overview strip ──
    overview_items = [
        ("Workflow", "Daily Batch", "Generate raw data", "indigo", ""),
        ("Storage", "Star Schema", "PostgreSQL Warehouse", "green", ""),
        ("Output", "BI Dashboard", "Managerial analytics", "yellow", ""),
    ]
    overview_html = "".join(
        f'<div class="overview-item {html.escape(tone)}">'
        f'<div class="overview-label">{html.escape(label)}</div>'
        f'<div class="overview-title">{icon} {html.escape(title)}</div>'
        f'<div class="overview-note">{html.escape(note)}</div>'
        "</div>"
        for label, title, note, tone, icon in overview_items
    )
    st.markdown(f'<div class="overview-strip">{overview_html}</div>', unsafe_allow_html=True)

    # ── Connection status ──
    connected, status_msg = connection_status()
    if connected:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:10px; padding:12px 18px;
                        background:rgba(34,197,94,.08); border:1px solid rgba(34,197,94,.22);
                        border-radius:12px; margin-bottom:20px;">
                <span style="width:10px; height:10px; border-radius:50%; background:#22C55E; display:inline-block;
                             box-shadow: 0 0 8px rgba(34,197,94,.50);"></span>
                <span style="color:#BBF7D0; font-weight:700; font-size:13px;">{html.escape(status_msg)}</span>
                <span style="color:#64748B; font-size:12px; margin-left:auto;">PostgreSQL ready</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:10px; padding:12px 18px;
                        background:rgba(248,113,113,.08); border:1px solid rgba(248,113,113,.22);
                        border-radius:12px; margin-bottom:20px;">
                <span style="width:10px; height:10px; border-radius:50%; background:#F87171; display:inline-block;
                             box-shadow: 0 0 8px rgba(248,113,113,.50);"></span>
                <span style="color:#FECACA; font-weight:700; font-size:13px;">Database not connected</span>
                <span style="color:#64748B; font-size:12px; margin-left:auto;">Check .env config</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Workflow overview ──
    st.markdown(
        """
        <div class="section-divider" style="margin-top:8px;">
            <div class="section-divider-icon">🔄</div>
            <div class="section-divider-text">
                <div class="section-divider-title">ETL Workflow</div>
                <div class="section-divider-sub">Alur kerja dari raw data menuju insight manajerial</div>
            </div>
            <div class="section-divider-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    workflow_items = [
        ("01", "Raw Batch", "Generate CSV transaksi harian dengan dirty data terkontrol untuk simulasi.", "indigo"),
        ("02", "ETL Pipeline", "Bersihkan, normalisasi, dan transformasi data dari raw menuju struktur analitik.", "yellow"),
        ("03", "Star Schema", "Load fact dan dimension tables ke PostgreSQL data warehouse.", "green"),
        ("04", "Analytics", "Pantau SLA, revenue, bottleneck rute, dan dapatkan rekomendasi DSS.", "yellow"),
    ]
    flow_parts = []
    for index, title, body, tone in workflow_items:
        flow_parts.append(
            f'<div class="flow-step {tone}">'
            f'<div class="flow-index">Step {index}</div>'
            f'<div class="flow-title">{title}</div>'
            f'<div class="flow-copy">{body}</div>'
            "</div>"
        )
    st.markdown(
        (
            '<div class="workflow-flow">'
            f"{flow_parts[0]}"
            '<div class="flow-arrow">→</div>'
            f"{flow_parts[1]}"
            '<div class="flow-arrow">→</div>'
            f"{flow_parts[2]}"
            '<div class="flow-arrow">→</div>'
            f"{flow_parts[3]}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    # ── Team section ──
    st.markdown(
        """
        <div class="section-divider">
            <div class="section-divider-icon">👥</div>
            <div class="section-divider-text">
                <div class="section-divider-title">Project Team</div>
                <div class="section-divider-sub">Tim pengembang proyek data warehouse logistik</div>
            </div>
            <div class="section-divider-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    members = [
        ("Ammara Azwadiena Alfiantie", "140810230073"),
        ("Aidan Ismail", "140810230075"),
        ("Atharik Putra Rajendra", "140810230077"),
    ]
    team_html = "".join(
        '<div class="team-card">'
        '<div class="team-role">Member</div>'
        f'<div class="team-name">{html.escape(name)}</div>'
        f'<div class="team-id">{html.escape(nim)}</div>'
        "</div>"
        for name, nim in members
    )
    st.markdown(f'<div class="team-grid">{team_html}</div>', unsafe_allow_html=True)

    # ── Quick start guide ──
    st.markdown(
        """
        <div class="takeaway-banner">
            <div class="takeaway-label">🚀 Quick Start</div>
            <div class="takeaway-text">
                Mulai dari halaman <strong>Data Operations</strong>: Generate Daily Batch → Run ETL Pipeline → lalu buka <strong>Analytics</strong> untuk melihat dashboard eksekutif dan rekomendasi DSS.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Logistics Data Warehouse", layout="wide")
load_css()

pages = {
    "Main": [
        st.Page(home_page, title="Home", icon=":material/home:"),
        st.Page("pages/01_Data_Operations.py", title="Data Operations", icon=":material/database_upload:"),
        st.Page("pages/02_Analytics.py", title="Analytics", icon=":material/monitoring:"),
    ],
    "More": [
        st.Page("pages/03_Data_Warehouse_Detail.py", title="Data Warehouse Detail", icon=":material/schema:"),
        st.Page("pages/04_ETL_Audit_Log.py", title="ETL Audit Log", icon=":material/history:"),
    ],
}

selected_page = st.navigation(pages, position="sidebar")
selected_page.run()
