"""Production-grade demo data for hackathon presentations."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import random

SITES = [
    {"id": "site-manhattan-01", "name": "Manhattan Campus", "city": "New York, NY", "type": "Campus", "capacity_mw": 2.5, "assets": 12, "status": "optimal", "lat": 40.71, "lng": -74.01},
    {"id": "site-brooklyn-02", "name": "Brooklyn Data Center", "city": "Brooklyn, NY", "type": "Data Center", "capacity_mw": 8.0, "assets": 34, "status": "optimal", "lat": 40.65, "lng": -73.95},
    {"id": "site-jersey-03", "name": "Newark Industrial Park", "city": "Newark, NJ", "type": "Industrial", "capacity_mw": 5.2, "assets": 22, "status": "elevated", "lat": 40.73, "lng": -74.17},
    {"id": "site-stamford-04", "name": "Stamford Hospital", "city": "Stamford, CT", "type": "Healthcare", "capacity_mw": 3.1, "assets": 18, "status": "optimal", "lat": 41.05, "lng": -73.54},
    {"id": "site-philly-05", "name": "Philadelphia Microgrid", "city": "Philadelphia, PA", "type": "Microgrid", "capacity_mw": 4.0, "assets": 28, "status": "warning", "lat": 39.95, "lng": -75.16},
    {"id": "site-boston-06", "name": "Cambridge Research Lab", "city": "Cambridge, MA", "type": "R&D", "capacity_mw": 1.8, "assets": 9, "status": "optimal", "lat": 42.36, "lng": -71.09},
]

ACTIVITIES = [
    ("optimization", "Battery dispatch optimized for peak shaving", "Manhattan Campus", "success"),
    ("anomaly", "Voltage sag detected on Feeder B-12", "Philadelphia Microgrid", "warning"),
    ("carbon", "Carbon budget 78% utilized for Q3", "Portfolio", "info"),
    ("market", "DR event dispatched — 450 kW curtailed", "Brooklyn Data Center", "success"),
    ("forecast", "Heat wave forecast updated — +12% cooling load", "Newark Industrial", "info"),
    ("automation", "EV fleet charging shifted to off-peak window", "Stamford Hospital", "success"),
    ("compliance", "NERC CIP audit evidence auto-collected", "Portfolio", "success"),
    ("resilience", "Islanding test completed — 99.2% success", "Cambridge Research Lab", "success"),
]


def get_portfolio() -> dict:
    sites = []
    total_load = 0
    total_solar = 0
    total_savings = 0
    for i, s in enumerate(SITES):
        load = round(random.uniform(400, 1800) if s["status"] != "warning" else random.uniform(1200, 2200), 0)
        solar = round(random.uniform(50, 600) if 6 <= datetime.now().hour <= 18 else random.uniform(0, 80), 0)
        savings = round(random.uniform(800, 4500), 0)
        total_load += load
        total_solar += solar
        total_savings += savings
        sites.append({
            **s,
            "load_kw": load,
            "solar_kw": solar,
            "battery_soc": round(random.uniform(35, 92), 1),
            "grid_import_kw": max(0, load - solar - random.uniform(50, 200)),
            "savings_mtd_usd": savings,
            "carbon_intensity": round(random.uniform(240, 480), 0),
            "renewable_pct": round(solar / max(load, 1) * 100, 1),
            "uptime_pct": round(random.uniform(99.5, 99.99), 2),
        })

    return {
        "total_sites": len(sites),
        "total_load_kw": round(total_load, 0),
        "total_solar_kw": round(total_solar, 0),
        "total_savings_mtd_usd": round(total_savings, 0),
        "avg_renewable_pct": round(total_solar / max(total_load, 1) * 100, 1),
        "portfolio_carbon_kg_24h": round(total_load * 0.35, 0),
        "active_alerts": sum(1 for s in sites if s["status"] in ("warning", "critical")),
        "sites": sites,
    }


def get_vpp_status() -> dict:
    return {
        "vpp_name": "GridMind Northeast VPP",
        "aggregated_capacity_kw": 2840,
        "available_capacity_kw": 1920,
        "enrolled_assets": 127,
        "active_bids": 3,
        "revenue_mtd_usd": 47820,
        "markets": [
            {"name": "NYISO Day-Ahead", "status": "active", "bid_kw": 800, "clearing_price": 0.142, "revenue_usd": 18400},
            {"name": "Con Edison DR", "status": "active", "bid_kw": 450, "clearing_price": 0.28, "revenue_usd": 12600},
            {"name": "Ancillary — Regulation", "status": "standby", "bid_kw": 200, "clearing_price": 0.065, "revenue_usd": 3200},
            {"name": "Capacity Market", "status": "scheduled", "bid_kw": 1200, "clearing_price": 8.50, "revenue_usd": 13620},
        ],
        "dispatch_schedule": [
            {"hour": h, "committed_kw": round(random.uniform(200, 900)), "price_usd": round(random.uniform(0.06, 0.22), 3)}
            for h in range(24)
        ],
    }


def get_activity_feed(limit: int = 15) -> list[dict]:
    now = datetime.now(UTC)
    feed = []
    for i, (atype, msg, site, level) in enumerate(ACTIVITIES[:limit]):
        feed.append({
            "id": f"act-{i}",
            "type": atype,
            "message": msg,
            "site": site,
            "level": level,
            "timestamp": (now - timedelta(minutes=i * 7 + random.randint(1, 5))).isoformat(),
            "automated": atype in ("optimization", "automation", "compliance", "market"),
        })
    return feed


def get_esg_report() -> dict:
    return {
        "reporting_period": "Q3 2026",
        "overall_score": 87,
        "scores": {
            "carbon_reduction": {"score": 92, "target": 85, "unit": "% vs baseline", "value": 34.2},
            "renewable_utilization": {"score": 78, "target": 80, "unit": "%", "value": 62.4},
            "grid_resilience": {"score": 89, "target": 90, "unit": "/100", "value": 89},
            "energy_efficiency": {"score": 85, "target": 82, "unit": "kWh/sqft", "value": 12.3},
            "compliance": {"score": 94, "target": 95, "unit": "%", "value": 96.1},
        },
        "certifications": ["ISO 50001", "LEED Gold", "GRESB 4-Star"],
        "emissions": {
            "scope1_kg": 1240,
            "scope2_kg": 48200,
            "scope3_kg": 8900,
            "total_kg": 58340,
            "yoy_change_pct": -18.4,
        },
        "renewable_mwh": 2840,
        "carbon_offset_mwh": 420,
    }


def get_digital_twin(site_id: str = "site-manhattan-01") -> dict:
    return {
        "site_id": site_id,
        "topology": {
            "grid_connection": {"status": "connected", "voltage_v": 12480, "capacity_kva": 5000},
            "solar_array": {"status": "generating", "capacity_kw": 500, "output_kw": round(random.uniform(200, 480), 0), "inverters_online": 8},
            "battery_storage": {"status": "discharging", "capacity_kwh": 2000, "soc_pct": round(random.uniform(40, 85), 1), "power_kw": round(random.uniform(-200, 300), 0)},
            "load_centers": [
                {"name": "Building A — HVAC", "load_kw": round(random.uniform(200, 400), 0), "status": "normal"},
                {"name": "Building B — Lighting", "load_kw": round(random.uniform(80, 150), 0), "status": "normal"},
                {"name": "EV Charging Hub", "load_kw": round(random.uniform(50, 200), 0), "status": "charging"},
                {"name": "Critical Loads", "load_kw": round(random.uniform(100, 180), 0), "status": "protected"},
            ],
            "transformers": [
                {"id": "T-01", "load_pct": 72, "temp_c": 58, "status": "normal"},
                {"id": "T-02", "load_pct": 45, "temp_c": 42, "status": "normal"},
            ],
        },
        "autonomy_level": "execute_with_approval",
        "last_optimization": (datetime.now(UTC) - timedelta(minutes=12)).isoformat(),
        "next_dr_event": (datetime.now(UTC) + timedelta(hours=4, minutes=30)).isoformat(),
    }


def get_notifications() -> list[dict]:
    return [
        {"id": "n1", "title": "Peak demand alert in 2 hours", "body": "Manhattan Campus projected to exceed 1,400 kW. Battery pre-charge recommended.", "severity": "warning", "read": False, "time": "2m ago"},
        {"id": "n2", "title": "DR event scheduled", "body": "Con Edison demand response event tomorrow 2–6 PM. 450 kW committed.", "severity": "info", "read": False, "time": "15m ago"},
        {"id": "n3", "title": "Optimization complete", "body": "Saved $847 across portfolio in last 24h.", "severity": "success", "read": True, "time": "1h ago"},
        {"id": "n4", "title": "Anomaly resolved", "body": "Voltage sag on Philadelphia Feeder B-12 — auto-corrected.", "severity": "success", "read": True, "time": "3h ago"},
    ]


def get_executive_summary() -> dict:
    return {
        "period": "Last 30 Days",
        "total_energy_kwh": 4_820_000,
        "total_cost_usd": 412_800,
        "cost_savings_usd": 67_400,
        "savings_pct": 14.0,
        "peak_reduction_kw": 2340,
        "carbon_avoided_tons": 184,
        "renewable_pct": 38.2,
        "uptime_pct": 99.97,
        "automation_rate_pct": 94.2,
        "roi_annual_pct": 23.5,
    }
