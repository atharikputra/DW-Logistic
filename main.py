import pandas as pd
import numpy as np
import random
from faker import Faker
from datetime import datetime, timedelta
import os  # tambahan

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))

# Initialize Faker with Indonesian locale
fake = Faker('id_ID')

# Configuration
NUM_ROWS = 25000

# ← Pakai timestamp supaya setiap run menghasilkan file baru, tidak override
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, f'raw_nasional_logistics_data_{timestamp}.csv')

# --- COMBINATORIAL DESCRIPTION GENERATOR (For realistic business notes) ---
KONDISI_AWAL = [
    "Cuaca ekstrem", "Hujan lebat", "Banjir di area tujuan", "Jalanan ditutup sementara", 
    "Alamat tidak ditemukan", "Penerima tidak ada di tempat", "Nomor telepon tidak aktif", 
    "Nomor telepon salah/tidak terdaftar", "Paket tertukar di hub transit", "Armada mengalami kendala mesin", 
    "Ban armada bocor saat pengantaran", "Kecelakaan lalu lintas di rute", "Penerima menolak menerima paket", 
    "Paket rusak/penyok saat transit", "Label resi sobek dan tidak terbaca", "Gudang transit mengalami overload", 
    "Penerima sudah pindah alamat", "Gang terlalu sempit, tidak bisa dilalui mobil", "Pagar rumah terkunci rapat", 
    "Terjadi demonstrasi/kepadatan di rute pengiriman"
]

DETAIL_KEJADIAN = [
    "saat kurir tiba di lokasi,", "sehingga proses pengantaran terhambat,", 
    "ketika kurir mencoba menghubungi,", "di area kecamatan tujuan,", 
    "pada saat proses sortir di fasilitas,", "sehingga paket tidak bisa diserahkan langsung,", 
    "membuat rute pengantaran harus dialihkan,", "menyebabkan penundaan jadwal keberangkatan,", 
    "sehingga tim operasional harus melakukan intervensi,", "saat pengecekan manifest harian,"
]

AKSI_LANJUTAN = [
    "paket dibawa kembali ke cabang.", "jadwal ulang pengantaran dilakukan besok.", 
    "menunggu konfirmasi lebih lanjut dari pihak pengirim.", "paket diamankan di gudang sementara.", 
    "kurir terpaksa melanjutkan rute berikutnya.", "menunggu update data nomor telepon dari CS.", 
    "paket sedang dalam proses retur ke pengirim.", "sedang dicarikan rute alternatif oleh tim lapangan.", 
    "pengantaran ditunda menunggu kondisi membaik.", "investigasi lebih lanjut sedang dilakukan oleh tim resolusi."
]

def generate_delay_description():
    return f"{random.choice(KONDISI_AWAL)} {random.choice(DETAIL_KEJADIAN)} {random.choice(AKSI_LANJUTAN)}"

# --- REFERENCE DATA ---
BRANCHES = [
    {'code': 'MDN-01', 'name': 'Hub Utama Medan',      'city': 'Medan',        'prov': 'Sumatera Utara'},
    {'code': 'PLB-01', 'name': 'Hub Utama Palembang',  'city': 'Palembang',    'prov': 'Sumatera Selatan'},
    {'code': 'CGK-01', 'name': 'Hub Utama Jakarta',    'city': 'Jakarta Pusat','prov': 'DKI Jakarta'},
    {'code': 'BDO-01', 'name': 'Hub Utama Bandung',    'city': 'Bandung',      'prov': 'Jawa Barat'},
    {'code': 'SUB-01', 'name': 'Hub Utama Surabaya',   'city': 'Surabaya',     'prov': 'Jawa Timur'},
    {'code': 'DPS-01', 'name': 'Hub Utama Denpasar',   'city': 'Denpasar',     'prov': 'Bali'},
    {'code': 'BPN-01', 'name': 'Hub Utama Balikpapan', 'city': 'Balikpapan',   'prov': 'Kalimantan Timur'},
    {'code': 'PNK-01', 'name': 'Hub Utama Pontianak',  'city': 'Pontianak',    'prov': 'Kalimantan Barat'},
    {'code': 'UPG-01', 'name': 'Hub Utama Makassar',   'city': 'Makassar',     'prov': 'Sulawesi Selatan'},
    {'code': 'MDC-01', 'name': 'Hub Utama Manado',     'city': 'Manado',       'prov': 'Sulawesi Utara'},
    {'code': 'AMQ-01', 'name': 'Hub Utama Ambon',      'city': 'Ambon',        'prov': 'Maluku'},
    {'code': 'DJJ-01', 'name': 'Hub Utama Jayapura',   'city': 'Jayapura',     'prov': 'Papua'}
]

