# Shared Writing Spec for the MandiGuard Master Study Guide (3-agent build)

Output: each agent writes ONE HTML fragment file (no <html>, <head>, <body>, <style> tags) into
`docs/study_guide_v2_parts/`. The coordinator concatenates fragments, adds the cover/TOC and CSS, embeds figures and prints to PDF with headless Chrome.

## Audience and tone
- Reader: a Class 10–12 student who must later defend this M.Tech thesis in front of examiners. Teach like the best teacher: intuition first, then the exact definition, then a numeric example, then "why we did it this way", then "what an examiner may ask".
- Plain, calm, precise English. No hype. BANNED words (case-insensitive): crushed, knockout, undeniable, provably superior, massive, shockingly, catastrophic, blazing, jackpot, surge, plunges, plunging, slash, slashes, huge, revolutionary, groundbreaking, "100% verified", "100% authentic".
- Explain every symbol and every abbreviation the first time it appears in your fragment.

## Accuracy rules (non-negotiable)
1. Every research number MUST be copied from repository sources: `paper/manuscript.md` (primary), `results/*.csv`, `FINDINGS.md`, `EXPERIMENT_REGISTRY.csv`, `research/literature_matrix.md`, `paper/references.bib`, `src/` code. Do not round differently from the source. If you cannot find a number in the repo, do not state it.
2. Teaching examples that are not research results must be visibly labelled with the word "Illustration".
3. Stage I (`MandiGuard`, pre-registered in Git commit e421d15, hypotheses H1–H4) and Stage II (`MandiGuard-CRC`, Exp 16–17, "[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]") must always be kept clearly separate.
4. NEVER claim that conformal prediction or Conformal Risk Control gives a mathematical guarantee in this setting (prices are not exchangeable; the dispatch count depends on lambda). Say "empirically calibrated on validation and checked on holdout".
5. Exp 11–13b (ACI, ZeroCloud, FPO pooling, Split-lot, Spoilage clock/SMS) are Appendix illustrations, never main contributions.
6. There is NO large language model and NO reinforcement learning inside MandiGuard.
7. Facts about published papers: only state what is in `research/literature_matrix.md`, `paper/references.bib`, `paper/manuscript.md`, or what you verify with web search. If unsure about a detail of a paper (e.g., a specific number from that paper), describe it qualitatively instead of inventing.
8. Key verified numbers (for consistency):
   - Holdout: 69,526 episodes (Jun 2025–Apr 2026), 174 origin mandis x 23 two-week blocks, 5,000 bootstrap resamples, Holm-Bonferroni.
   - Exp 1 (63,040 naive B1 dispatches): screen spread Rs 1,330.49 -> realized Rs 386.02; freight+fees Rs 160.81; spoilage Rs 68.76; traps/price drops Rs 714.90; 58.94% traps; 40.46% loss trips.
   - Stage I MandiGuard: Rs 452.79/qtl, dispatch 48.66%, LTR 9.97%, CVaR10 -Rs 37.89, 8.75 calls. B1 350.01 / 40.46% / -1,062.66; B2 446.66 / 18.11% / -436.67 / 7.87 calls / 62.11% dispatch; B3 330.85 / 45.28% / -1,097.80; B4 452.79 / 15.74 calls; B5 437.39; B6 431.94.
   - H1 +102.78 [48.66, 153.45] pHolm 0.0012 supported; H2 +6.13 [-17.02, 25.02] pHolm 0.2699 NOT supported; H3 -0.3729 pHolm 0.0008 supported; H4 calls 8.75 vs 15.74 (44.4% fewer) pHolm 0.0008 supported.
   - Coverage 78.85% (val), 79.07% (holdout). Safety margin Rs 50 chosen on validation from {50,100,150,200,250}.
   - Stage II: Val_2025H1 N = 42,794 episodes (arrival_date <= 2025-05-31); beta_target 0.095; lambda grid 0.00..1.20 step 0.05, first feasible; lambda* = 0.15 (Rung 3), 0.10 (Rung 2); training rows 274,296 settled 2024 corridors passing T1 and static_net > 0; holdout rungs 452.79 -> 455.15 -> 469.29 -> 479.17; MandiGuard-CRC +129.16 vs B1 (p 0.0004), +32.51 vs B2 [12.05, 50.49] (p 0.0016), +26.38 vs MG_v1 (p 0.0002); open-yard N 10,162: 533.75 at 7.14% LTR; HP apples N 1,537: 812.08 (+34.2%), Grade A 205.46 -> 477.56, LTR 20.0% -> 11.54%, B2 apples 1,150.83, CVaR -113.40 vs -272.50.
   - Exp 16: dropna removes 55.83% of raw Train_2024 corridors (12.64% post-T1); d0 open 89.10% -> 62.63% (train), 86.90% -> 62.97% (holdout); Q20 understatement up to 2.54x holdout (-10.55% vs -26.82%); coverage Q1 90.46% vs Q4 67.80% holdout (cushion 6.04% vs need 1.98%; 8.89% vs 17.08%); val 88.91% vs 67.84%; HP apple refusals blocked at T1 77.82% (holdout) / 82.75% (warmup), at T4 22.18% / 16.59%.

