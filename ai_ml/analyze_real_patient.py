"""
TRACE — Temporal Reasoning & Analysis for Clinical Exploration
Real-data validation: analyze_real_patient.py

Runs TRACE's CORE temporal reasoning concepts (personal baseline, "where it
changed", and "what changed together") on the selected REAL PhysioNet
participant (f16) and emits a frontend-ready JSON payload.

This is a validation of TRACE's core temporal reasoning on actual wearable
measurements. The controlled SYNTHETIC patient remains the main demonstration
of all seven TRACE capabilities. BioMissing, Counterfactual Patient, and
HealthFork are intentionally NOT produced for the real participant.

This module reuses the robust in-memory window builder from
select_real_participant.py (which already handles cross-participant format
quirks). It reads raw files directly, never copies them, exposes no absolute
timestamps, does not fabricate missing values, assigns no meaning to event
tags, and does not diagnose anything.
"""

import itertools
import json
import os

import numpy as np

# Reuse robust preprocessing (window builder + parsers) and constants.
from select_real_participant import (
    build_windows_in_memory,
    safe_std,
    SELECTION_FEATURES,
    BASELINE_FRACTION,
    MIN_BASELINE_WINDOWS,
    Z_DEVIATION,
    EVENT_WINDOW_MIN,
)
from prepare_physionet import DATASET_ROOT, DATA_SOURCE, EXPERIMENT

# ----- Configuration -----
PARTICIPANT = "f16"
DISPLAY_NAME = "Real Wearable Participant f16"

# Change-detection persistence rule (same transparent approach as selection).
SUSTAIN_WINDOW = 3
SUSTAIN_MIN_HITS = 2
CORR_THRESHOLD = 0.60  # |r| >= 0.60 kept as a strong association (demo criterion)

HERE = os.path.dirname(__file__)
OUTPUTS_DIR = os.path.normpath(os.path.join(HERE, "..", "outputs"))
ANALYSIS_PATH = os.path.join(OUTPUTS_DIR, f"real_{PARTICIPANT}_analysis.json")

DISCLAIMER = (
    "This analysis uses de-identified wearable measurements from a research "
    "dataset for exploratory temporal analysis. TRACE does not diagnose "
    "disease, determine stress severity, predict clinical outcomes, or provide "
    "medical advice."
)


def deviation_status(score):
    """Analytical demo bands (NOT clinical thresholds)."""
    if score < 1.0:
        return "Within personal baseline"
    if score < 2.0:
        return "Mild deviation"
    if score < 3.0:
        return "Moderate deviation"
    return "Strong deviation"


