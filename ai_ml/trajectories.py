"""
TRACE — Temporal Reasoning & Analysis for Clinical Exploration
Feature 7: "Where Could the Path Diverge?" / HealthFork

Generates three EXPLORATORY 7-day physiological trajectories from the patient's
current measured state, scores each simulated day with the same RMS baseline-
deviation concept from Feature 1, and identifies where/why the scenarios fork.

These are simulations for understanding model behavior under different
mathematical assumptions. They are NOT medical forecasts, NOT disease
predictions, NOT treatment recommendations, and are NOT probabilities. No
scenario is more or less likely than another here.
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
HORIZON = 7                 # simulate Day 31..37
TREND_WINDOW = 6           # use latest ~5-7 days for slope estimation
SEED = 42

# Divergence separation criterion (TRACE prototype):
# a "meaningful" spread = scenario score spread >= this many deviation units.
DIVERGENCE_SPREAD_CRITERION = 0.5

# Scenario shaping constants (transparent, deterministic).
RECOVERY_FRACTION = 0.6    # fraction of the gap to baseline closed by end of horizon
DIVERGENCE_DAMPEN = 0.6    # dampening applied to extrapolated recent slope
# Physically sensible clip bounds per feature (transparent limits).
CLIP_BOUNDS = {
    "sleep_hours": (3.0, 11.0),
    "hrv_ms": (20.0, 120.0),
    "resting_hr_bpm": (40.0, 120.0),
    "steps": (0.0, 30000.0),
    "temperature_f": (96.0, 102.0),
    "respiratory_rate": (8.0, 30.0),
    "eda": (0.1, 25.0),
    "fatigue_score": (0.0, 10.0),
    "stress_score": (0.0, 10.0),
}

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.normpath(os.path.join(HERE, "..", "data", "synthetic"))
OUTPUTS_DIR = os.path.normpath(os.path.join(HERE, "..", "outputs"))

DATA_PATH = os.path.join(DATA_DIR, "patient_001.csv")
BASELINE_SUMMARY_PATH = os.path.join(OUTPUTS_DIR, "baseline_summary.json")
CHANGE_SUMMARY_PATH = os.path.join(OUTPUTS_DIR, "change_point_summary.json")
COUNTERFACTUAL_PATH = os.path.join(OUTPUTS_DIR, "counterfactual_summary.json")
SELF_CHECK_PATH = os.path.join(OUTPUTS_DIR, "self_check_summary.json")
TRAJECTORY_PATH = os.path.join(OUTPUTS_DIR, "trajectory_summary.json")


def load_json(path):
    with open(path) as f:
        return json.load(f)


def deviation_score(values, means, stds):
    """RMS of per-feature z-scores (identical concept to Feature 1)."""
    zs = []
    for feat in FEATURES:
        std = stds[feat]
        if std is None or std == 0 or np.isnan(std):
            zs.append(0.0)
        else:
            zs.append((values[feat] - means[feat]) / std)
    return float(np.sqrt(np.mean(np.asarray(zs, dtype=float) ** 2)))


def clip_feature(feat, value):
    lo, hi = CLIP_BOUNDS[feat]
    return float(np.clip(value, lo, hi))


def main():
    rng = np.random.default_rng(SEED)

    # ---------------------------------------------------------------
    # PART 1 — Load existing TRACE results
    # ---------------------------------------------------------------
    df = pd.read_csv(DATA_PATH)
    baseline_summary = load_json(BASELINE_SUMMARY_PATH)
    change_summary = load_json(CHANGE_SUMMARY_PATH)
    counterfactual_summary = load_json(COUNTERFACTUAL_PATH)
    self_check_summary = load_json(SELF_CHECK_PATH)

    detected_change_day = int(change_summary["detected_change_day"])

    baseline_stats = baseline_summary["baseline_statistics"]
    means = {feat: float(baseline_stats[feat]["mean"]) for feat in FEATURES}
    stds = {feat: float(baseline_stats[feat]["std"]) for feat in FEATURES}

    latest_row = df.iloc[-1]
    observed_through_day = int(latest_row["day"])
    current_state = {feat: float(latest_row[feat]) for feat in FEATURES}
    starting_deviation = deviation_score(current_state, means, stds)

    # ---------------------------------------------------------------
    # PART 3 — Data-driven recent trend (slope per feature)
    # ---------------------------------------------------------------
    recent = df.tail(TREND_WINDOW)
    x = recent["day"].to_numpy(dtype=float)
    slopes = {}
    for feat in FEATURES:
        y = recent[feat].to_numpy(dtype=float)
        # Simple least-squares slope (per-day change).
        slope = float(np.polyfit(x, y, 1)[0]) if len(x) >= 2 else 0.0
        slopes[feat] = slope

    sim_days = [observed_through_day + k for k in range(1, HORIZON + 1)]
    sim_dates = [
        str((pd.to_datetime(latest_row["date"]) + pd.Timedelta(days=k)).date())
        for k in range(1, HORIZON + 1)
    ]

    # ---------------------------------------------------------------
    # Build the three scenarios (Parts 4, 5, 6)
    # Each returns a list of per-day dicts with feature values + score.
    # ---------------------------------------------------------------
    def build_recovery():
        """Smoothly interpolate each signal toward its baseline mean."""
        daily = []
        for step in range(1, HORIZON + 1):
            frac = RECOVERY_FRACTION * (step / HORIZON)  # 0 -> RECOVERY_FRACTION
            vals = {}
            for feat in FEATURES:
                target = means[feat]
                moved = current_state[feat] + frac * (target - current_state[feat])
                noise = rng.normal(0, stds[feat] * 0.05)
                vals[feat] = clip_feature(feat, moved + noise)
            daily.append(vals)
        return daily

    def build_persistent():
        """Hold near the latest value with small baseline-scaled variation."""
        daily = []
        for step in range(1, HORIZON + 1):
            vals = {}
            for feat in FEATURES:
                noise = rng.normal(0, stds[feat] * 0.15)
                vals[feat] = clip_feature(feat, current_state[feat] + noise)
            daily.append(vals)
        return daily

    def build_divergence():
        """Extend the dampened recent slope conservatively, with clipping."""
        daily = []
        for step in range(1, HORIZON + 1):
            vals = {}
            for feat in FEATURES:
                extended = current_state[feat] + DIVERGENCE_DAMPEN * slopes[feat] * step
                noise = rng.normal(0, stds[feat] * 0.08)
                vals[feat] = clip_feature(feat, extended + noise)
            daily.append(vals)
        return daily

    scenario_builders = {
        "Recovery toward baseline": build_recovery,
        "Persistent deviation": build_persistent,
        "Continued divergence": build_divergence,
    }
    scenario_descriptions = {
        "Recovery toward baseline": (
            "Signals gradually move toward the patient's personal baseline over "
            "the 7 simulated days."
        ),
        "Persistent deviation": (
            "Signals remain near their current values with small deterministic "
            "variation and no strong directional trend."
        ),
        "Continued divergence": (
            "Signals extend their recent observed trend, dampened and clipped to "
            "avoid exaggerated change."
        ),
    }

    # ---------------------------------------------------------------
    # PART 7 — Score each simulated day in each scenario
    # ---------------------------------------------------------------
    scenario_daily_vals = {}   # name -> list of feature-dicts
    scenario_scores = {}       # name -> list of scores
    for name, build in scenario_builders.items():
        daily_vals = build()
        scores = [deviation_score(v, means, stds) for v in daily_vals]
        scenario_daily_vals[name] = daily_vals
        scenario_scores[name] = scores

    # ---------------------------------------------------------------
    # PART 8 — Divergence point (earliest meaningfully separated day)
    # ---------------------------------------------------------------
    names = list(scenario_builders.keys())
    divergence_day = None
    divergence_date = None
    divergence_spread = None
    for i in range(HORIZON):
        day_scores = [scenario_scores[n][i] for n in names]
        spread = max(day_scores) - min(day_scores)
        if spread >= DIVERGENCE_SPREAD_CRITERION:
            divergence_day = sim_days[i]
            divergence_date = sim_dates[i]
            divergence_spread = spread
            break
    # Fallback: if never meets criterion, use the day of maximum spread.
    if divergence_day is None:
        spreads = [
            max(scenario_scores[n][i] for n in names)
            - min(scenario_scores[n][i] for n in names)
            for i in range(HORIZON)
        ]
        i = int(np.argmax(spreads))
        divergence_day = sim_days[i]
        divergence_date = sim_dates[i]
        divergence_spread = spreads[i]

    div_index = sim_days.index(divergence_day)

    # ---------------------------------------------------------------
    # PART 9 — Fork drivers at the divergence day
    # Standardize cross-scenario spread of each feature by baseline std.
    # ---------------------------------------------------------------
    driver_scores = {}
    for feat in FEATURES:
        feat_vals = [scenario_daily_vals[n][div_index][feat] for n in names]
        raw_spread = max(feat_vals) - min(feat_vals)
        std = stds[feat]
        z_spread = raw_spread / std if std and not np.isnan(std) else 0.0
        driver_scores[feat] = z_spread
    ranked_drivers = sorted(driver_scores.items(), key=lambda kv: kv[1], reverse=True)
    fork_drivers = [
        {"feature": feat, "standardized_separation": round(val, 4)}
        for feat, val in ranked_drivers[:3]
    ]

    # ---------------------------------------------------------------
    # PART 10 — Scenario summaries
    # ---------------------------------------------------------------
    def trajectory_direction(start, end):
        delta = end - start
        # Threshold scaled to the starting score so "stable" is meaningful.
        tol = max(0.5, 0.05 * abs(start))
        if delta < -tol:
            return "toward baseline"
        if delta > tol:
            return "away from baseline"
        return "approximately stable"

    scenarios_out = []
    for name in names:
        scores = scenario_scores[name]
        start_score = starting_deviation  # all scenarios start from current state
        end_score = scores[-1]
        daily_values = []
        for i in range(HORIZON):
            entry = {
                "day": sim_days[i],
                "date": sim_dates[i],
                "deviation_score": round(scores[i], 4),
            }
            for feat in FEATURES:
                entry[feat] = round(scenario_daily_vals[name][i][feat], 4)
            daily_values.append(entry)

        scenarios_out.append(
            {
                "scenario_name": name,
                "description": scenario_descriptions[name],
                "starting_deviation_score": round(start_score, 4),
                "ending_deviation_score": round(end_score, 4),
                "change_in_deviation": round(end_score - start_score, 4),
                "trajectory_direction": trajectory_direction(start_score, end_score),
                "daily_values": daily_values,
            }
        )

    # ---------------------------------------------------------------
    # Confidence context + explanation
    # ---------------------------------------------------------------
    interpretation_confidence_context = {
        "interpretation_confidence": self_check_summary.get(
            "interpretation_confidence"
        ),
        "confidence_band": self_check_summary.get("confidence_band"),
        "note": (
            "Interpretation confidence is carried over from the AI Self-Check "
            "feature and is not recalculated here. Trajectories are exploratory "
            "simulations, not probabilistic forecasts."
        ),
    }

    driver_names = ", ".join(d["feature"] for d in fork_drivers)
    explanation = (
        f"From the patient's state observed through Day {observed_through_day} "
        f"(starting deviation {starting_deviation:.3f}), TRACE simulated three "
        f"exploratory 7-day paths. The scenarios become meaningfully separated "
        f"around Day {divergence_day} ({divergence_date}), where the deviation-"
        f"score spread reaches {divergence_spread:.3f}. The features that most "
        f"separate the paths at that point are: {driver_names}. These are "
        f"mathematical what-if paths under different assumptions, not forecasts."
    )

    disclaimer = (
        "HealthFork trajectories are exploratory simulations showing how TRACE's "
        "measured deviation could evolve under different mathematical "
        "assumptions. They are not forecasts of a patient's health, disease "
        "progression, or treatment outcomes."
    )

    output = {
        "patient_id": PATIENT_ID,
        "observed_through_day": observed_through_day,
        "simulation_horizon": f"Day {sim_days[0]}-{sim_days[-1]}",
        "detected_change_day": detected_change_day,
        "starting_deviation_score": round(starting_deviation, 4),
        "recent_slopes": {f: round(s, 4) for f, s in slopes.items()},
        "scenarios": scenarios_out,
        "divergence": {
            "divergence_day": divergence_day,
            "divergence_date": divergence_date,
            "scenario_score_spread": round(float(divergence_spread), 4),
            "separation_criterion": DIVERGENCE_SPREAD_CRITERION,
            "fork_drivers": fork_drivers,
        },
        "interpretation_confidence_context": interpretation_confidence_context,
        "explanation": explanation,
        "disclaimer": disclaimer,
    }

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    with open(TRAJECTORY_PATH, "w") as f:
        json.dump(output, f, indent=2)

    # ---------------------------------------------------------------
    # PRINT
    # ---------------------------------------------------------------
    print("=" * 68)
    print("TRACE Feature 7 — Where Could the Path Diverge? / HealthFork")
    print("=" * 68)
    print(f"Observed through Day {observed_through_day}  |  "
          f"horizon Day {sim_days[0]}-{sim_days[-1]}")

    print("\n1. Recent slope per signal (per-day, from last "
          f"{TREND_WINDOW} days):")
    for feat in FEATURES:
        print(f"   {feat:<20} {slopes[feat]:+.4f}")

    print(f"\n2. Starting deviation score: {starting_deviation:.4f}")

    print("\n3. Daily deviation scores by scenario:")
    header = "   Day   " + "".join(f"{n[:22]:<24}" for n in names)
    print(header)
    for i in range(HORIZON):
        row = f"   {sim_days[i]:<6}"
        for n in names:
            row += f"{scenario_scores[n][i]:<24.4f}"
        print(row)

    print(f"\n4. Detected divergence day: Day {divergence_day} ({divergence_date})")
    print(f"5. Scenario score spread at divergence: {divergence_spread:.4f} "
          f"(criterion {DIVERGENCE_SPREAD_CRITERION})")

    print("\n6. Top 3 fork drivers:")
    for i, d in enumerate(fork_drivers, start=1):
        print(f"   {i}. {d['feature']:<20} "
              f"standardized separation = {d['standardized_separation']:.4f}")

    print("\n7. Ending deviation score per scenario:")
    for s in scenarios_out:
        print(f"   {s['scenario_name']:<26} "
              f"end={s['ending_deviation_score']:.4f} "
              f"(Δ={s['change_in_deviation']:+.4f}, {s['trajectory_direction']})")

    print(f"\nSaved trajectory summary JSON : {TRAJECTORY_PATH}")


if __name__ == "__main__":
    main()
