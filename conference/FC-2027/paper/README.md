# FC 2027 Paper — Build Guide

## Files

```
paper/
├── fc27-paper.tex           # Main file — compile this
├── references.bib           # Bibliography (copy of thesis refs)
├── sections/
│   ├── 01-introduction.tex
│   ├── 02-background.tex
│   ├── 03-impossibility.tex  ← WRITE THIS FIRST (the paper's core)
│   ├── 04-empirical.tex
│   ├── 05-deployment.tex
│   ├── 06-related.tex
│   ├── 07-discussion.tex
│   └── 08-conclusion.tex
├── appendix-a-alloy.tex
├── appendix-b-threat-matrix.tex
├── appendix-c-measurements.tex
├── figures/                 # TikZ sources / PDFs
├── SETUP.md                 # One-time setup (install LNCS class)
├── README.md                # This file
└── .gitignore
```

## Build

```bash
# First time — see SETUP.md
sudo tlmgr install llncs

# Each build
pdflatex -interaction=nonstopmode fc27-paper.tex
bibtex fc27-paper
pdflatex -interaction=nonstopmode fc27-paper.tex
pdflatex -interaction=nonstopmode fc27-paper.tex
```

Or with latexmk:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error fc27-paper.tex
```

Clean:

```bash
latexmk -C
```

## Section conventions

- Each `sections/NN-name.tex` begins with `\section{...}`, no document wrapping
- `\label{sec:...}` on every section/subsection for cross-references
- Use `\todo[inline]{...}` placeholders during drafting; remove before submission
- LNCS two-column; prefer single-column figures for complex diagrams
- Citations in `references.bib` use `plain` author-year keys (e.g., `MES16`
  for Möser-Eyal-Sirer 2016)

## Bibliography conventions

- Bibliography style: `splncs04` (Springer LNCS 2024 convention)
- Entries must have DOI or URL
- Anonymize any self-citations (replace with `[anonymized]`)

## Anonymization

Before submission, verify:

```bash
# Should return zero results:
grep -rin "praneeth\|gunas\|virginia tech\|arlington\|blacksburg\|matsuo\|wenjing\|na meng" .
```

## Page count verification

```bash
pdfinfo fc27-paper.pdf | grep Pages
# Target: 15 (main body; appendices unlimited)
```

To count the body only (excluding appendix):

```bash
# Use \pageref on a \label placed at the appendix start to find the page number
# Alternatively, visually inspect by opening the PDF
```

## Tagging

Tag major milestones:

```bash
git tag v0.1-skeleton       # Empty skeleton compiles
git tag v0.2-impossibility  # §3 drafted
git tag v0.3-preprint       # Preprint version ready for ePrint
git tag v0.4-anon-draft     # First anonymized FC draft
git tag v0.5-advisor        # Post-advisor review
git tag v0.6-external       # Post-external review
git tag v1.0-submitted      # Submitted to FC'27
```

## Common issues

### LaTeX class not found

See `SETUP.md`. `sudo tlmgr install llncs` should fix it.

### Running heads wrong

LNCS uses `\titlerunning{}` and `\authorrunning{}` macros. Set these to keep
running headers short. Already configured in `fc27-paper.tex`.

### Hyperlinks broken in compiled PDF

`hyperref` must be loaded last. Already done in the preamble.

### `spnewtheorem` not found

This is LNCS-specific; `\newtheorem` from `amsthm` conflicts with LNCS. Use
`\spnewtheorem` for custom theorem-like environments.

### Wide tables

LNCS is two-column by default. For wide tables, use `\begin{table*}` (spans
both columns). Already applied to Table 1 in §2.

### Too many pages

See `../OUTLINE.md` § "Length management" for cutting strategy.

## Preprint vs. submission versions

Keep two versions synced:

- `fc27-paper.tex` — anonymized, 15pp, for FC submission
- `fc27-preprint.tex` — non-anonymized, full-length, for IACR ePrint + arXiv

Create `fc27-preprint.tex` by duplicating the main file and:

1. Change `\author{Anonymous}` → your actual name + affiliation
2. Remove page limits / remove compression
3. Re-add thesis acknowledgments, advisor mentions

Both should share the same `sections/*.tex` files (use `\ifdefined` or
conditional comments if the content genuinely differs; otherwise keep them
identical).
