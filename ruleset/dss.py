"""
Decision Support System (DSS) untuk Logistics Data Warehouse.

Modul ini berisi:
- Kalkulasi risk score (weighted: late_rate 50%, late_volume 30%, avg_duration 20%)
- Build DSS ranking dari branch, destination, dan route
- Framework Manage-Control-Measure untuk setiap delay reason
- KPI Monitoring System dengan alert dan threshold
- Business Value analysis (before/after comparison)
- Actionable recommendation per root cause
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


def best_action_text(late_rate_value: float) -> str:
    if late_rate_value >= 25:
        return "Escalate kapasitas dan audit root cause harian pada area risiko tertinggi."
    if late_rate_value >= 12:
        return "Prioritaskan monitoring cabang/rute teratas sebelum risiko melebar."
    return "Pertahankan operasi, gunakan dashboard sebagai early warning batch berikutnya."


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
        route_rank["entity"] = (
            route_rank["origin_city"].astype(str)
            + " -> "
            + route_rank["transit_point"].astype(str)
            + " -> "
            + route_rank["destination_city"].astype(str)
        )
        frames.append(route_rank[["area", "entity", "volume", "late_shipments", "late_rate", "avg_duration", "risk_score", "priority"]])

    if not frames:
        return pd.DataFrame()

    ranking = pd.concat(frames, ignore_index=True)
    return ranking.sort_values("risk_score", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Manage-Control-Measure framework per delay reason
# ---------------------------------------------------------------------------

DELAY_REASON_MCM: dict[str, dict[str, str]] = {
    "Gudang Overload": {
        "manage": "Tambah shift operasional gudang dan alokasikan buffer area untuk peak season. "
                  "Koordinasi dengan tim warehouse untuk redistribusi beban antar hub.",
        "control": "Pantau utilisasi gudang harian via dashboard. Gunakan batas risiko dinamis dari kuartil atas "
                   "utilisasi/durasi operasional pada data aktif.",
        "measure": "Picking cycle time, warehouse utilization rate, dan throughput per shift dibandingkan dengan "
                   "baseline Q3 dari data warehouse.",
    },
    "Kendala Armada": {
        "manage": "Siapkan armada cadangan dan kontrak mitra logistik tambahan untuk antisipasi lonjakan volume. "
                  "Buat jadwal maintenance preventif agar armada tidak breakdown di saat kritis.",
        "control": "Monitor ketersediaan armada real-time. Terapkan sistem rotasi kendaraan dengan jadwal maintenance "
                   "terstruktur. Review kapasitas armada setiap minggu.",
        "measure": "Vehicle utilization rate, breakdown frequency, dan fleet availability dibandingkan dengan "
                   "baseline historis/rata-rata performa armada.",
    },
    "Alamat Tidak Ditemukan": {
        "manage": "Implementasikan validasi alamat otomatis saat input order menggunakan geocoding API. "
                  "Standardisasi format alamat dan wajibkan kelengkapan data sebelum pengiriman.",
        "control": "Review dan bersihkan data alamat pelanggan secara berkala. "
                   "Buat SOP verifikasi alamat untuk kurir sebelum berangkat.",
        "measure": "Address accuracy rate, return-to-sender rate, dan first attempt delivery success rate "
                   "dibandingkan dengan distribusi data pengiriman aktif.",
    },
    "Penerima Tidak Ada": {
        "manage": "Implementasikan notifikasi otomatis (SMS/WhatsApp) kepada penerima 1 hari dan 2 jam sebelum "
                  "estimasi pengiriman. Sediakan opsi reschedule dan titik pickup alternatif.",
        "control": "Tracking jumlah percobaan pengiriman gagal per kurir dan wilayah. "
                   "Terapkan sistem appointment-based delivery untuk area berulang.",
        "measure": "First attempt delivery rate, notification response rate, dan re-delivery cost per shipment "
                   "dibandingkan dengan baseline data aktif.",
    },
    "Cuaca Ekstrem": {
        "manage": "Integrasikan data cuaca real-time ke sistem routing. Siapkan contingency plan untuk rute "
                  "rawan cuaca. Komunikasikan proaktif ke pelanggan soal potensi keterlambatan.",
        "control": "Monitor prakiraan cuaca 48 jam ke depan untuk semua rute aktif. "
                   "Aktifkan rute alternatif saat ada peringatan cuaca ekstrem.",
        "measure": "Weather-related delay rate, proactive customer notification rate, dan average recovery time "
                   "dibandingkan dengan rata-rata dan kuartil risiko periode aktif.",
    },
    "Kendala Operasional Kapal/Pesawat": {
        "manage": "Diversifikasi mitra transportasi antar-pulau. Siapkan buffer waktu SLA +1 hari untuk rute "
                  "laut/udara. Negosiasikan priority booking dengan carrier utama.",
        "control": "Monitor jadwal keberangkatan kapal/pesawat real-time. Terapkan early booking system "
                   "dan tracking status kargo end-to-end.",
        "measure": "Carrier on-time performance, inter-island transit time variance, dan booking confirmation lead time "
                   "dibandingkan dengan baseline performa carrier/rute.",
    },
}


def get_delay_mcm(reason_category: str) -> dict[str, str]:
    """Return Manage-Control-Measure recommendation for a given delay reason."""
    return DELAY_REASON_MCM.get(
        reason_category,
        {
            "manage": "Identifikasi akar masalah spesifik dan buat action plan terstruktur.",
            "control": "Pantau frekuensi kejadian dan terapkan early warning system.",
            "measure": "Track frequency, impact on SLA, dan cost of delay.",
        },
    )


# ---------------------------------------------------------------------------
# KPI Monitoring System (data-driven)
# ---------------------------------------------------------------------------

KPI_MONITORS: list[dict[str, str]] = [
    {
        "kpi": "On-Time Delivery Rate",
        "description": "Alert aktif jika on-time rate global berada di bawah batas bawah performa cabang.",
        "unit": "%",
        "alert_text": "SLA Below Peer Baseline",
        "action": "Review cabang dan rute dengan late rate tertinggi karena performa global berada di bawah baseline data.",
        "method": "Q1 on_time_rate dari distribusi performa cabang.",
    },
    {
        "kpi": "Late Shipment Rate",
        "description": "Alert aktif jika late rate global melewati batas atas risiko keterlambatan area operasional.",
        "unit": "%",
        "alert_text": "Delay Above Risk Baseline",
        "action": "Prioritaskan area di Risk Ranking dengan kontribusi late shipment terbesar.",
        "method": "Q3 late_rate dari gabungan branch, service, destination, dan route.",
    },
    {
        "kpi": "Average Duration",
        "description": "Alert aktif jika durasi rata-rata global lebih tinggi dari batas atas durasi rute/cabang.",
        "unit": " hari",
        "alert_text": "Transit Time Above Baseline",
        "action": "Audit rute dengan avg_duration tertinggi dan cek bottleneck transit point.",
        "method": "Q3 avg_duration dari gabungan branch, destination, dan route.",
    },
    {
        "kpi": "Cost per Shipment",
        "description": "Alert aktif jika biaya rata-rata per shipment melewati batas atas biaya operasional.",
        "unit": "Rp",
        "alert_text": "Cost Above Baseline",
        "action": "Evaluasi layanan, rute, dan customer segment dengan biaya rata-rata tertinggi.",
        "method": "Q3 avg_cost dari cabang dan customer segment.",
    },
    {
        "kpi": "Root Cause Concentration",
        "description": "Alert aktif jika satu penyebab delay jauh lebih dominan dibanding penyebab lain.",
        "unit": " kasus",
        "alert_text": "Dominant Root Cause",
        "action": "Jalankan Manage-Control-Measure untuk root cause dominan terlebih dahulu.",
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
            "action": str(monitor["action"]),
            "method": str(monitor["method"]),
            "direction": str(evaluation["direction"]),
        })

    return alerts


# ---------------------------------------------------------------------------
# Business Value - Before/After comparison
# ---------------------------------------------------------------------------

BUSINESS_VALUE_TABLE: list[dict[str, str]] = [
    {
        "aspek": "Picking Cycle Time",
        "before": "8.5 menit/order dan juga masih manual",
        "after": "<3 menit/order dengan rute Warehouse Management System (WMS)",
        "impact": "Waktu picking berkurang sekitar 65%",
    },
    {
        "aspek": "Inventory Record Accuracy",
        "before": "92.4% dan juga rawan human error",
        "after": ">99.5% dengan validasi barcode/RFID otomatis",
        "impact": "Akurasi stok yang meningkat",
    },
    {
        "aspek": "Dead Stock Ratio",
        "before": "12% (~480 SKU) dead stock",
        "after": "Dead stock dapat terdeteksi secara otomatis melalui RFID alert",
        "impact": "Modal kerja menjadi lebih lancar",
    },
    {
        "aspek": "Performance Monitoring",
        "before": "Manual reporting 24-48 jam",
        "after": "Dashboard secara real-time",
        "impact": "Keputusan yang lebih cepat",
    },
    {
        "aspek": "Data Visibility Rate",
        "before": "Tidak ada tracking real-time dan tracking lokasi masih manual",
        "after": "Lokasi barang terpantau secara real-time",
        "impact": "Barang jadi lebih mudah untuk dilacak",
    },
    {
        "aspek": "Human Error",
        "before": "Validasi yang manual menyebabkan rawan error",
        "after": "Barang mudah tervalidasi otomatis dengan barcode/RFID",
        "impact": "Kesalahan proses berkurang sehingga retur dan rework menurun",
    },
]


def get_business_value_df() -> pd.DataFrame:
    """Return a DataFrame with business value before/after analysis."""
    return pd.DataFrame(BUSINESS_VALUE_TABLE)


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
    """
    Generate executive-level insight narratives for the managerial view.
    Each insight has a title, description, and severity (green/yellow/red).
    """
    insights: list[dict[str, str]] = []

    # SLA Health insight
    if on_time_rate >= 90:
        insights.append({
            "title": "SLA Performance Sehat",
            "body": f"On-time delivery rate saat ini berada di {on_time_rate:.1f}%, di atas target 90%. "
                    "Operasi berjalan normal dan SLA terjaga. Fokus pada mempertahankan konsistensi.",
            "tone": "green",
        })
    elif on_time_rate >= 75:
        insights.append({
            "title": "SLA Performance Perlu Perhatian",
            "body": f"On-time delivery rate turun ke {on_time_rate:.1f}%, mendekati batas bawah toleransi. "
                    "Perlu monitoring intensif pada area dengan late rate tertinggi sebelum situasi memburuk.",
            "tone": "yellow",
        })
    else:
        insights.append({
            "title": "SLA Performance Kritis",
            "body": f"On-time delivery rate hanya {on_time_rate:.1f}%, jauh di bawah target 90%. "
                    "Diperlukan eskalasi segera dan intervensi operasional pada root cause utama.",
            "tone": "red",
        })

    # Root cause insight
    if top_reason is not None:
        reason_name = str(top_reason["reason_category"])
        reason_count = int(top_reason["late_shipments"])
        mcm = get_delay_mcm(reason_name)
        insights.append({
            "title": f"Root Cause Dominan: {reason_name}",
            "body": f"Penyebab delay terbanyak adalah \"{reason_name}\" dengan {reason_count:,} kasus. "
                    f"Rekomendasi: {mcm['manage'].split('.')[0]}.",
            "tone": "red" if reason_count > 500 else "yellow",
        })

    # Route bottleneck insight
    if top_route is not None:
        route_str = f"{top_route['origin_city']} → {top_route['transit_point']} → {top_route['destination_city']}"
        route_late = int(top_route["late_shipments"])
        insights.append({
            "title": "Bottleneck Rute Teridentifikasi",
            "body": f"Rute {route_str} menyumbang {route_late:,} keterlambatan. "
                    "Perlu evaluasi kapasitas transit hub dan pertimbangkan rute alternatif.",
            "tone": "yellow",
        })

    # Branch insight
    if worst_branch is not None:
        branch_name = str(worst_branch["branch_city"])
        branch_late_rate = float(worst_branch["late_rate"])
        insights.append({
            "title": f"Cabang Prioritas: {branch_name}",
            "body": f"Cabang {branch_name} memiliki late rate {branch_late_rate:.1f}%, tertinggi dari semua cabang. "
                    "Audit operasional dan review kapasitas gudang cabang ini perlu diprioritaskan.",
            "tone": "red" if branch_late_rate >= 25 else "yellow",
        })

    return insights
