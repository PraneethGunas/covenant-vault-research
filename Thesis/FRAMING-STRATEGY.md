# Research Framing Strategy

## Core Positioning

The BIPs tell you what each vault does. This work proves that no vault can do everything, measures exactly what each one costs, and shows that the safest choice depends on a parameter (fee rate) that the BIPs don't analyze.

---

## Contribution Tiers

### Tier 1: Genuinely Novel (cannot be derived from any BIP)

1. **Fee-Dependent Security Inversion (Theorem 2).** The relative safety ordering of CTV vs CCV/OP_VAULT inverts with the fee environment. CTV's fee-invariant fee-pinning vulnerability dominates at low fees; CCV/OP_VAULT's per-UTXO recovery-cost scaling dominates at high fees. Crossover at ~50 sat/vB for a 0.5 BTC vault. No BIP, mailing list post, or prior paper demonstrates this.

2. **Griefing-Safety Impossibility (Theorem 1).** No covenant vault simultaneously achieves permissionless recovery and griefing resistance. Recovery is either keyless (enabling griefing) or key-gated (creating key-loss risk). Swambo et al. identified the tension qualitatively; this work formalizes it as a provable design constraint with an exhaustive case-based proof.

3. **OP_VAULT Vsize Correction.** Prior hand-estimates suggested ~200 vB triggers. Measured: 292 vB. A 46% error in the only numbers anyone had. OP_VAULT's lifecycle is 36% more expensive than CCV's — not previously quantified.

4. **CCV Splits/Block Correction.** Harding estimated ~3,000 splits/block based on OP_VAULT-sized transactions. CCV's smaller trigger_and_revault yields ~6,172 splits/block — 80% more than assumed.

5. **Two-Dimensional Security Tradeoff Space.** Griefing resistance and fund safety under key loss are anti-correlated across the CTV/CCV/OP_VAULT triple. CAT+CSFS occupies a distinct position (strongest hot-key resistance, weakest cold-key safety) that doesn't fit a single-axis ranking.

### Tier 2: Novel Synthesis (individual facts known, combination is new)

6. **Parameterized Attack Cost Functions.** BIPs say "fee pinning is possible." This work says: fee pinning costs 2,640r + 13,104 sats, is rational whenever vault > 20,000 sats, and remains below 3% of vault value at any historical fee rate. Quantitative risk models, not qualitative warnings.

7. **Cross-Design Comparison Under Uniform Methodology.** The first four-way empirical comparison of CTV, CCV, OP_VAULT, and CAT+CSFS. Each BIP is written in isolation; no single document compares all designs side-by-side with measured data.

8. **CAT+CSFS Cold Key Recovery Analysis.** The unconstrained recovery path (bare OP_CHECKSIG) means cold key compromise is immediate total theft. The cross-covenant security ranking and the Poelstra-style reset cost model are novel.

9. **Deployment Guidance by Fee Regime.** Low fees (< 10 sat/vB): CCV or OP_VAULT. High fees (> 100 sat/vB): CTV. Mixed/uncertain: OP_VAULT. No prior work provides fee-conditional deployment recommendations.

### Tier 3: Verification (confirms BIP-specified behavior — lowest novelty)

10. Address reuse (CTV commits to input count — BIP-119 §4)
11. CCV mode bypass (undefined modes trigger OP_SUCCESS — BIP-443 text)
12. CAT+CSFS hot key theft prevention (follows from Schnorr construction)
13. CAT+CSFS witness manipulation resistance (follows from SHA256 collision resistance)
14. CAT+CSFS destination lock (follows from sha_single_output embedding)

These are implementation correctness checks, not findings.

---

## Framing Principles

### Lead with impossibility results, not experiments

Open with: "We prove that no covenant vault simultaneously achieves permissionless recovery and griefing resistance (Theorem 1), and that the security ordering of existing designs inverts with the fee environment (Theorem 2)."

The experiments are evidence for the theorems, not the contribution themselves. The experiments measure vsize; the theorems use those measurements to derive fundamental constraints.

### Frame experiments as measurement infrastructure

Instead of: "We discovered that CTV is vulnerable to descendant-chain pinning."

Write: "We measure the cost of the descendant-chain pinning attack identified by [Optech, Zhao] at 2,640r + 13,104 sats, and show this cost remains below 3% of vault value at all historical fee rates (1-500 sat/vB), making it the fee-environment-invariant vulnerability in the design space."

The experiment isn't the contribution. The parameterized cost function derived from the experiment is.

### Kill or demote verification experiments

Tier 3 experiments (M, N, I, O, and parts of B) confirm what the BIP spec says. Options:

- **Best:** Consolidate into a single "Implementation Correctness" appendix section. One paragraph: "We verified that the reference implementations correctly enforce BIP-specified behavior across N test vectors."
- **Acceptable:** Keep them but tag explicitly as verification with zero novelty claim.
- **Worst:** Present alongside genuine findings as if they're equal contributions.

