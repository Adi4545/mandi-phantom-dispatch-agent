#!/usr/bin/env python3
"""Build the beginner-friendly (Class 10-12 level) MandiGuard Study Guide PDF.

Generates:
  1. docs/MandiGuard_Student_Study_Guide.html
  2. docs/MandiGuard_Student_Study_Guide.pdf

Every number in this guide is copied from verified project outputs
(paper/manuscript.md, results/*.csv). Worked examples that are purely
illustrative (to teach a concept) are labelled "Illustration".
"""

from __future__ import annotations

import base64
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "figures"
DOCS_DIR = ROOT / "docs"
HTML_OUT = DOCS_DIR / "MandiGuard_Student_Study_Guide.html"
PDF_OUT = DOCS_DIR / "MandiGuard_Student_Study_Guide.pdf"
CHROME_BIN = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def b64_img(filename: str) -> str:
    path = FIG_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing figure: {path}")
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


# ---------------------------------------------------------------------------
# Small HTML helpers for flowcharts (pure CSS, no JavaScript needed)
# ---------------------------------------------------------------------------
def hflow(items: list[tuple[str, str, str]], arrow: str = "&#10140;") -> str:
    """Horizontal flowchart. items = [(title, subtitle, colour_class), ...]."""
    parts = []
    for i, (title, sub, col) in enumerate(items):
        parts.append(f'<div class="fbox {col}"><b>{title}</b><span>{sub}</span></div>')
        if i < len(items) - 1:
            parts.append(f'<div class="farrow">{arrow}</div>')
    return '<div class="flow">' + "".join(parts) + "</div>"


def vgate(steps: list[tuple[str, str, str]], final_yes: str, final_no: str) -> str:
    """Vertical decision flow: each gate can PASS (down) or FAIL (right, to refuse)."""
    rows = []
    for title, question, fail in steps:
        rows.append(
            '<div class="gate-row">'
            f'<div class="gate">{title}<span>{question}</span></div>'
            '<div class="gate-fail-arrow">NO &#10140;</div>'
            f'<div class="gate-fail">{fail}</div>'
            "</div>"
            '<div class="gate-down">&#8595; YES (pass)</div>'
        )
    rows.append(f'<div class="gate-row"><div class="gate final-yes">{final_yes}</div>'
                f'<div class="gate-fail-arrow">else &#10140;</div><div class="gate-fail">{final_no}</div></div>')
    return '<div class="gates">' + "".join(rows) + "</div>"


CSS = """
@page { size: A4; margin: 13mm 13mm 15mm 13mm; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
       font-size: 10.2pt; line-height: 1.5; color: #1f2937; margin: 0; }
h1 { font-size: 18pt; color: #0b3b5c; border-bottom: 3px solid #0b3b5c; padding-bottom: 4px; margin: 0 0 8px 0; }
h2 { font-size: 13pt; color: #0e5a7a; border-left: 5px solid #0ea5e9; padding-left: 8px; margin: 16px 0 6px 0;
     break-after: avoid; page-break-after: avoid; }
h3 { font-size: 11pt; color: #1e3a5f; margin: 12px 0 4px 0; break-after: avoid; }
p { margin: 0 0 7px 0; }
ul, ol { margin: 3px 0 8px 0; padding-left: 20px; }
li { margin-bottom: 3px; }
b, strong { color: #0f172a; }
code { font-family: Menlo, Consolas, monospace; font-size: 8.8pt; background: #f1f5f9; border: 1px solid #e2e8f0;
       border-radius: 3px; padding: 0 3px; }
.pb { break-before: page; page-break-before: always; }
.avoid { break-inside: avoid; page-break-inside: avoid; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 10px 0; font-size: 9pt; break-inside: avoid; }
th { background: #0b3b5c; color: #fff; padding: 5px 6px; text-align: left; font-weight: 600; }
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
.formula { font-family: Menlo, Consolas, monospace; font-size: 9.6pt; background: #ffffff; border: 1px dashed #a855f7;
           padding: 6px 8px; border-radius: 5px; margin: 5px 0; display: block; white-space: pre-wrap; }
.cover { border: 3px solid #0b3b5c; border-radius: 12px; padding: 26px 28px; margin-top: 10mm;
         background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 60%, #ecfdf5 100%); }
.cover h1 { border: none; font-size: 25pt; margin-bottom: 4px; }
.cover .sub { font-size: 13pt; color: #0e5a7a; margin-bottom: 14px; }
.pill { display: inline-block; background: #0b3b5c; color: #fff; border-radius: 12px; padding: 2px 10px;
        font-size: 8.8pt; margin: 2px 3px 2px 0; }
.flow { display: flex; flex-wrap: wrap; align-items: stretch; gap: 3px; margin: 8px 0 10px 0; break-inside: avoid; }
.fbox { flex: 1 1 0; min-width: 72px; border: 1.6px solid; border-radius: 7px; padding: 6px 6px; text-align: center;
        font-size: 8.6pt; line-height: 1.3; display: flex; flex-direction: column; justify-content: center; }
.fbox b { font-size: 9pt; margin-bottom: 2px; display: block; }
.fbox span { color: #334155; }
.farrow { display: flex; align-items: center; font-size: 15pt; color: #64748b; padding: 0 1px; }
.c1 { background: #e0f2fe; border-color: #0284c7; } .c2 { background: #dcfce7; border-color: #16a34a; }
.c3 { background: #fef9c3; border-color: #ca8a04; } .c4 { background: #fee2e2; border-color: #dc2626; }
.c5 { background: #ede9fe; border-color: #7c3aed; } .c6 { background: #f1f5f9; border-color: #475569; }
.gates { margin: 8px 0 12px 0; break-inside: avoid; }
.gate-row { display: flex; align-items: center; gap: 6px; }
.gate { flex: 0 0 56%; background: #e0f2fe; border: 1.8px solid #0284c7; border-radius: 7px; padding: 6px 9px;
        font-weight: 700; font-size: 9.3pt; }
.gate span { display: block; font-weight: 400; font-size: 8.7pt; color: #334155; }
.gate.final-yes { background: #dcfce7; border-color: #16a34a; }
.gate-fail-arrow { flex: 0 0 9%; color: #dc2626; font-weight: 700; font-size: 8.5pt; text-align: center; }
.gate-fail { flex: 1; background: #fee2e2; border: 1.6px solid #dc2626; border-radius: 7px; padding: 5px 8px; font-size: 8.7pt; }
.gate-down { margin: 1px 0 1px 18%; color: #16a34a; font-weight: 700; font-size: 8.6pt; }
.timeline { display: flex; margin: 8px 0 10px 0; break-inside: avoid; border-radius: 7px; overflow: hidden; border: 1.5px solid #334155; }
.timeline div { padding: 7px 6px; font-size: 8.6pt; text-align: center; line-height: 1.3; }
.figure { text-align: center; margin: 8px 0 12px 0; break-inside: avoid; }
.figure img { max-width: 100%; max-height: 105mm; border: 1px solid #cbd5e1; border-radius: 4px; }
.figure .cap { font-size: 8.6pt; color: #475569; margin-top: 3px; text-align: left; }
.qa { border-left: 4px solid #22c55e; background: #f8fafc; padding: 5px 9px; margin: 6px 0; break-inside: avoid; }
.qa .q { font-weight: 700; color: #0f172a; }
.qa .a { margin-top: 2px; }
.slide { border: 1.5px solid #0b3b5c; border-radius: 7px; margin: 7px 0; break-inside: avoid; }
.slide .sh { background: #0b3b5c; color: #fff; padding: 4px 9px; font-weight: 700; font-size: 9.6pt; }
.slide .sb { padding: 6px 10px; font-size: 9.2pt; }
.toc li { margin-bottom: 2px; }
.small { font-size: 8.8pt; color: #475569; }
"""

# ---------------------------------------------------------------------------
# CONTENT
# ---------------------------------------------------------------------------
COVER = """
<div class="cover">
  <h1>MandiGuard &mdash; The Complete Student Study Guide</h1>
  <div class="sub">Phantom Spatial Arbitrage in Indian Mandis: Stage I (MandiGuard) + Stage II (MandiGuard-CRC)<br/>
  Explained from first principles &mdash; so that any Class 10&ndash;12 student can follow every step</div>
  <span class="pill">Why this topic</span><span class="pill">First principles</span><span class="pill">Data collection</span>
  <span class="pill">Data validation</span><span class="pill">Method (step by step)</span><span class="pill">Fair testing</span>
  <span class="pill">Results</span><span class="pill">Stage II autopsy &amp; fix</span><span class="pill">Related papers</span>
  <span class="pill">What we did differently</span><span class="pill">Limitations</span><span class="pill">Synopsis slides</span>
  <span class="pill">Viva Q&amp;A</span>
  <div class="box key" style="margin-top:14px;"><span class="t">The whole thesis in 3 sentences</span>
  A price on a mobile screen can show that a mandi 200 km away pays &#8377;600 more per quintal, but after the truck reaches,
  the market may be closed, the exact variety may not be bought, diesel and fees cost money, and tomatoes rot in the heat &mdash;
  so most of that &ldquo;extra money&rdquo; is a <b>phantom</b>. We measured this with real government price data
  (69,526 real dispatch opportunities, 6 states, 4 crops) and built <b>MandiGuard</b>, a checklist-style decision helper that
  checks the cheap facts first, keeps a safety cushion, and says <b>&ldquo;stay home&rdquo;</b> when the trip is risky.
  Then we honestly examined why it did not beat a strong simple rule on average, fixed three causes
  (<b>MandiGuard-CRC</b>), and tested the fix on data it had never seen.</div>
  <div class="box think"><span class="t">How to use this guide</span>
  Read Chapters 1&ndash;3 to understand the idea. Chapters 4&ndash;9 are the research journey in order (data &rarr; method &rarr; testing &rarr; results).
  Chapters 10&ndash;12 cover papers, novelty and limitations. Chapters 13&ndash;15 prepare you for the synopsis presentation and viva.
  Yellow boxes = intuition, blue = key facts, purple = maths, green = what to say in the viva, red = traps to avoid.</div>
</div>

<h2>Contents</h2>
<ol class="toc">
  <li>The story: why this topic was chosen</li>
  <li>First principles: the 12 ideas you need (no prior knowledge assumed)</li>
  <li>The big picture: one flowchart that connects every dot</li>
  <li>Data collection: where every number came from</li>
  <li>Data validation: how we proved the data is trustworthy</li>
  <li>Building fair test questions: episodes, time splits and the &ldquo;no peeking&rdquo; firewall</li>
  <li>Stage I method: MandiGuard step by step (with a worked Tomato example)</li>
  <li>Fair testing: baselines, metrics, pre-registration and statistics</li>
  <li>Stage I results and robustness checks</li>
  <li>Stage II: the honest autopsy and MandiGuard-CRC</li>
  <li>Relevant papers, explained simply (37 references in 6 groups)</li>
  <li>What we did differently (novelty) and limitations</li>
  <li>Synopsis presentation: slide-by-slide plan with speaking notes</li>
  <li>Viva defence: 35 likely questions with simple answers + red lines</li>
  <li>Glossary and one-page revision sheet</li>
</ol>
"""

