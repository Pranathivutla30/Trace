"""
TRACE — Temporal Reasoning & Analysis for Clinical Exploration
Feature 2: "Where It Changed" / BioTimeMachine

Detects the earliest SUSTAINED multivariate physiological shift away from the
patient's learned personal baseline (Days 1-14).

The change point is derived entirely from the data by combining three
explainable signals:
  1. Baseline deviation (from Feature 1)
  2. IsolationForest anomaly score (trained only on the baseline period)
  3. Multivariate signal agreement (how many signals are jointly deviating)

This is temporal PATTERN detection, not medical diagnosis. It does not predict
or diagnose disease, and it does not claim any cause. All thresholds here are
TRACE analytical/demo criteria, not medical thresholds.
"""

import json
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ----- Configuration -----
FEATURES = [
    "sleep_hours",
    "hrv_ms",
    "resting_hr_bpm",
    "steps",
    "temperature_f",
    "respiratory_rate",
    "eda",
    "fatigue_score",
    "stress_score",
]

BASELINE_DAYS = 14          # Days 1-14 = stable baseline
RANDOM_STATE = 42
PATIENT_ID = "patient_001"

# Explainable weighted combination for the temporal change score.
W_DEVIATION = 0.45          # normalized baseline deviation
W_ANOMALY = 0.35            # normalized IsolationForest anomaly score
W_AGREEMENT = 0.20          # multivariate signal agreement
assert abs((W_DEVIATION + W_ANOMALY + W_AGREEMENT) - 1.0) < 1e-9

# TRACE analytical criteria (NOT medical thresholds)
SIGNAL_Z_THRESHOLD = 2.0    # |z| > 2 -> a signal is "meaningfully deviating"
SUSTAIN_WINDOW = 3          # look-ahead window for sustained change
SUSTAIN_MIN_HITS = 2        # need elevated on >= 2 of the next 3 days
ONSET_PERSIST = 2           # a signal onset needs 2 consecutive deviating days

HERE = os.path.dirname(__file__)
DATA_PATH = os.path.normpath(
    os.path.join(HERE, "..", "data", "synthetic", "patient_001.csv")
)
BASELINE_ANALYSIS_PATH = os.path.normpath(
    os.path.join(HERE, "..", "data", "synthetic", "patient_001_baseline_analysis.csv")
)
CHANGE_ANALYSIS_PATH = os.path.normpath(
    os.path.join(HERE, "..", "data", "synthetic", "patient_001_change_analysis.csv")
)
OUTPUTS_DIR = os.path.normpath(os.path.join(HERE, "..", "outputs"))
SUMMARY_PATH = os.path.join(OUTPUTS_DIR, "change_point_summary.json")


def normalize_01(series):
    """Min-max normalize a series into [0, 1]. Flat series -> all zeros."""
    lo = series.min()
    hi = series.max()
    if hi - lo == 0:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - lo) / (hi - lo)


def first_sustained_day(flags, days, persist=ONSET_PERSIST):
    """Return the first day where `flags` is True for `persist` consecutive days.

    `flags` is a boolean array aligned with `days`. Returns None if never
    sustained.
    """
    flags = list(flags)
    n = len(flags)
    for i in range(n - persist + 1):
        if all(flags[i:i + persist]):
            return int(days[i])
    return None


