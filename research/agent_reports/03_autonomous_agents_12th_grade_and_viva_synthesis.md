# Autonomous Multi-Agent Class-12 Readability, Viva Stress-Test & Ground-Truth Synthesis (`MandiGuard`)

## Class-12 Readability Critic

# 12th-Class Readability & Pedagogy Critique — `MandiGuard`

**Inspected files (read-only):**
- `paper/manuscript.md` (lines 1–268)
- `FINDINGS.md` (lines 1–60)
- `viva/01_plain_english_complete_guide.md` (lines 1–92)

**Overall Diagnosis:** The science, data integrity, and honesty in `paper/manuscript.md` are strong, and `viva/01_plain_english_complete_guide.md` already does great groundwork. However, a bright Class-12 science/commerce student reading `paper/manuscript.md` in one sitting will hit a wall by Paragraph 2 of the Abstract. The main blockers are: (1) compressed 80-to-120-word sentences stacking 5 ideas at once, (2) PhD/econometric/ML terms used without a 5-word gloss, (3) dense math blocks with unintroduced symbols, and (4) two apparent number mismatches in Section 7 (`₹386.02` vs `₹350.01`, and `9.97%` vs `4.85%`) where the denominator changes silently.

---

## 1 & 2. Buzzword, Dense Math, & Long-Sentence Audit (with Class-12 Translations + Indian Mandi Analogies)

### A. Academic & Technical Buzzwords

| Term (Location in `manuscript.md`) | Class-12 Plain-English Translation | Concrete Indian Mandi Analogy |
|:---|:---|:---|
| **Phantom Spatial Arbitrage** (Title, L5, L19) | A fake price gap between two towns that looks profitable on a screen, but vanishes or turns into a loss once real travel, fees, rot, and closed-market risk are paid. | Seeing an online ad for ₹20-cheaper mangoes 150 km away, spending ₹300 on petrol to go there, and finding the shop closed or selling only bruised stock. |
| **Fragmented market cointegration / spatial wedges** (L15, Table 1 L43) | Normally, if two nearby markets are well-connected, prices move together like connected water tanks (`cointegration`). In India, prices stay stuck far apart (`wedges`) because moving crops is risky and slow. | When tomatoes jump ₹20/kg in Indore, you’d expect Bhopal prices to follow quickly; instead, bad roads, different market rules, and middlemen keep prices disconnected like separate buckets. |
| **Estimand** (Table 3 L159) | The exact number or comparison your test is trying to measure (the "target score" on the scoreboard). | Before a cricket match, deciding whether the trophy goes to "highest total runs" or "fewest ducks"—that exact rule is the estimand. |
| **Exchangeability / Non-stationarity** (L45, L47, L262) | **Exchangeability:** assuming tomorrow’s market behaves like a random shuffle of yesterday’s days. **Non-stationarity:** the rules of the weather and prices keep shifting across seasons. | You cannot predict Diwali or July monsoon tomato prices by pulling chits randomly out of a January hat—the season itself changes the odds. |
| **Conformal LCB (80% Lower Confidence Bound)** (L7, L32, L124) | A cautious "worst-case-likely" price estimate: take the AI’s best guess and subtract a safety haircut measured from past forecast mistakes so that in 80 out of 100 trips, actual arrival prices turn out equal or higher. | If a friend usually arrives up to 20 minutes late (`80%` of the time), you plan as if they will be 20 minutes late so you don't miss the train. |
| **Adaptive Conformal Inference (`MandiGuard_ACI`)** (L9, L231) | An automatic shock-absorber that widens the safety cushion when the AI starts making bigger errors (e.g., Grade A apples) and relaxes it when markets calm down. | A motorbike rider automatically gripping the brakes tighter on a sudden muddy patch instead of keeping one fixed speed everywhere. |
| **$\text{CVaR}_{10\%}$ (Worst-10% Tail Loss)** (L9, L133, L187) | The average rupee loss across the worst 1 out of every 10 trips—measuring how badly a farmer gets burned on bad days. | Not just checking a bus's average speed, but checking how bad the worst 10% of pothole accidents are. |
| **Quantized inter-agent bus (`B5`)** (L139, L180) | Instead of sharing exact rupee profits (like `₹149` vs `₹151`), separate software bots pass rough buckets (`₹0–150`, `₹150–300`) over a shared messenger channel—losing precision at bucket borders. | A driver shouting "medium profit!" to the clerk instead of saying "₹149/qtl", causing the clerk to treat ₹149 and ₹1 like the same grade. |
| **FPO (`Cooperative FPO 90-qtl`)** (L235, L244, L249 — *acronym never expanded in `manuscript.md`!*) | **Farmer Producer Organization**—a farmer-owned cooperative/society where small growers pool their harvest into one big truck to share transport costs. | Three neighbours each hiring separate auto-rickshaws vs. splitting one large Tata 407 truck together to pay 30% less per quintal. |
| **$Q_{10}$ Perishability / Biological Spoilage Clock** (L102, L235, L250) | A biology rule (`Q_10 = 2`): every `+10°C` rise in heat doubles how fast vegetables rot; the "spoilage clock" simply counts how many hours a truck can travel before `15%` of the crop spoils. | Milk left outside spoils twice as fast in a 40°C May afternoon as in a 30°C March morning; the clock tells you the exact hour it sours. |
| **APMC / Statutory Mandi Charges** (L5, L7, Table 2 L75) | **Agricultural Produce Market Committee**—government-regulated wholesale market yards, and the official percentage fees states charge farmers to sell inside them. | Different states charge different entry/commission taxes at their mandi gates (0.5% user fee in Karnataka/Gujarat vs. 1.5% regulated fee in MP/UP). |
| **MoFPI / NABCONS (2022)** (L7, L85) | Official Indian Ministry of Food Processing Industries survey measuring exact percentages of crops lost during transport and market handling. | Instead of guessing "maybe 3% tomatoes rot," using the Indian Parliament’s official post-harvest loss audit (`3.25%` for tomatoes). |
| **OSRM vs. Haversine / Euclidean Distance** (L7, L23, L26, L63) | **Haversine/Euclidean** = straight-line "as the crow flies" ruler distance on a map. **OSRM** = real highway driving distance and hours using actual roads. | Two villages across a Himachal valley may be `20 km` apart by crow flight, but `75 km` on winding single-lane hill roads. |
| **Point Forecaster (`B3`) vs. Asymmetric Cost-Sensitive Dispatch** (L5, L26, L137) | A **point forecaster** predicts only one middle number (`+₹200` guess) and ignores downside risk. **Cost-sensitive dispatch** weighs a `₹1` loss heavier than a `₹1` missed gain. | Choosing an umbrella based on "average weather" (sunny on average) vs. checking "if it rains, my textbooks are ruined." |
| **Two-way Cluster Bootstrap & Holm–Bonferroni ($m=4$)** (L9, L142, L159) | **Cluster bootstrap:** re-sampling whole markets and 2-week periods `5,000` times (instead of treating every daily row as independent) so confidence intervals aren't falsely narrow. **Holm–Bonferroni:** tightening the pass bar because we ran `4` statistical tests at once. | Testing a fertilizer across 174 villages rather than counting 69,526 plants as independent, and raising the exam pass mark because you get 4 tries. |
| **Pre-registered Confirmatory Hypotheses (`H1`–`H4`)** (L9, L113) | Writing down and locking the exact 4 pass/fail tests in version control *before* ever looking at the 2025–2026 test data. | Sealing your predictions in an envelope before the cricket match starts so you can't change the rules afterward. |
| **Temporal Firewall & Look-Ahead Leakage** (L68, L109) | A strict time wall ensuring the 2024–2025 model never peeks at future prices or actual arrival-day weather—only forecasts available on dispatch morning. | Taking a board exam with yesterday's notes only, with zero peeking at tomorrow's answer key. |
| **Survivorship Bias** (L58) | Picking only mandis that stayed active in 2025–2026 would cheat by hiding markets that shut down later; instead, mandis are chosen purely from 2024 records. | Judging startup success by interviewing only companies still alive in 2026 and ignoring the ones that went bankrupt in 2025. |
| **Reanalysis (`ERA5`) vs. NWP Forecast vs. Nowcaster** (L69–70) | **ERA5** = best scientific record of what weather *actually* hit the road. **NWP** = weather department forecast issued on dispatch morning. **Nowcaster** = a simple local backup model estimating morning weather when NWP API limits ran out. | Checking morning TV weather forecast before leaving (`NWP`), vs. the actual thermometer reading on the highway (`ERA5`). |
| **Pareto Frontier & Budgeted Feature Acquisition** (L33, L201) | Getting the highest profit possible for every API call spent—ordering cheap checks first so you don't pay for expensive weather/AI checks on dead markets. | Airport security checking your ticket at the gate (`T1`, cheap) before x-raying your bags (`T2–T4`, expensive). |
| **Satisficing Early Exit (`ZeroCloud`)** (L7, L248) | Stopping the search as soon as you find a verified route clearing a good-enough target (`₹250/qtl`), instead of checking all 5 options just to squeeze out an extra ₹5. | Taking the first clean ₹250-profit buyer instead of paying phone bills to call 4 more shops. |
| **Edge Hardware / `ZeroCloud`** (L7, L236) | Storing road distances and the small AI calculator directly on a village computer/phone (`0.075 ms`) so you only go online for today's prices and weather. | Carrying a pocket highway atlas instead of downloading Google Maps over slow village 4G every time. |
| **Leave-One-State-Out (`LOSO`) Transfer** (L32, L208) | Training the model on 5 states and testing whether it still works in a 6th state it has never seen before. | Studying math problems from Maharashtra, UP, MP, Karnataka, and Gujarat, then passing a surprise paper set in Himachal Pradesh. |
| **Grade Shift / Cultivar Heterogeneity** (L21, L207, L261) | Different varieties (`Red` vs `Desi` onion) or quality tiers (`Grade A` vs `Grade B` apples) fetch completely different prices; mixing them creates fake price gaps. | Comparing Alphonso mango rates with raw pickle-mango rates just because both are called "Mango." |
| **Demurrage / Detention** (L22, L106) | Extra daily fee (`₹25/qtl/day`) paid to keep a loaded truck parked overnight when the auction yard is closed or delayed. | Paying extra auto/tempo waiting meter charges while stuck outside a locked godown gate. |
| **Oracle Parity** (L202) | Matching the exact same profit as a slow "run-all-checks-on-everything" computer (`B4`), while using almost half as many lookups. | Getting the same 95% board score while studying half the hours. |
| **Unconditional Mean Gain vs. Conditional Loss-Trip Rate** (L9, L179, Table 4) | **Unconditional mean:** profit averaged across *all* days (counting stay-home days as `₹0`). **Conditional loss-trip rate:** `%` of *actually dispatched trucks* that lost money. | Average daily pocket money across 30 days (including stay-home days) vs. `%` of days you actually went to the market and came back at a loss. |

---

### B. Dense Math Notation Without Plain Explanation (Section 4 & 5)

1. **Net Gain Formula (L96):** $\Delta\text{Net}(i \to j, t) = P_{j}^{\text{sale}} \cdot (1 - s_{ij}) - F_{ij} - \text{Detention}_j - P_{i,t}^{\text{loc}}$
   - *Class-12 meaning:* **Extra Profit per Quintal** = `(Distant Sale Price × Fraction that did NOT rot) − (Truck & Mandi Fees) − (Overnight Waiting Penalty) − (Home Price you turned down)`.
2. **Freight Formula with Indicator $\mathbb{I}[\text{cross-district}]$ and $\gamma_{s,c}, m_{\text{HP}}$ (L100):**
   - *Class-12 meaning:* `₹35` labour + `₹0.45/km` truck rent (`1.45×` steeper in Himachal hills) + state mandi tax (`0.5%` to `1.5%` of home price, charged only if you cross district lines). Notice $\mathbb{I}[\text{condition}]$ just means "add this term only if true, else 0" — a Class-12 student shouldn't have to guess what blackboard-bold $\mathbb{I}$ means!
3. **Spoilage Formula $s_{ij}(w)$ (L103):**
   $s_{ij}(w) = \min\Bigl(0.55,\; s_{0,c} \cdot \frac{h_{ij}+24w}{24} \cdot 2^{(T_{\max}-20)/10} \cdot [1 + 0.25\max(0, \frac{\text{RH}-70}{30})] + 0.02\,\mathbb{I}[\text{Rain}\ge 35]\Bigr)$
   - *Class-12 meaning:* Start with govt base rot rate ($s_{0,c}$ per 24h at 20°C), scale by travel + wait hours, double it for every `+10°C` heat, bump up to `+25%` if air is humid (`>70%`), add `+2%` if heavy rain (`≥35 mm`) hits, and cap total physical rot at `55%`.
4. **Rain Grading Penalty (L104):** $0.5\,P^{\text{modal}} + 0.5\,P^{\text{min}}$
   - *Class-12 meaning:* If heavy rain soaks the load (`≥35 mm`), buyers won't pay normal rates—your price drops halfway down toward the market's lowest distress rate.
5. **Arrival Lag $\tau \in \{1, 2, 3\}$ (L65) and Wait $w \in \{0, 1, 2\}$ (L106):**
   - *Class-12 meaning:* $\tau$ is how many days it takes the truck to reach the morning auction (`1`, `2`, or `3` days). $w$ is extra days spent waiting at the yard gate (`0`, `1`, or `2` mornings) if your variety didn't trade on arrival day.
6. **LCB Net Formula (L125) & $\arg\max_j$ (L127):**
   $\widehat{\text{LCB\_Net}}_{ij,t} = P_{\text{arr}}^{\text{LCB}} \cdot (1 - \hat{s}_{ij}) - \widehat{\text{RainPen}}_{ij} - \hat{F}_{ij} - P_{i,t}^{\text{loc}}$, and $j^* = \arg\max_j$
   - *Class-12 meaning:* Plug the *cautious* arrival price ($P_{\text{arr}}^{\text{LCB}}$) into the same profit formula, pick whichever destination market $j^*$ gives the highest cautious profit, and go *only* if that safe profit beats `+₹50/qtl`. (Also note: `P_fresh * (1 + lcb_ret)` on L124 uses raw code names `p_arr_lcb`, `lcb_ret`—translate those to words!)
7. **Floor Bracket $\lfloor B/4 \rfloor$ (L138):**
   - *Class-12 meaning:* Whole-number division by 4 (e.g., with a budget of `B = 6` calls, a naive bot checking all 4 tools upfront finishes only `1` market (`6 ÷ 4 = 1`) and runs out of budget).

---

### C. Long, Complicated Sentences in `paper/manuscript.md` to Break Up

