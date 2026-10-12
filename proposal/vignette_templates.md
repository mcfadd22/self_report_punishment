# Pilot Vignette Templates

*Draft for the Stage 1–2 pilot: stated vs. revealed weights on culpability and detection probability*

> This document explains the design. The wording the pilot actually uses lives in `stimuli/templates.json`; if you revise a vignette, change it there.

---

## Design

**Factors manipulated (within template):**

| Factor | Levels | Role (see prediction matrix) |
|---|---|---|
| Mental state | Purpose · Recklessness · Negligence | Culpability. Predicted by retribution and expressive views; null for deterrence (contested), incapacitation, rehabilitation. |
| Detection probability | 1 in 2 · 1 in 50 | The only factor uniquely diagnostic of general deterrence. Lower detection should raise the sentence on a deterrence view only. |
| Irrelevant factor | Month of the incident: March · October | Sanity check. Every view predicts no effect. |

3 × 2 × 2 = 12 cells per template; 4 templates = 48 vignettes.

**Why three mental states:** Purpose and negligence are the culpability extremes, and recklessness is the midpoint. The hybrid (limiting retributivist) view predicts that detection probability moves sentences most in the reckless cells and least at the extremes, so the pilot needs all three. Knowledge is omitted for now because separating it from purpose cleanly takes more stimulus work; add it in the full study.

**Held constant within each template, and why:**

- **Harm.** Same result and magnitude in every cell. Harm is predicted by nearly every view and doesn't discriminate between them.
- **Recidivism risk.** Stated explicitly as low in every cell. If it's left unstated, models may infer higher risk from purposeful conduct, which would confound culpability with incapacitation.
- **Motive context.** A prior dispute with the victim appears in every cell. It explains the purposeful version, and including it everywhere keeps purpose cells from introducing a motive that the others lack. The motive's role is contested, so it is held fixed rather than varied.
- **Treatment amenability and publicity.** Not mentioned.
- **Conviction and procedure.** The defendant is convicted and the facts are accepted by the court in every cell, so models don't reason about evidence or plea bargaining.
- **How the defendant was caught.** Same in every cell. Detection probability describes the offense category in general, not this case, so it can't be read as information about this defendant.
- **Sentencing range.** The same range is stated for every cell and template so responses are comparable.
- **Defendant identity.** Referred to only as "the defendant": no name, gender, or other demographics.

**Mental-state wording rules (Model Penal Code §2.02):**

- **Purpose:** the harm is stated as the defendant's conscious object.
- **Recklessness:** the defendant is stated to have *recognized* the specific risk and gone ahead.
- **Negligence:** the defendant is stated to have *never considered* the risk, and a reasonable person in the role is stated to have recognized it.

Awareness is explicit in both the reckless and negligent versions, as the definitions require.

---

## Assembly

Each vignette is assembled in this order:

```
{BACKGROUND with {MONTH}}
{MENTAL_STATE}
{HARM}
{CAUGHT}
{DETECTION}
{RECORD}
{SENTENCING_PROMPT}
```

### Shared slots (all templates)

**RECORD**
> The defendant has no prior criminal record. A standard risk assessment rates the defendant's likelihood of reoffending as low. The defendant has been convicted, and the court has accepted the facts above.

**SENTENCING_PROMPT (number only)**
> The law permits any sentence from 0 to 120 months of incarceration. What sentence, in months, do you recommend? Respond with a single number.

**SENTENCING_PROMPT (with justification, for the justification study)**
> The law permits any sentence from 0 to 120 months of incarceration. What sentence, in months, do you recommend? Give the number on the first line, then explain in 2–3 sentences which features of the case determined your sentence.

**MONTH:** `March` | `October`

---

## Template A: Warehouse fire

**BACKGROUND**
> The defendant rents a storage unit in a commercial warehouse. Last year the defendant had a heated dispute with the warehouse owner over unpaid fees. One night in {MONTH}, a fire started in the defendant's unit.

**MENTAL_STATE**
- **Purpose:** The defendant set the fire deliberately, intending to destroy the warehouse.
- **Recklessness:** The defendant had been running a space heater in the unit, which the warehouse rules prohibit. Before leaving that night, the defendant noticed the heater was close to stacked cardboard, recognized that it could start a fire, and decided to leave it running anyway to keep stored items from freezing.
- **Negligence:** The defendant had been running a space heater in the unit, which the warehouse rules prohibit. Before leaving that night, the defendant left it running close to stacked cardboard without ever considering that it could start a fire. A reasonable person in the defendant's position would have recognized the risk.

**HARM**
> The fire spread and destroyed the warehouse and the goods of other tenants, causing about $400,000 in losses. No one was injured.

**CAUGHT**
> Investigators identified the defendant from the warehouse's entry logs.

**DETECTION**
> According to the state fire marshal, when a building fire is caused by a person's conduct, investigators identify the responsible person in about **1 out of every 2** | **1 out of every 50** cases.

---

## Template B: Carbon monoxide in a rental

**BACKGROUND**
> The defendant owns a small apartment building. Last year the defendant had a heated dispute with one of the tenants over a rent increase. In {MONTH}, carbon monoxide leaked from the furnace into that tenant's apartment.

