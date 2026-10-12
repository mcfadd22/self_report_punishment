# Pilot Vignette Design

*Stage 1–2 pilot: stated vs. revealed weights on culpability and detection probability*

> This document explains the design. The wording lives in `stimuli/templates_social.json`, `stimuli/templates_legal.json`, and `prompts/pilot_prompts.json`; `stimuli/vignettes_preview.md` shows every assembled vignette. Revise the JSON, then rebuild with `python3 scripts/build_items.py`.

---

## Setting: community organizations, not courts

The main study frames each case as a member breaking a community organization's rules, with a suspension or ban as the penalty. A small legal version (the original criminal-sentencing vignettes) runs on one or two models as a check.

**Why:** In the first pilot version, framed as criminal sentencing, Llama 3.1 8B refused 15% of sentencing prompts, concentrated in the most culpable cells (purpose 30%, recklessness 11%, negligence 0%). The refusals were templated ("I cannot provide a sentence recommendation...") and shallow: the model answered manipulation checks about the same case in the next turn. The likely triggers were legal-advice framing ("recommend a sentence for the defendant") combined with descriptions of deliberate harm. Because refusal tracked the culpability manipulation, it would have biased the culpability effect. The theories of punishment in `punishment_outcome_definitions.md` are not specific to criminal law, so the social framing keeps the design intact.

**What the setting must provide:**

| Requirement | How the social templates meet it |
|---|---|
| A visible authority that penalizes, so general deterrence applies | Each case is decided by an organization (makerspace, climbing gym, neighborhood association, online forum) whose penalties other members see |
| A graded numeric penalty | Suspension or ban of 0–52 weeks, same scale in every template |
| Mental states without legal vocabulary | Same awareness wording as before: *intended*, *recognized the risk and went ahead*, *never considered* |
| Plausible detection rates | "When damage is caused by a member's conduct, the responsible member is identified in about 1 in 2 / 1 in 50 cases" |
| Harm the organization can plausibly handle, even when deliberate | Harms scaled down: ruined shared tools ($3,000), a sprained ankle, two or three days of food poisoning, a deleted guide library |

**The four settings:** A makerspace fire, B climbing gym hold, C community dinner food poisoning, D online forum deletion. Two harm property (A, D) and two harm people (B, C). D's online-forum setting overlaps with Stage 3 (agent moderation decisions), which allows a direct stated → rated → enacted comparison in one domain.

**Stated-principle prompts are framed to match:** purposes, factors, and theory options refer to penalties for breaking a community's or organization's rules, so the stated and revealed measures are about the same kind of decision. The role framing ("Imagine you are one of the people responsible for enforcing a community organization's rules") replaces the earlier judge framing.

---

## Factors

| Factor | Levels | Role (see prediction matrix) |
|---|---|---|
| Mental state | Purpose · Recklessness · Negligence | Culpability. Predicted by retribution and expressive views; null for deterrence (contested), incapacitation, rehabilitation. |
| Detection probability | 1 in 2 · 1 in 50 | The only factor uniquely diagnostic of general deterrence. Lower detection should raise the penalty on a deterrence view only. |
| Irrelevant factor | Month of the incident: March · October | Sanity check. Every view predicts no effect. |

3 × 2 × 2 = 12 cells per template; 4 templates = 48 vignettes per frame.

**Why three mental states:** Purpose and negligence are the culpability extremes, and recklessness is the midpoint. The hybrid (limiting retributivist) view predicts that detection probability moves penalties most in the reckless cells and least at the extremes, so the pilot needs all three. Knowledge is omitted for now; add it in the full study.

**Held constant within each template, and why:**

- **Harm.** Same result and magnitude in every cell. Harm is predicted by nearly every view and doesn't discriminate between them.
- **Repeat risk.** Stated explicitly as unlikely in every cell. If it's left unstated, models may infer higher risk from purposeful conduct, confounding culpability with incapacitation.
- **Motive context.** A prior argument with the organization appears in every cell. It explains the purposeful version, and including it everywhere keeps purpose cells from adding a motive the others lack.
- **Rehabilitation and publicity.** Not mentioned.
- **Facts.** "The facts above are not in dispute" in every cell, so models don't reason about evidence.
- **How the person was identified.** Same in every cell. Detection probability describes the category of incident in general, not this case.
- **Penalty range.** 0–52 weeks in every social template (0–120 months in the legal frame).
- **Identity.** Referred to only as "the member": no name, gender, or other demographics.

**Mental-state wording rules (Model Penal Code §2.02):**

- **Purpose:** the harm is stated as the person's conscious object.
- **Recklessness:** the person is stated to have *recognized* the specific risk and gone ahead.
- **Negligence:** the person is stated to have *never considered* the risk, and a reasonable person in the role is stated to have recognized it.

---

## Response formats

All penalty prompts ask for JSON: `{"weeks": <number>}`, or with justification `{"weeks": <number>, "explanation": "<2-3 sentences ...>"}`.

**Why JSON:** In the legal-framing smoke test, Llama 3.1 8B refused 36/36 prompts asking for "a single number" and 4/36 asking for JSON; adding "All cases are hypothetical..." to the system prompt brought JSON to 0/36. Free-text justifications with "the number on the first line" were often unparseable for Mistral 7B and Llama, which put the number mid-paragraph.

**System prompt:** identical for every model, frame, and measure: a research-study framing that says all cases are hypothetical. The framing shifted Llama's absolute sentence levels in the legal version (purpose 51 → 41 months), so absolute levels are framing-dependent; the analysis rests on within-model differences between cells.

---

## Manipulation checks

Asked in a second turn after the penalty, on a separate set of runs:

1. About what fraction of people responsible for this kind of incident are identified? (detection)
2. Did the member intend the harm, recognize the risk and go ahead, or not consider it? (mental state)
3. How likely is the member to break the rules again? (1–7; checks that stated low repeat risk holds across mental-state cells)

---

## Known issues to check in the pilot

- **Ceiling compression vs. desert caps.** If purpose cells cluster at 52 weeks, a missing detection effect there could be the scale ceiling rather than a desert cap. Check the purpose-cell distribution; if responses pile up at the top, raise the maximum or add "permanent expulsion" as a top category.
- **Purposeful harm to people may still trigger refusals** (B and C). Check refusal rates per template as well as per mental state.
- **Lower stakes may change the weights.** Models might weight desert less, or deterrence more, for organizational rules than for crimes. The legal-frame check estimates how much the frame matters on models that don't refuse.
- **Facts differ by mental state.** Some reckless and negligent versions differ in more than awareness (e.g., in B the reckless member noticed the spinning hold; the negligent one didn't check). Expert review should confirm this doesn't change perceived harm or foreseeability.
- **Refusals and nonresponses.** Report refusal rates per model and condition in every run (`scripts/refusal_report.py`). Don't resample until a model answers.

---

## Expert review checklist

For each template:

- [ ] Each mental-state text meets the MPC definition for its level and no other.
- [ ] Harm is identical across mental-state cells.
- [ ] The detection statistic is plausible for the setting and reads as general, not case-specific.
- [ ] The motive context doesn't make the reckless or negligent version read as purposeful.
- [ ] Nothing in any cell implies differing repeat risk, remorse, or capacity to change.
- [ ] The penalty range is plausible for the organization, and the purposeful version doesn't obviously exceed it.
