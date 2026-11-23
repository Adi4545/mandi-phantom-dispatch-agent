#!/usr/bin/env python3
"""Build Revision v5 publication deliverables from canonical markdown & results:
  1. paper/MandiGuard_Research_Paper.html & .pdf (from paper/manuscript.md)
  2. paper/manuscript.tex (compile-ready LaTeX linking paper/references.bib)
  3. paper/MandiGuard_Research_Paper.docx (Word submission bundle)
  4. paper/MandiGuard_Easy_Reading_Edition.html & .pdf (from 12th_class_easy_reading_edition.md)
  5. viva/MandiGuard_Viva_Defense_Slides.html & .pdf (12-slide 16:9 widescreen deck)

Portable across machines (zero hardcoded home paths); validates output PDFs via pypdf.
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
]


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
        (r"\implies", " &#10233; "),
        (r"\to", " &#8594; "),
        (r"\cdot", "&#183;"),
        (r"\times", "&#215;"),
        (r"\approx", " &#8776; "),
        (r"\le", " &#8804; "),
        (r"\ge", " &#8805; "),
        (r"\ne", " &#8800; "),
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


def format_inline_html(text: str, bib_keys: set[str] | None = None) -> str:
    """Format inline markdown (code, bold, italic, math, links) cleanly to HTML."""
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

    # Style bib citations subtly if bib_keys supplied
    if bib_keys:
        def _cite_repl(m: re.Match) -> str:
            raw = m.group(1)
            parts = [p.strip() for p in raw.split(",")]
            if parts and all(p in bib_keys for p in parts):
                return f'<span class="cite">[{raw}]</span>'
            return m.group(0)
        esc = re.sub(r"\[([a-z0-9_,\s]+)\]", _cite_repl, esc)

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


def markdown_to_html_body(md_text: str, bib_keys: set[str] | None = None, base_dir: Path = PAPER_DIR) -> str:
    """Convert structured Markdown (headings, tables, blockquotes, lists, display math, images) to HTML."""
    lines = md_text.splitlines()
    out: List[str] = []
    i = 0
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
            tbl = ['<div class="tbl-wrap"><table><thead><tr>']
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
                    items.append([re.sub(r"^[-*]\s+", "", s)])
                    i += 1
                elif lines[i].startswith("  ") and s and items:
                    items[-1].append(s)
                    i += 1
                else:
                    break
            cls = ' class="ref-list"' if in_references else ""
            lis = "".join(f"<li>{format_inline_html(' '.join(it), bib_keys)}</li>" for it in items)
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
@page { size: A4; margin: 15mm 15mm 17mm 15mm; }
* { box-sizing: border-box; }
body {
  font-family: "Georgia", "Times New Roman", serif;
  color: #1a202c;
  font-size: 9.7pt;
  line-height: 1.48;
  max-width: 180mm;
  margin: 0 auto;
  background: #ffffff;
}
.title-banner {
  border-bottom: 2.5px solid #0f4c5c;
  padding-bottom: 10px;
  margin-bottom: 14px;
}
.meta-pill {
  display: inline-block;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 7.5pt;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #0f4c5c;
  background: #e6f4f6;
  padding: 2px 8px;
  border-radius: 3px;
  margin-bottom: 6px;
}
h1.doc-title {
  font-size: 16.5pt;
  line-height: 1.22;
  color: #0f293a;
  margin: 4px 0 6px 0;
}
.subline {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 8.3pt;
  color: #475569;
}
h2 {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 11.5pt;
  color: #0f4c5c;
  border-bottom: 1px solid #cbd5e1;
  padding-bottom: 3px;
  margin: 15px 0 7px 0;
  break-after: avoid;
}
h3 {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 10pt;
  color: #1e3a5f;
  margin: 10px 0 5px 0;
  break-after: avoid;
}
p { margin: 0 0 7px 0; text-align: justify; }
ul, ol { margin: 4px 0 8px 0; padding-left: 18px; }
li { margin-bottom: 3.5px; }
hr { border: none; border-top: 1px solid #e2e8f0; margin: 11px 0; }
code {
  font-family: "SFMono-Regular", Menlo, Consolas, monospace;
  font-size: 8.2pt;
  background: #f1f5f9;
  color: #0f172a;
  padding: 1px 3.5px;
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
  padding: 7px 12px;
  margin: 8px 0;
  text-align: center;
  font-size: 10.2pt;
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
.tbl-wrap { margin: 8px 0 11px 0; break-inside: avoid; }
table {
  width: 100%;
  border-collapse: collapse;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 6.9pt;
  line-height: 1.25;
}
th {
  background: #0f4c5c;
  color: #ffffff;
  font-weight: 600;
  padding: 3.2px 3px;
  border-bottom: 1.5px solid #0a3642;
  white-space: normal;
}
td {
  padding: 3px 3px;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: top;
}
td[style*="right"] { white-space: nowrap; }
td:first-child code { font-size: 6.7pt; }
tbody tr:nth-child(even) { background: #f8fafc; }
.worked-box, .note-box {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-left: 4px solid #0284c7;
  border-radius: 4px;
  padding: 8px 11px;
  margin: 8px 0 10px 0;
  font-size: 8.9pt;
  break-inside: avoid;
}
.worked-box p:last-child, .worked-box ol:last-child, .worked-box ul:last-child { margin-bottom: 0; }
figure.fig-card {
  margin: 10px 0 12px 0;
  padding: 6px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: #ffffff;
  break-inside: avoid;
  text-align: center;
}
figure.fig-card img { max-width: 100%; height: auto; display: block; margin: 0 auto 5px auto; }
figure.fig-card figcaption {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 7.9pt;
  color: #334155;
  text-align: left;
  line-height: 1.35;
}
.cite { color: #0f4c5c; font-size: 9pt; }
ul.ref-list { font-size: 8.2pt; line-height: 1.38; padding-left: 16px; }
ul.ref-list li { margin-bottom: 2.5px; }
"""


def _split_manuscript_header(lines: List[str]) -> Tuple[str, str, List[str]]:
    """Return (title, author_line, remaining_body_lines) without duplicating the author line."""
    title_line = lines[0].lstrip("# ").strip()
    author_line = "Aditya Sharma — Shoolini University, Solan, Himachal Pradesh, India"
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


