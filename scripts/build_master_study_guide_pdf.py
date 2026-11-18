#!/usr/bin/env python3
"""Assemble the 3-agent MandiGuard Master Study Guide into HTML + PDF.

Inputs  : docs/study_guide_v2_parts/part1_foundations_data.html
          docs/study_guide_v2_parts/part2_method_results.html
          docs/study_guide_v2_parts/part3_literature_defense.html
Outputs : docs/MandiGuard_Master_Study_Guide.html
          docs/MandiGuard_Master_Study_Guide.pdf
The script fails loudly if a part is missing, if an unknown figure placeholder
remains, or if markdown residue / banned hype words are found.
"""

from __future__ import annotations

import base64
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTS_DIR = ROOT / "docs" / "study_guide_v2_parts"
FIG_DIR = ROOT / "figures"
HTML_OUT = ROOT / "docs" / "MandiGuard_Master_Study_Guide.html"
PDF_OUT = ROOT / "docs" / "MandiGuard_Master_Study_Guide.pdf"
CHROME_BIN = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

PARTS = [
    "part1_foundations_data.html",
    "part2_method_results.html",
    "part3_literature_defense.html",
]
FIGS = {
    "{FIG1}": "fig1_phantom_arbitrage_anatomy.png",
    "{FIG2}": "fig2_main_policy_comparison.png",
    "{FIG3}": "fig3_tool_ablation_and_monsoon_heat.png",
    "{FIG4}": "fig4_tool_budget_pareto.png",
    "{FIG5}": "fig5_hp_apple_grade_traps.png",
    "{FIG6}": "fig6_sensitivity_and_govt_fees.png",
    "{FIG7}": "fig7_decade_2017_2026_evolution.png",
    "{FIG8}": "fig9_mechanistic_autopsy_and_uncensored_crc.png",
    "{FIGA1}": "fig8_zerocloud_fpo_and_modern_ai.png",
}
BANNED = re.compile(
    r"\b(crushed|knockout|undeniable|provably superior|massive|shockingly|catastrophic|blazing|jackpot|"
    r"surge|surges|plunges|plunging|slash|slashes|huge|revolutionary|groundbreaking)\b|100% verified|100% authentic",
    re.I,
)

