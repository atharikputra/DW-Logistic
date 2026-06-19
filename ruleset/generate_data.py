import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from faker import Faker

from utils.dataset_naming import next_raw_batch_path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = SCRIPT_DIR / "dataset"
DYNAMIC_DIR = DATASET_DIR / "dynamic"
RAW_DIR = DYNAMIC_DIR / "raw"
PROCESSED_DIR = DYNAMIC_DIR / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

fake = Faker("id_ID")

DEFAULT_START_DATE = date(2025, 1, 1)
DEFAULT_END_DATE = date(2025, 12, 31)

BRANCHES = [
    {"code": "CGK-01", "name": "Hub Utama Jakarta", "city": "Jakarta Pusat", "province": "DKI Jakarta", "island": "Java", "ops_risk": 0.01},
    {"code": "SUB-01", "name": "Hub Utama Surabaya", "city": "Surabaya", "province": "Jawa Timur", "island": "Java", "ops_risk": 0.015},
    {"code": "BDO-01", "name": "Hub Utama Bandung", "city": "Bandung", "province": "Jawa Barat", "island": "Java", "ops_risk": 0.012},
    {"code": "MDN-01", "name": "Hub Utama Medan", "city": "Medan", "province": "Sumatera Utara", "island": "Sumatra", "ops_risk": 0.025},
    {"code": "UPG-01", "name": "Hub Utama Makassar", "city": "Makassar", "province": "Sulawesi Selatan", "island": "Sulawesi", "ops_risk": 0.03},
]
BRANCH_WEIGHTS = [0.42, 0.20, 0.16, 0.11, 0.11]

SERVICES = [
    {"type": "REG", "name": "Reguler", "sla": 3, "base_cost": 18000, "kg_cost": 3500, "risk": 0.10},
    {"type": "EXP", "name": "Express Overnight", "sla": 1, "base_cost": 32000, "kg_cost": 5500, "risk": 0.08},
    {"type": "ECO", "name": "Economy / Cargo", "sla": 6, "base_cost": 14000, "kg_cost": 2500, "risk": 0.12},
]
SERVICE_WEIGHTS = [0.58, 0.30, 0.12]

DESTINATIONS = [
    {"city": "Jakarta Selatan", "province": "DKI Jakarta", "island": "Java", "zone": 1, "weight": 0.20, "risk": 0.00},
    {"city": "Bandung", "province": "Jawa Barat", "island": "Java", "zone": 1, "weight": 0.13, "risk": 0.01},
    {"city": "Surabaya", "province": "Jawa Timur", "island": "Java", "zone": 2, "weight": 0.13, "risk": 0.015},
    {"city": "Semarang", "province": "Jawa Tengah", "island": "Java", "zone": 2, "weight": 0.07, "risk": 0.015},
    {"city": "Yogyakarta", "province": "DI Yogyakarta", "island": "Java", "zone": 2, "weight": 0.06, "risk": 0.015},
    {"city": "Tangerang", "province": "Banten", "island": "Java", "zone": 1, "weight": 0.06, "risk": 0.01},
    {"city": "Medan", "province": "Sumatera Utara", "island": "Sumatra", "zone": 3, "weight": 0.08, "risk": 0.04},
    {"city": "Palembang", "province": "Sumatera Selatan", "island": "Sumatra", "zone": 3, "weight": 0.05, "risk": 0.035},
    {"city": "Denpasar", "province": "Bali", "island": "Bali", "zone": 3, "weight": 0.05, "risk": 0.03},
    {"city": "Balikpapan", "province": "Kalimantan Timur", "island": "Kalimantan", "zone": 4, "weight": 0.05, "risk": 0.055},
    {"city": "Makassar", "province": "Sulawesi Selatan", "island": "Sulawesi", "zone": 4, "weight": 0.05, "risk": 0.06},
    {"city": "Manado", "province": "Sulawesi Utara", "island": "Sulawesi", "zone": 4, "weight": 0.03, "risk": 0.075},
    {"city": "Ambon", "province": "Maluku", "island": "Maluku", "zone": 5, "weight": 0.02, "risk": 0.095},
    {"city": "Jayapura", "province": "Papua", "island": "Papua", "zone": 5, "weight": 0.02, "risk": 0.11},
]

