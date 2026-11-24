#!/usr/bin/env python3
"""Build Revision v7 publication deliverables from canonical markdown & results:
  1. paper/MandiGuard_Research_Paper.html & .pdf (from paper/manuscript.md)
  2. paper/manuscript.tex (compile-ready LaTeX linking paper/references.bib)
  3. paper/MandiGuard_Research_Paper.docx (Word submission bundle)
  4. paper/MandiGuard_Easy_Reading_Edition.html & .pdf (from 12th_class_easy_reading_edition.md)
  5. viva/MandiGuard_Viva_Defense_Slides.html & .pdf (12-slide 16:9 widescreen deck)

Portable across machines (zero hardcoded home paths); renders crisp (Author, Year)
citations from references.bib; validates output PDFs via pypdf.
"""

from __future__ import annotations

import base64
import html
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"
PAPER_DIR = ROOT / "paper"
VIVA_DIR = ROOT / "viva"

FORBIDDEN_LATEX_LEAKS = [
    r"\frac",
    r"\text{",
    r"\Longleftrightarrow",
    r"\Delta\text",
    r"\times",
    r"\cdot",
    r"\implies",
    r"\lfloor",
    r"\rfloor",
    r"\widehat",
    r"\left(",
    r"\right)",
    r"\big(",
    r"\big)",
    r"\Big(",
    r"\Big)",
    r"\sum_",
    r"\tau_",
    r"\kappa",
    r"\theta",
    r"\equiv",
    r"\cap",
]

FORBIDDEN_LEGACY_STRINGS = [
    "B3_MLPoint",
    "cvar_10",
    "fig1_phantom_arbitrage",
    "fig2_main_policy_comparison",
    "≤ ft(",
    r"\%",
    "@@TOK",
    "<br",
    "**",
    "/" + "Users/",
    "TO CONFIRM",
    "Crushes",
    "slashes",
    "slashing",
    "$S_",
    "[jensen2007digital]",
    "[baulch1997transfer]",
    "exploratory: true",
    "make reproduce",
]

PAPER_TABLE_CAPTIONS: Dict[int, str] = {
    1: "Epistemic classification of observed quantities, causal <= t - 1 features, stylized survey-anchored assumptions, bounded unobservables, and out-of-scope mechanisms.",
    2: "Main equal-menu lagged test benchmark on the zero-lookahead 171-market panel (N = 57,634, 20C closed-yard settlement) reporting both unconditional ES10 and dispatched cond_ES10.",
    3: "Specification-locked exploratory PREREG_A18 four-test family (R = 2,000, two-sided p_holm_2s_prereg4) alongside unregistered secondary contrasts across three State-prefixed clusterings.",
    4: "2x2 orthogonal decomposition (cv28 vs p_dow), scale-invariant 24*tau triage, and clean 5m vs 17m ML/OR/heteroscedastic Split-CQR Pareto frontier trained on purged validation data (N = 57,634), including ML_HGBR_Q20_m0.",
    5: "Summary of counterfactual missingness, <= t - 2 portal latency, repaired return-leg Schedule #7 x ERA5 x Stoch_CondMAR, non-collided geocodes, outsider MinPrice+LCV stress, and clean 166-market 2018-2023 archives.",
}


_CORP_AUTHOR_MAP = {
    "nabcons2022phl": "NABCONS",
    "pib154554apmc": "PIB relid=154554",
    "nss77report587": "NSO MoSPI",
    "hpeconsurvey2026": "GoHP",
    "nitiaayog2021freight": "NITI Aayog & RMI",
}


