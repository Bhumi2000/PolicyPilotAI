# Prompts

This folder follows the structure requested in the SCSE4041 Milestone 2 guidelines.

```
prompts/
  v1/       earlier saved prompt versions (one file per version)
  v2/
  v3/
  final/    the final prompt used by the shipped solution
```

| Folder | Version | What it is |
| --- | --- | --- |
| `v1/basic_reply.txt` | v1 | Baseline free-text reply prompt (no system prompt, no schema). |
| `v2/structured_analysis.txt` | v2 | Adds a role system prompt and a fixed 9-key JSON schema. |
| `v3/policy_grounded_resolution.txt` | v3 | Adds retrieved-clause grounding, guardrails and escalation. |
| `final/P3_policy_grounded_resolution.txt` | final | The production prompt = v3. |

**Counting for the form:** the shipped solution uses **1 final prompt** (P3, shown in
`final/`). The iteration log records **3 saved versions** (v1, v2, v3). The Prompt
Engineering Lab in the app can re-run all three versions on the same complaint so the
before/after can be demonstrated live.

The prompt text here is generated from `backend/app/prompts/versions.py`, which is the
single source of truth shared by the API, the UI and the Milestone 2 PDF.
