#!/usr/bin/env python3
"""
Overnight Experimenter — CLI

Usage:
    python cli.py init <name>                              Create experiment from templates
    python cli.py run <name> [--budget 8h] [--agent claude] [--direction minimize]
    python cli.py status <name>                            Show current progress
    python cli.py report <name>                            Generate HTML report
"""

import argparse
import json
import os
import shutil
import stat
import sys
from datetime import datetime
from pathlib import Path

# Resolve paths relative to this script's location
SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"


def cmd_init(args):
    """Create a new experiment directory from templates."""
    experiment_dir = Path(args.name).resolve()

    if experiment_dir.exists():
        print(f"Error: {experiment_dir} already exists")
        sys.exit(1)

    experiment_dir.mkdir(parents=True)
    (experiment_dir / "workspace").mkdir()
    (experiment_dir / "best").mkdir()

    # Copy templates
    program_src = TEMPLATES_DIR / "program.md"
    evaluate_src = TEMPLATES_DIR / "evaluate.sh"

    if program_src.exists():
        shutil.copy2(program_src, experiment_dir / "program.md")
    else:
        (experiment_dir / "program.md").write_text(
            "# Experiment Program\n\n## Objective\nDescribe what you're optimizing.\n\n"
            "## Constraints\nWhat should NOT be changed.\n\n"
            "## Evaluation\nHow evaluate.sh works.\n\n"
            "## Strategy Hints\nOptional guidance for the agent.\n"
        )

    if evaluate_src.exists():
        shutil.copy2(evaluate_src, experiment_dir / "evaluate.sh")
        # Ensure executable
        st = os.stat(experiment_dir / "evaluate.sh")
        os.chmod(experiment_dir / "evaluate.sh", st.st_mode | stat.S_IEXEC)
    else:
        eval_script = experiment_dir / "evaluate.sh"
        eval_script.write_text("#!/bin/bash\necho 0.0\n")
        st = os.stat(eval_script)
        os.chmod(eval_script, st.st_mode | stat.S_IEXEC)

    print(f"Created experiment: {experiment_dir}")
    print(f"  1. Edit program.md with your experiment instructions")
    print(f"  2. Edit evaluate.sh with your evaluation metric")
    print(f"  3. Add your files to workspace/")
    print(f"  4. Run: python cli.py run {args.name}")


def cmd_run(args):
    """Run the experiment loop."""
    from overnight_experimenter.runner import run_experiment_loop, parse_duration

    experiment_dir = Path(args.name).resolve()
    if not experiment_dir.exists():
        print(f"Error: Experiment directory not found: {experiment_dir}")
        print(f"  Run 'python cli.py init {args.name}' first")
        sys.exit(1)

    budget_seconds = parse_duration(args.budget)
    run_experiment_loop(
        experiment_dir=experiment_dir,
        budget_seconds=budget_seconds,
        agent=args.agent,
        direction=args.direction,
        max_experiments=args.max_experiments,
    )


def cmd_status(args):
    """Show current experiment progress."""
    experiment_dir = Path(args.name).resolve()
    jsonl = experiment_dir / "experiments.jsonl"

    if not jsonl.exists():
        print(f"No experiments found in {experiment_dir}")
        return

    experiments = []
    for line in jsonl.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                experiments.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not experiments:
        print("No experiments recorded yet.")
        return

    total = len(experiments)
    improvements = sum(1 for e in experiments if e.get("improved"))
    scored = [e for e in experiments if e.get("score") is not None]
    best_score = scored[-1].get("best_score") if scored else None
    total_duration = sum(e.get("duration_s", 0) for e in experiments)

    first_ts = experiments[0].get("timestamp", "?")[:19]
    last_ts = experiments[-1].get("timestamp", "?")[:19]

    print(f"Experiment: {experiment_dir.name}")
    print(f"  Total experiments: {total}")
    print(f"  Improvements:      {improvements}")
    print(f"  Best score:        {best_score}")
    print(f"  Time elapsed:      {total_duration/3600:.1f}h")
    print(f"  First:             {first_ts}")
    print(f"  Last:              {last_ts}")

    # Show last 5 experiments
    print(f"\nRecent experiments:")
    for e in experiments[-5:]:
        eid = e.get("experiment_id", "?")
        score = e.get("score")
        score_str = f"{score}" if score is not None else "error"
        improved = "+" if e.get("improved") else " "
        desc = str(e.get("description", ""))[:60]
        print(f"  {improved} #{eid}: {score_str:>10}  {desc}")


def cmd_report(args):
    """Generate HTML report."""
    from overnight_experimenter.report import generate_report

    experiment_dir = Path(args.name).resolve()
    if not experiment_dir.exists():
        print(f"Error: Experiment directory not found: {experiment_dir}")
        sys.exit(1)

    path = generate_report(experiment_dir)
    print(f"Report generated: {path}")


def main():
    parser = argparse.ArgumentParser(
        prog="overnight",
        description="Overnight Experimenter — Autonomous experimentation framework",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init", help="Create a new experiment")
    p_init.add_argument("name", help="Experiment name/path")
    p_init.set_defaults(func=cmd_init)

    # run
    p_run = subparsers.add_parser("run", help="Run the experiment loop")
    p_run.add_argument("name", help="Experiment name/path")
    p_run.add_argument("--budget", default="8h", help="Time budget (e.g. '8h', '30m')")
    p_run.add_argument("--agent", default="claude", choices=["claude", "codex"],
                       help="Coding agent to use")
    p_run.add_argument("--direction", default="maximize",
                       choices=["minimize", "maximize"],
                       help="Optimization direction")
    p_run.add_argument("--max-experiments", type=int, default=None,
                       help="Max number of experiments")
    p_run.set_defaults(func=cmd_run)

    # status
    p_status = subparsers.add_parser("status", help="Show experiment progress")
    p_status.add_argument("name", help="Experiment name/path")
    p_status.set_defaults(func=cmd_status)

    # report
    p_report = subparsers.add_parser("report", help="Generate HTML report")
    p_report.add_argument("name", help="Experiment name/path")
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