def _strip_tex_accents(s: str) -> str:
    rep = [
        (r"{\`e}", "è"),
        (r"{\'e}", "é"),
        (r"{\v{e}}", "ě"),
        (r"{\v{c}}", "č"),
        (r"{\v{s}}", "š"),
        (r"{\v{r}}", "ř"),
        (r"{\r{u}}", "ů"),
        (r"{\'a}", "á"),
        (r"{\"a}", "ä"),
        (r"\&", "&"),
    ]
    for a, b in rep:
        s = s.replace(a, b)
    s = re.sub(r"[{}]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def build_author_year_map(bib_text: str | None = None) -> Dict[str, str]:
    """Parse paper/references.bib into clean '(Author, Year)' display strings."""
    if bib_text is None:
        bib_text = (PAPER_DIR / "references.bib").read_text(encoding="utf-8")
    mapping: Dict[str, str] = {}
    entries = re.split(r"(?=@\w+\s*\{)", bib_text)
    for ent in entries:
        m_hdr = re.match(r"@\w+\s*\{\s*([^,\s]+)\s*,", ent)
        if not m_hdr:
            continue
        key = m_hdr.group(1)
        m_yr = re.search(r"\byear\s*=\s*\{([^}]+)\}", ent)
        yr = m_yr.group(1).strip() if m_yr else ""
        if key in _CORP_AUTHOR_MAP:
            mapping[key] = f"{_CORP_AUTHOR_MAP[key]}, {yr}"
            continue
        m_au = re.search(r"\b(?:author|editor)\s*=\s*\{(.+?)\}\s*(?:,\s*\n|\n\s*\})", ent, flags=re.S)
        raw_au = m_au.group(1) if m_au else key
        parts = [p.strip() for p in re.split(r"\s+and\s+", raw_au.strip(), flags=re.I) if p.strip()]
        has_others = bool(parts and parts[-1].lower() == "others")
        if has_others:
            parts = parts[:-1]

        def _surname(p: str) -> str:
            clean = _strip_tex_accents(p)
            return clean.split(",")[0].strip() if "," in clean else clean.split()[-1].strip()

        surnames = [_surname(p) for p in parts if p]
        if not surnames:
            author_lbl = key
        elif has_others or len(surnames) >= 3:
            author_lbl = f"{surnames[0]} et al."
        elif len(surnames) == 2:
            author_lbl = f"{surnames[0]} & {surnames[1]}"
        else:
            author_lbl = surnames[0]
        mapping[key] = f"{author_lbl}, {yr}"
    return mapping


def _resolve_bib_map(bib_keys: Dict[str, str] | set[str] | None) -> Dict[str, str]:
    full = build_author_year_map()
    if isinstance(bib_keys, dict):
        return bib_keys
    if isinstance(bib_keys, set):
        return {k: full.get(k, k) for k in bib_keys}
    return full


def find_chrome() -> Path:
    env_bin = os.environ.get("CHROME_BIN")
    if env_bin and Path(env_bin).exists():
        return Path(env_bin)
    candidates = [
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    ]
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError("Headless Chrome/Chromium binary not found. Set CHROME_BIN to override.")


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    chrome = find_chrome()
    cmd = [
        str(chrome),
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path.resolve().as_uri(),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not pdf_path.exists():
        raise RuntimeError(f"Chrome PDF build failed for {pdf_path.name}: {proc.stderr or proc.stdout}")


def b64_img(rel_or_name: str) -> str:
    p = (FIG_DIR / Path(rel_or_name).name).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Missing figure: {p}")
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")


def _extract_balanced(s: str, pos: int) -> Tuple[str, int]:
    """Extract content inside balanced {...} starting at '{' index pos."""
    if pos >= len(s) or s[pos] != "{":
        return "", pos
    depth = 0
    start = pos + 1
    i = pos
    while i < len(s):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start:i], i + 1
        i += 1
    return s[start:], len(s)


def latex_to_html_fragment(expr: str) -> str:
    """Convert inline/display LaTeX math into crisp HTML spans & Unicode math."""
    s = expr.strip()
    # Hold escaped underscores so identifiers inside \text{...} never become subscripts
    s = s.replace(r"\_", "@@UNDER@@").replace(r"\,", "\u2009").replace(r"\;", " ").replace(r"\!", "")
    s = s.replace(r"\quad", "\u2003").replace(r"\qquad", "\u2003\u2003")

    # Simple symbol substitutions first (longest keys first so \left( beats \le)
    sym_map = [
        (r"\Longleftrightarrow", " &#10234; "),
        (r"\iff", " &#8660; "),
        (r"\implies", " &#10233; "),
        (r"\to", " &#8594; "),
        (r"\cdot", "&#183;"),
        (r"\times", "&#215;"),
        (r"\approx", " &#8776; "),
        (r"\le", " &#8804; "),
        (r"\ge", " &#8805; "),
        (r"\ne", " &#8800; "),
        (r"\equiv", " &#8801; "),
        (r"\cap", " &#8745; "),
        (r"\in", " &#8712; "),
        (r"\dots", "&#8230;"),
        (r"\lfloor", "&#8970;"),
        (r"\rfloor", "&#8971;"),
        (r"\left(", "("),
        (r"\right)", ")"),
        (r"\left\{", "{"),
        (r"\right\}", "}"),
        (r"\big(", "("),
        (r"\big)", ")"),
        (r"\Big(", "("),
        (r"\Big)", ")"),
        (r"\big\{", "{"),
        (r"\big\}", "}"),
        (r"\%", "%"),
        (r"\{", "{"),
        (r"\}", "}"),
        (r"\Delta", "&#916;"),
        (r"\alpha", "&#945;"),
        (r"\beta", "&#946;"),
        (r"\gamma", "&#947;"),
        (r"\theta", "&#952;"),
        (r"\lambda", "&#955;"),
        (r"\mu", "&#956;"),
        (r"\sigma", "&#963;"),
        (r"\kappa", "&#954;"),
        (r"\tau", "&#964;"),
        (r"\arg", "arg"),
        (r"\min", "min"),
        (r"\max", "max"),
    ]
    for k, v in sorted(sym_map, key=lambda kv: -len(kv[0])):
        s = s.replace(k, v)

    # Iterative balanced macro replacements (\text, \widehat, \hat, \sum, \frac)
    for _ in range(64):
        changed = False
        # \text{...}
        idx = s.find(r"\text{")
        if idx != -1:
            inner, end = _extract_balanced(s, idx + 5)
            s = s[:idx] + f'<span class="mtxt">{html.escape(inner)}</span>' + s[end:]
            changed = True
            continue
        # \widehat{...}
        idx = s.find(r"\widehat{")
        if idx != -1:
            inner, end = _extract_balanced(s, idx + 8)
            s = s[:idx] + f'<span class="hat">{inner}&#770;</span>' + s[end:]
            changed = True
            continue
        # \hat{...}
        idx = s.find(r"\hat{")
        if idx != -1:
            inner, end = _extract_balanced(s, idx + 4)
            s = s[:idx] + f"{inner}&#770;" + s[end:]
            changed = True
            continue
        # \frac{a}{b}
        idx = s.find(r"\frac{")
        if idx != -1:
            num, p1 = _extract_balanced(s, idx + 5)
            if p1 < len(s) and s[p1] == "{":
                den, p2 = _extract_balanced(s, p1)
                frac_html = f'<span class="frac"><span class="num">{num}</span><span class="den">{den}</span></span>'
                s = s[:idx] + frac_html + s[p2:]
                changed = True
                continue
        if not changed:
            break

    # \sum_{i=1}^{k}
    s = re.sub(r"\\sum_\{([^}]+)\}\^\{([^}]+)\}", r"&#8721;<sub>\1</sub><sup>\2</sup>", s)
    s = s.replace(r"\sum", "&#8721;")

    # Subscripts & superscripts outside tags
    s = re.sub(r"_\{([^}]+)\}", r"<sub>\1</sub>", s)
    s = re.sub(r"_([A-Za-z0-9])", r"<sub>\1</sub>", s)
    s = re.sub(r"\^\{([^}]+)\}", r"<sup>\1</sup>", s)
    s = re.sub(r"\^\*", r"<sup>*</sup>", s)
    s = s.replace("@@UNDER@@", "_")

    # Clean leftover backslashes
    assert not any(tok in s for tok in FORBIDDEN_LATEX_LEAKS), f"Unrendered LaTeX leak in HTML math: {s}"
    return s


def latex_to_plain_unicode(expr: str) -> str:
    """Convert LaTeX math into clean Unicode text for DOCX / slide captions."""
    s = expr.strip()
    s = s.replace(r"\_", "_").replace(r"\,", " ").replace(r"\;", " ").replace(r"\!", "")
    s = s.replace(r"\quad", "   ").replace(r"\qquad", "     ")
    uni_map = [
        (r"\Longleftrightarrow", " ⟺ "),
        (r"\implies", " ⇒ "),
        (r"\to", " → "),
        (r"\cdot", "·"),
        (r"\times", "×"),
        (r"\approx", " ≈ "),
        (r"\le", " ≤ "),
        (r"\ge", " ≥ "),
        (r"\ne", " ≠ "),
        (r"\equiv", " ≡ "),
        (r"\cap", " ∩ "),
        (r"\in", " ∈ "),
        (r"\dots", "…"),
        (r"\lfloor", "⌊"),
        (r"\rfloor", "⌋"),
        (r"\left(", "("),
        (r"\right)", ")"),
        (r"\left\{", "{"),
        (r"\right\}", "}"),
        (r"\big(", "("),
        (r"\big)", ")"),
        (r"\Big(", "("),
        (r"\Big)", ")"),
        (r"\big\{", "{"),
        (r"\big\}", "}"),
        (r"\%", "%"),
        (r"\{", "{"),
        (r"\}", "}"),
        (r"\Delta", "Δ"),
        (r"\alpha", "α"),
        (r"\beta", "β"),
        (r"\gamma", "γ"),
        (r"\theta", "θ"),
        (r"\lambda", "λ"),
        (r"\mu", "μ"),
        (r"\sigma", "σ"),
        (r"\kappa", "κ"),
        (r"\tau", "τ"),
        (r"\min", "min"),
        (r"\max", "max"),
    ]
    for k, v in sorted(uni_map, key=lambda kv: -len(kv[0])):
        s = s.replace(k, v)
    for _ in range(64):
        if r"\text{" in s:
            i = s.find(r"\text{")
            inner, end = _extract_balanced(s, i + 5)
            s = s[:i] + inner + s[end:]
            continue
        if r"\widehat{" in s:
            i = s.find(r"\widehat{")
            inner, end = _extract_balanced(s, i + 8)
            s = s[:i] + inner + "\u0302" + s[end:]
            continue
        if r"\hat{" in s:
            i = s.find(r"\hat{")
            inner, end = _extract_balanced(s, i + 4)
            s = s[:i] + inner + "\u0302" + s[end:]
            continue
        if r"\frac{" in s:
            i = s.find(r"\frac{")
            num, p1 = _extract_balanced(s, i + 5)
            if p1 < len(s) and s[p1] == "{":
                den, p2 = _extract_balanced(s, p1)
                s = s[:i] + f"({num}) / ({den})" + s[p2:]
                continue
        break
    s = re.sub(r"\\sum_\{([^}]+)\}\^\{([^}]+)\}", r"∑_{\1}^{\2}", s)
    s = re.sub(r"_\{([^}]+)\}", r"_\1", s)
    s = re.sub(r"\^\{([^}]+)\}", r"^\1", s)
    return re.sub(r"\s+", " ", s).strip()


def format_inline_html(text: str, bib_keys: Dict[str, str] | set[str] | None = None) -> str:
    """Format inline markdown (code, bold, italic, math, links, Author-Year cites) cleanly to HTML."""
    bib_map = _resolve_bib_map(bib_keys)
    tokens: Dict[str, str] = {}

    def hold(rendered: str) -> str:
        tok = f"@@TOK{len(tokens)}@@"
        tokens[tok] = rendered
        return tok

    # 1. Backtick code spans
    text = re.sub(r"`([^`]+)`", lambda m: hold(f"<code>{html.escape(m.group(1))}</code>"), text)
    # 2a. Accidental inline display-math spans $$...$$ (e.g. indented under list items)
    text = re.sub(r"\$\$([^$\n]+?)\$\$", lambda m: hold(f'<div class="eq-box">{latex_to_html_fragment(m.group(1))}</div>'), text)
    # 2b. Inline math spans $...$
    text = re.sub(r"\$([^$\n]+?)\$", lambda m: hold(f'<span class="math-inline">{latex_to_html_fragment(m.group(1))}</span>'), text)
    # 3. Markdown links [label](url)
    text = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", lambda m: hold(f'<a href="{html.escape(m.group(2))}">{html.escape(m.group(1))}</a>'), text)

    # Escape raw HTML characters in remaining prose
    esc = html.escape(text, quote=False)
    # Bold & Italic
    esc = re.sub(r"\*\*\*([^\*]+)\*\*\*", r"<strong><em>\1</em></strong>", esc)
    esc = re.sub(r"\*\*([^\*]+)\*\*", r"<strong>\1</strong>", esc)
    esc = re.sub(r"\*([^*\n]+)\*", r"<em>\1</em>", esc)

    # Render bib keys cleanly as Academic Author-Year citations: (Jensen, 2007; Goyal, 2010)
    def _cite_repl(m: re.Match) -> str:
        raw = m.group(1)
        parts = [p.strip() for p in re.split(r"[,;]\s*", raw) if p.strip()]
        if parts and all(p in bib_map for p in parts):
            joined = "; ".join(html.escape(bib_map[p]) for p in parts)
            return f'<span class="cite">({joined})</span>'
        return m.group(0)
    esc = re.sub(r"\[([a-z0-9_,;\s]+)\]", _cite_repl, esc)

    for tok, val in reversed(list(tokens.items())):
        esc = esc.replace(tok, val)
    assert "@@TOK" not in esc, f"Unexpanded token leaked in inline HTML: {esc}"
    return esc


def _split_md_table_row(row: str) -> List[str]:
    """Split a Markdown pipe table row while ignoring `|` inside code spans or escaped `\\|`."""
    s = row.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    cells: List[str] = []
    cur: List[str] = []
    in_code = False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
            cur.append(ch)
        elif ch == "|" and not in_code:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def markdown_to_html_body(
    md_text: str,
    bib_keys: Dict[str, str] | set[str] | None = None,
    base_dir: Path = PAPER_DIR,
    table_captions: Dict[int, str] | None = None,
) -> str:
    """Convert structured Markdown (headings, tables, blockquotes, lists, display math, images) to HTML."""
    bib_map = _resolve_bib_map(bib_keys)
    lines = md_text.splitlines()
    out: List[str] = []
    i = 0
    tbl_idx = 0
    in_references = False

    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()

        if stripped in ("<!-- WORKED_EXAMPLE_START -->", "<!-- WORKED_EXAMPLE_END -->"):
            i += 1
            continue
        if stripped == "---":
            out.append("<hr>")
            i += 1
            continue
        if not stripped:
            i += 1
            continue

        # Headings
        hm = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if hm:
            lvl = len(hm.group(1))
            title_txt = hm.group(2)
            if title_txt.lower().startswith("references"):
                in_references = True
            if lvl == 1:
                out.append(f'<h1 class="doc-title">{format_inline_html(title_txt, bib_keys)}</h1>')
            elif lvl == 2:
                out.append(f'<h2>{format_inline_html(title_txt, bib_keys)}</h2>')
            else:
                out.append(f'<h3>{format_inline_html(title_txt, bib_keys)}</h3>')
            i += 1
            continue

        # Display equation $$...$$
        if stripped.startswith("$$"):
            eq_lines = [stripped]
            while not eq_lines[-1].endswith("$$") or (len(eq_lines) == 1 and eq_lines[0] == "$$"):
                i += 1
                if i >= len(lines):
                    break
                eq_lines.append(lines[i].strip())
            raw_eq = " ".join(eq_lines).strip()
            raw_eq = raw_eq.strip("$").strip()
            out.append(f'<div class="eq-box">{latex_to_html_fragment(raw_eq)}</div>')
            i += 1
            continue

        # Standalone image ![alt](path)
        im = re.match(r"^!\[(.*?)\]\(([^\)]+)\)$", stripped)
        if im:
            alt, rel_path = im.group(1), im.group(2)
            fig_uri = b64_img(rel_path)
            out.append(
                f'<figure class="fig-card"><img src="{fig_uri}" alt="{html.escape(alt)}">'
                f'<figcaption>{format_inline_html(alt, bib_keys)}</figcaption></figure>'
            )
            i += 1
            continue

        # Blockquote / Worked Example
        if stripped.startswith(">"):
            bq_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                bq_lines.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            inner_html = markdown_to_html_body("\n".join(bq_lines), bib_keys=bib_keys, base_dir=base_dir)
            cls = "worked-box" if "Worked" in " ".join(bq_lines) else "note-box"
            out.append(f'<div class="{cls}">{inner_html}</div>')
            continue

        # Markdown Table
        if stripped.startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|") and "---" in lines[i + 1]:
            hdr = _split_md_table_row(stripped)
            align_raw = _split_md_table_row(lines[i + 1])
            aligns = ["right" if a.endswith(":") and not a.startswith(":") else ("center" if a.startswith(":") and a.endswith(":") else "left") for a in align_raw]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_split_md_table_row(lines[i]))
                i += 1
            tbl_idx += 1
            tbl = ['<div class="tbl-wrap">']
            if table_captions and tbl_idx in table_captions:
                tbl.append(
                    f'<div class="tbl-cap"><strong>Table {tbl_idx}:</strong> '
                    f'{format_inline_html(table_captions[tbl_idx], bib_keys)}</div>'
                )
            tbl.append('<table><thead><tr>')
            for idx_c, h in enumerate(hdr):
                al = aligns[idx_c] if idx_c < len(aligns) else "left"
                tbl.append(f'<th style="text-align:{al}">{format_inline_html(h, bib_keys)}</th>')
            tbl.append("</tr></thead><tbody>")
            for r in rows:
                tbl.append("<tr>")
                for idx_c, cell in enumerate(r):
                    al = aligns[idx_c] if idx_c < len(aligns) else "left"
                    tbl.append(f'<td style="text-align:{al}">{format_inline_html(cell, bib_keys)}</td>')
                tbl.append("</tr>")
            tbl.append("</tbody></table></div>")
            out.append("".join(tbl))
            continue

        # Numbered list (preserve explicit start ordinal across split display equations / tables)
        m_ol_start = re.match(r"^(\d+)\.\s+", stripped)
        if m_ol_start:
            start_num = int(m_ol_start.group(1))
            items: List[Tuple[str, List[str]]] = []
            while i < len(lines):
                s = lines[i].strip()
                m_ol = re.match(r"^\d+\.\s+(.*)$", s)
                if m_ol:
                    items.append((m_ol.group(1), []))
                    i += 1
                elif items and re.match(r"^[-*]\s+", s):
                    sub_li = re.sub(r"^[-*]\s+", "", s)
                    items[-1][1].append(sub_li)
                    i += 1
                else:
                    break
            li_parts = []
            for main_it, sub_its in items:
                main_h = format_inline_html(main_it, bib_keys)
                if sub_its:
                    sub_h = "<ul>" + "".join(f"<li>{format_inline_html(sb, bib_keys)}</li>" for sb in sub_its) + "</ul>"
                    li_parts.append(f"<li>{main_h}{sub_h}</li>")
                else:
                    li_parts.append(f"<li>{main_h}</li>")
            start_attr = f' start="{start_num}"' if start_num != 1 else ""
            out.append(f"<ol{start_attr}>{''.join(li_parts)}</ol>")
            continue

        # Bulleted list
        if re.match(r"^[-*]\s+", stripped):
            items = []
            while i < len(lines):
                s = lines[i].strip()
                if re.match(r"^[-*]\s+", s):
                    item_txt = re.sub(r"^[-*]\s+", "", s)
                    if in_references:
                        item_txt = re.sub(r"^`?\[[a-z0-9_]+\]`?\s*", "", item_txt)
                    items.append([item_txt])
                    i += 1
                elif lines[i].startswith("  ") and s and items:
                    items[-1].append(s)
                    i += 1
                else:
                    break
            cls = ' class="ref-list"' if in_references else ""
            lis = "".join(f"<li>{format_inline_html(' '.join(it), bib_map)}</li>" for it in items)
            out.append(f"<ul{cls}>{lis}</ul>")
            continue

        # Paragraph
        para_lines = []
        while i < len(lines):
            s = lines[i].strip()
            if not s or s == "---" or s.startswith("#") or s.startswith("$$") or s.startswith(">") or s.startswith("|") or re.match(r"^!\[", s) or re.match(r"^[-*]\s+", s) or re.match(r"^\d+\.\s+", s) or s.startswith("<!--"):
                break
            para_lines.append(s)
            i += 1
        out.append(f"<p>{format_inline_html(' '.join(para_lines), bib_keys)}</p>")

    return "\n".join(out)


