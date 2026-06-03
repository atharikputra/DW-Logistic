from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine

from etl_process import get_default_db_url
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

st.set_page_config(page_title="Delivery Analytics", layout="wide")


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


def make_sankey(df: pd.DataFrame) -> go.Figure:
    nodes = list(pd.unique(df[["origin_city", "transit_point", "destination_city"]].astype(str).values.ravel("K")))
    node_map = {node: idx for idx, node in enumerate(nodes)}
    sources: list[int] = []
    targets: list[int] = []
    values: list[float] = []
    colors: list[str] = []

    for row in df.itertuples(index=False):
        origin = str(row.origin_city)
        transit = str(row.transit_point)
        destination = str(row.destination_city)
        color = "rgba(214, 69, 65, 0.45)" if float(row.late_rate or 0) >= 25 else "rgba(51, 122, 183, 0.28)"

        sources.extend([node_map[origin], node_map[transit]])
        targets.extend([node_map[transit], node_map[destination]])
        values.extend([float(row.volume), float(row.volume)])
        colors.extend([color, color])

    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(pad=16, thickness=18, line=dict(color="#2f3a45", width=0.4), label=nodes),
                link=dict(source=sources, target=targets, value=values, color=colors),
            )
        ]
    )
    fig.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=430)
    return fig


def build_insights(kpis: pd.Series, branch_df: pd.DataFrame, dest_df: pd.DataFrame, delay_df: pd.DataFrame, route_df: pd.DataFrame) -> list[str]:
    insights: list[str] = []
    if branch_df.empty or int(kpis.get("total_volume", 0) or 0) == 0:
        return ["Belum ada data pada filter ini."]

    worst_branch = branch_df.sort_values(["late_rate", "late_shipments"], ascending=False).iloc[0]
    insights.append(
        f"Prioritas cabang: {worst_branch['branch_city']} memiliki late rate {worst_branch['late_rate']:.1f}% dari {int(worst_branch['volume']):,} pengiriman."
    )

    if not dest_df.empty:
        risky_dest = dest_df.iloc[0]
        insights.append(
            f"Destinasi paling berisiko: {risky_dest['destination_city']} ({risky_dest['destination_province']}) dengan late rate {risky_dest['late_rate']:.1f}%."
        )

    if not delay_df.empty:
        top_reason = delay_df.iloc[0]
        insights.append(
            f"Root cause dominan: {top_reason['reason_category']} muncul pada {int(top_reason['late_shipments']):,} keterlambatan."
        )

    if not route_df.empty:
        top_route = route_df.iloc[0]
        insights.append(
            f"Rute bottleneck: {top_route['origin_city']} -> {top_route['transit_point']} -> {top_route['destination_city']} menyumbang {int(top_route['late_shipments']):,} keterlambatan."
        )

    if float(kpis.get("late_rate", 0) or 0) >= 20:
        insights.append("Aksi manajerial: fokuskan kapasitas hub, armada cadangan, dan validasi alamat pada cabang/rute berisiko tinggi.")
    else:
        insights.append("Aksi manajerial: pertahankan SLA sambil memonitor rute remote dan periode peak season.")

    return insights


engine = get_engine()

st.title("Delivery Performance Analytics")
st.caption("Dashboard eksekutif untuk memonitor SLA, revenue, cabang, destinasi, rute, root cause, dan detail shipment.")

try:
    options = load_options()
    overview = get_warehouse_overview(engine)
except Exception as exc:
    st.error("Data warehouse belum siap. Jalankan ETL dari halaman ETL Operations terlebih dahulu.")
    with st.expander("Detail error"):
        st.exception(exc)
    st.stop()

if int(overview.get("fact_rows", 0) or 0) == 0:
    st.warning("Warehouse belum berisi data. Jalankan Generate Raw Data lalu Run ETL Pipeline dari halaman ETL Operations.")
    st.stop()

min_date = pd.to_datetime(options["min_date"]).date()
max_date = pd.to_datetime(options["max_date"]).date()

with st.sidebar:
    st.header("Filter Managerial")
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

# --- Baris Pertama (3 Metrik Utama) ---
k1, k2, k3 = st.columns(3)
k1.metric("Shipment Volume", fmt_int(kpis["total_volume"]))
k2.metric("On-Time Rate", fmt_pct(kpis["on_time_rate"]))
k3.metric("Late Shipments", fmt_int(kpis["total_late"]))

# Beri sedikit jarak vertikal (opsional, hapus jika terlalu lebar)
st.markdown("<br>", unsafe_allow_html=True) 

# --- Baris Kedua (3 Metrik Finansial & Durasi) ---
k4, k5, k6 = st.columns(3)
k4.metric("Avg Duration", fmt_days(kpis["avg_duration"]))
k5.metric("Avg Cost", fmt_rp(kpis["avg_cost"]))
k6.metric("Revenue", fmt_rp(kpis["total_revenue"]))

st.divider()

with st.container():
    st.subheader("Executive Insights")
    insights = build_insights(kpis, branch_df, destination_df, delay_df, route_df)
    for insight in insights:
        st.write(f"- {insight}")

tab_summary, tab_branch, tab_routes, tab_segments, tab_detail = st.tabs(
    ["Executive Summary", "Branch KPI", "Routes & Root Cause", "Customer & Item", "Shipment Detail"]
)

