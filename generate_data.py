import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

fake = Faker("id_ID")

PROVINCES = [
    "DKI Jakarta", "Jawa Barat", "Jawa Tengah", "Jawa Timur", "Banten",
    "DI Yogyakarta", "Bali", "Sumatera Utara", "Sumatera Selatan",
    "Kalimantan Timur", "Kalimantan Barat", "Sulawesi Selatan",
    "Sulawesi Utara", "Maluku", "Papua"
]

DEST_CITIES = [
    "Jakarta Pusat", "Jakarta Selatan", "Bandung", "Bekasi", "Bogor",
    "Depok", "Tangerang", "Semarang", "Yogyakarta", "Surabaya",
    "Malang", "Denpasar", "Medan", "Palembang", "Balikpapan",
    "Pontianak", "Makassar", "Manado", "Ambon", "Jayapura"
]

BRANCHES = [
    {"code": "CGK-01", "name": "Hub Utama Jakarta", "city": "Jakarta Pusat", "province": "DKI Jakarta"},
    {"code": "BDO-01", "name": "Hub Utama Bandung", "city": "Bandung", "province": "Jawa Barat"},
    {"code": "SUB-01", "name": "Hub Utama Surabaya", "city": "Surabaya", "province": "Jawa Timur"},
    {"code": "MDN-01", "name": "Hub Utama Medan", "city": "Medan", "province": "Sumatera Utara"},
    {"code": "UPG-01", "name": "Hub Utama Makassar", "city": "Makassar", "province": "Sulawesi Selatan"},
]

SERVICES = [
    {"type": "EXP", "name": "Express Overnight", "sla": 1},
    {"type": "REG", "name": "Reguler", "sla": 3},
    {"type": "ECO", "name": "Economy / Cargo", "sla": 6},
]

ITEM_CATEGORIES = ["Pakaian", "Elektronik", "Dokumen", "Makanan Kering", "Kosmetik", "Farmasi"]
CUSTOMER_TYPES = ["Individual", "Corporate", "E-Commerce"]
DELAY_REASONS = [
    "Cuaca Ekstrem",
    "Alamat Tidak Ditemukan",
    "Kendala Armada",
    "Gudang Overload",
    "Penerima Tidak Ada",
    "Kendala Operasional Kapal/Pesawat",
]


def generate_dataset(num_rows: int = 15000) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RAW_DIR / f"raw_nasional_logistics_data_{timestamp}.csv"

    data = []
    start_date = datetime(2025, 1, 1)

    for _ in range(num_rows):
        branch = random.choice(BRANCHES)
        service = random.choice(SERVICES)

        dest_city = random.choice(DEST_CITIES)
        dest_province = random.choice(PROVINCES)
        item_category = random.choice(ITEM_CATEGORIES)
        customer_type = random.choice(CUSTOMER_TYPES)

        is_fragile = random.random() < 0.22
        base_delay_risk = 0.14

        if dest_city in ["Jayapura", "Ambon", "Manado", "Makassar"]:
            base_delay_risk += 0.08

        if item_category in ["Elektronik", "Farmasi"]:
            base_delay_risk += 0.05

        if is_fragile:
            base_delay_risk += 0.04

        is_late = random.random() < base_delay_risk

        if is_late:
            actual_duration = service["sla"] + random.randint(1, 5)
            shipping_status = random.choice(["Delayed", "Failed", "In Transit"])
            delay_reason = random.choice(DELAY_REASONS)
            delay_description = f"Paket mengalami kendala: {delay_reason.lower()}."
        else:
            actual_duration = max(1, service["sla"] - random.choice([0, 1]))
            shipping_status = "Delivered"
            delay_reason = None
            delay_description = None

        row = {
            "Nomor_Resi": f"{service['type']}{fake.unique.random_number(digits=10, fix_len=True)}",
            "Shipping_Date": start_date + timedelta(days=random.randint(0, 365)),
            "Branch_Code": branch["code"],
            "Branch_Name": branch["name"],
            "Branch_City": branch["city"],
            "Branch_Province": branch["province"],
            "Service_Type": service["type"],
            "Service_Name": service["name"],
            "SLA_Days": service["sla"],
            "Receiver_Address": fake.address().replace("\n", ", "),
            "Dest_District": f"Kecamatan {fake.word().title()}",
            "Dest_City": dest_city,
            "Dest_Province": dest_province,
            "Dest_ZIP": fake.postcode(),
            "Item_Name": f"{item_category} {fake.word().title()}",
            "Item_Category": item_category,
            "Weight_Kg": round(random.uniform(0.2, 50.0), 2),
            "Fragile_Status": is_fragile,
            "Origin_City": branch["city"],
            "Transit_Point": random.choice(["CGK", "SUB", "UPG", None]),
            "Destination_City_Code": dest_city[:3].upper(),
            "Customer_Name": fake.name(),
            "Customer_Type": customer_type,
            "Customer_Phone": fake.phone_number(),
            "Shipping_Status": shipping_status,
            "Shipping_Cost": random.randint(15, 300) * 1000,
            "Shipping_Duration": actual_duration,
            "Is_Late": is_late,
            "Delay_Reason_Category": delay_reason,
            "Delay_Description": delay_description,
        }

        data.append(row)

    df = pd.DataFrame(data)

    # Dirty data untuk latihan ETL
    df.loc[df.sample(frac=0.02, random_state=42).index, "Customer_Phone"] = np.nan
    df.loc[df.sample(frac=0.01, random_state=43).index, "Dest_ZIP"] = np.nan
    df.loc[df.sample(frac=0.005, random_state=44).index, "Weight_Kg"] = -1
    df.loc[df.sample(frac=0.005, random_state=45).index, "Shipping_Cost"] = -150000

    df.to_csv(output_file, index=False)
    print(f"Data generated at: {output_file}")
    return str(output_file)


if __name__ == "__main__":
    generate_dataset()