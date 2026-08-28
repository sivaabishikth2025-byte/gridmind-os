"""
Real open-source live grid data — no API keys required.

Sources (easy to explain to judges):
  1. NYISO MIS Public Archive — official NY grid operator, real-time load & fuel mix
  2. Open-Meteo — NOAA/GFS weather driving solar forecasts
  3. EPA eGRID emission factors — applied to fuel mix for carbon intensity
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

NYISO_BASE = "http://mis.nyiso.com/public/csv"
ET = ZoneInfo("America/New_York")

# EPA eGRID 2022 approximate lb CO2/MWh by fuel type
EMISSION_FACTORS_LB_PER_MWH = {
    "Natural Gas": 850,
    "Dual Fuel": 900,
    "Nuclear": 0,
    "Hydro": 0,
    "Wind": 0,
    "Other Renewables": 50,
    "Other Fossil Fuels": 950,
    "Oil": 1100,
}

CAMPUS_SCALE = 0.00012  # ~850 kW campus vs ~7000 MW NYC zone


class LiveDataService:
    async def fetch_all(self) -> dict:
        """Fetch all live open data sources in parallel."""
        import asyncio
        load_task = self.fetch_nyiso_load()
        fuel_task = self.fetch_nyiso_fuel_mix()
        price_task = self.fetch_nyiso_prices()
        weather_task = self.fetch_weather()

        load, fuel, prices, weather = await asyncio.gather(
            load_task, fuel_task, price_task, weather_task,
            return_exceptions=True,
        )

        sources = []
        nyiso_load = load if isinstance(load, dict) else None
        fuel_mix = fuel if isinstance(fuel, dict) else None
        nyiso_prices = prices if isinstance(prices, dict) else None
        weather_data = weather if isinstance(weather, dict) else None

        if nyiso_load:
            sources.append({"name": "NYISO", "dataset": "Real-Time Actual Load (P-58B)", "status": "live", "url": nyiso_load.get("source_url")})
        if fuel_mix:
            sources.append({"name": "NYISO", "dataset": "Real-Time Fuel Mix", "status": "live", "url": fuel_mix.get("source_url")})
        if nyiso_prices:
            sources.append({"name": "NYISO", "dataset": "Real-Time Zonal LBMP (P-24A)", "status": "live", "url": nyiso_prices.get("source_url")})
        if weather_data:
            sources.append({"name": "Open-Meteo", "dataset": "NOAA/GFS Weather Forecast", "status": "live", "url": "https://open-meteo.com"})

        carbon = self._compute_carbon_from_fuel_mix(fuel_mix) if fuel_mix else None

        campus = self._derive_campus_metrics(nyiso_load, fuel_mix, weather_data, carbon, nyiso_prices)

        return {
            "fetched_at": datetime.now(UTC).isoformat(),
            "sources": sources,
            "nyiso": {
                "nyc_zone_load_mw": nyiso_load.get("nyc_load_mw") if nyiso_load else None,
                "total_ny_load_mw": nyiso_load.get("total_load_mw") if nyiso_load else None,
                "load_history": nyiso_load.get("history", []) if nyiso_load else [],
                "zone": "N.Y.C.",
            },
            "fuel_mix": fuel_mix.get("breakdown", []) if fuel_mix else [],
            "carbon": carbon,
            "prices": nyiso_prices,
            "weather": weather_data,
            "campus": campus,
            "judge_summary": self._judge_summary(nyiso_load, fuel_mix, carbon, weather_data),
        }

    async def fetch_nyiso_load(self) -> dict:
        today = datetime.now(ET).strftime("%Y%m%d")
        url = f"{NYISO_BASE}/pal/{today}pal.csv"
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            text = resp.text

        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        nyc_rows = [r for r in rows if r.get("Name", "").strip() == "N.Y.C."]
        if not nyc_rows:
            raise ValueError("No NYC zone data")

        latest = nyc_rows[-1]
        nyc_load = float(latest["Load"])

        # Build history for last 3 hours (36 x 5-min intervals)
        history = []
        for r in nyc_rows[-36:]:
            ts = r["Time Stamp"].strip()
            history.append({
                "timestamp": ts,
                "load_mw": round(float(r["Load"]), 1),
                "campus_kw": round(float(r["Load"]) * 1000 * CAMPUS_SCALE, 1),
            })

        # Total NY load from latest timestamp
        latest_ts = latest["Time Stamp"].strip()
        total = sum(float(r["Load"]) for r in rows if r.get("Time Stamp", "").strip() == latest_ts and r.get("Name") != "NYISO")

        return {
            "source_url": url,
            "nyc_load_mw": round(nyc_load, 1),
            "total_load_mw": round(total, 1),
            "timestamp": latest_ts,
            "history": history,
        }

    async def fetch_nyiso_fuel_mix(self) -> dict:
        today = datetime.now(ET).strftime("%Y%m%d")
        url = f"{NYISO_BASE}/rtfuelmix/{today}rtfuelmix.csv"
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            text = resp.text

        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        latest_ts = rows[-1]["Time Stamp"].strip()
        latest_rows = [r for r in rows if r.get("Time Stamp", "").strip() == latest_ts]

        breakdown = []
        total_gen = 0.0
        for r in latest_rows:
            fuel = r["Fuel Category"].strip()
            gen = float(r["Gen MW"])
            total_gen += gen
            breakdown.append({"fuel": fuel, "mw": round(gen, 1)})

        for b in breakdown:
            b["pct"] = round(b["mw"] / total_gen * 100, 1) if total_gen else 0

        breakdown.sort(key=lambda x: x["mw"], reverse=True)

        return {
            "source_url": url,
            "timestamp": latest_ts,
            "total_generation_mw": round(total_gen, 1),
            "breakdown": breakdown,
        }

    async def fetch_nyiso_prices(self) -> dict:
        today = datetime.now(ET).strftime("%Y%m%d")
        url = f"{NYISO_BASE}/realtime/{today}realtime_zone.csv"
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            text = resp.text

        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        nyc_rows = [r for r in rows if "N.Y.C" in r.get("Name", "") or "NYC" in r.get("Name", "")]
        if not nyc_rows:
            nyc_rows = [r for r in rows if r.get("Name", "").strip() in ("N.Y.C.", "NYC")]

        if not nyc_rows:
            # fallback: use any zone
            latest_ts = rows[-1]["Time Stamp"].strip()
            zone_rows = [r for r in rows if r.get("Time Stamp", "").strip() == latest_ts]
            if zone_rows:
                price = float(zone_rows[0].get("LBMP ($/MWHr)", zone_rows[0].get("LBMP", 50)))
            else:
                price = 45.0
        else:
            price = float(nyc_rows[-1].get("LBMP ($/MWHr)", nyc_rows[-1].get("LBMP", 50)))

        return {
            "source_url": url,
            "nyc_lbmp_mwh": round(price, 2),
            "nyc_lbmp_kwh": round(price / 1000, 4),
            "timestamp": nyc_rows[-1]["Time Stamp"] if nyc_rows else "",
        }

    async def fetch_weather(self) -> dict:
        params = {
            "latitude": settings.site_latitude,
            "longitude": settings.site_longitude,
            "current": "temperature_2m,cloud_cover,wind_speed_10m",
            "hourly": "temperature_2m,direct_normal_irradiance,cloud_cover",
            "forecast_days": 1,
            "timezone": "America/New_York",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(settings.open_meteo_url, params=params)
            resp.raise_for_status()
            data = resp.json()

        current = data.get("current", {})
        hourly = data.get("hourly", {})
        hour_idx = datetime.now(ET).hour
        irr = hourly.get("direct_normal_irradiance", [0])[hour_idx] or 0

        return {
            "temperature_c": current.get("temperature_2m", 22),
            "cloud_cover_pct": current.get("cloud_cover", 30),
            "wind_speed_ms": current.get("wind_speed_10m", 3),
            "solar_irradiance_wm2": irr,
            "source": "Open-Meteo (NOAA GFS model)",
        }

    def _compute_carbon_from_fuel_mix(self, fuel_mix: dict) -> dict:
        breakdown = fuel_mix.get("breakdown", [])
        total_gen = fuel_mix.get("total_generation_mw", 1)
        total_emissions = 0.0
        renewable_mw = 0.0
        for b in breakdown:
            factor = EMISSION_FACTORS_LB_PER_MWH.get(b["fuel"], 500)
            total_emissions += b["mw"] * factor
            if b["fuel"] in ("Nuclear", "Hydro", "Wind", "Other Renewables"):
                renewable_mw += b["mw"]

        # gCO2/kWh = (lb/MWh * 453.592 g/lb) / 1000 kWh/MWh
        intensity_g = (total_emissions / total_gen) * 453.592 / 1000 if total_gen else 400
        renewable_pct = renewable_mw / total_gen * 100 if total_gen else 0

        return {
            "intensity_gco2_kwh": round(intensity_g, 1),
            "renewable_pct": round(renewable_pct, 1),
            "method": "EPA eGRID factors × NYISO live fuel mix",
            "source": "NYISO Fuel Mix + EPA eGRID 2022",
        }

    def _derive_campus_metrics(self, load, fuel, weather, carbon, prices) -> dict:
        """Scale real NYISO NYC zone data to campus microgrid size."""
        nyc_mw = load.get("nyc_load_mw", 7000) if load else 7000
        campus_load_kw = round(nyc_mw * 1000 * CAMPUS_SCALE, 1)

        irr = weather.get("solar_irradiance_wm2", 0) if weather else 0
        cloud = weather.get("cloud_cover_pct", 30) if weather else 30
        solar_kw = round(max(0, irr / 1000 * 500 * (1 - cloud / 100 * 0.6) * 0.85), 1)

        price_kwh = prices.get("nyc_lbmp_kwh", 0.08) if prices else 0.08
        intensity = carbon.get("intensity_gco2_kwh", 350) if carbon else 350

        battery_soc = 65.0
        net = campus_load_kw - solar_kw
        battery_power = -80 if net > 700 else 120 if net < 400 else 0
        grid_import = max(0, net - battery_power)

        return {
            "load_kw": campus_load_kw,
            "solar_kw": solar_kw,
            "battery_soc": battery_soc,
            "battery_power_kw": battery_power,
            "grid_import_kw": round(grid_import, 1),
            "price_kwh": price_kwh,
            "carbon_intensity": intensity,
            "scale_note": f"Campus scaled from NYISO N.Y.C. zone ({nyc_mw:,.0f} MW × {CAMPUS_SCALE:.4%})",
        }

    def _judge_summary(self, load, fuel, carbon, weather) -> str:
        parts = []
        if load:
            parts.append(f"NYISO reports {load['nyc_load_mw']:,.0f} MW of real load in the NYC zone right now.")
        if fuel:
            top = fuel["breakdown"][0] if fuel.get("breakdown") else {}
            parts.append(f"The NY grid is {top.get('pct', 0)}% {top.get('fuel', 'unknown')} generation.")
        if carbon:
            parts.append(f"Carbon intensity is {carbon['intensity_gco2_kwh']} gCO₂/kWh ({carbon['renewable_pct']:.0f}% renewable).")
        if weather:
            parts.append(f"Weather: {weather['temperature_c']}°C, {weather['cloud_cover_pct']}% cloud cover.")
        return " ".join(parts)


live_data_service = LiveDataService()
