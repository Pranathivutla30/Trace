"""
TRACE — Temporal Reasoning & Analysis for Clinical Exploration
Real-data participant selection: select_real_participant.py

Scans the full PhysioNet STRESS dataset, builds the same 60-second TRACE window
format for each participant IN MEMORY (reusing the parsing functions from
prepare_physionet.py), and ranks participants by how clearly they show a
baseline-to-change temporal pattern — purely to pick a visually useful real-data
demo recording.

The selection_score is ONLY for choosing a demonstration recording. It is NOT a
medical risk score, NOT a ranking of health, stress severity, or disease, and
participant IDs are NOT treated as demographic labels. Event tags are used only
as supporting context, with no assumed meaning and no causal claim.

This module reads raw files directly, does not copy them, does not permanently
write per-participant processed CSVs, and does not modify any existing file.
"""

import json
import math
import os
from datetime import datetime

import numpy as np

# Reuse parsing + constants from the preprocessor (do not duplicate parsing).
import prepare_physionet
from prepare_physionet import (
    DATASET_ROOT,
    DATA_SOURCE,
    EXPERIMENT,
    WINDOW_SECONDS,
    MIN_IBI_FOR_RMSSD,
    read_single_column_signal,
    read_acc,
    read_tags,
    sample_times,
)


# ------------------------------------------------------------------
# Robust start-timestamp parsing for the full dataset.
#
# prepare_physionet._parse_start handles S12's format (unix float or
# "%Y-%m-%d %H:%M:%S"), but other participants store fractional seconds
# (e.g. "1959-10-05 21:01:14.828125"). We must NOT modify prepare_physionet.py,
# so we install a more tolerant parser onto the imported module at runtime.
# This only affects this batch-selection process; the file on disk is unchanged.
# ------------------------------------------------------------------
def _tolerant_parse_start(token):
    token = token.strip()
    try:
        return float(token)  # classic unix-seconds variant
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(token, fmt).timestamp()
        except ValueError:
            continue
    # Last resort: pandas can infer many formats.
    import pandas as pd
    return pd.to_datetime(token).timestamp()


# Install the tolerant parser so the reused readers can handle every variant.
prepare_physionet._parse_start = _tolerant_parse_start


def read_ibi_resilient(path):
    """Resilient IBI reader for the batch scan.

    Some participants' IBI.csv include a header row (e.g. 'timestamp, IBI') or
    other non-numeric lines that the imported read_ibi does not expect. This
    reuses the same semantics — line 0 = start timestamp, subsequent lines =
    [offset_seconds, interval_seconds] -> ms — but skips any row that is not a
    clean numeric pair. It does not modify prepare_physionet.py.
    """
    with open(path, "r") as f:
        lines = [ln.strip() for ln in f if ln.strip() != ""]
    if not lines:
        return 0.0, np.array([]), np.array([])
    start = _tolerant_parse_start(lines[0].split(",")[0])
    offsets, intervals_ms = [], []
    for ln in lines[1:]:
        parts = ln.split(",")
        if len(parts) < 2:
            continue
        try:
            off = float(parts[0])
            interval = float(parts[1])
        except ValueError:
            continue  # skip header/non-numeric rows; do not fabricate
        offsets.append(off)
        intervals_ms.append(interval * 1000.0)  # seconds -> milliseconds
    return start, np.array(offsets, dtype=float), np.array(intervals_ms, dtype=float)

# ----- Configuration -----
REQUIRED_FILES = ["HR.csv", "IBI.csv", "EDA.csv", "TEMP.csv", "ACC.csv"]
SELECTION_FEATURES = [
    "heart_rate_bpm",
    "hrv_rmssd_ms",
    "eda_mean",
    "temperature_c",
    "activity_mean",
]

# Eligibility thresholds.
MIN_USABLE_WINDOWS = 15
MIN_MEAN_QUALITY = 0.80

# Baseline settings.
BASELINE_FRACTION = 0.20
MIN_BASELINE_WINDOWS = 3

# TRACE analytical criteria (NOT medical thresholds).
Z_DEVIATION = 2.0
EVENT_WINDOW_MIN = 1.0   # +/- 1 minute for event alignment