PAPER_CSS = """
@page { size: A4; margin: 11.5mm 12.5mm 12.5mm 12.5mm; }
* { box-sizing: border-box; }
body {
  font-family: "Georgia", "Times New Roman", serif;
  color: #1a202c;
  font-size: 8.8pt;
  line-height: 1.38;
  max-width: 185mm;
  margin: 0 auto;
  background: #ffffff;
}
.title-banner {
  border-bottom: 2.5px solid #0f4c5c;
  padding-bottom: 8px;
  margin-bottom: 10px;
}
.meta-pill {
  display: inline-block;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 7.2pt;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #0f4c5c;
  background: #e6f4f6;
  padding: 2px 8px;
  border-radius: 3px;
  margin-bottom: 4px;
}
h1.doc-title {
  font-size: 15.2pt;
  line-height: 1.18;
  color: #0f293a;
  margin: 3px 0 4px 0;
}
.subline {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 7.9pt;
  color: #475569;
}
h2 {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 10.8pt;
  color: #0f4c5c;
  border-bottom: 1px solid #cbd5e1;
  padding-bottom: 2px;
  margin: 11px 0 5px 0;
  break-after: avoid;
}
h3 {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 9.4pt;
  color: #1e3a5f;
  margin: 7.5px 0 3.5px 0;
  break-after: avoid;
}
p { margin: 0 0 5px 0; text-align: justify; }
ul, ol { margin: 3px 0 5.5px 0; padding-left: 16px; }
li { margin-bottom: 2px; }
hr { border: none; border-top: 1px solid #e2e8f0; margin: 8px 0; }
code {
  font-family: "SFMono-Regular", Menlo, Consolas, monospace;
  font-size: 7.7pt;
  background: #f1f5f9;
  color: #0f172a;
  padding: 0.5px 3px;
  border-radius: 3px;
}
.math-inline {
  font-family: "Georgia", "Times New Roman", serif;
  font-style: italic;
}
.math-inline .mtxt, .eq-box .mtxt { font-style: normal; font-family: "Georgia", serif; }
.eq-box {
  background: #f8fafc;
  border-left: 3px solid #0f4c5c;
  padding: 5px 10px;
  margin: 6px 0;
  text-align: center;
  font-size: 9.5pt;
  break-inside: avoid;
}
.frac {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  vertical-align: middle;
  margin: 0 2px;
  font-size: 0.9em;
  line-height: 1.1;
}
.frac .num { border-bottom: 1px solid #1a202c; padding: 0 3px 1px 3px; white-space: nowrap; }
.frac .den { padding: 1px 3px 0 3px; white-space: nowrap; }
.tbl-wrap { margin: 5px 0 7px 0; break-inside: avoid; }
.tbl-cap { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 7.2pt; color: #334155; margin-bottom: 2px; line-height: 1.24; }
table {
  width: 100%;
  border-collapse: collapse;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 6.7pt;
  line-height: 1.22;
}
th {
  background: #0f4c5c;
  color: #ffffff;
  font-weight: 600;
  padding: 2.6px 2.8px;
  border-bottom: 1.5px solid #0a3642;
  white-space: normal;
}
th code { background: rgba(255, 255, 255, 0.18); color: #ffffff; }
td {
  padding: 2.5px 2.8px;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: top;
}
td[style*="right"] { white-space: nowrap; }
td:first-child code { font-size: 6.5pt; }
tbody tr:nth-child(even) { background: #f8fafc; }
.worked-box, .note-box {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-left: 4px solid #0284c7;
  border-radius: 4px;
  padding: 6px 9px;
  margin: 6px 0 8px 0;
  font-size: 8.3pt;
  break-inside: avoid;
}
.worked-box p:last-child, .worked-box ol:last-child, .worked-box ul:last-child { margin-bottom: 0; }
figure.fig-card {
  margin: 7px 0 8px 0;
  padding: 4px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: #ffffff;
  break-inside: avoid;
  text-align: center;
}
figure.fig-card img { max-width: 100%; max-height: 67mm; width: auto; height: auto; display: block; margin: 0 auto 3.5px auto; }
figcaption { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
figure.fig-card figcaption {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 7.4pt;
  color: #334155;
  text-align: left;
  line-height: 1.28;
}
.cite { color: #0f4c5c; font-size: 8.5pt; }
ul.ref-list {
  font-size: 7.1pt;
  line-height: 1.24;
  padding-left: 13px;
  column-count: 2;
  column-gap: 12px;
}
ul.ref-list li { margin-bottom: 2px; break-inside: avoid; }
"""


def _split_manuscript_header(lines: List[str]) -> Tuple[str, str, List[str]]:
    """Return (title, author_line, remaining_body_lines) without duplicating the author line."""
    title_line = lines[0].lstrip("# ").strip()
    author_line = "Aditya Sharma (M.Tech Thesis Research, supervised by Dr. Sonia) — Shoolini University, Solan, Himachal Pradesh, India"
    body_start = 1
    for idx in range(1, min(6, len(lines))):
        s = lines[idx].strip()
        if not s:
            continue
        if s.startswith("**Aditya Sharma**"):
            author_line = s.replace("**", "")
            body_start = idx + 1
        break
    return title_line, author_line, lines[body_start:]


def build_paper_html_and_pdf(bib_map: Dict[str, str]) -> None:
    ms_text = (PAPER_DIR / "manuscript.md").read_text()
    title_line, author_line, body_lines = _split_manuscript_header(ms_text.splitlines())
    body_html = markdown_to_html_body(
        "\n".join(body_lines),
        bib_keys=bib_map,
        base_dir=PAPER_DIR,
        table_captions=PAPER_TABLE_CAPTIONS,
    )

    doc_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(title_line)}</title>
<style>{PAPER_CSS}
.author-line {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 8.8pt; font-weight: 600; color: #1e293b; margin: 3px 0 3px 0; }}
</style>
</head>
<body>
<div class="title-banner">
  <span class="meta-pill">M.Tech Research Manuscript &bull; Revision v8 Audited</span>
  <h1 class="doc-title">{html.escape(title_line)}</h1>
  <div class="author-line">{html.escape(author_line)}</div>
  <div class="subline">Zero-Lookahead 171-Mkt Panel &bull; &lt;= t&minus;1 Firewall &bull; Exploratory PREREG_A18 (R = 2,000) &amp; CGM G* &bull; 17m ML Frontier &amp; 2&times;2 Split &bull; Clean 166-Mkt 2018&ndash;2023</div>
</div>
{body_html}
</body>
</html>
"""
    html_out = PAPER_DIR / "MandiGuard_Research_Paper.html"
    pdf_out = PAPER_DIR / "MandiGuard_Research_Paper.pdf"
    html_out.write_text(doc_html, encoding="utf-8")
    render_pdf(html_out, pdf_out)
    print(f"Built {html_out.name} & {pdf_out.name} ({len(PdfReader(str(pdf_out)).pages)} pages)")


def build_easy_reading_html_and_pdf(bib_map: Dict[str, str]) -> None:
    ez_text = (PAPER_DIR / "12th_class_easy_reading_edition.md").read_text()
    # Append 2 key visual figures so the standalone PDF is visually complete
    ez_text += (
        "\n\n---\n\n## 5. Visual Summary Charts\n\n"
        "![Risk-coverage curves and zero-tuned-parameter tail savings (Safe_EV_Sunk_m0 & RT_2F_Min_m0)](../figures/rev_fig1_risk_coverage_ci.png)\n\n"
        "![Fair controls and crop/state breakdown across Onion, Potato, Tomato, NonApple, and Apple](../figures/rev_fig2_ablations_and_crops.png)\n"
    )
    lines = ez_text.splitlines()
    title_line = lines[0].lstrip("# ").strip()
    body_html = markdown_to_html_body("\n".join(lines[1:]), bib_keys=bib_map, base_dir=PAPER_DIR)

    ez_css = PAPER_CSS + """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 9.5pt; }
p { text-align: left; }
"""
    doc_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(title_line)}</title>
<style>{ez_css}</style>
</head>
<body>
<div class="title-banner">
  <span class="meta-pill">Plain-English Pocket-Calculator Edition &bull; Revision v8 Audited</span>
  <h1 class="doc-title">{html.escape(title_line)}</h1>
  <div class="subline">Aditya Sharma (Supervised by Dr. Sonia) &mdash; Shoolini University, Solan, Himachal Pradesh, India &bull; Zero-Tuned-Parameter <code>Safe_EV_Sunk_m0</code> &amp; Class-8 <code>RT_2F_Min_m0</code> (<code>4.3 &rarr; 1.2 / 5</code> Difficulty)</div>
</div>
{body_html}
</body>
</html>
"""
    html_out = PAPER_DIR / "MandiGuard_Easy_Reading_Edition.html"
    pdf_out = PAPER_DIR / "MandiGuard_Easy_Reading_Edition.pdf"
    html_out.write_text(doc_html, encoding="utf-8")
    render_pdf(html_out, pdf_out)
    print(f"Built {html_out.name} & {pdf_out.name} ({len(PdfReader(str(pdf_out)).pages)} pages)")


def _tex_escape_plain(s: str) -> str:
    """Escape plain LaTeX text (outside math & code) into strict 7-bit ASCII."""
    s = s.replace("\\", r"\textbackslash{}")
    for ch, rep in [
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]:
        s = s.replace(ch, rep)
    s = s.replace("₹", r"Rs.\,")
    s = s.replace("−", "-").replace("–", "--").replace("—", "---")
    s = s.replace("≤", r"$\le$").replace("≥", r"$\ge$").replace("≠", r"$\ne$")
    s = s.replace("°", r"$^\circ$").replace("×", r"$\times$").replace("->", r"$\to$").replace("→", r"$\to$")
    for u_ch, asc_rep in (
        ("κ", r"$\kappa$"),
        ("τ", r"$\tau$"),
        ("α", r"$\alpha$"),
        ("β", r"$\beta$"),
        ("γ", r"$\gamma$"),
        ("σ", r"$\sigma$"),
        ("λ", r"$\lambda$"),
        ("Δ", r"$\Delta$"),
        ("±", r"$\pm$"),
        ("⇔", r"$\iff$"),
        ("≈", r"$\approx$"),
        ("∩", r"$\cap$"),
        ("•", r"$\bullet$"),
    ):
        s = s.replace(u_ch, asc_rep)
    return s


