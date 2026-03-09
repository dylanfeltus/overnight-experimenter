#!/bin/bash
# evaluate.sh — Evaluation script for Overnight Experimenter
#
# This script must output a single numeric score (float) on the LAST line of stdout.
# Everything else printed to stdout before the last line is ignored.
# Stderr is captured but not parsed.
#
# Exit code 0 = success, non-zero = evaluation failed.
#
# ============================================================================
# CUSTOMIZE THIS SCRIPT for your experiment. Examples:
#
# --- Lighthouse performance score ---
# lighthouse http://localhost:3000 --output=json --quiet | jq '.categories.performance.score'
#
# --- pytest pass rate ---
# TOTAL=$(python -m pytest workspace/ --tb=no -q 2>&1 | tail -1)
# PASSED=$(echo "$TOTAL" | grep -oP '\d+ passed' | grep -oP '\d+')
# FAILED=$(echo "$TOTAL" | grep -oP '\d+ failed' | grep -oP '\d+')
# echo "scale=4; $PASSED / ($PASSED + $FAILED)" | bc
#
# --- Custom Python scorer ---
# python score.py workspace/
#
# --- API response time ---
# TIME=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8080/api/health)
# echo "$TIME"
#
# --- Word count / brevity metric ---
# wc -w < workspace/output.txt
# ============================================================================

# Placeholder: replace with your actual evaluation
echo "Running evaluation..."
echo "0.5"