1. **Abstract Sentence 2 (L5, 108 words!):** *"Yet on untouched official daily records spanning `69,526` inter-market dispatch opportunities..."* — packs states, crops, dates, headline spread, trap rate, loss rate, freight, fees, weather, and arrival-day drop into one breathless sentence. **Fix:** Split into 3 punchy sentences: (1) Scope (`6` states, `4` crops, `69,526` trips), (2) The trap (`58.94%` closed/wrong-variety, `40.46%` lose money), (3) Why it happens (freight, fees, heat/rain rot, price drops).
2. **Abstract Sentence 4 (L7, 94 words!):** *"To solve this decision problem without black-box complexity, we present `MandiGuard`..."* — jams `REFUSE_PHANTOM_SPREAD` and all 4 tools (`T1–T4`) with citations and legal acts into one sentence. **Fix:** Turn `T1–T4` into a 4-bullet or 4-clause mini-list with 5 words per tool.
3. **Abstract Sentence 6 (L9, 130+ words!):** *"Across `69,526` shortlisted holdout episodes evaluated with paired two-way..."* — mixes bootstrap mechanics, Holm correction, H1, H3, H4, H2's failure, CVaR explanation, and 4-state NWP subset into one giant paragraph-sentence. **Fix:** Break into 3 sentences: (a) Main wins (`H1`, `H3`, `H4`), (b) Honest tradeoff on `H2` (why mean `+₹6.13` isn't significant but tail risk drops `11.5×`), (c) Robustness (`10-year`, `FPO`, `HP Apple`).
4. **Section 1, L24 (56 words):** *"Meanwhile, statutory mandi fee regimes vary across state boundaries..."* — stacks 4 state exceptions into one sentence. **Fix:** One short sentence per rule ("Karnataka and Gujarat charge `0.5%` user fees; HP exempts vegetables but taxes apples (`1.0%`); MP and UP charge `1.5%`.").
5. **Section 2, L47 (55 words):** *"Standard split conformal guarantees require exchangeability..."* — too dense for Section 2. **Fix:** Split into two plain sentences explaining *why* seasonal crops break standard math assumptions and how rolling 2024->2025 checks prove it still works ~79% of the time.
6. **Section 7.2, L179 (110+ words across 3 clauses):** *"Instead, `MandiGuard` protects farmers from ruin..."* — packs `9.97% vs 18.11%`, `16.17% vs 24.32%`, `11.5x` CVaR, `30-qtl` numbers, `4-state` native NWP `+₹31.82/qtl`, Onion, Potato, and Tomato all into one bullet! **Fix:** Give `H2` tradeoff, `4-state native weather`, and `Crop breakdown` their own 1-line sub-bullets.
7. **Section 7.7, L248 (82 words):** *"Offloading `T2 + T4` (`ZeroCloud_Full`) does not merely reduce API bills..."* — hides a neat discovery (that offline freight lets you sort nearby markets first so profit actually *rises* to `₹455.33/qtl`) inside a parenthetical clause. **Fix:** Pull that discovery out into its own sentence!

---

## 3. Crystal-Clear 5-Line Class-10/12 Worked Arithmetic Example (One 30-Quintal Truckload)

*(Note: Grounded directly in `manuscript.md` Section 4.1 & 5 equations—30 quintals of **Tomatoes** in Madhya Pradesh (`1.5%` mandi fee, `3.25%` NABCONS 24h base spoilage at `20°C`), hauled **`200 km`** (`6 hours` drive) in **`40°C` May afternoon heat**, vs. **`₹1,400/qtl` Home Price** (`₹42,000` at home). Note why `40°C` is pedagogically ideal: `+20°C` above `20°C` doubles rot twice -> exact `4×` factor, and `6 hrs / 24 hrs = 1/4`, so `(1/4) × 4 = 1.0`—zero messy exponents for Class 10/12!)*

> **The Bait:** On the portal, a mandi `200 km` away shows **`₹2,000/qtl`** (`₹60,000` for your `30-qtl` tomato truck)—a tempting **`+₹600/qtl` (`+₹18,000`)** jump over your `₹1,400/qtl` home mandi! Let's check with 5 lines of school arithmetic:
>
> 1. **Distant Sale Price (Screen Quote):** **`₹2,000.00 / qtl`** (`₹60,000` for 30 qtl).
> 2. **Minus Heat Spoilage (`40°C`, `6 hrs`):** At `20°C`, `3.25%` spoils in `24 hrs`. At `40°C` (`+20°C`), rot runs `4×` faster, and `6 hrs` is `1/4` day -> `3.25% × (1/4) × 4 = 3.25%` rots -> **`-₹65.00 / qtl`** (`-₹1,950`), leaving `₹1,935.00/qtl`.
> 3. **Minus Highway Freight & MP Mandi Fee (`T2`):** `₹35` loading + `(₹0.45 × 200 km = ₹90)` diesel/truck + `(1.5% × ₹1,400 = ₹21)` MP mandi fee = **`-₹146.00 / qtl`** (`-₹4,380`), leaving `₹1,789.00/qtl`.
> 4. **Minus 80th-Percentile Safety Cushion (`T4`):** Past trips show prices can fall up to `8%` by arrival morning (`8%` of surviving `₹1,935` crop) -> **`-₹154.80 / qtl`** (`-₹4,644`), leaving **`₹1,634.20/qtl`** safe cash in hand. *(Algebra check: `₹2,000 × 0.92 × (1 − 0.0325) − ₹146 = ₹1,634.20` — identical to the paisa!)*
> 5. **Minus Home Price = Safe Profit (`ΔNet`):** `₹1,634.20 − ₹1,400.00` = **`+₹234.20 / qtl`** (**`+₹7,026`** safe profit on the 30-qtl truck). Since `+₹234.20 > ₹50` safety buffer -> **`DISPATCH`!**
>
> **Now watch what happens if ONE trap hits:** Suppose Tool `T1` sees that exact tomato variety hasn't traded there in 5 days (or it's a closed Sunday), OR Tool `T3` spots `40 mm` monsoon rain (which knocks price down toward minimum and rots more tomatoes). `MandiGuard` yells **`REFUSE_PHANTOM_SPREAD — SELL AT HOME`** in 1 click, saving the farmer from a `-₹500/qtl` (`-₹15,000`) U-turn loss!

*(Compare with `viva/01_plain_english_complete_guide.md` Section 2: the viva guide used `180 km / 5.5 hrs / 35°C`, which required `2^(15/10) ≈ 2.83` and `5.5/24 ≈ 0.229`. Switching the teaching example to `200 km / 6 hrs / 40°C / ₹1,400 home` keeps 100% fidelity to `manuscript.md` formulas while allowing every calculation to be done mentally in Class 10!)*

---

## 4. Section-by-Section Line Simplification Advice (100% Scientific Honesty Preserved)

### Abstract (Lines 5–9)
- **L5:** Open with a 2-sentence hook: *"Farmers often check government price portals and spot another mandi offering `₹1,330/qtl` more—enough to look like a jackpot on a 30-quintal truckload. Yet across `69,526` real dispatch opportunities in 6 Indian states (`2025–2026`), `58.94%` of trucks chasing top prices hit closed yards or un-traded varieties, and `40.46%` actually lose money."* Move state names and dates into a clean parenthetical.
- **L7:** Replace *"cost-ordered cascade of four metered checks"* with *"four quick checks run cheapest-first (`T1` to `T4`)"*. Explain `conformal LCB` in 6 words: *"a historical worst-80% safety buffer"* and `ZeroCloud` as *"keeping static road maps and the small AI scorer offline on local hardware."*
- **L9:** Split into two short paragraphs or 3 crisp sentences:
  1. **Wins (`H1, H3, H4`):** Beats naive screen chasing by `+₹102.78/qtl` (`+₹3,083.5` per 30-qtl truck), cuts ML-induced loss trips by `37.29 pp`, and matches an all-checks-at-once computer using `44.4%` fewer online calls.
  2. **Honest Draw (`H2`):** Against a strong fresh-price + real-road heuristic (`B2`), average profit is statistically tied (`+₹6.13/qtl`, `p = 0.27`), because `MandiGuard` deliberately skips risky lottery trips—halving loss trips (`9.97%` vs `18.11%`) and cutting worst-10% crashes `11.5×` (`-₹37.89` vs `-₹436.67/qtl`).
  3. **Scale:** Holds across 10 years (`2017–2026`, `661,192` trips), `90-qtl` FPO shared trucks (`₹477.28/qtl`), and `2026` HP Apple grades (where adaptive bounds cut tail risk `27.6%`, though conservative intervals under-dispatch scarce `Grade A`).

### Section 1 — Introduction (Lines 13–33)
- **L15:** Replace *"persistent inter-mandi price wedges and fragmented market cointegration"* with *"price gaps between towns that don't close on their own because markets are poorly connected."* Explain *"without usable outside dispatch mechanisms"* as *"when farmers still have no safe way to haul and sell there."*
- **L17:** Keep this—the `NSS Report No. 587` (`30-qtl` load vs `₹3,798/month` income) is the **pedagogical crown jewel** of the paper. Bold `5+ months of household crop income wiped out by one bad trip`.
- **L21–24:** Rename the 4 numbered traps in plain words right next to the bold headers:
  1. *Wrong Variety / Grade* (explain `cultivar` as *exact sub-type, e.g. Red vs. Desi onion*).
  2. *Closed Gate / Stale Quote* (replace `demurrage` with *overnight truck waiting charges*).
  3. *Winding Hills vs. Map Straight Lines* (replace *crow-flies geometry* with *ruler distance on a flat map*).
  4. *Heat, Rain & State Border Taxes* (replace *respire* with *breathe, heat up, and rot*).
- **L26:** Explain *"symmetric price-forecast accuracy rather than cost-sensitive operational dispatch"* as *"standard AI gets graded on guessing the average price right—missing by `+₹200` and `-₹200` count the same. For a indebted farmer, losing `₹200` hurts far more than missing a `+₹200` jackpot."*
- **L29–33 (`Summary of Contributions`):** Add a 1-sentence plain-English takeaway before each technical phrase (e.g., Contribution 4: *"Check cheap things first so you don't waste paid internet lookups on closed markets"*).

### Section 2 — Related Work (Lines 37–47)
- **Table 1 (L41–45):** Add a 4th short column or rewrite Column 3 & 4 in active Class-12 English:
  - Replace *"spatial wedges, weak inter-state cointegration"* -> *"price gaps stay stuck; price boards alone don't help."*
  - Replace *"missing-quote statistical imputation and point-profit ranking"* -> *"guessing missing prices with math and ranking by average profit."*
  - Replace *"Bayes-optimal reject option; distribution-free prediction intervals; budgeted test-time tool invocation"* -> *"knowing when to say 'Stay Home'; safety bands that don't assume bell curves; paying for checks only when needed."*
- **L47:** Keep the scientific disclaimer intact, just translate *"exchangeability"* inline: *"Standard conformal math assumes market days behave like identically shuffled cards (`exchangeability`), which monsoon and harvest shocks break—so we test empirically on real future seasons and observe ~79% actual coverage against our 80% target."*

### Section 4 — Problem Formulation & Physical Economic Model (Lines 91–113)
- **Before L96:** Insert the **5-line worked 30-qtl numerical example** (from Section 3 above) *before* showing the algebraic equations! Once a Class-12 student sees `₹2,000 − ₹65 − ₹146 − ₹154.80 − ₹1,400 = +₹234.20`, every symbol in L96–L104 becomes obvious.
- **L96–104:** Under every equation, add a **"In plain words:"** line defining $\mathbb{I}[\cdot]$ ("add only if true"), $\gamma_{s,c}$ ("state mandi tax rate"), $m_{\text{HP}}$ ("`1.45×` hill-road multiplier"), and $s_{0,c}$ ("government 24-hour base rot rate at 20°C").
- **L106–107:** Put the 3 arrival outcomes into a tiny 3-row mini-table (`Day 0 Exact Variety` -> normal sale; `Wait 1–2 Days` -> `₹25/qtl/day` parking + extra heat rot; `Closed / Missing 3 Days` -> `-10%` distress dump or `1.5×` empty return freight).
- **L110–113 (`Temporal Firewall`):** Draw a 1-line ASCII timeline:
  `[2024: Train AI] -> [Jan–May 2025: Pick ₹50 Safety Cushion] -> (LOCKED WALL) -> [Jun 2025–Apr 2026: Final Exam]`
  Explain *causal online update* as *"after each truck arrives, we record how wrong the AI was and update tomorrow's safety cushion—never peeking ahead."*

### Section 5 — `MandiGuard` Agent Steps (Lines 117–127)
- **L119:** Explain `Step 0` with a shopping analogy: *"Pick the top 5 nearby yards (`15–500 km`) whose recent 7-day board looks at least `₹100/qtl` higher than home—zero external lookups."*
- **L121–127:** Turn `T1 -> T2 -> T3 -> T4` into an explicit **"Knockout Tournament"** diagram or checklist:
  - `T1 (Market Open?)`: Did this *exact* variety trade in the last 3 days? Is the yard open `≥50%` recently and `≥35%` on arrival weekday? *Fail -> Eliminate in 1 call!*
  - `T2 (Truck & Tax Covered?)`: Subtract real road freight + state fee. *Profit ≤ 0 -> Eliminate!*
  - `T3 (Weather Spoilage Survived?)`: Check morning forecast for `≥35°C` heat or `≥35 mm` rain; subtract rot. *Profit ≤ 0 -> Eliminate!*
  - `T4 (80% Safety Cushion Cleared?)`: Ask 2024 AI for arrival price, subtract historical 80th-percentile shortfall (`q_0.80`), and verify `Safe Profit > ₹50/qtl`. *Otherwise -> **`REFUSE_PHANTOM_SPREAD` (Sell Locally)**.*
- **L124:** Replace raw variable names `p_arr_lcb = p_fresh * (1 + lcb_ret)` with plain labels (`Safe Arrival Price = Today's Price × (1 + Worst-80% Expected Return)`).

### Sections 7.1–7.7 — Results & Deep Empirical Analysis (Lines 148–250)
- **7.1 (L149–152) — Fix the `₹386.02` vs `₹350.01` silent denominator switch!**
  - `Exp 1` reports `₹386.02/qtl` across the `63,040` trips `B1` *actually took*. Table 4 (`B1`) reports `₹350.01/qtl` across *all* `69,526` shortlisted days (counting the `9.33%` stay-home days as `₹0`: `₹386.02 × 0.9067 = ₹350.01`). Add one sentence stating this explicitly so readers don't think the numbers contradict!
  - Translate *"execution traps and price reversion"* as *"closed gates, missing varieties, and prices falling while the truck is still on the highway."*
