"""Load and solar forecasting using sklearn GradientBoosting on engineered features."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import TelemetryReading
from app.schemas.api import ForecastPoint
from app.services.external_data import NYISO_HOURLY_SHAPE, weather_service

logger = logging.getLogger(__name__)

BASE_LOAD_KW = 850.0
SOLAR_CAPACITY_KW = 500.0


def _solar_clear_sky(irradiance_wm2: float, capacity_kw: float = SOLAR_CAPACITY_KW) -> float:
    return max(0.0, min(capacity_kw, irradiance_wm2 / 1000.0 * capacity_kw * 0.85))


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["load_lag1"] = df["load_kw"].shift(1)
    df["load_lag4"] = df["load_kw"].shift(4)
    df["load_roll_mean"] = df["load_kw"].rolling(4, min_periods=1).mean()
    return df.dropna()


class ForecastingService:
    async def get_historical(
        self, db: AsyncSession, site_id: str, metric: str, hours: int = 72
    ) -> pd.DataFrame:
        since = datetime.now(UTC) - timedelta(hours=hours)
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
        if not rows:
            return pd.DataFrame(columns=["timestamp", "value"])
        return pd.DataFrame([{"timestamp": r.timestamp, "value": r.value} for r in rows])

    async def forecast(
        self, db: AsyncSession, site_id: str, horizon_hours: int = 24
    ) -> list[ForecastPoint]:
        load_df = await self.get_historical(db, site_id, "load_kw", hours=168)
        solar_df = await self.get_historical(db, site_id, "solar_kw", hours=168)
        weather = await weather_service.fetch()

        if len(load_df) < 12:
            return self._fallback_forecast(horizon_hours, weather)

        load_df.columns = ["timestamp", "load_kw"]
        solar_df.columns = ["timestamp", "solar_kw"] if len(solar_df) else ["timestamp", "load_kw"]
        if len(solar_df) < 12:
            solar_df = pd.DataFrame({"timestamp": load_df["timestamp"], "solar_kw": 0.0})

        merged = load_df.merge(solar_df, on="timestamp", how="left").fillna(0)
        features = _build_features(merged)
        feature_cols = ["hour_sin", "hour_cos", "dow_sin", "dow_cos", "is_weekend",
                        "load_lag1", "load_lag4", "load_roll_mean"]

        X = features[feature_cols].values
        y = features["load_kw"].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
        model.fit(X_scaled, y)

        residuals = y - model.predict(X_scaled)
        std_err = float(np.std(residuals)) if len(residuals) > 1 else 50.0

        last_row = features.iloc[-1]
        last_load = float(last_row["load_kw"])
        now = datetime.now(UTC)
        forecasts: list[ForecastPoint] = []

        for h in range(1, horizon_hours + 1):
            ts = now + timedelta(hours=h)
            hour = ts.hour
            dow = ts.weekday()
            wf_idx = min(h - 1, len(weather.forecast_hours) - 1)
            irr = weather.forecast_hours[wf_idx]["irradiance_wm2"] if weather.forecast_hours else 0
            solar_pred = _solar_clear_sky(irr)

            feat = np.array([[
                np.sin(2 * np.pi * hour / 24),
                np.cos(2 * np.pi * hour / 24),
                np.sin(2 * np.pi * dow / 7),
                np.cos(2 * np.pi * dow / 7),
                1 if dow >= 5 else 0,
                last_load,
                last_load * 0.98,
                last_load,
            ]])
            load_pred = float(model.predict(scaler.transform(feat))[0])
            load_pred = max(200.0, load_pred)

            forecasts.append(ForecastPoint(
                timestamp=ts,
                load_kw=round(load_pred, 2),
                solar_kw=round(solar_pred, 2),
                confidence_low=round(load_pred - 1.96 * std_err, 2),
                confidence_high=round(load_pred + 1.96 * std_err, 2),
            ))
            last_load = load_pred

        return forecasts

    def _fallback_forecast(self, horizon_hours: int, weather) -> list[ForecastPoint]:
        now = datetime.now(UTC)
        forecasts = []
        for h in range(1, horizon_hours + 1):
            ts = now + timedelta(hours=h)
            hour = ts.hour
            shape = float(NYISO_HOURLY_SHAPE[hour])
            is_weekend = ts.weekday() >= 5
            load = BASE_LOAD_KW * shape * (0.85 if is_weekend else 1.0)
            wf_idx = min(h - 1, len(weather.forecast_hours) - 1)
            irr = weather.forecast_hours[wf_idx]["irradiance_wm2"] if weather.forecast_hours else 0
            solar = _solar_clear_sky(irr)
            forecasts.append(ForecastPoint(
                timestamp=ts,
                load_kw=round(load, 2),
                solar_kw=round(solar, 2),
                confidence_low=round(load * 0.9, 2),
                confidence_high=round(load * 1.1, 2),
            ))
        return forecasts


forecasting_service = ForecastingService()
