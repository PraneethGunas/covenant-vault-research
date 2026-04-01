# Alloy Models for Bitcoin Covenant Vault Verification

## 1. Module Structure

```
alloy-models/
├── btc_base.als           # Bitcoin UTXO model: Tx, UTXO, Key, Address, Time, CSV
├── vault_base.als         # Abstract vault state machine: VaultUTXO, Transition, VaultFamily
├── threat_model.als       # Attacker capabilities, key definitions, extraction predicates
├── ctv_vault.als          # CTV (BIP-119): 3-state, no revault, address reuse model
├── ccv_vault.als          # CCV (BIP-443): revault loop, keyless recovery, mode confusion
├── opvault_vault.als      # OP_VAULT (BIP-345): authorized recovery, fee wallet, 3-key
├── cat_csfs_vault.als     # CAT+CSFS (BIP-347+348): dual verification, unconstrained recovery
├── simplicity_vault.als   # Simplicity (Elements): outputs_hash, output-constrained recovery
├── cross_covenant.als     # Cross-vault composition: input injection, dust termination
└── ANALYSIS.md            # This file: scope guidance, limitations, property mapping
```

**Why this decomposition (not a flat file):**

Alloy's module system supports `open` for importing signatures and facts. The layered
structure lets you check each vault model independently (faster SAT solving at smaller
scope) while sharing the UTXO graph semantics. The alternative—one monolithic file—would
force the SAT solver to consider all three vault types simultaneously even when checking
CTV-only properties, inflating the state space unnecessarily.

**Import graph:**
```
btc_base ← vault_base ← threat_model ← ctv_vault
                                       ← ccv_vault
                                       ← opvault_vault
                                       ← cat_csfs_vault
                                       ← simplicity_vault
                                       ← cross_covenant (imports ctv + ccv + opv)
```

Each concrete vault module can be analyzed independently. The cross_covenant module
imports ctv_vault, ccv_vault, and opvault_vault for composition analysis with
concrete covenant guards active. CAT+CSFS and Simplicity are analyzed independently.

## 2. Property-to-Assertion Mapping

| # | Property | Module | Assertion | Expected Result |
|---|----------|--------|-----------|-----------------|
| 1 | Fund conservation | vault_base | `fundConservation` | HOLDS (by construction) |
| 2 | No unauthorized extraction | ctv/ccv/opv | `*NoExtraction_NoKey` | HOLDS |
| 2' | Hot/trigger key extraction | ctv/ccv/opv | `*NoExtraction_*Key` | COUNTEREXAMPLE |
| 3 | Recovery destination integrity | vault_base | `recoveryDestinationIntegrity` | HOLDS |
| 4 | Single-spend | btc_base | `singleSpend` | HOLDS (structural) |
| 5 | CSV enforcement | ctv/ccv/opv | `*CSVEnforced` | HOLDS |
| 6 | Eventual withdrawal | ctv_vault | `ctvEventualWithdrawal` | COUNTEREXAMPLE (address reuse) |
| 7 | Recovery always possible | opvault_vault | `opvRecoveryAlwaysPossible` | COUNTEREXAMPLE (key loss) |
| 8 | No state proliferation | ccv/opv | `*BoundedState` | COUNTEREXAMPLE (revault loop) |
| 9 | Cross-vault injection | cross_covenant | `noCrossVaultInjection` | DEPENDS on CCV config |
| 10 | Revault-to-dust termination | cross_covenant | `splittingTerminates` | INSTANCE found |
| 11 | Fee wallet contention | opvault_vault | `opvNoFeeContention` | COUNTEREXAMPLE |
| 12a | Mode confusion bypass | ccv_vault | `ccvNoModeConfusionBypass` | HOLDS (closing axioms) |
| 12b | Mode confusion contained | ccv_vault | `ccvModeConfusionContained` | COUNTEREXAMPLE |
| 13 | CAT+CSFS cold key theft | cat_csfs_vault | `catcsfsNoExtraction_ColdKeyOnly` | COUNTEREXAMPLE (unconstrained recovery) |
| 14 | CAT+CSFS destination lock | cat_csfs_vault | `catcsfsDestinationLock` | HOLDS (dual verification) |
| 15 | CAT+CSFS hot key isolation | cat_csfs_vault | `catcsfsNoExtraction_HotKeyOnly` | HOLDS |
| 16 | Simplicity output binding | simplicity_vault | `simplicityOutputBinding` | HOLDS (all paths) |
| 17 | Simplicity cold key constrained | simplicity_vault | `simplicityNoExtraction_ColdKeyOnly` | HOLDS (output-constrained recovery) |
| 18 | Simplicity hot key isolation | simplicity_vault | `simplicityNoExtraction_HotKeyOnly` | HOLDS |

