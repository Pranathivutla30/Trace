// TRACE app shell / router.
//
// Flow: Welcome -> Onboarding (first visit) -> Choose Experience -> Dashboard.
// Returning visit: Welcome (recognized) -> Choose Experience -> Dashboard.
// The existing Investigation dashboard is rendered unchanged; onboarding is a
// frontend-only layer in front of it. Profile persistence lives entirely in
// services/profileStorage.js (localStorage prototype).

import { useState } from "react";
import Investigation from "./pages/Investigation.jsx";
import Aurora from "./components/Aurora.jsx";
import Welcome from "./components/onboarding/Welcome.jsx";
import OnboardingFlow from "./components/onboarding/OnboardingFlow.jsx";
import ExperienceSelector from "./components/onboarding/ExperienceSelector.jsx";
import ProfileMenu from "./components/onboarding/ProfileMenu.jsx";
import { useTheme } from "./hooks/useUi.js";
import {
  loadTraceProfile,
  saveTraceProfile,
  clearTraceProfile,
  hasCompletedProfile,
  firstName,
} from "./services/profileStorage.js";

// Flow stages.
const STAGE = {
  WELCOME: "welcome",
  ONBOARDING: "onboarding",
  CHOOSE: "choose",
  DASHBOARD: "dashboard",
};

export default function App() {
  // Keep the theme active on all screens (onboarding included).
  useTheme();

  const [profile, setProfile] = useState(() => loadTraceProfile());
  const [stage, setStage] = useState(STAGE.WELCOME);
  const [source, setSource] = useState(null); // chosen experience: "synthetic" | "real"
  const [editing, setEditing] = useState(false);

  const completed = !!(profile && profile.onboardingCompleted);

  // ----- Welcome actions -----
  const startOnboarding = () => {
    setEditing(false);
    setStage(STAGE.ONBOARDING);
  };
  const continueToChoose = () => setStage(STAGE.CHOOSE);
  const editProfile = () => {
    setEditing(true);
    setStage(STAGE.ONBOARDING);
  };
  const useDifferentProfile = () => {
    clearTraceProfile();
    setProfile(null);
    setEditing(false);
    setStage(STAGE.WELCOME);
  };

  // ----- Onboarding complete -----
  const handleComplete = (p) => {
    const saved = saveTraceProfile(p);
    setProfile(saved);
    setEditing(false);
    // After first-time onboarding go to experience choice; after an edit from
    // inside the dashboard, return to the dashboard.
    setStage(STAGE.CHOOSE);
  };
  const handleCancelOnboarding = () => {
    // Back from the first step: return to Welcome (keep any existing profile).
    setStage(STAGE.WELCOME);
  };

  // ----- Experience choice -----
  const pickExperience = (src) => {
    setSource(src);
    setStage(STAGE.DASHBOARD);
  };

  // ----- In-dashboard profile menu -----
  const exitProfile = () => {
    // Return to welcome WITHOUT deleting the saved profile.
    setStage(STAGE.WELCOME);
  };
  const changeExperience = () => setStage(STAGE.CHOOSE);
  const editFromDashboard = () => {
    setEditing(true);
    setStage(STAGE.ONBOARDING);
  };

  // ----- Render by stage -----
  if (stage === STAGE.WELCOME) {
    return (
      <>
        <Aurora />
        <Welcome
          profile={completed ? profile : null}
          onStart={startOnboarding}
          onContinue={continueToChoose}
          onEdit={editProfile}
          onUseDifferent={useDifferentProfile}
        />
      </>
    );
  }

  if (stage === STAGE.ONBOARDING) {
    return (
      <>
        <Aurora />
        <OnboardingFlow
          initial={editing ? profile : null}
          onComplete={handleComplete}
          onCancel={handleCancelOnboarding}
        />
      </>
    );
  }

  if (stage === STAGE.CHOOSE) {
    return (
      <>
        <Aurora />
        <ExperienceSelector name={firstName(profile)} onPick={pickExperience} />
      </>
    );
  }

  // DASHBOARD -- existing Investigation page, unchanged, with a profile control.
  const userName = firstName(profile) || profile?.account?.fullName || "";
  return (
    <Investigation
      initialSource={source || "synthetic"}
      userName={userName}
      profileControl={
        <ProfileMenu
          profile={profile}
          onEdit={editFromDashboard}
          onChangeExperience={changeExperience}
          onExit={exitProfile}
        />
      }
    />
  );
}

// Re-export for any callers that check completion at module level.
export { hasCompletedProfile };
