// 01 Your Baseline (BioShadow): a compact table — one row per available
// signal — showing the person's usual value, today's value, and the percent
// deviation from their personal baseline. Color is driven by the z-score so a
// signal keeps a consistent "how far from normal" cue.

import { motion } from "framer-motion";
import { signalMeta } from "../config/signals.js";
import { zScore, zLevel, decimalsFor } from "../config/format.js";
import { Card, CardHead } from "./ui.jsx";
import { useReducedMotion } from "../hooks/useUi.js";

export default function Baseline({ baseline, timeline, availableSignals }) {
  const reduced = useReducedMotion();
  if (!baseline) return null;
  const last = timeline?.[timeline.length - 1] || {};

  const rows = availableSignals
    .map((key) => {
      const b = baseline[key];
      if (!b) return null;
      const meta = signalMeta(key);
      const current = last[key];
      const z = zScore(baseline, timeline, key) ?? 0;
      // Percent change of today's value vs. the personal baseline mean.
      const pct =
        typeof current === "number" && typeof b.mean === "number" && b.mean !== 0
          ? ((current - b.mean) / Math.abs(b.mean)) * 100
          : null;
      return { key, meta, b, current, z, pct };
    })
    .filter(Boolean);

  return (
    <Card id="baseline" className="span-7" delay={0.05}>
      <CardHead title="BioShadow — Your Baseline" eyebrow="What's normal for this person, day to day" />
      <p className="help-line">
        For each signal: the person's usual value, their latest value, and how far that is from normal.
      </p>

      <div className="bl-table" role="table" aria-label="Baseline comparison">
        <div className="bl-head" role="row">
          <span role="columnheader">Signal</span>
          <span role="columnheader">Baseline (usual)</span>
          <span role="columnheader">Latest value</span>
          <span role="columnheader">Deviation</span>
        </div>

        {rows.map((r, i) => (
          <motion.div
            className="bl-row"
            role="row"
            key={r.key}
            initial={reduced ? false : { opacity: 0, y: 8 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.05 + i * 0.04 }}
          >
            <span className="bl-sig" role="cell">
              <span className="sig-dot" style={{ background: r.meta.color }} />
              <span className="bl-sig-text">
                <b>{r.meta.label}</b>
                {r.meta.full && <small className="sig-full">{r.meta.full}</small>}
              </span>
            </span>
            <span className="bl-num" role="cell">
              {fmt(r.b.mean)} <em>{r.meta.unit}</em>
            </span>
            <span className="bl-num" role="cell">
              {typeof r.current === "number" ? fmt(r.current) : "--"} <em>{r.meta.unit}</em>
            </span>
            <span className="bl-dev" role="cell">
              <span
                className={`zchip ${zLevel(r.z)}`}
                title={
                  r.pct == null
                    ? "No comparison available"
                    : `${r.pct >= 0 ? "Higher" : "Lower"} than usual`
                }
              >
                {r.pct == null
                  ? "--"
                  : `${r.pct >= 0 ? "↑" : "↓"} ${Math.abs(r.pct).toFixed(0)}% ${r.pct >= 0 ? "higher" : "lower"}`}
              </span>
            </span>
          </motion.div>
        ))}
      </div>
    </Card>
  );
}

function fmt(v) {
  return typeof v === "number" ? Math.round(v * 100) / 100 : "--";
}
