// API client for the TRACE backend.
// One function per capability; all return standardized TRACE JSON.

import { API_BASE } from "../config/index.js";

async function getJson(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`TRACE API ${res.status}: ${path}`);
  }
  return res.json();
}

export const traceApi = {
  health: () => getJson("/health"),
  listPatients: () => getJson("/api/v1/patients"),
  baseline: (id) => getJson(`/api/v1/patients/${id}/baseline`),
  temporalTrace: (id) => getJson(`/api/v1/patients/${id}/temporal-trace`),
  connections: (id) => getJson(`/api/v1/patients/${id}/connections`),
  missingEvidence: (id) => getJson(`/api/v1/patients/${id}/missing-evidence`),
  selfCheck: (id) => getJson(`/api/v1/patients/${id}/self-check`),
  counterfactual: (id) => getJson(`/api/v1/patients/${id}/counterfactual`),
  trajectory: (id) => getJson(`/api/v1/patients/${id}/trajectory`),
};
