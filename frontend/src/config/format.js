// Small display helpers shared across sections (no data logic).

// Compact time label for chips/axes. Reads plainly for a non-expert:
//   minute data -> "min 13"
//   day data    -> "today", "10 days ago" (negatives), "in 3 days" (positive)
export function fmtT(t, unit) {
  if (typeof t !== "number") return "--";
  if (unit === "minute") return `min ${t}`;
  if (t === 0) return "today";
  if (t < 0) return `${Math.abs(t)} ${Math.abs(t) === 1 ? "day" : "days"} ago`;
  return `in ${t} ${t === 1 ? "day" : "days"}`;
}

// Human session-length label. For minute/day data the length is derived from
// the actual timeline (pointCount) rather than a hardcoded value; falls back
// to the patient's own window string when no timeline is available.
export function windowLabel(patient, timeline) {
  if (!patient) return "";
  const n = Array.isArray(timeline) ? timeline.length : null;
  if (patient.time_unit === "minute") {
    return n ? `${n}-Minute Session` : patient.window || "Session";
  }
  if (patient.time_unit === "day") {
    return n ? `${n}-Day Investigation` : "30-Day Investigation";
  }
  return patient.window || "";
}

// Fallback std when the baseline has none: spread of the timeline itself.
export function estimateStd(timeline, key, mean) {
  if (!timeline?.length) return 0;
  const vals = timeline.map((p) => p[key]).filter((v) => typeof v === "number");
  if (!vals.length) return 0;
  const variance = vals.reduce((s, v) => s + (v - mean) ** 2, 0) / vals.length;
  return Math.sqrt(variance) || 1;
}

// z-score of the latest timeline value against the personal baseline.
export function zScore(baseline, timeline, key) {
  const b = baseline?.[key];
  if (!b) return null;
  const last = timeline?.[timeline.length - 1] || {};
  const current = last[key];
  if (typeof current !== "number") return null;
  const std = b.std ?? estimateStd(timeline, key, b.mean);
  return std ? (current - b.mean) / std : 0;
}

export function zLevel(z) {
  const a = Math.abs(z);
  if (a >= 2) return "danger";
  if (a >= 1) return "warn";
  return "ok";
}

export function decimalsFor(v) {
  if (typeof v !== "number" || Math.abs(v) >= 100 || Number.isInteger(v)) return 0;
  const s = String(v).split(".")[1] || "";
  return Math.min(2, s.length);
}

// Display-only: turn a raw variable/label string into human-readable text.
// Known signal keys are left to signalMeta elsewhere; this handles the
// contextual variable names used by BioMissing (e.g. "subjective_stress_level"
// -> "Subjective stress level"). Strings that already contain spaces (already
// human-readable, e.g. "Subjective context label") are returned unchanged.
export function humanizeLabel(name) {
  if (typeof name !== "string" || !name) return name;
  if (name.includes(" ")) return name; // already human-readable
  const words = name.split("_").filter(Boolean);
  if (!words.length) return name;
  return words
    .map((w, i) =>
      i === 0 ? w.charAt(0).toUpperCase() + w.slice(1) : w.toLowerCase()
    )
    .join(" ");
}
