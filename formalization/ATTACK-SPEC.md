# Attack Specification — Bitcoin Covenant Vaults

Formal attack descriptions with measured costs and proofs.
Reference companion to `covenant-vault-paper.tex`.

All vsize values measured on Bitcoin regtest. Fee projections use
V = 50,000,000 sats (0.5 BTC) as the reference vault balance.

---

## Notation

| Symbol | Definition |
|--------|------------|
| V | Vault balance (sats) |
| r | Fee rate (sat/vB) |
| delta | Timelock parameter (blocks) |
| v_x | Transaction vsize (vB) for transaction type x |
| K_A | Adversary key set |

---

## Measured Transaction Sizes

| Transaction         | CTV (vB) | CCV (vB) | OPV (vB) |
|---------------------|----------|----------|----------|
| Deposit             | 122      | 300      | 154      |
| Trigger             | 94       | 154      | 292      |
| Withdraw            | 152      | 111      | 121      |
| Recover             | 133      | 122      | 246      |
| Trigger-and-Revault | N/A      | 162      | 292      |
| **Total lifecycle** | **368**  | **565**  | **567**  |

---

## Attack 1: Fee Pinning (TM1)

**Applies to:** CTV only
**Adversary:** K_A = {k_fee}
**Violated property:** LIVENESS

### Mechanism

The adversary constructs a chain of 24 descendant transactions from the
anchor output of the cold sweep transaction (tocold, 133 vB). Bitcoin Core's
descendant limit (25 transactions per parent) blocks any additional CPFP
child on any output of the pinned transaction. The limit applies
per-parent transaction, not per-output — pinning vout[1] blocks CPFP
on vout[0].

Since CTV commits to the transaction template (preventing RBF), the
defender has no fee-bumping mechanism.

### Cost

```
C_pin(r) = 24 * (110r + 546) = 2,640r + 13,104 sats
```

| r (sat/vB) | Pin cost (sats) | % of vault |
|------------|-----------------|------------|
| 1          | 15,744          | 0.032%     |
| 10         | 39,504          | 0.082%     |
| 50         | 145,104         | 0.307%     |
| 100        | 277,104         | 0.587%     |
| 300        | 805,104         | 1.709%     |
| 500        | 1,333,104       | 2.830%     |

### Escalation

With K_A = {k_hot, k_fee}, fund safety is violated.
Total theft cost: C_pin(r) + 94r sats.

### Immunity

- **CCV:** No anchor outputs; fees paid directly from vault balance.
- **OP_VAULT:** Fee-wallet UTXO pattern, not an anchor chain.

### Mitigation

