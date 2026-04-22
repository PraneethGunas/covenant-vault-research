# Novelty Analysis — Literature Gap Assessment

Based on exhaustive search of arxiv, ePrint, Delving Bitcoin, bitcoin-dev mailing list, Bitcoin Optech, Blockstream Research, and FC/USENIX/CCS proceedings (2016–2026).

---

## 1. Landscape: What Exists

| Published work | Covers | Does NOT cover |
|---|---|---|
| Swambo et al. (2020, 2023) | Vault lifecycle model, deleted-key covenants, formal treatment | No CTV/CCV/OP_VAULT. No empirical data. No comparison. |
| Swambo, Poinsot (FC 2021) | Attack-tree library for Revault (pre-signed txs) | Revault-specific. No active-key covenants. No cost data. |
| dgpv (Delving Bitcoin, 2024) | Alloy model of ONE vault (Rijndael's OP_CAT) | Only structural properties. No CTV/CCV/OP_VAULT. No fees. No temporal. |
| Bartoletti, Lande, Zunino (ISoLA 2020) | Formal covenant model (BitML) | Predates all modern proposals. No vault-specific analysis. |
| Bartoletti, Zunino et al. (FC 2018) | Formal model of Bitcoin transactions | Predates CTV/CCV/OP_VAULT. No vault analysis. |
| O'Connor, Piekarska (FC 2017) | CSFS-based covenants on Elements Alpha | No comparison across opcodes. No cost measurement. |
| Liu et al. (ePrint 2024/1768) | bitguard: synthesis-aided Bitcoin Script verifier | General script verification. No vault/covenant analysis. |
| Heilman et al. (ePrint 2024/1802) | ColliderScript: covenants via hash collisions | Not practical (~$50M/spend). No vault analysis. |
| Alhabardi et al. (2022) | Agda verification of P2PKH/P2MS scripts | Only basic scripts. No covenant opcodes. |
| Grundmann, Hartenstein (2023, 2025) | TLA+ verification of Lightning Network | Payment channels only. No vaults or covenants. |
| Harding (Delving Bitcoin, 2024) | Watchtower exhaustion estimate (~3,000 splits) | Back-of-envelope. Not measured. Only OP_VAULT-sized. |
| O'Connor (PLAS 2017) | Simplicity language with Coq semantics | Language design. No vault analysis. No contract-level proofs. |
| covenants.info | Qualitative feature matrix (yes/no/?) | Zero quantitative data. No transaction sizes. No costs. No security ranking. |
| BIP-119, BIP-345, BIP-443, BIP-347+348 | Individual opcode specifications | Each in isolation. No cross-comparison. No empirical data. |
| Rijndael (Delving Bitcoin, 2024) | OP_CAT vault proof-of-concept | No security analysis. No cost measurements. No comparison. |
| B-SSL (Delving Bitcoin, 2025) | Covenant-free vault using Taproot+CSV+CLTV | Different category (no new opcodes). No comparison with covenants. |
| [alloc]init (ePrint 2026/186) | Bitcoin PIPEs v2: covenants via witness encryption | Early-stage. No vault implementation. No measurements. |

**The gap is enormous.** No published work provides:
- Multi-covenant empirical comparison with measured transaction sizes
- Formal verification of BIP-specified covenant vault state machines
- Fee-environment-dependent security analysis
- Parameterized attack cost functions across covenant designs
- Cross-chain (Bitcoin + Elements) covenant vault comparison

---

## 2. Timing Context

CTV+CSFS activation signaling started **March 30, 2026**. The ecosystem is actively deciding whether to activate these opcodes.

Key community positions:
- **Antoine Poinsot** (Bitcoin Core): Called the activation push "reckless," demanded "a comprehensive exploration gives confidence a use case is actually realistic in practice" and "something to show."
- **Gregory Sanders** (Bitcoin Core): Rejected time-based ultimatums, proposed alternative P2CTV approach.
- **Anthony Towns**: Noted three years of "public pressure to force adoption on an accelerated timeline."
- **66 developers/firms** signed an open letter requesting Bitcoin Core prioritize CTV+CSFS review.

The debate is drowning in qualitative arguments. covenants.info has checkboxes. Nobody has measured numbers.

---

## 3. Confirmed Novelty Claims

### Claim 1: First empirical multi-covenant comparison

No published work runs CTV, CCV, OP_VAULT, and CAT+CSFS head-to-head on regtest with measured transaction sizes under a uniform adapter interface. All prior work analyzes a single design in isolation or compares designs qualitatively.

Supported by: exhaustive search of arxiv, ePrint, FC/USENIX/CCS proceedings, Delving Bitcoin, bitcoin-dev mailing list. The closest prior work is Swambo et al. (2020), which compares three covenant *enforcement mechanisms* (deleted-key, recovered-key, script-based) theoretically, not four *opcode-level implementations* empirically.

### Claim 2: First formal verification of BIP covenant vault protocols

dgpv's Alloy work covers one vault (Rijndael's OP_CAT prototype, not a BIP). No Alloy, TLA+, SPIN, NuSMV, or any model checker has been applied to BIP-119, BIP-443, or BIP-345 vault state machines. Bartoletti et al.'s formal model predates all current proposals. The Simplicity Coq proofs cover language semantics, not contract-level properties.

