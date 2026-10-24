"""Pydantic response schemas for the TRACE API.

Signal fields are OPTIONAL: real wearable data lacks some signals the synthetic
set has (e.g. no HRV/sleep in the real stress recording), so every signal-keyed
structure tolerates missing keys. These models describe the standardized TRACE
JSON contract; the backend validates/serves it but never computes it.
"""

from __future__ import annotations

from pydantic import BaseModel


class SourceInfo(BaseModel):
    id: str
    label: str
    patient_id: str


class PatientOverview(BaseModel):
    id: str
    source: str
    time_unit: str
    available_signals: list[str]
    window: str | None = None
    data_status: str


class TimelineEvent(BaseModel):
    t: float
    label: str


class TimelineResponse(BaseModel):
    id: str
    source: str
    time_unit: str
    available_signals: list[str]
    # Each timeline point is {"t": <n>, "<signal>": <value>, ...}; signals vary
    # by source, so points are loosely typed dicts rather than a fixed model.
    timeline: list[dict]
    events: list[TimelineEvent] = []
    change_point: dict | None = None
    data_status: str


class SignalBaseline(BaseModel):
    unit: str | None = None
    mean: float | None = None


class AnalysisResponse(BaseModel):
    id: str
    source: str
    data_status: str
    baseline: dict | None = None
    temporal_trace: dict | None = None
    connections: dict | None = None
    missing_evidence: dict | None = None
    self_check: dict | None = None
    counterfactuals: dict | None = None
    trajectories: list[dict] | None = None


class CounterfactualRequest(BaseModel):
    signal: str


class CounterfactualResponse(BaseModel):
    signal: str
    actual: float | None = None
    baseline: float | None = None
    original_deviation: float | None = None
    new_deviation: float | None = None
    message: str | None = None
