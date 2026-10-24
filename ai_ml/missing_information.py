"""
TRACE — Temporal Reasoning & Analysis for Clinical Exploration
Feature 4: "What Should We Learn Next?" / BioMissing

Estimates which currently-unavailable contextual information would most reduce
uncertainty about the observed physiological pattern, using a simple, explainable
value-of-information (VOI) calculation over the Feature 3 hypothesis groups.

This is NOT diagnosis and NOT a question of "which disease". It answers:
"what additional context would best help TRACE distinguish between the currently
plausible interpretation paths?" All variable->hypothesis mappings below are
explicitly PROTOTYPE DEMO ASSUMPTIONS, not medical conclusions. Nothing here
claims any variable caused the pattern.
"""

import json
import os

import numpy as np

# ----- Configuration -----
PATIENT_ID = "patient_001"

HERE = os.path.dirname(__file__)
OUTPUTS_DIR = os.path.normpath(os.path.join(HERE, "..", "outputs"))
BASELINE_SUMMARY_PATH = os.path.join(OUTPUTS_DIR, "baseline_summary.json")
CHANGE_SUMMARY_PATH = os.path.join(OUTPUTS_DIR, "change_point_summary.json")
RELATIONSHIP_SUMMARY_PATH = os.path.join(OUTPUTS_DIR, "relationship_summary.json")
MISSING_SUMMARY_PATH = os.path.join(OUTPUTS_DIR, "missing_information_summary.json")

# ------------------------------------------------------------------
# PART 2 — Missing context variables and their PROTOTYPE DEMO mappings
#
# Each missing variable has:
#   - possible outcomes (with a prior probability for each outcome)
#   - per-outcome multiplicative "support nudges" applied to hypothesis groups
#
# The hypothesis group KEYS are matched loosely (case-insensitive substring)
# against the group names coming from relationship_summary.json, so this stays
# robust if the exact wording shifts. These nudges are demo reasoning
# assumptions only — NOT medical facts.
# ------------------------------------------------------------------
HYPOTHESIS_KEYS = {
    "stress": "Physiological stress pattern",
    "activity": "Activity / behavioral pattern",
    "recovery": "Recovery / autonomic pattern",
    "measurement": "Possible measurement/context effect",
}

# A nudge > 1 raises a hypothesis's support, < 1 lowers it. Neutral = 1.0.
MISSING_VARIABLES = {
    "recent_illness": {
        "outcomes": {
            "yes": {
                "prior": 0.3,
                "nudges": {"recovery": 1.8, "measurement": 1.4, "activity": 0.8},
            },
            "no": {
                "prior": 0.7,
                "nudges": {"recovery": 0.9, "stress": 1.1},
            },
        },
    },
    "medication_change": {
        "outcomes": {
            "yes": {
                "prior": 0.25,
                "nudges": {"recovery": 1.5, "measurement": 1.3},
            },
            "no": {
                "prior": 0.75,
                "nudges": {"stress": 1.05, "activity": 1.05},
            },
        },
    },
    "ferritin_or_iron_status": {
        "outcomes": {
            "low": {
                "prior": 0.25,
                "nudges": {"recovery": 1.7, "activity": 1.3},
            },
            "typical": {
                "prior": 0.45,
                "nudges": {"stress": 1.2, "recovery": 0.85},
            },
            "unknown": {
                "prior": 0.30,
                "nudges": {},  # uninformative outcome
            },
        },
    },
    "subjective_stress_level": {
        "outcomes": {
            "low": {
                "prior": 0.3,
                "nudges": {"stress": 0.5, "activity": 1.3},
            },
            "moderate": {
                "prior": 0.4,
                "nudges": {"stress": 1.2},
            },
            "high": {
                "prior": 0.3,
                "nudges": {"stress": 2.0, "recovery": 0.8},
            },
        },
    },
    "sleep_schedule_change": {
        "outcomes": {
            "yes": {
                "prior": 0.4,
                "nudges": {"activity": 1.9, "stress": 0.8},
            },
            "no": {
                "prior": 0.6,
                "nudges": {"activity": 0.8, "stress": 1.2, "recovery": 1.1},
            },
        },
    },
    "recent_intense_exercise": {
        "outcomes": {
            "yes": {
                "prior": 0.35,
                "nudges": {"activity": 1.6, "recovery": 1.3, "measurement": 1.2},
            },
            "no": {
                "prior": 0.65,
                "nudges": {"stress": 1.15},
            },
        },
    },
}