ITEM_CATEGORIES = [
    {"name": "Pakaian", "weight_range": (0.2, 5.0), "fragile_rate": 0.03, "risk": 0.00},
    {"name": "Kosmetik", "weight_range": (0.1, 3.0), "fragile_rate": 0.25, "risk": 0.02},
    {"name": "Elektronik", "weight_range": (0.5, 12.0), "fragile_rate": 0.55, "risk": 0.045},
    {"name": "Makanan Kering", "weight_range": (0.2, 8.0), "fragile_rate": 0.08, "risk": 0.015},
    {"name": "Farmasi", "weight_range": (0.1, 4.0), "fragile_rate": 0.30, "risk": 0.04},
    {"name": "Dokumen", "weight_range": (0.1, 1.0), "fragile_rate": 0.01, "risk": -0.01},
]
ITEM_WEIGHTS = [0.32, 0.18, 0.16, 0.14, 0.08, 0.12]

CUSTOMER_TYPES = [
    {"type": "E-Commerce", "weight": 0.62, "risk": 0.025},
    {"type": "Corporate", "weight": 0.24, "risk": -0.005},
    {"type": "Individual", "weight": 0.14, "risk": 0.005},
]

PEAK_MONTH_WEIGHTS = {
    1: 1.1,
    2: 1.0,
    3: 1.2,
    4: 1.4,
    5: 1.0,
    6: 1.0,
    7: 1.0,
    8: 1.0,
    9: 1.0,
    10: 1.8,
    11: 3.2,
    12: 3.5,
}

DEFAULT_DIRTY_RATES = {
    "missing_phone": 0.020,
    "missing_zip": 0.015,
    "negative_weight": 0.006,
    "negative_cost": 0.006,
    "messy_branch": 0.004,
    "duplicate_rows": 0.004,
}


def _as_date(value: date | datetime | str | None, default: date) -> date:
    if value is None:
        return default
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def _date_pool(start_date: date, end_date: date) -> tuple[list[date], np.ndarray]:
    if end_date < start_date:
        raise ValueError("end_date tidak boleh lebih awal dari start_date.")

    days = (end_date - start_date).days + 1
    dates = [start_date + timedelta(days=offset) for offset in range(days)]
    weights = []
    for value in dates:
        month_weight = PEAK_MONTH_WEIGHTS.get(value.month, 1.0)
        weekend_weight = 1.12 if value.weekday() >= 5 else 1.0
        payday_weight = 1.15 if value.day in {25, 26, 27, 28} else 1.0
        weights.append(month_weight * weekend_weight * payday_weight)
    weights_array = np.array(weights, dtype=float)
    return dates, weights_array / weights_array.sum()


def _choice(rng: np.random.Generator, items: list[dict[str, Any]], weights: list[float] | None = None) -> dict[str, Any]:
    if weights is None:
        weights = [float(item.get("weight", 1.0)) for item in items]
    probabilities = np.array(weights, dtype=float)
    probabilities = probabilities / probabilities.sum()
    return items[int(rng.choice(len(items), p=probabilities))]


def _route_zone(branch: dict[str, Any], destination: dict[str, Any]) -> int:
    if branch["city"] == destination["city"]:
        return 1
    if branch["island"] == destination["island"]:
        return max(2, int(destination["zone"]))
    return int(destination["zone"])


def _transit_point(branch: dict[str, Any], destination: dict[str, Any], rng: np.random.Generator) -> str | None:
    if branch["city"] == destination["city"]:
        return None
    if branch["island"] == "Java" and destination["island"] == "Java":
        return rng.choice(["CGK", "SUB", None], p=[0.35, 0.35, 0.30])
    if destination["island"] in {"Sulawesi", "Maluku", "Papua"}:
        return rng.choice(["UPG", "CGK", "SUB"], p=[0.55, 0.30, 0.15])
    if destination["island"] in {"Sumatra", "Kalimantan"}:
        return rng.choice(["CGK", "SUB", None], p=[0.55, 0.25, 0.20])
    return rng.choice(["CGK", "SUB", "UPG", None], p=[0.45, 0.25, 0.15, 0.15])


