# Python Performance Optimizer

## Objective

Make `workspace/solve.py` as fast as possible while keeping it correct.

The file finds all prime numbers up to 10,000 using a naive trial division algorithm. Your job is to optimize it — better algorithms, fewer operations, smarter data structures.

## Constraints

- Only modify `workspace/solve.py`
- The function `find_primes(n)` must return the correct list of primes
- Must find exactly 1229 primes up to 10000 (correctness is verified)
- Pure Python only — no C extensions, no numpy, no multiprocessing
- Keep it readable. No code golf.

## Evaluation

`evaluate.sh` runs the script 3 times and averages the wall-clock execution time. Lower is better.

If the answer is wrong, the score is set to 999.0 (worst possible).

Direction: **minimize** (lower time = better).

## Strategy Hints

- Sieve of Eratosthenes is the classic improvement over trial division
- Only check divisors up to sqrt(candidate)
- Skip even numbers after 2
- Consider bitwise sieves or array-based approaches
- Each experiment should make ONE focused change
