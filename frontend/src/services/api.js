// TRACE API client.
//
// Two modes, automatic:
//  1. Live backend (local dev): calls /api/... which Vite proxies to FastAPI.
//  2. Static fallback (e.g. GitHub Pages, no backend): if the live call fails,
//     it loads the bundled analysis JSON from <base>/data/{source}_{id}.json
//     and reconstructs each endpoint's response client-side.
//
// The static files are the exact adapter output (frontend/public/data/*.json),
// so the dashboard shows identical analysis with or without a backend.

const BASE = "/api";
// Vite injects the deploy base (e.g. "/Trace/" on GitHub Pages, "/" in dev).
const DATA_BASE = `${import.meta.env.BASE_URL || "/"}data`;

// Map a source id to its static patient id (matches the backend SOURCES).
const STATIC_ID = { synthetic: "001", real: "f16" };

async function getJson(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    let detail = `${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(`TRACE API error: ${detail}`);
  }
  return res.json();
}

// Load and cache a source's full static analysis document.
const _staticCache = {};
async function loadStatic(source) {
  if (_staticCache[source]) return _staticCache[source];
  const id = STATIC_ID[source] || source;
  const res = await fetch(`${DATA_BASE}/${source}_${id}.json`);
  if (!res.ok) throw new Error(`TRACE static data missing for ${source}`);
  const doc = await res.json();
  doc.data_status = "live"; // the static JSON IS the real analysis
  _staticCache[source] = doc;
  return doc;
}

// Try the live backend first; on any failure fall back to static JSON,
// shaping the static doc to match what each endpoint returns.
async function liveOrStatic(path, source, shape) {
  try {
    return await getJson(path);
  } catch {
    const doc = await loadStatic(source);
    return shape(doc);
  }
}

export async function getSources() {
  try {
    return await getJson("/sources");
  } catch {
    return [
      { id: "synthetic", label: "Synthetic Demo", patient_id: "001" },
      { id: "real", label: "Real Wearable Data (de-identified)", patient_id: "f16" },
    ];
  }
}

export function getPatient(id, source) {
  return liveOrStatic(`/patient/${id}?source=${source}`, source, (d) => ({
    id: d.id,
    source: d.source,
    time_unit: d.time_unit,
    available_signals: d.available_signals,
    window: d.window,
    data_status: d.data_status,
  }));
}

export function getTimeline(id, source) {
  return liveOrStatic(`/patient/${id}/timeline?source=${source}`, source, (d) => ({
    id: d.id,
    source: d.source,
    time_unit: d.time_unit,
    available_signals: d.available_signals,
    timeline: d.timeline || [],
    events: d.events || [],
    change_point: d.change_point ?? null,
    data_status: d.data_status,
  }));
}

export function getAnalysis(id, source) {
  return liveOrStatic(`/patient/${id}/analysis?source=${source}`, source, (d) => ({
    id: d.id,
    source: d.source,
    data_status: d.data_status,
    baseline: d.baseline ?? null,
    temporal_trace: d.temporal_trace ?? null,
    connections: d.connections ?? null,
    missing_evidence: d.missing_evidence ?? null,
    self_check: d.self_check ?? null,
    counterfactuals: d.counterfactuals ?? null,
    trajectories: d.trajectories ?? null,
    ml_transition_model: d.ml_transition_model ?? null,
  }));
}

export async function runCounterfactual(id, source, signal) {
  try {
    const res = await fetch(`${BASE}/patient/${id}/counterfactual?source=${source}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ signal }),
    });
    if (!res.ok) throw new Error(`TRACE API error: ${res.status}`);
    return res.json();
  } catch {
    // Static fallback: reconstruct the counterfactual from the bundled JSON.
    const doc = await loadStatic(source);
    const cf = doc.counterfactuals || {};
    const signals = cf.signals || {};
    const current = cf.current_deviation;
    const entry = signals[signal];
    if (!entry) {
      const available = Object.keys(signals).join(", ") || "none";
      return {
        signal,
        message: `No precomputed counterfactual for '${signal}'. Available signals: ${available}.`,
      };
    }
    const sigBaseline = (doc.baseline || {})[signal] || {};
    return {
      signal,
      actual: sigBaseline.mean ?? null,
      baseline: sigBaseline.mean ?? null,
      original_deviation: current ?? null,
      new_deviation: entry.new_deviation ?? null,
      message: entry.note ?? null,
    };
  }
}
