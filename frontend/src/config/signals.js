// Single source of truth for every signal's label, unit and color.
// EVERY component looks signals up here so a signal keeps the same color
// in every section. Components render only signals present in the data's
// `available_signals`, so missing signals never appear as empty charts.

export const SIGNALS = {
  // Synthetic (30-day wearable) signals
  sleep_h: { label: "Sleep", unit: "h", color: "#7C83F7" }, // indigo
  hrv_ms: { label: "HRV", unit: "ms", color: "#2FB8D8" }, // cyan
  resting_hr: { label: "Resting HR", unit: "bpm", color: "#F0697A" }, // coral
  steps: { label: "Steps", unit: "count", color: "#3CC48A" }, // green
  temp_c: { label: "Temperature", unit: "°C", color: "#F2A93B" }, // amber
  fatigue: { label: "Fatigue", unit: "score", color: "#A98AF2" }, // purple
  stress: { label: "Stress", unit: "score", color: "#EE7DB8" }, // pink
  resp_rate: { label: "Respiration", unit: "brpm", color: "#2BBFAE" }, // teal
  spo2: { label: "SpO₂", unit: "%", color: "#4C8DF6" }, // blue

  // Real (wearable stress session) signals
  hr_bpm: { label: "Heart Rate", unit: "bpm", color: "#F0697A" }, // coral
  eda_us: { label: "EDA", unit: "µS", color: "#F58B4C" }, // orange
};

// Fallback for any signal not in the map, so the UI never crashes.
export function signalMeta(key) {
  return SIGNALS[key] || { label: key, unit: "", color: "#9AA8BC" };
}
