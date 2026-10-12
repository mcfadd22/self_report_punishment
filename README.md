# self_report_punishment

Do AI models' accounts of their reasoning match what they do? This project tests whether LLM self-reports (stated principles, justifications, reasoning traces, self-predictions) are reliable evidence of how models actually make punishment judgments, in rating tasks and as agents, with a parallel track on outcome bias in LLM judges.

## Layout

- `proposal/`: project outline, stimulus-design definitions, and the pilot vignette design (`vignette_templates.md`)
- `stimuli/templates.json`: vignette text and slots (source of truth for the vignettes)
- `prompts/pilot_prompts.json`: all other pilot prompt wording (sentencing, manipulation checks, stated principles, self-prediction)
- `scripts/build_items.py`: assembles the two JSON sources into `stimuli/vignettes.jsonl` and `prompts/items.jsonl`

- `config/models.json`: models to run (local via Ollama, or APIs)
- `scripts/run_pilot.py`: sends items to models and saves responses to `data/responses/<model>.jsonl`

Edit the JSON sources, then rebuild with `python3 scripts/build_items.py`. Don't edit the `.jsonl` files by hand.

## Running the pilot

Local models need [Ollama](https://ollama.com): install it, then `ollama pull llama3.1:8b` (and the other enabled models in `config/models.json`).

```
python3 scripts/run_pilot.py --dry-run                          # show what would run
python3 scripts/run_pilot.py --models mock --samples 2          # test the pipeline offline
python3 scripts/run_pilot.py --models llama3.1-8b --limit 20    # smoke test on a real model
python3 scripts/run_pilot.py --samples 10                       # full pilot, all enabled models
```

Reruns skip completed rows, so an interrupted run resumes where it left off. Raw replies are always saved; `parsed` is a best-effort parse that can be redone in analysis.
