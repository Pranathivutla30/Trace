# TRACE — Design

## Overview

TRACE is a one-directional pipeline: Python analysis → JSON → adapter → FastAPI
→ React. Each layer has a single responsibility, which keeps the AI/ML results
immutable as they flow to the UI.

## Components

### AI/ML (`ai_ml/`)
- `generate_patient.py` creates the synthetic dataset (seed 42).
- Seven feature scripts each read prior outputs and emit a JSON summary in
  `outputs/`. They chain: baseline → change_detection → relationships →
  missing_information → self_check → counterfactual → trajectories.
- `build_analysis.py` merges the synthetic feature outputs into one payload.
- Real-data path: `prepare_physionet.py` (robust Empatica parsing: HR/EDA/TEMP
  single-column, ACC 3-axis magnitude, irregular IBI → RMSSD; elapsed seconds
  only) → `select_real_participant.py` (eligibility + change-strength score) →
  `analyze_real_patient.py`.
- `train_transition_model.py` trains an IsolationForest on per-participant
  baseline-relative z-scores, excluding f16, saved via joblib.

### Adapter (`ai_ml/export_for_backend.py`)
- Translates pipeline output into the backend contract: signal renames
  (`sleep_hours`→`sleep_h`, etc.), °F→°C for synthetic temperature, day index
  → `t` where the last day is 0, and reshapes each analysis block.
- Merges per-window ML anomaly scores and a `ml_transition_model` summary into
  the real output. Missing early scores stay `null` (no fabrication).

### Backend (`backend/`)
- FastAPI endpoints: `/api/sources`, `/api/patient/{id}`,
  `/api/patient/{id}/timeline`, `/api/patient/{id}/analysis`, and a
  counterfactual POST.
- `data_service.load_analysis` reads `ai_ml/output/` first (`data_status:
  "live"`), falls back to `backend/mock/` (`"mock"`).

### Frontend (`frontend/`)
- `App.jsx` routes Welcome → Onboarding → Choose Experience → Dashboard.
- `Investigation.jsx` orchestrates the dashboard; one component per feature.
  Source-aware nav hides unavailable features (e.g. no counterfactual/trajectory
  for real f16); a dedicated `MlAnomaly` card shows the trained model.
- `signals.js` is the single source of truth for labels, plain-English
  full-forms, and colors. `profileStorage.js` isolates all localStorage access.

## Key decisions
- Determinism (seed 42) so results are reproducible for judging.
- Profile is cosmetic + a clearly-labeled "Your Context" comparison; it is a
  deliberate firewall, never an input to the analysis.
- The backend computes nothing, so the UI can never alter analysis values.

## Testing / verification
- Frontend: `npm run build` must pass.
- Integration: start FastAPI, hit endpoints, confirm `data_status: "live"` and
  that real f16 retains anomaly 0.1454 / 0.6694 / 1.0 at window 29 (35 trained,
  f16 held out).
