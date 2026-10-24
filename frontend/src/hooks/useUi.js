// Small shared hooks for the Clinical Glass UI.

import { useEffect, useState, useRef } from "react";

// True when the user prefers reduced motion. All non-essential animation
// should check this and render final states instantly.
export function useReducedMotion() {
  const [reduced, setReduced] = useState(
    () =>
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
  );

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const onChange = () => setReduced(mq.matches);
    mq.addEventListener?.("change", onChange);
    return () => mq.removeEventListener?.("change", onChange);
  }, []);

  return reduced;
}

// Light/dark theme stored on <html data-theme>. Remembers the choice when
// storage is available; otherwise follows the OS preference.
export function useTheme() {
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem("trace-theme");
      if (saved === "light" || saved === "dark") return saved;
    } catch {
      /* storage unavailable */
    }
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("trace-theme", theme);
    } catch {
      /* storage unavailable */
    }
  }, [theme]);

  return [theme, setTheme];
}

// Scroll-spy: returns the id of the section nearest the top of the viewport.
// Sections in the same row tie on position; the one later in `ids` wins only
// once it is strictly higher, so the nav follows reading order.
export function useScrollSpy(ids, offset = 140) {
  const [active, setActive] = useState(ids[0]);

  useEffect(() => {
    let raf = 0;
    const update = () => {
      raf = 0;
      const atBottom =
        window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4;
      if (atBottom) {
        setActive(ids[ids.length - 1]);
        return;
      }
      let best = ids[0];
      let bestTop = -Infinity;
      for (const id of ids) {
        const el = document.getElementById(id);
        if (!el) continue;
        const top = el.getBoundingClientRect().top;
        if (top <= offset && top > bestTop + 1) {
          best = id;
          bestTop = top;
        }
      }
      setActive(best);
    };
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(update);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    update();
    return () => {
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(raf);
    };
  }, [ids.join("|"), offset]);

  return [active, setActive];
}

// Cursor spotlight: attach the returned ref to a `.glass` element. It writes
// --mx/--my CSS vars on mousemove so a radial highlight can follow the cursor.
// No-op under reduced motion.
export function useSpotlight(enabled = true) {
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || !enabled) return;
    const onMove = (e) => {
      const r = el.getBoundingClientRect();
      el.style.setProperty("--mx", `${e.clientX - r.left}px`);
      el.style.setProperty("--my", `${e.clientY - r.top}px`);
    };
    el.addEventListener("mousemove", onMove);
    return () => el.removeEventListener("mousemove", onMove);
  }, [enabled]);

  return ref;
}
