# Overnight Experimenter

General-purpose autonomous experimentation framework for the studio. Inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch).

## Status: In Progress (Prototype)

## Concept

Give an AI agent a codebase, a metric, and a time budget — let it run experiments autonomously overnight. You wake up to a log of what it tried, what worked, and what didn't.

Unlike autoresearch (which is ML-specific), this is **general-purpose**:

- **Landing page conversion** — agent tweaks copy/layout, runs A/B tests, measures click-through
- **Performance optimization** — agent modifies code, benchmarks, keeps improvements
- **Prompt engineering** — agent iterates on prompts, evaluates against a test set
- **Design exploration** — agent generates variations, scores against criteria
- **SEO optimization** — agent tweaks meta/content, checks lighthouse scores

## Architecture

```
experiment/
├── program.md          # Instructions for the agent (what to optimize, constraints)
├── workspace/          # The files the agent can modify
├── evaluate.sh         # Script that returns a numeric score (lower = better or higher = better, configurable)
├── experiments.jsonl   # Log of all experiments (auto-generated)
└── best/               # Snapshot of the best-performing version
```

### Core Loop

1. Agent reads `program.md` for context and constraints
2. Agent modifies files in `workspace/`
3. Runner executes `evaluate.sh` → gets a numeric score
4. If score improves: snapshot to `best/`, log success
5. If score worsens: revert `workspace/` to best, log failure
6. Repeat until time budget exhausted

### Components

- **`runner.py`** — Orchestrator: spawns the coding agent, manages the experiment loop, handles snapshots/reverts, enforces time budget
- **`program.md`** — Template instructions (user customizes per experiment)
- **`evaluate.sh`** — Template evaluation script (user provides their metric)
- **Dashboard** — Simple HTML report of experiment history with charts

## Usage

```bash
# Set up an experiment
overnight init my-experiment
# Edit program.md and evaluate.sh
# Place your code in workspace/

# Run overnight (8 hour budget, using Claude)
overnight run my-experiment --budget 8h --agent claude

# Check progress
overnight status my-experiment

# View results
overnight report my-experiment
```
