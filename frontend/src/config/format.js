// Small display helpers shared across sections (no data logic).

// Time label for a timeline index, driven by the patient's time_unit.
export function fmtT(t, unit) {
  if (typeof t !== "number") return "--";
  if (unit === "minute") return `min ${t}`;
  if (t === 0) return "Today";
  return `Day ${t}`;
}

export function windowLabel(patient) {
  if (!patient) return "";
  if (patient.time_unit === "minute") return "40-Minute Session";
  if (patient.time_unit === "day") return "30-Day Investigation";
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
