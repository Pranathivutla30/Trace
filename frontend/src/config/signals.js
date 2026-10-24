// Single source of truth for every signal's label, unit and color.
// EVERY component looks signals up here so a signal keeps the same color
// in every section. Components render only signals present in the data's
// `available_signals`, so missing signals never appear as empty charts.

// `full` is a plain-English expansion shown in small text under the label so
// people unfamiliar with the abbreviations still understand each signal.
export const SIGNALS = {
  // Synthetic (30-day wearable) signals
  sleep_h: { label: "Sleep", full: "hours of sleep", unit: "h", color: "#7C83F7" }, // indigo
  hrv_ms: { label: "HRV", full: "heart rate variability", unit: "ms", color: "#2FB8D8" }, // cyan
  resting_hr: { label: "Resting HR", full: "resting heart rate", unit: "bpm", color: "#F0697A" }, // coral
  steps: { label: "Steps", full: "daily step count", unit: "count", color: "#3CC48A" }, // green
  temp_c: { label: "Temperature", full: "body temperature", unit: "°C", color: "#F2A93B" }, // amber
  fatigue: { label: "Fatigue", full: "how tired you feel", unit: "score", color: "#A98AF2" }, // purple
  stress: { label: "Stress", full: "stress level", unit: "score", color: "#EE7DB8" }, // pink
  resp_rate: { label: "Respiration", full: "breaths per minute", unit: "brpm", color: "#2BBFAE" }, // teal
  eda: { label: "EDA", full: "electrical skin activity", unit: "µS", color: "#F58B4C" }, // orange (synthetic EDA key)
  spo2: { label: "SpO₂", full: "blood oxygen", unit: "%", color: "#4C8DF6" }, // blue

  // Real (wearable stress session) signals
  hr_bpm: { label: "Heart Rate", full: "heart rate", unit: "bpm", color: "#F0697A" }, // coral
  eda_us: { label: "EDA", full: "electrical skin activity", unit: "µS", color: "#F58B4C" }, // orange
  // Accelerometer magnitude (sqrt(x^2+y^2+z^2)); NOT steps/calories/minutes.
  activity: { label: "Activity", full: "overall body movement", unit: "accel mag", color: "#3CC48A" }, // green
};

// Fallback for any signal not in the map, so the UI never crashes.
export function signalMeta(key) {
  return SIGNALS[key] || { label: key, full: "", unit: "", color: "#9AA8BC" };
}
