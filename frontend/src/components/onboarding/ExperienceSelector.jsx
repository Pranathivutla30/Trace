// Choose-experience screen shown after onboarding / returning welcome.
// Both cards connect to the EXISTING source-selection: Synthetic -> 001,
// Real -> f16. It does not duplicate the dashboard; it just picks the source
// the existing Investigation page will load.

import { Icon } from "../ui.jsx";

export default function ExperienceSelector({ onPick, name }) {
  return (
    <div className="onb-screen">
      <div className="onb-choose">
        <div className="onb-choose-head">
          <h1 className="onb-title">How would you like to explore TRACE?</h1>
          {name && <p className="onb-sub">Welcome, {name}. Pick a starting point — you can switch inside the dashboard.</p>}
        </div>

        <div className="onb-cards">
          <div className="onb-xcard glass-plain">
            <span className="onb-badge">FULL TRACE EXPERIENCE</span>
            <h2>Synthetic Demo</h2>
            <p className="onb-xlede">Explore TRACE’s complete 30-day investigation workflow.</p>
            <p className="onb-xdesc">
              Demonstrates all seven TRACE reasoning capabilities using a
              controlled synthetic longitudinal patient story.
            </p>
            <button className="cta onb-cta" onClick={() => onPick("synthetic")}>
              <Icon name="arrow" size={16} /> Explore Synthetic Demo
            </button>
          </div>

          <div className="onb-xcard glass-plain">
            <span className="onb-badge real">REAL DATA · PhysioNet</span>
            <h2>Real Wearable Data</h2>
            <p className="onb-xlede">Explore TRACE on de-identified real wearable research data.</p>
            <p className="onb-xdesc">
              See temporal change detection and a trained physiological anomaly
              model evaluated on held-out real wearable data.
            </p>
            <button className="cta onb-cta" onClick={() => onPick("real")}>
              <Icon name="arrow" size={16} /> Explore Real Data
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
