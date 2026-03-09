"""
Find all prime numbers up to N using trial division.
This is intentionally naive — the experimenter should optimize it.
"""


def find_primes(n: int) -> list[int]:
    primes = []
    for candidate in range(2, n + 1):
        is_prime = True
        for divisor in range(2, candidate):
            if candidate % divisor == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(candidate)
    return primes


if __name__ == "__main__":
    result = find_primes(10000)
    print(f"Found {len(result)} primes up to 10000")
