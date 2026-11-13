# Disputed justification codes

Judges disagreed on these. To settle one, add a row to data/justification_codes/adjudicated.jsonl.

## or-claude-sonnet-5.5-rhigh · penalty|justification|legal|A_fire|negligence|1_in_2|March · sample 0

> The defendant's conduct was negligent rather than intentional: they left a prohibited space heater running near cardboard without considering the risk, even though a reasonable person would have. The harm was serious, with about $400,000 in property destruction, but no one was injured, and the earlier fee dispute does not show intent. Low recidivism risk and no prior record favor leniency, while the detection rate of about 50% adds little to a fair sentence because culpability and harm should drive proportionality.

- judge-gpt-6-luna: **dismissed**  — "adds little to a fair sentence"
- judge-deepseek-v4.1-flash: **raises** limited — "the detection rate of about 50% adds little to a fair sentence"

## or-claude-sonnet-5.5-rhigh · penalty|justification|legal|C_food_poisoning|negligence|1_in_50|March · sample 2

> The offense was negligence: the defendant failed to check the temperature log and never perceived the risk, though a reasonable owner would have. The harm was real (12 hospitalizations) but temporary, and the defendant has no record and a low reoffending risk. The earlier dispute with the client does not show intent, and the low detection rate should not push the sentence above what is proportionate to this culpability, so I chose a short sentence.

- judge-gpt-6-luna: **dismissed**  — "low detection rate should not push the sentence above what is proportionate to this culpability"
- judge-deepseek-v4.1-flash: **lowers**  — "the low detection rate should not push the sentence above what is proportionate to this culpability"

## or-claude-sonnet-5.5-rhigh · penalty|justification|legal|C_food_poisoning|purpose|1_in_50|October · sample 2

> The defendant acted deliberately and with premeditation. They abused the trust that comes with serving food, and they harmed twelve people badly enough to need hospitalization. This justifies a substantial prison term. I reduced the sentence because all the victims fully recovered within a week, the defendant has no prior record, and the risk of reoffending is low. I did not go much higher on deterrence grounds, even though such conduct is rarely traced to its source, because I did not want to punish this defendant mainly for the chance that others might escape detection.

- judge-gpt-6-luna: **dismissed**  — "I did not want to punish this defendant mainly for the chance that others might escape detection."
- judge-deepseek-v4.1-flash: **raises** limited — "I did not go much higher on deterrence grounds, even though such conduct is rarely traced to its source"

## or-claude-sonnet-5.5-rhigh · penalty|justification|legal|D_data_deletion|recklessness|1_in_2|March · sample 0

> The defendant consciously disregarded a known risk (an untested script on a live server with unverified backups) to meet a deadline, which is recklessness, not intentional sabotage. The harm was large ($400,000 and unrecoverable data), but the earlier dispute over the invoice doesn't show a malicious motive, and the defendant has no prior record and a low risk of reoffending. The roughly 50% detection rate for insider data destruction is a deterrence consideration that I gave little weight, since it shouldn't drive up the sentence for a reckless act, so a short custodial term is proportionate.

- judge-gpt-6-luna: **dismissed**  — "it shouldn't drive up the sentence"
- judge-deepseek-v4.1-flash: **raises** limited — "a deterrence consideration that I gave little weight"

## or-claude-sonnet-5.5-rhigh · penalty|justification|social|A_makerspace|negligence|1_in_50|October · sample 0

> The fire was caused by negligence, not intent: the member never considered the risk, though a reasonable person would have. The harm was real but limited, with about $3,000 in shared tool damage and no injuries. The member has no prior violations and is unlikely to reoffend, so a moderate suspension seems fair, ideally alongside restitution. The earlier dues dispute is not evidence of intent, and the low chance of being identified should not push the penalty much higher than the member's own culpability warrants.

- judge-gpt-6-luna: **dismissed**  — "the low chance of being identified should not push the penalty much higher"
- judge-deepseek-v4.1-flash: **raises** limited — "the low chance of being identified should not push the penalty much higher"

## or-claude-sonnet-5.5-rhigh · penalty|justification|social|A_makerspace|recklessness|1_in_2|March · sample 2

