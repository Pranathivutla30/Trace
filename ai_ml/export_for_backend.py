"""
TRACE — Temporal Reasoning & Analysis for Clinical Exploration
Backend adapter: export_for_backend.py

Non-destructive adapter between the completed AI/ML pipeline and the EXISTING
backend/frontend JSON contract (defined by backend/mock/*.json).

Reads (does not modify):
    outputs/patient_001_analysis.json      (synthetic, unified)
    outputs/real_f16_analysis.json          (real f16 core temporal analysis)
    outputs/real_f16_ml_analysis.json       (real f16 trained-model evaluation)

Writes (the live files the backend's data_service looks for first):
    ai_ml/output/synthetic_001.json
    ai_ml/output/real_f16.json

This script does NOT modify any AI/ML scripts, any existing TRACE analysis JSON,
or any backend/frontend code. It only translates completed outputs into the
backend contract. It invents no medical data: signals the pipeline does not
produce (e.g. SpO2, respiration for the real recording) are simply omitted, and
missing ML scores are null rather than fabricated.
"""

import json
import os

HERE = os.path.dirname(__file__)
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, ".."))
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
LIVE_DIR = os.path.join(HERE, "output")  # backend reads ai_ml/output/{source}_{id}.json

SYN_IN = os.path.join(OUTPUTS_DIR, "patient_001_analysis.json")
REAL_IN = os.path.join(OUTPUTS_DIR, "real_f16_analysis.json")
REAL_ML_IN = os.path.join(OUTPUTS_DIR, "real_f16_ml_analysis.json")

SYN_OUT = os.path.join(LIVE_DIR, "synthetic_001.json")
REAL_OUT = os.path.join(LIVE_DIR, "real_f16.json")


def load_json(path):
    with open(path) as f:
        return json.load(f)


def f_to_c(f):
    return round((f - 32.0) * 5.0 / 9.0, 4)


# ------------------------------------------------------------------
# SYNTHETIC ADAPTER
# ------------------------------------------------------------------
# Signal name map: pipeline -> backend contract.
SYN_SIGNAL_MAP = {
    "sleep_hours": "sleep_h",
    "hrv_ms": "hrv_ms",
    "resting_hr_bpm": "resting_hr",
    "steps": "steps",
    "temperature_f": "temp_c",      # value also converted F -> C
    "respiratory_rate": "resp_rate",
    "eda": "eda",
    "fatigue_score": "fatigue",
    "stress_score": "stress",
}
SYN_BACKEND_SIGNALS = [
    "sleep_h", "hrv_ms", "resting_hr", "steps", "temp_c",
    "resp_rate", "eda", "fatigue", "stress",
]
SYN_UNITS = {
    "sleep_h": "h", "hrv_ms": "ms", "resting_hr": "bpm", "steps": "count",
    "temp_c": "degC", "resp_rate": "brpm", "eda": "uS",
    "fatigue": "score", "stress": "score",
}


