#!/usr/bin/env python3
"""Build the First-Principles Textbook & Thesis Defense Master PDF for MandiGuard.

Generates:
  1. docs/MandiGuard_First_Principles_and_Thesis_Defense_Handbook.html
  2. docs/MandiGuard_First_Principles_and_Thesis_Defense_Handbook.pdf
"""

from __future__ import annotations

import base64
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "figures"
DOCS_DIR = ROOT / "docs"
HTML_OUT = DOCS_DIR / "MandiGuard_First_Principles_and_Thesis_Defense_Handbook.html"
PDF_OUT = DOCS_DIR / "MandiGuard_First_Principles_and_Thesis_Defense_Handbook.pdf"

CHROME_BIN = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def b64_img(filename: str) -> str:
    path = FIG_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing figure: {path}")
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


CSS = """
@page {
  size: A4;
  margin: 14mm 14mm 16mm 14mm;
}

* {
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 9.5pt;
  line-height: 1.46;
  color: #1e293b;
  margin: 0;
  padding: 0;
  background: #ffffff;
}

h1, h2, h3, h4 {
  color: #0f172a;
  font-weight: 700;
  margin-top: 1.0em;
  margin-bottom: 0.35em;
  page-break-after: avoid;
  break-after: avoid;
}

h1.chapter-title {
  font-size: 16pt;
  color: #0f3d5e;
  border-bottom: 2.5px solid #0f3d5e;
  padding-bottom: 5px;
  margin-top: 0;
  padding-top: 2px;
}

h2 {
  font-size: 11.8pt;
  color: #164e63;
  border-left: 4px solid #0284c7;
  padding-left: 8px;
  margin-top: 14px;
}

h3 {
  font-size: 10.3pt;
  color: #1e3a5f;
  margin-top: 10px;
}

p {
  margin: 0 0 6.5px 0;
  text-align: left;
}

ul, ol {
  margin: 4px 0 8px 0;
  padding-left: 20px;
}

li {
  margin-bottom: 3px;
}

code {
  font-family: "SFMono-Regular", Menlo, Monaco, Consolas, monospace;
  font-size: 8.3pt;
  background: #f1f5f9;
  color: #0f172a;
  padding: 1px 4px;
  border-radius: 3px;
  border: 1px solid #e2e8f0;
}

.page-break {
  page-break-before: always;
  break-before: page;
}

/* Cover Page */
.cover {
  border: 2px solid #0f3d5e;
  border-radius: 8px;
  padding: 20px 24px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 45%, #f0f9ff 100%);
  margin-bottom: 12px;
}

.cover-badge {
  display: inline-block;
  background: #0f3d5e;
  color: #ffffff;
  font-size: 8.2pt;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 4px;
  margin-bottom: 8px;
}

.cover-title {
  font-size: 19.5pt;
  line-height: 1.18;
  color: #0f172a;
  font-weight: 800;
  margin: 4px 0 8px 0;
}

.cover-subtitle {
  font-size: 10.6pt;
  color: #334155;
  font-weight: 500;
  margin-bottom: 10px;
}

.meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 8px;
  font-size: 8.5pt;
}

.meta-item {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-left: 3px solid #0284c7;
  padding: 6px 9px;
  border-radius: 4px;
}

/* Callouts and Boxes */
.box {
  border-radius: 6px;
  padding: 9px 12px;
  margin: 8px 0 10px 0;
  break-inside: avoid;
  page-break-inside: avoid;
}

.box-intuition {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-left: 4.5px solid #0284c7;
}

.box-math {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-left: 4.5px solid #0f3d5e;
}

.box-numerical {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-left: 4.5px solid #16a34a;
}

.box-warning {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-left: 4.5px solid #d97706;
}

.box-redline {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-left: 4.5px solid #dc2626;
}

.box-title {
  font-weight: 700;
  font-size: 9.5pt;
  margin-bottom: 4px;
  color: #0f172a;
}

.math-formula {
  font-family: "Cambria Math", "Times New Roman", Georgia, serif;
  font-size: 10.3pt;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 6px 10px;
  margin: 5px 0;
  text-align: center;
  color: #0f172a;
}

.frac {
  display: inline-block;
  vertical-align: middle;
  text-align: center;
  font-size: 0.90em;
  margin: 0 2px;
}
.frac > span {
  display: block;
  padding: 0 3px;
}
.frac > span.num {
  border-bottom: 1px solid #0f172a;
}

/* Tables */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 6px 0 9px 0;
  font-size: 8.1pt;
  break-inside: avoid;
  page-break-inside: avoid;
}

th {
  background: #0f3d5e;
  color: #ffffff;
  font-weight: 600;
  text-align: left;
  padding: 5px 6px;
  border: 1px solid #0f3d5e;
}

td {
  padding: 4.2px 6px;
  border: 1px solid #cbd5e1;
  vertical-align: top;
}

tr:nth-child(even) td {
  background: #f8fafc;
}

tr.highlight td {
  background: #ecfdf5 !important;
  font-weight: 600;
}

tr.warn-row td {
  background: #fef2f2 !important;
}

.num-col {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

/* Figures */
.figure-box {
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 7px 9px;
  margin: 8px 0 10px 0;
  background: #ffffff;
  text-align: center;
  break-inside: avoid;
  page-break-inside: avoid;
}

.figure-box img {
  max-width: 100%;
  max-height: 92mm;
  height: auto;
  display: block;
  margin: 0 auto 4px auto;
}

.figure-caption {
  font-size: 8.1pt;
  color: #475569;
  text-align: left;
  line-height: 1.36;
}

/* SVG diagram box */
.svg-box {
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 7px 9px;
  margin: 7px 0 9px 0;
  background: #ffffff;
  text-align: center;
  break-inside: avoid;
  page-break-inside: avoid;
}

/* Viva Cards */
.qa-item {
  border: 1px solid #cbd5e1;
  border-left: 4px solid #0f3d5e;
  border-radius: 5px;
  padding: 6px 9px;
  margin-bottom: 6px;
  background: #ffffff;
  break-inside: avoid;
  page-break-inside: avoid;
}

.qa-q {
  font-weight: 700;
  color: #0f3d5e;
  margin-bottom: 2.5px;
  font-size: 9pt;
}

.qa-a {
  font-size: 8.7pt;
  color: #1e293b;
}

.paper-card {
  border: 1px solid #cbd5e1;
  border-top: 3px solid #0284c7;
  border-radius: 5px;
  padding: 6px 9px;
  margin-bottom: 6.5px;
  background: #ffffff;
  break-inside: avoid;
  page-break-inside: avoid;
}

.paper-title {
  font-weight: 700;
  color: #0f172a;
  font-size: 9.1pt;
}

.paper-meta {
  font-size: 7.9pt;
  color: #475569;
  margin-bottom: 3px;
}

.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 9px;
}

.quote-script {
  background: #f8fafc;
  border-left: 4px solid #0f3d5e;
  padding: 8px 11px;
  font-style: italic;
  border-radius: 4px;
  margin: 6px 0 9px 0;
  font-size: 8.8pt;
  break-inside: avoid;
}
"""


def sec_cover_and_blueprint() -> str:
    return """
<div class="cover">
  <div class="cover-badge">M.Tech Thesis First-Principles Textbook &amp; Viva Defense Playbook (Stage I + Stage II)</div>
  <div class="cover-title">MandiGuard &amp; MandiGuard-CRC: Phantom Spatial Arbitrage, Mechanistic Autopsy &amp; Risk-Gated Dispatch</div>
  <div class="cover-subtitle">
    Complete Under-the-Hood Study &amp; Defense Guide: Intuition → Physics &amp; Statutory Economics → Histogram GBDTs, Conformal Bounds &amp; Uncensored CRC → Cluster Bootstrap → 20 Research Papers → 17 Experiments → 9 Figures → 50 Viva Q&amp;As
  </div>
  <div class="meta-grid">
    <div class="meta-item"><strong>Two-Stage System Architecture:</strong> <strong>Stage I</strong> Pre-Registered Cascade (<code>T1 → T2 → T3 → T4</code> + 2024 HGBR + Causal 80% Conformal LCB); <strong>Stage II</strong> (<code>[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]</code>): Dual-Head Uncensored <code>MandiGuard-CRC</code> (<code>λ* = 0.15</code> on <code>Val_2025H1</code>) + Grade-Aware <code>T1</code>. <em>Zero runtime LLM or RL policy.</em></div>
    <div class="meta-item"><strong>Empirical Scale:</strong> 6 Indian States (MH, UP, KA, MP, GJ, HP) × 4 Crops (Onion, Potato, Tomato, Apple) • 178 Core Mandis • 8,147 OSRM Corridors • 2017–2026 (42.72M raw AGMARKNET mirror rows streamed).</div>
    <div class="meta-item"><strong>Confirmatory &amp; Post-Diagnostic Holdout:</strong> Holdout Jun 2025–Apr 2026 (<code>N = 69,526</code> shortlisted episodes, 174 mandis × 23 blocks) + HP Graded Apple 2026 (<code>N = 1,537</code>) + Matched Open-Yard Cohort (<code>N = 10,162</code>).</div>
    <div class="meta-item"><strong>Dual-Tier Official Parity (<code>Exp 14</code>):</strong> <code>data.gov.in</code> XML Spot-Check (<code>172</code> keys: 100% Min/Max, 99.42% Modal) + <strong>149-Day AGMARKNET 2.0 Direct Export (<code>2,042</code> keys: 100.00% Min/Max/Modal)</strong> • ERA5 &amp; NASA POWER • MoFPI/NABCONS (2022) • GoI APMC Fees • GoHP Survey 2025–26 • NSO NSS 77th Round.</div>
  </div>
</div>

<div class="box box-intuition">
  <div class="box-title">How to Use This Master Handbook to Defend Both Your Synopsis and Final Thesis</div>
  <ol style="margin-bottom:0;">
    <li><strong>Chapter 1 (First Principles):</strong> Why a tempting ₹700–₹1,330/qtl portal spread turns negative in real life (<em>Phantom Spatial Arbitrage</em>) and how a 30-quintal truck compares against ₹3,798/month smallholder household income.</li>
    <li><strong>Chapter 2 (Most Relevant Research — Deep Dive):</strong> All 20 foundational academic papers (14 Stage-I pillars + 6 Stage-II conformal/selective-label/liquidity papers) + 8 closest mandi systems, plus our Stage-I &amp; Stage-II novelty ledger.</li>
    <li><strong>Chapter 3 (Under the Hood — Math, Numerics &amp; Code):</strong> Every line of arithmetic, physics (Q10 rot, APMC fees, 1.45× hill roads), HGBR 255-bin gradient boosting, Min-Heap conformal firewall, PLUS Stage-II uncensored <code>Y_full</code> dual-head <code>MandiGuard-CRC</code> scoring &amp; validation calibration worked numerically!</li>
    <li><strong>Chapter 4 (Auction Payoffs, Metrics &amp; Cluster Bootstrap):</strong> The 4 ground-truth auction outcomes, CVaR<sub>10%</sub> hand calculation, Two-Way Origin-Mandi × Week-Block Bootstrap matrix algebra (<code>np.einsum</code>), and Holm–Bonferroni multiple-testing control.</li>
    <li><strong>Chapter 5 (Complete Experiments <code>Exp 1</code>–<code>Exp 17</code> &amp; All 9 Figures):</strong> View 1 confirmatory results, View 2 Dual Open-Yard Cohorts (<code>Exp 15</code>), Dual-Tier <code>Exp 14</code>, Stage-II <code>Exp 16</code>–<code>Exp 17</code> + <strong>Figure 8</strong>, Ablations, Budgets, Apples, LOSO, 10-year shocks, and Appendix illustrations (<code>Exp 11–13b</code> + <strong>Figure A1</strong>).</li>
    <li><strong>Chapter 6 (Defense Playbook):</strong> Updated Two-Stage 1-min, 5-min, and 15-min presentation scripts, non-negotiable Red-Lines, all <strong>50 examiner Q&amp;As</strong> (incl. Stage-II defense), and a 10-minute whiteboard blank-sheet mastery drill.</li>
  </ol>
</div>

<div class="svg-box">
  <div class="box-title" style="text-align:left;">Master System Blueprint: MandiGuard Deterministic Four-Step Verification Cascade</div>
  <svg width="100%" viewBox="0 0 820 185" xmlns="http://www.w3.org/2000/svg" style="font-family: sans-serif;">
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 10 5 L 0 9 z" fill="#0f3d5e" />
      </marker>
      <marker id="arrow-red" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 10 5 L 0 9 z" fill="#dc2626" />
      </marker>
    </defs>

    <rect x="8" y="18" width="128" height="82" rx="6" fill="#f1f5f9" stroke="#475569" stroke-width="1.5"/>
    <text x="72" y="36" text-anchor="middle" font-size="10.2" font-weight="bold" fill="#0f172a">Step 0: Free Screen</text>
    <text x="72" y="50" text-anchor="middle" font-size="8.8" fill="#334155">0 API Calls</text>
    <text x="72" y="64" text-anchor="middle" font-size="8.3" fill="#334155">15–500 km intra-state</text>
    <text x="72" y="77" text-anchor="middle" font-size="8.3" fill="#334155">Spread &gt; ₹100/qtl</text>
    <text x="72" y="90" text-anchor="middle" font-size="8.5" font-weight="bold" fill="#0f3d5e">Keep Top K = 5</text>

    <line x1="136" y1="59" x2="158" y2="59" stroke="#0f3d5e" stroke-width="1.5" marker-end="url(#arrow)"/>

    <rect x="160" y="18" width="136" height="82" rx="6" fill="#e0f2fe" stroke="#0284c7" stroke-width="1.5"/>
    <text x="228" y="36" text-anchor="middle" font-size="10.2" font-weight="bold" fill="#0f3d5e">T1: Yard Vitality</text>
    <text x="228" y="50" text-anchor="middle" font-size="8.8" fill="#0369a1">+1 Call / Cand</text>
    <text x="228" y="64" text-anchor="middle" font-size="8.3" fill="#1e293b">Exact variety age ≤ 3d</text>
    <text x="228" y="77" text-anchor="middle" font-size="8.3" fill="#1e293b">14d open_prob ≥ 0.50</text>
    <text x="228" y="90" text-anchor="middle" font-size="8.3" fill="#1e293b">Arr. DOW open ≥ 0.35</text>

    <line x1="296" y1="59" x2="318" y2="59" stroke="#0f3d5e" stroke-width="1.5" marker-end="url(#arrow)"/>

    <rect x="320" y="18" width="136" height="82" rx="6" fill="#e0f2fe" stroke="#0284c7" stroke-width="1.5"/>
    <text x="388" y="36" text-anchor="middle" font-size="10.2" font-weight="bold" fill="#0f3d5e">T2: Road + APMC</text>
    <text x="388" y="50" text-anchor="middle" font-size="8.8" fill="#0369a1">+1 Call / Cand</text>
    <text x="388" y="64" text-anchor="middle" font-size="8.3" fill="#1e293b">OSRM road + HP 1.45×</text>
    <text x="388" y="77" text-anchor="middle" font-size="8.3" fill="#1e293b">GoI Fee (0.5–1.5%)</text>
    <text x="388" y="90" text-anchor="middle" font-size="8.3" fill="#1e293b">Pass if Spread &gt; F_ij</text>

    <line x1="456" y1="59" x2="478" y2="59" stroke="#0f3d5e" stroke-width="1.5" marker-end="url(#arrow)"/>

    <rect x="480" y="18" width="136" height="82" rx="6" fill="#e0f2fe" stroke="#0284c7" stroke-width="1.5"/>
    <text x="548" y="36" text-anchor="middle" font-size="10.2" font-weight="bold" fill="#0f3d5e">T3: Climate Rot</text>
    <text x="548" y="50" text-anchor="middle" font-size="8.8" fill="#0369a1">+1 Call / Cand</text>
    <text x="548" y="64" text-anchor="middle" font-size="8.3" fill="#1e293b">Day-t Forecast Tmax,RH,Rain</text>
    <text x="548" y="77" text-anchor="middle" font-size="8.3" fill="#1e293b">Q10 = 2^((T-20)/10)</text>
    <text x="548" y="90" text-anchor="middle" font-size="8.3" fill="#1e293b">Pass if Net after rot &gt; 0</text>

    <line x1="616" y1="59" x2="638" y2="59" stroke="#0f3d5e" stroke-width="1.5" marker-end="url(#arrow)"/>

    <rect x="640" y="18" width="172" height="82" rx="6" fill="#dcfce7" stroke="#16a34a" stroke-width="1.8"/>
    <text x="726" y="36" text-anchor="middle" font-size="10.2" font-weight="bold" fill="#14532d">T4: Tree + Conformal LCB</text>
    <text x="726" y="50" text-anchor="middle" font-size="8.8" fill="#15803d">+1 Call (0.09 ms CPU)</text>
    <text x="726" y="64" text-anchor="middle" font-size="8.3" fill="#1e293b">Frozen 2024 HGBR Forecast</text>
    <text x="726" y="77" text-anchor="middle" font-size="8.3" fill="#1e293b">Minus 80th-pct past error</text>
    <text x="726" y="90" text-anchor="middle" font-size="8.4" font-weight="bold" fill="#14532d">Gate: LCB Net &gt; ₹50/qtl</text>

    <line x1="228" y1="100" x2="228" y2="134" stroke="#dc2626" stroke-width="1.2" marker-end="url(#arrow-red)"/>
    <line x1="388" y1="100" x2="388" y2="134" stroke="#dc2626" stroke-width="1.2" marker-end="url(#arrow-red)"/>
    <line x1="548" y1="100" x2="548" y2="134" stroke="#dc2626" stroke-width="1.2" marker-end="url(#arrow-red)"/>
    <line x1="688" y1="100" x2="688" y2="134" stroke="#dc2626" stroke-width="1.2" marker-end="url(#arrow-red)"/>
    <line x1="766" y1="100" x2="766" y2="134" stroke="#16a34a" stroke-width="1.6" marker-end="url(#arrow)"/>

    <rect x="160" y="137" width="548" height="36" rx="5" fill="#fef2f2" stroke="#dc2626" stroke-width="1.2"/>
    <text x="434" y="152" text-anchor="middle" font-size="9.2" font-weight="bold" fill="#991b1b">Early Elimination &rarr; REFUSE_PHANTOM_SPREAD (SELL_LOCAL, ΔNet = ₹0)</text>
    <text x="434" y="165" text-anchor="middle" font-size="8.0" fill="#7f1d1d">T1 stops 30.82% upfront (~3.0–3.6 calls) • T2 stops 2.24% • T3 stops 0.71% • T4 stops 17.58% (ARRIVAL_REVERSION_RISK)</text>

    <rect x="716" y="137" width="96" height="36" rx="5" fill="#16a34a" stroke="#14532d" stroke-width="1.5"/>
    <text x="764" y="153" text-anchor="middle" font-size="9.3" font-weight="bold" fill="#ffffff">DISPATCH j*</text>
    <text x="764" y="165" text-anchor="middle" font-size="7.9" fill="#dcfce7">48.66% episodes</text>
  </svg>
</div>

<div class="two-col">
  <div class="box box-math" style="margin-top:0;">
    <div class="box-title">View 1: Full Holdout (<code>N = 69,526</code>, Stage I + Stage II)</div>
    <table>
      <tr><th>Policy</th><th class="num-col">Mean</th><th class="num-col">LTR</th><th class="num-col">CVaR<sub>10%</sub></th><th class="num-col">Calls</th></tr>
      <tr><td><code>B0_SellLocal</code></td><td class="num-col">₹0.00</td><td class="num-col">0.0%</td><td class="num-col">₹0.00</td><td class="num-col">0.0</td></tr>
      <tr><td><code>B1_NaiveScreen</code></td><td class="num-col">₹350.01</td><td class="num-col">40.46%</td><td class="num-col">-₹1,062.66</td><td class="num-col">0.0</td></tr>
      <tr><td><code>B2_FreshRoad</code></td><td class="num-col">₹446.66</td><td class="num-col">18.11%</td><td class="num-col">-₹436.67</td><td class="num-col">7.87</td></tr>
      <tr class="warn-row"><td><code>B3_MLPoint</code></td><td class="num-col">₹330.85</td><td class="num-col">45.28%</td><td class="num-col">-₹1,097.80</td><td class="num-col">7.87</td></tr>
      <tr><td><code>MG_v1 (Stage I)</code></td><td class="num-col">₹452.79</td><td class="num-col">9.97%</td><td class="num-col">-₹37.89</td><td class="num-col">8.75</td></tr>
      <tr class="highlight"><td><code>MandiGuard-CRC (Stage II)</code></td><td class="num-col"><strong>₹479.17</strong></td><td class="num-col"><strong>10.48%</strong></td><td class="num-col"><strong>-₹44.03</strong></td><td class="num-col">9.07</td></tr>
    </table>
    <p style="font-size:7.8pt;margin:0;"><strong>Stage I:</strong> H1/H3/H4 SUPPORTED (<code>p_Holm≤0.0012</code>), H2 tie (<code>p=0.27</code>). <strong>Stage II (<code>[POST-DIAG]</code>):</strong> +₹32.51 vs <code>B2</code> (<code>p=0.0016</code>), +₹26.38 vs <code>MG_v1</code> (<code>p=0.0002</code>).</p>
  </div>
  <div class="box box-math" style="margin-top:0;">
    <div class="box-title">View 2: Matched Open Yards (<code>N = 10,162</code>, Zero Traps)</div>
    <table>
      <tr><th>Policy (Identical Cohort)</th><th class="num-col">Disp.</th><th class="num-col">Mean</th><th class="num-col">LTR</th><th class="num-col">CVaR<sub>10%</sub></th></tr>
      <tr><td><code>B1_NaiveScreen</code></td><td class="num-col">74.8%</td><td class="num-col">₹472.51</td><td class="num-col">19.84%</td><td class="num-col">-₹694.72</td></tr>
      <tr><td><code>B2_FreshRoad</code></td><td class="num-col">64.4%</td><td class="num-col">₹469.99</td><td class="num-col">15.09%</td><td class="num-col">-₹94.70</td></tr>
      <tr><td><code>B3_MLPoint</code></td><td class="num-col">73.5%</td><td class="num-col"><strong>₹553.22</strong></td><td class="num-col">14.77%</td><td class="num-col">-₹362.40</td></tr>
      <tr><td><code>MG_v1 (Stage I)</code></td><td class="num-col">47.3%</td><td class="num-col">₹510.89</td><td class="num-col"><strong>6.82%</strong></td><td class="num-col">-₹36.07</td></tr>
      <tr class="highlight"><td><code>MandiGuard-CRC (Stage II)</code></td><td class="num-col">55.4%</td><td class="num-col"><strong>₹533.75</strong></td><td class="num-col"><strong>7.14%</strong></td><td class="num-col"><strong>-₹35.00</strong></td></tr>
    </table>
    <p style="font-size:7.8pt;margin:0;"><strong>Zero Simulated Trap Bias:</strong> Stage-II <code>MandiGuard-CRC</code> adds +₹22.86 over <code>MG_v1</code> &amp; +₹63.76 over <code>B2</code> while halving <code>B3</code> LTR (14.77%→7.14%).</p>
  </div>
</div>
"""


