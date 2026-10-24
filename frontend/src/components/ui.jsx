// Shared presentational building blocks for the dashboard: animated Card,
// CardHead, CountUp numbers, a small inline icon set and the chart tooltip.

import { useEffect, useRef, useState } from "react";
import { motion, useInView } from "framer-motion";
import { useReducedMotion, useSpotlight } from "../hooks/useUi.js";

// Card surface that rises into place the first time it scrolls into view,
// with a cursor-following spotlight.
export function Card({ id, className = "", delay = 0, children }) {
  const reduced = useReducedMotion();
  const ref = useSpotlight(!reduced);
  return (
    <motion.section
      id={id}
      ref={ref}
      className={`card spot ${className}`}
      initial={reduced ? false : { opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.1 }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1], delay }}
    >
      {children}
    </motion.section>
  );
}

export function CardHead({ title, eyebrow, right }) {
  return (
    <header className="card-head">
      <div>
        <h2 className="card-title">{title}</h2>
        {eyebrow && <p className="card-eyebrow">{eyebrow}</p>}
      </div>
      {right}
    </header>
  );
}

// Counts from the previously shown value to `value` once visible.
export function CountUp({ value, decimals = 0, duration = 1100 }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });
  const reduced = useReducedMotion();
  const [shown, setShown] = useState(0);
  const cur = useRef(0);

  useEffect(() => {
    if (typeof value !== "number" || !inView) return;
    if (reduced) {
      cur.current = value;
      setShown(value);
      return;
    }
    const from = cur.current;
    const start = performance.now();
    let raf;
    const tick = (now) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      cur.current = from + (value - from) * eased;
      setShown(cur.current);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, inView, reduced, duration]);

  if (typeof value !== "number") return <span ref={ref}>--</span>;
  return (
    <span ref={ref} className="num-tab">
      {shown.toFixed(decimals)}
    </span>
  );
}

const PATHS = {
  dashboard: (
    <>
      <rect x="3" y="3" width="7" height="9" rx="2" />
      <rect x="14" y="3" width="7" height="5" rx="2" />
      <rect x="14" y="12" width="7" height="9" rx="2" />
      <rect x="3" y="16" width="7" height="5" rx="2" />
    </>
  ),
  layers: (
    <>
      <path d="m12 3 9 5-9 5-9-5 9-5z" />
      <path d="m3 13 9 5 9-5" />
    </>
  ),
  pulse: <path d="M3 12h4l2.5-6 4 12 2.5-6H21" />,
  link: (
    <>
      <circle cx="6" cy="6" r="2.5" />
      <circle cx="18" cy="18" r="2.5" />
      <path d="M8.5 6h4a4 4 0 0 1 4 4v5.5" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </>
  ),
  shield: (
    <>
      <path d="M12 3 4 6v6c0 4.5 3.4 8.3 8 9 4.6-.7 8-4.5 8-9V6l-8-3z" />
      <path d="m9 12 2 2 4-4" />
    </>
  ),
  sliders: (
    <>
      <path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1" />
      <circle cx="15" cy="6" r="2" />
      <circle cx="9" cy="12" r="2" />
      <circle cx="17" cy="18" r="2" />
    </>
  ),
  branch: (
    <>
      <path d="M6 3v12" />
      <circle cx="6" cy="18" r="3" />
      <circle cx="18" cy="6" r="3" />
      <path d="M18 9a9 9 0 0 1-9 9" />
    </>
  ),
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </>
  ),
  moon: <path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" />,
  chevron: <path d="m9 6 6 6-6 6" />,
  arrow: <path d="M5 12h14m-5-5 5 5-5 5" />,
  zap: <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z" />,
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  check: <path d="m5 12 5 5 9-10" />,
  star: <path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1 6.2L12 17.3 6.5 20.2l1-6.2L3 9.6l6.2-.9L12 3z" />,
  alert: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v6M12 16.5v.5" />
    </>
  ),
};

export function Icon({ name, size = 18, fill = "none", ...rest }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={fill}
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...rest}
    >
      {PATHS[name]}
    </svg>
  );
}

// Recharts custom tooltip, styled via CSS so it follows the theme.
export function ChartTooltip({ active, payload, label, labelFormatter, unit }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tip">
      <div className="chart-tip-label">
        {labelFormatter ? labelFormatter(label) : label}
      </div>
      {payload.map((p) => (
        <div className="chart-tip-row" key={p.dataKey}>
          <span className="dot" style={{ background: p.stroke || p.color }} />
          {p.name}
          <b>
            {typeof p.value === "number" ? Math.round(p.value * 100) / 100 : p.value}
            {unit ? ` ${unit}` : ""}
          </b>
        </div>
      ))}
    </div>
  );
}
