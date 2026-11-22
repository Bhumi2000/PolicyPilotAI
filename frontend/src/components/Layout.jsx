import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useHealth } from "../context/HealthContext";

const NAV = [
  { to: "/", label: "Dashboard", end: true, icon: "grid" },
  { to: "/analyze", label: "Analyze Complaint", icon: "spark" },
  { to: "/policies", label: "Policy Library", icon: "doc" },
  { to: "/prompt-lab", label: "Prompt Engineering Lab", icon: "lab" },
  { to: "/history", label: "Complaint History", icon: "clock" },
  { to: "/settings", label: "Settings / About", icon: "cog" },
];

function Icon({ name }) {
  const common = { fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" };
  const paths = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></>,
    spark: <path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" />,
    doc: <><path d="M7 3h7l4 4v14H7z" /><path d="M14 3v4h4" /><path d="M9.5 12h6M9.5 15.5h6" /></>,
    lab: <><path d="M9 3h6" /><path d="M10 3v6l-4.5 8A2 2 0 007.3 20h9.4a2 2 0 001.8-3L14 9V3" /><path d="M7.5 14h9" /></>,
    clock: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></>,
    cog: <><circle cx="12" cy="12" r="3" /><path d="M12 3v2.2M12 18.8V21M4.2 7.5l1.9 1.1M17.9 15.4l1.9 1.1M4.2 16.5l1.9-1.1M17.9 8.6l1.9-1.1" /></>,
  };
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" {...common}>
      {paths[name]}
    </svg>
  );
}

function ModePill({ health, loading, error }) {
  if (loading) return <span className="badge bg-slate-100 text-slate-500">Checking backend…</span>;
  if (error) return <span className="badge bg-red-50 text-red-700">Backend offline</span>;
  const mode = health?.ai_mode;
  if (mode === "live") return <span className="badge bg-emerald-50 text-emerald-700">Live · {health.model}</span>;
  if (mode === "demo") return <span className="badge bg-amber-50 text-amber-700">Demo mode (no key)</span>;
  return <span className="badge bg-red-50 text-red-700">AI not configured</span>;
}

export default function Layout() {
  const { health, loading, error } = useHealth();
  const unconfigured = !loading && !error && health?.ai_mode === "unconfigured";
  const demo = !loading && !error && health?.ai_mode === "demo";
  const offline = !loading && !!error;

  return (
    <div className="min-h-full flex bg-slate-100">
      <aside className="hidden lg:flex w-64 shrink-0 flex-col bg-navy-900 text-slate-200">
        <div className="px-5 py-6 flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-brand-600 flex items-center justify-center font-bold text-white">
            P
          </div>
          <div>
            <p className="font-bold text-white leading-tight">PolicyPilot AI</p>
            <p className="text-[11px] text-slate-400">Policy-grounded support</p>
          </div>
        </div>
        <nav className="px-3 space-y-1 flex-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-brand-600 text-white"
                    : "text-slate-300 hover:bg-navy-800 hover:text-white"
                }`
              }
            >
              <Icon name={item.icon} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 text-[11px] text-slate-500 border-t border-navy-800">
          Fictional sample policy data is used for demonstration.
        </div>
      </aside>

      <div className="flex-1 min-w-0 flex flex-col">
        <header className="sticky top-0 z-10 bg-white/90 backdrop-blur border-b border-slate-200">
          <div className="px-5 sm:px-8 h-16 flex items-center justify-between gap-4">
            <div className="lg:hidden font-bold text-navy-900">PolicyPilot AI</div>
            <div className="hidden lg:block" />
            <div className="flex items-center gap-3">
              <ModePill health={health} loading={loading} error={error} />
            </div>
          </div>
        </header>

        <main className="flex-1 px-5 sm:px-8 py-6 space-y-5">
          {offline && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              Cannot reach the backend at <code>/api</code>. Start it with{" "}
              <code>uvicorn app.main:app --reload</code> inside the <code>backend</code> folder.
            </div>
          )}
          {unconfigured && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <strong>AI backend not configured.</strong> Add <code>GEMINI_API_KEY</code> to{" "}
              <code>backend/.env</code>, or set <code>ENABLE_DEMO_MODE=true</code> to explore the
              interface with clearly-labelled demo output. Real analysis is disabled so that no
              fake result is shown.
            </div>
          )}
          {demo && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              <strong>Demo mode is on.</strong> Outputs are deterministic placeholders for offline
              UI testing and are tagged <code>mode: demo</code>. Add a Gemini API key for real
              results.
            </div>
          )}
          <Outlet />
        </main>

        <footer className="px-5 sm:px-8 py-4 text-xs text-slate-400 border-t border-slate-200">
          PolicyPilot AI · SCSE4041 Mini Project · sample policies are fictional.
        </footer>
      </div>
    </div>
  );
}