## 3. Scope Guidance

### 3.1 What Alloy scope means

Alloy's `check ... for N` bounds every top-level signature to at most N atoms. The SAT
solver explores all possible configurations within that bound. This is *sound for the
bounded scope*: if Alloy finds no counterexample within scope N, the property holds for
all instances of size ≤ N. It says nothing about larger instances.

### 3.2 Recommended scopes per property

**CTV properties (no revault — small state space):**
- `check ... for 6 but 5 Int, 8 Time` suffices for all CTV assertions.
- Address reuse needs `exactly 2 CTVVaultFamily` to manifest. Scope 6 is enough.
- CTV's state machine has at most 3 VaultUTXOs per family (deposit, unvaulted, terminal).
  With 2 families: 6 VaultUTXOs. Scope 8 gives comfortable headroom.

**CCV revault/splitting (key challenge):**
- Each revault adds 2 VaultUTXOs (unvaulting + new vault). After N revaults from one
  family: 1 + 2N VaultUTXOs.
- **Scope 3 revaults** (7 VaultUTXOs) → `for 10 but 5 Int, 12 Time`
- **Scope 5 revaults** (11 VaultUTXOs) → `for 14 but 5 Int, 16 Time`
  SAT solving time grows roughly as O(2^scope). Scope 14 is feasible on a modern
  machine with SAT4J (minutes); scope 20+ requires Plingeling.
- **You cannot model 410 splits.** But you don't need to. The structural vulnerability
  (unbounded state growth) is visible at scope 3: Alloy finds that `ccvBoundedState`
  has a counterexample with 3 revaults. The 410-split number is an *economic* threshold
  (how many splits to exhaust a watchtower at 500 sat/vB) — Alloy proves the structural
  *possibility*; your fee sensitivity experiment proves the *economics*.

**OP_VAULT fee wallet contention:**
- Needs `exactly 2 OPVaultFamily` and `exactly 1-2 FeeWalletUTXO`.
- Scope 8-10 suffices. The contention emerges when two families compete for the same
  fee UTXO — only 2 families needed.

**Cross-covenant composition:**
- Needs at least 1 VaultFamily of each type. Minimum scope 8-10.
- The cross-input injection analysis is subtle: it requires modeling both CTV's
  output-only commitment and CCV's taptree enforcement simultaneously.

### 3.3 Int scope and overflow

Alloy uses Java's 2's-complement integers with `N` bits → range [-2^(N-1), 2^(N-1)-1].
With `5 Int`: range [-16, 15]. This is adequate for abstract values (we're checking
structural properties, not exact satoshi arithmetic).

**For fund conservation:** Values represent abstract "units," not sats. A deposit of
value 10 split into 6+4 is representable. We don't need 500,000,000 (5 BTC in sats).

**For splitting depth:** The number of revaults is bounded by the number of
RevaultTransition atoms, not by Int arithmetic. At scope 10, you get up to 10 revaults.

**If you need exact economics:** Don't use Alloy's Int. Instead, model value as an
abstract ordered set with `open util/ordering[Value]` and define conservation as
"output values partition input values." This avoids overflow entirely.

