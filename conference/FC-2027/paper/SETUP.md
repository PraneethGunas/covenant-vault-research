# One-time setup for the FC 2027 paper workspace

## 1. Install Springer LNCS class

The LNCS LaTeX class (`llncs.cls`) is a TeX Live package but is not installed
by default in most TeX Live distributions. Install it once:

```bash
sudo tlmgr install llncs
```

Verify:

```bash
kpsewhich llncs.cls
# Should output: /usr/local/texlive/2026basic/texmf-dist/tex/latex/llncs/llncs.cls
```

If `tlmgr` is not available (e.g., on a minimal install), download the class
directly from Springer:

```bash
cd /Users/praneeth/Desktop/research\ experiments/conference/FC-2027/paper
curl -L -O https://resource-cms.springernature.com/springer-cms/rest/v1/content/19238648/data/v6
unzip v6
# The zip contains llncs.cls, splncs04.bst, and samples
mv llncs.cls splncs04.bst .
rm -rf v6 __MACOSX 2>/dev/null || true
```

## 2. Verify the skeleton compiles

```bash
cd /Users/praneeth/Desktop/research\ experiments/conference/FC-2027/paper
pdflatex -interaction=nonstopmode fc27-paper.tex
bibtex fc27-paper
pdflatex -interaction=nonstopmode fc27-paper.tex
pdflatex -interaction=nonstopmode fc27-paper.tex
```

If there are no errors (warnings about undefined references in an empty skeleton
are expected), open `fc27-paper.pdf` and confirm:

- Title renders as "The Cost of Custody: Fee-Dependent Security Inversion in Bitcoin Covenant Vaults"
- Abstract placeholder renders
- Section headers 1–8 render
- "Anonymous Authors" byline renders
- References placeholder renders

## 3. Populate the bibliography

Copy from the thesis:

```bash
cp "/Users/praneeth/Desktop/research experiments/Thesis/references.bib" \
   "/Users/praneeth/Desktop/research experiments/conference/FC-2027/paper/references.bib"
```

Then verify:

```bash
bibtex fc27-paper
# Should succeed with no undefined entries (some will still be unused in the skeleton)
```

## 4. Install the LNCS theme in your editor

If you use VS Code:
- Install extension: James-Yu.latex-workshop
- Configure `latex-workshop.latex.tools` to use `latexmk -pdf -interaction=nonstopmode -halt-on-error`
- Configure a recipe that runs `pdflatex → bibtex → pdflatex → pdflatex`

If you use Overleaf (optional collaborative workflow):
- Upload the entire `paper/` folder
- Set compiler: "pdfLaTeX"
- Set main document: `fc27-paper.tex`
- Run first compile to confirm

## 5. Commit the workspace

```bash
cd /Users/praneeth/Desktop/research\ experiments/
git add conference/
git commit -m "feat(conference): scaffold FC 2027 paper workspace"
```

Do NOT commit:
- `*.aux`, `*.bbl`, `*.blg`, `*.log`, `*.out`, `*.toc`, `*.synctex.gz`, `*.pdf`
  (except for source figure PDFs in `paper/figures/`)
- Anything in `drafts/` that you haven't explicitly pushed
- Any file matching `anonymized-*` or `private-*`

A `.gitignore` is provided at `paper/.gitignore`.

## Troubleshooting

### "! LaTeX Error: File `llncs.cls' not found"

LNCS class is missing. Re-run step 1.

### "! LaTeX Error: Missing \begin{document}"

The sections/*.tex files contain `\section{...}` directly (no document
wrapping) — this is correct. If you see this error, you probably tried to
compile a section file directly. Always compile `fc27-paper.tex`.

### Bibliography not rendering

Bibliography uses `splncs04.bst`. If it's missing:

```bash
sudo tlmgr install llncs
# or download the Springer bundle as in step 1
```

### Too many pages

The skeleton renders with placeholder content and may be short. Once populated,
use `pdfinfo` to count pages:

```bash
pdfinfo fc27-paper.pdf | grep Pages
```

Target: 15 pages in the main body (the paper counts until the appendix).

---

**Once all 5 steps pass, you're ready to write §3. See `../WRITING-SCHEDULE.md` Week 2.**
