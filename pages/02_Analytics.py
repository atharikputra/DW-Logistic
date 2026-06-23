import html as _html

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine

from ruleset.etl_process import get_default_db_url
from ruleset.dss import (
    build_dss_ranking,
    evaluate_kpi_alerts,
    generate_executive_insights,
    get_business_value_df,
    get_delay_mcm,
    risk_label,
    DELAY_REASON_MCM,
    KPI_MONITORS,
)
from utils.ui import hero, load_css, metric_card
from utils.queries import (
    ALL_VALUE,
    get_branch_performance,
    get_customer_segments,
    get_delay_reason_by_branch,
    get_delay_reasons,
    get_destination_risk,
    get_detail_rows,
    get_filter_options,
    get_item_category_performance,
    get_kpis,
    get_route_bottlenecks,
    get_service_performance,
    get_trend_data,
    get_warehouse_overview,
)

load_css()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@st.cache_resource
def get_engine():
    return create_engine(get_default_db_url(), pool_pre_ping=True)


@st.cache_data(show_spinner=False)
def load_options():
    return get_filter_options(get_engine())


def fmt_int(value) -> str:
    return f"{int(value or 0):,}"


def fmt_pct(value) -> str:
    return f"{float(value or 0):.1f}%"


def fmt_rp(value) -> str:
    return f"Rp {float(value or 0):,.0f}"


def fmt_days(value) -> str:
    return f"{float(value or 0):.2f} hari"


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------

CITY_COORDS: dict[str, tuple[float, float]] = {
    "Ambon": (-3.6954, 128.1814),
    "Balikpapan": (-1.2379, 116.8529),
    "Bandung": (-6.9175, 107.6191),
    "Banjarmasin": (-3.3186, 114.5944),
    "Bau-Bau": (-5.4667, 122.6333),
    "Bekasi": (-6.2383, 106.9756),
    "Bukittinggi": (-0.3056, 100.3692),
    "Cilegon": (-6.0025, 106.0111),
    "Denpasar": (-8.6705, 115.2126),
    "Jakarta Pusat": (-6.1865, 106.8341),
    "Jakarta Selatan": (-6.2615, 106.8106),
    "Jambi": (-1.6101, 103.6131),
    "Jayapura": (-2.5916, 140.6690),
    "Kendari": (-3.9985, 122.5120),
    "Kupang": (-10.1772, 123.6070),
    "Makassar": (-5.1477, 119.4327),
    "Malang": (-7.9666, 112.6326),
    "Manado": (1.4748, 124.8421),
    "Mataram": (-8.5833, 116.1167),
    "Merauke": (-8.4991, 140.4049),
    "Medan": (3.5952, 98.6722),
    "Palembang": (-2.9761, 104.7754),
    "Parepare": (-4.0135, 119.6255),
    "Palu": (-0.9003, 119.8780),
    "Pekanbaru": (0.5071, 101.4478),
    "Pontianak": (-0.0263, 109.3425),
    "Sabang": (5.8933, 95.3214),
    "Samarinda": (-0.5022, 117.1536),
    "Semarang": (-6.9667, 110.4167),
    "Surabaya": (-7.2575, 112.7521),
    "Sorong": (-0.8762, 131.2558),
    "Tangerang": (-6.1702, 106.6319),
    "Tangerang Selatan": (-6.2889, 106.7181),
    "Yogyakarta": (-7.7956, 110.3695),
}

HUB_COORDS: dict[str, tuple[float, float]] = {
    "CGK": (-6.1256, 106.6559),
    "SUB": (-7.3798, 112.7869),
    "UPG": (-5.0616, 119.5540),
}


def route_coord(name: str) -> tuple[float, float] | None:
    return HUB_COORDS.get(name) or CITY_COORDS.get(name)


def route_late_rate_thresholds(df: pd.DataFrame) -> tuple[float, float]:
    rates = pd.to_numeric(df.get("late_rate"), errors="coerce").dropna()
    if rates.empty:
        return 12.0, 25.0
    if rates.nunique() < 3:
        value = float(rates.median())
        return max(value - 1, 0), value + 1
    return float(rates.quantile(0.33)), float(rates.quantile(0.66))