def _shipping_cost(service: dict[str, Any], weight_kg: float, zone: int, fragile: bool, peak: bool, rng: np.random.Generator) -> int:
    zone_surcharge = {1: 0, 2: 8000, 3: 18000, 4: 32000, 5: 52000}[zone]
    fragile_surcharge = 6000 if fragile else 0
    peak_surcharge = 5000 if peak else 0
    noise = rng.normal(0, 2500)
    raw_cost = service["base_cost"] + service["kg_cost"] * weight_kg + zone_surcharge + fragile_surcharge + peak_surcharge + noise
    return int(max(9000, round(raw_cost / 500) * 500))


def _delay_reason(is_peak: bool, destination: dict[str, Any], transit_point: str | None, rng: np.random.Generator) -> str:
    reasons = [
        ("Gudang Overload", 0.36 if is_peak else 0.12),
        ("Kendala Armada", 0.18),
        ("Alamat Tidak Ditemukan", 0.16),
        ("Penerima Tidak Ada", 0.14),
        ("Cuaca Ekstrem", 0.12 if destination["zone"] >= 4 else 0.08),
        ("Kendala Operasional Kapal/Pesawat", 0.18 if destination["zone"] >= 4 or transit_point else 0.06),
    ]
    labels = [label for label, _ in reasons]
    weights = np.array([weight for _, weight in reasons], dtype=float)
    weights = weights / weights.sum()
    return labels[int(rng.choice(len(labels), p=weights))]