def adapt_synthetic():
    doc = load_json(SYN_IN)
    timeline_in = doc["timeline"]
    n_days = len(timeline_in)
    last_day = max(int(r["day"]) for r in timeline_in)

    # Day 1..30 -> t where the final observed day is t=0 and earlier days
    # are negative: t = day - last_day.
    def day_to_t(day):
        return int(day) - last_day

    def conv_value(pipeline_key, value):
        if value is None:
            return None
        if pipeline_key == "temperature_f":
            return f_to_c(value)
        return value

    timeline = []
    for r in timeline_in:
        point = {"t": day_to_t(r["day"])}
        for p_key, b_key in SYN_SIGNAL_MAP.items():
            if p_key in r:
                point[b_key] = conv_value(p_key, r[p_key])
        timeline.append(point)

    # ---- change point ----
    cd = doc.get("change_detection", {})
    detected_day = cd.get("detected_change_day")
    change_point = None
    if detected_day is not None:
        change_point = {"detected_t": day_to_t(detected_day), "actual_t": None}

    # ---- events: derive from signal onsets (earliest) ----
    signal_onsets = cd.get("signal_onsets", {}) or {}
    events = []
    if signal_onsets:
        earliest_feat, earliest_day = min(
            ((f, d) for f, d in signal_onsets.items() if d is not None),
            key=lambda kv: kv[1], default=(None, None),
        )
        if earliest_feat is not None:
            events.append({
                "t": day_to_t(earliest_day),
                "label": f"{SYN_SIGNAL_MAP.get(earliest_feat, earliest_feat)} begins shifting",
            })

    # ---- baseline: per-signal mean (convert temp) ----
    base_stats = doc.get("baseline", {}).get("baseline_statistics", {}) or {}
    baseline = {}
    for p_key, b_key in SYN_SIGNAL_MAP.items():
        if p_key in base_stats:
            mean = base_stats[p_key].get("mean")
            if p_key == "temperature_f" and mean is not None:
                mean = f_to_c(mean)
            baseline[b_key] = {"unit": SYN_UNITS[b_key], "mean": mean}

    # ---- temporal_trace: earliest shift + onset order ----
    ordered = []
    for feat, day in sorted(
        ((f, d) for f, d in signal_onsets.items() if d is not None),
        key=lambda kv: kv[1],
    ):
        ordered.append({
            "signal": SYN_SIGNAL_MAP.get(feat, feat),
            "first_change_t": day_to_t(day),
        })
    temporal_trace = {
        "earliest_coordinated_shift_t": (
            day_to_t(detected_day) if detected_day is not None else None
        ),
        "order": ordered,
    }

    # ---- connections: from relationships (ordered onsets -> precedes edges) ----
    rel = doc.get("relationships", {})
    edges = []
    for a, b in zip(ordered, ordered[1:]):
        edges.append({"from": a["signal"], "to": b["signal"], "relation": "precedes"})
    connections = {
        "edges": edges,
        "hypothesis": (
            "Earlier signal shifts preceded later ones in a coordinated "
            "temporal pattern (association, not causation)."
        ),
    }

    # ---- missing_evidence: from missing_information ----
    mi = doc.get("missing_information", {})
    candidates = mi.get("candidate_information", []) or []
    items = []
    # Present signals we actually measured:
    for b_key in ["hrv_ms", "sleep_h", "temp_c"]:
        items.append({"name": b_key, "present": True})
    # Unavailable contextual variables -> present False.
    for c in candidates[:4]:
        items.append({"name": c.get("variable"), "present": False})
    top_missing = mi.get("most_valuable_missing_information", {}) or {}
    most_valuable = []
    if top_missing.get("variable"):
        most_valuable.append(top_missing["variable"])
    missing_evidence = {"items": items, "most_valuable_missing": most_valuable}

    # ---- self_check: map to backend's compact shape ----
    sc = doc.get("self_check", {})
    conf = sc.get("interpretation_confidence")
    band = sc.get("confidence_band", "")
    comp = sc.get("component_scores", {}) or {}
    pattern_evidence = (
        "Strong" if comp.get("deviation_strength", 0) >= 0.66
        else "Moderate" if comp.get("deviation_strength", 0) >= 0.33 else "Limited"
    )
    dqs = comp.get("data_completeness", 0)
    data_completeness = (
        "High" if dqs >= 0.9 else "Moderate" if dqs >= 0.6 else "Low"
    )
    self_check = {
        "pattern_evidence": pattern_evidence,
        "data_completeness": data_completeness,
        "interpretation_confidence": round(conf) if conf is not None else None,
    }

    # ---- counterfactuals: current_deviation + per-signal new_deviation ----
    cf = doc.get("counterfactual", {})
    orig = cf.get("original_deviation_score")
    singles = cf.get("single_signal_counterfactuals", []) or []
    cf_signals = {}
    # Scale deviation to a 0-100-ish display using percentage reductions so the
    # frontend's deviation bars behave. current_deviation anchored at 100 * a
    # bounded transform of the raw score is avoided; instead we express the
    # counterfactual as current minus the percentage reduction (relative scale).
    current_display = round(min(100.0, orig)) if orig is not None else None
    # Use percentage_reduction to derive a comparable "new_deviation".
    for s in singles:
        b_key = SYN_SIGNAL_MAP.get(s["feature"], s["feature"])
        pct = s.get("percentage_reduction")
        if current_display is not None and pct is not None:
            new_dev = round(current_display * (1.0 - pct / 100.0))
        else:
            new_dev = None
        cf_signals[b_key] = {
            "new_deviation": new_dev,
            "note": f"If {b_key} stayed near baseline",
        }
    counterfactuals = {"current_deviation": current_display, "signals": cf_signals}

    # ---- trajectories: map scenarios -> name/assumption/points ----
    trajectories = []
    for sc_obj in doc.get("trajectories", {}).get("scenarios", []) or []:
        pts = [p.get("deviation_score") for p in sc_obj.get("daily_values", [])]
        trajectories.append({
            "name": sc_obj.get("scenario_name"),
            "assumption": sc_obj.get("description"),
            "points": pts,
        })

    out = {
        "id": "001",
        "source": "synthetic",
        "time_unit": "day",
        "window": f"Day {day_to_t(1)} to Day {day_to_t(last_day)}",
        "available_signals": SYN_BACKEND_SIGNALS,
        "timeline": timeline,
        "events": events,
        "change_point": change_point,
        "baseline": baseline,
        "temporal_trace": temporal_trace,
        "connections": connections,
        "missing_evidence": missing_evidence,
        "self_check": self_check,
        "counterfactuals": counterfactuals,
        "trajectories": trajectories,
        "disclaimer": doc.get("relationships", {}).get("disclaimer"),
    }
    return out, len(timeline), change_point