Supported by: dgpv's Delving Bitcoin post is the only Alloy analysis of any Bitcoin construct. Alloy's official case studies page has no Bitcoin/blockchain entries. No TLA+ specification of any Bitcoin covenant or vault protocol exists.

### Claim 3: Fee-dependent security inversion is undocumented

No prior analysis shows how security rankings change across fee environments. All prior work discusses attacks at single fee points. The crossover between low-fee regimes (where CCV/OP_VAULT are safer) and high-fee regimes (where CTV's fee-pinning resistance matters less) has not been identified.

### Claim 4: OP_VAULT vsize correction

Prior hand-estimates suggested ~200 vB triggers. Measured: 292 vB (46% error). The 36% lifecycle cost premium over CCV was not previously quantified. This correction matters because OP_VAULT (BIP-345) was withdrawn in favor of CCV (BIP-443) but the economic justification was never published.

### Claim 5: Harding estimate correction

Harding estimated ~3,000 splits/block for OP_VAULT-sized transactions. CCV's smaller trigger_and_revault yields ~6,172 splits/block (80% more). Nobody had measured this because nobody had measured CCV's trigger_and_revault vsize.

### Claim 6: Cross-chain covenant comparison (Bitcoin + Elements)

No prior academic work compares covenant vault designs across Bitcoin and Elements/Liquid. The Simplicity vault with measured lifecycle costs alongside Bitcoin covenant vaults is unique.

---

## 4. Novelty Angles for Framing

### Angle 1: Decision framework for the soft fork debate

Position: "As the Bitcoin ecosystem begins signaling for the CTV+CSFS soft fork with zero quantitative analysis of the vault use case, we provide the first empirical comparison of four covenant vault designs, prove that no design is universally safest, and deliver parameterized deployment guidance as a function of fee environment."

Strength: Timely (activation is live), unique (first empirical comparison), practical (deployment guidance).

### Angle 2: First formal verification of BIP covenant vaults

Position: "We present the first bounded model checking analysis of BIP-specified covenant vault protocols (BIP-119, BIP-443, BIP-345), extending dgpv's Alloy analysis of a single OP_CAT vault to a multi-covenant formal comparison with 12 machine-checked properties."

Strength: Builds on recognized prior art (dgpv). Clear scope extension. Addresses the "no formal verification of any specific BIP covenant design" gap.

### Angle 3: Impossibility results that constrain all future designs

Position: "We prove two impossibility results applicable to any covenant vault design: (1) permissionless recovery and griefing resistance are incompatible, and (2) no design is universally safest — the security ordering inverts at a fee-rate crossover point."

Strength: These are design-space results, not implementation findings. They survive any future covenant proposal.

### Angle 4: Three-layer evidence methodology

Position: "We introduce a three-layer verification methodology for covenant security: bounded model checking (structural possibility), regtest measurement (concrete cost), and fee-parameterized economic modeling (rationality threshold). Each threat model receives evidence at all three layers."

Strength: Novel methodology, not just results. No prior work combines formal + empirical + economic for the same properties.

### Angle 5: Correcting the field's only quantitative estimates

Position: "We provide the first regtest-validated measurements of covenant vault transaction sizes, correcting prior hand-estimates: OP_VAULT trigger 292 vB (vs ~200 estimated), CCV splits/block 6,172 (vs Harding's ~3,000 estimate based on OP_VAULT-sized transactions)."

Strength: Empirical correction of cited numbers. Directly usable by the community.

---

## 5. Experiments That Would Further Strengthen Novelty

### A. Replacement cycling interaction (genuinely unexplored)

Riard's replacement cycling attack (2023) showed mempool manipulation can prevent time-critical Lightning transactions from confirming. The same attack class applies to covenant vaults: an attacker could cycle out a watchtower's recovery transaction during the CSV window. Nobody has analyzed this against covenant vaults — not in any paper, not on Delving Bitcoin, not in any BIP discussion.

### B. TRUC/v3 impact quantification

The community knows TRUC/v3 would mitigate CTV fee pinning. Nobody has quantified by how much. Running the fee pinning experiment with descendant limit = 1 (simulating TRUC) would produce the first measured estimate of TRUC's impact on vault security. Directly feeds the activation debate.

### C. Vault-size sensitivity for Theorem 2

The fee-dependent inversion fixes V = 0.5 BTC. Show how r* shifts with vault size (0.01, 0.1, 1, 10 BTC). Turns a single theorem into a deployment heatmap practitioners can use.

### D. Key rotation cost comparison

Key rotation after suspected compromise differs dramatically across designs:
- CTV: destroy + recreate (full lifecycle cost x 2)
- CCV: re-trigger with new keys (single trigger cost)
- OP_VAULT: recovery + re-vault (recovery + deposit)
- CAT+CSFS: recovery + re-vault (cold key = total theft risk during transition)

No published measurement of rotation costs across covenant designs exists.

### E. Formal CAT+CSFS Alloy model

Adding CAT+CSFS to the Alloy models would:
- Verify the cold key recovery vulnerability (TM11) structurally
- Model the destination lock as a template constraint
- Check the dual CSFS+CHECKSIG binding property
- Extend dgpv's work to a fourth covenant type

---

## 6. What Prior Work Established vs. What This Work Contributes

### Prior work (we quantify, not discover)
- Vault lifecycle model and threat vocabulary — Swambo et al. [SHMB20]
- Keyless recovery griefing as inherent CCV property — Ingala [Ing23]
- Fee pinning via descendant chains, TRUC/v3 mitigation — Zhao
- Authorized recovery tradeoff, watchtower fee exhaustion estimates — O'Beirne/Sanders, Harding [Har24]
- CAT-based transaction introspection via dual signature verification — Poelstra [Poe21]
- Alloy analysis of a single OP_CAT vault — dgpv [dgpv24]
- Simplicity language with Coq-verified semantics — O'Connor [OC17]

### This work contributes
1. First four-way empirical comparison with measured vsize (correcting prior estimates)
2. Fee-dependent inversion of security rankings (Theorem 2) — novel result
3. Griefing-safety impossibility (Theorem 1) — formalizes qualitative observation
4. First bounded model checking of BIP-specified covenant vault protocols (extends dgpv)
5. Parameterized economic models extending Harding with variable fractions, batching, spend-delay sensitivity
6. Three-layer evidence methodology (Alloy + regtest + fee model)
7. Deployment guidance conditional on fee environment
8. OP_VAULT deprecation context (36% cost premium over CCV, quantified)
9. Simplicity vault as cross-chain reference point with federation trust caveats

---

## 7. One-Sentence Pitch Variants

**For a security venue (IEEE S&P, USENIX Security, CCS):**
"We prove two impossibility results for covenant vault security — recovery/griefing incompatibility and fee-dependent safety inversion — and validate them with the first empirical four-way comparison and bounded model checking of BIP-specified vault protocols."

**For a cryptocurrency venue (FC, AFT):**
"As Bitcoin begins signaling for the CTV+CSFS soft fork, we provide the first quantitative vault comparison across four covenant designs, proving that no design is universally safest and delivering fee-conditional deployment guidance."

**For a formal methods venue (FM, CAV):**
"We extend Alloy-based bounded model checking from a single OP_CAT vault prototype to three BIP-specified covenant protocols, combining structural verification with empirical measurement and economic modeling in a three-layer evidence methodology."

---

## Sources

### Academic Papers
- [Moser, Eyal, Sirer — Bitcoin Covenants (FC 2016)](https://maltemoeser.de/paper/covenants.pdf)
- [O'Connor, Piekarska — Enhancing Bitcoin Transactions with Covenants (FC 2017)](https://fc17.ifca.ai/bitcoin/papers/bitcoin17-final28.pdf)
- [Bartoletti, Zunino et al. — Formal Model of Bitcoin Transactions (FC 2018)](https://arxiv.org/abs/1806.09806)
- [Bartoletti, Lande, Zunino — Bitcoin Covenants Unchained (ISoLA 2020)](https://arxiv.org/abs/2006.03918)
- [Swambo et al. — Custody Protocols Using Bitcoin Vaults (2020)](https://arxiv.org/abs/2005.11776)
- [Swambo et al. — Bitcoin Covenants: Three Ways to Control the Future (2020)](https://arxiv.org/abs/2006.16714)
- [Swambo, Poinsot — Revault Risk Framework (FC 2021)](https://arxiv.org/abs/2102.09392)
- [Alhabardi et al. — Verification of Bitcoin Script in Agda (2022)](https://arxiv.org/abs/2203.03054)
- [Swambo — Evolving Bitcoin Custody (PhD thesis, 2023)](https://arxiv.org/abs/2310.11911)
- [Grundmann, Hartenstein — TLA+ Verification of Lightning (2023)](https://arxiv.org/abs/2307.02342)
- [Liu et al. — bitguard: Synthesis-Aided Bitcoin Script Verification (2024)](https://eprint.iacr.org/2024/1768)
- [Heilman et al. — ColliderScript (2024)](https://eprint.iacr.org/2024/1802)
- [Grundmann, Hartenstein — Model Checking Lightning Security (2025)](https://arxiv.org/abs/2505.15568)
- [[alloc]init — Bitcoin PIPEs v2 (2026)](https://eprint.iacr.org/2026/186)
- [O'Connor — Simplicity: A New Language for Blockchains (PLAS 2017)](https://arxiv.org/abs/1711.03028)

### BIPs and Specifications
- [BIP-119: OP_CHECKTEMPLATEVERIFY](https://bips.dev/119/)
- [BIP-345: OP_VAULT](https://bips.dev/345/)
- [BIP-443: OP_CHECKCONTRACTVERIFY](https://bips.dev/443/)
- [BIP-347: OP_CAT](https://bips.dev/347/)
- [BIP-348: OP_CHECKSIGFROMSTACK](https://bips.dev/348/)

### Community Discussions
- [Harding — OP_VAULT comments (Delving Bitcoin, 2024)](https://delvingbitcoin.org/t/op-vault-comments/521)
- [dgpv — Analyzing simple vault covenant with Alloy (Delving Bitcoin, 2024)](https://delvingbitcoin.org/t/analyzing-simple-vault-covenant-with-alloy/819)
- [Rijndael — Basic vault prototype using OP_CAT (Delving Bitcoin, 2024)](https://delvingbitcoin.org/t/basic-vault-prototype-using-op-cat/576)
- [CTV+CSFS: Can we reach consensus? (Delving Bitcoin, 2025)](https://delvingbitcoin.org/t/ctv-csfs-can-we-reach-consensus-on-a-first-step-towards-covenants/1509)
- [BIP 119 CTV Activation Client (Delving Bitcoin, 2026)](https://delvingbitcoin.org/t/bip-119-ctv-activation-client/2242)
- [CTV+CSFS open letter](https://ctv-csfs.com/)
- [Ingala — OP_CHECKCONTRACTVERIFY amount semantic (Delving Bitcoin, 2025)](https://delvingbitcoin.org/t/op-checkcontractverify-and-its-amount-semantic/1527)
- [O'Beirne — Withdrawing OP_VAULT (Delving Bitcoin, 2025)](https://delvingbitcoin.org/t/withdrawing-op-vault-bip-345/1670)
- [B-SSL Covenant-Free Vault (Delving Bitcoin, 2025)](https://delvingbitcoin.org/t/concept-review-b-ssl-bitcoin-secure-signing-layer-covenant-free-vault-model-using-taproot-csv-and-cltv/2047)
- [Riard — Replacement Cycling Attacks (bitcoin-dev, 2023)](https://lists.linuxfoundation.org/pipermail/bitcoin-dev/2023-October/022000.html)

### Tools and Implementations
- [Blockstream — Simplicity GitHub](https://github.com/BlockstreamResearch/simplicity)
- [Blockstream — Simplicity launches on Liquid mainnet (2025)](https://blog.blockstream.com/simplicity-launches-on-liquid-mainnet/)
- [Blockstream — Covenants in Production on Liquid](https://blog.blockstream.com/covenants-in-production-on-liquid/)
- [dgpv — B'SST: Bitcoin Script Symbolic Tracer](https://github.com/dgpv/bsst)
- [Taproot Wizards — purrfect_vault](https://github.com/taproot-wizards/purrfect_vault)
- [covenants.info — Summary Table](https://covenants.info/overview/summary/)
- [Bitcoin Optech — Vaults](https://bitcoinops.org/en/topics/vaults/)
- [Bitcoin Optech — Covenants](https://bitcoinops.org/en/topics/covenants/)
- [Elements Tapscript Opcodes](https://github.com/ElementsProject/elements/blob/master/doc/tapscript_opcodes.md)