**Int range caveat for splitting results:** With `5 Int` (range [-16, 15]), splitting
results with >3 revaults approach the Int ceiling. The `dustThreshold` returns 2 and
`minViableWithdraw` returns 3, so a deposit of value 10 supports at most 3-4 meaningful
splits before values hit the floor. Results from `splittingTerminates` and
`indefiniteSplitting` at >3 revaults should be interpreted with this limitation in mind.
For higher-fidelity splitting analysis, use `6 Int` (range [-32, 31]) to provide more
headroom, or rely on the analytical fee_sensitivity experiment for exact economics.

### 3.4 Solver choice

- **SAT4J** (built-in): Fine for scope ≤ 10. Available immediately.
- **Plingeling**: 3-5× faster for scope 12+. Install separately.
- **MiniSat**: Good middle ground. Often pre-installed on Linux.

For the revault/splitting analysis at scope 14+, use Plingeling.

## 4. What Alloy Can and Cannot Tell You

### 4.1 In scope for Alloy (bounded model checking)

| Capability | Example in these models |
|---|---|
| State reachability | "Is WITHDRAWN reachable without hot_key?" |
| Invariant violations | "Does fund conservation hold for all reachable states?" |
| Deadlocks | "Is there a state from which no transition is possible?" |
| Structural counterexamples | "Show me a concrete trace where address reuse causes stuck funds" |
| Bounded liveness | "Within N steps, can the owner always withdraw?" |
| Composition conflicts | "Can two vaults interfere via shared resources?" |

### 4.2 Out of scope for Alloy

| Property | Why Alloy can't check it | Better tool |
|---|---|---|
| Probabilistic timing (mempool races) | Alloy has no probability distributions | **PRISM** (probabilistic model checker) |
| Fee market dynamics | Requires continuous-value game theory | **Gambit** or custom game-theoretic analysis |
| Unbounded liveness (LTL/CTL) | Alloy checks bounded traces only | **TLA+/TLC** (supports temporal logic over infinite traces) |
| Cryptographic soundness | Alloy doesn't model hash preimage resistance | **Tamarin** (symbolic crypto protocol verifier) |
| Mempool relay policy | Implementation-specific, not structural | **Bitcoin Core functional tests** (your regtest harness) |
| Exact fee arithmetic (satoshi precision) | Int overflow at realistic values | **Z3/SMT** or **PRISM** with real-valued variables |
| Network-level attacks (eclipse, sybil) | Alloy models state, not network topology | **NS-3** or **Shadow** (network simulators) |

### 4.3 Specific recommendations for your properties

**Property 8 (griefing loop cost ratio):** Alloy can prove the loop *exists* (structural)
but cannot compute the 1.26× cost ratio. Your regtest measurements give the ratio;
Alloy gives the existence proof.

**Property 10 (dust termination):** Alloy can find instances where splitting terminates
AND instances where it doesn't (within bounded scope). The actual dust threshold
(546 sats) requires exact arithmetic — use Z3 or your Python fee sensitivity analysis.

**Property 11 (fee wallet contention):** Alloy is excellent here. The resource contention
is purely structural (two transitions competing for the same input) and doesn't depend
on timing or fees.

**Temporal properties (recovery race):** The race between attacker's withdrawal and
watchtower's recovery is inherently temporal — it depends on transaction propagation
delays, miner inclusion preferences, and fee priority. For this, consider:
- **TLA+** for the abstract race condition (who confirms first?)
- **PRISM** for probabilistic analysis (probability of successful recovery given
  X blocks of delay and Y mempool congestion)

### 4.4 Complementary verification strategy

```
Alloy (structural)     → "Is this attack structurally possible?"
  ↓ if yes
Regtest (empirical)    → "What does this attack cost in vbytes?"
  ↓ cost data
Fee analysis (analytical) → "Is this attack economically rational at fee rate F?"
  ↓ if economically relevant
TLA+/PRISM (temporal)  → "Does the watchtower win the race with probability P?"
  ↓ if probability < threshold
Tamarin (crypto)       → "Does the cryptographic construction actually prevent X?"
```