# Visible selection-score weights (applied to cross-participant normalized
# components). These shape demo selection only.
SELECTION_WEIGHTS = {
    "separation": 0.30,       # post-baseline minus baseline deviation
    "peak_deviation": 0.20,
    "signal_agreement": 0.20,
    "sustained_fraction": 0.20,
    "data_quality": 0.10,
}

HERE = os.path.dirname(__file__)
OUTPUTS_DIR = os.path.normpath(os.path.join(HERE, "..", "outputs"))
SELECTION_PATH = os.path.join(OUTPUTS_DIR, "real_participant_selection.json")

DISCLAIMER = (
    "This ranking identifies recordings that provide clear temporal variation "
    "for demonstrating TRACE. It is not a ranking of participant health, stress "
    "severity, disease risk, or clinical status."
)


def safe_std(x):
    """Sample std with a floor so near-zero variance can't blow up z-scores."""
    if len(x) < 2:
        return np.nan
    s = float(np.nanstd(x, ddof=1))
    return s if s > 1e-9 else 1e-9


def build_windows_in_memory(pdir):
    """Build the 60-second TRACE windows for one participant, in memory.

    Reuses the raw parsers from prepare_physionet. Returns (windows, tags_min)
    where windows is a list of dicts and tags_min is event elapsed minutes.
    Mirrors the windowing in prepare_physionet without re-writing the parsers.
    """
    hr_start, hr_fs, hr_vals = read_single_column_signal(os.path.join(pdir, "HR.csv"))
    eda_start, eda_fs, eda_vals = read_single_column_signal(os.path.join(pdir, "EDA.csv"))
    temp_start, temp_fs, temp_vals = read_single_column_signal(os.path.join(pdir, "TEMP.csv"))
    acc_start, acc_fs, acc_mag = read_acc(os.path.join(pdir, "ACC.csv"))
    ibi_start, ibi_offsets, ibi_ms = read_ibi_resilient(os.path.join(pdir, "IBI.csv"))
    tag_epochs = read_tags(os.path.join(pdir, "tags.csv"))

    # Anchor the recording origin to the regularly-sampled signals only.
    # Some participants' IBI.csv carry a corrupt/placeholder start timestamp
    # (e.g. a 1959 date while the real signals are 2013). The IBI *offsets* are
    # already relative seconds from recording start, so we align IBI to the
    # shared origin rather than letting its bogus header define origin/duration.
    regular_starts = [hr_start, eda_start, temp_start, acc_start]
    origin = min(regular_starts)

    hr_t = sample_times(hr_start, hr_fs, len(hr_vals), origin)
    eda_t = sample_times(eda_start, eda_fs, len(eda_vals), origin)
    temp_t = sample_times(temp_start, temp_fs, len(temp_vals), origin)
    acc_t = sample_times(acc_start, acc_fs, len(acc_mag), origin)

    # Decide whether the IBI header start is consistent with the real signals.
    # If it falls within the regular recording span, honor it; otherwise treat
    # IBI offsets as measured from the shared origin (offset 0 == origin).
    regular_end = max(
        (float(t[-1]) for t in (hr_t, eda_t, temp_t, acc_t) if len(t)),
        default=0.0,
    )
    ibi_rel_start = ibi_start - origin
    if 0.0 <= ibi_rel_start <= regular_end + WINDOW_SECONDS:
        ibi_t = ibi_rel_start + ibi_offsets
    else:
        ibi_t = ibi_offsets.copy()  # bogus IBI header -> align to shared origin

    tags_min = sorted((t - origin) / 60.0 for t in tag_epochs)

    # Recording duration is defined by the regularly-sampled signals only, so a
    # corrupt IBI timestamp cannot inflate the window count.
    end_candidates = [float(t[-1]) for t in (hr_t, eda_t, temp_t, acc_t) if len(t)]
    duration_s = max(end_candidates) if end_candidates else 0.0
    n_windows = int(math.ceil(duration_s / WINDOW_SECONDS)) if duration_s > 0 else 0

    # Sample-time arrays are strictly increasing, so window membership can be
    # found with binary search (searchsorted) instead of scanning every array
    # for every window. This keeps the full 37-participant scan fast.
    def wslice(times, values, w0, w1):
        lo = int(np.searchsorted(times, w0, side="left"))
        hi = int(np.searchsorted(times, w1, side="left"))
        return values[lo:hi]

    windows = []
    for w in range(n_windows):
        w0, w1 = w * WINDOW_SECONDS, w * WINDOW_SECONDS + WINDOW_SECONDS
        hr_w = wslice(hr_t, hr_vals, w0, w1)
        eda_w = wslice(eda_t, eda_vals, w0, w1)
        temp_w = wslice(temp_t, temp_vals, w0, w1)
        acc_w = wslice(acc_t, acc_mag, w0, w1)
        ibi_w = wslice(ibi_t, ibi_ms, w0, w1)

        rmssd = (
            float(np.sqrt(np.mean(np.diff(ibi_w) ** 2)))
            if len(ibi_w) >= MIN_IBI_FOR_RMSSD else np.nan
        )

        expected = {"hr": hr_fs * WINDOW_SECONDS, "eda": eda_fs * WINDOW_SECONDS,
                    "temp": temp_fs * WINDOW_SECONDS, "acc": acc_fs * WINDOW_SECONDS}
        got = {"hr": len(hr_w), "eda": len(eda_w), "temp": len(temp_w), "acc": len(acc_w)}
        comp = [min(1.0, got[k] / expected[k]) for k in expected if expected[k] > 0]
        dq = float(np.mean(comp)) if comp else 0.0

        windows.append({
            "window": w,
            "elapsed_minutes": w0 / 60.0,
            "heart_rate_bpm": float(np.mean(hr_w)) if len(hr_w) else np.nan,
            "hrv_rmssd_ms": rmssd,
            "eda_mean": float(np.mean(eda_w)) if len(eda_w) else np.nan,
            "temperature_c": float(np.mean(temp_w)) if len(temp_w) else np.nan,
            "activity_mean": float(np.mean(acc_w)) if len(acc_w) else np.nan,
            "data_quality_score": dq,
        })
    return windows, tags_min


