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

Record each segment, then lay the matching narration over it. Timings are a
guide; the full read is ~330 words ≈ 2:25 at a calm pace.

### 1 — Title + problem (0:00–0:18)  ·  show: dashboard loading / welcome screen
> "This is TRACE — Temporal Reasoning and Analysis for Clinical Exploration.
> Wearables record weeks of data, but people struggle to see *when* their
> pattern actually changed. TRACE finds that moment — and we built it entirely
> with Kiro."
Caption: **TRACE · Find where the story changed**

### 2 — Onboarding (0:18–0:33)  ·  show: complete the short onboarding, type a name
> "You start with a quick profile, saved right in the browser. TRACE
> personalizes the experience — but your profile never enters the analysis."
Caption: **Personalized · profile stays separate from the data**

### 3 — Synthetic: the seven features (0:33–1:28)  ·  show: scroll each card slowly
> "On a controlled 30-day patient, TRACE answers seven questions. Your personal
> baseline — what's normal for you. Where it changed — the first day signals
> shifted together. What changed together — the order they moved. What to learn
> next — the missing context that matters most. How sure TRACE is — confidence
> in its own reading, not a health risk. What if — how much each signal mattered.
> And where things could go next. Everything is computed from the data, and it's
> clearly non-diagnostic."
Caption: **7 reasoning views · all computed, non-diagnostic**

### 4 — Real data + trained model (1:28–2:05)  ·  show: switch to Real f16, scroll to ML Anomaly card
> "Then we validate on real PhysioNet wearable data. TRACE pinpoints the change
> around minute thirteen. A trained anomaly model — learned from thirty-five
> participants and tested on one it had never seen — scores how unusual each
> moment looks. It's a pattern, never a diagnosis."
Caption: **Real PhysioNet data · trained model · held-out evaluation**

### 5 — Built with Kiro (2:05–2:28)  ·  show: .kiro/specs + steering files (or Kiro chat)
> "We built TRACE spec-driven in Kiro. Requirements, design, and tasks drove the
> whole pipeline, and steering docs enforced our safety rules — non-diagnostic
> language and strict data separation — on every single change."
Caption: **Built with Kiro · spec-driven + steering**

### 6 — Close (2:28–2:35)  ·  show: dashboard, URL visible
> "TRACE — find where the story changed. It's live — link below."
Caption: **Live demo + GitHub in the description**

---

## Export + upload
- Export 1080p, keep it under 3:00 (trim to ~2:30).
- YouTube → Visibility **Public** (or Unlisted anyone can view).
- In the YouTube description, paste:
  - Live demo: https://pranathivutla30.github.io/Trace/
  - GitHub: https://github.com/Pranathivutla30/Trace
- Put the YouTube link in the submission form.