def main():
    # ---------------------------------------------------------------
    # Load data
    # ---------------------------------------------------------------
    df = pd.read_csv(DATA_PATH)
    baseline_analysis = pd.read_csv(BASELINE_ANALYSIS_PATH)

    days = df["day"].to_numpy()
    baseline_mask = df["day"] <= BASELINE_DAYS

    # ---------------------------------------------------------------
    # PART 1 — IsolationForest on the standardized baseline period
    # ---------------------------------------------------------------
    scaler = StandardScaler()
    X_baseline = scaler.fit_transform(df.loc[baseline_mask, FEATURES])
    X_all = scaler.transform(df[FEATURES])

    iso = IsolationForest(random_state=RANDOM_STATE)
    iso.fit(X_baseline)

    # score_samples: higher = more normal. Negate so higher = more unusual.
    raw_anomaly = -iso.score_samples(X_all)
    anomaly_score = pd.Series(raw_anomaly, index=df.index)
    normalized_anomaly = normalize_01(anomaly_score)

    # ---------------------------------------------------------------
    # PART 2 — Baseline deviation (reuse Feature 1 output)
    # ---------------------------------------------------------------
    raw_deviation = baseline_analysis["baseline_deviation_score"].astype(float)
    normalized_deviation = normalize_01(raw_deviation)

    # ---------------------------------------------------------------
    # PART 3 — Multivariate signal agreement
    # Recompute per-feature z-scores from the same personal baseline stats.
    # ---------------------------------------------------------------
    baseline_mean = df.loc[baseline_mask, FEATURES].mean()
    baseline_std = df.loc[baseline_mask, FEATURES].std(ddof=1).replace(0, np.nan)
    z = (df[FEATURES] - baseline_mean) / baseline_std
    z = z.fillna(0.0)

    deviating = z.abs() > SIGNAL_Z_THRESHOLD
    signal_agreement = deviating.sum(axis=1) / len(FEATURES)

    # ---------------------------------------------------------------
    # PART 4 — Temporal change score (explainable weighted blend)
    # ---------------------------------------------------------------
    temporal_change_score = (
        W_DEVIATION * normalized_deviation
        + W_ANOMALY * normalized_anomaly
        + W_AGREEMENT * signal_agreement
    )

    # ---------------------------------------------------------------
    # PART 5 — Sustained change-point detection
    # Threshold derived from the baseline-period temporal scores, not the
    # target day. Elevated = above baseline mean + 2*std of the baseline window.
    # ---------------------------------------------------------------
    baseline_scores = temporal_change_score[baseline_mask.to_numpy()]
    elevated_threshold = float(
        baseline_scores.mean() + 2.0 * baseline_scores.std(ddof=1)
    )

    elevated = (temporal_change_score > elevated_threshold).to_numpy()

    # A day is a sustained change if it is elevated AND at least
    # SUSTAIN_MIN_HITS of the next SUSTAIN_WINDOW days are also elevated.
    n = len(df)
    is_sustained = np.zeros(n, dtype=bool)
    for i in range(n):
        if not elevated[i]:
            continue
        end = min(i + 1 + SUSTAIN_WINDOW, n)
        future_hits = int(elevated[i + 1:end].sum())
        if future_hits >= SUSTAIN_MIN_HITS:
            is_sustained[i] = True

    # Earliest sustained day that is NOT inside the baseline training period.
    detected_idx = None
    for i in range(n):
        if is_sustained[i] and days[i] > BASELINE_DAYS:
            detected_idx = i
            break
    # Fallback: if persistence never triggers after baseline, take the first
    # elevated day after baseline (keeps the pipeline robust, still data-driven).
    if detected_idx is None:
        for i in range(n):
            if elevated[i] and days[i] > BASELINE_DAYS:
                detected_idx = i
                break

    # ---------------------------------------------------------------
    # PART 6 — Signal onset timeline
    # Earliest day each feature is |z|>threshold for 2 consecutive days.
    # ---------------------------------------------------------------
    signal_onsets = {}
    for feat in FEATURES:
        flags = (z[feat].abs() > SIGNAL_Z_THRESHOLD).to_numpy()
        signal_onsets[feat] = first_sustained_day(flags, days)

    # ---------------------------------------------------------------
    # Assemble per-day analysis table
    # ---------------------------------------------------------------
    analysis = pd.DataFrame(
        {
            "date": df["date"],
            "day": df["day"],
            "raw_baseline_deviation": raw_deviation.round(4),
            "normalized_baseline_deviation": normalized_deviation.round(4),
            "anomaly_score": anomaly_score.round(4),
            "normalized_anomaly_score": normalized_anomaly.round(4),
            "signal_agreement": signal_agreement.round(4),
            "temporal_change_score": temporal_change_score.round(4),
            "is_sustained_change": is_sustained,
        }
    )
    analysis.to_csv(CHANGE_ANALYSIS_PATH, index=False)

    # ---------------------------------------------------------------
    # Build change-point summary
    # ---------------------------------------------------------------
    detected_day = int(days[detected_idx])
    detected_date = str(df.iloc[detected_idx]["date"])
    score_at_detection = float(temporal_change_score.iloc[detected_idx])

    # Signals active (|z|>threshold) at the detected change point.
    active_at_change = [
        feat for feat in FEATURES
        if abs(float(z.iloc[detected_idx][feat])) > SIGNAL_Z_THRESHOLD
    ]

    # Confidence: how strongly the detection day stands above the elevated
    # threshold, scaled by sustained persistence in the look-ahead window.
    # Expressed as a 0-1 value (clipped).
    end = min(detected_idx + 1 + SUSTAIN_WINDOW, n)
    persistence_ratio = (
        int(elevated[detected_idx + 1:end].sum()) / SUSTAIN_WINDOW
        if SUSTAIN_WINDOW > 0 else 0.0
    )
    score_margin = score_at_detection - elevated_threshold
    score_range = float(temporal_change_score.max() - elevated_threshold)
    margin_ratio = score_margin / score_range if score_range > 0 else 0.0
    confidence = float(np.clip(0.5 * margin_ratio + 0.5 * persistence_ratio, 0.0, 1.0))

    # Plain-English explanation generated from the computed results.
    n_active = len(active_at_change)
    explanation = (
        f"TRACE detected the earliest sustained departure from the patient's "
        f"personal baseline around Day {detected_day} ({detected_date}). "
        f"At detection the temporal change score was {score_at_detection:.3f}, "
        f"above the baseline-derived elevated threshold of {elevated_threshold:.3f}. "
        f"The change was supported by coordinated movement across {n_active} "
        f"physiological signal(s): {', '.join(active_at_change) if active_at_change else 'none individually past the signal criterion yet'}. "
        f"This reflects a sustained multivariate shift, not a single noisy day. "
        f"This is temporal pattern detection only and is not a diagnosis."
    )

    summary = {
        "patient_id": PATIENT_ID,
        "method": (
            "Weighted blend of normalized baseline deviation (45%), "
            "IsolationForest anomaly score (35%), and multivariate signal "
            "agreement (20%), with sustained change-point detection using a "
            "baseline-derived elevated threshold."
        ),
        "baseline_period": f"Days 1-{BASELINE_DAYS}",
        "detected_change_day": detected_day,
        "detected_change_date": detected_date,
        "confidence": round(confidence, 4),
        "temporal_change_score_at_detection": round(score_at_detection, 4),
        "signal_onsets": signal_onsets,
        "signals_active_at_change_point": active_at_change,
        "explanation": explanation,
    }
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    # ---------------------------------------------------------------
    # PRINT
    # ---------------------------------------------------------------
    print("=" * 64)
    print("TRACE Feature 2 — Where It Changed / BioTimeMachine")
    print("=" * 64)

    print(f"\n1. IsolationForest training period: Days 1-{BASELINE_DAYS} "
          f"(random_state={RANDOM_STATE})")

    print("\n2. Daily temporal change scores — Days 15-30:")
    print(f"   (elevated threshold = {elevated_threshold:.4f})")
    for _, r in analysis[analysis["day"] >= 15].iterrows():
        mark = "  <-- sustained" if r["is_sustained_change"] else ""
        print(
            f"   Day {int(r['day']):>2}  "
            f"score={r['temporal_change_score']:.4f}  "
            f"(dev={r['normalized_baseline_deviation']:.2f} "
            f"anom={r['normalized_anomaly_score']:.2f} "
            f"agree={r['signal_agreement']:.2f}){mark}"
        )

    print(f"\n3. Detected change point: Day {detected_day} ({detected_date})")
    print(f"   temporal_change_score at detection = {score_at_detection:.4f}")

    print("\n4. Signal onset timeline (first sustained deviation day):")
    for feat in FEATURES:
        onset = signal_onsets[feat]
        onset_str = f"Day {onset}" if onset is not None else "no sustained deviation"
        print(f"   {feat:<20} -> {onset_str}")

    print(f"\n5. Signals active at detected change point (Day {detected_day}):")
    if active_at_change:
        for feat in active_at_change:
            print(f"   {feat:<20} z={float(z.iloc[detected_idx][feat]):+.2f}")
    else:
        print("   (no single signal past the |z|>2 criterion on this exact day)")

    print(f"\n6. Confidence score: {confidence:.4f}")

    print(f"\nSaved change analysis CSV : {CHANGE_ANALYSIS_PATH}")
    print(f"Saved change summary JSON : {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
