import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import logging

# --- CONFIGURATION ---
DB_URL = 'postgresql://admin:admin123@localhost:5432/logitrack_dw'
FILE_PATH = 'raw_nasional_logistics_data.csv'
OUTPUT_CSV = 'Logistics_Clean_Final.csv'

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LogiTrackETL:
    def __init__(self, file_path, db_url):
        self.file_path = file_path
        self.engine = create_engine(db_url)
        self.df = None

    # ==========================================
    # 1. EXTRACT STAGE
    # ==========================================
    def extract(self):
        logging.info(f"🔍 Extracting data from {self.file_path}...")
        self.df = pd.read_csv(self.file_path)
        logging.info(f"✅ Extraction complete. Total rows: {len(self.df)}")

    # ==========================================
    # 2. TRANSFORM STAGE (Cleaning & Normalization)
    # ==========================================
    def _normalize_text(self, text_col):
        return text_col.astype(str).str.strip().str.title()

    def transform(self):
        logging.info("🛠️ Starting Transformation & Cleaning...")
        
        # A. Handling Dates
        self.df['Shipping_Date'] = pd.to_datetime(self.df['Shipping_Date'])
        
        # B. Normalizing Text
        text_columns = ['Branch_Name', 'Item_Category', 'Customer_Name', 'Shipping_Status', 'Dest_City', 'Service_Name']
        for col in text_columns:
            self.df[col] = self._normalize_text(self.df[col])

        # C. Handling Missing Values
        self.df['Transit_Point'] = self.df['Transit_Point'].fillna('Direct').replace('Nan', 'Direct')
        self.df['Delay_Reason_Category'] = self.df['Delay_Reason_Category'].fillna('No Delay')
        self.df['Dest_ZIP'] = self.df['Dest_ZIP'].fillna(0).astype(int).astype(str).str.zfill(5)

        # D. Data Validation
        self.df = self.df.dropna(subset=['Nomor_Resi'])
        
        # E. Feature Engineering (Dim_Time)
        self.df['day'] = self.df['Shipping_Date'].dt.day
        self.df['month'] = self.df['Shipping_Date'].dt.month
        self.df['year'] = self.df['Shipping_Date'].dt.year
        self.df['quarter'] = self.df['Shipping_Date'].dt.quarter
        
        logging.info("✨ Transformation & Cleaning complete.")

    # ==========================================
    # 3. LOAD STAGE (Filling the Star Schema)
    # ==========================================
    def load_dimensions(self):
        logging.info("📥 Loading all Dimension Tables...")

        def sync_dim(df_dim, table_name):
            df_dim = df_dim.drop_duplicates()
            # Gunakan chunksize agar stabil saat upload dimensi
            df_dim.to_sql(table_name, self.engine, if_exists='append', index=False, chunksize=1000)
            logging.info(f"   - Table {table_name} sync successful.")

        sync_dim(self.df[['Branch_Code', 'Branch_Name', 'Branch_City', 'Branch_Province']]
                 .rename(columns={'Branch_Code': 'branch_code', 'Branch_Name': 'branch_name', 
                                  'Branch_City': 'city', 'Branch_Province': 'region_province'}), 'dim_branch')

        sync_dim(self.df[['Item_Name', 'Item_Category', 'Weight_Kg', 'Fragile_Status']]
                 .rename(columns={'Item_Name': 'item_name', 'Item_Category': 'item_category', 
                                  'Weight_Kg': 'weight_kg', 'Fragile_Status': 'fragile_status'}), 'dim_item')

        dim_time = self.df[['Shipping_Date', 'day', 'month', 'year', 'quarter']].copy()
        dim_time.columns = ['date', 'day', 'month', 'year', 'quarter']
        dim_time['date'] = dim_time['date'].dt.date 
        sync_dim(dim_time, 'dim_time')

        sync_dim(self.df[['Service_Type', 'Service_Name', 'SLA_Days']]
                 .rename(columns={'Service_Type': 'service_type', 'Service_Name': 'service_name', 'SLA_Days': 'sla_days'}), 'dim_service')

        sync_dim(pd.DataFrame({'status_name': self.df['Shipping_Status'].unique()}), 'dim_status')

        sync_dim(self.df[['Receiver_Address', 'Dest_District', 'Dest_City', 'Dest_Province', 'Dest_ZIP']]
                 .rename(columns={'Receiver_Address': 'receiver_address', 'Dest_District': 'district', 
                                  'Dest_City': 'city', 'Dest_Province': 'province', 'Dest_ZIP': 'zip_code'}), 'dim_destination')

        sync_dim(self.df[['Delay_Reason_Category', 'Delay_Description']]
                 .rename(columns={'Delay_Reason_Category': 'reason_category', 'Delay_Description': 'description'}), 'dim_reason')

    def load_fact(self):
        logging.info("🔗 Mapping IDs (Optimized Memory Method)...")
        
        # Helper untuk menarik ID dari DB ke Dictionary (Sangat hemat RAM)
        def get_map(query, key_col, id_col):
            temp_df = pd.read_sql(query, self.engine)
            return dict(zip(temp_df[key_col], temp_df[id_col]))

        # Buat kamus pemetaan
        branch_map = get_map("SELECT branch_id, branch_code FROM dim_branch", "branch_code", "branch_id")
        service_map = get_map("SELECT service_id, service_name FROM dim_service", "service_name", "service_id")
        status_map = get_map("SELECT status_id, status_name FROM dim_status", "status_name", "status_id")
        item_map = get_map("SELECT item_id, item_name FROM dim_item", "item_name", "item_id")
        dest_map = get_map("SELECT destination_id, receiver_address FROM dim_destination", "receiver_address", "destination_id")
        reason_map = get_map("SELECT reason_id, reason_category FROM dim_reason", "reason_category", "reason_id")

        # Mapping Time (Khusus tanggal harus dikonversi ke format yang sama)
        d_time = pd.read_sql("SELECT time_id, date FROM dim_time", self.engine)
        d_time['date'] = pd.to_datetime(d_time['date']).dt.date
        time_map = dict(zip(d_time['date'], d_time['time_id']))

        # Terapkan Mapping ke DataFrame Utama menggunakan .map()
        fact = self.df.copy()
        fact['date_only'] = fact['Shipping_Date'].dt.date
        
        fact['branch_id'] = fact['Branch_Code'].map(branch_map)
        fact['service_id'] = fact['Service_Name'].map(service_map)
        fact['status_id'] = fact['Shipping_Status'].map(status_map)
        fact['item_id'] = fact['Item_Name'].map(item_map)
        fact['destination_id'] = fact['Receiver_Address'].map(dest_map)
        fact['reason_id'] = fact['Delay_Reason_Category'].map(reason_map)
        fact['time_id'] = fact['date_only'].map(time_map)

        # Memilih kolom akhir sesuai skema Fact_Shipping
        final_fact = fact[[
            'time_id', 'branch_id', 'service_id', 'destination_id', 
            'item_id', 'status_id', 'reason_id',
            'Nomor_Resi', 'Shipping_Duration', 'Shipping_Cost', 'Is_Late'
        ]].rename(columns={
            'Nomor_Resi': 'nomor_resi', 
            'Shipping_Duration': 'shipping_duration',
            'Shipping_Cost': 'shipping_cost',
            'Is_Late': 'is_late'
        })
        
        # Hapus data yang gagal ter-mapping (jika ada ID yang NULL)
        final_fact = final_fact.dropna(subset=['time_id', 'branch_id', 'service_id'])

        # Upload ke Database dengan chunksize agar tidak berat
        final_fact.to_sql('fact_shipping', self.engine, if_exists='append', index=False, chunksize=1000)
        logging.info(f"✅ Fact_Shipping loaded with {len(final_fact)} rows.")

    def export_clean_csv(self):
        logging.info(f"💾 Saving clean data to {OUTPUT_CSV}...")
        self.df.to_csv(OUTPUT_CSV, index=False)

    def run_full_pipeline(self):
        try:
            self.extract()
            self.transform()
            self.load_dimensions()
            self.load_fact()
            self.export_clean_csv()
            logging.info("🔥🔥 ETL PROCESS COMPLETE! Data is ready for Analysis.")
        except Exception as e:
            logging.error(f"❌ ETL Failed: {e}")

# --- EXECUTION ---
if __name__ == "__main__":
    etl = LogiTrackETL(FILE_PATH, DB_URL)
    etl.run_full_pipeline()