// The single TRACE investigation page. One patient, one story.
//
// Source state defaults to "synthetic". When it changes, the timeline and
// analysis refetch; a skeleton shows during the switch. Only signals in
// `available_signals` render, so flipping sources never leaves empty charts,
// and any fetch error shows a message instead of a blank screen.

import { useState, useEffect } from "react";
import { getSources, getPatient, getTimeline, getAnalysis } from "../services/api.js";
import Overview from "../components/Overview.jsx";
import PatientCard from "../components/PatientCard.jsx";
import Baseline from "../components/Baseline.jsx";
import TemporalTrace from "../components/TemporalTrace.jsx";
import Connections from "../components/Connections.jsx";
import MissingEvidence from "../components/MissingEvidence.jsx";
import SelfCheck from "../components/SelfCheck.jsx";
import Counterfactual from "../components/Counterfactual.jsx";
import Trajectory from "../components/Trajectory.jsx";
import MlAnomaly from "../components/MlAnomaly.jsx";
import YourContext from "../components/YourContext.jsx";
import Aurora from "../components/Aurora.jsx";
import TopBar from "../components/TopBar.jsx";
import Sidebar, { NAV } from "../components/Sidebar.jsx";
import { Icon } from "../components/ui.jsx";
import { fmtT, windowLabel } from "../config/format.js";
import { useScrollSpy, useTheme } from "../hooks/useUi.js";

const CITATION =
  "Hongn, A., Bosch, F., Prado, L., & Bonomini, P. (2025). Wearable Device Dataset from Induced Stress and Structured Exercise Sessions (v1.0.1). PhysioNet. https://doi.org/10.13026/he0v-tf17";

