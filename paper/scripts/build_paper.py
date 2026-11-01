#!/usr/bin/env python
"""Build the CryoLean paper from one source, paper/src/paper.md, into:

    paper/CryoLean_paper.tex   XeLaTeX / LuaLaTeX / Tectonic source (+ paper/references.bib)
    paper/build/CryoLean_paper.typ  -> paper/CryoLean_paper.pdf  (compiled here with Typst; LaTeX math via mitex)

Source syntax (a small Markdown subset):
  front matter between '---' lines: title, author, affiliation, email, date, keywords, abstract (block '|')
  '# Heading {#sec:x}'  '## Sub'  '### Subsub'      '\\appendix' line starts appendices
  **bold**  *italic*  `code`  $inline math$  [@key] or [@a; @b] citations   @fig:x @tab:x @sec:x @eq:x references
  $$ display math $$ {#eq:x}   (on its own lines; the label line is optional)
  ![Caption.](fig_name){#fig:x width=0.95 wide}      figure from paper/figures (pdf for LaTeX, svg for Typst)
  pipe tables followed by 'Table: Caption. {#tab:x wide}'
  ```lean ... ```   code blocks
  ::: theorem Name ... :::     theorem-style boxes (also 'definition', 'remark')
  - item / 1. item lists;  {PROVEN} {COMPUTED} {MEASURED} {MODELED} {SOURCED} {PROPOSED} claim tags
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper"
SRC = PAPER / "src" / "paper.md"
BUILD = PAPER / "build"
CLAIMS = ("PROVEN", "COMPUTED", "MEASURED", "MODELED", "SOURCED", "PROPOSED", "ILLUSTRATIVE")
CLAIM_COLORS = {"PROVEN": "1a7f37", "COMPUTED": "2a4d8f", "MEASURED": "7c6ee6", "MODELED": "d9663a",
                "SOURCED": "52514e", "PROPOSED": "898781", "ILLUSTRATIVE": "898781"}


# ---------------------------------------------------------------- parsing
def front_matter(text: str):
    m = re.match(r"---\n(.*?)\n---\n", text, flags=re.S)
    meta, body = {}, text
    if m:
        body = text[m.end():]
        key = None
        for line in m.group(1).splitlines():
            if key and (line.startswith("  ") or not line.strip()):
                meta[key] += line[2:] + "\n"
                continue
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if v == "|":
                key, meta[k] = k, ""
            else:
                key, meta[k] = None, v
    return meta, body


def blocks(body: str):
    """Yield (kind, payload) blocks."""
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1
            continue
        if s.startswith("```"):
            lang = s[3:].strip()
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            yield "code", (lang, "\n".join(lines[i + 1:j]))
            i = j + 1
            continue
        if s.startswith("$$"):
            j = i
            if s.endswith("$$") and len(s) > 4:
                content = s[2:-2]
            else:
                j = i + 1
                while j < len(lines) and not lines[j].strip().endswith("$$"):
                    j += 1
                content = "\n".join([s[2:]] + lines[i + 1:j] + [lines[j].strip()[:-2]])
            label = None
            if j + 1 < len(lines) and re.match(r"\s*\{#(eq:[\w-]+)\}\s*$", lines[j + 1]):
                label = re.match(r"\s*\{#(eq:[\w-]+)\}", lines[j + 1]).group(1)
                j += 1
            yield "math", (content.strip(), label)
            i = j + 1
            continue
        if s.startswith(":::"):
            kind_name = s[3:].strip().split(None, 1)
            j = i + 1
            while j < len(lines) and lines[j].strip() != ":::":
                j += 1
            yield "box", (kind_name[0], kind_name[1] if len(kind_name) > 1 else "", "\n".join(lines[i + 1:j]))
            i = j + 1
            continue
        m = re.match(r"(#{1,3})\s+(.*?)(?:\s*\{#([\w:-]+)\})?\s*$", s)
        if m:
            yield "heading", (len(m.group(1)), m.group(2), m.group(3))
            i += 1
            continue
        if s == r"\appendix":
            yield "appendix", None
            i += 1
            continue
        m = re.match(r"!\[(.*)\]\(([\w.-]+)\)(?:\{(.*)\})?\s*$", s)
        if m:
            attrs = m.group(3) or ""
            lab = re.search(r"#(fig:[\w-]+)", attrs)
            w = re.search(r"width=([\d.]+)", attrs)
            yield "figure", (m.group(1), m.group(2), lab.group(1) if lab else None, float(w.group(1)) if w else 1.0,
                             "wide" in attrs)
            i += 1
            continue
        if s.startswith("|"):
            j = i
            rows = []
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(lines[j].strip())
                j += 1
            cap, lab, wide = "", None, False
            if j < len(lines) and lines[j].strip().startswith("Table:"):
                c = lines[j].strip()[6:].strip()
                mm = re.search(r"\{(.*)\}\s*$", c)
                if mm:
                    lab = (re.search(r"#(tab:[\w-]+)", mm.group(1)) or [None, None])[1]
                    wide = "wide" in mm.group(1)
                    c = c[:mm.start()].strip()
                cap = c
                j += 1
            cells = [[x.strip() for x in r.strip("|").split("|")] for r in rows]
            align = cells[1] if len(cells) > 1 and all(re.match(r":?-+:?$", x) for x in cells[1]) else None
            data = [cells[0]] + cells[2:] if align else cells
            aligns = ["c" if a.startswith(":") and a.endswith(":") else "r" if a.endswith(":") else "l"
                      for a in (align or ["-"] * len(cells[0]))]
            yield "table", (data, aligns, cap, lab, wide)
            i = j
            continue
        if re.match(r"(-|\d+\.)\s", s):
            ordered = bool(re.match(r"\d+\.", s))
            items = []
            j = i
            while j < len(lines) and lines[j].strip():
                t = lines[j]
                if re.match(r"\s*(-|\d+\.)\s", t):
                    items.append(re.sub(r"^\s*(-|\d+\.)\s+", "", t))
                else:
                    items[-1] += " " + t.strip()
                j += 1
            yield "list", (ordered, items)
            i = j
            continue
        j = i
        para = []
        while j < len(lines) and lines[j].strip() and not re.match(r"\s*(#{1,3}\s|```|\$\$|:::|!\[|\||(-|\d+\.)\s)", lines[j]):
            para.append(lines[j].strip())
            j += 1
        if not para:          # a line that looks like a block start but did not parse: treat as text
            para, j = [lines[i].strip()], i + 1
        yield "para", " ".join(para)
        i = j


# ---------------------------------------------------------------- inline conversion
TOKEN = re.compile(r"(`[^`]+`|\$[^$]+\$|\[@[^\]]+\]|@(?:fig|tab|sec|eq):[\w-]+|\*\*[^*]+\*\*|\*[^*\s][^*]*\*|\{(?:%s)\})"
                   % "|".join(CLAIMS))

TEX_ESC = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
           "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def tex_text(s: str) -> str:
    return "".join(TEX_ESC.get(c, c) for c in s)


def tex_inline(s: str) -> str:
    out, pos = [], 0
    for m in TOKEN.finditer(s):
        out.append(tex_text(s[pos:m.start()]))
        t = m.group(0)
        if t.startswith("`"):
            out.append(r"\texttt{" + tex_text(t[1:-1]) + "}")
        elif t.startswith("$"):
            out.append(t)
        elif t.startswith("[@"):
            keys = [k.strip().lstrip("@") for k in t[1:-1].split(";")]
            out.append(r"~\cite{" + ",".join(keys) + "}")
        elif t.startswith("@"):
            out.append(r"\cref{" + t[1:] + "}")
        elif t.startswith("**"):
            out.append(r"\textbf{" + tex_inline(t[2:-2]) + "}")
        elif t.startswith("*"):
            out.append(r"\emph{" + tex_inline(t[1:-1]) + "}")
        elif t.startswith("{"):
            out.append(r"\claim{" + t[1:-1] + "}")
        pos = m.end()
    out.append(tex_text(s[pos:]))
    return "".join(out)


TYP_SPECIAL = set("#*_`$<>@[]\\~")


def typ_text(s: str) -> str:
    return "".join("\\" + c if c in TYP_SPECIAL else c for c in s)


def typ_raw(s: str) -> str:
    n = 1
    while "`" * n in s:
        n += 1
    fence = "`" * max(n, 1)
    if n > 1:
        return f"{fence} {s} {fence}"
    return f"`{s}`"


def typ_math_inline(m: str) -> str:
    return "#mi(" + typ_raw(m) + ")"


def typ_inline(s: str) -> str:
    out, pos = [], 0
    for m in TOKEN.finditer(s):
        out.append(typ_text(s[pos:m.start()]))
        t = m.group(0)
        if t.startswith("`"):
            out.append(typ_raw(t[1:-1]))
        elif t.startswith("$"):
            out.append(typ_math_inline(t[1:-1]))
        elif t.startswith("[@"):
            keys = [k.strip().lstrip("@") for k in t[1:-1].split(";")]
            out.append(" " + " ".join(f"@{k}" for k in keys))
        elif t.startswith("@"):
            out.append(t)
        elif t.startswith("**"):
            out.append("#strong[" + typ_inline(t[2:-2]) + "]")
        elif t.startswith("*"):
            out.append("#emph[" + typ_inline(t[1:-1]) + "]")
        elif t.startswith("{"):
            out.append(f'#claim("{t[1:-1]}")')
        pos = m.end()
    out.append(typ_text(s[pos:]))
    return "".join(out)


# ---------------------------------------------------------------- LaTeX writer
TEX_PREAMBLE = r"""%% Generated by paper/scripts/build_paper.py from paper/src/paper.md. Edit the source, not this file.
%% Compile with XeLaTeX or LuaLaTeX (Unicode source):  latexmk -xelatex CryoLean_paper.tex   or   tectonic CryoLean_paper.tex
\documentclass[10pt,twocolumn,letterpaper]{article}
\usepackage[margin=0.75in,columnsep=0.25in]{geometry}
\usepackage{fontspec}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{unicode-math}
\setmathfont{Latin Modern Math}
\usepackage{graphicx,booktabs,array,xcolor,caption,float}
\usepackage{fvextra}
\usepackage[numbers,sort&compress]{natbib}
\usepackage[colorlinks=true,linkcolor={blue!50!black},citecolor={blue!50!black},urlcolor={blue!50!black}]{hyperref}
\usepackage[capitalise,nameinlink]{cleveref}
\captionsetup{font=small,labelfont=bf}
\newtheorem{theorem}{Theorem}
\theoremstyle{definition}\newtheorem{definition}{Definition}\newtheorem{remark}{Remark}
\definecolor{clPROVEN}{HTML}{1a7f37}\definecolor{clCOMPUTED}{HTML}{2a4d8f}\definecolor{clMEASURED}{HTML}{7c6ee6}
\definecolor{clMODELED}{HTML}{d9663a}\definecolor{clSOURCED}{HTML}{52514e}\definecolor{clPROPOSED}{HTML}{898781}
\definecolor{clILLUSTRATIVE}{HTML}{898781}
\newcommand{\claim}[1]{\textsf{\scriptsize\colorbox{cl#1!14}{\textcolor{cl#1}{#1}}}}
\DefineVerbatimEnvironment{code}{Verbatim}{fontsize=\footnotesize,breaklines=true,frame=leftline,framesep=2mm}
"""


def to_tex(meta, body):
    out = [TEX_PREAMBLE]
    out.append(r"\title{" + tex_inline(meta.get("title", "")) + "}")
    auth = tex_inline(meta.get("author", ""))
    if meta.get("affiliation"):
        auth += r"\\ \normalsize " + tex_inline(meta["affiliation"])
    if meta.get("email"):
        auth += r"\\ \normalsize\texttt{" + tex_text(meta["email"]) + "}"
    out.append(r"\author{" + auth + "}")
    out.append(r"\date{" + tex_inline(meta.get("date", "")) + "}")
    out.append(r"\begin{document}")
    out.append(r"\twocolumn[\begin{@twocolumnfalse}\maketitle\begin{abstract}" + tex_inline(" ".join(meta.get("abstract", "").split()))
               + (r"\par\smallskip\noindent\textbf{Keywords:} " + tex_inline(meta["keywords"]) if meta.get("keywords") else "")
               + r"\end{abstract}\bigskip\end{@twocolumnfalse}]")
    for kind, p in blocks(body):
        if kind == "heading":
            lvl, txt, lab = p
            cmd = {1: "section", 2: "subsection", 3: "subsubsection"}[lvl]
            out.append(f"\\{cmd}{{{tex_inline(txt)}}}" + (f"\\label{{{lab}}}" if lab else ""))
        elif kind == "appendix":
            out.append(r"\appendix")
        elif kind == "para":
            out.append(tex_inline(p) + "\n")
        elif kind == "math":
            content, lab = p
            if lab:
                out.append("\\begin{equation}\\label{" + lab + "}\n" + content + "\n\\end{equation}")
            else:
                out.append("\\begin{equation*}\n" + content + "\n\\end{equation*}")
        elif kind == "code":
            out.append("\\begin{code}\n" + p[1] + "\n\\end{code}")
        elif kind == "box":
            k, name, text = p
            inner = "\n\n".join(tex_inline(" ".join(x.split())) for x in re.split(r"\n\s*\n", text.strip()))
            out.append(f"\\begin{{{k}}}" + (f"[{tex_inline(name)}]" if name else "") + "\n" + inner + f"\n\\end{{{k}}}")
        elif kind == "figure":
            cap, name, lab, w, wide = p
            env = "figure*" if wide else "figure"
            out.append(f"\\begin{{{env}}}[t]\\centering\\includegraphics[width={w}\\linewidth]{{figures/{name}.pdf}}"
                       f"\\caption{{{tex_inline(cap)}}}" + (f"\\label{{{lab}}}" if lab else "") + f"\\end{{{env}}}")
        elif kind == "table":
            data, aligns, cap, lab, wide = p
            env = "table*" if wide else "table"
            rows = [" & ".join(tex_inline(c) for c in data[0]) + r" \\ \midrule"]
            rows += [" & ".join(tex_inline(c) for c in r) + r" \\" for r in data[1:]]
            out.append(f"\\begin{{{env}}}[t]\\centering\\small\\caption{{{tex_inline(cap)}}}" + (f"\\label{{{lab}}}" if lab else "")
                       + "\n\\resizebox{\\linewidth}{!}{\\begin{tabular}{" + "".join(aligns) + "}\\toprule\n" + "\n".join(rows)
                       + "\n\\bottomrule\\end{tabular}}\\end{" + env + "}")
        elif kind == "list":
            ordered, items = p
            env = "enumerate" if ordered else "itemize"
            out.append(f"\\begin{{{env}}}\n" + "\n".join(r"\item " + tex_inline(x) for x in items) + f"\n\\end{{{env}}}")
    out.append(r"\bibliographystyle{plainnat}")
    out.append(r"\bibliography{references}")
    out.append(r"\end{document}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- Typst writer
TYP_PREAMBLE = r"""// Generated by paper/scripts/build_paper.py from paper/src/paper.md. Edit the source, not this file.
#import "@preview/mitex:0.2.7": *
#set document(title: "%(title)s", author: "%(author)s")
#set page(paper: "us-letter", margin: (x: 0.75in, y: 0.8in), columns: 2,
  numbering: "1", number-align: center, header: context { if counter(page).get().first() > 1 [
    #set text(size: 7.5pt, fill: rgb("#52514e")); CryoLean: formally verified compatibility analysis for cryogenic experiments #h(1fr) #counter(page).display()
  ] })
#set columns(gutter: 0.25in)
#set text(font: "New Computer Modern", size: 9.6pt, lang: "en")
#set par(justify: true, leading: 0.55em, spacing: 0.75em)
#set heading(numbering: (..n) => if n.pos().len() <= 3 { numbering("1.1", ..n) })
#show heading.where(level: 1): it => block(above: 1.1em, below: 0.6em, text(size: 11pt, weight: "bold", it))
#show heading.where(level: 2): it => block(above: 0.9em, below: 0.5em, text(size: 10pt, weight: "bold", it))
#show heading.where(level: 3): it => block(above: 0.8em, below: 0.4em, text(size: 9.6pt, weight: "bold", style: "italic", it))
#set math.equation(numbering: "(1)")
#show figure.caption: set text(size: 8.4pt)
#show figure.where(kind: table): set figure.caption(position: top)
#show raw.where(block: true): set text(size: 7.6pt)
#show raw.where(block: true): it => block(width: 100%%, inset: (left: 6pt, y: 4pt), stroke: (left: 1.5pt + rgb("#7c6ee6")), fill: rgb("#f6f5fd"), it)
#show link: set text(fill: rgb("#2a4d8f"))
#show ref: set text(fill: rgb("#2a4d8f"))
#let claim(c) = {
  let col = (PROVEN: rgb("#1a7f37"), COMPUTED: rgb("#2a4d8f"), MEASURED: rgb("#7c6ee6"), MODELED: rgb("#d9663a"),
             SOURCED: rgb("#52514e"), PROPOSED: rgb("#898781"), ILLUSTRATIVE: rgb("#898781")).at(c)
  box(fill: col.lighten(86%%), inset: (x: 2pt, y: 1pt), radius: 2pt, baseline: 1pt,
      text(size: 6.2pt, weight: "bold", fill: col, font: "DejaVu Sans", c))
}
#let thmbox(kind, name, body) = block(width: 100%%, inset: 6pt, radius: 3pt, stroke: 0.6pt + rgb("#9a8ef0"),
  fill: rgb("#f8f7fe"), breakable: true)[#strong[#kind]#if name != "" [ (#name)]. #body]
"""


def to_typ(meta, body):
    out = [TYP_PREAMBLE % {"title": meta.get("title", "").replace('"', "'"), "author": meta.get("author", "")}]
    title = typ_inline(meta.get("title", ""))
    auth = typ_inline(meta.get("author", ""))
    aff = typ_inline(meta.get("affiliation", ""))
    email = meta.get("email", "")
    abstract = typ_inline(" ".join(meta.get("abstract", "").split()))
    kw = typ_inline(meta.get("keywords", ""))
    out.append("#place(top, scope: \"parent\", float: true, clearance: 1.2em)[\n#align(center)[\n"
               f"#text(size: 16pt, weight: \"bold\")[{title}]\n\n#v(0.4em)#text(size: 10.5pt)[{auth}]\\\n"
               f"#text(size: 9pt)[{aff}]" + (f"\\\n#text(size: 8.5pt, font: \"DejaVu Sans Mono\")[{typ_text(email)}]" if email else "")
               + (f"\\\n#text(size: 8.5pt)[{typ_inline(meta['date'])}]" if meta.get("date") else "")
               + "\n]\n#v(0.6em)\n#block(inset: (x: 0.5in))[#set par(justify: true)\n#text(size: 9pt)[#strong[Abstract.] " + abstract
               + (f"\\\n#v(0.3em)#strong[Keywords:] {kw}" if kw else "") + "]]\n]\n")
    in_appendix = False
    for kind, p in blocks(body):
        if kind == "heading":
            lvl, txt, lab = p
            out.append("=" * lvl + " " + typ_inline(txt) + (f" <{lab}>" if lab else ""))
        elif kind == "appendix":
            in_appendix = True
            out.append('#set heading(numbering: "A.1")\n#counter(heading).update(0)')
        elif kind == "para":
            out.append(typ_inline(p) + "\n")
        elif kind == "math":
            content, lab = p
            out.append("#mitex(" + typ_raw(content.replace("\n", " ")) + ")" + (f" <{lab}>" if lab else ""))
        elif kind == "code":
            lang, code = p
            fence = "````" if "```" in code else "```"
            out.append(f"{fence}{lang}\n{code}\n{fence}")
        elif kind == "box":
            k, name, text = p
            inner = " #parbreak() ".join(typ_inline(" ".join(x.split())) for x in re.split(r"\n\s*\n", text.strip()))
            out.append(f'#thmbox("{k.capitalize()}", "{name}")[{inner}]')
        elif kind == "figure":
            cap, name, lab, w, wide = p
            scope = ', scope: "parent"' if wide else ""
            out.append(f'#figure(image("../figures/{name}.svg", width: {int(round(w * 100))}%), caption: [{typ_inline(cap)}],'
                       f" placement: top{scope})" + (f" <{lab}>" if lab else ""))
        elif kind == "table":
            data, aligns, cap, lab, wide = p
            al = ", ".join({"l": "left", "c": "center", "r": "right"}[a] for a in aligns)
            cells = ", ".join("[" + typ_inline(c) + "]" for c in data[0])
            body_cells = ", ".join("[" + typ_inline(c) + "]" for r in data[1:] for c in r)
            scope = ', scope: "parent"' if wide else ""
            out.append(f"#figure(placement: top{scope}, kind: table, caption: [{typ_inline(cap)}],\n"
                       f"  text(size: 7.6pt, table(columns: {len(data[0])}, align: ({al},), stroke: none, inset: (x: 3pt, y: 2.2pt),\n"
                       f"    table.hline(stroke: 0.8pt), table.header({cells}), table.hline(stroke: 0.4pt), {body_cells}, table.hline(stroke: 0.8pt))))"
                       + (f" <{lab}>" if lab else ""))
        elif kind == "list":
            ordered, items = p
            mark = "+" if ordered else "-"
            out.append("\n".join(f"{mark} " + typ_inline(x) for x in items) + "\n")
    out.append('#v(0.5em)\n#bibliography("../references.bib", title: "References", style: "ieee")')
    return "\n".join(out) + "\n"


def main():
    import typst
    sys.stdout.reconfigure(encoding="utf-8")
    meta, body = front_matter(SRC.read_text(encoding="utf-8"))
    tex = to_tex(meta, body)
    (PAPER / "CryoLean_paper.tex").write_text(tex, encoding="utf-8")
    BUILD.mkdir(exist_ok=True)
    typ = to_typ(meta, body)
    tp = BUILD / "CryoLean_paper.typ"
    tp.write_text(typ, encoding="utf-8")
    typst.compile(str(tp), output=str(PAPER / "CryoLean_paper.pdf"), root=str(PAPER))
    pngs = typst.compile(str(tp), format="png", ppi=70, root=str(PAPER))
    prev = BUILD / "preview"
    shutil.rmtree(prev, ignore_errors=True)
    prev.mkdir()
    for i, png in enumerate(pngs if isinstance(pngs, list) else [pngs], 1):
        (prev / f"page{i:02d}.png").write_bytes(png)
    print(f"wrote paper/CryoLean_paper.tex, paper/CryoLean_paper.pdf ({len(pngs) if isinstance(pngs, list) else 1} pages), previews in paper/build/preview/")


if __name__ == "__main__":
    main()