Your existing framework already covers layers 1-3. Alloy adds layer 0: proving that
the state space your experiments explore is actually complete (no missed states), and
finding structural vulnerabilities in unexplored composition scenarios.

## 5. Model Fixes Applied (Post-First-Run Analysis)

After the initial Alloy run, 7 unexpected counterexamples and 2 unexpected holds were traced
to model under-constraints. Five categories of fixes were applied:

**Fix 1 — Closing axioms (vault_base.als + all three vault modules):**
The base `transitionConsistency` fact used `some` for transition production. Alloy's
open-world assumption meant `WithdrawnUTXO` atoms could exist without being produced by
any `WithdrawTransition`. Fixed by requiring `one` (exactly one) producing transition for
every non-deposit VaultUTXO, plus per-vault closing facts that tie each concrete UTXO
subtype to its corresponding transition type.

**Fix 2 — Family well-formedness (ctv_vault.als, ccv_vault.als, opvault_vault.als):**
Recovery assertions quantified over typed families (e.g., `all f : CTVVaultFamily`) but
`f.allUTXOs` could contain base `VaultUTXO` atoms that weren't CTV-subtyped. Since
`CTVRecover.src` requires `src in CTVUnvaultedUTXO`, no recovery transition could match
a base VaultUTXO, causing the assertion to fail vacuously. Fixed by constraining each
family's `allUTXOs` to contain only UTXO subtypes of the correct vault design.

**Fix 3 — Fee wallet population (opvault_vault.als):**
`opvNoFeeContention` held (no counterexample) because the solver created degenerate models
with empty `FeeWallet.utxos`. Added `fact feeWalletPopulated` requiring `some FeeWallet.utxos`
and updated `opvFeeContentionScenario` to force exactly 1 fee UTXO with 2+ families.

**Fix 4 — Mode confusion assertion rewrite (ccv_vault.als):**
Original `ccvNoModeConfusionTheft` checked whether mode confusion leads to theft at
AttackerAddr. This is the wrong property — mode confusion (OP_SUCCESS) enables arbitrary
script execution, not necessarily theft. Replaced with two assertions:
`ccvNoModeConfusionBypass` (should hold: closing axioms prevent orphan spending) and
`ccvModeConfusionContained` (should find counterexample: OP_SUCCESS voids covenant).

**Fix 5 — allUTXOs transitive closure (vault_base.als):**
`f.allUTXOs` was under-constrained: the solver could add arbitrary VaultUTXOs to a family.
`ctvNoStateProliferation` found spurious counterexamples with multiple VAULTED UTXOs.
Added `allUTXOsClosure` fact requiring every member of `allUTXOs` to be either the deposit
or reachable via a chain of transitions from the deposit.

### Expected impact on re-run

| Previously unexpected result | Fix responsible | Expected new result |
|---|---|---|
| `*NoExtraction_NoKey` counterexamples (CTV/CCV/OPV) | Fix 1 (closing axioms) | HOLDS |
| `ctvNoStateProliferation` counterexample | Fix 5 (allUTXOs closure) | HOLDS |
| `ctvRecoveryAlwaysPossible` counterexample | Fix 2 (family well-formedness) | HOLDS |
| `ccvRecoveryAlwaysPossible` counterexample | Fix 2 (family well-formedness) | HOLDS |
| `ccvNoModeConfusionTheft` held | Fix 4 (assertion rewrite) | Split into two checks |
| `opvNoFeeContention` held | Fix 3 (fee wallet population) | COUNTEREXAMPLE |
| `opvFeeContentionScenario` no instance | Fix 3 (fee wallet population) | INSTANCE found |

## 6. Round 2 Fixes (Post-Second-Run Analysis)

The round 1 closing axioms changed the *shape* of counterexample witnesses (orphan UTXOs
were eliminated) but most spurious results persisted because three deeper under-constraints
remained. Round 2 addresses each root cause.

