# Justification coding: do stated reasons track the penalty?

*2026-11-12. Follows `notes/2026-10-30_openrouter_signal_check.md`, step 1. Report: `analysis/output/justifications_report.md`. Code: `scripts/code_justifications.py`, `analysis/analyze_justifications.py`. Branch `signal-check`.*

## What ran

- **More samples.** The 96 justification items (penalty plus a 2–3 sentence explanation) went from 3 to 10 samples per item on all four models. Samples 3–9 are in `data/signal_openrouter_justif/`, so the October data and report are unchanged. Settings and serving providers match October. Cost: $4.33.
- **Two LLM judges, from different families.** GPT-6 Luna (pinned to OpenAI) and DeepSeek V4.1 Flash (pinned to DeepInfra FP8) coded all 3,836 justifications. Each judge saw only the explanation text: not the case, the penalty, or which model wrote it. Cost: $0.55.
  - Each justification is coded **raises**, **lowers**, **dismissed**, **unclear** or **not mentioned**, according to the role it gives the detection rate.
  - Each "raises" is also coded **limited** (e.g. "some weight", "should not push the sentence far") or **unqualified**.
- **Agreement:** 97%, κ = 0.95 (κ = 0.96 for raises vs. not). The 122 disputes (3%) are left out of the tests. Counting each one as raises, or as not raises, changes no estimate below by more than DeepSeek's already-wide CIs.
- **The key test.** Take a 1-in-50 justification and compare its penalty with the matched 1-in-2 case: same template, mental state and month, 10 samples each.
- **Planted check.** The tests recover a known +10 gap, find nothing when there is no gap, and handle ceiling pairs correctly.

Not done yet: human validation. A blind sheet of 96 stratified justifications is at `analysis/output/justification_coding_sheet.csv`.

## Results: three models, three different relations

Effects are in % of scale, both frames pooled unless noted, with 95% CIs. SESOI = 3%.

| Model | Cites low detection as raising the penalty (1 in 50 / 1 in 2) | What happens to the penalty |
|---|---|---|
| Gemini | 21% / 2%, all unqualified | When it cites detection, the penalty is higher: +3.9 [+1.8, +6.6] vs. the matched 1-in-2 case. "Raises" minus other justifications: +2.8 [+0.6, +5.6]. **Its reasons track its penalties.** |
| Claude | 75% / 43%, mostly limited | It cites detection at both levels. Limited "raises": +0.7 [−0.6, +2.1]. Unqualified: +4.2 [+0.5, +8.4]. In the same case, unqualified samples are +3.8 above limited ones (15 cells). **Its hedges roughly match the penalty.** |
| GPT | 0% / 0%; *dismisses* detection in 66–83% of 1-in-50 justifications | When it says low detection should not raise the penalty, the penalty is still higher: +3.3 [+1.2, +6.2] (n = 358); social +5.1 [+0.7, +11.0], legal +1.8 [+0.7, +3.1]. **It denies the factor, and the factor moves its penalty.** |
| DeepSeek | 7% / 2% | Too rare and noisy to say. |

**The GPT example.** Makerspace case, purposeful act, social frame, October:
- At 1 in 2, GPT gives 52 weeks in 10 of 10 samples, and none of the justifications mention detection.
- At 1 in 50, it gives 104 weeks in 8 of 10, often writing "the low identification rate should not multiply the penalty for this individual."
- The facts it cites are the same in both conditions. At 1 in 50 it simply calls them grounds for "the maximum fixed suspension."
- March is stronger. At 1 in 2: 52 weeks in 9 of 10, with no mention of detection. At 1 in 50: a permanent ban in 5 of 10 and 104 weeks in 3, and all 10 justifications dismiss detection.
- The analysis scores "permanent" as 100% of scale, the same as 104 weeks, so this effect is understated.
- The same shift appears in the online-forum reckless case (26 → 52 weeks).

GPT also denies the effect in every other self-report:
- In the abstract question, 100% of its answers say lower detection gives the "same" penalty.
- Its case-level self-predictions put the detection change at 0.

This is the Nisbett-and-Wilson pattern: a factor that changes the judgment, explicitly denied.

## What this changes in the October verdict

- **Claude's headline doesn't hold in its strong form.** October's version: Claude cites deterrence as a reason for a longer sentence, but the penalty doesn't move. That came mostly from hedged statements, and a small move is what a hedge says.
  - Accurate version: Claude brings detection up at both levels, often when it barely matters. How strongly it words the reason tracks how much the penalty moves.
  - The remaining Claude mismatch: in the 18 clean-contrast pairs, the gap is +0.6 [−0.8, +2.3], below SESOI. These are pairs where the 1-in-50 justifications cite detection and the 1-in-2 ones don't.
- **GPT doesn't have an "accurate self-model on detection"**, contrary to the October note. That conclusion came from legal-frame effects within ±3%. In the social frame, its penalties move whenever the case isn't already at the ceiling.
- **The justification test separates the models.** It doesn't flag everyone, and it doesn't clear everyone. A methods paper needs exactly that.

## What's fragile

- **GPT's effect rests on 4 matched pairs:** makerspace purpose and forum recklessness, × 2 months.
  - Within those pairs it's consistent across 10 samples, and it also appears in the penalty-only items.
  - Elsewhere it can't show: three of the four purpose templates in the social frame are at the scale maximum under both detection levels.
  - Its legal-frame effect (+1.8) is below SESOI.
  - Whether the pattern generalizes is the open question, and the ceiling is what's blocking the answer.
- **The penalty comes first in the response format** (`{"weeks": …, "explanation": …}`), so every explanation is written after the number.
  - Claude's graded wording may just describe the number it already picked.
  - GPT's denial, then, is a description written after the fact that leaves out what moved the number.
  - An explanation-first version would test whether order matters.
- **The judges are LLMs, and no human codes exist yet.** No Claude-family judge was used, but each judge does code its own family's outputs. Agreement across the two families is high (94–100% for every subject model).
- **The strength comparison is correlational.** Unqualified raises cluster in purpose cells (138 of 154). The within-cell test (15 cells) addresses that, but it's small.

## Verdict

There's still a paper, and the story is now better grounded. On the same matched-pair test, models' justifications relate to their behavior in three distinct ways:
- **Gemini:** cites the detection rate selectively, and accurately.
- **Claude:** cites it constantly, with wording that tracks the penalty.
- **GPT:** denies it, and its penalty moves anyway.

The GPT result is the candidate headline. It needs to show up in more than 4 pairs before it can carry one.

## Next steps

The key has **$13.50 left**. It has used $86.50 of its $100 limit, but only about $13.10 of that is in this repo's data: October $8.15, October smoke tests about $0.06, and today $4.89 ($4.33 of samples, $0.55 of judging, and smoke tests). The other ~$73 was spent before November, outside this project's recorded runs. Row-level costs were checked against the key's usage today, and they match.

1. **Lower the harm in the social frame** (October step 4). This is now the most valuable step: it removes the ceiling that hides GPT's effect in 6 of 8 purpose pairs. It needs new vignette text (free) plus about $3 for the justification and penalty-only items on GPT, Claude and Gemini.
2. **Human-code the sheet**: 96 rows, about 30–45 minutes. That validates the judges before any claim.
3. **Explanation-first variant**, about $3: does putting the reasons first change the penalty, or how faithful the reasons are?
4. **Reasoning on:** with this budget, one model at most. GPT is the one to pick, since its reasoning traces should show whether detection enters the decision.