export default function Investigation({ initialSource = "synthetic", profileControl = null, userName = "" }) {
  const [sources, setSources] = useState([]);
  const [source, setSource] = useState(initialSource);
  const [patient, setPatient] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [theme, setTheme] = useTheme();
  const [activeId, setActiveId] = useScrollSpy(NAV.map((n) => n.id));

  // Load the source list once.
  useEffect(() => {
    getSources().then(setSources).catch((e) => setError(e.message));
  }, []);

  // Refetch whenever the source changes.
  useEffect(() => {
    const meta = sourcePatientId(sources, source);
    const patientId = meta || (source === "real" ? "f16" : "001");

    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([
      getPatient(patientId, source),
      getTimeline(patientId, source),
      getAnalysis(patientId, source),
    ])
      .then(([p, t, a]) => {
        if (cancelled) return;
        setPatient(p);
        setTimeline(t);
        setAnalysis(a);
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [source, sources]);

  const patientId = patient?.id || (source === "real" ? "f16" : "001");
  const available = timeline?.available_signals || patient?.available_signals || [];
  const timeUnit = timeline?.time_unit || patient?.time_unit;
  const changePoint = timeline?.change_point;
  const detectedT = changePoint?.detected_t ?? changePoint?.t;
  const sourceList = sources.length ? sources : DEFAULT_SOURCES;
  const sourceLabel = sourceList.find((s) => s.id === source)?.label || source;

  function jump(id) {
    setActiveId(id);
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  const tl = timeline?.timeline;
  const isReal = source === "real";
  // Counterfactual and HealthFork exist only for the synthetic demo.
  const hasWhatIf = !!analysis?.counterfactuals;
  const hasTrajectories = !!(analysis?.trajectories && analysis.trajectories.length);

  const subtitle = patient
    ? `${windowLabel(patient, tl)} · ${available.length} signals · story changed ${fmtT(detectedT, timeUnit)}`
    : "Find where the story changed.";

  return (
    <>
      <Aurora />
      <div className="shell">
        <Sidebar
          active={activeId}
          onNav={jump}
          counts={{ missing: analysis?.missing_evidence?.most_valuable_missing?.length }}
          patientId={patientId}
          userName={userName}
          subtitle={windowLabel(patient, tl)}
          theme={theme}
          onTheme={setTheme}
          hiddenIds={navHidden(hasWhatIf, hasTrajectories, !!analysis?.ml_transition_model)}
        />

        <main className="main">
          <TopBar
            title={userName ? `${userName}'s Investigation` : "TRACE Investigation"}
            subtitle={subtitle}
            sources={sourceList}
            source={source}
            onChange={setSource}
            loading={loading}
            onCta={hasWhatIf ? () => jump("whatif") : null}
            profileControl={profileControl}
          />

          {error && (
            <div className="state-card" role="alert">
              <Icon name="alert" size={22} />
              Could not load the investigation: {error}
            </div>
          )}

          {loading && !error && <Skeleton />}

          {!loading && !error && patient && (
            <div key={source}>
              <div className="bento">
                <Overview
                  analysis={analysis}
                  timeline={timeline?.timeline}
                  availableSignals={available}
                  timeUnit={timeUnit}
                  changePoint={changePoint}
                />
              </div>

              <div className="bento">
                <YourContext
                  source={source}
                  analysis={analysis}
                  timeUnit={timeUnit}
                  changePoint={changePoint}
                />
              </div>

              <div className="bento">
                <PatientCard
                  patient={patient}
                  availableSignals={available}
                  changePoint={changePoint}
                  sourceLabel={sourceLabel}
                  onJump={() => jump("trace")}
                  timeline={tl}
                  userName={userName}
                />
                <Counterfactual
                  counterfactuals={analysis?.counterfactuals}
                  patientId={patientId}
                  source={source}
                />
                <SelfCheck selfCheck={analysis?.self_check} />
              </div>

              <div className="bento">
                <TemporalTrace
                  timeline={timeline?.timeline}
                  availableSignals={available}
                  timeUnit={timeUnit}
                  changePoint={changePoint}
                  events={timeline?.events}
                  temporalTrace={analysis?.temporal_trace}
                />
                <div className="stack span-4">
                  <Connections
                    connections={analysis?.connections}
                    temporalTrace={analysis?.temporal_trace}
                    timeUnit={timeUnit}
                  />
                  <MissingEvidence missing={analysis?.missing_evidence} />
                </div>
              </div>

              {analysis?.ml_transition_model && (
                <div className="bento">
                  <MlAnomaly
                    model={analysis.ml_transition_model}
                    timeline={timeline?.timeline}
                    timeUnit={timeUnit}
                    changePoint={changePoint}
                  />
                </div>
              )}

              <div className="bento">
                <Baseline
                  baseline={analysis?.baseline}
                  timeline={timeline?.timeline}
                  availableSignals={available}
                />
                <Trajectory trajectories={analysis?.trajectories} />
              </div>
            </div>
          )}

          <footer className="cite">
            {isReal ? (
              CITATION
            ) : (
              <>
                Synthetic demonstration patient generated for TRACE. For
                demonstration of the full temporal investigation workflow.
              </>
            )}
          </footer>
        </main>
      </div>
    </>
  );
}

function Skeleton() {
  const blocks = [
    [4, 150], [4, 150], [4, 150],
    [4, 300], [4, 300], [4, 300],
    [8, 520], [4, 520],
  ];
  return (
    <div className="skeleton" aria-busy="true" aria-label="Loading the investigation">
      {blocks.map(([span, h], i) => (
        <div key={i} className="skel" style={{ gridColumn: `span ${span}`, height: h, animationDelay: `${i * 0.08}s` }} />
      ))}
    </div>
  );
}

const DEFAULT_SOURCES = [
  { id: "synthetic", label: "Synthetic Demo", patient_id: "001" },
  { id: "real", label: "Real Wearable Data", patient_id: "f16" },
];

function sourcePatientId(sources, source) {
  const found = sources.find((s) => s.id === source);
  return found?.patient_id;
}

// Which sidebar nav ids to hide for the current source. Counterfactual
// ("whatif") and HealthFork ("trajectories") exist only for the synthetic
// demo; the ML section is real-only. Hidden sections simply aren't in the DOM,
// so the scroll-spy skips them safely.
function navHidden(hasWhatIf, hasTrajectories, hasMl) {
  const hidden = [];
  if (!hasWhatIf) hidden.push("whatif");
  if (!hasTrajectories) hidden.push("trajectories");
  if (!hasMl) hidden.push("mlanomaly");
  return hidden;
}
