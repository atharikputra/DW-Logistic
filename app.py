import streamlit as st

st.set_page_config(page_title="Logistics Data Warehouse", layout="centered")

st.title("Executive Logistics Data Warehouse")
st.caption("Tugas Akhir Data Warehouse - Logistics Delivery Performance")
st.markdown("""
<div >
    <ul>
         <li>Ammara Azwadiena Alfiantie - 140810230073</li>
         <li>Aidan Ismail - 140810230075</li>
         <li>Atharik Putra - 140810230077</li>
    </ul>
</div>
""", unsafe_allow_html=True)
st.markdown(
    """
Project ini memisahkan workflow utama data warehouse menjadi tiga area:

1. **ETL Operations**  
   Simulasi raw data, eksekusi ETL, monitoring run log, dan audit step pipeline.

2. **Delivery Analytics**  
   Dashboard manajerial untuk KPI pengiriman, SLA, cabang, rute, destinasi, customer segment, root cause delay, dan shipment detail.

3. **PostgreSQL Star Schema**  
   Data hasil ETL disimpan dalam tabel fact dan dimension sehingga bisa dianalisis dari banyak sudut bisnis.

Gunakan sidebar Streamlit untuk masuk ke halaman `ETL Operations` atau `Delivery Analytics`.
"""
)

st.info("Urutan demo yang disarankan: Generate Raw Data -> Run ETL Pipeline -> buka Delivery Analytics.")
