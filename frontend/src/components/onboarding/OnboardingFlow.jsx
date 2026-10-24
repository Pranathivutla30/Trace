// TRACE onboarding wizard. Six steps with a progress rail, Back/Continue, and
// a single draft object so answers are preserved when moving backward. On the
// final step it calls onComplete(profile) with onboardingCompleted=true.
//
// The collected data is USER CONTEXT ONLY; it is never sent to the AI/ML model.
// Supports editing: pass an existing profile via `initial` to prefill.

import { useState } from "react";
import { emptyProfile } from "../../services/profileStorage.js";
import { Icon } from "../ui.jsx";

const STEPS = [
  "Profile",
  "About You",
  "Everyday Health",
  "Recent Changes",
  "Ready",
];

export default function OnboardingFlow({ initial, onComplete, onCancel }) {
  const [step, setStep] = useState(0);
  const [draft, setDraft] = useState(() => ({ ...emptyProfile(), ...(initial || {}) }));

  // Update one top-level section of the draft (merging nested keys).
  const setSection = (section, patch) =>
    setDraft((d) => ({ ...d, [section]: { ...d[section], ...patch } }));
  const setField = (key, value) => setDraft((d) => ({ ...d, [key]: value }));

  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1));
  const back = () => (step === 0 ? onCancel?.() : setStep((s) => s - 1));

  const finish = () => onComplete({ ...draft, onboardingCompleted: true });

  const canContinue = validateStep(step, draft);

  return (
    <div className="onb-screen">
      <div className="onb-wizard glass-plain">
        <Progress step={step} />

        <div className="onb-step" key={step}>
          {step === 0 && <ProfileSetup draft={draft} setSection={setSection} />}
          {step === 1 && <AboutYou draft={draft} setSection={setSection} />}
          {step === 2 && <Lifestyle draft={draft} setSection={setSection} />}
          {step === 3 && <RecentChanges draft={draft} setSection={setSection} setField={setField} />}
          {step === 4 && <ProfileReady draft={draft} />}
        </div>

        <div className="onb-nav">
          <button className="onb-ghost" onClick={back}>
            <Icon name="chevron" size={16} /> Back
          </button>
          {step < STEPS.length - 1 ? (
            <button className="cta onb-cta" onClick={next} disabled={!canContinue}>
              Continue
            </button>
          ) : (
            <button className="cta onb-cta" onClick={finish}>
              Continue to TRACE
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ---- Progress rail ----
function Progress({ step }) {
  return (
    <ol className="onb-progress" aria-label="Onboarding progress">
      {STEPS.map((label, i) => (
        <li key={label} className={`onb-pstep ${i === step ? "on" : ""} ${i < step ? "done" : ""}`}>
          <span className="onb-pnum">{i < step ? <Icon name="check" size={13} strokeWidth="2.6" /> : i + 1}</span>
          <span className="onb-plabel">{label}</span>
        </li>
      ))}
    </ol>
  );
}

// ---- Step validation (minimal, non-restrictive) ----
function validateStep(step, d) {
  if (step === 0) {
    const nameOk = d.account.fullName.trim().length > 0;
    const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(d.account.email.trim());
    return nameOk && emailOk;
  }
  if (step === 1) {
    const age = d.about.age;
    const ageOk = age === null || age === "" || (Number(age) > 0 && Number(age) < 130);
    return ageOk; // all About You fields are soft/optional beyond sane ranges
  }
  return true; // steps 2-4 are selection-based and optional; 5 is review
}

// ---- Reusable pill group ----
function Pills({ legend, options, value, onChange, name }) {
  return (
    <fieldset className="onb-field">
      <legend>{legend}</legend>
      <div className="onb-pills" role="radiogroup" aria-label={legend}>
        {options.map((opt) => {
          const val = typeof opt === "string" ? opt : opt.value;
          const label = typeof opt === "string" ? opt : opt.label;
          const active = value === val;
          return (
            <button
              type="button"
              key={val}
              role="radio"
              aria-checked={active}
              className={`onb-pill ${active ? "active" : ""}`}
              onClick={() => onChange(val)}
            >
              {label}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}

// ========== STEP 1: Profile ==========
function ProfileSetup({ draft, setSection }) {
  const a = draft.account;
  return (
    <>
      <h2 className="onb-title">Create your TRACE profile</h2>
      <p className="onb-sub">Tell us a little about yourself before we explore your health story.</p>

      <label className="onb-label" htmlFor="pf-name">Full Name *</label>
      <input id="pf-name" className="onb-input" type="text" autoComplete="name" required
        value={a.fullName} onChange={(e) => setSection("account", { fullName: e.target.value })} />

      <label className="onb-label" htmlFor="pf-email">Email Address *</label>
      <input id="pf-email" className="onb-input" type="email" autoComplete="email" required
        value={a.email} onChange={(e) => setSection("account", { email: e.target.value })} />

      <label className="onb-label" htmlFor="pf-phone">Phone Number <span className="onb-opt">(optional)</span></label>
      <input id="pf-phone" className="onb-input" type="tel" autoComplete="tel"
        value={a.phone} onChange={(e) => setSection("account", { phone: e.target.value })} />
    </>
  );
}

// ========== STEP 2: About You ==========
function AboutYou({ draft, setSection }) {
  const ab = draft.about;
  return (
    <>
      <h2 className="onb-title">About You</h2>
      <p className="onb-sub">Basic information helps provide context for your health story.</p>

      <label className="onb-label" htmlFor="ab-age">Age</label>
      <input id="ab-age" className="onb-input onb-narrow" type="number" min="1" max="129"
        value={ab.age ?? ""} onChange={(e) => setSection("about", { age: e.target.value === "" ? null : Number(e.target.value) })} />

      <label className="onb-label" htmlFor="ab-h">Height</label>
      <div className="onb-row">
        <input id="ab-h" className="onb-input onb-narrow" type="number" min="0"
          value={ab.height.value ?? ""}
          onChange={(e) => setSection("about", { height: { ...ab.height, value: e.target.value === "" ? null : Number(e.target.value) } })} />
        <UnitToggle units={["cm", "ft/in"]} value={ab.height.unit}
          onChange={(u) => setSection("about", { height: { ...ab.height, unit: u } })} />
      </div>

      <label className="onb-label" htmlFor="ab-w">Weight</label>
      <div className="onb-row">
        <input id="ab-w" className="onb-input onb-narrow" type="number" min="0"
          value={ab.weight.value ?? ""}
          onChange={(e) => setSection("about", { weight: { ...ab.weight, value: e.target.value === "" ? null : Number(e.target.value) } })} />
        <UnitToggle units={["kg", "lb"]} value={ab.weight.unit}
          onChange={(u) => setSection("about", { weight: { ...ab.weight, unit: u } })} />
      </div>

      <Pills legend="Sex"
        options={["Female", "Male", "Other", "Prefer not to say"]}
        value={ab.sex} onChange={(v) => setSection("about", { sex: v })} />

      <Pills legend="Do you currently use a wearable device?"
        options={["Yes", "No"]} value={ab.usesWearable}
        onChange={(v) => setSection("about", { usesWearable: v })} />

      {ab.usesWearable === "Yes" && (
        <Pills legend="Which wearable do you use?"
          options={["Apple Watch", "Fitbit", "Garmin", "Oura", "Samsung", "Other"]}
          value={ab.wearable} onChange={(v) => setSection("about", { wearable: v })} />
      )}
    </>
  );
}

function UnitToggle({ units, value, onChange }) {
  return (
    <div className="onb-units" role="group">
      {units.map((u) => (
        <button type="button" key={u} className={`onb-unit ${value === u ? "active" : ""}`}
          onClick={() => onChange(u)}>{u}</button>
      ))}
    </div>
  );
}

// ========== STEP 3: Everyday Health ==========
function Lifestyle({ draft, setSection }) {
  const l = draft.lifestyle;
  const set = (k) => (v) => setSection("lifestyle", { [k]: v });
  return (
    <>
      <h2 className="onb-title">Your Everyday Health</h2>
      <p className="onb-sub">Simple everyday context can help organize the health story.</p>

      <Pills legend="How many hours do you usually sleep each night?"
        options={["Less than 5 hours", "5–6 hours", "6–7 hours", "7–8 hours", "More than 8 hours"]}
        value={l.sleepDuration} onChange={set("sleepDuration")} />
      <Pills legend="How would you describe your daily activity level?"
        options={["Mostly inactive", "Lightly active", "Moderately active", "Very active"]}
        value={l.activityLevel} onChange={set("activityLevel")} />
      <Pills legend="How many days per week do you usually exercise?"
        options={["0 days", "1–2 days", "3–4 days", "5+ days"]}
        value={l.exerciseFrequency} onChange={set("exerciseFrequency")} />
      <Pills legend="How would you describe your usual stress level?"
        options={["Low", "Moderate", "High", "Prefer not to say"]}
        value={l.stressLevel} onChange={set("stressLevel")} />
      <Pills legend="How would you describe your energy level most days?"
        options={["Low", "Moderate", "High"]}
        value={l.energyLevel} onChange={set("energyLevel")} />
      <Pills legend="How would you describe your sleep quality?"
        options={["Poor", "Fair", "Good", "Very good"]}
        value={l.sleepQuality} onChange={set("sleepQuality")} />
      <Pills legend="Do you usually wake up feeling rested?"
        options={["Usually", "Sometimes", "Rarely"]}
        value={l.wakeRested} onChange={set("wakeRested")} />
    </>
  );
}

// ========== STEP 4: Recent Changes ==========
const CHANGE_OPTS = [
  "My sleep", "My stress", "My activity", "My energy",
  "My routine", "My general health", "Nothing noticeable", "Other",
];
const GOAL_OPTS = [
  "Changes in my wearable data", "Sleep and recovery", "Stress-related patterns",
  "Activity and recovery", "Changes in my daily routine", "General health patterns",
  "Just exploring TRACE",
];

function RecentChanges({ draft, setField }) {
  const selected = draft.recentChanges;
  const toggle = (opt) => {
    const has = selected.includes(opt);
    setField("recentChanges", has ? selected.filter((x) => x !== opt) : [...selected, opt]);
  };
  return (
    <>
      <h2 className="onb-title">Has anything changed recently?</h2>
      <p className="onb-sub">Choose anything you have personally noticed.</p>

      <div className="onb-pills" role="group" aria-label="Recent changes">
        {CHANGE_OPTS.map((opt) => (
          <button type="button" key={opt}
            className={`onb-pill ${selected.includes(opt) ? "active" : ""}`}
            aria-pressed={selected.includes(opt)} onClick={() => toggle(opt)}>
            {opt}
          </button>
        ))}
      </div>

      {selected.includes("Other") && (
        <>
          <label className="onb-label" htmlFor="rc-other">Tell us more <span className="onb-opt">(optional)</span></label>
          <input id="rc-other" className="onb-input" type="text" value={draft.recentChangesOther}
            onChange={(e) => setField("recentChangesOther", e.target.value)} />
        </>
      )}

      <Pills legend="What would you like TRACE to help you explore?"
        options={GOAL_OPTS} value={draft.explorationGoal}
        onChange={(v) => setField("explorationGoal", v)} />

      <p className="onb-note">
        TRACE keeps this context separate from physiological evidence and uses it
        to organize your investigation.
      </p>
    </>
  );
}

// ========== STEP 5: Ready ==========
function ProfileReady({ draft }) {
  const name = draft.account.fullName || "--";
  const rows = [
    ["Name", name],
    ["Age", draft.about.age ?? "—"],
    ["Wearable", draft.about.usesWearable === "Yes" ? (draft.about.wearable || "Yes") : "Not used"],
    ["Typical sleep", draft.lifestyle.sleepDuration || "—"],
    ["Activity level", draft.lifestyle.activityLevel || "—"],
    ["Exploration goal", draft.explorationGoal || "Just exploring TRACE"],
  ];
  return (
    <>
      <h2 className="onb-title">Your TRACE profile is ready</h2>
      <p className="onb-sub">Here’s a quick summary of the context you shared.</p>

      <div className="onb-summary">
        {rows.map(([k, v]) => (
          <div className="onb-sumrow" key={k}>
            <span>{k}</span>
            <b>{String(v)}</b>
          </div>
        ))}
      </div>

      <p className="onb-note">
        TRACE is an exploratory health-data tool and does not provide medical
        diagnoses or treatment recommendations.
      </p>
      <p className="onb-foot">
        For this hackathon prototype, your profile is stored locally in this
        browser so it remains available when you return on this device.
      </p>
    </>
  );
}
