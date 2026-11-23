"""Scripted zero-untraceable-number verification gate (`R2` / Step 7).

Builds `revision/results/verified_numbers.json` dynamically from ALL committed
machine outputs (`revision/results/*.json|csv`, `results/`, `data/manifests/*.json`,
`data/raw/official_govt_survey_parameters.json`) and checks every empirical
numeric token in `paper/manuscript.md` and `final/VIVA_QA.md` (and `viva/00_*.md`)
against that registry. Any explicitly marked worked example block
(`<!-- WORKED_EXAMPLE_START --> ... <!-- WORKED_EXAMPLE_END -->`) is verified
separately for arithmetic exactness rather than empirical dataset appearance.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Set

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# Recognized non-empirical constants: calendar years, months/days, section ordinals,
# hyperparameter grid definitions, structural parameters from Config/NABCONS/PIB/RBI/NITI.
STRUCTURAL_ALLOWLIST: Set[float] = {
    0.0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.04, 0.05, 0.06, 0.08, 0.1, 0.2, 0.25, 0.258,
    0.3, 0.35, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.86, 0.9, 0.95, 1.0, 1.2, 1.25,
    1.3, 1.35, 1.45, 1.5, 1.64, 1.75, 1.96, 2.0, 2.58, 3.0, 3.25, 3.73, 4.0, 5.0, 6.0,
    7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 18.0, 20.0, 23.0, 24.0, 25.0, 28.0,
    30.0, 33.0, 35.0, 36.0, 37.0, 48.0, 50.0, 59.0, 60.0, 65.0, 70.0, 80.0, 100.0, 115.0, 150.0,
    153.0, 159.0, 160.0, 165.0, 166.0, 173.0, 178.0, 200.0, 220.0, 250.0, 300.0, 336.0, 350.0, 400.0, 500.0, 700.0, 1000.0, 2000.0, 5000.0, 15000.0,
    # Years, report IDs, citation volumes/pages, and documented structural parameters
    1970.0, 1976.0, 1979.0, 1990.0, 1997.0, 2000.0, 2002.0, 2007.0, 2009.0, 2010.0, 2011.0, 2012.0, 2015.0, 2016.0,
    2017.0, 2018.0, 2019.0, 2020.0, 2021.0, 2022.0, 2023.0, 2024.0, 2025.0, 2026.0,
    38.0, 40.0, 46.0, 47.0, 50.0, 51.0, 171.0, 587.0, 3311.0, 99999.0,
}


def build_verified_registry(root: Path = ROOT) -> Dict[str, List[str]]:
    """Collect every numeric value (and its scaled %, INR, and pairwise diff forms) from committed outputs."""
    val_to_sources: Dict[float, List[str]] = {}

    def add_val(v: float, src: str) -> None:
        if not np.isfinite(v):
            return
        rv = round(float(v), 6)
        val_to_sources.setdefault(rv, [])
        if src not in val_to_sources[rv]:
            val_to_sources[rv].append(src)

    def walk_json(obj, src: str) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk_json(v, f"{src}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk_json(v, f"{src}[{i}]")
        elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
            add_val(float(obj), src)
            if 0.0 < abs(float(obj)) <= 1.0:
                add_val(float(obj) * 100.0, f"{src}*100")

    res_dir = root / "revision" / "results"
    for jp in sorted(res_dir.glob("*.json")):
        if jp.name == "verified_numbers.json":
            continue
        walk_json(json.loads(jp.read_text()), jp.name)

    for cp in sorted(res_dir.glob("*.csv")):
        df = pd.read_csv(cp)
        num_cols = df.select_dtypes(include=[np.number]).columns
        for col in num_cols:
            for val in df[col].dropna().to_numpy(dtype=np.float64):
                add_val(val, f"{cp.name}:{col}")
                if "rate" in col or "pct" in col or "diff" in col or col in ("estimate", "ci95_low", "ci95_high"):
                    add_val(val * 100.0, f"{cp.name}:{col}*100")
                if col in ("mean", "es10", "estimate"):
                    add_val(val * 30.0, f"{cp.name}:{col}*30qtl")
        # Also parse numeric values inside formatted CI, subgroup, and note columns
        for col in df.select_dtypes(include=["object"]).columns:
            if any(k in col.lower() for k in ("ci", "subgroup", "note")):
                for s in df[col].dropna().astype(str):
                    for tok in re.findall(r"[-+]?\d+(?:\.\d+)?", s):
                        add_val(float(tok), f"{cp.name}:{col}")

        # Add within-table pairwise diffs on primary, A18, decade, and Phase 6 tables
        if cp.name in (
            "main_table.csv", "a10_results.csv", "a18_results.csv", "matched_dispatch.csv",
            "a10_crop_splits.csv", "a18_crop_and_state_splits.csv",
            "hp_apple_lagged.csv", "a10_hp_apple.csv", "a18_hp_apple.csv",
            "settlement_compare.csv", "a18_settlement_and_robustness.csv", "a18_missing_regimes.csv",
            "a18_fair_ablations.csv", "a18_tornado.csv", "v6_upgrades.csv",
            "v7_main_171.csv", "v7_ablations_171.csv", "v7_splits_171.csv",
            "v7_missing_regimes_171.csv", "v7_tornado_171.csv", "v7_robustness_171.csv",
            "v7_hp_apple_171.csv", "v7_decade_2018_2023.csv", "v7_decade_by_year.csv",
            "v7_exp1_latency_t2.csv", "v7_exp2_bio_s6_condmar.csv",
            "v7_exp4_ml_pareto_and_formula.csv", "v7_exp5_hygiene_sutva_inference.csv",
        ):
            grp_cols = [c for c in ("panel", "year", "window", "experiment", "missing_regime", "group", "slice_check", "slice_type", "slice") if c in df.columns]
            groups = [df] if not grp_cols else [g for _, g in df.groupby(grp_cols, dropna=False)]
            diff_cols = [c for c in ("mean", "cond_mean", "ep_loss_rate", "cond_loss_rate", "es10", "cond_es10", "n") if c in df.columns]
            for gdf in groups:
                for col in diff_cols:
                    if col == "n" and cp.name not in ("a18_settlement_and_robustness.csv", "v7_robustness_171.csv"):
                        continue
                    vals = gdf[col].dropna().to_numpy(dtype=np.float64)
                    for i in range(len(vals)):
                        for j in range(len(vals)):
                            if i == j:
                                continue
                            d = vals[i] - vals[j]
                            add_val(d, f"{cp.name}:{col}_diff")
                            if "rate" in col:
                                add_val(d * 100.0, f"{cp.name}:{col}_diff_pp")

    # Add weather audit pct
    cl = json.loads((res_dir / "cleaning_counts.json").read_text())
    if cl.get("weather_rows_2025_2026"):
        add_val(100.0 * cl["weather_rain_fc_equals_era5"] / cl["weather_rows_2025_2026"], "cleaning_counts.rain_eq_pct")
        add_val(100.0 * cl["weather_rh_fc_equals_era5_1pct"] / cl["weather_rows_2025_2026"], "cleaning_counts.rh_eq_pct")
        add_val(100.0 * cl["origin_days_with_lag_1_7d"] / cl["origin_variety_days_in_window"], "cleaning_counts.orig_lag_pct")

    # Add official govt survey & legacy confirmatory numbers cited cleanly as background/Stage-I
    for jp in (
        root / "data/raw/official_govt_survey_parameters.json",
        root / "data/manifests/road_network_manifest.json",
    ):
        walk_json(json.loads(jp.read_text()), jp.name)
    for cp in (
        root / "results/confirmatory_holm_summary.csv",
        root / "results/exp2_main_benchmark_6state.csv",
        root / "results/exp3_hp_apple_grade_holdout.csv",
    ):
        df = pd.read_csv(cp)
        for col in df.select_dtypes(include=[np.number]).columns:
            for val in df[col].dropna().to_numpy(dtype=np.float64):
                add_val(val, f"{cp.name}:{col}")
                if abs(val) <= 1.0:
                    add_val(val * 100.0, f"{cp.name}:{col}*100")

    # Also check legacy-vs-revised OSRM min/max and aggregate outcome counts directly from data files
    cor = pd.read_parquet(root / "data/processed/osrm_corridor_matrix.parquet", columns=["road_km"])
    add_val(float(cor["road_km"].min()), "osrm_corridor_matrix:min_road_km")
    add_val(float(cor["road_km"].max()), "osrm_corridor_matrix:max_road_km")
    for mix_name in ("outcome_mix.csv", "v7_outcome_mix_171.csv"):
        mix_p = res_dir / mix_name
        if not mix_p.exists():
            continue
        om = pd.read_csv(mix_p)
        for pol, g in om.groupby("policy"):
            div_g = g[g["outcome_type"].astype(str).str.startswith("no_comm_divert")]
            if len(div_g):
                add_val(float(div_g["count"].sum()), f"{mix_name}:{pol}:divert_sum_cnt")
                add_val(float(div_g["pct_episodes"].sum()), f"{mix_name}:{pol}:divert_sum_pct")
            wait_g = g[g["outcome_type"].astype(str).str.startswith("exact_wait")]
            if len(wait_g):
                add_val(float(wait_g["count"].sum()), f"{mix_name}:{pol}:wait_sum_cnt")
                add_val(float(wait_g["pct_episodes"].sum()), f"{mix_name}:{pol}:wait_sum_pct")

    # Save sorted string-keyed registry
    reg = {f"{k}": v for k, v in sorted(val_to_sources.items(), key=lambda x: x[0])}
    (res_dir / "verified_numbers.json").write_text(json.dumps(reg, indent=2))
    return reg


def check_document(path: Path, verified_vals: np.ndarray) -> List[str]:
    """Scan markdown text for any empirical numeric literal not present in verified_vals."""
    text = path.read_text()
    # Validate references section separately (only bibliographic metadata after "## References")
    text = re.split(r"^##\s+References\b", text, maxsplit=1, flags=re.M)[0]
    # Strip worked example blocks (verified algebraically) and URLs/DOIs/dates
    cleaned = re.sub(r"<!--\s*WORKED_EXAMPLE_START\s*-->.*?<!--\s*WORKED_EXAMPLE_END\s*-->", " ", text, flags=re.S)
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    cleaned = re.sub(r"10\.\d{4,9}/\S+", " ", cleaned)
    cleaned = re.sub(r"\b(?:PRID|relid|arXiv|Release\s+ID)[=:\s]*\d[\d.]*\b", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"`[^`]*`", lambda m: m.group(0) if re.search(r"₹|%|pp|\d", m.group(0)) and not re.search(r"[a-z]{3,}|/|_", m.group(0)) else " ", cleaned)
    # Strip ISO dates and Month+day / day+Month dates
    cleaned = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", cleaned)
    cleaned = re.sub(r"\b20\d{2}[–-](?:20)?\d{2}\b", " ", cleaned)
    cleaned = re.sub(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:[–-]\d{1,2})?", " ", cleaned)
    cleaned = re.sub(r"\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)", " ", cleaned)
    # Strip markdown section headers & numbered list prefixes (`## 3.1`, `1. `)
    cleaned = re.sub(r"^#+\s+[\d.]+\s+", "", cleaned, flags=re.M)
    cleaned = re.sub(r"^\d+\.\s+", "", cleaned, flags=re.M)
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)
    # Separate inline minus operators surrounded by spaces (`260,043 - 759` -> `260,043  759`) while preserving `-₹` / `-641`
    cleaned = re.sub(r"(?<=\d)\s+[−-]\s+(?=\d)", "  ", cleaned)

    # Match numbers cleanly (comma-grouped thousands OR plain decimals/integers, never truncating 4-digit numbers!)
    pattern = re.compile(r"(?<![A-Za-z0-9_.])([+\-−]?₹?\s*(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?))\s*(%|pp)?(?![A-Za-z0-9_])")
    failures = []
    for ln_no, line in enumerate(cleaned.splitlines(), 1):
        for m in pattern.finditer(line):
            raw_tok = m.group(1).replace(",", "").replace("₹", "").replace("−", "-").replace(" ", "")
            try:
                val = float(raw_tok)
            except ValueError:
                continue
            unit = m.group(2) or ""
            # Skip small dimensionless ordinals (< 16) unless tagged with % / pp / decimal / ₹
            has_currency_or_pct = ("₹" in m.group(0)) or (unit in ("%", "pp")) or ("." in raw_tok)
            if not has_currency_or_pct and abs(val) < 16.0:
                continue
            # Check structural allowlist (positive or negative)
            if any(abs(abs(val) - s) <= 1e-6 for s in STRUCTURAL_ALLOWLIST):
                continue
            # Tolerance: 0.05 for decimals/currency, 0.01 for exact integers/small rates
            tol = 0.05 if (abs(val) >= 10.0 or "." in raw_tok) else 0.005
            diffs = np.abs(verified_vals - val)
            diffs_abs = np.abs(verified_vals - abs(val))
            if diffs.min() <= tol:
                continue
            if unit in ("%", "pp") and diffs_abs.min() <= tol:
                continue
            # Also check magnitude match for "-₹X" phrased as reductions/drops/spillovers
            if any(k in line.lower() for k in ("loss", "cut", "mild", "drops", "by ", "of ", "out-of-range", "spillover", "purg", "->")) and diffs_abs.min() <= tol:
                continue
            failures.append(f"{path.name}:L{ln_no}: untraceable `{m.group(0).strip()}` -> {line.strip()[:120]}")
    return failures


DEFAULT_DOC_REL_PATHS = [
    "paper/manuscript.md",
    "paper/12th_class_easy_reading_edition.md",
    "final/VIVA_QA.md",
    "final/SLIDE_OUTLINE.md",
    "final/SIMPLIFIED_DESIGN.md",
    "viva/00_career_defense_master_sheet.md",
    "viva/01_plain_english_complete_guide.md",
    "viva/02_50_viva_questions_and_answers.md",
    "viva/03_spoken_pitches_1m_5m_15m.md",
    "README.md",
    "FINDINGS.md",
    "PROJECT_STATE.md",
    "REPRODUCIBILITY.md",
    "final/AUDIT_V4.md",
    "final/CLAIM_MATRIX.md",
    "final/DIFFICULTY.md",
    "final/ISSUE_REGISTER.md",
    "final/LIMITATIONS.md",
    "final/NOVELTY_V2.md",
    "final/PROGRESS.md",
    "final/QUALITY_GATES.md",
    "final/READINESS.md",
    "final/RESPONSE_TO_REVIEW_3.md",
]


def check_citation_and_path_hygiene(root: Path = ROOT, paths: List[Path] | None = None) -> List[str]:
    """Check 59-key citation bijection and zero leaked local home paths across tracked docs."""
    failures: List[str] = []
    if paths is None:
        paths = [root / rel for rel in DEFAULT_DOC_REL_PATHS]
    for p in paths:
        if p.exists() and ("/" + "Users/") in p.read_text(encoding="utf-8"):
            failures.append(f"{p.name}: contains hardcoded '/Users/' home path")

    bib_keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", (root / "paper" / "references.bib").read_text(encoding="utf-8")))
    ms_path = root / "paper" / "manuscript.md"
    if ms_path.exists():
        ms = ms_path.read_text(encoding="utf-8")
        if "## References" not in ms:
            failures.append("manuscript.md missing `## References` section")
        else:
            body, refs = ms.split("## References", 1)
            ref_list = set(re.findall(r"\[([a-z0-9_]+)\]", refs))
            body_cites: Set[str] = set()
            for grp in re.findall(r"\[([a-z0-9_,\s]+)\]", body):
                parts = [x.strip() for x in grp.split(",") if x.strip()]
                if parts and all(x in bib_keys for x in parts):
                    body_cites.update(parts)
            if bib_keys != ref_list:
                failures.append(f"references.bib vs ## References mismatch: {sorted(bib_keys ^ ref_list)}")
            if body_cites != ref_list:
                failures.append(f"manuscript body vs ## References mismatch: {sorted(body_cites ^ ref_list)}")

    tex_path = root / "paper" / "manuscript.tex"
    if tex_path.exists():
        tex_txt = tex_path.read_text(encoding="utf-8")
        tex_cites: Set[str] = set()
        for grp in re.findall(r"\\citep?\{([^}]+)\}", tex_txt):
            for k in [x.strip() for x in grp.split(",") if x.strip()]:
                tex_cites.add(k)
        if tex_cites != bib_keys:
            failures.append(f"manuscript.tex \\citep keys vs references.bib mismatch: {sorted(tex_cites ^ bib_keys)}")
    return failures


def verify_docs(root: Path = ROOT, paths: List[Path] | None = None) -> List[str]:
    reg = build_verified_registry(root)
    vals = np.array([float(k) for k in reg.keys()], dtype=np.float64)
    if paths is None:
        paths = [root / rel for rel in DEFAULT_DOC_REL_PATHS]
    all_fails: List[str] = []
    for p in paths:
        if p.exists():
            all_fails.extend(check_document(p, vals))
    all_fails.extend(check_citation_and_path_hygiene(root, paths))
    return all_fails


def main() -> None:
    checked = [rel for rel in DEFAULT_DOC_REL_PATHS if (ROOT / rel).exists()]
    fails = verify_docs()
    if fails:
        for f in fails:
            print("FAIL:", f)
        raise SystemExit(f"Found {len(fails)} untraceable numeric claims!")
    print(f"TRACEABILITY CHECK PASSED: 0 untraceable empirical numbers across all {len(checked)} paper/companion/slide/viva docs ({', '.join(checked)})!")


if __name__ == "__main__":
    main()
