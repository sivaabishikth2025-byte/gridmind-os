import Link from "next/link";
import {
  Zap, ArrowRight, Brain, Shield, Leaf, BarChart3, Cpu,
  Globe, Battery, TrendingDown, CheckCircle2, Play,
} from "lucide-react";

const FEATURES = [
  { icon: Brain, title: "AI Load Forecasting", desc: "Gradient boosting models predict demand 24–48h ahead with confidence intervals and weather integration." },
  { icon: Battery, title: "Battery Dispatch Optimization", desc: "PuLP linear programming optimizes cost, carbon, and peak shaving across your entire portfolio." },
  { icon: Shield, title: "Anomaly Detection", desc: "Isolation Forest + rule-based root cause analysis catches faults before they become outages." },
  { icon: Leaf, title: "Carbon Auditing", desc: "Real-time Scope 1/2/3 emissions ledger with marginal intensity dispatch and ESG report generation." },
  { icon: Globe, title: "Climate Stress Testing", desc: "IPCC-aligned scenarios project peak load, resilience scores, and adaptation recommendations." },
  { icon: Cpu, title: "Virtual Power Plant", desc: "Aggregate distributed assets into a single bidirectional resource for market participation." },
];

const STATS = [
  { value: "23.5%", label: "Avg. Cost Reduction" },
  { value: "2,340 kW", label: "Peak Shaving" },
  { value: "184 t", label: "CO₂ Avoided / Month" },
  { value: "99.97%", label: "Platform Uptime" },
];

const STEPS = [
  { step: "01", title: "Connect Assets", desc: "Ingest telemetry from meters, inverters, batteries, and BMS via MQTT, Modbus, or REST." },
  { step: "02", title: "AI Analyzes", desc: "Forecasting, anomaly detection, and carbon modeling run continuously on live data streams." },
  { step: "03", title: "Optimize & Act", desc: "Multi-objective optimizer dispatches batteries, shifts loads, and bids into energy markets." },
  { step: "04", title: "Measure Impact", desc: "Track savings, emissions, and resilience with executive dashboards and ESG reports." },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0b0f19]">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 border-b border-[#2a3548]/50 bg-[#0b0f19]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold">GridMind OS</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-slate-400">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a>
            <a href="#impact" className="hover:text-white transition-colors">Impact</a>
          </div>
          <Link href="/dashboard"
            className="px-5 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-white text-sm font-medium transition-colors flex items-center gap-2">
            Launch Command Center <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero-glow pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-sm mb-8">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Autonomous Grid Intelligence Platform
          </div>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 leading-tight">
            Optimize Energy.<br />
            <span className="gradient-text">Reduce Carbon.</span><br />
            Automate the Grid.
          </h1>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            GridMind OS pulls <strong className="text-slate-300">real live data</strong> from NYISO (NY grid operator),
            Open-Meteo (NOAA weather), and EPA eGRID — then uses AI to optimize energy, cut costs, and reduce carbon.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/dashboard"
              className="px-8 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-semibold transition-all flex items-center gap-2 animate-pulse-glow">
              <Play className="w-5 h-5" /> Open Live Demo
            </Link>
            <a href="#features"
              className="px-8 py-3.5 rounded-xl border border-[#2a3548] hover:border-emerald-500/50 text-slate-300 hover:text-white font-medium transition-all">
              Explore Features
            </a>
          </div>

          {/* Hero stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20 max-w-4xl mx-auto">
            {STATS.map((s) => (
              <div key={s.label} className="glass-card p-5">
                <div className="text-2xl md:text-3xl font-bold gradient-text">{s.value}</div>
                <div className="text-xs text-slate-500 mt-1">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Everything You Need in One Platform</h2>
            <p className="text-slate-400 max-w-xl mx-auto">From real-time telemetry to autonomous market bidding — built for utilities, enterprises, and grid operators.</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f) => (
              <div key={f.title} className="glass-card p-6 hover:border-emerald-500/30 transition-all group">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center mb-4 group-hover:bg-emerald-500/20 transition-colors">
                  <f.icon className="w-5 h-5 text-emerald-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-20 px-6 bg-[#111827]/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">How GridMind Works</h2>
            <p className="text-slate-400">From data ingestion to autonomous action in four steps.</p>
          </div>
          <div className="grid md:grid-cols-4 gap-8">
            {STEPS.map((s) => (
              <div key={s.step} className="relative">
                <div className="text-4xl font-bold text-emerald-500/20 mb-3">{s.step}</div>
                <h3 className="text-lg font-semibold mb-2">{s.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Impact */}
      <section id="impact" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="glass-card p-10 md:p-16 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-cyan-500/5" />
            <div className="relative">
              <BarChart3 className="w-12 h-12 text-emerald-400 mx-auto mb-6" />
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Proven Results Across 6 Sites</h2>
              <p className="text-slate-400 max-w-2xl mx-auto mb-10">
                Managing 6.8 MW of load across campuses, data centers, hospitals, and microgrids —
                with $67,400 in savings and 184 tons of CO₂ avoided in the last 30 days.
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto mb-10">
                {[
                  { icon: TrendingDown, val: "$67.4K", label: "Monthly Savings" },
                  { icon: Leaf, val: "38.2%", label: "Renewable Mix" },
                  { icon: Zap, val: "6.8 MW", label: "Managed Load" },
                  { icon: CheckCircle2, val: "94.2%", label: "Automation Rate" },
                ].map((item) => (
                  <div key={item.label}>
                    <item.icon className="w-5 h-5 text-emerald-400 mx-auto mb-2" />
                    <div className="text-2xl font-bold">{item.val}</div>
                    <div className="text-xs text-slate-500">{item.label}</div>
                  </div>
                ))}
              </div>
              <Link href="/dashboard"
                className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-semibold transition-all">
                See It Live <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#2a3548] py-10 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-emerald-400" />
            <span className="font-semibold">GridMind OS</span>
            <span className="text-slate-500 text-sm ml-2">© 2026</span>
          </div>
          <p className="text-sm text-slate-500">Autonomous Grid Intelligence for a Sustainable Future</p>
        </div>
      </footer>
    </div>
  );
}