def sec_ch1_first_principles() -> str:
    fig1 = b64_img("fig1_phantom_arbitrage_anatomy.png")
    return f"""
<div class="page-break"></div>
<h1 class="chapter-title">Chapter 1: First-Principles Problem Formulation — Spatial Arbitrage &amp; Why It Turns "Phantom"</h1>

<h2>1.1 Starting From Zero: What Is Spatial Arbitrage?</h2>
<p>In classical economics, the <strong>Law of One Price (LOP)</strong> says that if two wholesale markets <em>i</em> (local origin) and <em>j</em> (distant destination) are connected by truck transport cost <code>F<sub>ij</sub></code>, the equilibrium price gap between them cannot exceed <code>F<sub>ij</sub></code>. Whenever <code>P<sub>j</sub> − P<sub>i</sub> &gt; F<sub>ij</sub></code>, traders buy at <em>i</em>, ship to <em>j</em>, and collect riskless arbitrage.</p>

<p>When an Indian farmer checks an app like AGMARKNET or e-NAM every morning <em>t</em>, the screen displays the <em>nominal screen spread</em>:</p>
<div class="math-formula">
  ΔP<sup>screen</sup><sub>i→j, t</sub> &nbsp;=&nbsp; P<sup>screen</sup><sub>j, t</sub> &nbsp;−&nbsp; P<sup>local</sup><sub>i, t</sub> &nbsp;&nbsp; (₹ per quintal, 1 qtl = 100 kg)
</div>

<p>Why do these numbers matter so urgently for a smallholder?</p>
<ul>
  <li>According to Government of India's <strong>MoSPI NSO NSS Report No. 587 (77th Round Situation Assessment Survey, PIB PRID 1753856)</strong>, Indian Potato and Onion farmers harvest an average of <strong>29.33–38.73 quintals per season</strong>—fixing our physical decision unit at <strong>one 30-quintal mini-truckload</strong> (<code>₹1/qtl = ₹30/truck</code>).</li>
  <li>The same national survey shows the average agricultural household earns only <strong>₹3,798/month</strong> in net crop income, while 50.2% of households carry an average debt of ₹74,121.</li>
  <li>So a ₹1,000/qtl screen spread across a 30-qtl truck looks like <strong>+₹30,000</strong> (~7.9 months of household net crop earnings) from a single dispatch!</li>
</ul>

<h2>1.2 First-Principles Decomposition: Four Hidden Frictions Between Screen and Auction Cash</h2>
<p>Between seeing a quote on the morning of day <em>t</em> and unloading a non-refrigerated open truck at destination <em>j</em> on arrival day <code>t + τ</code> (<code>τ ∈ &#123;1, 2, 3&#125;</code> days), four physical and institutional frictions erode that paper spread:</p>

<ol>
  <li><strong>Cultivar / Grade Mismatch ("Apples vs. Oranges on One Screen"):</strong> Portals highlight a single crop modal price (e.g., "Onion" or "Apple"). In reality, wholesale auctions clear strictly by variety (Red vs. Desi Onion; Badshah vs. Kufri Jyoti Potato) and grade (HP Apple Grade A vs. Grade B vs. Grade C). Arriving with Grade B when buyers bid only on Grade A forces distress liquidation at another variety's <code>Min_Price − 10%</code>.</li>
  <li><strong>Closed Gates &amp; Forward-Filled Stale Quotes:</strong> Indian APMC yards observe rotating weekly closing holidays and local mandi disruptions. Price apps often forward-fill quotes up to 7 days old. Across 63,040 naive dispatches, <strong>46.69%</strong> find zero exact-variety arrivals over 3 consecutive arrival mornings <code>[t+τ, t+τ+2]</code>, and <strong>58.94%</strong> either wait 1–2 days or miss exact-variety trading entirely.</li>
  <li><strong>Winding Highways &amp; Single-Lane Hill Roads (OSRM vs. Haversine):</strong> Straight-line Euclidean distance ("as the crow flies") systematically understates real rural and mountain highway distances and transit times. Per the <em>Government of Himachal Pradesh Economic Survey 2025–26 (Table 28)</em>, <strong>91.59% (39,465 / 43,091 km)</strong> of HP motorable roads are single-lane hill roads—forcing a <code>1.45×</code> freight penalty and slower transit speeds.</li>
  <li><strong>Biological <code>Q<sub>10</sub></code> Thermal/Rain Rot &amp; Arrival Price Reversion:</strong> Open mini-trucks hauling tomatoes or onions across 35–42°C summer plains or ≥35 mm monsoon downpours lose salable weight and grade en route. Meanwhile, during the 1–3 day haul <code>τ</code>, regional inflows attracted by the same high screen price frequently pull arrival prices downward (<em>arrival reversion</em>).</li>
</ol>

<div class="box box-numerical">
  <div class="box-title">Formal Definition: Phantom Spatial Arbitrage</div>
  <p style="margin-bottom:0;">An episode exhibits <strong>Phantom Spatial Arbitrage</strong> whenever nominal portal gain appears attractive (<code>ΔP<sup>screen</sup> &gt; ₹100/qtl</code>), yet realized net profit over local sale turns negative (<code>ΔNet<sub>i→j,t</sub> &lt; 0</code>) once exact-variety availability, OSRM freight + GoI state fees, biological spoilage, and arrival prices settle.</p>
</div>

<h2>1.3 Exact Numerical Anatomy Across Crops, States &amp; Distance Bands (<code>Exp 1</code>, <code>N = 63,040</code> Dispatches)</h2>
<p>Across all <code>69,526</code> shortlisted holdout episodes, naive screen chasing <code>B1</code> dispatches <code>63,040</code> times (90.67%). A large <strong>₹1,330.49/qtl</strong> headline screen spread loses <strong>71%</strong> of its value before cash reaches the farmer:</p>

<table>
  <tr>
    <th>Slice (Naive <code>B1</code> Dispatches)</th>
    <th class="num-col">Trips</th>
    <th class="num-col">Screen Spread</th>
    <th class="num-col">− Freight &amp; Fee</th>
    <th class="num-col">− Q10 Rot</th>
    <th class="num-col">− Traps &amp; Drops</th>
    <th class="num-col">= Net Realized</th>
    <th class="num-col">Loss Rate</th>
    <th class="num-col">Trap Rate</th>
    <th class="num-col">30-qtl (₹)</th>
  </tr>
  <tr class="highlight">
    <td><strong>Overall (All Holdout)</strong></td>
    <td class="num-col">63,040</td><td class="num-col">₹1,330.49</td><td class="num-col">-₹160.81</td><td class="num-col">-₹68.76</td><td class="num-col">-₹714.90</td><td class="num-col">₹386.02</td><td class="num-col"><strong>40.46%</strong></td><td class="num-col"><strong>58.94%</strong></td><td class="num-col">₹11,580.5</td>
  </tr>
  <tr><td>Crop: Apple</td><td class="num-col">7,784</td><td class="num-col">₹3,499.80</td><td class="num-col">-₹250.18</td><td class="num-col">-₹191.68</td><td class="num-col">-₹1,982.36</td><td class="num-col">₹1,075.58</td><td class="num-col">40.02%</td><td class="num-col">55.13%</td><td class="num-col">₹32,267.5</td></tr>
  <tr><td>Crop: Onion (Worst Loss Rate)</td><td class="num-col">20,355</td><td class="num-col">₹704.50</td><td class="num-col">-₹138.07</td><td class="num-col">-₹28.60</td><td class="num-col">-₹484.23</td><td class="num-col">₹53.61</td><td class="num-col"><strong>48.69%</strong></td><td class="num-col">57.26%</td><td class="num-col">₹1,608.2</td></tr>
  <tr><td>Crop: Potato</td><td class="num-col">15,354</td><td class="num-col">₹817.36</td><td class="num-col">-₹146.00</td><td class="num-col">-₹19.34</td><td class="num-col">-₹418.54</td><td class="num-col">₹233.47</td><td class="num-col">37.83%</td><td class="num-col">60.54%</td><td class="num-col">₹7,004.1</td></tr>
  <tr><td>Crop: Tomato</td><td class="num-col">19,547</td><td class="num-col">₹1,521.55</td><td class="num-col">-₹160.55</td><td class="num-col">-₹100.45</td><td class="num-col">-₹683.16</td><td class="num-col">₹577.39</td><td class="num-col">34.14%</td><td class="num-col">60.96%</td><td class="num-col">₹17,321.8</td></tr>
  <tr><td>State: Gujarat</td><td class="num-col">14,271</td><td class="num-col">₹1,371.78</td><td class="num-col">-₹152.59</td><td class="num-col">-₹64.95</td><td class="num-col">-₹701.72</td><td class="num-col">₹452.53</td><td class="num-col">34.44%</td><td class="num-col">58.63%</td><td class="num-col">₹13,575.8</td></tr>
  <tr><td>State: Himachal Pradesh</td><td class="num-col">8,575</td><td class="num-col">₹2,185.77</td><td class="num-col">-₹182.53</td><td class="num-col">-₹142.25</td><td class="num-col">-₹1,467.21</td><td class="num-col">₹393.77</td><td class="num-col">46.82%</td><td class="num-col">59.42%</td><td class="num-col">₹11,813.0</td></tr>
  <tr><td>State: Karnataka</td><td class="num-col">6,448</td><td class="num-col">₹1,162.71</td><td class="num-col">-₹144.94</td><td class="num-col">-₹58.21</td><td class="num-col">-₹614.40</td><td class="num-col">₹345.16</td><td class="num-col">42.74%</td><td class="num-col">60.03%</td><td class="num-col">₹10,354.7</td></tr>
  <tr><td>State: Madhya Pradesh (Worst!)</td><td class="num-col">5,821</td><td class="num-col">₹824.54</td><td class="num-col">-₹118.25</td><td class="num-col">-₹22.78</td><td class="num-col">-₹587.69</td><td class="num-col">₹95.82</td><td class="num-col"><strong>51.57%</strong></td><td class="num-col">59.70%</td><td class="num-col">₹2,874.5</td></tr>
  <tr><td>State: Maharashtra</td><td class="num-col">14,401</td><td class="num-col">₹1,477.73</td><td class="num-col">-₹157.62</td><td class="num-col">-₹62.23</td><td class="num-col">-₹635.55</td><td class="num-col">₹622.33</td><td class="num-col">38.87%</td><td class="num-col">61.76%</td><td class="num-col">₹18,669.8</td></tr>
  <tr><td>State: Uttar Pradesh</td><td class="num-col">13,524</td><td class="num-col">₹885.60</td><td class="num-col">-₹185.01</td><td class="num-col">-₹57.95</td><td class="num-col">-₹438.96</td><td class="num-col">₹203.67</td><td class="num-col">38.61%</td><td class="num-col">55.13%</td><td class="num-col">₹6,110.2</td></tr>
  <tr><td>Band: 15–100 km Short</td><td class="num-col">10,578</td><td class="num-col">₹1,109.91</td><td class="num-col">-₹86.06</td><td class="num-col">-₹44.94</td><td class="num-col">-₹688.35</td><td class="num-col">₹290.56</td><td class="num-col">40.41%</td><td class="num-col">52.79%</td><td class="num-col">₹8,716.8</td></tr>
  <tr><td>Band: 100–250 km Medium</td><td class="num-col">29,560</td><td class="num-col">₹1,328.34</td><td class="num-col">-₹140.65</td><td class="num-col">-₹58.66</td><td class="num-col">-₹668.25</td><td class="num-col">₹460.78</td><td class="num-col">38.35%</td><td class="num-col">58.01%</td><td class="num-col">₹13,823.5</td></tr>
  <tr><td>Band: 250–500 km Long-Haul</td><td class="num-col">22,902</td><td class="num-col">₹1,435.14</td><td class="num-col">-₹221.36</td><td class="num-col">-₹92.80</td><td class="num-col">-₹787.37</td><td class="num-col">₹333.60</td><td class="num-col">43.21%</td><td class="num-col"><strong>62.99%</strong></td><td class="num-col">₹10,008.1</td></tr>
</table>

<p style="font-size:8.4pt;"><strong>Arithmetic Bridge:</strong> Across all <code>69,526</code> episodes, <code>B1</code> dispatches 90.67% of days and stays home (₹0) 9.33% of days, giving unconditional mean <code>₹386.02 × 0.9067 = <strong>₹350.01/qtl</strong></code>. Worst-10% <code>CVaR_10%</code> is <strong>-₹1,062.66/qtl</strong> = <strong>-₹31,879.8</strong> on one 30-qtl load (8.4× monthly household net crop income).</p>

<div class="figure-box">
  <img src="{fig1}" alt="Figure 1: Phantom Arbitrage Anatomy"/>
  <div class="figure-caption"><strong>Figure 1 (Exp 1):</strong> Decomposition of Phantom Spatial Arbitrage across states, crops, and distance bands on <code>N = 63,040</code> naive dispatches. Note that observed AGMARKNET traps &amp; arrival reversion (-₹714.90/qtl) dominate modeled spoilage (-₹68.76/qtl) by more than 10×.</div>
</div>
"""


