#!/usr/bin/env python3
"""Assemble the Revision v5 MandiGuard Master Study Guide into HTML + PDF.

Inputs  : docs/study_guide_v2_parts/part1_foundations_data.html
          docs/study_guide_v2_parts/part2_method_results.html
          docs/study_guide_v2_parts/part3_literature_defense.html
Outputs : docs/MandiGuard_Master_Study_Guide.html
          docs/MandiGuard_Master_Study_Guide.pdf

Builds cleanly from Revision v5 fragments referencing `figures/rev_fig1..4*.png`.
Enforces zero backticks, zero markdown `**`, zero raw LaTeX leaks, zero legacy Stage-I/II claims.
"""

from __future__ import annotations

import base64
import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_revision_v5_deliverables import (
    FORBIDDEN_LATEX_LEAKS,
    FORBIDDEN_LEGACY_STRINGS,
    b64_img,
    markdown_to_html_body,
    render_pdf,
)

PARTS_DIR = ROOT / "docs" / "study_guide_v2_parts"
FIG_DIR = ROOT / "figures"
HTML_OUT = ROOT / "docs" / "MandiGuard_Master_Study_Guide.html"
PDF_OUT = ROOT / "docs" / "MandiGuard_Master_Study_Guide.pdf"

PARTS = [
    "part1_foundations_data.html",
    "part2_method_results.html",
    "part3_literature_defense.html",
]
FIGS = {
    "{RFIG1}": "rev_fig1_risk_coverage_ci.png",
    "{RFIG2}": "rev_fig2_ablations_and_crops.png",
    "{RFIG3}": "rev_fig3_sensitivity_tornado_and_missing.png",
    "{RFIG4}": "rev_fig4_settlement_and_hp_apple.png",
}
BANNED = re.compile(
    r"\b(crushed|crushes|knockout|undeniable|provably superior|massive|shockingly|catastrophic|blazing|jackpot|"
    r"surge|surges|plunges|plunging|slash|slashes|huge|revolutionary|groundbreaking)\b|100% verified|100% authentic",
    re.I,
)

CSS = """
@page { size: A4; margin: 13mm 13mm 15mm 13mm; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
       font-size: 9.8pt; line-height: 1.48; color: #1f2937; margin: 0; max-width: 184mm; margin: 0 auto; }
h1 { font-size: 17pt; color: #0b3b5c; border-bottom: 3px solid #0b3b5c; padding-bottom: 4px; margin: 0 0 8px 0; }
h2 { font-size: 12.2pt; color: #0e5a7a; border-left: 5px solid #0ea5e9; padding-left: 8px; margin: 14px 0 6px 0;
     break-after: avoid; page-break-after: avoid; }
h3 { font-size: 10.4pt; color: #1e3a5f; margin: 10px 0 4px 0; break-after: avoid; page-break-after: avoid; }
p { margin: 0 0 6px 0; }
ul, ol { margin: 3px 0 7px 0; padding-left: 20px; }
li { margin-bottom: 3px; }
b, strong { color: #0f172a; }
code { font-family: Menlo, Consolas, monospace; font-size: 8.4pt; background: #f1f5f9; border: 1px solid #e2e8f0;
       border-radius: 3px; padding: 0 3px; }
.pb { break-before: page; page-break-before: always; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 10px 0; font-size: 8.1pt; }
tr { break-inside: avoid; page-break-inside: avoid; }
th { background: #0b3b5c; color: #fff; padding: 4.5px 5.5px; text-align: left; font-weight: 600; }
td { border: 1px solid #cbd5e1; padding: 3.8px 5.5px; vertical-align: top; }
tr:nth-child(even) td { background: #f8fafc; }
.worked-box, .note-box, .box { border-radius: 7px; padding: 8px 11px; margin: 8px 0 10px 0; break-inside: avoid; border: 1.5px solid #0284c7; background: #f0f9ff; }
.key { background: #eff6ff; border-color: #3b82f6; }
.think { background: #fefce8; border-color: #eab308; }
.eq-box { font-family: Georgia, serif; font-size: 10pt; background: #f8fafc; border-left: 3.5px solid #0b3b5c; padding: 7px 10px; margin: 7px 0; text-align: center; break-inside: avoid; }
.frac { display: inline-flex; flex-direction: column; align-items: center; vertical-align: middle; margin: 0 2px; font-size: 0.9em; line-height: 1.1; }
.frac .num { border-bottom: 1px solid #1a202c; padding: 0 3px 1px 3px; }
.frac .den { padding: 1px 3px 0 3px; }
.cover { border: 3px solid #0b3b5c; border-radius: 12px; padding: 20px 24px; margin-top: 6mm;
         background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 60%, #ecfdf5 100%); }
.cover h1 { border: none; font-size: 23pt; margin-bottom: 4px; }
.cover .sub { font-size: 11.2pt; color: #0e5a7a; margin-bottom: 10px; }
.pill { display: inline-block; background: #0b3b5c; color: #fff; border-radius: 12px; padding: 2px 10px;
        font-size: 8.5pt; margin: 2px 3px 2px 0; }
.flow { display: flex; flex-wrap: wrap; align-items: stretch; gap: 4px; margin: 8px 0 10px 0; break-inside: avoid; }
.fbox { flex: 1 1 0; min-width: 72px; border: 1.6px solid; border-radius: 7px; padding: 6px; text-align: center;
        font-size: 8.4pt; line-height: 1.3; display: flex; flex-direction: column; justify-content: center; }
.farrow { display: flex; align-items: center; font-size: 14pt; color: #64748b; padding: 0 1px; }
.c1 { background: #e0f2fe; border-color: #0284c7; } .c2 { background: #dcfce7; border-color: #16a34a; }
.c3 { background: #fef9c3; border-color: #ca8a04; } .c4 { background: #fee2e2; border-color: #dc2626; }
.c5 { background: #ede9fe; border-color: #7c3aed; }
figure.fig-card { text-align: center; margin: 8px 0 12px 0; break-inside: avoid; border: 1px solid #cbd5e1; border-radius: 5px; padding: 6px; }
figure.fig-card img { max-width: 100%; max-height: 108mm; }
figure.fig-card figcaption { font-size: 8.2pt; color: #475569; margin-top: 3px; text-align: left; }
.small { font-size: 8.4pt; color: #475569; }
"""

