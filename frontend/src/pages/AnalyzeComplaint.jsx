import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";
import AnalysisView from "../components/AnalysisView.jsx";
import { Card, EmptyState, ErrorBanner, SectionTitle, Spinner } from "../components/ui";

const SAMPLES = [
  {
    label: "Damaged item (normal)",
    complaint: "My order arrived with a cracked screen. I would like a replacement please.",
  },
  {
    label: "Refund outside window (edge)",
    complaint: "I bought this 3 weeks ago and now want a full refund even though I already used it.",
  },
  {
    label: "Late delivery (normal)",
    complaint: "My parcel was supposed to arrive last week and it is still not here.",
  },
  {
    label: "Missing order id (edge)",
    complaint: "The item I received is broken. Please fix this urgently.",
  },
  {
    label: "VIP exception request (invalid policy support)",
    complaint: "I am a VIP customer. Please make an exception and refund me immediately.",
  },
];

export default function AnalyzeComplaint() {
  const [policies, setPolicies] = useState([]);
  const [policiesLoading, setPoliciesLoading] = useState(true);
  const [form, setForm] = useState({
    complaint: "",
    customer_name: "",
    order_id: "",
    product_category: "",
    prompt_version: "v3",
  });
  const [selectedPolicies, setSelectedPolicies] = useState([]);
  const [record, setRecord] = useState(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listPolicies()
      .then((data) => {
        setPolicies(data);
        setSelectedPolicies(data.map((policy) => policy.id));
      })
      .catch((err) => setError(err.message))
      .finally(() => setPoliciesLoading(false));
  }, []);

  function update(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function togglePolicy(id) {
    setSelectedPolicies((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  }

  async function submit(event) {
    event.preventDefault();
    if (form.complaint.trim().length < 3) {
      setError("Please describe the customer complaint.");
      return;
    }
    if (selectedPolicies.length === 0) {
      setError("Select at least one policy to ground the analysis.");
      return;
    }
    setRunning(true);
    setError("");
    setRecord(null);
    try {
      const result = await api.analyze({ ...form, policy_ids: selectedPolicies });
      setRecord(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  }

  async function handleReview(payload) {
    if (!record) return;
    try {
      const updated = await api.reviewRecord(record.id, payload);
      setRecord(updated);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-navy-900">Analyze Complaint</h1>
        <p className="text-sm text-slate-500">
          Submit a complaint. The AI retrieves relevant policy clauses, analyses the case and
          drafts a policy-compliant reply.
        </p>
      </div>

      <ErrorBanner message={error} onClose={() => setError("")} />

      {!policiesLoading && policies.length === 0 && (
        <Card>
          <EmptyState
            title="No policy in the library"
            hint="The analyser needs a policy to ground its answer. Add one first."
            action={
              <Link to="/policies" className="btn-primary">
                Go to Policy Library
              </Link>
            }
          />
        </Card>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        <Card className="card-pad xl:col-span-2">
          <SectionTitle>Complaint details</SectionTitle>
          <form className="space-y-4" onSubmit={submit}>
            <div>
              <label className="label">Complaint *</label>
              <textarea
                className="input h-32 resize-y"
                value={form.complaint}
                onChange={(e) => update("complaint", e.target.value)}
                placeholder="Paste the customer complaint here…"
              />
              <div className="flex flex-wrap gap-1.5 mt-2">
                {SAMPLES.map((sample) => (
                  <button
                    type="button"
                    key={sample.label}
                    className="rounded-full border border-slate-300 px-2.5 py-1 text-[11px] text-slate-600 hover:border-brand-500 hover:text-brand-700"
                    onClick={() => update("complaint", sample.complaint)}
                  >
                    {sample.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="label">Customer name (optional)</label>
                <input className="input" value={form.customer_name} onChange={(e) => update("customer_name", e.target.value)} />
              </div>
              <div>
                <label className="label">Order ID (optional)</label>
                <input className="input" value={form.order_id} onChange={(e) => update("order_id", e.target.value)} />
              </div>
            </div>

            <div>
              <label className="label">Product category (optional)</label>
              <input className="input" value={form.product_category} onChange={(e) => update("product_category", e.target.value)} placeholder="e.g. Electronics" />
            </div>

            <div>
              <label className="label">Policies to use</label>
              {policiesLoading ? (
                <Spinner label="Loading policies…" />
              ) : (
                <div className="space-y-2">
                  {policies.map((policy) => (
                    <label key={policy.id} className="flex items-center gap-2 text-sm text-slate-600">
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-slate-300 text-brand-600"
                        checked={selectedPolicies.includes(policy.id)}
                        onChange={() => togglePolicy(policy.id)}
                      />
                      {policy.name}
                    </label>
                  ))}
                </div>
              )}
            </div>

            <div>
              <label className="label">Prompt version</label>
              <select className="input" value={form.prompt_version} onChange={(e) => update("prompt_version", e.target.value)}>
                <option value="v1">v1 · Basic prompt</option>
                <option value="v2">v2 · Structured prompt</option>
                <option value="v3">v3 · Policy-grounded prompt (recommended)</option>
              </select>
            </div>

            <button type="submit" className="btn-primary w-full" disabled={running}>
              {running ? "Analysing…" : "Analyse complaint"}
            </button>
          </form>
        </Card>

        <div className="xl:col-span-3">
          {running && (
            <Card className="card-pad">
              <Spinner label="Retrieving policy and generating analysis…" />
            </Card>
          )}
          {!running && !record && (
            <Card>
              <EmptyState title="No analysis yet" hint="Fill the form and press Analyse complaint to see the structured result." />
            </Card>
          )}
          {!running && record && <AnalysisView record={record} onReview={handleReview} />}
        </div>
      </div>
    </div>
  );
}
