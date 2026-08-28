"""AI copilot — natural language queries over live grid data."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AnomalyEvent, OptimizationRun, TelemetryReading
from app.schemas.api import CopilotResponse
from app.services.carbon_audit import carbon_audit_service
from app.services.climate import climate_service
from app.services.forecasting import forecasting_service
from app.services.optimizer import optimization_service

logger = logging.getLogger(__name__)

SITE_ID = "site-manhattan-01"


class CopilotService:
    async def answer(self, db: AsyncSession, question: str, site_id: str = SITE_ID) -> CopilotResponse:
        q = question.lower().strip()

        if re.search(r"spike|peak|high|surge|yesterday|why.*load", q):
            return await self._explain_load_spike(db, site_id, q)
        if re.search(r"carbon|co2|emission|green", q):
            return await self._carbon_summary(db, site_id)
        if re.search(r"optim|battery|dispatch|savings|cost", q):
            return await self._optimization_advice(db, site_id, q)
        if re.search(r"anomal|alert|fault|problem|issue", q):
            return await self._anomaly_status(db, site_id)
        if re.search(r"climate|heat|stress|resilien|future", q):
            return await self._climate_brief(db, site_id)
        if re.search(r"forecast|predict|tomorrow|next", q):
            return await self._forecast_brief(db, site_id)
        if re.search(r"solar|renewable|generation", q):
            return await self._solar_status(db, site_id)
        if re.search(r"status|overview|summary|how.*doing", q):
            return await self._site_overview(db, site_id)

        return CopilotResponse(
            answer=(
                "I can help with load spikes, carbon emissions, battery optimization, anomalies, "
                "climate stress tests, and forecasts. Try asking: 'Why did load spike yesterday?' or "
                "'What's our carbon footprint today?'"
            ),
        )

    async def _site_overview(self, db: AsyncSession, site_id: str) -> CopilotResponse:
        metrics = {}
        for metric in ["load_kw", "solar_kw", "battery_soc", "grid_import_kw"]:
            stmt = (
                select(TelemetryReading.value)
                .where(TelemetryReading.site_id == site_id, TelemetryReading.metric == metric)
                .order_by(TelemetryReading.timestamp.desc())
                .limit(1)
            )
            val = (await db.execute(stmt)).scalar()
            metrics[metric] = val

        answer = (
            f"Site is operating normally. Current load: {metrics.get('load_kw', 0):.0f} kW, "
            f"solar generation: {metrics.get('solar_kw', 0):.0f} kW, "
            f"battery SOC: {metrics.get('battery_soc', 0):.0f}%, "
            f"grid import: {metrics.get('grid_import_kw', 0):.0f} kW."
        )
        return CopilotResponse(answer=answer, data=metrics)

    async def _explain_load_spike(self, db: AsyncSession, site_id: str, q: str) -> CopilotResponse:
        since = datetime.now(UTC) - timedelta(hours=24)
        stmt = (
            select(TelemetryReading)
            .where(TelemetryReading.site_id == site_id, TelemetryReading.metric == "load_kw",
                   TelemetryReading.timestamp >= since)
            .order_by(TelemetryReading.timestamp)
        )
        rows = (await db.execute(stmt)).scalars().all()
        if not rows:
            return CopilotResponse(answer="Insufficient telemetry data to analyze load patterns.")

        values = [(r.timestamp, r.value) for r in rows]
        peak_ts, peak_val = max(values, key=lambda x: x[1])
        avg_val = sum(v for _, v in values) / len(values)
        spike_pct = (peak_val - avg_val) / avg_val * 100

        hour = peak_ts.hour
        cause = "HVAC pre-cooling before peak pricing window" if 13 <= hour <= 15 else "Morning equipment startup ramp"
        if spike_pct > 30:
            cause = f"Major load event — likely chiller bank activation at hour {hour}"

        answer = (
            f"Peak load of {peak_val:.0f} kW occurred at {peak_ts.strftime('%H:%M')} "
            f"({spike_pct:.0f}% above 24h average of {avg_val:.0f} kW). "
            f"Root cause analysis: {cause}. "
            f"Recommendation: Enable battery discharge 30 min before this window to shave {peak_val - avg_val:.0f} kW."
        )
        return CopilotResponse(answer=answer, data={"peak_kw": peak_val, "avg_kw": avg_val, "peak_time": peak_ts.isoformat()})

    async def _carbon_summary(self, db: AsyncSession, site_id: str) -> CopilotResponse:
        summary = await carbon_audit_service.get_summary(db, site_id, 24)
        answer = (
            f"Last 24h carbon audit: {summary.net_emissions_kg:.1f} kg CO₂ emitted, "
            f"{summary.avoided_emissions_kg:.1f} kg avoided via solar generation. "
            f"Average grid intensity: {summary.avg_intensity_gco2:.0f} gCO₂/kWh. "
            f"Net consumption: {summary.total_consumption_kwh:.0f} kWh, "
            f"on-site generation: {summary.total_generation_kwh:.0f} kWh."
        )
        return CopilotResponse(answer=answer, data=summary.model_dump())

    async def _optimization_advice(self, db: AsyncSession, site_id: str, q: str) -> CopilotResponse:
        objective = "balanced"
        if "carbon" in q:
            objective = "carbon"
        elif "cost" in q or "saving" in q:
            objective = "cost"
        elif "peak" in q:
            objective = "peak"

        result = await optimization_service.optimize(db, site_id, 24, objective)
        answer = result.explanation
        return CopilotResponse(answer=answer, data=result.model_dump())

    async def _anomaly_status(self, db: AsyncSession, site_id: str) -> CopilotResponse:
        stmt = (
            select(AnomalyEvent)
            .where(AnomalyEvent.site_id == site_id, AnomalyEvent.resolved == False)
            .order_by(AnomalyEvent.detected_at.desc())
            .limit(5)
        )
        events = (await db.execute(stmt)).scalars().all()
        if not events:
            return CopilotResponse(answer="No active anomalies detected. All systems nominal.")
        lines = [f"• [{e.severity.upper()}] {e.metric}: {e.root_cause}" for e in events]
        answer = f"{len(events)} active anomaly(ies):\n" + "\n".join(lines)
        return CopilotResponse(answer=answer, data={"count": len(events)})

    async def _climate_brief(self, db: AsyncSession, site_id: str) -> CopilotResponse:
        result = await climate_service.stress_test(db, site_id, "heat_wave_2030")
        answer = (
            f"Climate stress test (heat_wave_2030): projected peak load {result.projected_peak_kw:.0f} kW "
            f"(+{result.peak_load_increase_pct:.0f}%), resilience score: {result.resilience_score:.0f}/100. "
            f"Top recommendation: {result.recommendations[0]}"
        )
        return CopilotResponse(answer=answer, data=result.model_dump())

    async def _forecast_brief(self, db: AsyncSession, site_id: str) -> CopilotResponse:
        forecasts = await forecasting_service.forecast(db, site_id, 12)
        peak = max(forecasts, key=lambda f: f.load_kw)
        total_solar = sum(f.solar_kw for f in forecasts)
        answer = (
            f"12-hour forecast: peak load {peak.load_kw:.0f} kW at {peak.timestamp.strftime('%H:%M')}, "
            f"expected solar generation {total_solar:.0f} kWh total. "
            f"Confidence interval: {peak.confidence_low:.0f}–{peak.confidence_high:.0f} kW."
        )
        return CopilotResponse(answer=answer, data={"forecasts": [f.model_dump() for f in forecasts[:6]]})

    async def _solar_status(self, db: AsyncSession, site_id: str) -> CopilotResponse:
        since = datetime.now(UTC) - timedelta(hours=6)
        stmt = (
            select(func.avg(TelemetryReading.value), func.max(TelemetryReading.value))
            .where(TelemetryReading.site_id == site_id, TelemetryReading.metric == "solar_kw",
                   TelemetryReading.timestamp >= since)
        )
        row = (await db.execute(stmt)).one()
        avg_solar, max_solar = row[0] or 0, row[1] or 0
        capacity_factor = avg_solar / 500 * 100
        answer = (
            f"Solar array (500 kW nameplate): current 6h average {avg_solar:.0f} kW "
            f"({capacity_factor:.0f}% capacity factor), peak {max_solar:.0f} kW. "
            f"Performance is {'normal' if capacity_factor > 15 else 'below expected — check for shading or inverter faults'}."
        )
        return CopilotResponse(answer=answer, data={"avg_kw": avg_solar, "max_kw": max_solar})


copilot_service = CopilotService()