COVER = """
<div class="cover">
  <h1>MandiGuard &mdash; Master Study Guide (Revision v6)</h1>
  <div class="sub">Aditya Sharma &mdash; Shoolini University, Solan, Himachal Pradesh, India &bull; Zero-Parameter Dispatch Filtering (Safe_EV_Sunk_m0, Safe_EV_Phys_m0 &amp; RT_2F_Min_m0)<br/>
  Explained from first principles so a motivated student can verify, present, and defend every equation and number</div>
  <span class="pill">Data Provenance &amp; Cleaning</span><span class="pill">Timing Firewall (&le; t&minus;1)</span>
  <span class="pill">Sequential &amp; Realized ERA5 Settlement</span><span class="pill">Zero-Parameter Rules</span>
  <span class="pill">R = 5,000 Cluster Bootstrap</span><span class="pill">Break-Even &amp; Open-MAR Bounds</span>
  <span class="pill">49 Verified Citations</span><span class="pill">Viva Defense Bank</span>
  <div class="box key" style="margin-top:12px;"><strong>The thesis in four sentences:</strong>
  Online AGMARKNET spreads tempt dispatchers, yet chasing top lagged spreads (<code>B1_lagged_screen</code>) across 58,676 test episodes loses money on 45.21% of dispatches (worst-10% <code>ES10 &minus;&#8377;641.26/qtl</code>, with 28.98% turning back sequentially). Earlier black-box trees, weather leaks, and tuned <code>kappa* = 5.0</code> thresholds were audited and retired. Replacing them with zero-parameter <code>Safe_EV_Sunk_m0</code> (weekday reporting probability &times; 1-SD safe spread exceeding sunk freight), settlement-matched <code>Safe_EV_Phys_m0</code> (1.5F), and Class-8 <code>RT_2F_Min_m0</code> lowers losses to 14.93% and strengthens <code>ES10</code> to &minus;&#8377;344.09/qtl (+&#8377;181.17 vs road baseline <code>B2_age_matched</code>, two-sided Holm <code>p = 0.0024</code> at <code>R = 5,000</code> across all 3 clusterings, 1/2/4-week blocks, strict 2024-only 171 markets, realized ERA5 settlement, and all 6 states). These rules act transparently as an upstream 6 a.m. alert filter ahead of live <em>arhtiya</em> phone confirmation while disclosing exact silent-market break-even (+&#8377;328.37/qtl above turn-back; 23.79% Open-MAR share), Open-MAR mean bounds, 41.38% HP apple conditional losses, and blocked future Gate J.</div>
</div>

<h2>Three-Part Roadmap</h2>
<div class="flow">
  <div class="fbox c1"><strong>Part 1</strong><span>Problem, Epistemic Table 1, Data Funnel, Firewall &amp; Settlement</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c2"><strong>Part 2</strong><span>Zero-Parameter Formulas, Results, 171-Mkt / ERA5 / Break-Even</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c3"><strong>Part 3</strong><span>49 Citations, Novelty Overlap, Limitations, Audit &amp; Viva Bank</span></div>
</div>
"""

