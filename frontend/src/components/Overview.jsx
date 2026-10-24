// KPI row: deviation from baseline (with per-signal |z| mini bars),
// interpretation confidence (mini ring) and when the story changed
// (sparkline of the earliest-moving signal with the change marker).

import { motion } from "framer-motion";
import { Card, CountUp, Icon } from "./ui.jsx";
import { signalMeta } from "../config/signals.js";
import { zScore } from "../config/format.js";
import { useReducedMotion } from "../hooks/useUi.js";

export default function Overview({ analysis, timeline, availableSignals, timeUnit, changePoint }) {
  const deviation = analysis?.counterfactuals?.current_deviation;
  const conf = analysis?.self_check?.interpretation_confidence;
  const detectedT = changePoint?.detected_t ?? changePoint?.t;

  const zs = availableSignals
    .map((key) => ({ key, z: zScore(analysis?.baseline, timeline, key) }))
    .filter((d) => d.z != null)
    .slice(0, 7);

  const lead = analysis?.temporal_trace?.order?.[0]?.signal || availableSignals[0];

  const changeValue =
    typeof detectedT !== "number" ? null : timeUnit === "minute" ? detectedT : Math.abs(detectedT);
  const changeUnit = timeUnit === "minute" ? "min in" : detectedT === 0 ? "today" : "days ago";

  return (
    <>
      <Card id="overview" className="span-4 kpi-card kpi" delay={0}>
        <div className="kpi-title">How far from normal</div>
        <div className="kpi-body">
          <span className="icon-circle">
            <Icon name="zap" size={20} />
          </span>
          <div>
            <div className="kpi-value">
              <CountUp value={deviation} />
            </div>
            <div className="kpi-note">0 = normal · higher = bigger change</div>
          </div>
          <MiniBars data={zs} />
        </div>
      </Card>

      <Card className="span-4 kpi-card kpi" delay={0.08}>
        <div className="kpi-title">How sure is TRACE</div>
        <div className="kpi-body">
          <span className="icon-circle">
            <Icon name="shield" size={20} />
          </span>
          <div>
            <div className="kpi-value">
              <CountUp value={conf} />
              <span className="kpi-unit">%</span>
            </div>
            <div className="kpi-note">how sure TRACE is · not a health risk</div>
          </div>
          <MiniRing value={conf} />
        </div>
      </Card>

      <Card className="span-4 kpi-card kpi" delay={0.16}>
        <div className="kpi-title">Story changed</div>
        <div className="kpi-body">
          <span className="icon-circle">
            <Icon name="clock" size={20} />
          </span>
          <div>
            <div className="kpi-value">
              {changeValue == null ? "--" : <CountUp value={changeValue} />}
              <span className="kpi-unit">{changeUnit}</span>
            </div>
            <div className="kpi-note">led by {signalMeta(lead).label}</div>
          </div>
          <Spark timeline={timeline} signal={lead} marker={detectedT} />
        </div>
      </Card>
    </>
  );
}

function MiniBars({ data }) {
  const reduced = useReducedMotion();
  if (!data.length) return null;
  const max = Math.max(...data.map((d) => Math.abs(d.z)), 1);
  const hottest = data.reduce((a, b) => (Math.abs(b.z) > Math.abs(a.z) ? b : a));
  return (
    <div className="kpi-viz" aria-hidden="true">
      {data.map((d, i) => (
        <div className="mini-bar-col" key={d.key} title={`${signalMeta(d.key).label}: ${d.z >= 0 ? "higher" : "lower"} than usual`}>
          <motion.div
            className={`mini-bar ${d === hottest ? "hot" : ""}`}
            style={{ height: `${Math.max(10, (Math.abs(d.z) / max) * 46)}px` }}
            initial={reduced ? false : { scaleY: 0 }}
            whileInView={{ scaleY: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, delay: 0.3 + i * 0.06, ease: [0.22, 1, 0.36, 1] }}
          />
        </div>
      ))}
    </div>
  );
}

function MiniRing({ value }) {
  const reduced = useReducedMotion();
  const r = 22;
  const c = 2 * Math.PI * r;
  const pct = typeof value === "number" ? Math.max(0, Math.min(100, value)) / 100 : 0;
  return (
    <svg className="kpi-viz" width="58" height="58" viewBox="0 0 58 58" aria-hidden="true">
      <circle cx="29" cy="29" r={r} fill="none" stroke="var(--accent-soft)" strokeWidth="7" />
      <motion.circle
        cx="29"
        cy="29"
        r={r}
        fill="none"
        stroke="var(--accent)"
        strokeWidth="7"
        strokeLinecap="round"
        strokeDasharray={c}
        transform="rotate(-90 29 29)"
        initial={reduced ? false : { strokeDashoffset: c }}
        whileInView={{ strokeDashoffset: c * (1 - pct) }}
        viewport={{ once: true }}
        transition={{ duration: 1.2, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
      />
    </svg>
  );
}

function Spark({ timeline, signal, marker }) {
  const reduced = useReducedMotion();
  if (!timeline?.length || !signal) return null;
  const W = 96;
  const H = 52;
  const pts = timeline.filter((p) => typeof p[signal] === "number");
  if (pts.length < 2) return null;
  const t0 = pts[0].t;
  const t1 = pts[pts.length - 1].t;
  const vals = pts.map((p) => p[signal]);
  const lo = Math.min(...vals);
  const hi = Math.max(...vals);
  const x = (t) => ((t - t0) / (t1 - t0 || 1)) * (W - 6) + 3;
  const y = (v) => H - 6 - ((v - lo) / (hi - lo || 1)) * (H - 12);
  const d = pts.map((p, i) => `${i ? "L" : "M"}${x(p.t).toFixed(1)},${y(p[signal]).toFixed(1)}`).join(" ");
  const step = Math.max(1, Math.round(pts.length / 6));
  const dots = pts.filter((_, i) => i % step === 0 || i === pts.length - 1);

  return (
    <svg className="kpi-viz" width={W} height={H} viewBox={`0 0 ${W} ${H}`} aria-hidden="true">
      {typeof marker === "number" && (
        <line x1={x(marker)} x2={x(marker)} y1="2" y2={H - 2} stroke="var(--change)" strokeWidth="1.5" strokeDasharray="3 3" />
      )}
      <motion.path
        d={d}
        fill="none"
        stroke="var(--accent)"
        strokeWidth="2"
        strokeLinecap="round"
        initial={reduced ? false : { pathLength: 0 }}
        whileInView={{ pathLength: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 1.4, delay: 0.3, ease: "easeInOut" }}
      />
      {dots.map((p, i) => (
        <motion.circle
          key={p.t}
          className="spark-dot"
          cx={x(p.t)}
          cy={y(p[signal])}
          r="3"
          initial={reduced ? false : { scale: 0 }}
          whileInView={{ scale: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 + i * 0.12 }}
        />
      ))}
    </svg>
  );
}
