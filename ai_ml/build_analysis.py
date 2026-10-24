"""
TRACE — Temporal Reasoning & Analysis for Clinical Exploration
Aggregator: build_analysis.py

Combines the outputs of all seven TRACE features into ONE standardized JSON
file (outputs/patient_001_analysis.json) that a FastAPI backend and React
frontend can consume directly.

This module only READS existing feature outputs and the CSVs. It does not
recalculate any feature, does not modify the dataset, and does not change any
previous output file. It is presentation/assembly only — not diagnosis.
"""

import json
import os

import pandas as pd

PATIENT_ID = "001"

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.normpath(os.path.join(HERE, "..", "data", "synthetic"))
OUTPUTS_DIR = os.path.normpath(os.path.join(HERE, "..", "outputs"))

# Inputs
BASELINE_SUMMARY = os.path.join(OUTPUTS_DIR, "baseline_summary.json")
CHANGE_SUMMARY = os.path.join(OUTPUTS_DIR, "change_point_summary.json")
RELATIONSHIP_SUMMARY = os.path.join(OUTPUTS_DIR, "relationship_summary.json")
MISSING_SUMMARY = os.path.join(OUTPUTS_DIR, "missing_information_summary.json")
SELF_CHECK_SUMMARY = os.path.join(OUTPUTS_DIR, "self_check_summary.json")
COUNTERFACTUAL_SUMMARY = os.path.join(OUTPUTS_DIR, "counterfactual_summary.json")
TRAJECTORY_SUMMARY = os.path.join(OUTPUTS_DIR, "trajectory_summary.json")

PATIENT_CSV = os.path.join(DATA_DIR, "patient_001.csv")
BASELINE_CSV = os.path.join(DATA_DIR, "patient_001_baseline_analysis.csv")
CHANGE_CSV = os.path.join(DATA_DIR, "patient_001_change_analysis.csv")

# Output
ANALYSIS_PATH = os.path.join(OUTPUTS_DIR, "patient_001_analysis.json")