def discover_participants():
    """Discover participant dirs that contain all required files."""
    if not os.path.isdir(DATASET_ROOT):
        raise SystemExit(f"Dataset root not found: {DATASET_ROOT}")
    found = []
    for name in sorted(os.listdir(DATASET_ROOT)):
        pdir = os.path.join(DATASET_ROOT, name)
        if not os.path.isdir(pdir):
            continue
        if all(os.path.exists(os.path.join(pdir, fn)) for fn in REQUIRED_FILES):
            found.append(name)
    return found


def analyze_participant(name):
    """Return a per-participant metrics dict (pre-normalization), or an
    exclusion record."""
    pdir = os.path.join(DATASET_ROOT, name)
    windows, tags_min = build_windows_in_memory(pdir)

    n_windows = len(windows)
    dq_vals = np.array([w["data_quality_score"] for w in windows], dtype=float)
    mean_dq = float(np.mean(dq_vals)) if n_windows else 0.0

    # Missingness per processed signal.
    missing = {}
    for feat in SELECTION_FEATURES:
        col = np.array([w[feat] for w in windows], dtype=float)
        missing[feat] = float(np.mean(np.isnan(col))) if n_windows else 1.0

    # Eligibility filter.
    reasons = []
    if n_windows < MIN_USABLE_WINDOWS:
        reasons.append(f"only {n_windows} windows (<{MIN_USABLE_WINDOWS})")
    if mean_dq < MIN_MEAN_QUALITY:
        reasons.append(f"mean data quality {mean_dq:.2f} (<{MIN_MEAN_QUALITY})")

    base = {
        "participant_id": name,
        "number_of_windows": n_windows,
        "mean_data_quality": round(mean_dq, 4),
        "missingness": {k: round(v, 4) for k, v in missing.items()},
    }
    if reasons:
        base["eligible"] = False
        base["exclusion_reasons"] = reasons
        return base

    # ---- Provisional personal baseline (first 20% of windows) ----
    n_base = max(MIN_BASELINE_WINDOWS, int(round(BASELINE_FRACTION * n_windows)))
    n_base = min(n_base, n_windows - 1)  # leave at least one later window
    base_windows = windows[:n_base]
    later_windows = windows[n_base:]

    base_mean, base_std = {}, {}
    for feat in SELECTION_FEATURES:
        col = np.array([w[feat] for w in base_windows], dtype=float)
        col = col[~np.isnan(col)]
        base_mean[feat] = float(np.mean(col)) if len(col) else np.nan
        base_std[feat] = safe_std(col) if len(col) >= 2 else np.nan

    def window_z(w):
        zs = {}
        for feat in SELECTION_FEATURES:
            val = w[feat]
            m, s = base_mean[feat], base_std[feat]
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

    base_devs = [deviation_and_agreement(w)[0] for w in base_windows]
    base_devs = [d for d in base_devs if not np.isnan(d)]
    baseline_mean_deviation = float(np.mean(base_devs)) if base_devs else 0.0
    baseline_std_deviation = safe_std(np.array(base_devs)) if len(base_devs) >= 2 else 0.0

    later_dev, later_agree = [], []
    accum_z = {feat: [] for feat in SELECTION_FEATURES}
    for w in later_windows:
        dev, agree, zs = deviation_and_agreement(w)
        if not np.isnan(dev):
            later_dev.append(dev)
            later_agree.append(agree)
            for feat, zval in zs.items():
                accum_z[feat].append(abs(zval))

    post_baseline_mean_deviation = float(np.mean(later_dev)) if later_dev else 0.0
    peak_deviation = float(np.max(later_dev)) if later_dev else 0.0
    mean_signal_agreement = float(np.mean(later_agree)) if later_agree else 0.0

    # Sustained change: later windows above baseline mean + 2*baseline std.
    sustain_threshold = baseline_mean_deviation + 2.0 * (baseline_std_deviation or 0.0)
    sustained_change_fraction = (
        float(np.mean([d > sustain_threshold for d in later_dev]))
        if later_dev else 0.0
    )

    # Strongest changed signals = highest mean |z| among later windows.
    strongest = sorted(
        ((feat, float(np.mean(vals))) for feat, vals in accum_z.items() if vals),
        key=lambda kv: kv[1], reverse=True,
    )
    strongest_changed_signals = [f for f, _ in strongest[:3]]

    # ---- Event alignment as SUPPORTING context (not causal) ----
    event_overlap_fraction = 0.0
    if tags_min and later_dev:
        # Large deviation windows = above the same sustain threshold.
        big_minutes = [
            later_windows[i]["elapsed_minutes"]
            for i, d in enumerate(later_dev) if d > sustain_threshold
        ]
        if big_minutes:
            near = 0
            for m in big_minutes:
                if any(abs(m - t) <= EVENT_WINDOW_MIN for t in tags_min):
                    near += 1
            event_overlap_fraction = near / len(big_minutes)

    base.update({
        "eligible": True,
        "baseline_windows": int(n_base),
        "baseline_mean_deviation": round(baseline_mean_deviation, 4),
        "post_baseline_mean_deviation": round(post_baseline_mean_deviation, 4),
        "peak_deviation": round(peak_deviation, 4),
        "mean_signal_agreement": round(mean_signal_agreement, 4),
        "sustained_change_fraction": round(sustained_change_fraction, 4),
        "event_overlap_fraction": round(event_overlap_fraction, 4),
        "strongest_changed_signals": strongest_changed_signals,
        # raw components for cross-participant normalization
        "_separation": post_baseline_mean_deviation - baseline_mean_deviation,
    })
    return base


