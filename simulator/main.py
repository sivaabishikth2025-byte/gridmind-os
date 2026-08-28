"""Physics-based grid microgrid simulator with real weather integration."""

from __future__ import annotations

import math
import random
from datetime import UTC, datetime, timedelta

import httpx
import numpy as np
from fastapi import FastAPI

app = FastAPI(title="GridMind Grid Simulator")

SITE_ID = "site-manhattan-01"
BASE_LOAD_KW = 850.0
SOLAR_CAPACITY_KW = 500.0
BATTERY_CAPACITY_KWH = 2000.0
BATTERY_MAX_POWER_KW = 500.0
BATTERY_EFFICIENCY = 0.92

# Simulated state
_state = {
    "battery_soc": 55.0,
    "battery_power_kw": 0.0,
    "battery_temp_c": 28.0,
    "battery_mode": "auto",
    "tick": 0,
    "anomaly_injected": False,
}

NYISO_SHAPE = np.array([
    0.62, 0.58, 0.55, 0.54, 0.56, 0.60, 0.68, 0.78, 0.85, 0.90, 0.93, 0.95,
    0.94, 0.92, 0.90, 0.91, 0.94, 0.98, 1.00, 0.97, 0.90, 0.82, 0.74, 0.67,
])

_weather_cache: dict = {"fetched_at": None, "irradiance": 0.0, "cloud_cover": 30.0, "temp_c": 22.0}


async def _fetch_weather() -> dict:
    now = datetime.now(UTC)
    if _weather_cache["fetched_at"] and (now - _weather_cache["fetched_at"]).seconds < 600:
        return _weather_cache

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://api.open-meteo.com/v1/forecast", params={
                "latitude": 40.7128,
                "longitude": -74.0060,
                "current": "temperature_2m,cloud_cover",
                "hourly": "direct_normal_irradiance",
                "forecast_days": 1,
                "timezone": "America/New_York",
            })
            data = resp.json()
            current = data.get("current", {})
            hourly = data.get("hourly", {})
            hour_idx = datetime.now().astimezone().hour
            irr = hourly.get("direct_normal_irradiance", [0])[hour_idx] or 0
            _weather_cache.update({
                "fetched_at": now,
                "irradiance": irr,
                "cloud_cover": current.get("cloud_cover", 30),
                "temp_c": current.get("temperature_2m", 22),
            })
    except Exception:
        hour = datetime.now().astimezone().hour
        _weather_cache.update({
            "fetched_at": now,
            "irradiance": max(0, 800 * math.sin(math.pi * (hour - 6) / 12)) if 6 <= hour <= 18 else 0,
            "cloud_cover": 30,
            "temp_c": 22,
        })
    return _weather_cache


def _compute_load(hour: int, is_weekend: bool, temp_c: float, tick: int) -> float:
    shape = float(NYISO_SHAPE[hour])
    load = BASE_LOAD_KW * shape
    if is_weekend:
        load *= 0.82

    # Temperature sensitivity
    if temp_c > 24:
        load *= 1 + (temp_c - 24) * 0.025
    elif temp_c < 10:
        load *= 1 + (10 - temp_c) * 0.02

    noise = random.gauss(0, load * 0.02)
    # Occasional equipment startup spike
    if tick % 47 == 0:
        noise += load * 0.15

    return max(200, load + noise)


def _compute_solar(irradiance: float, cloud_cover: float) -> float:
    if irradiance <= 0:
        return 0.0
    cloud_factor = 1 - (cloud_cover / 100) * 0.6
    efficiency = 0.85
    return max(0, min(SOLAR_CAPACITY_KW, irradiance / 1000 * SOLAR_CAPACITY_KW * efficiency * cloud_factor))