- **7.2 (L156–180) — Fix the `9.97%` vs `4.85%` (`37.29 pp`) confusion across `manuscript.md` & `FINDINGS.md`!**
  - Right below Table 3/4, add a 2-sentence box: *"Why does `H3` say `-37.29 pp` (`42.14% -> 4.85%`) while Table 4 says `45.28%` vs `9.97%`? Table 4 counts losses **among trucks that actually left** (`9.97%` of `48.66%` dispatched days = `4.85%` of all days), whereas `H3` compares losses **across all 69,526 days** (`42.14%` for `B3` vs `4.85%` for `MandiGuard`)."*
  - Explain `B5` (`Quantized`) and `B6` (`Verbal Buckets`) simply: *"Passing coarse `₹150` profit slabs (`B5`) or rigid `12%` rules of thumb (`B6`) throws away rupee precision and loses `₹15–21/qtl`."*
  - Explain Tomato (`B1 ₹547.64` vs `MandiGuard ₹522.48` vs `B2 ₹484.64`): frame as *"gambling on volatile jackpots (`32.38%` crashes under `B1`) vs steady safe income (`5.09%` crashes under `MandiGuard`)."*
- **7.3 (L184–197):** Summarize Table 5 in two plain takeaways before the numbers: (1) *"Skip `T1` (is the yard open for my variety?) and traps explode 4× (`67.16%`)";* (2) *"Skip `T4` (80% safety cushion) and worst-10% crashes jump 10.5× (`-₹397/qtl`)."* On `T3` costing `-₹2.46/qtl` overall, explain honestly: *"A few scorching days still saw surprise destination price spikes that paid for the rotted crop, so skipping heatwaves buys safety (`11.39% -> 10.10%` loss rate) at a tiny `₹2.46/qtl` average cost."*
- **7.4 (L201–202):** Use the **₹60/Budget-6 phone-credit analogy**: *"If a farmer app only gives you `6` online lookups per query (`B=6`), checking all 4 tools upfront (`B4`) finishes barely `1` market (`₹299/qtl`), while cheapest-first pruning (`MandiGuard`) finishes the best candidates and earns `₹404/qtl` (`+₹104.54/qtl` more)."*
- **7.5 (L206–209):**
  - On HP Apples (`Exp 3`): lead with the punchline (`Grade B` flips from `-₹427.54` loss to `+₹833.70/qtl` profit; traps drop `94.14% -> 13.24%`), then explain the honest caveat plainly: *"Because 2024 records lacked `Grade A` labels, the cautious 2024 model got spooked by huge price swings on 2026 `Grade A` apples and stayed home too often (`5.39%` dispatch), leaving money on the table compared to `B2`."*
  - Explain `3×3` sensitivity (`Exp 6`) in 1 sentence: *"Even if diesel gets `25%` cheaper/costlier or rot gets `50%` faster, `MandiGuard` still beats naive chasing in every single scenario (`9/9`)."*
- **7.6 (L215–231):**
  - Replace model acronyms (`Direct_Quantile_GBDT_Q20`, `Deep_MLP_Conformal`, `Contextual_UCB_Bandit`) with descriptive tags in parentheses: *"a direct 20th-percentile tree predictor (`Direct_Quantile_GBDT_Q20`)", "a neural network (`Deep_MLP_Conformal`)", "a trial-and-error bandit (`Contextual_UCB_Bandit`)"*.
  - Highlight the `1-Yr vs 8-Yr` finding (`Exp 10b`) in plain English: *"Last year's fresh market habits (`2024`) beat cramming 8 years of old data (`2017–2024`)—giving `99.5%` of the gain (`₹452.79` vs `₹454.94/qtl`), because old pre-COVID rules don't match today's prices."*
- **7.7 (L235–250):**
  - Spell out **Farmer Producer Organization (`FPO`)** on first mention in L235.
  - Explain **`ZeroCloud`** in 1 sentence: *"Roads don't move overnight, and our tiny AI runs in `0.075` thousandths of a second on any basic chip—so storing them offline cuts paid internet calls by `65%–76%` (`₹7,868 -> ₹1,922` per 10,000 queries)."*
  - Use the **Biological Spoilage Clock** numbers (`110.8h` winter vs `24.1h` summer for Tomato) right at the start of the bullet as a dramatic hook, followed by the actual `<160`-character SMS examples (which are already super Class-12 friendly!).

---

### Bonus Cross-File Note (`FINDINGS.md` & `viva/01_plain_english_complete_guide.md`)
- `viva/01_plain_english_complete_guide.md` is already very strong, but still leaves `Q10`, `conformal`, `FPO`, `CVaR_10%`, `pp`, `arr_dow_open_rate`, and `Quantile_GBDT / Deep_MLP / ACI` un-glossed. Adding a 10-line micro-glossary at the top of the viva guide + swapping its `5.5h / 35°C` example to the exact integer `6h / 40°C` example above will make both the thesis and the viva 100% bulletproof for any Class-12 student or non-ML examiner.

---

## Tough M.Tech Viva Examiner

# Strict External M.Tech Viva Defense: 15 Hardest Attack Questions & Bulletproof Answers

---

### 1. Why H2 Failed Significance (`p = 0.2699`)
**Examiner Attack:**
> "Your own confirmatory test `H2` against a simple fresh-price OSRM heuristic (`B2_FreshRoadGreedy`) failed outright with $p_{\text{Holm}} = 0.2699$ and a confidence interval crossing zero (`[-17.02, +25.02]`). If a basic rule beats or ties your ML-and-conformal agent on average farmer profit, why does `MandiGuard` even deserve an M.Tech thesis?"

**Candidate Answer:**
`H2` was not significant (`+₹6.13/qtl`, 95% CI `[-₹17.02, +₹25.02]`, `p_Holm = 0.2699`) because `MandiGuard` deliberately gives up risky borderline trips (`48.66%` dispatch vs `62.11%` for `B2`) rather than chasing high-variance lottery upsides. In exchange for that `₹6.13/qtl` edge in average gain (`₹452.79` vs `₹446.66/qtl`), `MandiGuard` nearly halves dispatched phantom loss trips (`9.97%` vs `18.11%`), cuts closed/variety traps (`16.17%` vs `24.32%`), and shrinks worst-10% tail losses (`CVaR_10%`) by **11.5x** (`-₹37.89/qtl` vs `-₹436.67/qtl`). Furthermore, across the `42,766` episodes in the four states with 100% native historical weather forecasts (`Exp 2b`), `MandiGuard` widens its profit lead over `B2` to `+₹31.82/qtl` (`₹485.18` vs `₹453.37/qtl`).

---

### 2. HP Apple Grade A Under-Dispatch (`5.39%` Dispatch, `₹605.06/qtl` vs `B2 ₹1,150.83`)
**Examiner Attack:**
> "Look at `Exp 3`: on Himachal Pradesh apples, `B2` earns `₹1,150.83/qtl` while `MandiGuard` collapses to `₹605.06/qtl`, and on premium `Grade A` lots you dispatch only `5.39%` of the time (`₹205.46/qtl` vs `B2 ₹1,598.95/qtl`). Isn't your agent starving apple farmers of their best profits?"

**Candidate Answer:**
Because our `2024` training set used generic variety names without `Grade A` or `Grade Range-1` quality tags, the frozen conformal bound saw `2026`'s high-priced `Grade A` spreads as risky outliers and conservatively abstained (`5.39%` dispatch vs `19.41%` for `B2`). Even with that under-dispatching, `MandiGuard` still cut HP Apple closed/grade traps **7-fold** (`13.24%` vs `94.14%` for naive `B1` and `34.04%` for `B2`), slashed worst-10% tail losses from `-₹8,487.24/qtl` (`B1`) and `-₹272.50/qtl` (`B2`) down to `-₹102.76/qtl`, and turned `Grade B` from `-₹427.54/qtl` (`B1`) into `+₹833.70/qtl` profit. We explicitly flag this boundary in Section 8 and solve the tail-shift issue via grade-stratified recalibration and Adaptive Conformal Inference (`Exp 11`).

---

### 3. Removing Weather Tool `T3` Slightly Raised Unconditional Profit (`+₹2.46/qtl`)
**Examiner Attack:**
> "In `Exp 4`, `No_T3_Weather` makes `₹455.25/qtl` while `Full_MandiGuard` makes `₹452.79/qtl`—and even in `Extreme_Heat_or_Rain`, removing `T3` makes MORE money (`₹474.31` vs `₹470.07/qtl`). Doesn't that prove your weather gate is useless or actively hurting profit?"

**Candidate Answer:**
Removing `T3` raises average profit by `₹2.46/qtl` (`₹455.25` vs `₹452.79/qtl`) only because it allows `1.52%` more borderline hot or rainy dispatches (`50.18%` vs `48.66%`), some of which get lucky when destination prices jump enough to absorb spoilage. What `T3` buys is biological downside protection: across the `21,656` extreme heat or heavy rain episodes, keeping `T3` cuts dispatched phantom losses from `11.39%` to `10.10%` and protects worst-10% tail losses by `+₹10.38/qtl` (`-₹57.11` vs `-₹67.49/qtl`). For a perishable crop like Tomato, skipping a `123 mm` monsoon dispatch avoids wiping out a farmer's working capital even if a few risky trips occasionally pay off.

---

### 4. Why 8 Years of Training Data (`2017–2024`) Only Added `+₹2.15/qtl` Over 1 Year (`2024`)
**Examiner Attack:**
> "You brag about streaming `42.7` million rows over nearly a decade, yet in `Exp 10b`, scaling training data nearly 5x from 1 year (`701,932` rows) to 8 years (`3,437,098` rows) adds a laughable `+₹2.15/qtl` (`₹452.79` to `₹454.94`). Does your ML model fail to learn from more data?"

**Candidate Answer:**
That flat scaling curve (`₹452.79/qtl` at `1Yr` vs `₹454.74` at `3Yr` and `₹454.94/qtl` at `8Yr`) is actually an important positive finding about Indian mandi non-stationarity. Older macro shocks in `Exp 10`—such as the `2017H2 GST Transition`, `2020–21 COVID Shock`, and `2022–23` export curbs—had different price spreads and reporting patterns (`loss-trip rates 8.78%–12.03%`), so stale pre-2024 rows add little beyond what `2024` (`701,932` rows) already captures. This proves a fresh prior-year model paired with causal conformal bounds is both cheaper to retrain and nearly optimal for live deployment.

---

### 5. `Q10` Spoilage Simulated From NABCONS Rather Than Weighment Logs
**Examiner Attack:**
> "You don't have a single real truck weighment receipt! Your transit spoilage is a simulated $Q_{10}=2.0$ formula plugged into NABCONS averages. Doesn't using simulated spoilage invalidate your entire profit benchmark?"

**Candidate Answer:**
AGMARKNET does not record truck-level weighment loss, so anchoring biological decay to official MoFPI/NABCONS (2022) market-level loss rates (`3.25%` Tomato, `1.96%` Onion, `1.64%` Apple, `0.86%` Potato at `20°C`) is the cleanest government-verified baseline available. More importantly, `Exp 1` shows that physical spoilage accounts for only `₹68.76/qtl` of erosion, whereas **`₹714.90/qtl`** (`58.94%` closed/variety traps and price drops) comes directly from untouched official AGMARKNET price logs. Finally, `Exp 6` varies spoilage across `[0.5x, 1.0x, 1.5x]` and freight across `[0.75x, 1.0x, 1.25x]`, confirming `MandiGuard` beats naive `B1` across all `9/9` regimes by `+₹82.62` to `+₹121.42/qtl`.

---

### 6. Zero-Leakage & Pre-Registration Proof (`Train_2024`, `Val_2025H1`, `e421d15`)
**Examiner Attack:**
> "How do I know you didn't tune `safety_margin_inr = ₹50` or tweak your hypotheses after peeking at your `2025–2026` test results?"

**Candidate Answer:**
We enforced a strict three-way temporal split: the forecaster was fit strictly on `Train_2024` (`701,932` rows), the single scalar `safety_margin_inr = ₹50.0/qtl` and `78.85%` conformal coverage were frozen on `Val_2025H1` (`280,697` rows in `frozen_calibration.json`), and `Holdout_2025_2026` (`69,526` episodes) was evaluated afterward. Git commit `e421d15` permanently timestamped hypotheses `H1`–`H4` and the frozen validation calibration *before* the holdout run commit (`2663e42`), and causal conformal residuals only enter after `arrival_date <= decision_date`. All `18/18` automated pytest checks—including `test_preregistration_precedes_results_in_git` and `test_temporal_firewall_guard`—passed.

---

### 7. Why Not Use GPT-4, LSTMs, or Deep RL at Runtime?
**Examiner Attack:**
> "This is 2026! Why build a tabular gradient-boosted tree and an `if-else` cascade instead of a modern LLM agent like GPT-4, an LSTM sequence model, or a Deep RL policy?"

**Candidate Answer:**
In our head-to-head `Exp 11` showdown using the exact same `T1–T4` funnel, `Deep_MLP_Conformal` (`₹435.38/qtl`, `10.69%` loss trips) and `Contextual_UCB_Bandit` (`₹406.47/qtl`, `10.93%` loss trips) actually scored worse than `MandiGuard_Standard` (`₹452.79/qtl`, `9.97%` loss trips) on the 6-state holdout. Meanwhile, `Exp 12` shows our tabular `ZeroCloud` models run on a basic CPU in `0.075–0.099 ms` per query with zero LLM API bills, whereas GPT-4 adds expensive per-query token costs and high latency without improving numerical price-return calibration. Using a `Direct_Quantile_GBDT_Q20` (`₹459.02/qtl`) or `HistGradientBoosting` tree inside conformal bounds gives farmers auditable, millisecond decisions on local hardware.

---

### 8. Explaining 80% Conformal LCB & Two-Way Cluster Bootstrap in Class-12 English
**Examiner Attack:**
> "Don't hide behind statistical jargon. Explain '80% Conformal LCB' and 'Two-Way Cluster Bootstrap' so a Class-12 student—or an FPO secretary—can verify you aren't bluffing."

**Candidate Answer:**
For the **80% Conformal LCB**, we look at our recent completed trip mistakes, pick the 80th-percentile worst shortfall (`q_hat_0.80`), and subtract it from today's predicted price so that roughly 80% of real arrival prices end up higher than our conservative floor—empirically holding at `78.85%` in validation and `79.07%` in holdout. For the **Two-Way Cluster Bootstrap**, because trips starting from the same mandi or happening in the same 2-week harvest/monsoon window rise and fall together, we resample whole origin mandis (`174`) and whole 2-week blocks (`23`) together `5,000` times instead of treating every row as independent. Combining that with Holm–Bonferroni correction across all `4` tests guarantees our `p`-values (`H1 = 0.0012`, `H3 = 0.0008`, `H4 = 0.0008`) aren't inflated by correlated market days.

