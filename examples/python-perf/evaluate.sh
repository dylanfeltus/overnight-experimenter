#!/bin/bash
# Benchmark solve.py — measures execution time in seconds.
# The experimenter tries to minimize this number.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOLVE="$SCRIPT_DIR/workspace/solve.py"

# Correctness check: must find exactly 1229 primes up to 10000
output=$(python3 "$SOLVE" 2>&1)
count=$(echo "$output" | grep -oE '[0-9]+ primes' | grep -oE '[0-9]+')

if [ "$count" != "1229" ]; then
    echo "WRONG ANSWER: expected 1229 primes, got $count" >&2
    echo "999.0"
    exit 0
fi

# Benchmark: average of 3 runs
total=0
for i in 1 2 3; do
    elapsed=$( { time python3 "$SOLVE" > /dev/null; } 2>&1 | grep real | sed 's/real[[:space:]]*//' )
    # Parse time format (e.g., 0m1.234s)
    minutes=$(echo "$elapsed" | sed 's/m.*//')
    seconds=$(echo "$elapsed" | sed 's/.*m//;s/s//')
    run_time=$(echo "$minutes * 60 + $seconds" | bc)
    total=$(echo "$total + $run_time" | bc)
done

avg=$(echo "scale=4; $total / 3" | bc)
echo "Avg time: ${avg}s (3 runs)"
echo "$avg"