def sec_ch2_literature_deep_dive() -> str:
    return """
<div class="page-break"></div>
<h1 class="chapter-title">Chapter 2: Deep Dive Into the Most Relevant Research (20 Core + 8 Mandi Papers)</h1>

<p>In an M.Tech defense, your literature review is tested on precision: <em>What exact theorem, econometric design, or algorithm did each paper invent, and where does that method break on Indian horticultural dispatch?</em> Below is the complete paper-by-paper breakdown across our 5 foundational pillars (14 Stage-I papers + 6 Stage-II mechanistic/uncertainty/liquidity citations).</p>

<h2>2.1 Pillar I: Spatial Arbitrage &amp; Indian Mandi Market Economics</h2>

<div class="paper-card">
  <div class="paper-title">1. Robert Jensen (2007) — "The Digital Provide: Information (Technology), Market Performance, and Welfare in the South Indian Fisheries Sector"</div>
  <div class="paper-meta"><em>The Quarterly Journal of Economics (QJE)</em>, 122(3):879–924 • DOI: <code>10.1162/qjec.122.3.879</code></div>
  <p><strong>Intuition &amp; Method:</strong> Difference-in-differences natural experiment tracking Kerala sardine fishermen (1997–2001) across sequential mobile-tower rollouts. Before mobile coverage, boats landed fish at home beaches with zero knowledge of neighboring landing ports—leading to 5–8% dumped catch in saturated markets while nearby ports went empty. Once phones arrived at sea, captains called ahead and arbitrage equalized coastal prices.</p>
  <p><strong>Exact Gap Left Open:</strong> Sardines are homogeneous and coastal sea hops had negligible quality mismatch, closed-yard holidays, or mountainous single-lane road congestion. Inland Indian APMC mandis violate every one of Jensen's implicit frictionless assumptions.</p>
</div>

<div class="paper-card">
  <div class="paper-title">2. C. S. C. Sekhar (2012) — "Agricultural Market Integration in India: An Analysis of Select Commodities"</div>
  <div class="paper-meta"><em>Food Policy</em>, 37(3):309–322 • DOI: <code>10.1016/j.foodpol.2012.03.002</code></div>
  <p><strong>Intuition &amp; Method:</strong> Applies Johansen cointegration and error-correction econometric tests across Indian wholesale price series (gram, oilseeds, rice, wheat). Demonstrates that inter-state regulatory and physical barriers keep Indian wholesale markets segmented rather than frictionlessly integrated.</p>
  <p><strong>Exact Gap Left Open:</strong> Long-run monthly/weekly cointegration coefficients cannot diagnose why a 30-qtl truck dispatched <em>tomorrow morning</em> crashes into a stale variety quote or closed gate.</p>
</div>

<div class="paper-card">
  <div class="paper-title">3. Shoumitro Chatterjee &amp; Devesh Kapur (2016/2017) — "Six Puzzles in Indian Agriculture"</div>
  <div class="paper-meta"><em>India Policy Forum (NCAER/SAGE)</em>, 13(1):185–229 • Price Variation &amp; Market Dispersion</div>
  <p><strong>Intuition &amp; Method:</strong> Granular mandi-level dispersion study showing immense spatial price spreads persist even across nearby Indian districts after adjusting for rough transport costs, attributing the wedge to APMC laws, intermediaries, and unobserved quality.</p>
  <p><strong>Exact Gap Left Open:</strong> Stops at macro documentation; does not decompose daily operational screen spreads into exact-variety mismatch, OSRM routing friction, ERA5 thermal spoilage, and arrival-day execution risk.</p>
</div>

<div class="paper-card">
  <div class="paper-title">4. Negi, Birthal, Roy, &amp; Khan (2018) — "Farmers' Choice of Market Channels &amp; Producer Prices in India"</div>
  <div class="paper-meta"><em>Food Policy</em>, 81:106–121 • DOI: <code>10.1016/j.foodpol.2018.10.008</code></div>
  <p><strong>Intuition &amp; Method:</strong> Nationally representative farm household regression analysis proving that poor road connectivity and weak market information jointly trap Indian smallholders in low-margin village-trader sales rather than competitive wholesale mandis.</p>
  <p><strong>Exact Gap Left Open:</strong> Cross-sectional household surveys cannot power real-time route selection, road-hour transit spoilage accounting, or uncertainty-calibrated local abstention.</p>
</div>

<div class="paper-card">
  <div class="paper-title">5. Madaan, Sharma, Khandelwal, Goel, Singla, &amp; Seth (2019) — "Price Forecasting &amp; Anomaly Detection for Agricultural Commodities in India"</div>
  <div class="paper-meta"><em>Proceedings of ACM COMPASS '19</em>, pp. 52–64 • DOI: <code>10.1145/3314344.3332488</code></div>
  <p><strong>Intuition &amp; Method:</strong> Flagship CS/ICTD study mining multi-year AGMARKNET onion and potato series to forecast point prices and flag hoarding/supply anomalies across mandis.</p>
  <p><strong>Exact Gap Left Open:</strong> Evaluates price forecasting MSE and anomaly alerts—NOT executable spatial dispatch under closed yards, variety mismatches, OSRM highways, Q10 heat shrinkage, or asymmetric selective refusal.</p>
</div>

<h2>2.2 Pillar II: Indian Post-Harvest Loss Biology, Climate Reanalysis &amp; Road Routing</h2>

<div class="paper-card">
  <div class="paper-title">6. Jha et al. (2015, ICAR-CIPHET) &amp; 7. NABCONS / MoFPI (2022, PIB PRID 2151371) — National Post-Harvest Loss Surveys</div>
  <div class="paper-meta">ICAR-CIPHET Ludhiana (45+ crops, 173 pp.) • MoFPI Final Audit (54 crops across 292 districts, Dec 2022)</div>
  <p><strong>Intuition &amp; Official Anchors:</strong> India's statutory empirical audits measuring physical weight/quality shrinkage via direct farm-to-retail weighments across 15 agro-climatic zones (fruits 6.02–15.05%, vegetables 4.87–11.61%). Crucially, NABCONS Annexure-II Table-2 isolates <strong>market/transport-stage losses</strong>: Tomato <code>3.25%</code>, Onion <code>1.96%</code>, Apple <code>1.64%</code>, Potato <code>0.86%</code>.</p>
  <p><strong>Exact Gap Left Open:</strong> Macro annual national averages cannot dynamically scale with corridor transit hours, 40°C summer spikes, or 35 mm rainstorms on a specific morning dispatch.</p>
</div>

<div class="paper-card">
  <div class="paper-title">8. Hersbach et al. (2020, QJRMS) — ERA5 Global Reanalysis [&amp; Sparks 2018 NASA POWER; Luxen &amp; Vetter 2011 OSRM]</div>
  <div class="paper-meta"><em>QJRMS</em> 146(730):1999–2049 (DOI: <code>10.1002/qj.3803</code>) • Sparks <em>JOSS</em> (NASA POWER) • Luxen &amp; Vetter <em>ACM SIGSPATIAL</em> (OSRM)</div>
  <p><strong>Intuition &amp; Method:</strong> ERA5 assimilates atmospheric physics onto a gap-free 0.1°/0.25° global grid (matching NASA POWER 0.5° for 2017–2023), solving missing rural weather-station coverage across India; OSRM uses Contraction Hierarchies on OpenStreetMap road graphs to query real turning highways in sub-millisecond speed.</p>
  <p><strong>Exact Gap Left Open:</strong> Meteorological grids and contraction-hierarchy routers existed separately—<code>MandiGuard</code> couples them causally (forecasted NWP at decision time vs. realized ERA5 in evaluation) to price corridor Q10 rot.</p>
</div>

<h2>2.3 Pillar III: Selective Prediction, Asymmetric Reject Option &amp; Conformal Uncertainty</h2>

<div class="paper-card">
  <div class="paper-title">9. C. K. Chow (1970) — "On Optimum Recognition Error and Reject Tradeoff"</div>
  <div class="paper-meta"><em>IEEE Transactions on Information Theory</em>, 16(1):41–46 • DOI: <code>10.1109/TIT.1970.1054406</code></div>
  <p><strong>First-Principles Math:</strong> Given decision loss <code>c_error</code> and abstention cost <code>c_reject</code>, Chow proved the Bayes-optimal predictor abstains whenever maximum posterior certainty falls below <code>1 − (c_reject / c_error)</code>. In dispatch, a false-positive truck crash costs sunk freight + rot + diversion (<code>c_error ≫ 0</code>), whereas refusing returns safe local price (<code>c_reject = 0</code> net opportunity).</p>
</div>

<div class="paper-card">
  <div class="paper-title">10. Franc, Průša, &amp; Voráček (2023, JMLR) &amp; 11. Angelopoulos &amp; Bates (2023, FnTML) [+ Gibbs &amp; Candès 2021 ACI]</div>
  <div class="paper-meta">Franc et al.: <em>JMLR</em> 24(11):1–49 • Angelopoulos &amp; Bates: <em>FnTML</em> 16(4):494–591 (DOI: <code>10.1561/2200000101</code>)</div>
  <p><strong>Intuition &amp; Honest Gap:</strong> Franc et al. prove risk–coverage optimal selective rules rely on monotonic calibrated uncertainty scores. Angelopoulos &amp; Bates formalize distribution-free split conformal prediction: subtracting the <code>(1−α)</code> empirical residual quantile wraps any black-box tree in guaranteed coverage <em>under i.i.d. exchangeability</em>. Because daily agricultural prices shift across harvest/monsoon regimes, we explicitly treat conformal bounds as empirical chronological calibration verified out-of-sample (<code>78.85%</code> val / <code>79.07%</code> holdout) and test Gibbs &amp; Candès (2021) Adaptive Conformal Inference (<code>ACI</code>) in Appendix A.1.</p>
</div>

<h2>2.4 Pillar IV: Budgeted Feature Acquisition &amp; Uncertainty-Gated Tool Calling</h2>

<div class="paper-card">
  <div class="paper-title">12. Yao et al. (2023, ICLR — ReAct), 13. Kachuee et al. (2019, ICLR — Opportunistic Learning), 14. Han et al. (2024, ACL — UALA)</div>
  <div class="paper-meta">ReAct: <em>ICLR '23</em> (Notable-Top-5%) • Opportunistic Learning: <em>ICLR '19</em> • UALA: <em>Findings of ACL '24</em>, pp. 6662–6685</div>
  <p><strong>Intuition &amp; Design Bridge:</strong> Yao et al. showed tool grounding eliminates hallucinations—but polling every external API upfront wastes budget. Kachuee et al. formalized acquiring costly features sequentially under test-time query budgets, while Han et al. (UALA) proved uncalibrated confidence fails unless gated by calibrated uncertainty quantiles on held-out calibration buffers. <code>MandiGuard</code> implements this cleanly—without LLM fragility or latency—as an ascending-cost deterministic cascade (<code>T1 → T2 → T3 → T4</code>).</p>
</div>

<h2>2.4b Pillar V: Selective Labels, Heteroscedastic Conformal, CRC &amp; Grade Liquidity (6 Stage-II Papers)</h2>

<div class="paper-card">
  <div class="paper-title">15. Lei et al. (2018, <em>JASA</em>) &amp; 16. Romano, Patterson, &amp; Candès (2019, <em>NeurIPS</em> — CQR)</div>
  <div class="paper-meta">Lei et al.: <em>JASA</em> 113(523):1094–1111 (<code>10.1080/01621459.2017.1307116</code>) • Romano et al.: <em>NeurIPS 32</em>:3538–3548</div>
  <p><strong>Intuition &amp; Gap Addressed:</strong> Proves why constant/pooled split conformal residual quantiles only satisfy <em>marginal</em> coverage while failing <em>conditional</em> coverage when input noise variance is heteroscedastic (motivating CQR). In Stage II (<code>Exp 16</code>), we quantify how pooled cushions inside Stage-I mandis produce a 21.07–22.66 pp coverage swing between calm <code>Q1</code> (90.46% Holdout) and volatile <code>Q4</code> (67.80% Holdout) markets.</p>
</div>

<div class="paper-card">
  <div class="paper-title">17. Angelopoulos, Bates, Fisch, Lei, &amp; Schuster (2024, <em>ICLR Spotlight</em> — Conformal Risk Control)</div>
  <div class="paper-meta"><em>ICLR 2024</em> (<a href="https://openreview.net/forum?id=uPD0kqYEfS">OpenReview</a>; <code>arXiv:2208.02814</code>)</div>
  <p><strong>Intuition &amp; Honest Method Boundary:</strong> Generalizes conformal calibration beyond 0–1 errors to monotone bounded loss functions via empirical threshold sweeping <code>(n_loss + 1)/(n_disp + 1) ≤ β</code>. Stage-II <code>MandiGuard-CRC</code> adapts this ratio to calibrate tail risk weight <code>λ* = 0.15</code> strictly on <code>Val_2025H1</code>—explicitly noting we do <strong>not</strong> claim Theorem 1 exchangeability guarantees under non-exchangeable monsoon shifts and post-selection denominators.</p>
</div>

<div class="paper-card">
  <div class="paper-title">18. Lakkaraju, Kleinberg, Leskovec, Ludwig, &amp; Mullainathan (2017, <em>ACM KDD</em> — Selective Labels)</div>
  <div class="paper-meta"><em>KDD '17</em>, pp. 275–284 • DOI: <code>10.1145/3097983.3098066</code></div>
  <p><strong>Intuition &amp; Domain Autopsy:</strong> Formalizes how fitting or auditing models only on observed ("uncensored") cases creates severe blind spots when selection correlates with missingness. <code>Exp 16</code> proves Stage-I's <code>dropna(target_ret)</code> discarded 55.83% of raw 2024 routes and understated 3-day Q20 downside drops up to <strong>2.54×</strong>.</p>
</div>

<div class="paper-card">
  <div class="paper-title">19. Aparajita Goyal (2010, <em>AEJ: Applied Economics</em>) &amp; 20. Levi et al. (2020, <em>PNAS</em>)</div>
  <div class="paper-meta">Goyal: <em>AEJ: Applied</em> 2(3):22–45 (<code>10.1257/app.2.3.22</code>) • Levi et al.: <em>PNAS</em> 117(5):2366–2371 (<code>10.1073/pnas.1906854117</code>)</div>
  <p><strong>Intuition &amp; Domain Autopsy:</strong> Proves in rural MP soy kiosks and Karnataka unified bidding platforms (<code>ReMS</code>) that auction liquidity &amp; grading fragmentation govern farmer realization. Explains why sparse Apple sub-grade reporting (<code>Grade A</code>/<code>Range-1</code>) fooled Stage-I <code>T1</code> rolling counters into blocking <strong>77.82%</strong> of holdout <code>B2</code>-profitable Apple opportunities.</p>
</div>

<h2>2.5 Direct Audit vs. Closest Prior Mandi Systems &amp; The Defensible Axes of Novelty</h2>
<table>
  <tr><th>Prior Work</th><th>What It Built</th><th>Exact Missing Piece Addressed by <code>MandiGuard</code></th></tr>
  <tr><td><strong>Mitra et al. (2018, <em>REStat</em>)</strong></td><td>Bengal potato RCT giving village price info</td><td>Proved raw price alerts fail without executable safe market routing &amp; buyer verification.</td></tr>
  <tr><td><strong>Ma et al. (2019, <em>ICTD</em>) &amp; Deka (2026)</strong></td><td>Missing AGMARKNET price imputation</td><td>Imputes missing entries statistically instead of detecting operational closed-yard traps (<code>T1</code>).</td></tr>
  <tr><td><strong>Guo, Woodruff, &amp; Yadav (2020, <em>AAAI</em>)</strong></td><td>CNN forecasting + closure note</td><td>Strips non-trading days as preprocessing noise instead of modeling arrival-day yard closures.</td></tr>
  <tr><td><strong><em>AgriMarket AI</em> (Divyashree &amp; Biradar, 2026)</strong></td><td>XGBoost profit ranker using <strong>Haversine</strong></td><td>Closest baseline (<code>B1/B3</code> family): lacks OSRM roads, exact variety, closed yards, Q10 rot, LCB.</td></tr>
  <tr><td><strong><em>Mandi Cast</em> (Manimegalai et al., 2026)</strong></td><td>SARIMA/XGBoost + OpenWeatherMap</td><td>Uses weather only to forecast price MSE, not transit biological decay or selective refusal.</td></tr>
</table>

<div class="box box-math">
  <div class="box-title">Borrowed vs. Novel Matrix — Two-Stage Defensible M.Tech Contributions (<code>NOVELTY_AUDIT.md</code>)</div>
  <ol style="margin-bottom:0;">
    <li><strong>Axis 1 (Empirical Measurement &amp; Dual-Tier Official Parity):</strong> Multi-state (6 states × 4 crops × 2017–2026) decomposition of Phantom Spatial Arbitrage across variety mismatch, closed yards, OSRM friction, and weather rot—audited via Dual-Tier <code>Exp 14</code> (<code>172</code> XML + <code>2,042</code> 149-day AGMARKNET 2.0 keys at 100.00% Min/Max/Modal parity).</li>
    <li><strong>Axis 2 (Stage-I Pre-Registered Selective Dispatch):</strong> Shifts mandi ML from point MSE (<code>B3</code>) to deterministic 4-step gating (<code>T1→T2→T3→T4</code>) + frozen 80% causal conformal <code>LCB</code> (<code>H1, H3, H4</code> confirmed; Dual-View <code>Exp 15</code>).</li>
    <li><strong>Axis 3 (Stage-II Mechanistic Autopsy — <code>[POST-DIAGNOSTIC]</code>):</strong> Pinpoints why Stage I tied <code>B2</code> (<code>H2</code>) and under-dispatched HP Apples via three verified mechanisms (<code>Exp 16</code>): Censored-Arrival Bias (up to <code>2.54×</code>), Heteroscedastic Coverage Collapse (<code>90.46%→67.80%</code>), and Sub-Grade <code>T1</code> Sparsity (<code>77.82%</code> vs <code>22.18%</code>).</li>
    <li><strong>Axis 4 (Stage-II Validation-Calibrated Uncensored Risk Control — <code>MandiGuard-CRC</code>):</strong> Dual-head estimators trained directly on uncensored <code>Y_full</code> + <code>Val_2025H1</code>-frozen penalty (<code>λ* = 0.15</code>) + grade-aware <code>T1</code> lift holdout profit to <strong>₹479.17/qtl</strong> (+₹32.51 vs <code>B2</code>, <code>p=0.0016</code>), win trap-free <code>N=10,162</code> open yards (₹533.75), and boost HP Apple +34.2% (₹812.08).</li>
  </ol>
</div>
"""