CSS = """
@page { size: A4; margin: 13mm 13mm 15mm 13mm; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
       font-size: 10.2pt; line-height: 1.5; color: #1f2937; margin: 0; }
h1 { font-size: 18pt; color: #0b3b5c; border-bottom: 3px solid #0b3b5c; padding-bottom: 4px; margin: 0 0 8px 0; }
h2 { font-size: 13pt; color: #0e5a7a; border-left: 5px solid #0ea5e9; padding-left: 8px; margin: 16px 0 6px 0;
     break-after: avoid; page-break-after: avoid; }
h3 { font-size: 11pt; color: #1e3a5f; margin: 12px 0 4px 0; break-after: avoid; page-break-after: avoid; }
p { margin: 0 0 7px 0; }
ul, ol { margin: 3px 0 8px 0; padding-left: 20px; }
li { margin-bottom: 3px; }
b, strong { color: #0f172a; }
code { font-family: Menlo, Consolas, monospace; font-size: 8.8pt; background: #f1f5f9; border: 1px solid #e2e8f0;
       border-radius: 3px; padding: 0 3px; }
.pb { break-before: page; page-break-before: always; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 10px 0; font-size: 8.9pt; }
tr { break-inside: avoid; page-break-inside: avoid; }
th { background: #0b3b5c; color: #fff; padding: 5px 6px; text-align: left; font-weight: 600; }
th b, th strong { color: #ffffff; }
th code { background: rgba(255, 255, 255, 0.16); color: #ffffff; border-color: rgba(255, 255, 255, 0.35); }
td { border: 1px solid #cbd5e1; padding: 4px 6px; vertical-align: top; }
tr:nth-child(even) td { background: #f8fafc; }
tr.hl td { background: #ecfdf5 !important; font-weight: 600; }
.num { text-align: right; white-space: nowrap; }
.box { border-radius: 7px; padding: 8px 11px; margin: 8px 0 10px 0; break-inside: avoid; border: 1.5px solid; }
.box .t { font-weight: 700; margin-bottom: 3px; display: block; }
.think { background: #fefce8; border-color: #eab308; }  .think .t { color: #854d0e; }
.key { background: #eff6ff; border-color: #3b82f6; }    .key .t { color: #1e40af; }
.viva { background: #f0fdf4; border-color: #22c55e; }   .viva .t { color: #166534; }
.warn { background: #fef2f2; border-color: #ef4444; }   .warn .t { color: #991b1b; }
.math { background: #faf5ff; border-color: #a855f7; }   .math .t { color: #6b21a8; }
.deep { background: #f8fafc; border-color: #64748b; }   .deep .t { color: #334155; }
.formula { font-family: Menlo, Consolas, monospace; font-size: 9.3pt; background: #ffffff; border: 1px dashed #a855f7;
           padding: 6px 8px; border-radius: 5px; margin: 5px 0; display: block; white-space: pre-wrap; }
.cover { border: 3px solid #0b3b5c; border-radius: 12px; padding: 24px 28px; margin-top: 8mm;
         background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 60%, #ecfdf5 100%); }
.cover h1 { border: none; font-size: 25pt; margin-bottom: 4px; }
.cover .sub { font-size: 12.5pt; color: #0e5a7a; margin-bottom: 12px; }
.pill { display: inline-block; background: #0b3b5c; color: #fff; border-radius: 12px; padding: 2px 10px;
        font-size: 8.8pt; margin: 2px 3px 2px 0; }
.flow { display: flex; flex-wrap: wrap; align-items: stretch; gap: 3px; margin: 8px 0 10px 0; break-inside: avoid; }
.fbox { flex: 1 1 0; min-width: 72px; border: 1.6px solid; border-radius: 7px; padding: 6px 6px; text-align: center;
        font-size: 8.5pt; line-height: 1.3; display: flex; flex-direction: column; justify-content: center; }
.fbox b { font-size: 8.9pt; margin-bottom: 2px; display: block; }
.fbox span { color: #334155; }
.farrow { display: flex; align-items: center; font-size: 15pt; color: #64748b; padding: 0 1px; }
.c1 { background: #e0f2fe; border-color: #0284c7; } .c2 { background: #dcfce7; border-color: #16a34a; }
.c3 { background: #fef9c3; border-color: #ca8a04; } .c4 { background: #fee2e2; border-color: #dc2626; }
.c5 { background: #ede9fe; border-color: #7c3aed; } .c6 { background: #f1f5f9; border-color: #475569; }
.gates { margin: 8px 0 12px 0; break-inside: avoid; }
.gate-row { display: flex; align-items: center; gap: 6px; }
.gate { flex: 0 0 56%; background: #e0f2fe; border: 1.8px solid #0284c7; border-radius: 7px; padding: 6px 9px;
        font-weight: 700; font-size: 9.2pt; }
.gate span { display: block; font-weight: 400; font-size: 8.6pt; color: #334155; }
.gate.final-yes { background: #dcfce7; border-color: #16a34a; }
.gate-fail-arrow { flex: 0 0 9%; color: #dc2626; font-weight: 700; font-size: 8.5pt; text-align: center; }
.gate-fail { flex: 1; background: #fee2e2; border: 1.6px solid #dc2626; border-radius: 7px; padding: 5px 8px; font-size: 8.6pt; }
.gate-down { margin: 1px 0 1px 18%; color: #16a34a; font-weight: 700; font-size: 8.6pt; }
.timeline { display: flex; margin: 8px 0 10px 0; break-inside: avoid; border-radius: 7px; overflow: hidden; border: 1.5px solid #334155; }
.timeline div { padding: 7px 6px; font-size: 8.5pt; text-align: center; line-height: 1.3; }
.figure { text-align: center; margin: 8px 0 12px 0; break-inside: avoid; }
.figure img { max-width: 100%; max-height: 110mm; border: 1px solid #cbd5e1; border-radius: 4px; }
.figure .cap { font-size: 8.6pt; color: #475569; margin-top: 3px; text-align: left; }
.qa { border-left: 4px solid #22c55e; background: #f8fafc; padding: 5px 9px; margin: 6px 0; break-inside: avoid; }
.qa.follow { border-left-color: #f59e0b; background: #fffbeb; margin-left: 18px; }
.qa .q { font-weight: 700; color: #0f172a; }
.qa .a { margin-top: 2px; }
.slide { border: 1.5px solid #0b3b5c; border-radius: 7px; margin: 7px 0; break-inside: avoid; }
.slide .sh { background: #0b3b5c; color: #fff; padding: 4px 9px; font-weight: 700; font-size: 9.6pt; }
.slide .sb { padding: 6px 10px; font-size: 9.1pt; }
.paper { border: 1.6px solid #0e5a7a; border-radius: 8px; padding: 8px 11px; margin: 10px 0; background: #fbfdff; }
.paper .pt { font-weight: 700; color: #0b3b5c; font-size: 10.6pt; }
.paper .pm { font-size: 8.6pt; color: #475569; margin-bottom: 5px; }
.toc li { margin-bottom: 2px; }
.small { font-size: 8.6pt; color: #475569; }
"""

