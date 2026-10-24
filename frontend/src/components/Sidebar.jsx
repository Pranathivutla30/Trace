// Left navigation rail: logo, section links with a sliding active pill
// (scroll-spy driven), the patient chip and the Light/Dark switch.

import { motion } from "framer-motion";
import { Icon } from "./ui.jsx";
import { useReducedMotion } from "../hooks/useUi.js";

export const NAV = [
  { id: "overview", label: "Overview", icon: "dashboard" },
  { id: "whatif", label: "What If", icon: "sliders" },
  { id: "selfcheck", label: "Self-Check", icon: "shield" },
  { id: "trace", label: "Change Point", icon: "pulse" },
  { id: "connections", label: "Connections", icon: "link" },
  { id: "missing", label: "Missing Evidence", icon: "search" },
  { id: "baseline", label: "Baseline", icon: "layers" },
  { id: "trajectories", label: "Trajectories", icon: "branch" },
];

const spring = { type: "spring", stiffness: 420, damping: 36 };

export default function Sidebar({ active, onNav, counts = {}, patientId, subtitle, theme, onTheme }) {
  const reduced = useReducedMotion();
  const transition = reduced ? { duration: 0 } : spring;

  return (
    <aside className="sidebar">
      <div className="logo">
        <span className="logo-mark">
          <Icon name="pulse" size={18} strokeWidth="2.4" />
        </span>
        <span className="logo-text">
          TRACE
          <small>Clinical story</small>
        </span>
      </div>

      <nav className="nav" aria-label="Sections">
        {NAV.map((item) => {
          const isActive = active === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? "active" : ""}`}
              onClick={() => onNav(item.id)}
              aria-current={isActive ? "true" : undefined}
              title={item.label}
            >
              {isActive && <motion.span layoutId="nav-pill" className="nav-pill" transition={transition} />}
              <span className="nav-icon">
                <Icon name={item.icon} size={19} />
              </span>
              <span className="nav-label">{item.label}</span>
              {counts[item.id] ? (
                <span className="nav-count">{counts[item.id]}</span>
              ) : (
                isActive && (
                  <span className="nav-chev">
                    <Icon name="chevron" size={16} />
                  </span>
                )
              )}
            </button>
          );
        })}
      </nav>

      <div className="side-foot">
        <div className="who">
          <span className="avatar">
            {String(patientId || "--").slice(0, 3)}
            <span className="online" />
          </span>
          <div className="who-text">
            <b>Patient {patientId || "--"}</b>
            <span>{subtitle}</span>
          </div>
        </div>

        <div className="theme-toggle" role="radiogroup" aria-label="Theme">
          {[
            ["light", "Light", "sun"],
            ["dark", "Dark", "moon"],
          ].map(([id, label, icon]) => (
            <button
              key={id}
              role="radio"
              aria-checked={theme === id}
              className={`theme-opt ${theme === id ? "active" : ""}`}
              onClick={() => onTheme(id)}
              title={label}
            >
              {theme === id && <motion.span layoutId="theme-pill" className="theme-pill" transition={transition} />}
              <Icon name={icon} size={15} />
              <span className="theme-text">{label}</span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
