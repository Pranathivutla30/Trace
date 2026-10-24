---
inclusion: always
---

# TRACE — Project Structure

```
Trace/
├── ai_ml/                     # Python analysis pipeline + model training
│   ├── generate_patient.py        # synthetic 30-day patient (seed 42)
│   ├── baseline.py                # Feature 1 — BioShadow
│   ├── change_detection.py        # Feature 2 — BioTimeMachine
│   ├── relationships.py           # Feature 3 — ReverseHealth
│   ├── missing_information.py     # Feature 4 — BioMissing
│   ├── self_check.py              # Feature 5 — AI Self-Check
│   ├── counterfactual.py          # Feature 6 — Counterfactual Patient
│   ├── trajectories.py            # Feature 7 — HealthFork
│   ├── build_analysis.py          # unified synthetic analysis JSON
│   ├── prepare_physionet.py       # real wearable preprocessing (Empatica E4)
│   ├── select_real_participant.py # data-driven participant selection -> f16
│   ├── analyze_real_patient.py    # core temporal analysis on real f16
│   ├── train_transition_model.py  # IsolationForest anomaly model
│   ├── export_for_backend.py      # adapter: pipeline output -> backend contract
│   └── output/                    # live JSON the backend serves
├── models/                    # trained model + metadata (joblib/json)
├── outputs/                   # raw per-feature analysis JSON
├── data/synthetic/            # synthetic patient CSVs (seed 42)
├── backend/                   # FastAPI (serves JSON, no ML, no raw data)
├── frontend/                  # React + Vite "Clinical Glass" dashboard
├── docs/
└── .kiro/                     # steering + specs (Kiro usage)
```

## Boundaries
- Changes to AI/ML stay in `ai_ml/`; the backend only reads JSON; the frontend
  only renders. Do not cross these boundaries.
- Raw PhysioNet data is never copied into the repo; only processed window CSVs
  and derived JSON may be committed.
