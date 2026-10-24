"""
TRACE — Temporal Reasoning & Analysis for Clinical Exploration
Small trained model: train_transition_model.py

Trains an UNSUPERVISED IsolationForest that learns baseline-like multivariate
physiological patterns from real PhysioNet STRESS wearable recordings, then
evaluates it on the held-out demonstration participant f16 without retraining.

This is NOT a disease classifier and NOT a stress classifier. It learns what a
person's own baseline-relative physiology looks like and flags windows that
deviate from that learned baseline shape. Anomaly scores are not disease or
stress probabilities, diagnoses, or clinical risk scores.

Reuses the robust preprocessing from prepare_physionet.py / select_real_participant.py
rather than duplicating raw parsing. Trains on baseline-relative z-scores pooled
across eligible participants (f16 excluded). Participant IDs are never features.
"""

import json
import os

import numpy as np
import joblib
from sklearn.ensemble import IsolationForest

# Reuse robust preprocessing + eligibility constants (no raw-parse duplication).
from prepare_physionet import DATASET_ROOT
from select_real_participant import (
    discover_participants,
    build_windows_in_memory,
    safe_std,
    SELECTION_FEATURES,
    BASELINE_FRACTION,
    MIN_BASELINE_WINDOWS,
    MIN_USABLE_WINDOWS,
    MIN_MEAN_QUALITY,
)

# ----- Configuration -----
HELD_OUT = "f16"              # demonstration participant, excluded from training
RANDOM_STATE = 42
FEATURES = list(SELECTION_FEATURES)  # HR, HRV, EDA, TEMP, ACC magnitude

HERE = os.path.dirname(__file__)
MODELS_DIR = os.path.normpath(os.path.join(HERE, "..", "models"))
OUTPUTS_DIR = os.path.normpath(os.path.join(HERE, "..", "outputs"))
MODEL_PATH = os.path.join(MODELS_DIR, "trace_transition_isolation_forest.joblib")
METADATA_PATH = os.path.join(MODELS_DIR, "trace_transition_model_metadata.json")
ML_ANALYSIS_PATH = os.path.join(OUTPUTS_DIR, "real_f16_ml_analysis.json")

MODEL_DISCLAIMER = (
    "This unsupervised model identifies deviations from learned baseline-like "
    "physiological patterns. Its anomaly scores are not disease probabilities, "
    "stress probabilities, diagnoses, or clinical risk scores."
)


def participant_baseline_z(name):
    """Build windows for a participant and return baseline-relative z-score
    vectors.

    Returns (baseline_z, all_z, windows, n_base) where:
      baseline_z : list of z-vectors for the baseline windows (training rows)
      all_z      : list of (window_index, elapsed_minutes, z-vector) for all
                   windows with full feature availability
      Returns None if the participant is ineligible.
    """
    windows, _tags = build_windows_in_memory(os.path.join(DATASET_ROOT, name))
    n_windows = len(windows)
    if n_windows < MIN_USABLE_WINDOWS:
        return None

    dq = np.array([w["data_quality_score"] for w in windows], dtype=float)
    if float(np.mean(dq)) < MIN_MEAN_QUALITY:
        return None

    n_base = max(MIN_BASELINE_WINDOWS, int(round(BASELINE_FRACTION * n_windows)))
    n_base = min(n_base, n_windows - 1)
    if n_base < MIN_BASELINE_WINDOWS:
        return None

    base_windows = windows[:n_base]

    # Personal baseline mean/std per feature (safe std for near-zero variance).
    base_mean, base_std = {}, {}
    for feat in FEATURES:
        col = np.array([w[feat] for w in base_windows], dtype=float)
        col = col[~np.isnan(col)]
        if len(col) < 2:
            return None  # cannot form a stable personal baseline
        base_mean[feat] = float(np.mean(col))
        base_std[feat] = safe_std(col)

    def z_vector(w):
        vec = []
        for feat in FEATURES:
            val = w[feat]
            if np.isnan(val):
                return None  # require full feature availability for a row
            vec.append((val - base_mean[feat]) / base_std[feat])
        return vec

    baseline_z = [z for z in (z_vector(w) for w in base_windows) if z is not None]
    all_z = []
    for i, w in enumerate(windows):
        z = z_vector(w)
        if z is not None:
            all_z.append((int(w["window"]), float(w["elapsed_minutes"]), z, i < n_base))

    if len(baseline_z) < MIN_BASELINE_WINDOWS:
        return None
    return baseline_z, all_z, n_base


