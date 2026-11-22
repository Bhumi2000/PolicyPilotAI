import React, { useEffect, useState } from "react";
import api from "../services/api";
import AnalysisView from "../components/AnalysisView.jsx";
import { Badge, Card, EmptyState, ErrorBanner, SectionTitle, Spinner } from "../components/ui";

function promptToText(prompt) {
  const variableLines = Object.entries(prompt.variables)
    .map(([key, value]) => `  - {${key}}: ${value}`)
    .join("\n");
  return [
    `Prompt ID and name: ${prompt.id} - ${prompt.name}`,
    `Step in the workflow: ${prompt.step}`,
    `Purpose: ${prompt.purpose}`,
    `Tool and model: ${prompt.tool_model}`,
    `Settings: ${prompt.settings}`,
    `System prompt: ${prompt.system_prompt}`,
    "User prompt template:",
    prompt.user_prompt_template,
    "Variables:",
    variableLines,
    `Examples included: ${prompt.examples_included}`,
    `Output format: ${prompt.output_format}`,
  ].join("\n");
}

function PromptSheet({ prompt }) {
  const [copied, setCopied] = useState(false);
  return (
    <Card className="card-pad">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Badge tone="blue">Prompt {prompt.id.toUpperCase()}</Badge>
          <p className="font-semibold text-navy-900">{prompt.name}</p>
        </div>
        <button
          className="btn-ghost !px-3 !py-1.5"
          onClick={async () => {
            await navigator.clipboard.writeText(promptToText(prompt));
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
          }}
        >
          {copied ? "Copied" : "Copy sheet"}
        </button>
      </div>

      <dl className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
        <div><dt className="text-xs text-slate-500">Step</dt><dd className="text-slate-700">{prompt.step}</dd></div>
        <div><dt className="text-xs text-slate-500">Settings</dt><dd className="text-slate-700">{prompt.settings}</dd></div>
        <div><dt className="text-xs text-slate-500">Examples included</dt><dd className="text-slate-700">{prompt.examples_included}</dd></div>
        <div><dt className="text-xs text-slate-500">Output format</dt><dd className="text-slate-700">{prompt.output_format}</dd></div>
      </dl>

      <p className="mt-3 text-xs font-semibold text-slate-500">Purpose</p>
      <p className="text-sm text-slate-700">{prompt.purpose}</p>

      <p className="mt-3 text-xs font-semibold text-slate-500">System prompt</p>
      <pre className="mt-1 whitespace-pre-wrap text-xs text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-3">{prompt.system_prompt}</pre>

      <p className="mt-3 text-xs font-semibold text-slate-500">User prompt template</p>
      <pre className="mt-1 whitespace-pre-wrap text-xs text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-3">{prompt.user_prompt_template}</pre>

      <p className="mt-3 text-xs font-semibold text-slate-500">Variables</p>
      <ul className="mt-1 text-xs text-slate-600 space-y-0.5">
        {Object.entries(prompt.variables).map(([key, value]) => (
          <li key={key}><code className="text-brand-700">{`{${key}}`}</code> — {value}</li>
        ))}
      </ul>
    </Card>
  );
}

export default function PromptLab() {
  const [prompts, setPrompts] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [complaint, setComplaint] = useState(
    "My order arrived with a cracked screen and I want a refund immediately."
  );
  const [policyId, setPolicyId] = useState("");
  const [result, setResult] = useState(null);
  const [active, setActive] = useState("v3");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getPrompts().then(setPrompts).catch((err) => setError(err.message));
    api
      .listPolicies()
      .then((data) => {
        setPolicies(data);
        if (data.length) setPolicyId(data[0].id);
      })
      .catch((err) => setError(err.message));
  }, []);

  async function runComparison(event) {
    event.preventDefault();
    if (!policyId) {
      setError("Add a policy first in the Policy Library.");
      return;
    }
    setRunning(true);
    setError("");
    setResult(null);
    try {
      const data = await api.compare({ complaint, policy_ids: [policyId] });
      setResult(data);
      setActive("v3");
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-navy-900">Prompt Engineering Lab</h1>
        <p className="text-sm text-slate-500">
          The core feature: three prompt versions, compared on the same complaint and policy.
        </p>
      </div>

      <ErrorBanner message={error} onClose={() => setError("")} />

      <Card className="card-pad">
        <SectionTitle>Run the same complaint through all three versions</SectionTitle>
        <form className="space-y-3" onSubmit={runComparison}>
          <textarea
            className="input h-24 resize-y"
            value={complaint}
            onChange={(e) => setComplaint(e.target.value)}
          />
          <div className="flex flex-wrap items-end gap-3">
            <div className="min-w-[240px]">
              <label className="label">Policy</label>
              <select className="input" value={policyId} onChange={(e) => setPolicyId(e.target.value)}>
                {policies.length === 0 && <option value="">No policies available</option>}
                {policies.map((policy) => (
                  <option key={policy.id} value={policy.id}>{policy.name}</option>
                ))}
              </select>
            </div>
            <button className="btn-primary" disabled={running || !policyId}>
              {running ? "Running v1, v2, v3…" : "Compare all versions"}
            </button>
          </div>
        </form>
      </Card>

      {running && <Card className="card-pad"><Spinner label="Generating and scoring outputs…" /></Card>}

      {result && (
        <>
          <Card className="card-pad">
            <SectionTitle>Comparison (computed from actual outputs)</SectionTitle>
            <div className="overflow-x-auto">
              <table className="table-base">
                <thead>
                  <tr>
                    <th>Criterion</th>
                    <th>v1 · Basic</th>
                    <th>v2 · Structured</th>
                    <th>v3 · Policy-grounded</th>
                  </tr>
                </thead>
                <tbody>
                  {result.comparison.map((row) => (
                    <tr key={row.criterion}>
                      <td className="font-medium">{row.criterion}</td>
                      <td>{row.v1}</td>
                      <td>{row.v2}</td>
                      <td>{row.v3}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card className="card-pad">
            <div className="flex flex-wrap items-center gap-2 mb-3">
              {["v1", "v2", "v3"].map((version) => (
                <button
                  key={version}
                  onClick={() => setActive(version)}
                  className={
                    active === version
                      ? "btn-primary !py-2"
                      : "btn-ghost !py-2"
                  }
                >
                  {version.toUpperCase()}
                </button>
              ))}
              <span className="text-xs text-slate-400 ml-1">
                Showing the {active.toUpperCase()} record for this run
              </span>
            </div>
            <AnalysisView record={result[active]} />
          </Card>
        </>
      )}

      <div>
        <SectionTitle>Final prompt sheets</SectionTitle>
        {prompts.length === 0 ? (
          <Card><EmptyState title="Prompt sheets unavailable" hint="Start the backend to load prompt definitions." /></Card>
        ) : (
          <div className="space-y-5">
            {prompts.map((prompt) => (
              <PromptSheet key={prompt.id} prompt={prompt} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