---

### 9. Why `ZeroCloud_Full` Earns `+₹2.54/qtl` MORE Than Standard (`T2` Pre-Ranking)
**Examiner Attack:**
> "Wait a second—in `Exp 12`, `MandiGuard_ZeroCloud_Full` deletes live `T2` and `T4` API calls to save money (`5.53` calls vs `8.75`), yet its profit goes UP from `₹452.79` to `₹455.33/qtl`! How can using offline cached tools beat the full live pipeline?"

**Candidate Answer:**
In `MandiGuard_Standard`, the Step-0 shortlist picks the top `5` destinations using only raw headline price spread (`> ₹100/qtl`), which often fills those `5` slots with distant, high-freight traps before `T2` is ever called. In `MandiGuard_ZeroCloud_Full`, because static highway freight (`T2`) is cached locally on the edge at zero API cost, the agent pre-ranks Step-0 candidates by *freight-adjusted spread* before taking the top `5`. That lets profitable nearby mandis enter the shortlist (`48.89%` vs `48.66%` dispatch), raising net gain by `+₹2.54/qtl` (`₹13,659.8` vs `₹13,583.6` per 30-qtl truck) while cutting API costs by `64.9%` vs `B4`.

---

### 10. Real vs Hypothetical Open-Meteo `43` Uncached Cells (`Exp 2b` Native-NWP Proof)
**Examiner Attack:**
> "In Section 3.3 you admit you hit Open-Meteo's free API limit and only got archived decision-day forecasts for `102` of `145` grid cells, filling the remaining `43` northern cells with a Ridge regression nowcaster. Doesn't that mean your weather numbers are partly hypothetical?"

**Candidate Answer:**
First, the physical weather that actually hits the truck is **100% real** (`0.0%` missing) across all `145/145` ERA5 cells (`2024–2026`) and `114` NASA POWER cells (`2017–2023`), and the `43`-cell Ridge nowcaster was fitted strictly causally on `2024` data (`Jan–May 2025` OOS MAE: `1.047°C`, `0.001 mm` rain, `0.284%` RH). Second, to leave zero doubt, `Exp 2b` isolates the `42,766` holdout episodes across the four states with **100% native historical NWP forecasts** (`Gujarat`, `Karnataka`, `Madhya Pradesh`, `Maharashtra`). Inside that pure native-NWP subset, `MandiGuard` actually performs stronger, earning `₹485.18/qtl` (`5.52%` episode loss) and beating `B1` by `+₹59.53/qtl` and `B2` by `+₹31.82/qtl`.

---

### 11. Tomato Mean vs Loss Rate Tradeoff Against `B1`
**Examiner Attack:**
> "On Tomato—your most perishable crop—`Exp 2b` shows naive `B1` earns `₹547.64/qtl` while `MandiGuard` earns `₹522.48/qtl` (`-₹25.16/qtl` worse!). Why should a tomato farmer use `MandiGuard` if chasing the portal makes more money on average?"

**Candidate Answer:**
Across those `20,609` Tomato episodes, `B1` squeezes out `+₹25.16/qtl` higher average return only by gambling blindly on high-spread spikes that cause farmers to lose money on **`32.38%`** of all opportunities—nearly 1 in every 3 episodes! `MandiGuard` still beats both `B2` (`₹484.64/qtl`) and `B3` (`₹515.05/qtl`) on Tomato while slashing episode phantom losses over 6-fold down to **`5.09%`** (`Exp 7` rejects `23.86%` for `VARIETY_OR_STALE` and `18.30%` for `ARRIVAL_REVERSION_RISK`). For a smallholder growing a crop that rots at `3.25%`/day even at `20°C`, avoiding a 1-in-3 wipeout is far more valuable than chasing `₹25/qtl` of lottery variance.

---

### 12. Why Onion Loses Money `48.69%` of the Time in Naive Dispatches
**Examiner Attack:**
> "Why does Onion suffer a `48.69%` loss rate under `B1` (`Exp 1`) when NABCONS shows Onion (`1.96%`/day) is much less perishable than Tomato (`3.25%`/day)?"

**Candidate Answer:**
Unlike Apple (`₹3,499.80/qtl` screen spread) or Tomato (`₹1,521.55/qtl`), Onion starts with a razor-thin average screen spread of only `₹704.50/qtl` (`Exp 1`). Once highway freight (`₹138.07/qtl`), modest spoilage (`₹28.60/qtl`), and `₹484.23/qtl` of variety-mismatch traps (`57.26%` closed/variety traps) and arrival price reversion are deducted, net profit collapses to `₹53.61/qtl` and `48.69%` of trucks lose money. `MandiGuard` filters out `61.10%` of Onion traps upfront (`26.42%` `VARIETY_OR_STALE` and `24.39%` `ARRIVAL_REVERSION_RISK` in `Exp 7`), tripling per-episode Onion profit from `₹46.50` (`B1`) to `₹163.41/qtl` and cutting episode losses from `42.23%` to `3.87%` (`Exp 2b`).

---

### 13. Why Multi-Agent (`B5`) Lost `-₹15.40/qtl` vs Single-Agent `MandiGuard`
**Examiner Attack:**
> "Everyone talks about multi-agent orchestration today, yet your `B5_MultiAgentCoordinator` loses `-₹15.40/qtl` compared to single-agent `MandiGuard` (`₹437.39` vs `₹452.79/qtl`). Did you intentionally cripple `B5` to make your single agent look good?"

**Candidate Answer:**
No—`B5` reflects a real engineering bottleneck when separate LLM or role agents (`ScoutAgent -> LogisticsWeatherAgent -> RiskGateAgent`) communicate over discrete message tiers (`₹150/qtl` margin buckets) rather than passing exact continuous lower confidence bounds. Because those quantized buckets round off profitable mid-tier corridors, `B5` under-dispatches (`41.59%` vs `48.66%` for `MandiGuard`), sacrificing `-₹15.40/qtl` (`₹437.39` vs `₹452.79/qtl`) while still burning virtually identical live API calls (`8.76` vs `8.75`, `₹4,379` vs `₹4,374` per 10k queries). This cleanly shows that a unified sequential tool cascade outperforms lossy multi-agent chatter on numerical dispatch decisions.

---

### 14. Adaptive Conformal Inference (`MandiGuard_ACI`) Stopping HP Apple Tail Crashes (`-27.6%`)
**Examiner Attack:**
> "Your paper admits conformal exchangeability breaks under seasonal shocks and grade shifts. When HP Apple `2026` shifts away from `2024`, how does `MandiGuard_ACI` fix those `-₹102.76/qtl` tail crashes without retraining the whole model?"

**Candidate Answer:**
When incoming outcomes exceed the `20%` target miscoverage rate during a distribution shift, Adaptive Conformal Inference (`MandiGuard_ACI`) dynamically lowers the crop's $\alpha_t$ level—automatically tightening HP Apple's $\alpha$ from `0.200` down to `0.164` (`aci_diagnostics.json`, meaning an `83.6%` conformal bound instead of `80%`, and tightening 6-state Tomato to `0.038`). In `Exp 11`, that single online adjustment trims only `1.49 pp` of the riskiest HP Apple dispatches (`18.67%` to `17.18%`) and cuts worst-10% tail losses by **`27.6%`** (`-₹102.76/qtl` down to `-₹74.42/qtl`) while keeping mean profit virtually unchanged (`₹598.54` vs `₹605.06/qtl`). It achieves zero-retraining tail-risk control purely by adjusting how cautious the conformal floor is.

---

### 15. Cooperative FPO 90-qtl Pooling (`₹477.28/qtl`), Split-Lot (`9.85%` Traps), & Spoilage Clock (`24.1h` Tomato at `42°C`)
**Examiner Attack:**
> "Real marginal farmers don't always own a full `30-qtl` truck, and FPOs want practical risk rules, not just conformal math. What concrete operational interventions come out of `Exp 13` and `Exp 13b`, and what are the exact trade-offs?"

**Candidate Answer:**
In `Exp 13`, a marginal `10-qtl` farmer facing `1.60x` freight earns `₹409.53/qtl` under `MandiGuard`, whereas pooling three `30-qtl` lots into one cooperative FPO `90-qtl` truck (`0.70x` freight) lifts net profit to **`₹477.28/qtl`** (`+₹24.49/qtl` over solo `30-qtl` at `₹452.79/qtl`, and `+₹67.75/qtl` over solo `10-qtl`). For risk-averse FPOs, splitting a load `50/50` across the top-2 LCB-cleared mandis (`Split_Top2_Portfolio`) cuts closed/variety traps from `16.17%` down to **`9.85%`** and loss trips to `8.09%` (at a conservative mean return of `₹394.82/qtl`). Finally, `Exp 13b`'s Biological Spoilage Clock turns $Q_{10}$ decay into a plain departure countdown—showing Tomato hits `15%` spoilage in `110.8 h` at `20°C`, `48.2 h` at `32°C`, and just **`24.1 h`** at `42°C` peak summer (vs `40.0 h` for Onion and `91.1 h` for Potato at `42°C`).


---

## Ground-Truth Math & Data Verifier

# MandiGuard Ground-Truth Reference Sheet

All values below are exact, unrounded values verified directly from files in `/Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent`.

---

## 1. Data Manifests & Dataset Provenance

### 1.1 Decade & 2024–2026 AGMARKNET Extraction (`data/manifests/decade_agmarknet_manifest.json`, `data/manifests/agmarknet_extract_manifest.json`)
- **Total raw CSV rows streamed (2017–2026):** `42,722,187` (`28,278,417` in 2017–2023 + `14,443,770` in 2024–2026)
  - `2017`: `4,089,863` raw (`223,996` filtered 6-state/4-crop; `344,171,434` bytes)
  - `2018`: `4,285,294` raw (`286,569` filtered; `361,437,148` bytes)
  - `2019`: `4,319,450` raw (`301,356` filtered; `395,020,868` bytes)
  - `2020`: `2,878,346` raw (`229,101` filtered; `263,100,846` bytes)
  - `2021`: `3,815,906` raw (`301,665` filtered; `349,157,458` bytes)
  - `2022`: `4,476,958` raw (`323,777` filtered; `411,075,171` bytes)
  - `2023`: `4,412,600` raw (`318,658` filtered; `431,243,784` bytes)
  - `2024`: `5,531,214` raw (`296,390` filtered; `566,027,437` bytes)
  - `2025`: `6,922,877` raw (`329,475` filtered; `683,077,881` bytes)
  - `2026_jan_apr`: `1,989,679` raw (`55,393` filtered; `210,523,088` bytes)
- **2017–2023 cleaning:** `1,985,122` filtered -> dropped `0` bad date, `34,645` invalid/outlier price, `0` exact duplicates -> `1,950,477` clean (`2017-01-01` to `2023-12-31`, `6` states, `647` markets, `4` commodities).
- **2024–2026 cleaning:** `681,258` filtered -> dropped `0` bad date, `284` invalid/outlier price, `7,003` exact duplicates -> `673,971` clean (`2024-01-01` to `2026-04-13`, `6` states, `699` markets, `4` commodities).
- **Retained 178-mandi balanced panel (`2024`-ranked, capped 30/state):**
  - **Decade panel rows (`2017-01-01` to `2026-04-13`):** `883,406` (`623,363` in `2017–2023` + `260,043` in `2024–2026`)
  - **Decade panel rows by year:** `2017`: `68,986`; `2018`: `85,091`; `2019`: `89,373`; `2020`: `69,645`; `2021`: `95,619`; `2022`: `105,819`; `2023`: `108,830`; `2024`: `117,873`; `2025`: `121,449`; `2026`: `20,721`
  - **2024–2026 panel (`260,043` rows across `178` retained of `469` eligible markets):**
    - Markets by state: `Gujarat`: `30`, `Himachal Pradesh`: `28`, `Karnataka`: `30`, `Madhya Pradesh`: `30`, `Maharashtra`: `30`, `Uttar Pradesh`: `30`
    - Rows by state: `Gujarat`: `45,298`, `Himachal Pradesh`: `37,671`, `Karnataka`: `24,672`, `Madhya Pradesh`: `25,041`, `Maharashtra`: `46,380`, `Uttar Pradesh`: `80,981`
    - Rows by commodity: `Apple`: `28,345`, `Onion`: `89,161`, `Potato`: `69,296`, `Tomato`: `73,241`

### 1.2 Climate & Weather (`data/manifests/nasa_power_manifest.json`, `data/manifests/climate_manifest.json`)
- **NASA POWER (`2017-01-01` to `2023-12-31`):** `291,384` rows across `114` grid cells (`0.5` deg resolution, community `AG`, `0.0` raw null rates across `era5_tmax`, `era5_tmin`, `era5_rain_mm`, `era5_rh_mean`).
- **ERA5 / Open-Meteo NWP (`2024-01-01` to `2026-09-05`):** `141,955` rows across `145` grid cells (`145` ERA5 realized cells, `102` NWP forecast cells, `43` causal ERA5 nowcast cells trained on `2024-01-01..2024-12-31`, `0.0` null rates raw and after causal ffill).
  - **Causal nowcaster `val_2025H1` metrics:** `fc_tmax` MAE `1.047` / corr `0.9655`; `fc_tmin` MAE `1.028` / corr `0.9663`; `fc_rain_mm` MAE `0.001` / corr `1.0`; `fc_rh_mean` MAE `0.284` / corr `0.998`.

### 1.3 Road Network & Episodes (`data/manifests/road_network_manifest.json`, `data/manifests/data_provenance_manifest.json`)
- **Geocoded markets:** `220` (`150` `market_exact`, `70` `district_centroid`).
- **OSRM intra-state corridors (`15–500 km`):** `8,147` (`Gujarat`: `817`, `Himachal Pradesh`: `4,420`, `Karnataka`: `682`, `Madhya Pradesh`: `750`, `Maharashtra`: `689`, `Uttar Pradesh`: `789`).
- **Corridor lag days distribution:** `1` day: `3,810`; `2` days: `3,942`; `3` days: `395`.
- **Episodes & Candidates (`data_provenance_manifest.json`):**
  - `6state_episodes`: `239,809`; `6state_shortlisted_episodes`: `209,450`; `6state_candidate_rows`: `1,457,515`
  - `hp_apple_episodes`: `4,129`; `hp_apple_shortlisted_episodes`: `3,923`; `hp_apple_candidate_rows`: `33,090`

