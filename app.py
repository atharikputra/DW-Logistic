from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

from generate_data import generate_dataset, RAW_DIR
from etl_process import LogiTrackETL, find_latest_raw_csv, DEFAULT_DB_URL

load_dotenv()

st.set_page_config(
    page_title="Executive Logistics Dashboard",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main {
        background-color: #f8f9fa;
    }

    h1, h2, h3 {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #2c3e50;
    }

    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    div[data-testid="stSidebar"] {
        background-color: #1f2430;
    }

    div[data-testid="stSidebar"] * {
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DB_URL = DEFAULT_DB_URL


@st.cache_resource
def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True)


engine = get_engine()


def run_etl_with_status(csv_path: str | Path):
    log_messages = []
    log_box = st.empty()

    def progress_callback(message: str):
        log_messages.append(message)
        log_box.code("\n".join(log_messages[-20:]), language="text")

    etl = LogiTrackETL(
        file_path=csv_path,
        db_url=DB_URL,
        refresh_warehouse=True,
        progress_callback=progress_callback,
    )

    return etl.run_full_pipeline()


@st.cache_data
def load_analytics():
    query = """
        SELECT
            f.nomor_resi,
            t.date AS shipping_date,
            b.branch_name,
            b.city AS branch_city,
            b.region_province AS branch_province,
            s.service_type,
            s.service_name,
            d.city AS dest_city,
            d.province AS dest_province,
            i.item_category,
            i.weight_kg,
            i.fragile_status,
            r.origin_city,
            r.transit_point,
            r.destination_city_code,
            c.customer_type,
            st.status_name,
            rs.reason_category AS delay_reason_category,
            f.shipping_duration,
            f.shipping_cost,
            f.is_late
        FROM fact_shipping f
        JOIN dim_time t ON f.time_id = t.time_id
        JOIN dim_branch b ON f.branch_id = b.branch_id
        JOIN dim_service s ON f.service_id = s.service_id
        JOIN dim_destination d ON f.destination_id = d.destination_id
        JOIN dim_item i ON f.item_id = i.item_id
        JOIN dim_route r ON f.route_id = r.route_id
        JOIN dim_customer c ON f.customer_id = c.customer_id
        JOIN dim_status st ON f.status_id = st.status_id
        JOIN dim_reason rs ON f.reason_id = rs.reason_id
        ORDER BY t.date;
    """

    try:
        df = pd.read_sql(query, engine)
        if not df.empty:
            df["shipping_date"] = pd.to_datetime(df["shipping_date"])
            df["is_late"] = df["is_late"].astype(bool)
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)


