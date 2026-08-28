import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.database import Base


class TelemetryReading(Base):
    __tablename__ = "telemetry_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    site_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False, default="kW")
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="simulator")

    __table_args__ = (
        Index("ix_telemetry_site_metric_ts", "site_id", "metric", "timestamp"),
    )


class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    site_id: Mapped[str] = mapped_column(String(64), nullable=False)
    horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    objective: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    total_savings_usd: Mapped[float] = mapped_column(Float, nullable=True)
    peak_reduction_kw: Mapped[float] = mapped_column(Float, nullable=True)
    carbon_reduction_kg: Mapped[float] = mapped_column(Float, nullable=True)
    schedule: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)


class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    site_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)


class CarbonLedgerEntry(Base):
    __tablename__ = "carbon_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    site_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    consumption_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    generation_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    carbon_intensity_gco2: Mapped[float] = mapped_column(Float, nullable=False)
    emissions_kg: Mapped[float] = mapped_column(Float, nullable=False)
    avoided_emissions_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source: Mapped[str] = mapped_column(String(64), nullable=False)


class BatteryState(Base):
    __tablename__ = "battery_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    site_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    soc_percent: Mapped[float] = mapped_column(Float, nullable=False)
    power_kw: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