COVER = """
<div class="cover">
  <h1>MandiGuard &mdash; Master Study Guide</h1>
  <div class="sub">Phantom Spatial Arbitrage in Indian Mandis &middot; Stage I (MandiGuard, pre-registered) + Stage II (MandiGuard-CRC, post-diagnostic)<br/>
  Taught from first principles so a Class 10&ndash;12 student can understand, present and defend every step</div>
  <span class="pill">Why this topic</span><span class="pill">First principles</span><span class="pill">Data collection</span>
  <span class="pill">Data validation</span><span class="pill">Method</span><span class="pill">Every experiment</span>
  <span class="pill">Stage II autopsy &amp; fix</span><span class="pill">Key papers in depth</span><span class="pill">Novelty</span>
  <span class="pill">Limitations</span><span class="pill">Synopsis masterclass</span><span class="pill">Viva bank</span>
  <div class="box key" style="margin-top:12px;"><span class="t">The whole thesis in four sentences</span>
  A mobile screen may show that a mandi 200 km away pays &#8377;600 more per quintal, but closed gates, missing varieties, diesel, fees and heat-rot
  make most of that gain disappear &mdash; a <b>phantom</b>. Using public government price data (69,526 real decision cases across 6 states and 4 crops),
  we measured how large the phantom is. <b>Stage I (MandiGuard)</b> is a transparent, pre-registered checklist that verifies cheap facts first, keeps an
  80% safety cushion and is allowed to say &ldquo;stay home&rdquo;; it beat naive chasing and point-forecast ML but only tied a strong simple rule on average.
  <b>Stage II (MandiGuard-CRC)</b> diagnosed three causes of that tie, fixed them, was tuned on validation data only, and then beat the strong rule on unseen months.</div>
  <div class="box think"><span class="t">How this guide was made and how to read it</span>
  Three specialist writing agents each produced one part (foundations &amp; data; method, experiments &amp; Stage II; literature &amp; viva defence), working from the
  thesis manuscript, result files and code. The coordinator assembled the parts, and an independent reviewer checked numbers against the source files.
  Read Part A first (Chapters 1&ndash;5), then Part B (6&ndash;10), then Part C (11&ndash;15). Box colours: yellow = intuition, blue = key facts,
  purple = maths, green = what to say in the viva, red = traps and limits, grey = go deeper.</div>
</div>

<h2>Roadmap: how every chapter connects</h2>
<div class="flow">
  <div class="fbox c4"><b>Ch 1</b><span>Problem &amp; why this topic</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c3"><b>Ch 2</b><span>First principles</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c1"><b>Ch 3</b><span>Data collection</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c2"><b>Ch 4</b><span>Validation &amp; no-leakage</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c1"><b>Ch 5</b><span>Episodes &amp; scoring</span></div>
</div>
<div class="flow">
  <div class="fbox c5"><b>Ch 6</b><span>Stage I method</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c6"><b>Ch 7</b><span>Fair testing design</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c2"><b>Ch 8</b><span>Results, every experiment</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c5"><b>Ch 9</b><span>Stage II autopsy &amp; CRC</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c6"><b>Ch 10</b><span>Appendix illustrations</span></div>
</div>
<div class="flow">
  <div class="fbox c1"><b>Ch 11</b><span>Key papers in depth</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c3"><b>Ch 12</b><span>Gap &amp; novelty</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c4"><b>Ch 13</b><span>Limitations &amp; future</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c5"><b>Ch 14</b><span>Synopsis masterclass</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c2"><b>Ch 15</b><span>Viva bank</span></div>
</div>
<div class="box key"><span class="t">The single logical chain to memorise</span>
Screen prices mislead &rarr; we measured by how much (Exp 1) &rarr; prior work predicts prices but does not check whether you can actually sell &rarr; we built a
verify-first checklist with a safety cushion and a stay-home option (Stage I) &rarr; tested it fairly on unseen months with hypotheses written in advance &rarr;
it beat naive chasing and point-ML but tied a strong simple rule on average &rarr; we investigated why (Exp 16) &rarr; fixed three causes (Exp 17) &rarr;
the fix beat the strong rule on unseen data &rarr; we state clearly what is still assumed rather than measured.</div>
"""

