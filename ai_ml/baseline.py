"""
TRACE — Temporal Reasoning & Analysis for Clinical Exploration
Feature 1: "Your Baseline" / BioShadow

Learns a patient's PERSONAL physiological baseline from Days 1-14 and measures
how far each later day drifts from that personal baseline.

The output is a relative, multivariate "distance from your own normal" signal.
It is NOT a diagnosis, NOT a disease prediction, and the interpretation bands
below are TRACE demo bands, not medical thresholds.
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

BASELINE_DAYS = 14  # Days 1-14 form the stable baseline period
PATIENT_ID = "patient_001"

HERE = os.path.dirname(__file__)
DATA_PATH = os.path.normpath(
    os.path.join(HERE, "..", "data", "synthetic", "patient_001.csv")
)
ANALYSIS_PATH = os.path.normpath(
    os.path.join(HERE, "..", "data", "synthetic", "patient_001_baseline_analysis.csv")
)
OUTPUTS_DIR = os.path.normpath(os.path.join(HERE, "..", "outputs"))
SUMMARY_PATH = os.path.join(OUTPUTS_DIR, "baseline_summary.json")


def interpret(score):
    """Map a deviation score to a TRACE demo interpretation band."""
    if score < 1.0:
        return "Within personal baseline"
    if score < 2.0:
        return "Mild deviation"
    if score < 3.0:
        return "Moderate deviation"
    return "Strong deviation"


def main():
    # 1. Load the existing dataset (do not modify or regenerate it).
    df = pd.read_csv(DATA_PATH)

    # 2. Baseline period = Days 1-14.
    baseline_df = df[df["day"] <= BASELINE_DAYS]

    # 3. Baseline mean and standard deviation per feature.
    #    Use sample std (ddof=1) so it reflects day-to-day baseline spread.
    baseline_mean = baseline_df[FEATURES].mean()
    baseline_std = baseline_df[FEATURES].std(ddof=1)

    # Guard against a zero-variance feature (avoids divide-by-zero).
    safe_std = baseline_std.replace(0, np.nan)

    # 4. Per-day, per-feature z-score relative to the patient's own baseline.
    z_scores = (df[FEATURES] - baseline_mean) / safe_std
    z_scores = z_scores.fillna(0.0)  # a flat baseline feature contributes 0

    # 5. Single multivariate deviation score = RMS of the feature z-scores.
    deviation_score = np.sqrt((z_scores ** 2).mean(axis=1))

    # 6. Interpretation band per day.
    status = deviation_score.apply(interpret)

    # 7. Top 3 contributing features per day (by absolute z-score magnitude).
    abs_z = z_scores.abs()
    top_contributors = abs_z.apply(
        lambda row: list(row.sort_values(ascending=False).index[:3]), axis=1
    )

    # Assemble the per-day analysis table.
    analysis = pd.DataFrame(
        {
            "date": df["date"],
            "day": df["day"],
            "baseline_deviation_score": deviation_score.round(4),
            "baseline_status": status,
            "top_contributor_1": [c[0] for c in top_contributors],
            "top_contributor_2": [c[1] for c in top_contributors],
            "top_contributor_3": [c[2] for c in top_contributors],
        }
    )

    # 8a. Save per-day analysis CSV.
    analysis.to_csv(ANALYSIS_PATH, index=False)

    # 8b. Save summary JSON.
    latest = analysis.iloc[-1]
    baseline_stats = {
        feat: {
            "mean": round(float(baseline_mean[feat]), 4),
            "std": round(float(baseline_std[feat]), 4),
        }
        for feat in FEATURES
    }
    summary = {
        "patient_id": PATIENT_ID,
        "baseline_period": f"Days 1-{BASELINE_DAYS}",
        "baseline_statistics": baseline_stats,
        "latest_day": int(latest["day"]),
        "latest_deviation_score": float(latest["baseline_deviation_score"]),
        "latest_status": latest["baseline_status"],
        "latest_top_contributors": [
            latest["top_contributor_1"],
            latest["top_contributor_2"],
            latest["top_contributor_3"],
        ],
    }
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    # 9. Reporting.
    print("=" * 60)
    print("TRACE Feature 1 — Your Baseline / BioShadow")
    print(f"Patient: {PATIENT_ID}   Baseline period: Days 1-{BASELINE_DAYS}")
    print("=" * 60)

    print("\nBaseline means (Days 1-14):")
    for feat in FEATURES:
        print(f"  {feat:<20} {baseline_mean[feat]:.4f}")

    print("\nBaseline standard deviations (Days 1-14):")
    for feat in FEATURES:
        print(f"  {feat:<20} {baseline_std[feat]:.4f}")

    print("\nDeviation scores — Days 1-5:")
    for _, r in analysis[analysis["day"] <= 5].iterrows():
        print(
            f"  Day {int(r['day']):>2}  "
            f"score={r['baseline_deviation_score']:.4f}  "
            f"[{r['baseline_status']}]"
        )

    print("\nDeviation scores — Days 15-30:")
    for _, r in analysis[analysis["day"] >= 15].iterrows():
        print(
            f"  Day {int(r['day']):>2}  "
            f"score={r['baseline_deviation_score']:.4f}  "
            f"[{r['baseline_status']}]"
        )

    print(f"\nLatest day (Day {summary['latest_day']}) top contributors:")
    for i, c in enumerate(summary["latest_top_contributors"], start=1):
        day_idx = latest["day"] - 1
        zval = z_scores.iloc[int(day_idx)][c]
        print(f"  {i}. {c:<20} z={zval:+.2f}")

    print(f"\nSaved analysis CSV : {ANALYSIS_PATH}")
    print(f"Saved summary JSON : {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
