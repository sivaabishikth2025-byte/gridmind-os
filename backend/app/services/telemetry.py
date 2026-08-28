"""MQTT telemetry ingestion and real-time streaming."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from app.core.redis_client import get_redis
from app.core.database import AsyncSessionLocal
from app.models.entities import BatteryState, TelemetryReading
from app.services.carbon_audit import carbon_audit_service

logger = logging.getLogger(__name__)

SITE_ID = "site-manhattan-01"
REDIS_CHANNEL = "gridmind:telemetry"
REDIS_STATE_KEY = "gridmind:live_state"


class TelemetryIngestor:
    def __init__(self) -> None:
        self._redis = None
        self._running = False
        self._latest_state: dict = {}

    async def start(self) -> None:
        self._redis = await get_redis()
        self._running = True
        logger.info("Telemetry ingestor started")

    async def stop(self) -> None:
        self._running = False
        if self._redis:
            try:
                await self._redis.aclose()
            except Exception:
                pass

    async def ingest_batch(self, readings: list[dict]) -> None:
        async with AsyncSessionLocal() as db:
            for r in readings:
                ts = datetime.fromisoformat(r["timestamp"]) if isinstance(r["timestamp"], str) else r["timestamp"]
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)

                reading = TelemetryReading(
                    timestamp=ts,
                    site_id=r.get("site_id", SITE_ID),
                    metric=r["metric"],
                    value=float(r["value"]),
                    unit=r.get("unit", "kW"),
                    source=r.get("source", "simulator"),
                )
                db.add(reading)
                self._latest_state[r["metric"]] = float(r["value"])

            if "battery_soc" in self._latest_state:
                batt = BatteryState(
                    timestamp=datetime.now(UTC),
                    site_id=SITE_ID,
                    soc_percent=self._latest_state.get("battery_soc", 55),
                    power_kw=self._latest_state.get("battery_power_kw", 0),
                    capacity_kwh=2000,
                    temperature_c=self._latest_state.get("battery_temp_c", 28),
                    mode=self._latest_state.get("battery_mode", "auto"),
                )
                db.add(batt)

            await db.commit()

            load = self._latest_state.get("load_kw", 0)
            solar = self._latest_state.get("solar_kw", 0)
            interval_kwh = load / 4
            gen_kwh = solar / 4
            await carbon_audit_service.record_interval(db, SITE_ID, interval_kwh, gen_kwh)

        if self._redis:
            payload = json.dumps({
                "timestamp": datetime.now(UTC).isoformat(),
                "site_id": SITE_ID,
                "metrics": self._latest_state,
            })
            await self._redis.publish(REDIS_CHANNEL, payload)
            await self._redis.set(REDIS_STATE_KEY, payload)

    def get_live_state(self) -> dict:
        return dict(self._latest_state)


telemetry_ingestor = TelemetryIngestor()