CH1 = """
<div class="pb"></div>
<h1>Chapter 1 &mdash; The Story: Why This Topic?</h1>

<h2>1.1 Meet the farmer</h2>
<p>Imagine a small tomato farmer in Madhya Pradesh. This morning he can sell his harvest at the <b>local mandi</b>
(wholesale market) for <b>&#8377;1,400 per quintal</b> (1 quintal = 100 kg). On his phone, a government price portal shows that
a mandi <b>200 km away</b> paid <b>&#8377;2,000 per quintal</b>. That looks like <b>&#8377;600 extra per quintal</b>.</p>
<p>How big is this for him? The Government of India&rsquo;s National Statistical Office survey (NSS Report No. 587) says
onion and potato households typically harvest about <b>29&ndash;39 quintals per season</b> &mdash; roughly one 30-quintal
mini-truck &mdash; and the average agricultural household earns only about <b>&#8377;3,798 per month</b> from crops, with
50.2% of households in debt (average &#8377;74,121).</p>
<div class="box key"><span class="t">Why the stakes are high</span>
&#8377;600 &times; 30 quintals = <b>&#8377;18,000</b> of apparent extra income from one truck &mdash; close to five months of
average crop income. A wrong decision is equally large in the other direction: diesel is spent, produce rots, and the farmer
may have to sell cheaply or drive back.</div>

<h2>1.2 The trap: the screen price is not the price you will actually get</h2>
<p>Between seeing a price on the screen and getting cash at the far mandi, four real-world frictions eat the gap:</p>
<ol>
  <li><b>Wrong variety or grade:</b> buyers bid separately for, say, Red vs Desi onions, or Grade A vs Grade B apples.
  If nobody is buying <i>your exact variety</i> that day, you sell at a discount.</li>
  <li><b>Closed gates and old (stale) quotes:</b> mandis have weekly holidays and sometimes simply do not report prices.
  The &#8377;2,000 you saw may be 4 days old, or the market may be shut on the day your truck arrives.</li>
  <li><b>Real roads are longer than straight lines:</b> in Himachal Pradesh, 91.59% of motorable roads (39,465 of 43,091 km)
  are single-lane hill roads (HP Economic Survey 2025&ndash;26). Diesel and time cost more than a map line suggests.</li>
  <li><b>Heat, rain and fees:</b> tomatoes rot faster in a 40&deg;C afternoon; heavy rain damages produce; states charge
  different market fees (0.5% to 1.5%).</li>
</ol>
<p>We call the part of the screen gap that disappears <b>&ldquo;Phantom Spatial Arbitrage&rdquo;</b>:
<i>spatial</i> = between places, <i>arbitrage</i> = buying/selling to profit from a price difference,
<i>phantom</i> = it looks real but vanishes.</p>

<h2>1.3 How big is the phantom? (our first measurement, Exp 1)</h2>
<p>We replayed what would happen if farmers simply chased the best screen price (we call this policy <b>B1</b>) on real data
from June 2025 to April 2026:</p>
<table>
<tr><th>What we measured (63,040 naive truck dispatches)</th><th class="num">Value</th></tr>
<tr><td>Average screen gap the farmer saw</td><td class="num">&#8377;1,330.49 / qtl</td></tr>
<tr><td>Average money actually gained after everything</td><td class="num">&#8377;386.02 / qtl (71% smaller)</td></tr>
<tr><td>Lost to diesel + fees</td><td class="num">&#8377;160.81 / qtl</td></tr>
<tr><td>Lost to heat/rain spoilage (modelled)</td><td class="num">&#8377;68.76 / qtl</td></tr>
<tr><td>Lost to closed gates, missing variety and arrival-day price drops</td><td class="num">&#8377;714.90 / qtl</td></tr>
<tr class="hl"><td>Trucks that hit a closed gate or missing-variety delay</td><td class="num">58.94%</td></tr>
<tr class="hl"><td>Trucks that <b>lost money</b> compared with selling at home</td><td class="num">40.46%</td></tr>
</table>
<div class="box think"><span class="t">The surprising part</span>
The biggest loss is <b>not</b> diesel or rot. It is <b>&ldquo;execution risk&rdquo;</b>: arriving and finding the market closed or not
buying your variety. A smarter price forecast alone cannot fix that, because the problem is not just &ldquo;what will the price be?&rdquo;
but &ldquo;will I even be able to sell there?&rdquo;</div>

<h2>1.4 Why we chose this topic (the reasons you should say in the synopsis)</h2>
<table>
<tr><th style="width:26%">Reason</th><th>Explanation</th></tr>
<tr><td><b>Real social value</b></td><td>Smallholders earn little; one bad truck trip can wipe out months of income. Helping them avoid bad trips matters.</td></tr>
<tr><td><b>A clear, measurable gap</b></td><td>Economics papers show price information alone does not raise farmer income when transport and selling are unreliable (Mitra et al., 2018). Computer-science papers forecast prices but rank markets using straight-line distance and ignore closed markets. Nobody had measured how much of the screen gap is phantom across many states and then built a decision rule around it.</td></tr>
<tr><td><b>Public, checkable data</b></td><td>AGMARKNET prices, OpenStreetMap roads, ERA5/NASA weather and government survey numbers are all public, so anyone can reproduce the work.</td></tr>
<tr><td><b>Right size for M.Tech</b></td><td>The method uses simple, explainable tools (rules + one tree model + a safety cushion) rather than a large black box, so it can be built, tested and defended in one thesis.</td></tr>
<tr><td><b>Honest science is possible</b></td><td>Because outcomes are recorded in history, we can test decisions on months the model never saw, and pre-register what we expect before looking.</td></tr>
</table>
<div class="box viva"><span class="t">Say this in the viva (30 seconds)</span>
&ldquo;Price portals made information free, but information is not money. Across 63,040 naive dispatches, a &#8377;1,330 screen gap
turned into &#8377;386 of real gain, and 40% of trucks lost money &mdash; mostly because markets were closed or not buying the exact variety.
So I studied the <i>decision</i> &mdash; go or stay &mdash; not just the price, and built a transparent checker that verifies the
cheap facts first, keeps a safety cushion and is allowed to say &lsquo;stay home&rsquo;.&rdquo;</div>
"""

CH2 = """
<div class="pb"></div>
<h1>Chapter 2 &mdash; First Principles: The 12 Ideas You Need</h1>
<p>Everything in this thesis is built from twelve simple ideas. Learn these and the rest is just careful bookkeeping.</p>

<h2>Idea 1 &mdash; Mandi, quintal and the three prices</h2>
<p>A <b>mandi</b> is a regulated wholesale market (APMC). Each day the portal records, for each crop and <b>variety</b>,
a <b>Min price</b>, a <b>Max price</b> and a <b>Modal price</b> (the most common price). Prices are in &#8377; per <b>quintal</b> (100 kg).</p>

<h2>Idea 2 &mdash; The spread</h2>
<div class="box math"><span class="t">Spread (what the screen promises)</span>
<span class="formula">Screen spread = Destination price on screen &minus; Local price at home</span>
Example: &#8377;2,000 &minus; &#8377;1,400 = &#8377;600 per quintal.</div>

<h2>Idea 3 &mdash; Net gain (what you actually earn compared with staying home)</h2>
<div class="box math"><span class="t">Net gain of a trip (per quintal)</span>
<span class="formula">Net gain = (Price you really get) &times; (1 &minus; fraction spoiled)
           &minus; freight and market fee
           &minus; waiting charges (if the market is late or closed)
           &minus; local price you gave up</span>
If Net gain is negative, the trip was a <b>loss trip</b>. Staying home (&ldquo;SELL_LOCAL&rdquo;) always has Net gain = &#8377;0.</div>
<p>In the thesis, freight = &#8377;35 loading + &#8377;0.45 per km (&times;1.45 on Himachal hill roads), plus the state market fee
(0.5%, 1.0% or 1.5%) on cross-district trips. Waiting costs &#8377;25 per quintal per day.</p>

<h2>Idea 4 &mdash; Spoilage grows with heat (the Q10 rule)</h2>
<p>Biology rule of thumb: many decay processes roughly <b>double for every +10&deg;C</b> (called Q10 = 2). The government NABCONS survey (2022)
gives market-stage losses at a reference condition: <b>Tomato 3.25%, Onion 1.96%, Apple 1.64%, Potato 0.86%</b>.</p>
<div class="box math"><span class="t">Spoilage in one line</span>
<span class="formula">spoiled fraction &asymp; base loss &times; (hours on road / 24) &times; 2^((temperature &minus; 20) / 10)</span>
At 40&deg;C, 2^((40&minus;20)/10) = 2^2 = 4, so decay runs 4 times faster than at 20&deg;C. (The full formula also adds humidity
and heavy-rain effects and is capped at 55%.)</div>

<h2>Idea 5 &mdash; Why the screen can lie: stale, closed, wrong variety</h2>
<ul>
  <li><b>Stale:</b> the quote is several days old. Prices may have moved.</li>
  <li><b>Closed:</b> the market does not open (or does not report) on the day your truck arrives.</li>
  <li><b>Wrong variety:</b> the market is open but nobody is buying your exact variety/grade.</li>
</ul>
<p>In live checks on 17 November 2026 (Exp 8), <b>11 of 22</b> benchmark corridors had no reported price at all for the previous 7 days.</p>

<h2>Idea 6 &mdash; Average is not enough: loss rate and the worst 10%</h2>
<p>Two plans can have the same average but very different risk. So we use four simple <b>metrics</b>:</p>
<table>
<tr><th>Metric</th><th>Simple meaning</th></tr>
<tr><td><b>Mean Net Gain</b> (&#8377;/qtl)</td><td>Average extra money per quintal over all opportunities (a &ldquo;stay home&rdquo; day counts as &#8377;0).</td></tr>
<tr><td><b>Loss-Trip Rate (LTR)</b></td><td>Of the trucks that were actually sent, what % lost money.</td></tr>
<tr><td><b>Worst-10% Loss (CVaR<sub>10%</sub>)</b></td><td>Take the worst 10% of outcomes and average them. It tells you how bad the bad days are.</td></tr>
<tr><td><b>Live API calls per query</b></td><td>How many external look-ups (roads, weather, model) we needed &mdash; a measure of cost and effort.</td></tr>
</table>
<div class="box think"><span class="t">Illustration: why worst-10% matters</span>
Plan X over 10 trips: +500, +500, +500, +500, +500, +500, +500, +500, +500, &minus;1,500 &rarr; average +300, worst-10% = &minus;1,500.<br/>
Plan Y over 10 trips: +300 every time &rarr; average +300, worst-10% = +300.<br/>
Same average, but a poor farmer would prefer Plan Y. This is why we never judge a plan only by its average.</div>

<h2>Idea 7 &mdash; Every prediction has errors, so keep a safety cushion</h2>
<p>A machine-learning model predicts the arrival price, but it is sometimes too optimistic. Instead of trusting the raw prediction,
we look at how wrong the model was on <b>recent, already-finished trips</b>, and subtract a cushion large enough to cover most of those errors.</p>
<div class="box think"><span class="t">Illustration: the 80% cushion</span>
Suppose on the last 10 finished trips the model over-predicted by 1%, 2%, 2%, 3%, 4%, 5%, 6%, 8%, 11%, 15%.
The value that 80% of errors stay below is about <b>8%</b>. So we subtract 8% from the next prediction. If the model&rsquo;s errors
behave like the past, about 4 out of 5 future trips should come in at or above this cautious estimate.</div>
<p>This idea is called <b>conformal prediction</b> (Angelopoulos &amp; Bates, 2023). In MandiGuard the cushion is recomputed from a rolling
window of the last 400 matured trips, using only trips whose arrival date has already passed. We checked it on new data: the cushion
covered <b>78.85%</b> of validation outcomes and <b>79.07%</b> of holdout outcomes &mdash; very close to the 80% target.</p>

<h2>Idea 8 &mdash; Saying &ldquo;No&rdquo; is a valid decision (the reject option)</h2>
<p>In 1970, C. K. Chow proved that when a wrong decision costs much more than not deciding, the best system should sometimes
<b>abstain</b>. For a farmer, a bad trip loses diesel, produce and time, while staying home costs nothing extra.
So MandiGuard has an explicit output: <b>REFUSE_PHANTOM_SPREAD</b> (sell locally).</p>

<h2>Idea 9 &mdash; Ask cheap questions first (the cascade)</h2>
<div class="box think"><span class="t">Analogy: a doctor</span>
A doctor first asks simple questions and checks temperature (cheap), and orders an MRI (expensive) only if needed.
MandiGuard does the same: first check &ldquo;is the market alive for my variety?&rdquo; (cheap), and only then fetch roads, weather and the model.</div>

<h2>Idea 10 &mdash; Fair testing: practice paper, mock test, board exam</h2>
<p>We split time into three parts, like exam preparation:</p>
<div class="timeline">
  <div style="flex:3; background:#dbeafe;"><b>2024 = Practice</b><br/>train the price model</div>
  <div style="flex:1.4; background:#fef9c3;"><b>Jan&ndash;May 2025 = Mock test</b><br/>choose settings (&#8377;50 margin)</div>
  <div style="flex:0.25; background:#0b3b5c; color:#fff;"><b>WALL</b></div>
  <div style="flex:2.6; background:#dcfce7;"><b>Jun 2025&ndash;Apr 2026 = Board exam</b><br/>final test, never used for tuning</div>
</div>
<p><b>Leakage</b> means accidentally using information from the future (like seeing the board exam answers while practising).
We built a &ldquo;firewall&rdquo; so the model can only use information available on the decision morning.</p>

<h2>Idea 11 &mdash; Is a difference real or luck? (bootstrap, p-value, Holm)</h2>
<ul>
  <li><b>Bootstrap:</b> re-draw the data many times (5,000 times) with replacement and see how much the result wobbles.
  We re-draw whole <b>origin mandis (174)</b> and whole <b>2-week blocks (23)</b>, because days in the same market or same fortnight
  are related &mdash; treating them as independent would make us over-confident.</li>
  <li><b>p-value:</b> roughly, how often a difference this large could appear just by chance if there were no real effect.
  Small (e.g., below 0.05) = probably real.</li>
  <li><b>Holm&ndash;Bonferroni:</b> when you test four hypotheses, the chance of one lucky &ldquo;win&rdquo; increases, so Holm makes the
  threshold stricter.</li>
</ul>

<h2>Idea 12 &mdash; Pre-registration: write your predictions before seeing results</h2>
<p>Before looking at the final test months, we wrote down four hypotheses (H1&ndash;H4) and saved them in Git (commit <code>e421d15</code>).
This prevents <b>HARKing</b> (&ldquo;Hypothesising After the Results are Known&rdquo;) &mdash; changing the story after seeing the data.
Anything we discovered later is clearly labelled <b>Stage II, post-diagnostic</b>.</p>
"""