**Fix R2-1 — Address separation (vault_base.als):**
The `*NoExtraction_NoKey` counterexamples persisted because the solver equated vault
addresses (hotAddr, coldAddr) with AttackerAddr. A fully authorized withdrawal then
delivered funds to the attacker — not via a missing guard, but because the vault was
"owned by the attacker" by construction. Added `hotAddr != AttackerAddr` to the
VaultFamily sig facts (coldAddr separation already existed from round 1).

**Fix R2-2 — Transition output cardinality (ctv_vault.als, ccv_vault.als, opvault_vault.als):**
`ctvNoStateProliferation` found 4 UTXOs in a CTV family because a single CTVTrigger
produced two CTVUnvaultedUTXO atoms (`t.dst` is a set). The real CTV trigger produces
exactly one unvaulting output. Added `ctvTransitionCardinality`, `ccvTransitionCardinality`,
and `opvTransitionCardinality` facts constraining `#t.dst` per transition type:
CTV: all 1-output. CCV: trigger=1, revault=2, withdraw=1, recover=1. OPV: same as CCV.

**Fix R2-3 — WildSpend for mode confusion (ccv_vault.als):**
`ccvModeConfusionContained` held because the closing axioms force ALL spent VaultUTXOs
through modeled transitions — but OP_SUCCESS means the attacker bypasses the covenant
entirely and spends via an unstructured path. Alloy can't represent "unstructured spending"
without an explicit transition type. Added `CCVModeBypassed extends Transition` with:
`src in CCVVaultUTXO`, `modeConfusion[src.contract]`, `#dst = 0` (outputs are plain
UTXOs, not vault-typed). Rewrote `ccvModeConfusionContained` to assert `no CCVModeBypassed`
(should now find a counterexample whenever a mode-confused contract exists in scope).

**Fix R2-4 — Contention predicate logic (opvault_vault.als):**
`recoveryBlockedByContention` required BOTH recovery transactions to confirm
(`some r1.txn.confirmTime and some r2.txn.confirmTime`), but contention means r2
*cannot* confirm because r1 already spent the shared fee UTXO. Changed to:
`some r1.txn.confirmTime and no r2.txn.confirmTime`.

**Fix R2-5 — Non-degenerate families (vault_base.als):**
`fundConservation` found counterexamples with empty VaultFamily atoms (no deposit,
no allUTXOs). The allUTXOs closure was vacuously satisfied. Added `familyNonDegenerate`
fact requiring `some f.deposit and some f.allUTXOs` for every VaultFamily, plus
uniqueness: `all disj f1, f2 | f1.deposit != f2.deposit`.

### Expected impact on re-run (round 2)

| Previously unexpected result | Fix responsible | Expected new result |
|---|---|---|
| `*NoExtraction_NoKey` counterexamples (all 3 + threat_model) | R2-1 (address separation) | HOLDS |
| `ctvNoStateProliferation` counterexample | R2-2 (transition cardinality) | HOLDS |
| `fundConservation` counterexample | R2-5 (non-degenerate families) | HOLDS |
| `ccvModeConfusionContained` held | R2-3 (WildSpend) | COUNTEREXAMPLE |
| `opvNoFeeContention` held | R2-4 (contention predicate) | COUNTEREXAMPLE |
| `opvFeeContentionScenario` no instance | R2-4 (contention predicate) | INSTANCE found |

**Not fixed (modeling limitation — see Section 7):**
`ctvRecoveryAlwaysPossible` and `ccvRecoveryAlwaysPossible` still find counterexamples
because Alloy doesn't auto-generate recovery transitions for every live UTXO. In real
Bitcoin, recovery is enabled by the UTXO's script — it's always structurally available.
In Alloy, transitions are explicit atoms. Making recovery universally available via a
fact would render the assertion trivially true. These assertions should be interpreted
as **infrastructure completeness checks**, not security properties. The actual security
property (recovery goes to the right address) is verified by `recoveryDestinationIntegrity`
which holds correctly.

## 7. Known Alloy Modeling Limitations in These Models

### 7.1 CTV template commitment is approximate