### The comparison IS the contribution

Individual measurements (CTV lifecycle = 368 vB) are derivable from reading the code. What's not derivable:

- The side-by-side comparison under a uniform methodology
- The delta between designs (OP_VAULT is 36% more expensive than CCV)
- The crossover analysis (safest design depends on fee environment)
- The impossibility results (emerge from comparing all designs, not any single one)

---

## Suggested Paper Structure

```
1. Introduction
   - "No universally safest vault design exists" (Theorem 2)
   - "Recovery and griefing resistance are incompatible" (Theorem 1)
   - Contributions: impossibility results + measurement framework

2. Background
   - Vault lifecycle model (Swambo et al.)
   - BIP summaries (brief — CTV, CCV, OP_VAULT, CAT+CSFS)
   - Threat taxonomy (8 models, extending Swambo)

3. Measurement Methodology
   - Adapter framework design
   - Regtest validity analysis (vsize is structural, fees are artifacts)
   - Vsize as primary metric; fee projection model
   - This section is INFRASTRUCTURE, not contribution

4. Empirical Results
   - Lifecycle costs (the NUMBERS — Table 1)
   - OP_VAULT overhead correction (292 vs ~200 estimated)
   - CCV splits/block correction (6,172 vs ~3,000 Harding estimate)
   - Batching efficiency (CCV: 106 vB marginal, ~1,600 vault ceiling)
   - These are DATA that feed the theorems

5. Security Analysis (THE CONTRIBUTION)
   - Theorem 1: Griefing-safety impossibility
   - Theorem 2: Fee-dependent security inversion
   - Corollary: Deployment guidance by fee regime
   - Attack cost functions parameterized by measured vsize
   - Cross-covenant threat model matrix (TM1-TM11)

6. Formal Verification
   - Alloy bounded model checking (structural reachability)
   - 12 verified properties, key counterexamples
   - Three-layer evidence: Alloy (possible?) -> Regtest (how much?) -> Fee model (rational?)

7. Discussion
   - Limitations (regtest, reference implementations, rational adversary)
   - Mitigations (TRUC/v3, batched recovery, key management)
   - Open problems (TLA+ for races, Tamarin for crypto)

8. Related Work

9. Conclusion
```

Key shift: experiments are in §3-4 (methodology + data). The contribution is in §5-6 (what you prove using that data).

---

## Answering "Why Not Just Read the BIPs?"

### Short answer
The BIPs tell you what each vault does. We prove that no vault can do everything, measure exactly what each one costs, and show that the safest choice depends on a parameter (fee rate) that the BIPs don't analyze.

### Long answer
Reading BIP-119 tells you CTV commits to input count. It does not tell you:
- That this makes the lifecycle 36% cheaper than OP_VAULT's
- That this creates a fee-invariant pinning vulnerability costing < 3% of vault value
- That this vulnerability is LESS dangerous than CCV's per-UTXO recovery-cost scaling above 50 sat/vB
- That no design can avoid both vulnerabilities simultaneously

These are cross-design, quantitative, and impossibility results. They require uniform measurement across implementations, parameterized cost modeling across fee environments, and formal argument across the design space. No single BIP provides any of this.

---

## What Prior Work Established vs. What This Work Contributes

### Prior work (we quantify, not discover)
- Vault lifecycle model and threat vocabulary — Swambo et al. [SHMB20]
- Keyless recovery griefing as inherent CCV property — Ingala [Ing23]
- Fee pinning via descendant chains, TRUC/v3 mitigation — Zhao
- Authorized recovery tradeoff, watchtower fee exhaustion estimates — O'Beirne/Sanders, Harding [Har24]
- CAT-based transaction introspection via dual signature verification — Poelstra [Poe21]

### This work contributes
1. First four-way empirical comparison with measured vsize (correcting prior estimates)
2. Fee-dependent inversion of security rankings (Theorem 2)
3. Griefing-safety impossibility (Theorem 1)
4. Parameterized economic models extending Harding with variable fractions, batching, spend-delay sensitivity
5. Structural verification via bounded model checking (Alloy)
6. Deployment guidance conditional on fee environment

---

## One-Sentence Pitch Variants

**For a security venue (IEEE S&P, USENIX Security, CCS):**
"We prove two impossibility results for covenant vault security — recovery/griefing incompatibility and fee-dependent safety inversion — and validate them with the first empirical four-way comparison and bounded model checking of BIP-specified vault protocols."

**For a cryptocurrency venue (FC, AFT):**
"As Bitcoin begins signaling for the CTV+CSFS soft fork, we provide the first quantitative vault comparison across four covenant designs, proving that no design is universally safest and delivering fee-conditional deployment guidance."

**For a formal methods venue (FM, CAV):**
"We extend Alloy-based bounded model checking from a single OP_CAT vault prototype to three BIP-specified covenant protocols, combining structural verification with empirical measurement and economic modeling in a three-layer evidence methodology."
