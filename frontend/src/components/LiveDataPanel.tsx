"use client";

import { Radio, ExternalLink, Database } from "lucide-react";
import type { LiveGridData } from "@/lib/live-data";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

const FUEL_COLORS: Record<string, string> = {
  "Natural Gas": "#f59e0b",
  "Nuclear": "#8b5cf6",
  "Dual Fuel": "#ef4444",
  "Hydro": "#3b82f6",
  "Wind": "#06b6d4",
  "Other Renewables": "#10b981",
  "Other Fossil Fuels": "#64748b",
};

export function LiveDataBanner({ live }: { live: LiveGridData | null }) {
  if (!live) return null;
  return (
    <div className="glass-card p-4 border-emerald-500/30 bg-emerald-500/5">
      <div className="flex items-start gap-3">
        <Radio className="w-5 h-5 text-emerald-400 mt-0.5 shrink-0 animate-pulse" />
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Live Open Data</span>
            <span className="text-[10px] text-slate-500">Updated {new Date(live.fetched_at).toLocaleTimeString()}</span>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">{live.judge_summary}</p>
          <p className="text-xs text-slate-500 mt-1">{live.campus.scale_note}</p>
        </div>
      </div>
    </div>
  );
}

export function DataSourcesPanel({ live }: { live: LiveGridData | null }) {
  if (!live) {
    return (
      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
          <Database className="w-4 h-4" /> Data Sources
        </h3>
        <p className="text-sm text-slate-500">Start the backend to load real NYISO + Open-Meteo data.</p>
      </div>
    );
  }

  return (
    <div className="glass-card p-5">
      <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
        <Database className="w-4 h-4 text-cyan-400" /> Live Data Sources
        <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400">{live.sources.length} active</span>
      </h3>
      <div className="space-y-2">
        {live.sources.map((s, i) => (
          <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-[#0b0f19] text-xs">
            <div>
              <span className="font-medium text-slate-200">{s.name}</span>
              <span className="text-slate-500 ml-2">{s.dataset}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-400 font-medium">{s.status}</span>
              {s.url && (
                <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-white">
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function FuelMixPanel({ live }: { live: LiveGridData | null }) {
  if (!live?.fuel_mix?.length) return null;

  const chartData = live.fuel_mix.map((f) => ({
    name: f.fuel,
    value: f.pct,
    mw: f.mw,
  }));

  return (
    <div className="glass-card p-5">
      <h3 className="text-sm font-semibold text-slate-300 mb-1">NY Grid Fuel Mix</h3>
      <p className="text-xs text-slate-500 mb-4">Real-time from NYISO — {live.fuel_mix.reduce((s, f) => s + f.mw, 0).toLocaleString()} MW total generation</p>
      <div className="flex gap-4 items-center">
        <ResponsiveContainer width={140} height={140}>
          <PieChart>
            <Pie data={chartData} dataKey="value" cx="50%" cy="50%" innerRadius={35} outerRadius={60} paddingAngle={2}>
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={FUEL_COLORS[entry.name] || "#64748b"} />
              ))}
            </Pie>
            <Tooltip formatter={(v) => `${v}%`} contentStyle={{ background: "#1a2234", border: "1px solid #2a3548", borderRadius: 8, fontSize: 12 }} />
          </PieChart>
        </ResponsiveContainer>
        <div className="flex-1 space-y-1.5">
          {live.fuel_mix.slice(0, 5).map((f) => (
            <div key={f.fuel} className="flex items-center gap-2 text-xs">
              <div className="w-2 h-2 rounded-full" style={{ background: FUEL_COLORS[f.fuel] || "#64748b" }} />
              <span className="text-slate-300 flex-1">{f.fuel}</span>
              <span className="text-slate-400">{f.pct}%</span>
              <span className="text-slate-500 w-16 text-right">{f.mw.toLocaleString()} MW</span>
            </div>
          ))}
        </div>
      </div>
      {live.carbon && (
        <div className="mt-4 pt-3 border-t border-[#2a3548] grid grid-cols-2 gap-3 text-xs">
          <div><span className="text-slate-500">Carbon Intensity</span><div className="text-lg font-bold text-green-400">{live.carbon.intensity_gco2_kwh} gCO₂/kWh</div></div>
          <div><span className="text-slate-500">Renewable</span><div className="text-lg font-bold text-emerald-400">{live.carbon.renewable_pct}%</div></div>
        </div>
      )}
    </div>
  );
}

export function NYLoadChart({ live }: { live: LiveGridData | null }) {
  if (!live?.nyiso?.load_history?.length) return null;

  const data = live.nyiso.load_history.map((h) => ({
    time: h.timestamp.split(" ")[1]?.slice(0, 5) || "",
    nyc: h.load_mw,
    campus: h.campus_kw,
  }));

  return (
    <div className="glass-card p-5">
      <h3 className="text-sm font-semibold text-slate-300 mb-1">NYISO NYC Zone Load</h3>
      <p className="text-xs text-slate-500 mb-4">
        Real grid load: <strong className="text-amber-400">{live.nyiso.nyc_zone_load_mw?.toLocaleString()} MW</strong> right now
        · Campus scaled: <strong className="text-cyan-400">{live.campus.load_kw} kW</strong>
      </p>
      <div className="h-48 flex items-end gap-0.5">
        {data.map((d, i) => (
          <div key={i} className="flex-1 flex flex-col items-center gap-1">
            <div className="w-full bg-amber-500/60 rounded-t" style={{ height: `${(d.nyc / Math.max(...data.map((x) => x.nyc))) * 100}%`, minHeight: 2 }} title={`${d.nyc} MW`} />
            {i % 6 === 0 && <span className="text-[9px] text-slate-600">{d.time}</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
