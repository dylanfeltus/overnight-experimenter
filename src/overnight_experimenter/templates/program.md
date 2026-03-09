# Experiment Program

## Objective

Optimize the landing page copy and layout in `workspace/` to maximize conversion rate.

The page is a single HTML file (`workspace/index.html`) for a SaaS product. The evaluation
script loads the page in a headless browser, runs a simulated user session, and returns a
conversion score between 0.0 and 1.0.

## Constraints

- Only modify files inside `workspace/`. Do not modify evaluate.sh or this file.
- Keep the page under 100KB total (HTML + inline CSS/JS).
- Do not add external dependencies, CDN links, or tracking scripts.
- Maintain accessibility: all images need alt text, proper heading hierarchy.
- Do not remove the product name or pricing section.
- Each experiment should make ONE focused change (don't rewrite everything at once).

## Evaluation

`evaluate.sh` runs a headless browser simulation that:
1. Loads the page
2. Simulates user scroll behavior
3. Checks CTA visibility and prominence
4. Scores based on: CTA clarity, above-fold content, load time, readability
5. Outputs a single float score (0.0 - 1.0) on the last line of stdout

Higher scores are better (direction: maximize).

## Strategy Hints

- Start with headline copy — it has the biggest impact on first impressions
- Try different CTA button colors, sizes, and text
- Experiment with social proof placement (testimonials, logos, stats)
- Test different value proposition framings
- Try reducing form fields if there's a signup form
- Whitespace and visual hierarchy matter — don't just change text
