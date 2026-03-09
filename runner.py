#!/usr/bin/env python3
"""
Overnight Experimenter — Core Runner

Orchestrates autonomous experimentation by spawning a coding agent,
managing workspace snapshots, evaluating results, and logging everything.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path


def parse_duration(s: str) -> float:
    """Parse a duration string like '8h', '30m', '2h30m' into seconds."""
    s = s.strip().lower()
    total = 0.0
    current = ""
    for ch in s:
        if ch.isdigit() or ch == ".":
            current += ch
        elif ch == "h":
            total += float(current) * 3600
            current = ""
        elif ch == "m":
            total += float(current) * 60
            current = ""
        elif ch == "s":
            total += float(current)
            current = ""
        else:
            raise ValueError(f"Unknown duration character: {ch}")
    if current:
        # bare number treated as seconds
        total += float(current)
    return total


def snapshot(src: Path, dst: Path):
    """Copy src directory to dst, replacing dst if it exists."""
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def revert(src: Path, dst: Path):
    """Restore dst from src snapshot."""
    if not src.exists():
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def get_diff(workspace: Path, best: Path) -> str:
    """Get a unified diff between best/ and workspace/."""
    try:
        result = subprocess.run(
            ["diff", "-ruN", str(best), str(workspace)],
            capture_output=True, text=True, timeout=30,
        )
        return result.stdout[:5000]  # cap diff length
    except Exception:
        return "(diff unavailable)"


def run_evaluation(experiment_dir: Path, timeout: int = 300) -> tuple[float | None, str]:
    """Run evaluate.sh and extract the numeric score from the last line of stdout.

    Returns (score, full_output). Score is None if evaluation fails.
    """
    eval_script = experiment_dir / "evaluate.sh"
    if not eval_script.exists():
        return None, "evaluate.sh not found"

    try:
        result = subprocess.run(
            ["bash", str(eval_script)],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(experiment_dir),
        )
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            return None, f"evaluate.sh failed (exit {result.returncode})\nstdout: {output}\nstderr: {stderr}"

        # Extract score from last non-empty line of stdout
        lines = [l.strip() for l in output.split("\n") if l.strip()]
        if not lines:
            return None, "evaluate.sh produced no output"

        try:
            score = float(lines[-1])
        except ValueError:
            return None, f"Last line is not a number: {lines[-1]!r}"

        return score, output

    except subprocess.TimeoutExpired:
        return None, f"evaluate.sh timed out after {timeout}s"
    except Exception as e:
        return None, f"Error running evaluate.sh: {e}"


def build_agent_prompt(program_text: str, experiment_num: int, history: list[dict],
                       best_score: float | None, direction: str) -> str:
    """Build the prompt sent to the coding agent."""
    direction_word = "lower" if direction == "minimize" else "higher"

    prompt_parts = [
        "You are running an autonomous experiment. Read the instructions below carefully.",
        "",
        "# Experiment Program",
        program_text,
        "",
        f"# Experiment #{experiment_num}",
        "",
        f"Optimization direction: {direction} ({direction_word} is better)",
    ]

    if best_score is not None:
        prompt_parts.append(f"Current best score: {best_score}")

    # Include recent history for context
    if history:
        prompt_parts.append("")
        prompt_parts.append("# Recent Experiment History (last 10)")
        for h in history[-10:]:
            status = "IMPROVED" if h.get("improved") else "no improvement"
            desc = h.get("description", "no description")
            prompt_parts.append(f"  #{h['experiment_id']}: score={h['score']} ({status}) — {desc}")

    prompt_parts.extend([
        "",
        "# Your Task",
        "Make exactly ONE modification to the files in the workspace/ directory.",
        "The modification should be guided by the program instructions above and the experiment history.",
        "Try something DIFFERENT from what has already been tried.",
        "Be creative but stay within the constraints.",
        "",
        "After making your change, briefly describe what you changed and why in a single line",
        "prefixed with 'CHANGE_DESCRIPTION:' — this will be logged.",
        "",
        "IMPORTANT: Only modify files inside the workspace/ directory. Do not modify any other files.",
    ])

    return "\n".join(prompt_parts)


def spawn_agent(prompt: str, experiment_dir: Path, agent: str = "claude",
                timeout: int = 600) -> tuple[str, str]:
    """Spawn the coding agent and return (description, full_output).

    Supports 'claude' and 'codex' agents.
    """
    if agent == "claude":
        cmd = [
            "claude", "-p", prompt,
            "--allowedTools", "Edit,Write,Read,Glob,Grep",
        ]
    elif agent == "codex":
        cmd = ["codex", "--prompt", prompt]
    else:
        cmd = [agent, prompt]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=timeout,
            cwd=str(experiment_dir),
        )
        output = result.stdout.strip()

        # Extract change description
        description = "no description"
        for line in output.split("\n"):
            if "CHANGE_DESCRIPTION:" in line:
                description = line.split("CHANGE_DESCRIPTION:", 1)[1].strip()
                break

        return description, output

    except subprocess.TimeoutExpired:
        return "agent timed out", "(timeout)"
    except FileNotFoundError:
        print(f"Error: Agent '{agent}' not found. Is it installed and in PATH?")
        sys.exit(1)
    except Exception as e:
        return f"agent error: {e}", str(e)


def load_history(experiment_dir: Path) -> list[dict]:
    """Load experiment history from experiments.jsonl."""
    jsonl = experiment_dir / "experiments.jsonl"
    if not jsonl.exists():
        return []
    history = []
    for line in jsonl.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                history.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return history


def append_experiment(experiment_dir: Path, record: dict):
    """Append an experiment record to experiments.jsonl."""
    jsonl = experiment_dir / "experiments.jsonl"
    with open(jsonl, "a") as f:
        f.write(json.dumps(record) + "\n")


def is_better(score: float, best: float, direction: str) -> bool:
    """Check if score is better than best given the optimization direction."""
    if direction == "minimize":
        return score < best
    else:
        return score > best


def run_experiment_loop(experiment_dir: Path, budget_seconds: float,
                        agent: str, direction: str, max_experiments: int | None):
    """Main experiment loop."""
    experiment_dir = experiment_dir.resolve()
    workspace = experiment_dir / "workspace"
    best_dir = experiment_dir / "best"
    program_file = experiment_dir / "program.md"

    # Validate experiment directory
    if not experiment_dir.exists():
        print(f"Error: Experiment directory not found: {experiment_dir}")
        sys.exit(1)
    if not program_file.exists():
        print(f"Error: program.md not found in {experiment_dir}")
        sys.exit(1)
    if not workspace.exists():
        print(f"Error: workspace/ not found in {experiment_dir}")
        sys.exit(1)

    program_text = program_file.read_text()
    history = load_history(experiment_dir)

    # Determine starting experiment number
    start_num = len(history) + 1

    # Get initial best score (run baseline if no history)
    best_score: float | None = None
    if history:
        improving = [h for h in history if h.get("improved")]
        if improving:
            best_score = improving[-1]["score"]
        elif history:
            best_score = history[0]["score"]

    if best_score is None:
        # Run baseline evaluation
        print("Running baseline evaluation...")
        if not best_dir.exists():
            snapshot(workspace, best_dir)

        score, eval_output = run_evaluation(experiment_dir)
        if score is None:
            print(f"Baseline evaluation failed: {eval_output}")
            sys.exit(1)

        best_score = score
        record = {
            "experiment_id": 0,
            "timestamp": datetime.now().isoformat(),
            "description": "baseline",
            "score": score,
            "best_score": score,
            "improved": True,
            "duration_s": 0,
            "diff": "",
        }
        append_experiment(experiment_dir, record)
        history.append(record)
        print(f"Baseline score: {score}")

    # Ensure best/ snapshot exists
    if not best_dir.exists():
        snapshot(workspace, best_dir)

    start_time = time.time()
    deadline = start_time + budget_seconds
    experiment_num = start_num

    print(f"\nStarting experiment loop")
    print(f"  Direction: {direction}")
    print(f"  Budget: {budget_seconds / 3600:.1f}h")
    print(f"  Agent: {agent}")
    print(f"  Best score: {best_score}")
    if max_experiments:
        print(f"  Max experiments: {max_experiments}")
    print()

    experiments_run = 0

    while time.time() < deadline:
        if max_experiments and experiments_run >= max_experiments:
            print(f"\nReached max experiments ({max_experiments}). Stopping.")
            break

        remaining = deadline - time.time()
        if remaining < 30:
            print("\nLess than 30s remaining. Stopping.")
            break

        print(f"{'='*60}")
        print(f"Experiment #{experiment_num}  |  Best: {best_score}  |  "
              f"Remaining: {remaining/60:.0f}m")
        print(f"{'='*60}")

        exp_start = time.time()

        # 1. Revert workspace to best state before agent modifies it
        revert(best_dir, workspace)

        # 2. Build prompt and spawn agent
        prompt = build_agent_prompt(program_text, experiment_num, history,
                                    best_score, direction)
        print(f"  Spawning {agent} agent...")
        description, agent_output = spawn_agent(prompt, experiment_dir, agent)
        print(f"  Change: {description}")

        # 3. Evaluate
        print(f"  Evaluating...")
        score, eval_output = run_evaluation(experiment_dir)

        if score is None:
            print(f"  Evaluation failed: {eval_output}")
            diff = get_diff(workspace, best_dir)
            record = {
                "experiment_id": experiment_num,
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "score": None,
                "best_score": best_score,
                "improved": False,
                "duration_s": round(time.time() - exp_start, 1),
                "diff": diff,
                "error": eval_output,
            }
            append_experiment(experiment_dir, record)
            history.append(record)
            revert(best_dir, workspace)
            experiment_num += 1
            experiments_run += 1
            continue

        # 4. Compare and decide
        diff = get_diff(workspace, best_dir)
        improved = is_better(score, best_score, direction)

        if improved:
            print(f"  IMPROVED: {best_score} → {score}")
            best_score = score
            snapshot(workspace, best_dir)
        else:
            print(f"  No improvement: {score} (best: {best_score})")
            revert(best_dir, workspace)

        # 5. Log
        record = {
            "experiment_id": experiment_num,
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "score": score,
            "best_score": best_score,
            "improved": improved,
            "duration_s": round(time.time() - exp_start, 1),
            "diff": diff,
        }
        append_experiment(experiment_dir, record)
        history.append(record)

        experiment_num += 1
        experiments_run += 1

    # Summary
    elapsed = time.time() - start_time
    improvements = sum(1 for h in history if h.get("improved"))
    print(f"\n{'='*60}")
    print(f"Experiment loop complete")
    print(f"  Total experiments: {len(history)}")
    print(f"  Improvements: {improvements}")
    print(f"  Best score: {best_score}")
    print(f"  Time elapsed: {elapsed/3600:.1f}h")
    print(f"{'='*60}")

    # Generate report
    from report import generate_report
    report_path = generate_report(experiment_dir)
    print(f"\nReport: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Overnight Experimenter — Autonomous experimentation runner"
    )
    parser.add_argument("experiment_dir", type=Path,
                        help="Path to the experiment directory")
    parser.add_argument("--budget", type=str, default="8h",
                        help="Time budget (e.g. '8h', '30m', '2h30m')")
    parser.add_argument("--agent", type=str, default="claude",
                        choices=["claude", "codex"],
                        help="Coding agent to use")
    parser.add_argument("--direction", type=str, default="maximize",
                        choices=["minimize", "maximize"],
                        help="Optimization direction")
    parser.add_argument("--max-experiments", type=int, default=None,
                        help="Maximum number of experiments to run")

    args = parser.parse_args()
    budget_seconds = parse_duration(args.budget)

    run_experiment_loop(
        experiment_dir=args.experiment_dir,
        budget_seconds=budget_seconds,
        agent=args.agent,
        direction=args.direction,
        max_experiments=args.max_experiments,
    )


if __name__ == "__main__":
    main()
