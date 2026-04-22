# Framing Guide — How to Adapt the Thesis for Each Venue

One thesis, multiple conference-specific narratives. Use this document when drafting each submission.

See `SUBMISSION-STRATEGY.md` for overall strategy and `TIMELINE.md` for deadlines.

---

## Framing principles

Every venue has a taste. Reviewers come from a specific community with specific expectations. The same contribution, framed wrong, gets desk-rejected; framed right, it lands in the top 25%.

**Three knobs to tune per venue:**

1. **Generality axis** — Bitcoin-specific (FC, ICBC) vs. L1-general (AFT, MARBLE)
2. **Contribution axis** — impossibility theorem (FC, MARBLE) vs. systematization (ICBC SoK) vs. empirical measurement (CAAW, DeFi workshop)
3. **Formality axis** — rigorous proofs (S&P, MARBLE) vs. measurement-driven (AFT, CAAW) vs. bounded model checking (FC — our comfort zone)

The same paper can lead with any of these by re-ordering sections and adjusting the abstract. The underlying content doesn't change much; framing does.

---

## FC 2027 — Primary target

### Abstract template (200 words)

> Bitcoin covenant proposals — OP_CHECKTEMPLATEVERIFY (BIP-119), OP_CHECKCONTRACTVERIFY (BIP-443), OP_VAULT (BIP-345), and the OP_CAT + OP_CHECKSIGFROMSTACK composition (BIP-347 + BIP-348) — enable self-custody vaults that enforce spending conditions beyond simple signature checks. Four years of active proposal development have produced a design space of competing covenant opcodes, but no systematic comparison of their security properties under realistic fee dynamics has been published.
>
> We present the first comparative analysis of five covenant vault designs (the four Bitcoin proposals plus Simplicity on Elements) through (i) empirical measurement on regtest across fifteen experiments and (ii) bounded model checking of state-machine invariants in Alloy. We prove two design constraints: a Griefing–Safety Incompatibility (no vault simultaneously achieves permissionless recovery and griefing resistance) and a Fee-Dependent Security Inversion theorem (no vault is universally safest; the ranking inverts at a fee rate that scales linearly with vault value). We validate the crossover empirically, showing that CTV, CCV, and OP_VAULT are each optimal in different fee regimes.
>
> Our findings yield fee-conditional deployment guidance for covenant vault operators and identify residual attack surface that requires mitigation before mainnet deployment.

### Opening paragraph (50 words)

> Which Bitcoin covenant design is safest? The question is not hypothetical: four covenant proposals are under active Bitcoin Improvement Proposal review, vault operators must choose among them, and yet no cross-covenant security comparison exists in the peer-reviewed literature.

### Section order (FC-specific rationale)