PROTOTYPE_ASSUMPTION_NOTE = (
    "Variable-to-hypothesis mappings are prototype demo assumptions, not medical "
    "conclusions."
)


def shannon_entropy(probs):
    """Shannon entropy (base 2) of a probability distribution."""
    p = np.asarray(probs, dtype=float)
    p = p[p > 0]
    if p.size == 0:
        return 0.0
    return float(-np.sum(p * np.log2(p)))


def normalize(dist):
    """Return a dict normalized to sum to 1 (safe against all-zero)."""
    total = sum(dist.values())
    if total <= 0:
        n = len(dist)
        return {k: 1.0 / n for k in dist}
    return {k: v / total for k, v in dist.items()}


def resolve_group_key(group_name):
    """Map a group display name to a short hypothesis key via substring match."""
    name = group_name.lower()
    for key, canonical in HYPOTHESIS_KEYS.items():
        if key in name:
            return key
    return None


def main():
    # ---------------------------------------------------------------
    # PART 1 — Read existing TRACE evidence
    # ---------------------------------------------------------------
    with open(BASELINE_SUMMARY_PATH) as f:
        baseline_summary = json.load(f)
    with open(CHANGE_SUMMARY_PATH) as f:
        change_summary = json.load(f)
    with open(RELATIONSHIP_SUMMARY_PATH) as f:
        relationship_summary = json.load(f)

    detected_change_day = int(change_summary["detected_change_day"])
    signal_onsets = change_summary.get("signal_onsets", {})
    active_signals = change_summary.get("signals_active_at_change_point", [])
    hypothesis_groups = relationship_summary["hypothesis_groups"]

    # Map each hypothesis group to a short key we can nudge.
    # group_key -> {"name":..., "support":...}
    groups = {}
    key_to_name = {}
    for g in hypothesis_groups:
        key = resolve_group_key(g["name"])
        if key is None:
            # Fall back to a slug so every group still participates.
            key = g["name"].lower().split()[0]
        groups[key] = float(g["support_score"])
        key_to_name[key] = g["name"]

    # ---------------------------------------------------------------
    # PART 3 — Current uncertainty (entropy of normalized support)
    # ---------------------------------------------------------------
    current_dist = normalize(groups)
    current_uncertainty = shannon_entropy(list(current_dist.values()))

    # ---------------------------------------------------------------
    # PART 4 — Approximate value of information per missing variable
    # ---------------------------------------------------------------
    # Build evidence helpers used for reasoning text.
    # Ordered onsets (signal -> day), earliest first.
    onset_pairs = sorted(
        ((s, d) for s, d in signal_onsets.items() if d is not None),
        key=lambda kv: kv[1],
    )
    earliest_signals = [s for s, _ in onset_pairs[:3]]

    candidate_results = []
    for var, spec in MISSING_VARIABLES.items():
        expected_entropy = 0.0
        related_keys = set()

        for outcome, odata in spec["outcomes"].items():
            prior = float(odata["prior"])
            nudges = odata.get("nudges", {})
            related_keys.update(nudges.keys())

            # Apply multiplicative nudges to a copy of current support, then
            # re-normalize to a valid distribution and measure entropy.
            adjusted = {}
            for key, support in current_dist.items():
                factor = nudges.get(key, 1.0)
                adjusted[key] = support * factor
            adjusted = normalize(adjusted)
            outcome_entropy = shannon_entropy(list(adjusted.values()))
            expected_entropy += prior * outcome_entropy

        information_gain = current_uncertainty - expected_entropy
        related_hypotheses = [
            key_to_name.get(k, k) for k in related_keys if k in current_dist
        ]

        candidate_results.append(
            {
                "variable": var,
                "information_gain": information_gain,
                "expected_uncertainty": expected_entropy,
                "related_hypotheses": sorted(related_hypotheses),
            }
        )

    # Rank by information gain (desc). Ranking comes only from the calculation.
    candidate_results.sort(key=lambda d: d["information_gain"], reverse=True)

    # ---------------------------------------------------------------
    # PART 5 — Explanations + example questions
    # ---------------------------------------------------------------
    def reasoning_for(var, related):
        related_txt = ", ".join(related) if related else "the current hypotheses"
        base = (
            f"Knowing '{var.replace('_', ' ')}' would reweight {related_txt} "
            f"relative to the pattern TRACE detected around Day {detected_change_day}."
        )
        # Tailor a little using actual evidence where it fits naturally.
        if var == "sleep_schedule_change" and "sleep_hours" in signal_onsets:
            if signal_onsets.get("sleep_hours") is not None:
                base = (
                    f"Sleep was among the earliest signals to move away from the "
                    f"personal baseline (onset Day {signal_onsets['sleep_hours']}). "
                    f"Knowing whether the patient's schedule changed around the "
                    f"detected change point (Day {detected_change_day}) could help "
                    f"distinguish behavioral/contextual explanations from broader "
                    f"physiological patterns."
                )
        elif var == "subjective_stress_level":
            base = (
                f"Stress-related signals ({', '.join([s for s in ['eda','stress_score','fatigue_score'] if s in signal_onsets])}) "
                f"were active around the change point. A subjective stress rating "
                f"would help confirm or down-weight the stress interpretation path."
            )
        elif var == "recent_intense_exercise" and "steps" in signal_onsets:
            base = (
                f"Activity signals shifted after the change point (steps onset "
                f"Day {signal_onsets.get('steps')}). Recent intense exercise could "
                f"help separate activity/behavioral explanations from recovery ones."
            )
        elif var == "recent_illness":
            base = (
                f"Several autonomic signals ({', '.join([s for s in ['resting_hr_bpm','respiratory_rate','temperature_f'] if s in signal_onsets])}) "
                f"shifted after Day {detected_change_day}. A recent illness flag "
                f"would help weigh recovery/context explanations."
            )
        elif var == "ferritin_or_iron_status":
            base = (
                f"Reduced HRV and activity after Day {detected_change_day} are "
                f"consistent with several explanations. Iron/ferritin context would "
                f"help separate recovery/autonomic from activity explanations."
            )
        elif var == "medication_change":
            base = (
                f"A medication change around Day {detected_change_day} could shift "
                f"autonomic readings, so it helps weigh recovery and measurement/"
                f"context explanations."
            )
        return base

    def question_for(var):
        q = {
            "recent_illness": (
                f"Were you unwell (e.g. a cold or infection) around the time TRACE "
                f"detected the first sustained shift (Day {detected_change_day})?"
            ),
            "medication_change": (
                f"Did any medication or supplement change around Day "
                f"{detected_change_day}?"
            ),
            "ferritin_or_iron_status": (
                "Do you have any recent information about your iron or ferritin "
                "status?"
            ),
            "subjective_stress_level": (
                f"How would you rate your stress level around Day "
                f"{detected_change_day} — low, moderate, or high?"
            ),
            "sleep_schedule_change": (
                f"Did your usual sleep schedule change around the time TRACE "
                f"detected the first sustained shift (Day {detected_change_day})?"
            ),
            "recent_intense_exercise": (
                f"Did you have any unusually intense exercise or training around "
                f"Day {detected_change_day}?"
            ),
        }
        return q.get(var, f"Can you share context about '{var}'?")

    # ---------------------------------------------------------------
    # Attach rank, reduction %, reasoning, question
    # ---------------------------------------------------------------
    candidate_information = []
    for rank, c in enumerate(candidate_results, start=1):
        reduction_pct = (
            (c["information_gain"] / current_uncertainty * 100.0)
            if current_uncertainty > 0 else 0.0
        )
        candidate_information.append(
            {
                "variable": c["variable"],
                "rank": rank,
                "information_gain": round(c["information_gain"], 4),
                "expected_uncertainty": round(c["expected_uncertainty"], 4),
                "uncertainty_reduction_percent": round(reduction_pct, 2),
                "related_hypotheses": c["related_hypotheses"],
                "reasoning": reasoning_for(c["variable"], c["related_hypotheses"]),
                "example_question": question_for(c["variable"]),
            }
        )

    # ---------------------------------------------------------------
    # PART 6 — Top recommendation
    # ---------------------------------------------------------------
    top = candidate_information[0]
    most_valuable = {
        "variable": top["variable"],
        "information_gain": top["information_gain"],
        "expected_uncertainty": top["expected_uncertainty"],
        "uncertainty_reduction_percent": top["uncertainty_reduction_percent"],
        "reasoning": top["reasoning"],
        "example_question": top["example_question"],
    }

    # ---------------------------------------------------------------
    # Assemble output
    # ---------------------------------------------------------------
    disclaimer = (
        "Information-value estimates are exploratory reasoning aids based on "
        "prototype assumptions. They do not represent medical advice, diagnostic "
        "testing recommendations, or clinical necessity."
    )

    output = {
        "patient_id": PATIENT_ID,
        "detected_change_day": detected_change_day,
        "current_uncertainty": round(current_uncertainty, 4),
        "uncertainty_method": (
            "Shannon entropy (base 2) of the normalized hypothesis support "
            "distribution; expected post-observation entropy computed over "
            "prototype outcome priors. " + PROTOTYPE_ASSUMPTION_NOTE
        ),
        "current_hypothesis_distribution": {
            key_to_name.get(k, k): round(v, 4) for k, v in current_dist.items()
        },
        "candidate_information": candidate_information,
        "most_valuable_missing_information": most_valuable,
        "disclaimer": disclaimer,
    }

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    with open(MISSING_SUMMARY_PATH, "w") as f:
        json.dump(output, f, indent=2)

    # ---------------------------------------------------------------
    # PRINT
    # ---------------------------------------------------------------
    print("=" * 66)
    print("TRACE Feature 4 — What Should We Learn Next? / BioMissing")
    print("=" * 66)
    print(f"Detected change day: Day {detected_change_day}")

    print("\n1. Current hypothesis distribution:")
    for k, v in current_dist.items():
        print(f"   {key_to_name.get(k, k):<38} {v:.4f}")

    print(f"\n2. Current uncertainty (Shannon entropy): "
          f"{current_uncertainty:.4f} bits")

    print("\n3-4. Ranking of missing variables by information gain:")
    print(f"   {'rank':<5}{'variable':<28}{'info_gain':<12}"
          f"{'exp_uncertainty':<16}{'reduction%'}")
    for c in candidate_information:
        print(
            f"   {c['rank']:<5}{c['variable']:<28}"
            f"{c['information_gain']:<12.4f}"
            f"{c['expected_uncertainty']:<16.4f}"
            f"{c['uncertainty_reduction_percent']:.2f}"
        )

    print("\n5. Most valuable missing information:")
    print(f"   variable        : {most_valuable['variable']}")
    print(f"   information_gain : {most_valuable['information_gain']:.4f} bits")
    print(f"   example_question : {most_valuable['example_question']}")

    print("\n6. Expected uncertainty reduction:")
    print(f"   {most_valuable['uncertainty_reduction_percent']:.2f}% "
          f"(from {current_uncertainty:.4f} to "
          f"{most_valuable['expected_uncertainty']:.4f} bits)")

    print(f"\nSaved missing-information summary JSON : {MISSING_SUMMARY_PATH}")


if __name__ == "__main__":
    main()