def sec_ch3_under_the_hood() -> str:
    return r"""
<div class="page-break"></div>
<h1 class="chapter-title">Chapter 3: Under the Hood — Math, Physics, HGBR Trees, Conformal LCB &amp; Worked Numerics</h1>

<h2>3.1 Chronological Split Firewall &amp; Causal Feature Mechanics</h2>
<p>Before evaluating any dispatch rule, 2024–2026 panel data (260,043 daily market rows across 178 core yards ranked strictly on 2024 trading days to kill survivorship bias) passes through a hard temporal firewall:</p>

<div class="svg-box">
  <svg width="100%" viewBox="0 0 800 96" xmlns="http://www.w3.org/2000/svg" style="font-family: sans-serif;">
    <rect x="10" y="12" width="215" height="72" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
    <text x="117" y="30" text-anchor="middle" font-size="9.8" font-weight="bold" fill="#1e3a8a">Train_2024 (Jan–Dec 2024)</text>
    <text x="117" y="44" text-anchor="middle" font-size="8.3" fill="#1e40af">701,932 corridor rows</text>
    <text x="117" y="58" text-anchor="middle" font-size="8.0" fill="#334155">Jan–Sep: Fit temporary HGBR</text>
    <text x="117" y="70" text-anchor="middle" font-size="8.0" fill="#334155">Oct–Dec: Seed 400-sample LCB buffer</text>
    <line x1="225" y1="48" x2="248" y2="48" stroke="#334155" stroke-width="1.8"/>
    <rect x="250" y="12" width="215" height="72" rx="6" fill="#fefce8" stroke="#ca8a04" stroke-width="1.5"/>
    <text x="357" y="30" text-anchor="middle" font-size="9.8" font-weight="bold" fill="#854d0e">Val_2025H1 (Jan–May 2025)</text>
    <text x="357" y="44" text-anchor="middle" font-size="8.3" fill="#a16207">280,697 rows (42,794 episodes)</text>
    <text x="357" y="58" text-anchor="middle" font-size="8.0" fill="#334155">Sweep {50,100,150,200,250}</text>
    <text x="357" y="70" text-anchor="middle" font-size="8.0" font-weight="bold" fill="#854d0e">Freeze Margin = ₹50/qtl (78.85% cov)</text>
    <rect x="478" y="6" width="44" height="84" rx="4" fill="#dc2626"/>
    <text x="500" y="36" text-anchor="middle" font-size="8.3" font-weight="bold" fill="#ffffff">GIT</text>
    <text x="500" y="49" text-anchor="middle" font-size="8.3" font-weight="bold" fill="#ffffff">WALL</text>
    <text x="500" y="62" text-anchor="middle" font-size="7.3" fill="#fecaca">e421d15</text>
    <rect x="534" y="12" width="256" height="72" rx="6" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
    <text x="662" y="30" text-anchor="middle" font-size="9.8" font-weight="bold" fill="#14532d">Holdout_2025_2026 (Jun '25–Apr '26)</text>
    <text x="662" y="44" text-anchor="middle" font-size="8.3" fill="#15803d">69,526 shortlisted episodes (468,816 pairs)</text>
    <text x="662" y="58" text-anchor="middle" font-size="8.0" fill="#334155">Frozen 2024 HGBR weights (never refit)</text>
    <text x="662" y="70" text-anchor="middle" font-size="8.0" fill="#334155">Buffer updates ONLY when arrival_date ≤ t</text>
  </svg>
</div>

<h2>3.2 Step 0 &amp; Tool T1: Free Shortlist and Yard Vitality Gate (<code>verify_vitality_and_variety</code>)</h2>
<p><strong>Step 0 (0 API Calls):</strong> Compare today's local exact-variety price <code>P<sup>local</sup><sub>i,t</sub></code> against headline ≤7-day modal prices at all intra-state mandis within <code>15 ≤ road_km ≤ 500 km</code>. Retain those with <code>screen_spread = P<sup>screen</sup><sub>j,t</sub> − P<sup>local</sup><sub>i,t</sub> &gt; ₹100/qtl</code>, and keep top <code>K<sub>max</sub> = 5</code>.</p>
<p><strong>Tool T1 (+1 API Call per candidate):</strong> Queries exact-variety trading history at yard <em>j</em> up to date <em>t</em> (never using future dates). Must satisfy all 3 rules simultaneously (<code>mandiguard_agent.py:137-144</code>):</p>
<div class="math-formula">
  T1_OK &nbsp;⟺&nbsp; (<code>dest_age_days ≤ 3</code>) &nbsp;∧&nbsp; (<code>dest_open_prob_14d ≥ 0.50</code>) &nbsp;∧&nbsp; (<code>dest_dow_open_rate ≥ 0.35</code>)
</div>
<p style="font-size:8.6pt;">Where <code>dest_dow_open_rate = (k + 1) / (n + 2)</code> is the Laplace-smoothed historical probability that yard <em>j</em> actively trades that exact variety on target arrival weekday <code>(dow(t) + τ) mod 7</code> over its last <code>n ≤ 12</code> occurrences prior to day <em>t</em>. For example, if over the past 10 Sundays a yard opened only 1 time, <code>(1+1)/(10+2) = 0.167 &lt; 0.35</code> → pruned immediately (<code>CLOSED_YARD_RISK</code>).</p>

<h2>3.3 Tool T2: OSRM Highway Freight, Transit Lag &amp; GoI Statutory Fees (<code>compute_freight_inr</code>)</h2>
<p>OSRM routing returns true highway distance <code>d<sub>ij</sub><sup>road</sup></code> and car travel hours. Multiplied by <code>1.35×</code> heavy truck factor (plus <code>1.25×</code> HP mountain factor) and <code>4.0 h</code> loading/auction buffer gives <code>truck_hours</code>, mapping morning dispatch into discrete auction arrival lags: <code>τ = 1d</code> (≤4.5 h), <code>τ = 2d</code> (4.5–8.5 h), or <code>τ = 3d</code> (&gt;8.5 h).</p>
<div class="math-formula">
  F<sub>ij</sub> &nbsp;=&nbsp; (35 &nbsp;+&nbsp; 0.45 &middot; m<sub>HP</sub> &middot; d<sub>ij</sub><sup>road</sup>) &middot; mult<sub>freight</sub> &nbsp;+&nbsp; &#120128;[cross_district] &middot; γ<sub>state, crop</sub> &middot; P<sup>local</sup><sub>i,t</sub>
</div>
<p style="font-size:8.6pt;"><strong>GoI Parameters:</strong> <code>m<sub>HP</sub> = 1.45</code> in HP (91.59% single-lane roads, GoHP Survey 2025–26), <code>1.0</code> elsewhere. Statutory fee <code>γ<sub>state,crop</sub></code> (GoI PIB 154554): <strong>0.5%</strong> (KA, GJ, HP-Veg), <strong>1.0%</strong> (MH, HP-Apple), <strong>1.5%</strong> (MP, UP). Prunes immediately if <code>P<sup>ref</sup><sub>j,t</sub> − P<sup>local</sup><sub>i,t</sub> − F<sub>ij</sub> ≤ 0</code> (<code>FREIGHT_EXCEEDS_SPREAD</code>).</p>
<p style="font-size:8.6pt;"><strong>Worked Numerics:</strong> MP Tomato (200 km, ₹1,400 local): <code>35 + 0.45×1.0×200 + 0.015×1,400 = <strong>₹146.00/qtl</strong></code>. HP Apple (180 km mountain road, ₹4,000 local): <code>35 + 0.45×1.45×180 + 0.010×4,000 = 35 + 117.45 + 40 = <strong>₹192.45/qtl</strong></code>.</p>

<h2>3.4 Tool T3: Q<sub>10</sub> Biological Thermal Spoilage &amp; Monsoon Rain Penalty (<code>compute_spoilage_fraction</code>)</h2>
<p>Anchored directly to MoFPI/NABCONS (2022) 24-hour market-level loss rates at 20°C (Tomato <code>3.25%</code>, Onion <code>1.96%</code>, Apple <code>1.64%</code>, Potato <code>0.86%</code>), biological respiration scales exponentially via <code>Q<sub>10</sub> = 2</code> per +10°C rise plus excess humidity (&gt;70% RH) and heavy rain (≥35 mm/day):</p>
<div class="math-formula">
  Q<sub>10</sub> = 2<sup>(T<sub>eff</sub> − 20)/10</sup> &nbsp;|&nbsp; F<sub>RH</sub> = 1 + 0.25·max(0, <span class="frac"><span class="num">RH<sub>eff</sub>−70</span><span>30</span></span>) &nbsp;|&nbsp; s<sub>ij</sub>(w) = min&#40;0.55, [s<sub>0,c</sub>·<span class="frac"><span class="num">h<sub>ij</sub>+24w</span><span>24</span></span>·Q<sub>10</sub>·F<sub>RH</sub> + 0.02·&#120128;(Rain≥35)]·mult<sub>spoil</sub>&#41;
</div>
<p style="font-size:8.6pt;">At <code>Rain ≥ 35 mm/day</code>, T3 also subtracts <code>RainPen = 0.50 × P<sup>ref</sup> × intra_spread<sub>14d</sub></code> (price shift toward yard minimum). <strong>Example (40°C May MP Tomato, 6 h drive, dry 50% RH):</strong> <code>Q<sub>10</sub> = 2² = 4×</code>, <code>s<sub>hat</sub> = 0.0325 × (6/24) × 4 × 1 = <strong>3.25%</strong></code> (<code>-₹65/qtl</code> on ₹2,000). Under 42 mm storm at 30°C (8h, 85% RH): <code>0.0325×(8/24)×2×1.125 + 0.02 = <strong>4.44%</strong></code> plus 50% grade downgrade!</p>

<h2>3.5 Tool T4 (Part A): Under the Hood of <code>HistGradientBoostingRegressor</code> (17 Causal Features)</h2>
<p>Instead of predicting raw ₹/qtl (uncomparable across ₹600 potatoes and ₹10,000 apples), we predict bounded arrival return <code>y = clip((P<sup>arr_d0</sup> − P<sup>ref</sup>)/P<sup>ref</sup>, -0.60, +0.80)</code> from <strong>17 strictly causal features (dates ≤ t)</strong>:</p>
<table>
  <tr><th>Category</th><th>Exact Features in <code>FEATURE_COLS</code></th><th>Physical / Market Signal (Strictly Computed Using ≤ t Only)</th></tr>
  <tr><td>Logistics/Vitality (4)</td><td><code>tau_days</code>, <code>dest_age_days</code>, <code>dest_open_prob_14d</code>, <code>dest_dow_open_rate</code></td><td>Arrival lag {1,2,3}, quote staleness, 14d open fraction, arrival-weekday activity rate.</td></tr>
  <tr><td>Momentum &amp; Risk (7)</td><td><code>dest_ret_1d</code>, <code>3d</code>, <code>7d</code>, <code>14d</code>; <code>dest_vol_14d</code>, <code>intra_spread_14d</code>, <code>level_ratio_30d</code></td><td>Price trend &amp; mean-reversion spike ratio (<code>P<sub>t</sub>/median_30d</code>), 14d volatility, <code>(Modal−Min)/Modal</code>.</td></tr>
  <tr><td>Macro &amp; Encodings (6)</td><td><code>state_hub_ret_7d</code>, <code>arrival_dow</code>, <code>month_sin</code>, <code>month_cos</code>, <code>commodity_code</code>, <code>state_code</code></td><td>Statewide 7d momentum, cyclical seasonality, native integer categories for trees.</td></tr>
</table>

<div class="box box-math">
  <div class="box-title">How Histogram GBDT Works Inside <code>arrival_forecaster.py</code> (255-Bin Speed + L2 Leaves)</div>
  <p style="margin-bottom:4px;">Hyperparameters: <code>max_iter = 180</code> trees, <code>max_depth = 5</code>, <code>min_samples_leaf = 80</code>, learning rate <code>η = 0.05</code>, L2 penalty <code>λ = 1.0</code>. Before tree building starts, each numeric column is quantized into ≤255 histogram bins once—reducing split search from <code>O(N log N)</code> to <code>O(255)</code> and giving <strong>0.09 ms/query</strong> CPU speed.</p>
  <p style="margin-bottom:0;"><strong>Numeric Step Trace (4 Sample Trips):</strong> Suppose true arrival returns are <code>y = [-0.10, -0.05, +0.02, +0.05]</code>.<br/>
  1. <code>F<sub>0</sub> = mean(y) = -0.02</code> → residuals (negative gradients of <code>½(y−F)²</code>) are <code>g = [-0.08, -0.03, +0.04, +0.07]</code>.<br/>
  2. Split bin <code>dest_level_ratio_30d &gt; 1.25</code> groups spiked markets <code>{-0.08, -0.03}</code> left and stable markets <code>{+0.04, +0.07}</code> right.<br/>
  3. L2-regularized optimal leaf weight is <code>w = (∑ g<sub>i</sub>) / (n<sub>leaf</sub> + λ)</code>: Left = <code>(-0.11)/(2+1) = -0.0367</code>, Right = <code>(+0.11)/3 = +0.0367</code>.<br/>
  4. Shrinkage update: <code>F<sub>1</sub> = -0.02 + 0.05 × (-0.0367) = -0.0218</code>. Repeating 180 trees smoothly captures non-linear price reversion!</p>
</div>

<h2>3.6 Tool T4 (Part B): Causal Conformal 80% LCB, Min-Heap Firewall &amp; Dynamic ACI</h2>

<div class="svg-box">
  <div class="box-title" style="text-align:left;">Inside Tool T4: Min-Heap Maturation Firewall + Conformal Asymmetric Safety Buffer</div>
  <svg width="100%" viewBox="0 0 800 128" xmlns="http://www.w3.org/2000/svg" style="font-family: sans-serif;">
    <rect x="8" y="16" width="165" height="92" rx="6" fill="#f8fafc" stroke="#475569" stroke-width="1.4"/>
    <text x="90" y="34" text-anchor="middle" font-size="9.5" font-weight="bold" fill="#0f172a">Pending Arrival Heap</text>
    <text x="90" y="49" text-anchor="middle" font-size="8.0" fill="#334155">Keyed by arrival_date (t+τ)</text>
    <text x="90" y="64" text-anchor="middle" font-size="8.0" fill="#dc2626">Locked if arrival_date &gt; t</text>
    <text x="90" y="79" text-anchor="middle" font-size="8.0" fill="#16a34a">Pops ONLY if arrival_date ≤ t</text>
    <text x="90" y="96" text-anchor="middle" font-size="7.8" fill="#475569">(Zero Future Feedback Leak)</text>

    <line x1="173" y1="62" x2="198" y2="62" stroke="#0f3d5e" stroke-width="1.5" marker-end="url(#arrow)"/>

    <rect x="200" y="16" width="190" height="92" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="1.4"/>
    <text x="295" y="34" text-anchor="middle" font-size="9.5" font-weight="bold" fill="#1e3a8a">Per-Crop Deque (W = 400)</text>
    <text x="295" y="50" text-anchor="middle" font-size="8.2" fill="#1e40af">Stores e_k = y_hat − y_real</text>
    <text x="295" y="65" text-anchor="middle" font-size="8.0" fill="#334155">Sorted errors: [-0.04, ..., +0.08, +0.14]</text>
    <text x="295" y="81" text-anchor="middle" font-size="8.4" font-weight="bold" fill="#0f3d5e">Extract 80th pct: q̂_0.80 = 0.08</text>
    <text x="295" y="96" text-anchor="middle" font-size="7.8" fill="#475569">(Empirical cov: 78.85% Val, 79.07% Test)</text>

    <line x1="390" y1="62" x2="415" y2="62" stroke="#0f3d5e" stroke-width="1.5" marker-end="url(#arrow)"/>

    <rect x="417" y="16" width="185" height="92" rx="6" fill="#dcfce7" stroke="#16a34a" stroke-width="1.5"/>
    <text x="509" y="34" text-anchor="middle" font-size="9.5" font-weight="bold" fill="#14532d">Conservative Floor P^LCB</text>
    <text x="509" y="50" text-anchor="middle" font-size="8.2" fill="#15803d">lcb_ret = y_hat − max(0, q̂_0.80)</text>
    <text x="509" y="66" text-anchor="middle" font-size="8.2" fill="#1e293b">P^LCB_arr = P^ref × (1 + lcb_ret)</text>
    <text x="509" y="82" text-anchor="middle" font-size="8.0" fill="#1e293b">Net_LCB = P^LCB·(1−s) − Rain − F − P_loc</text>
    <text x="509" y="97" text-anchor="middle" font-size="8.2" font-weight="bold" fill="#14532d">Dispatch iff Best Net_LCB &gt; ₹50/qtl</text>

    <line x1="602" y1="62" x2="625" y2="62" stroke="#0f3d5e" stroke-width="1.5" marker-end="url(#arrow)"/>

    <rect x="627" y="16" width="165" height="92" rx="6" fill="#fefce8" stroke="#ca8a04" stroke-width="1.4"/>
    <text x="709" y="34" text-anchor="middle" font-size="9.2" font-weight="bold" fill="#854d0e">Optional ACI (Exp 11 App.)</text>
    <text x="709" y="50" text-anchor="middle" font-size="8.0" fill="#334155">α_{t+1} = α_t + γ(0.20 − err_t)</text>
    <text x="709" y="65" text-anchor="middle" font-size="8.0" fill="#334155">If err_t=1 (miss): α drops →</text>
    <text x="709" y="79" text-anchor="middle" font-size="8.0" fill="#854d0e">1−α tightens (80%→83.6%)</text>
    <text x="709" y="95" text-anchor="middle" font-size="7.8" fill="#475569">HP Apple CVaR -27.6% tighter</text>
  </svg>
</div>

<h2>3.7 Putting It All Together — End-to-End 5-Candidate Master Trace (Morning Dispatch Simulation)</h2>
<div class="box box-numerical">
  <div class="box-title">Walk-Through of One Real Morning Decision (<code>P<sup>local</sup> = ₹1,400/qtl</code>, MP Tomato, May 40°C Heat)</div>
  <p style="margin-bottom:4px;">Step 0 screens 14 yards in MP within 15–500 km and keeps the Top-5 candidates with screen spread &gt; ₹100/qtl. Watch how sequential cheap-first pruning saves API calls compared to upfront <code>B4</code> (which blindly spends 5 × 4 = 20 calls):</p>
  <table style="margin-bottom:4px;">
    <tr><th>Cand</th><th>Screen Price</th><th>Step 1 (T1 Vitality)</th><th>Step 2 (T2 Road+Fee)</th><th>Step 3 (T3 Weather)</th><th>Step 4 (T4 Conformal LCB)</th><th>Calls Used</th></tr>
    <tr><td><strong>#1 Yard A</strong></td><td>₹2,200</td><td style="color:#dc2626;"><strong>PRUNE (age=6d &gt; 3d)</strong></td><td><em>Skipped</em></td><td><em>Skipped</em></td><td><em>Skipped</em></td><td class="num-col"><strong>1</strong> (vs 4)</td></tr>
    <tr><td><strong>#2 Yard B</strong></td><td>₹2,050</td><td style="color:#dc2626;"><strong>PRUNE (DOW=0.20 &lt; 0.35)</strong></td><td><em>Skipped</em></td><td><em>Skipped</em></td><td><em>Skipped</em></td><td class="num-col"><strong>1</strong> (vs 4)</td></tr>
    <tr><td><strong>#3 Yard C</strong></td><td>₹1,540</td><td>PASS (P<sup>ref</sup>=₹1,540)</td><td style="color:#dc2626;"><strong>PRUNE (F=₹180 &gt; ₹140)</strong></td><td><em>Skipped</em></td><td><em>Skipped</em></td><td class="num-col"><strong>2</strong> (vs 4)</td></tr>
    <tr><td><strong>#4 Yard D</strong></td><td>₹1,880</td><td>PASS (P<sup>ref</sup>=₹1,880)</td><td>PASS (F=₹150, +₹330)</td><td style="color:#dc2626;"><strong>PRUNE (10h + 45mm storm)</strong></td><td><em>Skipped</em></td><td class="num-col"><strong>3</strong> (vs 4)</td></tr>
    <tr class="highlight"><td><strong>#5 Yard E</strong></td><td>₹2,000</td><td>PASS (age=1d, P<sup>ref</sup>=₹2,000)</td><td>PASS (200km/6h, F=₹146)</td><td>PASS (-3.25% rot = -₹65)</td><td>ŷ=0%, q<sub>0.80</sub>=8% → <strong>LCB Net = +₹234.20/qtl</strong></td><td class="num-col"><strong>4</strong> (vs 4)</td></tr>
  </table>
  <p style="margin-bottom:0;"><strong>Final Verdict:</strong> <code>Best LCB (+₹234.20) &gt; ₹50/qtl</code> → <strong><code>DISPATCH Yard E</code></strong> (+₹7,026 expected safe profit on 30 qtl), using only <strong>1 + 1 + 2 + 3 + 4 = 11 calls</strong> instead of 20 (<code>-45%</code> calls vs <code>B4</code>)! Notice the exact 5-line arithmetic: <code>₹2,000 × (1 − 0.08) × (1 − 0.0325) − ₹146 − ₹1,400 = <strong>+₹234.20/qtl</strong></code> (equivalently as a sequential haircut: <code>₹2,000 − ₹65.00 − ₹146.00 − ₹154.80 − ₹1,400 = <strong>+₹234.20/qtl</strong></code>).</p>
</div>

<h2>3.8 Under the Hood of Stage-II <code>MandiGuard-CRC</code> (<code>uncensored_crc_forecaster.py</code>)</h2>
<div class="box box-math">
  <div class="box-title">Why Switch From Stage-I Censored Return LCB to Stage-II Dual-Head Uncensored Scoring?</div>
  <p style="margin-bottom:5px;">Stage-I dropped missing arrival rows (<code>dropna(target_ret)</code>, losing 55.83% of raw 2024 routes) and subtracted one crop-pooled residual buffer (causing 90.46% calm vs 67.80% volatile coverage). Stage-II fixes both with <strong>two frozen 2024 <code>HistGradientBoosting</code> heads</strong> trained on every settled corridor (<code>arrival_date + 2d ≤ 2024-12-31</code>) using <strong>full uncensored payoff <code>Y_full = real_delta_net_inr</code></strong> (so closed-yard crashes are directly visible during training):</p>
  <div class="math-formula">
    Score<sub>CRC</sub>(m) &nbsp;=&nbsp; μ̂(m) &nbsp;−&nbsp; λ* &middot; P<sub>loc</sub> &middot; p̂<sub>loss</sub>(m) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; [Dispatch iff Score<sub>CRC</sub>(m*) &gt; ₹50/qtl &amp; μ̂(m*) &gt; ₹50/qtl]
  </div>
  <p style="margin-bottom:4px;"><strong>Validation Calibration (<code>Val_2025H1</code>, N = 42,794, Zero Holdout Tuning):</strong> Fitting regression <code>μ̂</code> + raw <code>HistGradientBoostingClassifier.predict_proba</code> loss-risk estimator <code>p̂<sub>loss</sub></code> on <code>274,296</code> settled 2024 routes (<code>t1_ok &amp; static_net &gt; 0</code>) with <code>1.20×</code> Euclidean Step-0 sorting, we sweep <code>λ ∈ &#123;0.00, 0.05, ..., 1.20&#125;</code> on clean <code>Val_2025H1</code> (<code>arr_dt ≤ 2025-05-31</code>) and stop at the first feasible grid point (<code>break</code>) satisfying <code>(n<sub>loss</sub>(λ) + 1) / (n<sub>disp</sub>(λ) + 1) ≤ β<sub>target</sub> = 0.095</code> → freezing <strong><code>λ* = 0.15</code></strong> for <code>MandiGuard-CRC</code> (Val mean ₹365.46/qtl, 9.15% LTR; <code>Rung 2</code> strict <code>T1</code> freezes at <code>λ* = 0.10</code>, ₹358.52/qtl, 9.34% LTR). <em>Statistical Boundary:</em> Adapts Angelopoulos et al. (2024) as an empirical validation heuristic without claiming exchangeability Theorem 1 guarantees.</p>
  <p style="margin-bottom:0;"><strong>Worked Numerics (Calm vs Volatile Comparison, <code>P<sub>loc</sub> = ₹1,400/qtl</code>):</strong>
    (a) <em>Safe Calm Corridor:</em> <code>μ̂ = +₹220/qtl</code>, <code>p̂<sub>loss</sub> = 0.04</code> → Penalty = <code>0.15 × 1,400 × 0.04 = -₹8.40</code> → <code>Score = <strong>+₹211.60/qtl</strong> &gt; ₹50</code> (Stage I over-buffered calm routes, while CRC unlocks them!).<br/>
    (b) <em>Volatile 3-Day Stale Corridor:</em> <code>μ̂ = +₹140/qtl</code>, <code>p̂<sub>loss</sub> = 0.55</code> → Penalty = <code>0.15 × 1,400 × 0.55 = -₹115.50</code> → <code>Score = <strong>+₹24.50/qtl</strong> &lt; ₹50</code> → <strong>PRUNE cleanly</strong> even if point prediction looks profitable! Additionally, <strong>Grade-Aware <code>T1</code> (<code>fresh0 | strict</code>)</strong> admits fresh same-day quotes (<code>age = 0</code> with <code>open_prob_14d ≥ 0.20</code> and <code>dow_open_rate ≥ 0.25</code>) alongside persistent routes so sub-grade Apple tags aren't falsely blocked.</p>
</div>
"""


