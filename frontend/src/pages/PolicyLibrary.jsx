import React, { useEffect, useState } from "react";
import api from "../services/api";
import {
  Badge,
  Card,
  EmptyState,
  ErrorBanner,
  SectionTitle,
  Spinner,
} from "../components/ui";

function PolicyCard({ policy, onDelete }) {
  const [detail, setDetail] = useState(null);
  const [open, setOpen] = useState(false);

  async function toggle() {
    if (!open && !detail) {
      setDetail(await api.getPolicy(policy.id));
    }
    setOpen((value) => !value);
  }

  return (
    <Card className="card-pad">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-semibold text-navy-900">{policy.name}</p>
          <p className="text-xs text-slate-400 mt-0.5">
            {new Date(policy.uploaded_at).toLocaleString()} · {policy.characters} characters ·{" "}
            {policy.clauses} clauses
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone={policy.source_type === "pdf" ? "purple" : "blue"}>
            {policy.source_type.toUpperCase()}
          </Badge>
          <button className="btn-ghost !px-3 !py-1.5" onClick={toggle}>
            {open ? "Hide clauses" : "View clauses"}
          </button>
          <button className="btn-danger !px-3 !py-1.5" onClick={() => onDelete(policy.id)}>
            Delete
          </button>
        </div>
      </div>

      {open && (
        <div className="mt-4 space-y-2">
          {!detail ? (
            <Spinner label="Loading clauses…" />
          ) : (
            detail.extracted_clauses.map((clause) => (
              <div key={clause.clause_id} className="rounded-xl bg-slate-50 border border-slate-200 p-3">
                <p className="text-xs font-semibold text-brand-700">
                  [{clause.clause_id}] {clause.heading}
                </p>
                <p className="text-sm text-slate-600 mt-1 whitespace-pre-wrap">{clause.text}</p>
              </div>
            ))
          )}
        </div>
      )}
    </Card>
  );
}

export default function PolicyLibrary() {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [name, setName] = useState("");
  const [text, setText] = useState("");
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setPolicies(await api.listPolicies());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setError("");
    setSuccess("");
    setSaving(true);
    try {
      const policy = await api.uploadPolicy(file);
      setSuccess(`Uploaded "${policy.name}" with ${policy.clauses} clauses.`);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
      event.target.value = "";
    }
  }

  async function handlePaste(event) {
    event.preventDefault();
    if (text.trim().length < 20 || name.trim().length < 2) {
      setError("Enter a policy name and at least a couple of sentences of policy text.");
      return;
    }
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const policy = await api.addTextPolicy({ name: name.trim(), text: text.trim() });
      setSuccess(`Saved "${policy.name}" with ${policy.clauses} clauses.`);
      setName("");
      setText("");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id) {
    setError("");
    setSuccess("");
    try {
      await api.deletePolicy(id);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-navy-900">Policy Library</h1>
        <p className="text-sm text-slate-500">
          Upload PDF policies (text extracted with PyMuPDF) or paste policy text. Fictional sample
          policies are used for the demo.
        </p>
      </div>

      <ErrorBanner message={error} onClose={() => setError("")} />
      {success && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="card-pad">
          <SectionTitle>Upload a PDF policy</SectionTitle>
          <label className="flex flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 py-8 cursor-pointer hover:border-brand-500">
            <span className="text-sm font-semibold text-brand-700">Choose a PDF file</span>
            <span className="text-xs text-slate-500">Text is extracted automatically</span>
            <input type="file" accept="application/pdf,.pdf" className="hidden" onChange={handleUpload} disabled={saving} />
          </label>
        </Card>

        <Card className="card-pad">
          <SectionTitle>Paste policy text</SectionTitle>
          <form className="space-y-3" onSubmit={handlePaste}>
            <div>
              <label className="label">Policy name</label>
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. E-commerce Refund & Returns Policy" />
            </div>
            <div>
              <label className="label">Policy text</label>
              <textarea className="input h-32 resize-y" value={text} onChange={(e) => setText(e.target.value)} placeholder="1. REFUND POLICY&#10;Customers may request a refund within 7 days…" />
            </div>
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? "Saving…" : "Save policy"}
            </button>
          </form>
        </Card>
      </div>

      <div>
        <SectionTitle>Stored policies</SectionTitle>
        {loading ? (
          <Spinner label="Loading policies…" />
        ) : policies.length === 0 ? (
          <Card>
            <EmptyState title="No policies yet" hint="Upload a PDF or paste text above to get started." />
          </Card>
        ) : (
          <div className="space-y-4">
            {policies.map((policy) => (
              <PolicyCard key={policy.id} policy={policy} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
