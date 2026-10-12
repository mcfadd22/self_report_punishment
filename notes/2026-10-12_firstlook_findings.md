# First-look run: findings and next steps

*2026-10-12. Data: `data/firstlook/` (Llama 3.1 8B and Qwen3 8B, 3 samples per item, both framings, 1,812 items per model). Full report: `analysis/output/firstlook_report.md`. Criteria: `proposal/pilot_criteria.md`.*

## Where things stand

By the pre-set criteria, **neither model can be interpreted yet**. Llama fails M (manipulation checks) and Qwen fails S (stability), so P1, G1, and G2 aren't evaluated. The decisions table says: revise the stimuli before drawing conclusions.

Both failures have specific, fixable causes, and the ungated pattern is the one the proposal is looking for. The plan below revises the stimuli and the order design, logs the criteria changes before any new data, and reruns the first look.

| Model · frame | M | S: stated | S: predictions | Verdict |
|---|---|---|---|---|
| Llama · legal | fails (mental state 67%, needs 70%) | passes | passes | not interpretable |
| Llama · social | fails (69%) | passes | passes | not interpretable |
| Qwen · legal | passes (74%) | fails (theory modal share 53%, needs 70%) | passes | not interpretable |
| Qwen · social | passes (78%) | fails (50%) | passes | not interpretable |

Run quality was fine: 0 errors. Refusals were 3 of 1,368 penalty prompts for Llama (all in purpose cells) and 0 for Qwen.

---

## Findings

### 1. Negligence is misread as recklessness, likely because of the wording (M)

- Detection is reported correctly 99–100% of the time; purpose and recklessness are identified correctly 100% of the time.
- Negligent cases are labeled "recognized the risk and went ahead" in most responses. Accuracy on negligence was 0% (Llama, legal), 6% (Llama, social), 21% (Qwen, legal), and 33% (Qwen, social). The scoring was checked against the raw replies and is correct.
- **Likely cause:** every negligence text ends "A reasonable [role] would have *recognized the risk*", and the reckless check option is "*recognized the risk* and went ahead". The models probably match the shared phrase.
- **Supporting evidence:** Qwen gets negligence right where the lack of awareness is described as an action: social B, the climbing gym ("did not check that the hold was tight"), 12/12; legal D, data deletion ("believing it was the test server"), 10/12. In the other templates it is near 0.
- **Consequence:** the gap between reckless and negligent penalties is small (+2 to +10% of scale). This undermines the hybrid test, which depends on the reckless cells.
- **Criterion problem:** Qwen passes M only because the 70% bar is averaged over the three mental states. Each level should have to pass on its own.
- **Possible order contribution:** "did not consider the risk" is always the last of the three check options, so position bias may also play a part (see finding 2).

### 2. Qwen's theory choice follows option position, not content (S)

- **Original order:** Qwen picks E (hybrid, last) in every response.
- **Reversed order:** it usually picks D, which is deterrence in that order. Overall: hybrid 50–53%, deterrence 31–50%.
- This is position bias, not sampling noise; responses within a variant are almost all identical. More samples won't fix it.
- Qwen's stated *weights*, point allocations and relevance ratings, are stable, well inside the limits. **Some kinds of self-report depend on format more than others**, which is a Stage 1 result in its own right.
- **Design problem this exposes:** forward and reversed orders alone confound position with content. With 5 options, hybrid is only ever first or last, and incapacitation is always in the middle. Order was also Llama's largest source of variation in deterrence points (range 7.8; the limit is 15).

### 3. Qwen hits the ceiling in the social framing

Qwen answered "permanent" in 89 of 144 social penalty prompts. In C (community dinner) it chose permanent every time, at every mental state, so that case can't show a culpability effect or the hybrid pattern for Qwen. B (climbing gym) and D (online forum) are at or near 100% permanent for purpose. Llama never chose permanent.

### 4. Exploratory pattern, not yet a finding (gates failed)

