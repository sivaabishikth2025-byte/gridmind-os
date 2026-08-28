const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "";

export { API_BASE, WS_BASE };

export async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const base = API_BASE.startsWith("http") ? API_BASE : (typeof window !== "undefined" ? window.location.origin + API_BASE : API_BASE);
  const url = path.startsWith("http") ? path : `${base}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchAPIWithFallback<T>(path: string, fallback: T): Promise<T> {
  try {
    return await fetchAPI<T>(path);
  } catch {
    return fallback;
  }
}

export interface SiteOverview {
  site_id: string;
  name: string;
  load_kw: number;
  solar_kw: number;
  battery_soc: number;
  battery_power_kw: number;
  grid_import_kw: number;
  carbon_intensity: number;
  status: string;
}

export interface ForecastPoint {
  timestamp: string;
  load_kw: number;
  solar_kw: number;
  confidence_low: number;
  confidence_high: number;
}

export interface Anomaly {
  id: string;
  detected_at: string;
  severity: string;
  metric: string;
  actual_value: number;
  expected_value: number;
  anomaly_score: number;
  root_cause: string | null;
  resolved: boolean;
}

export interface CarbonSummary {
  period_hours: number;
  total_consumption_kwh: number;
  total_generation_kwh: number;
  net_emissions_kg: number;
  avoided_emissions_kg: number;
  avg_intensity_gco2: number;
  trend: { timestamp: string; emissions_kg: number; intensity: number }[];
}

export interface OptimizationResult {
  id: string;
  site_id: string;
  horizon_hours: number;
  objective: string;
  schedule: {
    hour: number;
    battery_power_kw: number;
    grid_import_kw: number;
    cost_usd: number;
    carbon_kg: number;
  }[];
  total_savings_usd: number;
  peak_reduction_kw: number;
  carbon_reduction_kg: number;
  explanation: string;
}

export interface ClimateStress {
  scenario: string;
  temperature_delta_c: number;
  peak_load_increase_pct: number;
  projected_peak_kw: number;
  resilience_score: number;
  recommendations: string[];
}

export interface PortfolioSite {
  id: string;
  name: string;
  city: string;
  type: string;
  capacity_mw: number;
  assets: number;
  status: string;
  load_kw: number;
  solar_kw: number;
  battery_soc: number;
  grid_import_kw: number;
  savings_mtd_usd: number;
  carbon_intensity: number;
  renewable_pct: number;
  uptime_pct: number;
}

export interface Portfolio {
  total_sites: number;
  total_load_kw: number;
  total_solar_kw: number;
  total_savings_mtd_usd: number;
  avg_renewable_pct: number;
  portfolio_carbon_kg_24h: number;
  active_alerts: number;
  sites: PortfolioSite[];
}

export interface ActivityItem {
  id: string;
  type: string;
  message: string;
  site: string;
  level: string;
  timestamp: string;
  automated: boolean;
}

export interface ESGReport {
  reporting_period: string;
  overall_score: number;
  scores: Record<string, { score: number; target: number; unit: string; value: number }>;
  certifications: string[];
  emissions: { scope1_kg: number; scope2_kg: number; scope3_kg: number; total_kg: number; yoy_change_pct: number };
  renewable_mwh: number;
  carbon_offset_mwh: number;
}

export interface ExecutiveSummary {
  period: string;
  total_energy_kwh: number;
  total_cost_usd: number;
  cost_savings_usd: number;
  savings_pct: number;
  peak_reduction_kw: number;
  carbon_avoided_tons: number;
  renewable_pct: number;
  uptime_pct: number;
  automation_rate_pct: number;
  roi_annual_pct: number;
}
