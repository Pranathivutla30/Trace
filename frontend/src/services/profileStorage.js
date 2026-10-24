// TRACE user-profile persistence (hackathon prototype).
//
// This is the ONLY place that touches browser storage for the user profile.
// It is intentionally the single swap point: to move to real backend auth +
// a database later, replace the four functions below with API calls and keep
// the same shapes. The profile is USER CONTEXT ONLY and is never fed into the
// AI/ML analysis.
//
// NOTE: localStorage is not secure storage. This is a prototype convenience so
// a returning user is recognized on the same browser/device. It is NOT real
// authentication, NOT a medical database, and NOT HIPAA-compliant.

export const PROFILE_KEY = "trace_user_profile_v1";
export const PROFILE_VERSION = 1;

// A fresh, empty profile matching the documented shape.
export function emptyProfile() {
  return {
    profileVersion: PROFILE_VERSION,
    createdAt: null,
    updatedAt: null,
    account: { fullName: "", email: "", phone: "" },
    about: {
      age: null,
      height: { value: null, unit: "cm" },
      weight: { value: null, unit: "kg" },
      sex: "",
      usesWearable: null,
      wearable: "",
    },
    lifestyle: {
      sleepDuration: "",
      activityLevel: "",
      exerciseFrequency: "",
      stressLevel: "",
      energyLevel: "",
      sleepQuality: "",
      wakeRested: "",
    },
    recentChanges: [],
    recentChangesOther: "",
    explorationGoal: "",
    optionalHealthContext: { conditions: "", medications: "" },
    onboardingCompleted: false,
  };
}

function safeParse(raw) {
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

// Load the saved profile, or null if none/invalid. Tolerates older/partial
// shapes by merging onto a fresh profile so the UI never crashes on a field.
export function loadTraceProfile() {
  if (typeof localStorage === "undefined") return null;
  const raw = localStorage.getItem(PROFILE_KEY);
  if (!raw) return null;
  const parsed = safeParse(raw);
  if (!parsed || typeof parsed !== "object") return null;
  return mergeProfile(emptyProfile(), parsed);
}

// True only when a completed onboarding profile exists.
export function hasCompletedProfile() {
  const p = loadTraceProfile();
  return !!(p && p.onboardingCompleted && p.account && p.account.fullName);
}

// Persist a full profile object, stamping timestamps.
export function saveTraceProfile(profile) {
  if (typeof localStorage === "undefined") return profile;
  const now = new Date().toISOString();
  const next = {
    ...profile,
    profileVersion: PROFILE_VERSION,
    createdAt: profile.createdAt || now,
    updatedAt: now,
  };
  localStorage.setItem(PROFILE_KEY, JSON.stringify(next));
  return next;
}

// Shallow-ish merge update: pass a partial profile; nested objects are merged
// one level deep so callers can update a single section at a time.
export function updateTraceProfile(partial) {
  const current = loadTraceProfile() || emptyProfile();
  const merged = mergeProfile(current, partial);
  return saveTraceProfile(merged);
}

// Remove the stored profile entirely (used only after explicit confirmation).
export function clearTraceProfile() {
  if (typeof localStorage === "undefined") return;
  localStorage.removeItem(PROFILE_KEY);
}

// Convenience: the user's first name for greetings.
export function firstName(profile) {
  const full = profile?.account?.fullName?.trim();
  if (!full) return "";
  return full.split(/\s+/)[0];
}

// One-level-deep merge used by load/update so nested sections combine cleanly.
function mergeProfile(base, incoming) {
  const out = { ...base, ...incoming };
  for (const key of [
    "account",
    "about",
    "lifestyle",
    "optionalHealthContext",
  ]) {
    out[key] = { ...(base[key] || {}), ...(incoming[key] || {}) };
  }
  // Nested unit objects under about.
  if (incoming.about) {
    out.about.height = {
      ...(base.about?.height || {}),
      ...(incoming.about.height || {}),
    };
    out.about.weight = {
      ...(base.about?.weight || {}),
      ...(incoming.about.weight || {}),
    };
  }
  return out;
}