CH3 = """
<div class="pb"></div>
<h1>Chapter 3 &mdash; The Big Picture: One Flowchart That Connects Every Dot</h1>
<p>Read this page as the &ldquo;map&rdquo; of the whole thesis. Every later chapter zooms into one box.</p>

<h3>Part A &mdash; From a real-world problem to a research question</h3>
""" + hflow([
    ("Problem", "Farmers chase screen prices", "c4"),
    ("Evidence", "Exp 1: 40.46% of trucks lose money", "c4"),
    ("Gap", "Papers predict prices; none verify execution + allow refusal", "c3"),
    ("Question", "Can a verify-first, refuse-when-risky rule do better?", "c5"),
]) + """
<h3>Part B &mdash; Data and its validation</h3>
""" + hflow([
    ("Collect", "Prices, roads, weather, govt rules", "c1"),
    ("Clean", "Remove bad rows, duplicates; fix names", "c1"),
    ("Validate", "Exp 14: official parity 100% Min/Max", "c2"),
    ("Build episodes", "69,526 test opportunities", "c1"),
    ("Firewall", "Train 2024 / Val H1-2025 / Test", "c6"),
]) + """
<h3>Part C &mdash; Stage I (pre-registered) method and testing</h3>
""" + hflow([
    ("Step 0", "Shortlist up to 5 markets", "c1"),
    ("T1", "Market alive for my variety?", "c2"),
    ("T2", "Freight + fee covered?", "c2"),
    ("T3", "Heat/rain rot OK?", "c2"),
    ("T4", "Model + 80% cushion > &#8377;50?", "c2"),
    ("Decide", "DISPATCH or REFUSE", "c5"),
]) + hflow([
    ("Compare", "vs B0&ndash;B6 baselines", "c6"),
    ("Pre-registered tests", "H1, H3, H4 supported; H2 not", "c3"),
    ("Robustness", "Ablation, budget, apples, 10 years, penalties", "c6"),
]) + """
<h3>Part D &mdash; Stage II (post-diagnostic): learn from what did not work</h3>
""" + hflow([
    ("Weakness", "Tied B2 on average; missed Apple trades", "c4"),
    ("Autopsy (Exp 16)", "3 causes found", "c3"),
    ("Fix (Exp 17)", "MandiGuard-CRC", "c5"),
    ("Calibrate on Val only", "&lambda;* = 0.15", "c6"),
    ("Test on unseen months", "&#8377;479.17/qtl; +&#8377;32.51 vs B2", "c2"),
]) + """
<h3>Part E &mdash; Honest closing</h3>
""" + hflow([
    ("Limitations", "Freight, rot, penalties are modelled", "c4"),
    ("Contributions", "Measurement + method + autopsy + fix", "c2"),
    ("Future", "Field pilots with real receipts", "c1"),
]) + """
<div class="box key"><span class="t">The single logical chain (memorise this)</span>
Screen prices mislead &rarr; we <b>measured</b> how much (Exp 1) &rarr; existing work predicts prices but does not check whether
you can actually sell &rarr; we built a <b>verify-first checklist with a safety cushion and a stay-home option</b> (Stage I) &rarr;
we tested it fairly on months it had never seen, with hypotheses written in advance &rarr; it beat naive chasing and point-ML,
but only tied a strong simple rule on average &rarr; we <b>investigated why</b> (Stage II autopsy) &rarr; fixed three causes &rarr;
the fix beat the strong rule on unseen data &rarr; we clearly state what is still assumed rather than measured.</div>

<h2>3.1 Research questions you can put on the synopsis slide</h2>
<table>
<tr><th style="width:9%">RQ</th><th>Question</th><th style="width:28%">Answered by</th></tr>
<tr><td>RQ1</td><td>How much of the cross-mandi screen spread disappears after closed markets, variety mismatch, freight, fees and spoilage?</td><td>Exp 1, Exp 10 (measurement)</td></tr>
<tr><td>RQ2</td><td>Can a transparent verify-first cascade with a safety cushion and a refuse option raise net gain and reduce loss trips compared with naive and point-ML baselines?</td><td>H1, H3 (Exp 2), robustness Exp 4&ndash;10, 15</td></tr>
<tr><td>RQ3</td><td>Can it reach the same quality using fewer external checks?</td><td>H4, Exp 5 (budget)</td></tr>
<tr><td>RQ4</td><td>Why did Stage I fail to beat the strong fresh-road rule (B2) on average, and does fixing those causes help on unseen data?</td><td>Exp 16 (autopsy), Exp 17 (MandiGuard-CRC)</td></tr>
</table>
"""

CH4 = """
<div class="pb"></div>
<h1>Chapter 4 &mdash; Data Collection: Where Every Number Came From</h1>
<p>Golden rule of this project: <b>no invented price data</b>. Prices, roads and weather come from public sources; cost parameters come
from government publications. Anything we had to assume (like truck hire rates) is clearly labelled as <i>modelled</i>.</p>

<h2>4.1 The six data sources</h2>
<table>
<tr><th style="width:20%">Source</th><th>What it gives</th><th style="width:30%">Size / coverage</th></tr>
<tr><td><b>AGMARKNET</b> (Govt of India price portal, via public archive mirror)</td><td>Daily Min/Max/Modal price per market, crop, variety</td><td>42,722,187 raw records (2017&ndash;2026) &rarr; 883,406 rows for our 178-mandi panel</td></tr>
<tr><td><b>HP Apple graded data</b> (AGMARKNET 2.0 export)</td><td>Apple prices separated by grade (A, B, C, &hellip;)</td><td>4,427 records, 42 markets; 1,537 test lots</td></tr>
<tr><td><b>OpenStreetMap + OSRM</b> (road router)</td><td>Real road distance and driving time between markets</td><td>8,147 directed corridors (15&ndash;500 km)</td></tr>
<tr><td><b>ERA5</b> (European reanalysis) and <b>NASA POWER</b></td><td>Actual temperature, rain, humidity on the road</td><td>ERA5: 141,955 rows, 145 grid cells (2024&ndash;26); NASA: 291,384 rows, 114 cells (2017&ndash;23); 0% missing</td></tr>
<tr><td><b>Open-Meteo forecasts</b> (NWP)</td><td>What the farmer could know on the morning (forecast, not actual)</td><td>102 of 145 cells archived; rest filled by a causal Ridge model (MAE 1.047&deg;C)</td></tr>
<tr><td><b>Government reports</b></td><td>Spoilage rates (NABCONS 2022), state fees (PIB), hill roads (GoHP 2025&ndash;26), truck size and income (NSS 587)</td><td>Fixed parameters, all cited</td></tr>
</table>

<h2>4.2 Step-by-step: from 14 million rows to a clean 178-mandi panel</h2>
""" + hflow([
    ("Stream", "14,443,770 records (2024&ndash;Apr 2026)", "c1"),
    ("Filter", "6 states &times; 4 crops = 681,258 rows", "c1"),
    ("Clean", "Remove 284 bad prices + 7,003 duplicates", "c3"),
    ("Clean result", "673,971 records, 699 markets", "c2"),
]) + hflow([
    ("Eligibility", "&ge; 20 trading days in 2024 and &ge; 80 total (469 markets)", "c3"),
    ("Select using 2024 only", "Top 30 per state by 2024 activity", "c5"),
    ("Fixed panel", "178 mandis, 260,043 daily records", "c2"),
]) + """
<div class="box think"><span class="t">Why choose markets using only 2024?</span>
If we chose markets because they traded a lot in 2025&ndash;26 (the test period), we would be quietly using the future &mdash;
markets that later shut down would be excluded, making results look better. This mistake is called <b>survivorship bias</b>.
Choosing with 2024 data only keeps the test honest.</div>
<p>We also <b>harmonised names</b>: generic clerk labels (e.g., &ldquo;Other&rdquo;, &ldquo;FAQ&rdquo;) became &ldquo;Standard&rdquo;; spelling
variants were unified (Deshi &rarr; Desi); but real commercial varieties (Red, Hybrid, Royal Delicious, &hellip;) were kept separate,
because variety mismatch is one of the traps we study.</p>

<h2>4.3 Placing markets on the map and measuring roads</h2>
""" + hflow([
    ("Market names", "220 (state, district, market) tuples", "c1"),
    ("Geocode with district check", "must lie &le; 110 km from district HQ", "c3"),
    ("Coordinates", "150 exact, 70 district-centre fall-backs", "c2"),
    ("OSRM roads", "8,147 corridors, 15&ndash;500 km", "c1"),
    ("Arrival lag", "1 day: 3,810 | 2 days: 3,942 | 3 days: 395", "c5"),
]) + """
<p>Why the district check? Many Indian villages share names across states. Without the check, a market could be placed hundreds of km away.
The arrival lag (1, 2 or 3 days) comes from driving time &times; 1.35 for trucks (plus hill adjustment in HP) plus 4 hours for loading and auction timing.</p>

<h2>4.4 Weather: what you knew vs what actually happened</h2>
<p>A subtle but important point: on the dispatch morning, the farmer only has a <b>forecast</b>. The truck, however, experiences the
<b>actual</b> weather. So we use forecasts to <b>make</b> decisions and actual weather (ERA5/NASA) to <b>score</b> what really happened.
Mixing them would be leakage.</p>

<h2>4.5 Government parameters (all cited)</h2>
<table>
<tr><th>State</th><th>Fruit &amp; vegetable fee rule (PIB 154554)</th><th class="num">Fee used</th></tr>
<tr><td>Gujarat</td><td>Market fee exempted; user fee allowed</td><td class="num">0.5%</td></tr>
<tr><td>Himachal Pradesh</td><td>Exempt except Apple</td><td class="num">0.5% veg / 1.0% apple</td></tr>
<tr><td>Karnataka</td><td>Zero market fee on F&amp;V; user fee only</td><td class="num">0.5%</td></tr>
<tr><td>Madhya Pradesh</td><td>Regulated inside notified yards</td><td class="num">1.5%</td></tr>
<tr><td>Maharashtra</td><td>Deregulated outside yards; supervision inside</td><td class="num">1.0%</td></tr>
<tr><td>Uttar Pradesh</td><td>Regulated (UP Krishi Utpadan Mandi Adhiniyam)</td><td class="num">1.5%</td></tr>
</table>
<p>Other anchors: NABCONS 2022 market-stage losses (Tomato 3.25%, Onion 1.96%, Apple 1.64%, Potato 0.86%);
30-quintal reference truck and &#8377;3,798/month income (NSS 587); 1.45&times; hill freight from 91.59% single-lane HP roads.</p>
"""