The real CTV hash commits to exact byte-level output serialization. Our model
represents this as set membership (`d in template.committedOutputs`). This correctly
captures the structural constraint (outputs must match) but doesn't model:
- Byte-level malleability (e.g., SegWit witness malleation)
- Exact amount matching (value equality is checked abstractly)

### 7.2 Taproot key/script path distinction is simplified

The CCV and OP_VAULT models use a `isNUMS` boolean to distinguish safe (NUMS internal
key) from vulnerable (real key) configurations. Real Taproot involves a point addition
on secp256k1 — the algebraic structure is beyond Alloy. Tamarin would be needed to
verify that a given key construction actually produces an unspendable point.

### 7.3 Transaction graph is acyclic by construction

The `noCycles` fact in btc_base.als prevents cyclic UTXO graphs. This is correct for
Bitcoin (blockchain is append-only) but means Alloy cannot model reorg-based attacks
where a confirmed transaction is reversed. Reorg attacks require a different model
(e.g., Markov chain for mining competition).

### 7.4 Fees are abstracted

The `validFee` predicate only checks `sum(inputs) >= sum(outputs)`. It does not model:
- Minimum relay fee (1 sat/vB)
- Fee rate competition
- CPFP / RBF mechanics
- Package relay (BIP 331)

These are implementation-layer concerns tested by your regtest harness.

### 7.5 Recovery transition completeness

Alloy requires explicit Transition atoms; it cannot auto-generate them. In real Bitcoin,
the recovery spending path is embedded in every vault UTXO's script — it's always
available. In Alloy, if the solver doesn't create a CCVRecover atom for a particular
live UTXO, the `*RecoveryAlwaysPossible` assertion fails spuriously. This is an inherent
limitation of bounded model checking with explicit transition atoms.

## 8. Running the Models

### Prerequisites
- Java 8+ (for Alloy Analyzer)
- Alloy 6.x (download from alloytools.org)

### Quick start
```bash
# Open Alloy Analyzer GUI
java -jar alloy6.jar

# Or command-line (Alloy 6 supports CLI):
java -jar alloy6.jar --run ctv_vault.als

# Check a specific assertion:
# In the GUI: Open ctv_vault.als → Execute → select check command
```

### Recommended checking order

1. **btc_base.als** — `singleSpend` (sanity check, should pass instantly)
2. **vault_base.als** — all four base checks (should pass, <1s each)
3. **ctv_vault.als** — start with `ctvNoUnauthorizedExtraction_NoKey` (should pass),
   then `ctvEventualWithdrawal` (should find counterexample via address reuse)
4. **ccv_vault.als** — `ccvBoundedState` (should find counterexample quickly at scope 8)
5. **opvault_vault.als** — `opvNoFeeContention` (novel result)
6. **cross_covenant.als** — `noCrossVaultInjection` (composition analysis)

### Interpreting results

- **"No counterexample found"** = property holds within the checked scope
- **"Counterexample found"** = Alloy produces a concrete instance violating the assertion.
  Click to visualize the UTXO graph and transition sequence.
- **"No instance found" (for `run`)** = the scenario is unreachable within scope.
  Try increasing scope.

## 9. Relationship to dgpv's Prior Art

The [Delving Bitcoin post](https://delvingbitcoin.org/t/analyzing-simple-vault-covenant-with-alloy/819)
by dgpv models a single generic vault covenant using Alloy. Key differences from our models:

| Aspect | dgpv's model | Our models |
|---|---|---|
| Scope | Single vault type (OP_CAT-based) | Three vault types + composition |
| State machine | trigger_or_cancel + complete_withdrawal | Full lifecycle per vault |
| Threat model | Implicit (covenant enforcement) | Explicit attacker capabilities |
| Revault | Not modeled | Explicit with state proliferation |
| Key requirements | Not modeled | Per-vault key sets with separation |
| Cross-vault | Not applicable | Novel (input injection, fee contention) |
| Recovery | Single path | Keyless (CCV) vs authorized (OP_VAULT) |

Our base UTXO model draws on dgpv's approach (explicit input/output graph, transaction
ordering) but extends it significantly for multi-vault comparative analysis.