def normalize_scores(raw):
    """Map raw anomaly scores (higher = more anomalous) to 0-1 for display."""
    arr = np.asarray(raw, dtype=float)
    lo, hi = float(np.min(arr)), float(np.max(arr))
    if hi - lo == 0:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)


def main():
    all_participants = discover_participants()

    # ---------------- Build training set (exclude f16) ----------------
    training_participants = []
    excluded_from_training = []
    X_rows = []
    per_participant_baseline_counts = {}

    for name in all_participants:
        if name == HELD_OUT:
            continue
        result = participant_baseline_z(name)
        if result is None:
            excluded_from_training.append(name)
            continue
        baseline_z, _all_z, _n_base = result
        X_rows.extend(baseline_z)
        training_participants.append(name)
        per_participant_baseline_counts[name] = len(baseline_z)

    if not X_rows:
        raise SystemExit("No training rows assembled.")
    X = np.asarray(X_rows, dtype=float)

    # ---------------- Train IsolationForest ----------------
    model = IsolationForest(random_state=RANDOM_STATE)
    model.fit(X)

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    metadata = {
        "model_type": "IsolationForest",
        "features": FEATURES,
        "training_participants": training_participants,
        "training_participant_count": len(training_participants),
        "training_window_count": int(X.shape[0]),
        "normalization_method": (
            "Per-participant baseline-relative z-scores: "
            "z = (value - personal_baseline_mean) / personal_baseline_std, "
            "using the first 20% of each participant's usable windows as that "
            "participant's provisional baseline (safe std for near-zero variance)."
        ),
        "random_state": RANDOM_STATE,
        "purpose": (
            "Learn baseline-like multivariate physiological patterns for "
            "unsupervised temporal transition detection."
        ),
        "limitations": (
            "Unsupervised; trained only on baseline-like windows from a small "
            "number of research participants. Anomaly scores reflect deviation "
            "from learned baseline shape, NOT disease, stress, diagnosis, or "
            "clinical risk. Not validated for any clinical use."
        ),
        "held_out_participant": HELD_OUT,
        "excluded_from_training_for_quality": excluded_from_training,
    }
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    # ---------------- Held-out evaluation on f16 (no retraining) ----------------
    held = participant_baseline_z(HELD_OUT)
    if held is None:
        raise SystemExit(f"Held-out participant {HELD_OUT} not usable.")
    _f16_base_z, f16_all_z, f16_n_base = held

    # Score every f16 window. score_samples: higher = more normal -> negate so
    # higher = more anomalous (consistent with the rest of TRACE).
    f16_vectors = np.asarray([z for (_w, _m, z, _b) in f16_all_z], dtype=float)
    raw_scores = -model.score_samples(f16_vectors)
    display_scores = normalize_scores(raw_scores)

    timeline = []
    baseline_disp, post_disp = [], []
    for idx, (win, minute, _z, is_base) in enumerate(f16_all_z):
        disp = float(display_scores[idx])
        timeline.append({
            "window": win,
            "elapsed_minutes": round(minute, 4),
            "ml_anomaly_score": round(disp, 4),
            "raw_model_score": round(float(raw_scores[idx]), 6),
            "is_baseline": bool(is_base),
        })
        (baseline_disp if is_base else post_disp).append(disp)

    baseline_mean_anomaly = round(float(np.mean(baseline_disp)), 4) if baseline_disp else None
    post_baseline_mean_anomaly = round(float(np.mean(post_disp)), 4) if post_disp else None

    peak_idx = int(np.argmax(display_scores))
    peak_anomaly_window = int(f16_all_z[peak_idx][0])
    peak_anomaly_score = round(float(display_scores[peak_idx]), 4)

    # Persistence: any run of >=3 consecutive windows above baseline mean + 2*std.
    if baseline_disp:
        base_arr = np.array(baseline_disp, dtype=float)
        persist_threshold = float(np.mean(base_arr) + 2.0 * (safe_std(base_arr) or 0.0))
    else:
        persist_threshold = float("inf")
    flags = [s > persist_threshold for s in display_scores]
    persistent_anomaly_detected = False
    run = 0
    for fl in flags:
        run = run + 1 if fl else 0
        if run >= 3:
            persistent_anomaly_detected = True
            break

    evaluation = {
        "baseline_mean_anomaly": baseline_mean_anomaly,
        "post_baseline_mean_anomaly": post_baseline_mean_anomaly,
        "peak_anomaly_window": peak_anomaly_window,
        "peak_anomaly_score": peak_anomaly_score,
        "persistent_anomaly_detected": bool(persistent_anomaly_detected),
        "persistence_threshold_display": round(persist_threshold, 4)
        if np.isfinite(persist_threshold) else None,
    }

    output = {
        "model": {
            "model_type": "IsolationForest",
            "features": FEATURES,
            "random_state": RANDOM_STATE,
            "model_path": os.path.relpath(MODEL_PATH, os.path.join(HERE, "..")),
        },
        "training_summary": {
            "training_participants": training_participants,
            "training_participant_count": len(training_participants),
            "training_window_count": int(X.shape[0]),
            "excluded_from_training_for_quality": excluded_from_training,
            "held_out_participant": HELD_OUT,
        },
        "held_out_participant": HELD_OUT,
        "timeline": timeline,
        "evaluation": evaluation,
        "disclaimer": MODEL_DISCLAIMER,
    }
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    with open(ML_ANALYSIS_PATH, "w") as f:
        json.dump(output, f, indent=2)

    # ---------------- VALIDATION + PRINT ----------------
    # 1. f16 excluded from training?
    f16_in_training = HELD_OUT in training_participants
    # 2. model reloads?
    reloaded = joblib.load(MODEL_PATH)
    reload_ok = reloaded is not None
    # 3. JSON parses?
    with open(ML_ANALYSIS_PATH) as f:
        json.load(f)
    # 4. reproducibility with the same seed?
    model2 = IsolationForest(random_state=RANDOM_STATE).fit(X)
    raw2 = -model2.score_samples(f16_vectors)
    reproducible = bool(np.allclose(raw_scores, raw2))

    print("=" * 70)
    print("TRACE — Transition model training + held-out evaluation")
    print("=" * 70)
    print(f"model type                   : IsolationForest (random_state={RANDOM_STATE})")
    print(f"training participant count   : {len(training_participants)}")
    print(f"training baseline windows    : {int(X.shape[0])}")
    print(f"features                     : {', '.join(FEATURES)}")
    print(f"held-out participant         : {HELD_OUT}")
    print(f"baseline mean anomaly        : {baseline_mean_anomaly}")
    print(f"post-baseline mean anomaly   : {post_baseline_mean_anomaly}")
    print(f"peak anomaly window          : {peak_anomaly_window}")
    print(f"peak anomaly score           : {peak_anomaly_score}")
    print(f"persistent anomaly detected  : {persistent_anomaly_detected}")
    print(f"saved model path             : {MODEL_PATH}")
    print(f"saved JSON path              : {ML_ANALYSIS_PATH}")

    print("\nVerification:")
    print(f"  1. f16 NOT in training       : {not f16_in_training}")
    print(f"  2. model reloads via joblib  : {reload_ok}")
    print(f"  3. JSON parses               : True")
    print(f"  4. reproducible (same seed)  : {reproducible}")

    if f16_in_training:
        raise SystemExit("ERROR: held-out participant leaked into training!")


if __name__ == "__main__":
    main()
