"""
TRACE — Temporal Reasoning & Analysis for Clinical Exploration
Feature 3: "What Changed Together?" / ReverseHealth

Analyzes which physiological signals moved together around and after the
detected change point, the temporal order in which they shifted, and simple
lagged relationships between them.

This is ASSOCIATION / hypothesis analysis only. It does NOT claim causality,
does NOT diagnose disease, and does NOT recommend treatment. Correlation and
lag thresholds here are TRACE demo criteria, not medical thresholds.
"""

import itertools
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

# TRACE demo criteria (NOT medical thresholds)
CORR_THRESHOLD = 0.60       # |r| >= 0.60 counts as a "strong" relationship
MAX_LAG = 3                 # test lags 0..3 days
STABLE_BAND = 0.5           # |z of post-change mean| < 0.5 -> "stable"

HERE = os.path.dirname(__file__)
DATA_PATH = os.path.normpath(
    os.path.join(HERE, "..", "data", "synthetic", "patient_001.csv")
)
OUTPUTS_DIR = os.path.normpath(os.path.join(HERE, "..", "outputs"))
CHANGE_SUMMARY_PATH = os.path.join(OUTPUTS_DIR, "change_point_summary.json")
RELATIONSHIP_PATH = os.path.join(OUTPUTS_DIR, "relationship_summary.json")


def direction_word(corr):
    return "move together" if corr > 0 else "move oppositely"


