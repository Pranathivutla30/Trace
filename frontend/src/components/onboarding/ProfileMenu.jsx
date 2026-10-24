// Small unobtrusive profile control for the dashboard top bar.
// Shows the user's initials/first name; opens a menu with View/Edit Profile,
// Change Experience, and Exit Profile. "Exit Profile" returns to Welcome but
// never deletes the saved profile (this is localStorage, not real auth).

import { useState, useRef, useEffect } from "react";
import { Icon } from "../ui.jsx";

export default function ProfileMenu({ profile, onEdit, onChangeExperience, onExit }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const name = profile?.account?.fullName?.trim()?.split(/\s+/)[0] || "Guest";
  const initials = name.slice(0, 2).toUpperCase();

  useEffect(() => {
    const onDoc = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  return (
    <div className="pm" ref={ref}>
      <button className="pm-trigger" onClick={() => setOpen((o) => !o)} aria-haspopup="menu" aria-expanded={open}>
        <span className="avatar pm-avatar">{initials}</span>
        <span className="pm-name">{name}</span>
        <Icon name="chevron" size={14} />
      </button>

      {open && (
        <div className="pm-menu glass-plain" role="menu">
          <button role="menuitem" className="pm-item" onClick={() => { setOpen(false); onEdit(); }}>
            <Icon name="layers" size={16} /> View / Edit Profile
          </button>
          <button role="menuitem" className="pm-item" onClick={() => { setOpen(false); onChangeExperience(); }}>
            <Icon name="sliders" size={16} /> Change Experience
          </button>
          <div className="pm-sep" />
          <button role="menuitem" className="pm-item" onClick={() => { setOpen(false); onExit(); }}>
            <Icon name="arrow" size={16} /> Exit Profile
          </button>
        </div>
      )}
    </div>
  );
}
