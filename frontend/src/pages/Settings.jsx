import React from "react";
import { useHealth } from "../context/HealthContext";
import { Badge, Card, SectionTitle } from "../components/ui";

export default function Settings() {
  const { health, loading, error } = useHealth();

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-navy-900">Settings / About</h1>
        <p className="text-sm text-slate-500">
          PolicyPilot AI — Intelligent, policy-grounded customer support & resolution assistant.
        </p>
      </div>

      <Card className="card-pad">
        <SectionTitle>Backend status</SectionTitle>
        {loading ? (
          <p className="text-sm text-slate-500">Checking…</p>
        ) : error ? (
          <p className="text-sm text-red-600">Backend unreachable: {error}</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-xs text-slate-500">AI mode</p>
              <Badge tone={health.ai_mode === "live" ? "green" : health.ai_mode === "demo" ? "amber" : "red"}>
                {health.ai_mode}
              </Badge>
            </div>
            <div>
              <p className="text-xs text-slate-500">Model</p>
              <p className="text-slate-700">{health.model}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Demo mode</p>
              <p className="text-slate-700">{String(health.demo_enabled)}</p>
            </div>
          </div>
        )}
      </Card>

      <Card className="card-pad">
        <SectionTitle>What this system does</SectionTitle>
        <ul className="list-disc pl-5 text-sm text-slate-600 space-y-1.5">
          <li>Extracts policy text from PDFs with PyMuPDF and splits it into clauses.</li>
          <li>Retrieves the most relevant clauses with a transparent keyword retriever.</li>
          <li>Analyses each complaint into summary, category, intent, sentiment, urgency and risk.</li>
          <li>Drafts a policy-grounded reply and blocks unsupported promises.</li>
          <li>Escalates unclear, high-risk or exception cases to a human reviewer.</li>
          <li>Compares three prompt versions (v1, v2, v3) on the same input.</li>
        </ul>
      </Card>

      <Card className="card-pad">
        <SectionTitle>How to run locally</SectionTitle>
        <ol className="list-decimal pl-5 text-sm text-slate-600 space-y-1.5">
          <li>Backend: <code>cd backend</code>, then <code>pip install -r requirements.txt</code>.</li>
          <li>Copy <code>.env.example</code> to <code>.env</code> and add your <code>GEMINI_API_KEY</code>.</li>
          <li>Run <code>uvicorn app.main:app --reload</code> (serves on port 8000).</li>
          <li>Frontend: <code>cd frontend</code>, then <code>npm install</code> and <code>npm run dev</code>.</li>
          <li>Open <code>http://localhost:5173</code>.</li>
        </ol>
      </Card>

      <Card className="card-pad">
        <SectionTitle>Important notes</SectionTitle>
        <p className="text-sm text-slate-600">
          All sample policies and customer details are fictional and used for demonstration only.
          PolicyPilot AI never completes external actions (emails, refunds, tickets); it only drafts
          responses for a human to review. The Gemini API key is held only in the backend
          environment and is never exposed to the browser.
        </p>
      </Card>
    </div>
  );
}