# ------------------------------------------------------------------
# REAL f16 ADAPTER
# ------------------------------------------------------------------
# Real pipeline signal -> backend real-contract signal. Only signals the real
# recording actually contains. No SpO2, no fabricated respiration.
REAL_SIGNAL_MAP = {
    "heart_rate_bpm": "hr_bpm",
    "hrv_rmssd_ms": "hrv_ms",
    "eda_mean": "eda_us",
    "temperature_c": "temp_c",
    "activity_mean": "activity",
}
REAL_BACKEND_SIGNALS = ["hr_bpm", "hrv_ms", "eda_us", "temp_c", "activity"]
REAL_UNITS = {
    "hr_bpm": "bpm", "hrv_ms": "ms", "eda_us": "uS",
    "temp_c": "degC", "activity": "g",
}


def adapt_real():
    doc = load_json(REAL_IN)
    ml = load_json(REAL_ML_IN)

    # Index ML scores by window for merge.
    ml_by_window = {int(r["window"]): r for r in ml.get("timeline", [])}

    timeline = []
    for r in doc["timeline"]:
        win = int(r["window"])
        point = {"t": round(float(r["elapsed_minutes"]), 4)}
        for p_key, b_key in REAL_SIGNAL_MAP.items():
            val = r.get(p_key)
            if val is not None:
                point[b_key] = val
        # Merge ML anomaly scores by window; null when unavailable (do not fabricate).
        mlrow = ml_by_window.get(win)
        point["ml_anomaly_score"] = (
            mlrow["ml_anomaly_score"] if mlrow is not None else None
        )
        point["raw_model_score"] = (
            mlrow["raw_model_score"] if mlrow is not None else None
        )
        timeline.append(point)

    # ---- change point (elapsed minutes) ----
    cd = doc.get("change_detection", {})
    change_point = {
        "detected_t": cd.get("change_elapsed_minutes"),
        "actual_t": None,
    }

    # ---- events (already elapsed minutes, generic labels) ----
    events = [
        {"t": round(float(e["elapsed_minutes"]), 4), "label": e["name"]}
        for e in doc.get("events", {}).get("events", [])
    ]

    # ---- baseline (per-signal mean) ----
    stats = doc.get("baseline", {}).get("statistics", {}) or {}
    baseline = {}
    for p_key, b_key in REAL_SIGNAL_MAP.items():
        st = stats.get(p_key)
        if st and st.get("mean") is not None:
            baseline[b_key] = {"unit": REAL_UNITS[b_key], "mean": st["mean"]}

    # ---- temporal_trace ----
    signals_changed = cd.get("signals_changed_at_change", []) or []
    temporal_trace = {
        "earliest_coordinated_shift_t": cd.get("change_elapsed_minutes"),
        "order": [
            {"signal": REAL_SIGNAL_MAP.get(s, s),
             "first_change_t": cd.get("change_elapsed_minutes")}
            for s in signals_changed
        ],
    }

    # ---- connections (strong relationships; may be empty for real data) ----
    rel = doc.get("relationships", {})
    edges = []
    for sr in rel.get("strong_relationships", []) or []:
        edges.append({
            "from": REAL_SIGNAL_MAP.get(sr["signal_a"], sr["signal_a"]),
            "to": REAL_SIGNAL_MAP.get(sr["signal_b"], sr["signal_b"]),
            "relation": "co-moves" if sr.get("correlation", 0) > 0 else "moves inversely",
        })
    connections = {
        "edges": edges,
        "hypothesis": (
            "Associations observed over the change period (not causation). "
            "Real wearable signals here are only loosely coupled."
            if not edges else
            "Signals that moved together over the change period (association, "
            "not causation)."
        ),
    }

    # ---- missing_evidence ----
    missing_items = []
    for p_key, b_key in REAL_SIGNAL_MAP.items():
        miss = doc.get("self_check", {}).get("signal_missingness", {}).get(p_key, 1.0)
        missing_items.append({"name": b_key, "present": miss < 0.5})
    missing_evidence = {
        "items": missing_items,
        "most_valuable_missing": ["Subjective context label"],
    }

    # ---- self_check ----
    sc = doc.get("self_check", {})
    ic = sc.get("interpretation_confidence", {}) or {}
    dq = sc.get("mean_data_quality", 0)
    self_check = {
        "pattern_evidence": (
            "Strong" if sc.get("change_persistence", 0) >= 0.66
            else "Moderate" if sc.get("change_persistence", 0) >= 0.33 else "Limited"
        ),
        "data_completeness": (
            "High" if dq >= 0.9 else "Moderate" if dq >= 0.6 else "Low"
        ),
        "interpretation_confidence": round(ic.get("score_0_100"))
        if ic.get("score_0_100") is not None else None,
    }

    # ---- ML transition model block (held-out evaluation) ----
    ev = ml.get("evaluation", {})
    ts = ml.get("training_summary", {})
    ml_transition_model = {
        "model_type": ml.get("model", {}).get("model_type"),
        "training_participant_count": ts.get("training_participant_count"),
        "held_out_participant": ts.get("held_out_participant"),
        "baseline_mean_anomaly": ev.get("baseline_mean_anomaly"),
        "post_baseline_mean_anomaly": ev.get("post_baseline_mean_anomaly"),
        "peak_anomaly_window": ev.get("peak_anomaly_window"),
        "peak_anomaly_score": ev.get("peak_anomaly_score"),
        "persistent_anomaly_detected": ev.get("persistent_anomaly_detected"),
        "note": (
            "Anomaly scores measure deviation from a learned baseline-like "
            "pattern. They are NOT disease probabilities, stress probabilities, "
            "or clinical risk scores."
        ),
    }

    duration = max((p["t"] for p in timeline), default=0)
    out = {
        "id": "f16",
        "source": "real",
        "time_unit": "minute",
        "window": f"0 to {round(duration)} min",
        "available_signals": REAL_BACKEND_SIGNALS,
        "data_source_label": (
            "De-identified wearable research data — PhysioNet Wearable Device "
            "Dataset from Induced Stress and Structured Exercise Sessions "
            "v1.0.1 (STRESS), participant f16."
        ),
        "is_real_patient_data": True,
        "timeline": timeline,
        "events": events,
        "change_point": change_point,
        "baseline": baseline,
        "temporal_trace": temporal_trace,
        "connections": connections,
        "missing_evidence": missing_evidence,
        "self_check": self_check,
        "ml_transition_model": ml_transition_model,
        "disclaimer": doc.get("disclaimer"),
    }
    scored = sum(1 for p in timeline if p.get("ml_anomaly_score") is not None)
    return out, len(timeline), scored, ml_transition_model, change_point


