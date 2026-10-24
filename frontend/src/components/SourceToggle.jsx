// Data-source segmented toggle + data badge.
// The active option sits on a white pill that slides between options via
// framer-motion layoutId (spring). The badge crossfades on source change.
// Purely presentational -- it calls onChange(id); no data logic changes.

import { motion, AnimatePresence } from "framer-motion";
import { useReducedMotion } from "../hooks/useUi.js";

export default function SourceToggle({ sources, source, onChange, loading }) {
  const reduced = useReducedMotion();
  const isReal = source === "real";

  return (
    <div className="toggle-wrap">
      <div className="toggle glass-plain" role="tablist" aria-label="Data source">
        {sources.map((s) => {
          const active = source === s.id;
          return (
            <button
              key={s.id}
              role="tab"
              aria-selected={active}
              className={`toggle-opt ${active ? "active" : ""}`}
              onClick={() => onChange(s.id)}
              disabled={loading && active}
            >
              {active && (
                <motion.span
                  layoutId="toggle-pill"
                  className="toggle-pill"
                  transition={
                    reduced
                      ? { duration: 0 }
                      : { type: "spring", stiffness: 400, damping: 32 }
                  }
                />
              )}
              <span className="toggle-label">{s.label}</span>
            </button>
          );
        })}
      </div>

      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={source}
          className={`badge ${isReal ? "real" : "synthetic"}`}
          initial={reduced ? false : { opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reduced ? { opacity: 0 } : { opacity: 0, y: 4 }}
          transition={{ duration: reduced ? 0 : 0.25 }}
        >
          <span className="badge-dot" />
          {isReal ? "REAL DATA · PhysioNet" : "SYNTHETIC DATA"}
        </motion.span>
      </AnimatePresence>
    </div>
  );
}
