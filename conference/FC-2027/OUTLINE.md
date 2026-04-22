# FC 2027 Paper — Detailed Outline

**Target:** 15 pages (LNCS). References unlimited. Appendix unlimited.

Page budget is *tight*. Over the 15pp main body, every paragraph earns its place.

---

## Page budget allocation

| Section | Pages | Role |
|---|---|---|
| Title + Abstract + Keywords | 0.5 | Venue-required header |
| §1 Introduction | 1.5 | Motivation, contribution summary, roadmap |
| §2 Background & Threat Model | 2.0 | Covenant taxonomy; TM1–TM11 summary |
| **§3 Impossibility Results** | **3.0** | **Paper's core — Prop 5.2 + Thm 5.3** |
| §4 Empirical Validation | 3.0 | Methodology snapshot + 2 key tables + crossover plot |
| §5 Deployment Guidance | 1.5 | Fee-conditional practitioner recommendations |
| §6 Related Work | 1.0 | Möser–Swambo–Rubin–Poelstra lineage |
| §7 Discussion & Limitations | 1.0 | Regtest scope, bounded verification, open problems |
| §8 Conclusion | 0.5 | Restate; forward-look |
| **Total main body** | **14.0** | Leaves 1pp float buffer |
| References | unlim | ~45–55 entries |
| Appendix A (Alloy details) | unlim | Full model source + assertions |
| Appendix B (Threat Matrix) | unlim | 11×4 full matrix with severity |
| Appendix C (Measurements) | unlim | Per-experiment vsize tables |

---

## §0 Title, Abstract, Keywords

### Title

> **The Cost of Custody: Fee-Dependent Security Inversion in Bitcoin Covenant Vaults**

Running title:
> Fee-Dependent Security Inversion in Covenant Vaults

### Abstract (200 words, structured)

Target ~200 words. Structure: problem → approach → result 1 → result 2 → validation → implication.

Draft:

> **Problem.** Bitcoin covenant proposals — OP_CHECKTEMPLATEVERIFY (BIP-119), OP_VAULT (BIP-345), OP_CHECKCONTRACTVERIFY (BIP-443), and the OP_CAT + OP_CHECKSIGFROMSTACK composition (BIP-347 + BIP-348) — enable self-custody vaults that enforce spending conditions beyond signature checks. Four years of active development have produced a design space of competing opcodes, but no systematic cross-design security comparison has been published.
>
> **Approach.** We present the first comparative security analysis of five covenant vault designs (four Bitcoin proposals plus Simplicity on Elements) combining empirical measurement on regtest (15 experiments) with bounded model checking in Alloy (41 assertions).
>
> **Results.** We prove two design constraints. First, a Griefing–Safety Incompatibility: no vault simultaneously achieves permissionless recovery and griefing resistance. Second, a Fee-Dependent Security Inversion: no vault is universally safest; the safety ranking inverts at a fee rate \(r^*\) that scales linearly with vault value.
>
> **Validation.** We measure transaction sizes across all five designs, compute \(r^*\) empirically (≈66 sat/vB for a 0.5 BTC vault), and demonstrate the crossover numerically.
>
> **Implication.** Our results yield fee-conditional deployment guidance for vault operators and expose residual attack surface that requires mitigation before mainnet deployment.

### Keywords (LNCS requires 3–5)

> Bitcoin · covenants · vault custody · formal verification · fee economics

---

## §1 Introduction (1.5 pp)

**Purpose:** Motivate the question; commit to the contribution; establish stakes.

### Paragraph 1 (3–4 sentences) — The question

Lead with the practitioner's dilemma:
- Four Bitcoin covenant proposals under active review
- Vault operators must choose among them
- No peer-reviewed cross-design security comparison exists

### Paragraph 2 (4–5 sentences) — Why it's hard

- Covenants differ in introspection model (output-hash vs. per-output vs. sighash-preimage)
- Different recovery authorization (keyless vs. key-gated)
- Different fee mechanics (anchor CPFP vs. fee wallet vs. SIGHASH_SINGLE)
- These differences create *qualitatively different* attack surfaces
- A single "safest" design cannot be named without specifying the fee environment

### Paragraph 3 (3–4 sentences) — Our approach

- Empirical measurement: 15 experiments × 5 designs on regtest
- Formal: bounded model checking of state machines in Alloy
- Analytical: derive closed-form constraints that hold regardless of implementation detail

### Paragraph 4 — Contribution summary (bulleted, 4 items)

