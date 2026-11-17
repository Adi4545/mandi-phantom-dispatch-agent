# M.Tech Viva Career Defense Master Sheet (`MandiGuard`)
### *Read This 10 Minutes Before Walking Into Your Thesis Defense Room*

---

## 1. Your 30-Second Core Story (Memorize Word-for-Word)
> *"Sir/Ma'am, most mandi AI papers only predict prices and get farmers hurt when distant yards are closed, lack their exact crop variety, or rot their vegetables in summer heat. Across `69,526` real holdout opportunities and `661,192` trips spanning nearly 10 years (`2017–2026`), naive price-board chasing loses money `40.46%` of the time and standard point-ML loses `45.28%`! So I built **`MandiGuard`**: a cheapest-first four-step verification agent (`Market Vitality -> OSRM Road & GoI Fee -> Q10 Weather Spoilage -> 80% Conformal Safety Cushion`) with an explicit Stay-Home refusal option. It beats naive chasing by **`+₹102.78/qtl` (`+₹3,083.5` per `30-qtl` smallholder truck = `81.2%` of monthly household crop income)**, shrinks tail crashes `11.5×`, and cuts paid live API bills up to **`75.6%`** (`3.84` calls/query) in our offline **`ZeroCloud`** design."*

---

## 2. The 4 Minimal Numbers to Keep on Your Fingertips
| Minimal Metric (`Holdout N = 69,526`) | Naive `B1` | Fresh+Road `B2` | Point ML `B3` | `MandiGuard` (Ours) | `ZeroCloud` / `FPO 90qtl` |
|:---|---:|---:|---:|---:|---:|
| **1. Mean Net Gain (`₹/qtl`)** | `₹350.01` | `₹446.66` | `₹330.85` | **`₹452.79`** (`+₹102.78` vs `B1`) | `₹455.33` / **`₹477.28`** |
| **2. Loss-Trip Rate (`%`)** | `40.46%` | `18.11%` | `45.28%` | **`9.97%`** | `9.89%` / `9.51%` |
| **3. Worst-10% Loss (`₹/qtl`)** | `-₹1,062.66` | `-₹436.67` | `-₹1,097.80` | **`-₹37.89`** (`11.5×` safer vs `B2`) | `-₹37.83` / `-₹37.44` |
| **4. Live API Calls / Query** | `0` *(blind)* | `7.87` | `7.87` | **`8.75`** (`-44.4%` vs `B4` `15.74`) | **`3.84`** (`-75.6%` API spend) |

---

## 3. Whiteboard Math in 5 Lines (Class-10 Arithmetic!)
**Setup (`30-qtl` MP Tomato, `200 km / 6 hrs`, `40°C` May heat, `₹1,400` home vs `₹2,000` portal):**
1. **Portal Price:** `₹2,000.00/qtl`
2. **Heat Rot (`Q10`):** At `20°C`, NABCONS loss = `3.25%/24h`. At `40°C` (`+20°C`), speed is `4×`; over `6h` (`1/4` day), `3.25% × 1/4 × 4 = 3.25%` rots $\to$ **`-₹65.00`** (`₹1,935.00` left)
3. **Truck + MP Tax (`1.5%`):** `₹35 + (₹0.45 × 200) + (1.5% × ₹1,400)` = **`-₹146.00`** (`₹1,789.00` left)
4. **`80%` Safety Cushion (`8%` dip):** `8% × ₹1,935` = **`-₹154.80`** (`₹1,634.20` safe cash)
5. **Minus Home Price (`₹1,400`):** **`+₹234.20/qtl`** (`+₹7,026` truck gain $> ₹50$ threshold $\to$ **`DISPATCH`**!).

---

## 4. The 15 Hardest Examiner Trap Questions (Calm 2-Sentence Answers)

1. **Q: Why did `H2` against `B2_FreshRoadGreedy` fail significance (`p = 0.2699`)?**  
   **A:** `MandiGuard` deliberately declines borderline high-variance lotteries (`48.66%` vs `62.11%` dispatch), trading a small `+₹6.13/qtl` average gap for **nearly halving loss trips (`9.97%` vs `18.11%`) and shrinking worst-10% tail losses `11.5×` (`-₹37.89` vs `-₹436.67/qtl`)**. Across the `42,766` episodes in the 4 states with `100%` archived NWP forecasts (`Exp 2b`), `MandiGuard` beats `B2` cleanly by **`+₹31.82/qtl`**.

