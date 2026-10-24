"""
TRACE — Temporal Reasoning & Analysis for Clinical Exploration
Synthetic longitudinal patient generator (hackathon demo data).

This script generates a controlled 30-day synthetic physiological record for a
single patient. It produces a stable personal baseline for the first ~17 days,
then introduces GRADUAL drift across several signals beginning on staggered days.

This is NOT a diagnostic tool. It does not label disease, infer conditions, or
recommend treatment. It only synthesizes realistic-looking longitudinal signals
with a known, controlled pattern change for downstream TRACE analysis.
"""

import os

import numpy as np
import pandas as pd

# Reproducibility
SEED = 42
rng = np.random.default_rng(SEED)

N_DAYS = 30
START_DATE = "2025-01-01"


def ramp(day, start_day, per_day, max_days=None):
    """Return a gradual cumulative drift that begins on `start_day`.

    Before `start_day` the drift is 0. From `start_day` onward it grows
    linearly by `per_day` for each elapsed day. `max_days` optionally caps
    how many days the ramp keeps growing (it holds flat afterwards).
    """
    if day < start_day:
        return 0.0
    elapsed = day - start_day + 1
    if max_days is not None:
        elapsed = min(elapsed, max_days)
    return per_day * elapsed


rows = []
dates = pd.date_range(start=START_DATE, periods=N_DAYS, freq="D")

for i in range(N_DAYS):
    day = i + 1  # 1-indexed day number

    # ----- Stable personal baselines (centers of each signal) -----
    base_sleep = 7.55          # hrs, baseline 7.3-7.8
    base_hrv = 62.0            # ms, baseline 58-66
    base_rhr = 62.5           # bpm, baseline 60-65
    base_steps = 8750         # baseline 8000-9500
    base_temp = 98.05         # F, baseline 97.8-98.3
    base_rr = 15.0            # breaths/min, baseline 14-16
    base_eda = 2.0            # microsiemens, stable low baseline
    base_fatigue = 2.0        # 1-3 baseline
    base_stress = 2.0         # 1-3 baseline

    # ----- Gradual drifts, each beginning around a specific day -----
    # Day 18: sleep gradually decreases
    sleep_drift = -ramp(day, 18, per_day=0.18)
    # Day 20: HRV gradually decreases
    hrv_drift = -ramp(day, 20, per_day=1.6)
    # Day 21: EDA / stress begin increasing
    eda_drift = ramp(day, 21, per_day=0.35)
    stress_drift = ramp(day, 21, per_day=0.45)
    # Day 23: resting heart rate gradually increases
    rhr_drift = ramp(day, 23, per_day=0.9)
    # Day 25: steps / activity gradually decreases
    steps_drift = -ramp(day, 25, per_day=550)
    # Day 27: temperature slightly increases
    temp_drift = ramp(day, 27, per_day=0.12)

    # Fatigue gradually increases as the overall pattern changes.
    # It responds to the combined physiological drift, starting with sleep.
    fatigue_drift = ramp(day, 18, per_day=0.28)

    # ----- Realistic small daily random variation (noise) -----
    sleep = base_sleep + sleep_drift + rng.normal(0, 0.15)
    hrv = base_hrv + hrv_drift + rng.normal(0, 1.2)
    rhr = base_rhr + rhr_drift + rng.normal(0, 0.8)
    steps = base_steps + steps_drift + rng.normal(0, 300)
    temp = base_temp + temp_drift + rng.normal(0, 0.08)
    rr = base_rr + (hrv_drift * -0.05) + rng.normal(0, 0.3)
    eda = base_eda + eda_drift + rng.normal(0, 0.2)
    fatigue = base_fatigue + fatigue_drift + rng.normal(0, 0.25)
    stress = base_stress + stress_drift + rng.normal(0, 0.3)

    # ----- Clamp to physically sensible ranges and round -----
    sleep = round(float(np.clip(sleep, 3.5, 10.0)), 2)
    hrv = round(float(np.clip(hrv, 20.0, 120.0)), 1)
    rhr = round(float(np.clip(rhr, 45.0, 110.0)), 1)
    steps = int(np.clip(round(steps), 0, 30000))
    temp = round(float(np.clip(temp, 96.5, 101.0)), 2)
    rr = round(float(np.clip(rr, 10.0, 25.0)), 1)
    eda = round(float(np.clip(eda, 0.1, 20.0)), 2)
    fatigue = round(float(np.clip(fatigue, 0.0, 10.0)), 2)
    stress = round(float(np.clip(stress, 0.0, 10.0)), 2)

    rows.append(
        {
            "date": dates[i].strftime("%Y-%m-%d"),
            "day": day,
            "sleep_hours": sleep,
            "hrv_ms": hrv,
            "resting_hr_bpm": rhr,
            "steps": steps,
            "temperature_f": temp,
            "respiratory_rate": rr,
            "eda": eda,
            "fatigue_score": fatigue,
            "stress_score": stress,
        }
    )

df = pd.DataFrame(
    rows,
    columns=[
        "date",
        "day",
        "sleep_hours",
        "hrv_ms",
        "resting_hr_bpm",
        "steps",
        "temperature_f",
        "respiratory_rate",
        "eda",
        "fatigue_score",
        "stress_score",
    ],
)

# ----- Save -----
output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.normpath(os.path.join(output_dir, "patient_001.csv"))
df.to_csv(output_path, index=False)

# ----- Report -----
print("Dataset shape:", df.shape)
print("\nColumn names:", list(df.columns))
print("\nFirst 5 rows:")
print(df.head().to_string(index=False))
print("\nLast 5 rows:")
print(df.tail().to_string(index=False))
print("\nSaved file path:", output_path)