def _battery_dispatch(soc: float, net_load: float, hour: int) -> float:
    """Simple rule-based dispatch — charge off-peak, discharge on-peak."""
    price_signal = NYISO_SHAPE[hour]
    power = 0.0

    if price_signal < 0.65 and soc < 90:
        power = -min(BATTERY_MAX_POWER_KW, (90 - soc) / 100 * BATTERY_CAPACITY_KWH)
    elif price_signal > 0.92 and soc > 20:
        power = min(BATTERY_MAX_POWER_KW, (soc - 20) / 100 * BATTERY_CAPACITY_KWH)

    if net_load > 1100 and soc > 25:
        power = min(BATTERY_MAX_POWER_KW, net_load - 1000, (soc - 15) / 100 * BATTERY_CAPACITY_KWH)

    return power


def _update_soc(soc: float, power_kw: float, interval_hours: float = 0.25) -> float:
    if power_kw > 0:
        soc -= (power_kw / BATTERY_EFFICIENCY) * interval_hours / BATTERY_CAPACITY_KWH * 100
    else:
        soc += (-power_kw * BATTERY_EFFICIENCY) * interval_hours / BATTERY_CAPACITY_KWH * 100
    return max(10, min(98, soc))


@app.get("/readings")
async def get_readings():
    global _state
    weather = await _fetch_weather()
    now = datetime.now(UTC)
    local = now.astimezone()
    hour = local.hour
    is_weekend = local.weekday() >= 5
    _state["tick"] += 1

    load_kw = _compute_load(hour, is_weekend, weather["temp_c"], _state["tick"])
    solar_kw = _compute_solar(weather["irradiance"], weather["cloud_cover"])

    net_before_battery = load_kw - solar_kw
    batt_power = _battery_dispatch(_state["battery_soc"], net_before_battery, hour)
    _state["battery_soc"] = _update_soc(_state["battery_soc"], batt_power)
    _state["battery_power_kw"] = batt_power
    _state["battery_temp_c"] = 26 + abs(batt_power) / 50 + random.gauss(0, 0.5)

    grid_import = max(0, net_before_battery - batt_power)
    voltage = 120.0 + random.gauss(0, 0.8)
    frequency = 60.0 + random.gauss(0, 0.02)

    # Inject anomaly every ~200 ticks for demo
    if _state["tick"] % 200 == 150 and not _state["anomaly_injected"]:
        voltage = 112.5
        load_kw *= 1.35
        _state["anomaly_injected"] = True
    elif _state["tick"] % 200 > 155:
        _state["anomaly_injected"] = False

    ts = now.isoformat()
    return [
        {"timestamp": ts, "site_id": SITE_ID, "metric": "load_kw", "value": round(load_kw, 2), "unit": "kW"},
        {"timestamp": ts, "site_id": SITE_ID, "metric": "solar_kw", "value": round(solar_kw, 2), "unit": "kW"},
        {"timestamp": ts, "site_id": SITE_ID, "metric": "battery_soc", "value": round(_state["battery_soc"], 1), "unit": "%"},
        {"timestamp": ts, "site_id": SITE_ID, "metric": "battery_power_kw", "value": round(batt_power, 2), "unit": "kW"},
        {"timestamp": ts, "site_id": SITE_ID, "metric": "battery_temp_c", "value": round(_state["battery_temp_c"], 1), "unit": "C"},
        {"timestamp": ts, "site_id": SITE_ID, "metric": "grid_import_kw", "value": round(grid_import, 2), "unit": "kW"},
        {"timestamp": ts, "site_id": SITE_ID, "metric": "voltage_v", "value": round(voltage, 2), "unit": "V"},
        {"timestamp": ts, "site_id": SITE_ID, "metric": "frequency_hz", "value": round(frequency, 3), "unit": "Hz"},
        {"timestamp": ts, "site_id": SITE_ID, "metric": "carbon_intensity", "value": round(280 + hour * 8, 1), "unit": "gCO2/kWh"},
    ]


@app.get("/state")
async def get_state():
    return _state


@app.get("/health")
async def health():
    return {"status": "ok", "service": "grid-simulator"}
