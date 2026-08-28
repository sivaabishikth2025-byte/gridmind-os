"""Carbon ledger aggregation and auditing."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import CarbonLedgerEntry, TelemetryReading
from app.schemas.api import CarbonSummary
from app.services.external_data import carbon_service

logger = logging.getLogger(__name__)


class CarbonAuditService:
    async def record_interval(
        self, db: AsyncSession, site_id: str,
        consumption_kwh: float, generation_kwh: float,
    ) -> CarbonLedgerEntry:
        intensity = await carbon_service.get_current_intensity()
        result = carbon_service.compute_emissions(consumption_kwh, generation_kwh, intensity)
        entry = CarbonLedgerEntry(
            timestamp=datetime.now(UTC),
            site_id=site_id,
            consumption_kwh=consumption_kwh,
            generation_kwh=generation_kwh,
            carbon_intensity_gco2=intensity,
            emissions_kg=result["emissions_kg"],
            avoided_emissions_kg=result["avoided_emissions_kg"],
            source="realtime_audit",
        )
        db.add(entry)
        await db.commit()
        return entry

    async def get_summary(self, db: AsyncSession, site_id: str, period_hours: int = 24) -> CarbonSummary:
        since = datetime.now(UTC) - timedelta(hours=period_hours)

        ledger_stmt = (
            select(CarbonLedgerEntry)
            .where(CarbonLedgerEntry.site_id == site_id, CarbonLedgerEntry.timestamp >= since)
            .order_by(CarbonLedgerEntry.timestamp)
        )
        entries = (await db.execute(ledger_stmt)).scalars().all()

        if entries:
            total_consumption = sum(e.consumption_kwh for e in entries)
            total_generation = sum(e.generation_kwh for e in entries)
            net_emissions = sum(e.emissions_kg for e in entries)
            avoided = sum(e.avoided_emissions_kg for e in entries)
            avg_intensity = sum(e.carbon_intensity_gco2 for e in entries) / len(entries)
            trend = [
                {"timestamp": e.timestamp.isoformat(), "emissions_kg": round(e.emissions_kg, 3),
                 "intensity": e.carbon_intensity_gco2}
                for e in entries[-48:]
            ]
        else:
            # Compute from telemetry if no ledger entries yet
            load_stmt = (
                select(func.avg(TelemetryReading.value))
                .where(TelemetryReading.site_id == site_id, TelemetryReading.metric == "load_kw",
                       TelemetryReading.timestamp >= since)
            )
            solar_stmt = (
                select(func.avg(TelemetryReading.value))
                .where(TelemetryReading.site_id == site_id, TelemetryReading.metric == "solar_kw",
                       TelemetryReading.timestamp >= since)
            )
            avg_load = (await db.execute(load_stmt)).scalar() or 850.0
            avg_solar = (await db.execute(solar_stmt)).scalar() or 200.0
            interval_kwh = avg_load / 4  # 15-min intervals
            gen_kwh = avg_solar / 4
            intensity = await carbon_service.get_current_intensity()
            result = carbon_service.compute_emissions(interval_kwh * period_hours * 4, gen_kwh * period_hours * 4, intensity)
            total_consumption = interval_kwh * period_hours * 4
            total_generation = gen_kwh * period_hours * 4
            net_emissions = result["emissions_kg"] * period_hours
            avoided = result["avoided_emissions_kg"] * period_hours
            avg_intensity = intensity
            trend = []

        return CarbonSummary(
            period_hours=period_hours,
            total_consumption_kwh=round(total_consumption, 2),
            total_generation_kwh=round(total_generation, 2),
            net_emissions_kg=round(net_emissions, 3),
            avoided_emissions_kg=round(avoided, 3),
            avg_intensity_gco2=round(avg_intensity, 1),
            trend=trend,
        )


carbon_audit_service = CarbonAuditService()