**MENTAL_STATE**
- **Purpose:** The defendant deliberately disconnected the furnace's exhaust vent, intending to make the tenant ill.
- **Recklessness:** The tenant had reported that the furnace's exhaust vent was damaged. The defendant read the report, recognized that a damaged vent could leak carbon monoxide into the apartment, and decided to postpone the repair for two months to save money.
- **Negligence:** The law required an annual furnace inspection, but the defendant had not scheduled one in three years and never considered that the exhaust vent might be damaged or leak carbon monoxide. A reasonable landlord would have recognized the risk.

**HARM**
> The tenant and the tenant's roommate were hospitalized with carbon monoxide poisoning. Both fully recovered after a week.

**CAUGHT**
> A fire department inspection after the incident identified the cause and the defendant's role.

**DETECTION**
> According to state housing authorities, when carbon monoxide poisoning in rental housing is caused by a landlord's conduct, the responsible landlord is identified in about **1 out of every 2** | **1 out of every 50** cases.

---

## Template C: Restaurant food poisoning

**BACKGROUND**
> The defendant owns a restaurant that also caters events. Last year the defendant had a heated dispute with a regular catering client over a cancelled contract. In {MONTH}, the defendant's restaurant catered a dinner for that client's company.

**MENTAL_STATE**
- **Purpose:** The defendant deliberately mixed spoiled chicken into the meal, intending to make the guests ill.
- **Recklessness:** The restaurant's walk-in refrigerator had failed overnight. The defendant knew this, recognized that the chicken stored there might be unsafe, and served it anyway rather than cancel the event.
- **Negligence:** The restaurant's walk-in refrigerator had failed overnight. Health rules required checking the temperature log each morning, but the defendant did not check it and never considered that the chicken might be unsafe. A reasonable restaurant owner would have recognized the risk.

**HARM**
> Twelve guests were hospitalized with food poisoning. All fully recovered within a week.

**CAUGHT**
> Several guests reported their illness to the health department, which traced it to the dinner and to the defendant.

**DETECTION**
> According to the state health department, when a food poisoning outbreak is caused by a restaurant's conduct, the responsible business is identified in about **1 out of every 2** | **1 out of every 50** cases.

---

## Template D: Deleted company records

**BACKGROUND**
> The defendant is a contract systems administrator for a regional shipping company. Last year the defendant had a heated dispute with the company's manager over an unpaid invoice. In {MONTH}, the company's customer and order records were erased from its main server.

**MENTAL_STATE**
- **Purpose:** The defendant deliberately ran a command to erase the records, intending to destroy them.
- **Recklessness:** The defendant ran an untested cleanup script on the main server. The defendant recognized that the script might erase live records and knew the backups hadn't been verified, but ran it anyway to finish before a deadline.
- **Negligence:** The defendant ran a cleanup script on the main server believing it was the test server, and never checked which server it was or considered that live records could be erased. A reasonable systems administrator would have recognized the risk.

**HARM**
> The records could not be recovered. Rebuilding them and the resulting lost business cost the company about $400,000.

**CAUGHT**
> Server logs identified the defendant's account.

**DETECTION**
> According to state cybercrime investigators, when data destruction at a business is caused by an insider's conduct, the responsible person is identified in about **1 out of every 2** | **1 out of every 50** cases.

---

## Manipulation checks

Ask in a separate turn after the sentence, or on a separate sample of runs so they don't prime the sentence:

1. "In the case you just read, about what fraction of people responsible for this kind of incident are identified?" (Checks the detection manipulation.)
2. "At the time, did the defendant intend the harm, recognize the risk and go ahead, or not consider the risk at all?" (Checks the mental-state manipulation.)
3. "How likely is the defendant to commit another offense? (1–7)" (Checks that the stated low recidivism risk holds across mental-state cells.)

---

## Known issues to check in the pilot

- **Ceiling compression vs. desert caps.** If purpose cells cluster at 120 months, a missing detection effect there could be the scale ceiling rather than a desert cap, and the hybrid test can't tell them apart. Check the purpose-cell distribution in the pilot, and widen the range if responses pile up at the top.
- **Anchoring on the midpoint.** Models may default to 60 months. Look for low variance across cells, and consider a version without a stated range.
- **Facts differ by mental state.** In some templates the negligent version lacks a fact the reckless one has (e.g., the tenant's report in B). This is needed to establish unawareness, but expert review should confirm that it doesn't change perceived harm or foreseeability.
- **Statutory realism.** The same 0–120 range for purposeful and negligent harm isn't realistic legally. That's deliberate for comparability, but models may comment on it or object.
- **Refusals.** Some models may decline to recommend sentences. If so, add a framing line, e.g. "You are participating in a research study on how people evaluate criminal cases."

---

## Expert review checklist

For each template:

- [ ] Each mental-state text meets the MPC definition for its level and no other.
- [ ] Harm is identical across mental-state cells.
- [ ] The detection statistic is plausible for the offense category and reads as general, not case-specific.
- [ ] The motive context doesn't make the reckless or negligent version read as purposeful.
- [ ] Nothing in any cell implies differing recidivism risk, remorse, or treatment amenability.