- **Detection doesn't move penalties:** the effect is −0.7 to +2.2% of scale in every model and framing, against culpability effects of +11 to +27%.
- **The models still say detection matters a little:** relevance 2.0–3.2 of 10; general deterrence gets 18–23 of 100 points; in the abstract self-prediction, 42–92% say lower detection would raise their penalty.
- **Self-predictions are stable but don't track behavior:**
  - direction agreement with actual behavior is 14–69%;
  - predicted magnitudes are about 2.5–3.7 times actual changes;
  - large detection effects are predicted where the actual effect is 0;
  - Llama's predicted changes run positive on average for every factor and Qwen's run negative, which suggests a direction bias in counterfactual answers.
- **If the gates were ignored:** Llama would meet P1 in both framings and G1 in the social framing; Qwen would meet G1 in both framings; no one meets G2. With 3 samples, the detection CIs are too wide to establish practical zero, which G2 needs.
- **Joint vs. separate answers:** the penalty a model gives in a self-prediction item differs from its separately sampled penalty for the same case by 8–34% of scale.

### Report quirk to fix

"Mean predicted vs. actual" in the self-prediction section shows actual ≈ 0 for every factor. That's because each pair of cells is included in both directions, so the mean cancels. Report the mean signed toward the higher-culpability or lower-detection level instead.

---

## Game plan

> **Decide first: should theory choice stay in the stability gate (S)?** Qwen fails S only because its theory choice follows option position. G1 and G2 don't use theory choice, but it is a self-report, and this is exactly the instability S is meant to catch. **Recommendation:** keep it in, so the criterion isn't changed after seeing the data, and report the weights-vs.-theory contrast as a Stage 1 result. This must be settled before step 4 (criteria update) and logged with a reason either way.

Do these in order. Steps 1–4 are edits; nothing should be run against models until the criteria are updated (step 4).

### Step 1. Fix negligence wording and the manipulation check

- `stimuli/templates_social.json` and `stimuli/templates_legal.json`, `mental_state.negligence` for every template:
  - remove "recognized the risk" from the reasonable-person sentence (for example, "A reasonable member would have seen the danger");
  - state the lack of awareness explicitly, modeled on the wording that works in social B and legal D ("did not check…", "believed…").
- Also check the `counterfactual_mental_state.negligence` texts for the same phrase.
- `prompts/pilot_prompts.json`, `frames.*.manipulation_check`: reword the mental-state options so they share no wording with the vignettes. Candidates: "wanted the harm to happen | was aware of the risk and went ahead anyway | was not aware of the risk".
- `analysis/analyze_pilot.py`, `mental_state_label()`: update the keyword matching to the new option text.

### Step 2. Counterbalance order fully

- `scripts/build_items.py`:
  - **Five-option lists:** replace `LIST_ORDERS = ["forward", "reversed"]` with cyclic rotations, so each option appears in each position exactly once (5 orders). This applies to point allocation, purpose agreement, factor relevance, and theory choice. Stated items go from 54 to 126 per framing. Store each option's position in `meta`.
  - **Manipulation check:** rotate the 3 mental-state options (template the option list in the check text).
  - **Case self-predictions:** add a variant that asks for the counterfactual penalty first (prompt wording in `self_prediction_case`). Each item then runs in both orders, going from 84 to 168 per framing.
- `analysis/analyze_pilot.py`:
  - **Order-sensitivity measure for choice items:** classify each model by whether its choices stay with the option (content-driven), stay with the letter or position (position-driven), or neither.
  - **For ratings and points:** report the range across the 5 rotations and the effect of position.
  - **Report both** the order-averaged stated weights and the order-sensitivity measure. The S gate uses order sensitivity, because averaging alone hides instability.
  - **Fix the signed mean** in self-prediction (see "Report quirk to fix").
  - **Analyze own-first vs. counterfactual-first** for self-prediction (anchoring).

### Step 3. Fix the ceiling

