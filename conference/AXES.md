# Design-Space Axes — Canonical Reference

This document is the single source of truth for the A1–A7 axis labels used across the FC 2027 paper, the thesis, experiment docstrings, and project artifacts. Settled per the plan at `~/.claude/plans/sleepy-dreaming-dream.md`.

**Rule:** Any new file or edit that references an axis MUST use the canonical label from §1 below. Any reference to an attack class MUST use the canonical class label from §4. Any reference to the Kerckhoffs threat model MUST use the canonical statement in §5.

---

## 1. The seven axes

| Axis | Canonical label | Formal symbol (proofs) | What it asks | Values |
|---|---|---|---|---|
| A1 | Recovery authorisation | $g$ | Who may initiate the recovery path? | `keyless` / `recoveryauth-key` / `hot-key` / `cold-key` |
| A2 | Revault support | $a$ | Does the covenant allow partial withdrawal (split one vault UTXO into withdrawn + remaining)? | `yes` / `no` |
| A3 | Fee-inclusion model | $f$ | Where does the spending transaction's fee come from? | `dynamic` (fee in the transaction itself) / `static-precommit` (fee baked at creation) / `out-of-band-anchor` (CPFP-only via anchor output) |
| A4 | Withdrawal-destination binding | subcomponent of $b$ | How is the withdrawal destination constrained to a committed value? | `template-hash-digest` / `per-output-amount+script` / `dedicated-opcode` / `signature-dual-bind` |
| A5 | Recovery-destination binding | subcomponent of $b$ | How is the recovery destination constrained? | `template-hash-digest` / `per-output-amount+script` / `dedicated-opcode` / `plain-signature` |
| A6 | Opcode surface | new | Is the covenant expressed by a single semantic opcode or a multi-mode polymorphic one with `OP_SUCCESS` fallthrough on unknown modes? | `single-mode` / `multi-mode-with-OP_SUCCESS` |
| A7 | Introspection primitive | new | How does the covenant read transaction data? | `digest-equality` / `merkle-membership-and-amount` / `dedicated-opcode` / `sighash-preimage-reconstruction` |

**Mapping to formal axes (proof apparatus — DO NOT renumber Lemmas D1–D4 or Propositions 1, 2):**

- `A1 ↔ g` (recovery gating)
- `A2 ↔ a` (amount flexibility)
- `A3 ↔ f` (fee model)
- `A4 + A5 ↔ b` (recovery binding — decomposed; see §3)
- `A6` — new; developer-footgun axis; not in the original proof apparatus
- `A7` — new; descriptive axis; surfaces *how* each covenant achieves binding

**Decision rationale (from plan §"Architectural decisions"):** Keep `(f, a, g, b)` as the formal axes used in proofs (Prop 1, Lemmas D1–D4, Prop 2). Introduce A1–A7 as canonical human-readable labels that cite the formal symbol when proof-relevant. This preserves the peer-review-ready proof apparatus, gets the expert-reader vocabulary benefit, and captures A6 + A7 which are genuinely new. Option B (renumbering lemmas) was rejected — too costly for zero analytical gain.

---

## 2. Four-covenant position table

The canonical position table. Copy into FC §2 and Thesis Ch 2 §2.6 verbatim.

| Axis | CTV | CCV | OP_VAULT | CAT+CSFS |
|---|---|---|---|---|
| **A1 Recovery auth** | hot-key | keyless | recoveryauth-key | cold-key |
| **A2 Revault** | no | yes | yes | no |
| **A3 Fee model** | out-of-band-anchor | dynamic | dynamic | dynamic |
| **A4 Withdrawal binding** | template-hash-digest | per-output-amount+script | dedicated-opcode | signature-dual-bind |
| **A5 Recovery binding** | template-hash-digest | per-output-amount+script | dedicated-opcode | plain-signature |
| **A6 Opcode surface** | single-mode | multi-mode-with-OP_SUCCESS | single-mode | single-mode |
| **A7 Introspection primitive** | digest-equality | merkle-membership-and-amount | dedicated-opcode | sighash-preimage-reconstruction |

**Simplicity's position (Appendix-only, not in main comparison):** A1 = `cold-key`, A2 = `atomic` (= `no`), A3 = `dynamic`, A4 = `dedicated-jets-combinator` (program-bound), A5 = `dedicated-jets-combinator` (program-bound), A6 = `single-mode`, A7 = `typed-combinator-introspection`. Simplicity occupies the dominant-corner position on A1, A2, A4, A5, A7 simultaneously; no Bitcoin covenant does.

---

## 3. A4/A5 decomposition from $b$

The formal $b$ axis conflates withdrawal-binding and recovery-binding. A4 and A5 stay split because CAT+CSFS occupies **different positions** on the two sub-axes: A4 = `signature-dual-bind` (strongest), A5 = `plain-signature` (weakest). Collapsing them forces a `Remark` (currently `ch5_security.tex:1276-1284`) instead of a mechanical lookup.

