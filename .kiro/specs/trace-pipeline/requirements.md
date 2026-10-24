# TRACE — Requirements

## Introduction

TRACE is an exploratory, non-diagnostic tool that analyzes longitudinal
physiological signals to identify when and how a person's pattern changed. It
runs on a controlled synthetic patient (full demo) and a de-identified real
PhysioNet wearable recording (validation + trained anomaly model), and presents
the results in a React dashboard with an onboarding profile layer.

## Requirements

### R1 — Synthetic longitudinal patient
**User story:** As a judge, I want a controlled patient whose pattern clearly
changes, so TRACE's reasoning is easy to follow.
- WHEN the generator runs THEN it SHALL produce 30 consecutive days of 9
  physiological signals using random seed 42.
- The signals SHALL hold a stable baseline, then drift gradually at staggered
  days (sleep, HRV, EDA/stress, resting HR, activity, temperature).
- It SHALL NOT include disease labels or diagnoses.

### R2 — Seven TRACE reasoning capabilities (synthetic)
- Baseline (BioShadow): per-signal personal baseline + deviation.
- Change point (BioTimeMachine): earliest sustained multivariate shift.
- Relationships (ReverseHealth): which signals moved together + order.
- Missing info (BioMissing): value-of-information ranking.
- Self-Check: confidence in the temporal interpretation (not clinical).
- Counterfactual: per-signal sensitivity of the deviation score.
- Trajectories (HealthFork): exploratory future scenarios.
- All results SHALL be computed from data; nothing hardcoded.

### R3 — Real wearable support
- The system SHALL preprocess an Empatica-E4-style PhysioNet recording into
  60-second windows without copying raw files or exposing absolute timestamps.
- It SHALL select a demonstration participant from the dataset by a transparent
  score (result: f16) and run the core temporal analysis on it.

### R4 — Trained anomaly model
- An unsupervised IsolationForest (seed 42) SHALL learn baseline-like patterns
  from participants EXCLUDING f16, and be evaluated on held-out f16.
- Anomaly scores SHALL be labeled as deviation from learned normal — never
  disease/stress probability or clinical risk.

### R5 — Backend contract
- A FastAPI backend SHALL serve standardized JSON for `synthetic` and `real`
  sources; it SHALL NOT run ML or read raw datasets.
- An adapter SHALL translate the pipeline output into the backend contract
  without changing any analysis value.

### R6 — Dashboard + onboarding
- The React dashboard SHALL render all features in the existing Clinical Glass
  design, conditionally hiding features a source lacks.
- An onboarding profile SHALL persist in localStorage, recognize returning
  users, and support edit / exit without deleting the profile.
- Profile data SHALL remain frontend-only and SHALL NOT affect any analysis.

### R7 — Accessibility & safety wording
- Abbreviations SHALL be expanded (HRV, EDA, etc.) and phrasing SHALL be
  understandable without a health background.
- No screen SHALL imply diagnosis, disease risk, or treatment.