def _format_inline_tex(text: str, bib_keys: set[str]) -> str:
    tokens: Dict[str, str] = {}

    def hold(val: str) -> str:
        k = f"TEXHOLD{len(tokens)}X"
        tokens[k] = val
        return k

    # Code spans
    text = re.sub(r"`([^`]+)`", lambda m: hold(r"\texttt{" + _tex_escape_plain(m.group(1)) + "}"), text)
    # Inline math spans (replace Unicode math symbols cleanly into ASCII TeX)
    def _math_fix(m: re.Match) -> str:
        inner = (
            m.group(1)
            .replace("₹", r"\text{Rs.\,}")
            .replace("−", "-")
            .replace("–", "-")
            .replace("×", r"\times ")
            .replace("≤", r"\le ")
            .replace("≥", r"\ge ")
            .replace("≠", r"\ne ")
            .replace("→", r"\to ")
            .replace("°", r"^\circ")
        )
        return hold("$" + inner + "$")

    text = re.sub(r"\$([^$\n]+?)\$", _math_fix, text)
    # Citations [k1, k2] where every item is in bib_keys -> natbib \citep{k1,k2}
    def _cite_fix(m: re.Match) -> str:
        parts = [p.strip() for p in re.split(r"[,;]\s*", m.group(1)) if p.strip()]
        if parts and all(p in bib_keys for p in parts):
            return hold(r"\citep{" + ",".join(parts) + "}")
        return m.group(0)

    text = re.sub(r"\[([a-z0-9_,;\s]+)\]", _cite_fix, text)
    # Markdown links [label](url)
    text = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", lambda m: hold(_tex_escape_plain(m.group(1))), text)

    esc = _tex_escape_plain(text)
    esc = re.sub(r"\*\*\*([^\*]+)\*\*\*", r"\\textbf{\\textit{\1}}", esc)
    esc = re.sub(r"\*\*([^\*]+)\*\*", r"\\textbf{\1}", esc)
    esc = re.sub(r"\*([^*\n]+)\*", r"\\textit{\1}", esc)

    for k, v in tokens.items():
        esc = esc.replace(k, v)
    return esc


def _md_to_tex_blocks(lines: List[str], bib_keys: set[str]) -> List[str]:
    out: List[str] = []
    tbl_counter = 0
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s or s == "---" or s in ("<!-- WORKED_EXAMPLE_START -->", "<!-- WORKED_EXAMPLE_END -->"):
            i += 1
            continue
        if s.startswith("## References"):
            break
        hm2 = re.match(r"^##\s+(.*)$", s)
        if hm2:
            title_clean = re.sub(r"^\d+\.\s+", "", hm2.group(1))
            if title_clean.lower() == "abstract":
                i += 1
                abs_lines = []
                while i < len(lines) and lines[i].strip() != "---":
                    if lines[i].strip():
                        abs_lines.append(_format_inline_tex(lines[i].strip(), bib_keys))
                    i += 1
                out.append("\\begin{abstract}\n" + "\n\n".join(abs_lines) + "\n\\end{abstract}\n")
            else:
                out.append(f"\\section{{{_format_inline_tex(title_clean, bib_keys)}}}\n")
                i += 1
            continue
        hm3 = re.match(r"^###\s+(.*)$", s)
        if hm3:
            title_clean = re.sub(r"^\d+\.\d+\s+", "", hm3.group(1))
            out.append(f"\\subsection{{{_format_inline_tex(title_clean, bib_keys)}}}\n")
            i += 1
            continue
        if s.startswith("$$"):
            eq_lines = [s]
            while not eq_lines[-1].endswith("$$") or (len(eq_lines) == 1 and eq_lines[0] == "$$"):
                i += 1
                if i >= len(lines):
                    break
                eq_lines.append(lines[i].strip())
            eq = " ".join(eq_lines).strip().strip("$").strip().replace("₹", r"\text{Rs.\,}").replace("−", "-")
            out.append(f"\\begin{{equation}}\n{eq}\n\\end{{equation}}\n")
            i += 1
            continue
        im = re.match(r"^!\[(.*?)\]\(([^\)]+)\)$", s)
        if im:
            cap, rel = im.group(1), im.group(2)
            out.append(
                "\\begin{figure}[htbp]\n\\centering\n"
                f"\\includegraphics[width=0.96\\linewidth]{{{rel}}}\n"
                f"\\caption{{{_format_inline_tex(cap, bib_keys)}}}\n"
                "\\end{figure}\n"
            )
            i += 1
            continue
        if s.startswith(">"):
            bq = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                bq.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            inner = _md_to_tex_blocks(bq, bib_keys)
            out.append("\\begin{quote}\n" + "\n".join(inner) + "\n\\end{quote}\n")
            continue
        if s.startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|") and "---" in lines[i + 1]:
            hdr = _split_md_table_row(s)
            al_raw = _split_md_table_row(lines[i + 1])
            cols_spec = "".join("r" if a.endswith(":") and not a.startswith(":") else "l" for a in al_raw)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_split_md_table_row(lines[i]))
                i += 1
            tbl_counter += 1
            cap_text = _tex_escape_plain(PAPER_TABLE_CAPTIONS.get(tbl_counter, f"{re.sub(r'[`*]', '', hdr[0])} summary table."))
            tlines = [
                "\\begin{table}[htbp]\n\\centering\n\\small\n",
                f"\\caption{{{cap_text}}}\\label{{tab:table{tbl_counter}}}\n",
                "\\resizebox{\\linewidth}{!}{\n",
                f"\\begin{{tabular}}{{{cols_spec}}}\n\\toprule\n",
                " & ".join(_format_inline_tex(h, bib_keys) for h in hdr) + " \\\\\n\\midrule\n",
            ]
            for r in rows:
                tlines.append(" & ".join(_format_inline_tex(c, bib_keys) for c in r) + " \\\\\n")
            tlines.append("\\bottomrule\n\\end{tabular}}\n\\end{table}\n")
            out.append("".join(tlines))
            continue
        m_ol_start = re.match(r"^(\d+)\.\s+", s)
        if m_ol_start:
            start_num = int(m_ol_start.group(1))
            items = []
            while i < len(lines):
                st = lines[i].strip()
                m_ol = re.match(r"^\d+\.\s+(.*)$", st)
                if m_ol:
                    items.append([m_ol.group(1)])
                    i += 1
                elif items and re.match(r"^[-*]\s+", st):
                    items[-1].append(" -- " + re.sub(r"^[-*]\s+", "", st))
                    i += 1
                else:
                    break
            body = "\n".join(f"  \\item {_format_inline_tex(' '.join(it), bib_keys)}" for it in items)
            set_cnt = f"  \\setcounter{{enumi}}{{{start_num - 1}}}\n" if start_num != 1 else ""
            out.append(f"\\begin{{enumerate}}\n{set_cnt}{body}\n\\end{{enumerate}}\n")
            continue
        if re.match(r"^[-*]\s+", s):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            body = "\n".join(f"  \\item {_format_inline_tex(it, bib_keys)}" for it in items)
            out.append(f"\\begin{{itemize}}\n{body}\n\\end{{itemize}}\n")
            continue
        para = []
        while i < len(lines):
            st = lines[i].strip()
            if not st or st == "---" or st.startswith("#") or st.startswith("$$") or st.startswith(">") or st.startswith("|") or re.match(r"^!\[", st) or re.match(r"^[-*]\s+", st) or re.match(r"^\d+\.\s+", st) or st.startswith("<!--"):
                break
            para.append(st)
            i += 1
        out.append(_format_inline_tex(" ".join(para), bib_keys) + "\n")
    return out


def build_latex_manuscript(bib_keys: set[str]) -> None:
    lines = (PAPER_DIR / "manuscript.md").read_text().splitlines()
    title_line, _author_line, body_lines = _split_manuscript_header(lines)
    blocks = _md_to_tex_blocks(body_lines, bib_keys)
    tex = (
        "\\documentclass[11pt,a4paper]{article}\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage[T1]{fontenc}\n"
        "\\usepackage[margin=22mm]{geometry}\n"
        "\\usepackage{amsmath,amssymb,booktabs,graphicx,hyperref,natbib,array,xcolor}\n"
        f"\\title{{{_tex_escape_plain(title_line)}}}\n"
        "\\author{Aditya Sharma (M.Tech Thesis Research, supervised by Dr. Sonia) \\\\ Shoolini University, Solan, Himachal Pradesh, India}\n"
        "\\date{Revision v8 --- Cleanroom Reproducible Retrospective Audit}\n"
        "\\begin{document}\n\\maketitle\n\n"
        + "\n".join(blocks)
        + "\n\\bibliographystyle{plainnat}\n\\bibliography{references}\n\\end{document}\n"
    )
    # Verify pure 7-bit ASCII, every \cite/\citep key, & \includegraphics path
    non_ascii = [(idx_c, ch, hex(ord(ch))) for idx_c, ch in enumerate(tex) if ord(ch) > 127]
    assert not non_ascii, f"Non-ASCII character(s) leaked into manuscript.tex: {non_ascii[:10]}"
    for cg in re.findall(r"\\citep?\{([^\}]+)\}", tex):
        for k in [p.strip() for p in cg.split(",")]:
            assert k in bib_keys, f"Unknown LaTeX cite key: {k}"
    for ig in re.findall(r"\\includegraphics\[[^\]]+\]\{([^\}]+)\}", tex):
        assert (PAPER_DIR / ig).resolve().exists(), f"Missing LaTeX graphic: {ig}"

    out_tex = PAPER_DIR / "manuscript.tex"
    out_tex.write_text(tex, encoding="utf-8")
    print(f"Built {out_tex.name} ({len(lines)} md lines -> {len(tex.splitlines())} tex lines)")


def _replace_bib_cites_plain(text: str, bib_map: Dict[str, str] | None) -> str:
    if not bib_map:
        return text

    def _repl(m: re.Match) -> str:
        parts = [p.strip() for p in re.split(r"[,;]\s*", m.group(1)) if p.strip()]
        if parts and all(p in bib_map for p in parts):
            return "(" + "; ".join(bib_map[p] for p in parts) + ")"
        return m.group(0)

    return re.sub(r"\[([a-z0-9_,;\s]+)\]", _repl, text)


def _add_inline_docx_runs(p, text: str, bib_map: Dict[str, str] | None = None) -> None:
    """Format inline bold, italic, code, math spans, and (Author, Year) citations into python-docx runs."""
    tokens: Dict[str, Tuple[str, str]] = {}

    def hold(kind: str, val: str) -> str:
        k = f"\x00D{len(tokens)}\x00"
        tokens[k] = (kind, val)
        return k

    text = re.sub(r"`([^`]+)`", lambda m: hold("code", m.group(1)), text)
    text = re.sub(r"\$([^$\n]+?)\$", lambda m: hold("math", latex_to_plain_unicode(m.group(1))), text)
    text = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", lambda m: m.group(1), text)
    text = _replace_bib_cites_plain(text, bib_map)
    # Split on **bold**, *italic*, or held tokens
    parts = re.split(r"(\*\*[^\*]+\*\*|\*[^*\n]+\*|\x00D\d+\x00)", text)
    for part in parts:
        if not part:
            continue
        if part in tokens:
            kind, val = tokens[part]
            r = p.add_run(val)
            if kind == "code":
                r.font.name = "Consolas"
                r.font.size = Pt(9.5)
            else:
                r.italic = True
        elif part.startswith("**") and part.endswith("**"):
            _add_inline_docx_runs_plain(p, part[2:-2], bold=True, tokens=tokens)
        elif part.startswith("*") and part.endswith("*"):
            _add_inline_docx_runs_plain(p, part[1:-1], italic=True, tokens=tokens)
        else:
            p.add_run(part)


def _add_inline_docx_runs_plain(p, sub: str, bold: bool = False, italic: bool = False, tokens: Dict[str, Tuple[str, str]] | None = None) -> None:
    for seg in re.split(r"(\x00D\d+\x00)", sub):
        if not seg:
            continue
        if tokens and seg in tokens:
            kind, val = tokens[seg]
            r = p.add_run(val)
            r.bold = bold
            if kind == "code":
                r.font.name = "Consolas"
                r.font.size = Pt(9.5)
            else:
                r.italic = True
        else:
            r = p.add_run(seg)
            r.bold = bold
            r.italic = italic


