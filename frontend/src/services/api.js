// TRACE API client. Every function takes `source` ("synthetic" | "real").
// Calls go to /api and are proxied to the FastAPI backend by Vite (dev).

const BASE = "/api";

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

export function getSources() {
  return getJson("/sources");
}

export function getPatient(id, source) {
  return getJson(`/patient/${id}?source=${source}`);
}

export function getTimeline(id, source) {
  return getJson(`/patient/${id}/timeline?source=${source}`);
}

export function getAnalysis(id, source) {
  return getJson(`/patient/${id}/analysis?source=${source}`);
}

export async function runCounterfactual(id, source, signal) {
  const res = await fetch(`${BASE}/patient/${id}/counterfactual?source=${source}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ signal }),
  });
  if (!res.ok) {
    throw new Error(`TRACE API error: ${res.status}`);
  }
  return res.json();
}
