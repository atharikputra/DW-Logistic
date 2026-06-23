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
    {"code": "SMG-01", "name": "Hub Regional Semarang", "city": "Semarang", "province": "Jawa Tengah", "island": "Java", "ops_risk": 0.018},
    {"code": "DPS-01", "name": "Hub Regional Denpasar", "city": "Denpasar", "province": "Bali", "island": "Bali", "ops_risk": 0.022},
    {"code": "PLM-01", "name": "Hub Regional Palembang", "city": "Palembang", "province": "Sumatera Selatan", "island": "Sumatra", "ops_risk": 0.026},
    {"code": "BPN-01", "name": "Hub Regional Balikpapan", "city": "Balikpapan", "province": "Kalimantan Timur", "island": "Kalimantan", "ops_risk": 0.032},
    {"code": "PNK-01", "name": "Hub Regional Pontianak", "city": "Pontianak", "province": "Kalimantan Barat", "island": "Kalimantan", "ops_risk": 0.035},
    {"code": "JOG-01", "name": "Hub Regional Yogyakarta", "city": "Yogyakarta", "province": "DI Yogyakarta", "island": "Java", "ops_risk": 0.016},
    {"code": "MDC-01", "name": "Hub Regional Manado", "city": "Manado", "province": "Sulawesi Utara", "island": "Sulawesi", "ops_risk": 0.040},
]
BRANCH_WEIGHTS = [0.28, 0.14, 0.12, 0.08, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.03, 0.02]

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
    {"city": "Bekasi", "province": "Jawa Barat", "island": "Java", "zone": 1, "weight": 0.07, "risk": 0.008},
    {"city": "Malang", "province": "Jawa Timur", "island": "Java", "zone": 2, "weight": 0.05, "risk": 0.018},
    {"city": "Cilegon", "province": "Banten", "island": "Java", "zone": 2, "weight": 0.025, "risk": 0.020},
    {"city": "Pekanbaru", "province": "Riau", "island": "Sumatra", "zone": 3, "weight": 0.04, "risk": 0.038},
    {"city": "Jambi", "province": "Jambi", "island": "Sumatra", "zone": 3, "weight": 0.025, "risk": 0.042},
    {"city": "Bukittinggi", "province": "Sumatera Barat", "island": "Sumatra", "zone": 3, "weight": 0.018, "risk": 0.047},
    {"city": "Pontianak", "province": "Kalimantan Barat", "island": "Kalimantan", "zone": 4, "weight": 0.032, "risk": 0.058},
    {"city": "Banjarmasin", "province": "Kalimantan Selatan", "island": "Kalimantan", "zone": 4, "weight": 0.032, "risk": 0.055},
    {"city": "Samarinda", "province": "Kalimantan Timur", "island": "Kalimantan", "zone": 4, "weight": 0.028, "risk": 0.060},
    {"city": "Parepare", "province": "Sulawesi Selatan", "island": "Sulawesi", "zone": 4, "weight": 0.018, "risk": 0.068},
    {"city": "Kendari", "province": "Sulawesi Tenggara", "island": "Sulawesi", "zone": 4, "weight": 0.020, "risk": 0.072},
    {"city": "Palu", "province": "Sulawesi Tengah", "island": "Sulawesi", "zone": 4, "weight": 0.018, "risk": 0.075},
    {"city": "Mataram", "province": "Nusa Tenggara Barat", "island": "Nusa Tenggara", "zone": 4, "weight": 0.025, "risk": 0.062},
    {"city": "Kupang", "province": "Nusa Tenggara Timur", "island": "Nusa Tenggara", "zone": 5, "weight": 0.020, "risk": 0.085},
    {"city": "Bau-Bau", "province": "Sulawesi Tenggara", "island": "Sulawesi", "zone": 5, "weight": 0.012, "risk": 0.090},
    {"city": "Sorong", "province": "Papua Barat Daya", "island": "Papua", "zone": 5, "weight": 0.014, "risk": 0.105},
    {"city": "Merauke", "province": "Papua Selatan", "island": "Papua", "zone": 5, "weight": 0.010, "risk": 0.120},
    {"city": "Sabang", "province": "Aceh", "island": "Sumatra", "zone": 5, "weight": 0.010, "risk": 0.095},
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