SERVICES = [
    {'type': 'REG', 'name': 'Reguler',            'sla': 3},
    {'type': 'EXP', 'name': 'Express Overnight',  'sla': 1},
    {'type': 'ECO', 'name': 'Economy / Cargo',    'sla': 6},
    {'type': 'SME', 'name': 'Same Day Delivery',  'sla': 0}
]

CATEGORIES = ['Elektronik', 'Pakaian', 'Dokumen', 'Kosmetik', 'Makanan Kering', 'Peralatan Rumah', 'Otomotif', 'Farmasi']
STATUSES   = ['Delivered', 'In Transit', 'Delayed', 'Failed', 'Returned to Sender']
REASONS    = ['Cuaca Buruk', 'Alamat Tidak Ditemukan', 'Penerima Tidak Ada', 'Kendala Operasional Kapal/Pesawat', 'Barang Rusak', None]

# --- DATA GENERATION ---
print(f"Generating {NUM_ROWS} rows of nationwide raw logistics data...")

data = []
start_date = datetime(2025, 1, 1)

for _ in range(NUM_ROWS):
    branch   = random.choice(BRANCHES)
    service  = random.choice(SERVICES)
    category = random.choice(CATEGORIES)
    status   = random.choices(STATUSES, weights=[0.72, 0.12, 0.1, 0.04, 0.02])[0]

    shipping_date = start_date + timedelta(days=random.randint(0, 365))
    is_late = 1 if status in ['Delayed', 'Failed', 'Returned to Sender'] else random.choices([0, 1], weights=[0.9, 0.1])[0]

    base_sla = 1 if service['sla'] == 0 else service['sla']

    if is_late:
        actual_duration = base_sla + random.randint(1, 7)
        reason = random.choice([r for r in REASONS if r is not None])
    else:
        actual_duration = random.randint(0 if service['sla'] == 0 else 1, base_sla)
        reason = None

    row = {
        'Nomor_Resi':            f"EXP{fake.unique.random_number(digits=11, fix_len=True)}",
        'Shipping_Date':         shipping_date.strftime('%Y-%m-%d %H:%M:%S'),
        'Branch_Code':           branch['code'],
        'Branch_Name':           branch['name'],
        'Branch_City':           branch['city'],
        'Branch_Province':       branch['prov'],
        'Service_Type':          service['type'],
        'Service_Name':          service['name'],
        'SLA_Days':              service['sla'],
        'Receiver_Address':      fake.street_address(),
        'Dest_District':         fake.city_name(),
        'Dest_City':             fake.city(),
        'Dest_Province':         fake.state(),
        'Dest_ZIP':              fake.postcode(),
        'Item_Name':             f"{category} {fake.word()}",
        'Item_Category':         category,
        'Weight_Kg':             round(random.uniform(0.1, 50.0), 2),
        'Fragile_Status':        random.choice([True, False]),
        'Origin_City':           branch['city'],
        'Transit_Point':         random.choice(['CGK', 'SUB', 'UPG']) if random.random() > 0.5 else None,
        'Destination_City_Code': fake.city()[:3].upper(),
        'Customer_Name':         fake.name(),
        'Customer_Type':         random.choices(['Individual', 'Corporate', 'E-Commerce'], weights=[0.5, 0.2, 0.3])[0],
        'Customer_Phone':        fake.phone_number(),
        'Shipping_Status':       status,
        'Shipping_Cost':         random.randint(15, 300) * 1000,
        'Shipping_Duration':     actual_duration,
        'Is_Late':               is_late,
        'Delay_Reason_Category': reason,
        'Delay_Description':     generate_delay_description() if reason else None
    }
    data.append(row)

df = pd.DataFrame(data)

# --- INJECT DIRTY DATA ---
print("Injecting 'dirty' data for ETL practice...")

df.loc[df.sample(frac=0.06).index, 'Customer_Phone'] = np.nan
df.loc[df.sample(frac=0.04).index, 'Dest_ZIP']       = np.nan

df['Item_Category'] = df['Item_Category'].apply(
    lambda x: x.upper() if random.random() > 0.8 else (x.lower() if random.random() > 0.8 else x)
)
df['Dest_City'] = df['Dest_City'].apply(
    lambda x: x.upper() if random.random() > 0.85 else x
)

df.loc[df.sample(frac=0.010).index, 'Weight_Kg']    = -2.5
df.loc[df.sample(frac=0.005).index, 'Weight_Kg']    = 8888.88
df.loc[df.sample(frac=0.015).index, 'Shipping_Cost'] = -150000
df.loc[df.sample(frac=0.010).index, 'SLA_Days']     = 99

duplicates = df.sample(n=600)
df = pd.concat([df, duplicates], ignore_index=True)
df = df.sample(frac=1).reset_index(drop=True)

df.to_csv(OUTPUT_FILE, index=False)
print(f"Success! File '{OUTPUT_FILE}' generated with {len(df)} rows.")