CLOSING = """
<div class="pb"></div>
<h1>Closing Verification Note (Revision v6)</h1>
<div class="box key">
  Every metric in this study guide traces directly to committed outputs in <code>revision/results/</code> regenerated via <code>make reproduce</code> (clean-clone discrepancy <code>0.0</code> across 31 CSV tables, independent <code>A16</code> parity <code>&#8377;0.00</code>, <code>0</code> untraceable numbers across all <code>23/23</code> active markdown documents, <code>36/36</code> pytest passing, <code>49/49</code> verified citations). See <code>final/READINESS.md</code> for the three external items: supervisor review, venue layout check, and prospective live FPO piloting.
</div>
<p class="small">Canonical Sources: paper/manuscript.md, final/SIMPLIFIED_DESIGN.md, final/DIFFICULTY.md, final/NOVELTY_V2.md, final/AUDIT_V4.md, final/LIMITATIONS.md, final/VIVA_QA.md. Rebuild cleanly with: python3 scripts/build_master_study_guide_pdf.py</p>
"""


def _strip_h1(md: str) -> str:
    lines = md.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).lstrip()
    return md


def regenerate_parts() -> None:
    """Regenerate docs/study_guide_v2_parts/part1..3.html from canonical Revision v6 markdown sources."""
    PARTS_DIR.mkdir(parents=True, exist_ok=True)
    bib = (ROOT / "paper" / "references.bib").read_text(encoding="utf-8")
    bib_keys = set(re.findall(r"@\w+\{([^,\s]+),", bib))
    ms = (ROOT / "paper" / "manuscript.md").read_text(encoding="utf-8")

    s1_start = ms.index("## 1. Three Research Questions")
    s33_start = ms.index("### 3.3 Equal-Menu Baselines")
    s5_start = ms.index("## 5. Related Work")

    ms_part1 = ms[s1_start:s33_start].strip()
    ms_part2 = ms[s33_start:s5_start].strip()
    ms_part3 = ms[s5_start:].strip()

    diff_md = _strip_h1((ROOT / "final" / "DIFFICULTY.md").read_text(encoding="utf-8"))
    nov_md = _strip_h1((ROOT / "final" / "NOVELTY_V2.md").read_text(encoding="utf-8"))
    viva_md = _strip_h1((ROOT / "final" / "VIVA_QA.md").read_text(encoding="utf-8"))

    p1_html = (
        '<div class="pb"></div>\n'
        "<h2>Part 1: Problem, Epistemic Table 1, Data Provenance &amp; Settlement Physics</h2>\n"
        + markdown_to_html_body(ms_part1, bib_keys=bib_keys, base_dir=ROOT / "paper")
    )
    p2_raw = (
        '<div class="pb"></div>\n'
        "<h2>Part 2: Zero-Parameter Dispatch Rules, Experiments, 171-Mkt / ERA5 &amp; Break-Even</h2>\n"
        + markdown_to_html_body(diff_md, bib_keys=bib_keys, base_dir=ROOT / "final")
        + "\n<hr>\n"
        + markdown_to_html_body(ms_part2, bib_keys=bib_keys, base_dir=ROOT / "paper")
    )
    for ph, fn in FIGS.items():
        p2_raw = p2_raw.replace(b64_img(fn), ph)
    p3_html = (
        '<div class="pb"></div>\n'
        "<h2>Part 3: Related Work (49 Citations), Limitations, Novelty Overlap &amp; Viva Defense Bank</h2>\n"
        + markdown_to_html_body(ms_part3, bib_keys=bib_keys, base_dir=ROOT / "paper")
        + "\n<hr>\n"
        + markdown_to_html_body(nov_md, bib_keys=bib_keys, base_dir=ROOT / "final")
        + "\n<hr>\n"
        + markdown_to_html_body(viva_md, bib_keys=bib_keys, base_dir=ROOT / "final")
    )

    (PARTS_DIR / "part1_foundations_data.html").write_text(p1_html, encoding="utf-8")
    (PARTS_DIR / "part2_method_results.html").write_text(p2_raw, encoding="utf-8")
    (PARTS_DIR / "part3_literature_defense.html").write_text(p3_html, encoding="utf-8")


def main() -> None:
    regenerate_parts()
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
    unknown = set(re.findall(r"\{[A-Z0-9]+\}", body)) - set(FIGS)
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

    doc_html = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><title>MandiGuard - Master Study Guide (Revision v6)</title>'
        "<style>" + CSS + "</style></head><body>" + body + "</body></html>"
    )
    HTML_OUT.write_text(doc_html, encoding="utf-8")
    render_pdf(HTML_OUT, PDF_OUT)

    txt = "\n".join((pg.extract_text() or "") for pg in PdfReader(str(PDF_OUT)).pages)
    for req in ("Safe_EV_Sunk_m0", "RT_2F_Min_m0", "58,676", "344.09"):
        assert req in txt, f"Missing expected Revision v5 token `{req}` in {PDF_OUT.name}"
    for bad in FORBIDDEN_LATEX_LEAKS + FORBIDDEN_LEGACY_STRINGS + ["92.77", "66.22"]:
        assert bad not in txt, f"Forbidden string `{bad}` found in {PDF_OUT.name}"
    print(f"Wrote {HTML_OUT.name} & {PDF_OUT.name} ({len(PdfReader(str(PDF_OUT)).pages)} pages, clean)")


if __name__ == "__main__":
    main()
