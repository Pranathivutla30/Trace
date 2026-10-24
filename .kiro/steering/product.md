---
inclusion: always
---

# TRACE — Product Steering

TRACE (Temporal Reasoning & Analysis for Clinical Exploration) explores
longitudinal physiological data to find **where a person's pattern changed**,
**what changed together**, **what information is missing**, **how confident the
interpretation is**, and **how alternative scenarios compare**.

Tagline: "Find where the story changed."

## Non-negotiable product rules

- TRACE is **exploratory and non-diagnostic**. Never output disease
  probability, stress probability, diagnosis, clinical risk, or treatment
  advice. Use words like *context, pattern, physiological evidence, observed
  change, exploration*.
- The ML anomaly score is "deviation from a learned baseline-like pattern" —
  never "disease/stress probability" or "clinical risk score".
- Correlations are **associations, not causation**. Trajectories are
  **example scenarios, not predictions**.
- Keep wording understandable for people without a health background: expand
  abbreviations (HRV = heart rate variability, EDA = electrical skin activity),
  and prefer plain phrasing ("10 days ago" over "Day -10").

## Two data sources

- **Synthetic Patient 001** — a controlled 30-day demo patient that showcases
  all seven TRACE capabilities.
- **Real f16** — a de-identified PhysioNet wearable recording used to validate
  the core temporal reasoning plus a trained anomaly model.

## Data separation (critical)

The onboarding user profile is **context only**. It must never be fed into the
AI/ML analysis, and must never change baseline, change point, anomaly scores,
self-check confidence, counterfactuals, trajectories, or missing-information
results.
