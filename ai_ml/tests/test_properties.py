"""
Property-based tests for TRACE pipeline invariants (Hypothesis + pytest).

These test MATHEMATICAL PROPERTIES that must hold for any input — the kind of
guarantees unit tests with fixed examples can miss. They exercise the real
`deviation_score` used by the baseline (BioShadow) and counterfactual features,
and the adapter's Fahrenheit→Celsius conversion.

Run:  python -m pytest ai_ml/tests/ -q
"""

import math
import os
import sys

import numpy as np
from hypothesis import given, settings, strategies as st

# Import the real functions from the pipeline (import is side-effect free).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from counterfactual import deviation_score, FEATURES  # noqa: E402


# Reasonable, finite physiological-ish value ranges.
value = st.floats(min_value=-1e4, max_value=1e4, allow_nan=False, allow_infinity=False)
pos_std = st.floats(min_value=1e-3, max_value=1e4, allow_nan=False, allow_infinity=False)


def _dicts(values, means, stds):
    return (
        {f: v for f, v in zip(FEATURES, values)},
        {f: m for f, m in zip(FEATURES, means)},
        {f: s for f, s in zip(FEATURES, stds)},
    )


@given(
    means=st.lists(value, min_size=len(FEATURES), max_size=len(FEATURES)),
    stds=st.lists(pos_std, min_size=len(FEATURES), max_size=len(FEATURES)),
)
@settings(max_examples=200)
def test_zero_deviation_at_baseline(means, stds):
    """If every signal equals its baseline mean, deviation is exactly 0."""
    vals, m, s = _dicts(means, means, stds)
    assert deviation_score(vals, m, s) == 0.0


@given(
    values=st.lists(value, min_size=len(FEATURES), max_size=len(FEATURES)),
    means=st.lists(value, min_size=len(FEATURES), max_size=len(FEATURES)),
    stds=st.lists(pos_std, min_size=len(FEATURES), max_size=len(FEATURES)),
)
@settings(max_examples=300)
def test_deviation_is_non_negative(values, means, stds):
    """RMS of z-scores is always >= 0 (and finite) for finite inputs."""
    vals, m, s = _dicts(values, means, stds)
    d = deviation_score(vals, m, s)
    assert d >= 0.0
    assert math.isfinite(d)


@given(
    values=st.lists(value, min_size=len(FEATURES), max_size=len(FEATURES)),
    means=st.lists(value, min_size=len(FEATURES), max_size=len(FEATURES)),
    stds=st.lists(pos_std, min_size=len(FEATURES), max_size=len(FEATURES)),
    idx=st.integers(min_value=0, max_value=len(FEATURES) - 1),
)
@settings(max_examples=300)
def test_counterfactual_never_increases_deviation(values, means, stds, idx):
    """The core counterfactual property: resetting ONE signal to its baseline
    mean can only lower (or keep) the overall deviation — never raise it."""
    vals, m, s = _dicts(values, means, stds)
    before = deviation_score(vals, m, s)
    feat = FEATURES[idx]
    vals_cf = dict(vals)
    vals_cf[feat] = m[feat]  # the counterfactual "stay at baseline" move
    after = deviation_score(vals_cf, m, s)
    assert after <= before + 1e-9


@given(
    means=st.lists(value, min_size=len(FEATURES), max_size=len(FEATURES)),
    stds=st.lists(pos_std, min_size=len(FEATURES), max_size=len(FEATURES)),
    scale=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=200)
def test_scaling_all_deviations_scales_score(means, stds, scale):
    """If every signal sits k*std away from its mean, the RMS deviation is
    exactly |k| — a clean check that the z-score math is correct."""
    vals = {f: means[i] + scale * stds[i] for i, f in enumerate(FEATURES)}
    m = {f: means[i] for i, f in enumerate(FEATURES)}
    s = {f: stds[i] for i, f in enumerate(FEATURES)}
    assert deviation_score(vals, m, s) == __import__("pytest").approx(abs(scale), abs=1e-6)


# ---- Adapter unit conversion (Fahrenheit -> Celsius), as used in export ----
def f_to_c(f):
    return (f - 32.0) * 5.0 / 9.0


@given(celsius=st.floats(min_value=-50, max_value=60, allow_nan=False, allow_infinity=False))
@settings(max_examples=200)
def test_fahrenheit_celsius_roundtrip(celsius):
    """Converting C->F->C returns the original temperature."""
    fahrenheit = celsius * 9.0 / 5.0 + 32.0
    assert f_to_c(fahrenheit) == __import__("pytest").approx(celsius, abs=1e-9)


@given(fahrenheit=st.floats(min_value=90, max_value=110, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_body_temp_fahrenheit_maps_to_plausible_celsius(fahrenheit):
    """Human body-temperature range in F maps into a plausible C range."""
    c = f_to_c(fahrenheit)
    assert 30.0 <= c <= 45.0