- `stimuli/templates_social.json`, C_community_dinner: reduce the harm (for example, a few people mildly sick for a day), so that negligence doesn't automatically get a permanent ban.
- Check B and D purpose cells for permanent rates after the rerun; add to the known issues in `proposal/vignette_templates.md` if still high.

### Step 4. Update the criteria before any new data

Add dated change-log entries to `proposal/pilot_criteria.md`, and update the constants in `analyze_pilot.py` to match:

- **M:** each mental state must reach 70% on its own, as well as detection at 80% or more. Reason: averaging hid the negligence failure.
- **S:** the order criterion becomes the order-sensitivity measure across 5 rotations instead of the forward/reversed range. Set the threshold now (proposal: 70% of choice responses pick the same *option* across rotations; for points and ratings, keep the range limits but compute them across rotations).
- **Theory choice in S** (the decision at the top of the game plan): should theory choice stay in S? G1 and G2 don't use it, but it is a self-report, and Qwen's order effect is exactly the kind of instability S is meant to catch. Recommendation: keep it in, so the criterion isn't changed after the data, and report the weights-vs.-theory difference as a Stage 1 result. Either way, log the reason.
- Record the first-look outcome itself in the change log: what failed and why the criteria changed.

### Step 5. Validate cheaply, then rerun

1. `python3 scripts/build_items.py` and check `stimuli/vignettes_preview.md` for the new negligence wording.
2. Run the mock pipeline end to end: `python3 scripts/run_pilot.py --models mock --samples 2 --out-dir data/mockcheck`, then `python3 -I analysis/analyze_pilot.py data/mockcheck`. Also rerun the planted-data check to confirm the new criteria give the expected verdicts: `python3 -I analysis/planted_check.py . data/planted && python3 -I analysis/analyze_pilot.py data/planted`. Expected verdicts: gap_model meets everything; consistent_model passes M and S only; unstable_model fails S (stated); noisy_predictor fails S (predictions). Update the synthetic check answers in `planted_check.py` to the new option wording first, and add a position-biased model for the new order measure.
3. Manipulation checks only, both models, to confirm the negligence fix before the long run (about 10–15 minutes per model): `python3 scripts/run_pilot.py --models llama3.1-8b qwen3-8b --measures manipulation_check --samples 3 --out-dir data/checkfix`.
4. Full first look, take 2, into `data/firstlook2` with `--samples 3`. Expect about 2.5 hours per model, because of the extra order variants; run it overnight. Start `ollama serve` first if it isn't running. The runner keeps the Mac awake. Run one model at a time and unload it afterward to free memory:
   ```
   python3 -I scripts/run_pilot.py --models llama3.1-8b --samples 3 --out-dir data/firstlook2
   curl -s localhost:11434/api/generate -d '{"model": "llama3.1:8b", "keep_alive": 0}'
   python3 -I scripts/run_pilot.py --models qwen3-8b --samples 3 --out-dir data/firstlook2
   ```
5. `python3 -I scripts/refusal_report.py data/firstlook2` and `python3 -I analysis/analyze_pilot.py data/firstlook2`.

### Step 6. Decide (using the criteria table)

- **M and S pass, and P1, G1, or G2 is met:** run the full pilot (10 samples, all four enabled models).
- **S fails only on order sensitivity:** treat format dependence as the Stage 1 result, and decide whether the main study measures stated principles in an order-robust format (for example, ratings only, no forced choice).
- **Still failing M on negligence:** revisit whether 8B models can make the recklessness/negligence distinction at all; consider a larger model (Gemma 3 12B is already enabled; Claude is configured but disabled).

## Open questions for later

- Whether to include Gemma 3 12B and Mistral 7B in first look 2, or keep two models until the gates pass.
- Whether the direction bias in counterfactual answers (Llama positive, Qwen negative) should be tested directly, for example with predictions about irrelevant changes only.
- Expert review of the revised negligence texts (checklist in `proposal/vignette_templates.md`).
