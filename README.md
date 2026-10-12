# self_report_punishment

Do AI models' accounts of their reasoning match what they do? This project tests whether LLM self-reports (stated principles, justifications, reasoning traces, self-predictions) are reliable evidence of how models actually make punishment judgments, in rating tasks and as agents, with a parallel track on outcome bias in LLM judges. The pilot runs every case in two framings, rule violations in community organizations (suspensions and bans) and criminal sentencing; see `proposal/vignette_templates.md` for why.

## Layout

- `proposal/`: project outline, stimulus-design definitions, and the pilot vignette design (`vignette_templates.md`)
- `stimuli/templates_social.json`, `stimuli/templates_legal.json`: vignette text and slots for the two framings; `stimuli/vignettes_preview.md` shows every assembled vignette
- `prompts/pilot_prompts.json`: all other pilot prompt wording (sentencing, manipulation checks, stated principles, self-prediction)
- `scripts/build_items.py`: assembles the two JSON sources into `stimuli/vignettes.jsonl` and `prompts/items.jsonl`

- `config/models.json`: models to run (local via Ollama, or APIs)
- `scripts/run_pilot.py`: sends items to models and saves responses to `data/responses/<model>.jsonl` (both framings by default; `--frames social` for one)
- `scripts/refusal_report.py`: refusal and nonresponse rates by model, frame, item type, and mental state
- `analysis/analyze_pilot.py`: applies the decision criteria in `proposal/pilot_criteria.md`; writes `analysis/output/<dir>_report.md`

Edit the JSON sources, then rebuild with `python3 scripts/build_items.py`. Don't edit the `.jsonl` files by hand.

## Running the pilot

Local models need [Ollama](https://ollama.com): install it, then `ollama pull llama3.1:8b` (and the other enabled models in `config/models.json`).

```
python3 scripts/run_pilot.py --dry-run                          # show what would run
python3 scripts/run_pilot.py --models mock --samples 2          # test the pipeline offline
python3 scripts/run_pilot.py --models llama3.1-8b --limit 20    # smoke test on a real model
python3 scripts/run_pilot.py --samples 10                       # full pilot, all enabled models
python3 scripts/run_pilot.py --frames social --samples 5        # one framing only
```

On a Mac, the runner keeps the machine from sleeping until it finishes (via `caffeinate`); pass `--allow-sleep` to turn that off.

Reruns skip completed rows, so an interrupted run resumes where it left off. Raw replies are always saved; `parsed` is a best-effort parse that can be redone in analysis.