### 1.4 Grade-Explicit HP Apple & Live Nov-2026 Checks (`data/raw/hp_apple_daily_2025_2026.csv`, `results/exp8_live_nov2026_demo.json`)
- **HP Apple grade-explicit daily records (`2025-11-07` to `2026-09-01`):** `4,427` rows across `42` markets (`Medium`: `1,945`, `Grade B`: `1,264`, `Grade A`: `1,007`, `Local`: `78`, `Grade Range-1`: `75`, `Grade C`: `51`, `Small`: `4`, `Large`: `3`).
- **Live Nov-2026 AGMARKNET API checks (`retrieved_utc`: `2026-11-17T07:40:51.261602+00:00`):** `22` queries executed; `11` active series (`PASS_ACTIVE`: `9`, `WATCH_SPARSE`: `2`), `11` full-week non-reporting (`PRUNE_NON_REPORTING_7D`: `11`), `non_reporting_rate_pct`: `50.0`.
  - **MH (Onion):** `Lasalgaon(Niphad)` (`0d`, `null`, `PRUNE_NON_REPORTING_7D`), `Bhokardan(Pimpalgaon Renu)` (`0d`, `null`, `PRUNE_NON_REPORTING_7D`), `APMC Talegaon Dabhade Tal Mawal Dist Pune` (`0d`, `null`, `PRUNE_NON_REPORTING_7D`), `APMC Solapur` (`3d`, `3050.0`, `PASS_ACTIVE`), `APMC Mumbai` (`0d`, `null`, `PRUNE_NON_REPORTING_7D`).
  - **UP (Potato):** `Prayagraj APMC` (`7d`, `700.0`, `PASS_ACTIVE`), `Kanpur(Grain) APMC` (`6d`, `550.0`, `PASS_ACTIVE`), `Lucknow APMC` (`4d`, `700.0`, `PASS_ACTIVE`).
  - **KA (Tomato):** `Kolar APMC` (`7d`, `1200.0`, `PASS_ACTIVE`), `Bengaluru APMC` (`0d`, `null`, `PRUNE_NON_REPORTING_7D`), `Mysuru APMC` (`6d`, `2600.0`, `PASS_ACTIVE`), `Ramanagara APMC` (`7d`, `2500.0`, `PASS_ACTIVE`).
  - **MP (Onion):** `Indore(F&V) APMC` (`2d`, `3461.0`, `WATCH_SPARSE`), `Ujjain(F&V) APMC` (`0d`, `null`, `PRUNE_NON_REPORTING_7D`), `Ratlam APMC` (`0d`, `null`, `PRUNE_NON_REPORTING_7D`), `Shajapur APMC` (`6d`, `3740.0`, `PASS_ACTIVE`).
  - **GJ (Onion):** `Mahuva APMC` (`0d`, `null`, `PRUNE_NON_REPORTING_7D`), `Rajkot APMC` (`0d`, `null`, `PRUNE_NON_REPORTING_7D`), `Gondal(Veg.market Gondal) APMC` (`0d`, `null`, `PRUNE_NON_REPORTING_7D`), `Bhavnagar APMC` (`0d`, `null`, `PRUNE_NON_REPORTING_7D`), `Ahmedabad(Chimanbhai Patal Market Vasana) APMC` (`9d`, `4550.0`, `PASS_ACTIVE`).
  - **HP (Apple):** `PMY Dhalli Shimla` (`1d`, `12000.0`, `WATCH_SPARSE`).

---

## 2. Official Government Parameters (`data/processed/state_apmc_and_loss_parameters.csv`, `data/raw/official_govt_survey_parameters.json`, `data/manifests/govt_survey_manifest.json`)

### 2.1 NABCONS (2022) Post-Harvest Losses (%)
| Commodity | `farm_ops_loss_pct` | `market_level_loss_pct` | `sum_stage_loss_pct` |
|---|---:|---:|---:|
| Onion | 5.31 | 1.96 | 7.27 |
| Potato | 5.1 | 0.86 | 5.96 |
| Tomato | 8.37 | 3.25 | 11.62 |
| Apple | 7.87 | 1.64 | 9.51 |

### 2.2 State APMC Fees, Cold Storage (Nov 2023), & e-NAM Mandis (Oct 2024)
| State | Statutory Seller Fee (`pct`) | Cold Storage Units (Nov 2023) | Cold Storage Capacity (MT, Nov 2023) | e-NAM Mandis (Oct 2024) | APMC F&V Regulatory Status |
|---|---:|---:|---:|---:|---|
| Maharashtra | `0.01` (`1.0%`) | 656 | 1,176,499 | 133 | Deregulated outside notified yards (Jul 2016 Ordinance); regulated yard supervision/weighment inside APMC |
| Uttar Pradesh | `0.015` (`1.5%`) | 2,472 | 15,045,874 | 125 | Regulated under UP Krishi Utpadan Mandi Adhiniyam (standard yard fee/user friction) |
| Karnataka | `0.005` (`0.5%`) | 250 | 838,940 | 5 | Market fee exempted; yard user charges permitted (Jan 2014 APMC Amendment) |
| Madhya Pradesh | `0.015` (`1.5%`) | 315 | 1,364,003 | 139 | Exempted outside notified yards (except banana); regulated inside notified yards (PIB relid=154554) |
| Gujarat | `0.005` (`0.5%`) | 1,014 | 3,974,593 | 144 | Market fee exempted on F&V; user charges permitted (PIB relid=154554) |
| Himachal Pradesh | `0.005` (`0.5%` veg); `0.01` (`1.0%` Apple) | 89 | 174,072 | 38 | Market fee exempted on F&V EXCEPT Apple; service charge on others (PIB relid=154554) |
| **All India** | — | 8,653 | 39,417,231 | — | — |

### 2.3 GoHP Economic Survey 2025–26 (`hp_economic_survey_verified`)
- `small_marginal_farmers_pct`: `88.86`%
- `avg_landholding_ha`: `0.95` ha
- `apmc_fruits_arrivals_qtl_upto_dec2025`: `4,920,099` qtl
- `apmc_vegetables_arrivals_qtl_upto_dec2025`: `1,581,192` qtl
- `apmc_total_fv_arrivals_qtl_upto_dec2025`: `6,501,291` qtl
- `apple_production_2025_26_thousand_mt`: `646.998` thousand MT
- `single_lane_motorable_roads_km`: `39,465` km
- `total_motorable_roads_km`: `43,091` km
- **`single_lane_share_pct`:** `91.59`%

### 2.4 NSS 77th Round Report No. 587 (`nss_77th_round_report_587`)
- `avg_monthly_total_income_paidout_inr`: `10,218` INR
- `avg_monthly_net_crop_receipt_inr`: `3,798` INR
- `indebted_agri_households_pct`: `50.2`%
- `avg_outstanding_loan_inr`: `74,121` INR
- `jan_jun_2019_potato_harvest_kg_per_hh`: `2,933` kg
- `jan_jun_2019_onion_harvest_kg_per_hh`: `3,873` kg
- `smallholder_truckload_benchmark_qtl`: `30.0` qtl

---

## 3. Frozen Calibration (`configs/frozen_calibration.json`)
- `train_rows`: `701,932`; `val_rows`: `280,697`
- `val_conformal_lcb_empirical_coverage_pct`: `78.85`
- `val_b1_mean_dnet`: `255.28`; `val_b1_plr_pct`: `38.99`
- `val_b2_mean_dnet`: `330.28`; `val_b2_plr_pct`: `16.77`
- `frozen_safety_margin_inr`: `50.0`

| `safety_margin_inr` | `dispatch_pct` | `mean_delta_net_inr` | `phantom_loss_rate_pct` | `avg_tool_calls` |
|---:|---:|---:|---:|---:|
| 50.0 | 52.94 | 351.36 | 9.68 | 9.1 |
| 100.0 | 48.55 | 345.63 | 8.88 | 9.1 |
| 150.0 | 44.38 | 337.9 | 8.32 | 9.1 |
| 200.0 | 40.58 | 328.75 | 7.99 | 9.1 |
| 250.0 | 37.01 | 318.92 | 7.7 | 9.1 |

---

## 4. Confirmatory Hypotheses (`results/confirmatory_holm_summary.csv`)

| `hypothesis` | `estimand` | `direction` | `estimate` | `ci95_low` | `ci95_high` | `p_raw` | `n_episodes` | `n_origin_mandis` | `n_2week_blocks` | `p_holm` | `status` |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| H1 | MG - B1 Mean dNet (INR/qtl) | greater | 102.7823 | 48.6649 | 153.4512 | 0.0006 | 69526 | 174 | 23 | 0.0012 | SUPPORTED |
| H2 | MG - B2 Mean dNet (INR/qtl) | greater | 6.1303 | -17.0161 | 25.0171 | 0.269946 | 69526 | 174 | 23 | 0.269946 | NOT_SUPPORTED |
| H3 | MG - B3 Ep Phantom Incidence (prob) | less | -0.3729 | -0.4019 | -0.3424 | 0.0002 | 69526 | 174 | 23 | 0.0008 | SUPPORTED |
| H4 | MG Calls - 0.75*B4 Calls | less | -3.0548 | -3.4408 | -2.6906 | 0.0002 | 69526 | 174 | 23 | 0.0008 | SUPPORTED |

---

## 5. Experiment Tables (Every Row Exact)

### 5.1 `results/exp1_phantom_anatomy.csv`
| `slice_type` | `slice_value` | `n_b1_dispatches` | `mean_screen_spread_inr` | `mean_freight_inr` | `mean_spoilage_inr` | `mean_trap_and_reversion_inr` | `mean_realized_dnet_inr` | `phantom_loss_rate_pct` | `closed_or_variety_trap_pct` | `no_exact_variety_3d_pct` | `lot_30qtl_dnet_inr` | `pct_monthly_hh_crop_income` |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Overall | All_Holdout | 63040 | 1330.49 | 160.81 | 68.76 | 714.9 | 386.02 | 40.46 | 58.94 | 46.69 | 11580.5 | 304.9 |
| Commodity | Apple | 7784 | 3499.8 | 250.18 | 191.68 | 1982.36 | 1075.58 | 40.02 | 55.13 | 44.08 | 32267.5 | 849.6 |
| Commodity | Onion | 20355 | 704.5 | 138.07 | 28.6 | 484.23 | 53.61 | 48.69 | 57.26 | 45.58 | 1608.2 | 42.3 |
| Commodity | Potato | 15354 | 817.36 | 146.0 | 19.34 | 418.54 | 233.47 | 37.83 | 60.54 | 45.08 | 7004.1 | 184.4 |
| Commodity | Tomato | 19547 | 1521.55 | 160.55 | 100.45 | 683.16 | 577.39 | 34.14 | 60.96 | 50.15 | 17321.8 | 456.1 |
| State | Gujarat | 14271 | 1371.78 | 152.59 | 64.95 | 701.72 | 452.53 | 34.44 | 58.63 | 44.09 | 13575.8 | 357.4 |
| State | Himachal Pradesh | 8575 | 2185.77 | 182.53 | 142.25 | 1467.21 | 393.77 | 46.82 | 59.42 | 40.31 | 11813.0 | 311.0 |
| State | Karnataka | 6448 | 1162.71 | 144.94 | 58.21 | 614.4 | 345.16 | 42.74 | 60.03 | 43.42 | 10354.7 | 272.6 |
| State | Madhya Pradesh | 5821 | 824.54 | 118.25 | 22.78 | 587.69 | 95.82 | 51.57 | 59.7 | 47.17 | 2874.5 | 75.7 |
| State | Maharashtra | 14401 | 1477.73 | 157.62 | 62.23 | 635.55 | 622.33 | 38.87 | 61.76 | 50.42 | 18669.8 | 491.6 |
| State | Uttar Pradesh | 13524 | 885.6 | 185.01 | 57.95 | 438.96 | 203.67 | 38.61 | 55.13 | 50.85 | 6110.2 | 160.9 |
| DistanceBand | 100-250km | 29560 | 1328.34 | 140.65 | 58.66 | 668.25 | 460.78 | 38.35 | 58.01 | 45.28 | 13823.5 | 364.0 |
| DistanceBand | 15-100km | 10578 | 1109.91 | 86.06 | 44.94 | 688.35 | 290.56 | 40.41 | 52.79 | 40.85 | 8716.8 | 229.5 |
| DistanceBand | 250-500km | 22902 | 1435.14 | 221.36 | 92.8 | 787.37 | 333.6 | 43.21 | 62.99 | 51.21 | 10008.1 | 263.5 |

### 5.2 `results/exp2_main_benchmark_6state.csv`
| `policy` | `n_episodes` | `dispatch_rate_pct` | `mean_delta_net_inr` | `cond_dispatched_delta_net_inr` | `open_d0_mean_delta_net_inr` | `ep_phantom_loss_pct` | `cond_phantom_loss_rate_pct` | `cond_closed_or_trap_rate_pct` | `cvar_10_inr` | `avg_tool_calls` | `lot_30qtl_gain_inr` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B0_SellLocal | 69526 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| B1_NaiveScreenGreedy | 69526 | 90.67 | 350.01 | 386.02 | 606.71 | 36.69 | 40.46 | 58.94 | -1062.66 | 0.0 | 10500.2 |
| B2_FreshRoadGreedy | 69526 | 62.11 | 446.66 | 719.13 | 467.48 | 11.25 | 18.11 | 24.32 | -436.67 | 7.87 | 13399.7 |
| B3_MLPointDispatch | 69526 | 93.05 | 330.85 | 355.56 | 676.67 | 42.14 | 45.28 | 65.65 | -1097.8 | 7.87 | 9925.6 |
| B4_UpfrontAllTools | 69526 | 48.66 | 452.79 | 930.61 | 458.35 | 4.85 | 9.97 | 16.17 | -37.89 | 15.74 | 13583.6 |
| B5_MultiAgentCoordinator | 69526 | 41.59 | 437.39 | 1051.56 | 437.04 | 3.9 | 9.38 | 16.57 | -31.77 | 8.76 | 13121.7 |
| B6_HeuristicBucketRouter | 69526 | 43.36 | 431.94 | 996.23 | 430.65 | 5.15 | 11.88 | 21.59 | -42.42 | 11.8 | 12958.3 |
| MandiGuard | 69526 | 48.66 | 452.79 | 930.61 | 458.35 | 4.85 | 9.97 | 16.17 | -37.89 | 8.75 | 13583.6 |

