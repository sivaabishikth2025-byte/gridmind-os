"""Multi-objective battery dispatch optimization using PuLP linear programming."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

import numpy as np
import pulp
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import OptimizationRun
from app.schemas.api import ForecastPoint, OptimizationResult, OptimizationScheduleItem
from app.services.external_data import carbon_service, pricing_service
from app.services.forecasting import forecasting_service

logger = logging.getLogger(__name__)

BATTERY_CAPACITY_KWH = 2000.0
BATTERY_MAX_POWER_KW = 500.0
BATTERY_MIN_SOC = 0.15
BATTERY_MAX_SOC = 0.95
BATTERY_EFFICIENCY = 0.92
INITIAL_SOC = 0.55


class OptimizationService:
    async def optimize(
        self,
        db: AsyncSession,
        site_id: str,
        horizon_hours: int = 24,
        objective: str = "balanced",
    ) -> OptimizationResult:
        forecasts = await forecasting_service.forecast(db, site_id, horizon_hours)
        prices = pricing_service.get_prices(horizon_hours)
        carbon = await carbon_service.get_hourly_forecast(horizon_hours)
        carbon_arr = np.array([c["carbon_intensity_gco2"] for c in carbon])

        load = np.array([f.load_kw for f in forecasts])
        solar = np.array([f.solar_kw for f in forecasts])
        net_load = load - solar

        # Weight objectives
        weights = {"cost": 0.5, "carbon": 0.3, "peak": 0.2}
        if objective == "cost":
            weights = {"cost": 0.8, "carbon": 0.1, "peak": 0.1}
        elif objective == "carbon":
            weights = {"cost": 0.2, "carbon": 0.7, "peak": 0.1}
        elif objective == "peak":
            weights = {"cost": 0.2, "carbon": 0.1, "peak": 0.7}

        T = horizon_hours
        prob = pulp.LpProblem("GridMind_Battery_Dispatch", pulp.LpMinimize)

        charge = [pulp.LpVariable(f"charge_{t}", 0, BATTERY_MAX_POWER_KW) for t in range(T)]
        discharge = [pulp.LpVariable(f"discharge_{t}", 0, BATTERY_MAX_POWER_KW) for t in range(T)]
        grid_import = [pulp.LpVariable(f"grid_{t}", 0) for t in range(T)]
        soc = [pulp.LpVariable(f"soc_{t}", BATTERY_MIN_SOC * BATTERY_CAPACITY_KWH,
                               BATTERY_MAX_SOC * BATTERY_CAPACITY_KWH) for t in range(T + 1)]

        prob += soc[0] == INITIAL_SOC * BATTERY_CAPACITY_KWH

        M = 10000.0
        for t in range(T):
            prob += grid_import[t] >= net_load[t] + charge[t] - discharge[t]
            prob += soc[t + 1] == soc[t] + charge[t] * BATTERY_EFFICIENCY - discharge[t] / BATTERY_EFFICIENCY

        # Objective: weighted cost + carbon + peak penalty
        cost_terms = []
        carbon_terms = []
        for t in range(T):
            normalized_carbon = carbon_arr[t] / 500.0
            cost_terms.append(grid_import[t] * prices[t] * weights["cost"])
            carbon_terms.append(grid_import[t] * normalized_carbon * weights["carbon"])

        peak_var = pulp.LpVariable("peak_demand", 0)
        for t in range(T):
            prob += grid_import[t] <= peak_var

        prob += (
            pulp.lpSum(cost_terms)
            + pulp.lpSum(carbon_terms)
            + peak_var * weights["peak"] * 0.01
        )

        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        schedule: list[OptimizationScheduleItem] = []
        baseline_cost = float(np.sum(np.maximum(net_load, 0) * prices))
        optimized_cost = 0.0
        baseline_peak = float(np.max(np.maximum(net_load, 0)))
        optimized_peak = 0.0
        baseline_carbon = float(np.sum(np.maximum(net_load, 0) * carbon_arr / 1000))
        optimized_carbon = 0.0

        for t in range(T):
            ch = pulp.value(charge[t]) or 0.0
            dis = pulp.value(discharge[t]) or 0.0
            batt_power = dis - ch
            gi = pulp.value(grid_import[t]) or 0.0
            hour_cost = gi * prices[t]
            hour_carbon = gi * carbon_arr[t] / 1000.0
            optimized_cost += hour_cost
            optimized_carbon += hour_carbon
            optimized_peak = max(optimized_peak, gi)

            schedule.append(OptimizationScheduleItem(
                hour=t,
                battery_power_kw=round(batt_power, 2),
                load_shift_kw=round(-batt_power, 2),
                grid_import_kw=round(gi, 2),
                cost_usd=round(hour_cost, 2),
                carbon_kg=round(hour_carbon, 3),
            ))

        savings = max(0, baseline_cost - optimized_cost)
        peak_reduction = max(0, baseline_peak - optimized_peak)
        carbon_reduction = max(0, baseline_carbon - optimized_carbon)

        explanation = self._build_explanation(
            objective, savings, peak_reduction, carbon_reduction, schedule, prices, carbon_arr
        )

        run_id = str(uuid.uuid4())
        run = OptimizationRun(
            id=run_id,
            site_id=site_id,
            horizon_hours=horizon_hours,
            objective=objective,
            status="completed",
            total_savings_usd=round(savings, 2),
            peak_reduction_kw=round(peak_reduction, 2),
            carbon_reduction_kg=round(carbon_reduction, 3),
            schedule={"items": [s.model_dump() for s in schedule]},
            explanation=explanation,
        )
        db.add(run)
        await db.commit()

        return OptimizationResult(
            id=run_id,
            site_id=site_id,
            horizon_hours=horizon_hours,
            objective=objective,
            schedule=schedule,
            total_savings_usd=round(savings, 2),
            peak_reduction_kw=round(peak_reduction, 2),
            carbon_reduction_kg=round(carbon_reduction, 3),
            explanation=explanation,
        )

    def _build_explanation(
        self, objective, savings, peak_reduction, carbon_reduction, schedule, prices, carbon_arr
    ) -> str:
        discharge_hours = [s.hour for s in schedule if s.battery_power_kw > 10]
        charge_hours = [s.hour for s in schedule if s.battery_power_kw < -10]
        low_carbon_hours = [i for i, c in enumerate(carbon_arr) if c < 350]

        parts = [
            f"Optimization completed with '{objective}' objective.",
            f"Projected savings: ${savings:.2f} over {len(schedule)} hours.",
            f"Peak demand reduction: {peak_reduction:.1f} kW.",
            f"Carbon reduction: {carbon_reduction:.2f} kg CO₂.",
        ]
        if charge_hours:
            parts.append(f"Charge battery during hours {charge_hours[:5]} (low price/carbon windows).")
        if discharge_hours:
            parts.append(f"Discharge during peak hours {discharge_hours[:5]} to shave demand.")
        if low_carbon_hours:
            parts.append(f"Low-carbon windows detected at hours {low_carbon_hours[:5]} — shifted load accordingly.")
        return " ".join(parts)


optimization_service = OptimizationService()
