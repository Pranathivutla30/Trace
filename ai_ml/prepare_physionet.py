"""
TRACE — Temporal Reasoning & Analysis for Clinical Exploration
Real wearable data preparation: prepare_physionet.py

Converts the raw Empatica-E4-style wearable files for ONE participant from the
PhysioNet "Induced Stress and Structured Exercise Sessions" dataset into a small
TRACE-ready, 60-second-window dataset.

Key properties:
  * Reads directly from the Downloads dataset path; never copies raw files in.
  * Inspects and parses each Empatica file format correctly (HR/EDA/TEMP are
    single-column with a start-timestamp + sampling-rate header; ACC is 3-column
    x/y/z; IBI is irregular [offset_seconds, interval_seconds]).
  * Produces ONLY elapsed/relative time; no absolute patient-identifying
    timestamps are written to output.
  * Computes HRV (RMSSD) only where enough IBI observations exist; never
    fabricates or interpolates HRV.

This does NOT run the seven synthetic TRACE modules and does NOT modify them.
It is data preparation only — not diagnosis or medical advice.
"""

import argparse
import json
import math
import os
from datetime import datetime

import numpy as np
import pandas as pd

# ----- Configuration -----
DEFAULT_PARTICIPANT = "S12"
WINDOW_SECONDS = 60
MIN_IBI_FOR_RMSSD = 3  # need at least 3 IBI in a window to form >=2 successive diffs

DATASET_ROOT = (
    "/Users/lakshmipranathivutla/Downloads/"
    "wearable-device-dataset-from-induced-stress-and-structured-exercise-"
    "sessions-1.0.1/Wearable_Dataset/STRESS"
)
DATA_SOURCE = (
    "PhysioNet Wearable Device Dataset from Induced Stress and Structured "
    "Exercise Sessions v1.0.1"
)
EXPERIMENT = "STRESS"

HERE = os.path.dirname(__file__)
PROCESSED_DIR = os.path.normpath(
    os.path.join(HERE, "..", "data", "processed", "physionet")
)
OUTPUTS_DIR = os.path.normpath(os.path.join(HERE, "..", "outputs"))

DISCLAIMER = (
    "This output contains processed wearable measurements from a research "
    "dataset. TRACE uses these measurements for exploratory temporal analysis "
    "and does not provide diagnosis or medical advice."
)


# ------------------------------------------------------------------
# Parsing helpers
# ------------------------------------------------------------------
def _parse_start(token):
    """Parse an Empatica start token.

    This dataset variant stores a datetime string (e.g. '2013-02-24 10:26:46').
    The classic Empatica format stores unix seconds as a float. Handle both,
    returning a float count of seconds (epoch) so offsets can be computed.
    Absolute values never leave this module.
    """
    token = token.strip()
    try:
        return float(token)  # classic unix-seconds variant
    except ValueError:
        dt = datetime.strptime(token, "%Y-%m-%d %H:%M:%S")
        return dt.timestamp()


def read_single_column_signal(path):
    """Read an Empatica single-column file (HR / EDA / TEMP).

    Returns (start_epoch, fs_hz, values[np.ndarray]).
    Line 0 = start timestamp, line 1 = sampling frequency, lines 2+ = values.
    """
    with open(path, "r") as f:
        lines = [ln.strip() for ln in f if ln.strip() != ""]
    start = _parse_start(lines[0].split(",")[0])
    fs = float(lines[1].split(",")[0])
    values = np.array([float(x) for x in lines[2:]], dtype=float)
    return start, fs, values


def read_acc(path):
    """Read Empatica ACC (3-column x,y,z).

    Line 0 = start timestamp (x3), line 1 = sampling freq (x3), lines 2+ = x,y,z.
    Returns (start_epoch, fs_hz, magnitude[np.ndarray]).
    """
    with open(path, "r") as f:
        lines = [ln.strip() for ln in f if ln.strip() != ""]
    start = _parse_start(lines[0].split(",")[0])
    fs = float(lines[1].split(",")[0])
    xyz = np.array(
        [[float(v) for v in ln.split(",")] for ln in lines[2:]], dtype=float
    )
    magnitude = np.sqrt((xyz ** 2).sum(axis=1))
    return start, fs, magnitude