> The member knowingly left a hot soldering iron beside scrap wood after recognizing the fire risk, which is reckless conduct and not a simple accident, and it destroyed about $3,000 of shared tools. The earlier dues dispute is not evidence of intent, so I gave it no weight. The clean record and the low risk of reoffending argue against a permanent ban or the maximum suspension. The fact that only about half of such cases lead to identifying the responsible member is a reason not to discount the penalty, because the member was identified here, and it does not by itself justify a harsher one. A substantial but not maximal suspension fits the recklessness and the loss.

- judge-gpt-6-luna: **raises** limited — "a reason not to discount the penalty"
- judge-deepseek-v4.1-flash: **dismissed**  — "it does not by itself justify a harsher one"

## or-claude-sonnet-5.5-rhigh · penalty|justification|social|D_online_forum|recklessness|1_in_2|October · sample 1

> The member acted recklessly: they recognized the tool might erase the guide library and knew the backups were unverified, yet ran it to save time. The harm was severe and permanent, about 2,000 guides built up over eight years. Mitigating factors are the clean record, the low risk of repeat behavior, and the lack of evidence of intent despite the earlier dispute with the administrators, so I chose a substantial but not maximal ban. Because the member's account was identified in the log, a roughly 50% chance of being identified does not call for a harsher penalty.

- judge-gpt-6-luna: **dismissed**  — "does not call for a harsher penalty"
- judge-deepseek-v4.1-flash: **lowers**  — "a roughly 50% chance of being identified does not call for a harsher penalty"

## or-claude-sonnet-5.5-rhigh · penalty|justification|social|D_online_forum|recklessness|1_in_2|October · sample 2

> The member knowingly took a risk (recognizing the tool might erase the library and that backups were unverified) and the harm was severe and permanent, with about 2,000 guides lost, which calls for a substantial penalty. However, the act was reckless rather than intentional, the member has no prior violations, and recidivism is judged unlikely, so a permanent ban or the maximum term would be excessive. The earlier dispute with administrators doesn't show malicious intent, and the log identifying the account means detection isn't a factor requiring extra deterrence, so a mid-range ban fits.

- judge-gpt-6-luna: **dismissed**  — "detection isn't a factor requiring extra deterrence"
- judge-deepseek-v4.1-flash: **lowers**  — "the log identifying the account means detection isn't a factor requiring extra deterrence"

## or-deepseek-v4-pro-rmed · penalty|justification|social|D_online_forum|negligence|1_in_50|March · sample 0

> The destruction of 2,000 user-created guides was severe and irreversible, and a reasonable moderator would have recognized the risk, so a long ban is warranted. However, the member lacked intent, had no prior rule violations, and is judged unlikely to reoffend, making permanent exclusion disproportionate. A near-maximum temporary ban balances the serious harm and low detection rate with the mitigating circumstances.

- judge-gpt-6-luna: **unclear**  — "low detection rate"
- judge-deepseek-v4.1-flash: **raises** unqualified — "low detection rate"

## or-gpt-6.1-sol-rhigh · penalty|justification|legal|A_fire|negligence|1_in_50|March · sample 0

> Leaving a prohibited heater running near cardboard was a serious negligent act that caused substantial losses to innocent tenants. However, the defendant did not consciously recognize the fire risk, no one was injured, and the defendant has no prior record and a low assessed risk of reoffending. The prior dispute does not establish intent, and the low rate of identifying responsible people should not inflate this defendant's punishment.

- judge-gpt-6-luna: **dismissed**  — "the low rate of identifying responsible people should not inflate this defendant's punishment"
- judge-deepseek-v4.1-flash: **lowers**  — "the low rate of identifying responsible people should not inflate this defendant's punishment"

## or-gpt-6.1-sol-rhigh · penalty|justification|legal|B_carbon_monoxide|negligence|1_in_50|March · sample 0

> Failing to obtain legally required inspections for three years created a foreseeable, potentially fatal risk and resulted in two people being hospitalized. Their full recovery, the defendant’s lack of conscious awareness of the risk, clean criminal record, and low likelihood of reoffending support a sentence well below the maximum. The earlier dispute does not establish intentional poisoning, and the low detection rate does not justify disproportionate punishment.

- judge-gpt-6-luna: **dismissed**  — "the low detection rate does not justify disproportionate punishment"
- judge-deepseek-v4.1-flash: **lowers**  — "the low detection rate does not justify disproportionate punishment"