2. **Q: On HP Graded Apples (`Exp 3`), why does `MandiGuard` earn `₹605.06/qtl` while `B2` earns `₹1,150.83` (`Grade A` only `5.39%` dispatch)?**  
   **A:** Our `2024` model had no `Grade A` tags, so high `2026` `Grade A` prices widened the frozen conformal penalty and made the agent over-cautious (`5.39%` dispatch). Still, it cut physical traps **7-fold (`94.14% -> 13.24%`)**, flipped `Grade B` from **`-₹427.54` to `+₹833.70/qtl`**, and Adaptive Conformal (`MandiGuard_ACI`) fixes tail risk **`-27.6%` (`-₹102.76 -> -₹74.42/qtl`)**.

3. **Q: Why does removing Weather `T3` slightly raise unconditional profit by `₹2.46/qtl` (`₹455.25` vs `₹452.79`)?**  
   **A:** Dropping `T3` admits `1.52%` extra hot/rainy trips (`50.18%` vs `48.66%`) where a few spot spikes absorbed spoilage. Keeping `T3` buys perishable safety on `21,656` extreme heat/rain trips, cutting heat/rain loss rate (`11.39% -> 10.10%`) and improving tail risk (`-₹67.49 -> -₹57.11/qtl`).

4. **Q: Why did 8 years of training data (`2017–2024`, `3.44M` rows) add only `+₹2.15/qtl` over 1 year (`2024`)?**  
   **A:** That proves Indian mandi spreads shift across macro regimes (`GST`, `COVID`, `El-Niño`), so older pre-2024 spreads add diminishing value (`₹452.79` $\to$ `₹454.94/qtl`). A single fresh prior year plus causal conformal cushions is both cheaper and nearly optimal.

5. **Q: Doesn't simulating `Q10` spoilage from NABCONS instead of truck weighment receipts weaken the proof?**  
   **A:** Public portals don't publish truck weighment slips, so NABCONS (2022) market loss rates are the official GoI anchor—accounting for just `₹68.76/qtl` of erosion, whereas **`₹714.90/qtl`** (`58.94%` traps/drops) is raw untouched AGMARKNET price truth. Furthermore, `MandiGuard` beats `B1` across all **`9/9`** `[0.5×..1.5×]` sensitivity scenarios (`+₹82.62` to `+₹121.42/qtl`).

6. **Q: How do you prove ZERO data leakage or hindsight `₹50` margin tuning?**  
   **A:** Weights trained strictly on `2024` (`701,932` rows), scalar `₹50/qtl` froze on `Jan–May 2025` (`Val_2025H1`, `280,697` rows), hypotheses `H1`–`H4` locked in Git commit `e421d15` before holdout ran, conformal errors update only once `arrival_date <= decision_date`, and all **`19/19` automated leakage, `.gov.in` parity, & integrity tests** pass.

7. **Q: Why didn't you run GPT-4, LSTMs, or Deep RL at runtime?**  
   **A:** In `Exp 11` inside the same `T1–T4` funnel, `Deep_MLP_Conformal` (`₹435.38/qtl`) and `Contextual_UCB_Bandit` (`₹406.47/qtl`) trailed `MandiGuard_Standard` (`₹452.79/qtl`) on 6-state holdout, while tabular trees run locally in **`0.075–0.099 ms/query`** with zero LLM API bills or hallucinations.

8. **Q: Explain "80% Conformal LCB" and "Two-Way Cluster Bootstrap" in 2 sentences each.**  
   **A:** **80% Conformal LCB:** Subtract the 80th-percentile worst recent forecast mistake so actual arrival prices equal or beat our floor roughly 80% of the time (`78.85%` Val, `79.07%` Holdout). **Two-Way Cluster Bootstrap:** Resample whole origin mandis (`174`) and whole 2-week blocks (`23`) together `5,000` times so correlated days never produce fake narrow confidence intervals.

9. **Q: How can `ZeroCloud_Full` earn `+₹2.54/qtl` MORE than Standard (`₹455.33` vs `₹452.79`) with fewer calls?**  
   **A:** Standard sorts Step-0 candidates by raw portal spread before checking roads (`T2`), letting distant high-freight traps crowd the top 5; `ZeroCloud_Full` has `T2` cached locally for free, so it pre-ranks Step-0 options by *freight-adjusted spread* first, promoting profitable nearby mandis into the top-5 shortlist!

10. **Q: What about the `43` Open-Meteo grid cells that hit API rate limits?**  
    **A:** Physical weather hitting trucks (`ERA5` `2024–2026`, `NASA POWER` `2017–2023`) is **100% real (`0.0%` missing)**, the 43-cell backup nowcaster trained strictly on `2024 <= t` data (`1.047°C` MAE), and `Exp 2b` isolates the `42,766` episodes in the 4 states with `100%` native archived NWP forecasts—where `MandiGuard` wins by `+₹59.53/qtl` vs `B1` and `+₹31.82/qtl` vs `B2`.

