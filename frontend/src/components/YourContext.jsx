// "Your Context" — shows the user's self-reported onboarding profile ALONGSIDE
// the current investigation, as a transparent, qualitative comparison.
//
// CRITICAL: this is frontend-only and context-only. It reads the saved profile
// (localStorage via profileStorage) and the already-fetched dashboard analysis.
// It NEVER sends profile data to the backend and NEVER changes any AI/ML result
// (baseline, change point, anomaly, confidence, counterfactuals, trajectories).
// Wording stays safe: reported / observed / context / pattern — never
// unhealthy / abnormal / disease / risk / diagnosis / caused by.

import { Card, CardHead, Icon } from "./ui.jsx";
import { fmtT } from "../config/format.js";
import { loadTraceProfile, firstName } from "../services/profileStorage.js";

// Rough midpoint (hours) for each sleep bucket — used ONLY to pick a
// lower/higher/similar direction word, never shown as a precise value.
const SLEEP_MIDPOINT = {
  "Less than 5 hours": 4.5,
  "5–6 hours": 5.5,
  "6–7 hours": 6.5,
  "7–8 hours": 7.5,
  "More than 8 hours": 8.5,
};

function direction(userHours, baselineHours) {
  if (userHours == null || baselineHours == null) return null;
  const diff = userHours - baselineHours;
  if (Math.abs(diff) < 0.6) return "about the same as";
  return diff < 0 ? "lower than" : "higher than";
}

// Signals in the demo that are "stress-related" / "activity-related" for the
// descriptive overlap wording.
const STRESS_SIGNALS = ["stress", "fatigue", "eda"];
const ACTIVITY_SIGNALS = ["steps"];
const SLEEP_SIGNALS = ["sleep_h"];

// Map the user's free "recent changes" selections to dashboard signal groups
// so we can describe overlap descriptively (not causally).
const CHANGE_TO_SIGNALS = {
  "My sleep": SLEEP_SIGNALS,
  "My stress": STRESS_SIGNALS,
  "My activity": ACTIVITY_SIGNALS,
  "My energy": ["fatigue"],
};

