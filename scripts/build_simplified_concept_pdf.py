#!/usr/bin/env python3
"""Build the Ultra-Simplified Concept & Most Relevant Research Papers PDF (Revision v8).

Designed for effortless, first-principles understanding and confident oral viva defense.
Grounded 100% in verified Revision v8 (Honest Candidate C Synthesis) outputs:
  - Primary 2024-only 171-market panel N = 57,634 (n_train_17m = 113,374 for 17m ML/CQR)
  - Specification-locked exploratory PREREG_A18 4-test R = 2,000 inference + CGM G*
  - Clean 166-market 2018-2023 N = 383,952 reverse-survivorship archive (481/647 excluded)
Outputs:
  - docs/MandiGuard_Ultra_Simplified_Concept_and_Key_Papers_Guide.html
  - docs/MandiGuard_Ultra_Simplified_Concept_and_Key_Papers_Guide.pdf
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

from scripts.build_revision_v5_deliverables import render_pdf

FIG_DIR = ROOT / "figures"
HTML_OUT = ROOT / "docs" / "MandiGuard_Ultra_Simplified_Concept_and_Key_Papers_Guide.html"
PDF_OUT = ROOT / "docs" / "MandiGuard_Ultra_Simplified_Concept_and_Key_Papers_Guide.pdf"


def img_uri(fname: str) -> str:
    data = base64.b64encode((FIG_DIR / fname).read_bytes()).decode("ascii")
    return "data:image/png;base64," + data


CSS = """
@page { size: A4; margin: 9.5mm 11mm 9.5mm 11mm; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 8.8pt;
  line-height: 1.38;
  color: #1e293b;
  margin: 0 auto;
  max-width: 188mm;
}
.hero {
  background: linear-gradient(135deg, #0b3b5c 0%, #0f5f7a 65%, #127475 100%);
  color: #ffffff;
  border-radius: 9px;
  padding: 12px 16px;
  margin-bottom: 9px;
}
.hero .tag {
  display: inline-block;
  background: rgba(255,255,255,0.18);
  border: 1px solid rgba(255,255,255,0.32);
  border-radius: 20px;
  padding: 2px 9px;
  font-size: 7.3pt;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 4px;
}
.hero h1 {
  margin: 0 0 4px 0;
  font-size: 17pt;
  line-height: 1.15;
  color: #ffffff;
}
.hero p {
  margin: 0;
  font-size: 8.8pt;
  color: #e0f2fe;
}
h2 {
  font-size: 11.4pt;
  color: #0b3b5c;
  border-left: 4px solid #0284c7;
  padding-left: 8px;
  margin: 9px 0 5px 0;
  break-after: avoid;
  page-break-after: avoid;
}
h3 {
  font-size: 9.5pt;
  color: #0f4c5c;
  margin: 6px 0 3px 0;
  break-after: avoid;
}
p { margin: 0 0 4.5px 0; }
ul, ol { margin: 2px 0 5px 0; padding-left: 16px; }
li { margin-bottom: 2.5px; }

/* Cards & Boxes */
.story-box {
  background: #f0f9ff;
  border: 1.5px solid #38bdf8;
  border-radius: 8px;
  padding: 8px 11px;
  margin: 5px 0 8px 0;
  break-inside: avoid;
}
.warn-box {
  background: #fffbeb;
  border: 1.5px solid #f59e0b;
  border-left: 5px solid #d97706;
  border-radius: 7px;
  padding: 7px 10px;
  margin: 5px 0 8px 0;
  break-inside: avoid;
}
.green-box {
  background: #ecfdf5;
  border: 1.5px solid #10b981;
  border-left: 5px solid #059669;
  border-radius: 7px;
  padding: 7px 10px;
  margin: 5px 0 8px 0;
  break-inside: avoid;
}
.formula-card {
  background: #f8fafc;
  border: 1.5px solid #0b3b5c;
  border-radius: 8px;
  padding: 7px 10px;
  margin: 5px 0 7px 0;
  break-inside: avoid;
}
.formula-big {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 10.5pt;
  font-weight: 700;
  color: #0b3b5c;
  text-align: center;
  background: #ffffff;
  border: 1px dashed #94a3b8;
  border-radius: 6px;
  padding: 4px 8px;
  margin: 4px 0;
}

/* Flowcharts */
.flow {
  display: flex;
  align-items: stretch;
  gap: 4px;
  margin: 5px 0 8px 0;
  break-inside: avoid;
}
.fstep {
  flex: 1;
  border-radius: 6px;
  padding: 5px 5px;
  text-align: center;
  font-size: 7.8pt;
  line-height: 1.25;
  border: 1.5px solid;
}
.fstep strong { display: block; font-size: 8.1pt; margin-bottom: 1.5px; }
.farrow { display: flex; align-items: center; font-size: 11pt; color: #64748b; font-weight: 700; }
.c-blue { background: #e0f2fe; border-color: #0284c7; }
.c-amber { background: #fef3c7; border-color: #d97706; }
.c-red { background: #fee2e2; border-color: #dc2626; }
.c-green { background: #dcfce7; border-color: #16a34a; }
.c-purple { background: #f3e8ff; border-color: #7c3aed; }

/* Two-column grids */
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; margin: 5px 0 7px 0; break-inside: avoid; }
.mini-card {
  background: #ffffff;
  border: 1.2px solid #cbd5e1;
  border-radius: 7px;
  padding: 6px 8px;
  font-size: 8.3pt;
}
.mini-card h4 { margin: 0 0 2.5px 0; font-size: 8.8pt; color: #0b3b5c; }

/* Stat strip */
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin: 5px 0 8px 0; break-inside: avoid; }
.kpi {
  background: #f8fafc;
  border: 1.5px solid #cbd5e1;
  border-top: 3px solid #0284c7;
  border-radius: 6px;
  padding: 5px 5px;
  text-align: center;
}
.kpi .val { font-size: 11.8pt; font-weight: 800; color: #0b3b5c; line-height: 1.15; }
.kpi .lbl { font-size: 7.2pt; color: #475569; margin-top: 2px; }

/* Tables */
table { width: 100%; border-collapse: collapse; margin: 4px 0 7px 0; font-size: 7.7pt; table-layout: fixed; break-inside: avoid; }
th { background: #0b3b5c; color: #ffffff; padding: 4px 5px; text-align: left; font-weight: 600; word-wrap: break-word; }
th code { background: rgba(255, 255, 255, 0.18); color: #ffffff; }
td { border: 1px solid #cbd5e1; padding: 3.5px 5px; vertical-align: top; word-wrap: break-word; }
tr:nth-child(even) td { background: #f8fafc; }
.num { text-align: right; }
.res-table { font-size: 7.5pt; }
.res-table td.num { line-height: 1.26; }
.es-tag { color: #0b3b5c; font-weight: 700; }
.hl td { background: #ecfdf5 !important; font-weight: 600; }

/* Figures */
figure {
  margin: 5px 0 7px 0;
  padding: 4px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #ffffff;
  text-align: center;
  break-inside: avoid;
}
figure img { max-width: 100%; max-height: 59mm; height: auto; }
figcaption { font-size: 7.6pt; color: #475569; text-align: left; margin-top: 2.5px; line-height: 1.28; }

.pillar-badge {
  display: inline-block;
  background: #0b3b5c;
  color: #ffffff;
  font-size: 7.1pt;
  font-weight: 700;
  padding: 1px 6.5px;
  border-radius: 4px;
  margin-bottom: 1.5px;
}
.qa-item {
  border-left: 3.5px solid #0284c7;
  padding: 3px 8px;
  margin-bottom: 3.5px;
  background: #f8fafc;
  border-radius: 0 5px 5px 0;
  font-size: 8.3pt;
  break-inside: avoid;
}
.qa-q { font-weight: 700; color: #0b3b5c; margin-bottom: 1px; }
.footer-note { font-size: 7.3pt; color: #64748b; margin-top: 4px; border-top: 1px solid #e2e8f0; padding-top: 3px; }
"""


HTML_BODY = f"""
<div class="hero">
  <span class="tag">Ultra-Simplified Visual Concept &amp; Literature Guide &bull; Revision v8 (Honest Candidate C Synthesis)</span>
  <h1>MandiGuard Explained Simply:<br/>The Full Concept, 2&times;2 Orthogonal Math, 17m ML Frontier &amp; Top 10 Papers</h1>
  <p><strong>Aditya Sharma (M.Tech Thesis Research, supervised by Dr. Sonia) &mdash; Shoolini University</strong> &bull; Everything needed to understand the research in 10 minutes and defend it calmly &mdash; plain-English intuition, 9-choice zero-weight cold-start rules vs full-season ML/CQR, and verified Revision v8 numbers.</p>
</div>

<div class="story-box">
  <h3 style="margin-top:0;">The Entire Thesis in One Real-Life Story (30 Seconds)</h3>
  <p>Imagine you manage a tomato farmer cooperative (FPO) in Madhya Pradesh. It is <strong>6:00 a.m.</strong> You open the government's <strong>AGMARKNET</strong> website on your phone. Your local mandi paid <strong>&#8377;1,500 per quintal</strong> yesterday, while another mandi 200 km away listed <strong>&#8377;2,000 per quintal</strong> yesterday.</p>
  <p style="margin-bottom:0;">That looks like an easy <strong>+&#8377;500/qtl profit</strong>! So you load a truck and send it. <strong>What goes wrong?</strong> When the truck arrives, three real-world traps hit: (1) truck freight, yard fees, and heat decay eat into the spread; (2) yesterday's &#8377;2,000 spike crashes back down in a volatile market; or (3) worst of all, the destination mandi has <strong>no auction running for your crop that day</strong> (a "silent/blank" arrival board), forcing an expensive turn-back. Our study proves that chasing tempting online spreads loses money nearly <strong>half the time (45.07%)</strong> &mdash; and shows how <strong>9-choice zero-tuned-weight pocket-calculator rules</strong> capture ~98.8% of full-season 17-month ML Mean and ~94% of conditional tail protection at <code>n_train = 0</code> <em>before</em> you call the destination trader on the phone.</p>
</div>

<div class="kpi-row">
  <div class="kpi"><div class="val">45.07%</div><div class="lbl">Loss rate when blindly chasing top portal spreads (ES10 &minus;&#8377;642.15)</div></div>
  <div class="kpi"><div class="val">9 Choices</div><div class="lbl">Zero tuned weights; ~98.8% of 17m ML Mean at n_train = 0</div></div>
  <div class="kpi"><div class="val">+&#8377;179.24</div><div class="lbl">ES10 gain (+&#8377;180.89 cond_ES10) on 171-mkt (exploratory Holm p=0.0040)</div></div>
  <div class="kpi"><div class="val">6 / 6 Years</div><div class="lbl">ES10 &amp; cond_ES10 gains across 166 mkts (2018&ndash;2023, N=384k)</div></div>
</div>

<h2>1. The Big Picture: How the Whole System Works (5 Simple Steps)</h2>

<div class="flow">
  <div class="fstep c-blue"><strong>Step 1: 6 a.m. Screen</strong>Check yesterday's prices only (never today's price &mdash; zero peeking!)</div>
  <div class="farrow">&rarr;</div>
  <div class="fstep c-amber"><strong>Step 2: 3 Real Costs</strong>Subtract road freight, stylized yard fee, and price volatility</div>
  <div class="farrow">&rarr;</div>
  <div class="fstep c-purple"><strong>Step 3: Cold-Start / ML</strong>Filter via 9-choice calculator (n=0) or 17m Mean-Q10 / Split-CQR</div>
  <div class="farrow">&rarr;</div>
  <div class="fstep c-green"><strong>Step 4: Live Phone Call</strong><code>PhoneCall_TopK_Open</code>: FPO calls destination <em>arhtiya</em> to confirm</div>
  <div class="farrow">&rarr;</div>
  <div class="fstep c-red"><strong>Step 5: Honest Settlement</strong>Track exact arrival outcome &mdash; including blank-yard Manski bounds</div>
</div>

<div class="grid2">
  <div class="mini-card">
    <h4>What This Tool ACTUALLY Is</h4>
    <ul>
      <li>An <strong>upstream 6 a.m. call-priority alert filter</strong> (<code>PhoneCall_TopK_Open</code>: 4.99% loss, <code>cond_ES10 &minus;&#8377;355.07</code> vs <code>B2 &minus;&#8377;691.79</code>) ahead of live trader dialing.</li>
      <li>Built strictly on <strong>&le; t&minus;1 public quotes</strong> across <strong>171 zero-lookahead markets</strong> (2025&ndash;2026) AND <strong>166 clean markets over 2018&ndash;2023 (383,952 trips)</strong> conditioned on 2024 corridor inclusion (reverse-survivorship: 481/647 historical markets excluded).</li>
      <li>Verified inside shared dispatches (<code>CommonIntersection_DS_cap_DB</code>, n=33,398): <strong>+&#8377;65.66 Mean &amp; +&#8377;53.40 ES10 pure routing lift</strong>.</li>
    </ul>
  </div>
  <div class="mini-card">
    <h4>What This Tool Does NOT Claim</h4>
    <ul>
      <li>Does <strong>NOT</strong> replace calling a trader (<em>arhtiya</em>) before loading a truck, nor claim 0-parameter beats full-season ML (17m <code>Mean-Q10</code> edges Mean &amp; tail at <code>n_train=113,374</code>).</li>
      <li>Does <strong>NOT</strong> measure actual farmer cash receipts (under <code>Outsider_MinPrice_LCV_4pctArh</code>, Safe_EV Mean compresses to &#8377;102.62 vs B2 &#8377;33.86).</li>
      <li>Does <strong>NOT</strong> guarantee exact OSRM coordinates everywhere: 56/171 markets collide on legacy parent coordinates (35.23% exact coverage, <code>N=6,605</code> still holds <code>p=0.001</code>).</li>
    </ul>
  </div>
</div>

<h2>2. Why Naive Online Spreads Fail: The Four Hidden Traps</h2>

<ol>
  <li><strong>Reporting Lag (Yesterday's Price &ne; Today's Price):</strong> At 6 a.m., today's auction hasn't happened yet. Many smaller mandis upload prices 1 to 7 days late. Yesterday's high price is often an outdated spike that already dropped.</li>
  <li><strong>Physical Frictions (Freight + Stylized Fees + Transit Decay):</strong>
    <ul>
      <li><strong>Road Freight (F):</strong> Base loading &#8377;35 + &#8377;0.45 per road km (&times;1.45 in Himachal Pradesh, where 91.59% of roads are single-lane hill roads; LCV + 4% <em>arhtiya</em> stress also tested).</li>
      <li><strong>Stylized State Fee Tiers:</strong> 0.5% to 1.5% charged on destination sale value (0% inside the same district or if unsold), anchored qualitatively to state APMC deregulation status (PIB 154554) and stress-tested from 0% to 6% commission.</li>
      <li><strong>Transit Decay:</strong> Modeled operationally from NABCONS (2022) marketing-level crop loss shares (Tomato 3.25%, Onion 1.96%, Apple 1.64%, Potato 0.86%), stress-tested under repaired <code>_spoil_return_leg</code> <code>S6</code> (full <code>24&tau;+hrs+24w</code> + ERA5: Safe_EV Mean &#8377;307.39, ES10 &minus;&#8377;576.57, <code>cond_ES10 &minus;&#8377;725.73</code>).</li>
    </ul>
  </li>
  <li><strong>Silent / Blank Arrival Boards (28.67% of Naive Trips!):</strong> On 28.67% of naive spread-chasing trips, the destination market uploads <em>no trade at all</em> for that crop on arrival day. Under sequential arrival rules (you don't know tomorrow's prices in advance!), a truck facing a blank yard turns back instead of gambling blindly.</li>
  <li><strong>Sunday / Weekly Holiday Blindness &amp; Price Swings:</strong> A mandi closed every Sunday still looks "75% active" in a 28-day average &mdash; fooling average-based filters on weekends. Meanwhile, high-variance markets (like Apple and Tomato) swing violently between yesterday and arrival day.</li>
</ol>

<h2>3. The Honest Candidate C Breakthrough: 9-Choice Cold-Start, 2&times;2 Split &amp; 17m ML/CQR</h2>

<p>Earlier drafts concluded that ML and conformal models failed because initial models suffered from <strong>5-month off-season training starvation</strong> (<code>Ridge</code>, <code>HGBR_RiskAverse</code>, and unnormalized <code>OR_Vargas_MeanVar_g0002</code> at <code>cond_ES10 &minus;&#8377;511.42</code>) and a <strong>homoscedastic Split-CQR bug (0 switches)</strong>. Once fixed in Revision v8: (a) heteroscedastic Split-CQR re-ranks destinations (<strong>8,848 switches</strong> in 5m: <code>MG_T1..T4_Intact_matched</code> 66.32%, Mean &#8377;356.78, ES10 &minus;&#8377;323.41, <code>cond_ES10 &minus;&#8377;414.44</code>; <strong>8,115 switches</strong> in 17m: <code>ML_17m_CQR80_valmatch</code> 57.30%, Mean &#8377;364.03, <code>cond_ES10 &minus;&#8377;367.09</code>); and (b) full-season <strong>17m GBDTs</strong> (<code>n_train_17m = 113,374</code>) reach <strong>Mean &#8377;455.83, ES10 &minus;&#8377;320.02, <code>cond_ES10 &minus;&#8377;420.57</code></strong> (<code>ML_17m_MeanQ10_Hybrid_eq63</code>; ablating <code>safe_ev_feat</code> in <code>NoSafeEV_eq63</code> hits <strong>&#8377;458.27 / &minus;&#8377;423.88</strong> autonomously!), while <code>OR_Stylized_MeanSD_17m_valmatch</code> hits &#8377;443.57 / &minus;&#8377;439.77. <strong>Why keep the 9-choice calculator rule?</strong> With <strong>zero tuned weights and zero training data (<code>n_train = 0</code>)</strong>, <code>Safe_EV_Sunk_m0</code> captures <strong>~98.8% of <code>MeanQ10</code> Mean and ~94% of <code>cond_ES10</code> tail protection</strong> on day 1!</p>

<div class="formula-card">
  <h3 style="margin-top:0;">Rule 1: Safe_EV_Sunk_m0 (9 Fixed Choices, 0 Tuned Weights) &amp; 2&times;2 Orthogonal Decomposition</h3>
  <div class="formula-big">p<sub>dow</sub> &middot; G<sub>1SD</sub> &minus; F<sub>road</sub> &nbsp;&equiv;&nbsp; p<sub>dow</sub>(G<sub>1SD</sub> &minus; F<sub>road</sub>) + (1 &minus; p<sub>dow</sub>)(&minus;1.0 F<sub>road</sub>) &nbsp;&gt;&nbsp; 0</div>
  <p style="margin-bottom:3px;"><strong>Plain English + Exact Identity:</strong> <em>G<sub>1SD</sub></em> subtracts 1-SD recent swing (<code>cv<sub>28</sub></code>) and stylized fee from yesterday's price; <em>p<sub>dow</sub></em> is 8-week same-weekday reliability. The identity proves it prices <code>&minus;1.0 F</code> sunk freight on silent days (<code>Safe_EV_Phys_m0</code> uses <code>&minus;1.5 F</code>). <strong>2&times;2 Orthogonal Split:</strong> <code>Ortho_Pure_cv28_only</code> (71.91% disp, Mean &#8377;421.62, ES10 &minus;&#8377;387.46, <strong><code>cond_ES10 &minus;&#8377;447.13</code></strong>) drives ~100% of tail truncation, whereas <code>Ortho_Pure_pdow_only</code> (84.10% disp, <strong>Mean &#8377;466.68</strong>, <code>cond_ES10 &minus;&#8377;607.18</code>) drives diversion avoidance and Mean lift!</p>
  <p style="margin-bottom:0; font-size:8.4pt; color:#475569;"><strong>HP Scale Non-Invariance Fix (<code>ScaleInv_Safe_EV_24tau</code>):</strong> When <code>F/G<sub>1SD</sub> &lt; 0.10</code> (79.52% of HP apple trips), omitting proportional spoilage breaks <code>p<sub>dow</sub></code>. Adding <code>24&tau;</code> spoilage + <code>1.5F</code> cuts HP apple <code>ep_loss</code> from <code>27.91% &rarr; 17.92%</code> (<code>ES10 &minus;&#8377;958.08</code>, <code>cond_ES10 &minus;&#8377;1,616.08</code> vs <code>&minus;&#8377;2,003.68</code>; <code>Safe_EV_Sunk_pFloor50</code> hits <code>15.17%</code>).</p>
</div>

<div class="formula-card">
  <h3 style="margin-top:0;">Rule 2: RT_2F_Min_m0 (Class-8 4-Function Phone Calculator &mdash; Omits Volatility cv<sub>28</sub>)</h3>
  <div class="formula-big">p<sub>min</sub> &times; G &nbsp;&gt;&nbsp; 2 &times; F<sub>road</sub> &nbsp;&nbsp;&nbsp;&nbsp;(equivalently: &nbsp; G / (2 F<sub>road</sub>) &nbsp;&gt;&nbsp; 1 / p<sub>min</sub>)</div>
  <p style="margin-bottom:0;"><strong>Plain English:</strong> Uses plain fee-adjusted spread <strong>G</strong> and stricter reliability <strong>p<sub>min</sub> = min(rep<sub>28</sub>, p<sub>dow</sub>)</strong> against round-trip freight <strong>2F</strong>. Because it omits <code>cv<sub>28</sub></code>, it keeps high Mean (&#8377;463.98) yet misses conditional tail truncation (<code>cond_ES10 &minus;&#8377;618.35</code>) and fails under <code>&le; t&minus;2</code> latency (<code>p = 0.981</code>).</p>
</div>

<div class="green-box">
  <h3 style="margin-top:0;">10-Second Phone Calculator Example (Real Numbers!)</h3>
  <p><strong>Route:</strong> 200 km MP Tomato trip. Local = <strong>&#8377;1,500</strong>, dest = <strong>&#8377;2,000</strong>, fee = <strong>1.5%</strong>, freight <strong>F = 35 + 0.45 &times; 200 = &#8377;125</strong>, swing <strong>cv<sub>28</sub> = 15%</strong> &rarr; <strong>G = +&#8377;470/qtl</strong>, <strong>G<sub>1SD</sub> = +&#8377;174.50/qtl</strong>.</p>
  <ul style="margin-bottom:0;">
    <li><strong>Case A &mdash; Reliable Weekday Mandi (<code>p<sub>dow</sub> = 0.90, p<sub>min</sub> = 0.85</code>):</strong> Safe_EV: <code>0.90(174.50&minus;125)+0.10(&minus;125) = +&#8377;32.05 &gt; 0</code> &rarr; <strong>DISPATCH!</strong> | RT_2F: <code>0.85 &times; 470 = &#8377;399.50 &gt; &#8377;250</code> &rarr; <strong>DISPATCH!</strong></li>
    <li><strong>Case B &mdash; Sunday-Closed Mandi (<code>p<sub>dow</sub> = 0.20, p<sub>min</sub> = 0.20</code>):</strong> Road baseline <code>B2</code> sees <code>470 &minus; 125 = +&#8377;345</code> and goes blindly! Safe_EV gives <code>0.20 &times; 174.50 &minus; 125 = &minus;&#8377;90.10</code>; RT_2F gives <code>0.20 &times; 470 &minus; 250 = &minus;&#8377;156.00</code> &rarr; <strong>STAY HOME!</strong></li>
  </ul>
</div>

<h2>4. What the Data Proves: 171 Mkts, 17m ML Frontier &amp; Clean 166-Mkt Backtest</h2>

<p>Our primary benchmark uses strictly <strong>2024-selected 171 markets</strong> (<code>N = 57,634</code> test episodes, June 2025&ndash;April 2026) under <strong>specification-locked exploratory inference</strong> (<code>PREREG_A18</code>, <code>R = 2,000</code>, <code>p<sub>holm,2s</sub> = 0.0040</code>; finite-sample CGM <code>p<sub>cgm,gstar</sub> = 0.00511 / 0.01001</code> for <code>H_A18_1</code> and <code>0.04887 / 0.06800</code> for <code>H_A18_2</code>; 1-way <code>p<sub>wild,webb6,1w</sub> = 0.0005</code>). We then run frozen cold-start rules on clean <strong>166 markets (2018&ndash;2023, N = 383,952; reverse-survivorship 481/647 excluded)</strong> and head-to-head against <code>17m</code> ML/CQR (<code>n<sub>train</sub> = 113,374</code>):</p>

<table class="res-table">
  <colgroup>
    <col style="width:33%;"/>
    <col style="width:8%;"/>
    <col style="width:20%;"/>
    <col style="width:20%;"/>
    <col style="width:19%;"/>
  </colgroup>
  <thead>
    <tr>
      <th>Decision Rule / Model</th>
      <th class="num">Disp%</th>
      <th class="num">Primary 171 Mkts (57.6k)<br/>Mean | Loss% &bull; ES10</th>
      <th class="num">Cond. Tail (171) / Note<br/>cond_ES10 &bull; Key Spec</th>
      <th class="num">Clean 166 (2018&ndash;23)<br/>Mean | ES10 &bull; cond_ES10</th>
    </tr>
  </thead>
  <tbody>
    <tr><td><strong>B1_lagged_screen</strong> (top spread &gt; &#8377;100)</td><td class="num">100.0%</td><td class="num">&#8377;384.61 | 45.07%<br/><span class="es-tag">ES10 &minus;&#8377;642.15</span></td><td class="num"><span class="es-tag">cond_ES10 &minus;&#8377;642.15</span><br/>28.67% sequential turn-backs</td><td class="num">&#8377;288.85 | &minus;&#8377;555.94<br/>cond &minus;&#8377;555.94</td></tr>
    <tr><td><strong>B2_age_matched</strong> (road+fee &gt; &#8377;200, 1&ndash;3d)</td><td class="num">71.73%</td><td class="num">&#8377;419.62 | 26.43%<br/><span class="es-tag">ES10 &minus;&#8377;524.78</span></td><td class="num"><span class="es-tag">cond_ES10 &minus;&#8377;628.37</span><br/>Road-adjusted comparator</td><td class="num">&#8377;321.57 | &minus;&#8377;473.56<br/>cond &minus;&#8377;576.44</td></tr>
    <tr><td><strong>Ortho_Pure_cv28_only</strong> (p<sub>dow</sub>=1, 2&times;2)</td><td class="num">71.91%</td><td class="num">&#8377;421.62 | 24.10%<br/><span class="es-tag">ES10 &minus;&#8377;387.46</span></td><td class="num"><span class="es-tag">cond_ES10 &minus;&#8377;447.13</span><br/>~100% of tail truncation</td><td class="num"><em>(2&times;2 ablation;<br/>171-mkt diag.)</em></td></tr>
    <tr><td><strong>Ortho_Pure_pdow_only</strong> (cv<sub>28</sub>=0, 2&times;2)</td><td class="num">84.10%</td><td class="num">&#8377;466.68 | 24.63%<br/><span class="es-tag">ES10 &minus;&#8377;546.75</span></td><td class="num"><span class="es-tag">cond_ES10 &minus;&#8377;607.18</span><br/>Diversion avoidance &amp; Mean</td><td class="num"><em>(2&times;2 ablation;<br/>171-mkt diag.)</em></td></tr>
    <tr class="hl"><td><strong>Safe_EV_Sunk_m0</strong> (9 choices, n<sub>train</sub>=0)</td><td class="num">63.23%</td><td class="num">&#8377;452.74 | 14.88%<br/><span class="es-tag">ES10 &minus;&#8377;345.53</span></td><td class="num"><span class="es-tag">cond_ES10 &minus;&#8377;447.48</span><br/>~98.8% of 17m MeanQ10 Mean</td><td class="num">&#8377;356.57 | &minus;&#8377;304.29<br/>cond &minus;&#8377;421.35</td></tr>
    <tr class="hl"><td><strong>Safe_EV_Phys_m0</strong> (1.5F, n<sub>train</sub>=0)</td><td class="num">60.84%</td><td class="num">&#8377;449.52 | 13.70%<br/><span class="es-tag">ES10 &minus;&#8377;334.80</span></td><td class="num"><span class="es-tag">cond_ES10 &minus;&#8377;447.33</span><br/>+&#8377;0.15 cond vs Sunk</td><td class="num">&#8377;353.33 | &minus;&#8377;288.47<br/>cond &minus;&#8377;417.71</td></tr>
    <tr><td><strong>RT_2F_Min_m0</strong> (Class-8, NO cv<sub>28</sub>)</td><td class="num">64.79%</td><td class="num">&#8377;463.98 | 16.21%<br/><span class="es-tag">ES10 &minus;&#8377;464.84</span></td><td class="num"><span class="es-tag">cond_ES10 &minus;&#8377;618.35</span><br/>Fails t&minus;2 lag (p=0.981)</td><td class="num">&#8377;370.86 | &minus;&#8377;395.63<br/>cond &minus;&#8377;553.64</td></tr>
    <tr><td><strong>MG_T1..T4_Intact_matched</strong> (5m CQR)</td><td class="num">66.32%</td><td class="num">&#8377;356.78 | 14.94%<br/><span class="es-tag">ES10 &minus;&#8377;323.41</span></td><td class="num"><span class="es-tag">cond_ES10 &minus;&#8377;414.44</span><br/>8,848 dest switches (IQR)</td><td class="num"><em>(5m CQR;<br/>171-mkt)</em></td></tr>
    <tr><td><strong>ML_17m_CQR80_valmatch</strong> (17m CQR)</td><td class="num">57.30%</td><td class="num">&#8377;364.03 | 12.85%<br/><span class="es-tag">ES10 &minus;&#8377;261.29</span></td><td class="num"><span class="es-tag">cond_ES10 &minus;&#8377;367.09</span><br/>8,115 switches (n=113,374)</td><td class="num"><em>(17m CQR;<br/>171-mkt)</em></td></tr>
    <tr class="hl"><td><strong>ML_17m_MeanQ10_Hybrid_eq63</strong> (17m)</td><td class="num">63.23%</td><td class="num">&#8377;455.83 | 14.94%<br/><span class="es-tag">ES10 &minus;&#8377;320.02</span></td><td class="num"><span class="es-tag">cond_ES10 &minus;&#8377;420.57</span><br/>NoSafeEV: &#8377;458.27 / &minus;&#8377;423.88</td><td class="num"><em>(17m GBDT;<br/>n=113,374)</em></td></tr>
    <tr><td><strong>OR_Stylized_MeanSD_17m_valmatch</strong></td><td class="num">61.40%</td><td class="num">&#8377;443.57 | 13.06%<br/><span class="es-tag">ES10 &minus;&#8377;324.93</span></td><td class="num"><span class="es-tag">cond_ES10 &minus;&#8377;439.77</span><br/>EV &minus; 0.35&middot;IQR (vs Vargas &minus;&#8377;511.42)</td><td class="num"><em>(17m OR;<br/>171-mkt)</em></td></tr>
  </tbody>
</table>

<p style="font-size:8.2pt; color:#475569;"><strong>Key verified takeaways:</strong> On clean <code>166</code>-mkt <code>2018&ndash;2023</code> (<code>N = 383,952</code>, reverse-survivorship 481/647 excluded), <code>Safe_EV_Sunk_m0</code> wins <code>ES10</code> (+&#8377;169.27) and <code>cond_ES10</code> (+&#8377;155.08; +&#8377;174.27 vs equal-dispatch <code>B2_eq_SafeM0</code>) in <strong>6/6 years</strong> (<code>p = 0.001</code>; <code>2020/2023</code> Means NS). On <code>171</code>-mkt, it holds under <code>&le; t&minus;2</code> lag (<code>p=0.001</code>), repaired <code>S6_Frozen</code> (<code>&#8377;307.39 / &minus;&#8377;576.57 / &minus;&#8377;725.73</code>; <code>Stoch_CondMAR_p1.00 +&#8377;366.85 cond_ES10</code>), exact coupled Manski <code>cond_ES10</code> (<code>Supp1 +&#8377;152.20</code>, <code>Supp2 +&#8377;105.96</code>), and non-collided exact geocodes (<code>N=6,605</code>: Mean &#8377;194.97 vs &#8377;200.37, <code>ES10 &minus;&#8377;231.27</code> vs <code>&minus;&#8377;449.14</code>, <code>p=0.001</code>).</p>

<figure>
  <img src="{img_uri('rev_fig1_risk_coverage_ci.png')}" alt="Risk Coverage Curves"/>
  <figcaption><strong>Visual Proof 1 (Risk vs Coverage):</strong> 9-choice zero-tuned-weight <code>Safe_EV_Sunk_m0</code> cuts losses and lifts worst-10% shortfall <code>ES10</code> far above <code>B2</code> and hard gates across 57,634 episodes, capturing ~98.8% of 17m <code>MeanQ10</code> Mean and ~94% of <code>cond_ES10</code> tail protection at <code>n_train = 0</code>.</figcaption>
</figure>

<figure>
  <img src="{img_uri('rev_fig4_settlement_and_hp_apple.png')}" alt="Untouched 2018-2023 Backtest and HP Apples"/>
  <figcaption><strong>Visual Proof 2 (Six Historical Years &amp; HP Graded Apples):</strong> Left: 166 clean markets over 2018&ndash;2023 (reverse-survivorship 481/647 excluded) preserve <code>ES10</code> in 6/6 years. Right: On HP apples (<code>N = 2,802</code>), <code>F/G<sub>1SD</sub> &lt; 0.10</code> on 79.52% breaks <code>cond_ES10</code> (<code>p = 0.094</code> NS, 41.38% cond loss); <code>ScaleInv_Safe_EV_24tau</code> cuts <code>ep_loss</code> 27.91% &rarr; 17.92% (<code>ES10 &minus;&#8377;958.08</code>, <code>cond_ES10 &minus;&#8377;1,616.08</code>).</figcaption>
</figure>

<h2>5. The 10 Most Relevant Research Papers (Your Literature Map in Plain English)</h2>

<p>Your thesis connects <strong>four classic research areas</strong>. Memorize these <strong>10 foundational literature anchors</strong> &mdash; each is explained in two plain-English sentences so you can cite them naturally in any viva or review response:</p>

<span class="pillar-badge">PILLAR 1 &bull; Agricultural Spatial Arbitrage &amp; Why Price Portals Alone Fail</span>
<table>
  <thead><tr><th style="width:22%;">Paper &amp; Venue</th><th style="width:42%;">Core Idea in Plain English</th><th style="width:36%;">How MandiGuard Connects / Differs</th></tr></thead>
  <tbody>
    <tr>
      <td><strong>1. Baulch (1997)</strong><br/><em>Am. J. Agric. Econ. (AJAE)</em></td>
      <td>Introduced the <em>Parity Bounds Model</em>: two markets are only profitably connected if their price gap exceeds real transfer costs (freight + fees + risk).</td>
      <td>Our economic foundation &mdash; we translate parity bounds from ex-post macro tests into an ex-ante 6 a.m. truck dispatch filter.</td>
    </tr>
    <tr>
      <td><strong>2. Jensen (2007)</strong><br/><em>Quarterly J. Economics (QJE)</em></td>
      <td>Classic Kerala fishermen study: mobile phones let fishermen call coastal markets in real time, eliminating waste and raising profits dramatically.</td>
      <td>Explains why <strong>live phone calls</strong> (<code>PhoneCall_TopK_Open</code>) remain vital &mdash; MandiGuard prioritizes alerts <em>before</em> dialing <em>arhtiyas</em>.</td>
    </tr>
    <tr>
      <td><strong>3. Fafchamps &amp; Minten (2012)</strong><br/><em>World Bank Econ. Rev.</em></td>
      <td>Large field RCT in Maharashtra sending daily SMS mandi prices to farmers found <strong>almost zero average income gain</strong> because transport and execution frictions blocked arbitrage.</td>
      <td>Directly proves why raw AGMARKNET screens mislead (our 45.07% naive loss rate) &mdash; raw prices need reliability and volatility filtering.</td>
    </tr>
    <tr>
      <td><strong>4. Mitra et al. (2018)</strong><br/><em>Rev. Econ. &amp; Statistics</em></td>
      <td>Field experiment with West Bengal potato farmers showing middlemen, transport barriers, and asymmetric information absorb raw price spreads.</td>
      <td>Reinforces why we stress-test <code>Outsider_Mid/MinPrice_LCV_4pctArh</code> (compressing Mean to &#8377;102.62) and never claim modeled cash receipts.</td>
    </tr>
    <tr>
      <td><strong>5. Levi et al. (2020; 2025)</strong><br/><em>PNAS &amp; Manuf. Serv. Oper. Manag. (MSOM)</em></td>
      <td>Evaluated Karnataka's Unified Market Platform (e-auctions), showing digital platforms raise realized farmer prices when auction execution is reliable and transparent.</td>
      <td>Shows the institutional complement: reliable execution platforms solve the arrival uncertainty our filter guards against today.</td>
    </tr>
  </tbody>
</table>

<span class="pillar-badge">PILLAR 2 &bull; Indian Mandi Forecasting, Missing Data &amp; Farmer Workflows</span>
<table>
  <thead><tr><th style="width:22%;">Paper &amp; Venue</th><th style="width:42%;">Core Idea in Plain English</th><th style="width:36%;">How MandiGuard Connects / Differs</th></tr></thead>
  <tbody>
    <tr>
      <td><strong>6. Madaan et al. (2019)</strong> &amp; <strong>Ma et al. (2019)</strong><br/><em>ACM COMPASS &amp; ICTD</em></td>
      <td>Built time-series and matrix-completion ML models on AGMARKNET to forecast prices and fill in missing daily quotes, optimizing RMSE (average prediction error).</td>
      <td><strong>Key Research Gap:</strong> Predicting prices accurately does not protect against a truck arriving at a blank yard or losing big on volatile days.</td>
    </tr>
    <tr>
      <td><strong>7. Ziegler et al. (2019)</strong><br/><em>ACM ICTD</em></td>
      <td>Field user study with Indian vegetable farmers showing market tools only get adopted if they are ultra-simple and fit morning trader-calling habits.</td>
      <td>Motivates our 9-choice cold-start calculator (<code>Safe_EV_Sunk_m0</code>) that captures ~98.8% of 17m ML Mean with zero training history.</td>
    </tr>
  </tbody>
</table>

<span class="pillar-badge">PILLAR 3 &bull; Decision-Focused Learning, Heuristics &amp; Risk-Aware Abstention</span>
<table>
  <thead><tr><th style="width:22%;">Paper &amp; Venue</th><th style="width:42%;">Core Idea in Plain English</th><th style="width:36%;">How MandiGuard Connects / Differs</th></tr></thead>
  <tbody>
    <tr>
      <td><strong>8. Chow (1970)</strong> &amp; <strong>El-Yaniv &amp; Wiener (2010)</strong><br/><em>IEEE TIT &amp; JMLR</em></td>
      <td>Founded <em>selective prediction (reject option)</em>: when mistakes are far costlier than staying silent, abstaining cuts catastrophic risk dramatically.</td>
      <td>Theoretical root of staying home at &#8377;0; <code>CommonIntersection_DS_cap_DB</code> proves we also add +&#8377;65.66 Mean / +&#8377;53.40 ES10 routing lift.</td>
    </tr>
    <tr>
      <td><strong>9. Elmachtoub &amp; Grigas (2022)</strong> &amp; <strong>Mandi et al. (2024)</strong><br/><em>Manage. Sci. &amp; JAIR 80</em></td>
      <td>Introduced Smart "Predict, Then Optimize" (SPO) and surveyed Decision-Focused Learning (DFL) benchmarks across 80+ combinatorial settings (<code>mandi2024dfl</code>).</td>
      <td>Frames our 17m <code>Mean-Q10</code> GBDT frontier (autonomously reaching &#8377;458.27 / &minus;&#8377;423.88 without <code>safe_ev_feat</code>) alongside 0-data <code>Safe_EV_Sunk_m0</code> (<code>DeMiguel 2009</code>; <code>Vargas 2026</code> Mean-SD &#8377;443.57 / &minus;&#8377;439.77).</td>
    </tr>
  </tbody>
</table>

<span class="pillar-badge">PILLAR 4 &bull; Missing-Data Bounds &amp; Worst-Case Tail Risk (ES10)</span>
<table>
  <thead><tr><th style="width:22%;">Paper &amp; Venue</th><th style="width:42%;">Core Idea in Plain English</th><th style="width:36%;">How MandiGuard Connects / Differs</th></tr></thead>
  <tbody>
    <tr>
      <td><strong>10. Manski (1990)</strong> &amp; <strong>Rockafellar &amp; Uryasev (2000)</strong><br/><em>AER &amp; Journal of Risk</em></td>
      <td>Manski introduced <em>nonparametric bounds</em> under non-ignorable missingness; Rockafellar &amp; Uryasev formalized coherent <em>Expected Shortfall / CVaR</em> (worst 10% average).</td>
      <td>Anchors exact fractional <code>ES10</code>/<code>cond_ES10</code>, 25.45% Open-MAR break-even, and exact coupled Manski <code>cond_ES10</code> (<code>Supp1 +&#8377;152.20</code>, <code>Supp2 +&#8377;105.96</code>).</td>
    </tr>
  </tbody>
</table>

<h2>6. Radical Honesty: Every Negative Result &amp; Boundary You MUST Know</h2>

<div class="warn-box">
  <h3 style="margin-top:0;">Why Knowing Your Own Weaknesses Wins Every Viva &amp; Review</h3>
  <p style="margin-bottom:4px;">Examiners love catching students hiding negative results &mdash; and immediately respect students who state exact failure boundaries clearly. Memorize these <strong>five honest disclosures</strong>:</p>
  <ol style="margin-bottom:0;">
    <li><strong>Missing-Quote Bounds (Open-MAR Reversal &amp; Coupled Manski <code>cond_ES10</code>):</strong> Under 100% Open-MAR, road baseline <code>B2</code> earns <strong>+&#8377;97.01/qtl higher Mean</strong> (&#8377;698.17 vs &#8377;601.16; break-even <strong>25.45%</strong> or <strong>+&#8377;348.61/qtl</strong>; 26.65% ERA5), while coupled Manski <code>cond_ES10</code> remains positive on <code>Supp1</code> (+&#8377;152.20) and <code>Supp2</code> (+&#8377;105.96).</li>
    <li><strong>When Mean Gains Vanish (Free Turn-Back &amp; Hindsight):</strong> Under free return (<code>div = 0</code>), Mean (+&#8377;12.03 / +&#8377;11.21, <code>p = 0.22&ndash;0.26</code>) is NS while <code>ES10</code> keeps +&#8377;174.40 / +&#8377;169.82. Under 3-day hindsight, <code>B2</code> leads Mean (&#8377;549.81 vs &#8377;533.14), while <code>Safe_EV</code> cuts <code>ES10</code> (&minus;&#8377;279.93 vs &minus;&#8377;588.34).</li>
    <li><strong>Subgroup, UP Atom &amp; Reverse-Survivorship Limits:</strong> HP (<code>B = 12</code>) fails <code>cond_ES10</code> (<code>p = 0.1239</code>) and studentized checks (<code>p = 0.1879</code>, <code>p<sub>cgm,gstar</sub> = 0.2995</code>); Apple is borderline (<code>cond_ES10 p = 0.0550</code>); UP has an <strong>unconditional <code>q10 = 0</code> atom</strong> (7.28% &lt; 10% loss rate); Potato trails <code>RR</code> by &minus;&#8377;17.20; 166-mkt 2018&ndash;2023 is reverse-survivorship conditioned on 2024 (<strong>481/647 excluded</strong>; <code>2020/2023</code> Means NS); and 56/171 legacy geocodes collide (35.23% exact coverage, <code>N=6,605 p=0.001</code>).</li>
    <li><strong>HP Scale Non-Invariance &amp; Honest 17m ML Frontier:</strong> On HP apples (<code>N = 2,802</code>), <code>F/G<sub>1SD</sub> &lt; 0.10</code> on 79.52% breaks <code>p<sub>dow</sub></code> (41.38% cond loss, <code>cond_ES10 p = 0.0940</code> NS); <code>ScaleInv_Safe_EV_24tau</code> cuts <code>ep_loss</code> 27.91% &rarr; 17.92% (<code>cond_ES10 &minus;&#8377;1,616.08</code>; <code>pFloor50</code> 15.17%). On full 17m (<code>n<sub>train</sub> = 113,374</code>), <code>MeanQ10</code> reaches &#8377;455.83 / &minus;&#8377;420.57 (<code>NoSafeEV</code> &#8377;458.27 / &minus;&#8377;423.88) and Split-CQR hits <code>cond_ES10 &minus;&#8377;367.09</code> (8,115 switches), though zero formal conformal coverage guarantees are claimed.</li>
    <li><strong>Outsider Bargaining, SUTVA Crowding &amp; Blocked Gate J:</strong> <code>Outsider_MinPrice_LCV_4pctArh</code> compresses Safe_EV Mean to &#8377;102.62 (34.29% loss), SUTVA 10% crowding drops Mean to &minus;&#8377;5.31 (needs <code>k &le; 2</code> coordination), and prospective field validation (<code>Gate J</code>) remains open.</li>
  </ol>
</div>

<h2>7. Quick Viva Survival Guide: 6 Toughest Examiner Questions &amp; 15-Second Answers</h2>

<div class="qa-item">
  <div class="qa-q">Q1: "How does your 9-choice calculator rule compare against properly trained ML and Split-CQR?"</div>
  <div><strong>Answer:</strong> "Earlier 5m off-season starvation and homoscedastic CQR (0 switches) masked ML's potential. Trained on 17 full seasonal months (<code>n_train = 113,374</code>), <code>ML_17m_MeanQ10_Hybrid_eq63</code> hits &#8377;455.83 / <code>cond_ES10 &minus;&#8377;420.57</code> (<code>NoSafeEV</code> hits &#8377;458.27 / &minus;&#8377;423.88 autonomously) and heteroscedastic Split-CQR reaches <code>cond_ES10 &minus;&#8377;367.09</code> (8,115 switches). Yet <code>Safe_EV_Sunk_m0</code> (<code>n_train = 0</code>) captures ~98.8% of that Mean and ~94% of conditional tail protection with zero historical training data and pocket-calculator transparency."</div>
</div>

<div class="qa-item">
  <div class="qa-q">Q2: "Isn't this post-hoc to 2025&ndash;2026, and how do small clusters (<code>B=12</code>) and <code>2018&ndash;2023</code> hold up?"</div>
  <div><strong>Answer:</strong> "We label 2025&ndash;2026 explicitly as <strong>specification-locked exploratory inference</strong> (<code>PREREG_A18</code> <code>p<sub>holm,2s</sub> = 0.0040</code>; CGM <code>p<sub>cgm,gstar</sub> = 0.00511 / 0.01001</code> for <code>H_A18_1</code>, <code>0.04887 / 0.06800</code> for <code>H_A18_2</code>; 1-way <code>p<sub>wild,webb6,1w</sub> = 0.0005</code>), and disclose HP <code>B=12</code> non-significance and UP's unconditional <code>q10=0</code> atom. Frozen rules also transfer to clean 166 markets over 2018&ndash;2023 (<code>N = 383,952</code>, 6/6 yrs <code>ES10</code> &amp; <code>cond_ES10</code>, <code>2020/2023</code> Means NS), conditioned transparently on 2024 corridor inclusion (481/647 excluded)."</div>
</div>

<div class="qa-item">
  <div class="qa-q">Q3: "What drives Safe_EV's gain &mdash; volatility, reliability, routing, or just abstaining? What about trader calls?"</div>
  <div><strong>Answer:</strong> "Our 2&times;2 orthogonal decomposition proves <code>Ortho_Pure_cv28_only</code> (<code>cond_ES10 &minus;&#8377;447.13</code>) supplies ~100% of tail truncation while <code>Ortho_Pure_pdow_only</code> (Mean &#8377;466.68, <code>&minus;&#8377;607.18</code>) supplies diversion avoidance and Mean lift. Inside shared dispatches (<code>CommonIntersection_DS_cap_DB</code>, <code>n = 33,398</code>), Safe_EV also adds +&#8377;65.66 Mean and +&#8377;53.40 ES10 purely from better routing. Before loading, <code>PhoneCall_TopK_Open</code> still cuts losses to 4.99% (<code>cond_ES10 &minus;&#8377;355.07</code> vs B2 &minus;&#8377;691.79)."</div>
</div>

<div class="qa-item">
  <div class="qa-q">Q4: "What if blank AGMARKNET rows were open yards, or return legs suffer full heat decay?"</div>
  <div><strong>Answer:</strong> "B2 only passes Safe_EV on Mean if &ge; 25.45% of silent yards clear at full lagged prices (Open-MAR gives B2 +&#8377;97.01/qtl Mean), yet exact coupled Manski <code>cond_ES10</code> stays positive through <code>Supp1</code> (+&#8377;152.20) and <code>Supp2</code> (+&#8377;105.96). Under repaired <code>_spoil_return_leg</code> <code>S6</code> (full <code>24&tau;+hrs+24w</code> + ERA5), Safe_EV earns &#8377;307.39 / &minus;&#8377;576.57 / &minus;&#8377;725.73, and keeps +&#8377;366.85 <code>cond_ES10</code> under <code>Stoch_CondMAR_p1.00</code>."</div>
</div>

<div class="qa-item">
  <div class="qa-q">Q5: "What breaks on Himachal graded apples and real-world geocodes / outsider pricing?"</div>
  <div><strong>Answer:</strong> "On HP apples (<code>N=2,802</code>), <code>F/G<sub>1SD</sub> &lt; 0.10</code> on 79.52% breaks the <code>p<sub>dow</sub></code> screen (scale non-invariance); <code>ScaleInv_Safe_EV_24tau</code> solves this by cutting <code>ep_loss</code> 27.91% &rarr; 17.92% (<code>cond_ES10 &minus;&#8377;1,616.08</code>). On geocodes, 56/171 markets collided, leaving 35.23% exact coverage (<code>N=6,605</code> still passes <code>ES10 p=0.001</code>). On <code>Outsider_MinPrice_LCV_4pctArh</code>, Safe_EV Mean drops to &#8377;102.62 (vs B2 &#8377;33.86)."</div>
</div>

<div class="qa-item">
  <div class="qa-q">Q6: "What is your single next step to turn this into a top-tier journal paper?"</div>
  <div><strong>Answer:</strong> "A one-season FPO field pilot logging 200&ndash;500 real 6 a.m. <em>arhtiya</em> confirmation calls, truck bills, and auction <em>patti</em> slips &mdash; directly measuring the true silent-open rate against our 25.45% break-even threshold while rebuilding corridors with our repaired sub-yard-first geocoder (<code>Gate J</code>)."</div>
</div>

<div class="footer-note">
  <strong>MandiGuard Revision v8 Concept &amp; Literature Guide</strong> &bull; Aditya Sharma (M.Tech Thesis Research, supervised by Dr. Sonia) &mdash; Shoolini University &bull; Verified from <code>revision/results/v7_*.csv</code> (171-mkt N = 57,634; 17m n = 113,374; 166-mkt 2018&ndash;2023 N = 383,952; exploratory PREREG_A18 R = 2,000 + CGM G*; 59 verified citations).
</div>
"""


def main() -> None:
    doc = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>'
        "<title>MandiGuard — Ultra-Simplified Concept &amp; Top 10 Research Papers Guide (Revision v8)</title>"
        f"<style>{CSS}</style></head><body>{HTML_BODY}</body></html>"
    )
    HTML_OUT.write_text(doc, encoding="utf-8")
    render_pdf(HTML_OUT, PDF_OUT)

    reader = PdfReader(str(PDF_OUT))
    txt = "\n".join((p.extract_text() or "") for p in reader.pages)
    assert len(reader.pages) <= 8, f"Expected compact <= 8 pages, got {len(reader.pages)}"
    raw_macros = sorted(set(re.findall(r"\\[a-zA-Z]{2,}", txt)))
    assert raw_macros == [], f"Raw LaTeX macros leaked: {raw_macros}"
    for bad in (
        "TO CONFIRM", "exploratory: true", "make reproduce", "[jensen2007digital]",
        "525.17", "530.30", "512.43", "496.76", "444.86", "266.43",
        "Locked confirmatory", "zero-parameter beats", "propensity", "/" + "Users/",
    ):
        assert bad not in txt, f"Forbidden token `{bad}` found in {PDF_OUT.name}"
    print(f"Wrote {HTML_OUT.name} & {PDF_OUT.name} ({len(reader.pages)} pages, clean)")


if __name__ == "__main__":
    main()
