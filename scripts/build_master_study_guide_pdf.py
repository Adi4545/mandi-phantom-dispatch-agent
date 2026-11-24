#!/usr/bin/env python3
"""Assemble the Revision v8 (Honest Candidate C Synthesis) MandiGuard Master Study Guide into HTML + PDF.

Inputs  : docs/study_guide_v2_parts/part1_foundations_data.html
          docs/study_guide_v2_parts/part2_method_results.html
          docs/study_guide_v2_parts/part3_literature_defense.html
Outputs : docs/MandiGuard_Master_Study_Guide.html
          docs/MandiGuard_Master_Study_Guide.pdf

Builds cleanly from Revision v8 fragments referencing `figures/rev_fig1..4*.png`.
Enforces zero backticks, zero markdown `**`, zero raw LaTeX leaks, zero stale 5m-starved ML/CQR illusions.
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
th code { background: rgba(255, 255, 255, 0.18); color: #fff; border-color: transparent; }
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
  <h1>MandiGuard &mdash; Master Study Guide (Revision v8)</h1>
  <div class="sub">Aditya Sharma (M.Tech Thesis Research, supervised by Dr. Sonia) &mdash; Shoolini University, Solan, Himachal Pradesh, India &bull; 9-Choice Cold-Start Triage (<code>Safe_EV_Sunk_m0</code>, <code>Safe_EV_Phys_m0</code>, <code>RT_2F_Min_m0</code>), <code>2&times;2</code> Orthogonal Audit &amp; <code>17m</code> ML/CQR Frontier<br/>
  Explained from first principles so a motivated student can verify, present, and defend every equation, mechanism, and boundary</div>
  <span class="pill">Primary 171-Mkt Zero-Lookahead</span><span class="pill">Timing Firewall (&le; t&minus;1 / t&minus;2)</span>
  <span class="pill">Clean 166-Mkt 2018&ndash;2023 (N=383,952)</span><span class="pill">9 Fixed Choices (0 Tuned Weights)</span>
  <span class="pill">Exploratory R=2,000 Holm p=0.0040</span><span class="pill">17m ML/CQR + 2&times;2 Decomp</span>
  <span class="pill">59 (Author, Year) Citations</span><span class="pill">Viva Defense Bank</span>
  <div class="box key" style="margin-top:12px;"><strong>The thesis in four sentences (Honest Candidate C Synthesis):</strong>
  Online AGMARKNET spreads tempt dispatchers, yet chasing top lagged spreads (<code>B1_lagged_screen</code>) across 57,634 zero-lookahead 171-market test episodes loses money on 45.07% of dispatches (worst-10% <code>ES10 &minus;&#8377;642.15/qtl</code>, with 28.67% turning back sequentially). Prior claims that ML fails reflected 5-month off-season training starvation, unnormalized variance penalties (<code>OR_Vargas_MeanVar_g0002</code> <code>&minus;&#8377;511.42</code>), and a homoscedastic CQR bug (0 switches): trained over a full <code>17m</code> season (<code>n_train_17m = 113,374</code>), <code>ML_17m_MeanQ10_Hybrid_eq63</code> hits Mean <code>&#8377;455.83 / ES10 &minus;&#8377;320.02 / cond_ES10 &minus;&#8377;420.57</code> (<code>NoSafeEV_eq63</code> reaches <code>&#8377;458.27 / &minus;&#8377;423.88</code> autonomously) and heteroscedastic Split-CQR unlocks 8,848 (<code>5m</code>) and 8,115 (<code>17m</code>) switches (<code>ML_17m_CQR80_valmatch</code> <code>cond_ES10 &minus;&#8377;367.09</code> at <code>&#8377;364.03</code> Mean), while zero-tuned-weight <code>Safe_EV_Sunk_m0</code> (<code>9</code> fixed structural choices, <code>n_train = 0</code>; <code>p_dow&middot;G_1SD &minus; F &equiv; p_dow(G_1SD &minus; F) + (1 &minus; p_dow)(&minus;1.0F)</code>) captures ~98.8% of <code>MeanQ10</code> Mean (<code>&#8377;452.74</code>) and ~94% of <code>cond_ES10</code> tail protection (<code>&minus;&#8377;447.48</code> vs <code>&minus;&#8377;628.37</code>) with pocket-calculator portability. A <code>2&times;2</code> orthogonal decomposition shows <code>Ortho_Pure_cv28_only</code> (71.91%, <code>cond_ES10 &minus;&#8377;447.13</code>) drives ~100% of tail truncation while <code>Ortho_Pure_pdow_only</code> (84.10%, Mean <code>&#8377;466.68</code>, <code>&minus;&#8377;607.18</code>) drives diversion avoidance and Mean lift, with <code>CommonIntersection_DS_cap_DB</code> (<code>n = 33,398</code>) confirming <code>+&#8377;65.66</code> Mean / <code>+&#8377;53.40</code> <code>ES10</code> pure routing lift; specification-locked exploratory <code>PREREG_A18</code> (<code>p_holm_2s = 0.0040</code>, CGM <code>p_cgm_gstar = 0.00511 / 0.01001</code> &amp; <code>0.04887 / 0.06800</code>, <code>p_wild_webb6_1w_block_only</code>) holds across <code>&le; t&minus;2</code> lag, repaired <code>_spoil_return_leg</code> <code>S6</code> (<code>&#8377;307.39 / &minus;&#8377;725.73</code>; <code>Stoch_CondMAR_p1.00</code> <code>+&#8377;366.85</code>), and <code>166</code> clean markets (<code>2018&ndash;2023</code>, N = 383,952). These rules serve strictly as a 6 a.m. call-priority filter (<code>PhoneCall_TopK_Open</code>) while disclosing HP apple scale non-invariance (<code>F/G_1SD &lt; 0.10</code> on 79.52%; <code>ScaleInv_Safe_EV_24tau</code> cuts <code>ep_loss</code> 27.91% &rarr; 17.92%, <code>cond_ES10 &minus;&#8377;1,616.08</code>), legacy geocode collisions (56/171 collided, 35.23% exact <code>N=6,605</code> <code>p=0.001</code>), <code>Outsider_Mid/MinPrice_LCV_4pctArh</code>, coupled Manski <code>cond_ES10</code> (<code>Supp1 +&#8377;152.20</code>, <code>Supp2 +&#8377;105.96</code>) &amp; 25.45% Open-MAR break-even, UP unconditional <code>q10 = 0</code> atom, <code>2018&ndash;2023</code> reverse-survivorship (481/647), SUTVA <code>k &le; 2</code> crowding bounds, and blocked Gate J.</div>
</div>

<h2>Three-Part Roadmap</h2>
<div class="flow">
  <div class="fbox c1"><strong>Part 1</strong><span>Problem, Epistemic Table 1, Geocode Audit, Firewall &amp; Settlement</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c2"><strong>Part 2</strong><span>2&times;2 Orthogonal Triage, 17m ML/CQR Frontier, Phase 6 Stress &amp; 2018&ndash;2023</span></div><div class="farrow">&#10140;</div>
  <div class="fbox c3"><strong>Part 3</strong><span>59 Citations, 18-Work Novelty Overlap, Limitations &amp; Viva Bank</span></div>
</div>
"""

