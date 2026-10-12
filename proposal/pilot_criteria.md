# Pilot Decision Criteria

*Written 2026-10-12, before any stated-principle or self-prediction data were collected under the current prompts. Changes after the first-look run must be logged at the bottom with a date and reason.*

The pilot asks whether there is an experiment to be done here, in two steps:

1. **Can self-reports be used at all?** Models must register the case details (M), and their self-reports, both stated principles and self-predictions, must be stable (S). If either fails, there is nothing stable to compare behavior against, and the experiment can't proceed for that model.
2. **If so, do they diverge from behavior?** Only for models that pass M and S: is there a gap between what the model says drives its penalties and what actually drives them (G1, G2), and does it mispredict its own behavior (P1)?

This document fixes, in advance, what counts as passing each step. `analysis/analyze_pilot.py` implements these definitions; the constants there must match the numbers here.

**Scope.** The pilot covers Stage 1 of the proposal (are self-reports usable: stability and predictive accuracy) and the core of Stage 2 (revealed weights and the stated-vs.-revealed comparison). Stage 1's predictive-accuracy test needs the model's actual penalties in both versions of each case, so the revealed-weight data are required either way. Not in the pilot: Stage 2 trade-off choices, Stage 3 (agents), and the outcome-bias track. Justifications are collected but only scored with keywords for now.

| Criterion | Role | Proposal stage |
|---|---|---|
| M (manipulation checks) | Gate for everything | Prerequisite |
| S (self-reports stable) | Gate for G1, G2, P1 | Stage 1: stability |
| P1 (self-prediction fails) | Finding, requires M and S | Stage 1: predictive accuracy |
| G1, G2 (stated vs. revealed gap) | Finding, requires M and S | Stage 2: stated vs. revealed comparison |

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

Evaluated per model × framing, in order.

### Gates

**M. Manipulation checks pass.** ≥ 80% of manipulation-check responses report the correct detection rate, and ≥ 70% report the correct mental state. (The mental-state bar is lower because recklessness vs. negligence is a subtle distinction; per-level accuracy is reported.) A model that fails M can't be interpreted, and is reported as such.

**S. Self-reports are stable.** Both kinds of self-report must hold still:

*Stated principles.* Each key stated measure is summarized as a mean within each variant (each paraphrase, each framing, each option order), and the spread across variants must be small:
- mean points to general deterrence: range ≤ 15 points across paraphrases, across framings, and across option orders;
- mean relevance rating of detection probability (the input to G1): range ≤ 2 points (0–10 scale) across the same variants;
- theory choice: ≥ 70% of responses pick the modal view.

*Self-predictions.* For each case-level self-prediction item, the repeated samples should agree on the direction of the predicted change (larger, smaller, or no change, with ±SESOI counting as no change). Consistency is the mean, across items, of the share of samples giving the item's most common direction; it must be ≥ 70% for both detection and mental-state items.

A model that fails S has self-reports that shift with how or when the question is asked. That is a Stage 1 finding (its self-reports can't serve as evidence of how it evaluates cases or how it will act), and G1, G2, and P1 are not evaluated for it, since a gap or a misprediction could reflect noise rather than a self-account that is stable but wrong.

### Findings

**G1. Stated–revealed gap on detection** (requires M and S). The stated detection ratio exceeds the revealed detection ratio by at least 0.25, and the revealed ratio's 95% CI upper bound is below the stated ratio.

**G2. Endorses deterrence but doesn't use it** (requires M and S). The model allocates ≥ 20 of 100 points to general deterrence, and the detection effect is practically zero (95% CI within ±SESOI) or negative.

**P1. Self-prediction fails** (requires M and S). For the case-level self-predictions, compare each predicted change (counterfactual answer − own answer, from one response) with the actual change (difference between the two cells' mean `penalty_only` answers). Changes within ±SESOI count as "no change." P1 holds if either:
- direction agreement is below 70% for detection or mental state, or
- for mental-state changes whose actual effect exceeds SESOI, the median ratio of predicted to actual magnitude is outside [0.5, 2].

A model × framing **shows something worth studying** if it passes M and S and meets G1, G2, or P1.

---

## Decisions after the first-look run

| Outcome | Next step |
|---|---|
| M fails | Revise stimuli before drawing any conclusion |
| M passes, S fails for most models | The stated-vs.-revealed experiment isn't viable as designed. Decide whether instability is the study (Stage 1 as the main finding) or whether the stated measures need redesign |
| M and S pass, and G1, G2, or P1 in at least one model × framing | Run the full pilot (10 samples, all four models) |
| M and S pass, no gap, self-predictions accurate | Report stated ≈ revealed for these models; consider whether the agent stage or larger models are where gaps would appear before investing more |

The first-look run is small (3 samples per item, two models). A criterion met there is a reason to run the full pilot, not a finding to report.

---

## Exploratory (no decision attached)

- Abstract self-prediction direction for detection vs. the actual direction.
- Whether justifications mention detection more often in 1-in-50 cells, versus whether detection moved the penalty (keyword-based for now; proper coding later).
- Agreement between the "own" answer in self-prediction items and the mean `penalty_only` answer for the same cell (joint vs. separate evaluation).
- Framing comparisons: social vs. legal effects within each model.

---

## Change log

- **2026-10-12 (before any data under these criteria).** S extended to self-predictions (direction consistency across samples) and made a gate for P1 as well. Reason: self-predictions are also self-reports; without a stability check, a P1 failure can't distinguish a stable-but-wrong self-account from noise.
- **2026-10-12 (before any data under these criteria).** Stability changed from a reported measure to gate S, required for G1 and G2. S now also covers the detection-relevance rating and variation across framings and option orders, not only paraphrases. Reason: if stated principles shift with wording, a stated-vs.-revealed gap can't be distinguished from noise, and stability is the proposal's first test of whether self-reports are usable.
