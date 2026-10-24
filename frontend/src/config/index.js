// Frontend configuration.
//
// The backend decides which data source ("synthetic" | "real") is active via
// its own TRACE_DATA_SOURCE env var; the frontend just talks to the API.
// Override the API base at build/runtime with VITE_API_BASE.

export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

// Logical data-source labels shared with the backend, for display only.
export const DATA_SOURCES = ["synthetic", "real"];
