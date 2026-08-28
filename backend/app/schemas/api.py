from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TelemetryPoint(BaseModel):
    timestamp: datetime
    site_id: str
    metric: str
    value: float
    unit: str = "kW"
    source: str = "simulator"


class SiteOverview(BaseModel):
    site_id: str
    name: str
    load_kw: float
    solar_kw: float
    battery_soc: float
    battery_power_kw: float
    grid_import_kw: float
    carbon_intensity: float
    status: str


class ForecastPoint(BaseModel):
    timestamp: datetime
    load_kw: float
    solar_kw: float
    confidence_low: float
    confidence_high: float


class OptimizationScheduleItem(BaseModel):
    hour: int
    battery_power_kw: float
    load_shift_kw: float
    grid_import_kw: float
    cost_usd: float
    carbon_kg: float


class OptimizationResult(BaseModel):
    id: UUID | None = None
    site_id: str
    horizon_hours: int
    objective: str
    schedule: list[OptimizationScheduleItem]
    total_savings_usd: float
    peak_reduction_kw: float
    carbon_reduction_kg: float
    explanation: str


class AnomalyOut(BaseModel):
    id: UUID
    detected_at: datetime
    site_id: str
    severity: str
    metric: str
    actual_value: float
    expected_value: float
    anomaly_score: float
    root_cause: str | None
    resolved: bool


class CarbonSummary(BaseModel):
    period_hours: int
    total_consumption_kwh: float
    total_generation_kwh: float
    net_emissions_kg: float
    avoided_emissions_kg: float
    avg_intensity_gco2: float
    trend: list[dict[str, Any]]


class ClimateStressResult(BaseModel):
    scenario: str
    temperature_delta_c: float
    peak_load_increase_pct: float
    projected_peak_kw: float
    resilience_score: float
    recommendations: list[str]


class CopilotQuery(BaseModel):
    question: str


class CopilotResponse(BaseModel):
    answer: str
    data: dict[str, Any] = Field(default_factory=dict)


class WeatherData(BaseModel):
    temperature_c: float
    humidity_pct: float
    wind_speed_ms: float
    cloud_cover_pct: float
    solar_irradiance_wm2: float
    forecast_hours: list[dict[str, Any]] = Field(default_factory=list)
