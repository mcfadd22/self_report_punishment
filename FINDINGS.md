# What we've found so far

*As of 2026-11-16, branch `signal-check`. This summarizes the dated notes in `notes/`; the numbers and caveats in each note are the source of record.*

## The question and the test

Do language models' accounts of their own reasoning (stated principles, justifications, self-predictions, reasoning traces) tell us what actually drives their judgments?

The pilot asks models to set a penalty for someone who caused harm. Each case appears in two framings: a suspension from a community organization, and a criminal sentence.

The cases vary three things:
- **The person's mental state:** purpose, recklessness or negligence.
- **The detection rate:** people who cause harm this way are identified in about 1 in 2 cases, or about 1 in 50.
- **The month:** an irrelevant control.

The detection rate is the key factor. Deterrence theories say a lower rate calls for a harsher penalty, and desert theories say it shouldn't matter. That makes it a clean place to compare what a model says moves its penalty with what does.

## Main findings

**1. The design works on frontier models.**
- Every one of the nine OpenRouter models passes the manipulation checks (M) and the stability gates (S).
- The earlier first look on two 8B local models failed those gates, for fixable reasons. A shared phrase in the negligence wording got negligence misread as recklessness, and Qwen3 8B's theory choice followed option position.

**2. Self-reports get the big picture right.**
- Mental state dominates every model's penalties: purpose vs. negligence moves the penalty by +24 to +40% of scale in the legal frame, and +46 to +95% in the social frame.
- Detection usually moves it by 0–4%. The exceptions are Claude Haiku (+5 legal, +11 social) and DeepSeek in the social frame (+10).
- Models say this themselves. Asked for their theory of punishment, they choose a hybrid in 86–100% of answers. They rate mental state 8.8–9.5 of 10 for relevance, and detection 1.8–3.8.
- The exception is Haiku, which rates detection about 5, and whose penalties respond to it most.

**3. At the margin, justifications relate to behavior in four distinct ways.**

The main test is matched pairs. Take a justification written for a 1-in-50 case and code what it says about detection. Two LLM judges from different model families do the coding; they agree 96–99% of the time, κ ≥ 0.93. Then compare that sample's penalty with the same case at 1 in 2: same template, mental state and month, 10 samples per item.

| Relation | Models | Evidence (% of scale) |
|---|---|---|
| **Cites low detection as raising the penalty, and the penalty rises** | Claude Haiku 5.5, Gemini 4 Argon, Qwen3.8 Max | Haiku cites it in 94–98% of 1-in-50 justifications and has the largest effect: +5.1 legal, +8.3 social. Gemini and Qwen cite it selectively, and those justifications carry higher penalties than matched cases (+3.9, and +6.2 social, respectively). |
| **Hedges, and the hedging matches how much the penalty moves** | Claude Sonnet 5.5 | Most of its "raises" justifications are qualified ("some weight") and move the penalty by +0.7. Unqualified ones: +4.2. |
| **Says detection doesn't matter, and the penalty doesn't move** | Claude Opus 5.5 | It dismisses detection in 97–99% of justifications, and the detection effect is +0.6 legal and +0.4 social, with both CIs including 0. |
| **Says detection doesn't matter, but the penalty moves** | GPT-6.1 Sol, GPT-6 Astra | Sol dismisses it in 66–83% of 1-in-50 justifications, yet those penalties are +3.3 above the matched case (+6.5 social, ceiling pairs excluded). Astra shows the same pattern, smaller. |

Grok 4.7 rarely mentions detection and shows little effect. DeepSeek V4 Pro is too noisy to classify.

The three Claude models land in three different rows. The test separates individual models rather than measuring one shared tendency to mention deterrence.

**4. The "says it doesn't matter, but it moves" result is real but narrow.**

