#!/usr/bin/env python3
"""Build Revision v5 First-Principles & Thesis Defense Handbook HTML + PDF.

Compiles directly from canonical Revision v5 markdown sources:
  - viva/00_career_defense_master_sheet.md
  - paper/12th_class_easy_reading_edition.md
  - final/SIMPLIFIED_DESIGN.md
  - final/DIFFICULTY.md
  - paper/manuscript.md
  - final/NOVELTY_V2.md
  - final/AUDIT_V4.md
  - final/LIMITATIONS.md
  - final/VIVA_QA.md
  - viva/03_spoken_pitches_1m_5m_15m.md

Zero legacy Stage-I/II stale claims, zero hardcoded home paths, portable Chrome PDF.
"""

from __future__ import annotations

import html
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
    PAPER_CSS,
    b64_img,
    markdown_to_html_body,
    render_pdf,
)

DOCS_DIR = ROOT / "docs"
HTML_OUT = DOCS_DIR / "MandiGuard_First_Principles_and_Thesis_Defense_Handbook.html"
PDF_OUT = DOCS_DIR / "MandiGuard_First_Principles_and_Thesis_Defense_Handbook.pdf"

HANDBOOK_EXTRA_CSS = """
.cover {
  border: 2.5px solid #0f4c5c;
  border-radius: 10px;
  padding: 20px 24px;
  margin-bottom: 14px;
  background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 70%, #ecfdf5 100%);
  break-after: page;
}
.cover h1 { border: none; font-size: 21pt; color: #0b2538; margin: 4px 0 8px 0; }
.cover .sub { font-size: 10.5pt; color: #0f4c5c; margin-bottom: 12px; }
.ch-banner {
  background: #0f4c5c;
  color: #ffffff;
  padding: 7px 12px;
  border-radius: 5px;
  margin: 14px 0 8px 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  break-after: avoid;
}
.ch-banner .ch-k { font-size: 7.5pt; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.85; }
.ch-banner .ch-t { font-size: 12pt; font-weight: 700; margin-top: 1px; }
.pb { break-before: page; page-break-before: always; }
.badge-row { margin: 8px 0; }
.badge {
  display: inline-block; background: #0f4c5c; color: #fff;
  font-family: -apple-system, sans-serif; font-size: 8pt; font-weight: 600;
  padding: 2px 9px; border-radius: 10px; margin: 2px 4px 2px 0;
}
"""

CHAPTERS = [
    ("Part 1 • Executive Elevator Summary", "45-Second Core Pitch & Headline Ledger", "viva/00_career_defense_master_sheet.md"),
    ("Part 2 • First-Principles Intuition", "Class-12 Pocket-Calculator Walkthrough", "paper/12th_class_easy_reading_edition.md"),
    ("Part 3 • Difficulty Reduction Audit", "How Complexity Dropped 4.3 → 1.2 / 5 (A15 + A18)", "final/DIFFICULTY.md"),
    ("Part 4 • Simplified Equations", "Zero-Parameter Safe_EV_Sunk_m0 & RT_2F_Min_m0", "final/SIMPLIFIED_DESIGN.md"),
    ("Part 5 • Complete Scientific Paper", "Revision v5 Full Manuscript (N = 58,676 & 88,014)", "paper/manuscript.md"),
    ("Part 6 • Literature & Novelty Defense", "15-Work Overlap Matrix & Surviving Claim (NOVELTY_V2)", "final/NOVELTY_V2.md"),
    ("Part 7 • Cleanroom & Examiner Sign-Off", "A16 Parity (₹0.00) & A17 Post-Remediation Audit (8.7/10)", "final/AUDIT_V4.md"),
    ("Part 8 • Prominent Boundaries (R6 & R7)", "Eight Binding Non-Claims & Open-MAR / Apple Disclosures", "final/LIMITATIONS.md"),
    ("Part 9 • Examiner Viva Bank", "Scripted-Verified Q&A (C2 & R2 Clean)", "final/VIVA_QA.md"),
    ("Part 10 • Oral Defense Scripts", "1-Minute, 5-Minute & 15-Minute Spoken Pitches", "viva/03_spoken_pitches_1m_5m_15m.md"),
]


