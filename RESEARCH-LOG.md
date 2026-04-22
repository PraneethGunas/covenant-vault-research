# Research Log

**Project:** The Cost of Custody
**Student:** Praneeth Gunas (Virginia Tech, Arlington)
**Defense:** April 29, 2026
**Last updated:** 2026-04-18

Context-preservation document capturing major research decisions,
additions, modifications, and deletions across the thesis, FC 2027
conference paper, experimental framework, and supporting scripts.
Read this first after context compaction.

---

## 1. TL;DR

- Thesis is at **120 pages**, defense-ready.
- FC 2027 paper skeleton is at **19 pages**, framework complete; §1/§2/§4/§6/§7/§8 still need prose fill.
- Title across all documents: **"The Cost of Custody"** (subtitle dropped).
- Core contribution evolved through three framings; the current (Option B) framing is a **4-dimensional structural decomposition of the covenant-vault design space** with feature-to-vulnerability lemmas D1–D4.
- Batched-recovery measurements on regtest surfaced an **ordering-flip finding**: CCV safer than OP_VAULT under single-input recovery, OP_VAULT safer under batched recovery.
- Simplicity reframed throughout as an **"alternative script primitive"** cross-substrate reference point, not a peer of the four Bitcoin proposals.

---

## 2. Framework evolution (three iterations)

### Iteration 1 (original thesis, pre-defense v1.0)
**Framing:** "Fee-Dependent Security Inversion" theorem — the safety ranking of CTV vs CCV/OP_VAULT inverts at fee rate $r^* \approx 50$ sat/vB.
**Status:** Rejected.
**Why rejected:** Conflated *theft* (CTV fee pinning outcome = $V$) with *griefing* (CCV/OP_VAULT per-UTXO recovery-cost scaling outcome = dust lockup + defender fees, not theft). The "ranking inversion" compared apples to oranges and a reviewer could rebut in one sentence.

