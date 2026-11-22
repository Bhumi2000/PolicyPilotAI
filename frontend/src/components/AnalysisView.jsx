import React, { useState } from "react";
import { Badge, Card, RiskBadge, ScoreBar, SectionTitle, UrgencyBadge } from "./ui";

function Field({ label, children }) {
  return (
    <div className="rounded-xl border border-slate-200 p-3 bg-slate-50/60">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <div className="mt-1 text-sm text-slate-700">{children || <span className="text-slate-400">—</span>}</div>
    </div>
  );
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      className="btn-ghost !px-3 !py-1.5"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        } catch {
          setCopied(false);
        }
      }}
    >
      {copied ? "Copied" : "Copy reply"}
    </button>
  );
}

export default function AnalysisView({ record, onReview = null, showEvidence = true }) {
  const [editedReply, setEditedReply] = useState(record.edited_reply || record.result.generated_reply);
  const [editing, setEditing] = useState(false);
  const { result, evaluation } = record;

  return (
    <div className="space-y-5">
      <Card className="card-pad">
        <div className="flex flex-wrap items-center gap-2 justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="blue">Prompt {record.prompt_version}</Badge>
            <Badge tone={record.mode === "live" ? "green" : "amber"}>
              {record.mode === "live" ? `Live · ${record.model}` : "Demo output"}
            </Badge>
            <RiskBadge level={result.risk_level} />
            <UrgencyBadge level={result.urgency} />
          </div>
          <div className="text-xs text-slate-400">
            {new Date(record.created_at).toLocaleString()} · {record.latency_ms} ms
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
          <Field label="Complaint summary">{result.complaint_summary}</Field>
          <Field label="Category">
            <Badge tone="purple">{result.category}</Badge>
          </Field>
          <Field label="Customer intent">{result.customer_intent}</Field>
          <Field label="Sentiment">{result.sentiment}</Field>
          <Field label="Suggested resolution">{result.suggested_resolution}</Field>
          <Field label="Missing information">
            {result.missing_information.length ? (
              <ul className="list-disc pl-5 space-y-0.5">
                {result.missing_information.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : (
              "None identified"
            )}
          </Field>
        </div>
      </Card>

      <Card
        className={`card-pad border-l-4 ${
          result.human_review_required ? "border-l-amber-500" : "border-l-emerald-500"
        }`}
      >
        <SectionTitle>Human-in-the-loop review</SectionTitle>
        <p className="text-sm">
          <span className="font-semibold">Human review required: </span>
          <Badge tone={result.human_review_required ? "amber" : "green"}>
            {result.human_review_required ? "Yes" : "No"}
          </Badge>
        </p>
        {result.human_review_reason && (
          <p className="mt-2 text-sm text-slate-600">
            <span className="font-semibold">Reason: </span>
            {result.human_review_reason}
          </p>
        )}
        <p className="mt-2 text-sm text-slate-600">
          <span className="font-semibold">Suggested next action: </span>
          {result.human_review_required
            ? "A support representative should verify the policy and customer details before any commitment."
            : "The policy supports sending the generated reply directly."}
        </p>
      </Card>

      <Card className="card-pad">
        <SectionTitle right={<CopyButton text={editing ? editedReply : result.generated_reply} />}>
          Generated customer reply
        </SectionTitle>
        {editing ? (
          <>
            <textarea
              className="input h-40 resize-y"
              value={editedReply}
              onChange={(e) => setEditedReply(e.target.value)}
            />
            <div className="flex gap-2 mt-2">
              <button
                className="btn-primary !py-2"
                onClick={() => {
                  setEditing(false);
                  onReview?.({ review_status: "edited", edited_reply: editedReply });
                }}
              >
                Save edit
              </button>
              <button className="btn-ghost !py-2" onClick={() => setEditing(false)}>
                Cancel
              </button>
            </div>
          </>
        ) : (
          <>
            <pre className="whitespace-pre-wrap text-sm text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-4">
              {record.edited_reply || result.generated_reply}
            </pre>
            {onReview && (
              <div className="flex flex-wrap gap-2 mt-3">
                <button
                  className="btn-primary !py-2"
                  onClick={() => onReview({ review_status: "approved" })}
                >
                  Approve response
                </button>
                <button className="btn-ghost !py-2" onClick={() => setEditing(true)}>
                  Edit before sending
                </button>
                {record.review_status !== "pending" && (
                  <Badge tone="green">Status: {record.review_status}</Badge>
                )}
              </div>
            )}
          </>
        )}
      </Card>

      {showEvidence && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <Card className="card-pad">
            <SectionTitle>Retrieved policy clauses (keyword retriever)</SectionTitle>
            {record.retrieved_clauses.length === 0 ? (
              <p className="text-sm text-slate-500">
                No clause matched. The system escalates instead of inventing a rule.
              </p>
            ) : (
              <div className="space-y-2">
                {record.retrieved_clauses.map((clause) => (
                  <div key={clause.clause_id} className="rounded-xl bg-slate-50 border border-slate-200 p-3">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-semibold text-brand-700">
                        [{clause.clause_id}] {clause.heading}
                      </p>
                      <span className="text-xs text-slate-400">score {clause.score}</span>
                    </div>
                    <p className="text-sm text-slate-600 mt-1 whitespace-pre-wrap">{clause.text}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card className="card-pad">
            <SectionTitle>Evaluation ({evaluation.total}/25)</SectionTitle>
            <div className="space-y-3">
              <div>
                <p className="text-xs text-slate-500 mb-1">Policy adherence</p>
                <ScoreBar value={evaluation.policy_adherence} />
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Completeness</p>
                <ScoreBar value={evaluation.completeness} />
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Tone and empathy</p>
                <ScoreBar value={evaluation.tone_empathy} />
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Unsupported claims (higher = fewer)</p>
                <ScoreBar value={evaluation.unsupported_claims} />
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Escalation appropriateness</p>
                <ScoreBar value={evaluation.escalation_appropriateness} />
              </div>
              {evaluation.flags.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-semibold text-slate-500">Flags</p>
                  <ul className="list-disc pl-5 text-xs text-slate-500 mt-1 space-y-0.5">
                    {evaluation.flags.map((flag) => (
                      <li key={flag}>{flag}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
