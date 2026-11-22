import React from "react";

export function Card({ className = "", children }) {
  return <div className={`card ${className}`}>{children}</div>;
}

export function SectionTitle({ children, right = null }) {
  return (
    <div className="flex items-center justify-between mb-3">
      <h2 className="section-title">{children}</h2>
      {right}
    </div>
  );
}

const TONES = {
  neutral: "bg-slate-100 text-slate-700",
  blue: "bg-brand-50 text-brand-700",
  green: "bg-emerald-50 text-emerald-700",
  amber: "bg-amber-50 text-amber-700",
  red: "bg-red-50 text-red-700",
  purple: "bg-violet-50 text-violet-700",
};

export function Badge({ tone = "neutral", children }) {
  return <span className={`badge ${TONES[tone] || TONES.neutral}`}>{children}</span>;
}

export function RiskBadge({ level }) {
  const map = {
    low: ["green", "Low risk"],
    medium: ["amber", "Medium risk"],
    high: ["red", "High risk"],
    unknown: ["neutral", "Unknown risk"],
  };
  const [tone, text] = map[level] || map.unknown;
  return <Badge tone={tone}>{text}</Badge>;
}

export function UrgencyBadge({ level }) {
  const map = { low: "green", medium: "amber", high: "red", unknown: "neutral" };
  return <Badge tone={map[level] || "neutral"}>Urgency: {level || "unknown"}</Badge>;
}

export function Spinner({ label = "Working..." }) {
  return (
    <div className="flex items-center gap-3 text-slate-500 text-sm py-6">
      <span className="h-5 w-5 rounded-full border-2 border-slate-300 border-t-brand-600 animate-spin" />
      {label}
    </div>
  );
}

export function EmptyState({ title, hint, action = null }) {
  return (
    <div className="text-center py-12 px-6">
      <div className="mx-auto h-12 w-12 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400 text-xl">
        ∅
      </div>
      <p className="mt-3 font-semibold text-slate-700">{title}</p>
      {hint && <p className="mt-1 text-sm text-slate-500 max-w-md mx-auto">{hint}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorBanner({ message, onClose = null }) {
  if (!message) return null;
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 flex items-start justify-between gap-4">
      <span>{message}</span>
      {onClose && (
        <button className="text-red-500 hover:text-red-700" onClick={onClose}>
          Dismiss
        </button>
      )}
    </div>
  );
}

export function Stat({ label, value, hint, tone = "blue" }) {
  const ring = {
    blue: "text-brand-700",
    red: "text-red-600",
    amber: "text-amber-600",
    green: "text-emerald-600",
  };
  return (
    <Card className="card-pad">
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-1 text-3xl font-bold ${ring[tone] || ring.blue}`}>{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </Card>
  );
}

export function ScoreBar({ value, max = 5 }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  const color =
    pct >= 80 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-full rounded-full bg-slate-200 overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-semibold text-slate-600 whitespace-nowrap">
        {value}/{max}
      </span>
    </div>
  );
}