def _inject_dirty_data(
    df: pd.DataFrame,
    rng: np.random.Generator,
    dirty_rates: dict[str, float] | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df

    dirty_df = df.copy()
    rates = {**DEFAULT_DIRTY_RATES, **(dirty_rates or {})}

    def sample_index(frac: float) -> pd.Index:
        if frac <= 0:
            return pd.Index([])
        size = max(1, int(len(dirty_df) * frac))
        return dirty_df.sample(n=size, random_state=int(rng.integers(0, 1_000_000))).index

    dirty_df.loc[sample_index(rates["missing_phone"]), "Customer_Phone"] = np.nan
    dirty_df.loc[sample_index(rates["missing_zip"]), "Dest_ZIP"] = np.nan
    dirty_df.loc[sample_index(rates["negative_weight"]), "Weight_Kg"] = -1
    dirty_df.loc[sample_index(rates["negative_cost"]), "Shipping_Cost"] = -150000
    messy_index = sample_index(rates["messy_branch"])
    dirty_df.loc[messy_index, "Branch_Name"] = "  " + dirty_df.loc[messy_index, "Branch_Name"].astype(str).str.lower() + "  "

    duplicate_count = int(len(dirty_df) * rates["duplicate_rows"])
    if duplicate_count > 0:
        duplicates = dirty_df.sample(n=duplicate_count, random_state=int(rng.integers(0, 1_000_000))).copy()
        dirty_df = pd.concat([dirty_df, duplicates], ignore_index=True)

    return dirty_df.sample(frac=1, random_state=int(rng.integers(0, 1_000_000))).reset_index(drop=True)


def generate_dataset(
    num_rows: int = 15_000,
    start_date: date | datetime | str | None = None,
    end_date: date | datetime | str | None = None,
    seed: int | None = None,
    inject_dirty: bool = True,
    dirty_rates: dict[str, float] | None = None,
) -> str:
    start = _as_date(start_date, DEFAULT_START_DATE)
    end = _as_date(end_date, DEFAULT_END_DATE)
    rng = np.random.default_rng(seed)
    py_random = random.Random(seed)
    if seed is not None:
        fake.seed_instance(seed)
    fake.unique.clear()

    date_values, date_weights = _date_pool(start, end)
    output_file = next_raw_batch_path(RAW_DIR, PROCESSED_DIR)
    data = []

    for _ in range(num_rows):
        branch = _choice(rng, BRANCHES, BRANCH_WEIGHTS)
        service = _choice(rng, SERVICES, SERVICE_WEIGHTS)
        destination = _choice(rng, DESTINATIONS)
        customer = _choice(rng, CUSTOMER_TYPES)
        item = _choice(rng, ITEM_CATEGORIES, ITEM_WEIGHTS)
        shipping_date = date_values[int(rng.choice(len(date_values), p=date_weights))]

        peak_season = shipping_date.month in {10, 11, 12}
        weight_min, weight_max = item["weight_range"]
        weight_kg = round(float(rng.uniform(weight_min, weight_max)), 2)
        fragile = rng.random() < item["fragile_rate"]
        route_zone = _route_zone(branch, destination)
        transit_point = _transit_point(branch, destination, rng)
        shipping_cost = _shipping_cost(service, weight_kg, route_zone, fragile, peak_season, rng)

        delay_risk = (
            service["risk"]
            + branch["ops_risk"]
            + destination["risk"]
            + item["risk"]
            + customer["risk"]
            + (0.11 if peak_season else 0.0)
            + (0.025 if fragile else 0.0)
            + (0.025 if weight_kg >= 10 else 0.0)
        )
        delay_risk = min(max(delay_risk, 0.02), 0.62)
        is_late = rng.random() < delay_risk

        if is_late:
            actual_duration = service["sla"] + int(rng.integers(1, 5 + route_zone))
            shipping_status = rng.choice(["Delayed", "Failed", "Returned To Sender"], p=[0.72, 0.17, 0.11])
            delay_reason = _delay_reason(peak_season, destination, transit_point, rng)
            delay_description = f"Kendala operasional: {delay_reason.lower()}."
        else:
            early_or_on_time = int(rng.choice([0, 0, 1], p=[0.55, 0.25, 0.20]))
            actual_duration = max(1, service["sla"] - early_or_on_time)
            shipping_status = rng.choice(["Delivered", "In Transit"], p=[0.94, 0.06])
            delay_reason = None
            delay_description = None

        data.append(
            {
                "Nomor_Resi": f"{service['type']}{fake.unique.random_number(digits=10, fix_len=True)}",
                "Shipping_Date": datetime.combine(shipping_date, datetime.min.time()),
                "Branch_Code": branch["code"],
                "Branch_Name": branch["name"],
                "Branch_City": branch["city"],
                "Branch_Province": branch["province"],
                "Service_Type": service["type"],
                "Service_Name": service["name"],
                "SLA_Days": service["sla"],
                "Receiver_Address": fake.address().replace("\n", ", "),
                "Dest_District": f"Kecamatan {fake.word().title()}",
                "Dest_City": destination["city"],
                "Dest_Province": destination["province"],
                "Dest_ZIP": fake.postcode(),
                "Item_Name": f"{item['name']} {fake.word().title()}",
                "Item_Category": item["name"],
                "Weight_Kg": weight_kg,
                "Fragile_Status": fragile,
                "Origin_City": branch["city"],
                "Transit_Point": transit_point,
                "Destination_City_Code": destination["city"][:3].upper(),
                "Customer_Name": fake.name(),
                "Customer_Type": customer["type"],
                "Customer_Phone": fake.phone_number(),
                "Shipping_Status": shipping_status,
                "Shipping_Cost": shipping_cost,
                "Shipping_Duration": actual_duration,
                "Is_Late": is_late,
                "Delay_Reason_Category": delay_reason,
                "Delay_Description": delay_description,
            }
        )

    df = pd.DataFrame(data)
    if inject_dirty:
        df = _inject_dirty_data(df, rng, dirty_rates=dirty_rates)

    df.to_csv(output_file, index=False)
    print(f"Data generated at: {output_file}")
    return str(output_file)


if __name__ == "__main__":
    generate_dataset()