CH5 = """
<div class="pb"></div>
<h1>Chapter 5 &mdash; Data Validation: How We Proved the Data Is Trustworthy</h1>
<p>An examiner will ask: <i>&ldquo;Your bulk prices came from an archive mirror. How do you know they match the government?&rdquo;</i>
This chapter is your answer. Validation happened in <b>five layers</b>.</p>

""" + hflow([
    ("Layer 1", "Clean: bad prices, duplicates, names", "c1"),
    ("Layer 2", "Official parity checks (Exp 14)", "c2"),
    ("Layer 3", "Location &amp; weather sanity", "c3"),
    ("Layer 4", "No-future-leakage firewall", "c5"),
    ("Layer 5", "22 automated tests + independent reviewers", "c6"),
]) + """

<h2>5.1 Layer 2 &mdash; Comparing our copy with official government data (Exp 14)</h2>
<table>
<tr><th>Check</th><th>What was compared</th><th class="num">Matched keys</th><th class="num">Min</th><th class="num">Max</th><th class="num">Modal</th></tr>
<tr><td><b>Tier 1</b>: data.gov.in official XML (18 Oct 2023)</td><td>6,434 all-India rows &rarr; 532 in our states/crops &rarr; 181 in our panel</td><td class="num">172</td><td class="num">100%</td><td class="num">100%</td><td class="num">99.42%</td></tr>
<tr><td><b>Tier 2</b>: AGMARKNET 2.0 official export (149 trading days)</td><td>4,427 HP Apple rows &rarr; 2,082 inside the mirror&rsquo;s date window</td><td class="num">2,042</td><td class="num">100%</td><td class="num">100%</td><td class="num">100%</td></tr>
</table>
<div class="box key"><span class="t">How to explain it</span>
&ldquo;We took the same market, date, variety and grade from the official government source and from our copy, and compared the rupee values.
On 172 keys from a single official day, Min and Max matched exactly and Modal matched 171 of 172. On 2,042 keys spread over 149 days,
all three prices matched exactly.&rdquo; Be honest that this is a strong <b>sample</b> check, not a full re-download of all years.</div>

<h2>5.2 Layer 3 &mdash; Location and weather sanity</h2>
<ul>
  <li>Every market coordinate must be within 110 km of its district headquarters (catches same-name villages).</li>
  <li>Weather grids: 0.0% missing values for ERA5 (2024&ndash;26) and NASA POWER (2017&ndash;23).</li>
  <li>Forecast filler (Ridge model) was trained only on 2024 and tested on Jan&ndash;May 2025: average temperature error 1.047&deg;C.</li>
  <li>An extra check on the 42,766 episodes from the 4 states with 100% real archived forecasts confirmed the filler did not distort results.</li>
</ul>

<h2>5.3 Layer 4 &mdash; The &ldquo;no peeking&rdquo; firewall</h2>
<ul>
  <li>The price model is trained on 2024 only and then <b>frozen</b>.</li>
  <li>The safety cushion only learns from trips whose <b>arrival date has already passed</b> on the decision morning.</li>
  <li>Validation (Jan&ndash;May 2025) is only used to choose settings; we also require arrival dates &le; 31 May 2025 so no validation outcome leaks into June.</li>
  <li>The code contains an automatic check (<code>assert_no_future_leakage_dates</code>) that stops the program if training dates overlap later periods.</li>
</ul>

<h2>5.4 Layer 5 &mdash; Software tests and independent review</h2>
<p><b>22 out of 22</b> automated tests pass. They check: file checksums (SHA-256), split dates, no-leakage rules, fee and spoilage parameters,
bootstrap and Holm arithmetic, and that every result file and figure exists and is consistent. Two independent review agents audited the code,
data, results, paper and viva material over three rounds until both returned <b>PASS</b>.</p>
<div class="box warn"><span class="t">Do not over-claim</span>
Tests prove the code is <b>correct and reproducible</b>. They do <b>not</b> prove real-world truck costs or rot rates &mdash; those are
modelled from government averages and still need field receipts.</div>
"""

CH6 = """
<div class="pb"></div>
<h1>Chapter 6 &mdash; Building Fair Test Questions: Episodes and Time Splits</h1>

<h2>6.1 What is an &ldquo;episode&rdquo;?</h2>
<p>An <b>episode</b> = one farmer, at one origin market, with one crop/variety, on one morning, deciding whether to send a truck,
and if yes, to which of the shortlisted destination markets. Each episode is like one exam question. Because history recorded what
prices actually were on the arrival days, we can <b>score</b> every decision afterwards.</p>
""" + hflow([
    ("Morning t", "Farmer at origin, local price known", "c1"),
    ("Step 0", "Up to 5 destinations, 15&ndash;500 km, screen gap &gt; &#8377;100", "c1"),
    ("Decision", "Send to market j, or stay home", "c5"),
    ("Arrival t+&tau;", "Look up real price on arrival days", "c3"),
    ("Score", "Net gain, loss?, trap?", "c2"),
]) + """
<h2>6.2 How a real outcome is scored (the three arrival situations)</h2>
<table>
<tr><th>Situation on arrival</th><th>What we assume happens</th><th>Label</th></tr>
<tr><td>Market open and buying your exact variety on arrival day</td><td>Sell at that day&rsquo;s real modal price</td><td>Clean sale</td></tr>
<tr><td>Not buying your variety today, but does within 1&ndash;2 days</td><td>Wait (&#8377;25/qtl/day) and extra rot, then sell</td><td>Delay trap</td></tr>
<tr><td>Variety never trades in 3 days</td><td>Sell another variety at Min price &minus;10%, or if the crop is absent, pay 1.5&times; return freight + rot</td><td>Closed trap</td></tr>
</table>
<p>The last row uses <b>modelled</b> penalties (we cannot observe what a real farmer would have done). That is why Exp 15 tests what
happens if these penalties are much smaller or even zero (Chapter 9).</p>

<h2>6.3 The three time zones</h2>
<div class="timeline">
  <div style="flex:3; background:#dbeafe;"><b>Train_2024</b><br/>701,932 corridor rows<br/>fit model (Jan&ndash;Sep), first cushion (Oct&ndash;Dec)</div>
  <div style="flex:1.6; background:#fef9c3;"><b>Val_2025H1</b><br/>42,794 episodes<br/>pick &#8377;50 margin; coverage 78.85%</div>
  <div style="flex:0.3; background:#0b3b5c; color:#fff;"><b>Pre-reg wall</b></div>
  <div style="flex:2.8; background:#dcfce7;"><b>Holdout Jun 2025&ndash;Apr 2026</b><br/>69,526 shortlisted episodes<br/>final scoring only</div>
</div>
<ul>
  <li>The <b>&#8377;50 safety margin</b> was chosen from {50, 100, 150, 200, 250} using validation data only (validation mean &#8377;351.36/qtl).</li>
  <li>During the holdout, the cushion keeps updating, but only from trips that have already arrived &mdash; exactly what a real app could do.</li>
</ul>
"""

CH7 = """
<div class="pb"></div>
<h1>Chapter 7 &mdash; Stage I Method: MandiGuard Step by Step</h1>
<p>MandiGuard is <b>not</b> a chatbot or a self-learning robot. It is a <b>deterministic checklist</b> (same input &rarr; same output)
plus <b>one frozen tree model</b> and a <b>safety cushion</b>. There is no large language model and no reinforcement learning inside it.</p>

<h2>7.1 The decision flowchart (for each shortlisted market)</h2>
""" + vgate(
    [
        ("Step 0 &mdash; Free shortlist (0 calls)",
         "Up to 5 markets within 15&ndash;500 km whose 7-day screen price beats local by &gt; &#8377;100/qtl",
         "No candidate &rarr; SELL LOCAL"),
        ("T1 &mdash; Is the market alive for my exact variety? (1 call)",
         "Quote &le; 3 days old AND reported on &ge; 50% of last 14 days AND open on &ge; 35% of past same-weekdays",
         "Reject this market (stale / closed / wrong variety)"),
        ("T2 &mdash; Do roads + fees still leave profit? (+1 call)",
         "Real OSRM km/hours, freight &#8377;35 + &#8377;0.45/km (&times;1.45 in HP), state fee",
         "Reject (spread eaten by freight)"),
        ("T3 &mdash; Will heat/rain rot eat the gain? (+1 call)",
         "Morning forecast &rarr; Q10 spoilage + rain penalty; gain must stay &gt; 0",
         "Reject (spoilage risk)"),
        ("T4 &mdash; Cautious profit after the 80% cushion (+1 call)",
         "Frozen 2024 tree model predicts arrival return; subtract recent 80th-percentile error",
         "Reject (not safe enough)"),
    ],
    "Pick the surviving market with the highest cautious profit. If it is &gt; &#8377;50/qtl &rarr; DISPATCH",
    "REFUSE_PHANTOM_SPREAD (sell locally, &#8377;0 change)",
) + """
<div class="box think"><span class="t">Why this order?</span>
T1 is the cheapest check and removes the biggest danger (closed / wrong-variety markets). Removing T1 in testing made traps jump to
67.16% and cut average gain by &#8377;134.05/qtl. So it makes sense to ask it first and avoid paying for road, weather and model look-ups
on markets that are already dead.</div>

<h2>7.2 The tree model in simple words</h2>
<p>The model is a <b>HistGradientBoostingRegressor</b> &mdash; many small decision trees added together, each correcting the previous ones&rsquo; mistakes.
It predicts the <b>arrival return</b> = (arrival price &minus; reference price) / reference price, using <b>17 causal features</b> such as recent price
changes, volatility, how often the market reports, and calendar effects. &ldquo;Causal&rdquo; here means each feature only uses information available
on or before the decision morning. It was trained on 2024 and then frozen.</p>

<h2>7.3 Worked example 1 &mdash; one Tomato trip through the maths (from the thesis)</h2>
<div class="box math"><span class="t">Madhya Pradesh, 40&deg;C May afternoon, 200 km (6 hours), local &#8377;1,400, screen &#8377;2,000</span>
<span class="formula">1. Screen price                                   &#8377;2,000.00
2. Heat spoilage: 3.25% &times; (6/24) &times; 4 = 3.25%    &minus; &#8377;65.00   &rarr; &#8377;1,935.00
3. Freight &#8377;35 + 0.45&times;200 = &#8377;125; MP fee 1.5%&times;1,400 = &#8377;21
                                                 &minus; &#8377;146.00  &rarr; &#8377;1,789.00
4. 80% cushion: 8% &times; &#8377;1,935                  &minus; &#8377;154.80  &rarr; &#8377;1,634.20
5. Minus home price                              &minus; &#8377;1,400.00
   Cautious net gain                             = +&#8377;234.20 per quintal (+&#8377;7,026 on 30 qtl)</span>
Since +&#8377;234.20 &gt; &#8377;50 safety margin &rarr; <b>DISPATCH</b>. If T1 had found the variety not traded for 5 days, or T3 had found 40 mm rain,
the answer would be <b>REFUSE</b> and the farmer keeps &#8377;0 change instead of risking a loss.</div>

<h2>7.4 Worked example 2 &mdash; how the cascade saves look-ups (Illustration)</h2>
<table>
<tr><th>Market</th><th>What happens</th><th class="num">Calls used</th></tr>
<tr><td>A</td><td>T1 fails: quote is 5 days old</td><td class="num">1</td></tr>
<tr><td>B</td><td>T1 fails: market usually closed on arrival weekday</td><td class="num">1</td></tr>
<tr><td>C</td><td>Passes T1; T2 fails: freight eats the spread</td><td class="num">2</td></tr>
<tr><td>D</td><td>Passes T1, T2; T3 fails: heavy rain forecast</td><td class="num">3</td></tr>
<tr class="hl"><td>E</td><td>Passes all four checks; cautious gain +&#8377;234.20 &gt; &#8377;50 &rarr; DISPATCH to E</td><td class="num">4</td></tr>
<tr><td colspan="2"><b>Total</b> (MandiGuard) vs checking all 4 tools on all 5 markets (B4 = 20 calls)</td><td class="num"><b>11 vs 20</b></td></tr>
</table>
<p>On the real holdout, MandiGuard averaged <b>8.75 calls</b> vs <b>15.74</b> for &ldquo;check everything&rdquo; (B4) &mdash; 44.4% fewer &mdash; with identical profit.</p>
"""

CH8 = """
<div class="pb"></div>
<h1>Chapter 8 &mdash; Fair Testing: Baselines, Hypotheses and Statistics</h1>

<h2>8.1 Who did we compare against? (baselines)</h2>
<p>A result only means something when compared with sensible alternatives. We used seven comparators:</p>
<table>
<tr><th style="width:24%">Baseline</th><th>What it does</th><th style="width:28%">Why include it</th></tr>
<tr><td><b>B0</b> Sell local</td><td>Never sends a truck</td><td>Zero-risk reference (&#8377;0)</td></tr>
<tr><td><b>B1</b> Naive screen chasing</td><td>Highest screen price minus straight-line freight &gt; &#8377;100</td><td>What many farmers would do</td></tr>
<tr><td><b>B2</b> Fresh + road rule</td><td>Needs a same-day exact-variety quote, real road freight and fees &gt; &#8377;100</td><td>A <b>strong simple</b> rule &mdash; hard to beat</td></tr>
<tr><td><b>B3</b> Point-ML</td><td>Uses ML average prediction + road freight, no T1/T3/cushion</td><td>Like typical price-forecasting apps</td></tr>
<tr><td><b>B4</b> Check everything upfront</td><td>Calls all 4 tools on every candidate</td><td>Tests if the ordered cascade saves effort</td></tr>
<tr><td><b>B5</b> Multi-agent buckets</td><td>Roles talk in coarse LOW/MED/HIGH buckets</td><td>Tests if exact rupee values matter</td></tr>
<tr><td><b>B6</b> Rule-of-thumb router</td><td>Fixed thresholds and a flat 12% weather cut</td><td>Tests a rigid heuristic</td></tr>
</table>

<h2>8.2 The four pre-registered hypotheses (written before seeing the test data)</h2>
<table>
<tr><th>ID</th><th>Hypothesis in plain words</th></tr>
<tr><td><b>H1</b></td><td>MandiGuard earns more on average than naive screen chasing (B1).</td></tr>
<tr><td><b>H2</b></td><td>MandiGuard earns more on average than the fresh + road rule (B2).</td></tr>
<tr><td><b>H3</b></td><td>MandiGuard causes fewer loss episodes than point-ML (B3).</td></tr>
<tr><td><b>H4</b></td><td>MandiGuard needs at least 25% fewer external calls than checking everything (B4).</td></tr>
</table>

<h2>8.3 How we decided if a difference is real</h2>
""" + hflow([
    ("Pair the policies", "Same 69,526 episodes for all", "c1"),
    ("Two-way cluster bootstrap", "174 mandis &times; 23 two-week blocks, 5,000 redraws", "c5"),
    ("Exact p-value", "Phipson&ndash;Smyth (never zero)", "c3"),
    ("Holm correction", "4 tests, family error 5%", "c2"),
]) + """
<div class="box think"><span class="t">Why &ldquo;paired&rdquo; and &ldquo;clustered&rdquo;?</span>
<b>Paired</b>: every policy faces exactly the same farmers on the same mornings, so differences come from the decisions, not from luck in which days were picked.
<b>Clustered</b>: days in the same market and the same fortnight move together (a festival or a strike affects all of them). Re-drawing whole
markets and whole fortnights gives honest, wider confidence intervals.</div>
"""