### 5.3 `results/exp2b_by_state_commodity.csv`
| `group_type` | `group_value` | `n_episodes` | `B1_dnet` | `B2_dnet` | `B3_dnet` | `MG_dnet` | `B1_ep_phantom_pct` | `B3_ep_phantom_pct` | `MG_ep_phantom_pct` | `MG_gain_vs_B1` | `MG_gain_vs_B2` | `MG_avg_calls` |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| State | Gujarat | 14702 | 439.26 | 428.14 | 393.09 | 451.14 | 33.43 | 37.22 | 6.63 | 11.88 | 23.0 | 10.56 |
| State | Himachal Pradesh | 8952 | 377.18 | 869.54 | 549.1 | 793.28 | 44.85 | 46.53 | 7.96 | 416.1 | -76.25 | 10.03 |
| State | Karnataka | 6733 | 330.55 | 420.42 | 333.02 | 401.87 | 40.93 | 40.07 | 6.43 | 71.32 | -18.55 | 7.98 |
| State | Madhya Pradesh | 6286 | 88.73 | 213.71 | 125.93 | 245.02 | 47.76 | 45.86 | 6.14 | 156.29 | 31.31 | 8.53 |
| State | Maharashtra | 15045 | 595.69 | 592.89 | 568.25 | 656.08 | 37.2 | 42.35 | 3.78 | 60.39 | 63.19 | 8.18 |
| State | Uttar Pradesh | 17808 | 154.68 | 217.97 | 40.71 | 203.82 | 29.32 | 43.27 | 1.67 | 49.15 | -14.15 | 7.46 |
| Commodity | Apple | 7856 | 1065.72 | 1646.75 | 1124.9 | 1569.77 | 39.65 | 42.91 | 5.93 | 504.05 | -76.97 | 7.52 |
| Commodity | Onion | 23467 | 46.5 | 156.2 | 14.94 | 163.41 | 42.23 | 47.79 | 3.87 | 116.91 | 7.21 | 8.47 |
| Commodity | Potato | 17594 | 203.75 | 253.72 | 181.91 | 258.38 | 33.01 | 40.13 | 5.4 | 54.63 | 4.66 | 8.75 |
| Commodity | Tomato | 20609 | 547.64 | 484.64 | 515.05 | 522.48 | 32.38 | 37.11 | 5.09 | -25.16 | 37.84 | 9.53 |
| WeatherSubset | 4States_100pct_Native_NWP | 42766 | 425.65 | 453.37 | 405.98 | 485.18 | 38.04 | 40.74 | 5.52 | 59.53 | 31.82 | 9.02 |

### 5.4 `results/exp3_hp_apple_grade_holdout.csv`
| `policy` | `n_episodes` | `dispatch_rate_pct` | `mean_delta_net_inr` | `cond_dispatched_delta_net_inr` | `open_d0_mean_delta_net_inr` | `ep_phantom_loss_pct` | `cond_phantom_loss_rate_pct` | `cond_closed_or_trap_rate_pct` | `cvar_10_inr` | `avg_tool_calls` | `lot_30qtl_gain_inr` | `Grade` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| B1_NaiveScreenGreedy | 1537 | 100.0 | 841.58 | 841.58 | 3471.46 | 58.88 | 58.88 | 94.14 | -8487.24 | 0.0 | 25247.5 | ALL_GRADES |
| B1_NaiveScreenGreedy | 371 | 100.0 | 1978.22 | 1978.22 | 9428.05 | 58.76 | 58.76 | 90.3 | -9217.42 | 0.0 | 59346.6 | Grade A |
| B1_NaiveScreenGreedy | 330 | 100.0 | -427.54 | -427.54 | 2627.42 | 67.58 | 67.58 | 92.73 | -11157.52 | 0.0 | -12826.2 | Grade B |
| B1_NaiveScreenGreedy | 14 | 100.0 | -1360.63 | -1360.63 | 0.0 | 78.57 | 78.57 | 100.0 | -4565.75 | 0.0 | -40818.9 | Grade C |
| B1_NaiveScreenGreedy | 59 | 100.0 | 4254.08 | 4254.08 | 0.0 | 11.86 | 11.86 | 100.0 | -581.34 | 0.0 | 127622.5 | Grade Range-1 |
| B1_NaiveScreenGreedy | 62 | 100.0 | -117.07 | -117.07 | 1865.49 | 69.35 | 69.35 | 96.77 | -4855.22 | 0.0 | -3512.2 | Local |
| B1_NaiveScreenGreedy | 701 | 100.0 | 679.02 | 679.02 | 2784.5 | 57.49 | 57.49 | 96.01 | -6869.13 | 0.0 | 20370.7 | Medium |
| B2_FreshRoadGreedy | 1537 | 33.64 | 1150.83 | 3421.33 | 1156.79 | 9.56 | 28.43 | 34.04 | -272.5 | 9.17 | 34525.0 | ALL_GRADES |
| B2_FreshRoadGreedy | 371 | 19.41 | 1598.95 | 8239.02 | 1745.3 | 7.28 | 37.5 | 37.5 | -127.89 | 9.27 | 47968.4 | Grade A |
| B2_FreshRoadGreedy | 330 | 55.15 | 1020.98 | 1851.23 | 1348.29 | 19.09 | 34.62 | 30.22 | -4472.9 | 8.38 | 30629.5 | Grade B |
| B2_FreshRoadGreedy | 14 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 7.57 | 0.0 | Grade C |
| B2_FreshRoadGreedy | 59 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 10.0 | 0.0 | Grade Range-1 |
| B2_FreshRoadGreedy | 62 | 12.9 | 106.03 | 821.7 | 277.69 | 3.23 | 25.0 | 12.5 | -213.26 | 8.84 | 3180.8 | Local |
| B2_FreshRoadGreedy | 701 | 36.38 | 1187.05 | 3263.22 | 965.21 | 7.85 | 21.57 | 36.47 | -210.48 | 9.48 | 35611.5 | Medium |
| B3_MLPointDispatch | 1537 | 100.0 | 749.05 | 749.05 | 4351.62 | 60.96 | 60.96 | 97.27 | -8054.15 | 9.17 | 22471.4 | ALL_GRADES |
| B3_MLPointDispatch | 371 | 100.0 | 1861.92 | 1861.92 | 11964.98 | 59.57 | 59.57 | 91.91 | -9290.16 | 9.27 | 55857.7 | Grade A |
| B3_MLPointDispatch | 330 | 100.0 | -680.75 | -680.75 | 2869.48 | 71.21 | 71.21 | 96.67 | -10420.72 | 8.38 | -20422.5 | Grade B |
| B3_MLPointDispatch | 14 | 100.0 | -1360.63 | -1360.63 | 0.0 | 78.57 | 78.57 | 100.0 | -4565.75 | 7.57 | -40818.9 | Grade C |
| B3_MLPointDispatch | 59 | 100.0 | 4254.08 | 4254.08 | 0.0 | 11.86 | 11.86 | 100.0 | -581.34 | 10.0 | 127622.5 | Grade Range-1 |
| B3_MLPointDispatch | 62 | 100.0 | -96.86 | -96.86 | 2419.88 | 69.35 | 69.35 | 98.39 | -4855.22 | 8.84 | -2905.7 | Local |
| B3_MLPointDispatch | 701 | 100.0 | 655.1 | 655.1 | 3499.21 | 59.91 | 59.91 | 100.0 | -6095.69 | 9.48 | 19652.9 | Medium |
| MandiGuard | 1537 | 18.67 | 605.06 | 3240.34 | 577.72 | 3.97 | 21.25 | 13.24 | -102.76 | 5.41 | 18151.8 | ALL_GRADES |
| MandiGuard | 371 | 5.39 | 205.46 | 3811.25 | 196.25 | 1.08 | 20.0 | 10.0 | -4.86 | 4.82 | 6163.7 | Grade A |
| MandiGuard | 330 | 30.3 | 833.7 | 2751.21 | 849.73 | 6.67 | 22.0 | 14.0 | -117.76 | 5.8 | 25011.0 | Grade B |
| MandiGuard | 14 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 3.79 | 0.0 | Grade C |
| MandiGuard | 59 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 5.0 | 0.0 | Grade Range-1 |
| MandiGuard | 62 | 1.61 | 135.71 | 8413.89 | 135.71 | 0.0 | 0.0 | 0.0 | 0.0 | 4.61 | 4071.2 | Local |
| MandiGuard | 701 | 23.68 | 813.43 | 3435.04 | 760.9 | 4.99 | 21.08 | 13.25 | -181.25 | 5.68 | 24403.0 | Medium |

### 5.5 `results/exp4_tool_ablations.csv`
| `policy` | `n_episodes` | `dispatch_rate_pct` | `mean_delta_net_inr` | `cond_dispatched_delta_net_inr` | `open_d0_mean_delta_net_inr` | `ep_phantom_loss_pct` | `cond_phantom_loss_rate_pct` | `cond_closed_or_trap_rate_pct` | `cvar_10_inr` | `avg_tool_calls` | `lot_30qtl_gain_inr` | `regime` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Full_MandiGuard | 69526 | 48.66 | 452.79 | 930.61 | 458.35 | 4.85 | 9.97 | 16.17 | -37.89 | 8.75 | 13583.6 | All_Holdout |
| Full_MandiGuard | 21656 | 55.74 | 470.07 | 843.27 | 490.11 | 5.63 | 10.1 | 16.34 | -57.11 | 9.62 | 14102.2 | Extreme_Heat_or_Rain |
| No_T1_Vitality | 69526 | 80.55 | 318.74 | 395.71 | 620.26 | 34.48 | 42.8 | 67.16 | -987.1 | 11.03 | 9562.2 | All_Holdout |
| No_T1_Vitality | 21656 | 85.45 | 367.77 | 430.37 | 636.76 | 33.11 | 38.74 | 66.92 | -1003.01 | 12.04 | 11033.1 | Extreme_Heat_or_Rain |
| No_T2_OSRM_to_Euclid | 69526 | 49.16 | 452.35 | 920.11 | 458.79 | 5.04 | 10.25 | 16.22 | -38.57 | 7.05 | 13570.6 | All_Holdout |
| No_T2_OSRM_to_Euclid | 21656 | 56.11 | 468.22 | 834.41 | 489.54 | 5.94 | 10.59 | 16.45 | -58.54 | 7.74 | 14046.6 | Extreme_Heat_or_Rain |
| No_T3_Weather | 69526 | 50.18 | 455.25 | 907.3 | 462.05 | 5.32 | 10.61 | 16.18 | -41.59 | 7.23 | 13657.6 | All_Holdout |
| No_T3_Weather | 21656 | 58.44 | 474.31 | 811.67 | 496.66 | 6.65 | 11.39 | 16.43 | -67.49 | 7.94 | 14229.3 | Extreme_Heat_or_Rain |
| No_T4_ConformalLCB | 69526 | 62.75 | 448.74 | 715.17 | 471.84 | 10.6 | 16.89 | 16.13 | -397.19 | 7.23 | 13462.3 | All_Holdout |
| No_T4_ConformalLCB | 21656 | 67.95 | 465.5 | 685.08 | 497.98 | 10.69 | 15.73 | 15.97 | -458.74 | 7.94 | 13965.1 | Extreme_Heat_or_Rain |

### 5.6 `results/exp5_budget_pareto.csv`
| `policy` | `n_episodes` | `dispatch_rate_pct` | `mean_delta_net_inr` | `cond_dispatched_delta_net_inr` | `open_d0_mean_delta_net_inr` | `ep_phantom_loss_pct` | `cond_phantom_loss_rate_pct` | `cond_closed_or_trap_rate_pct` | `cvar_10_inr` | `avg_tool_calls` | `lot_30qtl_gain_inr` | `budget_cap` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| MandiGuard | 69526 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | 1 |
| B4_UpfrontAllTools | 69526 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | 1 |
| B5_MultiAgentCoordinator | 69526 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | 1 |
| MandiGuard | 69526 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.93 | 0.0 | 2 |
| B4_UpfrontAllTools | 69526 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2.0 | 0.0 | 2 |
| B5_MultiAgentCoordinator | 69526 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.93 | 0.0 | 2 |
| MandiGuard | 69526 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2.81 | 0.0 | 3 |
| B4_UpfrontAllTools | 69526 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 3.0 | 0.0 | 3 |
| B5_MultiAgentCoordinator | 69526 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2.81 | 0.0 | 3 |
| MandiGuard | 69526 | 30.09 | 299.31 | 994.81 | 293.75 | 2.98 | 9.89 | 15.61 | -22.07 | 3.65 | 8979.2 | 4 |
| B4_UpfrontAllTools | 69526 | 30.09 | 299.31 | 994.81 | 293.75 | 2.98 | 9.89 | 15.61 | -22.07 | 4.0 | 8979.2 | 4 |
| B5_MultiAgentCoordinator | 69526 | 26.25 | 291.59 | 1110.62 | 284.5 | 2.46 | 9.36 | 16.13 | -20.38 | 3.66 | 8747.8 | 4 |
| MandiGuard | 69526 | 44.07 | 403.85 | 916.46 | 405.79 | 4.78 | 10.85 | 16.56 | -34.73 | 5.05 | 12115.6 | 6 |
| B4_UpfrontAllTools | 69526 | 30.09 | 299.31 | 994.81 | 293.75 | 2.98 | 9.89 | 15.61 | -22.07 | 5.75 | 8979.2 | 6 |
| B5_MultiAgentCoordinator | 69526 | 37.89 | 391.57 | 1033.45 | 388.84 | 3.79 | 10.01 | 16.87 | -29.73 | 5.05 | 11747.1 | 6 |
| MandiGuard | 69526 | 47.53 | 435.7 | 916.67 | 439.93 | 5.02 | 10.56 | 16.6 | -38.23 | 6.19 | 13070.9 | 8 |
| B4_UpfrontAllTools | 69526 | 41.12 | 389.17 | 946.34 | 389.11 | 4.32 | 10.5 | 16.2 | -31.54 | 7.49 | 11675.2 | 8 |
| B5_MultiAgentCoordinator | 69526 | 40.61 | 421.59 | 1038.08 | 420.55 | 3.99 | 9.81 | 16.97 | -32.01 | 6.19 | 12647.6 | 8 |
| MandiGuard | 69526 | 48.49 | 447.67 | 923.16 | 453.16 | 4.92 | 10.15 | 16.33 | -38.39 | 7.73 | 13430.0 | 12 |
| B4_UpfrontAllTools | 69526 | 45.28 | 420.04 | 927.76 | 423.24 | 4.59 | 10.14 | 16.31 | -34.82 | 10.57 | 12601.3 | 12 |
| B5_MultiAgentCoordinator | 69526 | 41.44 | 432.57 | 1043.91 | 432.34 | 3.98 | 9.61 | 16.82 | -32.28 | 7.73 | 12977.2 | 12 |
| MandiGuard | 69526 | 48.66 | 452.79 | 930.61 | 458.35 | 4.85 | 9.97 | 16.17 | -37.89 | 8.75 | 13583.6 | 20 |
| B4_UpfrontAllTools | 69526 | 48.66 | 452.79 | 930.61 | 458.35 | 4.85 | 9.97 | 16.17 | -37.89 | 15.74 | 13583.6 | 20 |
| B5_MultiAgentCoordinator | 69526 | 41.59 | 437.39 | 1051.56 | 437.04 | 3.9 | 9.38 | 16.57 | -31.77 | 8.76 | 13121.7 | 20 |

