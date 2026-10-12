# Do AI Models' Accounts of Their Reasoning Match What They Do?

*Proposal outline*

---

## The question

- Oversight of models and agents relies on what they say about themselves: stated principles, reasoning traces, and explanations.
- Can those self-reports be used as evidence of how a model evaluates cases?
- Human template: people endorse deterrence as the purpose of punishment but sentence by culpability.

---

## Stage 1: Are self-reports usable?

### Stability
- **Test:** Ask the model about its principles of punishment repeatedly, varying wording, format (open-ended, point allocation, agreement ratings), and framing, and check whether the answers stay consistent.
- **Why:** If answers shift with phrasing, they can't be evidence of a stable way of evaluating cases.

### Predictive accuracy
- **Test:** Ask how the model's sentence would change if one factor changed (e.g., detection probability from 1 in 2 to 1 in 50), then run both versions and compare its prediction to its actual change.
- **Why:** This directly tests whether the model's account of itself matches its behavior, which is what anyone relying on its explanations needs to know.

---

## Stage 2: Stated vs. applied justice judgments

### Revealed weights
- **Test:** Present sentencing vignettes that vary culpability, detection probability, recidivism risk, and an irrelevant factor independently, then estimate how much each factor moves the sentence.
- **Why:** This shows what actually drives the model's judgments, giving a behavioral benchmark to compare against what it says.

### Stated vs. revealed comparison
- **Test:** Compare the principles the model endorses in Stage 1 with the factors that actually move its sentences.
- **Why:** A systematic gap means declared principles aren't reliable evidence of how the model evaluates cases.

### Justifications
- **Test:** Ask for a justification with each sentence, and compare the factors it cites with the factors that actually moved the sentence.
- **Why:** This tests case-level explanations, which are what people actually read, rather than abstract principles.

### Trade-off choices
- **Test:** Present pairs where one offender is more culpable and the other's sentence has more deterrent value, with limited capacity, and ask who gets the longer sentence.
- **Why:** Ratings let a model hedge, but forced choices reveal which factor wins when they conflict.

---

## Stage 3: Stated vs. enacted, in agents

### Enacted decisions
- **Test:** Agents make graded decisions through tool calls in a simulated environment (e.g., moderation penalties), with analogs of the Stage 2 factors varied independently.
- **Why:** This tests whether the Stage 2 pattern holds when the model acts rather than rates, which is where it matters most for safety.

### Reasoning traces and explanations
- **Test:** Compare the factors cited in the agent's reasoning and after-the-fact explanations with the factors that actually drove its actions.
- **Why:** Monitoring agents relies on these traces and explanations, and this tests whether they can be trusted.

### Agent self-prediction
- **Test:** Before the task, ask the agent how it would act if a factor changed, then compare with what it does.
- **Why:** Agents that plan or delegate depend on predicting their own behavior, and Stages 1–2 provide the baseline for whether acting makes predictions better or worse.

---

## Parallel track: Outcome bias in AI judges

### Outcome manipulation
- **Test:** Hold a decision's evidence, stated risk, and motives fixed and vary only whether it turned out well or badly, then rate decision quality, the agent, and the outcome separately.
- **Why:** This shows whether judges penalize bad luck, and which judgment, the decision or the agent, it contaminates.

### Random-mechanism outcomes
- **Test:** Make the outcome depend on an explicitly random event like a die roll.
- **Why:** The outcome then carries no information about decision quality, so any effect on ratings can't be defended as reasonable inference.

### Hindsight check
- **Test:** After showing the outcome, ask how likely harm was beforehand, and check against the probability stated in the vignette.
- **Why:** This distinguishes rewriting what was knowable from directly weighting luck, which matters for remedies, since only the former would yield to better comprehension.

### Quality of will
- **Test:** Vary whether the agent ignored, accepted, or mitigated the risk, crossed with outcome.
- **Why:** This tests whether outcomes matter more when the agent's attitude was poor, as in human moral judgment.

### Agent trajectory judging
- **Test:** Have LLM judges score agent trajectories where randomness determines success, using rubrics like those used in practice.
- **Why:** Judges like these evaluate and train agents, so rewarding luck over sound decisions has direct consequences.

---

## Methods

- **Grounded stimuli:** Use Model Penal Code mental states and theory-specific predictions, with expert review, so each vignette manipulates what we intend and results map onto recognized positions.
- **Template-based vignettes:** A small set of templates with interchangeable slots generates all cells, which keeps writing and validation manageable.
- **Models:** Llama, Qwen, Mistral, and Gemma at multiple scales, plus frontier models, so we can test whether patterns hold across families, scale, and the systems actually deployed.

---

## Payoff

- When can we take a model's account of its own reasoning at face value, and does that change when it acts as an agent?