@st.cache_data
def load_etl_logs():
    try:
        run_log = pd.read_sql(
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
                clean_csv,
                error_message
            FROM etl_run_log
            ORDER BY run_id DESC
            LIMIT 10;
            """,
            engine,
        )

        step_log = pd.read_sql(
            """
            SELECT
                s.step_id,
                s.run_id,
                s.step_name,
                s.status,
                s.started_at,
                s.ended_at,
                s.duration_seconds,
                s.rows_processed,
                s.message
            FROM etl_step_log s
            ORDER BY s.step_id DESC
            LIMIT 30;
            """,
            engine,
        )

        return run_log, step_log, None
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), str(e)


with st.sidebar:
    st.header("Pipeline Operations")
    st.caption(f"Raw folder aktif: `{RAW_DIR}`")

    if st.button("Run Data Generation", use_container_width=True):
        try:
            with st.spinner("Generating raw data..."):
                generated_file = generate_dataset()
                st.session_state["latest_raw_file"] = generated_file

            st.success(f"Data berhasil dibuat:")
            st.code(generated_file, language="text")

        except Exception as e:
            st.error("Data generation gagal.")
            st.exception(e)

    if st.button("Run ETL Process", use_container_width=True):
        try:
            csv_file = st.session_state.get("latest_raw_file")

            if not csv_file or not Path(csv_file).exists():
                latest = find_latest_raw_csv(raw_dir=RAW_DIR)
                csv_file = str(latest) if latest else None

            if not csv_file:
                st.error("Tidak ada file CSV di folder raw. Klik Run Data Generation dulu.")
            else:
                with st.spinner("Running ETL process..."):
                    result = run_etl_with_status(csv_file)

                st.cache_data.clear()
                st.success("ETL berhasil. Warehouse sudah diperbarui.")
                st.json(result)

        except Exception as e:
            st.error("ETL gagal.")
            st.exception(e)

    if st.button("Run Full Pipeline", use_container_width=True, type="primary"):
        try:
            with st.spinner("Generating data dan menjalankan ETL..."):
                generated_file = generate_dataset()
                st.session_state["latest_raw_file"] = generated_file
                result = run_etl_with_status(generated_file)

            st.cache_data.clear()
            st.success("Full pipeline berhasil. Data sudah masuk ke PostgreSQL dan dashboard siap.")
            st.json(result)

        except Exception as e:
            st.error("Full pipeline gagal.")
            st.exception(e)

    st.divider()

    raw_files = sorted(
        RAW_DIR.glob("raw_nasional_logistics_data_*.csv"),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )

    st.subheader("Raw Files")
    if raw_files:
        for file in raw_files[:5]:
            st.caption(file.name)
    else:
        st.caption("Belum ada file raw aktif. Kalau ETL sudah selesai, file raw biasanya dipindah ke data_db/processed.")


st.title("Executive Logistics Performance")

tab_dashboard, tab_etl = st.tabs(["Dashboard", "ETL Monitor"])

with tab_dashboard:
    df, error = load_analytics()

    if error:
        st.info("No data available. Jalankan Run Full Pipeline dari sidebar dulu.")
        with st.expander("Detail error query dashboard"):
            st.code(error, language="text")

    elif df.empty:
        st.info("No data available. Jalankan Run Full Pipeline dari sidebar dulu.")

    else:
        total_vol = len(df)
        late_count = int(df["is_late"].sum())
        on_time_rate = (1 - (late_count / total_vol)) * 100 if total_vol else 0
        avg_cost = df["shipping_cost"].mean()
        total_revenue = df["shipping_cost"].sum()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Shipments", f"{total_vol:,}")
        col2.metric("SLA Compliance", f"{on_time_rate:.1f}%")
        col3.metric("Avg. Shipping Cost", f"Rp {avg_cost:,.0f}")
        col4.metric("Total Revenue", f"Rp {total_revenue:,.0f}")

        st.markdown("---")

        r1c1, r1c2 = st.columns(2)

        with r1c1:
            st.subheader("Shipment Volume by Branch City")
            branch_df = (
                df.groupby("branch_city")
                .size()
                .reset_index(name="volume")
                .sort_values("volume", ascending=False)
            )

            fig1 = px.bar(
                branch_df,
                x="branch_city",
                y="volume",
                labels={"branch_city": "Branch City", "volume": "Volume"},
                template="simple_white",
            )
            st.plotly_chart(fig1, use_container_width=True)

        with r1c2:
            st.subheader("SLA Compliance by Service Tier")
            sla_svc = (
                df.groupby("service_type")["is_late"]
                .mean()
                .reset_index()
            )
            sla_svc["on_time_rate"] = (1 - sla_svc["is_late"]) * 100

            fig2 = px.bar(
                sla_svc,
                x="service_type",
                y="on_time_rate",
                labels={"service_type": "Service Type", "on_time_rate": "On-Time %"},
                template="simple_white",
            )
            st.plotly_chart(fig2, use_container_width=True)

        r2c1, r2c2 = st.columns(2)

        with r2c1:
            st.subheader("Delay Root-Cause Analysis")
            delay_df = (
                df[df["is_late"]]
                .groupby("delay_reason_category")
                .size()
                .reset_index(name="frequency")
                .sort_values("frequency", ascending=True)
            )

            if delay_df.empty:
                st.success("Tidak ada keterlambatan pada data saat ini.")
            else:
                fig3 = px.bar(
                    delay_df,
                    y="delay_reason_category",
                    x="frequency",
                    orientation="h",
                    labels={
                        "delay_reason_category": "Delay Reason",
                        "frequency": "Frequency",
                    },
                    template="simple_white",
                )
                st.plotly_chart(fig3, use_container_width=True)

        with r2c2:
            st.subheader("Customer Segmentation Analysis")
            cust_df = (
                df.groupby("customer_type")
                .size()
                .reset_index(name="volume")
            )

            fig4 = px.pie(
                cust_df,
                names="customer_type",
                values="volume",
                hole=0.5,
                template="simple_white",
            )
            st.plotly_chart(fig4, use_container_width=True)

        r3c1, r3c2 = st.columns(2)

        with r3c1:
            st.subheader("Route Bottlenecks by Destination")
            route_df = (
                df[df["is_late"]]
                .groupby("dest_city")
                .size()
                .nlargest(10)
                .reset_index(name="delays")
            )

            if route_df.empty:
                st.success("Tidak ada bottleneck pada data saat ini.")
            else:
                fig5 = px.bar(
                    route_df,
                    x="dest_city",
                    y="delays",
                    labels={"dest_city": "Destination City", "delays": "Delays"},
                    template="simple_white",
                )
                st.plotly_chart(fig5, use_container_width=True)

        with r3c2:
            st.subheader("Item Category Delay Risk")
            item_df = (
                df.groupby("item_category")["is_late"]
                .mean()
                .reset_index()
            )
            item_df["delay_risk"] = item_df["is_late"] * 100

            fig6 = px.bar(
                item_df,
                x="item_category",
                y="delay_risk",
                labels={
                    "item_category": "Item Category",
                    "delay_risk": "Delay Risk (%)",
                },
                template="simple_white",
            )
            st.plotly_chart(fig6, use_container_width=True)

        st.markdown("---")
        st.subheader("Preview Data Warehouse")
        st.dataframe(df.head(100), use_container_width=True)

with tab_etl:
    st.subheader("ETL Run Log")

    run_log, step_log, log_error = load_etl_logs()

    if log_error:
        st.info("ETL log belum tersedia. Jalankan pipeline dulu.")
        with st.expander("Detail error ETL log"):
            st.code(log_error, language="text")
    else:
        st.write("Riwayat eksekusi pipeline:")
        st.dataframe(run_log, use_container_width=True)

        st.write("Detail step ETL:")
        st.dataframe(step_log, use_container_width=True)