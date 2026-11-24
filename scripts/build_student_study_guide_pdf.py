#!/usr/bin/env python3
"""Build Revision v8 (Honest Candidate C Synthesis) beginner-friendly (Class 10-12 level) MandiGuard Student Study Guide.

Generates cleanly from canonical Revision v8 sources:
  1. docs/MandiGuard_Student_Study_Guide.html
  2. docs/MandiGuard_Student_Study_Guide.pdf

Zero stale 5m-starved ML/CQR illusions, zero hardcoded home paths, portable Chrome PDF.
"""

from __future__ import annotations

import html
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
HTML_OUT = DOCS_DIR / "MandiGuard_Student_Study_Guide.html"
PDF_OUT = DOCS_DIR / "MandiGuard_Student_Study_Guide.pdf"

STUDENT_CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 9.8pt; }
p { text-align: left; }
.ch-pill {
  display: inline-block; background: #0f4c5c; color: #fff;
  font-size: 7.5pt; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; padding: 2px 8px; border-radius: 3px; margin-bottom: 6px;
}
.step-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 10px 0 12px 0; break-inside: avoid; }
.step-card { background: #f8fafc; border: 1.5px solid #0f4c5c; border-radius: 6px; padding: 8px; text-align: center; font-size: 8.4pt; }
.step-card strong { display: block; color: #0f4c5c; margin-bottom: 3px; font-size: 9pt; }
.pb { break-before: page; page-break-before: always; }
"""


def _strip_top_h1(md: str) -> str:
    lines = md.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).lstrip()
    return md


def build() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    parts = [
        ("Chapter 1 &bull; Class-12 Intuition &amp; Pocket-Calculator Guide", "paper/12th_class_easy_reading_edition.md"),
        ("Chapter 2 &bull; Plain-English Complete Explanation", "viva/01_plain_english_complete_guide.md"),
        ("Chapter 3 &bull; Complexity Audit, 2&times;2 Split &amp; 17m ML Frontier", "final/DIFFICULTY.md"),
        ("Chapter 4 &bull; Top 10 Viva Questions &amp; Simple Answers", "final/VIVA_QA.md"),
        ("Chapter 5 &bull; What This Research Does NOT Claim (14 Boundaries)", "final/LIMITATIONS.md"),
    ]
    blocks = [
        """
        <div class="title-banner">
          <span class="ch-pill">Student Study Guide (Class 10&ndash;12 Level) &bull; Revision v8 Audited</span>
          <h1 class="doc-title">MandiGuard Student Study Guide: Pocket-Calculator Dispatch Filtering</h1>
          <div class="subline">Aditya Sharma (M.Tech Thesis Research, supervised by Dr. Sonia) &mdash; Shoolini University, Solan, Himachal Pradesh, India &bull; 9-Choice <code>Safe_EV_Sunk_m0</code>, <code>ScaleInv_Safe_EV_24tau</code> &amp; Class-8 <code>RT_2F_Min_m0</code></div>
        </div>
        <div class="step-row">
          <div class="step-card"><strong>Step 1: Problem</strong>Lagged AGMARKNET screens lose 45.07% (<code>ES10 &minus;&#8377;642.15</code>, N=57,634)</div>
          <div class="step-card"><strong>Step 2: 2 Rules &amp; 2&times;2</strong><code>p_dow&middot;G_1SD &gt; F</code> (<code>cv28</code> cuts tail, <code>p_dow</code> lifts Mean) &amp; <code>p_min&middot;G &gt; 2F</code></div>
          <div class="step-card"><strong>Step 3: Proof &amp; ML</strong>+&#8377;179.24 ES10, +&#8377;180.89 cond_ES10 (~98.8% of 17m ML Mean); 6/6 yrs 2018&ndash;2023 (N=383,952)</div>
          <div class="step-card"><strong>Step 4: Honesty</strong>6 a.m. call filter (<code>PhoneCall_TopK_Open</code>); Open-MAR, HP scale &amp; Gate J limits</div>
        </div>
        """
    ]
    for i, (title_lbl, rel) in enumerate(parts):
        md_raw = (ROOT / rel).read_text(encoding="utf-8")
        pb = ' class="pb"' if i > 0 else ""
        blocks.append(f'<section{pb}><h2>{title_lbl}</h2>{markdown_to_html_body(_strip_top_h1(md_raw))}</section>')

    blocks.append(
        f"""<section class="pb">
        <h2>Chapter 6 &bull; Key Revision v8 Visual Charts</h2>
        <figure class="fig-card"><img src="{b64_img('rev_fig1_risk_coverage_ci.png')}" alt="Risk Coverage"><figcaption>Figure 1: Risk-coverage curves showing 9-choice zero-tuned-weight Safe_EV_Sunk_m0 and RT_2F_Min_m0 against age-matched road dispatch and hard gates across 57,634 primary 171-market episodes (capturing ~98.8% of full-season 17m MeanQ10 Mean and ~94% of cond_ES10 protection at n_train = 0).</figcaption></figure>
        <figure class="fig-card"><img src="{b64_img('rev_fig2_ablations_and_crops.png')}" alt="Fair Controls and Crops"><figcaption>Figure 2: Equal-dispatch and fixed-haircut ablations (left) and worst-10% ES10 gains across every crop subset including Apple (right) on the 171-market panel (disclosing UP unconditional q10=0 atom and HP B=12 / Apple cond_ES10 limits).</figcaption></figure>
        <figure class="fig-card"><img src="{b64_img('rev_fig3_sensitivity_tornado_and_missing.png')}" alt="Sensitivity and Missing Bounds"><figcaption>Figure 3: Parameter tornado stability across 10 representative freight/commission shifts from the 18-scenario suite (left) and missing-quote identification bounds including Open-MAR Mean reversal and exact coupled Manski cond_ES10 (right).</figcaption></figure>
        <figure class="fig-card"><img src="{b64_img('rev_fig4_settlement_and_hp_apple.png')}" alt="2018-2023 Backtest and HP Apples"><figcaption>Figure 4: Clean 166-market 2018&ndash;2023 annual ES10 generalization (reverse-survivorship conditioned on 2024 corridor inclusion, 481/647 excluded, N = 383,952, left) and HP graded apples (N = 2,802, right, where F/G_1SD &lt; 0.10 on 79.52% drives scale non-invariance partially solved by ScaleInv_Safe_EV_24tau).</figcaption></figure>
        </section>"""
    )

    doc_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>MandiGuard Student Study Guide (Revision v8)</title>
<style>{PAPER_CSS}\n{STUDENT_CSS}</style></head>
<body>{''.join(blocks)}</body></html>"""
    HTML_OUT.write_text(doc_html, encoding="utf-8")
    render_pdf(HTML_OUT, PDF_OUT)

    txt = "\n".join((pg.extract_text() or "") for pg in PdfReader(str(PDF_OUT)).pages)
    for req in ("Safe_EV_Sunk_m0", "RT_2F_Min_m0", "57,634", "345.53", "383,952", "ScaleInv_Safe_EV_24tau"):
        assert req in txt, f"Missing expected Revision v8 token `{req}` in {PDF_OUT.name}"
    for bad in FORBIDDEN_LATEX_LEAKS + FORBIDDEN_LEGACY_STRINGS + ["92.77", "66.22", "Locked confirmatory"]:
        assert bad not in txt, f"Forbidden string `{bad}` found in {PDF_OUT.name}"
    print(f"Wrote {HTML_OUT.name} & {PDF_OUT.name} ({len(PdfReader(str(PDF_OUT)).pages)} pages, clean)")


if __name__ == "__main__":
    build()