def build_paper_html_and_pdf(bib_keys: set[str]) -> None:
    ms_text = (PAPER_DIR / "manuscript.md").read_text()
    title_line, author_line, body_lines = _split_manuscript_header(ms_text.splitlines())
    body_html = markdown_to_html_body("\n".join(body_lines), bib_keys=bib_keys, base_dir=PAPER_DIR)

    doc_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(title_line)}</title>
<style>{PAPER_CSS}
.author-line {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 9.2pt; font-weight: 600; color: #1e293b; margin: 4px 0 4px 0; }}
</style>
</head>
<body>
<div class="title-banner">
  <span class="meta-pill">M.Tech Research Manuscript &bull; Revision v6 Verified (<code>make reproduce</code>)</span>
  <h1 class="doc-title">{html.escape(title_line)}</h1>
  <div class="author-line">{html.escape(author_line)}</div>
  <div class="subline">Zero-Parameter Wholesale Dispatch Replay &bull; Strictly &lt;= t&minus;1 Firewall &bull; 178 &amp; 171-Market Panels &bull; Realized ERA5 Settlement &bull; <code>R = 5,000</code> Cluster Bootstrap (<code>exploratory: true</code>)</div>
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


def build_easy_reading_html_and_pdf(bib_keys: set[str]) -> None:
    ez_text = (PAPER_DIR / "12th_class_easy_reading_edition.md").read_text()
    # Append 2 key visual figures so the standalone PDF is visually complete
    ez_text += (
        "\n\n---\n\n## 5. Visual Summary Charts\n\n"
        "![Risk-coverage curves and zero-parameter tail savings (Safe_EV_Sunk_m0 & RT_2F_Min_m0)](../figures/rev_fig1_risk_coverage_ci.png)\n\n"
        "![Fair controls and crop/state breakdown across Onion, Potato, Tomato, NonApple, and Apple](../figures/rev_fig2_ablations_and_crops.png)\n"
    )
    lines = ez_text.splitlines()
    title_line = lines[0].lstrip("# ").strip()
    body_html = markdown_to_html_body("\n".join(lines[1:]), bib_keys=bib_keys, base_dir=PAPER_DIR)

    ez_css = PAPER_CSS + """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 9.8pt; }
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
  <span class="meta-pill">Plain-English Pocket-Calculator Edition &bull; Revision v6 Verified</span>
  <h1 class="doc-title">{html.escape(title_line)}</h1>
  <div class="subline">Aditya Sharma &mdash; Shoolini University, Solan, Himachal Pradesh, India &bull; 12th-Class Pocket-Calculator Guide to Zero-Parameter <code>Safe_EV_Sunk_m0</code> &amp; Class-8 <code>RT_2F_Min_m0</code> (<code>4.3 &rarr; 1.2 / 5</code> Difficulty)</div>
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
    """Escape plain LaTeX text (outside math & code)."""
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
    s = s.replace("°", r"$^\circ$").replace("×", r"$\times$").replace("->", r"$\to$")
    return s


def _format_inline_tex(text: str, bib_keys: set[str]) -> str:
    tokens: Dict[str, str] = {}

    def hold(val: str) -> str:
        k = f"TEXHOLD{len(tokens)}X"
        tokens[k] = val
        return k

    # Code spans
    text = re.sub(r"`([^`]+)`", lambda m: hold(r"\texttt{" + _tex_escape_plain(m.group(1)) + "}"), text)
    # Inline math spans (replace ₹ cleanly inside math)
    def _math_fix(m: re.Match) -> str:
        inner = m.group(1).replace("₹", r"\text{Rs.\,}").replace("−", "-")
        return hold("$" + inner + "$")

    text = re.sub(r"\$([^$\n]+?)\$", _math_fix, text)
    # Citations [k1, k2] where every item is in bib_keys
    def _cite_fix(m: re.Match) -> str:
        parts = [p.strip() for p in m.group(1).split(",")]
        if parts and all(p in bib_keys for p in parts):
            return hold(r"\cite{" + ",".join(parts) + "}")
        return m.group(0)

    text = re.sub(r"\[([a-z0-9_,\s]+)\]", _cite_fix, text)
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
            descriptive_caps = {
                1: "Epistemic classification of observed quantities, causal features, survey-anchored assumptions, bounded unobservables, and out-of-scope mechanisms.",
                2: "Reconciled data cleaning funnel from raw official portal archives to Top-5 lagged evaluation episodes across the 6-state and HP graded-apple panels.",
                3: "Main equal-menu lagged test benchmark comparing baselines, hard-gated heuristics, tuned RR-Abstain, and zero-parameter rules (N = 58,676, 20°C closed-yard settlement).",
                4: "Paired two-way cluster bootstrap inference across three State-prefixed spatial clusterings (R = 5,000, two-sided Holm-Bonferroni p_holm_2s).",
                5: "Fair feature, volatility-haircut, Euclidean-distance, and equal-test-dispatch control ablations against Safe_EV_Sunk_m0.",
                6: "Missing-quote counterfactual identification bounds from harsh diversion (div = 2.0) to optimistic open-yard MAR settlement.",
                7: "Revision v6 robustness panels comparing full 178-market and freshly rebuilt strict 2024-only 171-market panels under 20°C reference and realized ERA5 arrival-day weather, with exact silent-market break-even thresholds.",
            }
            cap_text = _tex_escape_plain(descriptive_caps.get(tbl_counter, f"{re.sub(r'[`*]', '', hdr[0])} summary table."))
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
        "\\author{Aditya Sharma \\\\ Shoolini University, Solan, Himachal Pradesh, India}\n"
        "\\date{Revision v6 --- Cleanroom Reproducible Exploratory Audit}\n"
        "\\begin{document}\n\\maketitle\n\n"
        + "\n".join(blocks)
        + "\n\\bibliographystyle{plainnat}\n\\bibliography{references}\n\\end{document}\n"
    )
    # Verify every \cite key & \includegraphics path
    for cg in re.findall(r"\\cite\{([^\}]+)\}", tex):
        for k in [p.strip() for p in cg.split(",")]:
            assert k in bib_keys, f"Unknown LaTeX cite key: {k}"
    for ig in re.findall(r"\\includegraphics\[[^\]]+\]\{([^\}]+)\}", tex):
        assert (PAPER_DIR / ig).resolve().exists(), f"Missing LaTeX graphic: {ig}"

    out_tex = PAPER_DIR / "manuscript.tex"
    out_tex.write_text(tex, encoding="utf-8")
    print(f"Built {out_tex.name} ({len(lines)} md lines -> {len(tex.splitlines())} tex lines)")


def _add_inline_docx_runs(p, text: str) -> None:
    """Format inline bold, italic, code, and math spans cleanly into python-docx runs."""
    tokens: Dict[str, Tuple[str, str]] = {}

    def hold(kind: str, val: str) -> str:
        k = f"\x00D{len(tokens)}\x00"
        tokens[k] = (kind, val)
        return k

    text = re.sub(r"`([^`]+)`", lambda m: hold("code", m.group(1)), text)
    text = re.sub(r"\$([^$\n]+?)\$", lambda m: hold("math", latex_to_plain_unicode(m.group(1))), text)
    text = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", lambda m: m.group(1), text)
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


def build_docx_manuscript() -> None:
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
    sub = doc.add_paragraph("M.Tech Research Paper • Revision v6 Verified (Zero-Parameter Safe_EV_Sunk_m0, Safe_EV_Phys_m0 & RT_2F_Min_m0 • make reproduce)")
    sub.runs[0].italic = True
    sub.runs[0].font.color.rgb = RGBColor(0x0F, 0x4C, 0x5C)

    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s or s == "---" or s in ("<!-- WORKED_EXAMPLE_START -->", "<!-- WORKED_EXAMPLE_END -->"):
            i += 1
            continue
        hm2 = re.match(r"^##\s+(.*)$", s)
        if hm2:
            hp = doc.add_heading("", level=1)
            _add_inline_docx_runs(hp, hm2.group(1).replace("->", "→"))
            i += 1
            continue
        hm3 = re.match(r"^###\s+(.*)$", s)
        if hm3:
            hp = doc.add_heading("", level=2)
            _add_inline_docx_runs(hp, hm3.group(1).replace("->", "→"))
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
                    _add_inline_docx_runs(pb, bl.strip())
            continue
        if s.startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|") and "---" in lines[i + 1]:
            hdr = _split_md_table_row(s)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_split_md_table_row(lines[i]))
                i += 1
            tbl = doc.add_table(rows=1 + len(rows), cols=len(hdr))
            tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            tbl.style = "Table Grid"
            for ci, hv in enumerate(hdr):
                cell = tbl.rows[0].cells[ci]
                cell.text = ""
                p_c = cell.paragraphs[0]
                run = p_c.add_run(re.sub(r"[`*]", "", latex_to_plain_unicode(hv) if "$" in hv else hv))
                run.bold = True
                run.font.size = Pt(8)
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="0F4C5C"/>')
                cell._tc.get_or_add_tcPr().append(shading)
            for ri, rv in enumerate(rows, 1):
                for ci in range(len(hdr)):
                    val = rv[ci] if ci < len(rv) else ""
                    val_clean = re.sub(r"\$([^$]+)\$", lambda m: latex_to_plain_unicode(m.group(1)), val)
                    val_clean = re.sub(r"[`*]", "", val_clean)
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
                _add_inline_docx_runs(pl, " ".join(it))
            continue
        if re.match(r"^[-*]\s+", s):
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                pl = doc.add_paragraph(style="List Bullet")
                _add_inline_docx_runs(pl, re.sub(r"^[-*]\s+", "", lines[i].strip()))
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
        _add_inline_docx_runs(pp, " ".join(para))

    out_docx = PAPER_DIR / "MandiGuard_Research_Paper.docx"
    doc.save(str(out_docx))
    print(f"Built {out_docx.name} ({out_docx.stat().st_size / 1024:.1f} KB)")


def build_viva_slides() -> None:
    """Build exact 12-slide 16:9 widescreen PDF matching final/SLIDE_OUTLINE.md & Revision v6."""
    splits_df = pd.read_csv(ROOT / "revision" / "results" / "a18_crop_and_state_splits.csv")
    v6_b5 = pd.read_csv(ROOT / "revision" / "results" / "v6_bootstrap_5000.csv")
    v6_be = pd.read_csv(ROOT / "revision" / "results" / "v6_breakeven.csv")
    be_20c = v6_be[(v6_be["panel"] == "full_178_20C_closed") & (v6_be["policy_a"] == "Safe_EV_Sunk_m0") & (v6_be["policy_b"] == "B2_age_matched")].iloc[0]
    be_era = v6_be[(v6_be["panel"] == "strict2024_171_ERA5_closed") & (v6_be["policy_a"] == "Safe_EV_Sunk_m0") & (v6_be["policy_b"] == "B2_age_matched")].iloc[0]
    es10_gain_era178 = float(v6_b5[(v6_b5["family"] == "full_178_ERA5_closed") & (v6_b5["scheme"] == "origin_x_2week") & (v6_b5["hypothesis_id"] == "H_V6_1")]["estimate"].iloc[0])
    es10_gain_era171 = float(v6_b5[(v6_b5["family"] == "strict2024_171_ERA5_closed") & (v6_b5["scheme"] == "origin_x_2week") & (v6_b5["hypothesis_id"] == "H_V6_1")]["estimate"].iloc[0])

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
            "Slide 1 of 12 &bull; Thesis Scope & Question",
            "When Online Mandi Prices Mislead: Zero-Parameter Dispatch Filtering",
            f"""
            <div class="grid2">
              <div class="card accent">
                <h3>The Operational Illusion</h3>
                <p>Portals such as AGMARKNET display neighbouring wholesale spreads above <strong>&#8377;100/qtl</strong>. Chasing raw lagged spreads across <code>58,676</code> test episodes (<code>B1_lagged_screen</code>) loses money on <strong>45.21%</strong> of dispatches (<code>ES10 &#8722;&#8377;641.26/qtl</code>).</p>
                <p><strong>Role (`A17` #10):</strong> <code>MandiGuard</code> sits at <strong>6 a.m. upstream portal-alert triage</strong> ahead of a 30-second confirmation call to a destination <em>arhtiya</em> &mdash; cutting noise, not replacing trader verification.</p>
              </div>
              <div class="card">
                <h3>Core Verified Headline (`N = 58,676`, `exploratory: true`)</h3>
                <div class="kpi-row">
                  <div class="kpi"><div class="val">0 Params</div><div class="lbl">No ML pickles, no ERA5 weather, no tuned &kappa;</div></div>
                  <div class="kpi"><div class="val">4.3 &rarr; 1.2 / 5</div><div class="lbl">Defense complexity cut (DIFFICULTY.md)</div></div>
                </div>
                <div class="kpi-row">
                  <div class="kpi good"><div class="val">+&#8377;181.17/qtl</div><div class="lbl">Safe_EV_Sunk_m0 ES10 gain vs B2 (p_holm_2s = 0.0024, R=5k)</div></div>
                  <div class="kpi"><div class="val">&#8377;478.38/qtl</div><div class="lbl">RT_2F_Min_m0 Mean (+&#8377;44.82 vs B2, Class-8 math)</div></div>
                </div>
              </div>
            </div>
            """,
        ),
        (
            "Slide 2 of 12 &bull; Tracked Data & Cleaning Funnel",
            "100% Tracked Official Data & Reconciled Funnel (`A2`)",
            """
            <div class="grid2">
              <div class="card">
                <h3>Pipeline Stage Counts (`cleaning_counts.json`)</h3>
                <table><thead><tr><th>Pipeline Stage</th><th style="text-align:right">6-State Core</th><th style="text-align:right">HP Graded Apple</th></tr></thead><tbody>
                  <tr><td>Raw daily portal records</td><td style="text-align:right">260,043</td><td style="text-align:right">4,427</td></tr>
                  <tr><td>Dropped out-of-range (`Modal&lt;Min` or `&gt;Max`)</td><td style="text-align:right">759</td><td style="text-align:right">0</td></tr>
                  <tr><td>Valid cleaned records retained</td><td style="text-align:right">259,284</td><td style="text-align:right">4,427</td></tr>
                  <tr><td>Raw 7-column key deduplication (`median`/`min`)</td><td style="text-align:right">256,997</td><td style="text-align:right">4,427</td></tr>
                  <tr><td>Canonical `(State, Market, Comm, VarKey, Date)`</td><td style="text-align:right">248,302</td><td style="text-align:right">4,427</td></tr>
                  <tr><td>Prior-origin (`<= t-1`), OSRM 15&ndash;500km, `spread > 100`</td><td style="text-align:right">95,074 eps</td><td style="text-align:right">2,802 eps</td></tr>
                  <tr><td><strong>Val (2025-01..05) / Test (2025-06..2026-04)</strong></td><td style="text-align:right"><strong>36,398 / 58,676</strong></td><td style="text-align:right"><strong>0 / 2,802</strong></td></tr>
                  <tr><td><em>Unconditional origin panel (restoring missing d0)</em></td><td style="text-align:right"><strong>88,014 test</strong></td><td style="text-align:right">&mdash;</td></tr>
                </tbody></table>
              </div>
              <div class="card accent">
                <h3>Six Primary Tracked Benchmarks</h3>
                <ul>
                  <li><strong>AGMARKNET Core (`178` markets):</strong> Onion, Potato, Tomato, Apple across 6 states (`2024-01..2026-04-13`).</li>
                  <li><strong>HP Graded Apples (`42` yards):</strong> `4,427` explicit commercial grade rows (`2025-11..2026-09-01`).</li>
                  <li><strong>OSRM Matrix (`8,147` corridors):</strong> `15.19&ndash;499.43 km` (`150` exact geocodes, `70` centroids; `58.29%` exact test coverage).</li>
                  <li><strong>Govt Benchmarks:</strong> APMC fees (PIB 154554: `0.5&ndash;1.5%`, `0` intra-district/divert), NABCONS 24h decay (PIB 2151371), NITI freight floor (`&#8377;0.258/qtl-km`), GoHP single-lane hill roads (`91.59%`, `1.45x`), RBI *arhtiya* ranges.</li>
                </ul>
              </div>
            </div>
            """,
        ),
        (
            "Slide 3 of 12 &bull; Timing Firewall (`R3`)",
            "Strict `<= t - 1` Information Firewall & Weather Leak Removal",
            """
            <div class="grid2">
              <div class="card accent">
                <h3>What Was Audited and Removed (`N1`, `C1`)</h3>
                <ul>
                  <li><strong>Removed Day-t Price/Shortlist Leak (`C1`):</strong> Legacy `candidates_6state.parquet` built shortlists with same-day origin/dest prices. Replaced end-to-end from raw parquets (`dest_quote_date &lt; t`, `origin_quote_date &lt; t` verified across `324,992` candidate rows).</li>
                  <li><strong>Removed `98.64%` ERA5 Weather Leak (`N1`):</strong> Auditing `67,135` rows (`2025-01..2026-04`) showed `fc_rain_mm == era5_rain_mm` on `66,222` rows (`99.93%` RH within `1%`).</li>
                  <li><strong>Primary `20°C` NABCONS Reference:</strong> Zero weather telemetry needed (`2024` climatology shifts Safe_EV mean by only `&#8722;&#8377;2.93/qtl`).</li>
                </ul>
              </div>
              <div class="card">
                <h3>Property-Test Proof (`pytest`)</h3>
                <p><code>tests/test_timing_and_leakage_r3.py</code> mutates <strong>all portal records on days &ge; t*</strong>:</p>
                <ul>
                  <li>Inserts <code>&#8377;99,999/qtl</code> spikes at excluded yards on day <code>t*</code>;</li>
                  <li>Halves origin day-<code>t*</code> modal prices;</li>
                  <li>Deletes active candidate yards on day <code>t*</code>.</li>
                </ul>
                <p class="pill-ok">Result: Bit-for-bit equality verified on candidate menu &amp; every decision feature for t &le; t* (`36/36` pytest green).</p>
              </div>
            </div>
            """,
        ),
        (
            "Slide 4 of 12 &bull; Physical Settlement & Costs",
            "Destination-Base APMC Fees (`M9`) & Sequential Settlement (`A4`)",
            """
            <div class="grid2">
              <div class="card">
                <h3>Physical Cost & Decay Model</h3>
                <div class="eq-s">F<sub>road</sub> = 35.0 + 0.45 &times; h<sub>s</sub> &times; road_km &nbsp;&nbsp;(h<sub>s</sub> = 1.45 in HP, 1.0 elsewhere)</div>
                <div class="eq-s">s(k, w) = min(0.55, b<sub>k</sub> &times; max(1, hours + 24w) / 24) &nbsp;&nbsp;[0.86%&ndash;3.25% / 24h]</div>
                <p>Statutory fee `0.5%&ndash;1.5%` applies strictly to <strong>post-spoilage destination sale revenue</strong> (`0%` intra-district or on unsold return).</p>
                <p><strong>Day-by-Day Non-Anticipative Settlement (`tau = 1..3d`):</strong> Sell if exact variety prints on arrival day `w`; wait `1d` (`&#8377;25/qtl` detention) only if another variety trades; otherwise turn back (`-div*F - loc*sp`).</p>
              </div>
              <div class="card accent">
                <h3>Why Sequential Settlement Matters</h3>
                <table><thead><tr><th>B1_lagged_screen Outcomes (`58,676`)</th><th style="text-align:right">Trips</th><th style="text-align:right">Share</th></tr></thead><tbody>
                  <tr><td>Exact variety sells on arrival day `w = 0`</td><td style="text-align:right">40,765</td><td style="text-align:right">69.47%</td></tr>
                  <tr><td>Waits `w = 1..2` &amp; sells exact variety</td><td style="text-align:right">288</td><td style="text-align:right">0.49%</td></tr>
                  <tr><td>Day-2 cross-variety fallback (`0.90*min`)</td><td style="text-align:right">618</td><td style="text-align:right">1.05%</td></tr>
                  <tr><td><strong>No-commodity return (`w = 0..2`)</strong></td><td style="text-align:right"><strong>17,005</strong></td><td style="text-align:right"><strong>28.98%</strong></td></tr>
                </tbody></table>
                <p>Scoring identical `B1` trips with <strong>3-day hindsight lookahead</strong> masks loss rate from <strong>45.21% &rarr; 31.35%</strong> (`&#8377;397.87 &rarr; &#8377;538.96`).</p>
              </div>
            </div>
            """,
        ),
        (
            "Slide 5 of 12 &bull; Why Complexity Was Removed",
            "Evolution Across Audits: `4.3 / 5` &rarr; `1.6 / 5` &rarr; `1.2 / 5` Difficulty",
            """
            <div class="grid2">
              <div class="card">
                <h3>What Previous Methods Got Wrong</h3>
                <ul>
                  <li><strong>Stage I GBDT + Conformal (`4.3/5`):</strong> Required `sklearn 1.3.0` pickle + ERA5 leaks; confirmatory `H2` stayed inconclusive (`+&#8377;6.13`, `p = 0.2699`).</li>
                  <li><strong>Hard-Gated `MG_matched` (`4` params):</strong> Lifted mean slightly yet <strong>failed `ES10` tail risk (`&#8722;&#8377;512.78` vs `&#8722;&#8377;525.25`, `p_holm_2s = 1.000`)</strong>.</li>
                  <li><strong>Tuned `RR_Abstain_matched` (`A10`, `1.6/5`):</strong> `val` hit grid edge `kappa* = 5.0` (at `k=20`, matched threshold shifted to `&#8722;&#8377;328.99`); `0.5*rep28 + 0.5*dow8` masked Sunday holiday closures; ignored `cv28`; fell to NS at `div=0` (`p_2s = 0.603`).</li>
                </ul>
              </div>
              <div class="card accent">
                <h3>Zero-Parameter Simplification (`A18`)</h3>
                <ul>
                  <li>Removed `kappa` grid search (`0` tuned parameters).</li>
                  <li>Removed polluted `rep28` Sunday bias inside `p_dow`.</li>
                  <li>Replaced deterministic `G` with 1-SD safe spread `G_1SD` (only `0.23%` fallback).</li>
                  <li>Stripped Q10 biology parameters from 6 a.m. formulas (`+&#8377;0.44` noise).</li>
                  <li>Added Class-8 `RT_2F_Min_m0` requiring zero volatility input.</li>
                </ul>
              </div>
            </div>
            """,
        ),
        (
            "Slide 6 of 12 &bull; The Two Zero-Parameter Rules",
            "Two Zero-Parameter Pocket-Calculator Equations (`PREREG_A18.md`)",
            """
            <div class="grid2">
              <div class="card accent">
                <h3>1. `Safe_EV_Sunk_m0` (Scientific &amp; `ES10` Champion, `0` Params)</h3>
                <div class="eq-s">G<sub>1SD</sub> = P<sub>dest</sub>(1 &minus; cv<sub>28</sub>)(1 &minus; &tau;<sub>fee</sub>) &minus; P<sub>orig</sub></div>
                <div class="eq-big">p<sub>dow</sub> &middot; G<sub>1SD</sub> &minus; F<sub>road</sub> &gt; 0 &nbsp;&hArr;&nbsp; G<sub>1SD</sub> / F<sub>road</sub> &gt; 1 / p<sub>dow</sub></div>
                <p><strong>Worked MP Tomato Route (`200km`, `F=&#8377;125`, `G=&#8377;470`, `cv28=0.15` &rarr; `G_1SD=&#8377;174.50`):</strong></p>
                <ul>
                  <li>Steady Yard A (`p_dow = 0.90`): `0.90 &times; 174.50 &minus; 125 = +&#8377;32.05` &rarr; <strong>DISPATCH</strong></li>
                  <li>Sunday-Closed Yard B (`p_dow = 0.20`): `0.20 &times; 174.50 &minus; 125 = &#8722;&#8377;90.10` &rarr; <strong>ABSTAIN</strong></li>
                </ul>
              </div>
              <div class="card">
                <h3>2. `RT_2F_Min_m0` (Class-8 4-Function Calculator, `0` Params)</h3>
                <div class="eq-s">G = P<sub>dest</sub>(1 &minus; &tau;<sub>fee</sub>) &minus; P<sub>orig</sub>, &nbsp;&nbsp; p<sub>min</sub> = min(rep<sub>28</sub>, p<sub>dow</sub>)</div>
                <div class="eq-big">p<sub>min</sub> &middot; G &minus; 2 F<sub>road</sub> &gt; 0 &nbsp;&hArr;&nbsp; G / (2 F<sub>road</sub>) &gt; 1 / p<sub>min</sub></div>
                <p><strong>No `cv28` volatility and no NABCONS decay needed!</strong></p>
                <ul>
                  <li>Steady Yard A (`p_min = 0.85`): `0.85 &times; 470 &minus; 250 = +&#8377;149.50` &rarr; <strong>DISPATCH</strong></li>
                  <li>Sunday Yard B (`p_min = 0.20`): `0.20 &times; 470 &minus; 250 = &#8722;&#8377;156.00` &rarr; <strong>ABSTAIN</strong> (`B2` chased `+&#8377;345`!)</li>
                </ul>
              </div>
            </div>
            """,
        ),
        (
            "Slide 7 of 12 &bull; Main Results & Risk-Coverage",
            "Headline Test Performance (`N = 58,676`, Two-Sided Holm `p_holm_2s`)",
            f"""
            <div class="grid-img">
              <div class="card">
                <table><thead><tr><th>Policy (`lag 1..3` eq.)</th><th style="text-align:right">Param</th><th style="text-align:right">Disp</th><th style="text-align:right">Mean</th><th style="text-align:right">EpLoss</th><th style="text-align:right">ES10</th><th style="text-align:right">LGL</th></tr></thead><tbody>
                  <tr><td><code>B1_lagged_screen</code></td><td style="text-align:right">1</td><td style="text-align:right">100.0%</td><td style="text-align:right">&#8377;397.87</td><td style="text-align:right">45.21%</td><td style="text-align:right">&#8722;&#8377;641.26</td><td style="text-align:right">&#8722;&#8377;271.24</td></tr>
                  <tr><td><code>B2_age_matched</code></td><td style="text-align:right">1</td><td style="text-align:right">72.03%</td><td style="text-align:right">&#8377;433.56</td><td style="text-align:right">26.72%</td><td style="text-align:right">&#8722;&#8377;525.25</td><td style="text-align:right">&#8722;&#8377;293.73</td></tr>
                  <tr><td><code>MG_matched</code></td><td style="text-align:right">4</td><td style="text-align:right">69.51%</td><td style="text-align:right">&#8377;467.90</td><td style="text-align:right">18.57%</td><td style="text-align:right">&#8722;&#8377;512.78</td><td style="text-align:right">&#8722;&#8377;331.27</td></tr>
                  <tr><td><code>RR_Abstain_matched</code></td><td style="text-align:right">2</td><td style="text-align:right">69.02%</td><td style="text-align:right">&#8377;475.36</td><td style="text-align:right">17.23%</td><td style="text-align:right">&#8722;&#8377;460.72</td><td style="text-align:right">&#8722;&#8377;308.18</td></tr>
                  <tr class="hi"><td><strong><code>Safe_EV_Sunk_m0</code></strong></td><td style="text-align:right"><strong>0</strong></td><td style="text-align:right"><strong>63.27%</strong></td><td style="text-align:right"><strong>&#8377;465.59</strong></td><td style="text-align:right"><strong>14.93%</strong></td><td style="text-align:right"><strong>&#8722;&#8377;344.09</strong></td><td style="text-align:right"><strong>&#8722;&#8377;260.05</strong></td></tr>
                  <tr class="hi"><td><strong><code>RT_2F_Min_m0</code></strong></td><td style="text-align:right"><strong>0</strong></td><td style="text-align:right">64.92%</td><td style="text-align:right"><strong>&#8377;478.38</strong></td><td style="text-align:right">16.26%</td><td style="text-align:right">&#8722;&#8377;468.32</td><td style="text-align:right">&#8722;&#8377;325.70</td></tr>
                </tbody></table>
                <p class="small"><strong>`R = 5,000` Paired Cluster Bootstrap (`v6_bootstrap_5000.csv`):</strong> <code>Safe_EV_Sunk_m0</code>, <code>Safe_EV_Phys_m0</code> (`&#8722;&#8377;333.57` ES10), and <code>RT_2F_Min_m0</code> achieve <code>p_holm_2s = 0.0024</code> across ALL 3 `State|` clusterings &amp; 1-, 2-, 4-week blocks.</p>
              </div>
              <div class="img-pane"><img src="{b64_img('rev_fig1_risk_coverage_ci.png')}" alt="Risk Coverage"></div>
            </div>
            """,
        ),
        (
            "Slide 8 of 12 &bull; Fair Controls & Crop Splits",
            "Equal-Dispatch Controls, Volatility Ablations & Every Crop (`rev_fig2`)",
            f"""
            <div class="grid-img">
              <div class="card">
                <h3>What Fair Controls Prove (`a18_fair_ablations.csv`)</h3>
                <ul>
                  <li><strong>Equal Test Dispatch (`63.27%`):</strong> Forcing `B2` down to `th = &#8377;298.92` gives `ES10 &#8722;&#8377;500.75` (`23.27%` loss) &mdash; `Safe_EV_Sunk_m0` still leads by <strong>`+&#8377;156.66/qtl` `ES10`</strong> (`-8.34 pp` losses).</li>
                  <li><strong>Adaptive `1 - cv28` vs Static 10%:</strong> Adaptive price volatility adds <strong>`+&#8377;100.66/qtl` `ES10`</strong> over `Safe_EV_fixed10pct_m0` (`&#8722;&#8377;444.75`).</li>
                  <li><strong>`val-ES10` Hard-Gated `MG`:</strong> Tuning `rep28 &ge; 0.75` cuts `ES10` to `&#8722;&#8377;445.92` only by reducing Mean (`&#8377;358.44/qtl`).</li>
                  <li><strong>Euclid `1.20x`:</strong> Mean `&#8377;465.20` (within `&#8377;0.39` of OSRM).</li>
                </ul>
              </div>
              <div class="img-pane"><img src="{b64_img('rev_fig2_ablations_and_crops.png')}" alt="Fair Ablations and Crops"></div>
            </div>
            """,
        ),
        (
            "Slide 9 of 12 &bull; Subgroup Generalizability",
            "State (`6/6`) & Crop (`5/5`) Breakdown & Honest Mean Boundaries",
            f"""
            <div class="grid2">
              <div class="card accent">
                <h3>Strictly Positive `ES10` 95% CIs Across ALL 6 States &amp; Crops</h3>
                <table><thead><tr><th>Slice</th><th style="text-align:right">Safe_EV Mean</th><th style="text-align:right">RT_2F Mean</th><th style="text-align:right">Safe_EV ES10 Gain vs B2 (95% CI)</th></tr></thead><tbody>
                  {slide9_state_rows}
                </tbody></table>
              </div>
              <div class="card">
                <h3>Complete Subgroup Transparency</h3>
                <ul>
                  <li><strong>All 5 Crop `ES10` Wins:</strong> NonApple `+&#8377;135.58`, Onion `+&#8377;123.49`, Potato `+&#8377;72.31`, Tomato `+&#8377;195.65`, Generic Apple `+&#8377;561.37` (where tuned `RR` was NS in MH/HP and Apple).</li>
                  <li><strong>Honest Mean Boundary:</strong> Because `Safe_EV_Sunk_m0` filters volatile lots aggressively, its Mean 95% CIs vs `B2` cross zero in GJ, MH, UP, Tomato (`&#8377;461.42` vs `&#8377;462.27`), and Apple &mdash; while <strong>`RT_2F_Min_m0` beats `B2` point Mean in ALL 6 states &amp; 5 crops</strong> (`Tomato &#8377;504.35`).</li>
                </ul>
              </div>
            </div>
            """,
        ),
        (
            "Slide 10 of 12 &bull; Sensitivity Tornado &amp; Exact Break-Even Bounds",
            "36/36 Tornado Robustness, Open-MAR &amp; Exact Silent-Market Break-Even",
            f"""
            <div class="grid-img">
              <div class="card">
                <ul>
                  <li><strong>36 / 36 Tornado Cells:</strong> Across 18 freight (`&#8377;0.258` NITI floor to `&#8377;1.20` steep), <em>arhtiya</em> (`0&ndash;6%`), HP hill (`1.0&ndash;1.75`), spoilage (`0.5&ndash;2x`), detention (`&#8377;0&ndash;100`), frozen &amp; re-scored, `Safe_EV` improves Mean (`+&#8377;13.31..+&#8377;61.11`) &amp; `ES10` (`+&#8377;144.94..+&#8377;329.37`).</li>
                  <li><strong>Exact Silent-Market Break-Even (`v6_breakeven.csv`):</strong> `B2` catches `Safe_EV` on Mean only if silent yards average <strong>`+&#8377;{float(be_20c["breakeven_silent_extra_inr"]):,.2f}/qtl` above turn-back</strong> (or flat `+&#8377;{float(be_20c["breakeven_silent_abs_payoff_inr"]):,.2f}` constant-payoff counterfactual; `{float(be_20c["breakeven_open_mar_share_pct"]):.2f}%` MAR share; `resid = 0.0`).</li>
                  <li><strong>Open-MAR Bound Disclosed:</strong> `B2` earns `+&#8377;102.58` Mean; `Safe_EV` keeps `+&#8377;190.00 ES10` &amp; `4.78%` vs `7.08%` losses.</li>
                </ul>
              </div>
              <div class="img-pane"><img src="{b64_img('rev_fig3_sensitivity_tornado_and_missing.png')}" alt="Tornado and Missing Bounds"></div>
            </div>
            """,
        ),
        (
            "Slide 11 of 12 &bull; Zero-Lookahead 171-Mkt, Realized ERA5 &amp; HP Apples",
            "171-Market Zero-Lookahead, Realized ERA5 Settlement &amp; HP Apples",
            f"""
            <div class="grid-img">
              <div class="card">
                <ul>
                  <li><strong>Strict `2024`-Only `171` Markets (`N=57,634`) &amp; Realized ERA5:</strong> Zero weather in decisions; settling with `100.0%` arrival ERA5 (`Q10` + `RH` + rain &ge;35mm) widens `Safe_EV` `ES10` gain to <strong>`+&#8377;{es10_gain_era178:,.2f}` (`178`-mkt)</strong> &amp; <strong>`+&#8377;{es10_gain_era171:,.2f}` (`171`-mkt)</strong> (`p_holm_2s = 0.0024`; break-even `+&#8377;{float(be_era["breakeven_silent_extra_inr"]):,.2f}`).</li>
                  <li><strong>`N = 88,014` Unconditional Origin Panel:</strong> `Safe_EV` `ES10 &#8722;&#8377;335.04` vs `&#8722;&#8377;515.93`, Mean `&#8377;483.03` vs `&#8377;445.37`; holds on exact-geocode (`N=40,690`) &amp; clean keys (`N=56,857`).</li>
                  <li><strong>HP Graded Apples (`N=2,802`):</strong> `Safe_EV` (`&#8377;1,354.85 / &#8722;&#8377;1,454.86`) beats `B2` (`&#8722;&#8377;2,392.12`) &amp; `MG` (`&#8722;&#8377;1,953.20`) &mdash; yet `41.38%` cond losses remain visible (`R6`).</li>
                </ul>
              </div>
              <div class="img-pane"><img src="{b64_img('rev_fig4_settlement_and_hp_apple.png')}" alt="Settlement and HP Apples"></div>
            </div>
            """,
        ),
        (
            "Slide 12 of 12 &bull; Cleanroom Verification &amp; Next Steps",
            "100% Cleanroom Verification (`Revision v6`) &amp; Prospective Field Trial",
            """
            <div class="grid2">
              <div class="card accent">
                <h3>Automated Cleanroom Verification (`make reproduce`)</h3>
                <ul>
                  <li><strong>Independent `A16` Script:</strong> Re-derives all 8 policies from raw parquets with <strong>`&#8377;0.00` parity</strong> &amp; enforces `n_clusters &le; 178`.</li>
                  <li><strong>Zero-Untraceable-Number Check (`verify_traceability.py`):</strong> `0` untraceable numbers across all `23/23` active markdown documents &amp; `49/49` verified bibliography citations.</li>
                  <li><strong>Clean-Clone `make reproduce`:</strong> Fresh clone reproduces all `31` CSV tables with <strong>`0.0` max abs diff</strong> &amp; `36/36` pytest green (`R = 5,000` cluster bootstrap).</li>
                </ul>
              </div>
              <div class="card">
                <h3>Explicit Limitations (`R6` / `R7`) &amp; Gate J</h3>
                <ul>
                  <li>Alert filter ahead of live *arhtiya* phone calls (`R7`).</li>
                  <li>Modeled survey payoffs &ne; physical auction *patti* cash receipts.</li>
                  <li>`Stage I H2` inconclusive (`+&#8377;6.13`, `p=0.2699`); Open-MAR reverses Mean (`B2 +&#8377;102.58`); HP Apples `41.38%` cond loss.</li>
                  <li><strong>Gate J = `BLOCKED (disclosed)`:</strong> Bulk AGMARKNET stops `2026-04-13`; next milestone is a live FPO pilot logging 6 a.m. alerts, trader calls, and physical truck bills.</li>
                </ul>
              </div>
            </div>
            """,
        ),
    ]

    slides_html = []
    for idx_s, (kicker, heading, inner) in enumerate(slides, 1):
        # Format backticks, **bold**, and *italic* cleanly without escaping HTML entities
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
              <footer class="s-foot"><span>Aditya Sharma &mdash; Shoolini University, Solan, Himachal Pradesh, India &bull; MandiGuard Revision v6</span><span>Slide {idx_s} / 12</span></footer>
            </section>"""
        )

    deck_css = """
@page { size: 13.333in 7.5in; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #0f172a; background: #ffffff; }
.slide {
  width: 13.333in; height: 7.5in;
  padding: 0.44in 0.56in 0.36in 0.56in;
  overflow: hidden;
  page-break-after: always;
  display: flex; flex-direction: column; justify-content: space-between;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 22%);
}
.slide:last-child { page-break-after: auto; }
.s-head { border-bottom: 2.5px solid #0f4c5c; padding-bottom: 8px; margin-bottom: 12px; }
.kicker { font-size: 10pt; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #0f4c5c; margin-bottom: 3px; }
h1 { margin: 0; font-size: 20pt; line-height: 1.18; color: #0b2538; }
h3 { margin: 0 0 8px 0; font-size: 13pt; color: #0f4c5c; }
.s-body { flex: 1; display: flex; flex-direction: column; justify-content: center; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: stretch; }
.grid-img { display: grid; grid-template-columns: 0.92fr 1.08fr; gap: 16px; align-items: center; }
.card { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px 16px; font-size: 11.2pt; line-height: 1.42; }
.card.accent { background: #f0f9ff; border-color: #7dd3fc; border-left: 5px solid #0284c7; }
ul { margin: 4px 0; padding-left: 18px; }
li { margin-bottom: 6px; }
code { font-family: Menlo, Consolas, monospace; font-size: 9.8pt; background: #e2e8f0; padding: 1px 4px; border-radius: 3px; }
.kpi-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 8px; }
.kpi { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px 12px; }
.kpi.good { background: #ecfdf5; border-color: #6ee7b7; }
.kpi .val { font-size: 18pt; font-weight: 800; color: #0f4c5c; }
.kpi .lbl { font-size: 9.2pt; color: #334155; margin-top: 2px; }
.eq-s { background: #ffffff; border: 1px solid #bae6fd; padding: 6px 10px; border-radius: 5px; font-weight: 600; margin-bottom: 7px; font-size: 11pt; }
.eq-big { background: #0f4c5c; color: #ffffff; padding: 10px 14px; border-radius: 6px; font-weight: 700; font-size: 13pt; text-align: center; margin: 8px 0; }
.pill-ok { background: #dcfce7; border: 1px solid #86efac; color: #14532d; padding: 7px 10px; border-radius: 5px; font-weight: 600; margin-top: 10px; font-size: 10.5pt; }
table { width: 100%; border-collapse: collapse; font-size: 9.2pt; }
th { background: #0f4c5c; color: #ffffff; padding: 5px 5.5px; text-align: left; }
td { padding: 4.5px 5.5px; border-bottom: 1px solid #e2e8f0; }
td[style*="right"], th[style*="right"] { white-space: nowrap; }
tr.hi { background: #ecfdf5; font-weight: 700; }
.small { font-size: 9.8pt; color: #334155; margin-top: 8px; }
.img-pane img { max-width: 100%; max-height: 5.4in; object-fit: contain; display: block; margin: 0 auto; border: 1px solid #cbd5e1; border-radius: 6px; background: #fff; padding: 4px; }
.s-foot { border-top: 1px solid #cbd5e1; padding-top: 6px; font-size: 9pt; color: #64748b; display: flex; justify-content: space-between; }
"""
    deck_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>MandiGuard Viva Defense Slides (Revision v6)</title><style>{deck_css}</style></head>
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
    bib_keys = set(re.findall(r"@\w+\{([^,\s]+),", bib))
    build_paper_html_and_pdf(bib_keys)
    build_latex_manuscript(bib_keys)
    build_docx_manuscript()
    build_easy_reading_html_and_pdf(bib_keys)
    build_viva_slides()

    # Final assertion pass over all generated HTML & PDF text
    for p in (
        PAPER_DIR / "MandiGuard_Research_Paper.pdf",
        PAPER_DIR / "MandiGuard_Easy_Reading_Edition.pdf",
        VIVA_DIR / "MandiGuard_Viva_Defense_Slides.pdf",
    ):
        txt = "\n".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)
        for bad in FORBIDDEN_LATEX_LEAKS + FORBIDDEN_LEGACY_STRINGS:
            assert bad not in txt, f"Forbidden string `{bad}` found in {p.name}"
    print("ALL Step-2 deliverables built & verified cleanly!")


if __name__ == "__main__":
    main()