SENSOR_FEATURES = [
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


def load_json(path):
    with open(path) as f:
        return json.load(f)


def main():
    # ---------------------------------------------------------------
    # Load every feature output
    # ---------------------------------------------------------------
    baseline = load_json(BASELINE_SUMMARY)
    change = load_json(CHANGE_SUMMARY)
    relationships = load_json(RELATIONSHIP_SUMMARY)
    missing = load_json(MISSING_SUMMARY)
    self_check = load_json(SELF_CHECK_SUMMARY)
    counterfactual = load_json(COUNTERFACTUAL_SUMMARY)
    trajectories = load_json(TRAJECTORY_SUMMARY)

    patient_df = pd.read_csv(PATIENT_CSV)
    baseline_df = pd.read_csv(BASELINE_CSV)
    change_df = pd.read_csv(CHANGE_CSV)

    # ---------------------------------------------------------------
    # PATIENT
    # ---------------------------------------------------------------
    observed_days = int(len(patient_df))
    patient = {
        "patient_id": PATIENT_ID,
        "display_name": "Synthetic Demo Patient",
        "observed_days": observed_days,
    }

    # ---------------------------------------------------------------
    # DATA SOURCE
    # ---------------------------------------------------------------
    data_source = {
        "type": "synthetic_demo",
        "label": "Synthetic longitudinal demonstration patient",
        "is_real_patient_data": False,
    }

    # ---------------------------------------------------------------
    # TIMELINE (merge CSVs by day)
    # ---------------------------------------------------------------
    baseline_by_day = baseline_df.set_index("day").to_dict("index")
    change_by_day = change_df.set_index("day").to_dict("index")

    timeline = []
    for _, row in patient_df.iterrows():
        day = int(row["day"])
        b = baseline_by_day.get(day, {})
        c = change_by_day.get(day, {})
        entry = {
            "date": str(row["date"]),
            "day": day,
            "sleep_hours": float(row["sleep_hours"]),
            "hrv_ms": float(row["hrv_ms"]),
            "resting_hr_bpm": float(row["resting_hr_bpm"]),
            "steps": int(row["steps"]),
            "temperature_f": float(row["temperature_f"]),
            "respiratory_rate": float(row["respiratory_rate"]),
            "eda": float(row["eda"]),
            "fatigue_score": float(row["fatigue_score"]),
            "stress_score": float(row["stress_score"]),
            "baseline_deviation_score": (
                float(b["baseline_deviation_score"])
                if "baseline_deviation_score" in b else None
            ),
            "baseline_status": b.get("baseline_status"),
            "temporal_change_score": (
                float(c["temporal_change_score"])
                if "temporal_change_score" in c else None
            ),
            "signal_agreement": (
                float(c["signal_agreement"]) if "signal_agreement" in c else None
            ),
        }
        timeline.append(entry)

    # ---------------------------------------------------------------
    # BASELINE
    # ---------------------------------------------------------------
    baseline_block = {
        "baseline_period": baseline.get("baseline_period"),
        "baseline_statistics": baseline.get("baseline_statistics"),
        "latest_deviation_score": baseline.get("latest_deviation_score"),
        "latest_status": baseline.get("latest_status"),
        "latest_top_contributors": baseline.get("latest_top_contributors"),
    }

    # ---------------------------------------------------------------
    # CHANGE DETECTION
    # ---------------------------------------------------------------
    change_block = {
        "detected_change_day": change.get("detected_change_day"),
        "detected_change_date": change.get("detected_change_date"),
        "confidence": change.get("confidence"),
        "temporal_change_score_at_detection": change.get(
            "temporal_change_score_at_detection"
        ),
        "signal_onsets": change.get("signal_onsets"),
        "signals_active_at_change_point": change.get(
            "signals_active_at_change_point"
        ),
        "explanation": change.get("explanation"),
    }

    # ---------------------------------------------------------------
    # RELATIONSHIPS
    # ---------------------------------------------------------------
    relationships_block = {
        "ordered_signal_onsets": relationships.get("ordered_signal_onsets"),
        "strong_correlations": relationships.get("strong_correlations"),
        "lagged_relationships": relationships.get("lagged_relationships"),
        "graph": relationships.get("graph"),
        "hypothesis_groups": relationships.get("hypothesis_groups"),
        "disclaimer": relationships.get("disclaimer"),
    }

    # ---------------------------------------------------------------
    # MISSING INFORMATION
    # ---------------------------------------------------------------
    missing_block = {
        "current_uncertainty": missing.get("current_uncertainty"),
        "candidate_information": missing.get("candidate_information"),
        "most_valuable_missing_information": missing.get(
            "most_valuable_missing_information"
        ),
        "disclaimer": missing.get("disclaimer"),
    }

    # ---------------------------------------------------------------
    # SELF CHECK
    # ---------------------------------------------------------------
    self_check_block = {
        "component_scores": self_check.get("component_scores"),
        "interpretation_uncertainty_penalty": self_check.get(
            "interpretation_uncertainty_penalty"
        ),
        "interpretation_confidence": self_check.get("interpretation_confidence"),
        "confidence_band": self_check.get("confidence_band"),
        "sensitivity_analysis": self_check.get("sensitivity_analysis"),
        "evidence_supporting_interpretation": self_check.get(
            "evidence_supporting_interpretation"
        ),
        "evidence_limiting_interpretation": self_check.get(
            "evidence_limiting_interpretation"
        ),
        "what_would_increase_confidence": self_check.get(
            "what_would_increase_confidence"
        ),
        "disclaimer": self_check.get("disclaimer"),
    }

    # ---------------------------------------------------------------
    # COUNTERFACTUAL
    # ---------------------------------------------------------------
    counterfactual_block = {
        "original_deviation_score": counterfactual.get("original_deviation_score"),
        "single_signal_counterfactuals": counterfactual.get(
            "single_signal_counterfactuals"
        ),
        "most_influential_counterfactual": counterfactual.get(
            "most_influential_counterfactual"
        ),
        "combined_counterfactual": counterfactual.get("combined_counterfactual"),
        "interpretation_confidence_context": counterfactual.get(
            "interpretation_confidence_context"
        ),
        "disclaimer": counterfactual.get("disclaimer"),
    }

    # ---------------------------------------------------------------
    # TRAJECTORIES
    # ---------------------------------------------------------------
    trajectories_block = {
        "simulation_horizon": trajectories.get("simulation_horizon"),
        "scenarios": trajectories.get("scenarios"),
        "divergence": trajectories.get("divergence"),
        "interpretation_confidence_context": trajectories.get(
            "interpretation_confidence_context"
        ),
        "explanation": trajectories.get("explanation"),
        "disclaimer": trajectories.get("disclaimer"),
    }

    # ---------------------------------------------------------------
    # DEMO SUMMARY (generated from calculated results)
    # ---------------------------------------------------------------
    detected_change_day = change.get("detected_change_day")
    current_deviation_status = baseline.get("latest_status")
    # Top changed signals: active signals at change point, else latest top contributors.
    top_changed_signals = (
        change.get("signals_active_at_change_point")
        or baseline.get("latest_top_contributors")
        or []
    )
    top_missing = missing.get("most_valuable_missing_information", {})
    most_valuable_missing = top_missing.get("variable")
    interpretation_confidence = self_check.get("interpretation_confidence")
    confidence_band = self_check.get("confidence_band")
    most_influential_cf = counterfactual.get(
        "most_influential_counterfactual", {}
    ).get("feature")
    fork_day = trajectories.get("divergence", {}).get("divergence_day")

    one_sentence_summary = (
        f"TRACE detected a sustained physiological shift around Day "
        f"{detected_change_day}, identified the strongest contributing signals "
        f"({', '.join(top_changed_signals) if top_changed_signals else 'n/a'}), "
        f"highlighted '{most_valuable_missing}' as the most valuable missing "
        f"context, and tested how the interpretation changes under counterfactual "
        f"and trajectory scenarios — with an interpretation confidence of "
        f"{interpretation_confidence} ({confidence_band})."
    )

    demo_summary = {
        "headline": "TRACE found where the story changed.",
        "detected_change_day": detected_change_day,
        "current_deviation_status": current_deviation_status,
        "top_changed_signals": top_changed_signals,
        "most_valuable_missing_information": most_valuable_missing,
        "interpretation_confidence": interpretation_confidence,
        "confidence_band": confidence_band,
        "most_influential_counterfactual": most_influential_cf,
        "trajectory_fork_day": fork_day,
        "one_sentence_summary": one_sentence_summary,
    }

    # ---------------------------------------------------------------
    # Assemble top-level structure
    # ---------------------------------------------------------------
    analysis = {
        "patient": patient,
        "data_source": data_source,
        "timeline": timeline,
        "baseline": baseline_block,
        "change_detection": change_block,
        "relationships": relationships_block,
        "missing_information": missing_block,
        "self_check": self_check_block,
        "counterfactual": counterfactual_block,
        "trajectories": trajectories_block,
        "demo_summary": demo_summary,
    }

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    with open(ANALYSIS_PATH, "w") as f:
        json.dump(analysis, f, indent=2)

    # ---------------------------------------------------------------
    # Validate + print
    # ---------------------------------------------------------------
    with open(ANALYSIS_PATH) as f:
        reparsed = json.load(f)  # 1. validate it parses

    print("=" * 66)
    print("TRACE — Unified Analysis Build")
    print("=" * 66)
    print(f"Wrote and re-parsed: {ANALYSIS_PATH}")

    print("\n2. Top-level keys:")
    for k in reparsed.keys():
        print(f"   - {k}")

    print(f"\n3. Detected change day: Day "
          f"{reparsed['change_detection']['detected_change_day']}")
    print(f"4. Interpretation confidence: "
          f"{reparsed['self_check']['interpretation_confidence']} "
          f"({reparsed['self_check']['confidence_band']})")
    print(f"5. Most valuable missing information: "
          f"{reparsed['missing_information']['most_valuable_missing_information']['variable']}")
    print(f"6. Most influential counterfactual: "
          f"{reparsed['counterfactual']['most_influential_counterfactual']['feature']}")
    print(f"7. Trajectory fork day: Day "
          f"{reparsed['trajectories']['divergence']['divergence_day']}")
    print("\n8. One-sentence demo summary:")
    print(f"   {reparsed['demo_summary']['one_sentence_summary']}")


if __name__ == "__main__":
    main()