def main():
    # ---------------------------------------------------------------
    # PART 1 — Load detected change point + data
    # ---------------------------------------------------------------
    with open(CHANGE_SUMMARY_PATH) as f:
        change_summary = json.load(f)

    detected_change_day = int(change_summary["detected_change_day"])
    signal_onsets = change_summary.get("signal_onsets", {})

    df = pd.read_csv(DATA_PATH)

    # Baseline stats for change-direction and "stable" determination.
    baseline_mask = df["day"] <= BASELINE_DAYS
    baseline_mean = df.loc[baseline_mask, FEATURES].mean()
    baseline_std = df.loc[baseline_mask, FEATURES].std(ddof=1).replace(0, np.nan)

    # Change-period window: detected change day through Day 30.
    change_df = df[df["day"] >= detected_change_day].reset_index(drop=True)

    # ---------------------------------------------------------------
    # PART 2 — Correlation analysis over the change period
    # ---------------------------------------------------------------
    corr_matrix = change_df[FEATURES].corr(method="pearson")

    strong_correlations = []
    for a, b in itertools.combinations(FEATURES, 2):
        r = float(corr_matrix.loc[a, b])
        if np.isnan(r):
            continue
        if abs(r) >= CORR_THRESHOLD:
            strong_correlations.append(
                {
                    "signal_a": a,
                    "signal_b": b,
                    "correlation": round(r, 4),
                    "direction": direction_word(r),
                }
            )
    strong_correlations.sort(key=lambda d: abs(d["correlation"]), reverse=True)

    # ---------------------------------------------------------------
    # PART 3 — Temporal ordering (from calculated onset days)
    # ---------------------------------------------------------------
    # Keep only signals with a real onset; order by onset day ascending.
    onset_items = [
        (feat, day) for feat, day in signal_onsets.items() if day is not None
    ]
    onset_items.sort(key=lambda kv: (kv[1], kv[0]))
    ordered_signal_onsets = [
        {"signal": feat, "onset_day": int(day)} for feat, day in onset_items
    ]

    # ---------------------------------------------------------------
    # PART 4 — Lagged relationships over the change period
    # For an ordered pair (a, b), lag L means a is shifted to lead b by L days:
    # correlate a[:-L] with b[L:]. Pick the lag with the strongest |r|.
    # ---------------------------------------------------------------
    lagged_relationships = []
    for a, b in itertools.permutations(FEATURES, 2):
        best = {"lag": 0, "corr": 0.0}
        for lag in range(0, MAX_LAG + 1):
            if lag == 0:
                x = change_df[a]
                y = change_df[b]
            else:
                x = change_df[a].iloc[:-lag].reset_index(drop=True)
                y = change_df[b].iloc[lag:].reset_index(drop=True)
            if len(x) < 3:
                continue
            r = x.corr(y)
            if np.isnan(r):
                continue
            if abs(r) > abs(best["corr"]):
                best = {"lag": lag, "corr": float(r)}
        if abs(best["corr"]) >= CORR_THRESHOLD and best["lag"] > 0:
            lagged_relationships.append(
                {
                    "leading_signal": a,
                    "following_signal": b,
                    "lag_days": best["lag"],
                    "correlation": round(best["corr"], 4),
                }
            )
    lagged_relationships.sort(key=lambda d: abs(d["correlation"]), reverse=True)

    # ---------------------------------------------------------------
    # PART 5 — Relationship graph (nodes + edges)
    # ---------------------------------------------------------------
    post_mean = change_df[FEATURES].mean()

    def change_direction(feat):
        # Standardized distance of the post-change mean from baseline.
        std = baseline_std[feat]
        if pd.isna(std) or std == 0:
            return "stable"
        zshift = (post_mean[feat] - baseline_mean[feat]) / std
        if abs(zshift) < STABLE_BAND:
            return "stable"
        return "increased" if zshift > 0 else "decreased"

    nodes = []
    for feat in FEATURES:
        nodes.append(
            {
                "name": feat,
                "onset_day": (
                    int(signal_onsets[feat])
                    if signal_onsets.get(feat) is not None
                    else None
                ),
                "change_direction": change_direction(feat),
            }
        )

    edges = []
    # Correlation edges (undirected associations).
    for rel in strong_correlations:
        edges.append(
            {
                "source": rel["signal_a"],
                "target": rel["signal_b"],
                "correlation": rel["correlation"],
                "lag_days": 0,
                "relationship": (
                    "moves with" if rel["correlation"] > 0 else "moves inversely with"
                ),
            }
        )
    # Lagged edges (earlier-change associated with later-change).
    for rel in lagged_relationships:
        edges.append(
            {
                "source": rel["leading_signal"],
                "target": rel["following_signal"],
                "correlation": rel["correlation"],
                "lag_days": rel["lag_days"],
                "relationship": "earlier change associated with later change",
            }
        )

    # ---------------------------------------------------------------
    # PART 6 — Hypothesis groups (broad, non-diagnostic)
    # Support score = evidence from onset activity + correlation strength
    # among the group's signals, normalized to 0-1. Not hardcoded per group.
    # ---------------------------------------------------------------
    group_defs = {
        "Recovery / autonomic pattern": ["hrv_ms", "resting_hr_bpm", "respiratory_rate"],
        "Activity / behavioral pattern": ["steps", "sleep_hours"],
        "Physiological stress pattern": ["eda", "stress_score", "fatigue_score"],
        "Possible measurement/context effect": ["temperature_f"],
    }

    def onset_evidence(feats):
        """Fraction of the group's signals that had a detected onset."""
        if not feats:
            return 0.0
        active = sum(1 for f in feats if signal_onsets.get(f) is not None)
        return active / len(feats)

    def corr_evidence(feats):
        """Mean |r| among the group's signal pairs over the change period."""
        pairs = list(itertools.combinations(feats, 2))
        if not pairs:
            # Single-signal group: lean on its own movement magnitude.
            f = feats[0]
            std = baseline_std[f]
            if pd.isna(std) or std == 0:
                return 0.0
            zshift = abs((post_mean[f] - baseline_mean[f]) / std)
            return float(np.clip(zshift / 5.0, 0.0, 1.0))
        vals = []
        for a, b in pairs:
            r = corr_matrix.loc[a, b]
            if not np.isnan(r):
                vals.append(abs(float(r)))
        return float(np.mean(vals)) if vals else 0.0

    hypothesis_groups = []
    for name, feats in group_defs.items():
        oe = onset_evidence(feats)
        ce = corr_evidence(feats)
        support = float(np.clip(0.5 * oe + 0.5 * ce, 0.0, 1.0))
        active_signals = [f for f in feats if signal_onsets.get(f) is not None]
        reasoning = (
            f"{len(active_signals)} of {len(feats)} signals in this group showed a "
            f"detected onset; mean within-group association strength over the change "
            f"period was {ce:.2f}. This is a non-diagnostic hypothesis category."
        )
        hypothesis_groups.append(
            {
                "name": name,
                "supporting_signals": feats,
                "support_score": round(support, 4),
                "reasoning": reasoning,
            }
        )
    hypothesis_groups.sort(key=lambda g: g["support_score"], reverse=True)

    # ---------------------------------------------------------------
    # Assemble output
    # ---------------------------------------------------------------
    disclaimer = (
        "Observed relationships are statistical associations and temporal "
        "patterns, not evidence of medical causation or diagnosis."
    )
    detected_change_date = str(
        df.loc[df["day"] == detected_change_day, "date"].iloc[0]
    )

    output = {
        "patient_id": PATIENT_ID,
        "detected_change_day": detected_change_day,
        "detected_change_date": detected_change_date,
        "change_period": f"Day {detected_change_day}-30",
        "ordered_signal_onsets": ordered_signal_onsets,
        "strong_correlations": strong_correlations,
        "lagged_relationships": lagged_relationships,
        "graph": {"nodes": nodes, "edges": edges},
        "hypothesis_groups": hypothesis_groups,
        "disclaimer": disclaimer,
    }

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    with open(RELATIONSHIP_PATH, "w") as f:
        json.dump(output, f, indent=2)

    # ---------------------------------------------------------------
    # PRINT
    # ---------------------------------------------------------------
    print("=" * 64)
    print("TRACE Feature 3 — What Changed Together? / ReverseHealth")
    print("=" * 64)

    print(f"\n1. Detected change day: Day {detected_change_day} "
          f"({detected_change_date})")

    print("\n2. Ordered signal onset timeline:")
    for i, item in enumerate(ordered_signal_onsets):
        arrow = "   " if i == 0 else "-> "
        print(f"   {arrow}{item['signal']:<20} (Day {item['onset_day']})")

    print("\n3. Top 10 strongest correlations (change period):")
    if strong_correlations:
        for rel in strong_correlations[:10]:
            print(
                f"   {rel['signal_a']:<18} <-> {rel['signal_b']:<18} "
                f"r={rel['correlation']:+.3f}  ({rel['direction']})"
            )
    else:
        print("   (none at |r| >= 0.60)")

    print("\n4. Top useful lagged relationships:")
    if lagged_relationships:
        for rel in lagged_relationships[:10]:
            print(
                f"   {rel['leading_signal']:<18} -> {rel['following_signal']:<18} "
                f"lag={rel['lag_days']}d  r={rel['correlation']:+.3f}"
            )
    else:
        print("   (none at |r| >= 0.60 with lag > 0)")

    print("\n5. Hypothesis groups and support scores:")
    for g in hypothesis_groups:
        print(f"   [{g['support_score']:.3f}] {g['name']}")
        print(f"           signals: {', '.join(g['supporting_signals'])}")

    print(f"\nSaved relationship summary JSON : {RELATIONSHIP_PATH}")


if __name__ == "__main__":
    main()