def main():
    pdir = os.path.join(DATASET_ROOT, PARTICIPANT)
    if not os.path.isdir(pdir):
        raise SystemExit(f"Participant directory not found: {pdir}")

    # ---------------- 1. PREPROCESS (reuse robust builder) ----------------
    windows, tags_min = build_windows_in_memory(pdir)
    n_windows = len(windows)
    if n_windows == 0:
        raise SystemExit("No usable windows for participant.")

    # ---------------- 2. PERSONAL BASELINE ----------------
    n_base = max(MIN_BASELINE_WINDOWS, int(round(BASELINE_FRACTION * n_windows)))
    n_base = min(n_base, n_windows - 1)
    base_windows = windows[:n_base]

    base_mean, base_std = {}, {}
    for feat in SELECTION_FEATURES:
        col = np.array([w[feat] for w in base_windows], dtype=float)
        col = col[~np.isnan(col)]
        base_mean[feat] = float(np.mean(col)) if len(col) else np.nan
        base_std[feat] = safe_std(col) if len(col) >= 2 else np.nan

    def window_z(w):
        """Per-feature z-scores for a window (only available features)."""
        zs = {}
        for feat in SELECTION_FEATURES:
            val, m, s = w[feat], base_mean[feat], base_std[feat]
            if np.isnan(val) or np.isnan(m) or np.isnan(s):
                continue
            zs[feat] = (val - m) / s
        return zs

    def deviation_and_agreement(w):
        zs = window_z(w)
        if not zs:
            return np.nan, np.nan, {}
        zarr = np.array(list(zs.values()), dtype=float)
        dev = float(np.sqrt(np.mean(zarr ** 2)))
        agree = float(np.mean(np.abs(zarr) >= Z_DEVIATION))
        return dev, agree, zs

    per_window = []
    for w in windows:
        dev, agree, zs = deviation_and_agreement(w)
        per_window.append({"dev": dev, "agree": agree, "z": zs})

    # Baseline-period deviation stats for the elevated threshold.
    base_devs = [per_window[i]["dev"] for i in range(n_base)
                 if not np.isnan(per_window[i]["dev"])]
    baseline_mean_dev = float(np.mean(base_devs)) if base_devs else 0.0
    baseline_std_dev = safe_std(np.array(base_devs)) if len(base_devs) >= 2 else 0.0
    elevated_threshold = baseline_mean_dev + 2.0 * (baseline_std_dev or 0.0)

    # ---------------- 3. WHERE IT CHANGED ----------------
    devs = np.array([pw["dev"] for pw in per_window], dtype=float)
    elevated = np.array([
        (not np.isnan(d)) and (d > elevated_threshold) for d in devs
    ])

    change_idx = None
    for i in range(n_windows):
        if i < n_base or not elevated[i]:
            continue
        end = min(i + 1 + SUSTAIN_WINDOW, n_windows)
        if int(elevated[i + 1:end].sum()) >= SUSTAIN_MIN_HITS:
            change_idx = i
            break
    if change_idx is None:  # fallback: first elevated after baseline
        for i in range(n_base, n_windows):
            if elevated[i]:
                change_idx = i
                break
    if change_idx is None:  # still nothing -> most deviated later window
        later = [(i, devs[i]) for i in range(n_base, n_windows) if not np.isnan(devs[i])]
        change_idx = max(later, key=lambda t: t[1])[0] if later else n_base

    change_window = int(windows[change_idx]["window"])
    change_elapsed_minutes = round(float(windows[change_idx]["elapsed_minutes"]), 4)
    change_strength = round(float(devs[change_idx]), 4) if not np.isnan(devs[change_idx]) else None

    # Signals changed at the change point (|z| >= 2).
    signals_changed_at_change = [
        feat for feat, zval in per_window[change_idx]["z"].items()
        if abs(zval) >= Z_DEVIATION
    ]

    # Persistence of elevation after the change (fraction of later windows elevated).
    later_elevated = elevated[change_idx:]
    change_persistence = (
        round(float(np.mean(later_elevated)), 4) if len(later_elevated) else 0.0
    )

    # Temporal-pattern confidence (NOT diagnostic). Margin above threshold +
    # persistence, each 0-1, averaged.
    post_devs = devs[change_idx:]
    post_devs = post_devs[~np.isnan(post_devs)]
    score_range = float(np.nanmax(devs) - elevated_threshold) if n_windows else 0.0
    margin_ratio = (
        (change_strength - elevated_threshold) / score_range
        if score_range > 0 and change_strength is not None else 0.0
    )
    temporal_confidence_0_1 = float(np.clip(
        0.5 * np.clip(margin_ratio, 0, 1) + 0.5 * change_persistence, 0.0, 1.0
    ))

    # ---------------- 4. WHAT CHANGED TOGETHER ----------------
    change_rows = windows[change_idx:]
    # Build a matrix of available signals over the change period.
    import pandas as pd
    change_df = pd.DataFrame([{f: w[f] for f in SELECTION_FEATURES} for w in change_rows])

    strong_relationships = []
    corr = change_df.corr(method="pearson")
    for a, b in itertools.combinations(SELECTION_FEATURES, 2):
        if a not in corr or b not in corr:
            continue
        r = corr.loc[a, b]
        if np.isnan(r):
            continue
        if abs(float(r)) >= CORR_THRESHOLD:
            strong_relationships.append({
                "signal_a": a,
                "signal_b": b,
                "correlation": round(float(r), 4),
                "association": "move together" if r > 0 else "move oppositely",
            })
    strong_relationships.sort(key=lambda d: abs(d["correlation"]), reverse=True)

    # Signal directions: post-change mean vs baseline mean (standardized).
    post_mean = change_df.mean()
    signal_directions = {}
    abs_z_accum = {feat: [] for feat in SELECTION_FEATURES}
    for w in change_rows:
        for feat, zval in window_z(w).items():
            abs_z_accum[feat].append(abs(zval))
    for feat in SELECTION_FEATURES:
        m, s = base_mean[feat], base_std[feat]
        if np.isnan(m) or np.isnan(s) or np.isnan(post_mean.get(feat, np.nan)):
            signal_directions[feat] = "unknown"
            continue
        zshift = (post_mean[feat] - m) / s
        if abs(zshift) < 0.5:
            signal_directions[feat] = "approximately stable"
        else:
            signal_directions[feat] = "increased" if zshift > 0 else "decreased"

    strongest_changed_signals = [
        f for f, _ in sorted(
            ((feat, float(np.mean(vals))) for feat, vals in abs_z_accum.items() if vals),
            key=lambda kv: kv[1], reverse=True,
        )[:3]
    ]

    # ---------------- 5. DATA QUALITY / SELF-CHECK ----------------
    dq_vals = np.array([w["data_quality_score"] for w in windows], dtype=float)
    mean_data_quality = round(float(np.mean(dq_vals)), 4)

    signal_missingness = {}
    for feat in SELECTION_FEATURES:
        col = np.array([w[feat] for w in windows], dtype=float)
        signal_missingness[feat] = round(float(np.mean(np.isnan(col))), 4)

    # Baseline stability: lower baseline deviation spread -> more stable (0-1).
    baseline_stability = round(float(np.clip(1.0 - (baseline_std_dev or 0.0), 0.0, 1.0)), 4)
    mean_signal_agreement = round(float(np.nanmean(
        [pw["agree"] for pw in per_window[change_idx:] if not np.isnan(pw["agree"])]
    )) if n_windows > change_idx else 0.0, 4)

    # Interpretation confidence (temporal-pattern, NOT clinical) -> 0-100 + band.
    interp_0_100 = round(float(np.clip(
        100.0 * (
            0.4 * temporal_confidence_0_1
            + 0.25 * mean_data_quality
            + 0.2 * change_persistence
            + 0.15 * baseline_stability
        ), 0.0, 100.0)), 2)
    if interp_0_100 < 40:
        interp_band = "Low"
    elif interp_0_100 < 70:
        interp_band = "Moderate"
    else:
        interp_band = "High"

    self_check = {
        "mean_data_quality": mean_data_quality,
        "signal_missingness": signal_missingness,
        "baseline_stability": baseline_stability,
        "change_persistence": change_persistence,
        "signal_agreement": mean_signal_agreement,
        "interpretation_confidence": {
            "score_0_100": interp_0_100,
            "band": interp_band,
            "note": (
                "Confidence in TEMPORAL PATTERN detection only; not diagnostic "
                "or clinical confidence."
            ),
        },
    }

    # ---------------- 6. EVENT CONTEXT ----------------
    events = [
        {"name": f"event_{i+1}", "elapsed_minutes": round(float(t), 4)}
        for i, t in enumerate(tags_min)
    ]
    nearest_event = None
    change_near_event = False
    if events:
        diffs = [(e["name"], abs(e["elapsed_minutes"] - change_elapsed_minutes))
                 for e in events]
        name, dist = min(diffs, key=lambda kv: kv[1])
        nearest_event = {"name": name, "distance_minutes": round(float(dist), 4)}
        change_near_event = bool(dist <= EVENT_WINDOW_MIN)

    event_context = {
        "events": events,
        "nearest_event_to_change": nearest_event,
        "change_near_event": change_near_event,
        "note": (
            "Event markers are reported as context only. TRACE does not assign "
            "meaning to events or claim an event caused the detected change."
        ),
    }

    # ---------------- 7. TIMELINE ----------------
    timeline = []
    for i, w in enumerate(windows):
        dev = per_window[i]["dev"]
        agree = per_window[i]["agree"]
        timeline.append({
            "window": int(w["window"]),
            "elapsed_minutes": round(float(w["elapsed_minutes"]), 4),
            "heart_rate_bpm": None if np.isnan(w["heart_rate_bpm"]) else round(w["heart_rate_bpm"], 4),
            "hrv_rmssd_ms": None if np.isnan(w["hrv_rmssd_ms"]) else round(w["hrv_rmssd_ms"], 4),
            "eda_mean": None if np.isnan(w["eda_mean"]) else round(w["eda_mean"], 6),
            "temperature_c": None if np.isnan(w["temperature_c"]) else round(w["temperature_c"], 4),
            "activity_mean": None if np.isnan(w["activity_mean"]) else round(w["activity_mean"], 4),
            "deviation_score": None if np.isnan(dev) else round(dev, 4),
            "deviation_status": None if np.isnan(dev) else deviation_status(dev),
            "signal_agreement": None if np.isnan(agree) else round(agree, 4),
            "data_quality_score": round(float(w["data_quality_score"]), 4),
            "is_baseline": i < n_base,
            "is_change_point": i == change_idx,
        })

    # ---------------- 8. ASSEMBLE OUTPUT ----------------
    patient = {
        "participant_id": PARTICIPANT,
        "display_name": DISPLAY_NAME,
    }
    data_source = {
        "type": "real_research_dataset",
        "label": DATA_SOURCE,
        "experiment": EXPERIMENT,
        "is_real_patient_data": True,
    }
    baseline_block = {
        "baseline_window_count": int(n_base),
        "baseline_fraction": BASELINE_FRACTION,
        "statistics": {
            feat: {
                "mean": None if np.isnan(base_mean[feat]) else round(base_mean[feat], 4),
                "std": None if np.isnan(base_std[feat]) else round(base_std[feat], 4),
            } for feat in SELECTION_FEATURES
        },
        "baseline_mean_deviation": round(baseline_mean_dev, 4),
        "elevated_threshold": round(elevated_threshold, 4),
    }
    change_detection = {
        "change_window": change_window,
        "change_elapsed_minutes": change_elapsed_minutes,
        "change_strength": change_strength,
        "signals_changed_at_change": signals_changed_at_change,
        "confidence": round(temporal_confidence_0_1, 4),
        "confidence_note": (
            "Confidence in temporal pattern detection, not disease or stress "
            "diagnosis."
        ),
    }
    relationships = {
        "strong_relationships": strong_relationships,
        "signal_directions": signal_directions,
        "strongest_changed_signals": strongest_changed_signals,
        "note": "Relationships are statistical associations, not causes.",
    }

    demo_summary = {
        "headline": "TRACE detected a real physiological transition.",
        "detected_change": {
            "change_window": change_window,
            "change_elapsed_minutes": change_elapsed_minutes,
            "change_strength": change_strength,
        },
        "strongest_changed_signals": strongest_changed_signals,
        "interpretation_confidence": {
            "score_0_100": interp_0_100, "band": interp_band,
        },
        "event_context": {
            "nearest_event_to_change": nearest_event,
            "change_near_event": change_near_event,
        },
        "data_quality": mean_data_quality,
        "statement": (
            "This real research recording demonstrates TRACE's core temporal "
            "analysis on actual wearable measurements."
        ),
    }

    output = {
        "patient": patient,
        "data_source": data_source,
        "timeline": timeline,
        "baseline": baseline_block,
        "change_detection": change_detection,
        "relationships": relationships,
        "self_check": self_check,
        "events": event_context,
        "demo_summary": demo_summary,
        "disclaimer": DISCLAIMER,
    }

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    with open(ANALYSIS_PATH, "w") as f:
        json.dump(output, f, indent=2)

    # ---------------- 11. VALIDATION + PRINT ----------------
    with open(ANALYSIS_PATH) as f:
        json.load(f)  # verify it parses

    print("=" * 70)
    print(f"TRACE — Real patient analysis  |  participant {PARTICIPANT}")
    print("=" * 70)
    print(f"participant                : {PARTICIPANT}")
    print(f"number of windows          : {n_windows}")
    print(f"baseline window count      : {n_base}")
    print(f"detected change            : window {change_window} "
          f"({change_elapsed_minutes:.2f} min)")
    print(f"change strength            : {change_strength}")
    print(f"change confidence          : {temporal_confidence_0_1:.4f} "
          f"(temporal pattern, not diagnosis)")
    print(f"strongest changed signals  : {', '.join(strongest_changed_signals)}")
    print(f"strong relationships       : {len(strong_relationships)} "
          f"(|r| >= {CORR_THRESHOLD})")
    for r in strong_relationships[:5]:
        print(f"    {r['signal_a']:<16} <-> {r['signal_b']:<16} "
              f"r={r['correlation']:+.3f} ({r['association']})")
    print(f"mean data quality          : {mean_data_quality:.4f}")
    print(f"interpretation confidence  : {interp_0_100:.2f} / 100 ({interp_band})")
    if nearest_event:
        print(f"nearest event marker       : {nearest_event['name']} "
              f"({nearest_event['distance_minutes']:.2f} min away, "
              f"near={change_near_event})")
    else:
        print("nearest event marker       : (no events)")
    print(f"output JSON path           : {ANALYSIS_PATH}")
    print("JSON parsed successfully.")


if __name__ == "__main__":
    main()