def sec_ch4_payoff_metrics_stats() -> str:
    return r"""
<div class="page-break"></div>
<h1 class="chapter-title">Chapter 4: Realized Payoff Mechanics, Metrics &amp; Statistical Inference Under the Hood</h1>

<h2>4.1 The 4 Realized Ground-Truth Auction Cases (<code>payoff_model.py:115-214</code>)</h2>
<p>When any policy sends a truck on morning <code>t</code> over route <code>(i → j)</code> with transit lag <code>τ</code>, realized cash depends on observed destination prices across arrival window <code>[t+τ, t+τ+1, t+τ+2]</code> and realized ERA5/NASA transit weather:</p>

<table>
  <tr><th>Realized Case</th><th>Auction Condition at Destination</th><th>Exact Mathematical Realized Payoff (<code>ΔNet<sub>i→j,t</sub></code>)</th><th>Numeric Sample (<code>P<sup>loc</sup>=1,400, F=146</code>)</th></tr>
  <tr>
    <td><strong>1. <code>exact_open_d0</code></strong></td><td>Exact variety traded on arrival day <code>d0 = t+τ</code> (<code>w = 0</code> wait).</td><td><code>P<sub>sale</sub>·(1 − s(0)) − F<sub>ij</sub> − P<sup>loc</sup></code><br/><em>(If realized Rain ≥ 35mm: <code>P<sub>sale</sub> = 0.5·P<sup>modal</sup> + 0.5·P<sup>min</sup></code>)</em></td><td>d0 Modal ₹1,950, 3.25% rot → <code>1,950×0.9675 − 146 − 1,400 = <strong>+₹340.63/qtl</strong></code>.</td>
  </tr>
  <tr>
    <td><strong>2. <code>exact_wait_d1/d2</code></strong></td><td>Closed on <code>d0</code>; truck waits <code>w ∈ {1,2}</code> mornings until exact variety trades (trapped!).</td><td><code>P<sub>sale</sub>·(1 − s(w)) − F<sub>ij</sub> − 25·w − P<sup>loc</sup></code><br/><em>(<code>₹25/day</code> parking + <code>24w</code> extra rot hrs)</em></td><td>Waits 1 day (30h rot=16.25%), d1=1,950 → <code>1,950×0.8375 − 146 − 25 − 1,400 = <strong>+₹62.13/qtl</strong></code>.</td>
  </tr>
  <tr>
    <td><strong>3. <code>other_variety_distress</code></strong></td><td>Exact variety never trades in 3d, but other varieties trade on <code>d0</code>.</td><td>Sells at <code>P<sub>sale</sub> = OtherVar_Min<sub>d0</sub> × (1 − 0.10)</code>:<br/><code>P<sub>sale</sub>·(1 − s(0)) − F<sub>ij</sub> − P<sup>loc</sup></code></td><td>Other var Min ₹1,200 → <code>1,080×0.9675 − 146 − 1,400 = <strong>-₹501.10/qtl</strong></code>!</td>
  </tr>
  <tr>
    <td><strong>4. <code>closed_yard_divert</code></strong></td><td>Closed / zero trades for this commodity across all 3 arrival days (<code>w = 3</code>).</td><td>Diverts back / distress loss:<br/><code>− 1.50 · F<sub>ij</sub> − P<sup>loc</sup> · s(0)</code></td><td><code>−1.5×146 − 1,400×0.0325 = <strong>-₹264.50/qtl</strong></code> (on costly routes up to -₹1,200+).</td>
  </tr>
</table>

<h2>4.2 Four Core Evaluation Metrics (Plus Conditional vs. Unconditional Clarity)</h2>
<p>Suppose over 10 episodes, a policy <strong>stays home (₹0)</strong> twice and <strong>dispatches 8 times</strong> with outcomes <code>[-300, -100, +50, +100, +200, +300, +400, +550]</code>:</p>
<ol>
  <li><strong>Mean Net Gain (Unconditional):</strong> Sum across ALL 10 episodes / 10 = <code>₹1,200 / 10 = <strong>+₹120/qtl</strong></code> (+₹3,600/truck). Note: Conditional gain on dispatched trips is <code>₹1,200 / 8 = +₹150/qtl</code>, and <code>Mean = Cond_Gain × Dispatch_Rate</code>.</li>
  <li><strong>Loss-Trip Rate (LTR — Conditional Dispatched Loss Rate):</strong> Fraction of dispatched trucks losing money = <code>2 / 8 = <strong>25.0%</strong></code>. (Unconditional episode loss probability across all 10 episodes is <code>2 / 10 = 20.0%</code> — the exact target used in confirmatory Hypothesis <code>H3</code>!).</li>
  <li><strong>Worst-10% Loss (<code>CVaR_10%</code>):</strong> Sort all 10 episodes worst-to-best: <code>[-300, -100, 0, 0, +50, ...]</code>; average the bottom 10% (worst 1 entry) = <strong>-₹300/qtl</strong>. On holdout (<code>N = 69,526</code>), <code>CVaR_10%</code> averages the worst 6,952 episodes.</li>
  <li><strong>Live API Calls / Query:</strong> Mean online requests executed per episode before issuing <code>DISPATCH</code> or <code>REFUSE_PHANTOM_SPREAD</code>.</li>
</ol>

<h2>4.3 Under the Hood: Two-Way Cluster Bootstrap (<code>R = 5,000</code>) &amp; Holm–Bonferroni</h2>
<p>Why would a textbook paired <em>t</em>-test produce fake significance? Because mandi trips cluster two ways simultaneously: (a) <strong>Serial Correlation</strong> within the same origin market over consecutive days, and (b) <strong>Spatial Correlation</strong> across markets sharing state monsoon/export shocks in the same week.</p>

<div class="svg-box">
  <div class="box-title" style="text-align:left;">Two-Way Cluster Bootstrap Matrix Algebra (<code>bootstrap.py</code>, <code>174 Origin Mandis × 23 Two-Week Blocks</code>)</div>
  <svg width="100%" viewBox="0 0 800 120" xmlns="http://www.w3.org/2000/svg" style="font-family: sans-serif;">
    <rect x="10" y="14" width="215" height="92" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="1.4"/>
    <text x="117" y="32" text-anchor="middle" font-size="9.5" font-weight="bold" fill="#1e3a8a">Step 1: Pre-Aggregate Grid</text>
    <text x="117" y="48" text-anchor="middle" font-size="8.0" fill="#334155">Fold 69,526 paired diffs d_{i,t}</text>
    <text x="117" y="62" text-anchor="middle" font-size="8.0" fill="#334155">into compact (174 × 23) matrices:</text>
    <text x="117" y="77" text-anchor="middle" font-size="8.4" font-weight="bold" fill="#0f3d5e">SUM[m, b] &amp; CNT[m, b]</text>
    <text x="117" y="93" text-anchor="middle" font-size="7.8" fill="#475569">(Turns 5,000 draws into &lt;0.1s!)</text>

    <line x1="225" y1="60" x2="248" y2="60" stroke="#0f3d5e" stroke-width="1.5" marker-end="url(#arrow)"/>

    <rect x="250" y="14" width="255" height="92" rx="6" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.4"/>
    <text x="377" y="32" text-anchor="middle" font-size="9.5" font-weight="bold" fill="#14532d">Step 2: Resample Rows &amp; Cols Together</text>
    <text x="377" y="48" text-anchor="middle" font-size="8.0" fill="#1e293b">Sample 174 mandis w/ repl → weights m_w</text>
    <text x="377" y="62" text-anchor="middle" font-size="8.0" fill="#1e293b">Sample 23 2-wk blocks w/ repl → weights b_w</text>
    <text x="377" y="78" text-anchor="middle" font-size="8.3" font-weight="bold" fill="#14532d">θ*_r = (m_wᵀ · SUM · b_w) / (m_wᵀ · CNT · b_w)</text>
    <text x="377" y="94" text-anchor="middle" font-size="7.8" fill="#334155">3×3 Example: SUM·CNT = 1,300 / 90 = +₹14.44</text>

    <line x1="505" y1="60" x2="528" y2="60" stroke="#0f3d5e" stroke-width="1.5" marker-end="url(#arrow)"/>

    <rect x="530" y="14" width="260" height="92" rx="6" fill="#fefce8" stroke="#ca8a04" stroke-width="1.4"/>
    <text x="660" y="32" text-anchor="middle" font-size="9.5" font-weight="bold" fill="#854d0e">Step 3: Phipson–Smyth + Holm</text>
    <text x="660" y="48" text-anchor="middle" font-size="8.0" fill="#334155">p_raw = (1 + count(θ*_r ≤ 0)) / (5000 + 1)</text>
    <text x="660" y="63" text-anchor="middle" font-size="8.0" fill="#334155">Sort m=4 hypotheses; multiply by (4,3,2,1):</text>
    <text x="660" y="78" text-anchor="middle" font-size="8.2" font-weight="bold" fill="#14532d">H3: 0.0008 | H4: 0.0008 | H1: 0.0012</text>
    <text x="660" y="93" text-anchor="middle" font-size="8.2" font-weight="bold" fill="#991b1b">H2: 0.2699 × 1 = 0.2699 (NOT SUPPORTED)</text>
  </svg>
</div>

<div class="box box-numerical">
  <div class="box-title">Concrete 3×3 Bootstrap Matrix Calculation (Verify on Whiteboard!)</div>
  <p style="margin-bottom:0;">Suppose 3 mandis × 3 two-week blocks have <code>SUM = [[300,-100,200], [100,400,0], [500,100,300]]</code> and uniform <code>CNT = 10</code> per cell. If draw <em>r</em> samples mandis <code>[M1, M1, M3]</code> (<code>m<sub>w</sub> = [2, 0, 1]</code>) and blocks <code>[B2, B3, B3]</code> (<code>b<sub>w</sub> = [0, 1, 2]</code>), each cell <code>(m,b)</code> gets weight <code>m<sub>w</sub>[m] × b<sub>w</sub>[b]</code>: <code>SUM·b<sub>w</sub> = [0(300)+1(-100)+2(200)=300, ..., 0(500)+1(100)+2(300)=700]</code>. Multiplying by <code>m<sub>w</sub></code> gives <code>num = 2×300 + 0 + 1×700 = 1,300</code>; denominator <code>den = 2×(30) + 1×(30) = 90</code>; thus replicate mean is <code>1,300 / 90 = <strong>+₹14.44</strong></code>. Across 5,000 draws, the 2.5% and 97.5% quantiles form the exact Two-Way CI!</p>
</div>
"""


