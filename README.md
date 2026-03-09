# Overnight Experimenter

Give an AI agent a codebase, a metric, and a time budget — let it run experiments autonomously overnight. You wake up to a log of what it tried, what worked, and what didn't.

Inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch), but general-purpose. Works for performance optimization, prompt engineering, config tuning — anything with a measurable score.

~1000 lines of Python. Zero external dependencies.

## Install

```bash
pip install overnight-experimenter
```

Requires Python 3.10+ and a coding agent CLI ([Claude Code](https://docs.anthropic.com/en/docs/claude-code) or [Codex](https://github.com/openai/codex)).

## Quick Start

```bash
# Create an experiment
overnight init my-experiment

# Edit the files:
#   program.md   — what to optimize + constraints
#   evaluate.sh  — script that outputs a numeric score
#   workspace/   — the files the agent can modify

# Run it
overnight run my-experiment --budget 8h --agent claude --direction minimize

# Check progress
overnight status my-experiment

# Generate an HTML report
overnight report my-experiment
```

## How It Works

```
experiment/
├── program.md          # Instructions for the agent
├── workspace/          # Files the agent modifies
├── evaluate.sh         # Returns a numeric score
├── experiments.jsonl   # Auto-generated log
└── best/               # Snapshot of best version
```

**The loop:**

1. Agent reads `program.md` + experiment history
2. Agent makes ONE modification to `workspace/`
3. `evaluate.sh` runs → numeric score
4. If improved → snapshot to `best/`, log success
5. If not → revert to `best/`, log failure
6. Repeat until time budget is exhausted

## Example: Python Performance

The included example optimizes a naive prime-finding algorithm:

```bash
# Copy the example
cp -r examples/python-perf my-experiment

# Run for 30 minutes
overnight run my-experiment --budget 30m --agent claude --direction minimize
```

Starts with trial division (~0.11s), agent discovers sieve of Eratosthenes, bitwise tricks, etc.

## CLI Reference

| Command | Description |
|---------|-------------|
| `overnight init <name>` | Create experiment from templates |
| `overnight run <name> [options]` | Run the experiment loop |
| `overnight status <name>` | Show progress summary |
| `overnight report <name>` | Generate HTML report |

### Run Options

| Flag | Default | Description |
|------|---------|-------------|
| `--budget` | `8h` | Time budget (e.g. `8h`, `30m`, `2h30m`) |
| `--agent` | `claude` | Coding agent (`claude` or `codex`) |
| `--direction` | `maximize` | Optimization direction (`minimize` or `maximize`) |
| `--max-experiments` | — | Optional cap on number of experiments |

## License

MIT
