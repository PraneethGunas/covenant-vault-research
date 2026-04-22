# Framing Changes — Pending Revisions

Tracks framing-level changes to apply to the thesis and conference submissions. See `FRAMING-GUIDE.md` for venue-specific framing strategy and `SUBMISSION-STRATEGY.md` for submission priorities.

**Status convention:** `pending` = agreed but not yet applied. `applied` = change is in the thesis/paper. `dropped` = reconsidered and abandoned.

---

## 1. Kerckhoffs's principle as threat-model justification

**Status:** pending

**Motivation.**
Every attack in the paper assumes the adversary knows the vault's design and parameters — the covenant type, the script structure, the cold-key pubkey, the CSV delay, the construction algorithm. Without surfacing this explicitly, reviewers can (and will) push back on individual attacks with *"but taproot hides that leaf"* or *"but the attacker wouldn't know the cold address."* Those objections target on-chain information leakage, where the paper has no cryptographic defense — taproot genuinely does hide unused leaves.

The correct answer is not to argue on reveal mechanics but to surface the assumption as a **standard cryptographic threat-model choice**: Kerckhoffs's principle — security must rest on keys, not on the secrecy of the design. A vault whose griefing immunity depends on the attacker not knowing the cold address isn't cryptographically secure; it's obscured. The moment the recover path is ever legitimately used, or the cold address is disclosed for auditability, or the construction algorithm is open-sourced, the "hiding" defense collapses.

Making this assumption explicit moves the debate from *"does taproot leak?"* (paper weak) to *"should a vault's security depend on the secrecy of its construction?"* (paper strong).

**Change.**
Add one short paragraph to the methodology chapter (or the threat-model preamble of Chapter 5) stating: *"We adopt the standard cryptographic threat model. The attacker is assumed to know the vault's design, the covenant type, the script structure, and all public parameters (including the cold address where applicable). Security must rest on keys and on the script's semantics, not on the secrecy of the construction. This is Kerckhoffs's principle applied to covenant vault design, and is the threat-model assumption that underlies every attack in this work."*

