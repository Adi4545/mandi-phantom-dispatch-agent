#!/usr/bin/env python3
"""Build the Ultra-Simplified Concept & Most Relevant Research Papers PDF (Revision v7).

Designed for effortless, first-principles understanding and confident oral viva defense.
Grounded 100% in verified Revision v7 outputs (primary 2024-only 171-market panel N = 57,634,
locked PREREG_A18 4-test R = 2,000 inference, and clean 166-market 2018-2023 N = 383,952 backtest).
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
  <span class="tag">Ultra-Simplified Visual Concept &amp; Literature Guide &bull; Revision v7</span>
  <h1>MandiGuard Explained Simply:<br/>The Full Concept, Simple Math &amp; Top 10 Research Papers</h1>
  <p>Everything you need to understand the entire research idea in 10 minutes and defend it calmly in front of any thesis examiner or journal reviewer &mdash; zero jargon, zero black-box ML, 100% real verified numbers.</p>
</div>

<div class="story-box">
  <h3 style="margin-top:0;">The Entire Thesis in One Real-Life Story (30 Seconds)</h3>
  <p>Imagine you manage a tomato farmer cooperative (FPO) in Madhya Pradesh. It is <strong>6:00 a.m.</strong> You open the government's <strong>AGMARKNET</strong> website on your phone. Your local mandi paid <strong>&#8377;1,500 per quintal</strong> yesterday, while another mandi 200 km away listed <strong>&#8377;2,000 per quintal</strong> yesterday.</p>
  <p style="margin-bottom:0;">That looks like an easy <strong>+&#8377;500/qtl profit</strong>! So you load a truck and send it. <strong>What goes wrong?</strong> When the truck arrives, three real-world traps hit: (1) truck freight, yard fees, and heat decay eat into the spread; (2) yesterday's &#8377;2,000 spike crashes back down in a volatile market; or (3) worst of all, the destination mandi has <strong>no auction running for your crop that day</strong> (a "silent/blank" arrival board), forcing an expensive turn-back. Our study proves that chasing tempting online spreads loses money nearly <strong>half the time (45.1%)</strong> &mdash; and discovers <strong>two zero-tuned-parameter pocket-calculator rules</strong> that filter out trap alerts at 6 a.m. <em>before</em> you even call the destination trader on the phone.</p>
</div>

<div class="kpi-row">
  <div class="kpi"><div class="val">45.07%</div><div class="lbl">Loss rate when blindly chasing top portal spreads</div></div>
  <div class="kpi"><div class="val">0 Params</div><div class="lbl">No ML trees, no tuning, no live weather needed</div></div>
  <div class="kpi"><div class="val">+&#8377;179.24</div><div class="lbl">Worst-10% (ES10) gain on 171-mkt primary panel</div></div>
  <div class="kpi"><div class="val">6 / 6 Years</div><div class="lbl">ES10 &amp; cond_ES10 gains across 166 mkts (2018&ndash;2023, N=384k)</div></div>
</div>

<h2>1. The Big Picture: How the Whole System Works (5 Simple Steps)</h2>

<div class="flow">
  <div class="fstep c-blue"><strong>Step 1: 6 a.m. Screen</strong>Check yesterday's prices only (never today's price &mdash; zero peeking!)</div>
  <div class="farrow">&rarr;</div>
  <div class="fstep c-amber"><strong>Step 2: 3 Real Costs</strong>Subtract road freight, yard fee, and recent price volatility</div>
  <div class="farrow">&rarr;</div>
  <div class="fstep c-purple"><strong>Step 3: Calculator Filter</strong>Check if safe spread &times; weekday reliability beats freight</div>
  <div class="farrow">&rarr;</div>
  <div class="fstep c-green"><strong>Step 4: Live Phone Call</strong>If PASS, FPO manager calls the destination <em>arhtiya</em> to confirm</div>
  <div class="farrow">&rarr;</div>
  <div class="fstep c-red"><strong>Step 5: Honest Settlement</strong>Track exact arrival outcome &mdash; including blank-yard bounds</div>
</div>

<div class="grid2">
  <div class="mini-card">
    <h4>What This Tool ACTUALLY Is</h4>
    <ul>
      <li>An <strong>upstream 6 a.m. alert-triage filter</strong> that stops FPO managers from wasting time and trucks on fake/noisy portal gaps.</li>
      <li>Built strictly on <strong>yesterday-or-earlier public prices</strong> (zero future data leakage, verified by automated corruption tests).</li>
      <li>Verified across <strong>171 zero-lookahead markets</strong> (2025&ndash;2026) AND <strong>clean 166 non-lookahead markets over 2018&ndash;2023 (383,952 trips)</strong>.</li>
    </ul>
  </div>
  <div class="mini-card">
    <h4>What This Tool Does NOT Claim</h4>
    <ul>
      <li>Does <strong>NOT</strong> replace calling a trader (<em>arhtiya</em>) before loading a truck.</li>
      <li>Does <strong>NOT</strong> measure actual farmer cash receipts (AGMARKNET has no truck bills or auction <em>patti</em> slips).</li>
      <li>Does <strong>NOT</strong> prove a blank portal row means a locked gate &mdash; we bracket both closed-yard and open-yard views transparently!</li>
    </ul>
  </div>
</div>

<h2>2. Why Naive Online Spreads Fail: The Four Hidden Traps</h2>

<ol>
  <li><strong>Reporting Lag (Yesterday's Price &ne; Today's Price):</strong> At 6 a.m., today's auction hasn't happened yet. Many smaller mandis upload prices 1 to 7 days late. Yesterday's high price is often an outdated spike that already dropped.</li>
  <li><strong>Physical Frictions (Freight + Yard Fees + Transit Decay):</strong>
    <ul>
      <li><strong>Road Freight (F):</strong> Base loading &#8377;35 + &#8377;0.45 per road km (&times;1.45 in Himachal Pradesh, where 91.59% of roads are single-lane hill roads).</li>
      <li><strong>Stylized State Fee Tiers:</strong> 0.5% to 1.5% charged on destination sale value (0% inside the same district or if unsold), anchored qualitatively to state APMC deregulation status (PIB 154554) and stress-tested from 0% to 6% commission.</li>
      <li><strong>Transit Decay:</strong> Modeled operationally from NABCONS (2022) marketing-level crop loss shares (Tomato 3.25%, Onion 1.96%, Apple 1.64%, Potato 0.86%), stress-tested from 0.5&times; to 2.0&times; and under realized ERA5 arrival-day heat, humidity, and heavy rain.</li>
    </ul>
  </li>
  <li><strong>Silent / Blank Arrival Boards (28.7% of Naive Trips!):</strong> On 28.67% of naive spread-chasing trips, the destination market uploads <em>no trade at all</em> for that crop on arrival day. Under sequential arrival rules (you don't know tomorrow's prices in advance!), a truck facing a blank yard turns back instead of gambling blindly.</li>
  <li><strong>Sunday / Weekly Holiday Blindness &amp; Price Swings:</strong> A mandi closed every Sunday still looks "75% active" in a 28-day average &mdash; fooling average-based filters on weekends. Meanwhile, high-variance markets (like Apple and Tomato) swing violently between yesterday and arrival day.</li>
</ol>

<h2>3. The Breakthrough: Two Zero-Tuned-Parameter Pocket-Calculator Rules</h2>

<p>Earlier in this project, we tried complex gradient-boosted ML trees (Stage I) and tuned heuristics with cutoffs and penalty grids (<code>&kappa;* = 5.0</code>). Auditing proved the ML trees failed statistically (confirmatory <code>H2</code>: +&#8377;6.13, <code>p = 0.27</code>), hard gates failed tail risk, and tuned penalties hit grid walls. <strong>So we stripped away every ML model, weather input, and validation-tuned cutoff</strong>, leaving two transparent Class-10 rules with <strong>zero tuned parameters</strong> (dispatch only when score &gt; 0):</p>

<div class="formula-card">
  <h3 style="margin-top:0;">Rule 1: Safe_EV_Sunk (Best Tail-Risk Protection &mdash; 0 Tuned Parameters)</h3>
  <div class="formula-big">p<sub>dow</sub> &times; G<sub>1SD</sub> &nbsp;&gt;&nbsp; F<sub>road</sub> &nbsp;&nbsp;&nbsp;&nbsp;(equivalently: &nbsp; G<sub>1SD</sub> / F<sub>road</sub> &nbsp;&gt;&nbsp; 1 / p<sub>dow</sub>)</div>
  <p style="margin-bottom:3px;"><strong>Plain English:</strong> <em>"Take yesterday's destination price minus 1 standard deviation of its recent swings (so a normal dip won't wipe you out), subtract yard fee and local price to get safe spread <strong>G<sub>1SD</sub></strong>, multiply by how often this yard actually traded on this exact day of the week (<strong>p<sub>dow</sub></strong>, e.g., last 8 Tuesdays), and go ONLY if that expected safe gain beats one-way freight <strong>F<sub>road</sub></strong>."</em></p>
  <p style="margin-bottom:0; font-size:8.6pt; color:#475569;"><strong>Settlement-Matched Sibling (Safe_EV_Phys, also 0 tuned params):</strong> Uses the exact 1.5&times; return cost directly: <code>p<sub>dow</sub>(G<sub>1SD</sub> &minus; F) &minus; (1 &minus; p<sub>dow</sub>)(1.5 F) &gt; 0</code>. Cuts worst-10% losses even further.</p>
</div>

<div class="formula-card">
  <h3 style="margin-top:0;">Rule 2: RT_2F_Min (Class-8 4-Function Phone Calculator &mdash; No Volatility Needed!)</h3>
  <div class="formula-big">p<sub>min</sub> &times; G &nbsp;&gt;&nbsp; 2 &times; F<sub>road</sub> &nbsp;&nbsp;&nbsp;&nbsp;(equivalently: &nbsp; G / (2 F<sub>road</sub>) &nbsp;&gt;&nbsp; 1 / p<sub>min</sub>)</div>
  <p style="margin-bottom:0;"><strong>Plain English:</strong> <em>"Don't want to compute standard deviation? Just take the plain fee-adjusted spread <strong>G</strong>, multiply by the stricter of 28-day and same-weekday reporting reliability (<strong>p<sub>min</sub></strong>), and go ONLY if it clears <strong>round-trip freight (2F)</strong>!"</em></p>
</div>

<div class="green-box">
  <h3 style="margin-top:0;">10-Second Phone Calculator Example (Real Numbers!)</h3>
  <p><strong>Route:</strong> 200 km Madhya Pradesh Tomato trip. Local price = <strong>&#8377;1,500</strong>, destination price = <strong>&#8377;2,000</strong>, fee = <strong>1.5%</strong>, freight <strong>F = 35 + 0.45 &times; 200 = &#8377;125</strong>, recent price volatility <strong>cv<sub>28</sub> = 15%</strong>.</p>
  <ul>
    <li><strong>Plain spread G:</strong> &#8377;2,000 &times; 0.985 &minus; &#8377;1,500 = <strong>+&#8377;470/qtl</strong>.</li>
    <li><strong>1-SD safe spread G<sub>1SD</sub>:</strong> &#8377;2,000 &times; (1 &minus; 0.15) &times; 0.985 &minus; &#8377;1,500 = <strong>+&#8377;174.50/qtl</strong>.</li>
    <li><strong>Case A &mdash; Reliable Weekday Mandi (open 8/8 Tuesdays &rarr; p<sub>dow</sub> = 0.90, p<sub>min</sub> = 0.85):</strong><br/>
      Safe_EV_Sunk: <code>0.90 &times; 174.50 = &#8377;157.05 &gt; &#8377;125</code> &rarr; <strong>DISPATCH!</strong> &nbsp;|&nbsp; RT_2F_Min: <code>0.85 &times; 470 = &#8377;399.50 &gt; &#8377;250</code> &rarr; <strong>DISPATCH!</strong></li>
    <li><strong>Case B &mdash; Sunday-Closed / Sporadic Mandi (open 1/8 Sundays &rarr; p<sub>dow</sub> = 0.20, p<sub>min</sub> = 0.20):</strong><br/>
      Standard road rule <code>B2</code> still sees <code>&#8377;470 &minus; &#8377;125 = +&#8377;345 &gt; &#8377;200</code> and sends the truck blindly!<br/>
      Both zero-param rules stop it instantly: Safe_EV_Sunk gives <code>0.20 &times; 174.50 = &#8377;34.90 &lt; &#8377;125</code>; RT_2F_Min gives <code>0.20 &times; 470 = &#8377;94.00 &lt; &#8377;250</code> &rarr; <strong>STAY HOME!</strong></li>
  </ul>
</div>

<h2>4. What the Data Proves: Primary 171 Markets + Untouched 6-Year Backtest</h2>

<p>To prevent any future market-selection lookahead, our primary benchmark uses strictly <strong>2024-selected 171 markets</strong> (<code>N = 57,634</code> test episodes, June 2025&ndash;April 2026) with the exact locked 4-test, <code>R = 2,000</code> bootstrap family (<code>p<sub>holm,2s</sub> = 0.0040</code> across all 3 clusterings). Crucially, we then test the <strong>exact same frozen zero-tuned-parameter rules with zero retuning</strong> on the clean non-lookahead <strong>166-market historical archive (2018&ndash;2023, N = 383,952 episodes; 115-mkt N = 325,993)</strong>, including the 2020 COVID-19 supply shock:</p>

<table class="res-table">
  <colgroup>
    <col style="width:30%;"/>
    <col style="width:7%;"/>
    <col style="width:21%;"/>
    <col style="width:21%;"/>
    <col style="width:21%;"/>
  </colgroup>
  <thead>
    <tr>
      <th>Decision Rule</th>
      <th class="num">Free</th>
      <th class="num">Primary 171 Mkts (57.6k)<br/>Mean | Loss% &bull; ES10</th>
      <th class="num">Realized ERA5 (171)<br/>Mean | Loss% &bull; ES10</th>
      <th class="num">Clean 166 Mkts 2018&ndash;23 (384k)<br/>Mean | Loss% &bull; ES10</th>
    </tr>
  </thead>
  <tbody>
    <tr><td><strong>B1_lagged_screen</strong> (top spread &gt; &#8377;100)</td><td class="num">1</td><td class="num">&#8377;384.61 | 45.07%<br/><span class="es-tag">ES10 &minus;&#8377;642.15</span></td><td class="num">&#8377;366.71 | 45.78%<br/><span class="es-tag">ES10 &minus;&#8377;677.22</span></td><td class="num">&#8377;288.85 | 46.11%<br/><span class="es-tag">ES10 &minus;&#8377;555.94</span></td></tr>
    <tr><td><strong>B2_age_matched</strong> (road+fee &gt; &#8377;200, 1&ndash;3d)</td><td class="num">1</td><td class="num">&#8377;419.62 | 26.43%<br/><span class="es-tag">ES10 &minus;&#8377;524.78</span></td><td class="num">&#8377;405.73 | 26.69%<br/><span class="es-tag">ES10 &minus;&#8377;552.91</span></td><td class="num">&#8377;321.57 | 25.21%<br/><span class="es-tag">ES10 &minus;&#8377;473.56</span></td></tr>
    <tr><td><strong>MG_matched</strong> (4 hard gates, val-tuned)</td><td class="num">4</td><td class="num">&#8377;454.07 | 18.35%<br/><span class="es-tag">ES10 &minus;&#8377;508.72</span></td><td class="num">&#8377;440.10 | 18.65%<br/><span class="es-tag">ES10 &minus;&#8377;532.51</span></td><td class="num"><em>(val-tuned;<br/>omitted)</em></td></tr>
    <tr><td><strong>RR_Abstain_matched</strong> (tuned &kappa;* = 5.0)</td><td class="num">2</td><td class="num">&#8377;461.41 | 17.07%<br/><span class="es-tag">ES10 &minus;&#8377;459.46</span></td><td class="num">&#8377;447.88 | 17.44%<br/><span class="es-tag">ES10 &minus;&#8377;482.11</span></td><td class="num"><em>(val-tuned;<br/>omitted)</em></td></tr>
    <tr class="hl"><td><strong>Safe_EV_Sunk_m0</strong> (p<sub>dow</sub> &middot; G<sub>1SD</sub> &gt; F)</td><td class="num">0</td><td class="num">&#8377;452.74 | 14.88%<br/><span class="es-tag">ES10 &minus;&#8377;345.53</span></td><td class="num">&#8377;440.28 | 15.12%<br/><span class="es-tag">ES10 &minus;&#8377;365.11</span></td><td class="num">&#8377;356.57 | 12.64%<br/><span class="es-tag">ES10 &minus;&#8377;304.29</span></td></tr>
    <tr class="hl"><td><strong>Safe_EV_Phys_m0</strong> (1.5F settlement-matched)</td><td class="num">0</td><td class="num">&#8377;449.52 | 13.70%<br/><span class="es-tag">ES10 &minus;&#8377;334.80</span></td><td class="num">&#8377;437.31 | 13.94%<br/><span class="es-tag">ES10 &minus;&#8377;353.85</span></td><td class="num">&#8377;353.33 | 11.45%<br/><span class="es-tag">ES10 &minus;&#8377;288.47</span></td></tr>
    <tr class="hl"><td><strong>RT_2F_Min_m0</strong> (Class-8 p<sub>min</sub> &middot; G &gt; 2F)</td><td class="num">0</td><td class="num">&#8377;463.98 | 16.21%<br/><span class="es-tag">ES10 &minus;&#8377;464.84</span></td><td class="num">&#8377;450.56 | 16.50%<br/><span class="es-tag">ES10 &minus;&#8377;489.02</span></td><td class="num">&#8377;370.86 | 14.24%<br/><span class="es-tag">ES10 &minus;&#8377;395.63</span></td></tr>
  </tbody>
</table>

<p style="font-size:8.5pt; color:#475569;"><strong>Key statistical takeaway:</strong> On clean <code>166</code>-mkt <code>2018&ndash;2023</code> (<code>N = 383,952</code>; 160 origin / 159 b2dest clusters &times; 153 fortnights, <code>R = 2,000</code>), <code>Safe_EV_Sunk_m0</code> beats <code>B2</code> on <code>ES10</code> (+&#8377;169.27) and conditional <code>cond_ES10</code> (+&#8377;155.08; &minus;&#8377;421.35 vs &minus;&#8377;576.44; +&#8377;174.27 vs equal-dispatch <code>B2_eq_SafeM0</code>) in <strong>all 6 years</strong> (all <code>p = 0.001</code>, while <code>2020</code> &amp; <code>2023</code> Means are NS: <code>p = 0.208 / 0.077</code>), holding identically on <code>115</code>-mkt (<code>N = 325,993</code>, +&#8377;159.83 ES10) and under NASA POWER climate. On primary 171-mkt, all 4 locked tests pass (<code>p<sub>holm,2s</sub> = 0.0040</code>, <code>cond_ES10 &minus;&#8377;447.48</code> vs <code>&minus;&#8377;628.37</code>) and survive <code>&le; t&minus;2</code> lag (<code>p = 0.001</code>) and coupled <code>S6_Frozen &times; Stoch_CondMAR</code> (<code>+&#8377;366.85 cond_ES10</code>).</p>

<figure>
  <img src="{img_uri('rev_fig1_risk_coverage_ci.png')}" alt="Risk Coverage Curves"/>
  <figcaption><strong>Visual Proof 1 (Risk vs Coverage):</strong> At the exact same dispatch rate, zero-tuned-parameter Safe_EV_Sunk (purple) sits far below B2 and hard gates on episode losses (left) and far above them on worst-10% tail shortfall ES10 (right).</figcaption>
</figure>

<figure>
  <img src="{img_uri('rev_fig4_settlement_and_hp_apple.png')}" alt="Untouched 2018-2023 Backtest and HP Apples"/>
  <figcaption><strong>Visual Proof 2 (Six Historical Years &amp; Graded Apples):</strong> Left: Across every year from 2018 through 2023 on 166 clean markets (including 2020 COVID-19), zero-tuned-parameter Safe_EV_Sunk and Safe_EV_Phys consistently protect against worst-decile losses without retuning. Right: On HP graded apples (N = 2,802), Safe_EV cuts unconditional ES10 from &minus;&#8377;2,392 to &minus;&#8377;1,455, though 41.38% of dispatched trips lose money and <code>cond_ES10</code> (p = 0.094) is non-significant.</figcaption>
</figure>

<h2>5. The 10 Most Relevant Research Papers (Your Literature Map in Plain English)</h2>

<p>Your thesis connects <strong>four classic research areas</strong>. Memorize these <strong>10 real, verified foundational papers</strong> &mdash; each is explained in two plain-English sentences so you can cite them naturally in any viva or review response:</p>

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
      <td>Explains why <strong>live phone calls</strong> to destination <em>arhtiyas</em> remain vital &mdash; MandiGuard filters noisy AGMARKNET alerts <em>before</em> dialing.</td>
    </tr>
    <tr>
      <td><strong>3. Fafchamps &amp; Minten (2012)</strong><br/><em>World Bank Econ. Rev.</em></td>
      <td>Large field RCT in Maharashtra sending daily SMS mandi prices to farmers found <strong>almost zero average income gain</strong> because transport and execution frictions blocked arbitrage.</td>
      <td>Directly proves why raw AGMARKNET screens mislead (our 45.1% naive loss rate) &mdash; raw prices need reliability and volatility filtering.</td>
    </tr>
    <tr>
      <td><strong>4. Mitra et al. (2018)</strong><br/><em>Rev. Econ. &amp; Statistics</em></td>
      <td>Field experiment with West Bengal potato farmers showing middlemen, transport barriers, and asymmetric information absorb raw price spreads.</td>
      <td>Reinforces why we stress-test 2&ndash;6% <em>arhtiya</em> commissions and never claim modeled spreads equal farmer household cash.</td>
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
      <td>Directly motivates eliminating black-box ML trees in favor of our 10-second pocket-calculator rules (<code>Safe_EV_Sunk</code> &amp; <code>RT_2F_Min</code>).</td>
    </tr>
  </tbody>
</table>

<span class="pillar-badge">PILLAR 3 &bull; Knowing When to Abstain &amp; Optimizing Decisions (Not Accuracy)</span>
<table>
  <thead><tr><th style="width:22%;">Paper &amp; Venue</th><th style="width:42%;">Core Idea in Plain English</th><th style="width:36%;">How MandiGuard Connects / Differs</th></tr></thead>
  <tbody>
    <tr>
      <td><strong>8. Chow (1970)</strong> &amp; <strong>El-Yaniv &amp; Wiener (2010)</strong><br/><em>IEEE TIT &amp; JMLR</em></td>
      <td>Founded <em>selective prediction (reject option)</em>: when mistakes are far costlier than staying silent, abstaining cuts catastrophic risk dramatically.</td>
      <td>The theoretical root of "staying home at &#8377;0" when weekday reporting reliability is low &mdash; trading 8.5% fewer trips for 44% fewer losses.</td>
    </tr>
    <tr>
      <td><strong>9. Elmachtoub &amp; Grigas (2022)</strong><br/><em>Management Science</em></td>
      <td><em>Smart "Predict, Then Optimize"</em>: showed that training a model to minimize average price error often gives bad operational decisions when costs are asymmetric.</td>
      <td>Explains why our Stage I GBDT price-predictor failed (<code>H2 p = 0.27</code>) while direct lower-bound score ratios succeed with zero tuned parameters.</td>
    </tr>
  </tbody>
</table>

<span class="pillar-badge">PILLAR 4 &bull; Missing-Data Bounds &amp; Worst-Case Tail Risk (ES10)</span>
<table>
  <thead><tr><th style="width:22%;">Paper &amp; Venue</th><th style="width:42%;">Core Idea in Plain English</th><th style="width:36%;">How MandiGuard Connects / Differs</th></tr></thead>
  <tbody>
    <tr>
      <td><strong>10. Manski (1990)</strong> &amp; <strong>Rockafellar &amp; Uryasev (2000)</strong><br/><em>AER &amp; Journal of Risk</em></td>
      <td>Manski introduced <em>nonparametric bounds</em> when outcomes are missing (bracket best/worst cases instead of guessing). Rockafellar &amp; Uryasev formalized coherent <em>Expected Shortfall / CVaR</em> (average of worst 10% outcomes).</td>
      <td>Anchors our two signature metrics: exact fractional <strong>ES10</strong> (preventing disaster days) and exact <strong>closed-yard vs Open-MAR break-even bounds</strong> (25.45% silent-open share).</td>
    </tr>
  </tbody>
</table>

<h2>6. Radical Honesty: Every Negative Result &amp; Boundary You MUST Know</h2>

<div class="warn-box">
  <h3 style="margin-top:0;">Why Knowing Your Own Weaknesses Wins Every Viva &amp; Review</h3>
  <p style="margin-bottom:4px;">Examiners love catching students hiding negative results &mdash; and immediately respect students who explain their exact failure boundaries clearly. Memorize these <strong>five honest disclosures</strong>:</p>
  <ol style="margin-bottom:0;">
    <li><strong>The Missing-Quote Interpretation Bound (Open-MAR Reversal &amp; Break-Even):</strong> A blank AGMARKNET row could mean the yard was closed <em>or</em> that it traded and forgot to upload. Under the optimistic <em>Open-MAR</em> extreme (pretending 100% of blank yards actually cleared at yesterday's price), road baseline <code>B2</code> earns <strong>+&#8377;97.01/qtl higher Mean</strong> (&#8377;698.17 vs &#8377;601.16 on 171 markets; +&#8377;111.53 on 166-mkt 2018&ndash;2023), though <code>Safe_EV</code> still reduces losses and beats <code>B2</code> on <code>ES10</code> (+&#8377;189.97). Exact break-even algebra shows <code>B2</code> overtakes <code>Safe_EV</code> on Mean only if at least <strong>25.45%</strong> of silent yards clear at full lagged prices (26.65% under ERA5) &mdash; or if silent trips average <strong>+&#8377;348.61/qtl</strong> above turn-back.</li>
    <li><strong>When Mean Gains Disappear (Free Turn-Back &amp; Hindsight):</strong> If turning back is assumed free (<code>div = 0</code> or literal <code>&#8377;0</code> diversion), <code>Safe_EV</code>'s Mean gain over <code>B2</code> (+&#8377;12.03 / +&#8377;11.21) is <strong>not statistically significant</strong> (<code>p = 0.22&ndash;0.26</code>), though <code>ES10</code> (+&#8377;174.40 / +&#8377;169.82) remains strongly significant. Under clairvoyant 3-day hindsight settlement, <code>B2</code> beats both <code>Safe_EV</code> (&#8377;549.81 vs &#8377;533.14) and <code>RT_2F</code> (&#8377;534.11) on Mean, while <code>Safe_EV</code> still cuts <code>ES10</code> tail risk in half (&minus;&#8377;279.93 vs &minus;&#8377;588.34).</li>
    <li><strong>Subgroup Nuances (Mean vs ES10, and Potato vs RR):</strong> <code>Safe_EV_Sunk_m0</code> wins <strong>all 6 states and all 5 crop slices (4 crops incl. NonApple) on ES10 vs B2</strong>, but its <em>Mean</em> CIs cross zero in Gujarat (&minus;&#8377;1.66), Maharashtra, UP, Tomato, and Apple (whereas Class-8 <code>RT_2F_Min_m0</code> has strictly positive Mean CIs in all 6 states and all 5 crop slices!). On Potato, <code>Safe_EV</code> beats <code>B2</code> (+&#8377;70.61 ES10) but trails tuned <code>RR</code> by &minus;&#8377;17.20.</li>
    <li><strong>Graded Apples &amp; Legacy Stage I ML:</strong> On HP graded apples (<code>N = 2,802</code>), <code>Safe_EV</code> improves <code>ES10</code> from &minus;&#8377;2,392 to &minus;&#8377;1,455, yet <strong>41.38% of dispatched trips still lose money</strong>. Legacy Stage I GBDT/conformal stayed inconclusive (<code>H2 +&#8377;6.13, p = 0.27</code>) and we claim zero conformal guarantees.</li>
    <li><strong>No Live Field Receipts Yet (Prospective Gate J):</strong> Our 2025&ndash;2026 evaluation is exploratory (same calendar seen in earlier commits), and even our untouched 6-year 2018&ndash;2023 backtest uses historical public archives (no real truck bills or live phone logs). A small 1-season FPO field pilot logging actual <em>arhtiya</em> phone calls is the exact next step!</li>
  </ol>
</div>

<h2>7. Quick Viva Survival Guide: 6 Toughest Examiner Questions &amp; 15-Second Answers</h2>

<div class="qa-item">
  <div class="qa-q">Q1: "If this is an M.Tech thesis, why did you throw away Machine Learning and use a 1-line calculator formula?"</div>
  <div><strong>Answer:</strong> "Because we tested GBDT + conformal prediction first (Stage I) and audited it honestly &mdash; it leaked weather, failed confirmatory <code>H2</code> (<code>p = 0.27</code>), and lost on graded apples. Stripping away complexity to zero-tuned-parameter domain physics (<code>p<sub>dow</sub> &middot; G<sub>1SD</sub> &gt; F</code>) cut difficulty from 4.3 to 1.2/5 while beating comparable-coverage ML and tuned heuristics on worst-10% shortfall across 171 markets and 6 untouched years (2018&ndash;2023)."</div>
</div>

<div class="qa-item">
  <div class="qa-q">Q2: "Didn't you design these rules after seeing the 2025&ndash;2026 test set?"</div>
  <div><strong>Answer:</strong> "Yes &mdash; we explicitly label the 2025&ndash;2026 split exploratory and strictly report the locked <code>PREREG_A18</code> 4-test, <code>R = 2,000</code> family (<code>p<sub>holm,2s</sub> = 0.0040</code>). To prove it wasn't overfit to 2025&ndash;2026, we froze the exact zero-tuned-parameter formulas and ran them verbatim with zero retuning on clean 166 non-lookahead markets over 2018&ndash;2023 (383,952 episodes) &mdash; they beat <code>B2</code> on <code>ES10</code> and <code>cond_ES10</code> in all 6 years (2020 COVID-19 &amp; 2023 Means NS) and survive <code>&le; t&minus;2</code> latency."</div>
</div>

<div class="qa-item">
  <div class="qa-q">Q3: "Why not just call the destination trader on the phone instead of using math?"</div>
  <div><strong>Answer:</strong> "You <em>should</em> call the trader before loading a truck! Our rule does not replace the phone call &mdash; it filters dozens of noisy AGMARKNET alerts at 6 a.m. so the FPO manager only dials reliable, low-volatility corridors. And even on confirmed open auctions alone (<code>exact_d0</code>), <code>Safe_EV</code> halves worst-10% tail losses (&minus;&#8377;302 vs &minus;&#8377;626) while matching open mean (&#8377;901 vs &#8377;902)."</div>
</div>

<div class="qa-item">
  <div class="qa-q">Q4: "What if blank AGMARKNET rows were actually open markets that simply forgot to upload?"</div>
  <div><strong>Answer:</strong> "We cannot prove physical closure from a blank web row, so we follow Manski (1990) and bracket both extremes plus exact break-even algebra: <code>B2</code> only catches <code>Safe_EV</code> on Mean if at least 25.45% of silent yards clear at full lagged prices (Open-MAR gives <code>B2</code> +&#8377;97/qtl Mean), while <code>Safe_EV</code> still cuts losses and beats <code>B2</code> by +&#8377;190/qtl on <code>ES10</code> even under 100% Open-MAR."</div>
</div>

<div class="qa-item">
  <div class="qa-q">Q5: "Where did your fee percentages (0.5&ndash;1.5%) and spoilage numbers come from?"</div>
  <div><strong>Answer:</strong> "We are completely transparent: PIB 154554 lists qualitative state APMC exemptions/user-charge regimes (not exact percentages), so our 0.5&ndash;1.5% rates are stylized friction tiers anchored qualitatively to those regimes. Likewise, NABCONS (2022, PIB 2151371) reports cumulative marketing-level crop loss shares (3.25%, 1.96%, 1.64%, 0.86%), which we calibrate operationally as 24h decay parameters. Because both are modeling choices, we stress-tested 0% fees, 6% commissions, 0.5&times;&ndash;2.0&times; spoilage, and realized ERA5 weather &mdash; <code>Safe_EV</code> holds across all 36/36 tornado scenarios."</div>
</div>

<div class="qa-item">
  <div class="qa-q">Q6: "What is your single next step to turn this into a top-tier journal paper?"</div>
  <div><strong>Answer:</strong> "A one-season FPO field pilot logging 200&ndash;500 real 6 a.m. <em>arhtiya</em> confirmation calls, truck bills, and auction <em>patti</em> slips &mdash; that directly measures the true silent-open rate against our 25.45% break-even threshold and unblocks prospective causal validation (Gate J)."</div>
</div>

<div class="footer-note">
  <strong>MandiGuard Revision v7 Concept &amp; Literature Guide</strong> &bull; Every metric verified directly from <code>revision/results/v7_*.csv</code> (primary zero-lookahead 171-market panel N = 57,634; clean 166-mkt 2018&ndash;2023 panel N = 383,952; locked PREREG_A18 R = 2,000 bootstrap; 59 verified citations in <code>paper/references.bib</code>).
</div>
"""


def main() -> None:
    doc = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>'
        "<title>MandiGuard — Ultra-Simplified Concept &amp; Top 10 Research Papers Guide (Revision v7)</title>"
        f"<style>{CSS}</style></head><body>{HTML_BODY}</body></html>"
    )
    HTML_OUT.write_text(doc, encoding="utf-8")
    render_pdf(HTML_OUT, PDF_OUT)

    reader = PdfReader(str(PDF_OUT))
    txt = "\n".join((p.extract_text() or "") for p in reader.pages)
    assert len(reader.pages) <= 8, f"Expected compact <= 8 pages, got {len(reader.pages)}"
    raw_macros = sorted(set(re.findall(r"\\[a-zA-Z]{2,}", txt)))
    assert raw_macros == [], f"Raw LaTeX macros leaked: {raw_macros}"
    for bad in ("TO CONFIRM", "exploratory: true", "make reproduce", "[jensen2007digital]"):
        assert bad not in txt, f"Forbidden token `{bad}` found in {PDF_OUT.name}"
    print(f"Wrote {HTML_OUT.name} & {PDF_OUT.name} ({len(reader.pages)} pages, clean)")


if __name__ == "__main__":
    main()