def build_docx_manuscript(bib_map: Dict[str, str] | None = None) -> None:
    if bib_map is None:
        bib_map = build_author_year_map()
    doc = Document()
    for sec in doc.sections:
        sec.top_margin = Inches(0.8)
        sec.bottom_margin = Inches(0.8)
        sec.left_margin = Inches(0.8)
        sec.right_margin = Inches(0.8)
    style = doc.styles["Normal"]
    style.font.name = "Georgia"
    style.font.size = Pt(10.5)

    raw_lines = (PAPER_DIR / "manuscript.md").read_text().splitlines()
    title_line, author_line, lines = _split_manuscript_header(raw_lines)
    h = doc.add_heading(title_line, level=0)
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_auth = doc.add_paragraph(author_line)
    p_auth.runs[0].bold = True
    sub = doc.add_paragraph("M.Tech Research Paper • Revision v8 Audited (Zero-Lookahead 171-Mkt Panel, Exploratory PREREG_A18 R = 2,000 & CGM G*, 17m ML Frontier & 2x2 Split, Clean 166-Mkt 2018–2023)")
    sub.runs[0].italic = True
    sub.runs[0].font.color.rgb = RGBColor(0x0F, 0x4C, 0x5C)

    i = 0
    tbl_idx = 0
    in_references = False
    while i < len(lines):
        s = lines[i].strip()
        if not s or s == "---" or s in ("<!-- WORKED_EXAMPLE_START -->", "<!-- WORKED_EXAMPLE_END -->"):
            i += 1
            continue
        hm2 = re.match(r"^##\s+(.*)$", s)
        if hm2:
            if hm2.group(1).lower().startswith("references"):
                in_references = True
            hp = doc.add_heading("", level=1)
            _add_inline_docx_runs(hp, hm2.group(1).replace("->", "→"), bib_map)
            i += 1
            continue
        hm3 = re.match(r"^###\s+(.*)$", s)
        if hm3:
            hp = doc.add_heading("", level=2)
            _add_inline_docx_runs(hp, hm3.group(1).replace("->", "→"), bib_map)
            i += 1
            continue
        if s.startswith("$$"):
            eq_lines = [s]
            while not eq_lines[-1].endswith("$$") or (len(eq_lines) == 1 and eq_lines[0] == "$$"):
                i += 1
                if i >= len(lines):
                    break
                eq_lines.append(lines[i].strip())
            eq_u = latex_to_plain_unicode(" ".join(eq_lines).strip().strip("$"))
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(eq_u)
            r.bold = True
            i += 1
            continue
        im = re.match(r"^!\[(.*?)\]\(([^\)]+)\)$", s)
        if im:
            cap, rel = im.group(1), im.group(2)
            fig_path = (PAPER_DIR / rel).resolve()
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.add_run().add_picture(str(fig_path), width=Inches(6.4))
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            rc = p_cap.add_run(cap)
            rc.italic = True
            rc.font.size = Pt(9)
            i += 1
            continue
        if s.startswith(">"):
            bq_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                bq_lines.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            for bl in bq_lines:
                if bl.strip():
                    pb = doc.add_paragraph()
                    pb.paragraph_format.left_indent = Inches(0.35)
                    _add_inline_docx_runs(pb, bl.strip(), bib_map)
            continue
        if s.startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|") and "---" in lines[i + 1]:
            hdr = _split_md_table_row(s)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_split_md_table_row(lines[i]))
                i += 1
            tbl_idx += 1
            if tbl_idx in PAPER_TABLE_CAPTIONS:
                p_tcap = doc.add_paragraph()
                rc_b = p_tcap.add_run(f"Table {tbl_idx}: ")
                rc_b.bold = True
                rc_b.font.size = Pt(9)
                rc_t = p_tcap.add_run(PAPER_TABLE_CAPTIONS[tbl_idx])
                rc_t.italic = True
                rc_t.font.size = Pt(9)
            tbl = doc.add_table(rows=1 + len(rows), cols=len(hdr))
            tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            tbl.style = "Table Grid"
            for ci, hv in enumerate(hdr):
                cell = tbl.rows[0].cells[ci]
                cell.text = ""
                p_c = cell.paragraphs[0]
                hv_c = _replace_bib_cites_plain(re.sub(r"[`*]", "", latex_to_plain_unicode(hv) if "$" in hv else hv), bib_map)
                run = p_c.add_run(hv_c)
                run.bold = True
                run.font.size = Pt(8)
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="0F4C5C"/>')
                cell._tc.get_or_add_tcPr().append(shading)
            for ri, rv in enumerate(rows, 1):
                for ci in range(len(hdr)):
                    val = rv[ci] if ci < len(rv) else ""
                    val_clean = re.sub(r"\$([^$]+)\$", lambda m: latex_to_plain_unicode(m.group(1)), val)
                    val_clean = _replace_bib_cites_plain(re.sub(r"[`*]", "", val_clean), bib_map)
                    cell = tbl.rows[ri].cells[ci]
                    cell.text = ""
                    rc = cell.paragraphs[0].add_run(val_clean)
                    rc.font.size = Pt(7.8)
            doc.add_paragraph("")
            continue
        if re.match(r"^\d+\.\s+", s):
            items = []
            while i < len(lines):
                st = lines[i].strip()
                m_ol = re.match(r"^\d+\.\s+(.*)$", st)
                if m_ol:
                    items.append([m_ol.group(1)])
                    i += 1
                elif items and re.match(r"^[-*]\s+", st):
                    items[-1].append(" • " + re.sub(r"^[-*]\s+", "", st))
                    i += 1
                else:
                    break
            for it in items:
                pl = doc.add_paragraph(style="List Number")
                _add_inline_docx_runs(pl, " ".join(it), bib_map)
            continue
        if re.match(r"^[-*]\s+", s):
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                item_txt = re.sub(r"^[-*]\s+", "", lines[i].strip())
                if in_references:
                    item_txt = re.sub(r"^`?\[[a-z0-9_]+\]`?\s*", "", item_txt)
                pl = doc.add_paragraph(style="List Bullet")
                _add_inline_docx_runs(pl, item_txt, bib_map)
                i += 1
            continue
        para = []
        while i < len(lines):
            st = lines[i].strip()
            if not st or st == "---" or st.startswith("#") or st.startswith("$$") or st.startswith(">") or st.startswith("|") or re.match(r"^!\[", st) or re.match(r"^[-*]\s+", st) or re.match(r"^\d+\.\s+", st) or st.startswith("<!--"):
                break
            para.append(st)
            i += 1
        pp = doc.add_paragraph()
        _add_inline_docx_runs(pp, " ".join(para), bib_map)

    out_docx = PAPER_DIR / "MandiGuard_Research_Paper.docx"
    doc.save(str(out_docx))
    print(f"Built {out_docx.name} ({out_docx.stat().st_size / 1024:.1f} KB)")


