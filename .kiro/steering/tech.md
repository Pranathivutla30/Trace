---
inclusion: always
---

# TRACE — Technical Steering

## Architecture (data flows one direction)

```
ai_ml/ (Python pipeline)  →  outputs/*.json
        │
        ▼
ai_ml/export_for_backend.py  →  ai_ml/output/{source}_{id}.json   (adapter)
        │
        ▼
backend/ (FastAPI)  — reads the adapter JSON, serves it, computes nothing
        │
        ▼
frontend/ (React + Vite, "Clinical Glass" theme)  — renders the dashboard
```

## Layers

- **ai_ml/** — seven analysis scripts (baseline, change_detection,
  relationships, missing_information, self_check, counterfactual, trajectories),
  plus `generate_patient.py`, the PhysioNet prep/selection scripts, and
  `train_transition_model.py` (an IsolationForest, `random_state=42`).
- **models/** — the trained joblib model + metadata.
- **backend/** — FastAPI. `data_service.py` reads `ai_ml/output/` first, falls
  back to `backend/mock/`. It never opens a raw dataset and never runs ML.
- **frontend/** — React dashboard; signal metadata lives in
  `src/config/signals.js`; profile persistence in
  `src/services/profileStorage.js` (localStorage `trace_user_profile_v1`).

## Conventions

- Determinism: all randomness uses seed 42.
- The backend contract is defined by `backend/mock/*.json`; the adapter must
  match it (signal names, `t`-based timeline, block names).
- Never modify generated analysis JSON by hand. Never change analysis values to
  make the UI look nicer.
- Verify changes with `npm run build` (frontend) and by running the FastAPI
  server and hitting the endpoints.

## Commands

- Backend: `uvicorn main:app --reload` from `backend/`
- Frontend: `npm install && npm run dev` from `frontend/` (Vite proxies
  `/api` to `http://localhost:8000`)
- Regenerate adapter output: `python ai_ml/export_for_backend.py`
