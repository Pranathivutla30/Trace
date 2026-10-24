# How We Used Kiro to Build TRACE

TRACE (Temporal Reasoning & Analysis for Clinical Exploration) is a non-diagnostic
tool that finds *where a person's physiological pattern changed* in longitudinal
wearable data. It spans a Python analysis pipeline, a trained anomaly model, a
FastAPI backend, and a React dashboard. Kiro was the primary development
environment across all of it, and the structure of the repo reflects how we
worked.

## Which Kiro tools we used

We built TRACE almost entirely in the **Kiro IDE agent**. The agent did the
heavy lifting: reading our existing code before changing it, writing the seven
analysis modules and the adapter, running the FastAPI server and the frontend
build to verify each step, and iterating when something failed. Because TRACE is
a layered system (Python → JSON → FastAPI → React), the IDE's ability to run
commands, read command output, and self-correct in the same loop was what made
rapid, correct iteration possible — the agent would make a change, run
`npm run build` or hit the API endpoints, see the real result, and fix issues
before handing control back.

## Spec-driven development (our biggest lever)

We leaned on **spec-driven development** rather than pure "vibe coding," and it
was the single decision that kept a multi-layer project coherent. Our spec lives
in `.kiro/specs/trace-pipeline/`:

- **`requirements.md`** — user stories with explicit, testable acceptance
  criteria (e.g. "the generator SHALL produce 30 days of 9 signals with seed 42,"
  "anomaly scores SHALL NOT be labeled disease/stress probability").
- **`design.md`** — the one-directional architecture and the key decision that
  the backend computes nothing, so analysis values are immutable by the time they
  reach the UI.
- **`tasks.md`** — 19 discrete tasks, each linked back to a requirement, which
  became the actual build order.

How it improved the process: because each of the seven TRACE "features" was
specified before it was written, Kiro implemented them as a **chain**
(baseline → change detection → relationships → missing-information → self-check →
counterfactual → trajectories), where each stage consumed the previous stage's
output. The spec also encoded our hardest constraint — *onboarding/profile data
must never enter the AI/ML analysis* — so every later change was checked against
it. Compared to vibe coding, the spec gave us a stable contract: when we later
added onboarding, an ML model, and a backend adapter, Kiro could extend the
system without silently breaking the analysis, because the requirements said
exactly what must not change.

## Steering docs (the strategy that mattered most)

We wrote three always-on steering files in `.kiro/steering/` that shaped every
response:

- **`product.md`** — the non-negotiable product rules: TRACE is **exploratory and
  non-diagnostic**; never output disease/stress probability, diagnosis, or
  clinical risk; correlations are associations not causation; keep language
  understandable for non-experts (expand HRV, EDA, etc.).
- **`tech.md`** — the architecture, conventions (determinism via seed 42, the
  backend contract defined by the mock JSON), and verification commands.
- **`structure.md`** — the folder boundaries (changes to AI/ML stay in `ai_ml/`;
  the backend only reads JSON; the frontend only renders).

The highest-impact strategy was putting the **safety and data-separation rules in
steering**. Healthcare is exactly where an AI assistant tends to drift into
diagnostic language. Because those rules were steering (not just a one-off
prompt), Kiro consistently produced safe wording ("deviation from a learned
normal," "not a health risk") across dozens of components without us re-stating
it each time — and it refused to let profile data leak into the model even as the
UI grew.

## Agent hooks, MCP, Property-based testing, Powers — honest scope

To be transparent about what we did and didn't use:

- **Agent hooks / MCP / PBT / Powers:** we did **not** use these for TRACE. Given
  the hackathon timeline, we focused our Kiro usage on spec-driven development and
  steering, which gave us the most leverage for a safety-critical, multi-layer
  project. Our verification instead ran through the IDE agent executing real
  commands (`npm run build`, live FastAPI endpoint checks) after every change.
- A natural **next step** we'd pursue with more time: a **PostFileSave hook** to
  auto-run the frontend build and a backend smoke test, and **property-based
  tests** for the pipeline invariants our spec already names (e.g. the baseline
  z-score is 0 when a value equals its baseline; the RMS deviation is
  monotonic in the number of deviating signals).

## Net effect

Kiro let a small team ship a genuinely layered system — a reproducible synthetic
dataset, seven chained analysis features, a model trained and evaluated on
held-out real PhysioNet data, an adapter, a FastAPI backend, and a polished React
dashboard — while holding a strict non-diagnostic, data-separation contract the
entire time. Spec-driven development gave us the contract; steering made Kiro
enforce it on every turn.