TRUC/v3 transactions (Bitcoin Core PRs #28948, #29496) restrict descendant
chains to 1 transaction, eliminating this vector.

---

## Attack 2: Recovery Griefing (TM2)

**Applies to:** All three (different entry barriers)
**Violated property:** GRIEF-RESIST

### Adversary Requirements

| Design | Required keys | Entry barrier |
|--------|---------------|---------------|
| CCV    | K_A = {} (none) | Any network participant |
| OPV    | K_A = {k_recoveryauth} | Significant |
| CTV    | K_A = {k_hot} | Significant |

### Mechanism

The adversary front-runs legitimate trigger transactions by broadcasting
recovery transactions to the same vault UTXO. The defender must re-trigger
after each griefing recovery. The cost asymmetry per round:

```
R = v_defender / v_attacker
```

### Griefing Ratios

| Design | Defender tx (vB) | Attacker tx (vB) | R     |
|--------|------------------|-------------------|-------|
| CCV    | 154 (trigger)    | 122 (recover)     | 1.262 |
| OPV    | 292 (trigger)    | 246 (recover)     | 1.187 |
| CTV    | 94 (trigger)     | 133 (sweep)       | 0.707 |

CCV is uniquely vulnerable: the 1.26x ratio applies with K_A = {},
meaning any network participant can impose net costs on the vault owner.
The ratio is fee-invariant (both costs scale linearly with r).

CTV's ratio is inverted (0.707 < 1): the attacker pays MORE per round
than the defender. This makes CTV griefing economically irrational at
all fee rates, though it still imposes operational disruption.

### Cumulative Costs

| r (sat/vB) | Rounds | CCV defender | OPV defender | CTV defender |
|------------|--------|-------------|-------------|-------------|
| 10         | 100    | 154,000     | 292,000     | 94,000      |
| 100        | 10     | 154,000     | 292,000     | 94,000      |
| 100        | 100    | 1,540,000   | 2,920,000   | 940,000     |
| 500        | 10     | 770,000     | 1,460,000   | 470,000     |

---

## Attack 3: Watchtower Exhaustion (TM4)

**Applies to:** CCV, OP_VAULT (CTV is immune — no revault)
**Adversary:** K_A = {k_trigger}
**Violated property:** STATE-BOUND, LIVENESS

### Mechanism

The adversary repeatedly calls trigger-and-revault, splitting the vault
into a cascade of dust-valued unvaulting UTXOs (546 sats each). The
watchtower must individually recover each before its delta-block timelock
expires.

### Split Count

```
N_split(V, r) = floor(V / (v_trigger * r + 546))
```

where v_trigger = 162 vB (CCV) or 292 vB (OPV).

### Irrationality Threshold

Recovery becomes irrational when the recovery fee exceeds the UTXO value:

```
v_recover * r > 546
```

- **CCV:** r > 546/122 = 4.48 sat/vB
- **OPV:** r > 546/246 = 2.22 sat/vB

Above these thresholds, dust-valued splits cost more to recover than they
contain. The watchtower must either abandon them or spend irrationally.

### Projected Split Counts (V = 0.5 BTC)

| r (sat/vB) | CCV splits | CCV recover/split | OPV splits | OPV recover/split |
|------------|------------|-------------------|------------|-------------------|
| 1          | ~409,000   | 122 sats          | ~171,000   | 246 sats          |
| 10         | ~27,000    | 1,220 sats        | ~14,000    | 2,460 sats        |
| 50         | 5,783      | 6,100 sats        | 3,301      | 12,300 sats       |
| 100        | 2,942      | 12,200 sats       | 1,682      | 24,600 sats       |
| 500        | 598        | 61,000 sats       | 342        | 123,000 sats      |

### Batching Mitigation

Consolidating multiple recoveries into a single transaction amortizes
per-recovery overhead. At batch size 100, per-input recovery cost decreases
by up to 46% (CCV) and 36% (OPV). This extends the viable fee range but
does not eliminate the fundamental attack.

---

## Impossibility 1: Griefing–Safety Tradeoff

No covenant vault protocol simultaneously achieves:

1. **Permissionless recoverability:** Fund safety under loss of any strict
   subset of keys.
2. **Griefing resistance:** Bounded adversary advantage with K_A = {}.

### Proof (exhaustive case analysis)

**Case 1: Recovery is permissionless.**
Any network participant can invoke recovery. Repeated recovery against each
trigger imposes v_trigger * r per round on the defender. The griefing game
is sustainable indefinitely.
- CCV: measured ratio 154/122 = 1.262.
- Property (2) is violated.

**Case 2: Recovery requires a key k_rec.**
Loss of k_rec disables recovery. If the trigger key is also compromised,
the vault can be triggered but never recovered, escalating to fund loss
after delta blocks.
- OPV: loss of k_recoveryauth with compromised k_trigger violates fund safety.
- Property (1) is violated.

No third case exists. Recovery is either permissionless or key-gated.

### Design Space Parameterization

Recovery authorization level alpha in [0, 1]:
- alpha = 0: fully keyless (CCV)
- alpha ~ 0.5: template-based (CTV)
- alpha = 1: fully authorized (OPV)

Griefing resistance increases monotonically with alpha.
Key-loss safety decreases monotonically with alpha.

---

## Impossibility 2: Fee-Dependent Security Inversion

The security ordering of CTV vs CCV/OPV is not total. It inverts with the
fee environment.

### Attack Cost Functions

```
A_CTV(r) = 2,640r + 13,104                (fee pinning, TM1)
A_CCV(r) = V / (162r + 546) * 122r        (watchtower exhaustion, TM4)
A_OPV(r) = V / (292r + 546) * 246r        (watchtower exhaustion, TM4)
```

### Crossover

r* ~ 50-100 sat/vB (for V = 0.5 BTC).

| Fee regime | Dominant vulnerability                       | Safer designs |
|------------|----------------------------------------------|---------------|
| r < r*     | CTV fee pinning (trivially cheap)             | CCV, OPV      |
| r > r*     | CCV/OPV watchtower exhaustion (dust irrecoverable) | CTV      |

### Proof Sketch

A_CTV(r) is linear in r with slope 2,640. Even at r = 500, the pin cost is
2.83% of vault value. The attack is effective at all fee rates.

A_CCV(r) and A_OPV(r) represent total watchtower recovery costs. As r
increases: (a) fewer splits are needed (each trigger is more expensive),
but (b) each recovery is also more expensive, and (c) dust splits become
irrational to recover (v_recover * r > 546 for r > 4.48).

Below r*, CTV fee pinning is the dominant vulnerability (trivially cheap,
requires only k_fee). Above r*, CCV/OPV watchtower exhaustion dominates
(dust splits are irrecoverable, requires only k_trigger).

There is no universally safest vault.

---

## Deployment Guidance

| Environment | Recommendation | Rationale |
|-------------|----------------|-----------|
| Low fees (< 10 sat/vB) | CCV or OPV | CTV fee pinning < 16,000 sats for 0.5 BTC vault; watchtower exhaustion infeasible (hundreds of thousands of splits) |
| High fees (> 100 sat/vB) | CTV | No revault surface; watchtower recovers single UTXO; CCV/OPV dust splits irrecoverable |
| Mixed/uncertain | OPV | Authorized recovery prevents keyless griefing; three-key separation; cost: +35.6% operational overhead |
