#!/usr/bin/env python3
"""
Overnight Experimenter — Report Generator

Generates a self-contained HTML report from experiments.jsonl with:
- Score over time chart (inline SVG)
- Experiment table
- Summary statistics
"""

import json
import html
from datetime import datetime
from pathlib import Path


def load_experiments(experiment_dir: Path) -> list[dict]:
    """Load experiments from experiments.jsonl."""
    jsonl = experiment_dir / "experiments.jsonl"
    if not jsonl.exists():
        return []
    experiments = []
    for line in jsonl.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                experiments.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return experiments


def generate_svg_chart(experiments: list[dict], width: int = 800, height: int = 300) -> str:
    """Generate an inline SVG chart of score over time."""
    scored = [e for e in experiments if e.get("score") is not None]
    if not scored:
        return '<p style="color:#888;">No scored experiments yet.</p>'

    scores = [e["score"] for e in scored]
    min_score = min(scores)
    max_score = max(scores)
    score_range = max_score - min_score if max_score != min_score else 1.0

    padding = 60
    chart_w = width - padding * 2
    chart_h = height - padding * 2

    n = len(scored)
    x_step = chart_w / max(n - 1, 1)

    def scale_y(score: float) -> float:
        return padding + chart_h - ((score - min_score) / score_range) * chart_h

    def scale_x(i: int) -> float:
        return padding + i * x_step

    lines = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
             f'style="width:100%;max-width:{width}px;height:auto;">']

    # Background
    lines.append(f'<rect width="{width}" height="{height}" fill="#1a1a2e" rx="8"/>')

    # Grid lines
    grid_lines = 5
    for i in range(grid_lines + 1):
        y = padding + (chart_h / grid_lines) * i
        val = max_score - (score_range / grid_lines) * i
        lines.append(f'<line x1="{padding}" y1="{y}" x2="{width-padding}" y2="{y}" '
                     f'stroke="#333" stroke-width="1" stroke-dasharray="4,4"/>')
        lines.append(f'<text x="{padding-8}" y="{y+4}" fill="#888" font-size="11" '
                     f'text-anchor="end" font-family="monospace">{val:.2f}</text>')

    # Score line
    points = []
    for i, e in enumerate(scored):
        x = scale_x(i)
        y = scale_y(e["score"])
        points.append(f"{x},{y}")

    if len(points) > 1:
        lines.append(f'<polyline points="{" ".join(points)}" fill="none" '
                     f'stroke="#888" stroke-width="1.5" opacity="0.5"/>')

    # Best score line
    best_points = []
    for i, e in enumerate(scored):
        if e.get("best_score") is not None:
            x = scale_x(i)
            y = scale_y(e["best_score"])
            best_points.append(f"{x},{y}")

    if len(best_points) > 1:
        lines.append(f'<polyline points="{" ".join(best_points)}" fill="none" '
                     f'stroke="#00d4aa" stroke-width="2"/>')

    # Dots
    for i, e in enumerate(scored):
        x = scale_x(i)
        y = scale_y(e["score"])
        color = "#00d4aa" if e.get("improved") else "#ff6b6b"
        lines.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}" '
                     f'stroke="#1a1a2e" stroke-width="1.5">')
        lines.append(f'<title>#{e["experiment_id"]}: {e["score"]}</title>')
        lines.append('</circle>')

    # Axis labels
    lines.append(f'<text x="{width/2}" y="{height-8}" fill="#888" font-size="12" '
                 f'text-anchor="middle" font-family="monospace">experiment</text>')
    lines.append(f'<text x="12" y="{height/2}" fill="#888" font-size="12" '
                 f'text-anchor="middle" font-family="monospace" '
                 f'transform="rotate(-90,12,{height/2})">score</text>')

    # Legend
    lines.append(f'<circle cx="{width-180}" cy="20" r="4" fill="#00d4aa"/>')
    lines.append(f'<text x="{width-170}" y="24" fill="#888" font-size="11" '
                 f'font-family="monospace">improved</text>')
    lines.append(f'<circle cx="{width-100}" cy="20" r="4" fill="#ff6b6b"/>')
    lines.append(f'<text x="{width-90}" y="24" fill="#888" font-size="11" '
                 f'font-family="monospace">no change</text>')

    lines.append('</svg>')
    return "\n".join(lines)