**Scope of effect.**
- Strengthens CCV recovery griefing (the attack's feasibility assumes cold-address knowledge)
- Strengthens CTV fee pinning (assumes fee-key hierarchy is known)
- Strengthens CCV mode bypass (assumes developer realistically mis-types a mode)
- Applies to every attack-feasibility claim downstream

**Where to add.**
- Thesis: Ch. 3 (Methodology) threat-model section, and/or Ch. 5 preamble before attack walkthroughs.
- FC paper: methodology section, one-sentence.
- Presentation: already discussed verbally; add a speaker-note on the threat-model slide.

---

## 2. Simplicity vault — reframe as "the unoccupied optimal corner," move to appendix

**Status:** pending

**Motivation.**
The four-dimensional design-space analysis (D1–D4) identifies a dominant corner — the combination of feature choices that closes every structural attack surface simultaneously. None of the four Bitcoin covenants (CTV, CCV, OP_VAULT, CAT+CSFS) occupies this corner; each has a blind spot. The current framing leaves this corner *theoretical* — "no current proposal closes all four attack surfaces."

Simplicity's vault arguably *does* occupy this corner, but it runs on Elements (not Bitcoin), uses a different script model (not Bitcoin Script), and requires a separate soft-fork path (Simplicity is not a covenant proposal for Bitcoin at all). Including Simplicity in the main four-way comparison muddies the claim and invites reviewer pushback about scope.

The right move is to reframe Simplicity as the **constructive existence proof** that the optimal corner is occupiable — just not by any current Bitcoin proposal. Keep it in the thesis (it strengthens the "structural gap" narrative) but confine it to an appendix so the main comparative chapter stays focused on Bitcoin covenants.

**Change.**
- Main chapters (Ch. 2 Background, Ch. 4 Results, Ch. 5 Security, Ch. 7 Discussion): remove Simplicity from the four-way comparison tables and figures. State the four-way comparison is over Bitcoin proposals only.
- New appendix (Appendix C or equivalent): "Simplicity as the Optimal Corner." Show that Simplicity's vault occupies the dominant corner of the D1–D4 axes, provide lifecycle measurements, and argue that this is a constructive existence proof — the corner is occupiable, just not by any current Bitcoin proposal.
- Update the "unoccupied safer corner" claim in Ch. 5 to: *"no Bitcoin proposal occupies the dominant corner; Simplicity on Elements demonstrates the corner is occupiable (Appendix C)."*

**Scope of effect.**
- Sharpens the "structural gap" contribution (Contribution #4)
- Removes the biggest reviewer-objection vector ("why is Simplicity even in this comparison?")
- Preserves the empirical Simplicity data without letting it dilute the main message

**Where to add.**
- Thesis: remove Simplicity rows/columns from main comparison tables; add Appendix C with full Simplicity analysis.
- FC paper: drop Simplicity from the body entirely; mention in related-work / future-work as the optimal corner demonstrator.

---

## 3. Covenant explanations — precise transaction-introspection mechanics

**Status:** pending

**Motivation.**
The Background chapter currently describes each covenant in prose, but does not precisely show *what part of the spending transaction each covenant inspects, and how it does it*. This is exactly the information the reader needs to understand why CTV, CCV, OP_VAULT, and CAT+CSFS have different attack surfaces — the attack surfaces are a direct consequence of what each covenant can (and cannot) introspect.

- **CTV** hashes a template of transaction fields (nVersion, nLockTime, sequences, outputs hash, input count, spend index) — it is a *digest equality check*. It inspects the whole transaction, in one shot, via a single committed hash.
- **CCV** inspects output[i]'s amount and taproot internal key/tree, checking Merkle-membership or amount-conservation depending on mode. It is a *per-output structural check*.
- **OP_VAULT** has dedicated opcodes (`OP_VAULT`, `OP_VAULT_RECOVER`) that inspect specific output structures — withdrawal template or recovery destination — without a general introspection mechanism.
- **CAT+CSFS** rebuilds a sighash preimage piece-by-piece with `OP_CAT`, then verifies a signature over it with `OP_CHECKSIGFROMSTACK`. It is *indirect* introspection via signature cross-binding — the script never reads transaction fields, but forces the signature to sign over specific reconstructed bytes.

The differences matter: they explain why CAT+CSFS uniquely blocks hot-key theft (signature binding), why CCV uniquely allows partial withdrawal (per-output amount semantics), why CTV uniquely pre-commits everything (whole-template digest), and why OP_VAULT's recovery needs a separate `recoveryauth` key (the opcodes do not expose a keyless recovery primitive).

**Change.**
For each of the four covenants in Chapter 2 (Background) and the corresponding presentation mechanism slides, add a small table or annotated diagram showing:
- **What transaction fields the covenant can observe** (inputs/outputs/amounts/scripts/sighash/templates)
- **How it observes them** (digest equality / Merkle membership / dedicated opcode / signature preimage reconstruction)
- **What it cannot observe** (e.g., CTV cannot inspect individual outputs dynamically; CCV cannot bind to a signature; etc.)

The goal is that a reader who studies this table knows — before reading any attack chapter — exactly what *each covenant's introspection primitive is*. The attack surfaces then follow mechanically from the primitive's limits.

**Scope of effect.**
- Makes the Chapter 5 security analysis feel *derived* rather than asserted.
- Sharpens Proposition 1 (the griefing–safety incompatibility) — it becomes a statement about introspection primitives, not about covenant names.
- Sharpens Proposition 2 (fee-dependent inversion) — the inversion follows from whether the covenant inspects per-output amounts (CCV/OPV) or whole-template hashes (CTV).

**Where to add.**
- Thesis: Ch. 2 §2.2 through §2.5 (one new subsection per covenant, "Introspection primitive"). Also extend Table 2.1 / 2.2 with a "What it introspects" column, or add a dedicated Table 2.5 comparing introspection primitives across all four.
- FC paper: one compact comparison table in the Background section, plus a sentence per covenant in the mechanism descriptions.
- Presentation: the existing mechanism slides (CTV / CCV / OP_VAULT / CAT+CSFS) should gain one bullet each: "What this covenant can see and how."

---

## 4. Watchtower exhaustion — reframe as a recovery-cost tail, not a multi-round attack

**Status:** pending

**Motivation.**
The current "watchtower exhaustion attack" framing does not survive adversarial reading. Two objections kill it:

1. **Watchtower authority is under-specified.** In CCV, recovery is keyless — any observer (including the watchtower) can recover *any* vault UTXO *at any time*, including proactively against the original vault UTXO before any trigger. In OP_VAULT, the watchtower holds `recoveryauth` and has the same proactive power. A watchtower with full recovery authority doesn't have to wait for a trigger, so the "chase the attacker" multi-round framing has no protocol basis.

2. **First-round full sweep ends the attack.** Once an unauthorized trigger is observed, a rational defender's dominant strategy is a full proactive sweep — recover the entire remaining vault UTXO (plus any in-flight unvaulting outputs) in a single transaction. One round, attack over. The "1,400 splits needed at 300 sat/vB" calculation assumes 1,400 rounds that no sane defender would allow.

The dramatic "attacker bankrupts the watchtower in 1,400 rounds" framing is empirically weak and invites reviewer attrition. It only holds under narrow conditions (minimal-disruption watchtower policy, operational inability to full-sweep, pre-existing UTXO fragmentation from legitimate use, short detection-to-action windows) — none of which we currently surface or justify.

**Change.**
Reframe the finding from "an active attacker exhausts the watchtower" to **a latent structural property of partial withdrawal that any attacker merely accelerates**:

> *CCV and OP_VAULT's support for partial withdrawal creates a latent recovery-cost tail that scales with the number of resulting UTXOs and the prevailing fee rate. Over ordinary operation the vault accumulates UTXOs whose per-unit recovery cost can, under congestion, exceed per-unit value — rendering them rationally unrecoverable by a watchtower that recovers per-UTXO. An attacker can accelerate this distribution, but the liability exists without one. The defender-side variable that governs whether the liability is absorbable is whether recovery is batched — which is also what causes the safety ranking between CCV and OP_VAULT to invert.*

Centre the finding on three claims, in this order:

1. **Structural cost tail.** Partial withdrawal is not free — every legitimate split grows the recovery-cost surface. CTV and CAT+CSFS do not have this tail because they do not support partial withdrawal. Direct tradeoff between operational flexibility and latent recovery cost.

2. **Economic abandonment threshold.** At high fee rates, UTXOs below a value threshold cost more to recover than they contain. This is an economic fact about Bitcoin's fee market, not an attack artefact. An attacker's role is to make the distribution adversarial; legitimate operation can produce the same distribution without one.

3. **The batched-recovery ordering flip (the headline).** Whether the watchtower recovers per-UTXO (linear cost in N) or batches (sub-linear) materially changes the safety profile. The CCV-vs-OP_VAULT safety ranking on this axis inverts based exactly on batching capability. This is the empirically novel finding and should be the slide's and paper's primary claim.

**Drop "watchtower exhaustion attack" as the chapter/slide title.** Replace with something like *"Per-UTXO recovery scaling under adverse fees"* or *"The recovery-cost tail of partial withdrawal."* The attack framing collapses; the measurement framing and the ordering flip survive.

**Scope of effect.**
- Eliminates the biggest "this attack assumes a stupid defender" reviewer objection.
- Sharpens Contribution #4 (the batched-defender ordering flip) by making it the central finding rather than a follow-on to a dramatic attack story.
- Aligns the exhaustion analysis with the paper's broader framing: structural-cost tradeoffs, not zero-day disclosures.
- Strengthens Proposition 2 (fee-dependent inversion) — the inversion becomes a property of routine operation under congestion, not a rare attacker scenario.

**Where to apply.**
- Thesis: Ch. 5 Security Analysis — rename the subsection currently titled "Watchtower Exhaustion Attack"; rewrite to lead with the structural cost tail and the ordering flip. Move the multi-round attacker scenario to a "Threat model variations" paragraph, explicitly listing the conditions (A–D) under which an active attacker accelerates the latent cost surface.
- Thesis: Ch. 4 Results — present the empirical numbers as "recovery-cost scaling measurements," not as "attack feasibility thresholds."
- FC paper: drop the "attack" framing from the abstract and section title. Lead with the structural tradeoff and the ordering flip.
- Presentation: rename the slide "Watchtower Exhaustion Attack — CCV & OP_VAULT" to match the new framing; rewrite bullets to emphasise structural cost scaling and defender batching policy. The "1,400 splits" number can stay as an illustrative congestion threshold, but should not be presented as a multi-round attack feasibility count.

---

## 5. Attacks as classes, not incidents — derive susceptibility from design

**Status:** pending

**Motivation.**
The current security chapter presents attacks as a catalogue: *"Fee Pinning Attack — CTV,"* *"Recovery Griefing Attack — CCV,"* *"Watchtower Exhaustion — CCV & OP_VAULT,"* and so on. Each attack is told as a self-contained story against a specific opcode. This framing has two problems:

1. **It reads as a bug list, not a structural analysis.** A reviewer walks away with *"CTV has fee pinning, CCV has griefing, OPV has exhaustion"* — four disconnected facts, one per covenant. There is no generalisation, and the comparative framing of the paper (*"these four designs are points in a structured design space"*) gets lost behind four isolated anecdotes.

2. **Immunity is asserted without being derived.** The slides say things like *"CTV and CAT+CSFS are immune to watchtower exhaustion (no partial withdrawal)"* as a footnote, rather than as the conclusion of a structural argument. A reader doesn't come away seeing *why* immunity falls out of the design choice; they see it as a fact the authors state.

The fix is to reframe every attack as a **class** with three parts: (a) the structural design property that enables the class, (b) the opcodes susceptible to it *and why*, (c) the opcodes immune to it *and why*. Every attack becomes a derivation from design primitives, not a found-in-the-wild incident. This produces a security narrative in which the design space (D1–D4 axes) and the attack classes are two views of the same structure.

This composes directly with items (1) and (3):
- Item (1) Kerckhoffs → *given the attacker knows the design...*
- Item (3) Introspection primitives → *each opcode's introspection primitive is X...*
- Item (5) Attack classes → *...therefore opcodes with property Y are susceptible to attack class Z, and opcodes without Y are immune by construction.*

Together these three items produce a security analysis that reads as theorem-and-proof rather than bug-list-and-commentary.

**Change.**
Restructure Chapter 5 (Security Analysis) and the corresponding slide block so that every attack is presented in this three-part form:

1. **Class definition.** What is the structural design property this class exploits? State it as a precise property of the covenant's introspection primitive, recovery gating, amount semantics, or key hierarchy — not as a covenant name.

2. **Susceptibility derivation.** For each covenant with that property, derive the attack. Show how the attack is a direct consequence of the design choice, not a bug. Give the attack mechanics and (where relevant) the empirical cost.

3. **Immunity derivation.** For each covenant without that property, derive the immunity. Name the design decision that produces it, and state the tradeoff that decision cost the design along other axes.

Concretely, the attack classes are approximately:

| Class | Structural property enabling it | Susceptible | Immune (and why) |
|---|---|---|---|
| **Fee-channel pinning** | Pre-commitment forces fees onto a separate anchor handle | CTV | CCV / OPV / CAT+CSFS — dynamic fee inclusion, no separate anchor key |
| **Permissionless griefing** | Recovery gate does not require authorisation | CCV | OPV (recoveryauth key), CTV (hot key needed), CAT+CSFS (cold key needed) |
| **Per-UTXO recovery-cost scaling** | Partial withdrawal produces per-UTXO recovery liability | CCV, OPV | CTV, CAT+CSFS — no partial withdrawal; revault not expressible |
| **Hot-key theft via destination substitution** | Destination not bound to the authorising signature | CTV (hot key substitutes destination after CSV), CCV, OPV | CAT+CSFS — signature dual-bound to transaction contents |
| **Cold-key theft via unconstrained recovery** | Recovery leaf lacks covenant-enforced destination | CAT+CSFS | CTV, CCV, OPV — recovery destination enforced by script |
| **Mode/parameter bypass** | Opcode accepts out-of-spec parameters as `OP_SUCCESS` | CCV (undefined modes) | CTV, OPV, CAT+CSFS — no multi-mode opcode surface |

Each class then gets its own subsection (or slide pair), organised by class rather than by covenant. Where today we have *"Fee Pinning — CTV"* and *"Recovery Griefing — CCV"* as parallel slides, we will instead have *"Class: fee-channel pinning"* with CTV-susceptible and CCV/OPV/CAT+CSFS-immune derivations on the same slide, and *"Class: permissionless griefing"* with CCV-susceptible and OPV/CTV/CAT+CSFS-immune derivations on the same slide.

The Proposition 1 (griefing–safety incompatibility) and Proposition 2 (fee-dependent inversion) statements become direct corollaries of the class-table structure.

**Scope of effect.**
- Chapter 5 becomes a structural derivation rather than a catalogue.
- The four-way comparison matrix (Table 5.1 / TM1–TM11) becomes the class table above, reframed.
- Propositions 1 and 2 become corollaries of the class-to-susceptibility mapping, tightening their proofs.
- The slide block shrinks naturally — classes deduplicate per-covenant stories that share a structural root.
- Reviewer attrition drops because there is no "*why is CCV in this attack but not that one?*" footnote-hunting; every inclusion and exclusion is derived on the same slide.

**Where to apply.**
- Thesis Ch. 5: reorganise subsection order from *per-covenant* to *per-class*. Each class subsection contains its enabling property, the susceptibility derivations, and the immunity derivations side-by-side.
- Thesis Ch. 4: the threat-model matrix (TM1–TM11) gets a new column: *"Structural property enabling the class."*
- FC paper: Section 4 (Attacks) restructured class-first. One table, six rows, three columns (class / susceptible / immune-by-construction).
- Presentation: consolidate pairs of attack slides (e.g., the current *"Recovery Griefing — CCV"* and its implicit immunity-for-others footnote) into single class-level slides that show susceptibility and immunity as two halves of the same structural fact.
- DESIGN.md: the experiment catalogue gets a *"class"* tag per experiment so the empirical measurements ladder up into the class taxonomy.

**Note on composition with other items.**
Items (1), (3), (4), (5) should be applied together or not at all. They are mutually reinforcing: Kerckhoffs establishes the threat model, introspection primitives establish the design axes, the watchtower reframe demonstrates the style (structural tail, not incident), and the class framing generalises it across the chapter. Applying only a subset produces inconsistent tone — some chapters argue structurally, others anecdotally.

---

## 6. Define the design-space axes explicitly and early — one vocabulary, consistently

**Status:** pending

**Motivation.**
The paper implicitly compares the four covenants along several dimensions — revault support, recovery authorisation, fee-inclusion model, destination-binding semantics, mode surface — but these dimensions are never defined in one place, never enumerated as a closed set, and never introduced before the attack analysis uses them. Each axis shows up in an attack narrative, a table footnote, or a propositional aside, but the reader never gets a single mental model of *"here are the N axes on which these designs differ; here is each design's position on each axis."*

This has three downstream costs:

1. **Terminology drifts across chapters.** The same axis gets called "keyless recovery" in one section, "permissionless recovery" in another, and "unauthorized recovery" in a third. The reader doesn't know whether these are the same thing or three subtly different properties. Reviewers notice. Citations become fragile.

2. **Attack classes cannot be derived cleanly (Item 5).** The class framing depends on a stable set of structural properties. If those properties are not pre-defined, each attack class derivation has to re-introduce and re-justify the property it exploits, duplicating exposition and producing inconsistent phrasing.

3. **Propositions 1 and 2 read as ad hoc rather than structural.** P1 (griefing–safety incompatibility) is a statement about two specific axes: recovery authorisation and fund-safety under key loss. P2 (fee-dependent inversion) is about the fee-inclusion axis interacting with the recovery-scaling axis. Without the axes formally named up front, both propositions read as bespoke observations rather than corollaries of a structured design-space.

The fix is to define the design-space axes **once, formally, in Chapter 2 (Background)**, and then use that vocabulary everywhere downstream — attack classes, propositions, tables, slide matrix, conclusion.

**Change.**
Add a section in Chapter 2 — probably §2.2 or a new §2.6 — titled *"The Design-Space Axes."* This section:

1. **Names each axis** with a short canonical label and a precise definition.
2. **Enumerates the possible values** on each axis (the discrete positions, not a continuum).
3. **Maps each of the four covenants** to its position on each axis, in a single table.
4. **Previews the attack-class consequences** of each position (forward-reference to Chapter 5's class derivations), without yet proving them.

Proposed axes, with canonical labels (final names to be decided):

| Axis | What it asks | Values |
|---|---|---|
| **A1 — Recovery authorisation** | Who may initiate the recovery path? | keyless / recoveryauth-key / hot-key / cold-key |
| **A2 — Revault support** | Does the covenant allow partial withdrawal (split one vault UTXO into withdrawn + remaining vault)? | yes / no |
| **A3 — Fee-inclusion model** | Where does the spending transaction's fee come from? | dynamic (fee in the transaction itself) / static pre-committed (fee baked at creation) / out-of-band anchor (CPFP-only) |
| **A4 — Withdrawal-destination binding** | How is the withdrawal destination constrained to a committed value? | template-hash digest / per-output amount + script / signature dual-binding (CAT+CSFS) |
| **A5 — Recovery-destination binding** | How is the recovery destination constrained? | template-hash / per-output amount + script / plain signature (no script constraint) |
| **A6 — Opcode surface** | Is the covenant expressed by a single semantic opcode or a multi-mode polymorphic one? | single-mode / multi-mode with `OP_SUCCESS` fallthrough |
| **A7 — Introspection primitive** (item 3) | How does the covenant read transaction data? | digest equality / Merkle membership / dedicated opcode / sighash-preimage reconstruction |

A7 is the mechanism-level axis (from item 3); A1–A6 are the observable-property axes. They are not independent — each observable property is a consequence of the introspection primitive plus other design choices — but they are the axes the paper's attack analysis actually uses, and treating them as named axes rather than implicit facts is what produces a consistent vocabulary.

The four-covenant position table (to be included in Chapter 2 and referenced everywhere):

| | CTV | CCV | OP_VAULT | CAT+CSFS |
|---|---|---|---|---|
| **A1 Recovery auth** | hot-key | keyless | recoveryauth-key | cold-key |
| **A2 Revault** | no | yes | yes | no |
| **A3 Fee model** | out-of-band anchor | dynamic | dynamic | dynamic |
| **A4 Withdraw binding** | template-hash | amount + script | dedicated opcode | signature dual-bind |
| **A5 Recovery binding** | template-hash | amount + script | dedicated opcode | plain signature |
| **A6 Opcode surface** | single-mode | multi-mode (`OP_SUCCESS`) | single-mode | single-mode |
| **A7 Introspection** | digest equality | Merkle/amount | dedicated opcode | sighash preimage |

From this table alone, the attack-class susceptibility map in item (5) is mechanically derivable — which is the whole point. Every "CTV is susceptible to fee pinning because of its fee model" becomes a direct reading off the A3 row, not an argument that has to be re-made in the attack chapter.

**Scope of effect.**
- **Single source of truth.** Every later chapter references the axes by canonical label. No more "keyless / permissionless / unauthorized" drift.
- **Attack-class derivation (item 5) becomes mechanical.** Susceptibility = *"designs with value X on axis An are susceptible to class Z."* Every derivation has the same shape.
- **Propositions gain structure.** P1 = incompatibility between a value on A1 and a property of A2/A4. P2 = interaction between A3 and the recovery-scaling consequence of A2. Both become corollaries of the axis structure.
- **Simplicity appendix (item 2) has a natural home.** Simplicity's "optimal corner" claim becomes *"Simplicity's vault occupies the strict-best position on A1, A2, A3, A4, A5, A6, A7 simultaneously — no Bitcoin covenant does."* One sentence instead of a paragraph.
- **Empirical tables become legible.** Ch. 4 measurement tables gain a header row showing which axis each column measures the consequence of.

**Where to apply.**
- **Thesis Ch. 2 (Background):** add §"The Design-Space Axes" with axis definitions, value enumerations, and the four-covenant position table. Position this *before* the per-covenant mechanism subsections so readers have the comparison scaffold before seeing each design in isolation.
- **Thesis Ch. 5 (Security Analysis):** every attack-class subsection opens with *"Class Z exploits axis An value V…"* — using the axis labels from Ch. 2. No re-definition.
- **Thesis Ch. 4 (Results):** measurement tables add "Axis measured" column headers so each vsize/cost number is pinned to which axis value it is a consequence of.
- **Thesis Ch. 7 (Discussion):** deployment recommendations are phrased in axis terms ("*low-fee regime → A3 dynamic-fee designs; high-griefing-risk environment → A1 authorized-recovery designs*"). Makes the recommendations transparent and machine-applicable.
- **FC paper:** one page in Section 2 (Background) for the axes table. Rest of the paper uses the labels.
- **Presentation:** promote the axes table to a standalone slide (replacing or augmenting the current "Four Proposed Covenant Designs" four-grid). Then every attack-class slide opens with the axis it exploits, highlighted in the table.
- **DESIGN.md:** add axis tags to experiments — each experiment states which axis/value combination it measures.

**Note on composition with other items.**
Item (6) is a *precondition* for item (5) — the class framing cannot be applied consistently without the axes defined first. The correct application order is:
1. Item (6) — define axes and values (Chapter 2).
2. Item (3) — populate axis A7 (introspection primitive) with precise descriptions.
3. Item (1) — state the Kerckhoffs assumption in the methodology.
4. Item (5) — derive attack classes using the axis vocabulary from (6) and (3).
5. Item (4) — apply the structural reframing to the specific case of watchtower exhaustion, using axis A2 (revault) + A3 (fee model) as the joint enabler.
6. Item (2) — position Simplicity in the appendix using the axis labels to state its optimal-corner claim precisely.

This is the full restructure. The end state is a paper where every security claim is a theorem of the form *"axis A<sub>n</sub> value V + axis A<sub>m</sub> value W implies property P,"* and the design space is a closed set of discrete tables rather than a cloud of prose.

---

## 7. Rationality section per attack — state the conditions and assumptions explicitly

**Status:** pending

**Motivation.**
Every attack in the paper holds under a specific set of attacker capabilities, defender behaviours, and economic/network conditions. Those conditions are implicit in the current narration but never surfaced in one place. The cost is that a reviewer (or an advisor, or a committee member) can puncture an attack's framing by raising a condition we never addressed — *"what if the watchtower just does a full sweep?"*, *"why does the attacker pay capital up-front instead of just leaving?"*, *"does this work at low fees?"* — and the paper has to answer these on the fly, usually poorly, because the assumptions were never inventoried.

The watchtower exhaustion discussion that triggered item (4) is the clearest example: the attack framing collapsed under a single probing question because the assumptions (watchtower policy, first-round sweep, detection latency, operational inability to reset) were never stated. Other attacks in the paper have the same vulnerability. Fee pinning implicitly assumes the attacker holds the fee key *and* holds capital for the descendant-chain anchor. Recovery griefing assumes the attacker knows the cold address and that the defender's policy is to re-trigger rather than abandon. Mode bypass assumes a realistic developer-error surface. None of these conditions are surfaced in a form a reviewer can audit.

The fix is a **standardised rationality block for every attack or measurement**, placed immediately below the attack statement, before the mechanics walk-through. Same block shape in every case. Reviewers get a single, predictable structure to audit against; authors get a forcing function that catches weak framing before it hits the page.

This composes with:
- Item (1) Kerckhoffs → the rationality block's "attacker capability" line cites the threat model, not re-states it.
- Item (5) Attack classes → each class inherits a rationality template; per-covenant susceptibility derivations restate only the per-covenant specifics.
- Item (4) Watchtower reframe → becomes the first attack where the rationality block is populated, and serves as the template for the rest.

**Change.**
Add, below each attack statement in Chapter 5 (and inside each per-class subsection after item 5 is applied), a **Rationality and Scope** block with the following seven fields. The block should be compact — bullet-style, not prose paragraphs — so it reads as a spec, not an essay.

1. **Attacker capability** — what the attacker holds or can do. Key material, capital, mempool access, compute, knowledge of vault parameters (cite the Kerckhoffs assumption from item 1, do not restate it). One line per capability.

2. **Defender model** — what the defender is assumed to do and not do. Specifically: watchtower authority (proactive / reactive, which keys it holds), watchtower recovery policy (per-UTXO / batched, minimal-disruption / full-sweep), user availability (online / offline), detection-to-action latency. If the attack depends on a specific defender choice, name it and explain why a rational defender might make that choice.

3. **Economic preconditions** — the fee regime and vault value range where the attack is economically rational. State the threshold below which the attack becomes unprofitable or infeasible. Quote the relevant empirical number from Chapter 4.

4. **Protocol / network assumptions** — anything the attack requires about Bitcoin mempool, relay policy, block inclusion, RBF semantics, descendant limits, dust thresholds. If the attack depends on a specific policy value (e.g., the 25-descendant cap), name it explicitly.

5. **Scope of validity** — under what conditions the attack applies; equally importantly, under what conditions it ceases to apply. State both. "*Attack applies when X; does not apply when Y.*"

6. **Rational-attacker check** — is it economically rational for the attacker to execute? What is the payoff, what is the cost, what is the residual (liveness denial, theft, both, neither)? If the attack is not economically rational without an external incentive, say so (extortion, competition, state actor).

7. **Counter-factual mitigations** — which single assumption, if falsified, kills the attack? This is the strongest framing of what a defender could do to invalidate the attack. It also doubles as the deployment-recommendation seed for Chapter 7.

**Example populated block (for watchtower exhaustion, post-item-4 reframe):**

> **Rationality and Scope**
>
> - **Attacker capability.** Hot key. No fee key. Capital sufficient for N trigger transactions at prevailing fee rate. Mempool visibility. Knowledge of vault parameters (Kerckhoffs — §3.X).
> - **Defender model.** Watchtower holds recovery authority (keyless for CCV; `recoveryauth` for OPV). Watchtower policy: recover per-UTXO (does not batch), minimal-disruption (does not full-sweep on first unauthorized trigger). User offline during the attack window. Detection-to-action latency bounded by watchtower polling interval.
> - **Economic preconditions.** Fee rate ≥ threshold *r\** such that `vsize_recover × r* > utxo_value_floor`; empirically ~300 sat/vB for 1 BTC vaults (§4.X). Attack unprofitable below this threshold.
> - **Protocol / network assumptions.** Standard Bitcoin relay policy (dust threshold ~546 sats P2WPKH, ~330 sats P2TR). No TRUC/v3 on the recovery path.
> - **Scope of validity.** Applies when axis A2 = revault-yes (items 6) *and* defender recovery policy is per-UTXO. Does not apply to CTV/CAT+CSFS (A2 = no). Does not apply against a defender who batches recovery or does full proactive sweep.
> - **Rational-attacker check.** Net gain = funds in abandoned UTXOs post-CSV (via hot key) — cost of N trigger txs. Rational only if attacker has external incentive (competitor, extortion) or the vault value × abandonment probability clearly exceeds attack cost. Pure liveness denial is irrational without external payoff.
> - **Counter-factual mitigations.** *Single-assumption kills:* (a) watchtower adopts batched recovery → attack cost scaling becomes sub-linear, infeasible; (b) defender adopts full-sweep-on-first-alert policy → attack collapses to one round, inefficient.

**Scope of effect.**
- Every reviewer's "but what if…" question is pre-empted. The block either answers it or explicitly delimits the attack to exclude it.
- The paper's security claims become **falsifiable by the reader** — a reader can check each assumption against their own deployment model and decide whether the attack applies to them. That is what a mature security paper looks like.
- Chapter 7 (Discussion / Deployment) becomes mostly a restatement of counter-factual mitigations. Deployment advice is derived, not asserted.
- The framing naturally exposes attacks whose rationality is weak — the watchtower exhaustion issue in item (4) would have been caught by populating its rationality block honestly.
- Cross-attack comparisons become cleaner — two attacks' rationality blocks can be compared field-by-field, not sentence-by-sentence.

**Where to apply.**
- **Thesis Ch. 5 (Security Analysis):** add the seven-field Rationality and Scope block under each attack (or attack class, once item 5 is applied). Keep block prose-free — bullet form only, one sentence per bullet where possible.
- **Thesis Ch. 4 (Results):** the same block shape, with "Attack" replaced by "Measurement," applied to empirical-cost experiments. States the conditions under which a given vsize/fee number holds, so a reader cannot mis-cite the measurement outside its regime.
- **FC paper:** one compact table (not seven-field blocks) per attack — tighter real estate but same information content. Possibly a single appendix table cross-referencing attacks × assumption fields.
- **Presentation:** the rationality block does not belong on the attack slide itself — too dense. But each attack should have a companion speaker-note paragraph summarising the block, so the presenter has the assumptions cached for Q&A. This closes the loop on the advisor's earlier objections — the moment a question lands, the presenter has the rationality block in front of them and knows whether to defend, concede, or refine.
- **DESIGN.md:** the experiment catalogue's "threat model" section for each experiment should already sketch these fields; this change hardens the format and requires all seven fields filled in (or marked "N/A — does not apply to this measurement").

**Note on composition with other items.**
Item (7) is the rigour pass that makes items (1), (4), (5) readable by an adversarial reviewer. Order of application: (6) axes defined → (3) introspection primitives populated → (5) attack classes derived → (7) rationality blocks added → (4) watchtower reframe applied as the flagship example → (1) Kerckhoffs preamble (whenever methodology lands) → (2) Simplicity moved.

Without item (7), the paper's attack claims are still exposed to the "what if the defender just…" objection family. With item (7), every such objection is already answered or explicitly out of scope, and the paper's security claims acquire the falsifiability that distinguishes mature security research from cataloguing.

---

## Next steps (not yet actioned)

None of the above have been applied. Before starting:
1. Decide priority order. Recommended application order (dependency-driven, not effort-driven): **(6) → (3) → (5) → (7) → (4) → (1) → (2)**. Rationale: (6) is a precondition for (3) and (5); (5) depends on (6); (7) hardens each class subsection from (5); (4) is a specific case of (5)+(7); (1) slots in wherever methodology lands; (2) is the largest restructure but benefits from all the above.
2. Check whether current thesis/FC draft already partially addresses any of these (avoid duplication).
3. For (2), audit all tables/figures that currently include Simplicity to estimate the restructure scope.
4. For (4), audit every place the phrase "watchtower exhaustion attack" appears (thesis, FC draft, slides, DESIGN.md, experiment module docstrings) so the rename can be applied consistently.
5. Items (1), (3), (4), (5), (6), (7) are mutually reinforcing and should be applied together — partial application produces inconsistent tone across chapters (structural in some, anecdotal in others). In particular, (5) and (6) must ship together (class framing without the axes reads as ad hoc; axes without the classes leaves "*so what?*" hanging), and (7) must ship with (5) (classes without rationality blocks are still puncturable by *"what if the defender just…"*).
6. For (6), the axis labels in the proposed table are placeholders. Before applying, decide on final canonical names (e.g., whether "A1" or "Recovery-auth" reads better throughout the paper) and whether 7 axes is the right granularity or whether some should collapse (e.g., A4 and A5 into a single "destination-binding" axis with two sub-positions).
7. For (7), populate the watchtower exhaustion rationality block first (it is already scoped in item 4) and use it as the template reference for the rest. Every other attack's rationality block should be structurally identical — same seven fields, same bullet form, same terseness.
