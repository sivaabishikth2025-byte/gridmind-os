"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, BarChart, Bar, Legend, RadialBarChart, RadialBar,
} from "recharts";
import {
  Zap, Sun, Battery, Grid3x3, Leaf, AlertTriangle, Brain, TrendingDown,
  Activity, Thermometer, MessageSquare, Play, Loader2, Bell, Building2,
  DollarSign, Shield, MapPin, ChevronRight, Home, BarChart3, Cpu, FileText,
  ArrowLeft, CheckCircle2, Clock, Radio,
} from "lucide-react";
import {
  fetchAPI, fetchAPIWithFallback,
  SiteOverview, ForecastPoint, Anomaly, CarbonSummary,
  OptimizationResult, ClimateStress, Portfolio, ActivityItem, ESGReport, ExecutiveSummary,
} from "@/lib/api";
import {
  DEMO_PORTFOLIO, DEMO_ACTIVITY, DEMO_ESG, DEMO_EXECUTIVE, DEMO_VPP,
  DEMO_NOTIFICATIONS, DEMO_DIGITAL_TWIN,
} from "@/lib/demo-data";
import type { LiveGridData } from "@/lib/live-data";
import { LiveDataBanner, DataSourcesPanel, FuelMixPanel, NYLoadChart } from "@/components/LiveDataPanel";

type Tab = "overview" | "portfolio" | "optimize" | "markets" | "climate" | "carbon" | "esg" | "twin";

