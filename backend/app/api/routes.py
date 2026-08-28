from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis_client import get_redis
from app.core.database import get_db
from app.schemas.api import (
    AnomalyOut,
    CarbonSummary,
    ClimateStressResult,
    CopilotQuery,
    CopilotResponse,
    ForecastPoint,
    OptimizationResult,
    SiteOverview,
    WeatherData,
)
from app.services.anomaly import anomaly_service
from app.services.carbon_audit import carbon_audit_service
from app.services.climate import climate_service
from app.services.copilot import copilot_service
from app.services.external_data import carbon_service, pricing_service, weather_service
from app.services.forecasting import forecasting_service
from app.services.optimizer import optimization_service
from app.services.telemetry import SITE_ID, telemetry_ingestor
from app.services.live_data import live_data_service
from app.models.entities import TelemetryReading
from app.services.demo import (
    get_activity_feed,
    get_digital_twin,
    get_esg_report,
    get_executive_summary,
    get_notifications,
    get_portfolio,
    get_vpp_status,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "gridmind-os", "timestamp": datetime.now(UTC).isoformat()}


@router.get("/site/overview", response_model=SiteOverview)
async def site_overview(db: AsyncSession = Depends(get_db)):
    # Prefer real NYISO + weather data
    try:
        live = await live_data_service.fetch_all()
        campus = live["campus"]
        return SiteOverview(
            site_id=SITE_ID,
            name=settings.site_name,
            load_kw=campus["load_kw"],
            solar_kw=campus["solar_kw"],
            battery_soc=campus["battery_soc"],
            battery_power_kw=campus["battery_power_kw"],
            grid_import_kw=campus["grid_import_kw"],
            carbon_intensity=campus["carbon_intensity"],
            status="optimal" if campus["load_kw"] < 1000 else "elevated",
        )
    except Exception as e:
        logger.warning("Live data unavailable, using telemetry: %s", e)

    state = telemetry_ingestor.get_live_state()
    if not state:
        for metric in ["load_kw", "solar_kw", "battery_soc", "grid_import_kw"]:
            stmt = (
                select(TelemetryReading.value)
                .where(TelemetryReading.site_id == SITE_ID, TelemetryReading.metric == metric)
                .order_by(TelemetryReading.timestamp.desc())
                .limit(1)
            )
            val = (await db.execute(stmt)).scalar()
            if val is not None:
                state[metric] = val

    intensity = await carbon_service.get_current_intensity()
    load = state.get("load_kw", 0)
    status = "optimal" if load < 1000 else "elevated" if load < 1300 else "critical"

    return SiteOverview(
        site_id=SITE_ID,
        name=settings.site_name,
        load_kw=state.get("load_kw", 0),
        solar_kw=state.get("solar_kw", 0),
        battery_soc=state.get("battery_soc", 55),
        battery_power_kw=state.get("battery_power_kw", 0),
        grid_import_kw=state.get("grid_import_kw", 0),
        carbon_intensity=intensity,
        status=status,
    )


