import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import api from "../services/api";
import {
  Badge,
  Card,
  EmptyState,
  ErrorBanner,
  RiskBadge,
  SectionTitle,
  Spinner,
  Stat,
} from "../components/ui";

const RISK_COLORS = { low: "#10b981", medium: "#f59e0b", high: "#ef4444", unknown: "#94a3b8" };

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    setLoading(true);
    api
      .dashboardStats()
      .then((data) => alive && setStats(data))
      .catch((err) => alive && setError(err.message))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, []);

  if (loading) return <Spinner label="Loading dashboard…" />;
  if (error) return <ErrorBanner message={error} />;
  if (!stats) return null;

  const categoryData = Object.entries(stats.by_category).map(([name, value]) => ({ name, value }));
  const riskData = Object.entries(stats.by_risk).map(([name, value]) => ({
    name,
    value,
    color: RISK_COLORS[name] || RISK_COLORS.unknown,
  }));
  const promptVersions = Object.entries(stats.prompt_evaluation);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-navy-900">Support Operations Dashboard</h1>
          <p className="text-sm text-slate-500">
            All figures are computed from stored records. No hard-coded statistics.
          </p>
        </div>
        <Link to="/analyze" className="btn-primary">
          Analyse a new complaint
        </Link>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <Stat label="Complaints analysed" value={stats.total_complaints} tone="blue" />
        <Stat
          label="Requiring human review"
          value={stats.human_review_required}
          tone="amber"
          hint="Flagged by the model or the safety rules"
        />
        <Stat label="High-risk complaints" value={stats.high_risk} tone="red" />
        <Stat
          label="Policies in library"
          value={stats.total_policies}
          tone="green"
          hint={`${stats.approved} responses reviewed`}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card className="card-pad xl:col-span-2">
          <SectionTitle>Complaints by category</SectionTitle>
          {categoryData.length === 0 ? (
            <EmptyState
              title="No complaints analysed yet"
              hint="Analyse a complaint to populate this chart."
            />
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#2563eb" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>

        <Card className="card-pad">
          <SectionTitle>Risk distribution</SectionTitle>
          {riskData.length === 0 ? (
            <EmptyState title="No data yet" />
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={riskData} dataKey="value" nameKey="name" outerRadius={90} label>
                    {riskData.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Card className="card-pad">
          <SectionTitle>Prompt evaluation overview</SectionTitle>
          {promptVersions.length === 0 ? (
            <EmptyState
              title="No runs yet"
              hint="Use the Prompt Engineering Lab to compare v1, v2 and v3."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="table-base">
                <thead>
                  <tr>
                    <th>Version</th>
                    <th>Runs</th>
                    <th>Avg total /25</th>
                    <th>Policy</th>
                    <th>Completeness</th>
                    <th>Tone</th>
                    <th>Escalation</th>
                  </tr>
                </thead>
                <tbody>
                  {promptVersions.map(([version, data]) => (
                    <tr key={version}>
                      <td className="font-semibold uppercase">{version}</td>
                      <td>{data.runs}</td>
                      <td className="font-semibold text-brand-700">{data.avg_total ?? "—"}</td>
                      <td>{data.avg_policy_adherence ?? "—"}</td>
                      <td>{data.avg_completeness ?? "—"}</td>
                      <td>{data.avg_tone_empathy ?? "—"}</td>
                      <td>{data.avg_escalation_appropriateness ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card className="card-pad">
          <SectionTitle
            right={
              <Link to="/history" className="text-xs font-semibold text-brand-600">
                View all
              </Link>
            }
          >
            Recent activity
          </SectionTitle>
          {stats.recent_activity.length === 0 ? (
            <EmptyState title="Nothing here yet" hint="Recent analyses will appear here." />
          ) : (
            <ul className="divide-y divide-slate-100">
              {stats.recent_activity.map((item) => (
                <li key={item.id} className="py-3 flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-700 truncate">
                      {item.summary || "(no summary)"}
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {new Date(item.created_at).toLocaleString()} · {item.prompt_version}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge tone="blue">{item.category}</Badge>
                    <RiskBadge level={item.risk_level} />
                    {item.human_review_required && <Badge tone="amber">Review</Badge>}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
