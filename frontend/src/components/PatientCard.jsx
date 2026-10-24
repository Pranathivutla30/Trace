// Patient details: signal count, window and change point as stat tiles, plus
// the patient row with a shortcut to the change-point chart.

import { Card, CardHead, Icon } from "./ui.jsx";
import { fmtT, windowLabel } from "../config/format.js";

export default function PatientCard({ patient, availableSignals, changePoint, sourceLabel, onJump }) {
  if (!patient) return null;
  const detectedT = changePoint?.detected_t ?? changePoint?.t;
  const unit = patient.time_unit;

  return (
    <Card className="span-4 half stretch" delay={0.05}>
      <CardHead
        title="Patient Details"
        eyebrow={
          <>
            {sourceLabel}
            <span className="sep">|</span>
            {patient.data_status === "mock" ? "Mock data" : "Live data"}
          </>
        }
      />
      <div className="stat-tiles">
        <div className="stat-tile">
          <b>{availableSignals.length}</b>
          <span>Signals</span>
        </div>
        <div className="stat-tile">
          <b>{unit === "minute" ? "40 min" : unit === "day" ? "30 days" : "--"}</b>
          <span>Window</span>
        </div>
        <div className="stat-tile">
          <b>{fmtT(detectedT, unit)}</b>
          <span>Change detected</span>
        </div>
      </div>

      <div className="sub-label">Subject</div>
      <div className="person">
        <span className="avatar">{String(patient.id).slice(0, 3)}</span>
        <div>
          <b>Patient {patient.id}</b>
          <span>{windowLabel(patient)}</span>
        </div>
        <button className="round-btn" onClick={onJump} title="Jump to change point">
          <Icon name="pulse" size={18} />
        </button>
      </div>
    </Card>
  );
}