def make_route_network_map(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    node_points: dict[str, tuple[float, float, str]] = {}
    low_cut, high_cut = route_late_rate_thresholds(df)

    max_volume = max(float(df["volume"].max() or 1), 1)
    for row in df.itertuples(index=False):
        origin = str(row.origin_city)
        transit = str(row.transit_point)
        destination = str(row.destination_city)
        origin_coord = route_coord(origin)
        destination_coord = route_coord(destination)
        if origin_coord is None or destination_coord is None:
            continue

        route_points = [(origin, origin_coord, "Origin")]
        if transit.upper() != "DIRECT":
            transit_coord = route_coord(transit)
            if transit_coord is not None:
                route_points.append((transit, transit_coord, "Transit"))
        route_points.append((destination, destination_coord, "Destination"))

        late_rate = float(row.late_rate or 0)
        if late_rate <= low_cut:
            line_color = "#22C55E"
        elif late_rate <= high_cut:
            line_color = "#FACC15"
        else:
            line_color = "#EF4444"
        line_width = 1.4 + (float(row.volume or 0) / max_volume) * 5.2
        hover = (
            f"{origin} -> {transit} -> {destination}<br>"
            f"Volume: {int(row.volume):,}<br>"
            f"Late shipments: {int(row.late_shipments):,}<br>"
            f"Late rate: {late_rate:.1f}%"
        )

        fig.add_trace(
            go.Scattergeo(
                lon=[point[1][1] for point in route_points],
                lat=[point[1][0] for point in route_points],
                mode="lines",
                line=dict(width=line_width, color=line_color),
                opacity=0.72,
                hoverinfo="text",
                text=hover,
                showlegend=False,
            )
        )

        for name, coord, role in route_points:
            node_points[name] = (coord[0], coord[1], role)

    if node_points:
        fig.add_trace(
            go.Scattergeo(
                lon=[point[1] for point in node_points.values()],
                lat=[point[0] for point in node_points.values()],
                text=list(node_points.keys()),
                mode="markers+text",
                textposition="top center",
                marker=dict(size=9, color="#A5B4FC", line=dict(width=1, color="#E5E7EB")),
                hoverinfo="text",
                showlegend=False,
            )
        )

    fig.update_geos(
        projection_type="mercator",
        lataxis_range=[-12, 7],
        lonaxis_range=[94, 142],
        showland=True,
        landcolor="#111827",
        showocean=True,
        oceancolor="#020617",
        showcountries=True,
        countrycolor="#334155",
        coastlinecolor="#475569",
        showframe=False,
    )
    fig.update_layout(
        template="plotly_dark",
        height=500,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="#0F172A",
        plot_bgcolor="#0F172A",
        font=dict(family="Inter", color="#E5E7EB"),
    )
    return fig


def polish_chart(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        height=height,
        font=dict(family="Inter", color="#E5E7EB"),
        paper_bgcolor="#0F172A",
        plot_bgcolor="#0F172A",
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#1E293B", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#1E293B", zeroline=False)
    return fig


# ---------------------------------------------------------------------------
# UI component helpers
# ---------------------------------------------------------------------------

def dss_panel(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="dss-panel">
            <div class="dss-title">{_html.escape(title)}</div>
            <div class="dss-copy">{_html.escape(copy)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def dss_summary_card(label: str, value: str, note: str, tone: str = "indigo") -> None:
    st.markdown(
        f"""
        <div class="dss-summary-card {_html.escape(tone)}">
            <div class="dss-summary-label">{_html.escape(label)}</div>
            <div class="dss-summary-value">{_html.escape(value)}</div>
            <div class="dss-summary-note">{_html.escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def formula_box(title: str, copy: str, formula: str) -> None:
    st.markdown(
        f"""
        <div class="formula-box">
            <div class="formula-title">{_html.escape(title)}</div>
            <div class="formula-copy">{_html.escape(copy)}</div>
            <div class="formula-code">{_html.escape(formula)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def formula_grid_box(title: str, copy: str, formulas: list[tuple[str, str]]) -> None:
    formula_items = "\n".join(
        f"""
        <div class="formula-mini-card">
            <div class="formula-mini-label">{_html.escape(label)}</div>
            <div class="formula-mini-code">{_html.escape(formula)}</div>
        </div>
        """
        for label, formula in formulas
    )
    st.markdown(
        f"""
        <div class="formula-box">
            <div class="formula-title">{_html.escape(title)}</div>
            <div class="formula-copy">{_html.escape(copy)}</div>
            <div class="formula-grid">{formula_items}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_indicator(text: str, tone: str = "neutral") -> None:
    st.markdown(
        f'<div class="chart-indicator {_html.escape(tone)}">{_html.escape(text)}</div>',
        unsafe_allow_html=True,
    )


def route_map_legend(df: pd.DataFrame) -> None:
    low_cut, high_cut = route_late_rate_thresholds(df)
    st.markdown(
        f"""
        <div class="route-map-legend">
            <div class="route-legend-item">
                <span class="route-line route-line-green"></span>
                <span>Rendah relatif (&lt;= {_html.escape(fmt_pct(low_cut))})</span>
            </div>
            <div class="route-legend-item">
                <span class="route-line route-line-yellow"></span>
                <span>Sedang ({_html.escape(fmt_pct(low_cut))}-{_html.escape(fmt_pct(high_cut))})</span>
            </div>
            <div class="route-legend-item">
                <span class="route-line route-line-red"></span>
                <span>Tinggi relatif (&gt; {_html.escape(fmt_pct(high_cut))})</span>
            </div>
            <div class="route-legend-item">
                <span class="route-line route-line-thick"></span>
                <span>Garis makin tebal = volume makin besar</span>
            </div>
            <div class="route-legend-item">
                <span class="route-node"></span>
                <span>Node = kota asal, hub, atau tujuan</span>
            </div>
            <div class="route-legend-item">
                <span class="route-code">DIRECT</span>
                <span>tanpa hub transit</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def readout_card(label: str, value: str, note: str, tone: str = "indigo") -> None:
    note_html = (
        f'<div class="readout-note"><span class="badge {tone}">{_html.escape(note)}</span></div>'
        if note
        else ""
    )
    st.markdown(
        f"""
        <div class="readout-card {_html.escape(tone)}">
            <div class="kpi-label">{_html.escape(label)}</div>
            <div class="readout-value">{_html.escape(value)}</div>
            {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_divider(icon: str, title: str, subtitle: str = "") -> None:
    sub_html = f'<div class="section-divider-sub">{_html.escape(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="section-divider">
            <div class="section-divider-icon">{icon}</div>
            <div class="section-divider-text">
                <div class="section-divider-title">{_html.escape(title)}</div>
                {sub_html}
            </div>
            <div class="section-divider-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def exec_insight_card(title: str, body: str, tone: str = "indigo") -> None:
    st.markdown(
        f"""
        <div class="exec-insight {_html.escape(tone)}">
            <div class="exec-insight-title">{_html.escape(title)}</div>
            <div class="exec-insight-body">{_html.escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mcm_card(phase: str, label: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="mcm-card {_html.escape(phase)}">
            <div class="mcm-label">{_html.escape(label)}</div>
            <div class="mcm-body">{_html.escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_monitor_card(
    name: str,
    desc: str,
    threshold: float,
    unit: str,
    triggered: bool,
    alert_text: str,
    actual: float | None = None,
    method: str = "",
) -> None:
    status_class = "triggered" if triggered else ""
    alert_class = "" if triggered else "ok"
    alert_label = alert_text if triggered else "Normal"
    threshold_display = f"{threshold:,.0f}" if threshold >= 100 else f"{threshold:.1f}"
    actual_display = ""
    if actual is not None:
        actual_fmt = f"{actual:,.0f}" if actual >= 100 else f"{actual:.1f}"
        actual_display = f" · Aktual: <strong>{actual_fmt}{unit}</strong>"
    st.markdown(
        f"""
        <div class="kpi-monitor {status_class}">
            <div class="kpi-monitor-header">
                <div class="kpi-monitor-name">{_html.escape(name)}</div>
                <div class="kpi-monitor-alert {alert_class}">{"⚠" if triggered else "✓"} {_html.escape(alert_label)}</div>
            </div>
            <div class="kpi-monitor-desc">{_html.escape(desc)}</div>
            <div class="kpi-monitor-threshold">
                Threshold: <strong>{threshold_display}{_html.escape(unit)}</strong>{actual_display}
            </div>
            <div class="kpi-monitor-threshold">
                Metode: <strong>{_html.escape(method)}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_monitor_grid(alerts: list[dict]) -> None:
    items: list[str] = []
    for alert in alerts:
        triggered = bool(alert["triggered"])
        status_class = "triggered" if triggered else ""
        alert_class = "" if triggered else "ok"
        alert_label = str(alert["alert_text"]) if triggered else "Normal"
        threshold = float(alert["threshold"])
        actual = float(alert["actual"]) if alert["actual"] is not None else None
        unit = str(alert["unit"])
        threshold_display = f"{threshold:,.0f}" if threshold >= 100 else f"{threshold:.1f}"
        actual_display = ""
        if actual is not None:
            actual_fmt = f"{actual:,.0f}" if actual >= 100 else f"{actual:.1f}"
            actual_display = f" &middot; Aktual: <strong>{actual_fmt}{_html.escape(unit)}</strong>"
        items.append(
            f'<div class="kpi-monitor {status_class}">'
            f'<div class="kpi-monitor-header">'
            f'<div class="kpi-monitor-name">{_html.escape(str(alert["kpi"]))}</div>'
            f'<div class="kpi-monitor-alert {alert_class}">{_html.escape(alert_label)}</div>'
            f'</div>'
            f'<div class="kpi-monitor-desc">{_html.escape(str(alert["description"]))}</div>'
            f'<div class="kpi-monitor-threshold">'
            f'Threshold: <strong>{threshold_display}{_html.escape(unit)}</strong>{actual_display}'
            f'</div>'
            f'<div class="kpi-monitor-threshold">'
            f'Metode: <strong>{_html.escape(str(alert["method"]))}</strong>'
            f'</div>'
            f'</div>'
        )
    st.markdown(
        f'<div class="kpi-monitor-grid">{"".join(items)}</div>',
        unsafe_allow_html=True,
    )


def takeaway_banner(text: str) -> None:
    st.markdown(
        f"""
        <div class="takeaway-banner">
            <div class="takeaway-label">🔑 Key Takeaway</div>
            <div class="takeaway-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_business_value_table(bv_df: pd.DataFrame) -> None:
    rows_html = ""
    for row in bv_df.itertuples(index=False):
        rows_html += (
            "<tr>"
            f'<td class="bv-aspek">{_html.escape(str(row.aspek))}</td>'
            f'<td class="bv-before">{_html.escape(str(row.before))}</td>'
            f'<td class="bv-after">{_html.escape(str(row.after))}</td>'
            f'<td class="bv-impact">{_html.escape(str(row.impact))}</td>'
            "</tr>"
        )
    st.markdown(
        f"""
        <div class="bv-table-wrap">
            <table class="bv-table">
                <thead>
                    <tr>
                        <th>Aspek</th>
                        <th>Before</th>
                        <th>After</th>
                        <th>Business Value Impact</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Page layout
# ═══════════════════════════════════════════════════════════════════════════

engine = get_engine()

hero(
    "Delivery Performance Analytics",
    "Dashboard eksekutif untuk memonitor SLA, revenue, performa cabang, risiko destinasi, bottleneck rute, customer segment, dan root cause delay.",
    "Managerial Dashboard",
)

try:
    options = load_options()
    overview = get_warehouse_overview(engine)
except Exception as exc:
    st.markdown(
        '<div class="empty-state">Data warehouse belum siap. Jalankan Generate Daily Batch dan Run ETL Pipeline dari halaman Data Operations.</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Detail error"):
        st.exception(exc)
    st.stop()

if int(overview.get("fact_rows", 0) or 0) == 0:
    st.markdown(
        '<div class="empty-state">Warehouse belum berisi data. Jalankan Generate Daily Batch lalu Run ETL Pipeline dari halaman Data Operations.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

min_date = pd.to_datetime(options["min_date"]).date()
max_date = pd.to_datetime(options["max_date"]).date()

with st.sidebar:
    st.header("Managerial Filters")
    grain = st.segmented_control("Time grain", options=["day", "week", "month"], default="month")
    selected_range = st.date_input("Rentang tanggal", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        date_from, date_to = selected_range
    else:
        date_from, date_to = min_date, max_date

    selected_branch = st.selectbox("Cabang asal", [ALL_VALUE] + options["branches"])
    selected_service = st.selectbox("Layanan", [ALL_VALUE] + options["services"])
    selected_destination = st.selectbox("Destinasi", [ALL_VALUE] + options["destinations"])
    selected_customer = st.selectbox("Customer type", [ALL_VALUE] + options["customer_types"])
    selected_item = st.selectbox("Kategori barang", [ALL_VALUE] + options["item_categories"])

filters = {
    "date_from": date_from,
    "date_to": date_to,
    "branch": selected_branch,
    "service": selected_service,
    "destination": selected_destination,
    "customer_type": selected_customer,
    "item_category": selected_item,
}

kpis = get_kpis(engine, filters)
if kpis is None or int(kpis.get("total_volume", 0) or 0) == 0:
    st.warning("Tidak ada data untuk filter yang dipilih. Longgarkan rentang tanggal atau filter dimensi.")
    st.stop()

trend_df = get_trend_data(engine, filters, grain=grain)
branch_df = get_branch_performance(engine, filters)
service_df = get_service_performance(engine, filters)
destination_df = get_destination_risk(engine, filters, limit=15)
delay_df = get_delay_reasons(engine, filters, limit=10)
delay_branch_df = get_delay_reason_by_branch(engine, filters)
route_df = get_route_bottlenecks(engine, filters, limit=20)
customer_df = get_customer_segments(engine, filters)
item_df = get_item_category_performance(engine, filters)

late_rate = float(kpis.get("late_rate", 0) or 0)
on_time_rate = float(kpis.get("on_time_rate", 0) or 0)
avg_cost = float(kpis.get("avg_cost", 0) or 0)
avg_duration = float(kpis.get("avg_duration", 0) or 0)
late_tone = "green" if late_rate < 12 else "yellow" if late_rate < 25 else "red"
on_time_tone = "green" if on_time_rate >= 90 else "yellow" if on_time_rate >= 75 else "red"
dss_ranking = build_dss_ranking(branch_df, destination_df, route_df)
top_dss = dss_ranking.iloc[0] if not dss_ranking.empty else None
decision_status, decision_tone_color = risk_label(
    float(top_dss["risk_score"]) if top_dss is not None else late_rate,
    dss_ranking["risk_score"] if not dss_ranking.empty else None,
)
worst_branch = branch_df.sort_values(["late_rate", "late_shipments"], ascending=False).iloc[0] if not branch_df.empty else None
risky_dest = destination_df.iloc[0] if not destination_df.empty else None
top_reason = delay_df.iloc[0] if not delay_df.empty else None
top_route = route_df.iloc[0] if not route_df.empty else None

# ── Top KPI cards ──
k1, k2, k3 = st.columns(3)
with k1:
    metric_card("Shipment Volume", fmt_int(kpis["total_volume"]), "filtered shipments", "indigo")
with k2:
    metric_card("On-Time Rate", fmt_pct(kpis["on_time_rate"]), "SLA health", on_time_tone)
with k3:
    metric_card("Late Shipments", fmt_int(kpis["total_late"]), f"{fmt_pct(kpis['late_rate'])} late rate", late_tone)

k4, k5, k6 = st.columns(3)
with k4:
    metric_card("Avg Duration", fmt_days(kpis["avg_duration"]), "delivery speed", "gray")
with k5:
    metric_card("Avg Cost", fmt_rp(kpis["avg_cost"]), "per shipment", "yellow")
with k6:
    metric_card("Revenue", fmt_rp(kpis["total_revenue"]), "gross shipping cost", "green")

st.divider()
st.markdown('<div class="dashboard-heading">Analytical Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="dashboard-subcopy">
        Dashboard ini dibuat supaya pembaca bisa langsung melihat kondisi pengiriman, area yang perlu diprioritaskan,
        penyebab keterlambatan, dan rekomendasi tindakan berbasis data warehouse.
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Operational Readout")
readout_cols = st.columns(4)
with readout_cols[0]:
    readout_card("Current SLA", f"{on_time_rate:.1f}%", "", on_time_tone)
with readout_cols[1]:
    readout_card(
        "Priority Area",
        str(top_dss["entity"]) if top_dss is not None else "-",
        "",
        decision_tone_color,
    )
with readout_cols[2]:
    readout_card(
        "Main Cause",
        str(top_reason["reason_category"]) if top_reason is not None else "-",
        "",
        "yellow",
    )
with readout_cols[3]:
    readout_card("Best Next Step", decision_status, "", decision_tone_color)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# Tabs
# ═══════════════════════════════════════════════════════════════════════════

tab_summary, tab_branch, tab_routes, tab_segments, tab_dss, tab_detail = st.tabs(
    ["Executive Summary", "Branch KPI", "Routes & Root Cause", "Customer & Item", "DSS Recommendation", "Shipment Detail"]
)

# ═══════════════════════════════════════════════════════════════════════════
# TAB: Executive Summary (enhanced with insights, descriptions, KPI monitoring)
# ═══════════════════════════════════════════════════════════════════════════

with tab_summary:

    # ── Executive Insights for Managerial View ──
    section_divider("📊", "Executive Insights", "Ringkasan kondisi operasional untuk pengambilan keputusan manajerial")

    exec_insights = generate_executive_insights(
        kpis=kpis,
        late_rate=late_rate,
        on_time_rate=on_time_rate,
        top_reason=top_reason,
        top_route=top_route,
        worst_branch=worst_branch,
        risky_dest=risky_dest,
        dss_ranking=dss_ranking,
    )

    insight_cols = st.columns(2)
    for idx, insight in enumerate(exec_insights):
        with insight_cols[idx % 2]:
            exec_insight_card(insight["title"], insight["body"], insight["tone"])

    # ── Charts ──
    section_divider("📈", "Trend & Distribusi", "Visualisasi tren volume pengiriman dan distribusi layanan")

    col_trend, col_service = st.columns([1.5, 1])
    with col_trend:
        st.subheader("Shipment Trend")
        chart_indicator("Volume tinggi bagus; late rate tinggi buruk.", "watch")
        if not trend_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=trend_df["period_start"], y=trend_df["volume"], name="Volume", marker_color="#4F46E5"))
            fig.add_trace(
                go.Scatter(
                    x=trend_df["period_start"],
                    y=trend_df["late_rate"],
                    name="Late Rate",
                    yaxis="y2",
                    mode="lines+markers",
                    line=dict(color="#DC2626", width=3),
                )
            )
            fig.update_layout(
                yaxis=dict(title="Volume"),
                yaxis2=dict(title="Late Rate (%)", overlaying="y", side="right"),
            )
            st.plotly_chart(polish_chart(fig, height=410), width="stretch")

    with col_service:
        st.subheader("Service SLA Risk")
        chart_indicator("Lower late rate is better.", "bad")
        if not service_df.empty:
            service_plot = service_df.sort_values("late_rate", ascending=False)
            fig = px.bar(
                service_plot,
                x="service_type",
                y="late_rate",
                color="late_rate",
                color_continuous_scale=["#16A34A", "#EAB308", "#DC2626"],
                text=service_plot["late_rate"].map(lambda value: f"{value:.1f}%"),
                labels={"service_type": "Service", "late_rate": "Late Rate (%)", "volume": "Volume"},
            )
            st.plotly_chart(polish_chart(fig, height=410), width="stretch")

    col_dest, col_delay = st.columns(2)
    with col_dest:
        st.subheader("Destination Risk")
        chart_indicator("Kanan/atas dan bubble besar = risiko lebih tinggi.", "bad")
        if not destination_df.empty:
            fig = px.scatter(
                destination_df,
                x="volume",
                y="late_rate",
                size="late_shipments",
                color="destination_province",
                hover_name="destination_city",
                labels={"volume": "Volume", "late_rate": "Late Rate (%)"},
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            st.plotly_chart(polish_chart(fig), width="stretch")

    with col_delay:
        st.subheader("Top Delay Reasons")
        chart_indicator("Slice lebih besar = penyebab delay lebih dominan.", "watch")
        if not delay_df.empty:
            fig = px.pie(
                delay_df,
                values="late_shipments",
                names="reason_category",
                hole=0.52,
                color_discrete_sequence=["#DC2626", "#EAB308", "#4F46E5", "#16A34A", "#64748B"],
            )
            st.plotly_chart(polish_chart(fig), width="stretch")
        else:
            st.success("Tidak ada keterlambatan pada filter ini.")

    # ── Delay reason actionable cards ──
    if not delay_df.empty:
        section_divider("🎯", "Actionable Root Cause Analysis", "Setiap penyebab delay disertai rekomendasi aksi menggunakan framework Manage-Control-Measure")

        for row in delay_df.head(5).itertuples(index=False):
            reason_name = str(row.reason_category)
            reason_count = int(row.late_shipments)
            mcm = get_delay_mcm(reason_name)

            st.markdown(
                f"""
                <div class="reason-cause-card">
                    <div class="reason-cause-header">
                        <div class="reason-cause-name">🔴 {_html.escape(reason_name)}</div>
                        <div class="reason-cause-count">{reason_count:,} kasus keterlambatan</div>
                    </div>
                    <div class="reason-cause-action">
                        <strong>Manage:</strong> {_html.escape(mcm['manage'].split('.')[0])}.<br>
                        <strong>Control:</strong> {_html.escape(mcm['control'].split('.')[0])}.<br>
                        <strong>Measure:</strong> {_html.escape(mcm['measure'].split('.')[0])}.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════
# TAB: Branch KPI
# ═══════════════════════════════════════════════════════════════════════════

with tab_branch:
    section_divider("🏢", "Branch Performance", "Analisis performa tiap cabang operasional beserta area dengan risiko tertinggi")
    
    if not branch_df.empty:
        worst_b = worst_branch
        best_b = branch_df.sort_values(["on_time_rate", "volume"], ascending=False).iloc[0]
        
        b_cols = st.columns(2)
        with b_cols[0]:
            readout_card("Top Performer", str(best_b["branch_city"]), f"{best_b['on_time_rate']:.1f}% on-time", "green")
        with b_cols[1]:
            readout_card("Highest Risk", str(worst_b["branch_city"]) if worst_b is not None else "-", f"{worst_b['late_rate']:.1f}% late rate" if worst_b is not None else "-", "red" if (worst_b is not None and worst_b["late_rate"] >= 25) else "yellow")
            
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    if not branch_df.empty:
        display_branch = branch_df.copy()
        display_branch["late_rate"] = display_branch["late_rate"].map(lambda value: round(value, 2))
        display_branch["on_time_rate"] = display_branch["on_time_rate"].map(lambda value: round(value, 2))
        display_branch["avg_duration"] = display_branch["avg_duration"].map(lambda value: round(value, 2))
        display_branch["avg_cost"] = display_branch["avg_cost"].map(lambda value: round(value, 0))
        display_branch["revenue"] = display_branch["revenue"].map(lambda value: round(value, 0))
        chart_indicator("Tabel: on-time rate/revenue tinggi bagus; late rate/duration/cost tinggi perlu diwaspadai.", "watch")
        st.dataframe(display_branch, width="stretch", hide_index=True)

        fig = px.bar(
            branch_df.sort_values("late_rate"),
            x="late_rate",
            y="branch_city",
            orientation="h",
            color="volume",
            labels={"late_rate": "Late Rate (%)", "branch_city": "", "volume": "Volume"},
            color_continuous_scale=["#16A34A", "#EAB308", "#DC2626"],
        )
        chart_indicator("Lower late rate is better; bar panjang berarti cabang lebih berisiko.", "bad")
        st.plotly_chart(polish_chart(fig, height=430), width="stretch")

    section_divider("🔍", "Branch vs Root Cause", "Pemetaan penyebab delay paling umum di masing-masing cabang")
    if not delay_branch_df.empty:
        pivot = delay_branch_df.pivot_table(
            index="branch_city",
            columns="reason_category",
            values="late_shipments",
            aggfunc="sum",
            fill_value=0,
        )
        fig = px.imshow(pivot, aspect="auto", labels=dict(x="Reason", y="Branch", color="Late"), color_continuous_scale="Reds")
        chart_indicator("Warna lebih pekat = jumlah delay lebih tinggi.", "bad")
        st.plotly_chart(polish_chart(fig, height=430), width="stretch")


# ═══════════════════════════════════════════════════════════════════════════
# TAB: Routes & Root Cause
# ═══════════════════════════════════════════════════════════════════════════

with tab_routes:
    section_divider("🛣️", "Route Bottlenecks", "Pemetaan aliran rute dari asal hingga tujuan yang menyumbang keterlambatan terbesar")
    
    if top_route is not None:
        takeaway_banner(
            f"Rute paling berisiko adalah <strong>{top_route['origin_city']} → {top_route['transit_point']} → {top_route['destination_city']}</strong> "
            f"dengan {int(top_route['late_shipments']):,} keterlambatan ({top_route['late_rate']:.1f}% dari total volume di rute ini)."
        )
    if not route_df.empty:
        chart_indicator("Tabel: late shipments, late rate, dan duration tinggi = bottleneck lebih kuat.", "bad")
        st.dataframe(
            route_df.assign(
                late_rate=route_df["late_rate"].map(lambda value: round(value, 2)),
                avg_duration=route_df["avg_duration"].map(lambda value: round(value, 2)),
            ),
            width="stretch",
            hide_index=True,
        )
        chart_indicator("Peta membaca rute dari origin ke transit/hub lalu destination. Arah detail rute bisa dilihat dari hover.", "watch")
        mapped_routes = route_df.head(20)
        route_map_legend(mapped_routes)
        st.plotly_chart(make_route_network_map(mapped_routes), width="stretch")
    else:
        st.info("Tidak ada data rute pada filter ini.")


# ═══════════════════════════════════════════════════════════════════════════
# TAB: Customer & Item
# ═══════════════════════════════════════════════════════════════════════════

with tab_segments:
    section_divider("👥", "Customer & Item Segments", "Analisis risiko SLA berdasarkan profil pelanggan dan tingkat kerentanan barang")

    col_customer, col_item = st.columns(2)
    with col_customer:
        st.markdown('<div class="dashboard-heading" style="font-size:18px; margin-bottom:12px; color:#F8FAFC; font-weight:700;">Customer Segment</div>', unsafe_allow_html=True)
        chart_indicator("Revenue tinggi bagus; warna merah berarti late rate lebih tinggi.", "watch")
        if not customer_df.empty:
            fig = px.bar(
                customer_df,
                x="customer_type",
                y="revenue",
                color="late_rate",
                text=customer_df["late_rate"].map(lambda value: f"{value:.1f}%"),
                labels={"customer_type": "Customer Type", "revenue": "Revenue", "late_rate": "Late Rate (%)"},
                color_continuous_scale=["#16A34A", "#EAB308", "#DC2626"],
            )
            st.plotly_chart(polish_chart(fig), width="stretch")
            st.dataframe(customer_df, width="stretch", hide_index=True)

    with col_item:
        st.markdown('<div class="dashboard-heading" style="font-size:18px; margin-bottom:12px; color:#F8FAFC; font-weight:700;">Item Category Risk</div>', unsafe_allow_html=True)
        chart_indicator("Lower late rate is better; fragile shipment tinggi perlu diawasi.", "bad")
        if not item_df.empty:
            fig = px.bar(
                item_df.sort_values("late_rate"),
                x="late_rate",
                y="item_category",
                orientation="h",
                color="fragile_shipments",
                labels={"late_rate": "Late Rate (%)", "item_category": "", "fragile_shipments": "Fragile"},
                color_continuous_scale=["#16A34A", "#EAB308", "#DC2626"],
            )
            st.plotly_chart(polish_chart(fig), width="stretch")
            st.dataframe(item_df, width="stretch", hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB: DSS Recommendation (enhanced with MCM, KPI Monitoring, Business Value)
# ═══════════════════════════════════════════════════════════════════════════

with tab_dss:

    # ── Top KPI indicators ──
    section_divider("🧠", "Decision Support Recommendation", "Rangkuman sistem rekomendasi untuk menentukan langkah strategis")
    top_risk_score = float(top_dss["risk_score"]) if top_dss is not None else 0.0
    top_risk_entity = f"{top_dss['area']} - {top_dss['entity']}" if top_dss is not None else "Belum ada ranking"
    main_cause = str(top_reason["reason_category"]) if top_reason is not None else "-"
    main_cause_note = f"{int(top_reason['late_shipments']):,} kasus delay" if top_reason is not None else "Belum ada delay"

    c1, c2, c3 = st.columns(3)
    with c1:
        dss_summary_card("DSS Status", decision_status, "Label dari posisi risk score terhadap distribusi ranking aktif.", decision_tone_color)
    with c2:
        dss_summary_card("Top Risk Score", f"{top_risk_score:.1f}", top_risk_entity, decision_tone_color)
    with c3:
        dss_summary_card("Main Cause", main_cause, main_cause_note, "yellow")

    formula_box(
        "Rumus Risk Score",
        "Skor risiko dihitung dari metrik warehouse pada filter aktif. Late shipments dan duration dinormalisasi terhadap nilai maksimum pada kelompok data yang sama.",
        "risk_score = (late_rate x 0.50) + (normalized_late_shipments x 100 x 0.30) + (normalized_avg_duration x 100 x 0.20)",
    )
    formula_box(
        "Rumus Status DSS",
        "Status Critical / At Risk / Controlled tidak memakai angka manual. Status ditentukan dari posisi score terhadap distribusi Risk Ranking aktif.",
        "Critical >= Q3 risk_score; At Risk >= median risk_score; Controlled < median risk_score",
    )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # ── Priority & Route panels ──
    panel_cols = st.columns(2)
    with panel_cols[0]:
        if top_dss is not None:
            priority_copy = (
                f"Prioritas utama adalah {top_dss['area']} {top_dss['entity']} dengan risk score "
                f"{float(top_dss['risk_score']):.1f}. Skor ini dihitung dari late rate, jumlah keterlambatan, "
                "dan rata-rata durasi pengiriman."
            )
        else:
            priority_copy = "Belum ada data cukup untuk menentukan prioritas. Jalankan ETL dan longgarkan filter bila dashboard kosong."
        dss_panel("Prioritas Keputusan", priority_copy)
    with panel_cols[1]:
        route_copy = (
            f"Rute paling perlu diawasi adalah {top_route['origin_city']} -> {top_route['transit_point']} -> {top_route['destination_city']} karena menyumbang {int(top_route['late_shipments']):,} keterlambatan."
            if top_route is not None
            else "Belum ada rute bottleneck pada filter ini."
        )
        dss_panel("Rute dan Hub yang Perlu Diawasi", route_copy)

    panel_cols = st.columns(2)
    with panel_cols[0]:
        dest_copy = (
            f"Destinasi {risky_dest['destination_city']} ({risky_dest['destination_province']}) memiliki late rate {risky_dest['late_rate']:.1f}%. Perlu validasi kapasitas last-mile, estimasi SLA, dan kesiapan mitra lokal."
            if risky_dest is not None
            else "Belum ada destinasi berisiko pada filter ini."
        )
        dss_panel("Destinasi Berisiko", dest_copy)
    with panel_cols[1]:
        cause_copy = (
            f"Root cause dominan adalah {top_reason['reason_category']} dengan {int(top_reason['late_shipments']):,} kasus. Keputusan terbaik adalah mengarahkan tindakan pada penyebab ini dulu sebelum memperluas perbaikan."
            if top_reason is not None
            else "Belum ada root cause delay pada filter ini."
        )
        dss_panel("Root Cause Utama", cause_copy)

    # ── Manage-Control-Measure Framework per Root Cause ──
    section_divider("🔧", "Manage-Control-Measure Framework", "Rekomendasi aksi terstruktur berdasarkan root cause delay terbesar")

    if top_reason is not None:
        top_reason_name = str(top_reason["reason_category"])
        top_mcm = get_delay_mcm(top_reason_name)

        st.markdown(
            f"""
            <div class="takeaway-banner">
                <div class="takeaway-label">🎯 Focus Area</div>
                <div class="takeaway-text">
                    Root cause dominan adalah <strong>{_html.escape(top_reason_name)}</strong> dengan
                    <strong>{int(top_reason['late_shipments']):,}</strong> kasus keterlambatan.
                    Berikut adalah rekomendasi aksi terstruktur menggunakan framework Manage-Control-Measure.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        mcm_cols = st.columns(3)
        with mcm_cols[0]:
            mcm_card("manage", "🔵 Manage", top_mcm["manage"])
        with mcm_cols[1]:
            mcm_card("control", "🟡 Control", top_mcm["control"])
        with mcm_cols[2]:
            mcm_card("measure", "🟢 Measure", top_mcm["measure"])

        # Show MCM for 2nd top reason if available
        if len(delay_df) > 1:
            second_reason = delay_df.iloc[1]
            second_reason_name = str(second_reason["reason_category"])
            second_mcm = get_delay_mcm(second_reason_name)
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            st.caption(f"Root cause ke-2: {second_reason_name} ({int(second_reason['late_shipments']):,} kasus)")
            mcm_cols2 = st.columns(3)
            with mcm_cols2[0]:
                mcm_card("manage", "🔵 Manage", second_mcm["manage"])
            with mcm_cols2[1]:
                mcm_card("control", "🟡 Control", second_mcm["control"])
            with mcm_cols2[2]:
                mcm_card("measure", "🟢 Measure", second_mcm["measure"])

    else:
        st.info("Belum ada root cause delay untuk ditampilkan. Jalankan ETL dan pastikan data tersedia.")

    # ── KPI Monitoring System ──
    section_divider("📡", "KPI Monitoring System", "Monitoring indikator kinerja utama dengan alert threshold")
    formula_grid_box(
        "Rumus Threshold KPI",
        "Threshold dihitung dari distribusi data warehouse yang sedang aktif setelah filter. Q1 dipakai untuk batas bawah performa, Q3 untuk batas atas risiko, dan mean + standar deviasi untuk mendeteksi penyebab delay yang terlalu dominan.",
        [
            ("On-Time Delivery", "on_time_threshold = Q1(branch.on_time_rate)"),
            ("Late Shipment", "late_shipment_threshold = Q3(branch/service/destination/route.late_rate)"),
            ("Average Duration", "duration_threshold = Q3(branch/destination/route.avg_duration)"),
            ("Cost per Shipment", "cost_threshold = Q3(branch/customer.avg_cost)"),
            ("Root Cause", "root_cause_threshold = mean(reason.late_shipments) + std(reason.late_shipments)"),
        ],
    )

    kpi_alerts = evaluate_kpi_alerts(
        kpis,
        on_time_rate,
        avg_cost,
        avg_duration,
        branch_df=branch_df,
        service_df=service_df,
        destination_df=destination_df,
        route_df=route_df,
        customer_df=customer_df,
        delay_df=delay_df,
    )
    kpi_monitor_grid(kpi_alerts)

    # ── Risk Ranking ──
    section_divider("🏆", "Risk Ranking", "Peringkat area (cabang, destinasi, rute) berdasarkan kombinasi risk score")
    if not dss_ranking.empty:
        ranking_display = dss_ranking.copy()
        ranking_display["late_rate"] = ranking_display["late_rate"].map(lambda value: round(value, 2))
        ranking_display["avg_duration"] = ranking_display["avg_duration"].map(lambda value: round(value, 2))
        ranking_display["risk_score"] = ranking_display["risk_score"].map(lambda value: round(value, 1))
        ranking_display = ranking_display.rename(
            columns={
                "area": "Area",
                "entity": "Entity",
                "volume": "Volume",
                "late_shipments": "Late Shipments",
                "late_rate": "Late Rate (%)",
                "avg_duration": "Avg Duration",
                "risk_score": "Risk Score",
                "priority": "Priority",
            }
        )
        chart_indicator("Higher risk score = prioritas DSS lebih tinggi.", "bad")
        st.dataframe(ranking_display, width="stretch", hide_index=True)
    else:
        st.info("Risk ranking belum tersedia untuk filter ini.")

    # ── Best Action Plan ──
    section_divider("✅", "Best Action Plan", "Strategi mitigasi utama berdasarkan kondisi operasional saat ini")
    if late_rate >= 25:
        action_plan = [
            ("Escalate", "Aktifkan escalation mode untuk cabang/rute prioritas selama periode filter."),
            ("Add Capacity", "Tambah kapasitas hub atau armada cadangan pada rute bottleneck."),
            ("Daily Audit", "Audit root cause dominan harian sampai late rate turun di bawah 20%."),
        ]
    elif late_rate >= 12:
        action_plan = [
            ("Monitor", "Fokuskan monitoring pada cabang dan destinasi dengan late rate tertinggi."),
            ("Prevent", "Lakukan preventive capacity planning untuk periode volume tinggi."),
            ("Improve", "Perbaiki proses yang terkait root cause dominan sebelum menjadi masalah sistemik."),
        ]
    else:
        action_plan = [
            ("Maintain", "Pertahankan pola operasi saat ini karena SLA relatif sehat."),
            ("Watchlist", "Monitor rute remote dan peak season sebagai early warning."),
            ("Benchmark", "Gunakan branch terbaik sebagai benchmark SOP untuk cabang lain."),
        ]

    action_cols = st.columns(3)
    for col, (title, action) in zip(action_cols, action_plan):
        with col:
            dss_panel(title, action)

    # ── Business Value Table ──
    section_divider("💎", "Business Value", "Perbandingan kondisi sebelum dan sesudah implementasi Data Warehouse")

    takeaway_banner(
        "Smart Warehouse mengubah perbaikan operasional melalui <strong>proses yang lebih cepat, akurat, dan juga terkendali</strong>. "
        "Terlihat pada <strong>penurunan lead time</strong>, berkurangnya risiko error, "
        "<strong>keputusan yang responsif</strong>, dan <strong>cashflow yang baik</strong>."
    )

    bv_df = get_business_value_df()
    render_business_value_table(bv_df)


# ═══════════════════════════════════════════════════════════════════════════
# TAB: Shipment Detail
# ═══════════════════════════════════════════════════════════════════════════

with tab_detail:
    section_divider("🔎", "Shipment Detail Preview", "Cuplikan 300 baris pertama dari data transaksi dengan filter yang aktif")
    detail_df = get_detail_rows(engine, filters, limit=300)
    chart_indicator("Detail table dipakai untuk audit baris transaksi; bukan ranking performa.", "neutral")
    st.dataframe(detail_df, width="stretch", hide_index=True)
