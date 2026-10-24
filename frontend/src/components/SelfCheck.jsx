// 05 Can TRACE Trust This? (Self-Check): a segmented ring gauge for the
// interpretation confidence, plus its supporting components as fact tiles.
// An internal reasoning check, not a second chatbot.

import { useRef } from "react";
import { useInView } from "framer-motion";
import { Card, CardHead, CountUp } from "./ui.jsx";

const N = 40;

export default function SelfCheck({ selfCheck }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, amount: 0.4 });
  if (!selfCheck) return null;

  const conf = selfCheck.interpretation_confidence;
  const lit = typeof conf === "number" ? Math.round((Math.max(0, Math.min(100, conf)) / 100) * N) : 0;

  return (
    <Card id="selfcheck" className="span-4 stretch" delay={0.15}>
      <CardHead title="AI Self-Check — Can We Trust This?" eyebrow="How strong and consistent the evidence is" />
      <p className="help-line">This is how sure TRACE is about its own reading of the data — <b>not</b> a chance that something is wrong with your health.</p>

      <div className="legend-dots">
        <span className="k"><span className="d" style={{ background: "var(--accent)" }} /> Confidence</span>
        <span className="k"><span className="d" style={{ background: "var(--solid)" }} /> Remaining</span>
      </div>

      <div className="gauge" ref={ref}>
        <svg viewBox="0 0 220 220" role="img" aria-label={`Interpretation confidence ${conf ?? "unknown"} percent`}>
          {Array.from({ length: N }, (_, i) => {
            const angle = (i / N) * 360;
            const on = inView && i < lit;
            return (
              <g key={i} transform={`rotate(${angle} 110 110)`}>
                <rect
                  className={`seg ${on ? "on" : ""}`}
                  x="105"
                  y="6"
                  width="10"
                  height="22"
                  rx="5"
                  style={{ transitionDelay: `${i * 22}ms` }}
                />
                <rect
                  className={`seg-in ${inView && i >= lit ? "on" : ""}`}
                  x="106.5"
                  y="34"
                  width="7"
                  height="14"
                  rx="3.5"
                  style={{ transitionDelay: `${(N - i) * 18 + 300}ms` }}
                />
              </g>
            );
          })}
        </svg>
        <div className="gauge-center">
          <b>
            <CountUp value={conf} />
            <small style={{ fontSize: 18, color: "var(--muted)" }}>%</small>
          </b>
          <span className="gauge-label">how sure TRACE is</span>
        </div>
      </div>

      <ul className="sc-checks" aria-label="Reasoning checks">
        {buildChecks(selfCheck).map((c) => (
          <li className={`sc-check ${c.level}`} key={c.label}>
            <span className="sc-dot" />
            <span className="sc-check-label">{c.label}</span>
            <b className="sc-check-val">{c.value}</b>
          </li>
        ))}
      </ul>

      <div className="facts">
        <div className="fact wide">
          <span>Based on</span>
          <b>How much things differ from this person's normal</b>
        </div>
      </div>
    </Card>
  );
}

// Build the reasoning checklist from the (real) available self-check fields.
// Each check gets a level (ok / warn / low) that drives the dot color via CSS.
// No invented numeric sub-scores — only what the backend actually provides.
function buildChecks(sc) {
  const conf = sc.interpretation_confidence;
  const wordLevel = (w) => {
    const s = String(w || "").toLowerCase();
    if (["strong", "high", "very good", "good"].some((k) => s.includes(k))) return "ok";
    if (["moderate", "fair"].some((k) => s.includes(k))) return "warn";
    return "low";
  };
  const confLevel =
    typeof conf !== "number" ? "low" : conf >= 70 ? "ok" : conf >= 40 ? "warn" : "low";

  return [
    { label: "How clear the pattern is", value: sc.pattern_evidence ?? "--", level: wordLevel(sc.pattern_evidence) },
    { label: "How complete the data is", value: sc.data_completeness ?? "--", level: wordLevel(sc.data_completeness) },
    { label: "Overall confidence", value: typeof conf === "number" ? `${Math.round(conf)}%` : "--", level: confLevel },
  ];
}
