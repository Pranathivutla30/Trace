// Page header: greeting-style title + story subtitle on the left; data source
// toggle, badge and the "Run what-if" call to action on the right.

import { motion } from "framer-motion";
import SourceToggle from "./SourceToggle.jsx";
import { Icon } from "./ui.jsx";
import { useReducedMotion } from "../hooks/useUi.js";

export default function TopBar({ title, subtitle, sources, source, onChange, loading, onCta, profileControl }) {
  const reduced = useReducedMotion();
  return (
    <motion.header
      className="header"
      initial={reduced ? false : { opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
    >
      <div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      <div className="header-actions">
        <SourceToggle sources={sources} source={source} onChange={onChange} loading={loading} />
        {onCta && (
          <button className="cta" onClick={onCta}>
            <Icon name="sliders" size={16} />
            Run what-if
          </button>
        )}
        {profileControl}
      </div>
    </motion.header>
  );
}