CLOSING = """
<div class="pb"></div>
<h1>Closing Note</h1>
<div class="box key"><span class="t">The final message</span>
Information is free, but information is not money. Verified, cautious decisions &mdash; including the discipline to say &ldquo;stay home&rdquo; &mdash; protect a
small farmer. This thesis measured the problem on public data, built a transparent solution, tested it fairly with pre-registered hypotheses, reported where
it fell short, diagnosed why, and fixed what it could, while stating clearly what still needs real-world proof.</div>
<p class="small">Sources: paper/manuscript.md, results/*.csv, FINDINGS.md, EXPERIMENT_REGISTRY.csv, research/literature_matrix.md, paper/references.bib and src/ in this
repository. Items marked &ldquo;Illustration&rdquo; are teaching examples, not research results. Rebuild with: python3 scripts/build_master_study_guide_pdf.py</p>
"""


def main() -> None:
    fragments = []
    for name in PARTS:
        p = PARTS_DIR / name
        if not p.exists():
            sys.exit(f"Missing part: {p}")
        txt = p.read_text(encoding="utf-8")
        if re.search(r"<\s*(html|head|body|style)\b", txt, re.I):
            sys.exit(f"{name} contains document-level tags; must be a fragment")
        fragments.append(txt)
    body = COVER + "".join(fragments) + CLOSING

    problems = []
    if "`" in body:
        problems.append("backtick found")
    if "**" in body:
        problems.append("markdown ** found")
    hits = sorted(set(m.group(0).lower() for m in BANNED.finditer(body)))
    if hits:
        problems.append(f"banned words: {hits}")
    unknown = set(re.findall(r"\{FIG[A-Z0-9]+\}", body)) - set(FIGS)
    if unknown:
        problems.append(f"unknown placeholders: {unknown}")
    for ph in FIGS:
        n = body.count(ph)
        if n > 1:
            problems.append(f"{ph} used {n} times")
    if problems:
        sys.exit("QUALITY CHECK FAILED: " + "; ".join(problems))

    for ph, fn in FIGS.items():
        if ph in body:
            data = base64.b64encode((FIG_DIR / fn).read_bytes()).decode("ascii")
            body = body.replace(ph, "data:image/png;base64," + data)

    html = ('<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><title>MandiGuard - Master Study Guide</title>'
            "<style>" + CSS + "</style></head><body>" + body + "</body></html>")
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"Wrote HTML: {HTML_OUT} ({HTML_OUT.stat().st_size / 1e6:.2f} MB)")

    cmd = [str(CHROME_BIN), "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
           f"--print-to-pdf={PDF_OUT}", HTML_OUT.resolve().as_uri()]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not PDF_OUT.exists():
        print(proc.stdout, proc.stderr)
        sys.exit("Chrome PDF generation failed")
    print(f"Wrote PDF: {PDF_OUT} ({PDF_OUT.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
