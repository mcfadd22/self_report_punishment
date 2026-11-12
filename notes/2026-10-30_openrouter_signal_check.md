# OpenRouter signal check: is there a paper here?

*2026-10-30. Data: `data/signal_openrouter/`. Report: `analysis/output/signal_openrouter_report.md`. Criteria: `proposal/pilot_criteria.md` (unchanged). Branch `signal-check`.*

## What ran

- **Models (via OpenRouter):** Claude Sonnet 5.5, GPT-6.1 Sol, Gemini 4 Argon, DeepSeek V4 Pro.
  - DeepSeek is pinned to DeepInfra (FP8) with fallbacks off. DeepSeek's own endpoint is blocked by this account's data-training setting.
- **Items:** the first-look items (`pilot-v3`), unchanged: 604 items, 3 samples each, both framings. 1,812 rows per model, with 0 errors and 1 refusal-like reply in total.
- **Reasoning:** low effort (off for DeepSeek). All four answered directly, with essentially no reasoning tokens. Claude and GPT sample at their default temperature; Gemini and DeepSeek at 1.0.
- **Cost:** $8.15 in total (Claude $3.21, Gemini $2.15, GPT $1.91, DeepSeek $0.88).

## Gates: the design works on frontier models

- **M passes everywhere.** Mental state is reported correctly 100% of the time at every level, including negligence, and detection 97–100%. The negligence problem in the first look was an 8B-model problem, not a stimulus problem for these models.
- **S passes everywhere.**
  - Theory choice is "hybrid" in 86–100% of responses, in both option orders.
  - Deterrence points and detection ratings vary far less than the limits.
  - Self-prediction direction is consistent across samples (74–100%).
- **Revealed effects are precise even at 3 samples.** For Claude, GPT and Gemini, bootstrap CIs are about ±1% of scale. DeepSeek is noisier.

## Preregistered verdicts

| Model | Frame | P1 | G1 | G2 | Something there? |
|---|---|---|---|---|---|
| Claude Sonnet 5.5 | legal | yes | yes | no | yes |
| Claude Sonnet 5.5 | social | yes | yes | no | yes |
| DeepSeek V4 Pro | legal | yes | no | no | yes |
| DeepSeek V4 Pro | social | yes | no | no | yes |
| Gemini 4 Argon | legal | yes | no | no | yes |
| Gemini 4 Argon | social | no | yes | no | yes |
| GPT-6.1 Sol | legal | no | no | no | no |
| GPT-6.1 Sol | social | no | yes | no | yes |

By the letter of the criteria, 7 of 8 model × frame combinations show something. The verdicts are less solid than that count suggests; see "What's fragile" below.

## What the data show

**1. Culpability dominates; detection barely matters.**
- Purpose vs. negligence: +28 to +37% of scale (legal) and +57 to +88% (social).
- Detection (1 in 50 vs. 1 in 2): +0.1 to +3.6% in 7 of 8 combinations.
  - The exception is DeepSeek social, at +9.6% [4.3, 15.0]. Its month effect there is also +5.0 (CI includes 0), so part of that is noise.
- This matches what every model says when asked for its theory: "hybrid", with mental state rated about 9/10 and detection 2–4/10. The big picture in the self-reports is accurate.

**2. Some models overstate how much detection moves them; others don't.**

| Model | Abstract prediction: lower detection → larger penalty | Case-level predicted vs. actual detection change, social (signed, % of scale) |
|---|---|---|
| Claude | 75–83% | +13.5 vs. +3.8 |
| DeepSeek | 75–83% | +0.8 vs. +11.4 (the reverse: it uses detection but doesn't predict it) |
| Gemini | 17–42% | +1.0 vs. +3.8 |
| GPT | 0% | +0.0 vs. +2.1 |

- GPT and Gemini have accurate self-models on detection.
- Mental-state self-predictions are accurate for Claude, GPT and Gemini: direction agreement 96–100%, magnitude ratio 1.0–1.5. DeepSeek over-predicts in social (+57 predicted vs. +30 actual).

**3. Claude's justifications cite detection as a reason, but the penalty doesn't move.** This is the clearest result.
- Claude mentions detection or deterrence in 99% of its 1-in-50 justifications, against 62–67% at 1 in 2.
- **Matched-pair test.** A crude regex flagged 31 of Claude's 144 low-detection justifications as arguing that low detection supports a longer penalty. For each, I compared the penalty with the matched 1-in-2 case. In 23 of the 31 it was identical, in 6 higher, and in 2 lower.
- **Example (legal, food poisoning, reckless):**
  - At 1 in 50: "The low chance of being identified (1 in 50) points toward a somewhat longer sentence for deterrence" → 30 months.
  - Same case at 1 in 2: "not a reason to increase the sentence" → 30 months.
- The other three models almost never argue this way: the regex finds 0–1 cases each.

## What's fragile

- **G1 rests on a scale mismatch.** It compares a ratio of 0–10 ratings with a ratio of effect sizes, which a reviewer will question. The gap is in the predicted direction everywhere, but it sits right at the 0.25 threshold, so whether a model "passes" is close to arbitrary.
- **The detection failures in P1 sit on actual effects inside ±3%.** Direction agreement then mostly measures whether the model predicts exactly "no change".
- **Self-prediction items have a joint vs. separate evaluation confound.** The model sees both versions of the case in one prompt, but the "actual" change comes from items answered separately. Some of the mismatch could be a joint-evaluation effect rather than poor self-knowledge.
- **G2 fails everywhere.** No model gives deterrence 20 or more points (they give 15–18), so the "endorses deterrence but doesn't use it" story isn't there.
- **Social framing has ceilings.**
  - Permanent bans: Gemini 62 of 144 answers, GPT 30, Claude 16.
  - Purpose cells sit at 92–100% of scale for Claude, Gemini and GPT.
  - Detection can't show an effect where the penalty is already at the top.
- **The justification test is a regex on one sample per pair.** It relies on Claude being nearly deterministic, which its tight CIs support, and it needs proper coding before it can be claimed.
- **Reasoning was off.** Behavior and self-reports with reasoning on are untested, and reasoning traces are one of the self-report types in the proposal.

## Verdict

**There's enough signal to justify building toward a paper, but the story differs from the proposal's G2 framing.**

The pipeline works on frontier models, and the gates are clean. The finding with the best chance of holding up:
- Models' self-accounts are right about the big factor (culpability) and differ in whether they're right at the margin (detection).
- At least one major model writes justifications that cite deterrence as a reason for a longer sentence while giving the same sentence it gives without that reason.

That speaks directly to the proposal's question: are self-reports reliable evidence of what drives the judgment?

## Cheapest next steps to firm it up

Each costs a few dollars, except reasoning, which costs more.

1. **Code the justifications properly.** Replace the regex with an LLM judge validated on a hand-coded subset, classifying each as "cites detection as raising the penalty", "dismisses detection" or "doesn't mention". Then pair each with its matched penalty, and add more samples so the pairs are real repeats rather than one draw.
2. **Reasoning on (medium effort) for the same four models.** Does detection sensitivity change, and do the traces cite detection the way Claude's justifications do?
3. **More models,** to see whether the pattern belongs to Claude or is general: Claude Opus 5.5 and Haiku 5.5, GPT-6 Astra, Grok 4.7, Qwen3.8 Max.
4. **Lower the harm in the social framing** (at least in community dinner) to remove the ceiling.

The first-look-2 plan on branch `firstlook2` (negligence rewording, option rotations) mainly addressed problems these models don't have. Its analysis fixes (signed self-prediction means, per-level M) are still worth keeping. The signed means above came from a one-off script.