11. **Q: Why does Tomato show higher naive `B1` mean (`₹547.64`) than `MandiGuard` (`₹522.48/qtl`)?**  
    **A:** Naive `B1` gets `+₹25.16/qtl` average extra only by gambling blindly on shortage spikes that lose money on **`32.38%`** of episodes (1 in 3!); `MandiGuard` still beats both `B2` (`₹484.64`) and `B3` (`₹515.05`) while slashing Tomato episode losses **over 6-fold to `5.09%`**.

12. **Q: Why does Onion fail `48.69%` of the time under `B1` even though Tomato rots faster?**  
    **A:** Onion's average screen spread (`₹704.50/qtl`) is tiny compared to Apple (`₹3,499.80`), so highway freight (`₹138.07`), spoilage (`₹28.60`), and `₹484.23` variety traps (`57.26%` closed/variety traps) wipe out profits completely (`+₹53.61/qtl` net). `MandiGuard` triples Onion per-episode profit (`₹46.50 -> ₹163.41/qtl`).

13. **Q: Why did the 3-bot multi-agent `B5` lose `-₹15.40/qtl` vs single-agent `MandiGuard`?**  
    **A:** Splitting into `Scout -> Weather -> RiskGate` communicating over discrete `₹150` profit buckets rounds off borderline winners near the threshold, cutting dispatch rate (`41.59%` vs `48.66%`) while spending the exact same live calls (`8.76` vs `8.75`).

14. **Q: How does `MandiGuard_ACI` fix HP Apple tail risk without retraining?**  
    **A:** When realized arrivals break `20%` errors, online Gibbs–Candès ACI lowers $\alpha_{\text{Apple}}$ (`0.200 -> 0.164`, and 6-state Tomato to `0.038`), trimming `1.49 pp` of risky trips and slashing HP Apple `Worst-10% Loss` by **`27.6%` (`-₹102.76 -> -₹74.42/qtl`)**.

15. **Q: Summarize `FPO 90-qtl`, `Split_Top2`, and `Biological Spoilage Clock` in one breath.**  
    **A:** Sharing one `90-qtl` FPO truck (`0.70×` freight) boosts profit to **`₹477.28/qtl`** (`+₹24.49` over solo `30-qtl`, `+₹67.75` over solo `10-qtl`); splitting `50/50` across top-2 markets cuts closed traps **`39%` (`16.17% -> 9.85%`)**; and the $Q_{10}$ Spoilage Clock warns when Tomato transit life shrinks from `110.8 h` (`20°C`) to **`24.1 h` (`42°C`)** before emitting `<160`-char SMS cards.

---

## 5. Two Examiner Knockouts (`data.gov.in` Direct Parity & Clerk Upload Lag Proof!)
* **"Wait—didn't your 10-year CSVs come from a HuggingFace mirror? How do you know they match official `data.gov.in`?" (`Exp 14`):**  
  We audited the official `data.gov.in` Resource `9ef84268-d588-465a-a308-a864a43d0070` XML datafile (`6,434` all-India rows, `172` matched core-panel keys) plus live `api.agmarknet.gov.in` endpoints (`22` benchmark queries, `4,427` official HP apples)—confirming **`100.00%` exact rupee parity on `Min_Price` and `Max_Price` and `99.42%` on `Modal_Price`**.
* **"What if 3-day missing portal data wasn't a closed yard—what if the clerk just forgot to upload?" (`Exp 15`):**  
  We re-ran all `69,526` holdout trips across 4 clerk-upload-lag assumptions (`+₹77.34` to `+₹91.66/qtl` over `B1`), **AND** checked ONLY dispatches where arrival-day exact-variety prices were **100% observed (`d0`, zero missing data)**: `MandiGuard` (`28,359` trips) earns **`₹1,035.32/qtl` (`4.98%` loss rate)** vs `B1` (`₹856.86`, `12.32%`) and `B2` (`₹833.73`, `10.32%`)—beating `B1` by **`+₹178.46/qtl`** and `B2` by **`+₹201.59/qtl`**! *(Prices/roads/weather are observed; freight `₹35 + ₹0.45/km`, rot, and `Exp 11–13` deployment scenarios are modeled.)*

---

## 6. 60-Second Live Examiner Demo Commands
```bash
cd /Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent
PYTHONPATH=. /Users/adityasharma/anaconda3/bin/python3 -m pytest -v tests
```
Or open `notebooks/colab_standalone_reproduction.ipynb` + `data/processed/colab_data_pack.tar.gz` (`4.82 MB`) in Google Colab and click **Run all** (`< 3` minutes).