def normalize_across(values):
    """Min-max normalize a list of floats to 0-1 (flat -> zeros)."""
    arr = np.array(values, dtype=float)
    lo, hi = np.min(arr), np.max(arr)
    if hi - lo == 0:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)


def main():
    discovered = discover_participants()
    analyses = [analyze_participant(name) for name in discovered]

    eligible = [a for a in analyses if a.get("eligible")]
    excluded = [a for a in analyses if not a.get("eligible")]

    # ---- Cross-participant normalization, then weighted selection_score ----
    if eligible:
        sep_n = normalize_across([a["_separation"] for a in eligible])
        peak_n = normalize_across([a["peak_deviation"] for a in eligible])
        agree_n = normalize_across([a["mean_signal_agreement"] for a in eligible])
        sust_n = normalize_across([a["sustained_change_fraction"] for a in eligible])
        dq_n = normalize_across([a["mean_data_quality"] for a in eligible])

        for i, a in enumerate(eligible):
            score = (
                SELECTION_WEIGHTS["separation"] * sep_n[i]
                + SELECTION_WEIGHTS["peak_deviation"] * peak_n[i]
                + SELECTION_WEIGHTS["signal_agreement"] * agree_n[i]
                + SELECTION_WEIGHTS["sustained_fraction"] * sust_n[i]
                + SELECTION_WEIGHTS["data_quality"] * dq_n[i]
            )
            a["selection_score"] = round(float(score), 4)

    eligible.sort(key=lambda a: a.get("selection_score", 0.0), reverse=True)

    def public_record(a):
        return {
            "participant_id": a["participant_id"],
            "selection_score": a.get("selection_score", 0.0),
            "number_of_windows": a["number_of_windows"],
            "mean_data_quality": a["mean_data_quality"],
            "baseline_windows": a.get("baseline_windows"),
            "post_baseline_mean_deviation": a.get("post_baseline_mean_deviation"),
            "peak_deviation": a.get("peak_deviation"),
            "mean_signal_agreement": a.get("mean_signal_agreement"),
            "sustained_change_fraction": a.get("sustained_change_fraction"),
            "event_overlap_fraction": a.get("event_overlap_fraction"),
            "strongest_changed_signals": a.get("strongest_changed_signals"),
        }

    top_5 = [public_record(a) for a in eligible[:5]]
    recommended = top_5[0]["participant_id"] if top_5 else None

    participants_excluded = [
        {
            "participant_id": a["participant_id"],
            "number_of_windows": a["number_of_windows"],
            "mean_data_quality": a["mean_data_quality"],
            "exclusion_reasons": a["exclusion_reasons"],
        }
        for a in excluded
    ]

    ranking_method = (
        "Per-participant provisional baseline (first 20% of windows); later-window "
        "multivariate z-deviation and signal agreement; components "
        "(baseline/later separation, peak deviation, signal agreement, sustained "
        "change fraction, data quality) min-max normalized across participants, "
        "then combined with visible weights "
        f"{SELECTION_WEIGHTS}. Event overlap is supporting context only."
    )

    output = {
        "dataset": DATA_SOURCE,
        "experiment": EXPERIMENT,
        "participants_discovered": discovered,
        "participants_eligible": [a["participant_id"] for a in eligible],
        "participants_excluded": participants_excluded,
        "ranking_method": ranking_method,
        "top_5": top_5,
        "recommended_participant": recommended,
        "disclaimer": DISCLAIMER,
    }

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    with open(SELECTION_PATH, "w") as f:
        json.dump(output, f, indent=2)

    # ---------------- PRINT ----------------
    print("=" * 70)
    print("TRACE — Real participant selection (STRESS experiment)")
    print("=" * 70)
    print(f"1. Participants discovered: {len(discovered)}")
    print(f"2. Participants eligible:   {len(eligible)}")

    print("\n3. Exclusions:")
    if participants_excluded:
        for e in participants_excluded:
            print(f"   {e['participant_id']:<8} "
                  f"windows={e['number_of_windows']:<4} "
                  f"dq={e['mean_data_quality']:.2f}  -> "
                  f"{'; '.join(e['exclusion_reasons'])}")
    else:
        print("   (none)")

    print("\n4-9. Top rankings:")
    header = (f"   {'rank':<5}{'id':<8}{'score':<9}{'wins':<6}{'dq':<7}"
              f"{'peak_dev':<10}{'sustain':<9}{'strongest_signals'}")
    print(header)
    for rank, a in enumerate(eligible[:10], start=1):
        print(
            f"   {rank:<5}{a['participant_id']:<8}"
            f"{a.get('selection_score', 0.0):<9.4f}"
            f"{a['number_of_windows']:<6}"
            f"{a['mean_data_quality']:<7.2f}"
            f"{a.get('peak_deviation', 0):<10.3f}"
            f"{a.get('sustained_change_fraction', 0):<9.3f}"
            f"{', '.join(a.get('strongest_changed_signals', []))}"
        )

    print(f"\n10. Recommended participant: {recommended}")
    print(f"\nSaved selection JSON : {SELECTION_PATH}")


if __name__ == "__main__":
    main()