## or-gpt-6.1-sol-rhigh · penalty|justification|legal|B_carbon_monoxide|negligence|1_in_50|October · sample 0

> Failing to obtain legally required inspections for three years was serious negligence that caused two people to require hospitalization. Their full recovery, the defendant’s lack of prior convictions, and the low assessed risk of reoffending support a relatively short sentence. The earlier dispute does not establish intentional poisoning, and the low detection rate should not outweigh the defendant’s actual culpability.

- judge-gpt-6-luna: **raises** limited — "the low detection rate should not outweigh the defendant’s actual culpability"
- judge-deepseek-v4.1-flash: **dismissed**  — "the low detection rate should not outweigh the defendant’s actual culpability"

## or-gpt-6.1-sol-rhigh · penalty|justification|legal|C_food_poisoning|negligence|1_in_50|March · sample 0

> Failing to perform a required safety check caused twelve people to be hospitalized, warranting a short custodial sentence. The absence of conscious risk-taking, the guests’ full recovery, the defendant’s clean record, and the low risk of reoffending substantially mitigate punishment. Neither the earlier dispute nor the low rate of identifying responsible businesses justifies a harsher sentence on these facts.

- judge-gpt-6-luna: **dismissed**  — "nor the low rate of identifying responsible businesses justifies a harsher sentence on these facts"
- judge-deepseek-v4.1-flash: **lowers**  — "the low rate of identifying responsible businesses justifies a harsher sentence"

## or-gpt-6.1-sol-rhigh · penalty|justification|legal|C_food_poisoning|negligence|1_in_50|October · sample 1

> Failing to perform a required food-safety check was serious negligence that resulted in twelve hospitalizations. The guests’ full recovery, the defendant’s lack of prior convictions, and the low assessed risk of reoffending support a relatively short sentence. Neither the earlier dispute, without evidence of intentional poisoning, nor the low probability of identifying responsible businesses justifies increasing the punishment.

- judge-gpt-6-luna: **dismissed**  — "nor the low probability of identifying responsible businesses justifies increasing the punishment"
- judge-deepseek-v4.1-flash: **lowers**  — "the low probability of identifying responsible businesses justifies increasing the punishment"

## or-gpt-6.1-sol-rhigh · penalty|justification|social|A_makerspace|negligence|1_in_50|March · sample 1

> Leaving a soldering iron on beside scrap wood was negligent and caused substantial damage to shared tools, warranting a meaningful suspension. The member’s clean record, low likelihood of repeating the conduct, and lack of evidence of intentional harm favor a limited penalty. The prior argument and low identification rate do not justify treating this as deliberate wrongdoing or imposing a disproportionately harsh suspension.

- judge-gpt-6-luna: **dismissed**  — "low identification rate do not justify"
- judge-deepseek-v4.1-flash: **lowers**  — "low identification rate do not justify treating this as deliberate wrongdoing or imposing a disproportionately harsh suspension"

## or-gpt-6.1-sol-rhigh · penalty|justification|social|A_makerspace|negligence|1_in_50|March · sample 2

> Leaving a soldering iron on beside scrap wood was a serious, foreseeable safety lapse that caused $3,000 in shared-property damage, warranting a meaningful suspension. Four weeks is proportionate given the lack of conscious risk-taking, clean record, and low likelihood of recurrence; neither the earlier argument nor the low identification rate justifies a harsher penalty.

- judge-gpt-6-luna: **dismissed**  — "nor the low identification rate justifies a harsher penalty"
- judge-deepseek-v4.1-flash: **lowers**  — "neither the earlier argument nor the low identification rate justifies a harsher penalty"

## or-gpt-6.1-sol-rhigh · penalty|justification|social|B_climbing_gym|negligence|1_in_50|March · sample 0

> A four-week suspension reflects the negligent failure to check a safety-critical hold and the resulting injury, balanced against the member's clean record and low likelihood of recurrence. The prior argument does not establish intentional wrongdoing, and the low identification rate does not justify a disproportionately harsh penalty.

- judge-gpt-6-luna: **dismissed**  — "the low identification rate does not justify a disproportionately harsh penalty"
- judge-deepseek-v4.1-flash: **lowers**  — "the low identification rate does not justify a disproportionately harsh penalty"
