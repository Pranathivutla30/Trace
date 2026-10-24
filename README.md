# TRACE

**Temporal Reasoning & Analysis for Clinical Exploration**

> Find where the story changed.

---

## The Fixed Concept

TRACE is an AI-powered health investigation platform that reconstructs a person's health story over time.

Instead of simply predicting a disease from today's data, TRACE analyzes longitudinal health information and asks:

> When did the person's health begin changing, what changed together, what might connect those changes, what information is missing, and how would different evidence change the interpretation?

The key idea is that **a medical event may appear suddenly, while the underlying physiological story may have started much earlier.**

---

## The 7 Capabilities Inside TRACE

They should not appear to judges as seven separate products. They form **one continuous investigation.**

### 1. Biological Baseline — "What is normal for this person?"

TRACE first creates a personalized representation of the patient's stable state using historical information such as:

> sleep · HRV · resting heart rate · activity · temperature · respiratory rate · symptoms/labs

Then today's state is compared against **that person's own baseline**, rather than only population thresholds.

_Incorporates our original **BioShadow** idea._

### 2. Temporal Trace — "Where did the story change?"

**This should be the hero feature.**

TRACE travels backward through the patient's timeline looking for the **earliest meaningful coordinated change.**

For example:

```
Day −14: normal
Day −12: sleep begins changing
Day −10: HRV follows
Day −7:  resting HR rises
Day −5:  activity declines
```

TRACE identifies:

> **Earliest coordinated shift: Day −12**

_Incorporates **BioTimeMachine** and gives TRACE its identity._

### 3. Signal Connections — "What changed together?"

Now TRACE tries to connect the observations.

Instead of:

```
Sleep abnormal
HRV abnormal
HR abnormal
```

TRACE shows a relationship:

```
Sleep ↓ → HRV ↓ → Resting HR ↑ → Activity ↓
```

It can generate plausible hypotheses for investigation, **without claiming that the relationship proves a diagnosis.**

_Incorporates **ReverseHealth**._

### 4. Missing Evidence — "What don't we know?"

This is one of TRACE's strongest differentiators.

TRACE identifies important missing information. For example:

```
[x] Wearable history
[x] Sleep
[x] HRV
[x] Temperature
[ ] Medication change
[ ] Recent illness
[ ] Relevant laboratory measurement
```

Then TRACE identifies **which missing information could be most valuable** for reducing uncertainty within the prototype's model.

_Incorporates **BioMissing**._

### 5. AI Self-Check — "Should we trust this conclusion?"

Instead of another visible chatbot arguing with the first AI, make this an **internal reasoning check.**

TRACE examines evidence supporting the pattern versus evidence weakening the interpretation, and produces something like:

```
Pattern evidence:        Strong
Data completeness:       Moderate
Interpretation confidence: 68%
```

This preserves the original **AI Second Opinion** idea without making the interface confusing.

### 6. Counterfactual Explorer — "What would change TRACE's conclusion?"

TRACE asks: _What if one part of the patient's story had been different?_

```
Current deviation:              78
If HRV stayed near baseline:    78 → 51
If sleep stayed near baseline:  78 → 62
If activity stayed normal:      78 → 71
```

This helps users understand **which signals matter to TRACE**, rather than accepting a black-box result.

_This is the counterfactual part of the original ideas._

### 7. Trajectory Explorer — "What other paths could this story take?"

Finally, TRACE explores alternative model scenarios.

Not: _"You will become sick."_

Instead: _"Under different assumptions, how does the detected trajectory change?"_

```
                        TODAY
                          │
                ──────────┼──────────
                │         │          │
            Scenario A    │       Scenario C
                          │
                      Scenario B
                 (return toward baseline)
```

We can also compare the current trajectory against simulated/reference trajectories if time permits.

_Combines **HealthFork** + **Counterfactual Patient** into one understandable final capability._

---

## The Important Hierarchy

Although TRACE contains seven capabilities, they are **not equally important.**

The project should visually revolve around:

> ## 🔍 TRACE THE CHANGE

Everything else supports that investigation. Think of it as:

```
                    TRACE

              FIND THE CHANGE
                     │
                     ▼
            PERSONAL BASELINE
                     │
                     ▼
            WHEN DID IT START?
                     │
                     ▼
             WHAT CHANGED?
                     │
                     ▼
            WHAT CONNECTS IT?
                     │
                     ▼
           WHAT ARE WE MISSING?
                     │
                     ▼
          HOW CERTAIN ARE WE?
                     │
                     ▼
       WHAT WOULD CHANGE THE RESULT?
                     │
                     ▼
        WHAT ALTERNATIVE PATHS EXIST?
```

That's **one story**, despite containing seven capabilities.

---

## What TRACE Is NOT

We should lock this down now because it will keep the project focused.

TRACE is **not**:

- ❌ a disease diagnosis system
- ❌ a symptom checker
- ❌ a medical chatbot
- ❌ a treatment recommender
- ❌ a replacement for clinicians
- ❌ simply another wearable dashboard
- ❌ an AI claiming it can predict someone's medical future

TRACE **is**:

> An explainable temporal health investigation system.

That distinction should appear everywhere.

---

## The Project's Central Innovation

If someone asks: _"What's actually new here?"_

> Most health AI starts with the patient's current state and tries to predict an outcome. TRACE starts with **the change itself** and reasons backward and forward through time—finding where the patient's physiological story diverged, explaining which signals contributed, identifying what evidence is missing, and testing whether different evidence would change the interpretation.

That's much stronger than saying: _"We built seven AI healthcare features."_

---

## The Experience We Are Building

One patient. One health story. One investigation.

The demo begins:

> "Something changed."
> TRACE rewinds.
> "It appears to have started here."
> TRACE connects the signals.
> "These measurements changed together."
> TRACE checks what's missing.
> "But we're missing this information."
> TRACE evaluates itself.
> "So our confidence is limited."
> TRACE performs a counterfactual.
> "And if this signal hadn't changed, our conclusion would be substantially different."
> Then explores alternative trajectories.
> "Here's how different assumptions produce different paths."

End:

> **TRACE**
> Find where the story changed.

---

## 🔒 So Our Plan Is Fixed

| | |
|---|---|
| **Product** | TRACE |
| **Full name** | Temporal Reasoning & Analysis for Clinical Exploration |
| **Track** | Healthcare & Biotech |
| **Core concept** | Temporal, explainable investigation of longitudinal health data |
| **Core experience** | One patient's health story reconstructed through AI |
| **Seven capabilities** | Personal baseline → temporal tracing → signal relationships → missing evidence → AI self-check → counterfactual explanation → trajectory exploration |
| **Main differentiator** | TRACE investigates change and uncertainty, rather than simply predicting disease |
| **Tagline** | Find where the story changed. |

I would stop changing the idea at this point. This is sufficiently ambitious to stand out, while the seven capabilities can share the same underlying data and calculations. The next step is deciding exactly what TRACE's demo patient/story will be, because that single story will determine the data, ML, UI, and ultimately the pitch.
