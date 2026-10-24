"""
TRACE — Temporal Reasoning & Analysis for Clinical Exploration
Feature 5: "Can We Trust This?" / AI Self-Check

Estimates how reliable TRACE's own temporal interpretation is, based on the
quality, coordination, persistence, completeness, and robustness of the
evidence produced by Features 1-4.

This is NOT diagnostic confidence, NOT a probability of disease, and NOT
clinical certainty. It is TRACE's confidence in its own temporal reading of the
data. All bands and criteria here are TRACE prototype values, not clinical ones.
"""

import json
import os

import numpy as np
import pandas as pd

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

BASELINE_DAYS = 14
PATIENT_ID = "patient_001"
CORR_THRESHOLD = 0.60          # matches Feature 3 demo criterion
SUSTAIN_WINDOW = 3             # matches Feature 2
SUSTAIN_MIN_HITS = 2           # matches Feature 2

# Overall-confidence weights (sum to 1). Visible and explainable.
WEIGHTS = {
    "deviation_strength": 0.22,
    "signal_agreement": 0.18,
    "temporal_persistence": 0.18,
    "data_completeness": 0.12,
    "relationship_consistency": 0.15,
    "robustness": 0.15,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

# How strongly interpretation ambiguity pulls confidence down (0-1 scale of
# the penalty's maximum effect).
UNCERTAINTY_PENALTY_WEIGHT = 0.30

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.normpath(os.path.join(HERE, "..", "data", "synthetic"))
OUTPUTS_DIR = os.path.normpath(os.path.join(HERE, "..", "outputs"))

DATA_PATH = os.path.join(DATA_DIR, "patient_001.csv")
CHANGE_ANALYSIS_PATH = os.path.join(DATA_DIR, "patient_001_change_analysis.csv")
BASELINE_SUMMARY_PATH = os.path.join(OUTPUTS_DIR, "baseline_summary.json")
CHANGE_SUMMARY_PATH = os.path.join(OUTPUTS_DIR, "change_point_summary.json")
RELATIONSHIP_SUMMARY_PATH = os.path.join(OUTPUTS_DIR, "relationship_summary.json")
MISSING_SUMMARY_PATH = os.path.join(OUTPUTS_DIR, "missing_information_summary.json")
SELF_CHECK_PATH = os.path.join(OUTPUTS_DIR, "self_check_summary.json")


def clip01(x):
    return float(np.clip(x, 0.0, 1.0))


def load_json(path):
    with open(path) as f:
        return json.load(f)


def detect_change_day(scores, days, baseline_mask, threshold,
                      sustain_window=SUSTAIN_WINDOW,
                      sustain_min_hits=SUSTAIN_MIN_HITS):
    """Re-run the earliest-sustained-change rule for a given threshold.

    This mirrors Feature 2's logic locally for sensitivity testing ONLY.
    Feature 2 itself is not modified. Returns the earliest change day after
    the baseline period, or None.
    """
    elevated = (scores > threshold).to_numpy()
    n = len(scores)
    for i in range(n):
        if not elevated[i] or days[i] <= BASELINE_DAYS:
            continue
        end = min(i + 1 + sustain_window, n)
        if int(elevated[i + 1:end].sum()) >= sustain_min_hits:
            return int(days[i])
    # Fallback: first elevated day after baseline.
    for i in range(n):
        if elevated[i] and days[i] > BASELINE_DAYS:
            return int(days[i])
    return None


def main():
    # ---------------------------------------------------------------
    # PART 1 — Load existing evidence
    # ---------------------------------------------------------------
    baseline_summary = load_json(BASELINE_SUMMARY_PATH)
    change_summary = load_json(CHANGE_SUMMARY_PATH)
    relationship_summary = load_json(RELATIONSHIP_SUMMARY_PATH)
    missing_summary = load_json(MISSING_SUMMARY_PATH)

    df = pd.read_csv(DATA_PATH)
    change_df = pd.read_csv(CHANGE_ANALYSIS_PATH)

    detected_change_day = int(change_summary["detected_change_day"])
    signal_onsets = change_summary.get("signal_onsets", {})

    days = change_df["day"].to_numpy()
    baseline_mask = change_df["day"] <= BASELINE_DAYS
    post_mask = change_df["day"] >= detected_change_day

    tcs = change_df["temporal_change_score"].astype(float)
    baseline_tcs = tcs[baseline_mask.to_numpy()]
    post_tcs = tcs[post_mask.to_numpy()]

    # ---------------------------------------------------------------
    # PART 2 — Deviation / separation strength
    # Separation between post-change and baseline temporal scores, scaled by
    # baseline spread (a standardized gap), squashed into 0-1.
    # ---------------------------------------------------------------
    baseline_mean_tcs = float(baseline_tcs.mean())
    baseline_std_tcs = float(baseline_tcs.std(ddof=1)) or 1e-9
    separation = (float(post_tcs.mean()) - baseline_mean_tcs) / baseline_std_tcs
    # Map a standardized separation (~0..6+) into 0-1; /6 keeps strong gaps high.
    deviation_strength = clip01(separation / 6.0)

    # ---------------------------------------------------------------
    # PART 3 — Multi-signal agreement
    # Mean of signal_agreement from the change point onward.
    # ---------------------------------------------------------------
    signal_agreement_score = clip01(
        float(change_df.loc[post_mask, "signal_agreement"].mean())
    )

    # ---------------------------------------------------------------
    # PART 4 — Temporal persistence
    # Fraction of post-change days whose temporal score stays elevated above
    # the baseline-derived threshold used in Feature 2.
    # ---------------------------------------------------------------
    elevated_threshold = baseline_mean_tcs + 2.0 * baseline_std_tcs
    post_elevated = (post_tcs > elevated_threshold)
    temporal_persistence_score = clip01(float(post_elevated.mean()))

    # ---------------------------------------------------------------
    # PART 5 — Data completeness (SENSOR data only)
    # Missing values across physiological sensor columns in the raw dataset.
    # Contextual BioMissing variables are intentionally absent and are NOT
    # treated as missing sensor records.
    # ---------------------------------------------------------------
    total_cells = len(df) * len(FEATURES)
    missing_cells = int(df[FEATURES].isna().sum().sum())
    data_completeness_score = clip01(
        (total_cells - missing_cells) / total_cells if total_cells else 0.0
    )

    # ---------------------------------------------------------------
    # PART 6 — Interpretation uncertainty penalty
    # Normalize current entropy by max entropy for the number of hypotheses.
    # ---------------------------------------------------------------
    current_uncertainty = float(missing_summary["current_uncertainty"])
    n_hypotheses = len(relationship_summary["hypothesis_groups"])
    max_entropy = np.log2(n_hypotheses) if n_hypotheses > 1 else 1.0
    normalized_uncertainty = clip01(current_uncertainty / max_entropy)
    # Penalty is a fraction that will scale down the blended confidence.
    interpretation_uncertainty_penalty = clip01(
        UNCERTAINTY_PENALTY_WEIGHT * normalized_uncertainty
    )

    # ---------------------------------------------------------------
    # PART 7 — Relationship consistency
    # Blend: strength of strong correlations, coverage of detected onsets,
    # and monotonic consistency of the temporal ordering.
    # ---------------------------------------------------------------
    strong = relationship_summary.get("strong_correlations", [])
    if strong:
        mean_strong_corr = float(np.mean([abs(c["correlation"]) for c in strong]))
    else:
        mean_strong_corr = 0.0

    onset_days = [d for d in signal_onsets.values() if d is not None]
    onset_coverage = len(onset_days) / len(FEATURES) if FEATURES else 0.0

    # Ordering consistency: are onsets well spread/monotonic through time?
    ordered = relationship_summary.get("ordered_signal_onsets", [])
    if len(ordered) >= 2:
        seq = [o["onset_day"] for o in ordered]
        non_decreasing = sum(
            1 for i in range(1, len(seq)) if seq[i] >= seq[i - 1]
        )
        ordering_consistency = non_decreasing / (len(seq) - 1)
    else:
        ordering_consistency = 0.0

    relationship_consistency_score = clip01(
        0.5 * mean_strong_corr + 0.3 * onset_coverage + 0.2 * ordering_consistency
    )

    # ---------------------------------------------------------------
    # PART 8 — Sensitivity / robustness check
    # Re-detect the change day at the original threshold, +/-10%, and with a
    # stricter persistence rule. Measure how far the detected day moves.
    # (Feature 2 is NOT modified; this reuses its score column.)
    # ---------------------------------------------------------------
    scenarios = {
        "original_threshold": (elevated_threshold, SUSTAIN_MIN_HITS),
        "threshold_minus_10pct": (elevated_threshold * 0.9, SUSTAIN_MIN_HITS),
        "threshold_plus_10pct": (elevated_threshold * 1.1, SUSTAIN_MIN_HITS),
        "stricter_persistence": (elevated_threshold, SUSTAIN_MIN_HITS + 1),
    }
    alternative_change_days = {}
    for name, (thr, min_hits) in scenarios.items():
        d = detect_change_day(
            tcs, days, baseline_mask, thr, sustain_min_hits=min_hits
        )
        alternative_change_days[name] = d

    valid_days = [d for d in alternative_change_days.values() if d is not None]
    if valid_days:
        max_change_day_shift = int(
            max(abs(d - detected_change_day) for d in valid_days)
        )
    else:
        max_change_day_shift = None

    # Robustness: small shifts -> high score. 0-day shift = 1.0; decays ~1/day.
    if max_change_day_shift is None:
        robustness_score = 0.0
    else:
        robustness_score = clip01(1.0 - (max_change_day_shift / 5.0))

    # ---------------------------------------------------------------
    # PART 9 — Overall interpretation confidence
    # ---------------------------------------------------------------
    components = {
        "deviation_strength": round(deviation_strength, 4),
        "signal_agreement": round(signal_agreement_score, 4),
        "temporal_persistence": round(temporal_persistence_score, 4),
        "data_completeness": round(data_completeness_score, 4),
        "relationship_consistency": round(relationship_consistency_score, 4),
        "robustness": round(robustness_score, 4),
    }

    blended = (
        WEIGHTS["deviation_strength"] * deviation_strength
        + WEIGHTS["signal_agreement"] * signal_agreement_score
        + WEIGHTS["temporal_persistence"] * temporal_persistence_score
        + WEIGHTS["data_completeness"] * data_completeness_score
        + WEIGHTS["relationship_consistency"] * relationship_consistency_score
        + WEIGHTS["robustness"] * robustness_score
    )
    # Apply uncertainty penalty multiplicatively.
    penalized = blended * (1.0 - interpretation_uncertainty_penalty)
    interpretation_confidence = round(clip01(penalized) * 100.0, 2)

    if interpretation_confidence < 40:
        confidence_band = "Low"
    elif interpretation_confidence < 70:
        confidence_band = "Moderate"
    else:
        confidence_band = "High"

    # ---------------------------------------------------------------
    # PART 10 — Evidence for / against (generated from results)
    # ---------------------------------------------------------------
    supporting = []
    limiting = []

    if temporal_persistence_score >= 0.6:
        supporting.append(
            f"Deviation is sustained: {temporal_persistence_score*100:.0f}% of "
            f"post-change days stayed elevated above the baseline-derived threshold."
        )
    else:
        limiting.append(
            "Elevation after the change point is not strongly sustained."
        )

    if signal_agreement_score >= 0.5:
        supporting.append(
            f"Multiple signals agree: average signal agreement after the change "
            f"point was {signal_agreement_score:.2f}."
        )
    else:
        limiting.append(
            "Relatively few signals jointly deviated after the change point."
        )

    if deviation_strength >= 0.5:
        supporting.append(
            "Post-change temporal scores separate clearly from the baseline period."
        )
    else:
        limiting.append(
            "Separation between baseline and post-change scores is modest."
        )

    if max_change_day_shift is not None and max_change_day_shift <= 1:
        supporting.append(
            f"Change point is robust: it moved at most {max_change_day_shift} day "
            f"under +/-10% threshold and stricter-persistence tests."
        )
    elif max_change_day_shift is not None:
        limiting.append(
            f"Change point shifts up to {max_change_day_shift} days under "
            f"sensitivity analysis."
        )

    if data_completeness_score >= 0.99:
        supporting.append("Sensor data is complete (no missing physiological values).")
    else:
        limiting.append(
            f"Sensor data completeness is {data_completeness_score*100:.1f}%."
        )

    if relationship_consistency_score >= 0.6:
        supporting.append(
            f"Signal relationships are consistent (score "
            f"{relationship_consistency_score:.2f})."
        )

    if normalized_uncertainty >= 0.8:
        limiting.append(
            "Competing hypothesis groups remain similar in support "
            f"(normalized interpretation uncertainty {normalized_uncertainty:.2f})."
        )

    top_missing = missing_summary.get("most_valuable_missing_information", {})
    if top_missing:
        limiting.append(
            f"Contextual information is missing; the most valuable would be "
            f"'{top_missing.get('variable')}'."
        )

    what_would_increase_confidence = []
    if top_missing:
        what_would_increase_confidence.append(
            f"Collect '{top_missing.get('variable')}' to reduce interpretation "
            f"ambiguity between hypothesis groups."
        )
    if normalized_uncertainty >= 0.6:
        what_would_increase_confidence.append(
            "Evidence that more clearly separates one hypothesis group from the "
            "others would lower interpretation uncertainty."
        )
    what_would_increase_confidence.append(
        "A longer observation window would further test whether the pattern persists."
    )

    # ---------------------------------------------------------------
    # Assemble output
    # ---------------------------------------------------------------
    disclaimer = (
        "TRACE confidence reflects the consistency and robustness of the "
        "available data and analytical interpretation. It is not diagnostic "
        "confidence, clinical certainty, or probability of disease."
    )

    output = {
        "patient_id": PATIENT_ID,
        "detected_change_day": detected_change_day,
        "component_scores": components,
        "interpretation_uncertainty_penalty": round(
            interpretation_uncertainty_penalty, 4
        ),
        "interpretation_confidence": interpretation_confidence,
        "confidence_band": confidence_band,
        "sensitivity_analysis": {
            "original_change_day": detected_change_day,
            "alternative_change_days": alternative_change_days,
            "max_change_day_shift": max_change_day_shift,
        },
        "evidence_supporting_interpretation": supporting,
        "evidence_limiting_interpretation": limiting,
        "what_would_increase_confidence": what_would_increase_confidence,
        "weights_used": WEIGHTS,
        "disclaimer": disclaimer,
    }

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    with open(SELF_CHECK_PATH, "w") as f:
        json.dump(output, f, indent=2)

    # ---------------------------------------------------------------
    # PRINT
    # ---------------------------------------------------------------
    print("=" * 66)
    print("TRACE Feature 5 — Can We Trust This? / AI Self-Check")
    print("=" * 66)
    print(f"Detected change day: Day {detected_change_day}")

    print("\n1. Component scores (0-1):")
    for k, v in components.items():
        print(f"   {k:<28} {v:.4f}")

    print(f"\n2. Interpretation uncertainty penalty: "
          f"{interpretation_uncertainty_penalty:.4f} "
          f"(normalized entropy {normalized_uncertainty:.3f})")

    print("\n3. Sensitivity-analysis change days:")
    for name, d in alternative_change_days.items():
        d_str = f"Day {d}" if d is not None else "none"
        print(f"   {name:<24} -> {d_str}")
    print(f"   max change-day shift: {max_change_day_shift}")

    print(f"\n4. Overall interpretation confidence: "
          f"{interpretation_confidence:.2f} / 100")
    print(f"5. Confidence band: {confidence_band}")

    print("\n6. Evidence supporting the interpretation:")
    for e in supporting:
        print(f"   + {e}")

    print("\n7. Evidence limiting the interpretation:")
    for e in limiting:
        print(f"   - {e}")

    print(f"\nSaved self-check summary JSON : {SELF_CHECK_PATH}")


if __name__ == "__main__":
    main()