def build_viva_slides() -> None:
    """Build exact 12-slide 16:9 widescreen PDF matching final/SLIDE_OUTLINE.md & Revision v8."""
    splits_df = pd.read_csv(ROOT / "revision" / "results" / "v7_splits_171.csv")
    v7_main = pd.read_csv(ROOT / "revision" / "results" / "v7_main_171.csv").set_index("policy")
    v7_b2k = pd.read_csv(ROOT / "revision" / "results" / "v7_bootstrap_prereg_2000.csv")
    v7_be = pd.read_csv(ROOT / "revision" / "results" / "v7_breakeven_171.csv")
    v7_rec = pd.read_csv(ROOT / "revision" / "results" / "v7_era5_and_reconcile.csv").set_index("policy")
    v7_dec = pd.read_csv(ROOT / "revision" / "results" / "v7_decade_2018_2023.csv")
    v7_db = pd.read_csv(ROOT / "revision" / "results" / "v7_decade_boot_2000.csv")

    be_20c = v7_be[(v7_be["panel"] == "strict2024_171_20C_closed") & (v7_be["policy_a"] == "Safe_EV_Sunk_m0") & (v7_be["policy_b"] == "B2_age_matched")].iloc[0]
    be_era = v7_be[(v7_be["panel"] == "strict2024_171_ERA5_closed") & (v7_be["policy_a"] == "Safe_EV_Sunk_m0") & (v7_be["policy_b"] == "B2_age_matched")].iloc[0]
    es10_gain_171 = float(v7_b2k[(v7_b2k["cluster"] == "origin_x_2week") & (v7_b2k["hypothesis_id"] == "H_A18_1")]["estimate"].iloc[0])
    dec_cl = v7_dec[v7_dec["panel"] == "decade_2018_2023_166clean_closed"].set_index("policy")
    dec_es10_gain = float(v7_db[(v7_db["cluster"] == "decade_origin_x_2week") & (v7_db["policy_a"] == "Safe_EV_Sunk_m0") & (v7_db["metric"] == "es10")]["estimate"].iloc[0])
    dec_cond_es10_gain = float(v7_db[(v7_db["cluster"] == "decade_origin_x_2week") & (v7_db["policy_a"] == "Safe_EV_Sunk_m0") & (v7_db["metric"] == "cond_es10")]["estimate"].iloc[0])
    v7_b5 = pd.read_csv(ROOT / "revision" / "results" / "v7_bootstrap_precision_5000.csv")
    es10_gain_era171 = float(v7_b5[(v7_b5["scheme"] == "171_ERA5_origin_x_2week") & (v7_b5["hypothesis_id"] == "H_A18_1")]["estimate"].iloc[0])

    state_rows_html: List[str] = []
    for st_name in ["Gujarat", "Himachal Pradesh", "Karnataka", "Madhya Pradesh", "Maharashtra", "Uttar Pradesh"]:
        sub = splits_df[(splits_df["slice_type"] == "State") & (splits_df["slice"] == st_name)]
        row_b2 = sub[sub["policy"] == "B2_age_matched"].iloc[0]
        row_safe = sub[sub["policy"] == "Safe_EV_Sunk_m0"].iloc[0]
        row_rt = sub[sub["policy"] == "RT_2F_Min_m0"].iloc[0]
        es10_gain = float(row_safe["es10"]) - float(row_b2["es10"])
        ci_es10 = str(row_safe["diff_vs_B2_es10_ci95"])
        state_rows_html.append(
            f'<tr><td>{st_name}</td>'
            f'<td style="text-align:right">&#8377;{float(row_safe["mean"]):,.2f}</td>'
            f'<td style="text-align:right">&#8377;{float(row_rt["mean"]):,.2f}</td>'
            f'<td style="text-align:right"><strong>+&#8377;{es10_gain:,.2f}</strong> {ci_es10}</td></tr>'
        )
    slide9_state_rows = "\n                  ".join(state_rows_html)

    slides: List[Tuple[str, str, str]] = [
        (
            "Slide 1 of 12 &bull; Thesis Scope &amp; Question",
            "When Online Mandi Prices Mislead: Risk-Aware Triage &amp; Orthogonal Audit",
            f"""
            <div class="grid2">
              <div class="card accent">
                <h3>The Operational Illusion (Zero-Lookahead `171` Mkts)</h3>
                <p>Portals such as AGMARKNET display neighbouring wholesale spreads above <strong>&#8377;100/qtl</strong>. Chasing raw lagged spreads across <code>57,634</code> test episodes (<code>B1_lagged_screen</code>) loses money on <strong>45.07%</strong> of dispatches (<code>ES10 &#8722;&#8377;642.15/qtl</code>).</p>
                <p><strong>Role (`PhoneCall_TopK_Open`):</strong> <code>MandiGuard</code> acts as a <strong>6 a.m. call-priority filter</strong> ahead of a 30-second confirmation call to a destination <em>arhtiya</em> &mdash; prioritizing calls, never replacing live verification.</p>
              </div>
              <div class="card">
                <h3>Zero-Data Cold-Start + Full-Season ML Frontier</h3>
                <div class="kpi-row">
                  <div class="kpi"><div class="val">9 Choices</div><div class="lbl">0 tuned weights; 17m Mean-Q10 edges Mean/tail without safe_ev_feat</div></div>
                  <div class="kpi"><div class="val">166 Mkts</div><div class="lbl">Clean 2018&ndash;2023 (N=383,952): +&#8377;{dec_es10_gain:,.2f} ES10 | +&#8377;{dec_cond_es10_gain:,.2f} cond_ES10</div></div>
                </div>
                <div class="kpi-row">
                  <div class="kpi good"><div class="val">+&#8377;{es10_gain_171:,.2f}/qtl</div><div class="lbl">Safe_EV_Sunk_m0 ES10 vs B2 (+&#8377;180.89 cond_ES10; p_holm=0.0040)</div></div>
                  <div class="kpi"><div class="val">&#8377;{float(v7_main.loc['RT_2F_Min_m0','mean']):,.2f}/qtl</div><div class="lbl">RT_2F_Min_m0 Mean (+&#8377;44.36 vs B2; fails cond_ES10 under t&minus;2)</div></div>
                </div>
              </div>
            </div>
            """,
        ),
        (
            "Slide 2 of 12 &bull; Tracked Data &amp; Reconciled Funnel",
            "100% Tracked Offline Data &amp; Geocode Collision Audit",
            """
            <div class="grid2">
              <div class="card">
                <h3>Pipeline Stage Counts (`171`-Mkt Primary &amp; `166`-Mkt `2018&ndash;2023`)</h3>
                <table><thead><tr><th>Pipeline Stage</th><th style="text-align:right">171-Mkt (`2024`)</th><th style="text-align:right">Clean 166-Mkt (`2018&ndash;2023`)</th></tr></thead><tbody>
                  <tr><td>Raw daily portal records</td><td style="text-align:right">257,576</td><td style="text-align:right">616,205 (legacy 173: 623,363)</td></tr>
                  <tr><td>Dropped (`Modal&lt;Min` or `&gt;Max`)</td><td style="text-align:right">759</td><td style="text-align:right">40</td></tr>
                  <tr><td>Raw-key dedup / canonical rows</td><td style="text-align:right">254,533 / 245,838</td><td style="text-align:right">616,165 / 614,973</td></tr>
                  <tr><td>Prior-origin (`<= t-1`), OSRM, `spread > 100`</td><td style="text-align:right">93,504 eps</td><td style="text-align:right">383,952 eps</td></tr>
                  <tr><td><strong>Val (`2025-01..05`) / Eval Episodes</strong></td><td style="text-align:right"><strong>35,870 / 57,634</strong></td><td style="text-align:right"><strong>0 / 383,952</strong></td></tr>
                  <tr><td><em>Unconditional / `2017`-active `115` mkt</em></td><td style="text-align:right"><strong>86,054 test</strong></td><td style="text-align:right"><strong>325,993 eps</strong></td></tr>
                  <tr><td><em>HP Graded Apples (`42` yards)</em></td><td style="text-align:right" colspan="2">4,427 raw &rarr; <strong>2,802 test eps</strong> (`val_171` thresholds)</td></tr>
                </tbody></table>
              </div>
              <div class="card accent">
                <h3>Tracked Benchmarks &amp; Forensic Geocodes</h3>
                <ul>
                  <li><strong>AGMARKNET (`171` Strict `2024` Mkts):</strong> `>= 80`d in `2024`, `<= 30`/state (`99.42%` [`171/172`] XML parity; reverse-survivorship on `2018&ndash;2023`).</li>
                  <li><strong>OSRM Matrix (`8,147` corridors):</strong> Legacy `59.50%` exact drops to `35.23%` (`6,605` non-collided eps) across `56` collided markets (`clean_market_query` fixed).</li>
                  <li><strong>Stylized APMC Tiers (PIB 154554):</strong> Buyer-paid statutory fees &amp; UP omitted; `0.5&ndash;1.5%` are stylized friction tiers.</li>
                  <li><strong>NABCONS Decay &amp; Weather:</strong> Cumulative shares scaled 24h alongside USDA Sched #7; `<= t-1` weather-free (`100%` ERA5 at settlement).</li>
                </ul>
              </div>
            </div>
            """,
        ),
        (
            "Slide 3 of 12 &bull; Timing Firewall (`R3`)",
            "Strict `<= t - 1` Information Firewall &amp; Weather Leak Removal",
            """
            <div class="grid2">
              <div class="card accent">
                <h3>What Was Audited and Removed (`N1`, `C1`)</h3>
                <ul>
                  <li><strong>Removed Day-t Price/Shortlist Leak (`C1`):</strong> Legacy shortlists leaked same-day prices. Replaced end-to-end from raw parquets (`dest_quote_date &lt; t`, `origin_quote_date &lt; t` across `317,985` shortlisted rows).</li>
                  <li><strong>Removed `98.64%` ERA5 Weather Leak (`N1`):</strong> Auditing `67,135` rows showed `fc_rain_mm == era5_rain_mm` on `66,222` rows (`99.93%` RH within `1%`).</li>
                  <li><strong>Weather-Free Decisions + Realized ERA5 Check:</strong> Primary `20°C` reference requires zero weather telemetry; `100.0%` arrival ERA5 runs strictly inside settlement.</li>
                </ul>
              </div>
              <div class="card">
                <h3>Counterfactual Corruption Proof (`pytest`)</h3>
                <p><code>tests/test_timing_and_leakage_r3.py</code> mutates <strong>all portal records on days &ge; t*</strong>:</p>
                <ul>
                  <li>Inserts <code>&#8377;99,999/qtl</code> spikes at excluded yards on day <code>t*</code>;</li>
                  <li>Halves origin day-<code>t*</code> modal prices;</li>
                  <li>Deletes active candidate yards on day <code>t*</code>.</li>
                </ul>
                <p class="pill-ok">Result: Bit-for-bit equality verified on candidate menu &amp; every decision feature for t &le; t*.</p>
              </div>
            </div>
            """,
        ),
        (
            "Slide 4 of 12 &bull; Physical Settlement &amp; Costs",
            "Destination-Base APMC Fees (`M9`) &amp; Sequential Settlement (`A4`)",
            """
            <div class="grid2">
              <div class="card">
                <h3>Physical Cost &amp; Decay Model</h3>
                <div class="eq-s">F<sub>road</sub> = 35.0 + 0.45 &times; h<sub>s</sub> &times; road_km &nbsp;&nbsp;(h<sub>s</sub> = 1.45 in HP, 1.0 elsewhere)</div>
                <div class="eq-s">s(k, w) = min(0.55, b<sub>k</sub> &times; max(1, hours + 24w) / 24) &nbsp;&nbsp;[0.86%&ndash;3.25% / 24h]</div>
                <p>Stylized fee tier `0.5%&ndash;1.5%` applies strictly to <strong>post-decay destination sale revenue</strong> (`0%` intra-district or on unsold return).</p>
                <p><strong>Day-by-Day Non-Anticipative Settlement (`tau = 1..3d`):</strong> Sell if exact variety prints on arrival day `w`; wait `1d` (`&#8377;25/qtl` detention) only if another variety trades; else turn back (`-div*F - loc*sp`).</p>
              </div>
              <div class="card accent">
                <h3>Why Sequential Settlement Matters (`B1`, `N = 57,634`)</h3>
                <table><thead><tr><th>B1_lagged_screen Outcomes (`57,634`)</th><th style="text-align:right">Trips</th><th style="text-align:right">Share</th></tr></thead><tbody>
                  <tr><td>Exact variety sells on arrival day `w = 0`</td><td style="text-align:right">40,217</td><td style="text-align:right">69.78%</td></tr>
                  <tr><td>Waits `w = 1..2` &amp; sells exact variety</td><td style="text-align:right">284</td><td style="text-align:right">0.49%</td></tr>
                  <tr><td>Day-2 cross-variety fallback (`0.90*min`)</td><td style="text-align:right">609</td><td style="text-align:right">1.06%</td></tr>
                  <tr><td><strong>No-commodity return (`w = 0..2`)</strong></td><td style="text-align:right"><strong>16,524</strong></td><td style="text-align:right"><strong>28.67%</strong></td></tr>
                </tbody></table>
                <p><strong>Honest Hindsight Check:</strong> 3-day hindsight drops `B1` losses `45.07% &rarr; 31.27%` (`&#8377;384.61 &rarr; &#8377;523.68`) and gives `B2` higher Mean (`&#8377;549.81` vs `Safe_EV &#8377;533.14`), while `Safe_EV` cuts `ES10` `&#8722;&#8377;588.34 &rarr; &#8722;&#8377;279.93`.</p>
              </div>
            </div>
            """,
        ),
        (
            "Slide 5 of 12 &bull; Honest ML/CQR &amp; Orthogonal Audit",
            "Orthogonal `cv28`/`p_dow` Split &amp; Full-Season `17m` ML/CQR Frontier",
            """
            <div class="grid2">
              <div class="card">
                <h3>Why `5m` ML &amp; Homoscedastic CQR Misled</h3>
                <ul>
                  <li><strong>`5m` Off-Season Starvation &amp; Quadratic OR:</strong> Training on Jan&ndash;May alone leaves `Ridge` (`&#8722;&#8377;542.58`) / `HGBR EV` (`&#8722;&#8377;543.57`) &amp; squared-INR `OR_Vargas` (`&#8722;&#8377;511.42`) noisy; heteroscedastic Split-CQR (`s80=0.53`, `8,848` switches) cuts `cond_ES10` to `&#8722;&#8377;414.44` (`356.78` Mean).</li>
                  <li><strong>Full `17m` Cycle (`n=113,374`):</strong> `ML_17m_MeanQ10` hits `&#8377;455.83` (`cond_ES10 &#8722;&#8377;420.57`), and `NoSafeEV` keeps `&#8377;458.27` (`&#8722;&#8377;423.88`) &mdash; GBDTs learn the interaction autonomously (`CQR80` `&#8722;&#8377;367.09` at `&#8377;364.03`).</li>
                </ul>
              </div>
              <div class="card accent">
                <h3>Orthogonal Decomposition &amp; Cold-Start Role</h3>
                <ul>
                  <li><strong>`cv28` vs `p_dow` (`2x2`, `v7_exp4`):</strong> `Ortho_Pure_cv28_only` (`71.91%`) hits `cond_ES10 &#8722;&#8377;447.13` (~all tail truncation); `Ortho_Pure_pdow_only` (`84.10%`) hits `&#8377;466.68` / `&#8722;&#8377;607.18` (diversion avoidance).</li>
                  <li><strong>Common Routing (`D_S &cap; D_B`, `n=33,398`):</strong> `+&#8377;65.66` Mean &amp; `+&#8377;53.40` `ES10` inside shared trips (`B2`-only `58.60%` loss).</li>
                  <li><strong>Cold-Start Niche:</strong> `Safe_EV_Sunk_m0` (`n_train=0`, `9` choices) recovers `&#8377;452.74` Mean / `&#8722;&#8377;447.48` `cond_ES10` (`cv28==0` invariant `&#8722;&#8377;447.65`).</li>
                </ul>
              </div>
            </div>
            """,
        ),
        (
            "Slide 6 of 12 &bull; Two Zero-Tuned-Parameter Rules",
            "Two Tuning-Free Pocket-Calculator Equations (`PREREG_A18.md`)",
            """
            <div class="grid2">
              <div class="card accent">
                <h3>1. `Safe_EV_Sunk_m0` (`9` Fixed Choices, `0` Fitted Weights)</h3>
                <div class="eq-s">p<sub>dow</sub>&middot;G<sub>1SD</sub> &minus; F &equiv; p<sub>dow</sub>(G<sub>1SD</sub> &minus; F) + (1 &minus; p<sub>dow</sub>)(&minus;1.0F) &nbsp; [G<sub>1SD</sub> = P<sub>d</sub>(1&minus;cv<sub>28</sub>)(1&minus;&tau;)&minus;P<sub>o</sub>]</div>
                <div class="eq-big">p<sub>dow</sub> &middot; G<sub>1SD</sub> &minus; F<sub>road</sub> &gt; 0 &nbsp;&hArr;&nbsp; G<sub>1SD</sub> / F<sub>road</sub> &gt; 1 / p<sub>dow</sub></div>
                <p><strong>Worked MP Tomato (`200km`, `F=&#8377;125`, `G_1SD=&#8377;174.50`):</strong></p>
                <ul>
                  <li>Steady Yard A (`p_dow = 0.90`): `0.90 &times; 174.50 &minus; 125 = +&#8377;32.05` &rarr; <strong>DISPATCH</strong></li>
                  <li>Sunday Yard B (`p_dow = 0.20`): `0.20 &times; 174.50 &minus; 125 = &#8722;&#8377;90.10` &rarr; <strong>ABSTAIN</strong> (`arg max` ratio switches `5,113`)</li>
                </ul>
              </div>
              <div class="card">
                <h3>2. `RT_2F_Min_m0` (`0` Params, NO `cv28`) &amp; `ScaleInv_Safe_EV_24tau`</h3>
                <div class="eq-s">G = P<sub>dest</sub>(1 &minus; &tau;<sub>fee</sub>) &minus; P<sub>orig</sub>, &nbsp;&nbsp; p<sub>min</sub> = min(rep<sub>28</sub>, p<sub>dow</sub>)</div>
                <div class="eq-big">p<sub>min</sub> &middot; G &minus; 2 F<sub>road</sub> &gt; 0 &nbsp;&nbsp;(Omits `cv28` &rarr; tail risk stays high)</div>
                <ul>
                  <li>Steady Yard A (`p_min = 0.85`): `+&#8377;149.50`; Sunday B (`0.20`): `&#8722;&#8377;156.00`.</li>
                  <li><strong>Scale Fix (`24&tau;` + `1.5F`):</strong> Prevents high-price collapse (`HP F/G &lt; 0.10` on `79.52%`), cutting `171`-mkt losses to `11.33%` (`cond_ES10 &#8722;&#8377;421.27`).</li>
                </ul>
              </div>
            </div>
            """,
        ),
        (
            "Slide 7 of 12 &bull; Primary `171`-Mkt Results &amp; Finite-Sample CGM `G*`",
            "Primary Benchmark (`N = 57,634`, Exploratory `PREREG_A18` `p_holm_2s = 0.0040`)",
            f"""
            <div class="grid-img">
              <div class="card">
                <table><thead><tr><th>Policy (`171`-Mkt Primary)</th><th style="text-align:right">Disp</th><th style="text-align:right">Mean</th><th style="text-align:right">EpL</th><th style="text-align:right">ES10</th><th style="text-align:right">cond_ES10</th></tr></thead><tbody>
                  <tr><td><code>B1_lagged_screen</code> (`1`)</td><td style="text-align:right">100.0%</td><td style="text-align:right">&#8377;384.61</td><td style="text-align:right">45.07%</td><td style="text-align:right">&#8722;&#8377;642.15</td><td style="text-align:right">&#8722;&#8377;642.15</td></tr>
                  <tr><td><code>B2_age_matched</code> (`1`)</td><td style="text-align:right">71.73%</td><td style="text-align:right">&#8377;419.62</td><td style="text-align:right">26.43%</td><td style="text-align:right">&#8722;&#8377;524.78</td><td style="text-align:right">&#8722;&#8377;628.37</td></tr>
                  <tr><td><code>MG_T1_T2_matched</code> (`4`)</td><td style="text-align:right">69.16%</td><td style="text-align:right">&#8377;454.07</td><td style="text-align:right">18.35%</td><td style="text-align:right">&#8722;&#8377;508.72</td><td style="text-align:right">&#8722;&#8377;638.55</td></tr>
                  <tr><td><code>RR_Abstain_matched</code> (`2`)</td><td style="text-align:right">68.75%</td><td style="text-align:right">&#8377;461.41</td><td style="text-align:right">17.07%</td><td style="text-align:right">&#8722;&#8377;459.46</td><td style="text-align:right">&#8722;&#8377;584.66</td></tr>
                  <tr class="hi"><td><strong><code>Safe_EV_Sunk_m0</code> (`0`)</strong></td><td style="text-align:right"><strong>63.23%</strong></td><td style="text-align:right"><strong>&#8377;452.74</strong></td><td style="text-align:right"><strong>14.88%</strong></td><td style="text-align:right"><strong>&#8722;&#8377;345.53</strong></td><td style="text-align:right"><strong>&#8722;&#8377;447.48</strong></td></tr>
                  <tr class="hl"><td><strong><code>Safe_EV_Phys_m0</code> (`0`)</strong></td><td style="text-align:right">60.84%</td><td style="text-align:right">&#8377;449.52</td><td style="text-align:right"><strong>13.70%</strong></td><td style="text-align:right"><strong>&#8722;&#8377;334.80</strong></td><td style="text-align:right"><strong>&#8722;&#8377;447.33</strong></td></tr>
                  <tr class="hi"><td><strong><code>RT_2F_Min_m0</code> (`0`)</strong></td><td style="text-align:right">64.79%</td><td style="text-align:right"><strong>&#8377;463.98</strong></td><td style="text-align:right">16.21%</td><td style="text-align:right">&#8722;&#8377;464.84</td><td style="text-align:right">&#8722;&#8377;618.35</td></tr>
                </tbody></table>
                <p class="small"><strong>Exploratory `PREREG_A18` (`R = 2,000`):</strong> All 4 pass `p_holm_2s = 0.0040` (`H_A18_1` CGM `p=0.005/0.010`, `p_stud=0.001`; `H_A18_2` `p_cgm=0.049/0.068`, `p_stud=0.012/0.057`, joint `p=0.0030`, `p_wild_webb6_1w=0.0005`). `Safe_EV_Phys` `cond_ES10` leads by only `+&#8377;0.15`.</p>
              </div>
              <div class="img-pane"><img src="{b64_img('rev_fig1_risk_coverage_ci.png')}" alt="Risk Coverage"></div>
            </div>
            """,
        ),
        (
            "Slide 8 of 12 &bull; Fair Controls, Non-Collided Geocodes &amp; Reality Stress",
            "Equal Controls, Repaired `S6`, Non-Collided Exact &amp; Outsider LCV (`rev_fig2`)",
            f"""
            <div class="grid-img">
              <div class="card">
                <h3>What Adversarial Checks Prove (`v7_exp1..5`)</h3>
                <ul>
                  <li><strong>Equal Dispatch (`63.23%`):</strong> `B2_test_matched` gives `cond_ES10 &#8722;&#8377;644.95`; `Safe_EV` leads by `+&#8377;197.47`. Under `<= t-2` (`N=57,047`), `Safe_EV` keeps `cond_ES10` (`p=0.001`); `RT_2F` fails (`p=0.981`).</li>
                  <li><strong>Repaired Return-Leg `S6` (`ERA5`):</strong> `Safe_EV` `&#8377;307.39 / &#8722;&#8377;725.73 cond_ES10` vs `B2 &#8377;247.15 / &#8722;&#8377;969.71`; `Stoch_CondMAR_p1.00` `+&#8377;366.85 cond_ES10`.</li>
                  <li><strong>Non-Collided Exact (`N=6,605`, `35.23%`):</strong> `Safe_EV` `ES10 &#8722;&#8377;231.27` vs `&#8722;&#8377;449.14` (`p=0.001`); `Outsider_MinPrice_LCV` `&#8377;102.62` (`34.29%` loss) vs `B2 &#8377;33.86`.</li>
                  <li><strong>SUTVA Crowding (`max=27`):</strong> `10%`/truck drops Mean to `&#8722;&#8377;5.31`; `k &le; 2` preserves `&#8377;207.00` Mean &amp; `&#8722;&#8377;523.12 cond_ES10`.</li>
                </ul>
              </div>
              <div class="img-pane"><img src="{b64_img('rev_fig2_ablations_and_crops.png')}" alt="Fair Ablations and Crops"></div>
            </div>
            """,
        ),
        (
            "Slide 9 of 12 &bull; Subgroup Generalizability (`171` Mkts)",
            "State (`6/6`) &amp; Crop (`5/5`) `ES10` vs Small-Cluster `cond_ES10` Limits",
            f"""
            <div class="grid2">
              <div class="card accent">
                <h3>Percentile `ES10` 95% CIs vs Studentized / `cond_ES10` Checks</h3>
                <table><thead><tr><th>Slice (`171`-Mkt)</th><th style="text-align:right">Safe_EV Mean</th><th style="text-align:right">RT_2F Mean</th><th style="text-align:right">Safe_EV ES10 Gain vs B2 (95% CI)</th></tr></thead><tbody>
                  {slide9_state_rows}
                </tbody></table>
              </div>
              <div class="card">
                <h3>Complete Subgroup Transparency (`v7_splits_171.csv`)</h3>
                <ul>
                  <li><strong>All 5 Crop-Slice `ES10` Wins:</strong> NonApple `+&#8377;134.80`, Onion `+&#8377;121.24`, Potato `+&#8377;70.61`, Tomato `+&#8377;197.24`, Apple `+&#8377;560.81` (`Holm11 &le; 0.039`; Potato `&#8722;&#8377;17.20` vs `RR`).</li>
                  <li><strong>Honest `cond_ES10` &amp; Small-Cluster Limits:</strong> HP (`B=12`, `g*=1.54` warn) is <strong>NS</strong> on `cond_ES10` (`+&#8377;250.82`, `p=0.124`) &amp; `p_stud=0.188` (`p_cgm=0.299`); Apple is borderline (`p_stud=0.059`, `cond_ES10 p=0.055`); UP shows `q10=0` atom (`7.28% < 10%`).</li>
                </ul>
              </div>
            </div>
            """,
        ),
        (
            "Slide 10 of 12 &bull; Sensitivity Tornado &amp; Manski / Negative Mean Bounds",
            "36/36 Tornado, Manski / Open-MAR Reversals, &amp; Exact Break-Even",
            f"""
            <div class="grid-img">
              <div class="card">
                <ul>
                  <li><strong>36 / 36 Tornado Cells (`171` Mkts):</strong> `Safe_EV` wins `36/36` on Mean (`+&#8377;15.03..+&#8377;61.22`), `ES10` (`+&#8377;114.97..+&#8377;263.60`), &amp; `cond_ES10` (`+&#8377;172.97..+&#8377;322.24`).</li>
                  <li><strong>Coupled Manski &amp; Negative Mean Regimes:</strong> `div=0` Mean is NS (`p=0.220&ndash;0.256`); Open-MAR reverses Mean (`B2 +&#8377;97.01`); worst-case Means (`&#8722;&#8377;125..&#8722;&#8377;325`) favor `B2`, yet exact coupled Manski **`cond_ES10`** stays strictly positive on `Supp1` (`[+&#8377;152.20, +&#8377;328.28]`) &amp; `Supp2` (`[+&#8377;105.96, +&#8377;394.89]`, vs decoupled `&#8722;&#8377;0.51`).</li>
                  <li><strong>Break-Even (`171`-Mkt):</strong> `+&#8377;{float(be_20c["breakeven_silent_extra_inr"]):,.2f}` shift (`+&#8377;{float(be_20c["breakeven_silent_abs_payoff_inr"]):,.2f}` flat; `{float(be_20c["breakeven_open_mar_share_pct"]):.2f}%` MAR; thin `29.78%` if thick=0).</li>
                </ul>
              </div>
              <div class="img-pane"><img src="{b64_img('rev_fig3_sensitivity_tornado_and_missing.png')}" alt="Tornado and Missing Bounds"></div>
            </div>
            """,
        ),
        (
            "Slide 11 of 12 &bull; Clean `166`-Mkt `2018&ndash;2023` (`384k`), ERA5 &amp; HP Apples",
            "Clean 6-Year Backtest, NASA POWER, ERA5 (`&#8722;&#8377;31.16` `B1`), &amp; HP Apples",
            f"""
            <div class="grid-img">
              <div class="card">
                <ul>
                  <li><strong>Clean `166`-Mkt `2018&ndash;2023` (`N=383,952`, Reverse-Survivorship `2024` Frame):</strong> `+&#8377;{dec_es10_gain:,.2f} ES10`, `+&#8377;{dec_cond_es10_gain:,.2f} cond_ES10` (`p=0.001`; `NASA × USDA_Sched7` `cond_ES10 &#8722;&#8377;507.15` vs `&#8722;&#8377;693.39`); `2020`/`2023` Means NS (`p=0.208`/`0.077`).</li>
                  <li><strong>Realized ERA5 &amp; `178&rarr;171` Gap:</strong> `Safe_EV` gains `+&#8377;{es10_gain_era171:,.2f} ES10` (break-even `+&#8377;{float(be_era["breakeven_silent_extra_inr"]):,.2f}`); `B1` shifts `&#8722;&#8377;{abs(float(v7_rec.loc['B1_lagged_screen','shift_total_178_20C_to_171_ERA5'])):.2f}` (`&#8722;&#8377;13.26` + `&#8722;&#8377;17.90`).</li>
                  <li><strong>HP Apple Scale Non-Invariance (`N=2,802`):</strong> `F/G &lt; 0.10` (`79.52%`) breaks `cond_ES10` (`p=0.094` NS, `41.38%` loss); `ScaleInv_Safe_EV_24tau` cuts `ep_loss` to `17.92%` (`cond_ES10 &#8722;&#8377;1,616.08`).</li>
                </ul>
              </div>
              <div class="img-pane"><img src="{b64_img('rev_fig4_settlement_and_hp_apple.png')}" alt="2018-2023 Backtest and HP Apples"></div>
            </div>
            """,
        ),
        (
            "Slide 12 of 12 &bull; Cleanroom Verification &amp; Prospective Field Pilot",
            "16-Agent Final Audit Sign-Off &amp; Next Milestone (`Gate J`)",
            """
            <div class="grid2">
              <div class="card accent">
                <h3>Automated Cleanroom &amp; Audit Verification</h3>
                <ul>
                  <li><strong>Independent `A16` Audit &amp; Leakage Tests:</strong> Re-derives rules from raw parquets (`&#8377;0.00` parity), enforces `n_clusters &le; 178`, and passes deterministic rebuild tests (`pytest`).</li>
                  <li><strong>Traceability &amp; Bibliography Parity (`verify_traceability.py`):</strong> `0` untraceable numbers across all `23/23` active markdown documents &amp; `59/59` `(Author, Year)` citation bijection.</li>
                  <li><strong>Supervision &amp; Clean-Clone Rebuild:</strong> Supervised by <strong>Dr. Sonia</strong> (Shoolini University); fresh clone rebuilds all CSVs with `0.0` max abs diff (`PREREG_A10/A18` untouched).</li>
                </ul>
              </div>
              <div class="card">
                <h3>Explicit Boundaries (`PARTIALLY SUPPORTED`) &amp; Next Step</h3>
                <ul>
                  <li>Zero validation-tuned params (`9` fixed choices); strictly 6 a.m. call-priority triage (`PhoneCall_TopK_Open`) before *arhtiya* calls.</li>
                  <li>Stylized buyer-paid vs `0.5&ndash;1.5%` fee tiers, NABCONS cumulative anchors, &amp; `2024`-active OSRM offline corridor frame.</li>
                  <li>Disclosed Mean/tail limits: Manski/Open-MAR reversals, `div=0` &amp; `2020/2023` NS Mean, HP `B=12` / Apple `cond_ES10` NS, SUTVA `max=27` crowding.</li>
                  <li><strong>Gate J (`BLOCKED` prospectively):</strong> Bulk portal stops `2026-04-13`; next step is a 1-season FPO field pilot logging live calls &amp; truck *patti* slips.</li>
                </ul>
              </div>
            </div>
            """,
        ),
    ]

    slides_html = []
    for idx_s, (kicker, heading, inner) in enumerate(slides, 1):
        def _format_slide_fragment(frag: str) -> str:
            held: Dict[str, str] = {}

            def _hold_code(m: re.Match) -> str:
                k = f"@@SLTOK{len(held)}@@"
                held[k] = f"<code>{html.escape(html.unescape(m.group(1)))}</code>"
                return k

            out = re.sub(r"`([^`]+)`", _hold_code, frag)
            out = re.sub(r"\*\*([^\*\n]+?)\*\*", r"<strong>\1</strong>", out)
            out = re.sub(r"(?<!\*)\*([^\*\n<>]+?)\*(?!\*)", r"<em>\1</em>", out)
            for k, v in reversed(list(held.items())):
                out = out.replace(k, v)
            assert "`" not in out and "**" not in out, f"Unrendered markdown leaked in slide {idx_s}"
            return out

        body_clean = _format_slide_fragment(inner)
        heading_clean = _format_slide_fragment(heading)
        kicker_clean = _format_slide_fragment(kicker)
        slides_html.append(
            f"""<section class="slide">
              <header class="s-head"><div class="kicker">{kicker_clean}</div><h1>{heading_clean}</h1></header>
              <main class="s-body">{body_clean}</main>
              <footer class="s-foot"><span>Aditya Sharma (Supervised by Dr. Sonia) &mdash; Shoolini University, Solan, Himachal Pradesh, India &bull; MandiGuard Revision v8</span><span>Slide {idx_s} / 12</span></footer>
            </section>"""
        )

    deck_css = """
@page { size: 13.333in 7.5in; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #0f172a; background: #ffffff; }
.slide {
  width: 13.333in; height: 7.5in;
  padding: 0.42in 0.54in 0.34in 0.54in;
  overflow: hidden;
  page-break-after: always;
  display: flex; flex-direction: column; justify-content: space-between;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 22%);
}
.slide:last-child { page-break-after: auto; }
.s-head { border-bottom: 2.5px solid #0f4c5c; padding-bottom: 7px; margin-bottom: 10px; }
.kicker { font-size: 9.8pt; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #0f4c5c; margin-bottom: 3px; }
h1 { margin: 0; font-size: 19.5pt; line-height: 1.16; color: #0b2538; }
h3 { margin: 0 0 7px 0; font-size: 12.5pt; color: #0f4c5c; }
.s-body { flex: 1; display: flex; flex-direction: column; justify-content: center; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: stretch; }
.grid-img { display: grid; grid-template-columns: 0.94fr 1.06fr; gap: 15px; align-items: center; }
.card { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 13px 15px; font-size: 10.6pt; line-height: 1.38; }
.card.accent { background: #f0f9ff; border-color: #7dd3fc; border-left: 5px solid #0284c7; }
ul { margin: 4px 0; padding-left: 17px; }
li { margin-bottom: 5px; }
code { font-family: Menlo, Consolas, monospace; font-size: 9.4pt; background: #e2e8f0; padding: 1px 4px; border-radius: 3px; }
.kpi-row { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; margin-top: 7px; }
.kpi { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 9px 11px; }
.kpi.good { background: #ecfdf5; border-color: #6ee7b7; }
.kpi .val { font-size: 17pt; font-weight: 800; color: #0f4c5c; }
.kpi .lbl { font-size: 8.8pt; color: #334155; margin-top: 2px; }
.eq-s { background: #ffffff; border: 1px solid #bae6fd; padding: 5.5px 9px; border-radius: 5px; font-weight: 600; margin-bottom: 6px; font-size: 10.6pt; }
.eq-big { background: #0f4c5c; color: #ffffff; padding: 9px 12px; border-radius: 6px; font-weight: 700; font-size: 12.4pt; text-align: center; margin: 7px 0; }
.pill-ok { background: #dcfce7; border: 1px solid #86efac; color: #14532d; padding: 6px 9px; border-radius: 5px; font-weight: 600; margin-top: 9px; font-size: 10pt; }
table { width: 100%; border-collapse: collapse; font-size: 8.8pt; }
th { background: #0f4c5c; color: #ffffff; padding: 4.5px 5px; text-align: left; }
th code { background: rgba(255, 255, 255, 0.18); color: #ffffff; }
td { padding: 4px 5px; border-bottom: 1px solid #e2e8f0; }
td[style*="right"], th[style*="right"] { white-space: nowrap; }
tr.hi, tr.hl { background: #ecfdf5; font-weight: 700; }
.small { font-size: 9.2pt; color: #334155; margin-top: 7px; }
.img-pane img { max-width: 100%; max-height: 5.3in; object-fit: contain; display: block; margin: 0 auto; border: 1px solid #cbd5e1; border-radius: 6px; background: #fff; padding: 4px; }
.s-foot { border-top: 1px solid #cbd5e1; padding-top: 5px; font-size: 8.6pt; color: #64748b; display: flex; justify-content: space-between; }
"""
    deck_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>MandiGuard Viva Defense Slides (Revision v8)</title><style>{deck_css}</style></head>