def read_ibi(path):
    """Read Empatica IBI (irregular).

    Line 0 = start timestamp (x2). Lines 1+ = [offset_seconds, interval_seconds].
    `offset_seconds` is time since the IBI start; `interval_seconds` is the beat
    interval. Returns (start_epoch, offsets[np.ndarray], intervals_ms[np.ndarray]).
    """
    with open(path, "r") as f:
        lines = [ln.strip() for ln in f if ln.strip() != ""]
    start = _parse_start(lines[0].split(",")[0])
    offsets = []
    intervals_ms = []
    for ln in lines[1:]:
        parts = ln.split(",")
        if len(parts) < 2:
            continue
        offsets.append(float(parts[0]))
        intervals_ms.append(float(parts[1]) * 1000.0)  # seconds -> milliseconds
    return start, np.array(offsets, dtype=float), np.array(intervals_ms, dtype=float)


def read_tags(path):
    """Read tags.csv -> list of absolute epoch seconds (one per line)."""
    if not os.path.exists(path):
        return []
    tags = []
    with open(path, "r") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                tags.append(_parse_start(ln.split(",")[0]))
            except (ValueError, IndexError):
                continue
    return tags


def sample_times(start_epoch, fs, n, origin):
    """Elapsed-seconds timestamps for a regularly sampled signal."""
    base = start_epoch - origin
    return base + np.arange(n) / fs


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Prepare one PhysioNet participant into TRACE windows."
    )
    parser.add_argument("--participant", default=DEFAULT_PARTICIPANT,
                        help="Participant id, e.g. S12")
    args = parser.parse_args()
    participant = args.participant

    pdir = os.path.join(DATASET_ROOT, participant)
    if not os.path.isdir(pdir):
        raise SystemExit(f"Participant directory not found: {pdir}")

    hr_path = os.path.join(pdir, "HR.csv")
    eda_path = os.path.join(pdir, "EDA.csv")
    temp_path = os.path.join(pdir, "TEMP.csv")
    acc_path = os.path.join(pdir, "ACC.csv")
    ibi_path = os.path.join(pdir, "IBI.csv")
    tags_path = os.path.join(pdir, "tags.csv")

    # ---------------- PART 2 — parse each signal ----------------
    hr_start, hr_fs, hr_vals = read_single_column_signal(hr_path)
    eda_start, eda_fs, eda_vals = read_single_column_signal(eda_path)
    temp_start, temp_fs, temp_vals = read_single_column_signal(temp_path)
    acc_start, acc_fs, acc_mag = read_acc(acc_path)
    ibi_start, ibi_offsets, ibi_ms = read_ibi(ibi_path)
    tag_epochs = read_tags(tags_path)

    # ---------------- PART 3 — elapsed time from earliest start ----------------
    # Anchor all signals to the earliest recording start so windows align.
    origin = min(hr_start, eda_start, temp_start, acc_start, ibi_start)

    hr_t = sample_times(hr_start, hr_fs, len(hr_vals), origin)
    eda_t = sample_times(eda_start, eda_fs, len(eda_vals), origin)
    temp_t = sample_times(temp_start, temp_fs, len(temp_vals), origin)
    acc_t = sample_times(acc_start, acc_fs, len(acc_mag), origin)
    # IBI absolute elapsed = (ibi_start - origin) + per-beat offset.
    ibi_t = (ibi_start - origin) + ibi_offsets
    tag_elapsed = sorted((t - origin) for t in tag_epochs)

    # Total recording duration = latest sample across signals.
    end_candidates = []
    for t in (hr_t, eda_t, temp_t, acc_t, ibi_t):
        if len(t):
            end_candidates.append(float(t[-1]))
    duration_s = max(end_candidates) if end_candidates else 0.0
    n_windows = int(math.ceil(duration_s / WINDOW_SECONDS)) if duration_s > 0 else 0

    # ---------------- PARTS 4,5,6 — build windows ----------------
    def window_slice(times, values, w0, w1):
        mask = (times >= w0) & (times < w1)
        return values[mask]

    rows = []
    for w in range(n_windows):
        w0 = w * WINDOW_SECONDS
        w1 = w0 + WINDOW_SECONDS

        hr_w = window_slice(hr_t, hr_vals, w0, w1)
        eda_w = window_slice(eda_t, eda_vals, w0, w1)
        temp_w = window_slice(temp_t, temp_vals, w0, w1)
        acc_w = window_slice(acc_t, acc_mag, w0, w1)
        ibi_mask = (ibi_t >= w0) & (ibi_t < w1)
        ibi_w = ibi_ms[ibi_mask]

        # HRV — RMSSD only if enough beats; never fabricate.
        if len(ibi_w) >= MIN_IBI_FOR_RMSSD:
            diffs = np.diff(ibi_w)
            rmssd = float(np.sqrt(np.mean(diffs ** 2)))
        else:
            rmssd = np.nan

        hr_mean = float(np.mean(hr_w)) if len(hr_w) else np.nan
        eda_mean = float(np.mean(eda_w)) if len(eda_w) else np.nan
        temp_mean = float(np.mean(temp_w)) if len(temp_w) else np.nan
        acc_mean = float(np.mean(acc_w)) if len(acc_w) else np.nan

        # Data quality: fraction of the regularly-sampled signals that reached
        # a reasonable share of their expected samples this window. Transparent
        # and simple; IBI is excluded because irregular IBI gaps are normal and
        # must NOT be treated as a medical abnormality.
        expected = {
            "hr": hr_fs * WINDOW_SECONDS,
            "eda": eda_fs * WINDOW_SECONDS,
            "temp": temp_fs * WINDOW_SECONDS,
            "acc": acc_fs * WINDOW_SECONDS,
        }
        got = {"hr": len(hr_w), "eda": len(eda_w),
               "temp": len(temp_w), "acc": len(acc_w)}
        completeness = [
            min(1.0, got[k] / expected[k]) for k in expected if expected[k] > 0
        ]
        data_quality_score = round(float(np.mean(completeness)), 4) if completeness else 0.0

        rows.append({
            "window": w,
            "elapsed_minutes": round(w0 / 60.0, 4),
            "heart_rate_bpm": round(hr_mean, 4) if not np.isnan(hr_mean) else np.nan,
            "hrv_rmssd_ms": round(rmssd, 4) if not np.isnan(rmssd) else np.nan,
            "eda_mean": round(eda_mean, 6) if not np.isnan(eda_mean) else np.nan,
            "temperature_c": round(temp_mean, 4) if not np.isnan(temp_mean) else np.nan,
            "activity_mean": round(acc_mean, 4) if not np.isnan(acc_mean) else np.nan,
            "hr_samples": int(len(hr_w)),
            "ibi_samples": int(len(ibi_w)),
            "eda_samples": int(len(eda_w)),
            "temperature_samples": int(len(temp_w)),
            "acc_samples": int(len(acc_w)),
            "data_quality_score": data_quality_score,
        })

    windows_df = pd.DataFrame(rows, columns=[
        "window", "elapsed_minutes", "heart_rate_bpm", "hrv_rmssd_ms",
        "eda_mean", "temperature_c", "activity_mean",
        "hr_samples", "ibi_samples", "eda_samples", "temperature_samples",
        "acc_samples", "data_quality_score",
    ])

    # ---------------- PART 8 — write outputs ----------------
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    csv_path = os.path.join(PROCESSED_DIR, f"{participant}_trace_windows.csv")
    windows_df.to_csv(csv_path, index=False)

    # Missingness per processed signal (fraction of windows with no value).
    processed_signals = [
        "heart_rate_bpm", "hrv_rmssd_ms", "eda_mean",
        "temperature_c", "activity_mean",
    ]
    missingness = {
        sig: round(float(windows_df[sig].isna().mean()), 4)
        for sig in processed_signals
    }

    signal_summary = {
        "HR": {"sampling_hz": hr_fs, "n_raw_samples": int(len(hr_vals))},
        "EDA": {"sampling_hz": eda_fs, "n_raw_samples": int(len(eda_vals))},
        "TEMP": {"sampling_hz": temp_fs, "n_raw_samples": int(len(temp_vals))},
        "ACC": {"sampling_hz": acc_fs, "n_raw_samples": int(len(acc_mag))},
        "IBI": {"sampling_hz": None, "n_raw_samples": int(len(ibi_ms)),
                "note": "irregular inter-beat intervals; not a fixed rate"},
    }

    available_event_tags = [
        {"name": f"event_{i+1}", "elapsed_minutes": round(t / 60.0, 4)}
        for i, t in enumerate(tag_elapsed)
    ]

    summary = {
        "participant_id": participant,
        "data_source": DATA_SOURCE,
        "experiment": EXPERIMENT,
        "raw_signals_used": ["HR", "IBI", "EDA", "TEMP", "ACC"],
        "window_size_seconds": WINDOW_SECONDS,
        "number_of_windows": int(n_windows),
        "recording_duration_minutes": round(duration_s / 60.0, 4),
        "available_event_tags": available_event_tags,
        "missingness": missingness,
        "signal_summary": signal_summary,
        "disclaimer": DISCLAIMER,
    }
    summary_path = os.path.join(OUTPUTS_DIR, f"real_{participant}_preprocessing_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # ---------------- PART 9 — validation + prints ----------------
    print("=" * 70)
    print(f"TRACE — PhysioNet preprocessing  |  participant {participant}")
    print("=" * 70)

    print("\n1. First raw values detected per source format:")
    print(f"   HR   start+fs header, values[:3]   = {hr_vals[:3].tolist()}")
    print(f"   EDA  start+fs header, values[:3]   = {eda_vals[:3].tolist()}")
    print(f"   TEMP start+fs header, values[:3]   = {temp_vals[:3].tolist()}")
    print(f"   ACC  magnitude[:3]                 = {np.round(acc_mag[:3],3).tolist()}")
    print(f"   IBI  [offset_s, interval_ms][:3]   = "
          f"{list(zip(np.round(ibi_offsets[:3],3).tolist(), np.round(ibi_ms[:3],2).tolist()))}")

    print("\n2. Detected sampling frequencies (Hz):")
    print(f"   HR={hr_fs}  EDA={eda_fs}  TEMP={temp_fs}  ACC={acc_fs}  "
          f"IBI=irregular")

    print(f"\n3. Recording duration: {duration_s/60.0:.2f} minutes "
          f"({duration_s:.0f} s)")
    print(f"4. Number of {WINDOW_SECONDS}s windows: {n_windows}")

    print("\n5. Missing percentage per processed signal:")
    for sig, frac in missingness.items():
        print(f"   {sig:<18} {frac*100:.1f}%")

    print("\n6. First 5 processed windows:")
    print(windows_df.head().to_string(index=False))

    print("\n7. Event timestamps (elapsed minutes):")
    if available_event_tags:
        for e in available_event_tags:
            print(f"   {e['name']:<10} {e['elapsed_minutes']:.3f} min")
    else:
        print("   (no event tags found)")

    # 8 & 9 — verify round-trip
    reread = pd.read_csv(csv_path)
    with open(summary_path) as f:
        _ = json.load(f)
    print(f"\n8. Output CSV re-read OK: {reread.shape} rows/cols -> {csv_path}")
    print(f"9. Summary JSON parsed OK -> {summary_path}")


if __name__ == "__main__":
    main()
