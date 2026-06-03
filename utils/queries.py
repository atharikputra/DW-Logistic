from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import text

ALL_VALUE = "Semua"


def _base_from_clause() -> str:
    return """
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
    """


def build_filter_clause(filters: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
    conditions = ["1=1"]
    params: dict[str, Any] = {}
    filters = filters or {}

    if filters.get("date_from"):
        conditions.append("t.date >= :date_from")
        params["date_from"] = filters["date_from"]

    if filters.get("date_to"):
        conditions.append("t.date <= :date_to")
        params["date_to"] = filters["date_to"]

    if filters.get("branch") and filters["branch"] != ALL_VALUE:
        conditions.append("b.city = :branch")
        params["branch"] = filters["branch"]

    if filters.get("service") and filters["service"] != ALL_VALUE:
        conditions.append("s.service_type = :service")
        params["service"] = filters["service"]

    if filters.get("destination") and filters["destination"] != ALL_VALUE:
        conditions.append("d.city = :destination")
        params["destination"] = filters["destination"]

    if filters.get("customer_type") and filters["customer_type"] != ALL_VALUE:
        conditions.append("c.customer_type = :customer_type")
        params["customer_type"] = filters["customer_type"]

    if filters.get("item_category") and filters["item_category"] != ALL_VALUE:
        conditions.append("i.item_category = :item_category")
        params["item_category"] = filters["item_category"]

    return " AND ".join(conditions), params


def _read_sql(engine, query: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    return pd.read_sql(text(query), engine, params=params or {})


def get_filter_options(engine) -> dict[str, Any]:
    date_range = _read_sql(
        engine,
        """
        SELECT MIN(date) AS min_date, MAX(date) AS max_date
        FROM dim_time
        """,
    ).iloc[0]

    return {
        "min_date": date_range["min_date"],
        "max_date": date_range["max_date"],
        "branches": _read_sql(engine, "SELECT DISTINCT city FROM dim_branch ORDER BY city")["city"].dropna().tolist(),
        "services": _read_sql(engine, "SELECT DISTINCT service_type FROM dim_service ORDER BY service_type")["service_type"].dropna().tolist(),
        "destinations": _read_sql(engine, "SELECT DISTINCT city FROM dim_destination ORDER BY city")["city"].dropna().tolist(),
        "customer_types": _read_sql(engine, "SELECT DISTINCT customer_type FROM dim_customer ORDER BY customer_type")["customer_type"].dropna().tolist(),
        "item_categories": _read_sql(engine, "SELECT DISTINCT item_category FROM dim_item ORDER BY item_category")["item_category"].dropna().tolist(),
    }


def get_warehouse_overview(engine) -> pd.Series:
    query = f"""
        SELECT
            COUNT(*) AS fact_rows,
            MIN(t.date) AS min_date,
            MAX(t.date) AS max_date,
            COUNT(DISTINCT t.date) AS active_days,
            COUNT(DISTINCT b.branch_id) AS branch_count,
            COUNT(DISTINCT d.city) AS destination_count
        {_base_from_clause()}
    """
    df = _read_sql(engine, query)
    return df.iloc[0] if not df.empty else pd.Series(dtype="object")


def get_kpis(engine, filters: dict[str, Any] | None = None) -> pd.Series | None:
    where_clause, params = build_filter_clause(filters)
    query = f"""
        SELECT
            COUNT(f.nomor_resi) AS total_volume,
            COALESCE(SUM(f.shipping_cost), 0) AS total_revenue,
            COALESCE(AVG(f.shipping_cost), 0) AS avg_cost,
            COALESCE(AVG(f.shipping_duration), 0) AS avg_duration,
            COALESCE(SUM(CASE WHEN f.is_late = 1 THEN 1 ELSE 0 END), 0) AS total_late,
            COALESCE(AVG(f.is_late::numeric), 0) * 100 AS late_rate,
            COALESCE(AVG(CASE WHEN f.is_late = 0 THEN 1 ELSE 0 END::numeric), 0) * 100 AS on_time_rate
        {_base_from_clause()}
        WHERE {where_clause}
    """
    df = _read_sql(engine, query, params)
    return df.iloc[0] if not df.empty else None


def get_trend_data(engine, filters: dict[str, Any] | None = None, grain: str = "month") -> pd.DataFrame:
    period_expr = {
        "day": "t.date",
        "week": "DATE_TRUNC('week', t.date::timestamp)::date",
        "month": "DATE_TRUNC('month', t.date::timestamp)::date",
    }.get(grain, "DATE_TRUNC('month', t.date::timestamp)::date")

    where_clause, params = build_filter_clause(filters)
    query = f"""
        SELECT
            {period_expr} AS period_start,
            COUNT(f.nomor_resi) AS volume,
            COALESCE(SUM(f.is_late), 0) AS late_shipments,
            COALESCE(AVG(f.is_late::numeric), 0) * 100 AS late_rate,
            COALESCE(AVG(f.shipping_duration), 0) AS avg_duration,
            COALESCE(SUM(f.shipping_cost), 0) AS revenue
        {_base_from_clause()}
        WHERE {where_clause}
        GROUP BY 1
        ORDER BY 1
    """
    return _read_sql(engine, query, params)


def get_branch_performance(engine, filters: dict[str, Any] | None = None) -> pd.DataFrame:
    where_clause, params = build_filter_clause(filters)
    query = f"""
        SELECT
            b.city AS branch_city,
            b.branch_name,
            COUNT(f.nomor_resi) AS volume,
            COALESCE(SUM(f.is_late), 0) AS late_shipments,
            COALESCE(AVG(f.is_late::numeric), 0) * 100 AS late_rate,
            COALESCE(AVG(CASE WHEN f.is_late = 0 THEN 1 ELSE 0 END::numeric), 0) * 100 AS on_time_rate,
            COALESCE(AVG(f.shipping_duration), 0) AS avg_duration,
            COALESCE(AVG(f.shipping_cost), 0) AS avg_cost,
            COALESCE(SUM(f.shipping_cost), 0) AS revenue
        {_base_from_clause()}
        WHERE {where_clause}
        GROUP BY b.city, b.branch_name
        ORDER BY late_rate DESC, volume DESC
    """
    return _read_sql(engine, query, params)


def get_service_performance(engine, filters: dict[str, Any] | None = None) -> pd.DataFrame:
    where_clause, params = build_filter_clause(filters)
    query = f"""
        SELECT
            s.service_type,
            s.service_name,
            s.sla_days,
            COUNT(f.nomor_resi) AS volume,
            COALESCE(SUM(f.is_late), 0) AS late_shipments,
            COALESCE(AVG(f.is_late::numeric), 0) * 100 AS late_rate,
            COALESCE(AVG(f.shipping_duration), 0) AS avg_duration,
            COALESCE(SUM(f.shipping_cost), 0) AS revenue
        {_base_from_clause()}
        WHERE {where_clause}
        GROUP BY s.service_type, s.service_name, s.sla_days
        ORDER BY late_rate DESC, volume DESC
    """
    return _read_sql(engine, query, params)


def get_destination_risk(engine, filters: dict[str, Any] | None = None, limit: int = 15) -> pd.DataFrame:
    where_clause, params = build_filter_clause(filters)
    params["limit"] = limit
    query = f"""
        SELECT
            d.city AS destination_city,
            d.province AS destination_province,
            COUNT(f.nomor_resi) AS volume,
            COALESCE(SUM(f.is_late), 0) AS late_shipments,
            COALESCE(AVG(f.is_late::numeric), 0) * 100 AS late_rate,
            COALESCE(AVG(f.shipping_duration), 0) AS avg_duration,
            COALESCE(AVG(f.shipping_cost), 0) AS avg_cost
        {_base_from_clause()}
        WHERE {where_clause}
        GROUP BY d.city, d.province
        HAVING COUNT(f.nomor_resi) > 0
        ORDER BY late_rate DESC, late_shipments DESC, volume DESC
        LIMIT :limit
    """
    return _read_sql(engine, query, params)


def get_delay_reasons(engine, filters: dict[str, Any] | None = None, limit: int = 10) -> pd.DataFrame:
    where_clause, params = build_filter_clause(filters)
    params["limit"] = limit
    query = f"""
        SELECT
            rs.reason_category,
            COUNT(f.nomor_resi) AS late_shipments,
            COALESCE(AVG(f.shipping_duration), 0) AS avg_duration
        {_base_from_clause()}
        WHERE {where_clause} AND f.is_late = 1
        GROUP BY rs.reason_category
        ORDER BY late_shipments DESC
        LIMIT :limit
    """
    return _read_sql(engine, query, params)


def get_delay_reason_by_branch(engine, filters: dict[str, Any] | None = None) -> pd.DataFrame:
    where_clause, params = build_filter_clause(filters)
    query = f"""
        SELECT
            b.city AS branch_city,
            rs.reason_category,
            COUNT(f.nomor_resi) AS late_shipments
        {_base_from_clause()}
        WHERE {where_clause} AND f.is_late = 1
        GROUP BY b.city, rs.reason_category
        ORDER BY b.city, late_shipments DESC
    """
    return _read_sql(engine, query, params)


def get_route_bottlenecks(engine, filters: dict[str, Any] | None = None, limit: int = 20) -> pd.DataFrame:
    where_clause, params = build_filter_clause(filters)
    params["limit"] = limit
    query = f"""
        SELECT
            b.city AS origin_city,
            r.transit_point,
            d.city AS destination_city,
            COUNT(f.nomor_resi) AS volume,
            COALESCE(SUM(f.is_late), 0) AS late_shipments,
            COALESCE(AVG(f.is_late::numeric), 0) * 100 AS late_rate,
            COALESCE(AVG(f.shipping_duration), 0) AS avg_duration
        {_base_from_clause()}
        WHERE {where_clause}
        GROUP BY b.city, r.transit_point, d.city
        HAVING COUNT(f.nomor_resi) > 0
        ORDER BY late_shipments DESC, late_rate DESC, volume DESC
        LIMIT :limit
    """
    return _read_sql(engine, query, params)


def get_customer_segments(engine, filters: dict[str, Any] | None = None) -> pd.DataFrame:
    where_clause, params = build_filter_clause(filters)
    query = f"""
        SELECT
            c.customer_type,
            COUNT(f.nomor_resi) AS volume,
            COALESCE(SUM(f.is_late), 0) AS late_shipments,
            COALESCE(AVG(f.is_late::numeric), 0) * 100 AS late_rate,
            COALESCE(AVG(f.shipping_cost), 0) AS avg_cost,
            COALESCE(SUM(f.shipping_cost), 0) AS revenue
        {_base_from_clause()}
        WHERE {where_clause}
        GROUP BY c.customer_type
        ORDER BY volume DESC
    """
    return _read_sql(engine, query, params)


def get_item_category_performance(engine, filters: dict[str, Any] | None = None) -> pd.DataFrame:
    where_clause, params = build_filter_clause(filters)
    query = f"""
        SELECT
            i.item_category,
            COUNT(f.nomor_resi) AS volume,
            COALESCE(SUM(f.is_late), 0) AS late_shipments,
            COALESCE(AVG(f.is_late::numeric), 0) * 100 AS late_rate,
            COALESCE(AVG(i.weight_kg), 0) AS avg_weight,
            COALESCE(SUM(CASE WHEN i.fragile_status THEN 1 ELSE 0 END), 0) AS fragile_shipments
        {_base_from_clause()}
        WHERE {where_clause}
        GROUP BY i.item_category
        ORDER BY late_rate DESC, volume DESC
    """
    return _read_sql(engine, query, params)


def get_detail_rows(engine, filters: dict[str, Any] | None = None, limit: int = 200) -> pd.DataFrame:
    where_clause, params = build_filter_clause(filters)
    params["limit"] = limit
    query = f"""
        SELECT
            f.nomor_resi,
            t.date AS shipping_date,
            b.city AS branch_city,
            s.service_type,
            d.city AS destination_city,
            c.customer_type,
            i.item_category,
            i.weight_kg,
            st.status_name,
            rs.reason_category,
            f.shipping_duration,
            f.shipping_cost,
            f.is_late
        {_base_from_clause()}
        WHERE {where_clause}
        ORDER BY t.date DESC, f.nomor_resi
        LIMIT :limit
    """
    return _read_sql(engine, query, params)