<body>{''.join(slides_html)}</body></html>"""

    html_out = VIVA_DIR / "MandiGuard_Viva_Defense_Slides.html"
    pdf_out = VIVA_DIR / "MandiGuard_Viva_Defense_Slides.pdf"
    html_out.write_text(deck_html, encoding="utf-8")
    render_pdf(html_out, pdf_out)
    n_pages = len(PdfReader(str(pdf_out)).pages)
    assert n_pages == 12, f"Expected exact 12 slides, got {n_pages} PDF pages!"
    print(f"Built {html_out.name} & {pdf_out.name} ({n_pages} slides verified)")


def main() -> None:
    bib = (PAPER_DIR / "references.bib").read_text()
    bib_keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib))
    bib_map = build_author_year_map(bib)
    build_paper_html_and_pdf(bib_map)
    build_latex_manuscript(bib_keys)
    build_docx_manuscript(bib_map)
    build_easy_reading_html_and_pdf(bib_map)
    build_viva_slides()

    # Final assertion pass over all generated PDFs and DOCX text
    for p in (
        PAPER_DIR / "MandiGuard_Research_Paper.pdf",
        PAPER_DIR / "MandiGuard_Easy_Reading_Edition.pdf",
        VIVA_DIR / "MandiGuard_Viva_Defense_Slides.pdf",
    ):
        txt = "\n".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)
        for bad in FORBIDDEN_LATEX_LEAKS + FORBIDDEN_LEGACY_STRINGS:
            assert bad not in txt, f"Forbidden string `{bad}` found in {p.name}"
    docx_doc = Document(str(PAPER_DIR / "MandiGuard_Research_Paper.docx"))
    docx_txt = "\n".join([p.text for p in docx_doc.paragraphs] + [c.text for t in docx_doc.tables for row in t.rows for c in row.cells])
    for bad in ("[jensen2007digital]", "[baulch1997transfer]", "exploratory: true", "make reproduce", "TO CONFIRM"):
        assert bad not in docx_txt, f"Forbidden string `{bad}` found in MandiGuard_Research_Paper.docx"
    print("ALL Revision v8 core deliverables built & verified cleanly!")


if __name__ == "__main__":
    main()