def _strip_top_h1(md: str) -> str:
    lines = md.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).lstrip()
    return md


def build() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    bib = (ROOT / "paper" / "references.bib").read_text()
    bib_keys = set(re.findall(r"@\w+\{([^,\s]+),", bib))

    cover = """
    <div class="cover">
      <span class="meta-pill">Thesis Defense Compendium &bull; Revision v5 Verified</span>
      <h1>MandiGuard: First-Principles &amp; Thesis Defense Handbook</h1>
      <div class="sub">When Online Mandi Prices Mislead: Zero-Parameter Safe_EV_Sunk_m0 &amp; RT_2F_Min_m0 Across 58,676 Lagged Indian Wholesale Episodes (<code>N = 88,014</code> Unconditional Robustness)</div>
      <div class="badge-row">
        <span class="badge">8.7 / 10 A17 Sign-Off</span>
        <span class="badge">0 Free Parameters</span>
        <span class="badge">4.3 &rarr; 1.2 / 5 Difficulty</span>
        <span class="badge">170&ndash;173 Fixed Clusters</span>
        <span class="badge">Two-Sided Holm p = 0.0040</span>
        <span class="badge">make reproduce &bull; &#8377;0.00 Audit</span>
      </div>
      <div class="worked-box">
        <p><strong>Canonical Scope Notice:</strong> Every metric, equation, cluster count, and figure in this handbook is compiled directly from Revision v5 canonical sources on branch <code>finalization</code>. Stage-I/II ML trees (<code>HistGradientBoostingRegressor</code>), weather leaks (<code>98.64%</code> ERA5 match), unweighted quantile-mean proxies, bare 336-market clusters, and even tuned <code>kappa* = 5.0</code> thresholds have been retired in favor of zero-parameter pocket-calculator formulas verified by <code>make reproduce</code> (<code>0.0</code> clean-clone max diff) and <code>verify_traceability.py</code> (<code>0</code> untraceable numbers).</p>
      </div>
    </div>
    """

    sections = [cover]
    for idx, (kicker, title, rel) in enumerate(CHAPTERS):
        md_raw = (ROOT / rel).read_text(encoding="utf-8")
        # Rewrite relative figure paths cleanly for b64_img (it strips dirs via .name)
        body_html = markdown_to_html_body(_strip_top_h1(md_raw), bib_keys=bib_keys, base_dir=(ROOT / rel).parent)
        pb_cls = ' class="pb"' if idx > 0 else ""
        sections.append(
            f'<section{pb_cls}>'
            f'<div class="ch-banner"><div class="ch-k">{html.escape(kicker)} &bull; Source: {html.escape(rel)}</div>'
            f'<div class="ch-t">{html.escape(title)}</div></div>'
            f'{body_html}'
            f'</section>'
        )

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>MandiGuard First-Principles &amp; Thesis Defense Handbook (Revision v5)</title>
<style>{PAPER_CSS}\n{HANDBOOK_EXTRA_CSS}</style>
</head>
<body>{''.join(sections)}</body>
</html>"""

    HTML_OUT.write_text(full_html, encoding="utf-8")
    render_pdf(HTML_OUT, PDF_OUT)

    txt = "\n".join((pg.extract_text() or "") for pg in PdfReader(str(PDF_OUT)).pages)
    for req in ("Safe_EV_Sunk_m0", "RT_2F_Min_m0", "58,676", "344.09"):
        assert req in txt, f"Missing expected Revision v5 token `{req}` in {PDF_OUT.name}"
    for bad in FORBIDDEN_LATEX_LEAKS + FORBIDDEN_LEGACY_STRINGS + ["92.77", "66.22"]:
        assert bad not in txt, f"Forbidden string `{bad}` found in {PDF_OUT.name}"
    print(f"Wrote {HTML_OUT.name} & {PDF_OUT.name} ({len(PdfReader(str(PDF_OUT)).pages)} pages, clean)")


if __name__ == "__main__":
    build()
