"""Climate stress testing with physics-based load sensitivity models."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import TelemetryReading
from app.schemas.api import ClimateStressResult
from app.services.external_data import weather_service

logger = logging.getLogger(__name__)

SCENARIOS = {
    "baseline": {"temp_delta": 0, "description": "Current conditions"},
    "heat_wave_2030": {"temp_delta": 4.5, "description": "IPCC SSP2-4.5 mid-century heat wave"},
    "extreme_heat_2050": {"temp_delta": 7.0, "description": "IPCC SSP5-8.5 extreme heat event"},
    "polar_vortex": {"temp_delta": -15.0, "description": "Winter storm heating surge"},
    "hurricane_resilience": {"temp_delta": 2.0, "description": "Post-hurricane grid degradation"},
}


class ClimateService:
    async def stress_test(
        self, db: AsyncSession, site_id: str, scenario: str = "heat_wave_2030"
    ) -> ClimateStressResult:
        config = SCENARIOS.get(scenario, SCENARIOS["heat_wave_2030"])
        temp_delta = config["temp_delta"]

        since = datetime.now(UTC) - timedelta(hours=24)
        stmt = (
            select(TelemetryReading)
            .where(
                TelemetryReading.site_id == site_id,
                TelemetryReading.metric == "load_kw",
                TelemetryReading.timestamp >= since,
            )
            .order_by(TelemetryReading.timestamp.desc())
            .limit(96)
        )
        rows = (await db.execute(stmt)).scalars().all()
        current_peak = max((r.value for r in rows), default=1200.0)
        avg_load = np.mean([r.value for r in rows]) if rows else 850.0

        weather = await weather_service.fetch()
        base_temp = weather.temperature_c

        # Cooling/heating degree-day sensitivity (ASHRAE-based approximation)
        if temp_delta > 0:
            # Each °C above 24°C adds ~3.5% cooling load
            load_increase_pct = max(0, (base_temp + temp_delta - 24) * 3.5)
            if base_temp < 24:
                load_increase_pct = temp_delta * 2.5
        else:
            # Heating: each °C below 18°C adds ~4% heating load
            load_increase_pct = abs(temp_delta) * 4.0

        projected_peak = current_peak * (1 + load_increase_pct / 100)
        headroom_kw = 1500 - projected_peak
        resilience_score = max(0, min(100, (headroom_kw / 1500) * 100))

        recommendations = []
        if projected_peak > 1400:
            recommendations.append("Install additional 500 kWh battery storage to cover peak shaving gap")
        if temp_delta > 5:
            recommendations.append("Upgrade HVAC chillers to high-efficiency models — estimated 18% cooling reduction")
        if resilience_score < 50:
            recommendations.append("Deploy microgrid islanding capability for grid outage resilience")
        if scenario == "hurricane_resilience":
            recommendations.append("Pre-position diesel backup at 80% fuel, test black-start sequence monthly")
        if not recommendations:
            recommendations.append("Current infrastructure adequate — maintain preventive maintenance schedule")

        return ClimateStressResult(
            scenario=scenario,
            temperature_delta_c=temp_delta,
            peak_load_increase_pct=round(load_increase_pct, 1),
            projected_peak_kw=round(projected_peak, 1),
            resilience_score=round(resilience_score, 1),
            recommendations=recommendations,
        )

    def list_scenarios(self) -> list[dict]:
        return [{"id": k, **v} for k, v in SCENARIOS.items()]


climate_service = ClimateService()