CLOSING = """
<div class="pb"></div>
<h1>Closing Verification Note (Revision v8)</h1>
<div class="box key">
  Every metric in this study guide traces directly to committed outputs in <code>revision/results/</code> regenerated via the single-command deterministic pipeline (clean-clone discrepancy <code>0.0</code> across CSV tables, independent <code>A16</code> parity <code>&#8377;0.00</code>, <code>0</code> untraceable numbers verified by traceability checks, <code>pytest</code> passing, and <code>59/59</code> verified citations). See <code>final/READINESS.md</code> for prospective live FPO piloting next steps.
</div>
<p class="small">Canonical Sources: paper/manuscript.md, final/SIMPLIFIED_DESIGN.md, final/DIFFICULTY.md, final/NOVELTY_V2.md, final/AUDIT_V4.md, final/LIMITATIONS.md, final/VIVA_QA.md. Rebuild cleanly with: python3 scripts/build_master_study_guide_pdf.py</p>
"""


def _strip_h1(md: str) -> str:
    lines = md.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).lstrip()
    return md


def regenerate_parts() -> None:
    """Regenerate docs/study_guide_v2_parts/part1..3.html from canonical Revision v8 markdown sources."""
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
        "<h2>Part 1: Problem, Epistemic Table 1, Geocode Audit &amp; Settlement Physics</h2>\n"
        + markdown_to_html_body(ms_part1, bib_keys=bib_keys, base_dir=ROOT / "paper")
    )
    p2_raw = (
        '<div class="pb"></div>\n'
        "<h2>Part 2: 2&times;2 Orthogonal Triage, 17m ML/CQR Frontier, Phase 6 Stress &amp; 2018&ndash;2023</h2>\n"
        + markdown_to_html_body(diff_md, bib_keys=bib_keys, base_dir=ROOT / "final")
        + "\n<hr>\n"
        + markdown_to_html_body(ms_part2, bib_keys=bib_keys, base_dir=ROOT / "paper")
    )
    for ph, fn in FIGS.items():
        p2_raw = p2_raw.replace(b64_img(fn), ph)
    p3_html = (
        '<div class="pb"></div>\n'
        "<h2>Part 3: Related Work (59 Citations), Limitations, Novelty Overlap &amp; Viva Defense Bank</h2>\n"
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
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><title>MandiGuard - Master Study Guide (Revision v8)</title>'
        "<style>" + CSS + "</style></head><body>" + body + "</body></html>"
    )
    HTML_OUT.write_text(doc_html, encoding="utf-8")
    render_pdf(HTML_OUT, PDF_OUT)

    txt = "\n".join((pg.extract_text() or "") for pg in PdfReader(str(PDF_OUT)).pages)
    for req in ("Safe_EV_Sunk_m0", "RT_2F_Min_m0", "57,634", "345.53", "383,952", "113,374", "ScaleInv_Safe_EV_24tau"):
        assert req in txt, f"Missing expected Revision v8 token `{req}` in {PDF_OUT.name}"
    for bad in FORBIDDEN_LATEX_LEAKS + FORBIDDEN_LEGACY_STRINGS + ["92.77", "66.22", "Locked confirmatory"]:
        assert bad not in txt, f"Forbidden string `{bad}` found in {PDF_OUT.name}"
    print(f"Wrote {HTML_OUT.name} & {PDF_OUT.name} ({len(PdfReader(str(PDF_OUT)).pages)} pages, clean)")


if __name__ == "__main__":
    main()
