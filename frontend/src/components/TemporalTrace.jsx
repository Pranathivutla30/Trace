// 02 Where Did It Change? (BioTimeMachine) -- HERO section.
// Stacked small area charts, one per available signal, sharing one x-axis.
// A ⚡ vertical line marks the detected change_point (with the span after it
// shaded); real data adds a dashed line for the actual event from `events`,
// with a "detected X after actual" note.

import { useRef } from "react";
import { useInView } from "framer-motion";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  ReferenceLine,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { signalMeta } from "../config/signals.js";
import { fmtT } from "../config/format.js";
import { Card, CardHead, ChartTooltip, Icon } from "./ui.jsx";
import { useReducedMotion } from "../hooks/useUi.js";

const ROW_H = 54;

export default function TemporalTrace({
  timeline,
  availableSignals,
  timeUnit,
  changePoint,
  events,
  temporalTrace,
}) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, amount: 0.15 });
  const reduced = useReducedMotion();
  if (!timeline?.length) return null;

  const detectedT = changePoint?.detected_t ?? changePoint?.t;
  const actualEvent = (events || [])[0];
  const actualT = actualEvent?.t;

  const first = timeline[0].t;
  const lastT = timeline[timeline.length - 1].t;

  // Map each signal to the point where it first deviates (for the sequence highlight).
  const seq = {};
  (temporalTrace?.order || []).forEach((o, i) => {
    seq[o.signal] = { t: o.first_change_t, rank: i + 1 };
  });

  const detectedLagMsg =
    timeUnit === "minute" && typeof detectedT === "number" && typeof actualT === "number"
      ? `TRACE detected the change ${detectedT - actualT} min after the known event.`
      : null;

  const mid = Math.round((first + lastT) / 2);

  return (
    <Card id="trace" className="span-8" delay={0.05}>
      <CardHead
        title="Where Did It Change?"
        eyebrow="BioTimeMachine · the earliest coordinated shift in the story"
        right={
          <div className="chips">
            <span className="chip">
              <span className="ln" /> ⚡ Story changed · {fmtT(detectedT, timeUnit)}
            </span>
            {typeof actualT === "number" && (
              <span className="chip">
                <span className="ln dash" /> {actualEvent.label} · {fmtT(actualT, timeUnit)}
              </span>
            )}
          </div>
        }
      />

      <div className="trace-list" ref={ref}>
        {availableSignals.map((key, i) => {
          const meta = signalMeta(key);
          const s = seq[key];
          return (
            <div className="trace-row" key={key}>
              <div className="trace-meta">
                <span className="sig-dot" style={{ background: meta.color, boxShadow: `0 0 0 4px ${meta.color}22` }} />
                <div style={{ minWidth: 0 }}>
                  <div className="trace-name">{meta.label}</div>
                  <div className="trace-unit">
                    {meta.unit}
                    {s && typeof s.t === "number" && (
                      <span className="order-tag" title={`first deviates ${fmtT(s.t, timeUnit)}`}>
                        #{s.rank} · {fmtT(s.t, timeUnit)}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div style={{ height: ROW_H }}>
                {inView && (
                  <ResponsiveContainer width="100%" height={ROW_H}>
                    <AreaChart data={timeline} margin={{ top: 6, right: 8, left: 0, bottom: 2 }}>
                      <defs>
                        <linearGradient id={`trace-g-${key}`} x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor={meta.color} stopOpacity={0.32} />
                          <stop offset="100%" stopColor={meta.color} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="t" type="number" domain={[first, lastT]} hide />
                      <YAxis hide domain={["auto", "auto"]} />
                      <Tooltip
                        content={<ChartTooltip labelFormatter={(t) => fmtT(t, timeUnit)} unit={meta.unit} />}
                        cursor={{ stroke: "var(--muted)", strokeDasharray: "3 3" }}
                      />
                      {typeof detectedT === "number" && (
                        <ReferenceArea x1={detectedT} x2={lastT} fill="var(--change)" fillOpacity={0.07} />
                      )}
                      {typeof detectedT === "number" && (
                        <ReferenceLine x={detectedT} stroke="var(--change)" strokeWidth={2} />
                      )}
                      {typeof actualT === "number" && (
                        <ReferenceLine x={actualT} stroke="var(--muted)" strokeDasharray="4 4" />
                      )}
                      <Area
                        type="monotone"
                        dataKey={key}
                        name={meta.label}
                        stroke={meta.color}
                        strokeWidth={2}
                        fill={`url(#trace-g-${key})`}
                        dot={false}
                        activeDot={{ r: 4, strokeWidth: 2, stroke: "var(--tile)" }}
                        isAnimationActive={!reduced}
                        animationBegin={i * 90}
                        animationDuration={1300}
                        animationEasing="ease-out"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="trace-axis">
        <span />
        <div>
          <span>{fmtT(first, timeUnit)}</span>
          <span>{fmtT(mid, timeUnit)}</span>
          <span>{fmtT(lastT, timeUnit)}</span>
        </div>
      </div>

      {detectedLagMsg && (
        <div className="callout">
          <Icon name="clock" size={18} />
          {detectedLagMsg}
        </div>
      )}
    </Card>
  );
}
