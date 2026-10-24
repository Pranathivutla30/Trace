// ML Physiological Anomaly (trained unsupervised transition model).
// Renders ONLY when analysis.ml_transition_model exists (real f16 today;
// never for synthetic). An anomaly-over-time area chart from the per-window
// ml_anomaly_score, plus the held-out evaluation summary.
//
// The anomaly score measures deviation from learned baseline-like physiological
// patterns. It is NOT a disease/stress probability, diagnosis, or clinical risk
// score. Uses only the existing Clinical Glass primitives -- no new design.

import { useRef } from "react";
import { useInView } from "framer-motion";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  ReferenceLine,
  ReferenceArea,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import { fmtT } from "../config/format.js";
import { Card, CardHead, ChartTooltip, Icon } from "./ui.jsx";
import { useReducedMotion } from "../hooks/useUi.js";

const ANOMALY_COLOR = "#B06CF2"; // violet -- distinct from signal colors

export default function MlAnomaly({ model, timeline, timeUnit, changePoint }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, amount: 0.25 });
  const reduced = useReducedMotion();
  if (!model) return null;

  // Keep only windows that actually have a score; null-skip the rest.
  const data = (timeline || [])
    .filter((p) => typeof p.ml_anomaly_score === "number")
    .map((p) => ({ t: p.t, score: p.ml_anomaly_score }));
  if (!data.length) return null;

  const first = data[0].t;
  const lastT = data[data.length - 1].t;
  const detectedT = changePoint?.detected_t ?? changePoint?.t;

  const facts = [
    { label: "Avg. early (normal)", value: model.baseline_mean_anomaly },
    { label: "Avg. later", value: model.post_baseline_mean_anomaly },
    { label: "Highest score", value: model.peak_anomaly_score },
    { label: "Highest at", value: model.peak_anomaly_window, raw: true },
  ];

  const fmtVal = (v, raw) =>
    typeof v !== "number" ? "--" : raw ? `#${v}` : v.toFixed(4);

  return (
    <Card id="mlanomaly" className="span-8" delay={0.05}>
      <CardHead
        title="ML Physiological Anomaly"
        eyebrow="How unusual each moment looks vs. a learned normal (trained model)"
        right={
          <div className="chips">
            <span className="chip">
              <span className="sig-dot" style={{ background: ANOMALY_COLOR }} /> anomaly score
            </span>
            {typeof detectedT === "number" && (
              <span className="chip">
                <span className="ln" /> ⚡ change · {fmtT(detectedT, timeUnit)}
              </span>
            )}
          </div>
        }
      />

      <p className="help-line">A trained model scores each moment 0–1: higher means it looks more unusual than a learned "normal". It is not a health score.</p>

      <div ref={ref} style={{ height: 210 }}>
        {inView && (
          <ResponsiveContainer width="100%" height={210}>
            <AreaChart data={data} margin={{ top: 8, right: 10, left: -14, bottom: 0 }}>
              <defs>
                <linearGradient id="ml-anom-g" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={ANOMALY_COLOR} stopOpacity={0.32} />
                  <stop offset="100%" stopColor={ANOMALY_COLOR} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} stroke="var(--line)" />
              <XAxis
                dataKey="t"
                type="number"
                domain={[first, lastT]}
                tick={{ fill: "var(--muted)", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(t) => fmtT(t, timeUnit)}
              />
              <YAxis
                domain={[0, 1]}
                tick={{ fill: "var(--muted)", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                content={<ChartTooltip labelFormatter={(t) => fmtT(t, timeUnit)} />}
                cursor={{ stroke: "var(--muted)", strokeDasharray: "3 3" }}
              />
              {typeof detectedT === "number" && (
                <ReferenceArea x1={detectedT} x2={lastT} fill="var(--change)" fillOpacity={0.07} />
              )}
              {typeof detectedT === "number" && (
                <ReferenceLine x={detectedT} stroke="var(--change)" strokeWidth={2} />
              )}
              <Area
                type="monotone"
                dataKey="score"
                name="Anomaly score"
                stroke={ANOMALY_COLOR}
                strokeWidth={2.5}
                fill="url(#ml-anom-g)"
                dot={false}
                activeDot={{ r: 4, strokeWidth: 2, stroke: "var(--tile)" }}
                isAnimationActive={!reduced}
                animationDuration={1300}
                animationEasing="ease-out"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="facts">
        {facts.map((f) => (
          <div className="fact" key={f.label}>
            <span>{f.label}</span>
            <b>{fmtVal(f.value, f.raw)}</b>
          </div>
        ))}
      </div>

      <div className="callout">
        <Icon name="shield" size={18} />
        {`Learned from ${model.training_participant_count ?? "--"} other people · `}
        {`then tested on ${model.held_out_participant ?? "--"}, who it had never seen`}
      </div>

      <p className="caption">
        {model.note ||
          "ML physiological anomaly score — deviation from learned baseline-like " +
            "patterns. Not a disease probability, stress probability, diagnosis, or " +
            "clinical risk score."}
      </p>
    </Card>
  );
}