CH9 = """
<div class="pb"></div>
<h1>Chapter 9 &mdash; Stage I Results and Robustness</h1>

<h2>9.1 The main result table (holdout, 69,526 episodes)</h2>
<table>
<tr><th>Policy</th><th class="num">Dispatch</th><th class="num">Mean gain &#8377;/qtl</th><th class="num">Per 30-qtl truck</th><th class="num">Loss-trip rate</th><th class="num">Worst-10%</th><th class="num">Calls</th></tr>
<tr><td>B1 Naive screen</td><td class="num">90.67%</td><td class="num">350.01</td><td class="num">&#8377;10,500</td><td class="num">40.46%</td><td class="num">&minus;1,062.66</td><td class="num">0.00</td></tr>
<tr><td>B2 Fresh + road</td><td class="num">62.11%</td><td class="num">446.66</td><td class="num">&#8377;13,400</td><td class="num">18.11%</td><td class="num">&minus;436.67</td><td class="num">7.87</td></tr>
<tr><td>B3 Point-ML</td><td class="num">93.05%</td><td class="num">330.85</td><td class="num">&#8377;9,926</td><td class="num">45.28%</td><td class="num">&minus;1,097.80</td><td class="num">7.87</td></tr>
<tr><td>B4 Check everything</td><td class="num">48.66%</td><td class="num">452.79</td><td class="num">&#8377;13,584</td><td class="num">9.97%</td><td class="num">&minus;37.89</td><td class="num">15.74</td></tr>
<tr class="hl"><td>MandiGuard (Stage I)</td><td class="num">48.66%</td><td class="num">452.79</td><td class="num">&#8377;13,584</td><td class="num">9.97%</td><td class="num">&minus;37.89</td><td class="num">8.75</td></tr>
</table>

<h2>9.2 Hypothesis verdicts</h2>
<table>
<tr><th>ID</th><th class="num">Estimate</th><th class="num">95% interval</th><th class="num">Holm p</th><th>Verdict</th></tr>
<tr><td>H1 vs B1 (mean)</td><td class="num">+&#8377;102.78/qtl</td><td class="num">[+48.66, +153.45]</td><td class="num">0.0012</td><td><b>Supported</b></td></tr>
<tr><td>H2 vs B2 (mean)</td><td class="num">+&#8377;6.13/qtl</td><td class="num">[&minus;17.02, +25.02]</td><td class="num">0.2699</td><td><b>Not supported</b></td></tr>
<tr><td>H3 vs B3 (loss episodes)</td><td class="num">&minus;37.29 points</td><td class="num">[&minus;40.19, &minus;34.24]</td><td class="num">0.0008</td><td><b>Supported</b></td></tr>
<tr><td>H4 vs B4 (calls)</td><td class="num">8.75 vs 15.74</td><td class="num">&mdash;</td><td class="num">0.0008</td><td><b>Supported</b></td></tr>
</table>
<div class="box viva"><span class="t">How to explain H2 honestly (examiners love this)</span>
&ldquo;H2 was not supported: +&#8377;6.13 is within noise. MandiGuard does not win on <i>average</i> against the strong fresh-road rule;
it wins on <i>safety</i>: it sends fewer trucks (48.66% vs 62.11%), nearly halves loss trips (9.97% vs 18.11%) and cuts the worst-10% loss from
&minus;&#8377;436.67 to &minus;&#8377;37.89. I reported this as a failed hypothesis, and in Stage II I investigated why.&rdquo;</div>
<div class="figure"><img src="{FIG2}"/><div class="cap"><b>Figure 2 (thesis numbering).</b> Holdout comparison of all policies.</div></div>

<h2>9.3 Robustness: do the conclusions survive tough questions?</h2>
<table>
<tr><th style="width:26%">Tough question</th><th>Experiment and answer</th></tr>
<tr><td>Which check matters most?</td><td><b>Exp 4 ablation:</b> without T1, mean drops by &#8377;134.05 and traps rise to 67.16%; without T4, loss trips rise from 9.97% to 16.89%. T2 (+&#8377;0.44) and T3 (safer in extreme weather: loss rate 11.39% &rarr; 10.10%) matter less overall.</td></tr>
<tr><td>What if look-ups are limited?</td><td><b>Exp 5 budget:</b> with only 6 calls per query, MandiGuard earns &#8377;403.85 vs B4 &#8377;299.31 (+&#8377;104.54).</td></tr>
<tr><td>Does it work on graded apples?</td><td><b>Exp 3:</b> naive B1 hits 94.14% traps; MandiGuard cuts traps to 13.24% and worst-10% from &minus;&#8377;8,487.24 to &minus;&#8377;102.76, but its mean (&#8377;605.06) trails B2 (&#8377;1,150.83) &rarr; explained in Stage II.</td></tr>
<tr><td>Does it work in a state it never trained on?</td><td><b>Exp 9:</b> beats B1 in 6 of 6 unseen states.</td></tr>
<tr><td>What if freight or rot assumptions are wrong?</td><td><b>Exp 6:</b> across 9 freight &times; spoilage combinations, beats B1 in all 9 (+&#8377;82.62 to +&#8377;121.42).</td></tr>
<tr><td>What if trap penalties are smaller?</td><td><b>Exp 15:</b> still ahead of B1 until penalties are set to exactly zero (then &minus;&#8377;10.00 vs B1, but loss trips 6.09% vs 18.52%).</td></tr>
<tr><td>Only on markets guaranteed open?</td><td><b>Exp 15 matched (10,162 episodes):</b> beats B1 (+&#8377;38.38) and B2 (+&#8377;40.91); B3 earns more on average (&#8377;553.22) but with 2.2&times; the loss-trip rate and 10&times; deeper tail losses.</td></tr>
<tr><td>Does it hold over many years?</td><td><b>Exp 10:</b> 661,192 trips over six eras (2017&ndash;2026): loss-trip rate 8.78%&ndash;12.03% vs 39.18%&ndash;44.29% naive; +&#8377;165.14 over B1 in the 2024 heatwave.</td></tr>
</table>
<div class="figure"><img src="{FIG3}"/><div class="cap"><b>Figure 3.</b> Removing each check (ablation) and extreme heat/rain behaviour.</div></div>
"""

CH10 = """
<div class="pb"></div>
<h1>Chapter 10 &mdash; Stage II: The Honest Autopsy and MandiGuard-CRC</h1>
<div class="box warn"><span class="t">First, the most important rule</span>
Stage II was designed <b>after</b> seeing Stage I results, so it is labelled <b>[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]</b>.
Stage I stays frozen exactly as pre-registered. Stage II models are trained on 2024, tuned only on Jan&ndash;May 2025 validation, and then
evaluated once on the untouched holdout.</div>

<h2>10.1 Why do an autopsy?</h2>
<p>Two things bothered us: (1) Stage I tied the simple B2 rule on average (H2 failed), and (2) it missed many profitable Grade A apple trades.
Instead of hiding these, we asked <b>&ldquo;what exactly went wrong inside our own design?&rdquo;</b> (Exp 16).</p>

<h2>10.2 Finding 1 &mdash; Hiding closed days made risky trips look safe (censored arrivals)</h2>
<div class="box think"><span class="t">Analogy</span>
Judging how hard an exam was by looking only at students who turned up &mdash; the ones who stayed away (because they were unprepared)
are invisible, so the exam looks easier than it was.</div>
<p>The Stage I model was trained only on trips where the destination recorded a price on arrival (<code>dropna</code>). This removed <b>55.83%</b> of
raw 2024 corridors. But closed days are exactly the bad outcomes! As quotes get older, the chance that the market is open on arrival drops
(89.10% for fresh quotes &rarr; 62.63% for 3-day-old quotes in 2024). Ignoring the closed cases made the bad-day (20th percentile) drop look
up to <b>2.54&times; smaller</b> than it really was on holdout (&minus;10.55% vs true &minus;26.82%). Researchers call this the <b>selective labels</b>
problem (Lakkaraju et al., 2017).</p>

<h2>10.3 Finding 2 &mdash; One umbrella for all weather (coverage illusion)</h2>
<div class="box think"><span class="t">Analogy</span>
Carrying the same small umbrella in a drizzle and in a storm. On average you stay &ldquo;mostly dry&rdquo;, but you are over-protected in drizzle
and soaked in storms.</div>
<p>The 80% cushion was one size per crop. Overall it covered ~79%, which looked perfect. But splitting markets by how volatile they were:</p>
<table>
<tr><th>Market group (holdout)</th><th class="num">Coverage</th><th class="num">Cushion given</th><th class="num">Cushion needed (true 80th-pct error)</th></tr>
<tr><td>Calmest quarter (Q1)</td><td class="num">90.46%</td><td class="num">6.04%</td><td class="num">1.98%</td></tr>
<tr><td>Most volatile quarter (Q4)</td><td class="num">67.80%</td><td class="num">8.89%</td><td class="num">17.08%</td></tr>
</table>
<p>So calm markets got too much cushion (good trips refused) and volatile markets too little (risky trips allowed). Validation showed the same pattern
(88.91% vs 67.84%). Known in theory as <b>heteroscedasticity</b> (Lei et al., 2018; Romano et al., 2019).</p>

<h2>10.4 Finding 3 &mdash; Splitting apples into thin grades fooled T1</h2>
<p>When Himachal markets report Grade A and Grade B separately, each grade appears on fewer days, so T1&rsquo;s &ldquo;reported on &ge;50% of days&rdquo;
test thought the market was inactive. Among apple lots where B2 sent a truck but MandiGuard refused, <b>77.82%</b> (holdout) were blocked at T1,
not by the cushion (22.18%). We had first guessed the cushion was the problem &mdash; the autopsy corrected us.</p>
<div class="figure"><img src="{FIG8}"/><div class="cap"><b>Figure 8 (thesis numbering).</b> (A) Censored-arrival bias by quote age; (B) coverage by volatility quarter; (C) Stage II improvement ladder.</div></div>

<h2>10.5 The fix: MandiGuard-CRC, built one rung at a time</h2>
""" + hflow([
    ("Rung 0", "Stage I MandiGuard &#8377;452.79", "c6"),
    ("Rung 1", "Sort shortlist by gap minus 1.20&times; straight-line freight &#8377;455.15", "c1"),
    ("Rung 2", "Two models on full (uncensored) outcomes + risk penalty &#8377;469.29", "c5"),
    ("Rung 3 = MandiGuard-CRC", "Grade-aware T1 (fresh0) &#8377;479.17", "c2"),
]) + """
<ul>
  <li><b>Rung 1:</b> before choosing the top 5 markets, sort them by screen gap minus an estimated freight (&#8377;35 + &#8377;0.45 &times; 1.20 &times; straight-line km). Costs zero extra calls.</li>
  <li><b>Rung 2:</b> train two tree models on <b>all</b> 274,296 settled 2024 trips that passed T1 and looked profitable before costs &mdash; <i>including</i> closed and delayed outcomes:
  one predicts expected net gain (&mu;&#770;), the other predicts the probability of losing money (p&#770;<sub>loss</sub>).</li>
  <li><b>Rung 3:</b> &ldquo;fresh0&rdquo; rule &mdash; a same-day exact quote (age 0) can pass T1 with relaxed history (&ge;20% of last 14 days, &ge;25% same-weekday),
  alongside the normal strict rule. This rescues thinly reported grades.</li>
</ul>

<div class="box math"><span class="t">The CRC score</span>
<span class="formula">Score = &mu;&#770;  &minus;  &lambda; &times; (local price) &times; p&#770;_loss
DISPATCH only if Score &gt; &#8377;50 and &mu;&#770; &gt; &#8377;50</span>
<b>Example A (safe route):</b> &mu;&#770; = +&#8377;320, p&#770;<sub>loss</sub> = 0.08, local &#8377;1,400 &rarr; penalty 0.15 &times; 1,400 &times; 0.08 = &#8377;16.80 &rarr; Score +&#8377;303.20 &rarr; DISPATCH.<br/>
<b>Example B (stale volatile route):</b> &mu;&#770; = +&#8377;140, p&#770;<sub>loss</sub> = 0.55 &rarr; penalty 0.15 &times; 1,400 &times; 0.55 = &#8377;115.50 &rarr; Score +&#8377;24.50 &lt; &#8377;50 &rarr; REFUSE.
(These two are teaching illustrations of the formula.)</div>

<h2>10.6 How &lambda; (the risk weight) was chosen &mdash; validation only</h2>
<ol>
  <li>Try &lambda; = 0.00, 0.05, 0.10, &hellip;, 1.20 (25 values) on the Jan&ndash;May 2025 validation set (42,794 episodes).</li>
  <li>For each &lambda;, count dispatched trucks and loss trips. Compute (losses + 1) / (dispatches + 1).</li>
  <li>Stop at the <b>first</b> &lambda; where this ratio is &le; 0.095 (9.5%). Result: &lambda;* = <b>0.15</b> for MandiGuard-CRC (validation loss ratio 9.15%, mean &#8377;365.46); &lambda;* = 0.10 for Rung 2.</li>
  <li>Freeze &lambda; and evaluate once on the holdout.</li>
</ol>
<p>This calibration idea comes from <b>Conformal Risk Control</b> (Angelopoulos et al., 2024). We use it as a practical validation recipe and
<b>do not claim</b> its mathematical guarantee, because crop prices change across seasons (not &ldquo;exchangeable&rdquo;) and the number of dispatches changes with &lambda;.</p>

<h2>10.7 Stage II results on data it never saw</h2>
<table>
<tr><th>Test set</th><th class="num">MandiGuard-CRC</th><th>Comparison</th></tr>
<tr class="hl"><td>Holdout, 69,526 episodes</td><td class="num">&#8377;479.17/qtl (&#8377;14,375 per truck), loss trips 10.48%</td><td>+&#8377;129.16 vs B1 (p=0.0004); <b>+&#8377;32.51 vs B2</b> (95% CI +12.05 to +50.49, p=0.0016); +&#8377;26.38 vs Stage I (p=0.0002)</td></tr>
<tr><td>Guaranteed-open markets, 10,162 episodes (no modelled penalties)</td><td class="num">&#8377;533.75, loss trips 7.14%</td><td>+&#8377;22.86 vs Stage I, +&#8377;61.24 vs B1, +&#8377;63.76 vs B2; B3 still higher mean (&#8377;553.22) at 14.77% loss trips</td></tr>
<tr><td>HP graded apples, 1,537 lots</td><td class="num">&#8377;812.08 (+34.2% vs Stage I)</td><td>Grade A: &#8377;205.46 &rarr; &#8377;477.56, loss trips 20.0% &rarr; 11.54%; still below B2 (&#8377;1,150.83) but worst-10% &minus;&#8377;113.40 vs &minus;&#8377;272.50</td></tr>
</table>
<div class="box viva"><span class="t">Why Stage II is not overfitting (say this)</span>
&ldquo;The models were trained on 2024 only, the single setting &lambda; was chosen on validation only, and the holdout was used once.
We also checked the guaranteed-open subset with zero modelled penalties, so the gain is not just an artefact of how we scored closed markets.
And Stage I remains the pre-registered headline.&rdquo;</div>
"""