export default function YourContext({ source, analysis, timeUnit, changePoint }) {
  const profile = loadTraceProfile();
  if (!profile || !profile.onboardingCompleted) return null; // hide gracefully

  const name = firstName(profile);
  const goal = profile.explorationGoal;

  // ---------- REAL f16: no sleep/stress signals -> honest, simple card ----------
  if (source === "real") {
    return (
      <Card id="context" className="span-12" delay={0.04}>
        <CardHead
          title="Your Context"
          eyebrow="Self-reported context alongside physiological evidence"
        />
        <p className="help-line">
          {name ? `${name}, your` : "Your"} profile is saved, but this research
          recording contains only heart rate, HRV (heart rate variability), EDA
          (electrical skin activity), temperature, and activity — so there’s no
          sleep or stress signal to compare against here.
        </p>
        {goal && (
          <div className="yc-goal">
            <Icon name="sliders" size={16} />
            You're exploring TRACE for: <b>{goal}</b>
          </div>
        )}
        <p className="yc-future">
          Connect your own longitudinal wearable data in a future TRACE version
          to run a truly personalized investigation.
        </p>
        <p className="caption">
          Context only — this does not change TRACE’s physiological analysis and
          is not a health assessment.
        </p>
      </Card>
    );
  }

  // ---------- SYNTHETIC: build the meaningful comparisons ----------
  const baseline = analysis?.baseline || {};
  const order = analysis?.temporal_trace?.order || [];
  const detectedT = changePoint?.detected_t ?? changePoint?.t;

  const firstChangeOf = (sig) => {
    const hit = order.find((o) => o.signal === sig);
    return hit ? hit.first_change_t : null;
  };

  const rows = [];

  // 1) SLEEP
  const userSleepBucket = profile.lifestyle?.sleepDuration;
  const baseSleep = baseline.sleep_h?.mean;
  if (userSleepBucket && typeof baseSleep === "number") {
    const dir = direction(SLEEP_MIDPOINT[userSleepBucket], baseSleep);
    rows.push({
      key: "sleep",
      youLabel: "Sleep",
      youValue: userSleepBucket,
      traceLabel: "Demo baseline",
      traceValue: `~${baseSleep.toFixed(1)} h`,
      note: dir
        ? `Your reported sleep duration is ${dir} this demonstration patient's baseline.`
        : null,
    });
  }

  // 2) STRESS (categorical vs. signal behavior — no numeric conversion)
  const userStress = profile.lifestyle?.stressLevel;
  const stressChangeT = firstChangeOf("stress");
  if (userStress && userStress !== "Prefer not to say") {
    rows.push({
      key: "stress",
      youLabel: "Stress",
      youValue: `${userStress} usual stress`,
      traceLabel: "TRACE observed",
      traceValue:
        stressChangeT != null
          ? `Stress-related values increased after ${fmtT(stressChangeT, timeUnit)}`
          : "Stress-related values shifted in this investigation",
      note: "Contextual comparison — different measurement types.",
    });
  }

  // 3) ACTIVITY (categorical vs. signal behavior — no numeric conversion)
  const userActivity = profile.lifestyle?.activityLevel;
  const stepsChangeT = firstChangeOf("steps");
  if (userActivity) {
    rows.push({
      key: "activity",
      youLabel: "Activity",
      youValue: userActivity,
      traceLabel: "TRACE observed",
      traceValue:
        stepsChangeT != null
          ? `Activity declined after ${fmtT(stepsChangeT, timeUnit)}`
          : "Activity declined later in the investigation",
      note: "Contextual comparison — different measurement types.",
    });
  }

  // 4) RECENT CHANGES overlap (descriptive only)
  const userChanges = (profile.recentChanges || []).filter(
    (c) => c !== "Nothing noticeable" && c !== "Other"
  );
  const changedSignals = new Set(order.map((o) => o.signal));
  const overlap = userChanges.filter((c) =>
    (CHANGE_TO_SIGNALS[c] || []).some((sig) => changedSignals.has(sig))
  );

  // Nothing meaningful to show? Hide gracefully.
  if (!rows.length && !userChanges.length && !goal) return null;

  return (
    <Card id="context" className="span-12" delay={0.04}>
      <CardHead
        title="Your Context"
        eyebrow="Self-reported context alongside physiological evidence"
      />
      <p className="help-line">
        {name ? `${name}, here's` : "Here's"} how the context you shared lines up
        with this demonstration investigation. It sits beside the analysis — it
        doesn't change it.
      </p>

      <div className="yc-grid">
        {rows.map((r) => (
          <div className="yc-row" key={r.key}>
            <div className="yc-col">
              <span className="yc-tag">You reported</span>
              <b>{r.youLabel}: {r.youValue}</b>
            </div>
            <span className="yc-arrow"><Icon name="arrow" size={16} /></span>
            <div className="yc-col">
              <span className="yc-tag">{r.traceLabel}</span>
              <b>{r.traceValue}</b>
            </div>
            {r.note && <div className="yc-note">{r.note}</div>}
          </div>
        ))}
      </div>

      {(userChanges.length > 0 || goal) && (
        <div className="yc-foot-rows">
          {userChanges.length > 0 && (
            <div className="yc-chips-row">
              <span className="yc-tag">You noticed</span>
              <span className="yc-chips">
                {userChanges.map((c) => (
                  <span className="chip" key={c}>{c.replace(/^My /, "")}</span>
                ))}
              </span>
            </div>
          )}
          {overlap.length > 0 && (
            <div className="yc-chips-row">
              <span className="yc-tag">Overlap with TRACE</span>
              <span className="yc-chips">
                {overlap.map((c) => (
                  <span className="chip hot" key={c}>{c.replace(/^My /, "")}</span>
                ))}
              </span>
            </div>
          )}
          {overlap.length > 0 && (
            <p className="yc-overlap-note">
              Both your selected context and this demonstration investigation
              include changes related to {overlap.map((c) => c.replace(/^My /, "").toLowerCase()).join(" and ")}.
              This is an overlap, not proof that one caused the other.
            </p>
          )}
          {goal && (
            <div className="yc-goal">
              <Icon name="sliders" size={16} />
              You're exploring TRACE for: <b>{goal}</b>
            </div>
          )}
        </div>
      )}

      <p className="caption">
        Context only — these comparisons do not change TRACE’s physiological
        analysis and are not a health assessment.
      </p>
    </Card>
  );
}