def sec_ch5_experiments_and_figures() -> str:
    fig2 = b64_img("fig2_main_policy_comparison.png")
    fig3 = b64_img("fig3_tool_ablation_and_monsoon_heat.png")
    fig4 = b64_img("fig4_tool_budget_pareto.png")
    fig5 = b64_img("fig5_hp_apple_grade_traps.png")
    fig6 = b64_img("fig6_sensitivity_and_govt_fees.png")
    fig7 = b64_img("fig7_decade_2017_2026_evolution.png")
    fig8 = b64_img("fig8_zerocloud_fpo_and_modern_ai.png")
    fig9 = b64_img("fig9_mechanistic_autopsy_and_uncensored_crc.png")

    return f"""
<div class="page-break"></div>
<h1 class="chapter-title">Chapter 5: Complete Experimental Verification &amp; Visual Guide (<code>Exp 1</code>–<code>Exp 17</code>, All 9 Figures)</h1>

<h2>5.1 Confirmatory View 1 Benchmark &amp; Holm Summary (<code>Exp 2</code>, <code>N = 69,526</code>)</h2>
<table>
  <tr><th>Policy Comparator</th><th class="num-col">Disp %</th><th class="num-col">Mean (₹/qtl)</th><th class="num-col">30-qtl Load</th><th class="num-col">Loss Rate</th><th class="num-col">Trap Rate</th><th class="num-col">CVaR<sub>10%</sub></th><th class="num-col">Calls</th></tr>
  <tr><td><code>B0_SellLocal</code></td><td class="num-col">0.00%</td><td class="num-col">₹0.00</td><td class="num-col">₹0</td><td class="num-col">0.00%</td><td class="num-col">0.00%</td><td class="num-col">₹0.00</td><td class="num-col">0.00</td></tr>
  <tr><td><code>B1_NaiveScreenGreedy</code></td><td class="num-col">90.67%</td><td class="num-col">₹350.01</td><td class="num-col">₹10,500.2</td><td class="num-col">40.46%</td><td class="num-col">58.94%</td><td class="num-col">-₹1,062.66</td><td class="num-col">0.00</td></tr>
  <tr><td><code>B2_FreshRoadGreedy</code></td><td class="num-col">62.11%</td><td class="num-col">₹446.66</td><td class="num-col">₹13,399.7</td><td class="num-col">18.11%</td><td class="num-col">24.32%</td><td class="num-col">-₹436.67</td><td class="num-col">7.87</td></tr>
  <tr class="warn-row"><td><code>B3_MLPointDispatch</code></td><td class="num-col">93.05%</td><td class="num-col">₹330.85</td><td class="num-col">₹9,925.6</td><td class="num-col"><strong>45.28%</strong></td><td class="num-col"><strong>65.65%</strong></td><td class="num-col">-₹1,097.80</td><td class="num-col">7.87</td></tr>
  <tr><td><code>B6_HeuristicBucketRouter</code></td><td class="num-col">43.36%</td><td class="num-col">₹431.94</td><td class="num-col">₹12,958.3</td><td class="num-col">11.88%</td><td class="num-col">21.59%</td><td class="num-col">-₹42.42</td><td class="num-col">11.80</td></tr>
  <tr><td><code>B5_MultiAgentCoordinator</code></td><td class="num-col">41.59%</td><td class="num-col">₹437.39</td><td class="num-col">₹13,121.7</td><td class="num-col">9.38%</td><td class="num-col">16.57%</td><td class="num-col">-₹31.77</td><td class="num-col">8.76</td></tr>
  <tr><td><code>B4_UpfrontAllTools</code></td><td class="num-col">48.66%</td><td class="num-col">₹452.79</td><td class="num-col">₹13,583.6</td><td class="num-col">9.97%</td><td class="num-col">16.17%</td><td class="num-col">-₹37.89</td><td class="num-col">15.74</td></tr>
  <tr class="highlight"><td><code>MandiGuard</code> (Ours)</td><td class="num-col">48.66%</td><td class="num-col">₹452.79</td><td class="num-col">₹13,583.6</td><td class="num-col"><strong>9.97%</strong></td><td class="num-col"><strong>16.17%</strong></td><td class="num-col"><strong>-₹37.89</strong></td><td class="num-col"><strong>8.75</strong></td></tr>
</table>

<p style="font-size:8.5pt;"><strong>State/Commodity Highlights (<code>Exp 2b</code>):</strong> <code>MandiGuard</code> vs <code>B1</code> gains: Apple +₹504.05, HP +₹416.10, MP +₹156.29, Onion +₹116.91, KA +₹71.32, MH +₹60.39, Potato +₹54.63, UP +₹49.15, GJ +₹11.88; Tomato trades -₹25.16 lottery upside vs <code>B1</code> while cutting loss incidence 32.38%→5.09% and beating <code>B2</code> by +₹37.84. Across the 4 states with 100% archived Open-Meteo NWP forecasts (GJ, KA, MP, MH; <code>N = 42,766</code>), <code>MandiGuard</code> earns ₹485.18/qtl vs <code>B2</code> ₹453.37 (+₹31.82/qtl) and <code>B1</code> ₹425.65 (+₹59.53/qtl)—treated strictly as an exploratory robustness check on the causal northern weather Ridge nowcaster, not a rescue of <code>H2</code>.</p>

<div class="figure-box">
  <img src="{fig2}" alt="Figure 2: Main Policy Comparison"/>
  <div class="figure-caption"><strong>Figure 2 (Exp 2):</strong> Multi-policy holdout performance showing <code>MandiGuard</code> achieving +₹102.78/qtl over <code>B1</code>, cutting episode losses by 37.29 pp over <code>B3</code>, tying <code>B2</code> on mean while halving loss trips and reducing CVaR<sub>10%</sub> 11.5×, and matching <code>B4</code> utility in 44.4% fewer calls.</div>
</div>

<h2>5.2 View 2 Dual-View Open-Yard Defense &amp; Crossover Curve (<code>Exp 15</code>)</h2>
<table>
  <tr><th><code>Exp 15</code> Counterfactual Regime (<code>Holdout_2025_2026</code>)</th><th class="num-col"><code>B1</code> (LTR)</th><th class="num-col"><code>B2</code> (LTR)</th><th class="num-col"><code>B3</code> (LTR)</th><th class="num-col"><code>MandiGuard</code> (LTR / CVaR)</th><th class="num-col"><code>MG−B1</code></th><th class="num-col"><code>MG−B3</code></th></tr>
  <tr><td><code>1_Baseline_Div1.5x_Disc10pct</code> (69,526)</td><td class="num-col">₹350.01 (40.5%)</td><td class="num-col">₹446.66 (18.1%)</td><td class="num-col">₹330.85 (45.3%)</td><td class="num-col">₹452.79 (9.97% / -₹37.9)</td><td class="num-col">+₹102.78</td><td class="num-col">+₹121.94</td></tr>
  <tr><td><code>2_OneWayDiv_Div1.0x_Disc10pct</code> (69,526)</td><td class="num-col">₹362.61 (40.5%)</td><td class="num-col">₹449.33 (18.1%)</td><td class="num-col">₹344.88 (45.3%)</td><td class="num-col">₹454.27 (9.97% / -₹35.3)</td><td class="num-col">+₹91.66</td><td class="num-col">+₹109.39</td></tr>
  <tr><td><code>3_HalfDiv_Div0.5x_Disc5pct</code> (69,526)</td><td class="num-col">₹413.57 (38.0%)</td><td class="num-col">₹452.32 (18.1%)</td><td class="num-col">₹409.88 (42.1%)</td><td class="num-col">₹456.00 (9.97% / -₹32.4)</td><td class="num-col">+₹42.43</td><td class="num-col">+₹46.12</td></tr>
  <tr><td><code>4_ZeroDiv_Div0.0x_Disc0pct</code> <em>(crossover)</em></td><td class="num-col">₹468.17 (18.5%)</td><td class="num-col">₹456.09 (12.5%)</td><td class="num-col">₹479.09 (20.4%)</td><td class="num-col">₹458.17 (6.09% / -₹28.7)</td><td class="num-col"><strong>-₹10.00</strong></td><td class="num-col"><strong>-₹20.93</strong></td></tr>
  <tr><td><code>5_ZeroTrap_BreakEven0_Missing3d</code> (69,526)</td><td class="num-col">₹376.77 (8.3%)</td><td class="num-col">₹457.24 (12.3%)</td><td class="num-col">₹385.42 (4.9%)</td><td class="num-col">₹459.03 (5.96% / -₹26.2)</td><td class="num-col">+₹82.26</td><td class="num-col">+₹73.61</td></tr>
  <tr class="highlight"><td><code>6_Fair_Matched_Observed_d0</code> (<strong>N=10,162</strong>)</td><td class="num-col">₹472.51 (19.8%)</td><td class="num-col">₹469.99 (15.1%)</td><td class="num-col">₹553.22 (14.8%)</td><td class="num-col">₹510.89 (<strong>6.82%</strong> / <strong>-₹36.1</strong>)</td><td class="num-col"><strong>+₹38.38</strong></td><td class="num-col">-₹42.33</td></tr>
  <tr class="highlight"><td><code>7_Fair_Matched_Observed_3d</code> (<strong>N=16,849</strong>)</td><td class="num-col">₹581.06 (20.6%)</td><td class="num-col">₹572.09 (15.8%)</td><td class="num-col">₹670.38 (15.0%)</td><td class="num-col">₹592.53 (<strong>7.74%</strong> / <strong>-₹48.3</strong>)</td><td class="num-col"><strong>+₹11.47</strong></td><td class="num-col">-₹77.85</td></tr>
</table>

<h2>5.3 Complete Tool Ablation (<code>Exp 4</code>), Rejection Reasons (<code>Exp 7</code>) &amp; Query Budgets (<code>Exp 5</code>)</h2>
<table>
  <tr><th>Tool Ablation Variant (<code>Exp 4</code>, <code>N = 69,526</code> / Extreme Weather <code>21,656</code>)</th><th class="num-col">Overall Mean</th><th class="num-col">Overall LTR</th><th class="num-col">Overall Trap</th><th class="num-col">Overall CVaR</th><th class="num-col">Wx Mean</th><th class="num-col">Wx LTR</th><th class="num-col">Wx CVaR</th><th class="num-col">Calls</th></tr>
  <tr class="highlight"><td><code>Full_MandiGuard</code> (All 4 Gates)</td><td class="num-col">₹452.79</td><td class="num-col"><strong>9.97%</strong></td><td class="num-col"><strong>16.17%</strong></td><td class="num-col"><strong>-₹37.89</strong></td><td class="num-col">₹470.07</td><td class="num-col"><strong>10.10%</strong></td><td class="num-col"><strong>-₹57.11</strong></td><td class="num-col">8.75</td></tr>
  <tr class="warn-row"><td><code>No_T1_Vitality</code> (Drops Market Check)</td><td class="num-col">₹318.74 (-₹134)</td><td class="num-col">42.80%</td><td class="num-col">67.16%</td><td class="num-col">-₹987.10</td><td class="num-col">₹367.77</td><td class="num-col">38.74%</td><td class="num-col">-₹1,003.01</td><td class="num-col">11.03</td></tr>
  <tr><td><code>No_T2_OSRM_to_Euclid</code> (1.15× Euclid)</td><td class="num-col">₹452.35</td><td class="num-col">10.25%</td><td class="num-col">16.22%</td><td class="num-col">-₹38.57</td><td class="num-col">₹468.22</td><td class="num-col">10.59%</td><td class="num-col">-₹58.54</td><td class="num-col">7.05</td></tr>
  <tr><td><code>No_T3_Weather</code> (Drops Heat/Rain)</td><td class="num-col">₹455.25 (+₹2.46)</td><td class="num-col">10.61%</td><td class="num-col">16.18%</td><td class="num-col">-₹41.59</td><td class="num-col">₹474.31</td><td class="num-col">11.39%</td><td class="num-col">-₹67.49</td><td class="num-col">7.23</td></tr>
  <tr class="warn-row"><td><code>No_T4_ConformalLCB</code> (Drops 80% Cushion)</td><td class="num-col">₹448.74</td><td class="num-col">16.89%</td><td class="num-col">16.13%</td><td class="num-col">-₹397.19</td><td class="num-col">₹465.50</td><td class="num-col">15.73%</td><td class="num-col">-₹458.74</td><td class="num-col">7.23</td></tr>
</table>

<div class="figure-box">
  <img src="{fig3}" alt="Figure 3: Tool Ablation and Monsoon Heat"/>
  <div class="figure-caption"><strong>Figure 3 (Exp 4):</strong> Removing <code>T1</code> loses -₹134.05/qtl and quadruples traps; removing <code>T4</code> causes CVaR<sub>10%</sub> to crash 10× deeper (-₹397.19/qtl). Removing <code>T3</code> nudges overall mean +₹2.46/qtl while increasing extreme-weather risk (LTR 10.10%→11.39%, CVaR -₹57.11→-₹67.49). Rejection distribution (<code>Exp 7</code>): Dispatch 48.66% (33,828 eps, 12.30 calls); T1 Stale/Variety 25.48% (17,713, 3.64 calls); T4 Reversion 17.58% (12,222, 8.86 calls); T1 Closed 5.34% (3,714, 3.04 calls); T2 Freight 2.24% (1,555); T3 Weather 0.71% (494).</div>
</div>

<div class="figure-box">
  <img src="{fig4}" alt="Figure 4: Tool Budget Pareto"/>
  <div class="figure-caption"><strong>Figure 4 (Exp 5):</strong> Budget-constrained Pareto frontier. At tight cap <code>B = 4</code> calls, both hit ₹299.31/qtl. At <code>B = 6</code> calls, upfront <code>B4</code> completes only <code>⌊6/4⌋ = 1</code> candidate (₹299.31 in 5.75 calls), whereas <code>MandiGuard</code> reaches <strong>₹403.85/qtl</strong> in 5.05 calls (<strong>+₹104.54/qtl</strong> advantage). At <code>B = 8</code>: ₹435.70 vs ₹389.17; at <code>B = 20</code>: both tie at ₹452.79 (8.75 vs 15.74 calls).</div>
</div>

<h2>5.4 HP Graded Apples (<code>Exp 3</code>), Sensitivity Grid (<code>Exp 6</code>), LOSO (<code>Exp 9</code>) &amp; 10-Year Regimes (<code>Exp 10/10b</code>)</h2>
<div class="figure-box">
  <img src="{fig5}" alt="Figure 5: HP Apple Grade Traps"/>
  <div class="figure-caption"><strong>Figure 5 (Exp 3, N = 1,537 grade-explicit HP Apple lots):</strong> Naive <code>B1</code> runs into 94.14% traps (Grade B loses -₹427.54/qtl; CVaR<sub>10%</sub> = -₹8,487.24). Stage-I <code>MandiGuard</code> reduces traps 7× (13.24%), flips Grade B to +₹833.70/qtl, and limits CVaR to -₹102.76/qtl. <em>Autopsy (Exp 16):</em> Stage-I trailed <code>B2</code> (₹605.06 vs ₹1,150.83) mainly because sparse <code>Grade A</code> tags triggered <code>T1</code> blocks on <strong>77.82%</strong> of <code>B2</code>-dispatched holdout refusals (fixed by Stage-II <code>MandiGuard-CRC</code> → <strong>₹812.08/qtl</strong>).</div>
</div>

<div class="figure-box">
  <img src="{fig6}" alt="Figure 6: Sensitivity Grid and Govt Fees"/>
  <div class="figure-caption"><strong>Figure 6 (Exp 6):</strong> 3×3 freight (0.75–1.25×) × spoilage (0.5–1.5×) sensitivity stress test plus statutory GoI APMC fee verification. <code>MandiGuard</code> leads <code>B1</code> across <strong>9/9 cells (+₹82.62 to +₹121.42/qtl)</strong>, leads <code>B2</code> across normal/severe decay (+₹5.27 to +₹14.50), and matches <code>B2</code> within -₹1.52/qtl if decay halves to 0.5×. Real GoI state fees lift net gain +₹7.12/qtl over uniform 1.5% charges (₹452.79 vs ₹445.67).</div>
</div>

<div class="two-col">
  <div class="box box-math" style="margin-top:0;">
    <div class="box-title">Zero-Shot State Transfer (<code>Exp 9</code> LOSO)</div>
    <table>
      <tr><th>Held-Out State</th><th class="num-col"><code>B1</code> Mean</th><th class="num-col"><code>MG_LOSO</code></th><th class="num-col"><code>MG</code> Arr Drop</th></tr>
      <tr><td>Maharashtra</td><td class="num-col">₹595.69</td><td class="num-col"><strong>₹651.08</strong></td><td class="num-col">3.91% (vs 52.3%)</td></tr>
      <tr><td>Uttar Pradesh</td><td class="num-col">₹154.68</td><td class="num-col"><strong>₹216.22</strong></td><td class="num-col">3.34% (vs 53.1%)</td></tr>
      <tr><td>Karnataka</td><td class="num-col">₹330.55</td><td class="num-col"><strong>₹400.06</strong></td><td class="num-col">8.08% (vs 46.7%)</td></tr>
      <tr><td>Madhya Pradesh</td><td class="num-col">₹88.73</td><td class="num-col"><strong>₹211.52</strong></td><td class="num-col">8.04% (vs 55.7%)</td></tr>
      <tr><td>Gujarat</td><td class="num-col">₹439.26</td><td class="num-col"><strong>₹450.76</strong></td><td class="num-col">6.78% (vs 47.6%)</td></tr>
      <tr><td>Himachal Pradesh</td><td class="num-col">₹377.18</td><td class="num-col"><strong>₹801.37</strong></td><td class="num-col">9.72% (vs 45.3%)</td></tr>
    </table>
    <p style="font-size:7.9pt;margin:0;">Also validated: <strong>Dual-Tier Official Audit (Exp 14):</strong> Tier 1 XML (<code>2023-10-18</code>, <code>172</code> keys: 100% Min/Max, 99.42% Modal); Tier 2 <strong>149-day AGMARKNET 2.0</strong> (<code>2,042</code> keys: <strong>100.00% Min/Max/Modal</strong>) + 22 live queries.</p>
  </div>
  <div class="box box-math" style="margin-top:0;">
    <div class="box-title">10-Year Macro Regimes (<code>Exp 10</code>, <code>N = 661,192</code>) &amp; <code>Exp 10b</code></div>
    <table>
      <tr><th>Era (Matched Trips)</th><th class="num-col"><code>B1</code> Mean (LTR)</th><th class="num-col"><code>MG</code> Mean (LTR)</th><th class="num-col"><code>MG</code> CVaR</th></tr>
      <tr><td>2017H2 GST (32k)</td><td class="num-col">₹393.39 (39.2%)</td><td class="num-col">₹425.04 (11.7%)</td><td class="num-col">-₹31.62</td></tr>
      <tr><td>2018–19 Pre-COV (146k)</td><td class="num-col">₹254.77 (42.4%)</td><td class="num-col">₹345.17 (8.8%)</td><td class="num-col">-₹20.93</td></tr>
      <tr><td>2020–21 COVID (139k)</td><td class="num-col">₹279.96 (42.2%)</td><td class="num-col">₹340.83 (10.6%)</td><td class="num-col">-₹23.42</td></tr>
      <tr><td>2022–23 Curbs (178k)</td><td class="num-col">₹278.41 (42.2%)</td><td class="num-col">₹394.37 (10.5%)</td><td class="num-col">-₹33.29</td></tr>
      <tr class="highlight"><td>2024 El-Niño (96k)</td><td class="num-col">₹222.77 (44.3%)</td><td class="num-col"><strong>₹387.91 (12.0%)</strong></td><td class="num-col">-₹36.82</td></tr>
      <tr><td>2025–26 Holdout (70k)</td><td class="num-col">₹350.01 (40.5%)</td><td class="num-col">₹452.79 (10.0%)</td><td class="num-col">-₹37.89</td></tr>
    </table>
    <p style="font-size:7.9pt;margin:0;"><strong>Exp 10b Training Scaling:</strong> 1-Yr (702k rows): ₹452.79; 3-Yr (1.67M): ₹454.74; 8-Yr (3.44M): ₹454.94 (<strong>only +₹2.15/qtl gain</strong> — recency beats volume).</p>
  </div>
</div>

<h2>5.4b Stage-II <code>[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]</code> Autopsy &amp; <code>MandiGuard-CRC</code> (<code>Exp 16</code>–<code>17</code>, Figure 8)</h2>
<div class="box box-warning" style="padding:6px 10px;margin-bottom:6px;">
  <strong>Anti-HARKing Quarantine:</strong> Pre-registered Stage I (<code>MG_v1</code>, commit <code>e421d15</code>) stays frozen. Stage II fits strictly on settled 2024 data and freezes scalar <code>λ* = 0.15</code> strictly on <code>Val_2025H1</code> (zero holdout tuning).
</div>

<table>
  <tr><th>Stage-II Evidence (<code>Exp 16</code> Autopsy &amp; <code>Exp 17</code> Validation-Calibrated CRC, <code>λ*=0.15</code>)</th><th class="num-col">Key Metric / Result</th><th class="num-col">Comparison / Causal Attribution</th></tr>
  <tr><td><strong>Exp 16A: Censored-Arrival Survivorship Bias</strong></td><td class="num-col">Train 55.83% dropped; <code>age_3d</code> d0-open 62.63%</td><td class="num-col">Understates Q20 drops <strong>1.82–2.00×</strong> (Train), <strong>2.54×</strong> (Holdout: -10.55% vs -26.82%)</td></tr>
  <tr><td><strong>Exp 16B: Heteroscedastic Coverage Illusion</strong></td><td class="num-col"><code>Q1_Calm</code> 90.46% → <code>Q4_Volatile</code> <strong>67.80%</strong></td><td class="num-col"><strong>22.66 pp</strong> collapse (Val: 88.91%→67.84%, -21.07 pp); Q4 true Q80 err 17.08% vs 8.89%</td></tr>
  <tr><td><strong>Exp 16C: HP Apple <code>B2_Disp &amp; MG_Refuse</code></strong></td><td class="num-col">Blocked by <strong><code>T1</code>: 77.82%</strong> (82.75% warmup)</td><td class="num-col">Blocked by T4 LCB: 22.18% (overturning initial T4 guess)</td></tr>
  <tr><td><strong>Exp 17 Causal Rungs (Holdout <code>N=69,526</code>)</strong></td><td class="num-col"><code>MG_v1</code> ₹452.79 → <code>R1</code> ₹455.15 → <code>R2</code> ₹469.29</td><td class="num-col">→ <strong><code>R3 MandiGuard-CRC</code>: ₹479.17/qtl</strong> (₹14,375.1 truck, 10.48% LTR, 9.07 calls)</td></tr>
  <tr class="highlight"><td><strong>Exp 17 Cluster Bootstrap (<code>R=5,000</code>, <code>N=69,526</code>)</strong></td><td class="num-col"><strong>+₹129.16 vs <code>B1</code></strong> (<code>p=0.0004</code>) • <strong>+₹32.51 vs <code>B2</code></strong> (<code>p=0.0016</code>)</td><td class="num-col"><strong>+₹26.38 vs <code>MG_v1</code></strong> (<code>p=0.0002</code>) • -36.36 pp Ep Loss vs <code>B3</code></td></tr>
  <tr><td><strong>Exp 17 Trap-Free Open-Yard Check (<code>N=10,162</code>)</strong></td><td class="num-col"><strong>₹533.75/qtl</strong> (55.4% disp, 7.14% LTR, -₹35.0 CVaR)</td><td class="num-col">Beats <code>MG_v1</code> (+₹22.86), <code>B1</code> (+₹61.24), <code>B2</code> (+₹63.76); half <code>B3</code>'s 14.77% LTR</td></tr>
  <tr><td><strong>Exp 17 HP Graded Apple (<code>N=1,537</code>)</strong></td><td class="num-col"><strong>₹812.08/qtl (+34.2%)</strong> • Grade A <code>₹205→₹478</code></td><td class="num-col">Grade A LTR 20.0%→11.54%; still below <code>B2</code> ₹1,151 at 2.4× smaller CVaR<sub>10%</sub></td></tr>
</table>

<div class="figure-box">
  <img src="{fig9}" alt="Figure 8: Stage-II Mechanistic Autopsy and Uncensored CRC"/>
  <div class="figure-caption"><strong>Figure 8 (<code>Exp 16</code>–<code>Exp 17</code>, Stage II <code>[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]</code>):</strong> (A) Censored-arrival Q20 understatement reaching 2.54× on stale Holdout quotes; (B) Commodity-pooled Stage-I conformal coverage collapsing 22.66 pp on Holdout across volatility quartiles (while Table 8 documents 77.82%–82.75% HP Apple refusals at <code>T1</code>); (C) Post-diagnostic CRC factorial ablation ladder reaching <strong>₹479.17/qtl</strong> on 6-State Holdout (<strong>+₹32.51/qtl</strong> vs <code>B2</code>, <code>p = 0.0016</code>) and <strong>₹812.08/qtl</strong> on HP Graded Apples.</div>
</div>

<h2>5.5 Exploratory Appendix Illustrations (<code>Exp 11</code>–<code>Exp 13b</code> — Framed Strictly Outside Core Contributions)</h2>
<div class="box box-warning" style="padding:7px 10px;">
  <strong>Scope Note:</strong> Experiments <code>Exp 11–Exp 13b</code> below are exploratory post-hoc architectural and cooperative deployment illustrations using un-preregistered forecasters or stylized operational costs (₹0.05/call API pricing, 0.70× FPO truck scaling, 50/50 split lots), strictly separated into Thesis Appendix A.
</div>

<div class="figure-box">
  <img src="{fig7}" alt="Figure 7: Decade Evolution and Modern AI"/>
  <div class="figure-caption"><strong>Figure 7 (Exp 10 [Left, Main] &amp; Exp 11 [Right, Appendix]):</strong> Across 661,192 decade trips (Left), <code>MandiGuard</code> holds loss trips at 8.78%–12.03%. Right (Appendix A.1): on 6-state holdout, <code>Direct_Quantile_GBDT_Q20</code> reaches ₹459.02/qtl (9.40% LTR); on shifted HP Apples, <code>Deep_MLP_Conformal</code> hits ₹615.34/qtl and <code>MandiGuard_ACI</code> (α_Apple 0.200→0.164) trims CVaR<sub>10%</sub> by 27.6% (-₹102.76→-₹74.42).</div>
</div>

<div class="figure-box">
  <img src="{fig8}" alt="Figure A1: Appendix ZeroCloud, FPO Pooling & Spoilage Clock"/>
  <div class="figure-caption"><strong>Figure A1 (Appendix A.2/A.3 — Exp 12, 13, 13b):</strong> <code>ZeroCloud_Full</code> caches OSRM distances + 0.09 ms CPU inference offline (pre-ranking shorter roads to ₹455.33/qtl at 5.53 calls = ₹2,764 per 10k queries @ ₹0.05/call vs ₹7,868 for <code>B4</code>); adding ≥₹250 satisficing exit drops calls to 3.84 (<strong>-75.6% modeled API spend</strong>, ₹1,922/10k). Sharing a 90-qtl <code>FPO</code> truck (0.70× freight) raises net gain to ₹477.28/qtl; 50/50 split across Top-2 reduces traps 39% (16.17%→9.85%); Tomato 15% Q10 safe transit shrinks from 110.8h (20°C) to 24.1h (42°C) inside sample <code>&le;160</code>-char SMS alerts.</div>
</div>
"""


