# TRACE — Demo Video Script (exactly 2:45, frontend-focused)

A tightly timed, plain-English walkthrough. You record the **frontend on screen**
following the "WHAT TO SHOW" cues; paste each "NARRATION" block into your AI
text-to-speech (ElevenLabs or CapCut). Total narration ≈ 400 words ≈ 2:40 at a
calm pace, leaving a short breath at the end — lands right on 2:45.

**Pacing rule:** read calmly, ~150 words/min. Pause ~1s between sections.
**Must-haves:** say "non-diagnostic" at least once; show the app actually running;
end with the live link on screen.

---

## SECTION 1 — The idea (0:00 – 0:22)
**WHAT TO SHOW:** TRACE welcome screen, then the dashboard fading in.
**NARRATION:**
> "This is TRACE — Temporal Reasoning and Analysis for Clinical Exploration.
> Wearables and health apps collect weeks of data, yet when something feels
> wrong, the hardest question is: when did it actually start? Most health AI
> looks at today and guesses a disease. TRACE does the opposite — it finds the
> moment the story changed, and explains it. It is an exploratory, non-diagnostic
> tool, and we built the whole thing with Kiro."

## SECTION 2 — Sign in & personal baseline (0:22 – 0:48)
**WHAT TO SHOW:** quick onboarding (type a name, pick a couple options) → land on
the dashboard → the "BioShadow — Your Baseline" card.
**NARRATION:**
> "You begin with a short profile, saved privately in your browser. TRACE then
> greets you by name — but your profile never touches the analysis. The first
> thing it builds is your personal baseline: what is normal for this specific
> person across sleep, heart-rate variability, resting heart rate, activity and
> temperature. Every reading is later judged against this person's own normal,
> not a population average."

## SECTION 3 — Where it changed — the hero (0:48 – 1:18)
**WHAT TO SHOW:** scroll to "BioTimeMachine — Where It Changed"; point at the
orange change line and the shaded region after it.
**NARRATION:**
> "This is the heart of TRACE. It rewinds the timeline to find the earliest point
> where signals started shifting together. Notice the real insight: the story did
> not begin when symptoms would appear — it began earlier. Around Day minus ten,
> fatigue and sleep start drifting, then heart-rate variability follows, then
> resting heart rate rises, and activity drops. TRACE marks that first
> coordinated shift as where the story changed."

## SECTION 4 — What changed together & what's missing (1:18 – 1:48)
**WHAT TO SHOW:** "ReverseHealth — What Changed Together" (the connected chain),
then "BioMissing — What to Learn Next".
**NARRATION:**
> "Instead of separate alarms, TRACE connects the signals into one chain — this
> moved, then this, then this. It is careful to call this an association to
> investigate, never proof of a cause. Then it does something unusual for health
> AI: it admits what it does not know. Here it flags a missing subjective stress
> reading as the single piece of information that would most reduce its
> uncertainty."

## SECTION 5 — How sure, and what-if (1:48 – 2:14)
**WHAT TO SHOW:** "AI Self-Check" confidence gauge (67%), then "Counterfactual —
What If?" — click a signal so the deviation value animates.
**NARRATION:**
> "Crucially, TRACE checks itself. It weighs the evidence and reports honest
> confidence — here, a strong pattern on complete data, but only sixty-seven
> percent certain. That number is how sure TRACE is of its own reading — not a
> health risk. And it is fully explainable: this what-if shows exactly which
> signals drove the result, so TRACE is never a black box."

## SECTION 6 — Paths + real data + Kiro (2:14 – 2:45)
**WHAT TO SHOW:** "HealthFork" three trajectories → switch the source toggle to
Real Wearable Data (f16) → the ML Physiological Anomaly card → a glance at the
`.kiro/` specs/steering → dashboard with the live URL visible.
**NARRATION:**
> "Finally, TRACE explores alternative paths — recover, hold, or drift — as
> scenarios to think about, not predictions. And it is not just a demo: switch to
> real PhysioNet wearable data and TRACE detects the change around minute
> thirteen, where a trained model, tested on a participant it never saw, scores
> how unusual each moment looks. We built every layer spec-driven in Kiro, with
> steering docs enforcing our non-diagnostic safety rules. TRACE — find where the
> story changed. It's live; the link is below."

---

## On-screen captions (optional, overlay per section)
1. TRACE · Find where the story changed
2. Personal baseline · your normal, not an average
3. Where it changed · earliest coordinated shift (~Day −10)
4. Signals connected · and the key missing evidence
5. Honest confidence · fully explainable (not a black box)
6. Real PhysioNet data · trained model · built with Kiro

## Accuracy guardrails (say what's on screen)
- Change point shows **Day −10**; onset chain **fatigue → sleep → HRV → resting HR → activity**.
- Confidence shows **67%**. Real change at **minute 13**. Model trained on **35**, held out **f16**.
- Keep the word **non-diagnostic** audible; never say predict/diagnose/risk.

## Timing cheat-sheet
| Section | In | Out | Len |
|---|---|---|---|
| 1 Idea | 0:00 | 0:22 | 22s |
| 2 Baseline | 0:22 | 0:48 | 26s |
| 3 Where it changed | 0:48 | 1:18 | 30s |
| 4 Connect + missing | 1:18 | 1:48 | 30s |
| 5 Confidence + what-if | 1:48 | 2:14 | 26s |
| 6 Paths + real + Kiro | 2:14 | 2:45 | 31s |

## Export + upload
- 1080p, final length ≤ 2:45. YouTube visibility **Public** (or Unlisted anyone can open).
- Description: Live demo https://pranathivutla30.github.io/Trace/ · GitHub https://github.com/Pranathivutla30/Trace
- Paste the YouTube link into the submission form.