## HTML building blocks (use ONLY these classes; the coordinator supplies CSS)
- Headings: `<h1>Chapter N — Title</h1>` (start each chapter with `<div class="pb"></div>` page break before the h1), `<h2>`, `<h3>`.
- Text: `<p>`, `<ul>/<ol>/<li>`, `<b>`, `<i>`, `<code>` (for identifiers only). Use HTML entities: `&#8377;` (rupee), `&rarr;`, `&times;`, `&minus;`, `&le;`, `&ge;`, `&lambda;`, `&mu;&#770;` (mu-hat), `&amp;`. Never use markdown (no backticks, no asterisks for bold).
- Boxes: `<div class="box think"><span class="t">Title</span>...</div>` (yellow intuition/analogy), `box key` (blue key facts), `box math` (purple maths; put formulas inside `<span class="formula">...</span>`, plain text, newlines allowed), `box viva` (green "say this in the viva"), `box warn` (red traps / limitations / what not to claim), `box deep` (grey "go deeper / for the curious").
- Tables: `<table><tr><th>..</th></tr><tr><td>..</td></tr></table>`; right-aligned numbers `<td class="num">`; highlight a row `<tr class="hl">`.
- Horizontal flowchart:
  `<div class="flow"><div class="fbox c1"><b>Title</b><span>detail</span></div><div class="farrow">&#10140;</div><div class="fbox c2"><b>..</b><span>..</span></div></div>`
  Colours: c1 blue (data/input), c2 green (pass/good), c3 yellow (processing/caution), c4 red (problem/fail), c5 purple (decision/model), c6 grey (neutral). Max 6 boxes per row; use several rows for longer flows.
- Vertical gate flowchart (decision with reject branch):
  `<div class="gates"><div class="gate-row"><div class="gate">T1 — Title<span>question</span></div><div class="gate-fail-arrow">NO &#10140;</div><div class="gate-fail">Reject ...</div></div><div class="gate-down">&#8595; YES (pass)</div> ... <div class="gate-row"><div class="gate final-yes">Final</div><div class="gate-fail-arrow">else &#10140;</div><div class="gate-fail">REFUSE</div></div></div>`
- Timeline bar: `<div class="timeline"><div style="flex:3; background:#dbeafe;"><b>Label</b><br/>detail</div> ... </div>`
- Figures: `<div class="figure"><img src="{FIG1}"/><div class="cap"><b>Figure 1.</b> caption</div></div>`. Placeholders available:
  {FIG1} fig1_phantom_arbitrage_anatomy.png (Exp 1), {FIG2} fig2_main_policy_comparison.png, {FIG3} fig3_tool_ablation_and_monsoon_heat.png, {FIG4} fig4_tool_budget_pareto.png, {FIG5} fig5_hp_apple_grade_traps.png, {FIG6} fig6_sensitivity_and_govt_fees.png, {FIG7} fig7_decade_2017_2026_evolution.png, {FIG8} fig9_mechanistic_autopsy_and_uncensored_crc.png (= thesis Figure 8, panels A–C), {FIGA1} fig8_zerocloud_fpo_and_modern_ai.png (= thesis Appendix Figure A1). Look at the PNGs before writing captions. Use each figure at most once across the whole guide (ownership listed in each agent brief).
- Q&A: `<div class="qa"><div class="q">Q1. question</div><div class="a">answer</div></div>`; follow-up: `<div class="qa follow"><div class="q">Follow-up: ...</div><div class="a">...</div></div>`.
- Slide plan: `<div class="slide"><div class="sh">Slide N — Title (time)</div><div class="sb">Show: ... <br/>Say: ...</div></div>`.
- Paper card: `<div class="paper"><div class="pt">Title / authors (year, venue)</div><div class="pm">citation details, DOI</div> ...content... </div>`.

## Done criteria for each fragment
- Valid HTML fragment, only the classes above, zero backticks, zero markdown asterisks, zero banned words.
- Every chapter ends with a short "Check your understanding" box (`box key`) of 3–5 self-test questions with one-line answers.
- Report back: file path, chapters written, approximate word count, and a list of every number you used that is NOT in the "Key verified numbers" list above together with its exact source file and line.