CH11 = """
<div class="pb"></div>
<h1>Chapter 11 &mdash; Relevant Papers, Explained Simply</h1>
<p>Our 37 references fall into six groups. For each group: what earlier researchers found, and how this thesis uses or extends it.</p>

<h2>Group 1 &mdash; Markets, information and farmers (economics)</h2>
<table>
<tr><th style="width:30%">Paper</th><th>What it found (simply)</th><th style="width:30%">How we use it</th></tr>
<tr><td>Jensen (2007), <i>Quarterly Journal of Economics</i></td><td>Mobile phones let Kerala fishermen choose better markets; prices became more equal and waste fell.</td><td>Classic success story &mdash; but fish markets at sea differ from inland mandis.</td></tr>
<tr><td>Goyal (2010), <i>AEJ: Applied</i></td><td>Internet kiosks for soybean in MP raised prices farmers received.</td><td>Information helps when selling is reliable.</td></tr>
<tr><td>Sekhar (2012), <i>Food Policy</i></td><td>Indian agricultural markets are only partly integrated.</td><td>Price gaps persist &rarr; temptation is real.</td></tr>
<tr><td>Chatterjee &amp; Kapur (2017), <i>India Policy Forum</i></td><td>Large price differences exist even between nearby districts.</td><td>Motivates measuring spreads.</td></tr>
<tr><td>Mitra et al. (2018), <i>Review of Economics &amp; Statistics</i></td><td>Telling potato farmers distant prices did not raise their farm-gate prices.</td><td><b>Key motivation:</b> information alone is not enough.</td></tr>
<tr><td>Negi et al. (2018), <i>Food Policy</i></td><td>Poor roads and communication push farmers to sell to local traders.</td><td>Transport friction matters.</td></tr>
<tr><td>Levi et al. (2020), <i>PNAS</i></td><td>Karnataka&rsquo;s unified market platform raised prices for some farmers.</td><td>Liquidity and grading matter (Finding 3).</td></tr>
<tr><td>Mahajan &amp; Tomar (2021), <i>AJAE</i></td><td>COVID lockdowns disrupted food supply chains in India.</td><td>Context for our 2020&ndash;21 era test.</td></tr>
</table>

<h2>Group 2 &mdash; Mandi price forecasting apps (closest prior work)</h2>
<table>
<tr><th style="width:30%">Paper</th><th>What it built</th><th style="width:30%">What it leaves open</th></tr>
<tr><td>Madaan et al. (2019), ACM COMPASS</td><td>Onion/potato price forecasts and anomaly alerts</td><td>No dispatch decision, closed markets or rot</td></tr>
<tr><td>Ma et al. (2019), ICTD</td><td>Interpretable price forecasts for small farmers</td><td>Forecast accuracy, not execution risk</td></tr>
<tr><td>Guo, Woodruff &amp; Yadav (2020), AAAI</td><td>CNN price prediction; non-trading days treated as noise</td><td>Closures removed, not modelled</td></tr>
<tr><td>Deka (2026), arXiv</td><td>Filling missing mandi prices statistically</td><td>Imputes gaps instead of flagging closed markets</td></tr>
<tr><td>Divyashree &amp; Biradar (2026), IJEDR &mdash; <i>AgriMarket AI</i></td><td>XGBoost market selection with straight-line distance</td><td>Closest baseline family (B1/B3); no variety, closure, rot or cushion</td></tr>
<tr><td>Manimegalai et al. (2026), IJRPR &mdash; <i>Mandi Cast</i></td><td>SARIMA/XGBoost forecasts with weather</td><td>Weather used for price, not transit spoilage or refusal</td></tr>
</table>

<h2>Group 3 &mdash; Saying &ldquo;no&rdquo; and safety cushions (machine learning theory)</h2>
<table>
<tr><th style="width:30%">Paper</th><th>Idea</th><th style="width:30%">Use in thesis</th></tr>
<tr><td>Chow (1970), IEEE Trans. Information Theory</td><td>Optimal trade-off between errors and abstaining</td><td>REFUSE_PHANTOM_SPREAD</td></tr>
<tr><td>Franc, Pr&#367;&scaron;a &amp; Vor&aacute;&#269;ek (2023), JMLR</td><td>Optimal strategies for reject-option classifiers</td><td>Why a good uncertainty score is needed</td></tr>
<tr><td>Angelopoulos &amp; Bates (2023), FnTML</td><td>Conformal prediction: cushions from past errors</td><td>The 80% cushion in T4</td></tr>
<tr><td>Lei et al. (2018), JASA</td><td>Distribution-free prediction intervals</td><td>Coverage theory; why one cushion can fail (Finding 2)</td></tr>
<tr><td>Romano, Patterson &amp; Cand&egrave;s (2019), NeurIPS</td><td>Conformalized quantile regression for uneven noise</td><td>Explains the coverage illusion</td></tr>
<tr><td>Gibbs &amp; Cand&egrave;s (2021), NeurIPS</td><td>Adaptive conformal inference under shift</td><td>Appendix experiment (ACI)</td></tr>
<tr><td>Angelopoulos et al. (2024), ICLR</td><td>Conformal Risk Control: tune a threshold to limit a loss</td><td>&lambda; calibration in MandiGuard-CRC (no theorem claimed)</td></tr>
<tr><td>Lakkaraju et al. (2017), KDD</td><td>Selective labels: outcomes missing for some decisions bias evaluation</td><td>Finding 1 (censored arrivals)</td></tr>
</table>

<h2>Group 4 &mdash; Asking for information step by step</h2>
<table>
<tr><th style="width:30%">Paper</th><th>Idea</th><th style="width:30%">Use in thesis</th></tr>
<tr><td>Kachuee et al. (2019), ICLR</td><td>Acquire costly features one at a time under a budget</td><td>Cheap-first cascade</td></tr>
<tr><td>Yao et al. (2023), ICLR &mdash; ReAct</td><td>Language models that reason and call tools</td><td>Tool grounding idea (we use no LLM)</td></tr>
<tr><td>Han, Buntine &amp; Shareghi (2024), ACL Findings &mdash; UALA</td><td>Uncertainty-aware agents call tools only when unsure</td><td>Uncertainty-gated checking</td></tr>
</table>

<h2>Group 5 &mdash; Statistics</h2>
<table>
<tr><td style="width:30%">Phipson &amp; Smyth (2010)</td><td>p-values from resampling should never be exactly zero; we use their formula.</td></tr>
<tr><td>Holm (1979)</td><td>Step-down correction when testing several hypotheses together.</td></tr>
</table>

<h2>Group 6 &mdash; Data and government sources</h2>
<table>
<tr><td style="width:30%">Hersbach et al. (2020) ERA5; Sparks (2018) NASA POWER</td><td>Gap-free daily weather grids.</td></tr>
<tr><td>Luxen &amp; Vetter (2011) OSRM</td><td>Fast real-road routing on OpenStreetMap.</td></tr>
<tr><td>NABCONS/MoFPI (2022); Jha et al. ICAR-CIPHET (2015)</td><td>National post-harvest loss surveys (spoilage rates).</td></tr>
<tr><td>PIB 154554 (APMC fees); PIB cold storage (2023); PIB 2086484 (e-NAM)</td><td>State fee rules and market infrastructure.</td></tr>
<tr><td>NSS Report 587 (2021); GoHP Economic Survey 2025&ndash;26</td><td>Truck size and farm income; hill road statistics.</td></tr>
</table>
<div class="box key"><span class="t">The research gap in one line</span>
Economics shows information alone does not help without reliable selling; computer science forecasts prices but treats closed days as noise and
uses straight-line distance; machine-learning theory offers abstention and cushions but had not been applied to this decision.
<b>This thesis joins the three</b> and measures the result on real Indian data.</div>
"""

