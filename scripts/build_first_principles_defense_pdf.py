#!/usr/bin/env python3
"""Build Revision v8 (Honest Candidate C Synthesis) First-Principles & Thesis Defense Handbook HTML + PDF.

Compiles directly from canonical Revision v8 markdown sources:
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

Zero stale 5m-starved ML/CQR illusions, zero hardcoded home paths, portable Chrome PDF.
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
    PAPER_TABLE_CAPTIONS,
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
    ("Part 3 • Difficulty Reduction Audit", "Complexity Reduction, 2x2 Decomposition & 17m ML Frontier", "final/DIFFICULTY.md"),
    ("Part 4 • Simplified Equations", "9-Choice Safe_EV_Sunk_m0, ScaleInv_Safe_EV_24tau & RT_2F_Min_m0", "final/SIMPLIFIED_DESIGN.md"),
    ("Part 5 • Complete Scientific Paper", "Revision v8 Full Manuscript (171 Mkts, 2x2 Audit, 17m ML/CQR, 2018–2023)", "paper/manuscript.md"),
    ("Part 6 • Literature & Novelty Defense", "18-Work Overlap Matrix & Surviving Claim (NOVELTY_V2)", "final/NOVELTY_V2.md"),
    ("Part 7 • Cleanroom & Examiner Sign-Off", "A16 Parity (₹0.00) & Independent Audit Record", "final/AUDIT_V4.md"),
    ("Part 8 • Prominent Boundaries (R6 & R7)", "Fourteen Binding Non-Claims & Manski / Scale / Crowding Disclosures", "final/LIMITATIONS.md"),
    ("Part 9 • Examiner Viva Bank", "Scripted-Verified Q&A (Revision v8 Clean)", "final/VIVA_QA.md"),
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
      <span class="meta-pill">Thesis Defense Compendium &bull; Revision v8 (Honest Candidate C Synthesis)</span>
      <h1>MandiGuard: First-Principles &amp; Thesis Defense Handbook</h1>
      <div class="sub">Aditya Sharma (M.Tech Thesis Research, supervised by Dr. Sonia) &mdash; Shoolini University, Solan, Himachal Pradesh, India &bull; 9-Choice Cold-Start <code>Safe_EV_Sunk_m0</code>, <code>2&times;2</code> Orthogonal Audit, <code>17m</code> ML/CQR Frontier &amp; <code>ScaleInv_Safe_EV_24tau</code></div>
      <div class="badge-row">
        <span class="badge">9 Fixed Choices (0 Tuned Weights)</span>
        <span class="badge">171-Mkt Primary (N=57,634)</span>
        <span class="badge">17m ML Frontier (n_train=113,374)</span>
        <span class="badge">Exploratory PREREG_A18 Holm p = 0.0040</span>
        <span class="badge">166-Mkt 2018&ndash;2023 (N=383,952)</span>
        <span class="badge">59 (Author, Year) Citations</span>
      </div>
      <div class="worked-box">
        <p><strong>Canonical Scope Notice (Revision v8 &mdash; Honest Candidate C Synthesis):</strong> Every metric, equation, and figure in this handbook is compiled directly from Revision v8 sources on branch <code>finalization</code>. On the zero-lookahead <code>2024</code>-selected <code>171</code>-market panel (<code>N = 57,634</code>), specification-locked exploratory inference (<code>PREREG_A18</code>, <code>R = 2,000</code>, <code>p<sub>holm,2s</sub> = 0.0040</code>; finite-sample CGM <code>p<sub>cgm,gstar</sub> = 0.00511 / 0.01001</code> for <code>H_A18_1</code>, <code>0.04887 / 0.06800</code> for <code>H_A18_2</code>; 1-way <code>p_wild_webb6_1w_block_only</code>) shows <code>Safe_EV_Sunk_m0</code> (<code>9</code> fixed choices, zero tuned weights; <code>p<sub>dow</sub>&middot;G<sub>1SD</sub> &minus; F &equiv; p<sub>dow</sub>(G<sub>1SD</sub> &minus; F) + (1 &minus; p<sub>dow</sub>)(&minus;1.0F)</code>) reaches Mean <code>&#8377;452.74</code>, <code>ES10 &minus;&#8377;345.53</code>, and <code>cond_ES10 &minus;&#8377;447.48</code>. A <code>2&times;2</code> orthogonal decomposition proves <code>Ortho_Pure_cv28_only</code> (<code>71.91%</code>, <code>cond_ES10 &minus;&#8377;447.13</code>) drives ~100% of conditional tail truncation while <code>Ortho_Pure_pdow_only</code> (<code>84.10%</code>, Mean <code>&#8377;466.68</code>, <code>cond_ES10 &minus;&#8377;607.18</code>) drives diversion avoidance and Mean lift; inside <code>CommonIntersection_DS_cap_DB</code> (<code>n = 33,398</code>), pure routing lift adds <code>+&#8377;65.66</code> Mean and <code>+&#8377;53.40</code> <code>ES10</code>. Honest full-season <code>17m</code> ML (<code>n<sub>train</sub> = 113,374</code>) resolves earlier <code>5m</code> off-season starvation and homoscedastic CQR bugs (<code>0</code> switches): <code>ML_17m_MeanQ10_Hybrid_eq63</code> hits Mean <code>&#8377;455.83 / ES10 &minus;&#8377;320.02 / cond_ES10 &minus;&#8377;420.57</code> (with <code>NoSafeEV_eq63</code> at <code>&#8377;458.27 / &minus;&#8377;423.88</code> autonomously) and heteroscedastic Split-CQR unlocks <code>8,848</code> (<code>5m</code>) and <code>8,115</code> (<code>17m</code>) switches (<code>cond_ES10 &minus;&#8377;367.09</code> at Mean <code>&#8377;364.03</code>), while <code>Safe_EV_Sunk_m0</code> captures ~98.8% of <code>MeanQ10</code> Mean and ~94% of <code>cond_ES10</code> tail protection at <code>n<sub>train</sub> = 0</code>. Also disclosed: HP apple scale non-invariance (<code>F/G<sub>1SD</sub> &lt; 0.10</code> on <code>79.52%</code>; solved by <code>ScaleInv_Safe_EV_24tau</code> cutting <code>ep_loss</code> <code>27.91% &rarr; 17.92%</code>, <code>cond_ES10 &minus;&#8377;1,616.08</code>), legacy geocode collisions (<code>56/171</code> collided, <code>35.23%</code> non-collided exact coverage, <code>N = 6,605</code> <code>p = 0.001</code>), repaired <code>_spoil_return_leg</code> <code>S6</code> (<code>&#8377;307.39 / &minus;&#8377;725.73</code>; <code>Stoch_CondMAR_p1.00 +&#8377;366.85</code>), exact coupled Manski <code>cond_ES10</code> (<code>Supp1 +&#8377;152.20</code>, <code>Supp2 +&#8377;105.96</code>), <code>PhoneCall_TopK_Open</code>, <code>Outsider_Mid/MinPrice_LCV_4pctArh</code>, UP unconditional <code>q10 = 0</code> atom, and <code>2018&ndash;2023</code> reverse-survivorship (<code>481/647</code>).</p>
      </div>
    </div>
    """

    sections = [cover]
    for idx, (kicker, title, rel) in enumerate(CHAPTERS):
        md_raw = (ROOT / rel).read_text(encoding="utf-8")
        # Rewrite relative figure paths cleanly for b64_img (it strips dirs via .name)
        body_html = markdown_to_html_body(
            _strip_top_h1(md_raw),
            bib_keys=bib_keys,
            base_dir=(ROOT / rel).parent,
            table_captions=PAPER_TABLE_CAPTIONS if rel == "paper/manuscript.md" else None,
        )
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
<title>MandiGuard First-Principles &amp; Thesis Defense Handbook (Revision v8)</title>
<style>{PAPER_CSS}\n{HANDBOOK_EXTRA_CSS}</style>
</head>
<body>{''.join(sections)}</body>
</html>"""

    HTML_OUT.write_text(full_html, encoding="utf-8")
    render_pdf(HTML_OUT, PDF_OUT)

    txt = "\n".join((pg.extract_text() or "") for pg in PdfReader(str(PDF_OUT)).pages)
    for req in ("Safe_EV_Sunk_m0", "RT_2F_Min_m0", "57,634", "345.53", "383,952", "113,374", "ScaleInv_Safe_EV_24tau"):
        assert req in txt, f"Missing expected Revision v8 token `{req}` in {PDF_OUT.name}"
    for bad in FORBIDDEN_LATEX_LEAKS + FORBIDDEN_LEGACY_STRINGS + ["92.77", "66.22", "Locked confirmatory"]:
        assert bad not in txt, f"Forbidden string `{bad}` found in {PDF_OUT.name}"
    print(f"Wrote {HTML_OUT.name} & {PDF_OUT.name} ({len(PdfReader(str(PDF_OUT)).pages)} pages, clean)")


if __name__ == "__main__":
    build()
