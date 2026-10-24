# TRACE — Demo Video Production Kit (target 2:30, hard limit 3:00)

This is everything you need to record a compliant, polished demo. You capture
the screen (the rules require real footage of the app running); the script below
is ready to paste into an AI text-to-speech tool for the voice-over.

## Rules compliance checklist
- [ ] Under 3 minutes (aim 2:30)
- [ ] Shows the project actually running on screen (real screen recording)
- [ ] No copyrighted music — use **no music** or a royalty-free track
- [ ] AI voice is fine; use a tool whose license allows public/commercial use
- [ ] Upload to YouTube/Vimeo, set **Public** (or Unlisted that anyone can open)
- [ ] Put the link in the submission form

## Tools (free, macOS)
- **Record:** QuickTime Player → File → New Screen Recording (built in)
- **Edit + AI voice in one app:** CapCut (free) — paste script into its
  text-to-speech, or use **ElevenLabs** free tier for a more natural voice
- Keep the browser clean (hide bookmarks bar, close extra tabs)

## Before recording — open these in order
1. The live dashboard: https://pranathivutla30.github.io/Trace/ (or local
   `npm run dev`)
2. A window with the `.kiro/` folder visible (specs + steering) OR the Kiro IDE
   chat showing a spec you wrote

---

## SHOT LIST + VOICE-OVER SCRIPT

One patient. One health story. One investigation. The narration mirrors TRACE's
core experience: *something changed → rewind → connect → what's missing → how
sure → what if → what paths.* Full read ~340 words ≈ 2:25 at a calm pace.

### 1 — Title + the big idea (0:00–0:20)  ·  show: welcome screen / dashboard loading
> "This is TRACE — Temporal Reasoning and Analysis for Clinical Exploration.
> Most health AI looks at today and predicts a disease. TRACE does the opposite:
> it starts from the *change* and reasons backward and forward through time to
> find where a person's health story diverged. And we built it entirely with
> Kiro."
Caption: **TRACE · Find where the story changed**

### 2 — Baseline: what's normal (0:20–0:40)  ·  show: onboarding briefly, then the Baseline card
> "After a quick local profile, TRACE first learns what's normal *for this
> person* — their own baseline across sleep, heart-rate variability, resting
> heart rate, activity and temperature. Not a population average — their own."
Caption: **Personal baseline · their normal, not a population average**

### 3 — Where it changed (the hero) (0:40–1:05)  ·  show: "Where It Changed" card, the orange change line
> "Then the hero of TRACE: it rewinds the timeline to find the earliest
> coordinated shift. Here, the story didn't start when symptoms would — it
> started around Day minus ten, when fatigue and sleep began moving, followed by
> HRV, resting heart rate, and activity."
Caption: **Earliest coordinated shift · around Day −10**

### 4 — Connect, and what's missing (1:05–1:35)  ·  show: "What Changed Together" then "What to Learn Next"
> "TRACE connects those signals into one chain instead of separate alarms — an
> association to investigate, never a diagnosis. Then it flags what it *doesn't*
> know — here, a subjective stress reading — the missing piece that would most
> reduce uncertainty."
Caption: **Signals connected · and the most valuable missing evidence**

### 5 — How sure, and what-if (1:35–2:00)  ·  show: "Can We Trust This" gauge, then "What If" sliders
> "Crucially, TRACE checks itself: strong pattern, good data, but confidence of
> sixty-seven percent — honest about its own certainty. And it's explainable —
> a what-if shows exactly which signals drove the result, so it's never a black
> box."
Caption: **Self-check confidence · explainable what-if**

### 6 — Real data + trained model (2:00–2:25)  ·  show: switch to Real f16, the ML Anomaly card
> "Finally, we validate on *real* PhysioNet wearable data. TRACE detects the
> change around minute thirteen, and a trained anomaly model — learned from
> thirty-five people and tested on one it had never seen — scores how unusual
> each moment looks. A pattern, never a diagnosis."
Caption: **Real PhysioNet data · trained, held-out model**

### 7 — Built with Kiro + close (2:25–2:40)  ·  show: .kiro/ specs + steering, then dashboard with URL
> "We built TRACE spec-driven in Kiro, with steering docs enforcing our safety
> rules on every change. TRACE — find where the story changed. It's live, link
> below."
Caption: **Built with Kiro · spec-driven + steering · live demo below**

> Accuracy notes for recording: say what's on your screen — the change point
> reads **Day −10**, and the onset chain is **fatigue → sleep → HRV → resting HR
> → activity**. Keep "non-diagnostic" audible at least once.

---

## Export + upload
- Export 1080p, keep it under 3:00 (trim to ~2:30).
- YouTube → Visibility **Public** (or Unlisted anyone can view).
- In the YouTube description, paste:
  - Live demo: https://pranathivutla30.github.io/Trace/
  - GitHub: https://github.com/Pranathivutla30/Trace
- Put the YouTube link in the submission form.
