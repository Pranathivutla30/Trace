"""TRACE API endpoints.

source must be "synthetic" or "real"; anything else is a clear 400.
All data comes through services.data_service.load_analysis (live-then-mock).
"""

from fastapi import APIRouter, HTTPException, Query

from schemas.trace import (
    AnalysisResponse,
    CounterfactualRequest,
    CounterfactualResponse,
    PatientOverview,
    SourceInfo,
    TimelineResponse,
)
from services.data_service import load_analysis

router = APIRouter(prefix="/api", tags=["trace"])

VALID_SOURCES = {"synthetic", "real"}

SOURCES = [
    {"id": "synthetic", "label": "Synthetic Demo", "patient_id": "001"},
    {"id": "real", "label": "Real Wearable Data (de-identified)", "patient_id": "f16"},
]


def _validate_source(source: str) -> None:
    if source not in VALID_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source '{source}'. Use 'synthetic' or 'real'.",
        )


def _load_or_404(source: str, patient_id: str) -> dict:
    _validate_source(source)
    doc = load_analysis(source, patient_id)
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"No analysis found for source='{source}', patient='{patient_id}'.",
        )
    return doc


@router.get("/sources", response_model=list[SourceInfo])
def list_sources():
    return SOURCES


@router.get("/patient/{patient_id}", response_model=PatientOverview)
def patient_overview(patient_id: str, source: str = Query(...)):
    doc = _load_or_404(source, patient_id)
    return {
        "id": doc.get("id", patient_id),
        "source": source,
        "time_unit": doc.get("time_unit", ""),
        "available_signals": doc.get("available_signals", []),
        "window": doc.get("window"),
        "data_status": doc.get("data_status", "mock"),
    }


@router.get("/patient/{patient_id}/timeline", response_model=TimelineResponse)
def patient_timeline(patient_id: str, source: str = Query(...)):
    doc = _load_or_404(source, patient_id)
    return {
        "id": doc.get("id", patient_id),
        "source": source,
        "time_unit": doc.get("time_unit", ""),
        "available_signals": doc.get("available_signals", []),
        "timeline": doc.get("timeline", []),
        "events": doc.get("events", []),
        "change_point": doc.get("change_point"),
        "data_status": doc.get("data_status", "mock"),
    }


@router.get("/patient/{patient_id}/analysis", response_model=AnalysisResponse)
def patient_analysis(patient_id: str, source: str = Query(...)):
    doc = _load_or_404(source, patient_id)
    return {
        "id": doc.get("id", patient_id),
        "source": source,
        "data_status": doc.get("data_status", "mock"),
        "baseline": doc.get("baseline"),
        "temporal_trace": doc.get("temporal_trace"),
        "connections": doc.get("connections"),
        "missing_evidence": doc.get("missing_evidence"),
        "self_check": doc.get("self_check"),
        "counterfactuals": doc.get("counterfactuals"),
        "trajectories": doc.get("trajectories"),
        "ml_transition_model": doc.get("ml_transition_model"),
    }


@router.post("/patient/{patient_id}/counterfactual", response_model=CounterfactualResponse)
def patient_counterfactual(
    patient_id: str,
    body: CounterfactualRequest,
    source: str = Query(...),
):
    doc = _load_or_404(source, patient_id)
    cf = doc.get("counterfactuals") or {}
    signals = cf.get("signals") or {}
    current = cf.get("current_deviation")

    entry = signals.get(body.signal)
    if entry is None:
        available = ", ".join(signals.keys()) or "none"
        return {
            "signal": body.signal,
            "message": (
                f"No precomputed counterfactual for '{body.signal}'. "
                f"Available signals: {available}."
            ),
        }

    # Pull the actual + baseline values from the analysis if present.
    baseline_block = doc.get("baseline") or {}
    sig_baseline = baseline_block.get(body.signal) or {}

    return {
        "signal": body.signal,
        "actual": sig_baseline.get("mean"),
        "baseline": sig_baseline.get("mean"),
        "original_deviation": current,
        "new_deviation": entry.get("new_deviation"),
        "message": entry.get("note"),
    }