def sec_ch6_defense_playbook() -> str:
    return """
<div class="page-break"></div>
<h1 class="chapter-title">Chapter 6: Complete Synopsis &amp; Thesis Viva Defense Playbook</h1>

<h2>6.1 Word-for-Word Spoken Scripts (1-Min Elevator, 5-Min Synopsis &amp; 15-Min Viva)</h2>
<div class="quote-script">
  <strong>1-Minute Elevator Pitch:</strong> "Every morning, price apps tell Indian vegetable and apple farmers that a distant mandi 200 km away pays ₹500–₹1,300/qtl more than their home yard. Across 69,526 holdout dispatch opportunities in six Indian states (Maharashtra, UP, Karnataka, MP, Gujarat, Himachal Pradesh), 58.94% of naive price-chasing dispatches hit closed yards or missing variety auctions and 40.46% lose money—a gap we call Phantom Spatial Arbitrage, where unfiltered point-ML loses even more often (45.28%). My thesis follows a strict Two-Stage architecture verified across nearly 10 years of AGMARKNET records (42.72M raw rows, dual-tier verified in Exp 14 against 172 official data.gov.in XML keys and a 149-day AGMARKNET 2.0 export of 2,042 keys at 100.00% Min/Max/Modal parity): In <strong>Stage I (Pre-Registered)</strong>, MandiGuard v1 (T1 → T2 → T3 → T4 + frozen 2024 HGBR + causal 80% conformal LCB) beats naive portals by +₹102.78/qtl (+₹3,083.5 per 30-qtl truck), cuts episode losses by 37.29 pp vs point-ML, and saves 44.4% external calls, while tying fresh-road greedy B2 on mean (+₹6.13/qtl, p = 0.27). In <strong>Stage II (<code>[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]</code>, Exp 16–17)</strong>, our autopsy showed dropna censoring understated 3-day downside risk up to 2.54×, pooled conformal coverage swung 90.46%→67.80%, and sub-grade T1 sparsity blocked 77.82% of holdout Apple lots vs B2. Training dual-head estimators on uncensored payoff Y_full with validation-frozen penalty λ* = 0.15 plus grade-aware T1 raises holdout return to <strong>₹479.17/qtl</strong>—beating B1 (+₹129.16), <strong>B2 (+₹32.51, p = 0.0016)</strong>, and MG_v1 (+₹26.38), winning trap-free N = 10,162 open yards (₹533.75/qtl), and lifting 2026 HP Graded Apples +34.2% (₹812.08/qtl)."
</div>

<div class="box box-math">
  <div class="box-title">5-Minute Synopsis Defense &amp; 15-Minute Final Viva Slide-by-Slide Guide</div>
  <ul style="margin-bottom:0;">
    <li><strong>5-Minute Pitch (5 Slides):</strong> <strong>Slide 1 (~45s):</strong> NSO NSS 587 (30-qtl truck, ₹3,798/mo net income); why ₹1,330.49/qtl spread loses 40.46% (-₹31,879.8 worst-10% load). <strong>Slide 2 (~60s):</strong> 10-yr dataset (42.72M raw → 178 2024-ranked yards, Dual-Tier Exp 14: 172 XML + 2,042 149d AGMARKNET 2.0 keys, 8,147 OSRM routes, ERA5+NASA POWER, GoI NABCONS/APMC/GoHP anchors). <strong>Slide 3 (~60s):</strong> Ordered <code>T1→T2→T3→T4</code> cascade (-44.4% calls; +₹104.54/qtl at <code>B=6</code>). <strong>Slide 4 (~90s):</strong> Stage-I Holm (<code>H1, H3, H4</code> supported; <code>H2</code> tie p=0.27) + Open-Yard Exp 15 (<code>N=10,162</code>) + <strong>Stage-II Autopsy &amp; MandiGuard-CRC</strong> (Exp 16–17: ₹479.17/qtl, +₹32.51 vs B2 <code>p=0.0016</code>, ₹533.75 open d0, ₹812.08 Apple). <strong>Slide 5 (~15s):</strong> Open limitations (modeled field parameters, Stage-II post-diagnostic label, 22/22 <code>pytest</code> verifies reproducibility/leakage) + &lt;3-min Colab pack (4.83 MB).</li>
    <li><strong>15-Minute Viva Walkthrough:</strong> <strong>Min 0–2:</strong> Whiteboard 5-line Tomato arithmetic (Stage I vs Stage II CRC scoring) contrasting Jensen (2007) vs Chatterjee &amp; Kapur (2017) &amp; Levi et al. (2020). <strong>Min 2–5:</strong> Pivot from <code>EVA-Mandi</code> v1; Dual-Tier Exp 14 audit, district HQ ≤110 km geocoding guard, Ridge weather imputation on 43 cells. <strong>Min 5–8:</strong> Chronological firewall, 17 causal features, Min-Heap maturation firewall, 80% LCB justification via Chow (1970). <strong>Min 8–12:</strong> Stage-I tables + Exp 15 crossover + Stage-II Exp 16–17 (censored 2.54× bias, 22.66 pp Q1→Q4 collapse, 77.82% Apple T1 sparsity, λ*=0.15 Val heuristic, Rungs 0–3 to ₹479.17/qtl) + optional Appendix <code>ACI</code>/<code>ZeroCloud</code>/<code>FPO</code>. <strong>Min 12–15:</strong> State all 5 Red-Lines calmly + offer live <code>pytest</code> / Colab run.</li>
  </ul>
</div>

<h2>6.2 The 5 Non-Negotiable Red-Lines (Never Overclaim These in Viva!)</h2>
<div class="box box-redline">
  <ol style="margin-bottom:0;">
    <li><strong>NEVER claim Theorem 1 exchangeability guarantees for Stage I or Stage II CRC:</strong> Stage-I coverage is empirical (78.85% val / 79.07% holdout) and Stage-II <code>(n_l+1)/(n_d+1)≤0.095</code> (<code>λ*=0.15</code> for Rung 3; <code>0.10</code> for Rung 2) is a <code>Val_2025H1</code> (<code>N=42,794</code>) calibration heuristic adapted from Angelopoulos et al. (2024)—non-stationary crop prices and varying <code>n_disp(λ)</code> break Theorem 1 assumptions.</li>
    <li><strong>NEVER pass Stage-II <code>MandiGuard-CRC</code> (₹479.17) off as pre-registered Stage I:</strong> Keep commit <code>e421d15</code> Stage I (₹452.79) strictly separate from <code>[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]</code> Stage II (anti-HARKing discipline).</li>
    <li><strong>NEVER claim an autonomous LLM/RL agent or beating point-ML mean on open yards:</strong> Zero runtime LLM/RL calls; and on <code>N=10,162</code> guaranteed-open yards, <code>B3</code> still tops unconditional mean (₹553.22 vs <code>MandiGuard-CRC</code> ₹533.75) at 2.1× LTR (14.77% vs 7.14%) and 10× deeper CVaR<sub>10%</sub>.</li>
    <li><strong>NEVER claim live farmer weighment receipts or full multi-year official API archival:</strong> Dual-Tier Exp 14 audits <code>172</code> XML keys + <code>2,042</code> 149-day AGMARKNET 2.0 keys; truck hire, Q10 rot, and diversion penalties remain modeled; <strong>22/22 <code>pytest</code></strong> checks prove deterministic code, Dual-Tier parity, &amp; zero future leakage—not field economics.</li>
    <li><strong>NEVER present Appendix illustrations (<code>Exp 11–13b</code>) as primary thesis contributions.</strong></li>
  </ol>
</div>

<h2>6.3 Complete Master Viva Q&amp;A Bank (All 50 Tough Examiner Questions)</h2>

<h3>Group A — Motivation, Novelty &amp; Agricultural Economics (Q1–Q9)</h3>
<div class="qa-item"><div class="qa-q">Q1. In one sentence, what is "Phantom Spatial Arbitrage"?</div><div class="qa-a">An apparent cross-mandi profit spread on price boards that turns negative or fails to execute once highway freight, state charges, variety/grade mismatches, closed destination yards, ambient rot, and arrival price drops are included (40.46% loss rate across 63,040 naive dispatches).</div></div>
<div class="qa-item"><div class="qa-q">Q2. Why didn't you just predict tomorrow's mandi price like most ML papers?</div><div class="qa-a">When yards are open on arrival day (<code>N=10,162</code>, Exp 15), point-ML <code>B3</code> earns higher mean (₹553.22/qtl) at 2.2× LTR (14.77%) and 10× deeper tail (-₹362.40). Across the full market (<code>N=69,526</code>), <code>B3</code> loses 45.28% of the time (65.65% traps, ₹330.85/qtl)—worse than naive <code>B1</code>—because it lacks <code>T1</code> openness checks and <code>T4</code> downside buffers.</div></div>
<div class="qa-item"><div class="qa-q">Q3. Why is MandiGuard scientific decision support rather than "simple if-else business rules"?</div><div class="qa-a">Verbal rule router <code>B6</code> loses -₹20.85/qtl vs <code>MandiGuard</code> (higher traps, 34.9% more calls); removing <code>T4</code> conformal LCB raises LTR 9.97%→16.89% and crashes CVaR -₹37.89→-₹397.19; and ascending-cost gating beats upfront <code>B4</code> by +₹104.54/qtl at <code>B=6</code>.</div></div>
<div class="qa-item"><div class="qa-q">Q4. What happened to your earlier multi-ensemble EVA-Mandi attempt? Why pivot?</div><div class="qa-a">Stacking 9 ensembles, Duan smearing, and Knowledge-Gradient integrals over small HP Apple subsets failed 4/5 pre-registered hypotheses and trailed a staleness filter. Preserving that archive untouched, we pivoted cleanly to multi-state physical arbitrage with transparent engineering math, supporting <code>H1, H3, H4</code>.</div></div>
<div class="qa-item"><div class="qa-q">Q5. Why is your local-sale option (<code>REFUSE_PHANTOM_SPREAD</code>) theoretically justified?</div><div class="qa-a">Chow (1970) and Franc et al. (2023) show abstaining is Bayes-optimal whenever false-positive mistake cost (sunk logistics + rot + diversion up to -₹1,062.66/qtl tail) far outweighs safe deterministic local realization (₹0).</div></div>
<div class="qa-item"><div class="qa-q">Q6. How are truckload size and household income grounded?</div><div class="qa-a">Directly from NSO NSS Report No. 587 (77th Round): Potato/Onion harvests average 29.33–38.73 qtl (grounding 30-qtl mini-truck) and net monthly household crop income averages ₹3,798—making +₹102.78/qtl (+₹3,083.5/load) 81.2% of monthly crop income.</div></div>
<div class="qa-item"><div class="qa-q">Q7. How do AgriMarket AI (2026) and Mandi Cast (2026) differ from MandiGuard?</div><div class="qa-a">They compute point gains using Haversine distances or weather price covariates without exact variety matching, arrival-weekday openness checks, Q10 transit spoilage, or selective conformal refusal—placing them in the <code>B1/B3</code> baseline family.</div></div>
<div class="qa-item"><div class="qa-q">Q8. Which crop suffers the highest phantom-loss rate, and why?</div><div class="qa-a">Onion (48.69% LTR under <code>B1</code>, ₹53.61 net on ₹704.50 spread) because slim margins are absorbed by ₹138.07 freight and ₹484.23 variety traps/drops. Apple suffers largest absolute erosion (₹3,499.8→₹1,982.36 traps/drops), and Tomato has highest market decay (3.25%/24h).</div></div>
<div class="qa-item"><div class="qa-q">Q9. Why did naive B1 get a higher Tomato mean (₹547.64) than MandiGuard (₹522.48)?</div><div class="qa-a"><code>B1</code> chases rare scarcity spikes that boost averages while losing money 32.38% of the time (1 in 3 trips). <code>MandiGuard</code> cuts Tomato episode losses to 5.09% and still beats <code>B2</code> Fresh+OSRM (₹484.64) by +₹37.84/qtl.</div></div>

<h3>Group B — Data Provenance, Official Anchors &amp; Physical Model (Q10–Q19)</h3>
<div class="qa-item"><div class="qa-q">Q10. Where did your 10-year mandi data come from, and what did Dual-Tier Exp 14 verify?</div><div class="qa-a">Public AGMARKNET archive mirror (42.72M raw rows streamed with SHA-256 checksums). Dual-Tier <code>Exp 14</code> verifies: <strong>Tier 1</strong> (<code>2023-10-18</code>, <code>172</code> keys vs <code>data.gov.in</code> Resource <code>9ef84268-d588-465a-a308-a864a43d0070</code> XML: 100.0% Min/Max, 99.42% Modal parity) and <strong>Tier 2</strong> (<strong>149-day direct official AGMARKNET 2.0 export</strong>, <code>2,042</code> matched market–variety–grade–day rows: <strong>100.00% Min/Max/Modal parity</strong>).</div></div>
<div class="qa-item"><div class="qa-q">Q11. How did you prevent survivorship bias when picking 178 core markets?</div><div class="qa-a">Markets were eligible and top-30 ranked per state using strictly calendar <strong>2024</strong> trading days (28 eligible in HP → 178 yards)—never peeking into 2025–2026 holdout closures.</div></div>
<div class="qa-item"><div class="qa-q">Q12. Where did base spoilage rates come from? Were they tuned?</div><div class="qa-a">Zero tuning: taken verbatim from MoFPI/NABCONS (2022) Annexure-II Table-2 (PIB PRID 2151371): Tomato 3.25%, Onion 1.96%, Apple 1.64%, Potato 0.86%.</div></div>
<div class="qa-item"><div class="qa-q">Q13. Don't you lack live farmer weighment receipts for freight, rot, and diversion penalties?</div><div class="qa-a">Yes—disclosed openly in Section 8. Trucking fees, Q10 rot, and diversion penalties are modeled rather than field-measured; yet observed AGMARKNET traps/drops drive ₹714.90/qtl erosion vs ₹68.76 spoilage, all 9/9 Exp 6 cells stay positive, and Exp 15 isolates fair observed cohorts and crossover sweeps.</div></div>
<div class="qa-item"><div class="qa-q">Q14. Why do cross-district APMC fees differ across your 6 states?</div><div class="qa-a">Agricultural marketing is a State subject (PIB 154554): KA &amp; GJ waive F&amp;V fees (0.5% user fee); HP exempts veg (0.5%) except Apple (1.0%); MH charges 1.0% inside APMC; MP &amp; UP levy 1.5%. Verified state rules lift spreads +₹7.12/qtl vs uniform 1.5% (Exp 6).</div></div>
<div class="qa-item"><div class="qa-q">Q15. Why does Himachal Pradesh carry a 1.45× freight multiplier?</div><div class="qa-a">Grounded directly in GoHP Economic Survey 2025–26 Table 28: 91.59% (39,465 / 43,091 km) of HP motorable roads are single-lane mountain roads.</div></div>
<div class="qa-item"><div class="qa-q">Q16. What happened when Open-Meteo hit daily rate limits on 43 northern grids?</div><div class="qa-a">We respected HTTP 429 cleanly. 145/145 realized ERA5 completed, plus 102/145 native NWP cells. The 43 remaining cells used a causal 2024 Ridge nowcaster using only day <code>≤ t</code> ERA5 (1.047°C MAE, verified by pytest), and Exp 2b confirmed +₹31.82/qtl over <code>B2</code> in the 4 full-NWP states.</div></div>
<div class="qa-item"><div class="qa-q">Q17. How did you prevent geocoding errors (Neemuch/Gonda homonym mismatches)?</div><div class="qa-a">Enforced <code>admin2</code> district-alias validation and a hard ≤110 km Haversine check against District HQ coordinates across all 220 mandis (checked in <code>pytest</code>).</div></div>
<div class="qa-item"><div class="qa-q">Q18. How do you handle clerks entering "Onion", "Other", and "FAQ" interchangeably?</div><div class="qa-a">Canonicalize generic commodity name, "Other", and "FAQ" to "Standard" and unify spellings ("Deshi"→"Desi"), while preserving commercial cultivars ("Red", "Hybrid", "Royal Delicious").</div></div>
<div class="qa-item"><div class="qa-q">Q19. What did the Live November 2026 AGMARKNET query check (Exp 8) show?</div><div class="qa-a">22 live queries on <code>agmarknet.gov.in</code> (Nov 17, 2026) found 11/22 (50.0%) benchmark corridors reported zero trades across the entire preceding 7 days.</div></div>

<h3>Group C — ML, Conformal Bounds, Statistics &amp; Limitations (Q20–Q35)</h3>
<div class="qa-item"><div class="qa-q">Q20. Explain Conformal Prediction (T4) in plain English.</div><div class="qa-a">Check how badly your forecast over-predicted across the last 400 settled trips, take the 80th-percentile worst downside miss (e.g., 8%), and subtract it from today's forecast so ~80% of arrivals clear your floor.</div></div>
<div class="qa-item"><div class="qa-q">Q21. Doesn't Conformal Prediction assume i.i.d. exchangeability—violated by prices?</div><div class="qa-a">Yes—disclosed candidly. Because seasons break strict exchangeability, we verify empirical chronological coverage directly (78.85% val, 79.07% holdout) and test adaptive ACI in Appendix A.1.</div></div>
<div class="qa-item"><div class="qa-q">Q22. Why train on 2024 only and never refit weights on 2025–2026?</div><div class="qa-a">Freezing tree weights in 2024 guarantees a clean 15-month out-of-time robustness test without holdout refitting leakage; only the 400-sample conformal residual window adapts causally.</div></div>
<div class="qa-item"><div class="qa-q">Q23. How was <code>safety_margin_inr = ₹50/qtl</code> selected?</div><div class="qa-a">Swept over <code>{50, 100, 150, 200, 250}</code> strictly on <code>Val_2025H1</code> (₹351.36/qtl mean, 9.68% LTR), locked in <code>frozen_calibration.json</code> and Git commit <code>e421d15</code> before unblinding holdout.</div></div>
<div class="qa-item"><div class="qa-q">Q24. Why did H2 (MandiGuard &gt; B2 Mean) fail significance (p = 0.27)?</div><div class="qa-a"><code>B2</code> ties <code>MandiGuard</code> on overall mean (₹446.66 vs ₹452.79; +₹6.13 is cluster noise). <code>MandiGuard</code> trades risky marginal dispatches (48.66% vs 62.11%) to halve loss rate (9.97% vs 18.11%) and reduce tail loss (-₹37.89 vs -₹436.67).</div></div>
<div class="qa-item"><div class="qa-q">Q25. Why use Two-Way Mandi × 2-Week-Block Bootstrap instead of a paired t-test?</div><div class="qa-a">Episodes correlate within the same mandi over time and across mandis sharing weekly shocks. Resampling 174 mandis × 23 two-week blocks together prevents artificially narrow CIs (yielding <code>[+₹48.66, +₹153.45]</code> for H1) with Phipson–Smyth + Holm control.</div></div>
<div class="qa-item"><div class="qa-q">Q26. In Exp 4, why does removing T3 slightly raise overall mean by ₹2.46/qtl?</div><div class="qa-a"><code>T3</code> + <code>T4</code> stack conservatively; dropping <code>T3</code> admits 1.52% extra hot/rainy trips whose spot spikes beat modeled rot slightly overall, while keeping <code>T3</code> protects the 21,656 extreme-weather episodes (LTR 11.39%→10.10%, CVaR -₹67.49→-₹57.11).</div></div>
<div class="qa-item"><div class="qa-q">Q27. On HP Graded Apples (Exp 3), why did B2 earn ₹1,150.83 vs Stage-I MandiGuard ₹605.06—and what did Exp 16 prove really happened?</div><div class="qa-a">Initially we guessed wide <code>T4</code> conformal bounds blocked scarce 2026 Grade A lots. <code>Exp 16</code> disproved that: <strong>77.82%</strong> of holdout refusals vs <code>B2</code> (<code>82.75%</code> warmup) were blocked at <strong><code>T1</code></strong> due to sub-grade rolling sparsity (<code>open_prob_14d &lt; 0.50</code>), vs only 22.18% at <code>T4</code>. Stage I still cut traps 7× (94.14%→13.24%), and Stage-II grade-aware <code>T1</code> lifts Apple mean <strong>+34.2% to ₹812.08/qtl</strong>.</div></div>
<div class="qa-item"><div class="qa-q">Q28. Is MandiGuard an autonomous LLM agent? Why no GPT-4 at decision time?</div><div class="qa-a">No—deterministic risk-gated decision-support system. Avoiding runtime LLMs guarantees &lt;0.1 ms latency, ₹0 token fee, zero hallucinations, and SMS/edge feasibility.</div></div>
<div class="qa-item"><div class="qa-q">Q29. Why did 3-module coordinator B5 earn -₹15.40/qtl less than unified MandiGuard?</div><div class="qa-a">Passing coarse ₹150 profit buckets loses boundary precision near the ₹50/qtl threshold without saving calls (8.76 vs 8.75).</div></div>
<div class="qa-item"><div class="qa-q">Q30. Does your model transfer to an unseen state (Exp 9)?</div><div class="qa-a">Yes: Leave-One-State-Out zero-shot transfer beat <code>B1</code> in 6/6 held-out states (+₹11.50 to +₹424.19/qtl), cutting arrival drops to 3.34%–9.72% (vs 45.3%–55.7%).</div></div>
<div class="qa-item"><div class="qa-q">Q31. What are the top rejection reasons across all 69,526 episodes (Exp 7)?</div><div class="qa-a">Dispatch 48.66% (12.30 calls); T1 Variety/Stale 25.48% (3.64 calls); T4 Arrival Reversion 17.58%; T1 Closed Risk 5.34% (3.04 calls); T2 Freight 2.24%; T3 Weather 0.71%.</div></div>
<div class="qa-item"><div class="qa-q">Q32. Why model +1/+2 wait days (₹25/day detention) instead of immediate abandonment?</div><div class="qa-a">Mirrors real trucker behavior around rotating mid-week yard closures: drivers wait 1–2 mornings paying parking and extra decay before liquidating or diverting.</div></div>
<div class="qa-item"><div class="qa-q">Q33. What happens under freight spikes or refrigerated trucks (Exp 6)?</div><div class="qa-a">Across 9/9 grid cells in <code>[0.75×..1.25×]</code> freight × <code>[0.5×..1.5×]</code> spoilage, <code>MandiGuard</code> beats <code>B1</code> (+₹82.62 to +₹121.42/qtl), beats <code>B2</code> at 1.0–1.5× rot (+₹5.27 to +₹14.50), and matches <code>B2</code> within -₹1.52/qtl at 0.5× rot.</div></div>
<div class="qa-item"><div class="qa-q">Q34. Why bound corridors to 15–500 km intra-state?</div><div class="qa-a">Reflects typical 30-qtl smallholder single-truck dispatch without inter-state permits; 1,500+ km interstate wholesale corridors remain future work.</div></div>
<div class="qa-item"><div class="qa-q">Q35. How can someone reproduce all experiments independently?</div><div class="qa-a">Run <code>notebooks/colab_standalone_reproduction.ipynb</code> + <code>colab_data_pack.tar.gz</code> (4.83 MB) in Google Colab in under 3 minutes, or run <code>pytest</code> locally (reproducing Stage I, Stage II CRC, Dual-Tier Exp 14, and Appendix checks).</div></div>

<h3>Group D — 10-Year Scale, Appendix Illustrations &amp; Tough Probes (Q36–Q44)</h3>
<div class="qa-item"><div class="qa-q">Q36. Does MandiGuard hold up across GST, COVID, Export Curbs, and El-Niño (2017–2026)?</div><div class="qa-a">Across 661,192 matched episodes over 6 regimes (<code>Exp 10</code>), causally expanding <code>MandiGuard</code> holds LTR to 8.78%–12.03% (vs 39.18%–44.29% naive) and beats <code>B1</code> by +₹165.14/qtl during 2024 El-Niño.</div></div>
<div class="qa-item"><div class="qa-q">Q37. Does training on 8 years (3.44M rows) beat 1 year (2024, 702k rows)?</div><div class="qa-a">Only +₹2.15/qtl (₹454.94 vs ₹452.79/qtl, Exp 10b): shifting spread regimes make recent fit + conformal bounds far more valuable than stale volume.</div></div>
<div class="qa-item"><div class="qa-q">Q38. (Appendix Exp 11) How did Quantile GBDT, Deep MLP, Bandits, and ACI perform?</div><div class="qa-a"><code>Direct_Quantile_GBDT_Q20</code> reached ₹459.02/qtl on 6 states; <code>Deep_MLP_Conformal</code> reached ₹615.34 on HP Apple; <code>MandiGuard_ACI</code> trimmed HP Apple CVaR<sub>10%</sub> 27.6% (-₹102.76→-₹74.42).</div></div>
<div class="qa-item"><div class="qa-q">Q39. (Appendix Exp 12) What is the real &amp; modeled API cost picture?</div><div class="qa-a"><strong>Actual project API spend = ₹0.00</strong> (public portals, OSRM, open climate grids, local CPU inference). Under illustrative ₹0.05/call commercial pricing (<code>Exp 12</code>), caching OSRM + local CPU <code>T4</code> drops live calls to 5.53 (₹2,764/10k queries vs ₹7,868 <code>B4</code>), and ₹250 satisficing exit hits 3.84 calls (-75.6% cost, ₹1,922/10k). Crucially, API rupee savings are minor vs crop profits; reducing calls mainly boosts rural 2G/3G responsiveness and avoids government API throttling.</div></div>
<div class="qa-item"><div class="qa-q">Q40. (Appendix Exp 13/13b) What do FPO pooling, Split-Lot, and Spoilage Clock illustrate?</div><div class="qa-a">90-qtl shared FPO trucks (0.70×) raise gain to ₹477.28/qtl; 50/50 Top-2 splitting cuts closed traps 39% (16.17%→9.85%); Tomato 15% Q10 safe window drops from 110.8h (20°C) to 24.1h (42°C) inside <code>&le;160</code>-char SMS cards.</div></div>
<div class="qa-item"><div class="qa-q">Q41. Isn't H4 (44.4% fewer calls than B4) obvious by construction?</div><div class="qa-a">Yes—fewer average calls (8.75 vs 15.74) follow directly by ordering cheap <code>T1</code> checks first. The empirical benefit shows under tight query budgets (<code>B=6</code>, Exp 5: +₹104.54/qtl over <code>B4</code>).</div></div>
<div class="qa-item"><div class="qa-q">Q42. How thoroughly was the archive mirror checked against official government servers?</div><div class="qa-a">Dual-Tier Exp 14 verified <code>172</code> keys on <code>2023-10-18</code> vs official <code>data.gov.in</code> XML (100% Min/Max, 99.42% Modal) AND <code>2,042</code> matched rows across <strong>149 trading days</strong> of direct <code>AGMARKNET 2.0</code> exports (100.00% Min/Max/Modal) + 22 live Nov-2026 queries.</div></div>
<div class="qa-item"><div class="qa-q">Q43. How do you defend Exp 15 if missing 3d entries have zero penalty or all yards are open?</div><div class="qa-a">Dual-view proof: View 1 crossover leads through 0.5×/5% (+₹42.43/qtl vs <code>B1</code>) and crosses only at 0.0×/0% (-₹10/qtl, holding LTR at 6.09% vs 18.52%); View 2 fair matched open-yard cohort (<code>N=10,162</code>) beats <code>B1/B2</code> while proving <code>B3</code> needs <code>T1+T4</code> on full markets.</div></div>
<div class="qa-item"><div class="qa-q">Q44. What do your 22/22 pytest tests actually prove?</div><div class="qa-a">Deterministic code reproducibility, SHA-256 data manifest parity, Dual-Tier Exp 14 &amp; Stage-II Exp 16–17 consistency, district HQ coordinate bounds, bootstrap/Holm arithmetic, and zero future leakage—NOT real-world field economics without live truck receipts.</div></div>

<h3>Group E — Stage-II <code>[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]</code> Autopsy &amp; <code>MandiGuard-CRC</code> (Q45–Q50)</h3>
<div class="qa-item"><div class="qa-q">Q45. What is Censored-Arrival Survivorship Bias (Exp 16A), and how much did it distort Stage I?</div><div class="qa-a">Stage-I <code>dropna(target_ret)</code> discarded <strong>55.83%</strong> of raw 2024 corridors (12.64% post-<code>T1</code>). Exact <code>d0</code> open rate falls from 89.10% (<code>0d</code>) to 62.63% (<code>3d</code> in train; 62.97% holdout), causing complete-case Q20 downside returns to understate true uncensored tail drops by <strong>1.82–2.00×</strong> (Train) and up to <strong>2.54×</strong> on Holdout (<code>-10.55%</code> vs <code>-26.82%</code>).</div></div>
<div class="qa-item"><div class="qa-q">Q46. What is the Heteroscedastic Coverage Illusion (Exp 16B) in Stage-I bounds?</div><div class="qa-a">Pooled additive quantiles masked a <strong>21.07–22.66 pp quartile coverage collapse</strong>: on Holdout, <code>MG_v1</code> hit <strong>90.46%</strong> coverage in calm <code>Q1</code> markets (over-cushioning 6.04% vs 1.98% true error) while dropping to <strong>67.80%</strong> in volatile <code>Q4</code> markets (8.89% cushion vs 17.08% true Q80 error; Val <code>88.91%→67.84%</code>).</div></div>
<div class="qa-item"><div class="qa-q">Q47. How does MandiGuard-CRC score routes, and do you claim Angelopoulos et al. (2024) Theorem 1 guarantees?</div><div class="qa-a">Dual 2024 heads (regression <code>μ̂</code> + raw <code>HistGradientBoostingClassifier.predict_proba</code> risk <code>p̂_loss</code>) trained on <code>274,296</code> settled profitable post-<code>T1</code> uncensored routes <code>Y_full</code> score <code>Score = μ̂ − λ*·P_loc·p̂_loss</code> (requiring Score&gt;₹50 &amp; μ̂&gt;₹50). Sweeping <code>λ ∈ [0, 1.20]</code> on clean <code>Val_2025H1</code> (<code>N=42,794</code>, <code>arr_dt≤2025-05-31</code>) and stopping at the first feasible point (<code>break</code>) via <code>(n_l+1)/(n_d+1)≤0.095</code> freezes <strong><code>λ* = 0.15</code></strong> (<code>Rung 2</code> strict <code>T1</code> freezes at <code>0.10</code>; zero holdout tuning). We explicitly <strong>do NOT claim Theorem 1 guarantees</strong> because agri prices violate exchangeability and <code>n_disp(λ)</code> varies with <code>λ</code>; we use it strictly as an empirical validation heuristic audited out-of-sample.</div></div>
<div class="qa-item"><div class="qa-q">Q48. Why keep Stage I (₹452.79) frozen instead of replacing it with Stage II (₹479.17)?</div><div class="qa-a">Zero-HARKing discipline (Nosek et al. 2018): <code>H1–H4</code> were pre-registered in commit <code>e421d15</code> for Stage I. Any post-diagnostic fix discovered from Stage-I failures must be cleanly quarantined as <code>[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]</code> alongside causal rungs (Rung 0→3) proving <code>+₹26.38/qtl</code> vs <code>MG_v1</code> (<code>p=0.0002</code>) and <code>+₹32.51/qtl</code> vs <code>B2</code> (<code>p=0.0016</code>).</div></div>
<div class="qa-item"><div class="qa-q">Q49. Could MandiGuard-CRC just overfit to simulated closed-yard penalties in Y_full?</div><div class="qa-a">Tested directly on trap-free <code>Matched_AllTopK_Observed_d0</code> (<code>N=10,162</code>, zero simulated penalties): <code>MandiGuard-CRC</code> reaches <strong>₹533.75/qtl</strong> at 7.14% LTR and -₹35.00 CVaR, beating <code>MG_v1</code> (+₹22.86), <code>B1</code> (+₹61.24), and <code>B2</code> (+₹63.76) while cutting <code>B3</code>'s 14.77% LTR in half.</div></div>
<div class="qa-item"><div class="qa-q">Q50. Why did MandiGuard-CRC jump +34.2% on HP Apples (₹605.06→₹812.08) yet still trail B2 (₹1,150.83)?</div><div class="qa-a">Grade-aware <code>T1</code> removed 77.82% false sparsity blocks, lifting Grade A from ₹205.46 to <strong>₹477.56/qtl</strong> (LTR 20.0%→11.54%) and Grade B to <strong>₹852.01/qtl</strong>. Remaining gap vs <code>B2</code> reflects safety–volume tradeoff: <code>B2</code> accepts 28.43% LTR and -₹272.50 CVaR (-₹4,472.90 on Grade B), vs CRC's -₹113.40 CVaR.</div></div>

<div class="box box-numerical">
  <div class="box-title">10-Minute Blank-Paper Whiteboard Mastery Drill (Write From Memory Before Viva!)</div>
  <ol style="margin-bottom:0;">
    <li><strong>Stage I vs Stage II Tomato Math:</strong> ₹2,000 portal − ₹65.00 Q10 heat rot (3.25% @ 40°C, 6h) − ₹146.00 truck+1.5% MP tax → Stage I (<code>-₹154.80</code> 8% LCB = <strong>+₹234.20/qtl</strong>) vs Stage II (<code>μ̂ +320 − 0.15×1400×0.08 = <strong>+₹303.20/qtl</strong></code> → <code>DISPATCH</code>).</li>
    <li><strong>Holdout Summary (<code>N = 69,526</code>):</strong> <code>B1</code> (₹350.01, 40.46% LTR), <code>B2</code> (₹446.66, 18.11%), <code>B3</code> (₹330.85, 45.28%), Stage-I <code>MG_v1</code> (<strong>₹452.79, 9.97%, -₹37.89</strong>), Stage-II <code>MandiGuard-CRC</code> (<strong>₹479.17, 10.48%, +₹32.51 vs <code>B2</code></strong>).</li>
    <li><strong>Matched Open-Yard (<code>N = 10,162</code>) &amp; Apple:</strong> Open d0: <code>MG_v1</code> ₹510.89 → <strong><code>MandiGuard-CRC</code> ₹533.75 (7.14% LTR, -₹35.00 CVaR)</strong>; HP Apple: ₹605.06 → <strong>₹812.08/qtl (+34.2%)</strong>.</li>
  </ol>
</div>
"""


def build() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>MandiGuard — First-Principles Textbook &amp; Thesis Defense Playbook</title>
  <style>{CSS}</style>
</head>
<body>
{sec_cover_and_blueprint()}
{sec_ch1_first_principles()}
{sec_ch2_literature_deep_dive()}
{sec_ch3_under_the_hood()}
{sec_ch4_payoff_metrics_stats()}
{sec_ch5_experiments_and_figures()}
{sec_ch6_defense_playbook()}
</body>
</html>
"""
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"Wrote HTML: {HTML_OUT} ({HTML_OUT.stat().st_size / 1e6:.2f} MB)")

    if not CHROME_BIN.exists():
        raise FileNotFoundError(f"Chrome binary not found at {CHROME_BIN}")

    cmd = [
        str(CHROME_BIN),
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_OUT}",
        HTML_OUT.resolve().as_uri(),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not PDF_OUT.exists():
        print("STDOUT:", proc.stdout)
        print("STDERR:", proc.stderr)
        sys.exit(f"Chrome PDF generation failed with exit code {proc.returncode}")

    print(f"Wrote PDF: {PDF_OUT} ({PDF_OUT.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    build()