with tab_summary:
    col_trend, col_service = st.columns([1.5, 1])
    with col_trend:
        st.subheader("Shipment Trend")
        if not trend_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=trend_df["period_start"], y=trend_df["volume"], name="Volume", marker_color="#406e8e"))
            fig.add_trace(
                go.Scatter(
                    x=trend_df["period_start"],
                    y=trend_df["late_rate"],
                    name="Late Rate",
                    yaxis="y2",
                    mode="lines+markers",
                    line=dict(color="#c8504b", width=3),
                )
            )
            fig.update_layout(
                template="plotly_white",
                yaxis=dict(title="Volume"),
                yaxis2=dict(title="Late Rate (%)", overlaying="y", side="right"),
                legend=dict(orientation="h"),
                margin=dict(l=0, r=0, t=20, b=0),
            )
            st.plotly_chart(fig, width="stretch")

    with col_service:
        st.subheader("Service SLA Risk")
        if not service_df.empty:
            fig = px.bar(
                service_df,
                x="service_type",
                y="late_rate",
                color="volume",
                text=service_df["late_rate"].map(lambda value: f"{value:.1f}%"),
                labels={"service_type": "Service", "late_rate": "Late Rate (%)", "volume": "Volume"},
                template="plotly_white",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig, width="stretch")

    col_dest, col_delay = st.columns(2)
    with col_dest:
        st.subheader("Destination Risk")
        if not destination_df.empty:
            fig = px.scatter(
                destination_df,
                x="volume",
                y="late_rate",
                size="late_shipments",
                color="destination_province",
                hover_name="destination_city",
                labels={"volume": "Volume", "late_rate": "Late Rate (%)"},
                template="plotly_white",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig, width="stretch")

    with col_delay:
        st.subheader("Top Delay Reasons")
        if not delay_df.empty:
            fig = px.bar(
                delay_df.sort_values("late_shipments"),
                x="late_shipments",
                y="reason_category",
                orientation="h",
                labels={"late_shipments": "Late Shipments", "reason_category": ""},
                template="plotly_white",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig, width="stretch")
        else:
            st.success("Tidak ada keterlambatan pada filter ini.")

with tab_branch:
    st.subheader("Branch Performance Ranking")
    if not branch_df.empty:
        display_branch = branch_df.copy()
        display_branch["late_rate"] = display_branch["late_rate"].map(lambda value: round(value, 2))
        display_branch["on_time_rate"] = display_branch["on_time_rate"].map(lambda value: round(value, 2))
        display_branch["avg_duration"] = display_branch["avg_duration"].map(lambda value: round(value, 2))
        display_branch["avg_cost"] = display_branch["avg_cost"].map(lambda value: round(value, 0))
        display_branch["revenue"] = display_branch["revenue"].map(lambda value: round(value, 0))
        st.dataframe(display_branch, width="stretch", hide_index=True)

        fig = px.bar(
            branch_df.sort_values("late_rate"),
            x="late_rate",
            y="branch_city",
            orientation="h",
            color="volume",
            labels={"late_rate": "Late Rate (%)", "branch_city": "", "volume": "Volume"},
            template="plotly_white",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, width="stretch")

    st.subheader("Branch vs Root Cause")
    if not delay_branch_df.empty:
        pivot = delay_branch_df.pivot_table(
            index="branch_city",
            columns="reason_category",
            values="late_shipments",
            aggfunc="sum",
            fill_value=0,
        )
        fig = px.imshow(pivot, aspect="auto", labels=dict(x="Reason", y="Branch", color="Late"))
        fig.update_layout(margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, width="stretch")

with tab_routes:
    st.subheader("Route Bottlenecks")
    if not route_df.empty:
        st.dataframe(
            route_df.assign(
                late_rate=route_df["late_rate"].map(lambda value: round(value, 2)),
                avg_duration=route_df["avg_duration"].map(lambda value: round(value, 2)),
            ),
            width="stretch",
            hide_index=True,
        )
        st.plotly_chart(make_sankey(route_df.head(12)), width="stretch")
    else:
        st.info("Tidak ada data rute pada filter ini.")

with tab_segments:
    col_customer, col_item = st.columns(2)
    with col_customer:
        st.subheader("Customer Segment")
        if not customer_df.empty:
            fig = px.bar(
                customer_df,
                x="customer_type",
                y="revenue",
                color="late_rate",
                text=customer_df["late_rate"].map(lambda value: f"{value:.1f}%"),
                labels={"customer_type": "Customer Type", "revenue": "Revenue", "late_rate": "Late Rate (%)"},
                template="plotly_white",
            )
            st.plotly_chart(fig, width="stretch")
            st.dataframe(customer_df, width="stretch", hide_index=True)

    with col_item:
        st.subheader("Item Category Risk")
        if not item_df.empty:
            fig = px.bar(
                item_df.sort_values("late_rate"),
                x="late_rate",
                y="item_category",
                orientation="h",
                color="fragile_shipments",
                labels={"late_rate": "Late Rate (%)", "item_category": "", "fragile_shipments": "Fragile"},
                template="plotly_white",
            )
            st.plotly_chart(fig, width="stretch")
            st.dataframe(item_df, width="stretch", hide_index=True)

with tab_detail:
    st.subheader("Shipment Detail Preview")
    detail_df = get_detail_rows(engine, filters, limit=300)
    st.dataframe(detail_df, width="stretch", hide_index=True)
