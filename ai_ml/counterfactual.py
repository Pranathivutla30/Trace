"""
TRACE — Temporal Reasoning & Analysis for Clinical Exploration
Feature 6: "What If?" / Counterfactual Patient

Explores how TRACE's multivariate deviation score would change if ONE (or a few)
measured signals had instead stayed near the patient's personal baseline, while
every other measured signal is left unchanged.

This is exploratory mathematical sensitivity analysis of the deviation score.
It is NOT treatment simulation, NOT medical advice, and NOT a prediction of what
would actually happen to the patient. Normalizing a signal here does not cure,
prevent, or treat anything — it only re-evaluates a formula.
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

PATIENT_ID = "patient_001"

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.normpath(os.path.join(HERE, "..", "data", "synthetic"))
OUTPUTS_DIR = os.path.normpath(os.path.join(HERE, "..", "outputs"))

DATA_PATH = os.path.join(DATA_DIR, "patient_001.csv")
BASELINE_SUMMARY_PATH = os.path.join(OUTPUTS_DIR, "baseline_summary.json")
CHANGE_SUMMARY_PATH = os.path.join(OUTPUTS_DIR, "change_point_summary.json")
SELF_CHECK_PATH = os.path.join(OUTPUTS_DIR, "self_check_summary.json")
COUNTERFACTUAL_PATH = os.path.join(OUTPUTS_DIR, "counterfactual_summary.json")


def load_json(path):
    with open(path) as f:
        return json.load(f)


def deviation_score(values, means, stds):
    """Multivariate deviation = RMS of per-feature z-scores (matches Feature 1).

    `values`, `means`, `stds` are dicts keyed by feature.
    """
    zs = []
    for feat in FEATURES:
        std = stds[feat]
        if std is None or std == 0 or np.isnan(std):
            zs.append(0.0)
        else:
            zs.append((values[feat] - means[feat]) / std)
    zs = np.asarray(zs, dtype=float)
    return float(np.sqrt(np.mean(zs ** 2)))


def main():
    # ---------------------------------------------------------------
    # PART 1 — Load data and baseline
    # ---------------------------------------------------------------
    df = pd.read_csv(DATA_PATH)
    baseline_summary = load_json(BASELINE_SUMMARY_PATH)
    change_summary = load_json(CHANGE_SUMMARY_PATH)
    self_check_summary = load_json(SELF_CHECK_PATH)

    detected_change_day = int(change_summary["detected_change_day"])

    # Personal baseline statistics from Feature 1.
    baseline_stats = baseline_summary["baseline_statistics"]
    means = {feat: float(baseline_stats[feat]["mean"]) for feat in FEATURES}
    stds = {feat: float(baseline_stats[feat]["std"]) for feat in FEATURES}

    # ---------------------------------------------------------------
    # PART 2 — Current patient state (latest available day)
    # ---------------------------------------------------------------
    latest_row = df.iloc[-1]
    current_day = int(latest_row["day"])
    current_state = {feat: float(latest_row[feat]) for feat in FEATURES}

    original_deviation_score = deviation_score(current_state, means, stds)

    # ---------------------------------------------------------------
    # PART 3 & 4 — Single-signal counterfactuals + interpretation
    # ---------------------------------------------------------------
    single_counterfactuals = []
    for feat in FEATURES:
        cf_state = dict(current_state)
        cf_state[feat] = means[feat]  # hold this signal at personal baseline mean
        cf_score = deviation_score(cf_state, means, stds)

        absolute_reduction = original_deviation_score - cf_score
        percentage_reduction = (
            absolute_reduction / original_deviation_score * 100.0
            if original_deviation_score > 0 else 0.0
        )

        single_counterfactuals.append(
            {
                "feature": feat,
                "original_value": round(current_state[feat], 4),
                "baseline_value": round(means[feat], 4),
                "counterfactual_value": round(means[feat], 4),
                "original_deviation_score": round(original_deviation_score, 4),
                "counterfactual_deviation_score": round(cf_score, 4),
                "absolute_reduction": round(absolute_reduction, 4),
                "percentage_reduction": round(percentage_reduction, 2),
                # interpretation filled after ranking (uses its own %)
            }
        )

    # Rank by percentage reduction (desc). Ranking from calculation only.
    single_counterfactuals.sort(
        key=lambda d: d["percentage_reduction"], reverse=True
    )
    for rank, cf in enumerate(single_counterfactuals, start=1):
        cf["rank"] = rank
        cf["interpretation"] = (
            f"If {cf['feature']} had remained near this patient's personal "
            f"baseline while all other measured signals stayed unchanged, the "
            f"overall physiological deviation score would decrease by "
            f"{cf['percentage_reduction']:.2f}% "
            f"(from {original_deviation_score:.4f} to "
            f"{cf['counterfactual_deviation_score']:.4f}). This describes "
            f"mathematical sensitivity of the score, not a health outcome."
        )

    # ---------------------------------------------------------------
    # PART 5 — Most influential single counterfactual
    # ---------------------------------------------------------------
    top = single_counterfactuals[0]
    most_influential = {
        "feature": top["feature"],
        "original_value": top["original_value"],
        "baseline_value": top["baseline_value"],
        "counterfactual_value": top["counterfactual_value"],
        "original_deviation_score": top["original_deviation_score"],
        "counterfactual_deviation_score": top["counterfactual_deviation_score"],
        "absolute_reduction": top["absolute_reduction"],
        "percentage_reduction": top["percentage_reduction"],
        "interpretation": top["interpretation"],
    }

    # ---------------------------------------------------------------
    # PART 6 — Combined top-3 counterfactual
    # ---------------------------------------------------------------
    top3 = [cf["feature"] for cf in single_counterfactuals[:3]]
    combined_state = dict(current_state)
    for feat in top3:
        combined_state[feat] = means[feat]
    combined_score = deviation_score(combined_state, means, stds)
    combined_abs = original_deviation_score - combined_score
    combined_pct = (
        combined_abs / original_deviation_score * 100.0
        if original_deviation_score > 0 else 0.0
    )

    combined_counterfactual = {
        "features_normalized": top3,
        "original_deviation_score": round(original_deviation_score, 4),
        "counterfactual_deviation_score": round(combined_score, 4),
        "absolute_reduction": round(combined_abs, 4),
        "percentage_reduction": round(combined_pct, 2),
        "interpretation": (
            f"If the three most influential measured signals "
            f"({', '.join(top3)}) had simultaneously remained near this "
            f"patient's personal baseline, the overall deviation score would "
            f"decrease by {combined_pct:.2f}% (from "
            f"{original_deviation_score:.4f} to {combined_score:.4f}). TRACE can "
            f"explore signal combinations, not only one variable at a time. This "
            f"is mathematical sensitivity, not a clinical prediction."
        ),
    }

    # ---------------------------------------------------------------
    # PART 7 — Counterfactual confidence context (read-only)
    # ---------------------------------------------------------------
    interpretation_confidence = self_check_summary.get("interpretation_confidence")
    confidence_band = self_check_summary.get("confidence_band")
    interpretation_confidence_context = {
        "interpretation_confidence": interpretation_confidence,
        "confidence_band": confidence_band,
        "note": (
            "Interpretation confidence is carried over from the AI Self-Check "
            "feature and is NOT recalculated here. Counterfactual results describe "
            "the mathematical sensitivity of TRACE's deviation score to the "
            "measured signals, not diagnostic confidence or clinical outcomes."
        ),
    }

    # ---------------------------------------------------------------
    # Assemble output
    # ---------------------------------------------------------------
    disclaimer = (
        "Counterfactual results show mathematical sensitivity of TRACE's "
        "deviation score to measured signals. They do not predict clinical "
        "outcomes or represent treatment recommendations."
    )

    output = {
        "patient_id": PATIENT_ID,
        "current_day": current_day,
        "detected_change_day": detected_change_day,
        "original_deviation_score": round(original_deviation_score, 4),
        "single_signal_counterfactuals": single_counterfactuals,
        "most_influential_counterfactual": most_influential,
        "combined_counterfactual": combined_counterfactual,
        "interpretation_confidence_context": interpretation_confidence_context,
        "disclaimer": disclaimer,
    }

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    with open(COUNTERFACTUAL_PATH, "w") as f:
        json.dump(output, f, indent=2)

    # ---------------------------------------------------------------
    # PRINT
    # ---------------------------------------------------------------
    print("=" * 68)
    print("TRACE Feature 6 — What If? / Counterfactual Patient")
    print("=" * 68)

    print(f"\n1. Current day: Day {current_day} "
          f"(detected change point: Day {detected_change_day})")
    print(f"2. Original multivariate deviation score: "
          f"{original_deviation_score:.4f}")

    print("\n3-5. Single-signal counterfactual ranking:")
    print(f"   {'rank':<5}{'feature':<20}{'cf_score':<12}"
          f"{'abs_red':<12}{'pct_red'}")
    for cf in single_counterfactuals:
        print(
            f"   {cf['rank']:<5}{cf['feature']:<20}"
            f"{cf['counterfactual_deviation_score']:<12.4f}"
            f"{cf['absolute_reduction']:<12.4f}"
            f"{cf['percentage_reduction']:.2f}%"
        )

    print("\n6. Most influential counterfactual:")
    print(f"   feature              : {most_influential['feature']}")
    print(f"   original_value       : {most_influential['original_value']}")
    print(f"   baseline_value       : {most_influential['baseline_value']}")
    print(f"   counterfactual_score : "
          f"{most_influential['counterfactual_deviation_score']:.4f}")
    print(f"   percentage_reduction : "
          f"{most_influential['percentage_reduction']:.2f}%")

    print("\n7. Combined top-3 counterfactual:")
    print(f"   features_normalized  : {', '.join(top3)}")
    print(f"   counterfactual_score : "
          f"{combined_counterfactual['counterfactual_deviation_score']:.4f}")
    print(f"   absolute_reduction   : "
          f"{combined_counterfactual['absolute_reduction']:.4f}")
    print(f"   percentage_reduction : "
          f"{combined_counterfactual['percentage_reduction']:.2f}%")

    print(f"\n   (interpretation confidence context: "
          f"{interpretation_confidence} / {confidence_band})")
    print(f"\nSaved counterfactual summary JSON : {COUNTERFACTUAL_PATH}")


if __name__ == "__main__":
    main()
