// 04 What Should We Learn Next? (BioMissing): ranked bars for missing evidence,
// with the single most valuable item called out at the top, and the evidence
// already on hand as chips.

import { motion } from "framer-motion";
import { Card, CardHead, Icon } from "./ui.jsx";
import { useReducedMotion } from "../hooks/useUi.js";

export default function MissingEvidence({ missing }) {
  const reduced = useReducedMotion();
  if (!missing) return null;
  const ranked = missing.most_valuable_missing || [];
  const items = missing.items || [];
  const present = items.filter((i) => i.present).map((i) => i.name);

  return (
    <Card id="missing" delay={0.15}>
      <CardHead title="What Should We Learn Next?" eyebrow="BioMissing · evidence that would most reduce uncertainty" />

      {ranked.map((name, i) => {
        const weight = 1 - i / (ranked.length + 1);
        return (
          <div className={`rank-row${i === 0 ? " top" : ""}`} key={name}>
            <div className="rank-top">
              <span>
                {i === 0 && (
                  <span className="star">
                    <Icon name="star" size={15} fill="currentColor" />
                  </span>
                )}
                {name}
              </span>
              <small>{i === 0 ? "Most valuable" : `#${i + 1}`}</small>
            </div>
            <div className="rank-track">
              <motion.div
                className="rank-fill"
                style={{ width: `${Math.round(weight * 100)}%` }}
                initial={reduced ? false : { scaleX: 0 }}
                whileInView={{ scaleX: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 1, delay: 0.25 + i * 0.15, ease: [0.22, 1, 0.36, 1] }}
              />
            </div>
          </div>
        );
      })}

      {present.length > 0 && (
        <div className="have" aria-label="Already available">
          {present.map((p) => (
            <span className="chip" key={p}>
              <Icon name="check" size={13} strokeWidth="2.6" />
              {p}
            </span>
          ))}
        </div>
      )}
    </Card>
  );
}