def _date_pool(
    start_date: date,
    end_date: date,
    rng: np.random.Generator | None = None,
) -> tuple[list[date], np.ndarray]:
    if end_date < start_date:
        raise ValueError("end_date tidak boleh lebih awal dari start_date.")

    days = (end_date - start_date).days + 1
    dates = [start_date + timedelta(days=offset) for offset in range(days)]
    month_factors = np.ones(12, dtype=float)
    campaign_days: set[int] = set()
    if rng is not None:
        # Each batch represents a different demand window: campaign months,
        # payday intensity, and seasonal noise change without ignoring the
        # realistic year-end peak entirely.
        month_factors = rng.lognormal(mean=0.0, sigma=0.75, size=12)
        active_months = sorted({value.month for value in dates})
        campaign_count = min(len(active_months), int(rng.integers(1, 4)))
        campaign_months = rng.choice(active_months, size=campaign_count, replace=False)
        for month in np.atleast_1d(campaign_months):
            month_factors[int(month) - 1] *= float(rng.uniform(2.0, 5.5))
        campaign_days = set(int(value) for value in rng.choice(np.arange(1, 29), size=3, replace=False))

    weights = []
    for value in dates:
        month_weight = PEAK_MONTH_WEIGHTS.get(value.month, 1.0)
        weekend_weight = 1.12 if value.weekday() >= 5 else 1.0
        payday_weight = 1.15 if value.day in {25, 26, 27, 28} else 1.0
        campaign_weight = 1.8 if value.day in campaign_days else 1.0
        weights.append(
            month_weight
            * float(month_factors[value.month - 1])
            * weekend_weight
            * payday_weight
            * campaign_weight
        )
    weights_array = np.array(weights, dtype=float)
    return dates, weights_array / weights_array.sum()


def _choice(rng: np.random.Generator, items: list[dict[str, Any]], weights: list[float] | None = None) -> dict[str, Any]:
    if weights is None:
        weights = [float(item.get("weight", 1.0)) for item in items]
    probabilities = np.array(weights, dtype=float)
    probabilities = probabilities / probabilities.sum()
    return items[int(rng.choice(len(items), p=probabilities))]


def _batch_distribution(
    rng: np.random.Generator,
    base_weights: list[float],
    concentration: float,
    variability: float = 0.65,
    min_alpha: float = 0.35,
) -> list[float]:
    """Create a plausible but visibly different mix for each generated batch.

    Sampling every row from one fixed distribution makes large datasets look
    almost identical because the observed shares converge to the same values.
    A Dirichlet draw gives each batch its own operating mix, while blending it
    with the baseline keeps small destinations and segments represented.
    """
    base = np.asarray(base_weights, dtype=float)
    base = base / base.sum()
    alpha = np.maximum(base * concentration, min_alpha)
    sampled = rng.dirichlet(alpha)
    mixed = ((1.0 - variability) * base) + (variability * sampled)
    return (mixed / mixed.sum()).tolist()


def _batch_risk_offsets(
    rng: np.random.Generator,
    size: int,
    hotspot_range: tuple[float, float],
    noise_std: float,
    hotspot_count: int = 1,
) -> np.ndarray:
    """Model temporary operational shocks so the priority area can move."""
    offsets = rng.normal(0.0, noise_std, size=size)
    hotspot_count = max(1, min(int(hotspot_count), size))
    hotspot_indices = np.atleast_1d(rng.choice(size, size=hotspot_count, replace=False)).astype(int)
    for hotspot_index in hotspot_indices:
        offsets[hotspot_index] += float(rng.uniform(*hotspot_range))

    if size > hotspot_count:
        recovery_candidates = [index for index in range(size) if index not in set(hotspot_indices)]
        recovery_index = int(rng.choice(recovery_candidates))
        offsets[recovery_index] -= float(rng.uniform(0.015, 0.045))
    return offsets


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


def _shipping_cost(
    service: dict[str, Any],
    weight_kg: float,
    zone: int,
    fragile: bool,
    peak: bool,
    rng: np.random.Generator,
    batch_cost_multiplier: float = 1.0,
    fuel_surcharge: int = 0,
) -> int:
    zone_surcharge = {1: 0, 2: 8000, 3: 18000, 4: 32000, 5: 52000}[zone]
    fragile_surcharge = 6000 if fragile else 0
    peak_surcharge = 5000 if peak else 0
    noise = rng.normal(0, 2500)
    raw_cost = (
        service["base_cost"]
        + service["kg_cost"] * weight_kg
        + zone_surcharge
        + fragile_surcharge
        + peak_surcharge
        + fuel_surcharge
        + noise
    ) * batch_cost_multiplier
    return int(max(9000, round(raw_cost / 500) * 500))


