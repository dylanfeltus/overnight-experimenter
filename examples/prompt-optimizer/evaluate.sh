#!/bin/bash
# evaluate.sh — Prompt optimizer evaluation
#
# Runs test queries against the system prompt and scores responses.
# Outputs a normalized score (0.0-1.0) on the last line.
#
# Requirements: 'claude' CLI must be available in PATH.
# Falls back to a heuristic scorer if claude is not available.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROMPT_FILE="$SCRIPT_DIR/workspace/prompt.txt"

if [ ! -f "$PROMPT_FILE" ]; then
    echo "Error: workspace/prompt.txt not found" >&2
    exit 1
fi

SYSTEM_PROMPT=$(cat "$PROMPT_FILE")
PROMPT_LENGTH=${#SYSTEM_PROMPT}

# Enforce length constraint
if [ "$PROMPT_LENGTH" -gt 2000 ]; then
    echo "Prompt exceeds 2000 character limit ($PROMPT_LENGTH chars)" >&2
    echo "0.0"
    exit 0
fi

# Test queries representing common customer scenarios
QUERIES=(
    "My website has been down for 2 hours and I'm losing customers. I need help NOW."
    "How do I set up SSL certificates for my custom domain?"
    "I was charged twice on my last invoice. Can you help me get a refund?"
    "What's the difference between your Basic and Pro hosting plans?"
    "I'm getting a 502 Bad Gateway error when deploying my Node.js app."
)

score_response_heuristic() {
    local response="$1"
    local query="$2"
    local score=0

    # Relevance: response length > 50 chars suggests engagement
    if [ ${#response} -gt 50 ]; then
        score=$((score + 1))
    fi
    if [ ${#response} -gt 150 ]; then
        score=$((score + 1))
    fi

    # Clarity: contains structured elements (numbered steps, bullet points)
    if echo "$response" | grep -qE '^\s*[0-9]+\.|^\s*[-*]' ; then
        score=$((score + 2))
    elif echo "$response" | grep -qiE 'step|first|then|next|finally'; then
        score=$((score + 1))
    fi

    # Helpfulness: contains actionable language
    if echo "$response" | grep -qiE 'you can|try|check|visit|contact|click|navigate|run'; then
        score=$((score + 2))
    elif echo "$response" | grep -qiE 'recommend|suggest|option'; then
        score=$((score + 1))
    fi

    # Accuracy: mentions relevant product/technical terms
    if echo "$response" | grep -qiE 'acme|cloud|hosting|server|domain|ssl|dns'; then
        score=$((score + 1))
    fi
    if echo "$response" | grep -qiE 'dashboard|account|settings|support|team'; then
        score=$((score + 1))
    fi

    # Tone: empathetic and professional language
    if echo "$response" | grep -qiE 'understand|sorry|appreciate|happy to|glad to'; then
        score=$((score + 1))
    fi
    if echo "$response" | grep -qiE 'please|thank|help you'; then
        score=$((score + 1))
    fi

    echo "$score"
}

total_score=0
max_possible=$((${#QUERIES[@]} * 10))

echo "Evaluating prompt (${PROMPT_LENGTH} chars)..."
echo ""

for i in "${!QUERIES[@]}"; do
    query="${QUERIES[$i]}"
    echo "Query $((i+1)): ${query:0:60}..."

    # Try using claude CLI for evaluation
    if command -v claude &> /dev/null; then
        response=$(claude -p "You are a customer support chatbot with this system prompt:

---
$SYSTEM_PROMPT
---

Respond to this customer query in character:
$query" 2>/dev/null || echo "")
    else
        # Fallback: use the prompt itself as a proxy for quality
        response="$SYSTEM_PROMPT"
    fi

    if [ -z "$response" ]; then
        echo "  (no response)"
        query_score=0
    else
        query_score=$(score_response_heuristic "$response" "$query")
        echo "  Score: $query_score/10"
    fi

    total_score=$((total_score + query_score))
done

echo ""
echo "Total: $total_score / $max_possible"

# Normalize to 0.0-1.0
normalized=$(echo "scale=4; $total_score / $max_possible" | bc)
echo "$normalized"