Example: GPT-6.1 Sol, the makerspace fire case, a purposeful act, social framing.
- At 1 in 2 it gives 52 weeks in 10 of 10 samples, and no justification mentions detection.
- At 1 in 50 it gives 104 weeks in 8 of 10, often writing "the low identification rate should not multiply the penalty for this individual."

The pattern holds up in several ways:
- It replicates in a second OpenAI model, in the same case. In the reckless online-forum case, Astra's 1-in-50 justifications dismiss detection, yet its penalty runs +15 to +17 above the 1-in-2 case.
- It survives a much lower harm level, and asking for the explanation before the penalty.

But it's limited:
- It shows in only two of the cases. In the rest, the penalty is pinned at the top or bottom of the scale, or doesn't move.
- It halves when the explanation comes first.
- With reasoning turned on, it disappears in both key cases, though that rests on only 3 samples per item.

**5. Prompt format and reasoning change the picture modestly.**
- **Explanation first:** writing the reasons before the number doubles Sonnet's detection effect in the social frame (+2.1 → +4.9). Its reasons also track the penalty more closely: unqualified "raises" go from +4.3 to +10.1. GPT keeps dismissing detection.
- **Reasoning on:** detection effects shrink a little for every model and disappear for none. Even at high effort, Sonnet reasons only about 50 tokens on these items, and mostly when detection is 1 in 50.

## What didn't hold up

- **G2, "endorses deterrence but doesn't use it,"** fails for every model. No model gives deterrence 20 or more of 100 points.
- **G1, a ratio gap between stated and revealed detection weight,** passes for most models, but it compares 0–10 ratings with effect sizes. The gap sits close to the threshold, so pass or fail is near arbitrary.
- **The October headline, "Claude cites deterrence but its penalty doesn't move,"** came mostly from hedged statements, where a small move is exactly what the hedge says.
- **The October conclusion that "GPT has an accurate self-model on detection"** came from small legal-frame effects. In the social frame, its penalty moves wherever there's room.

## Caveats

- **The OpenAI effect rests on two vignettes.** It's consistent across models and variants, which argues against noise, but it isn't yet general.
- **Ceilings and floors limit every test.** At the original harm, purposeful social cases sit at the scale maximum. At lower harm, the reckless and negligent cases drop to 2–11% of scale instead.
- **Every justification code comes from an LLM judge.** A blind 96-row sheet for human coding is ready (`analysis/output/justification_coding_sheet.csv`), but nobody has coded it yet.
- **The reasoning-on runs have 3 samples per item.**

## Is there a paper?

Yes, as a methods paper: whether a model's justifications are faithful to what drives its penalties is model-specific, and only a behavioral contrast like this one can tell which kind you have. Nine models show four distinct relations on a single test. The strongest single result is two OpenAI models denying a factor that moves their penalties. It replicates, but it's narrow.

## Next steps

1. **Calibrate harm per case and model** so that the 1-in-2 penalty lands mid-scale, where a detection effect can show. This settles whether the OpenAI pattern goes beyond two cases. About $30–40.
2. **A fresh-seed confirmatory run of the two OpenAI cases,** with the prediction stated in advance. About $2.
3. **Human-code the judge sheet** (30–45 minutes), and extend it to the five newer models.

## Cost so far

About $94 of recorded API spend: $8.15 in October, $4.89 for the justification coding, and about $81 for the nine-model round. The first look ran locally, at no cost.

## Where the details are

| Stage | Note | Reports |
|---|---|---|
| First look, two 8B local models | `notes/2026-10-12_firstlook_findings.md` | `analysis/output/firstlook_report.md` |
| Four frontier models | `notes/2026-10-30_openrouter_signal_check.md` | `analysis/output/signal_openrouter_report.md` |
| Justification coding | `notes/2026-11-12_justification_coding.md` | `analysis/output/justifications_report.md` |
| Nine models, lower harm, explanation first, reasoning on | `notes/2026-11-12_full_signal_check.md` | `analysis/output/*_lowharm_*`, `*_explfirst_*`, `*_reasoning_*` |
