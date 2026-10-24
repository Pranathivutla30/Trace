// 03 What Changed Together? (ReverseHealth): a vertical flow built from the
// hypothesis graph edges, each step annotated with when that signal first
// moved. Associations, explicitly NOT proven causation.

import { motion } from "framer-motion";
import { signalMeta } from "../config/signals.js";
import { fmtT } from "../config/format.js";
import { Card, CardHead } from "./ui.jsx";
import { useReducedMotion } from "../hooks/useUi.js";

export default function Connections({ connections, temporalTrace, timeUnit }) {
  const reduced = useReducedMotion();
  if (!connections) return null;
  const edges = connections.edges || [];

  // Build an ordered node chain from the edges (from -> to -> ...).
  const chain = [];
  edges.forEach((e, i) => {
    if (i === 0) chain.push(e.from);
    chain.push(e.to);
  });

  const firstChange = {};
  (temporalTrace?.order || []).forEach((o) => {
    firstChange[o.signal] = o.first_change_t;
  });

  return (
    <Card id="connections" delay={0.1}>
      <CardHead title="What Changed Together?" eyebrow="ReverseHealth · observed signal relationships" />

      {connections.hypothesis && <p className="hypo">{connections.hypothesis}</p>}

      <div className="flow" role="list">
        <span className="flow-line" aria-hidden="true">
          <motion.span
            className="flow-line-fill"
            initial={reduced ? false : { scaleY: 0 }}
            whileInView={{ scaleY: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 1.2, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
          />
        </span>
        {chain.map((key, i) => {
          const meta = signalMeta(key);
          const rel = edges[i]?.relation;
          return (
            <motion.div
              role="listitem"
              className="flow-step"
              key={`${key}-${i}`}
              style={{ "--c": meta.color }}
              initial={reduced ? false : { opacity: 0, x: -10 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.3 + i * 0.18 }}
            >
              <span className="flow-dot" />
              <div className="flow-body">
                <div>
                  <b>{meta.label}</b>
                  {rel && i < chain.length - 1 && <em>{rel} ↓</em>}
                </div>
                <span className="flow-time">
                  {typeof firstChange[key] === "number" ? fmtT(firstChange[key], timeUnit) : ""}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>

      <p className="caption">Observed temporal associations, not proven causation.</p>
    </Card>
  );
}
