// TRACE Welcome / landing screen. First visit shows "Get Started"; a returning
// visitor with a saved profile sees "Welcome back, <name>" and can continue,
// edit, or (with confirmation) use a different profile. Clinical Glass styling.

import { useState } from "react";
import { Icon } from "../ui.jsx";

export default function Welcome({
  profile,
  onStart,
  onContinue,
  onEdit,
  onUseDifferent,
}) {
  const [confirming, setConfirming] = useState(false);
  const name = profile?.account?.fullName?.trim()?.split(/\s+/)[0] || "";
  const returning = !!(profile && profile.onboardingCompleted && name);

  return (
    <div className="onb-screen">
      <div className="onb-card glass-plain" role="main">
        <div className="onb-brand">
          <span className="logo-mark">
            <Icon name="pulse" size={20} strokeWidth="2.4" />
          </span>
          <span className="onb-brand-text">TRACE</span>
        </div>

        <h1 className="onb-hero">Temporal Reasoning &amp; Analysis for Clinical Exploration</h1>
        <p className="onb-tagline">“Find where the story changed.”</p>

        {!returning ? (
          <div className="onb-actions">
            <button className="cta onb-cta" onClick={onStart}>
              <Icon name="arrow" size={16} />
              Get Started
            </button>
          </div>
        ) : (
          <>
            <div className="onb-welcomeback">
              <span className="avatar">{initials(name)}</span>
              <div>
                <b>Welcome back, {name}</b>
                <span>Ready to continue exploring your health story?</span>
              </div>
            </div>
            <div className="onb-actions">
              <button className="cta onb-cta" onClick={onContinue}>
                Continue to TRACE
              </button>
              <button className="onb-ghost" onClick={onEdit}>
                Edit Profile
              </button>
            </div>
            {!confirming ? (
              <button className="onb-link" onClick={() => setConfirming(true)}>
                Use a different profile
              </button>
            ) : (
              <div className="onb-confirm" role="alertdialog" aria-label="Confirm">
                <p>This will remove the TRACE profile stored in this browser. Continue?</p>
                <div className="onb-confirm-actions">
                  <button className="onb-ghost" onClick={() => setConfirming(false)}>
                    Cancel
                  </button>
                  <button className="onb-danger" onClick={onUseDifferent}>
                    Remove profile
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        <p className="onb-foot">
          TRACE is an exploratory health-data tool and does not provide medical
          diagnoses or treatment recommendations.
        </p>
      </div>
    </div>
  );
}

function initials(name) {
  return name ? name.slice(0, 2).toUpperCase() : "--";
}
