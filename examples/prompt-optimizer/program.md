# Prompt Optimizer Experiment

## Objective

Optimize the system prompt in `workspace/prompt.txt` for a customer support chatbot.

The goal is to maximize helpfulness, clarity, and accuracy of the chatbot's responses
when handling common customer queries. The evaluation script runs a set of test
conversations and scores the responses.

## Constraints

- Only modify `workspace/prompt.txt`. Do not modify any other files.
- The prompt must be under 2000 characters.
- The prompt must instruct the bot to be a customer support agent for "Acme Cloud" — a cloud hosting platform.
- Do not instruct the bot to make up information or hallucinate features.
- Do not include any harmful, deceptive, or manipulative instructions.
- Each experiment should make ONE focused change to the prompt.

## Evaluation

`evaluate.sh` runs 5 test customer queries against the prompt and scores each response on:
- **Relevance** (0-2): Does it address the actual question?
- **Clarity** (0-2): Is the response clear and well-structured?
- **Helpfulness** (0-2): Does it provide actionable next steps?
- **Accuracy** (0-2): Is the information plausible and consistent?
- **Tone** (0-2): Is it professional and empathetic?

Max score per query: 10. Total max: 50.
The script normalizes to 0.0-1.0 range.

Direction: maximize (higher is better).

## Strategy Hints

- Try adding explicit role framing: "You are a senior support engineer at Acme Cloud"
- Add instructions for response structure (greeting, diagnosis, solution, follow-up)
- Include tone guidelines: empathetic, professional, concise
- Add instructions for handling unknown questions (escalation path)
- Try including example Q&A pairs in the prompt
- Experiment with specificity: mention actual product features (compute, storage, DNS, SSL)
- Balance thoroughness vs. conciseness — users don't want novels
