# self_report_punishment

Do AI models' accounts of their reasoning match what they do? This project tests whether LLM self-reports (stated principles, justifications, reasoning traces, self-predictions) are reliable evidence of how models actually make punishment judgments, in rating tasks and as agents, with a parallel track on outcome bias in LLM judges.

## Layout

- `proposal/`: project outline, stimulus-design definitions, and the pilot vignette design (`vignette_templates.md`)
- `stimuli/templates.json`: vignette text and slots (source of truth for the vignettes)
- `prompts/pilot_prompts.json`: all other pilot prompt wording (sentencing, manipulation checks, stated principles, self-prediction)
- `scripts/build_items.py`: assembles the two JSON sources into `stimuli/vignettes.jsonl` and `prompts/items.jsonl`

Edit the JSON sources, then rebuild with `python3 scripts/build_items.py`. Don't edit the `.jsonl` files by hand.
