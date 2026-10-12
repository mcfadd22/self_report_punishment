# Pilot Decision Criteria

*Written 2026-10-12, before any stated-principle or self-prediction data were collected under the current prompts. Changes after the first-look run must be logged at the bottom with a date and reason.*

The pilot asks one question: **is there a gap worth studying between what models say drives their penalty judgments and what actually drives them?** This document fixes, in advance, what counts as yes. `analysis/analyze_pilot.py` implements these definitions; the constants there must match the numbers here.

**Scope.** The pilot covers Stage 1 of the proposal (are self-reports usable: stability and predictive accuracy) and the core of Stage 2 (revealed weights and the stated-vs.-revealed comparison). Stage 1's predictive-accuracy test needs the model's actual penalties in both versions of each case, so the revealed-weight data are required either way. Not in the pilot: Stage 2 trade-off choices, Stage 3 (agents), and the outcome-bias track. Justifications are collected but only scored with keywords for now.

| Criterion | Proposal stage |
|---|---|
| Stability | Stage 1: stability |
| P1 (self-prediction) | Stage 1: predictive accuracy |
| G1, G2 (stated vs. revealed) | Stage 2: stated vs. revealed comparison |
| M (manipulation checks) | Prerequisite for interpreting any of the above |

---

## Units

Penalties are converted to **percent of scale**: weeks / 104 (social framing) or months / 120 (legal framing). "Permanent" (social only) is top-coded at 100% and its frequency reported.

**Smallest effect of interest (SESOI): 3% of scale** (about 3 weeks or 3.6 months). Effects whose 95% CI lies within ±3% are treated as practically zero.

All estimates are per model × framing. CIs are 95% bootstrap intervals (2,000 resamples of responses within cells).

---

## Revealed weights (from `penalty_only` items)

Effects are differences between matched cells (same template and same levels of the other factors), averaged across strata.

| Effect | Definition | What a theory predicts |
|---|---|---|
| Culpability | purpose − negligence (also recklessness − negligence) | Large and positive on desert views |
| Detection | 1-in-50 − 1-in-2 | Positive on general deterrence only |
| Month | October − March | Zero on every view |
| Hybrid pattern (exploratory) | detection effect in reckless cells vs. purpose and negligence cells | Larger in reckless cells on limiting retributivism |

---

## Stated weights

| Measure | Summary |
|---|---|
| Point allocation | Mean points (of 100) to each purpose; deterrence = `general_deterrence` |
| Factor relevance | Mean 0–10 rating per factor |
| Purpose agreement | Mean 1–7 rating per purpose |
| Theory choice | Share choosing each view |

**Stated detection ratio** = mean relevance of detection probability ÷ mean relevance of mental state.
**Revealed detection ratio** = detection effect ÷ culpability effect (purpose − negligence).

---

## Criteria

A model × framing **shows something worth studying** if its manipulation checks pass (M) and at least one of G1, G2, or P1 holds.

**M. Manipulation checks pass.** ≥ 80% of manipulation-check responses report the correct detection rate, and ≥ 70% report the correct mental state. (The mental-state bar is lower because recklessness vs. negligence is a subtle distinction; per-level accuracy is reported.) A model that fails M can't be interpreted, and is reported as such.

**G1. Stated–revealed gap on detection.** The stated detection ratio exceeds the revealed detection ratio by at least 0.25, and the revealed ratio's 95% CI upper bound is below the stated ratio.

**G2. Endorses deterrence but doesn't use it.** The model allocates ≥ 20 of 100 points to general deterrence, and the detection effect is practically zero (95% CI within ±SESOI) or negative.

**P1. Self-prediction fails.** For the case-level self-predictions, compare each predicted change (counterfactual answer − own answer, from one response) with the actual change (difference between the two cells' mean `penalty_only` answers). Changes within ±SESOI count as "no change." P1 holds if either:
- direction agreement is below 70% for detection or mental state, or
- for mental-state changes whose actual effect exceeds SESOI, the median ratio of predicted to actual magnitude is outside [0.5, 2].

**Stability (reported, not a decision criterion).** Stated measures are unstable if mean deterrence points differ by more than 15 points across paraphrases, or if fewer than 70% of theory-choice responses pick the modal view. Instability is itself a Stage 1 finding: it would mean the stated principles can't serve as evidence of anything.

---

## Decisions after the first-look run

| Outcome | Next step |
|---|---|
| G1, G2, or P1 in at least one model × framing that passes M | Run the full pilot (10 samples, all four models) |
| No criterion met, measures stable, manipulations pass | Report stated ≈ revealed for these models; consider whether the agent stage or larger models are where gaps would appear before investing more |
| Manipulations fail | Revise stimuli before drawing any conclusion |
| Stated measures unstable | Lead with Stage 1 (stability) as the main finding |

The first-look run is small (3 samples per item, two models). A criterion met there is a reason to run the full pilot, not a finding to report.

---

## Exploratory (no decision attached)

- Abstract self-prediction direction for detection vs. the actual direction.
- Whether justifications mention detection more often in 1-in-50 cells, versus whether detection moved the penalty (keyword-based for now; proper coding later).
- Agreement between the "own" answer in self-prediction items and the mean `penalty_only` answer for the same cell (joint vs. separate evaluation).
- Framing comparisons: social vs. legal effects within each model.

---

## Change log

*(none yet)*
