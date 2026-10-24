"""The ONLY place that changes at ML integration time.

load_analysis(source, patient_id) looks for the live ML output first
(ai_ml/output/{source}_{patient_id}.json). If that file is missing or broken,
it falls back to the bundled mock (backend/mock/{source}_{patient_id}.json).

The returned dict always carries a "data_status" field:
    "live" -> served from ai_ml/output/
    "mock" -> served from backend/mock/

The backend only reads standardized TRACE JSON here. It never opens a raw
dataset and never computes anything an ML model should.
"""

from __future__ import annotations

import json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent

LIVE_DIR = PROJECT_ROOT / "ai_ml" / "output"
MOCK_DIR = BACKEND_DIR / "mock"


def _try_read(path: Path):
    """Return parsed JSON, or None if the file is missing or unparseable."""
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def load_analysis(source: str, patient_id: str) -> dict | None:
    """Load one patient's standardized TRACE JSON for the given source.

    Returns the analysis dict with "data_status" set to "live" or "mock",
    or None if neither the live file nor the mock exists/parses.
    """
    filename = f"{source}_{patient_id}.json"

    live = _try_read(LIVE_DIR / filename)
    if live is not None:
        live["data_status"] = "live"
        return live

    mock = _try_read(MOCK_DIR / filename)
    if mock is not None:
        mock["data_status"] = "mock"
        return mock

    return None