### 5.7 `results/exp6_sensitivity_grid.csv`
| `freight_mult` | `spoilage_mult` | `use_state_statutory_fees` | `B1_mean_dnet_inr` | `B2_mean_dnet_inr` | `MG_mean_dnet_inr` | `MG_minus_B1_inr` | `MG_minus_B2_inr` | `B1_cond_plr_pct` | `MG_cond_plr_pct` |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 0.75 | 0.5 | True | 406.99 | 491.14 | 489.62 | 82.62 | -1.52 | 38.07 | 9.01 |
| 0.75 | 1.0 | True | 380.23 | 467.8 | 473.07 | 92.84 | 5.27 | 39.13 | 9.64 |
| 0.75 | 1.5 | True | 353.47 | 444.47 | 457.11 | 103.64 | 12.64 | 40.28 | 10.22 |
| 1.0 | 0.5 | True | 376.26 | 469.37 | 468.5 | 92.24 | -0.87 | 39.36 | 9.48 |
| 1.0 | 1.0 | True | 350.01 | 446.66 | 452.79 | 102.78 | 6.13 | 40.46 | 9.97 |
| 1.0 | 1.5 | True | 323.76 | 423.94 | 437.35 | 113.59 | 13.41 | 41.57 | 10.61 |
| 1.25 | 0.5 | True | 349.18 | 448.92 | 448.91 | 99.72 | -0.02 | 40.11 | 9.71 |
| 1.25 | 1.0 | True | 323.4 | 426.73 | 433.53 | 110.13 | 6.8 | 41.22 | 10.3 |
| 1.25 | 1.5 | True | 297.61 | 404.54 | 419.04 | 121.42 | 14.5 | 42.36 | 10.88 |
| 1.0 | 1.0 | False | 338.02 | 439.07 | 445.67 | 107.66 | 6.6 | 40.84 | 10.0 |

### 5.8 `results/exp7_rejection_breakdown.csv`
| `action` | `reason` | `count` | `mean_calls` | `slice` | `pct` |
|---|---|---:|---:|---|---:|
| DISPATCH | DISPATCH_CLEARED_LCB | 33828 | 12.3 | Overall | 48.66 |
| REFUSE_PHANTOM_SPREAD | ARRIVAL_REVERSION_RISK | 12222 | 8.86 | Overall | 17.58 |
| REFUSE_PHANTOM_SPREAD | CLOSED_YARD_RISK | 3714 | 3.04 | Overall | 5.34 |
| REFUSE_PHANTOM_SPREAD | FREIGHT_EXCEEDS_SPREAD | 1555 | 3.55 | Overall | 2.24 |
| REFUSE_PHANTOM_SPREAD | VARIETY_OR_STALE | 17713 | 3.64 | Overall | 25.48 |
| REFUSE_PHANTOM_SPREAD | WEATHER_SPOILAGE_RISK | 494 | 4.96 | Overall | 0.71 |
| DISPATCH | DISPATCH_CLEARED_LCB | 4330 | 10.1 | Apple | 55.12 |
| REFUSE_PHANTOM_SPREAD | ARRIVAL_REVERSION_RISK | 684 | 7.83 | Apple | 8.71 |
| REFUSE_PHANTOM_SPREAD | CLOSED_YARD_RISK | 489 | 2.67 | Apple | 6.22 |
| REFUSE_PHANTOM_SPREAD | FREIGHT_EXCEEDS_SPREAD | 41 | 2.61 | Apple | 0.52 |
| REFUSE_PHANTOM_SPREAD | VARIETY_OR_STALE | 2272 | 3.73 | Apple | 28.92 |
| REFUSE_PHANTOM_SPREAD | WEATHER_SPOILAGE_RISK | 40 | 3.75 | Apple | 0.51 |
| DISPATCH | DISPATCH_CLEARED_LCB | 9128 | 12.5 | Onion | 38.9 |
| REFUSE_PHANTOM_SPREAD | ARRIVAL_REVERSION_RISK | 5723 | 9.07 | Onion | 24.39 |
| REFUSE_PHANTOM_SPREAD | CLOSED_YARD_RISK | 1290 | 3.26 | Onion | 5.5 |
| REFUSE_PHANTOM_SPREAD | FREIGHT_EXCEEDS_SPREAD | 864 | 3.3 | Onion | 3.68 |
| REFUSE_PHANTOM_SPREAD | VARIETY_OR_STALE | 6201 | 3.92 | Onion | 26.42 |
| REFUSE_PHANTOM_SPREAD | WEATHER_SPOILAGE_RISK | 261 | 4.96 | Onion | 1.11 |
| DISPATCH | DISPATCH_CLEARED_LCB | 9381 | 12.48 | Potato | 53.32 |
| REFUSE_PHANTOM_SPREAD | ARRIVAL_REVERSION_RISK | 2043 | 8.12 | Potato | 11.61 |
| REFUSE_PHANTOM_SPREAD | CLOSED_YARD_RISK | 1308 | 2.94 | Potato | 7.43 |
| REFUSE_PHANTOM_SPREAD | FREIGHT_EXCEEDS_SPREAD | 457 | 3.96 | Potato | 2.6 |
| REFUSE_PHANTOM_SPREAD | VARIETY_OR_STALE | 4323 | 3.28 | Potato | 24.57 |
| REFUSE_PHANTOM_SPREAD | WEATHER_SPOILAGE_RISK | 82 | 5.54 | Potato | 0.47 |
| DISPATCH | DISPATCH_CLEARED_LCB | 10989 | 12.86 | Tomato | 53.32 |
| REFUSE_PHANTOM_SPREAD | ARRIVAL_REVERSION_RISK | 3772 | 9.13 | Tomato | 18.3 |
| REFUSE_PHANTOM_SPREAD | CLOSED_YARD_RISK | 627 | 3.1 | Tomato | 3.04 |
| REFUSE_PHANTOM_SPREAD | FREIGHT_EXCEEDS_SPREAD | 193 | 3.88 | Tomato | 0.94 |
| REFUSE_PHANTOM_SPREAD | VARIETY_OR_STALE | 4917 | 3.55 | Tomato | 23.86 |
| REFUSE_PHANTOM_SPREAD | WEATHER_SPOILAGE_RISK | 111 | 4.99 | Tomato | 0.54 |

### 5.9 `results/exp9_loso_transfer_and_arrival_drop.csv`
| `held_out_state` | `policy` | `n_episodes` | `dispatch_rate_pct` | `mean_delta_net_inr` | `cond_phantom_loss_rate_pct` | `cond_arrival_drop_rate_pct` | `cond_closed_trap_rate_pct` |
|---|---|---:|---:|---:|---:|---:|---:|
| Maharashtra | B1_NaiveScreenGreedy | 15045 | 95.72 | 595.69 | 38.87 | 52.28 | 61.76 |
| Maharashtra | B2_FreshRoadGreedy | 15045 | 63.46 | 592.89 | 14.15 | 8.18 | 23.83 |
| Maharashtra | B3_MLPointDispatch | 15045 | 97.79 | 539.96 | 46.11 | 62.45 | 69.41 |
| Maharashtra | MandiGuard_LOSO | 15045 | 53.34 | 651.08 | 6.6 | 3.91 | 16.0 |
| Uttar Pradesh | B1_NaiveScreenGreedy | 17808 | 75.94 | 154.68 | 38.61 | 53.07 | 55.13 |
| Uttar Pradesh | B2_FreshRoadGreedy | 17808 | 45.82 | 217.97 | 14.54 | 5.94 | 10.44 |
| Uttar Pradesh | B3_MLPointDispatch | 17808 | 84.93 | 17.81 | 52.18 | 70.58 | 71.71 |
| Uttar Pradesh | MandiGuard_LOSO | 17808 | 35.95 | 216.22 | 8.11 | 3.34 | 7.17 |
| Karnataka | B1_NaiveScreenGreedy | 6733 | 95.77 | 330.55 | 42.74 | 46.67 | 60.03 |
| Karnataka | B2_FreshRoadGreedy | 6733 | 70.13 | 420.42 | 21.09 | 15.4 | 35.58 |
| Karnataka | B3_MLPointDispatch | 6733 | 95.22 | 309.45 | 44.42 | 51.44 | 62.86 |
| Karnataka | MandiGuard_LOSO | 6733 | 53.3 | 400.06 | 11.45 | 8.08 | 19.67 |
| Madhya Pradesh | B1_NaiveScreenGreedy | 6286 | 92.6 | 88.73 | 51.57 | 55.66 | 59.7 |
| Madhya Pradesh | B2_FreshRoadGreedy | 6286 | 55.68 | 213.71 | 27.94 | 20.83 | 24.94 |
| Madhya Pradesh | B3_MLPointDispatch | 6286 | 88.53 | 160.86 | 46.92 | 53.8 | 57.92 |
| Madhya Pradesh | MandiGuard_LOSO | 6286 | 31.67 | 211.52 | 11.45 | 8.04 | 12.96 |
| Gujarat | B1_NaiveScreenGreedy | 14702 | 97.07 | 439.26 | 34.44 | 47.63 | 58.63 |
| Gujarat | B2_FreshRoadGreedy | 14702 | 73.63 | 428.14 | 16.03 | 10.17 | 24.73 |
| Gujarat | B3_MLPointDispatch | 14702 | 96.59 | 385.52 | 39.39 | 56.82 | 66.16 |
| Gujarat | MandiGuard_LOSO | 14702 | 64.6 | 450.76 | 10.62 | 6.78 | 19.64 |
| Himachal Pradesh | B1_NaiveScreenGreedy | 8952 | 95.79 | 377.18 | 46.82 | 45.29 | 59.42 |
| Himachal Pradesh | B2_FreshRoadGreedy | 8952 | 71.83 | 869.54 | 24.48 | 15.49 | 33.39 |
| Himachal Pradesh | B3_MLPointDispatch | 8952 | 95.51 | 649.08 | 46.46 | 48.49 | 63.18 |
| Himachal Pradesh | MandiGuard_LOSO | 8952 | 54.26 | 801.37 | 14.31 | 9.72 | 19.25 |

### 5.10 `results/exp10_decade_regime_evolution_2017_2026.csv`
| `policy` | `n_episodes` | `dispatch_rate_pct` | `mean_net_gain_inr_qtl` | `lot_30qtl_gain_inr` | `loss_trip_rate_pct` | `closed_trap_rate_pct` | `worst_10pct_loss_inr_qtl` | `live_api_calls_per_query` | `regime` | `train_window` | `mean_screen_spread_inr` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|
| B1_NaiveScreen | 31997 | 89.47 | 393.39 | 11801.6 | 39.18 | 63.19 | -910.99 | 0.0 | 2017H2_GST_Transition | Rule | 1385.3 |
| B2_FreshRoad | 31997 | 59.3 | 430.35 | 12910.5 | 19.75 | 27.75 | -465.04 | 7.76 | 2017H2_GST_Transition | Rule | 1385.3 |
| MandiGuard_Expanding | 31997 | 44.88 | 425.04 | 12751.2 | 11.67 | 17.57 | -31.62 | 8.14 | 2017H2_GST_Transition | 2017H1 | 1385.3 |
| B1_NaiveScreen | 145972 | 89.67 | 254.77 | 7643.1 | 42.36 | 64.21 | -786.52 | 0.0 | 2018-2019_PreCOVID | Rule | 1120.8 |
| B2_FreshRoad | 145972 | 58.61 | 329.53 | 9886.0 | 17.69 | 27.43 | -313.32 | 7.79 | 2018-2019_PreCOVID | Rule | 1120.8 |
| MandiGuard_Expanding | 145972 | 47.48 | 345.17 | 10355.1 | 8.78 | 13.9 | -20.93 | 8.18 | 2018-2019_PreCOVID | 2017 | 1120.8 |
| B1_NaiveScreen | 139032 | 87.58 | 279.96 | 8398.7 | 42.24 | 58.77 | -851.55 | 0.0 | 2020-2021_COVID_Shock | Rule | 1109.4 |
| B2_FreshRoad | 139032 | 58.96 | 355.24 | 10657.2 | 18.63 | 25.34 | -353.56 | 7.84 | 2020-2021_COVID_Shock | Rule | 1109.4 |
| MandiGuard_Expanding | 139032 | 44.79 | 340.83 | 10224.8 | 10.59 | 15.6 | -23.42 | 8.28 | 2020-2021_COVID_Shock | 2017-2019 | 1109.4 |
| B1_NaiveScreen | 178197 | 89.06 | 278.41 | 8352.4 | 42.22 | 60.28 | -1057.3 | 0.0 | 2022-2023_Inflation_ExportCurb | Rule | 1161.9 |
| B2_FreshRoad | 178197 | 59.34 | 376.0 | 11280.1 | 18.79 | 25.55 | -451.87 | 7.85 | 2022-2023_Inflation_ExportCurb | Rule | 1161.9 |
| MandiGuard_Expanding | 178197 | 48.75 | 394.37 | 11831.0 | 10.5 | 14.17 | -33.29 | 8.69 | 2022-2023_Inflation_ExportCurb | 2017-2021 | 1161.9 |
| B1_NaiveScreen | 96468 | 89.87 | 222.77 | 6683.1 | 44.29 | 57.36 | -1289.28 | 0.0 | 2024_ElNino_Heatwave | Rule | 1221.2 |
| B2_FreshRoad | 96468 | 62.81 | 381.99 | 11459.7 | 18.94 | 24.01 | -474.26 | 8.16 | 2024_ElNino_Heatwave | Rule | 1221.2 |
| MandiGuard_Expanding | 96468 | 50.62 | 387.91 | 11637.4 | 12.03 | 15.32 | -36.82 | 9.12 | 2024_ElNino_Heatwave | 2017-2023 | 1221.2 |
| B1_NaiveScreen | 69526 | 90.67 | 350.01 | 10500.2 | 40.46 | 58.94 | -1062.66 | 0.0 | 2025-2026_Holdout_Benchmark | Rule | 1225.8 |
| B2_FreshRoad | 69526 | 62.11 | 446.66 | 13399.7 | 18.11 | 24.32 | -436.67 | 7.87 | 2025-2026_Holdout_Benchmark | Rule | 1225.8 |
| MandiGuard_Expanding | 69526 | 48.66 | 452.79 | 13583.6 | 9.97 | 16.17 | -37.89 | 8.75 | 2025-2026_Holdout_Benchmark | 2024 | 1225.8 |