1. **Introduction** — Lead with the question, not the method. FC reviewers want to know *why* before *how*.
2. **Background** — Assume familiarity with Bitcoin script, Taproot, BIP-68. Define covenants quickly; don't lecture.
3. **Threat model** — Explicitly reference Möser–Eyal–Sirer (BITCOIN'16) as the predecessor. Announce threat taxonomy extensions (TM1–TM11).
4. **Proposition 5.2 (Griefing–Safety Incompatibility)** — Formal statement, proof, corollary.
5. **Theorem 5.3 (Fee-Dependent Security Inversion)** — Formal statement, proof using measured vsize values.
6. **Empirical validation** — 2 key tables (fee pinning cost, watchtower exhaustion splits/block). Refer to appendix for full data.
7. **Formal models** — One paragraph summary; Alloy details in Appendix A.
8. **Deployment guidance** — Fee-conditional recommendations (low-fee → CCV; high-fee → CTV; hot-key-sensitive → CAT+CSFS).
9. **Related work** — Tight. Möser et al. + Swambo et al. as direct predecessors; Lightning-formal-verification as methodological sibling.
10. **Conclusion** — Restate the impossibility result; identify open problems (mainnet measurement, TRUC policy impact).

### What FC reviewers want to see

- **Precise formalism** — Definition 5.1 should use the set-theoretic notation from the thesis (`\mathcal{A}: 2^{\mathcal{K}} \rightarrow \{0,1\}`). No hand-waving.
- **BIP-level technical accuracy** — If you write "OP_VAULT," the reviewer knows what it does. Don't over-explain; do cite BIP-345 correctly.
- **Measurement rigor** — Regtest is acceptable; acknowledge its limitations (single mempool, no propagation race) explicitly.
- **Canonical lineage** — Cite Möser, Swambo, Poelstra, O'Beirne, Ingala, O'Connor. FC reviewers check who's in your bib.

### What FC reviewers will criticize (anticipate in the paper)

- "Unmerged BIPs, what if they change before deployment?" → Address in §Limitations: we study the current spec; BIP updates tracked via git hash.
- "Regtest is not mainnet." → §Limitations: fee pinning requires mempool propagation race, which regtest cannot model; cite signet availability for future work.
- "Alloy is bounded, not a real proof." → §Formal Models: explicit scope; Coq/Lean mechanization listed as future work.
- "How is this different from Möser–Eyal–Sirer?" → §Related Work: M-E-S predates all four BIPs studied here; our empirical/impossibility results are post-Taproot contributions.

### Don't do

- ❌ Don't lead with "This thesis presents..." (academic tone for a thesis, not a paper)
- ❌ Don't include the VT title page, dedication, acknowledgments, committee, keywords list
- ❌ Don't cite yourself as "Gunas 2026" (thesis) — use third-person where needed, avoid self-outing
- ❌ Don't include the 35-page Ch5 verbatim — the FC version needs to be *punchier*
- ❌ Don't skip related work — FC reviewers care about community continuity

---

## ICBC 2028 SoK — First backup

### Title
> **SoK: Bitcoin Covenant Vaults — Mechanisms, Economics, and Security**

### Abstract (200 words)

> Over four years, four Bitcoin Improvement Proposals have introduced covenant opcodes enabling spending conditions beyond signature checks: OP_CHECKTEMPLATEVERIFY (BIP-119), OP_VAULT (BIP-345), OP_CHECKCONTRACTVERIFY (BIP-443), and the OP_CAT + OP_CHECKSIGFROMSTACK composition (BIP-347 + BIP-348). Each proposal targets the same vault-custody use case but with distinct introspection models, recovery authorization schemes, and fee mechanics. The community lacks a systematic treatment of how these designs differ.
>
> This SoK provides the first comprehensive systematization of Bitcoin covenant vault proposals. We organize the design space across four axes — introspection granularity, recovery authorization, fee model, and formal semantics — and place each proposal within it. Through empirical measurement of reference implementations and formal analysis in Alloy, we characterize the security consequences of each design choice and prove two cross-design constraints: a Griefing-Safety incompatibility and a Fee-Dependent Security Inversion.
>
> We also survey Elements' Simplicity as a typed-functional alternative and connect our findings to Ethereum's account-abstraction vaults (EIP-7702, Argent, Safe), enabling future cross-chain comparisons. Our systematization informs deployment guidance and identifies open research problems.

### Key differences from FC version

| Dimension | FC version | ICBC SoK version |
|---|---|---|
| Emphasis | Impossibility theorems | Taxonomy + systematization |
| Background section | 2pp | 4pp (expand + historical narrative) |
| Related work | 1pp | 2pp (include Ethereum account abstraction) |
| Comparison table | 4-covenant threat matrix | 5-covenant + Ethereum AA comparison |
| Open problems section | Brief | Full section — SoK reviewers expect this |
| Code / artifacts emphasis | Medium | High (add to contribution statement) |

### SoK-specific reviewer expectations

- A 10-row "comparison table" that fits on one page (this is THE standard SoK fixture)
- A historical narrative: when was each BIP proposed, what motivated it, what's its current status
- Explicit "what the community has learned" paragraphs
- An "Open Problems" section with 4–6 numbered items

### Actionable re-framing steps

1. Retitle with `SoK:` prefix
2. Expand background (add 2pp on BIP history: BIP-119 → BIP-345 → BIP-443)
3. Add comparison column: Ethereum AA (Argent/Safe/EIP-7702)
4. Restructure §Security as "Systematic analysis of 11 threat models × 5 designs"
5. Convert conclusion to "Open Problems" — 6 items:
   1. Mainnet-deployed covenant measurement
   2. Mechanized proofs (Coq/Lean) of impossibility
   3. Recursive covenant design space
   4. TRUC/v3 interaction with fee pinning
   5. Cross-chain covenant generalization
   6. Watchtower incentive-compatibility

---

## AFT 2027 — Stretch archival

### Title
> **Fee-Dependent Security Inversion: An Impossibility Result for Covenant-Based On-Chain Vaults**

### Why the title shift matters

AFT's reviewer pool is ~70% Ethereum/DeFi researchers. "Bitcoin Covenant Vaults" signals niche specialization; "Covenant-Based On-Chain Vaults" signals general-interest result that happens to be instantiated in Bitcoin. Same content, ~5x broader reach.

### Abstract (200 words, recast for general blockchain audience)

> Smart-contract vaults — time-delayed spending escrows with permissionless recovery — are a recurring pattern across blockchain systems. Their security depends not only on cryptographic primitives but on transaction fee dynamics: an on-chain vault's resistance to theft depends on whether the defender's recovery transaction can outbid or outpace the attacker's transaction.
>
> We prove two fundamental constraints on covenant-based on-chain vault security. First, no vault simultaneously achieves permissionless recovery (anyone can invoke recovery) and griefing resistance (no unauthorized party can disrupt the owner's withdrawal). Second — our Fee-Dependent Security Inversion theorem — no vault design is universally safest; the safety ranking inverts at a fee rate that scales linearly with the vault's value.
>
> We instantiate our analysis over Bitcoin's four active covenant proposals (BIP-119, BIP-345, BIP-443, BIP-347+BIP-348) plus Simplicity on Elements, measuring their transaction sizes empirically and validating the theoretical crossover. We connect our findings to Ethereum account-abstraction vaults (Argent, Safe, EIP-7702), showing that similar tradeoffs appear across L1 designs. Our impossibility results inform vault design decisions for any blockchain with covenant-like introspection.

### Structural reshape

**AFT version leads with the model, not the instantiation.**

- §1 Introduction — General on-chain vault problem; teaser of both theorems
- §2 Formal model — **Abstract covenant system** (define introspection, authorization, fee model generically)
- §3 Impossibility Theorem 1 (Griefing-Safety) — Proved over the abstract model
- §4 Impossibility Theorem 2 (Fee-Inversion) — Proved over the abstract model
- §5 Bitcoin instantiation — Brief (2pp): CTV, CCV, OP_VAULT, CAT+CSFS, Simplicity
- §6 Empirical validation — Measurements
- §7 Ethereum connection — EIP-7702, Argent, Safe as parallel instantiations
- §8 Related work
- §9 Conclusion

### What AFT reviewers want

- General-interest introduction
- Abstract model *first*, concrete instantiations *after*
- Cross-chain connection (not only Bitcoin)
- LIPIcs format (open-access, CC-BY license)

### AFT-specific format changes

- LIPIcs one-column layout (not LNCS two-column)
- Figures can be wider
- Bibliography uses `plainurl` style
- CC-BY license statement required

---

## MARBLE 2027 — Mathematical-economics framing

### Title
> **A Mathematical Model of Fee-Dependent Vault Security**

### Why MARBLE is a fit

The Fee-Dependent Security Inversion theorem is fundamentally a mathematical-economics result: a closed-form characterization of a crossover point `r*(V) = V / (vsize_rec × B_max × S)` where `V` is vault value, `vsize_rec` is recovery transaction size, `B_max` is attacker block-budget, `S` is splits per block. This is exactly the kind of result MARBLE publishes.

### Structural reshape (MARBLE-specific)

- §1 Introduction — Pose the question as a mathematical-economics tradeoff
- §2 Model — Formal definitions: vault, covenant, adversary, fee rate, crossover
- §3 **Closed-form crossover theorem** — Expand Eq. (5) to r*(V, B_max, vsize_rec)
- §4 Comparative statics — How r* changes with V, B_max (sensitivity analysis from thesis Table 5.2)
- §5 Impossibility — Griefing-Safety proposition as a corollary of the model
- §6 Empirical validation — Shorter than FC version
- §7 Related work — Mechanism design, fee-market economics
- §8 Conclusion

### MARBLE-specific sensibilities

- Theorem/Proof environments used liberally
- Every claim gets a numbered equation
- Sensitivity analyses as theorems, not tables
- Economic intuition paragraphs between theorems
- Plots: log-log scaling, asymptotic analysis visible

---

## CAAW 2027 — Empirical workshop fallback

### Title
> **An Empirical Fee-Dynamics Study of Bitcoin Covenant Vault Designs**

### Framing shift

CAAW is the **Cryptoasset Analytics Workshop** — empirical, measurement-driven. If the FC paper's theorem-heavy framing gets rejected ("too theoretical," "no deployed measurement"), CAAW is the place to shift weight toward measurement.

### Structural reshape

- Lead with measurements (Ch4 content)
- Deemphasize the impossibility theorems (move to §4 Observations)
- Expand §Methodology: regtest setup, Docker reproducibility, fee accounting
- Add cost-of-attack plots for fee pinning and watchtower exhaustion
- Cite the ePrint/arXiv preprint for the full theorem (which will be public by then)

### CAAW reviewer expectations

- Reproducible experiments
- Clear data visualizations
- Practical deployment implications
- Less emphasis on theorems, more on "what actually happens"

---

## ACM DeFi @ CCS 2026 — Short-paper alternative

### Title
> **Fee-Dependent Security Inversion in Bitcoin Covenant Vaults**

### Why this is an 8-page paper

ACM DeFi workshop has a strict 8-page limit excluding references. You cannot fit the full thesis analysis; pick **one result** and make it airtight.

### Choose: Theorem 5.3 only

**Structure (8pp):**
1. Introduction (1pp)
2. Background: Bitcoin covenants (1pp — very tight)
3. Threat model: TM1 (fee pinning) + TM4 (watchtower exhaustion) (1pp)
4. Fee-Dependent Security Inversion theorem (2pp — the heart)
5. Empirical validation (1pp)
6. Discussion + deployment guidance (1pp)
7. Related work + conclusion (1pp)

### Strategic note

Submitting to ACM DeFi '26 does NOT preclude FC'27 submission if the FC version is ≥30% new material. Check FC'27 CFP "concurrent submission" clause carefully.

**Recommendation:** Skip ACM DeFi'26 unless you want a fast publication and are willing to forgo FC'27. The FC'27 main paper is archivally stronger.

---

## IACR ePrint — Preprint

### Title (same as thesis)
> **The Cost of Custody: Security Tradeoffs and Fee Dynamics in Bitcoin Covenant Vaults**

### Why ePrint matters in Bitcoin research

Bitcoin protocol developers (Poelstra, Rubin, O'Beirne, Ingala) read ePrint regularly. Posting there:
- Gets your work in front of the people who wrote the BIPs you study
- Establishes priority date (important in a fast-moving field)
- Is **not** prior publication (per IACR policy) — doesn't preclude FC/AFT/NDSS submission
- Typical visibility: 100+ downloads in the first month for Bitcoin papers

### What to post to ePrint

The **non-anonymized**, **complete** version. Include:
- Full thesis-length content (you can be generous with page count)
- All Alloy models
- All measurement tables
- Full bibliography
- Author name + affiliation

### Submission procedure

1. Register account at eprint.iacr.org
2. Fill in metadata: title, authors, keywords, abstract
3. Upload PDF (no page limit, but keep under 100pp for readability)
4. Classify: "Applications → Cryptocurrencies / Blockchain"
5. Wait ~1 week for editorial approval
6. Receive ePrint ID (e.g., `2026/xyz`)
7. Circulate the ID via bitcoin-dev, Delving Bitcoin, Twitter

### Can I have 2 versions (anonymized FC + non-anon ePrint)?

Yes, and this is standard. The FC submission is anonymized; the ePrint is not. FC'27 (and most venues) explicitly allow preprints of non-anonymized versions.

---

## Quick framing cheat-sheet

**If the venue is Bitcoin-native (FC, ICBC, CAAW):**
- Lead with "Which Bitcoin covenant is safest?"
- BIP numbers in abstract
- Cite Möser–Eyal–Sirer early
- Möser, Rubin, O'Beirne, Ingala in related work

**If the venue is blockchain-general (AFT, MARBLE, Tokenomics):**
- Lead with the abstract on-chain tradeoff
- Mention Ethereum AA (Argent, Safe, EIP-7702) in related work
- Abstract model before Bitcoin instantiation
- Connect to mechanism design / game theory

**If the venue is top-tier security (NDSS, S&P):**
- Lead with a concrete named attack
- Adversary-game formalism
- Mainnet or signet demonstration (not regtest)
- Mechanized proof (Coq/Lean), not Alloy
- **Do not submit as-is. Requires PhD-level extension.**

**If the venue is a workshop (CAAW, ACM DeFi, Tokenomics):**
- Pick one result, make it airtight
- Tight page limits — edit ruthlessly
- Full paper goes to ePrint for the complete version

---

**Last updated:** 2026-04-17
