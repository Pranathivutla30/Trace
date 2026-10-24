// Living aurora background: three large blurred blobs that drift slowly, plus
// a faint SVG noise texture so the glass feels physical. Fixed behind content.
// Drift is pure CSS (transform only); reduced motion freezes it via media query.

export default function Aurora() {
  return (
    <div className="aurora" aria-hidden="true">
      <span className="blob blob-a" />
      <span className="blob blob-b" />
      <span className="blob blob-c" />
      <svg className="noise" width="100%" height="100%">
        <filter id="trace-noise">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.9"
            numOctaves="2"
            stitchTiles="stitch"
          />
        </filter>
        <rect width="100%" height="100%" filter="url(#trace-noise)" />
      </svg>
    </div>
  );
}