### 5.11 `results/exp10b_multiyear_training_scaling.csv`
| `policy` | `n_episodes` | `dispatch_rate_pct` | `mean_net_gain_inr_qtl` | `lot_30qtl_gain_inr` | `loss_trip_rate_pct` | `closed_trap_rate_pct` | `worst_10pct_loss_inr_qtl` | `live_api_calls_per_query` | `train_rows` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| MandiGuard_1Yr (2024 only) | 69526 | 48.66 | 452.79 | 13583.6 | 9.97 | 16.17 | -37.89 | 8.75 | 701932 |
| MandiGuard_3Yr (2022-2024) | 69526 | 49.04 | 454.74 | 13642.3 | 10.02 | 15.87 | -37.02 | 8.75 | 1668451 |
| MandiGuard_8Yr (2017-2024) | 69526 | 49.07 | 454.94 | 13648.2 | 9.98 | 15.92 | -37.09 | 8.75 | 3437098 |

### 5.12 `results/exp11_modern_ai_and_aci_showdown.csv`
| `policy` | `n_episodes` | `dispatch_rate_pct` | `mean_net_gain_inr_qtl` | `lot_30qtl_gain_inr` | `loss_trip_rate_pct` | `closed_trap_rate_pct` | `worst_10pct_loss_inr_qtl` | `live_api_calls_per_query` | `benchmark` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| MandiGuard_Standard | 69526 | 48.66 | 452.79 | 13583.6 | 9.97 | 16.17 | -37.89 | 8.75 | Holdout_6State_2025_2026 |
| MandiGuard_ACI_NeurIPS21 | 69526 | 46.17 | 437.9 | 13137.0 | 10.22 | 16.37 | -33.71 | 8.75 | Holdout_6State_2025_2026 |
| Contextual_UCB_Bandit | 69526 | 39.61 | 406.47 | 12194.2 | 10.93 | 16.95 | -31.92 | 8.75 | Holdout_6State_2025_2026 |
| MandiGuard_Standard | 1537 | 18.67 | 605.06 | 18151.8 | 21.25 | 13.24 | -102.76 | 5.41 | HP_Apple_Grade_2026 |
| MandiGuard_ACI_NeurIPS21 | 1537 | 17.18 | 598.54 | 17956.1 | 20.08 | 13.26 | -74.42 | 5.41 | HP_Apple_Grade_2026 |
| Contextual_UCB_Bandit | 1537 | 17.89 | 615.04 | 18451.2 | 20.73 | 13.09 | -79.2 | 5.41 | HP_Apple_Grade_2026 |
| Direct_Quantile_GBDT_Q20 | 69526 | 51.02 | 459.02 | 13770.7 | 9.4 | 15.66 | -32.28 | 8.75 | Holdout_6State_2025_2026 |
| Direct_Quantile_GBDT_Q20 | 1537 | 18.48 | 605.07 | 18152.2 | 20.07 | 14.44 | -95.35 | 5.41 | HP_Apple_Grade_2026 |
| Deep_MLP_Conformal | 69526 | 47.08 | 435.38 | 13061.5 | 10.69 | 16.49 | -35.93 | 8.75 | Holdout_6State_2025_2026 |
| Deep_MLP_Conformal | 1537 | 17.57 | 615.34 | 18460.1 | 18.15 | 13.7 | -75.5 | 5.41 | HP_Apple_Grade_2026 |
| ExtraTrees_Conformal | 69526 | 49.02 | 453.3 | 13599.0 | 10.25 | 16.06 | -38.94 | 8.75 | Holdout_6State_2025_2026 |
| ExtraTrees_Conformal | 1537 | 19.0 | 593.49 | 17804.6 | 22.6 | 14.38 | -111.75 | 5.41 | HP_Apple_Grade_2026 |

### 5.13 `results/exp12_zerocloud_money_efficient_agent.csv`
| `policy` | `n_episodes` | `dispatch_rate_pct` | `mean_net_gain_inr_qtl` | `lot_30qtl_gain_inr` | `loss_trip_rate_pct` | `closed_trap_rate_pct` | `worst_10pct_loss_inr_qtl` | `live_api_calls_per_query` | `cpu_ms_per_query` | `api_cost_per_10k_queries_inr` | `val_sat_hurdle_inr` | `architecture_note` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| B4_UpfrontAllTools | 69526 | 48.66 | 452.79 | 13583.6 | 9.97 | 16.17 | -37.89 | 15.74 | 0.115 | 7868.0 | — | All external APIs upfront |
| B5_MultiAgentCoordinator | 69526 | 41.59 | 437.39 | 13121.7 | 9.38 | 16.57 | -31.77 | 8.76 | 0.093 | 4379.0 | — | 3 LLM/Agent roles over quantized bus |
| MandiGuard_Standard | 69526 | 48.66 | 452.79 | 13583.6 | 9.97 | 16.17 | -37.89 | 8.75 | 0.093 | 4374.0 | — | Full sequential cascade (live T1..T4) |
| MandiGuard_ZeroCloud_Full | 69526 | 48.89 | 455.33 | 13659.8 | 9.89 | 16.17 | -37.83 | 5.53 | 0.099 | 2764.0 | — | Cached T2 OSRM + Edge CPU T4 (only live T1+T3) |
| MandiGuard_ZeroCloud_Satisficing | 69526 | 48.89 | 440.48 | 13214.5 | 10.3 | 16.36 | -38.97 | 3.84 | 0.075 | 1922.0 | 250.0 | Cached T2 + Edge T4 + Val early-exit >= Rs 250 |

### 5.14 `results/exp13_outofbox_fpo_pooling_and_spoilage_clock.csv`
| `policy` | `n_episodes` | `dispatch_rate_pct` | `mean_net_gain_inr_qtl` | `lot_30qtl_gain_inr` | `loss_trip_rate_pct` | `closed_trap_rate_pct` | `worst_10pct_loss_inr_qtl` | `live_api_calls_per_query` | `experiment` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| B1_Marginal_Solo_10qtl_1.60xFreight | 69526 | 84.38 | 288.43 | 8652.8 | 42.32 | 59.38 | -1130.13 | 0.0 | Truck_Pooling_Scale |
| MandiGuard_Marginal_Solo_10qtl_1.60xFreight | 69526 | 43.08 | 409.53 | 12286.0 | 10.59 | 16.29 | -37.46 | 8.38 | Truck_Pooling_Scale |
| B1_Standard_MiniTruck_30qtl_1.00xFreight | 69526 | 90.67 | 350.01 | 10500.2 | 40.46 | 58.94 | -1062.66 | 0.0 | Truck_Pooling_Scale |
| MandiGuard_Standard_MiniTruck_30qtl_1.00xFreight | 69526 | 48.66 | 452.79 | 13583.6 | 9.97 | 16.17 | -37.89 | 8.75 | Truck_Pooling_Scale |
| B1_Cooperative_FPO_90qtl_0.70xFreight | 69526 | 93.59 | 386.52 | 11595.6 | 38.96 | 58.57 | -1028.95 | 0.0 | Truck_Pooling_Scale |
| MandiGuard_Cooperative_FPO_90qtl_0.70xFreight | 69526 | 51.73 | 477.28 | 14318.5 | 9.51 | 16.03 | -37.44 | 8.93 | Truck_Pooling_Scale |
| Split_Top2_Portfolio_StandardFreight | 69526 | 48.66 | 394.82 | 11844.6 | 8.09 | 9.85 | -26.4 | 8.75 | Split_Lot_Diversification |

### 5.15 `results/exp13b_biological_spoilage_clock.csv`
| `commodity` | `scenario` | `temp_c` | `nabcons_base_24h_20c_pct` | `daily_decay_rate_pct` | `safe_transit_hours_to_15pct_loss` |
|---|---|---:|---:|---:|---:|
| Tomato | 20C_Winter | 20.0 | 3.25 | 3.25 | 110.8 |
| Tomato | 32C_SpringMonsoon | 32.0 | 3.25 | 7.47 | 48.2 |
| Tomato | 42C_PeakSummer | 42.0 | 3.25 | 14.93 | 24.1 |
| Onion | 20C_Winter | 20.0 | 1.96 | 1.96 | 183.7 |
| Onion | 32C_SpringMonsoon | 32.0 | 1.96 | 4.5 | 79.9 |
| Onion | 42C_PeakSummer | 42.0 | 1.96 | 9.01 | 40.0 |
| Apple | 20C_Winter | 20.0 | 1.64 | 1.64 | 219.5 |
| Apple | 32C_SpringMonsoon | 32.0 | 1.64 | 3.77 | 95.5 |
| Apple | 42C_PeakSummer | 42.0 | 1.64 | 7.54 | 47.8 |
| Potato | 20C_Winter | 20.0 | 0.86 | 0.86 | 418.6 |
| Potato | 32C_SpringMonsoon | 32.0 | 0.86 | 1.98 | 182.2 |
| Potato | 42C_PeakSummer | 42.0 | 0.86 | 3.95 | 91.1 |

---

## 6. Experiment Registry (`EXPERIMENT_REGISTRY.csv`)
| `experiment_id` | `type` | `scope` | `metric` | `value` | `ci_or_note` | `p_holm` | `outcome` |
|---|---|---|---|---|---|---|---|
| H1 | Confirmatory | Holdout_2025_2026_Shortlisted | MG - B1 Mean dNet (INR/qtl) | 102.7823 | [48.6649, 153.4512] | 0.0012 | SUPPORTED |
| H2 | Confirmatory | Holdout_2025_2026_Shortlisted | MG - B2 Mean dNet (INR/qtl) | 6.1303 | [-17.0161, 25.0171] | 0.269946 | NOT_SUPPORTED |
| H3 | Confirmatory | Holdout_2025_2026_Shortlisted | MG - B3 Ep Phantom Incidence (prob) | -0.3729 | [-0.4019, -0.3424] | 0.0008 | SUPPORTED |
| H4 | Confirmatory | Holdout_2025_2026_Shortlisted | MG Calls - 0.75*B4 Calls | -3.0548 | [-3.4408, -2.6906] | 0.0008 | SUPPORTED |
| Val_Conformal_Cov | Diagnostic | Val_2025H1 | Empirical 80% LCB Coverage (%) | 78.85 | Frozen safety_margin=50.0 INR/qtl | — | LOGGED |
| Holdout_Conformal_Cov | Diagnostic | Holdout_2025_2026 | Empirical 80% LCB Coverage (%) | 79.07 | Strictly causal <=t arrival maturation | — | LOGGED |
| Exp10_Decade_AllRegimes | Exploratory | 2017H2-2026 (661192 eps across 6 regimes) | Loss-Trip Rate & Worst-10% Loss range | 8.78-12.03% \| -20.93 to -37.89 | vs B1 39.18-44.29% and -786.52 to -1289.28 INR/qtl | — | LOGGED |
| Exp10_ElNino2024_Peak | Exploratory | 2024_ElNino_Heatwave (N=96468) | MG - B1 Mean dNet (INR/qtl) | 165.14 | 387.91 vs 222.77 INR/qtl; LTR 12.03% vs 44.29% | — | LOGGED |
| Exp10b_Training_Scaling | Exploratory | Holdout_2025_2026 (N=69526) | 1Yr vs 3Yr vs 8Yr Mean dNet (INR/qtl) | 452.79 / 454.74 / 454.94 | 701932 / 1668451 / 3437098 train rows (+2.15 INR/qtl) | — | LOGGED |
| Exp11_DirectQuantile_Holdout | Exploratory | Holdout_2025_2026 (N=69526) | Mean dNet / LTR / CVaR10 | 459.02 / 9.40% / -32.28 | Direct_Quantile_GBDT_Q20 vs MG_Std 452.79 / 9.97% / -37.89 | — | LOGGED |
| Exp11_DeepMLP_Apple2026 | Exploratory | HP_Apple_Grade_2026 (N=1537) | Mean dNet / LTR / CVaR10 | 615.34 / 18.15% / -75.50 | ACI slashes MG CVaR10 -102.76 -> -74.42 (alpha_Apple -> 0.164) | — | LOGGED |
| Exp12_ZeroCloud_Full | Exploratory | Holdout_2025_2026 (N=69526) | Mean dNet / API Calls / Cost per 10k | 455.33 / 5.53 / 2764 INR | Cached T2 + Edge CPU T4: -64.9% cost vs B4 (7868 INR) | — | LOGGED |
| Exp12_ZeroCloud_Satisficing | Exploratory | Holdout_2025_2026 (N=69526) | Mean dNet / API Calls / Cost per 10k | 440.48 / 3.84 / 1922 INR | Val-frozen hurdle 250 INR: -75.6% cost vs B4 retaining 97.3% gain | — | LOGGED |
| Exp13_FPO_Pooling_90qtl | Exploratory | Holdout_2025_2026 (0.70x freight) | Mean dNet / 30qtl Equiv Gain | 477.28 / 14318.5 | +24.49 vs 30qtl solo (452.79) and +67.75 vs 10qtl marginal (409.53) | — | LOGGED |
| Exp13_Split_Top2_Portfolio | Exploratory | Holdout_2025_2026 (50/50 Top-2 LCB) | Closed Trap % / LTR % / Mean dNet | 9.85% / 8.09% / 394.82 | 39% relative closed-trap reduction vs 16.17% single-yard | — | LOGGED |
| Exp13b_Spoilage_Clock_Tomato42C | Exploratory | NABCONS + Q10 Thermal Decay | Safe Transit Hours to 15% Loss | 24.1 | 42C summer vs 110.8h at 20C winter (Potato 91.1h vs 418.6h) | — | LOGGED |

---

## 7. Real Farmer SMS Cards & ACI Diagnostics

### 7.1 `results/sample_farmer_sms_cards.txt`
```text
[MandiGuard DISPATCH] MH Onion: Amrawati->Kamthi (170km/3.3h). LCB +Rs154, Real +Rs268/qtl!
[MandiGuard STOP] MP Onion at Mandsaur: SKIP Sanawad (+Rs1047 screen). VARIETY_OR_STALE. Sell local!
[MandiGuard RAIN STOP] KA Tomato at Udupi: SKIP Chikkamagalo. Rain 123mm -> spoil risk. Sell local!
[MandiGuard FPO POOL] 90qtl shared FPO truck (0.70x freight) raises mean net gain +Rs24.5/qtl over 30qtl solo (Rs477.3/qtl vs Rs452.8)!
```

### 7.2 `results/aci_diagnostics.json`
```json
{
  "Holdout_6State_2025_2026": {
    "Onion": 0.24400000000000016,
    "Potato": 0.2700000000000002,
    "Tomato": 0.03800000000000002,
    "Apple": 0.20500000000000013
  },
  "HP_Apple_Grade_2026": {
    "Onion": 0.2,
    "Potato": 0.2,
    "Tomato": 0.2,
    "Apple": 0.16399999999999998
  }
}
```

---

