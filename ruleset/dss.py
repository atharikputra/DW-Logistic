"""
Decision Support System (DSS) untuk Logistics Data Warehouse.

Modul ini berisi:
- Kalkulasi risk score (weighted: late_rate 50%, late_volume 30%, avg_duration 20%)
- Build DSS ranking dari branch, destination, dan route
- KPI Monitoring System dengan threshold dari distribusi data aktif
- Executive insight rule-based yang hanya menjelaskan metrik warehouse
"""

from __future__ import annotations

import pandas as pd


# ---------------------------------------------------------------------------
# Risk scoring
# ---------------------------------------------------------------------------

def risk_label(score: float, reference_scores: pd.Series | None = None) -> tuple[str, str]:
    if reference_scores is not None:
        refs = pd.to_numeric(reference_scores, errors="coerce").dropna()
        if len(refs) >= 3:
            critical_threshold = float(refs.quantile(0.75))
            risk_threshold = float(refs.quantile(0.50))
            if score >= critical_threshold:
                return "Critical", "red"
            if score >= risk_threshold:
                return "At Risk", "yellow"
            return "Controlled", "green"

    if score >= 70:
        return "Critical", "red"
    if score >= 40:
        return "At Risk", "yellow"
    return "Controlled", "green"


def normalize_series(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").fillna(0)
    max_value = float(values.max() or 0)
    if max_value <= 0:
        return values * 0
    return values / max_value


def add_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    scored = df.copy()
    late_rate_component = pd.to_numeric(scored.get("late_rate", 0), errors="coerce").fillna(0)
    late_volume_component = normalize_series(scored.get("late_shipments", pd.Series([0] * len(scored)))) * 100
    duration_component = normalize_series(scored.get("avg_duration", pd.Series([0] * len(scored)))) * 100

    scored["risk_score"] = (
        (late_rate_component * 0.50)
        + (late_volume_component * 0.30)
        + (duration_component * 0.20)
    ).round(1)
    scored["priority"] = scored["risk_score"].map(lambda value: risk_label(float(value), scored["risk_score"])[0])
    return scored.sort_values("risk_score", ascending=False)


def format_route_entity(origin: object, transit: object, destination: object) -> str:
    """Return a compact route label without leaking None/nan into the UI."""
    origin_text = str(origin).strip()
    destination_text = str(destination).strip()
    transit_text = str(transit).strip()
    route = f"{origin_text} → {destination_text}"
    if transit_text.lower() not in {"", "none", "nan", "direct"}:
        route += f" via {transit_text}"
    return route


def build_dss_ranking(
    branch_df: pd.DataFrame,
    destination_df: pd.DataFrame,
    route_df: pd.DataFrame,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    if not branch_df.empty:
        branch_rank = add_risk_score(branch_df).head(5).copy()
        branch_rank["area"] = "Branch"
        branch_rank["entity"] = branch_rank["branch_city"].astype(str)
        frames.append(branch_rank[["area", "entity", "volume", "late_shipments", "late_rate", "avg_duration", "risk_score", "priority"]])

    if not destination_df.empty:
        dest_rank = add_risk_score(destination_df).head(5).copy()
        dest_rank["area"] = "Destination"
        dest_rank["entity"] = dest_rank["destination_city"].astype(str) + ", " + dest_rank["destination_province"].astype(str)
        frames.append(dest_rank[["area", "entity", "volume", "late_shipments", "late_rate", "avg_duration", "risk_score", "priority"]])

    if not route_df.empty:
        route_rank = add_risk_score(route_df).head(5).copy()
        route_rank["area"] = "Route"
        route_rank["entity"] = route_rank.apply(
            lambda row: format_route_entity(
                row["origin_city"],
                row["transit_point"],
                row["destination_city"],
            ),
            axis=1,
        )
        frames.append(route_rank[["area", "entity", "volume", "late_shipments", "late_rate", "avg_duration", "risk_score", "priority"]])

    if not frames:
        return pd.DataFrame()

    ranking = pd.concat(frames, ignore_index=True)
    return ranking.sort_values("risk_score", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# KPI Monitoring System (data-driven)
# ---------------------------------------------------------------------------

KPI_MONITORS: list[dict[str, str]] = [
    {
        "kpi": "On-Time Delivery Rate",
        "description": "Alert aktif jika on-time rate global berada di bawah batas bawah performa cabang.",
        "unit": "%",
        "alert_text": "SLA Below Peer Baseline",
        "method": "Q1 on_time_rate dari distribusi performa cabang.",
    },
    {
        "kpi": "Late Shipment Rate",
        "description": "Alert aktif jika late rate global melewati batas atas risiko keterlambatan area operasional.",
        "unit": "%",
        "alert_text": "Delay Above Risk Baseline",
        "method": "Q3 late_rate dari gabungan branch, service, destination, dan route.",
    },
    {
        "kpi": "Average Duration",
        "description": "Alert aktif jika durasi rata-rata global lebih tinggi dari batas atas durasi rute/cabang.",
        "unit": " hari",
        "alert_text": "Transit Time Above Baseline",
        "method": "Q3 avg_duration dari gabungan branch, destination, dan route.",
    },
    {
        "kpi": "Cost per Shipment",
        "description": "Alert aktif jika biaya rata-rata per shipment melewati batas atas biaya operasional.",
        "unit": "Rp",
        "alert_text": "Cost Above Baseline",
        "method": "Q3 avg_cost dari cabang dan customer segment.",
    },
    {
        "kpi": "Root Cause Concentration",
        "description": "Alert aktif jika satu penyebab delay jauh lebih dominan dibanding penyebab lain.",
        "unit": " kasus",
        "alert_text": "Dominant Root Cause",
        "method": "Mean + 1 standar deviasi dari late_shipments per reason.",
    },
]


def numeric_series(*frames_and_columns: tuple[pd.DataFrame | None, str]) -> pd.Series:
    series_list: list[pd.Series] = []
    for frame, column in frames_and_columns:
        if frame is not None and not frame.empty and column in frame:
            series_list.append(pd.to_numeric(frame[column], errors="coerce"))
    if not series_list:
        return pd.Series(dtype="float64")
    return pd.concat(series_list, ignore_index=True).dropna()


def q1_threshold(series: pd.Series, fallback: float = 0.0) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return float(fallback)
    return float(values.quantile(0.25))


def q3_threshold(series: pd.Series, fallback: float = 0.0) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return float(fallback)
    return float(values.quantile(0.75))


def mean_std_threshold(series: pd.Series, fallback: float = 0.0) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return float(fallback)
    if len(values) == 1:
        return float(values.iloc[0])
    return float(values.mean() + values.std(ddof=0))


def evaluate_kpi_alerts(
    kpis: dict,
    on_time_rate: float,
    avg_cost: float,
    avg_duration: float,
    branch_df: pd.DataFrame | None = None,
    service_df: pd.DataFrame | None = None,
    destination_df: pd.DataFrame | None = None,
    route_df: pd.DataFrame | None = None,
    customer_df: pd.DataFrame | None = None,
    delay_df: pd.DataFrame | None = None,
) -> list[dict]:
    """Evaluate KPI monitors using thresholds derived from the active filtered data."""
    late_rate = float(kpis.get("late_rate", 0) or 0)
    top_reason_count = 0.0
    if delay_df is not None and not delay_df.empty and "late_shipments" in delay_df:
        top_reason_count = float(pd.to_numeric(delay_df["late_shipments"], errors="coerce").fillna(0).max())

    on_time_baseline = q1_threshold(numeric_series((branch_df, "on_time_rate")), fallback=on_time_rate)
    late_rate_baseline = q3_threshold(
        numeric_series(
            (branch_df, "late_rate"),
            (service_df, "late_rate"),
            (destination_df, "late_rate"),
            (route_df, "late_rate"),
        ),
        fallback=late_rate,
    )
    duration_baseline = q3_threshold(
        numeric_series((branch_df, "avg_duration"), (destination_df, "avg_duration"), (route_df, "avg_duration")),
        fallback=avg_duration,
    )
    cost_baseline = q3_threshold(
        numeric_series((branch_df, "avg_cost"), (customer_df, "avg_cost")),
        fallback=avg_cost,
    )
    root_cause_baseline = mean_std_threshold(
        numeric_series((delay_df, "late_shipments")),
        fallback=top_reason_count,
    )

    evaluations = {
        "On-Time Delivery Rate": {
            "actual": on_time_rate,
            "threshold": on_time_baseline,
            "triggered": on_time_rate < on_time_baseline,
            "direction": "below",
        },
        "Late Shipment Rate": {
            "actual": late_rate,
            "threshold": late_rate_baseline,
            "triggered": late_rate > late_rate_baseline,
            "direction": "above",
        },
        "Average Duration": {
            "actual": avg_duration,
            "threshold": duration_baseline,
            "triggered": avg_duration > duration_baseline,
            "direction": "above",
        },
        "Cost per Shipment": {
            "actual": avg_cost,
            "threshold": cost_baseline,
            "triggered": avg_cost > cost_baseline,
            "direction": "above",
        },
        "Root Cause Concentration": {
            "actual": top_reason_count,
            "threshold": root_cause_baseline,
            "triggered": top_reason_count > root_cause_baseline,
            "direction": "above",
        },
    }

    alerts: list[dict] = []
    for monitor in KPI_MONITORS:
        kpi_name = str(monitor["kpi"])
        evaluation = evaluations[kpi_name]
        alerts.append({
            "kpi": kpi_name,
            "description": str(monitor["description"]),
            "threshold": float(evaluation["threshold"]),
            "unit": str(monitor["unit"]),
            "actual": float(evaluation["actual"]),
            "triggered": bool(evaluation["triggered"]),
            "alert_text": str(monitor["alert_text"]),
            "method": str(monitor["method"]),
            "direction": str(evaluation["direction"]),
        })

    return alerts


# ---------------------------------------------------------------------------
# Executive summary insight generation
# ---------------------------------------------------------------------------

def generate_executive_insights(
    kpis: dict,
    late_rate: float,
    on_time_rate: float,
    top_reason: object | None,
    top_route: object | None,
    worst_branch: object | None,
    risky_dest: object | None,
    dss_ranking: pd.DataFrame,
) -> list[dict[str, str]]:
    """Describe only facts calculated from the active warehouse filter."""
    insights: list[dict[str, str]] = []
    total_volume = int(kpis.get("total_volume", 0) or 0)
    total_late = int(kpis.get("total_late", 0) or 0)
    sla_tone = "green" if late_rate < 12 else "yellow" if late_rate < 25 else "red"
    insights.append({
        "title": "Kondisi Pengiriman",
        "body": (
            f"Dari {total_volume:,} shipment pada filter aktif, {total_late:,} terlambat "
            f"({late_rate:.1f}%) dan {on_time_rate:.1f}% tercatat on-time."
        ),
        "tone": sla_tone,
    })

    if top_reason is not None:
        reason_name = str(top_reason["reason_category"])
        reason_count = int(top_reason["late_shipments"])
        reason_share = (reason_count / total_late * 100) if total_late else 0.0
        insights.append({
            "title": f"Root Cause Teratas: {reason_name}",
            "body": (
                f"Terdeteksi {reason_count:,} kasus, setara {reason_share:.1f}% dari seluruh delay. "
                "Peringkat berasal dari jumlah kasus pada filter aktif."
            ),
            "tone": "red" if reason_share >= 35 else "yellow" if reason_share >= 20 else "indigo",
        })

    # Route bottleneck insight
    if top_route is not None:
        route_late = int(top_route["late_shipments"])
        route_rate_gap = float(top_route["late_rate"]) - late_rate
        insights.append({
            "title": "Rute dengan Delay Terbanyak",
            "body": (
                f"{format_route_entity(top_route['origin_city'], top_route['transit_point'], top_route['destination_city'])} "
                f"mencatat {route_late:,} delay, late rate {float(top_route['late_rate']):.1f}%, "
                f"dan durasi rata-rata {float(top_route['avg_duration']):.2f} hari."
            ),
            "tone": "red" if route_rate_gap >= 5 else "yellow" if route_rate_gap >= 0 else "indigo",
        })

    if worst_branch is not None:
        branch_name = str(worst_branch["branch_city"])
        branch_late_rate = float(worst_branch["late_rate"])
        rate_gap = branch_late_rate - late_rate
        insights.append({
            "title": f"Late Rate Cabang Tertinggi: {branch_name}",
            "body": (
                f"Cabang ini mencatat {int(worst_branch['late_shipments']):,} delay dari "
                f"{int(worst_branch['volume']):,} shipment ({branch_late_rate:.1f}%), "
                f"{abs(rate_gap):.1f} poin persentase {'di atas' if rate_gap >= 0 else 'di bawah'} rate global."
            ),
            "tone": "red" if rate_gap >= 5 else "yellow",
        })

    return insights
