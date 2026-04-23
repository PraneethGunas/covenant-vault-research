# FC 2027 Paper Workspace

Target venue: **Financial Cryptography and Data Security 2027** main conference.

**Deadline:** ~Sep 15, 2026 (exact date confirmed when FC'27 CFP releases, ~Jun 2026)
**Format:** 15 pp Springer LNCS + unlimited refs/appendix
**Review:** Double-blind

## Folder contents

```
FC-2027/
├── README.md                 # This file — navigation and quick start
├── OUTLINE.md                # Detailed 15pp section-by-section outline
├── WRITING-SCHEDULE.md       # Week-by-week plan (May → Sep 2026)
├── paper/                    # Actual paper files (compile this)
│   ├── fc27-paper.tex        # LNCS main file (skeleton ready to populate)
│   ├── references.bib        # Bibliography (copy of thesis bib to refine)
│   ├── sections/             # One .tex file per section
│   │   ├── 01-introduction.tex
│   │   ├── 02-background.tex
│   │   ├── 03-impossibility.tex
│   │   ├── 04-empirical.tex
│   │   ├── 05-deployment.tex
│   │   ├── 06-related.tex
│   │   ├── 07-discussion.tex
│   │   └── 08-conclusion.tex
│   ├── figures/              # TikZ figures / PDFs for the paper
│   ├── appendix-a-alloy.tex
│   ├── appendix-b-threat-matrix.tex
│   ├── appendix-c-measurements.tex
│   ├── README.md             # Build instructions
│   └── SETUP.md              # One-time setup (install LNCS)
└── drafts/                   # Draft iterations (commit each major revision)
```

## TL;DR — How to start writing

**Immediately (before defense):**
1. Read `OUTLINE.md` and `WRITING-SCHEDULE.md` to internalize the plan
2. Run the one-time setup in `paper/SETUP.md` (install LNCS class)
3. Verify the skeleton compiles: `cd paper && pdflatex fc27-paper.tex`

**Week 1 post-defense (May 1–7, 2026):**
1. Finalize thesis submission to VT
2. Copy `references.bib` from thesis (already done)
3. Audit the skeleton — ensure all section stubs are in place

**Week 2 post-defense (May 8–14, 2026):**
1. Write §3 (Impossibility Results) first — this is the paper's core and the only content that's locked-down
2. Port Proposition 5.2 and Theorem 5.3 from thesis `ch5_security.tex`
3. Tighten proofs for 3pp budget

**Week 3–4 post-defense (May 15–28, 2026):**
1. Write §1 (Intro) to match the theorems you just wrote
2. Write §2 (Background + threat model) — tight, 2pp
3. Assemble preprint version (non-anonymized, full length) → upload to IACR ePrint

**Weeks 5–16 (June – September 2026):**
1. Iteratively fill in §4 (Empirical), §5 (Deployment), §6 (Related Work), §7 (Discussion), §8 (Conclusion)
2. Advisor reviews, external reviews, polish cycles
3. Anonymize, double-check, submit Sep 15, 2026

See `WRITING-SCHEDULE.md` for the full day-by-day plan.

## Paper identity at a glance

| Attribute | Value |
|---|---|
| **Working title** | The Cost of Custody: Fee-Dependent Security Inversion in Bitcoin Covenant Vaults |
| **Running title** | Fee-Dependent Security Inversion in Covenant Vaults |
| **Paper type** | Regular paper (15 pp) |
| **Primary contribution** | Theorem (Fee-Dependent Security Inversion) + Proposition (Griefing-Safety Incompatibility) |
| **Secondary contribution** | Cross-covenant empirical measurement (5 designs, 15 experiments, regtest) |
| **Tertiary contribution** | Bounded-model-check formal validation (Alloy, 9 files, 42 assertions, 41 checks; 40 pass + 1 expected-fail counterexample) |
| **Intended audience** | FC community — Bitcoin protocol researchers, covenant proposal authors, vault operators |
| **Pitch sentence** | "No Bitcoin covenant vault design is universally safest; the safety ranking inverts at a fee rate that scales linearly with vault value." |

## Parallel preprint plan

In addition to FC'27, post a **non-anonymized, full-length** preprint to:
- **IACR ePrint** by May 20, 2026
- **arXiv** (cs.CR) mirror by May 22, 2026

This does NOT preclude the FC'27 submission. IACR policy explicitly permits ePrint preprints. See `../SUBMISSION-STRATEGY.md` § 9 for details.

## Key source files (in thesis repo)

These are the thesis chapters you'll extract from:

| Thesis file | Maps to FC paper section |
|---|---|
| `Thesis/chapters/ch1_introduction.tex` | §1 Introduction (compress 9pp → 1.5pp) |
| `Thesis/chapters/ch2_background.tex` | §2 Background (compress 13pp → 2pp) |
| `Thesis/chapters/ch3_methodology.tex` | §4 Empirical prelude + appendix C |
| `Thesis/chapters/ch4_results.tex` | §4 Empirical body + appendix C |
| `Thesis/chapters/ch5_security.tex` | **§3 Impossibility (heart) + §5 Deployment** |
| `Thesis/chapters/ch6_formal.tex` | §3 summary + appendix A |
| `Thesis/chapters/ch7_discussion.tex` | §7 Discussion |
| `Thesis/chapters/ch8_related_work.tex` | §6 Related Work (compress 8pp → 1pp) |
| `Thesis/chapters/ch9_conclusion.tex` | §8 Conclusion (compress 3pp → 0.5pp) |
| `Thesis/chapters/app_a_alloy.tex` | Appendix A Alloy details |

## Status

- [x] Workspace scaffolded (2026-04-17)
- [ ] LNCS class installed (`sudo tlmgr install llncs`)
- [ ] LaTeX skeleton compiles
- [ ] References.bib ported from thesis
- [ ] §3 Impossibility Results drafted
- [ ] §1 Introduction drafted
- [ ] §2 Background drafted
- [ ] Preprint posted to IACR ePrint
- [ ] Preprint mirrored on arXiv
- [ ] §4–§8 drafted
- [ ] Advisor review round 1
- [ ] External review round
- [ ] Anonymization pass
- [ ] Final review + submission check
- [ ] ★ FC'27 submitted (Sep 15, 2026)