def generate_report(experiment_dir: Path) -> Path:
    """Generate an HTML report from experiments.jsonl. Returns path to the report."""
    experiments = load_experiments(experiment_dir)
    report_path = experiment_dir / "report.html"

    if not experiments:
        report_path.write_text("<html><body><h1>No experiments yet</h1></body></html>")
        return report_path

    # Summary stats
    scored = [e for e in experiments if e.get("score") is not None]
    total = len(experiments)
    improvements = sum(1 for e in experiments if e.get("improved"))
    best_score = scored[-1].get("best_score") if scored else None
    total_duration = sum(e.get("duration_s", 0) for e in experiments)

    first_ts = experiments[0].get("timestamp", "")
    last_ts = experiments[-1].get("timestamp", "")

    chart_svg = generate_svg_chart(experiments)

    # Build table rows
    table_rows = []
    for e in experiments:
        eid = e.get("experiment_id", "?")
        ts = e.get("timestamp", "")[:19]
        desc = html.escape(str(e.get("description", "")))[:120]
        score = e.get("score")
        score_str = f"{score}" if score is not None else "error"
        improved = e.get("improved", False)
        status = '<span class="improved">improved</span>' if improved else '<span class="noimprove">—</span>'
        dur = e.get("duration_s", 0)

        table_rows.append(f"""<tr>
            <td>#{eid}</td>
            <td>{ts}</td>
            <td class="desc">{desc}</td>
            <td>{score_str}</td>
            <td>{status}</td>
            <td>{dur:.0f}s</td>
        </tr>""")

    report_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Experiment Report — {html.escape(experiment_dir.name)}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    background: #0d0d1a;
    color: #e0e0e0;
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    padding: 2rem;
    max-width: 1000px;
    margin: 0 auto;
}}
h1 {{
    color: #00d4aa;
    font-size: 1.4rem;
    margin-bottom: 0.5rem;
    font-weight: 500;
}}
h2 {{
    color: #888;
    font-size: 1rem;
    margin: 2rem 0 1rem;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}}
.stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
}}
.stat {{
    background: #1a1a2e;
    padding: 1rem 1.2rem;
    border-radius: 8px;
    border: 1px solid #2a2a4a;
}}
.stat-value {{
    font-size: 1.5rem;
    color: #00d4aa;
    font-weight: 600;
}}
.stat-label {{
    font-size: 0.75rem;
    color: #888;
    margin-top: 0.3rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
.chart-container {{
    background: #1a1a2e;
    border-radius: 8px;
    border: 1px solid #2a2a4a;
    padding: 1.5rem;
    margin: 1.5rem 0;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}}
th {{
    text-align: left;
    padding: 0.6rem 0.8rem;
    border-bottom: 2px solid #2a2a4a;
    color: #888;
    font-weight: 400;
    text-transform: uppercase;
    font-size: 0.7rem;
    letter-spacing: 0.05em;
}}
td {{
    padding: 0.5rem 0.8rem;
    border-bottom: 1px solid #1a1a2e;
}}
tr:hover {{
    background: #1a1a2e;
}}
.desc {{
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}
.improved {{
    color: #00d4aa;
    font-weight: 600;
}}
.noimprove {{
    color: #555;
}}
.footer {{
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid #2a2a4a;
    color: #555;
    font-size: 0.75rem;
}}
</style>
</head>
<body>
<h1>overnight experimenter</h1>
<p style="color:#888;font-size:0.85rem;">{html.escape(experiment_dir.name)} &mdash; {first_ts[:10]} to {last_ts[:10]}</p>

<div class="stats">
    <div class="stat">
        <div class="stat-value">{total}</div>
        <div class="stat-label">experiments</div>
    </div>
    <div class="stat">
        <div class="stat-value">{improvements}</div>
        <div class="stat-label">improvements</div>
    </div>
    <div class="stat">
        <div class="stat-value">{best_score if best_score is not None else '—'}</div>
        <div class="stat-label">best score</div>
    </div>
    <div class="stat">
        <div class="stat-value">{total_duration/3600:.1f}h</div>
        <div class="stat-label">elapsed</div>
    </div>
</div>

<h2>Score Over Time</h2>
<div class="chart-container">
{chart_svg}
</div>

<h2>Experiments</h2>
<table>
<thead>
<tr>
    <th>#</th>
    <th>Time</th>
    <th>Description</th>
    <th>Score</th>
    <th>Status</th>
    <th>Duration</th>
</tr>
</thead>
<tbody>
{"".join(table_rows)}
</tbody>
</table>

<div class="footer">
    Generated by Overnight Experimenter &mdash; {datetime.now().strftime("%Y-%m-%d %H:%M")}
</div>
</body>
</html>"""

    report_path.write_text(report_html)
    return report_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate experiment report")
    parser.add_argument("experiment_dir", type=Path, help="Path to experiment directory")
    args = parser.parse_args()
    path = generate_report(args.experiment_dir)
    print(f"Report generated: {path}")


if __name__ == "__main__":
    main()