CH12 = """
<div class="pb"></div>
<h1>Chapter 12 &mdash; What We Did Differently, and Limitations</h1>

<h2>12.1 Typical approach vs this thesis</h2>
<table>
<tr><th style="width:24%">Aspect</th><th>Typical mandi app / prior study</th><th>This thesis</th></tr>
<tr><td>Goal</td><td>Predict tomorrow&rsquo;s price</td><td>Decide: send the truck or stay home</td></tr>
<tr><td>Closed markets</td><td>Removed as noise or filled in</td><td>Checked first (T1) and studied as the main risk</td></tr>
<tr><td>Variety / grade</td><td>Often merged</td><td>Exact variety; grade-aware rule in Stage II</td></tr>
<tr><td>Distance</td><td>Straight line</td><td>Real roads (OSRM), hill multiplier</td></tr>
<tr><td>Spoilage</td><td>Ignored, or weather used only for price</td><td>Heat/rain spoilage on the actual route</td></tr>
<tr><td>Uncertainty</td><td>Single number</td><td>80% cushion from recent real errors; risk penalty in Stage II</td></tr>
<tr><td>Option to refuse</td><td>No</td><td>Yes &mdash; explicit &ldquo;stay home&rdquo;</td></tr>
<tr><td>Evaluation</td><td>Forecast error (MSE)</td><td>Money, loss-trip rate, worst-10%, calls; on unseen months</td></tr>
<tr><td>Honesty</td><td>Results after the fact</td><td>Pre-registered H1&ndash;H4; failed H2 reported; Stage II clearly labelled</td></tr>
</table>

<h2>12.2 The precise contributions (what is new)</h2>
<ol>
  <li><b>Measurement:</b> a multi-state, multi-crop measurement (6 states, 4 crops, 2017&ndash;2026) of how much screen spread is phantom, with official parity checks.</li>
  <li><b>Government-grounded profit model</b> and a two-view check of how much results depend on modelled penalties.</li>
  <li><b>Stage I MandiGuard:</b> a pre-registered, transparent cheap-first verification cascade with a causal 80% cushion and a refuse option (H1, H3, H4 supported).</li>
  <li><b>Stage II autopsy:</b> three measured failure mechanisms (censored arrivals, coverage illusion, thin-grade T1).</li>
  <li><b>Stage II MandiGuard-CRC:</b> uncensored two-model scoring with a validation-calibrated risk weight and grade-aware T1, beating B2 on unseen data.</li>
</ol>
<div class="box warn"><span class="t">What is NOT new (say it before the examiner does)</span>
We did not invent conformal prediction, Conformal Risk Control, gradient boosting, OSRM or the Q10 rule. We did not prove a new theorem.
The novelty is in <b>applying and combining</b> these to a real decision problem, <b>measuring</b> it carefully on Indian data, and
<b>diagnosing</b> why it works or fails.</div>

<h2>12.3 Limitations (say them calmly and confidently)</h2>
<table>
<tr><th style="width:30%">Limitation</th><th>What it means / how we addressed it</th></tr>
<tr><td>1. Field costs are modelled</td><td>Truck rates (&#8377;35 + &#8377;0.45/km), Q10 spoilage and closed-market penalties are not from real receipts. Sensitivity tests (Exp 6, Exp 15) show how results change.</td></tr>
<tr><td>2. Tests check code, not the real world</td><td>22/22 tests prove correctness and reproducibility, not real farm economics.</td></tr>
<tr><td>3. Mirror data, sample checks</td><td>Bulk data came from an archive mirror; verified on 172 + 2,042 official keys, not every row of every year.</td></tr>
<tr><td>4. Unobserved local factors</td><td>Trader credit ties, queues, tolls and same-day gluts are not in daily tables. On guaranteed-open markets, point-ML still has a higher average (with much higher risk).</td></tr>
<tr><td>5. Stage II is post-diagnostic</td><td>Designed after Stage I results; no theoretical guarantee claimed because prices are not exchangeable.</td></tr>
<tr><td>6. Apples still conservative</td><td>MandiGuard-CRC sends fewer apple trucks than B2 (22.84% vs 33.64%) and earns less on average there.</td></tr>
</table>
<p><b>Future work:</b> field pilots with farmer producer organisations (FPOs) and real weighment receipts; adaptive cushions per volatility level;
SMS delivery for feature phones (illustrated in the appendix experiments); extension to more states and crops.</p>
"""

CH13 = """
<div class="pb"></div>
<h1>Chapter 13 &mdash; Synopsis Presentation: Slide-by-Slide Plan</h1>
<p>Target: 12&ndash;15 minutes, 15 slides. Each slide: what to show and what to say. Keep text on slides short; speak the details.</p>

<div class="slide"><div class="sh">Slide 1 &mdash; Title (20 s)</div><div class="sb">Show: title, your name, guide, institute.
Say: &ldquo;My work asks a simple question: when a farmer sees a higher price in a distant mandi, should he send the truck?&rdquo;</div></div>
<div class="slide"><div class="sh">Slide 2 &mdash; The farmer&rsquo;s dilemma (1 min)</div><div class="sb">Show: Tomato story &#8377;1,400 vs &#8377;2,000, 200 km; NSS: 30 qtl, &#8377;3,798/month.
Say: &ldquo;An apparent &#8377;18,000 on one truck is about five months of crop income &mdash; a high-stakes choice.&rdquo;</div></div>
<div class="slide"><div class="sh">Slide 3 &mdash; Evidence of the problem (1 min)</div><div class="sb">Show: Figure 1 + four numbers: &#8377;1,330 &rarr; &#8377;386; 58.94% traps; 40.46% lose money.
Say: &ldquo;Most of the loss is execution risk &mdash; closed markets and missing varieties &mdash; not diesel.&rdquo;</div></div>
<div class="slide"><div class="sh">Slide 4 &mdash; Literature gap (1 min)</div><div class="sb">Show: three columns (Economics / Forecasting apps / ML theory) and the missing link.
Say: &ldquo;Information alone does not help (Mitra 2018); apps predict prices but ignore closures; abstention theory exists but was not applied here.&rdquo;</div></div>
<div class="slide"><div class="sh">Slide 5 &mdash; Problem statement, RQs, objectives (1 min)</div><div class="sb">Show: one-line problem + RQ1&ndash;RQ4 (Chapter 3.1).
Say: &ldquo;I measure the phantom, design a verify-first decision rule, test it fairly, and diagnose its weaknesses.&rdquo;</div></div>
<div class="slide"><div class="sh">Slide 6 &mdash; Data and validation (1 min)</div><div class="sb">Show: data pipeline flowchart (Chapter 4.2) + Exp 14 table.
Say: &ldquo;42.7 million raw records, 178 fixed markets chosen using 2024 only, roads, weather and government rules; official parity 100% on Min/Max.&rdquo;</div></div>
<div class="slide"><div class="sh">Slide 7 &mdash; Stage I method (1.5 min)</div><div class="sb">Show: T1&ndash;T4 decision flowchart.
Say: &ldquo;Cheap check first: is the market alive for my variety? Then roads, weather, and a frozen model with an 80% cushion. If not safe, stay home.&rdquo;</div></div>
<div class="slide"><div class="sh">Slide 8 &mdash; Worked example (1 min)</div><div class="sb">Show: the 5-line Tomato arithmetic ending at +&#8377;234.20.
Say each line slowly; examiners like to see you calculate.</div></div>
<div class="slide"><div class="sh">Slide 9 &mdash; Fair testing (1 min)</div><div class="sb">Show: timeline Train 2024 / Val H1-2025 / Holdout + &ldquo;pre-registered H1&ndash;H4 in commit e421d15&rdquo;.
Say: &ldquo;The final test months were never used for tuning, and hypotheses were written in advance.&rdquo;</div></div>
<div class="slide"><div class="sh">Slide 10 &mdash; Stage I results (1.5 min)</div><div class="sb">Show: hypothesis table + Figure 2.
Say: &ldquo;H1, H3, H4 supported; H2 not &mdash; MandiGuard ties B2 on average but nearly halves loss trips.&rdquo;</div></div>
<div class="slide"><div class="sh">Slide 11 &mdash; Robustness (1 min)</div><div class="sb">Show: 4 bullets: ablation (T1 most important), budget B=6 (+&#8377;104.54), 10 years (8.78&ndash;12.03% loss trips), penalties (Exp 15).</div></div>
<div class="slide"><div class="sh">Slide 12 &mdash; Stage II autopsy (1.5 min)</div><div class="sb">Show: Figure 8 A&ndash;B + three analogies (absent students, one umbrella, thin grades).
Say: &ldquo;I investigated my own failure instead of hiding it.&rdquo;</div></div>
<div class="slide"><div class="sh">Slide 13 &mdash; MandiGuard-CRC (1.5 min)</div><div class="sb">Show: rung ladder &#8377;452.79 &rarr; 455.15 &rarr; 469.29 &rarr; 479.17; +&#8377;32.51 vs B2 (p = 0.0016).
Say: &ldquo;Tuned on validation only, tested once on holdout, clearly labelled post-diagnostic.&rdquo;</div></div>
<div class="slide"><div class="sh">Slide 14 &mdash; Contributions and limitations (1 min)</div><div class="sb">Show: 5 contributions + top 3 limitations (modelled costs; tests check code; Stage II post-diagnostic).</div></div>
<div class="slide"><div class="sh">Slide 15 &mdash; Conclusion and future work (30 s)</div><div class="sb">Say: &ldquo;Information is not money; verified, cautious decisions are. Next step: field pilots with real receipts.&rdquo;</div></div>

<h2>13.1 One-minute pitch (memorise)</h2>
<div class="box viva">&ldquo;Price portals show farmers that distant mandis pay more, but across 63,040 naive dispatches a &#8377;1,330 screen gap shrank to &#8377;386,
and 40% of trucks lost money, mostly because markets were closed or not buying the exact variety. I built MandiGuard, a transparent
checklist that verifies market activity first, then roads, weather, and a frozen model with an 80% safety cushion, and refuses risky trips.
On 69,526 unseen opportunities, with hypotheses pre-registered, it earned &#8377;102.78 per quintal more than naive chasing, cut loss episodes
by 37 points versus point-ML, and used 44% fewer look-ups. It only tied a strong fresh-road rule on average, so I diagnosed three causes and built
MandiGuard-CRC, which, tuned only on validation, reached &#8377;479.17 per quintal and beat that rule by &#8377;32.51. Costs like freight and spoilage are
still modelled, so field pilots are the next step.&rdquo;</div>

<h2>13.2 Presentation tips</h2>
<ul>
  <li>Start with the farmer, not the algorithm. Examiners remember stories.</li>
  <li>Always say the <b>unit</b>: &ldquo;rupees per quintal&rdquo;, and translate to a 30-quintal truck when it helps.</li>
  <li>When showing H2, say &ldquo;not supported&rdquo; clearly &mdash; honesty builds trust.</li>
  <li>Keep Stage I and Stage II visually separate (two colours on slides).</li>
  <li>Have the T1&ndash;T4 flowchart and the Tomato arithmetic ready to draw on a whiteboard.</li>
</ul>
"""

