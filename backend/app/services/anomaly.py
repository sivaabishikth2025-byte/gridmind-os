"""Multivariate anomaly detection with Isolation Forest and rule-based root cause analysis."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AnomalyEvent, TelemetryReading
from app.schemas.api import AnomalyOut

logger = logging.getLogger(__name__)

METRICS = ["load_kw", "solar_kw", "battery_soc", "grid_import_kw", "voltage_v", "frequency_hz"]
ROOT_CAUSE_RULES = {
    "load_kw": [
        (lambda a, e: a > e * 1.3, "Sudden load spike — possible equipment startup or HVAC surge"),
        (lambda a, e: a < e * 0.6, "Abnormal load drop — possible circuit trip or meter fault"),
    ],
    "voltage_v": [
        (lambda a, e: a < 115, "Voltage sag detected — check transformer T-12 and upstream breaker B-7"),
        (lambda a, e: a > 125, "Overvoltage condition — inverter regulation may be failing"),
    ],
    "frequency_hz": [
        (lambda a, e: abs(a - 60) > 0.15, "Frequency deviation — grid instability or islanding event"),
    ],
    "battery_soc": [
        (lambda a, e: a < 15, "Battery critically low — risk of backup power failure"),
        (lambda a, e: a > 98, "Battery overcharge condition — BMS calibration needed"),
    ],
    "solar_kw": [
        (lambda a, e: a < e * 0.3 and e > 50, "Solar underproduction — check inverter INV-3 or panel shading"),
    ],
}


class AnomalyService:
    async def detect(self, db: AsyncSession, site_id: str) -> list[AnomalyOut]:
        since = datetime.now(UTC) - timedelta(hours=48)
        anomalies_found: list[AnomalyOut] = []

        for metric in METRICS:
            stmt = (
                select(TelemetryReading)
                .where(
                    TelemetryReading.site_id == site_id,
                    TelemetryReading.metric == metric,
                    TelemetryReading.timestamp >= since,
                )
                .order_by(TelemetryReading.timestamp)
            )
            rows = (await db.execute(stmt)).scalars().all()
            if len(rows) < 20:
                continue

            values = np.array([r.value for r in rows]).reshape(-1, 1)
            rolling_mean = pd.Series(values.flatten()).rolling(12, min_periods=4).mean()
            expected = rolling_mean.iloc[-1]
            actual = values[-1, 0]

            clf = IsolationForest(contamination=0.05, random_state=42)
            clf.fit(values[:-1])
            score = clf.decision_function(values[-1:])[0]
            prediction = clf.predict(values[-1:])[0]

            if prediction == -1 or abs(actual - expected) > 2.5 * np.std(values):
                severity = "critical" if abs(actual - expected) > 3 * np.std(values) else "warning"
                root_cause = self._diagnose(metric, actual, float(expected))

                event = AnomalyEvent(
                    id=str(uuid.uuid4()),
                    site_id=site_id,
                    severity=severity,
                    metric=metric,
                    actual_value=round(float(actual), 3),
                    expected_value=round(float(expected), 3),
                    anomaly_score=round(float(-score), 4),
                    root_cause=root_cause,
                )
                db.add(event)
                anomalies_found.append(AnomalyOut(
                    id=event.id,
                    detected_at=datetime.now(UTC),
                    site_id=site_id,
                    severity=severity,
                    metric=metric,
                    actual_value=event.actual_value,
                    expected_value=event.expected_value,
                    anomaly_score=event.anomaly_score,
                    root_cause=root_cause,
                    resolved=False,
                ))

        await db.commit()
        return anomalies_found

    async def get_recent(self, db: AsyncSession, site_id: str, limit: int = 20) -> list[AnomalyOut]:
        stmt = (
            select(AnomalyEvent)
            .where(AnomalyEvent.site_id == site_id)
            .order_by(AnomalyEvent.detected_at.desc())
            .limit(limit)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return [
            AnomalyOut(
                id=r.id,
                detected_at=r.detected_at,
                site_id=r.site_id,
                severity=r.severity,
                metric=r.metric,
                actual_value=r.actual_value,
                expected_value=r.expected_value,
                anomaly_score=r.anomaly_score,
                root_cause=r.root_cause,
                resolved=r.resolved,
            )
            for r in rows
        ]

    def _diagnose(self, metric: str, actual: float, expected: float) -> str:
        rules = ROOT_CAUSE_RULES.get(metric, [])
        for check, message in rules:
            try:
                if check(actual, expected):
                    return message
            except Exception:
                continue
        deviation_pct = abs(actual - expected) / max(abs(expected), 1) * 100
        return f"{metric} deviated {deviation_pct:.1f}% from expected — investigate sensor {metric.upper()}-S01"


anomaly_service = AnomalyService()
