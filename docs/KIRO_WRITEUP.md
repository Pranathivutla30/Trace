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

## Agent hooks

We added a Kiro **agent hook** (`.kiro/hooks/build-on-save.json`): a
`PostFileSave` hook, scoped by a matcher to `frontend/src/**/*.{js,jsx,css}`,
that runs the Vite production build whenever a frontend source file is saved.
Because TRACE's dashboard is a chain of many small components, this turned
"did my last edit break the build?" from a manual step into an automatic,
immediate check — the hook surfaces a broken build the moment it happens instead
of at the next release. It made iterating on the UI safe and fast.

## Property-based testing (PBT)

We used **Hypothesis** to property-test the pipeline's mathematical invariants —
the guarantees that fixed-example unit tests tend to miss
(`ai_ml/tests/test_properties.py`). Rather than checking one case, these generate
hundreds of random inputs and assert properties that must *always* hold:

- The multivariate deviation score is **exactly 0** when every signal equals its
  baseline, and is **always non-negative and finite** for finite inputs.
- The **counterfactual invariant**: resetting any one signal to its baseline can
  only lower (never raise) the overall deviation — the exact property the
  "What If?" feature depends on.
- If every signal sits `k` standard deviations from its mean, the RMS deviation
  equals `|k|` (a clean correctness check on the z-score math).
- The adapter's Fahrenheit→Celsius conversion round-trips and keeps body-temp
  values in a plausible range.

PBT gave us confidence that these core guarantees hold for *any* patient data,
not just the synthetic and f16 examples — important for a tool that must never
misreport a deviation.

## MCP and Powers — honest scope

We did **not** use MCP servers or Kiro Powers for TRACE. Given the hackathon
timeline we concentrated our Kiro usage where it had the most leverage for a
safety-critical, multi-layer project: spec-driven development, steering,
an agent hook, and property-based tests, all verified by the IDE agent running
real commands (`npm run build`, live FastAPI endpoint checks, `pytest`).

## Net effect

Kiro let a small team ship a genuinely layered system — a reproducible synthetic
dataset, seven chained analysis features, a model trained and evaluated on
held-out real PhysioNet data, an adapter, a FastAPI backend, and a polished React
dashboard — while holding a strict non-diagnostic, data-separation contract the
entire time. Spec-driven development gave us the contract; steering made Kiro
enforce it on every turn.