def main():
    os.makedirs(LIVE_DIR, exist_ok=True)

    syn, syn_points, syn_cp = adapt_synthetic()
    real, real_points, real_scored, mlblock, real_cp = adapt_real()

    with open(SYN_OUT, "w") as f:
        json.dump(syn, f, indent=2)
    with open(REAL_OUT, "w") as f:
        json.dump(real, f, indent=2)

    # ---------------- VALIDATION ----------------
    syn_reparsed = load_json(SYN_OUT)
    real_reparsed = load_json(REAL_OUT)

    # (4) no fabricated SpO2 / unavailable signals
    no_spo2_syn = all("spo2" not in p for p in syn_reparsed["timeline"])
    real_only_available = all(
        set(p.keys()) <= ({"t", "ml_anomaly_score", "raw_model_score"} | set(REAL_BACKEND_SIGNALS))
        for p in real_reparsed["timeline"]
    )
    # (5) temperature conversion sanity: synthetic temp_c should be ~36-38 C
    syn_temps = [p["temp_c"] for p in syn_reparsed["timeline"] if "temp_c" in p]
    temp_ok = all(30.0 <= t <= 42.0 for t in syn_temps) if syn_temps else False
    # (6) ML merge by window: f16 window 29 must carry the peak score
    peak_win = mlblock["peak_anomaly_window"]
    ml_in = load_json(REAL_ML_IN)
    peak_src = next((r for r in ml_in["timeline"] if r["window"] == peak_win), None)
    f16_src = load_json(REAL_IN)
    minute_for_peak = next(
        (p["elapsed_minutes"] for p in f16_src["timeline"] if p["window"] == peak_win),
        None,
    )
    merged_peak = next(
        (p for p in real_reparsed["timeline"]
         if minute_for_peak is not None and abs(p["t"] - minute_for_peak) < 1e-6),
        None,
    )
    merge_ok = bool(
        peak_src and merged_peak
        and merged_peak.get("ml_anomaly_score") == peak_src["ml_anomaly_score"]
    )
    # (7) f16 held out of training
    held_out_ok = ml_in["training_summary"]["held_out_participant"] == "f16" \
        and "f16" not in ml_in["training_summary"]["training_participants"]

    print("=" * 66)
    print("TRACE — Backend export adapter")
    print("=" * 66)
    print(f"Wrote: {SYN_OUT}")
    print(f"Wrote: {REAL_OUT}")
    print("\nValidation:")
    print(f"  1. both JSON parse                 : True")
    print(f"  2. synthetic has backend keys      : "
          f"{set(['id','source','time_unit','timeline','baseline','temporal_trace','connections','missing_evidence','self_check','counterfactuals','trajectories']) <= set(syn_reparsed.keys())}")
    print(f"  3. real has backend keys           : "
          f"{set(['id','source','time_unit','timeline','baseline','temporal_trace','connections','self_check']) <= set(real_reparsed.keys())}")
    print(f"  4. no fabricated SpO2/extra signals: {no_spo2_syn and real_only_available}")
    print(f"  5. synthetic temp F->C in range    : {temp_ok} "
          f"(e.g. {syn_temps[0] if syn_temps else 'n/a'} C)")
    print(f"  6. ML peak merged by window {peak_win}      : {merge_ok}")
    print(f"  7. f16 held out of training        : {held_out_ok}")
    print(f"\n  synthetic timeline points          : {syn_points}")
    print(f"  real timeline points               : {real_points}")
    print(f"  real ML scored windows             : {real_scored}")
    print(f"  real ML baseline mean anomaly      : {mlblock['baseline_mean_anomaly']}")
    print(f"  real ML post-baseline mean anomaly : {mlblock['post_baseline_mean_anomaly']}")
    print(f"  synthetic change point (t)         : {syn_cp}")
    print(f"  real change point (t, minutes)     : {real_cp}")


if __name__ == "__main__":
    main()