1. **Proposition (Griefing–Safety Incompatibility):** No vault simultaneously achieves permissionless recovery and griefing resistance (Section 3.1)
2. **Theorem (Fee-Dependent Security Inversion):** No vault is universally safest; ranking inverts at \(r^*\) scaling linearly with vault value (Section 3.2)
3. **Empirical measurements** of transaction sizes, attack costs, and crossover fee rate (Section 4)
4. **Deployment guidance** keyed to fee regime and threat priority (Section 5)

### Paragraph 5 — Roadmap

One-sentence description of each section 2–8.

### Figure 1: Safety landscape teaser

A single visual showing the crossover: safety ranking inverts as fee rate rises. Can reuse the fee-inversion pgfplot from thesis § 5.2.

---

## §2 Background and Threat Model (2 pp)

**Purpose:** Enable the reader who knows Bitcoin but not covenants.

### § 2.1 Covenants and introspection (0.5 pp)

- Define covenant formally (introspective script)
- Three introspection models: output-hash, per-output, sighash-preimage
- Recursive covenants: one paragraph; note CTV is non-recursive, CCV is recursive, etc.

### § 2.2 The five covenant designs (0.8 pp)

**Condense five sections of thesis Ch 2 into one compact design table.**

| Design | BIP | Introspection | Recovery | Fee model |
|---|---|---|---|---|
| CTV | 119 | Output-hash | Cold key | Anchor CPFP |
| CCV | 443 | Per-output | Keyless | In-value (no anchor) |
| OP_VAULT | 345 | Purpose-built | recoveryauth key | Fee-wallet input |
| CAT+CSFS | 347+348 | Sighash-preimage | Cold key (unconstrained) | SIGHASH_SINGLE\|ANYONECANPAY |
| Simplicity | — | Typed functional (jet) | Cold key | Elements model |

**One consolidated mechanism figure** — a single 4-panel diagram showing mechanism-at-a-glance for CTV/CCV/OP_VAULT/CAT+CSFS. The thesis has 5 separate mechanism figures; condense to 1 composite.

### § 2.3 Vault lifecycle (0.3 pp)

