// 06 What If? (Counterfactual): one pill per signal that has a precomputed
// counterfactual. Clicking calls the POST endpoint and animates the deviation
// from its current value to the counterfactual value (e.g. 78 -> 51), with a
// knob sliding along a 0-100 deviation track.

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { signalMeta } from "../config/signals.js";
import { runCounterfactual } from "../services/api.js";
import { Card, CardHead, Icon } from "./ui.jsx";
import { useReducedMotion } from "../hooks/useUi.js";

export default function Counterfactual({ counterfactuals, patientId, source }) {
  const [active, setActive] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const reduced = useReducedMotion();

  // Reset when the data source changes (signals disappear safely).
  useEffect(() => {
    setActive(null);
    setResult(null);
    setError(null);
  }, [source, patientId]);

  if (!counterfactuals) return null;
  const current = counterfactuals.current_deviation;
  const signals = Object.keys(counterfactuals.signals || {});

  async function onPick(signal) {
    setActive(signal);
    setError(null);
    try {
      const r = await runCounterfactual(patientId, source, signal);
      if (r.new_deviation == null) {
        setError(r.message || "No counterfactual available for this signal.");
        setResult(null);
      } else {
        setResult({ from: r.original_deviation ?? current, to: r.new_deviation, note: r.message });
      }
    } catch (e) {
      setError(e.message);
      setResult(null);
    }
  }

  const pos = (v) => `${Math.max(0, Math.min(100, typeof v === "number" ? v : 0))}%`;
  const target = result ? result.to : current;
  const spring = reduced ? { duration: 0 } : { type: "spring", stiffness: 120, damping: 18 };

  return (
    <Card id="whatif" className="span-4 half card-accent stretch" delay={0.1}>
      <span className="orb" aria-hidden="true" />
      <CardHead title="Counterfactual — What If?" eyebrow="See which signal moved the needle most" />
      <p className="help-line">Tap a signal to imagine it had stayed normal, and see how much the overall change would shrink.</p>

      <div className="cf-ends">
        <div>
          <span>Now</span>
          <b>{result ? result.from : current ?? "--"}</b>
        </div>
        <div className="cf-mid">
          <Icon name="arrow" size={22} />
        </div>
        <div className="right">
          <span>If back to normal</span>
          <b>{result ? <AnimatedNumber key={`${active}-${result.to}`} from={result.from} to={result.to} /> : "—"}</b>
        </div>
      </div>

      <div className="cf-track">
        <motion.span className="cf-fill" animate={{ width: pos(target) }} transition={spring} />
        {result && <span className="cf-ghost" style={{ left: pos(result.from) }} />}
        <motion.span className="cf-knob" animate={{ left: pos(target) }} transition={spring} />
      </div>
      <div className="cf-scale">
        <span>0 · normal</span>
        <span>how far from normal</span>
        <span>100</span>
      </div>

      <div className="cf-pills">
        {signals.map((key) => (
          <button
            key={key}
            className={`cf-pill ${active === key ? "active" : ""}`}
            onClick={() => onPick(key)}
          >
            What if {signalMeta(key).label} stayed normal?
          </button>
        ))}
      </div>

      {error && <div className="cf-error">{error}</div>}
      {result?.note && <div className="cf-note">{result.note}</div>}

      <Sensitivity current={current} signals={counterfactuals.signals} active={active} />


      <p className="caption">A "what if" based on the data — not a prediction.</p>
    </Card>
  );
}

// Ranks signals by how far normalizing each would pull the deviation down,
// using the precomputed counterfactuals already in the analysis payload.
function Sensitivity({ current, signals, active }) {
  const reduced = useReducedMotion();
  if (typeof current !== "number") return null;
  const rows = Object.entries(signals || {})
    .filter(([, v]) => typeof v?.new_deviation === "number")
    .map(([key, v]) => ({ key, drop: current - v.new_deviation }))
    .sort((a, b) => b.drop - a.drop);
  if (!rows.length) return null;
  const max = Math.max(...rows.map((r) => r.drop), 1);

  return (
    <div className="sens">
      <div className="sens-title">How much each signal pulls the score down</div>
      {rows.map((r, i) => (
        <div className={`sens-row ${active === r.key ? "on" : ""}`} key={r.key}>
          <span className="sens-name">{signalMeta(r.key).label}</span>
          <span className="sens-track">
            <motion.span
              className="sens-fill"
              style={{ width: `${(r.drop / max) * 100}%` }}
              initial={reduced ? false : { scaleX: 0 }}
              whileInView={{ scaleX: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.9, delay: 0.3 + i * 0.12, ease: [0.22, 1, 0.36, 1] }}
            />
          </span>
          <b>−{r.drop}</b>
        </div>
      ))}
    </div>
  );
}

function AnimatedNumber({ from, to }) {
  const [val, setVal] = useState(from);
  const raf = useRef();

  useEffect(() => {
    const start = performance.now();
    const dur = 900;
    cancelAnimationFrame(raf.current);
    const tick = (now) => {
      const p = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(Math.round(from + (to - from) * eased));
      if (p < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [from, to]);

  return <>{val}</>;
}