def _delay_reason(
    is_peak: bool,
    destination: dict[str, Any],
    transit_point: str | None,
    rng: np.random.Generator,
    batch_multipliers: np.ndarray | None = None,
) -> str:
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
    if batch_multipliers is not None:
        weights *= batch_multipliers
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
    if seed is not None:
        fake.seed_instance(seed)
    fake.unique.clear()

    date_values, date_weights = _date_pool(start, end, rng=rng)
    output_file = next_raw_batch_path(RAW_DIR, PROCESSED_DIR)
    data = []

    # Pick a coherent regional demand story for this batch. Branches and
    # destinations in the same focus region rise together, instead of every
    # column being randomized independently without business meaning.
    focus_island = str(rng.choice(sorted({branch["island"] for branch in BRANCHES})))
    disrupted_island = str(rng.choice(sorted({destination["island"] for destination in DESTINATIONS})))
    focus_zone = int(rng.integers(1, 6))
    regional_demand_boost = float(rng.uniform(2.2, 5.0))
    zone_demand_boost = float(rng.uniform(1.3, 2.8))
    focus_destination_candidates = [
        destination for destination in DESTINATIONS if destination["island"] == focus_island
    ]
    focus_destination = _choice(rng, focus_destination_candidates)
    focus_destination_city = str(focus_destination["city"])
    city_demand_boost = float(rng.uniform(3.5, 8.0))

    branch_base_weights = [
        float(weight) * (regional_demand_boost if branch["island"] == focus_island else 1.0)
        for branch, weight in zip(BRANCHES, BRANCH_WEIGHTS)
    ]
    destination_base_weights = [
        float(destination["weight"])
        * (regional_demand_boost if destination["island"] == focus_island else 1.0)
        * (zone_demand_boost if int(destination["zone"]) == focus_zone else 1.0)
        * (city_demand_boost if destination["city"] == focus_destination_city else 1.0)
        for destination in DESTINATIONS
    ]

    # Give every generated batch a distinct operating mix. Low concentration
    # makes the selected mix visibly different; baseline blending keeps it
    # plausible and prevents categories from disappearing completely.
    branch_weights = _batch_distribution(
        rng,
        branch_base_weights,
        concentration=3.5,
        variability=0.92,
        min_alpha=0.15,
    )
    service_weights = _batch_distribution(rng, SERVICE_WEIGHTS, concentration=3.5, variability=0.92)
    destination_weights = _batch_distribution(
        rng,
        destination_base_weights,
        concentration=30,
        variability=0.85,
        min_alpha=0.08,
    )
    customer_weights = _batch_distribution(
        rng,
        [float(customer["weight"]) for customer in CUSTOMER_TYPES],
        concentration=4,
        variability=0.88,
    )
    item_weights = _batch_distribution(rng, ITEM_WEIGHTS, concentration=6, variability=0.88)

    branch_risk_offsets = _batch_risk_offsets(rng, len(BRANCHES), (0.08, 0.20), 0.030, hotspot_count=2)
    destination_risk_offsets = _batch_risk_offsets(
        rng,
        len(DESTINATIONS),
        (0.10, 0.24),
        0.035,
        hotspot_count=3,
    )
    service_risk_offsets = _batch_risk_offsets(rng, len(SERVICES), (0.04, 0.10), 0.020)
    customer_risk_offsets = _batch_risk_offsets(rng, len(CUSTOMER_TYPES), (0.03, 0.08), 0.016)
    item_risk_offsets = _batch_risk_offsets(rng, len(ITEM_CATEGORIES), (0.04, 0.10), 0.020, hotspot_count=2)

    disruption_boost = float(rng.uniform(0.035, 0.11))
    for index, branch in enumerate(BRANCHES):
        if branch["island"] == disrupted_island:
            branch_risk_offsets[index] += disruption_boost
    for index, destination in enumerate(DESTINATIONS):
        if destination["island"] == disrupted_island:
            destination_risk_offsets[index] += disruption_boost

    branch_risk_by_code = {
        branch["code"]: float(branch_risk_offsets[index]) for index, branch in enumerate(BRANCHES)
    }
    destination_risk_by_city = {
        destination["city"]: float(destination_risk_offsets[index])
        for index, destination in enumerate(DESTINATIONS)
    }
    service_risk_by_type = {
        service["type"]: float(service_risk_offsets[index]) for index, service in enumerate(SERVICES)
    }
    customer_risk_by_type = {
        customer["type"]: float(customer_risk_offsets[index])
        for index, customer in enumerate(CUSTOMER_TYPES)
    }
    item_risk_by_name = {
        item["name"]: float(item_risk_offsets[index]) for index, item in enumerate(ITEM_CATEGORIES)
    }
    delay_reason_multipliers = rng.lognormal(mean=0.0, sigma=1.05, size=6)
    batch_global_risk = float(rng.uniform(-0.055, 0.105))
    batch_cost_multiplier = float(rng.uniform(0.72, 1.48))
    fuel_surcharge = int(rng.choice([0, 0, 2500, 5000, 7500, 10000, 15000, 20000]))
    batch_weight_scale = float(np.clip(rng.lognormal(mean=0.0, sigma=0.42), 0.55, 1.85))
    category_weight_scales = {
        item["name"]: float(np.clip(batch_weight_scale * rng.lognormal(0.0, 0.22), 0.45, 2.20))
        for item in ITEM_CATEGORIES
    }
    fragile_rate_shift = float(rng.uniform(-0.08, 0.14))
    late_status_weights = _batch_distribution(rng, [0.72, 0.17, 0.11], concentration=7, variability=0.72)
    success_status_weights = _batch_distribution(rng, [0.94, 0.06], concentration=8, variability=0.65)

    for _ in range(num_rows):
        branch = _choice(rng, BRANCHES, branch_weights)
        service = _choice(rng, SERVICES, service_weights)
        destination = _choice(rng, DESTINATIONS, destination_weights)
        customer = _choice(rng, CUSTOMER_TYPES, customer_weights)
        item = _choice(rng, ITEM_CATEGORIES, item_weights)
        shipping_date = date_values[int(rng.choice(len(date_values), p=date_weights))]

        peak_season = shipping_date.month in {10, 11, 12}
        weight_min, weight_max = item["weight_range"]
        weight_kg = round(
            float(np.clip(rng.uniform(weight_min, weight_max) * category_weight_scales[item["name"]], 0.1, 30.0)),
            2,
        )
        fragile_probability = float(np.clip(item["fragile_rate"] + fragile_rate_shift, 0.01, 0.85))
        fragile = rng.random() < fragile_probability
        route_zone = _route_zone(branch, destination)
        transit_point = _transit_point(branch, destination, rng)
        shipping_cost = _shipping_cost(
            service,
            weight_kg,
            route_zone,
            fragile,
            peak_season,
            rng,
            batch_cost_multiplier=batch_cost_multiplier,
            fuel_surcharge=fuel_surcharge,
        )

        delay_risk = (
            service["risk"]
            + branch["ops_risk"]
            + destination["risk"]
            + item["risk"]
            + customer["risk"]
            + branch_risk_by_code[branch["code"]]
            + destination_risk_by_city[destination["city"]]
            + service_risk_by_type[service["type"]]
            + customer_risk_by_type[customer["type"]]
            + item_risk_by_name[item["name"]]
            + batch_global_risk
            + (0.11 if peak_season else 0.0)
            + (0.025 if fragile else 0.0)
            + (0.025 if weight_kg >= 10 else 0.0)
        )
        delay_risk = min(max(delay_risk, 0.02), 0.62)
        is_late = rng.random() < delay_risk

        if is_late:
            actual_duration = service["sla"] + int(rng.integers(1, 5 + route_zone))
            shipping_status = rng.choice(["Delayed", "Failed", "Returned To Sender"], p=late_status_weights)
            delay_reason = _delay_reason(
                peak_season,
                destination,
                transit_point,
                rng,
                batch_multipliers=delay_reason_multipliers,
            )
            delay_description = f"Kendala operasional: {delay_reason.lower()}."
        else:
            early_or_on_time = int(rng.choice([0, 0, 1], p=[0.55, 0.25, 0.20]))
            actual_duration = max(1, service["sla"] - early_or_on_time)
            shipping_status = rng.choice(["Delivered", "In Transit"], p=success_status_weights)
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
