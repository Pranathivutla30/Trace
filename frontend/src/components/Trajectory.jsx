// 07 Where Could the Path Diverge? (HealthFork): three trajectory lines from
// one branch point. Simulated scenarios under different assumptions -- NOT
// predictions of a medical outcome.

import { useRef } from "react";
import { useInView } from "framer-motion";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import { Card, CardHead, ChartTooltip } from "./ui.jsx";
import { useReducedMotion } from "../hooks/useUi.js";

const COLORS = ["#22b07d", "#f2a93b", "#ef5a6f"]; // return / plateau / diverge

export default function Trajectory({ trajectories }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, amount: 0.3 });
  const reduced = useReducedMotion();
  if (!trajectories?.length) return null;

  // Re-shape [{name, points:[...]}] into row-per-step for recharts.
  const steps = Math.max(...trajectories.map((t) => t.points.length));
  const data = [];
  for (let i = 0; i < steps; i++) {
    const row = { step: i };
    trajectories.forEach((t) => {
      row[t.name] = t.points[i];
    });
    data.push(row);
  }

  const tick = { fill: "var(--muted)", fontSize: 11 };

  return (
    <Card id="trajectories" className="span-5" delay={0.1}>
      <CardHead title="HealthFork — Where Could the Path Diverge?" eyebrow="Three possible paths from here" />
      <p className="help-line">Three "what could happen" examples: getting back to normal, staying the same, or drifting further.</p>

      <div ref={ref} style={{ height: 210 }}>
        {inView && (
          <ResponsiveContainer width="100%" height={210}>
            <AreaChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
              <defs>
                {trajectories.map((t, i) => (
                  <linearGradient key={t.name} id={`traj-g-${i}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0.22} />
                    <stop offset="100%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid vertical={false} stroke="var(--line)" />
              <XAxis
                dataKey="step"
                tick={tick}
                axisLine={false}
                tickLine={false}
                tickFormatter={(s) => (s === 0 ? "Now" : `+${s}`)}
              />
              <YAxis tick={tick} axisLine={false} tickLine={false} domain={[0, 100]} />
              <Tooltip
                content={<ChartTooltip labelFormatter={(s) => (s === 0 ? "Now" : `Step +${s}`)} />}
                cursor={{ stroke: "var(--muted)", strokeDasharray: "3 3" }}
              />
              {trajectories.map((t, i) => (
                <Area
                  key={t.name}
                  type="monotone"
                  dataKey={t.name}
                  stroke={COLORS[i % COLORS.length]}
                  strokeWidth={2.5}
                  fill={`url(#traj-g-${i})`}
                  dot={{ r: 3, strokeWidth: 0, fill: COLORS[i % COLORS.length] }}
                  activeDot={{ r: 5, strokeWidth: 2, stroke: "var(--tile)" }}
                  isAnimationActive={!reduced}
                  animationBegin={i * 200}
                  animationDuration={1400}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="traj-legend">
        {trajectories.map((t, i) => (
          <div className="traj-item" key={t.name}>
            <span className="sig-dot" style={{ background: COLORS[i % COLORS.length] }} />
            <b>{t.name}</b>
            {t.assumption}
            <span className="end">{t.points[t.points.length - 1]}</span>
          </div>
        ))}
      </div>

      <p className="caption">Example scenarios to explore — not predictions of what will happen.</p>
    </Card>
  );
}
