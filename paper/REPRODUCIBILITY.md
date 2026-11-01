# Reproducing the CryoLean paper

Everything in `paper/` is regenerated from the repository by the commands below. No number in the paper is typed
by hand: tables and captions cite values from `paper/data/*.json`, which these scripts write.

## Environment used for the paper

| Item | Version |
|---|---|
| OS | Windows 11 (10.0.26200) |
| CPU | Intel Core i9 (Intel64 Family 6 Model 183), read from the OS by `platform.processor()` |
| Python | 3.12.10 |
| Lean | 4.35.0 (`lean/lean-toolchain`), via elan |
| Z3 | z3-solver (Python API) |
| Plotting | numpy, scipy, pandas, matplotlib, plotly, networkx |
| Paper build | Typst 0.15 (Python package `typst`) with the `mitex` package for LaTeX math |

The exact values are also saved in `paper/data/env.json` by the evaluation script.

## Steps

1. Install and build (once):

```bash
pip install -r requirements.txt
pip install numpy scipy pandas matplotlib plotly networkx typst
cd lean && lake build && cd ..
python -m cryolean build-db
```

2. Check the proofs and the axioms (this caches `lean/audit-axioms.json`, which each verdict card cites):

```bash
python scripts/audit_axioms.py
python scripts/run_forensics.py
python -m pytest
```

3. Run the evaluation (10 to 20 minutes; it calls the compiled Lean checker and Z3 thousands of times):

```bash
python paper/scripts/paper_eval.py
```

4. Draw every figure (each script writes PNG, SVG and PDF to `paper/figures/`, metadata to `paper/figures/meta/`, and the 3D figures' interactive HTML to `paper/interactive/`):

```bash
for f in paper/scripts/fig_*.py; do python "$f"; done
python paper/scripts/build_figure_index.py
```

5. Build the bibliography and the paper:

```bash
python paper/scripts/make_bib.py
python paper/scripts/build_paper.py
```

`build_paper.py` writes `paper/CryoLean_paper.tex` and compiles `paper/CryoLean_paper.pdf` with Typst. Both come from
the single source `paper/src/paper.md`.

## Building the LaTeX version

`paper/CryoLean_paper.tex` targets XeLaTeX or LuaLaTeX because the source is Unicode. It uses `figures/*.pdf` and
`references.bib`:

```bash
cd paper && latexmk -xelatex CryoLean_paper.tex
```

or `tectonic CryoLean_paper.tex`. **Status:** the PDF in this repository was built with Typst. No TeX engine was
installed on the build machine, and downloading one was blocked by the sandbox, so the `.tex` file has not been compiled
here. It is generated mechanically from the same source as the PDF, so the content is identical, but expect possible
small LaTeX fixes on first compile.

## Timing measurements

Timings depend on the machine and on background load. Benchmarks were run after the figure scripts, with no other
heavy work running. Each timing is a median over repeats, with the spread shown in the figures. Lean timings for single
checks include starting the checker process, about 0.1 s on this machine. Batch timings show the per-pair cost
without that overhead.

## Data provenance

The catalog is built from `data/` (JSON seeds with an evidence id on every value). `RESEARCH_SOURCES.md` lists every
source. The v3 gap research added for this paper is in `research/v3/` (raw results with the verifier's notes) and
`data/evidence/v3_gap_research.json` (imported records). Only records that a second, independent agent re-fetched and
confirmed were imported.