QA = [
    ("What is &ldquo;Phantom Spatial Arbitrage&rdquo;?", "The part of a price gap between two mandis that looks profitable on screen but disappears after closed markets, missing varieties, freight, fees, spoilage and arrival-day price drops are counted."),
    ("Why did you choose this topic?", "High stakes for small farmers, a clear gap between economics and forecasting research, fully public data, and a method small enough to build and defend in an M.Tech."),
    ("Why not just build a better price predictor?", "Because the biggest loss (&#8377;714.90/qtl in Exp 1) comes from execution traps, not forecast error. On guaranteed-open markets point-ML predicts well, but on real markets it lost money on 45.28% of trips."),
    ("Is refusing really a good outcome?", "Yes. Chow (1970) showed abstaining is optimal when errors are costly. Staying home costs &#8377;0 extra; a bad trip loses diesel, produce and time."),
    ("Is your data real?", "Yes: AGMARKNET prices, OSRM roads, ERA5/NASA weather and government reports. No synthetic prices. Costs like truck hire are modelled and clearly labelled."),
    ("How do you know the mirror data matches the government?", "Exp 14: 172 keys from data.gov.in XML (Min/Max 100%, Modal 99.42%) and 2,042 keys over 149 days from AGMARKNET 2.0 (all three 100%)."),
    ("How did you prevent data leakage?", "Time splits (train 2024, validate Jan&ndash;May 2025, test after), model frozen after 2024, cushion updated only from trips already arrived, markets selected using 2024 only, and an automatic leakage assertion in code."),
    ("Why an 80% cushion and a &#8377;50 margin?", "80% is a standard, interpretable coverage level and was verified empirically (78.85% val, 79.07% holdout). &#8377;50 was chosen from {50,...,250} on validation only."),
    ("What is conformal prediction in one line?", "Use the model&rsquo;s recent real errors to build a cushion so that roughly the chosen fraction (80%) of future outcomes lie above the cautious estimate."),
    ("Why a gradient-boosted tree model?", "Fast, strong on tabular data, handles non-linear patterns, and is easy to freeze and audit. Alternatives were tried in the appendix (Exp 11)."),
    ("Why did H2 fail?", "MandiGuard sends fewer trucks than B2, trading average profit for safety: loss trips 9.97% vs 18.11%, worst-10% &minus;&#8377;37.89 vs &minus;&#8377;436.67. The +&#8377;6.13 average difference is within noise."),
    ("Isn&rsquo;t H4 (fewer calls) obvious?", "Partly yes, by design. The real benefit shows under tight budgets: with 6 calls, MandiGuard beats B4 by &#8377;104.54/qtl."),
    ("Are the closed-market penalties made up?", "They are modelled rules. Exp 15 reduces them to half and to zero, and tests guaranteed-open markets with no penalties; conclusions vs B1 hold until penalties are exactly zero."),
    ("Why does point-ML win on open markets?", "When every market is open, price prediction is the main skill and B3 dispatches more. But it does so with 2.2&times; the loss-trip rate and 10&times; deeper tail losses."),
    ("What is CVaR / worst-10%?", "The average of the worst 10% of outcomes &mdash; how bad the bad days are."),
    ("Why a two-way cluster bootstrap?", "Outcomes in the same market and same fortnight are related; resampling whole mandis and whole 2-week blocks gives honest uncertainty."),
    ("Why Holm correction?", "Testing four hypotheses increases the chance of a lucky win; Holm keeps the overall false-positive rate at 5%."),
    ("What is pre-registration?", "Writing hypotheses before seeing test data (commit e421d15) so the story cannot be changed afterwards."),
    ("What did Stage II discover?", "Three causes: dropping closed arrivals hid bad outcomes (up to 2.54&times; understated risk), one cushion size over-protected calm and under-protected volatile markets (90.46% vs 67.80%), and thin apple grades fooled T1 (77.82% of missed apple trades)."),
    ("What is the selective labels problem?", "When you only see outcomes for some cases (here: days the market reported), and those cases are not random, your model learns a too-optimistic picture (Lakkaraju et al., 2017)."),
    ("What does the CRC score do?", "Score = expected gain &minus; &lambda; &times; local price &times; probability of loss. It penalises routes that might lose money in proportion to what is at stake."),
    ("How was &lambda; = 0.15 chosen?", "On validation only: try 0 to 1.20 in steps of 0.05 and take the first value where (losses+1)/(dispatches+1) &le; 9.5%."),
    ("Do you claim the CRC theorem guarantee?", "No. Crop prices are not exchangeable across seasons and the number of dispatches changes with &lambda;, so we use CRC as a validation recipe and check it on holdout."),
    ("Isn&rsquo;t Stage II overfitting to the holdout?", "No holdout tuning: trained on 2024, &lambda; chosen on validation, holdout used once; also checked on guaranteed-open markets with no modelled penalties."),
    ("Why keep Stage I if Stage II is better?", "Stage I is the pre-registered confirmatory result. Replacing it would be HARKing. Stage II is reported separately as a post-diagnostic improvement."),
    ("Why does MandiGuard-CRC still trail B2 on apples?", "It sends fewer apple trucks (22.84% vs 33.64%). B2 earns more on average but with 28.43% loss trips and a much deeper worst-10% (&minus;&#8377;272.50 vs &minus;&#8377;113.40)."),
    ("Is MandiGuard an AI agent or uses ChatGPT?", "No. No LLM and no reinforcement learning. It is a deterministic checklist plus one frozen tree model and a cushion."),
    ("What do your 22 tests prove?", "That the code is deterministic, splits are leak-free, files match checksums, and results are consistent &mdash; not that real-world costs are correct."),
    ("What is your biggest limitation?", "Freight, spoilage and closed-market penalties are modelled from government averages, not measured from real farmer receipts."),
    ("Does it work in new states?", "Exp 9: trained on 5 states and tested on the 6th, it beat naive chasing in all 6 cases."),
    ("Does it work across years and shocks?", "Exp 10: 661,192 trips over 2017&ndash;2026 (GST, COVID, export curbs, 2024 heatwave), loss-trip rate stayed 8.78%&ndash;12.03%."),
    ("What exactly is novel?", "Measuring the phantom across states and crops with official checks; a pre-registered verify-first cascade with a refuse option; a measured autopsy of its failures; and a validation-calibrated uncensored fix. The tools are known; the problem framing, combination and evidence are new."),
    ("How would a farmer use it?", "As a morning advisory (app or SMS) saying &ldquo;send to market X&rdquo; or &ldquo;sell locally today&rdquo;, ideally through an FPO; the appendix illustrates SMS cards and FPO truck sharing."),
    ("What would you do next?", "Field pilot with real receipts, volatility-aware cushions, more states and crops, and an SMS/FPO deployment study."),
    ("If you had to drop one gate, which?", "T2 or T3 have the smallest overall effect (+&#8377;0.44 for T2), though T3 helps in extreme weather. T1 and T4 should never be dropped."),
]

CH14_HEAD = """
<div class="pb"></div>
<h1>Chapter 14 &mdash; Viva Defence: 35 Likely Questions</h1>
<p>Answer in this pattern: <b>direct answer &rarr; one number &rarr; one honest boundary</b>. Keep it short; offer detail only if asked.</p>
"""

CH14_TAIL = """
<h2>14.1 Five red lines &mdash; never say these</h2>
<div class="box warn"><span class="t">Avoid these over-claims</span>
<ol style="margin-bottom:0;">
  <li>&ldquo;Conformal/CRC gives a guaranteed bound in our setting.&rdquo; &rarr; It does not; prices are not exchangeable. Say &ldquo;empirically calibrated and checked on holdout.&rdquo;</li>
  <li>&ldquo;MandiGuard-CRC was pre-registered.&rdquo; &rarr; Only Stage I was. Stage II is post-diagnostic.</li>
  <li>&ldquo;It is an autonomous AI agent&rdquo; or &ldquo;it beats point-ML on open markets on average.&rdquo; &rarr; Neither is true.</li>
  <li>&ldquo;Our costs are verified with farmers.&rdquo; &rarr; They are modelled; tests check code, not field economics.</li>
  <li>&ldquo;The appendix experiments (ACI, ZeroCloud, FPO) are main contributions.&rdquo; &rarr; They are illustrations only.</li>
</ol></div>
"""

CH15 = """
<div class="pb"></div>
<h1>Chapter 15 &mdash; Glossary and One-Page Revision Sheet</h1>
<h2>15.1 Glossary</h2>
<table>
<tr><th style="width:27%">Term</th><th>Meaning</th></tr>
<tr><td>Mandi / APMC</td><td>Regulated wholesale agricultural market</td></tr>
<tr><td>Quintal (qtl)</td><td>100 kg</td></tr>
<tr><td>Modal price</td><td>Most common traded price that day</td></tr>
<tr><td>Spread</td><td>Destination price minus local price</td></tr>
<tr><td>Episode</td><td>One farmer-morning decision (send or stay)</td></tr>
<tr><td>Loss-trip rate</td><td>% of sent trucks that lost money vs selling locally</td></tr>
<tr><td>CVaR<sub>10%</sub></td><td>Average of the worst 10% outcomes</td></tr>
<tr><td>Q10 = 2</td><td>Decay roughly doubles for each +10&deg;C</td></tr>
<tr><td>OSRM</td><td>Road-routing engine using OpenStreetMap</td></tr>
<tr><td>ERA5 / NASA POWER</td><td>Gridded historical weather datasets</td></tr>
<tr><td>Conformal cushion</td><td>Safety margin built from recent real prediction errors</td></tr>
<tr><td>Coverage</td><td>% of real outcomes that land above the cautious estimate</td></tr>
<tr><td>Leakage</td><td>Accidentally using future information</td></tr>
<tr><td>Survivorship bias</td><td>Studying only those that &ldquo;survived&rdquo;, hiding failures</td></tr>
<tr><td>Selective labels / censoring</td><td>Outcomes missing for some cases in a non-random way</td></tr>
<tr><td>Heteroscedasticity</td><td>Error size differs across groups (calm vs volatile markets)</td></tr>
<tr><td>Bootstrap</td><td>Re-drawing data many times to measure uncertainty</td></tr>
<tr><td>Holm correction</td><td>Stricter significance when testing several hypotheses</td></tr>
<tr><td>Pre-registration / HARKing</td><td>Writing hypotheses in advance / changing them after seeing results</td></tr>
<tr><td>CRC, &lambda;</td><td>Conformal Risk Control; the risk weight tuned on validation</td></tr>
<tr><td>fresh0</td><td>Stage II rule letting same-day quotes pass T1 with relaxed history</td></tr>
</table>

<h2>15.2 Numbers to remember</h2>
<table>
<tr><th>Item</th><th class="num">Number</th></tr>
<tr><td>Raw records / panel</td><td class="num">42,722,187 / 178 mandis</td></tr>
<tr><td>Holdout episodes</td><td class="num">69,526 (6 states, 4 crops)</td></tr>
<tr><td>Screen gap &rarr; real gain (B1 trucks)</td><td class="num">&#8377;1,330.49 &rarr; &#8377;386.02</td></tr>
<tr><td>B1 traps / loss trips</td><td class="num">58.94% / 40.46%</td></tr>
<tr><td>Official parity</td><td class="num">172 keys + 2,042 keys</td></tr>
<tr><td>Stage I mean / loss trips / calls</td><td class="num">&#8377;452.79 / 9.97% / 8.75</td></tr>
<tr><td>H1 / H3 / H4</td><td class="num">+&#8377;102.78 / &minus;37.29 pts / 44.4% fewer calls</td></tr>
<tr><td>H2 (not supported)</td><td class="num">+&#8377;6.13, p = 0.2699</td></tr>
<tr><td>Coverage val / holdout</td><td class="num">78.85% / 79.07%</td></tr>
<tr><td>Autopsy: censoring / coverage swing / thin grades</td><td class="num">2.54&times; / 90.46% vs 67.80% / 77.82%</td></tr>
<tr><td>CRC: &lambda;* / validation episodes / target</td><td class="num">0.15 / 42,794 / 9.5%</td></tr>
<tr><td>MandiGuard-CRC holdout</td><td class="num">&#8377;479.17; +&#8377;32.51 vs B2 (p = 0.0016)</td></tr>
<tr><td>Open markets / HP apples</td><td class="num">&#8377;533.75 / &#8377;812.08 (+34.2%)</td></tr>
<tr><td>Tests</td><td class="num">22 / 22 pass</td></tr>
</table>

<div class="box key"><span class="t">The final message</span>
Information is free, but information is not money. Verified, cautious decisions &mdash; including the courage to say &ldquo;stay home&rdquo; &mdash;
are what protect a small farmer. This thesis measured the problem honestly, built a transparent solution, tested it fairly, admitted where it
fell short, and fixed what it could, while clearly stating what still needs real-world proof.</div>
<p class="small">Source of all numbers: paper/manuscript.md and results/*.csv in this repository. Rows marked &ldquo;Illustration&rdquo; are teaching examples of a formula.</p>
"""


def build_qa() -> str:
    items = []
    for i, (q, a) in enumerate(QA, 1):
        items.append(f'<div class="qa"><div class="q">Q{i}. {q}</div><div class="a">{a}</div></div>')
    return CH14_HEAD + "".join(items) + CH14_TAIL


def build() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    fig1_block = (
        '<div class="figure"><img src="{FIG1}"/><div class="cap"><b>Figure 1 (thesis numbering).</b> '
        "Where the apparent profit disappears for naive screen chasing (Exp 1).</div></div>"
    )
    ch1 = CH1.replace(
        "<h2>1.4 Why we chose this topic",
        fig1_block + "\n<h2>1.4 Why we chose this topic",
    )
    body = "".join([COVER, ch1, CH2, CH3, CH4, CH5, CH6, CH7, CH8, CH9, CH10, CH11, CH12, CH13, build_qa(), CH15])
    figs = {
        "{FIG1}": b64_img("fig1_phantom_arbitrage_anatomy.png"),
        "{FIG2}": b64_img("fig2_main_policy_comparison.png"),
        "{FIG3}": b64_img("fig3_tool_ablation_and_monsoon_heat.png"),
        "{FIG8}": b64_img("fig9_mechanistic_autopsy_and_uncensored_crc.png"),
    }
    for k, v in figs.items():
        body = body.replace(k, v)
    html = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>'
        "<title>MandiGuard - Student Study Guide</title><style>" + CSS + "</style></head><body>"
        + body + "</body></html>"
    )
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"Wrote HTML: {HTML_OUT} ({HTML_OUT.stat().st_size / 1e6:.2f} MB)")

    if not CHROME_BIN.exists():
        raise FileNotFoundError(f"Chrome binary not found at {CHROME_BIN}")
    cmd = [
        str(CHROME_BIN), "--headless=new", "--no-sandbox", "--disable-gpu",
        "--no-pdf-header-footer", f"--print-to-pdf={PDF_OUT}", HTML_OUT.resolve().as_uri(),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not PDF_OUT.exists():
        print("STDOUT:", proc.stdout)
        print("STDERR:", proc.stderr)
        sys.exit(f"Chrome PDF generation failed with exit code {proc.returncode}")
    print(f"Wrote PDF: {PDF_OUT} ({PDF_OUT.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    build()
