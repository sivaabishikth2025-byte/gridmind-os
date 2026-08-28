export interface LiveGridData {
  fetched_at: string;
  sources: { name: string; dataset: string; status: string; url?: string }[];
  nyiso: {
    nyc_zone_load_mw: number;
    total_ny_load_mw: number;
    load_history: { timestamp: string; load_mw: number; campus_kw: number }[];
    zone: string;
  };
  fuel_mix: { fuel: string; mw: number; pct: number }[];
  carbon: {
    intensity_gco2_kwh: number;
    renewable_pct: number;
    method: string;
    source: string;
  };
  prices: { nyc_lbmp_mwh: number; nyc_lbmp_kwh: number; timestamp: string };
  weather: {
    temperature_c: number;
    cloud_cover_pct: number;
    wind_speed_ms: number;
    solar_irradiance_wm2: number;
    source: string;
  };
  campus: {
    load_kw: number;
    solar_kw: number;
    battery_soc: number;
    battery_power_kw: number;
    grid_import_kw: number;
    price_kwh: number;
    carbon_intensity: number;
    scale_note: string;
  };
  judge_summary: string;
}
