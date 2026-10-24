// Patient details: signal count, window and change point as stat tiles, plus
// the patient row with a shortcut to the change-point chart.

import { Card, CardHead, Icon } from "./ui.jsx";
import { fmtT, windowLabel } from "../config/format.js";

export default function PatientCard({ patient, availableSignals, changePoint, sourceLabel, onJump, timeline, userName }) {
  if (!patient) return null;
  const detectedT = changePoint?.detected_t ?? changePoint?.t;
  const unit = patient.time_unit;
  // The card describes the dataset subject (001 / f16), not the logged-in user.
  const subjectLabel = `Subject ${patient.id}`;
  const n = Array.isArray(timeline) ? timeline.length : null;
  const windowStat =
    unit === "minute"
      ? n ? `${n} min` : patient.window || "--"
      : unit === "day"
      ? n ? `${n} days` : "--"
      : "--";

  return (
    <Card className="span-4 half stretch" delay={0.05}>
      <CardHead
        title="Investigation Details"
        eyebrow={
          <>
            {userName ? `Reviewed by ${userName}` : sourceLabel}
            <span className="sep">|</span>
            {patient.data_status === "mock" ? "Mock data" : "Live data"}
          </>
        }
      />
      <div className="stat-tiles">
        <div className="stat-tile">
          <b>{availableSignals.length}</b>
          <span>Physiological signals</span>
        </div>
        <div className="stat-tile">
          <b>{windowStat}</b>
          <span>Window of data</span>
        </div>
        <div className="stat-tile">
          <b>{fmtT(detectedT, unit)}</b>
          <span>Story changed</span>
        </div>
      </div>

      <div className="sub-label">Exploring as</div>
      <div className="person">
        <span className="avatar">
          {String(userName || patient.id).slice(0, 2).toUpperCase()}
        </span>
        <div>
          <b>{userName || subjectLabel}</b>
          <span>
            {windowLabel(patient, timeline)}
            {userName ? ` · viewing ${subjectLabel.toLowerCase()}` : ""}
          </span>
        </div>
        <button className="round-btn" onClick={onJump} title="Jump to change point">
          <Icon name="pulse" size={18} />
        </button>
      </div>
    </Card>
  );
}