For proofs, cite $b$. For prose and class derivations, cite A4 / A5 separately.

---

## 4. Attack classes (Z1–Z6)

Every attack in the paper derives from a specific axis-value. Each class has three parts per Item 5 of `FRAMING-CHANGES.md`:

| Class | Label | Enabling axis-value | Susceptible | Immune (and why) |
|---|---|---|---|---|
| **Z1** | Fee-channel pinning | A3 = `out-of-band-anchor` | CTV | CCV, OPV, CAT+CSFS — A3 = dynamic, no separate anchor handle |
| **Z2** | Permissionless griefing | A1 = `keyless` | CCV | OPV (A1 = recoveryauth-key), CTV (A1 = hot-key required), CAT+CSFS (A1 = cold-key required) |
| **Z3** | Per-UTXO recovery-cost scaling | A2 = `yes` | CCV, OPV | CTV, CAT+CSFS — A2 = no; partial withdrawal not expressible |
| **Z4** | Hot-key theft via destination substitution | A4 ∈ {`template-hash-digest`, `per-output-amount+script`, `dedicated-opcode`} (i.e. NOT signature-dual-bind) | CTV, CCV, OPV | CAT+CSFS — A4 = signature-dual-bind |
| **Z5** | Cold-key theft via unconstrained recovery | A5 = `plain-signature` | CAT+CSFS | CTV (A5 = template-hash-digest), CCV (A5 = per-output-amount+script), OPV (A5 = dedicated-opcode) |
| **Z6** | Mode/parameter bypass | A6 = `multi-mode-with-OP_SUCCESS` | CCV | CTV, OPV, CAT+CSFS — A6 = single-mode |

**Propositions as corollaries:**
- **Proposition 1 (Griefing–Safety Incompatibility)** projects onto the (A1, A4, A5) sub-lattice: no assignment simultaneously zeros Z2 and {Z4 ∪ Z5}. Equivalently, if A1 = keyless (killing Z2 susceptibility by disabling the need for authorisation) then either A4 or A5 must be unbound (opening Z4 or Z5).
- **Proposition 2 (Fee-Dependent Security Inversion)** is a joint statement over (A2, A3, defender-batching-strategy): the ranking of Z1 cost against Z3 cost inverts as fee rate rises.

---

## 5. Kerckhoffs threat-model preamble (canonical statement)

Use the following text verbatim (or near-verbatim with only grammatical adaptation) wherever the threat model is introduced:

> **Threat model (Kerckhoffs).** We adopt the standard cryptographic threat model. The adversary knows the vault's design, the covenant type, the script structure, and all public parameters — including the recovery address where applicable. Security rests on keys and on the script's semantics, not on the secrecy of construction. Every attack-feasibility claim in this work is evaluated under this assumption. Concretely: we do not rely on taproot leaf hiding, address non-disclosure, or closed-source construction as security mechanisms.

Canonical placement: FC §2.3 (threat taxonomy section); Thesis Ch 3 (methodology) with a forward reference from Ch 2. Every attack-feasibility claim cites `(Kerckhoffs, §2.3)` or equivalent.

---

## 6. Class-to-threat-model mapping

The current TM1–TM11 threat taxonomy remains the authoritative per-threat vocabulary. Classes subsume threats: each class spans one or more TMs, and each TM is an instantiation of a class. Retain TM labels as citation anchors; classes are the *explanatory* abstraction.

| Class | Subsumes TMs | Notes |
|---|---|---|
| Z1 | TM1 (fee pinning) | Single-TM class; CTV-specific |
| Z2 | TM2 (recovery griefing) | CCV-specific; OPV near-immune via key-gating |
| Z3 | TM4 (formerly watchtower exhaustion, now per-UTXO recovery-cost scaling) | Structural cost tail; also TM2 amplifier for CCV |
| Z4 | TM3 (trigger key theft), TM9 (hot-key redirection) | Cross-covenant; CAT+CSFS immune |
| Z5 | TM11 (cold-key compromise under unconstrained recovery) | CAT+CSFS-specific |
| Z6 | TM8 (CCV mode bypass) | CCV-specific, developer-footgun framing |

Orphans (not yet classified as a Z-class):
- TM5–TM7: operational-correctness (address reuse, dust-limit interactions) — treat as "operational" or "axis-measurement" category in docstrings, not a Z-class.
- TM10 (witness manipulation / SHA-256 collision): cryptographic-verification — not an attack class per se.

---

## 7. Canonical rationality block (seven fields)

Every attack class (Z1–Z6) carries this seven-field block. FC paper compresses to 1–2 sentences per field; Thesis App D carries the full form.