- Deposit → Trigger → Withdraw / Recover
- Watchtower assumption: monitors chain during CSV
- Reference Swambo et al. (CoRR'20) for baseline model

### § 2.4 Threat taxonomy (0.4 pp)

- 11 threat models inherited/extended from thesis
- Focus on the three dominant: TM1 (fee pinning), TM3 (trigger key theft), TM4 (watchtower exhaustion)
- Full matrix moved to Appendix B

---

## §3 Impossibility Results (3 pp) — **THE CORE**

**Purpose:** The two formal results that make the paper accepted.

### § 3.1 Griefing–Safety Incompatibility (1 pp)

Port Proposition 5.2 verbatim from thesis.

Structure:
1. Definition 3.1 (Recovery Authorization)
2. Proposition 3.2 (Griefing–Safety Incompatibility)
3. Proof — exhaustive case analysis over \(\mathcal{A}(\emptyset) \in \{0, 1\}\)
4. Scope-of-assumption paragraph (cryptographic-only authorization)
5. Table: griefing–safety spectrum (reuse thesis Table 5.1)

### § 3.2 Fee-Dependent Security Inversion (1.5 pp)

Port Theorem 5.3 from thesis.

Structure:
1. Theorem 3.3 statement
2. Proof:
   - Compare fee pinning cost (fee-invariant) vs. watchtower exhaustion cost (decreasing in \(r\))
   - Derive closed-form crossover \(r^*\) from eqs (1)–(4)
   - Numerical crossover at \(V = 0.5\) BTC: \(r^* \approx 66\) sat/vB
3. Corollary 3.4 (No universal safest design)
4. Sensitivity analysis — table for \(V \in \{0.01, 0.1, 0.5, 1, 5, 10\}\) BTC (reuse thesis Table 5.2)
5. Fee-inversion plot — reuse thesis Figure 5.2 (pgfplots, log-scale blocks-to-attack vs. fee rate)

### § 3.3 Two-dimensional security tradeoff (0.5 pp)

- The impossibility results imply a 2D tradeoff space
- Reuse thesis Figure 5.3 (2D scatter: CTV/CCV/OP_VAULT/CAT+CSFS + Simplicity)
- Explain why CAT+CSFS is off the anti-correlated axis
- This observation drives §5 Deployment Guidance

---

## §4 Empirical Validation (3 pp)

**Purpose:** Show that the theorems are not vacuous; the crossover has measurable numerical value.

### § 4.1 Methodology snapshot (0.4 pp)

- Docker-based regtest harness
- Bitcoin node variants: Inquisition (CTV + CAT+CSFS), Merkleize CCV, jamesob opvault, Elements + Simplex (Simplicity)
- 15 experiments × 5 adapters
- Reproducibility: all measurements deterministic; commit hash in appendix

### § 4.2 Transaction sizing (0.6 pp)

One table (reuse thesis Table 4.1 or condense) showing vsize per operation per covenant:
- Vault creation
- Trigger
- Withdraw
- Recovery
- trigger_and_revault (CCV, OP_VAULT only)

Note the CCV recovery = 122 vB (smallest) and OP_VAULT recovery = 246 vB (largest) — drives watchtower exhaustion math.

### § 4.3 Fee pinning attack cost (0.7 pp)

- 25-descendant chain cost ≈ 14,300 sats (fee-invariant)
- Demonstrate on CTV regtest
- Note TRUC/v3 policy impact (future work)
- One figure: descendant chain structure (reuse thesis attack-fee-pinning diagram, condensed)

### § 4.4 Watchtower exhaustion capacity (0.7 pp)

- Compute splits per block: 6,172 (CCV), 3,427 (OP_VAULT)
- Previously estimated 3,000 (Harding 2024) — our measurement shows CCV is 2× worse
- Dust threshold derivation: \(N_{dust}(r) = \lfloor V / (\text{vsize}_{rec} \cdot r) \rfloor\)

### § 4.5 Empirical crossover (0.6 pp)

- Plug measured vsize values into Theorem 3.3
- At \(V = 0.5\) BTC: \(r^* \approx 66\) sat/vB
- Show thesis Fig 5.2 as primary visualization
- Compare to mainnet fee history (median, 95th percentile)

---

## §5 Deployment Guidance (1.5 pp)

**Purpose:** Give practitioners a concrete recommendation.

### § 5.1 Fee-regime recommendations (0.8 pp)

Port the 4-bullet list from thesis § 5.8:
- Low-fee environments (\(r < 10\)): CCV or OP_VAULT preferred
- High-fee environments (\(r > 100\)): CTV preferred
- Mixed/uncertain: OP_VAULT best compromise (note BIP withdrawn → CCV + app-level auth)
- Hot-key priority: CAT+CSFS (note cold-key TM11 caveat)

### § 5.2 Operational considerations (0.4 pp)

- Watchtower reserve sizing formula
- Recovery-budget requirements (\(N \cdot \text{vsize}_{rec} \cdot r\))
- For 0.5 BTC vault at 100 sat/vB defending against 1000 splits: 12.2M sats (0.122 BTC, 24% of vault)

### § 5.3 Pre-deployment checklist (0.3 pp)

Short bulleted list for vault operators.

---

## §6 Related Work (1 pp)

**Purpose:** Establish community continuity.

Port Ch 8 of thesis, heavily condensed to 1 page.

Structure (one paragraph each):

1. **Covenant proposals and analysis** — Möser–Eyal–Sirer (BITCOIN'16), McElrath (SoSF'18), O'Neill et al. (SBC'22), Rubin's MATT essay
2. **Vault-specific prior work** — Swambo et al. (CoRR'20), Van de Velde et al. (bitcoin-dev proposals), O'Beirne OP_VAULT writeup
3. **Formal verification of Bitcoin contracts** — Bhargavan et al. (CSF'20) for BitML; Grin's implementation; "A Formally Verified Lightning Network" (FC'25) — recent methodological sibling
4. **Fee economics and mempool policy** — Lavi–Sattath–Zohar (AFT'19); Huberman et al. (EC'21); Harding's fee-pinning writeup (2024)
5. **Our positioning** — One-sentence "we extend X and depart from Y in Z direction"

---

## §7 Discussion & Limitations (1 pp)

**Purpose:** Anticipate reviewer concerns; show epistemic maturity.

### § 7.1 Limitations (0.5 pp)

- Regtest ≠ mainnet (single mempool, no propagation race)
- Bounded model checking ≠ full proof (Alloy scope limits)
- Unmerged BIPs (specifications may evolve)
- Simplicity on federated sidechain (different trust model)

### § 7.2 Open problems (0.5 pp)

1. Mainnet-equivalent measurement on Inquisition signet
2. Mechanized proofs (Coq/Lean) of Theorem 3.3
3. Impact of TRUC/v3 policy on fee pinning
4. Recursive covenant design space (partial withdrawal beyond CCV)
5. Cross-chain generalization (Ethereum account abstraction as L1 analog)

---

## §8 Conclusion (0.5 pp)

**Purpose:** Land the plane.

Three sentences:
1. What we proved (impossibility results)
2. What it means (no universal safest design; fee-conditional choice)
3. What it opens (mechanized proofs; mainnet measurement; cross-chain comparison)

No new content in conclusion. Just restate.

---

## Figures and Tables inventory

### In body (15 pp)

| # | Type | Content | Source |
|---|---|---|---|
| Fig 1 | Teaser | Fee-safety inversion graph (condensed) | Thesis Fig 5.2 |
| Fig 2 | Composite | 4-panel covenant mechanisms | Thesis Figs 2.2–2.5 consolidated |
| Fig 3 | Plot | Full fee-inversion crossover | Thesis Fig 5.2 |
| Fig 4 | Scatter | 2D security tradeoff | Thesis Fig 5.3 |
| Fig 5 | Attack | Fee pinning descendant chain | Thesis Fig 5.4, condensed |
| Fig 6 | Vertical | Watchtower exhaustion dust cascade | Thesis Fig 5.5, condensed |
| Tab 1 | Taxonomy | 5-covenant design comparison | Thesis Tab 2.1, expanded |
| Tab 2 | Data | Transaction vsize by covenant | Thesis Tab 4.1 |
| Tab 3 | Data | Griefing–safety spectrum | Thesis Tab 5.1 |
| Tab 4 | Sensitivity | \(r^*\) across vault values | Thesis Tab 5.2 |

### Appendix (unlimited)

| # | Type | Content |
|---|---|---|
| App A | Alloy | Full 5 models: ctv, ccv, opvault, catcsfs, simplicity; 41 assertions |
| App B | Matrix | Full 11×4 threat matrix with severity + measured vsize |
| App C | Per-exp | Lifecycle, revault amplification, fee sensitivity per covenant |

---

## References strategy

Start from `thesis.bib` (49 entries already). Target 50–55 entries for the paper.

**Must-cite for FC reviewer signal:**
- Möser, Eyal, Sirer — "Bitcoin Covenants" (BITCOIN'16) — MANDATORY
- Swambo, Hommel, McElrath, Bishop — "Custody Protocols Using Bitcoin Vaults" (CoRR'20)
- BIP-119, BIP-345, BIP-443, BIP-347, BIP-348 — cite all five
- Nakamoto (2008) — Bitcoin whitepaper
- Poelstra — "CAT and Schnorr Tricks" series
- Rubin — OP_CTV draft and MATT writeup
- O'Connor — Simplicity (CoRR'17)
- Deker–Avarikioti — "A Formally Verified Lightning Network" (FC'25) — methodological precedent
- Garay et al. — "Composability Treatment of Bitcoin's Transaction Ledger" (FC'25)

**Consider adding:**
- Harding — "TRUC/v3 Transactions" writeup (2024)
- O'Beirne — "OP_VAULT" writeup
- Ingala — pymatt framework references
- Recent CCV proposals post-BIP-345 withdrawal

---

## Writing priorities (by importance)

1. **§3 Impossibility Results** — This is what FC reviewers accept/reject on. Get this airtight.
2. **§1 Introduction** — Second most important. The abstract + intro decide whether reviewers read §3 carefully.
3. **§4 Empirical Validation** — Supports §3; must be quantitatively specific.
4. **§2 Background** — Standard content; don't waste cycles here until others are solid.
5. **§5 Deployment Guidance** — Differentiator from pure-theory papers. Don't cut.
6. **§6 Related Work** — Signals community continuity. Tight but complete.
7. **§7 Discussion** — Limits + future work. Anticipate reviewer concerns.
8. **§8 Conclusion** — Write last. Keep short.

**Work order:** §3 → §1 → §2 → §4 → §5 → §7 → §6 → §8 → Abstract (last).

---

## Length management

- Keep **paragraph count** constant, tighten each paragraph
- Move tables/figures to **Table column-width** variants (LNCS two-column)
- Push detail to appendices — reviewers are permitted to ignore, which is fine
- If body exceeds 15pp by end of draft: first, cut §2 redundancy; then condense §4 tables; then trim §6

---

**Last updated:** 2026-04-17
