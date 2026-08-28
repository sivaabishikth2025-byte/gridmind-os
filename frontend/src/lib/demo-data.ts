import type { Portfolio, ActivityItem, ESGReport, ExecutiveSummary } from "./api";

export const DEMO_PORTFOLIO: Portfolio = {
  total_sites: 6,
  total_load_kw: 6840,
  total_solar_kw: 1420,
  total_savings_mtd_usd: 18420,
  avg_renewable_pct: 20.8,
  portfolio_carbon_kg_24h: 2394,
  active_alerts: 1,
  sites: [
    { id: "site-manhattan-01", name: "Manhattan Campus", city: "New York, NY", type: "Campus", capacity_mw: 2.5, assets: 12, status: "optimal", load_kw: 892, solar_kw: 340, battery_soc: 72, grid_import_kw: 512, savings_mtd_usd: 3240, carbon_intensity: 310, renewable_pct: 38.1, uptime_pct: 99.97 },
    { id: "site-brooklyn-02", name: "Brooklyn Data Center", city: "Brooklyn, NY", type: "Data Center", capacity_mw: 8.0, assets: 34, status: "optimal", load_kw: 1640, solar_kw: 180, battery_soc: 58, grid_import_kw: 1420, savings_mtd_usd: 4820, carbon_intensity: 420, renewable_pct: 11.0, uptime_pct: 99.99 },
    { id: "site-jersey-03", name: "Newark Industrial Park", city: "Newark, NJ", type: "Industrial", capacity_mw: 5.2, assets: 22, status: "elevated", load_kw: 1280, solar_kw: 420, battery_soc: 45, grid_import_kw: 820, savings_mtd_usd: 2890, carbon_intensity: 380, renewable_pct: 32.8, uptime_pct: 99.92 },
    { id: "site-stamford-04", name: "Stamford Hospital", city: "Stamford, CT", type: "Healthcare", capacity_mw: 3.1, assets: 18, status: "optimal", load_kw: 980, solar_kw: 280, battery_soc: 81, grid_import_kw: 680, savings_mtd_usd: 2100, carbon_intensity: 290, renewable_pct: 28.6, uptime_pct: 99.98 },
    { id: "site-philly-05", name: "Philadelphia Microgrid", city: "Philadelphia, PA", type: "Microgrid", capacity_mw: 4.0, assets: 28, status: "warning", load_kw: 1420, solar_kw: 120, battery_soc: 34, grid_import_kw: 1280, savings_mtd_usd: 1840, carbon_intensity: 450, renewable_pct: 8.5, uptime_pct: 99.85 },
    { id: "site-boston-06", name: "Cambridge Research Lab", city: "Cambridge, MA", type: "R&D", capacity_mw: 1.8, assets: 9, status: "optimal", load_kw: 628, solar_kw: 80, battery_soc: 67, grid_import_kw: 520, savings_mtd_usd: 3530, carbon_intensity: 260, renewable_pct: 12.7, uptime_pct: 99.96 },
  ],
};

export const DEMO_EXECUTIVE: ExecutiveSummary = {
  period: "Last 30 Days",
  total_energy_kwh: 4_820_000,
  total_cost_usd: 412_800,
  cost_savings_usd: 67_400,
  savings_pct: 14.0,
  peak_reduction_kw: 2340,
  carbon_avoided_tons: 184,
  renewable_pct: 38.2,
  uptime_pct: 99.97,
  automation_rate_pct: 94.2,
  roi_annual_pct: 23.5,
};

export const DEMO_ESG: ESGReport = {
  reporting_period: "Q3 2026",
  overall_score: 87,
  scores: {
    carbon_reduction: { score: 92, target: 85, unit: "% vs baseline", value: 34.2 },
    renewable_utilization: { score: 78, target: 80, unit: "%", value: 62.4 },
    grid_resilience: { score: 89, target: 90, unit: "/100", value: 89 },
    energy_efficiency: { score: 85, target: 82, unit: "kWh/sqft", value: 12.3 },
    compliance: { score: 94, target: 95, unit: "%", value: 96.1 },
  },
  certifications: ["ISO 50001", "LEED Gold", "GRESB 4-Star"],
  emissions: { scope1_kg: 1240, scope2_kg: 48200, scope3_kg: 8900, total_kg: 58340, yoy_change_pct: -18.4 },
  renewable_mwh: 2840,
  carbon_offset_mwh: 420,
};