function MetricCard({ icon: Icon, label, value, unit, color, sub }: {
  icon: React.ElementType; label: string; value: string | number; unit: string;
  color: string; sub?: string;
}) {
  return (
    <div className="glass-card p-4 hover:bg-[#1f2a40] transition-colors">
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="text-xs text-slate-400 uppercase tracking-wider">{label}</span>
      </div>
      <div className="metric-value">{value}<span className="text-sm text-slate-400 ml-1">{unit}</span></div>
      {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cls = status === "optimal" ? "bg-emerald-500/20 text-emerald-400"
    : status === "elevated" ? "bg-amber-500/20 text-amber-400"
    : status === "warning" ? "bg-orange-500/20 text-orange-400"
    : "bg-red-500/20 text-red-400";
  return <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${cls}`}>{status}</span>;
}

const NAV: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: "overview", label: "Overview", icon: Home },
  { id: "portfolio", label: "Portfolio", icon: Building2 },
  { id: "twin", label: "Digital Twin", icon: Cpu },
  { id: "optimize", label: "Optimization", icon: Brain },
  { id: "markets", label: "VPP & Markets", icon: DollarSign },
  { id: "climate", label: "Climate", icon: Thermometer },
  { id: "carbon", label: "Carbon", icon: Leaf },
  { id: "esg", label: "ESG Reports", icon: FileText },
];

export default function Dashboard() {
  const [overview, setOverview] = useState<SiteOverview | null>(null);
  const [telemetry, setTelemetry] = useState<Record<string, { t: string; v: number }[]>>({});
  const [forecast, setForecast] = useState<ForecastPoint[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [carbon, setCarbon] = useState<CarbonSummary | null>(null);
  const [optimization, setOptimization] = useState<OptimizationResult | null>(null);
  const [climate, setClimate] = useState<ClimateStress | null>(null);
  const [portfolio, setPortfolio] = useState<Portfolio>(DEMO_PORTFOLIO);
  const [activity, setActivity] = useState<ActivityItem[]>(DEMO_ACTIVITY);
  const [esg, setEsg] = useState<ESGReport>(DEMO_ESG);
  const [executive, setExecutive] = useState<ExecutiveSummary>(DEMO_EXECUTIVE);
  const [vpp, setVpp] = useState(DEMO_VPP);
  const [notifications] = useState(DEMO_NOTIFICATIONS);
  const [digitalTwin, setDigitalTwin] = useState(DEMO_DIGITAL_TWIN);
  const [copilotQ, setCopilotQ] = useState("");
  const [copilotA, setCopilotA] = useState("");
  const [loading, setLoading] = useState({ optimize: false, detect: false, copilot: false });
  const [liveData, setLiveData] = useState<LiveGridData | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [showNotifications, setShowNotifications] = useState(false);
  const [selectedSite, setSelectedSite] = useState("site-manhattan-01");

  useEffect(() => {
    loadAll();
    const interval = setInterval(loadAll, 30000);
    return () => clearInterval(interval);
  }, []);

  // Poll live data (more reliable than WebSocket for hackathon demo)
  useEffect(() => {
    async function pollLive() {
      try {
        const live = await fetchAPI<LiveGridData>("/live/grid");
        setLiveData(live);
        setConnected(true);
        setApiError(null);
        setOverview({
          site_id: "site-manhattan-01",
          name: "Manhattan Campus Microgrid",
          load_kw: live.campus.load_kw,
          solar_kw: live.campus.solar_kw,
          battery_soc: live.campus.battery_soc,
          battery_power_kw: live.campus.battery_power_kw,
          grid_import_kw: live.campus.grid_import_kw,
          carbon_intensity: live.campus.carbon_intensity,
          status: live.campus.load_kw < 1000 ? "optimal" : "elevated",
        });
      } catch {
        setConnected(false);
        setApiError("Backend offline — showing demo data. Run: python -m uvicorn app.main:app --port 8100");
      }
    }
    pollLive();
    const interval = setInterval(pollLive, 30000);
    return () => clearInterval(interval);
  }, []);

  async function loadAll() {
    const [ov, tel, fc, an, cb, cl, pf, act, esgR, exec, vppR, twin] = await Promise.all([
      fetchAPIWithFallback<SiteOverview>("/site/overview", { site_id: "site-manhattan-01", name: "Manhattan Campus", load_kw: 892, solar_kw: 340, battery_soc: 72, battery_power_kw: 180, grid_import_kw: 512, carbon_intensity: 310, status: "optimal" }),
      fetchAPIWithFallback<Record<string, { t: string; v: number }[]>>("/telemetry/multi?hours=3", {}),
      fetchAPIWithFallback<ForecastPoint[]>("/forecast?hours=24", []),
      fetchAPIWithFallback<Anomaly[]>("/anomalies", []),
      fetchAPIWithFallback<CarbonSummary>("/carbon/summary?hours=24", { period_hours: 24, total_consumption_kwh: 18400, total_generation_kwh: 4200, net_emissions_kg: 4820, avoided_emissions_kg: 1240, avg_intensity_gco2: 310, trend: [] }),
      fetchAPIWithFallback<ClimateStress>("/climate/stress-test?scenario=heat_wave_2030", { scenario: "heat_wave_2030", temperature_delta_c: 4.5, peak_load_increase_pct: 12, projected_peak_kw: 1420, resilience_score: 78, recommendations: ["Upgrade HVAC chillers", "Add 500 kWh battery storage"] }),
      fetchAPIWithFallback<Portfolio>("/demo/portfolio", DEMO_PORTFOLIO),
      fetchAPIWithFallback<ActivityItem[]>("/demo/activity", DEMO_ACTIVITY),
      fetchAPIWithFallback<ESGReport>("/demo/esg", DEMO_ESG),
      fetchAPIWithFallback<ExecutiveSummary>("/demo/executive-summary", DEMO_EXECUTIVE),
      fetchAPIWithFallback<typeof DEMO_VPP>("/demo/vpp", DEMO_VPP),
      fetchAPIWithFallback("/demo/digital-twin", DEMO_DIGITAL_TWIN),
    ]);
    setOverview(ov); setTelemetry(tel); setForecast(fc); setAnomalies(an);
    setCarbon(cb); setClimate(cl); setPortfolio(pf); setActivity(act);
    setEsg(esgR); setExecutive(exec); setVpp(vppR); setDigitalTwin(twin);
  }

  async function runOptimization(objective: string) {
    setLoading((l) => ({ ...l, optimize: true }));
    try {
      const result = await fetchAPI<OptimizationResult>(`/optimize?objective=${objective}&hours=24`, { method: "POST" });
      setOptimization(result);
      setActiveTab("optimize");
    } catch { /* demo fallback */ }
    setLoading((l) => ({ ...l, optimize: false }));
  }

  async function detectAnomalies() {
    setLoading((l) => ({ ...l, detect: true }));
    try {
      const result = await fetchAPI<Anomaly[]>("/anomalies/detect", { method: "POST" });
      setAnomalies(result.length ? result : anomalies);
    } catch { /* keep existing */ }
    setLoading((l) => ({ ...l, detect: false }));
  }

  async function askCopilot() {
    if (!copilotQ.trim()) return;
    setLoading((l) => ({ ...l, copilot: true }));
    try {
      const res = await fetchAPI<{ answer: string }>("/copilot", { method: "POST", body: JSON.stringify({ question: copilotQ }) });
      setCopilotA(res.answer);
    } catch {
      setCopilotA("Site is operating normally. Current load: 892 kW, solar: 340 kW, battery SOC: 72%. No active anomalies. Projected savings today: $847 with current optimization policy.");
    }
    setLoading((l) => ({ ...l, copilot: false }));
  }

  const chartData = (telemetry.load_kw || []).length > 0
    ? telemetry.load_kw.map((p, i) => ({
        time: new Date(p.t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        load: p.v, solar: telemetry.solar_kw?.[i]?.v ?? 0, grid: telemetry.grid_import_kw?.[i]?.v ?? 0,
      }))
    : Array.from({ length: 24 }, (_, i) => ({
        time: `${i}:00`, load: 600 + Math.sin(i / 3) * 200 + Math.random() * 50,
        solar: i >= 6 && i <= 18 ? Math.sin((i - 6) / 12 * Math.PI) * 400 : 0,
        grid: 500 + Math.random() * 100,
      }));

  const forecastData = forecast.length > 0
    ? forecast.map((f) => ({
        time: new Date(f.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        load: f.load_kw, solar: f.solar_kw, low: f.confidence_low, high: f.confidence_high,
      }))
    : Array.from({ length: 24 }, (_, i) => {
        const load = 600 + Math.sin(i / 3) * 200;
        const solar = i >= 6 && i <= 18 ? Math.sin((i - 6) / 12 * Math.PI) * 400 : 0;
        return { time: `${i}:00`, load, solar, low: load * 0.9, high: load * 1.1 };
      });

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="min-h-screen bg-[#0b0f19] flex">
      {/* Sidebar */}
      <aside className="w-56 border-r border-[#2a3548] bg-[#111827]/50 hidden lg:flex flex-col fixed h-full z-40">
        <div className="p-4 border-b border-[#2a3548]">
          <Link href="/" className="flex items-center gap-2 text-slate-400 hover:text-white text-xs mb-3">
            <ArrowLeft className="w-3 h-3" /> Back to Home
          </Link>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-bold text-sm">GridMind OS</div>
              <div className="text-[10px] text-slate-500">Command Center</div>
            </div>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV.map((item) => (
            <button key={item.id} onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                activeTab === item.id ? "bg-emerald-500/15 text-emerald-400" : "text-slate-400 hover:text-white hover:bg-[#1a2234]"
              }`}>
              <item.icon className="w-4 h-4" /> {item.label}
            </button>
          ))}
        </nav>
        <div className="p-4 border-t border-[#2a3548]">
          <div className="flex items-center gap-2 text-xs">
            <div className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-400 animate-pulse" : "bg-amber-400"}`} />
            <span className="text-slate-500">{connected ? "Live NYISO Data" : "Demo Mode"}</span>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 lg:ml-56">
        {/* Top bar */}
        <header className="border-b border-[#2a3548] bg-[#111827]/80 backdrop-blur-md sticky top-0 z-30">
          <div className="px-6 py-3 flex items-center justify-between">
            <div>
              <h1 className="text-lg font-bold">{NAV.find((n) => n.id === activeTab)?.label}</h1>
              <p className="text-xs text-slate-500">{overview?.name || "Manhattan Campus Microgrid"}</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="hidden md:flex items-center gap-6 text-xs text-slate-400 mr-4">
                <span>Savings MTD: <strong className="text-emerald-400">${executive.cost_savings_usd.toLocaleString()}</strong></span>
                <span>Automation: <strong className="text-cyan-400">{executive.automation_rate_pct}%</strong></span>
              </div>
              <div className="relative">
                <button onClick={() => setShowNotifications(!showNotifications)}
                  className="relative p-2 rounded-lg hover:bg-[#1a2234] transition-colors">
                  <Bell className="w-5 h-5 text-slate-400" />
                  {unreadCount > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 rounded-full text-[10px] flex items-center justify-center font-bold">{unreadCount}</span>
                  )}
                </button>
                {showNotifications && (
                  <div className="absolute right-0 top-12 w-80 glass-card p-3 shadow-xl z-50">
                    <h3 className="text-sm font-semibold mb-3">Notifications</h3>
                    {notifications.map((n) => (
                      <div key={n.id} className={`p-3 rounded-lg mb-2 ${n.read ? "opacity-60" : "bg-[#0b0f19]"}`}>
                        <div className="text-sm font-medium">{n.title}</div>
                        <div className="text-xs text-slate-400 mt-1">{n.body}</div>
                        <div className="text-[10px] text-slate-500 mt-1">{n.time}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center text-xs font-bold">GM</div>
            </div>
          </div>
          {/* Mobile tabs */}
          <div className="lg:hidden flex gap-1 px-4 pb-2 overflow-x-auto">
            {NAV.map((item) => (
              <button key={item.id} onClick={() => setActiveTab(item.id)}
                className={`px-3 py-1.5 text-xs rounded-lg whitespace-nowrap ${
                  activeTab === item.id ? "bg-emerald-500/20 text-emerald-400" : "text-slate-400"
                }`}>{item.label}</button>
            ))}
          </div>
        </header>

        <main className="p-6 space-y-6">
          {apiError && (
            <div className="glass-card p-3 border-amber-500/30 bg-amber-500/5 text-sm text-amber-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" /> {apiError}
            </div>
          )}

          <LiveDataBanner live={liveData} />

          {/* Executive banner */}
          <div className="glass-card p-4 flex flex-wrap items-center gap-6 text-sm">
            <div className="flex items-center gap-2"><BarChart3 className="w-4 h-4 text-emerald-400" /><span className="text-slate-400">Portfolio:</span><strong>{portfolio.total_sites} sites</strong></div>
            <div className="flex items-center gap-2"><Zap className="w-4 h-4 text-amber-400" /><span className="text-slate-400">Load:</span><strong>{portfolio.total_load_kw.toLocaleString()} kW</strong></div>
            <div className="flex items-center gap-2"><Sun className="w-4 h-4 text-yellow-400" /><span className="text-slate-400">Solar:</span><strong>{portfolio.total_solar_kw.toLocaleString()} kW</strong></div>
            <div className="flex items-center gap-2"><DollarSign className="w-4 h-4 text-emerald-400" /><span className="text-slate-400">Savings:</span><strong className="text-emerald-400">${portfolio.total_savings_mtd_usd.toLocaleString()} MTD</strong></div>
            <div className="flex items-center gap-2"><Shield className="w-4 h-4 text-cyan-400" /><span className="text-slate-400">Uptime:</span><strong>{executive.uptime_pct}%</strong></div>
            {portfolio.active_alerts > 0 && (
              <div className="flex items-center gap-2 text-amber-400"><AlertTriangle className="w-4 h-4" /><strong>{portfolio.active_alerts} active alert</strong></div>
            )}
          </div>

          {/* KPI Row */}
          {(activeTab === "overview") && (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <MetricCard icon={Zap} label="Load" value={overview?.load_kw?.toFixed(0) ?? "892"} unit="kW" color="text-amber-400" />
              <MetricCard icon={Sun} label="Solar" value={overview?.solar_kw?.toFixed(0) ?? "340"} unit="kW" color="text-yellow-400" />
              <MetricCard icon={Battery} label="Battery" value={overview?.battery_soc?.toFixed(0) ?? "72"} unit="%" color="text-emerald-400" sub={`${overview?.battery_power_kw?.toFixed(0) ?? 180} kW`} />
              <MetricCard icon={Grid3x3} label="Grid Import" value={overview?.grid_import_kw?.toFixed(0) ?? "512"} unit="kW" color="text-blue-400" />
              <MetricCard icon={Leaf} label="Carbon" value={overview?.carbon_intensity?.toFixed(0) ?? "310"} unit="gCO₂/kWh" color="text-green-400" />
              <MetricCard icon={TrendingDown} label="Emissions 24h" value={carbon?.net_emissions_kg?.toFixed(0) ?? "4,820"} unit="kg" color="text-cyan-400" sub={`${carbon?.avoided_emissions_kg?.toFixed(0) ?? "1,240"} kg avoided`} />
            </div>
          )}

          {/* OVERVIEW TAB */}
          {activeTab === "overview" && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <NYLoadChart live={liveData} />
                <div className="glass-card p-5">
                <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-400" /> Live Grid Telemetry
                  <span className="ml-auto flex items-center gap-1 text-xs text-emerald-400"><Radio className="w-3 h-3" /> Streaming</span>
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="loadGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} /><stop offset="95%" stopColor="#f59e0b" stopOpacity={0} /></linearGradient>
                      <linearGradient id="solarGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#eab308" stopOpacity={0.3} /><stop offset="95%" stopColor="#eab308" stopOpacity={0} /></linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a3548" />
                    <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip contentStyle={{ background: "#1a2234", border: "1px solid #2a3548", borderRadius: 8 }} />
                    <Area type="monotone" dataKey="load" stroke="#f59e0b" fill="url(#loadGrad)" name="Load (kW)" />
                    <Area type="monotone" dataKey="solar" stroke="#eab308" fill="url(#solarGrad)" name="Solar (kW)" />
                    <Line type="monotone" dataKey="grid" stroke="#3b82f6" dot={false} name="Grid (kW)" />
                  </AreaChart>
                </ResponsiveContainer>
                </div>
              </div>

              <div className="space-y-6">
                <DataSourcesPanel live={liveData} />
                <FuelMixPanel live={liveData} />
                <div className="glass-card p-5">
                <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-cyan-400" /> Activity Feed
                </h2>
                <div className="space-y-3 max-h-[300px] overflow-y-auto">
                  {activity.map((a) => (
                    <div key={a.id} className="flex gap-3 text-xs">
                      <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                        a.level === "success" ? "bg-emerald-400" : a.level === "warning" ? "bg-amber-400" : "bg-blue-400"
                      }`} />
                      <div>
                        <p className="text-slate-300">{a.message}</p>
                        <p className="text-slate-500 mt-0.5">{a.site} {a.automated && "· Auto"}</p>
                      </div>
                    </div>
                  ))}
                </div>
                </div>
              </div>

              <div className="lg:col-span-2 glass-card p-5">
                <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                  <Brain className="w-4 h-4 text-cyan-400" /> AI Load & Solar Forecast (24h)
                </h2>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={forecastData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a3548" />
                    <XAxis dataKey="time" stroke="#64748b" fontSize={10} interval="preserveStartEnd" />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip contentStyle={{ background: "#1a2234", border: "1px solid #2a3548", borderRadius: 8 }} />
                    <Legend />
                    <Line type="monotone" dataKey="load" stroke="#f59e0b" dot={false} name="Load" />
                    <Line type="monotone" dataKey="solar" stroke="#eab308" dot={false} name="Solar" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="glass-card p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400" /> Anomalies
                  </h2>
                  <button onClick={detectAnomalies} disabled={loading.detect}
                    className="text-xs px-3 py-1 rounded bg-amber-500/20 text-amber-400 hover:bg-amber-500/30 disabled:opacity-50">
                    {loading.detect ? <Loader2 className="w-3 h-3 animate-spin" /> : "Scan"}
                  </button>
                </div>
                <div className="space-y-3 max-h-[200px] overflow-y-auto">
                  {anomalies.length === 0 ? (
                    <div className="flex items-center gap-2 text-sm text-emerald-400"><CheckCircle2 className="w-4 h-4" /> All systems nominal</div>
                  ) : anomalies.map((a) => (
                    <div key={a.id} className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/5 text-xs">
                      <span className="font-bold text-amber-400 uppercase">{a.severity}</span>
                      <p className="text-slate-300 mt-1">{a.root_cause}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-4 pt-4 border-t border-[#2a3548]">
                  <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2"><MessageSquare className="w-4 h-4 text-purple-400" /> AI Copilot</h3>
                  <input value={copilotQ} onChange={(e) => setCopilotQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && askCopilot()}
                    placeholder="Ask anything about your grid..."
                    className="w-full bg-[#0b0f19] border border-[#2a3548] rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 mb-2" />
                  <button onClick={askCopilot} disabled={loading.copilot}
                    className="w-full py-2 rounded-lg bg-purple-500/20 text-purple-400 text-sm hover:bg-purple-500/30 disabled:opacity-50 flex items-center justify-center gap-2">
                    {loading.copilot ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />} Ask GridMind
                  </button>
                  {copilotA && <div className="mt-2 p-3 rounded-lg bg-[#0b0f19] border border-[#2a3548] text-xs text-slate-300">{copilotA}</div>}
                </div>
              </div>
            </div>
          )}

          {/* PORTFOLIO TAB */}
          {activeTab === "portfolio" && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard icon={Building2} label="Sites" value={portfolio.total_sites} unit="" color="text-blue-400" />
                <MetricCard icon={Zap} label="Total Load" value={portfolio.total_load_kw.toLocaleString()} unit="kW" color="text-amber-400" />
                <MetricCard icon={Sun} label="Renewable" value={portfolio.avg_renewable_pct} unit="%" color="text-yellow-400" />
                <MetricCard icon={DollarSign} label="Savings MTD" value={`$${(portfolio.total_savings_mtd_usd / 1000).toFixed(1)}K`} unit="" color="text-emerald-400" />
              </div>
              <div className="glass-card overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="border-b border-[#2a3548] text-slate-400 text-xs uppercase">
                    <tr>
                      <th className="text-left p-4">Site</th>
                      <th className="text-left p-4">Type</th>
                      <th className="text-right p-4">Load</th>
                      <th className="text-right p-4">Solar</th>
                      <th className="text-right p-4">Battery</th>
                      <th className="text-right p-4">Renewable</th>
                      <th className="text-right p-4">Savings</th>
                      <th className="text-center p-4">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolio.sites.map((site) => (
                      <tr key={site.id} className="border-b border-[#2a3548]/50 hover:bg-[#1a2234]/50 cursor-pointer transition-colors"
                        onClick={() => { setSelectedSite(site.id); setActiveTab("twin"); }}>
                        <td className="p-4">
                          <div className="font-medium">{site.name}</div>
                          <div className="text-xs text-slate-500 flex items-center gap-1"><MapPin className="w-3 h-3" />{site.city}</div>
                        </td>
                        <td className="p-4 text-slate-400">{site.type}</td>
                        <td className="p-4 text-right">{site.load_kw} kW</td>
                        <td className="p-4 text-right text-yellow-400">{site.solar_kw} kW</td>
                        <td className="p-4 text-right">{site.battery_soc}%</td>
                        <td className="p-4 text-right">{site.renewable_pct}%</td>
                        <td className="p-4 text-right text-emerald-400">${site.savings_mtd_usd.toLocaleString()}</td>
                        <td className="p-4 text-center"><StatusBadge status={site.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* DIGITAL TWIN TAB */}
          {activeTab === "twin" && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="glass-card p-6">
                <h2 className="text-sm font-semibold text-slate-300 mb-6 flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-cyan-400" /> Site Topology — {portfolio.sites.find(s => s.id === selectedSite)?.name || "Manhattan Campus"}
                </h2>
                <div className="space-y-4">
                  {/* Grid connection */}
                  <div className="flex items-center gap-4 p-4 rounded-lg bg-[#0b0f19] border border-[#2a3548]">
                    <Grid3x3 className="w-8 h-8 text-blue-400" />
                    <div className="flex-1">
                      <div className="font-medium">Grid Connection</div>
                      <div className="text-xs text-slate-500">{digitalTwin.topology.grid_connection.voltage_v} V · {digitalTwin.topology.grid_connection.capacity_kva} kVA</div>
                    </div>
                    <StatusBadge status="optimal" />
                  </div>
                  {/* Solar */}
                  <div className="flex items-center gap-4 p-4 rounded-lg bg-[#0b0f19] border border-[#2a3548]">
                    <Sun className="w-8 h-8 text-yellow-400" />
                    <div className="flex-1">
                      <div className="font-medium">Solar Array — {digitalTwin.topology.solar_array.output_kw} kW</div>
                      <div className="text-xs text-slate-500">{digitalTwin.topology.solar_array.inverters_online}/8 inverters online</div>
                    </div>
                    <StatusBadge status="optimal" />
                  </div>
                  {/* Battery */}
                  <div className="flex items-center gap-4 p-4 rounded-lg bg-[#0b0f19] border border-[#2a3548]">
                    <Battery className="w-8 h-8 text-emerald-400" />
                    <div className="flex-1">
                      <div className="font-medium">Battery — {digitalTwin.topology.battery_storage.soc_pct}% SOC</div>
                      <div className="text-xs text-slate-500">{digitalTwin.topology.battery_storage.power_kw} kW · {digitalTwin.topology.battery_storage.capacity_kwh} kWh</div>
                      <div className="w-full h-2 bg-[#2a3548] rounded-full mt-2">
                        <div className="h-full bg-emerald-500 rounded-full transition-all" style={{ width: `${digitalTwin.topology.battery_storage.soc_pct}%` }} />
                      </div>
                    </div>
                  </div>
                  {/* Load centers */}
                  {digitalTwin.topology.load_centers.map((lc: { name: string; load_kw: number; status: string }) => (
                    <div key={lc.name} className="flex items-center gap-4 p-3 rounded-lg bg-[#0b0f19]/50 border border-[#2a3548]/50">
                      <Zap className="w-5 h-5 text-amber-400" />
                      <div className="flex-1 text-sm">{lc.name}</div>
                      <div className="text-sm font-medium">{lc.load_kw} kW</div>
                      <StatusBadge status={lc.status === "protected" ? "optimal" : "optimal"} />
                    </div>
                  ))}
                </div>
              </div>
              <div className="space-y-6">
                <div className="glass-card p-5">
                  <h3 className="text-sm font-semibold text-slate-300 mb-4">Transformers</h3>
                  {digitalTwin.topology.transformers.map((t: { id: string; load_pct: number; temp_c: number; status: string }) => (
                    <div key={t.id} className="flex items-center justify-between p-3 rounded-lg bg-[#0b0f19] mb-2">
                      <span className="font-medium">{t.id}</span>
                      <span className="text-sm text-slate-400">{t.load_pct}% load · {t.temp_c}°C</span>
                      <StatusBadge status="optimal" />
                    </div>
                  ))}
                </div>
                <div className="glass-card p-5">
                  <h3 className="text-sm font-semibold text-slate-300 mb-4">Autonomy Settings</h3>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between"><span className="text-slate-400">Mode</span><span className="text-emerald-400 font-medium">Execute with Approval</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Last Optimization</span><span>12 min ago</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Next DR Event</span><span className="text-amber-400">In 4h 30m</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Safety Limits</span><span>Min SOC 15% · Max peak 1,500 kW</span></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* OPTIMIZE TAB */}
          {activeTab === "optimize" && (
            <div className="space-y-6">
              <div className="flex flex-wrap gap-3">
                {["balanced", "cost", "carbon", "peak"].map((obj) => (
                  <button key={obj} onClick={() => runOptimization(obj)} disabled={loading.optimize}
                    className="px-4 py-2 rounded-lg bg-emerald-500/20 text-emerald-400 text-sm hover:bg-emerald-500/30 disabled:opacity-50 flex items-center gap-2">
                    {loading.optimize ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                    Optimize: {obj}
                  </button>
                ))}
              </div>
              {optimization ? (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="glass-card p-5 space-y-4">
                    <h3 className="text-sm font-semibold text-slate-300">Results</h3>
                    <div className="space-y-3">
                      <div><span className="text-xs text-slate-500">Savings</span><div className="text-xl font-bold text-emerald-400">${optimization.total_savings_usd}</div></div>
                      <div><span className="text-xs text-slate-500">Peak Reduction</span><div className="text-xl font-bold text-amber-400">{optimization.peak_reduction_kw} kW</div></div>
                      <div><span className="text-xs text-slate-500">Carbon Reduction</span><div className="text-xl font-bold text-cyan-400">{optimization.carbon_reduction_kg} kg</div></div>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">{optimization.explanation}</p>
                  </div>
                  <div className="lg:col-span-2 glass-card p-5">
                    <h3 className="text-sm font-semibold text-slate-300 mb-4">Battery Dispatch Schedule</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={optimization.schedule}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a3548" />
                        <XAxis dataKey="hour" stroke="#64748b" fontSize={11} />
                        <YAxis stroke="#64748b" fontSize={11} />
                        <Tooltip contentStyle={{ background: "#1a2234", border: "1px solid #2a3548", borderRadius: 8 }} />
                        <Legend />
                        <Bar dataKey="battery_power_kw" fill="#10b981" name="Battery (kW)" />
                        <Bar dataKey="grid_import_kw" fill="#3b82f6" name="Grid Import (kW)" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : (
                <div className="glass-card p-10 text-center text-slate-400">
                  <Brain className="w-12 h-12 mx-auto mb-4 text-emerald-400/50" />
                  <p>Click an optimization objective above to run the AI dispatch engine.</p>
                  <p className="text-xs mt-2">Uses PuLP linear programming with real load forecasts and carbon intensity data.</p>
                </div>
              )}
            </div>
          )}

          {/* MARKETS TAB */}
          {activeTab === "markets" && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard icon={Cpu} label="VPP Capacity" value={vpp.aggregated_capacity_kw.toLocaleString()} unit="kW" color="text-blue-400" />
                <MetricCard icon={Zap} label="Available" value={vpp.available_capacity_kw.toLocaleString()} unit="kW" color="text-emerald-400" />
                <MetricCard icon={Building2} label="Assets" value={vpp.enrolled_assets} unit="" color="text-cyan-400" />
                <MetricCard icon={DollarSign} label="Revenue MTD" value={`$${(vpp.revenue_mtd_usd / 1000).toFixed(1)}K`} unit="" color="text-emerald-400" />
              </div>
              <div className="glass-card overflow-hidden">
                <div className="p-4 border-b border-[#2a3548]"><h3 className="font-semibold">{vpp.vpp_name}</h3></div>
                <table className="w-full text-sm">
                  <thead className="border-b border-[#2a3548] text-slate-400 text-xs uppercase">
                    <tr><th className="text-left p-4">Market</th><th className="text-center p-4">Status</th><th className="text-right p-4">Bid</th><th className="text-right p-4">Price</th><th className="text-right p-4">Revenue</th></tr>
                  </thead>
                  <tbody>
                    {vpp.markets.map((m) => (
                      <tr key={m.name} className="border-b border-[#2a3548]/50 hover:bg-[#1a2234]/50">
                        <td className="p-4 font-medium">{m.name}</td>
                        <td className="p-4 text-center"><StatusBadge status={m.status === "active" ? "optimal" : "elevated"} /></td>
                        <td className="p-4 text-right">{m.bid_kw} kW</td>
                        <td className="p-4 text-right">${m.clearing_price}</td>
                        <td className="p-4 text-right text-emerald-400">${m.revenue_usd.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* CLIMATE TAB */}
          {activeTab === "climate" && climate && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="glass-card p-5 space-y-4">
                <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                  <Thermometer className="w-4 h-4 text-red-400" /> Climate Stress: {climate.scenario}
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 rounded-lg bg-[#0b0f19]"><span className="text-xs text-slate-500">Temp Delta</span><div className="text-lg font-bold">+{climate.temperature_delta_c}°C</div></div>
                  <div className="p-3 rounded-lg bg-[#0b0f19]"><span className="text-xs text-slate-500">Peak Increase</span><div className="text-lg font-bold text-amber-400">+{climate.peak_load_increase_pct}%</div></div>
                  <div className="p-3 rounded-lg bg-[#0b0f19]"><span className="text-xs text-slate-500">Projected Peak</span><div className="text-lg font-bold">{climate.projected_peak_kw} kW</div></div>
                  <div className="p-3 rounded-lg bg-[#0b0f19]"><span className="text-xs text-slate-500">Resilience</span><div className="text-lg font-bold text-emerald-400">{climate.resilience_score}/100</div></div>
                </div>
              </div>
              <div className="glass-card p-5">
                <h3 className="text-sm font-semibold text-slate-300 mb-4">Recommendations</h3>
                <ul className="space-y-3">
                  {climate.recommendations.map((r, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-300"><ChevronRight className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* CARBON TAB */}
          {activeTab === "carbon" && carbon && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="glass-card p-5 space-y-4">
                <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2"><Leaf className="w-4 h-4 text-green-400" /> Carbon Audit (24h)</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 rounded-lg bg-[#0b0f19]"><span className="text-xs text-slate-500">Consumption</span><div className="text-lg font-bold">{carbon.total_consumption_kwh.toFixed(0)} kWh</div></div>
                  <div className="p-3 rounded-lg bg-[#0b0f19]"><span className="text-xs text-slate-500">Generation</span><div className="text-lg font-bold text-yellow-400">{carbon.total_generation_kwh.toFixed(0)} kWh</div></div>
                  <div className="p-3 rounded-lg bg-[#0b0f19]"><span className="text-xs text-slate-500">Net Emissions</span><div className="text-lg font-bold text-red-400">{carbon.net_emissions_kg.toFixed(0)} kg</div></div>
                  <div className="p-3 rounded-lg bg-[#0b0f19]"><span className="text-xs text-slate-500">Avoided</span><div className="text-lg font-bold text-emerald-400">{carbon.avoided_emissions_kg.toFixed(0)} kg</div></div>
                </div>
              </div>
              <div className="glass-card p-5 flex items-center justify-center">
                <ResponsiveContainer width="100%" height={200}>
                  <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="100%" data={[{ name: "Renewable", value: portfolio.avg_renewable_pct, fill: "#10b981" }]} startAngle={90} endAngle={-270}>
                    <RadialBar dataKey="value" cornerRadius={10} />
                    <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" className="fill-white text-2xl font-bold">{portfolio.avg_renewable_pct}%</text>
                  </RadialBarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* ESG TAB */}
          {activeTab === "esg" && (
            <div className="space-y-6">
              <div className="glass-card p-6 flex items-center gap-8">
                <div className="text-center">
                  <div className="text-5xl font-bold gradient-text">{esg.overall_score}</div>
                  <div className="text-sm text-slate-400 mt-1">ESG Score</div>
                  <div className="text-xs text-slate-500">{esg.reporting_period}</div>
                </div>
                <div className="flex-1 grid grid-cols-2 md:grid-cols-3 gap-4">
                  {Object.entries(esg.scores).map(([key, s]) => (
                    <div key={key} className="p-3 rounded-lg bg-[#0b0f19]">
                      <div className="text-xs text-slate-500 capitalize">{key.replace(/_/g, " ")}</div>
                      <div className="flex items-end gap-2 mt-1">
                        <span className="text-xl font-bold">{s.score}</span>
                        <span className="text-xs text-slate-500">/ {s.target} {s.unit}</span>
                      </div>
                      <div className="w-full h-1.5 bg-[#2a3548] rounded-full mt-2">
                        <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${Math.min(100, s.score)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="glass-card p-5">
                  <h3 className="text-sm font-semibold mb-4">Emissions</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-slate-400">Scope 1</span><span>{esg.emissions.scope1_kg.toLocaleString()} kg</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Scope 2</span><span>{esg.emissions.scope2_kg.toLocaleString()} kg</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Scope 3</span><span>{esg.emissions.scope3_kg.toLocaleString()} kg</span></div>
                    <div className="flex justify-between font-bold pt-2 border-t border-[#2a3548]"><span>YoY Change</span><span className="text-emerald-400">{esg.emissions.yoy_change_pct}%</span></div>
                  </div>
                </div>
                <div className="glass-card p-5">
                  <h3 className="text-sm font-semibold mb-4">Renewable Energy</h3>
                  <div className="text-3xl font-bold text-yellow-400">{esg.renewable_mwh.toLocaleString()} MWh</div>
                  <div className="text-sm text-slate-400 mt-2">+ {esg.carbon_offset_mwh} MWh carbon offsets</div>
                </div>
                <div className="glass-card p-5">
                  <h3 className="text-sm font-semibold mb-4">Certifications</h3>
                  <div className="space-y-2">
                    {esg.certifications.map((c) => (
                      <div key={c} className="flex items-center gap-2 text-sm"><CheckCircle2 className="w-4 h-4 text-emerald-400" />{c}</div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
