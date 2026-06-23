import html as _html

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

from ruleset.etl_process import get_default_db_url
from utils.ui import hero, load_css, metric_card


load_css()


TABLES = [
    "fact_shipping",
    "dim_time",
    "dim_branch",
    "dim_service",
    "dim_destination",
    "dim_item",
    "dim_route",
    "dim_customer",
    "dim_status",
    "dim_reason",
]

TABLE_DESCRIPTIONS = {
    "fact_shipping": "Tabel fakta utama yang menyimpan setiap transaksi pengiriman.",
    "dim_time": "Dimensi waktu dengan atribut tanggal, bulan, kuartal, dan tahun.",
    "dim_branch": "Dimensi cabang operasional beserta lokasi kota dan provinsi.",
    "dim_service": "Dimensi jenis layanan pengiriman (REG, EXP, ECO).",
    "dim_destination": "Dimensi destinasi tujuan pengiriman.",
    "dim_item": "Dimensi kategori barang yang dikirim.",
    "dim_route": "Dimensi rute pengiriman (origin → transit → destination).",
    "dim_customer": "Dimensi informasi pelanggan dan tipe customer.",
    "dim_status": "Dimensi status pengiriman (Delivered, Delayed, Failed, dsb).",
    "dim_reason": "Dimensi alasan keterlambatan atau kegagalan pengiriman.",
}


@st.cache_resource
def get_engine():
    return create_engine(get_default_db_url(), pool_pre_ping=True)


def table_count(engine, table: str) -> int:
    try:
        with engine.connect() as conn:
            return int(conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0)
    except Exception:
        return 0


def preview_table(engine, table: str, limit: int = 100) -> pd.DataFrame:
    return pd.read_sql(text(f"SELECT * FROM {table} LIMIT :limit"), engine, params={"limit": limit})


engine = get_engine()

hero(
    "Data Warehouse Detail",
    "Star schema PostgreSQL untuk menyimpan fakta pengiriman dan dimensi analitik yang dipakai dashboard manajerial.",
    "PostgreSQL Star Schema",
)

# ── Schema Map ──
st.markdown(
    """
    <div class="section-divider">
        <div class="section-divider-icon">🗺️</div>
        <div class="section-divider-text">
            <div class="section-divider-title">Schema Map</div>
            <div class="section-divider-sub">Klik tabel untuk membuka preview data di bawah</div>
        </div>
        <div class="section-divider-line"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "selected_warehouse_table" not in st.session_state:
    st.session_state["selected_warehouse_table"] = "fact_shipping"

st.markdown('<div class="section-label">Fact Table</div>', unsafe_allow_html=True)
fact_cols = st.columns([1, 2, 1])
with fact_cols[1]:
    if st.button("⭐ fact_shipping", key="schema_fact_shipping", width="stretch", type="primary"):
        st.session_state["selected_warehouse_table"] = "fact_shipping"

st.markdown('<div class="section-label">Dimension Tables</div>', unsafe_allow_html=True)
dimension_rows = [
    ["dim_time", "dim_branch", "dim_service", "dim_destination"],
    ["dim_item", "dim_route", "dim_customer", "dim_status", "dim_reason"],
]

for row in dimension_rows:
    cols = st.columns(len(row))
    for col, table in zip(cols, row):
        with col:
            if st.button(table, key=f"schema_{table}", width="stretch"):
                st.session_state["selected_warehouse_table"] = table

# ── Warehouse stats ──
st.markdown(
    """
    <div class="section-divider">
        <div class="section-divider-icon">📊</div>
        <div class="section-divider-text">
            <div class="section-divider-title">Warehouse Tables</div>
            <div class="section-divider-sub">Jumlah baris data di setiap tabel warehouse</div>
        </div>
        <div class="section-divider-line"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

counts = {table: table_count(engine, table) for table in TABLES}
count_cols = st.columns(4)
for idx, table in enumerate(["fact_shipping", "dim_time", "dim_branch", "dim_destination"]):
    with count_cols[idx]:
        metric_card(table, f"{counts.get(table, 0):,}", "rows", "indigo" if table == "fact_shipping" else "gray")

count_cols2 = st.columns(4)
for idx, table in enumerate(["dim_service", "dim_item", "dim_route", "dim_customer"]):
    with count_cols2[idx]:
        metric_card(table, f"{counts.get(table, 0):,}", "rows", "gray")

# ── Table Preview ──
selected_table = st.session_state.get("selected_warehouse_table", "fact_shipping")
if selected_table not in TABLES:
    selected_table = "fact_shipping"
    st.session_state["selected_warehouse_table"] = selected_table
desc = TABLE_DESCRIPTIONS.get(selected_table, "")
try:
    df = preview_table(engine, selected_table)
    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:14px; margin:8px 0 12px;">
            <div style="padding:6px 14px; background:rgba(129,140,248,.14); border:1px solid rgba(129,140,248,.28);
                        border-radius:10px; color:#C7D2FE; font-weight:800; font-size:14px;">
                {_html.escape(selected_table)}
            </div>
            <div style="color:#94A3B8; font-size:13px;">{counts.get(selected_table, 0):,} rows</div>
            <div style="color:#64748B; font-size:12px; margin-left:auto;">{_html.escape(desc)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.dataframe(df, width="stretch", hide_index=True)
except Exception as exc:
    st.markdown(
        '<div class="empty-state">Tabel belum tersedia. Jalankan ETL Pipeline terlebih dahulu.</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Detail error"):
        st.exception(exc)
