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
      <CardHead title="Can TRACE Trust This?" eyebrow="Self-Check · internal reasoning check" />

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
          <span className="gauge-label">confidence</span>
        </div>
      </div>

      <div className="facts">
        <div className="fact">
          <span>Pattern evidence</span>
          <b>{selfCheck.pattern_evidence ?? "--"}</b>
        </div>
        <div className="fact">
          <span>Data completeness</span>
          <b>{selfCheck.data_completeness ?? "--"}</b>
        </div>
        <div className="fact wide">
          <span>Basis</span>
          <b>Deviation from personal baseline</b>
        </div>
      </div>
    </Card>
  );
}