@router.get("/telemetry/history")
async def telemetry_history(
    metric: str = "load_kw",
    hours: int = Query(6, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(UTC) - timedelta(hours=hours)
    stmt = (
        select(TelemetryReading)
        .where(TelemetryReading.site_id == SITE_ID, TelemetryReading.metric == metric,
               TelemetryReading.timestamp >= since)
        .order_by(TelemetryReading.timestamp)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {"timestamp": r.timestamp.isoformat(), "value": r.value, "metric": r.metric, "unit": r.unit}
        for r in rows
    ]


@router.get("/telemetry/multi")
async def telemetry_multi(hours: int = Query(2, ge=1, le=24), db: AsyncSession = Depends(get_db)):
    since = datetime.now(UTC) - timedelta(hours=hours)
    metrics = ["load_kw", "solar_kw", "battery_soc", "grid_import_kw", "voltage_v", "frequency_hz"]
    result = {}
    for metric in metrics:
        stmt = (
            select(TelemetryReading)
            .where(TelemetryReading.site_id == SITE_ID, TelemetryReading.metric == metric,
                   TelemetryReading.timestamp >= since)
            .order_by(TelemetryReading.timestamp)
        )
        rows = (await db.execute(stmt)).scalars().all()
        result[metric] = [{"t": r.timestamp.isoformat(), "v": r.value} for r in rows]
    return result


@router.get("/forecast", response_model=list[ForecastPoint])
async def get_forecast(hours: int = Query(24, ge=1, le=48), db: AsyncSession = Depends(get_db)):
    return await forecasting_service.forecast(db, SITE_ID, hours)


@router.post("/optimize", response_model=OptimizationResult)
async def run_optimization(
    objective: str = Query("balanced", pattern="^(balanced|cost|carbon|peak)$"),
    hours: int = Query(24, ge=6, le=48),
    db: AsyncSession = Depends(get_db),
):
    return await optimization_service.optimize(db, SITE_ID, hours, objective)


@router.get("/anomalies", response_model=list[AnomalyOut])
async def get_anomalies(db: AsyncSession = Depends(get_db)):
    return await anomaly_service.get_recent(db, SITE_ID)


@router.post("/anomalies/detect", response_model=list[AnomalyOut])
async def detect_anomalies(db: AsyncSession = Depends(get_db)):
    return await anomaly_service.detect(db, SITE_ID)


@router.get("/carbon/summary", response_model=CarbonSummary)
async def carbon_summary(hours: int = Query(24, ge=1, le=168), db: AsyncSession = Depends(get_db)):
    return await carbon_audit_service.get_summary(db, SITE_ID, hours)


@router.get("/carbon/intensity")
async def carbon_intensity_forecast(hours: int = Query(24, ge=1, le=48)):
    return await carbon_service.get_hourly_forecast(hours)


@router.get("/climate/stress-test", response_model=ClimateStressResult)
async def stress_test(
    scenario: str = Query("heat_wave_2030"),
    db: AsyncSession = Depends(get_db),
):
    return await climate_service.stress_test(db, SITE_ID, scenario)


@router.get("/climate/scenarios")
async def list_scenarios():
    return climate_service.list_scenarios()


@router.get("/weather", response_model=WeatherData)
async def get_weather():
    return await weather_service.fetch()


@router.get("/pricing")
async def get_pricing():
    prices = pricing_service.get_prices(24)
    return {
        "current_price_kwh": pricing_service.get_current_price(),
        "hourly": [{"hour": i, "price_usd": round(float(p), 4)} for i, p in enumerate(prices)],
        "demand_charge_kw": pricing_service.DEMAND_CHARGE_KW,
    }


@router.post("/copilot", response_model=CopilotResponse)
async def copilot_query(body: CopilotQuery, db: AsyncSession = Depends(get_db)):
    return await copilot_service.answer(db, body.question)


@router.get("/stats")
async def platform_stats(db: AsyncSession = Depends(get_db)):
    since = datetime.now(UTC) - timedelta(hours=24)
    count_stmt = select(func.count()).select_from(TelemetryReading).where(
        TelemetryReading.timestamp >= since
    )
    total_readings = (await db.execute(count_stmt)).scalar() or 0

    peak_stmt = (
        select(func.max(TelemetryReading.value))
        .where(TelemetryReading.site_id == SITE_ID, TelemetryReading.metric == "load_kw",
               TelemetryReading.timestamp >= since)
    )
    peak_load = (await db.execute(peak_stmt)).scalar() or 0

    return {
        "readings_24h": total_readings,
        "peak_load_24h_kw": round(peak_load, 1),
        "site_id": SITE_ID,
        "uptime": "99.97%",
        "active_assets": 12,
    }


@router.get("/live/grid")
async def live_grid_data():
    """Real open-source data: NYISO load/fuel mix/prices + Open-Meteo weather."""
    return await live_data_service.fetch_all()


@router.get("/demo/portfolio")
async def demo_portfolio():
    return get_portfolio()


@router.get("/demo/vpp")
async def demo_vpp():
    return get_vpp_status()


@router.get("/demo/activity")
async def demo_activity(limit: int = Query(15, ge=1, le=50)):
    return get_activity_feed(limit)


@router.get("/demo/esg")
async def demo_esg():
    return get_esg_report()


@router.get("/demo/digital-twin")
async def demo_digital_twin(site_id: str = Query("site-manhattan-01")):
    return get_digital_twin(site_id)


@router.get("/demo/notifications")
async def demo_notifications():
    return get_notifications()


@router.get("/demo/executive-summary")
async def demo_executive_summary():
    return get_executive_summary()


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await websocket.accept()
    redis_client = await get_redis()
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("gridmind:telemetry")

    try:
        cached = await redis_client.get("gridmind:live_state")
        if cached:
            await websocket.send_text(cached)

        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                data = message["data"]
                if isinstance(data, str):
                    await websocket.send_text(data)
                else:
                    await websocket.send_text(json.dumps(data))
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                if data == "ping":
                    await websocket.send_text('{"type":"pong"}')
            except TimeoutError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe("gridmind:telemetry")
        try:
            await redis_client.aclose()
        except Exception:
            pass
