import React, { useEffect, useMemo, useState } from "react";
import api from "../services/api";
import AnalysisView from "../components/AnalysisView.jsx";
import { Badge, Card, EmptyState, ErrorBanner, RiskBadge, SectionTitle, Spinner } from "../components/ui";

export default function ComplaintHistory() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);
  const [riskFilter, setRiskFilter] = useState("all");
  const [reviewOnly, setReviewOnly] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setRecords(await api.history());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(
    () =>
      records.filter((record) => {
        if (riskFilter !== "all" && record.result.risk_level !== riskFilter) return false;
        if (reviewOnly && !record.result.human_review_required) return false;
        return true;
      }),
    [records, riskFilter, reviewOnly]
  );

  async function openRecord(id) {
    try {
      setSelected(await api.getRecord(id));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-navy-900">Complaint History</h1>
          <p className="text-sm text-slate-500">
            Every analysis is stored with its inputs, output, evidence and evaluation.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select className="input !w-auto" value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
            <option value="all">All risk levels</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input type="checkbox" className="h-4 w-4 rounded border-slate-300 text-brand-600" checked={reviewOnly} onChange={(e) => setReviewOnly(e.target.checked)} />
            Review only
          </label>
        </div>
      </div>

      <ErrorBanner message={error} onClose={() => setError("")} />

      <Card className="card-pad">
        <SectionTitle right={<span className="text-xs text-slate-400">{filtered.length} records</span>}>
          Stored analyses
        </SectionTitle>
        {loading ? (
          <Spinner label="Loading history…" />
        ) : filtered.length === 0 ? (
          <EmptyState title="No matching records" hint="Analyse a complaint to build up history." />
        ) : (
          <div className="overflow-x-auto">
            <table className="table-base">
              <thead>
                <tr>
                  <th>Summary</th>
                  <th>Category</th>
                  <th>Risk</th>
                  <th>Version</th>
                  <th>Review</th>
                  <th>Date</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {filtered.map((record) => (
                  <tr key={record.id}>
                    <td className="max-w-xs truncate">
                      {record.result.complaint_summary || record.input.complaint}
                    </td>
                    <td><Badge tone="purple">{record.result.category}</Badge></td>
                    <td><RiskBadge level={record.result.risk_level} /></td>
                    <td className="uppercase">{record.prompt_version}</td>
                    <td>
                      <Badge tone={record.result.human_review_required ? "amber" : "green"}>
                        {record.result.human_review_required ? "Required" : "Not required"}
                      </Badge>
                    </td>
                    <td className="whitespace-nowrap text-xs text-slate-500">
                      {new Date(record.created_at).toLocaleString()}
                    </td>
                    <td>
                      <button className="btn-ghost !px-3 !py-1.5" onClick={() => openRecord(record.id)}>
                        Open
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {selected && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <SectionTitle>Record {selected.id}</SectionTitle>
            <button className="btn-ghost !px-3 !py-1.5" onClick={() => setSelected(null)}>
              Close
            </button>
          </div>
          <AnalysisView
            record={selected}
            onReview={async (payload) => {
              const updated = await api.reviewRecord(selected.id, payload);
              setSelected(updated);
              await load();
            }}
          />
        </div>
      )}
    </div>
  );
}