### Iteration 2 (mid-session refactor)
**Framing:** Introduced `Adversary Advantage` ($\mathrm{Adv}$) and `Defender Loss` ($\mathcal{L}$) as unified metrics; stated "No Pareto-Optimal Design" theorem whose proof enumerates four designs and for each picks a counterexample $(TM, D')$.
**Status:** Superseded by Iteration 3.
**Why superseded:** The "theorem" was a four-case enumeration over opaque designs. A reviewer would say "this is a combinatorial observation, not a theorem." Flagged as W17 in the internal audit.

### Iteration 3 (current — Option B structural decomposition)
**Framing:** Every covenant vault $D = (f, a, g, b)$ makes a choice in four nearly-orthogonal dimensions:
- $f$: fee model (anchor CPFP / fee-wallet / in-value / SIGHASH_ANYONECANPAY)
- $a$: amount flexibility (atomic / partial)
- $g$: recovery gating (keyless / key-gated)
- $b$: recovery binding (bound / unbound)

Four feature-vulnerability lemmas (D1–D4) deterministically map each feature choice to a vulnerability surface. The dominant corner $D^\star = (f_{\neq\text{anchor}}, a_{\text{atomic}}, g_{\text{key}}, b_{\text{bound}})$ has $\mathcal{L} = 0$ across $\{\mathrm{TM1}, \mathrm{TM2}, \mathrm{TM4}, \mathrm{TM11}\}$. No proposed BIP occupies $D^\star$; each is $\geq 1$ Hamming step away, and that step entails a positive $\mathcal{L}$ on the corresponding threat via the lemmas.

**Status:** Current. Thesis §5.2 and paper §3 fully rewritten.
**Why:** Replaces enumeration with structural derivation. Provides a **localisation tool**: any new BIP can be placed in the $(f, a, g, b)$ lattice and its vulnerability profile read off from D1–D4 without running measurements. This is the "extrapolation framework" the user specifically asked for as a contribution to future covenant design and user awareness.

---

## 3. Thesis changes (`Thesis/`)

### Title page & abstract
- **Title:** "The Cost of Custody: Security Tradeoffs and Fee Dynamics in Bitcoin Covenant Vaults" → **"The Cost of Custody"**
- **Keywords:** "Bitcoin covenants, vault custody, transaction introspection, fee-dependent security, formal verification" → **"Bitcoin, Script extensions, vault custody, covenants, formal verification, fee dynamics"**
- **Abstract:** Rewritten to reflect four Script extensions + Simplicity cross-substrate reference, $\mathcal{L}$ metric, No Pareto-Optimal result, batched-recovery ordering flip.
- **General-audience abstract:** Rewritten for accessibility; emphasises tradeoffs over "universal safest" claim; mentions batching ordering flip.
- **Committee:** chair Matsuo, co-chair Lou, committee Meng (already set, unchanged).
- **Location:** Arlington, Virginia, April 29, 2026 (already set, unchanged).

### Ch1 Introduction
- Contribution list expanded from 6 to **7 items**: added formal adversary-advantage framework, per-threat characterisation, batched-defender measurements as standalone contributions.
- Contribution 5 reframed from "Fee-dependent security inversion theorem" → **"Structural design-space decomposition"** with explicit reference to lemmas D1–D4.
- New "Scope" paragraph narrows theorems to four Bitcoin Script extensions; Simplicity = cross-substrate reference.
- Theorem/Proposition references updated across the chapter.

### Ch2 Background
- §2.1 intro paragraph: "five covenant designs" → **"four Bitcoin Script extension proposals + Simplicity as alternative script primitive"**.
- §2.9 Simplicity renamed "Simplicity on Elements" → **"Simplicity on Elements: An Alternative Script Primitive"** with new intro paragraph distinguishing Script extensions from Simplicity's combinator calculus.
- All 5 mechanism diagrams (Fig 2.2–2.6) replaced with custom 2D TikZ diagrams (iterative improvements — layout issues fixed across multiple passes).

### Ch5 Security (largest changes)
- §5.2 retitled "Fee-Dependent Security Inversion" → **"Adversary Advantage and Structural Analysis"**.
- **§5.2.1 Framework** added: Definition 5.2 (per-strategy cost/outcome), Definition 5.3 (Defender loss + Adversary advantage) with **rational-adversary budget $B_A \leq V$** constraint (W20 fix).
- **§5.2.2 Design-Space Decomposition** added: defines $(f, a, g, b)$ dimensions, lists feature values per design.
- **§5.2.3 Feature-Vulnerability Implications** added: Lemmas `lem:anchor_pinning` (D1), `lem:revault_exhaust` (D2), `lem:keyless_grief` (D3), `lem:unbound_theft` (D4) with structural proofs. Includes "Protocol-level vs user-parameter-level" paragraph (W3 corrected framing).
- **§5.2.4 Structural Consequence** added: `Proposition` (label `thm:fee_inversion` reused) replacing the old theorem — now a structural result derived from the lemmas, not enumeration. Table 5.4 `tab:design_space` places each BIP in the lattice. Corollary `cor:open_corner` identifies the dominant corner as unoccupied.
- **§5.2.5 Relationship to Proposition 5.1** added: Proposition 5.1 (Griefing-Safety) reframed as the $(g, b)$ sublattice projection of the 4D framework.
- **§5.2.6 Fee-Rate Sensitivity of TM4** retained from v1 but reframed as a TM4-specific sensitivity analysis, not a standalone theorem.
- §5.4 **§5.4.1 Batched Defender Strategy** added: measured constants $(\alpha, \beta)$ for CCV (54, 68) and OP_VAULT (154, 92) — showing batched $r^\dagger$ rises 1.8× (CCV) and 2.7× (OP_VAULT), and the ordering under TM4 **flips**.
- §5.7 (TM11 Cold Key Recovery) — CAT+CSFS paragraph tightened (overfull hbox fix).
- §5.8 entirely replaced: old 2D scatter plot → **Lemma `lem:projection`** + `Remark rem:asymmetric_binding` + 2×2 lattice diagram showing occupied cells and the unreachable $(g_{\text{keyless}}, b_{\text{unbound}})$ cell (E2 Option B).
- §5.9 Table 5.4 (threat matrix `tab:tm_full`) — all severity labels now uniformly bold; every N/A cell has one-phrase reason (W21 fix).
- §5.1 Proposition 1 now has motivation paragraph before Definition (W5 fix).

### Ch7 Discussion
- Reference to "fee-dependent security inversion" → **"No Pareto-Optimal Design theorem"** → **"Structural design-space decomposition"** (final).
- TRUC paragraph scoped to TM1 branch of enumeration.
- Batched Recovery subsection replaced structural estimates with **measured constants** from regtest Phase 6a.
- Substrate heterogeneity paragraph added (Simplicity cross-substrate framing).
- **TM3 out-of-scope paragraph** added in §7 Limitations (E item): acknowledges TM3 race as network-layer, outside Script-level decomposition; notes existing watchtower formalisations treat confirmation atomically and don't model pinning-composed races; flags CAT+CSFS hot-leaf dual binding as the one Script-level mitigation.

### Ch8 Related Work
- Added 6 missing section labels: `se:rw_vault_custody`, `se:rw_covenants`, `se:rw_formal`, `se:rw_layer2`, `se:rw_qualitative`, `se:rw_positioning`.

### Ch9 Conclusion
- Result 2 reframed from "No Pareto-Optimal" → **"Structural design-space decomposition"**, summarising the four dimensions and pointing to $D^\star$'s dominance.
- "Batched recovery and ordering flip" paragraph added.
- Simplicity paragraph updated to "cross-substrate reference point" framing.
- TRUC future-work bullet scoped to TM1 branch.

### references.bib
- `covenants_info` entry: added `author = {{Covenants.info Contributors}}` (W21 BibTeX warning fix).

### Thesis macro preamble (thesis.tex)
- Added `\opcat`, `\opcsfs`, `\sighash{}` macros (were in FC paper only).

### Custom TikZ diagrams (iteratively improved)
Ch2: 5 mechanism diagrams (CTV, CCV, OP_VAULT, CAT+CSFS, Simplicity). Ch5: 5 attack diagrams (fee pinning, per-UTXO recovery-cost scaling, recovery griefing, trigger key theft, CAT+CSFS cold key theft). All replaced the earlier SVG-converted animations. Multiple rounds of layout fixes for overlapping labels, arrow routing, asymmetric binding visualisation, etc.

---

## 4. FC 2027 paper changes (`conference/FC-2027/paper/`)

### Workspace setup
- Created `conference/FC-2027/` with `README.md`, `OUTLINE.md`, `WRITING-SCHEDULE.md`.
- `paper/` subdir contains LNCS skeleton (`fc27-paper.tex`) + `sections/01-introduction.tex` through `08-conclusion.tex` + three appendix stubs + `references.bib` (copy of thesis) + `SETUP.md` + `.gitignore`.
- Build confirmed via `pdflatex` cycle; LNCS class installed via `sudo tlmgr install llncs` + `aliascnt`.

### Title + abstract
- **Title:** "The Cost of Custody: Fee-Dependent Security Inversion in Bitcoin Covenant Vaults" → **"The Cost of Custody"** (subtitle dropped, running head matches).
- **Abstract:** Rewritten to match thesis abstract's framing. Keywords: "Bitcoin, Script Extensions, Vault Custody, Covenants, Formal Verification, Fee Dynamics".

### §3 Impossibility Results — fully written, core contribution
Mirrors thesis §5.2 structure:
- **§3.1 Framework** (Definitions 1 + 2 with rational-adversary budget)
- **§3.2 Griefing-Safety Incompatibility** (Proposition 1, unchanged from v1)
- **§3.3 Per-Threat Fee Sensitivity** (TM1, TM2, TM3, TM4, TM11 subsections)
- **§3.4 Design-Space Decomposition** (Lemma `lem:feature_vuln` bundling D1–D4; Proposition `thm:no-pareto` derived structurally; Corollary `cor:no-universal` identifying dominant corner; paragraph "Protocol-level vs user-parameter-level" for W3)

Table 3 `tab:pareto-matrix` cleanup: numeric/symbolic values throughout, every zero-loss cell carries a superscript (a–f) justifying the structural reason; single table (per user choice not to split); legend updated.

### Other paper sections
- **§1 Introduction:** scope paragraph added; contribution 5 reframed to match structural decomposition.
- **§2 Background:** Table 1 has "Batching" column; §2.6 **"Simplicity: An Alternative Script Primitive on Elements"** added.
- **§4 Empirical:** §4.7 "Batched-Recovery Measurements" added with measured $\alpha$, $\beta$; "Batching flips the TM4 ordering" paragraph added. §4.8 "Simplicity: A Cross-Substrate Reference" added.
- **§5 Deployment Guidance:** added "Federation-acceptable deployments" bullet + "Watchtower batching" bullet with per-design fee-range multipliers.
- **§7 Discussion:** added "Batching operational complexity", "Substrate heterogeneity", and (today) **"TM3 race dynamics are network-layer"** paragraphs.

### Remaining placeholder sections
§1 intro paragraphs, §2 subsections, §4.1–§4.4 methodology, §6 Related Work paragraphs, §7 remaining limits, §8 Conclusion still have `\todo[inline]{...}` markers pending prose fill from thesis.

### Cross-references
All `Theorem~\ref{thm:fee_inversion}` → `Proposition~\ref{thm:fee_inversion}` via `sed` across ch1, ch4, ch5, ch7, ch9.

---

## 5. Implementation changes (`vault-comparison/`)

### Base adapter (`adapters/base.py`)
- Added `supports_batched_recovery()` capability flag (default `False`).
- Added abstract `recover_batched(states)` method; default raises `NotImplementedError`.
- `capabilities()` dict now exposes `batched_recovery`.

### CCV adapter (`adapters/ccv_adapter.py`)
- Implemented `recover_batched(states)` using pymatt `get_spend_tx` with multiple `(instance, "recover", {out_i: 0})` spends. BIP-443 default aggregation permits this.
- Capability flag set to `True`.
- Added `.. note::` docstring explaining the `out_i=0` single-output simplification and when real watchtowers might want multi-output distribution (W31).

### OP_VAULT adapter (`adapters/opvault_adapter.py`)
- Implemented `recover_batched(states)` using upstream `ov.get_recovery_tx()` with $N$ UTXOs. Uses shared `VaultConfig` (single `recoveryauth` key).
- Capability flag set to `True`.
- **Not implemented:** cross-recovery-group batching (BIP-345 lines 618–621, distinct `<recovery-sPK-hash>` values). Marked W32 in backlog.

### Simplicity adapter (`adapters/simplicity_adapter.py`)
- **Not modified yet.** User wants `recover_batched()` implemented; requires careful reading of simple-simplicity-vault Rust code. Deferred.

### Experiment (`experiments/exp_watchtower_exhaustion.py`)
- Added `_measure_batched_recovery(adapter, result, rpc)` helper.
- Added Phase 6a to main flow: creates $N$ vaults, triggers each, constructs one batched recovery tx, measures vsize. Sweep $N \in \{2, 5, 10, 25, 50\}$.
- Linear regression extracts $(\alpha, \beta)$ from measured points.
- Phase 6 (existing estimate-based analysis) now consumes measured constants when available; falls back to structural estimate otherwise.

### pymatt compatibility patch (`pymatt/src/matt/contracts.py`)
- Python 3.13 strictness: `next_state: 'ContractState' = EMPTY_STATE` rejected as mutable default.
- Fix: `next_state: 'ContractState' = field(default_factory=lambda: EMPTY_STATE)`.
- Added `field` to the `dataclasses` import.
- One-line change; enables running CCV experiments on Python 3.13.

---

## 6. Scripts (`scripts/`)

### `update_paper_from_results.py`
- Created today's session.
- Reads `vault-comparison/results/<timestamp>/watchtower_exhaustion/{ccv,opvault}.json`.
- Extracts Phase-6a linear-fit constants via regex on `observations` list.
- Computes derived values: batched $r^\dagger$, fee-range factors.
- Rewrites LaTeX macros in `fc27-paper.tex` (`\overheadCCV`, `\perinputCCV`, `\overheadOPV`, `\perinputOPV`).
- Rewrites inline `\measured{key}` tokens in section files (4 known keys: `r-dagger-CCV-batched`, `r-dagger-OPV-batched`, `fee-range-factor-CCV`, `fee-range-factor-OPV`).
- Supports `--dry-run`.
- **Regex lesson learned:** Original pattern `[^}]*` failed on nested `\measured{x}` placeholders; fixed to `(?:[^{}]|\{[^{}]*\})*` to permit one level of brace nesting.
- Idempotent: re-running with same data produces no changes.

---

## 7. Measured empirical values (actual numbers)

From `results/2026-04-18_015719/watchtower_exhaustion/ccv.json` and `results/2026-04-18_015842/watchtower_exhaustion/opvault.json`:

| Design | $\alpha$ (vB) | $\beta$ (vB) | Unbatched $r^\dagger$ | Batched $r^\dagger$ | Factor |
|---|---|---|---|---|---|
| CCV | 54 | 68 | 66 sat/vB | 119 sat/vB | 1.8× |
| OP_VAULT | 154 | 92 | 59 sat/vB | 159 sat/vB | 2.7× |

(at $V = 0.5$ BTC, $B_{\max} = 1$ block)

**Ordering-flip finding:** CCV safer than OP_VAULT under single-input recovery (66 > 59); OP_VAULT safer under batched recovery (159 > 119). Driven by OP_VAULT's larger unbatched recovery tx (246 vB vs 122 vB for CCV) amortising disproportionately when batched.

---

## 8. Diagrams (`Thesis/figures/` + inline TikZ)

Ten custom 2D TikZ diagrams replacing earlier SVG-converted animations:

**Ch2 mechanism diagrams:**
1. CTV: vault → unvault tx → two leaves + anchor (Fig 2.2)
2. CCV: per-output check, mode byte, keyless recovery leaf (Fig 2.3)
3. OP_VAULT: three-key separation + fee-wallet requirement (Fig 2.4)
4. CAT+CSFS: dual signature verification + unbound recovery leaf (Fig 2.5)
5. Simplicity: DAG + jet evaluation + compile-time parameter (Fig 2.6)

**Ch5 attack diagrams:**
1. Fee pinning (TM1): 4-phase attack timeline
2. Watchtower exhaustion (TM4): cascading splits → dust threshold
3. Recovery griefing (TM2): loop with γ=0.27 asymmetry callout
4. Trigger key theft (TM3): two parallel race lanes with outcomes
5. CAT+CSFS cold key theft (TM11): hot-leaf safe vs cold-leaf total theft contrast

Multiple iterative fixes for: edge label overlaps, arrow routing through boxes, asymmetric binding visualisation (CAT+CSFS two-leaf structure), 2D tradeoff layout (eventually replaced with lattice in Option B rewrite).

---

## 9. Conference submission strategy (`conference/`)

### Created
- `conference/README.md`, `SUBMISSION-STRATEGY.md`, `TIMELINE.md`, `FRAMING-GUIDE.md`
- `conference/FC-2027/` workspace (see §4)

### Primary target
**Financial Cryptography 2027 main conference**, 15 pp LNCS, double-blind. Deadline ~Sep 15, 2026. Acceptance ~22–25%. Submission portal opens mid-2026.

### Backup cascade
1. CAAW @ FC'27 workshop (~Jan 2027, post-FC-rejection fallback)
2. IEEE ICBC 2028 SoK track (~Dec 2027)
3. AFT 2027 (~May 2027, with structural-result framing for general L1 audience)
4. ACM DeFi Workshop @ CCS 2026 (~Jul 2026, short-paper alternative)

### Parallel
IACR ePrint + arXiv preprint — post ~May 2026 post-defense. Non-anonymised full-length version; establishes priority date; does not preclude FC submission.

### Avoided venues
USENIX Security, IEEE S&P, ACM CCS main (too niche for top-tier systems venues); Scaling Bitcoin, CESC, ConsensusDay (dormant); SBC, DSS, RWC (talk-only, no proceedings).

---

## 10. Build state

| Document | Pages | Status |
|---|---|---|
| `Thesis/thesis.pdf` | **120** | Clean, 3 trivial overfull hboxes (all <8pt), 0 undefined refs |
| `Thesis/thesis_ithenticate.pdf` | **109** | Clean |
| `Thesis/The Cost of Custody.pdf` | 109 | iThenticate upload copy |
| `conference/FC-2027/paper/fc27-paper.pdf` | **19** | Clean, skeleton + filled §3 + partial §2/§4/§5/§7 |

Compilation commands:
```bash
# Thesis
cd Thesis && xelatex thesis.tex && bibtex thesis && xelatex thesis.tex && xelatex thesis.tex

# FC paper
cd conference/FC-2027/paper && pdflatex fc27-paper.tex && bibtex fc27-paper && pdflatex fc27-paper.tex && pdflatex fc27-paper.tex
```

---

## 11. Open backlog

### Ready to execute (no decisions needed)
1. **Paper §1, §2, §4, §6, §7, §8 prose fill** — `\todo{}` markers to replace with prose ported from thesis. ~6–8 hours mechanical work.
2. **§3 trim 5 pp → 3 pp** — compression after §1/§2/§4–§8 are filled. Move per-threat detail to appendix.
3. **Final end-to-end proofread** — one continuous read of thesis + paper after all structural work settles. Catches terminology drift, stale framing references. ~2–3 hrs.

### Needs user decision (deferred to "tomorrow brainstorm")
4. **Simplicity `recover_batched()` implementation** — user asked for this; needs careful reading of `simple-simplicity-vault` Rust code for multi-input tx construction. Two sub-options: (a) modify CLI, (b) wrap Simplex SDK directly.
5. **W32: OP_VAULT cross-recovery-group batching** — BIP-345 lines 618–621. Low priority per user.

### Resolved this session (reference list)
- **W1, W15** (safer undefined) — added $\mathcal{L}$/Adv definitions
- **W2** (theorem scope) — per-threat characterisation
- **W3** (r† implementation vs design) — **corrected framing**: $r^\dagger$ existence is protocol-level, value depends on user parameters ($V$, $N_{\text{budget}}$), BIP-specified $\text{vsize}_{\text{rec}}$
- **W4** (CAT+CSFS missing) — per-threat framing includes it
- **W5** (Proposition 1 motivation) — motivation paragraph added
- **W6** (threshold schemes) — note in Definition
- **W7** (Simplicity hand-wavy) — cross-substrate reference reframing
- **W8** (2D tradeoff asserted) — Lemma projection
- **W9** (Core policy qualifier) — explicit "Bitcoin Core 28.x default relay policy" on D1
- **W10, W11, W12** (citations) — Möser, Swambo, Harding cited and verified
- **W13, W14** (prose polish) — applied
- **W17** (Theorem by enumeration) — Option B structural rewrite
- **W18** (Simplicity in theorem scope) — dropped from $\mathcal{D}$
- **W20** (sup unbounded) — rational-adversary budget $B_A \leq V$ added to Definition
- **W21** (Table 5.4 mix) — uniform bold severity labels, every N/A has reason
- **W22** (paper Table 3 NA semantics) — superscript annotations, single table
- **W25** (abstract update) — rewritten
- **W26** (title misalignment) — simplified to "The Cost of Custody"
- **W27** (CCV β measured) — 68 vB
- **W29** (attacker doesn't benefit from batching) — stated in §4.7 and §5.4.1
- **W30** ($N_{\text{budget}}$ sensitivity) — Defender-budget-interpretation paragraph added
- **W31** (CCV docstring) — note added
- **E1** (Theorem 1 framing) — Option B structural
- **E2** (2D tradeoff) — projection lemma
- **BibTeX `covenants_info`** — author added
- **Ch8 labels** — 6 added
- **Overfull hboxes** — reduced from 5 (max 24pt) to 3 (max 7.5pt)
- **TM3 out of scope** — paragraph added in both documents

### Decisions rejected (with reasoning, for context)
- **E1 Option A (demote to Proposition)** — user chose B (structural derivation) to make it a real contribution, not admission of weakness.
- **E2 Option A (drop 2D plot)** — user chose B (derive via projection lemma) for same reason.
- **Proper-noun naming of framework** — user prefers unnamed ("Just assert for now; giving it names will create biases").
- **W22 split into two tables** — user prefers single table with justifications inline.
- **Pisa / Brick / Ride-Lightning citations** — not added; verified citations would require re-reading those papers, which we haven't done. Prose kept generic ("existing state-channel watchtower formalisations").
- **W32 cross-group batching** — user marked low priority.
- **Simplicity cross-substrate inclusion in theorem scope** — user chose to exclude; Simplicity runs on Elements federated sidechain, threats don't transfer identically.

---

## 12. Future work (for framework paper, not this submission)

Per user: "Come up with a design based security vulnerability extrapolation which can help people think about new covenants that will be built and for users being aware who are using them in the near future (this addition for later)."

The 4-dimensional $(f, a, g, b)$ decomposition is the seed for this. Future contributions:
- **Formal model of the design space:** generalise beyond the four current BIPs to arbitrary covenants defined over introspection + authorisation + amount-flexibility primitives.
- **Dynamic $\mathcal{L}$:** incorporate network-layer race probabilities (TM3) into the Script-layer framework.
- **Machine-verifiable framework:** Coq or Lean formalisation of D1–D4 lemmas plus the design-space proposition.
- **BIP localisation tool:** practitioner-facing utility that takes a BIP draft and outputs its $(f, a, g, b)$ tuple + vulnerability profile.

---

## 13. Key files cross-reference

### Thesis
- Main: `Thesis/thesis.tex`, `Thesis/thesis_ithenticate.tex`
- Chapters: `Thesis/chapters/ch1_introduction.tex` through `ch9_conclusion.tex` + `app_a_alloy.tex`
- Class: `Thesis/VTthesis.cls`
- Bib: `Thesis/references.bib`
- Output: `Thesis/thesis.pdf`, `Thesis/The Cost of Custody.pdf`

### FC 2027 paper
- Main: `conference/FC-2027/paper/fc27-paper.tex`
- Sections: `conference/FC-2027/paper/sections/01-introduction.tex` through `08-conclusion.tex`
- Appendices: `conference/FC-2027/paper/appendix-a-alloy.tex`, `-b-threat-matrix.tex`, `-c-measurements.tex`
- Bib: `conference/FC-2027/paper/references.bib`
- Planning: `conference/FC-2027/README.md`, `OUTLINE.md`, `WRITING-SCHEDULE.md`

### Experimental framework
- Adapters: `vault-comparison/adapters/{base,ccv,opvault,ctv,cat_csfs,simplicity}_adapter.py`
- Experiments: `vault-comparison/experiments/exp_watchtower_exhaustion.py` (Phase 6a), `exp_multi_input.py`, others
- Results: `vault-comparison/results/<timestamp>/<experiment>/<covenant>.json`

### Scripts
- `scripts/update_paper_from_results.py`

### Pymatt (patched)
- `pymatt/src/matt/contracts.py` (Python 3.13 dataclass fix)

---

**End of log.**