export const DEMO_ACTIVITY: ActivityItem[] = [
  { id: "a1", type: "optimization", message: "Battery dispatch optimized for peak shaving", site: "Manhattan Campus", level: "success", timestamp: new Date(Date.now() - 120000).toISOString(), automated: true },
  { id: "a2", type: "anomaly", message: "Voltage sag detected on Feeder B-12", site: "Philadelphia Microgrid", level: "warning", timestamp: new Date(Date.now() - 600000).toISOString(), automated: false },
  { id: "a3", type: "market", message: "DR event dispatched — 450 kW curtailed", site: "Brooklyn Data Center", level: "success", timestamp: new Date(Date.now() - 1800000).toISOString(), automated: true },
  { id: "a4", type: "forecast", message: "Heat wave forecast updated — +12% cooling load", site: "Newark Industrial", level: "info", timestamp: new Date(Date.now() - 3600000).toISOString(), automated: true },
  { id: "a5", type: "automation", message: "EV fleet charging shifted to off-peak window", site: "Stamford Hospital", level: "success", timestamp: new Date(Date.now() - 7200000).toISOString(), automated: true },
  { id: "a6", type: "compliance", message: "NERC CIP audit evidence auto-collected", site: "Portfolio", level: "success", timestamp: new Date(Date.now() - 14400000).toISOString(), automated: true },
];

export const DEMO_VPP = {
  vpp_name: "GridMind Northeast VPP",
  aggregated_capacity_kw: 2840,
  available_capacity_kw: 1920,
  enrolled_assets: 127,
  active_bids: 3,
  revenue_mtd_usd: 47820,
  markets: [
    { name: "NYISO Day-Ahead", status: "active", bid_kw: 800, clearing_price: 0.142, revenue_usd: 18400 },
    { name: "Con Edison DR", status: "active", bid_kw: 450, clearing_price: 0.28, revenue_usd: 12600 },
    { name: "Ancillary — Regulation", status: "standby", bid_kw: 200, clearing_price: 0.065, revenue_usd: 3200 },
    { name: "Capacity Market", status: "scheduled", bid_kw: 1200, clearing_price: 8.50, revenue_usd: 13620 },
  ],
};

export const DEMO_NOTIFICATIONS = [
  { id: "n1", title: "Peak demand alert in 2 hours", body: "Manhattan Campus projected to exceed 1,400 kW.", severity: "warning", read: false, time: "2m ago" },
  { id: "n2", title: "DR event scheduled", body: "Con Edison demand response tomorrow 2–6 PM.", severity: "info", read: false, time: "15m ago" },
  { id: "n3", title: "Optimization complete", body: "Saved $847 across portfolio in last 24h.", severity: "success", read: true, time: "1h ago" },
];

export const DEMO_DIGITAL_TWIN = {
  site_id: "site-manhattan-01",
  autonomy_level: "execute_with_approval",
  topology: {
    grid_connection: { status: "connected", voltage_v: 12480, capacity_kva: 5000 },
    solar_array: { status: "generating", capacity_kw: 500, output_kw: 340, inverters_online: 8 },
    battery_storage: { status: "discharging", capacity_kwh: 2000, soc_pct: 72, power_kw: 180 },
    load_centers: [
      { name: "Building A — HVAC", load_kw: 320, status: "normal" },
      { name: "Building B — Lighting", load_kw: 120, status: "normal" },
      { name: "EV Charging Hub", load_kw: 150, status: "charging" },
      { name: "Critical Loads", load_kw: 140, status: "protected" },
    ],
    transformers: [
      { id: "T-01", load_pct: 72, temp_c: 58, status: "normal" },
      { id: "T-02", load_pct: 45, temp_c: 42, status: "normal" },
    ],
  },
};