1. **Attacker capability.** Keys, capital, mempool access, compute. Cite Kerckhoffs by reference.
2. **Defender model.** Watchtower authority, policy (proactive/reactive, batched/per-UTXO), user availability, detection latency.
3. **Economic preconditions.** Fee regime, vault-value range, rationality threshold.
4. **Protocol / network assumptions.** Mempool policy (descendant limits, dust thresholds), RBF/BIP-125 rules, TRUC/BIP-431 modifiers, cluster-mempool scope-limits, relay floor.
5. **Scope of validity.** When the attack applies; equally important, when it does NOT.
6. **Rational-attacker check.** Is execution economically rational? Payoff vs cost vs residual (theft/liveness/both/neither).
7. **Counter-factual mitigations.** Which single falsified assumption kills the attack.

Rule per FRAMING-CHANGES line 341: every field populated OR marked `N/A — [reason]`. No partial blocks.

---

## 8. LaTeX macros (shared FC + Thesis preamble)

Define in both `conference/FC-2027/paper/fc27-paper.tex` and `Thesis/thesis.tex` preambles (or a shared `axes.tex` file included by both). Canonical names:

```latex
% Axis labels — canonical
\newcommand{\axauth}{A1}          % Recovery authorisation (formal: g)
\newcommand{\axrevault}{A2}       % Revault support (formal: a)
\newcommand{\axfee}{A3}           % Fee-inclusion model (formal: f)
\newcommand{\axwdbind}{A4}        % Withdrawal-destination binding (subcomp. of b)
\newcommand{\axrecbind}{A5}       % Recovery-destination binding (subcomp. of b)
\newcommand{\axopsurf}{A6}        % Opcode surface (new)
\newcommand{\axintro}{A7}         % Introspection primitive (new)

% Class labels — canonical
\newcommand{\classfee}{Z1}        % Fee-channel pinning
\newcommand{\classgrief}{Z2}      % Permissionless griefing
\newcommand{\classscale}{Z3}      % Per-UTXO recovery-cost scaling
\newcommand{\classhot}{Z4}        % Hot-key theft via destination substitution
\newcommand{\classcold}{Z5}       % Cold-key theft via unconstrained recovery
\newcommand{\classmode}{Z6}       % Mode/parameter bypass

% Convenience: axis with formal symbol aside
\newcommand{\axauthf}{\axauth\,($g$)}
\newcommand{\axrevaultf}{\axrevault\,($a$)}
\newcommand{\axfeef}{\axfee\,($f$)}
\newcommand{\axbindf}{\axwdbind+\axrecbind\,($b$)}
```

Do NOT invent variant macros. If a section needs a form not listed above, add it here first, then use it.

---

## 9. Vocabulary retirement list

The following phrases are retired. Do NOT use them in any new content:

| Retired phrase | Replacement |
|---|---|
| "watchtower exhaustion" / "watchtower exhaustion attack" | "per-UTXO recovery-cost scaling" (structural), "\classscale" (class reference), or "TM4" (when citing the threat-taxonomy anchor) |
| "5 covenants" / "five covenant vault implementations" (as headline scope claim) | "four Bitcoin covenant proposals" (for main comparison); Simplicity separately as cross-substrate reference |
| "CCV mode bypass" as a **novel finding** | "documented consequence of BIP-443's specified OP_SUCCESS fallthrough"; the **novelty** is the class-level framing and the systematic mode sweep, not the discovery |
| "watchtower exhaustion attack" (dramatic multi-round framing) | Structural cost tail; multi-round attacker becomes one rationality-block "threat-model variation" |

Exception: retrospective references that explain the retired framing are allowed (e.g., speaker notes, commit messages, this document) — but never in the body of the paper or thesis.

---

## 10. Simplicity scoping rule

Simplicity on Elements is:
- **Excluded** from the main 4-way comparison tables, propositions, and empirical-contribution claim.
- **Included** in:
  - FC paper as Appendix D ("Simplicity on the Optimal Corner").
  - Thesis as Appendix C ("Simplicity on Elements: The Unoccupied Optimal Corner").
  - Future-work references in both documents.

Canonical one-sentence claim (use verbatim or near-verbatim): *"Simplicity's atomic-vault program occupies the strict-best position on A1, A2, A4, A5, A7 simultaneously; no Bitcoin proposal does. This demonstrates the dominant corner is occupiable; the gap identified in §3 is about the unoccupied status among current Bitcoin proposals, not about theoretical impossibility."*

---

## 11. Update protocol

If any axis, class, or field in this document needs to change:
1. Update this file first.
2. Grep for every affected canonical label across the four surfaces.
3. Update each surface in lockstep.
4. Re-run the cross-surface verification from the plan.
5. Commit in a single coherent changeset.

Do not let this file and any downstream surface drift.
