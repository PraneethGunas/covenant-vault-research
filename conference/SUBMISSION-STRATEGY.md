# Conference Submission Strategy
## "The Cost of Custody: Security Tradeoffs and Fee Dynamics in Bitcoin Covenant Vaults"

**Author:** Praneeth Gunas
**Thesis defense:** April 29, 2026 (Virginia Tech, Arlington)
**Working dir:** `/Users/praneeth/Desktop/research experiments/Thesis/`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Contribution Summary](#2-contribution-summary)
3. [Venue Tiering](#3-venue-tiering)
4. [Master Timeline (work-back from graduation)](#4-master-timeline)
5. [Primary Venue — Financial Cryptography 2027](#5-primary-venue--financial-cryptography-2027)
6. [Backup Venue — IEEE ICBC 2027 SoK](#6-backup-venue--ieee-icbc-2027-sok)
7. [Stretch Archival — AFT 2027](#7-stretch-archival--aft-2027)
8. [Workshop Fallbacks (CAAW, ACM DeFi, MARBLE, Tokenomics)](#8-workshop-fallbacks)
9. [Parallel / Preprint Track (IACR ePrint + arXiv)](#9-parallel--preprint-track)
10. [High-Stretch Targets (NDSS, IEEE S&P)](#10-high-stretch-targets)
11. [Venues to Avoid](#11-venues-to-avoid)
12. [Framing Matrix — One Thesis, Four Angles](#12-framing-matrix)
13. [Pre-submission Checklist (Universal)](#13-pre-submission-checklist)
14. [Decision Tree](#14-decision-tree)

---

## 1. Executive Summary

**Primary plan.** Submit to **Financial Cryptography 2027 main conference** (15-page LNCS, double-blind). Deadline ~**Sep 15, 2026**. This is the natural home for a formal-verification + empirical-measurement paper on Bitcoin covenants. FC'25 accepted directly comparable work ("A Formally Verified Lightning Network"; Möser–Eyal–Sirer "Bitcoin Covenants" is a canonical FC predecessor from 2016).

**Parallel preprint.** Post to **IACR ePrint + arXiv** immediately after defense (May 2026). This is the norm in Bitcoin research, does not preclude FC submission (FC and IACR explicitly allow preprints), and establishes date-of-record.

**Backup plan.** If FC'27 rejects, cascade to **IEEE ICBC 2027 SoK track** (16 pp, Bitcoin-friendly, Dec 2026 deadline has already passed → target ICBC 2028 SoK, Dec 2027) or **AFT 2027** (20 pp LIPIcs, May 2027).

**Long shot.** Extract the Fee-Dependent Security Inversion theorem as a standalone adversarial attack paper and target **NDSS 2027 Fall cycle** (Aug 2026) or **IEEE S&P Cycle 2** (Nov 2026). Requires substantial reframing — not recommended until FC outcome is known.

**Venues to skip entirely:** USENIX Security, ACM CCS main, Scaling Bitcoin (dormant), CESC (dormant), SBC/DSS/RWC (talk-only).

---

## 2. Contribution Summary

What the paper delivers, in order of novelty:

1. **Theorem (Fee-Dependent Security Inversion).** No covenant vault design is universally safest; the ranking inverts at fee rate \(r^*\) whose value scales linearly with vault value.
2. **Proposition (Griefing–Safety Incompatibility).** No vault simultaneously achieves permissionless recovery and griefing resistance. Exhaustive case analysis over boolean \(\mathcal{A}(\emptyset)\).
3. **Cross-covenant threat matrix.** 11 threat models × 4 Bitcoin covenant designs + Simplicity, with per-cell vsize-quantified severity.
4. **Empirical measurements.** 15 experiments × 5 covenants on regtest (Bitcoin Inquisition for CTV/CAT+CSFS, Merkleize CCV node, jamesob opvault, Elements for Simplicity).
5. **Formal models.** 5 Alloy models (41 assertions) covering vault state machines and covenant-specific properties.
6. **First working CAT+CSFS vault implementation** (contributed upstream; appears in simple-cat-csfs-vault).

**Length budget.** Thesis is 110 pp → condense to:
- 15 pp (FC regular / LNCS)
- 16 pp (ICBC SoK / IEEE 2-col)
- 20 pp (AFT / LIPIcs)

---

## 3. Venue Tiering

| Tier | Venue | Deadline (target cycle) | Fit | Accept % | Verdict |
|---|---|---|---|---|---|
| **A (primary)** | FC 2027 main | ~Sep 15, 2026 | **Strong** | 22–25% | Submit first |
| **A-parallel** | IACR ePrint + arXiv | Rolling (immediate) | **Strong** | — | Post May 2026 |
| **B (backup)** | IEEE ICBC 2028 SoK | ~Dec 1, 2027 | **Strong** | ~25% (SoK) | Use if FC rejects |
| **B** | AFT 2027 | ~May 28, 2027 | **Moderate (reframing)** | 26–30% | Use if FC rejects |
| **C (workshop)** | CAAW @ FC 2027 | ~Jan 2027 | **Strong** | 25–40% | Empirical-only fallback |
| **C** | ACM DeFi @ CCS 2026 | ~Jul 2026 | **Strong** | ~30% | Earlier workshop option |
| **C** | MARBLE 2027 | ~Feb 2027 | **Strong (econ framing)** | 30–40% | Theorem-centric paper |
| **C** | Tokenomics 2026 | TBD (watch LIP6) | Moderate | 30–40% | Economic-mechanism framing |
| **D (stretch)** | NDSS 2027 Fall | ~Aug 6, 2026 | **Weak (reframe as attack)** | 15–16% | Only after FC outcome |
| **D** | IEEE S&P Cycle 2 (2027) | ~Nov 13, 2026 | **Weak** | 15–18% | Only after FC outcome |
| **skip** | USENIX Security | — | Too niche for venue | — | Don't submit as-is |
| **skip** | ACM CCS main | — | Too niche for venue | — | Don't submit as-is |
| **skip** | Scaling Bitcoin, CESC | — | **Dormant** | — | — |
| **skip** | SBC, DSS, RWC | — | **Talk-only, no proceedings** | — | Use for visibility only |

---

## 4. Master Timeline

**Work-back from thesis defense (April 29, 2026).** All dates in **2026** unless marked.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  APR 2026                                                                │
│  ──  29  │ THESIS DEFENSE (VT, Arlington)                                │
│          │                                                               │
│  MAY 2026                                                                │
│  ──  01-07  Final thesis submission to VT graduate school                │
│  ──  08-15  Create LNCS-formatted paper skeleton (port ch1-9 → 15pp)     │
│  ──  16-31  First draft of FC paper — compress, reframe, anonymize       │
│                                                                          │
│  JUN 2026                                                                │
│  ──  01-15  Advisor review round 1 (Matsuo / Lou / Meng)                 │
│  ──  15-30  Revise based on feedback                                     │
│  ──  30     → IACR ePrint preprint posted (sets priority date)           │
│  ──  30     → arXiv preprint mirrored                                    │
│                                                                          │
│  JUL 2026                                                                │
│  ──  01-15  External-review round — send to Rubin/Ingala/O'Beirne        │
│  ──  15-31  Incorporate external feedback                                │
│  ──  (Optional alt-path: submit to ACM DeFi @ CCS 2026, deadline ~Jul)   │
│                                                                          │
│  AUG 2026                                                                │
│  ──  01-31  Polish — reproducibility appendix, artifact prep             │
│                                                                          │
│  SEP 2026                                                                │
│  ──  15     ★★★ FC 2027 SUBMISSION DEADLINE ★★★                         │
│             (exact date announced on ifca.ai/fc27 ~Jun 2026; watch)     │
│             - 15 pp LNCS, double-blind, PDF-only                         │
│             - Unlimited refs & appendix                                  │
│                                                                          │
│  OCT-NOV 2026  Review period (no author action)                          │
│                                                                          │
│  NOV 2026                                                                │
│  ──  ~20-25  FC 2027 notification (historical pattern)                   │
│                                                                          │
│  DEC 2026                                                                │
│  ──  01-15  Rebuttal / camera-ready revisions                            │
│  ──  15     If ACCEPTED → camera-ready due ~Jan 12, 2027                 │
│  ──  15     If REJECTED → begin ICBC 2028 SoK prep                       │
│                                                                          │
│  JAN 2027                                                                │
│  ──  12     FC 2027 camera-ready deadline                                │
│  ──  (Alt: CAAW 2027 @ FC deadline ~mid-Jan)                             │
│                                                                          │
│  MAR 2027                                                                │
│  ──  2-6    FC 2027 CONFERENCE — travel, present, network                │
└─────────────────────────────────────────────────────────────────────────┘
```

**Critical external dates (confirm each ~3 months before):**

| Event | Expected date | Source to check |
|---|---|---|
| FC'27 CFP released | ~Jun 2026 | https://ifca.ai (watch for fc27 subpage) |
| FC'27 submission deadline | ~Sep 15, 2026 | FC'27 CFP |
| FC'27 notification | ~Nov 20, 2026 | FC'27 CFP |
| FC'27 camera-ready | ~Jan 12, 2027 | FC'27 CFP |
| FC'27 conference | Mar 2–6, 2027 (tentative) | FC'27 site |
| CAAW 2027 submission | ~Jan 2027 | https://caaw.io/ |
| ACM DeFi 2026 submission | ~Jul 10, 2026 | https://defiwork.shop |
| MARBLE 2027 | ~Feb 2027 | https://marble-conference.org |
| AFT 2027 submission | ~May 28, 2027 | https://aft.acm.org |
| ICBC 2028 SoK | ~Dec 1, 2027 | https://icbc-2028 (TBA) |
| NDSS 2027 Fall | ~Aug 6, 2026 | https://ndss-symposium.org |
| IEEE S&P 2027 Cycle 2 | ~Nov 13, 2026 | https://ieee-security.org |

---

## 5. Primary Venue — Financial Cryptography 2027

### 5.1 Venue snapshot

- **Full name:** International Conference on Financial Cryptography and Data Security
- **Sponsor:** International Financial Cryptography Association (IFCA)
- **URL:** https://fc27.ifca.ai (site will open ~mid-2026)
- **Publisher:** Springer Lecture Notes in Computer Science (LNCS)
- **Conference:** Mar 2–6, 2027 (tentative, location TBA)

### 5.2 Format requirements (from FC'26, stable year-to-year)

| Item | Spec |
|---|---|
| Template | Springer LNCS (`llncs.cls`) — **PDF desk-reject if non-LNCS** |
| Length — regular | **15 pages** + unlimited refs + unlimited appendix |
| Length — SoK | 20 pages + unlimited refs + unlimited appendix |
| Length — short | 8 pages total (no appendix) |
| Review | **Double-blind.** No author names, affiliations, acks, obvious self-references |
| Preprints | **Allowed.** arXiv/ePrint OK; don't cite yourself non-anonymously |
| Abstract | Standard LNCS format, 150–250 words |
| Ethics | Lightweight (describe human-subjects/responsible-disclosure if applicable; N/A for this paper) |

### 5.3 Why FC is the right primary target

- FC'25 accepted "A Formally Verified Lightning Network" (Fabiański et al.) — formal-verification-of-Bitcoin-L2 work.
- FC'25 accepted "A Composability Treatment of Bitcoin's Transaction Ledger" (Garay et al.) — Bitcoin-specific formal model.
- FC'16 BITCOIN workshop: Möser–Eyal–Sirer **"Bitcoin Covenants"** — the direct predecessor of this work; citation is mandatory and signals community lineage.
- FC reviewers include the Bitcoin-Lightning-covenants subcommunity (Avarikioti, Decker, Poelstra, Sonnino, Wattenhofer). They understand BIP numbers without explanation.
- 15 pp + unlimited appendix exactly fits our content budget (theorems + measurements in body, Alloy + tables in appendix).

### 5.4 Framing for FC

**Pitch angle:** "Fee-dependent security tradeoffs in Bitcoin covenant vaults: an impossibility result and a cross-covenant empirical study."

**Suggested paper title:**
> **"The Cost of Custody: Fee-Dependent Security Inversion in Bitcoin Covenant Vaults"**

(Keep the thesis title; it's punchy and matches FC style.)

**Abstract (~200 words):** Lead with the *question* — "Which covenant design is safest?" — then the *answer* — "None universally; the ranking inverts with fee rate." One sentence on empirical method, one sentence on formal method (Alloy), one sentence on Proposition 5.2, one on Theorem 5.3, one on the practical implication (deployment guidance).

**Section priorities (15 pp budget):**

| Thesis → FC paper mapping | Thesis pages | FC pages |
|---|---|---|
| § Introduction | Ch 1 (9 pp) | 1.5 pp (tight) |
| § Background & Covenant Taxonomy | Ch 2 (13 pp, 5 mechanism diagrams) | 2 pp + **1 combined mechanism figure** (drop 4 of 5) |
| § Methodology | Ch 3 (~12 pp) | 1.5 pp |
| § Measurements | Ch 4 (~17 pp, 8 tables) | 3 pp + 2 key tables (fee pinning, watchtower exhaustion) |
| § Security Analysis | Ch 5 (35 pp, 2 theorems, 5 attack figs) | **5 pp** (the heart of the paper: Prop 5.2 + Thm 5.3 + 2D tradeoff) |
| § Formal Models (Alloy) | Ch 6 + App A | 1 pp summary + **full Alloy in appendix** |
| § Discussion | Ch 7 (~6 pp) | 0.5 pp |
| § Related Work | Ch 8 (8 pp) | 1 pp |
| § Conclusion | Ch 9 (~3 pp) | 0.5 pp |
| References | 49 entries | unlimited (keep all) |
| Appendix A: Alloy | Ch 6 + App A | unlimited |
| Appendix B: Full threat matrix | Ch 5 | unlimited |
| Appendix C: Per-experiment vsize data | Ch 4 | unlimited |

**Reviewer concerns and responses:**

| Concern | Mitigation |
|---|---|
| "Measurements are on regtest, not mainnet" | Explicitly section-title the limitation; point to Inquisition signet availability; note CCV testnet deployment (if applicable by 2026) |
| "Unmerged BIPs are speculative" | Cite the active bitcoin-dev discussion; note that covenant-enabled Liquid (Simplicity) is a deployed baseline; frame as "pre-deployment design analysis" |
| "Alloy bounded model checking is not a proof" | Acknowledge; reference Coq/Lean as future work; argue that bounded finding is sufficient for refutation of broad claims |
| "Why not just cite Möser–Eyal–Sirer and call it done?" | M-E-S (2016) predates CTV/OP_VAULT/CCV/CAT+CSFS/Simplicity; our empirical + impossibility results are post-Taproot contributions |

**Actionable pre-submission items (FC-specific):**

- [ ] Download `llncs.cls` v2.24 from Springer (https://www.springer.com/gp/computer-science/lncs/conference-proceedings-guidelines)
- [ ] Port `thesis.tex` → `fc27-paper.tex` using LNCS class
- [ ] Strip VT-specific frontmatter (title page, dedication, committee, acknowledgments)
- [ ] Switch bibliography style from `plainnat` → `splncs04.bst`
- [ ] **Anonymize:** remove Praneeth/Matsuo/Lou/Meng/Virginia Tech/Blacksburg/Arlington mentions from body, acknowledgments, repo URLs, comments; replace "we contributed back to upstream" with "[anonymized contribution]"
- [ ] Replace `\cite{ThesisSelf}` with anonymous reference if needed
- [ ] Compress 10 TikZ figures → 4 (1 per Bitcoin covenant consolidated + 1 attack composite); move 6 to appendix
- [ ] Redraft abstract to 200 words, leading with the theorem
- [ ] Reformat tables to LNCS 2-column-compatible widths
- [ ] Produce a separate `anonymized-appendix.pdf` if artifact/Alloy models are submitted as supplementary
- [ ] Spellcheck with LNCS stylistic conventions (British English acceptable; use consistent tense)

### 5.5 Backup FC submission: **CAAW 2027** (co-located workshop)

If the FC'27 main conference rejects, submit an expanded version to the **Cryptoasset Analytics Workshop (CAAW)** at FC. CAAW is:
- Empirical / measurement-focused
- LNCS format, similar page limit (12 pp typical)
- Single-blind, higher acceptance rate (~35–40%)
- Same Springer proceedings; respectable for a Master's thesis paper
- Deadline typically **mid-Jan 2027** (~6 weeks after FC rejection notification — tight but feasible)

---

## 6. Backup Venue — IEEE ICBC 2028 SoK

### 6.1 Venue snapshot

- **Full name:** IEEE International Conference on Blockchain and Cryptocurrency
- **URL:** https://icbc2028.ieee-icbc.org (TBA)
- **Publisher:** IEEE
- **Conference:** ~May/Jun 2028
- **Note on cycle:** ICBC 2027 deadline was Dec 2026 (likely missed by the time this plan executes); ICBC 2028 is the realistic target

### 6.2 Format

| Item | Spec |
|---|---|
| Template | IEEE 2-column conference template (IEEEtran) |
| Length — SoK | **16 pages** excluding references |
| Length — Full | 8 pages excluding references |
| Length — Short | 4 pages excluding references |
| Review | Double-blind with rebuttal |
| Submission | EDAS |
| Blinding policy | Strict; use third-person self-citation |

### 6.3 Framing for ICBC (SoK track)

**Pitch angle:** "A systematization of Bitcoin covenant vault designs: mechanisms, economics, and security tradeoffs."

**Suggested title:**
> **"SoK: Bitcoin Covenant Vaults — Mechanisms, Economics, and Security"**

(The SoK prefix signals the systematization intent immediately.)

**Why ICBC SoK is a good fit:**
- 16-page limit accommodates 5-covenant comparative structure
- IEEE ICBC regularly accepts Bitcoin L1 work (ICBC'24 had "Bitcoin Inscriptions: Foundations and Beyond")
- SoK track acceptance ~25% (slightly more permissive than full-paper 18%)
- Reviewers are blockchain-specialists, familiar with BIPs
- The thesis is *already* a systematization — ICBC SoK matches natively

**Reframing from FC version to ICBC SoK version:**
- Shift emphasis from "novel impossibility result" → "comprehensive systematization"
- Expand the taxonomy section (2 pp → 4 pp); deepen the historical narrative (BITCOIN'16 → BIP-119 → BIP-345 → BIP-443 → BIP-347)
- Keep Theorem 5.3 + Proposition 5.2 but frame them as *consequences of the systematization* rather than standalone results
- Add a broader comparison table (include Simplicity and cross-reference with Ethereum account-abstraction vaults like Argent/Safe, for reviewer context)
- Strengthen "open problems" section at end (what SoK reviewers look for)

**Actionable items for ICBC:**
- [ ] Convert FC paper → IEEE 2-col format (IEEEtran class)
- [ ] Retitle with "SoK:" prefix
- [ ] Expand Section 2 (Background) and Section 8 (Related Work)
- [ ] Add comparison row for account-abstraction vaults (Ethereum context)
- [ ] Add explicit "Open Problems" and "Future Research Directions" section
- [ ] Submit via EDAS

---

## 7. Stretch Archival — AFT 2027

### 7.1 Venue snapshot

- **Full name:** ACM Advances in Financial Technologies
- **URL:** https://aft.ifca.ai (AFT is ACM but uses IFCA domain)
- **Publisher:** Schloss Dagstuhl LIPIcs (open-access since 2024)
- **Conference:** ~Oct 2027
- **Deadline:** ~May 28, 2027

### 7.2 Format

| Item | Spec |
|---|---|
| Template | **LIPIcs** (NOT ACM sigconf) — `lipics-v2021.cls` |
| Length | **20 pages** main + unlimited refs + unlimited appendix (reviewers optional) |
| Review | Double-blind |
| Open access | Yes; CC-BY license |

### 7.3 Framing for AFT

**Pitch angle:** "Covenant expressivity vs. fee-dependent security is a fundamental L1 blockchain tradeoff. Bitcoin's covenant proposals provide a natural testbed."

**Suggested title (broader, less Bitcoin-specific):**
> **"Fee-Dependent Security Inversion: An Impossibility Result for Covenant-Based On-Chain Vaults"**

**Why the reframe matters for AFT:**
- AFT skews Ethereum/DeFi/MEV (0 covenant papers in 2023–2025)
- Reviewers may treat "Bitcoin BIP catalog" as niche
- Framing the theorem as a **general on-chain property** (applies to any script system with covenant-like introspection + fee pressure) widens the audience
- Use Ethereum account-abstraction wallets as a foil in the Related Work (Argent, Safe, EIP-7702) to signal generality

**Section priorities for AFT (20 pp):**
1. Intro framed as general on-chain tradeoff (1.5 pp)
2. Model: abstract covenant system (not Bitcoin-specific) (2 pp)
3. Impossibility theorems — **front-and-center** (3 pp)
4. Instantiation: 5 Bitcoin covenant designs (3 pp)
5. Empirical validation (3 pp)
6. Cross-system comparison (Bitcoin + Ethereum account abstraction) (2 pp)
7. Deployment guidance (1.5 pp)
8. Related work (2 pp)
9. Conclusion (1 pp)
10. Refs + Alloy + data — all appendix

**Reviewer concerns and responses:**

| AFT concern | Mitigation |
|---|---|
| "This is Bitcoin-specific" | Present the model abstractly first; Bitcoin designs as instantiations |
| "No Ethereum comparison" | Add § Cross-system — briefly treat Argent/Safe/EIP-7702 account-abstraction vaults |
| "Formal methods too light" | Mention Coq/Lean as future work; frame Alloy as exploratory verification |

**Actionable items for AFT:**
- [ ] Download `lipics-v2021.cls`
- [ ] Rewrite §1–§3 with venue-neutral abstract covenant model
- [ ] Add Ethereum account-abstraction comparison section
- [ ] Recompile under LIPIcs — layout differs significantly from LNCS
- [ ] Re-tune figures for single-column LIPIcs layout (wider than LNCS 2-col)

---

## 8. Workshop Fallbacks

### 8.1 CAAW @ FC 2027 (Cryptoasset Analytics Workshop)

- **Deadline:** ~Jan 2027 (post-FC rejection)
- **Format:** LNCS, 12 pp typical
- **Blinding:** Single-blind
- **Accept:** 35–40%
- **Fit:** Strong for the empirical measurements; de-emphasize theorems
- **Framing:** "An empirical fee-dynamics study of Bitcoin covenant vault designs"
- **Action:** If FC rejects Nov 2026 → have CAAW version ready by ~Jan 15, 2027

### 8.2 ACM DeFi @ CCS 2026

- **Deadline:** ~Jul 10, 2026 (earlier than FC — could submit here *first* and still target FC'27 later as extended version)
- **Format:** ACM `sigconf` 2-col, 8 pp excl refs
- **Blinding:** Double-blind
- **Accept:** ~30%
- **Fit:** Strong; DeFi workshop welcomes security/formal-methods work
- **Framing:** "Short workshop paper focusing only on the Fee-Dependent Security Inversion result"
- **Strategy note:** ACM DeFi is compatible with later FC main submission as long as FC version is ≥30% new material. Not recommended as first submission because it locks in an 8-page framing early.

### 8.3 MARBLE 2027 (Mathematical Research for Blockchain Economy)

- **Deadline:** ~Feb 2027
- **Format:** Springer LNCS (post-proceedings)
- **Blinding:** Double-blind
- **Accept:** 30–40%
- **Fit:** Strong for the theorem — MARBLE is a mathematics-of-blockchain venue, and the Fee-Dependent Security Inversion is fundamentally a mathematical-economics result
- **Framing:** "Mathematical analysis of fee-dependent security inversion in on-chain vault designs"
- **Strategy:** Only target MARBLE if FC rejects; the mathematical-economics framing requires substantive rewriting of the abstract and intro

### 8.4 Tokenomics 2026 (International Conference on Blockchain Economics, Security and Protocols)

- **Deadline:** TBD (watch https://tokenomics-conference.lip6.fr/)
- **Format:** Varies — accepts extended abstracts and full papers; dual CS + Economics tracks
- **Accept:** 30–40%
- **Fit:** Moderate; economic framing needed
- **Use case:** If the mathematical-economics angle becomes the paper's thesis

---

## 9. Parallel / Preprint Track

### 9.1 IACR ePrint — POST IMMEDIATELY AFTER DEFENSE

**URL:** https://eprint.iacr.org/
**Deadline:** Rolling (accept takes ~1 week for initial review)
**Target date:** **~May 15, 2026** (2 weeks post-defense)

**Why this matters:**
- Bitcoin research community reads ePrint religiously; posting there = community-wide visibility
- Establishes date-of-record for priority (important if someone else publishes parallel work)
- Does NOT preclude FC or any conference submission — IACR explicitly states "ePrint is not prior publication"
- Gets feedback from the community before formal conference submission
- Commonly cited: "Bitcoin PIPEs v2" (ePrint 2026/186), Poelstra's CAT Schnorr Tricks notes, etc.

**Actionable steps:**
- [ ] Create IACR ePrint account (eprint.iacr.org/register)
- [ ] Prepare "ePrint-submittable" version: can include author names (ePrint is single-blind / de-anonymized by design)
- [ ] 15-page version recommended (same as FC target, non-anonymized) + full appendix
- [ ] Upload PDF + BibTeX-ready metadata
- [ ] Get ePrint ID (e.g., "2026/xyz")
- [ ] Announce on: bitcoin-dev mailing list, Delving Bitcoin, @rubensomsen / @JeremyRubin / Bitcoin Twitter

### 9.2 arXiv — mirror the ePrint submission

**URL:** https://arxiv.org/submit/
**Category:** cs.CR (Cryptography and Security) — primary; cs.DC (Distributed Computing) — secondary
**Target date:** ~May 20, 2026 (after ePrint is live)

**Why both:**
- ePrint: reached by Bitcoin/crypto researchers
- arXiv: reached by general CS community (indexed by Semantic Scholar, Connected Papers)
- Cross-linking: put arXiv link in ePrint, and vice versa

**Actionable steps:**
- [ ] arxiv.org account (institutional email endorsement from VT advisor)
- [ ] Upload same PDF + source tex files (arXiv requires .tex source)
- [ ] Set categories: cs.CR primary, cs.DC secondary
- [ ] Request endorsement if first submission (VT-affiliated ok)
- [ ] ArXiv ID (e.g., `arXiv:2605.12345`)
- [ ] Update ePrint with arXiv cross-link

### 9.3 Delving Bitcoin / bitcoin-dev announcement

**Why:** Bitcoin covenant research community discusses on these forums; announcement drives reviews/feedback.

**Template post:**

> Subject: [Research] The Cost of Custody: Security Tradeoffs and Fee Dynamics in Bitcoin Covenant Vaults
>
> Hi all — I recently completed a Master's thesis comparing 5 covenant vault designs (CTV/BIP-119, CCV/BIP-443, OP_VAULT/BIP-345, CAT+CSFS, Simplicity) through empirical measurement on regtest plus Alloy formal verification.
>
> Key findings:
> - No covenant vault design is universally safest; the safety ranking inverts at a fee rate that scales linearly with vault value (Theorem X).
> - No vault simultaneously achieves permissionless recovery and griefing resistance (Proposition Y).
> - Cross-covenant threat matrix (11 threats × 4 designs).
>
> Preprint: [IACR ePrint link] / [arXiv link]
> Code: github.com/PraneethGunas/...
>
> Feedback welcome — especially from vault implementers.

---

## 10. High-Stretch Targets

These require substantial reframing. Do NOT attempt as first submission.

### 10.1 NDSS 2027 Fall cycle

- **Deadline:** ~Aug 6, 2026 (before FC'27 deadline)
- **Format:** NDSS template, 13 pp + unlimited refs/appendix, 2-col
- **Accept:** 15–16%
- **Why it's a stretch:** NDSS wants attacks on deployed systems, not comparative analysis of unmerged proposals
- **Only viable if:** you extract Fee-Dependent Security Inversion as a **named attack** — "The Fee Inversion Attack: Adversarial Covenant Selection" — with a quantified cost model, an adversary-game definition, and experimental demonstration on Inquisition signet (not just regtest)
- **Recommended action:** skip initially; revisit if FC rejects

### 10.2 IEEE S&P 2027 Cycle 2

- **Deadline:** ~Nov 13, 2026 (abstracts Nov 6)
- **Format:** IEEE `compsoc` IEEEtran, 13 pp + 5 pp refs/appendix
- **Accept:** 15–18%
- **Why it's a stretch:** S&P reviewers are less familiar with Bitcoin script; mechanized proofs (Coq/Lean) are effectively required at this tier
- **Only viable if:** thesis is extended with (a) Coq or Lean mechanization of the impossibility theorems, and (b) an empirical attack demonstration on a live signet
- **Recommended action:** skip; realistic only for a PhD-level extension

---

## 11. Venues to Avoid

Evidence-backed reasons NOT to target these:

| Venue | Reason to skip |
|---|---|
| **USENIX Security** | 0 covenant papers in 2023–2025; reviewers want attacks on deployed systems |
| **ACM CCS main** | Same as USENIX; Bitcoin L1 papers are rare and typically primitive-driven |
| **BITCOIN Workshop (named)** | **Ended in 2018.** No longer exists as a track at FC |
| **Scaling Bitcoin** | **Dormant** since 2019 (Tel Aviv); no new editions |
| **CESC (Crypto Economics Security Conference)** | **Dormant**; last edition 2022 |
| **CES Conference @ MIT** | **Dormant**; last edition 2020. (CES *journal* still accepts — viable archival alternative, not a conference) |
| **ConsensusDay** | No active CFP since ~2023 |
| **Stanford SBC / Science of Blockchain** | **Talk-only, no archival paper.** Good for visibility post-publication, not as a submission target |
| **DeFi Security Summit (DSS)** | **Industry, talk-only.** Distinct from ACM DeFi workshop |
| **Real World Crypto (RWC)** | **Talk-only**; IACR flagship but no proceedings |
| **IOHK internal summits** | Not open CFP |

---

## 12. Framing Matrix

**One thesis, four venue-specific angles.** Use this table when adapting the paper.

| Axis | FC main (primary) | ICBC SoK (backup) | AFT (stretch archival) | MARBLE (econ framing) |
|---|---|---|---|---|
| **Lead with** | Impossibility theorem | Taxonomy + systematization | Abstract model → instantiation | Mathematical economics result |
| **Paper title** | "The Cost of Custody: Fee-Dependent Security Inversion in Bitcoin Covenant Vaults" | "SoK: Bitcoin Covenant Vaults — Mechanisms, Economics, Security" | "Fee-Dependent Security Inversion: An Impossibility for Covenant-Based On-Chain Vaults" | "A Mathematical Model of Fee-Dependent Vault Security" |
| **Framing sentence** | "We prove that no vault is universally safest." | "We systematize 5 covenant designs and their tradeoffs." | "We identify a fundamental L1 security–expressivity tradeoff." | "We give a closed-form characterization of the security crossover fee rate." |
| **Audience assumption** | Knows BIPs, Lightning, Taproot | Blockchain researchers (Bitcoin + Ethereum) | General fintech/financial-crypto | Mathematicians, economists |
| **Bitcoin-specificity** | High (OK) | High (OK) | Low (frame as L1-general) | Low (frame as covenant-abstract) |
| **Empirical emphasis** | Medium | High | Medium | Low |
| **Formal emphasis** | Medium (Alloy) | Low | High (Alloy + future Coq) | High (analytic + Alloy) |
| **Related work emphasis** | Möser–Eyal–Sirer lineage; Lightning formal verification | Full systematization of BIPs + industry | Cross-chain (Ethereum AA, Stark vaults) | Mechanism design, economic incentive papers |
| **Future work ask** | "Mechanized proofs; mainnet measurement" | "Extend to Ethereum AA; more BIPs" | "Generalization to Plutus/Cardano" | "Close-form for multi-user vaults" |
| **Page budget** | 15 | 16 | 20 | 12 |
| **Template** | LNCS | IEEEtran 2-col | LIPIcs | LNCS |

---

## 13. Pre-submission Checklist (Universal)

Items to complete **regardless of venue**:

### Content polish
- [ ] Resolve 5 overfull hboxes in thesis (carry over fixes to paper)
- [ ] Fix BibTeX warning on `covenants_info` entry (add author or key field)
- [ ] Add `\label{}` to all Ch8 related-work sections
- [ ] Spell-check entire paper (`aspell check` or IDE plugin)
- [ ] Grammar pass (consider Grammarly Premium or LanguageTool)
- [ ] Consistency: BIP numbers (119, 345, 443, 347, 348), opcode casing (`OP_CHECKTEMPLATEVERIFY`), vsize units (`\vB`), fee units (sat/vB)

### Anonymization (for double-blind venues)
- [ ] Remove "Praneeth Gunas" from all body text, footnotes, figure credits
- [ ] Replace "Virginia Tech," "Arlington," "Blacksburg" → anonymized
- [ ] Remove committee names (Matsuo, Lou, Meng) from acknowledgments
- [ ] Anonymize GitHub repo URLs: "anonymized-repo.github.io"
- [ ] Replace specific dedication/acknowledgments: delete entire sections
- [ ] Use "we" throughout (not "I"); third-person self-citation

### Artifact / reproducibility
- [ ] README for regtest reproduction (vault-comparison/ already has this)
- [ ] Dockerfile for one-command experiment replay
- [ ] Separate artifact submission PDF (2-page appendix) if venue supports
- [ ] Upload code + data to anonymized Zenodo/figshare for blind review

### Figures & tables
- [ ] All 10 custom TikZ diagrams render correctly at target venue page size
- [ ] Captions are self-contained (readable without body text)
- [ ] Color-blind safe palette check (viridis, okabe-ito)
- [ ] Grayscale-print test (FC prints B&W in proceedings by default)

### Bibliography
- [ ] DOI or URL for every reference
- [ ] Consistent capitalization of paper titles
- [ ] Cross-check with Möser–Eyal–Sirer cite format
- [ ] Include arXiv/ePrint IDs where applicable
- [ ] Venue-correct `.bst`: `splncs04` (FC, MARBLE), `IEEEtran` (ICBC), `plainurl` (LIPIcs/AFT), `ACM-Reference-Format` (CCS DeFi)

### Submission meta
- [ ] 200-word abstract written in the past tense
- [ ] 3–5 keywords matching venue's track categories
- [ ] Author / affiliation (non-anonymous version for camera-ready)
- [ ] Corresponding email
- [ ] Conflicts-of-interest declarations
- [ ] Ethics statement (N/A for this paper, state briefly)

---

## 14. Decision Tree

```
                        START
                          │
                   ▼ Is it May 2026? ▼
                          │
                         YES
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
  Post IACR ePrint   Post arXiv     Start FC'27 draft
          │               │               │
          └───────────────┴───────────────┘
                          │
                          ▼
                  Sep 2026: Submit to FC'27
                          │
                          ▼
                  Nov 2026: FC'27 notification
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
          ACCEPTED               REJECTED
              │                       │
              ▼                       ▼
  Jan 2027: Camera-ready    ┌─────────┴─────────┐
              │             ▼                   ▼
              ▼         Extract attack      Stay comparative
  Mar 2027: Conference      │                   │
              │             ▼                   ▼
              ▼         NDSS'27 Fall        CAAW'27 (Jan)
            DONE        (Aug 2026 —              │
                         already missed          ▼
                         → NDSS'28 Summer    Rejected?
                         Apr 2027)               │
                                                 ▼
                                          ICBC'28 SoK
                                          (Dec 2027)
                                                 │
                                                 ▼
                                          Rejected?
                                                 │
                                                 ▼
                                          AFT'27 (May)
                                                 │
                                                 ▼
                                          Rejected?
                                                 │
                                                 ▼
                                          MARBLE'27
                                          or ACM DeFi'27
```

---

## Appendix: Useful commands

```bash
# Download LNCS template
curl -O https://resource-cms.springernature.com/springer-cms/rest/v1/content/19238648/data/v6

# Count pages in a specific template (estimate before full write)
pdftotext -layout paper.pdf - | wc -l  # rough LOC estimate

# Verify double-blind compliance
grep -i "praneeth\|gunas\|virginia tech\|arlington\|matsuo\|wenjing lou\|na meng" paper.tex

# Compile under LNCS
pdflatex -interaction=nonstopmode fc27-paper.tex
bibtex fc27-paper
pdflatex fc27-paper.tex
pdflatex fc27-paper.tex

# Diff the paper against the thesis for extra-content verification
diff <(pdftotext -layout thesis.pdf -) <(pdftotext -layout paper.pdf -)
```

---

**Last updated:** 2026-04-17
**Status:** Strategy locked; execution begins post-defense (2026-05-01)
