// The single TRACE investigation view -- one patient, one story.
// Capability components mount here in investigation order. Starter shell only.

import CapabilityCard from "../components/CapabilityCard.jsx";

const CAPABILITIES = [
  ["Personal Baseline", "What is normal for this person?"],
  ["Temporal Trace", "Where did the story change?"],
  ["Signal Connections", "What changed together?"],
  ["Missing Evidence", "What don't we know?"],
  ["AI Self-Check", "Should we trust this conclusion?"],
  ["Counterfactual Explorer", "What would change the conclusion?"],
  ["Trajectory Explorer", "What other paths could this story take?"],
];

export default function InvestigationPage() {
  return (
    <main>
      <h1>TRACE</h1>
      <p>Find where the story changed.</p>
      {CAPABILITIES.map(([title, question]) => (
        <CapabilityCard key={title} title={title} question={question} />
      ))}
    </main>
  );
}
