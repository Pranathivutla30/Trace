// 01 Your Baseline (BioShadow): one tile per available signal.
// Shows current vs. baseline and the z-score (deviation from personal
// baseline), with a knob on a -3..+3 z band.

import { motion } from "framer-motion";
import { signalMeta } from "../config/signals.js";
import { zScore, zLevel, decimalsFor } from "../config/format.js";
import { Card, CardHead, CountUp } from "./ui.jsx";
import { useReducedMotion } from "../hooks/useUi.js";

export default function Baseline({ baseline, timeline, availableSignals }) {
  const reduced = useReducedMotion();
  if (!baseline) return null;
  const last = timeline?.[timeline.length - 1] || {};

  return (
    <Card id="baseline" className="span-7" delay={0.05}>
      <CardHead title="Your Baseline" eyebrow="BioShadow · what is normal for this person?" />
      <div className="tiles">
        {availableSignals.map((key, i) => {
          const meta = signalMeta(key);
          const b = baseline[key];
          if (!b) return null;
          const current = last[key];
          const z = zScore(baseline, timeline, key) ?? 0;
          const left = ((Math.max(-3, Math.min(3, z)) + 3) / 6) * 100;
          return (
            <motion.div
              className="tile"
              key={key}
              initial={reduced ? false : { opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 + i * 0.05 }}
            >
              <div className="tile-top">
                <span className="sig-dot" style={{ background: meta.color }} />
                {meta.label}
                <span className={`zchip ${zLevel(z)}`}>
                  z {z >= 0 ? "+" : ""}
                  {z.toFixed(1)}
                </span>
              </div>
              <div className="tile-value">
                <CountUp value={current} decimals={decimalsFor(current)} />
                <small>{meta.unit}</small>
              </div>
              <div className="tile-sub">
                Baseline {fmt(b.mean)} {meta.unit}
              </div>
              <div className="zbar">
                <motion.span
                  className="zbar-knob"
                  initial={reduced ? false : { left: "50%" }}
                  whileInView={{ left: `${left}%` }}
                  viewport={{ once: true }}
                  transition={{ type: "spring", stiffness: 90, damping: 14, delay: 0.3 + i * 0.05 }}
                  style={reduced ? { left: `${left}%` } : undefined}
                />
              </div>
            </motion.div>
          );
        })}
      </div>
    </Card>
  );
}

function fmt(v) {
  return typeof v === "number" ? Math.round(v * 100) / 100 : "--";
}
