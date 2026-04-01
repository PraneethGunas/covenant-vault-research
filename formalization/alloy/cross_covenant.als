/**
 * cross_covenant.als — Cross-Covenant Composition Analysis
 *
 * Models interactions between different vault types co-existing on
 * the same blockchain. Imports ALL concrete vault modules to ensure
 * covenant guards are active (not abstract).
 *
 * Properties modeled:
 * 1. Cross-vault input injection: CTV trigger tx consuming a CCV vault
 *    UTXO as an additional input (CTV doesn't commit to input prevouts).
 * 2. Fee wallet contention: shared fee wallet across OP_VAULT instances.
 * 3. Revault-to-dust termination: splitting attack fixed point.
 */
module cross_covenant

open btc_base
open vault_base
open threat_model
open ctv_vault
open ccv_vault
open opvault_vault

-- ============================================================
-- PROPERTY 9: Cross-vault input injection
-- ============================================================
-- CTV does not commit to input prevouts (BIP-119 §4). A CTV-locked
-- transaction can consume ANY set of inputs as long as outputs match
-- the template. If a CCV vault UTXO is included as an additional input,
-- and the CCV spending conditions happen to be satisfied (e.g., via
-- mode confusion or keypath bypass), funds from both vaults are consumed.

-- A transaction consuming inputs from different vault families
sig CrossVaultTx extends Tx {
  ctvInput   : one CTVVaultedUTXO,  -- input governed by CTV
  extraInput : one CCVVaultUTXO     -- input from a CCV vault
} {
  ctvInput in inputs
  extraInput in inputs
  ctvInput != extraInput
  ctvInput.vaultFamily != extraInput.vaultFamily
}

-- Can a CTV trigger tx pull in a CCV vault UTXO?
-- For this to work, the CCV UTXO must be spendable. This requires either:
-- (a) Mode confusion: CCV uses undefined mode → OP_SUCCESS bypasses checks
-- (b) Keypath bypass: CCV contract uses real pubkey instead of NUMS
pred crossInputInjection {
  some t : CrossVaultTx |
    t.ctvInput.status = VAULTED and
    t.extraInput.status = VAULTED and
    -- The CCV input has a vulnerability allowing it to be spent
    -- without proper CCV covenant enforcement
    (some c : t.extraInput.contract |
      not c.isNUMS or  -- keypath bypass: real pubkey allows keypath spend
      some m : CCVModeBypassed | m.src = t.extraInput)  -- mode confusion
}

-- Assertion: cross-vault injection should not be possible if both
-- vaults are correctly configured (NUMS internal key, no mode confusion)
assert noCrossVaultInjection {
  -- With proper CCV configuration, the extra input cannot be spent
  -- without satisfying CCV guards, which a CTV tx doesn't do
  all t : CrossVaultTx |
    let ccvUtxo = t.extraInput |
      ccvUtxo.contract.isNUMS and
      no m : CCVModeBypassed | m.src = ccvUtxo
}

-- ============================================================
-- PROPERTY 10: Revault-to-Dust Termination
-- ============================================================
-- The splitting attack creates progressively smaller UTXOs via revault.
-- Does it terminate at the dust threshold?

fun dustThreshold : Int { 2 }  -- abstract proxy for 546 sats

pred isDust[u: UTXO] {
  u.value <= dustThreshold
}

-- Does every chain of revaults eventually produce a dust UTXO?
pred splittingTerminates {
  all f : (CCVVaultFamily + OPVaultFamily) |
    (#{r : RevaultTransition | r.family = f} > 2) implies
      some u : f.allUTXOs | isDust[u]
}

-- Can an attacker craft splits that stay above dust indefinitely?
pred indefiniteSplitting {
  some f : (CCVVaultFamily + OPVaultFamily) |
    #{r : RevaultTransition | r.family = f} > 3 and
    all u : f.allUTXOs | not isDust[u]
}

-- ============================================================
-- PROPERTY 11: Fee wallet contention (OP_VAULT specific)
-- ============================================================
-- Two OP_VAULT families sharing a single fee wallet. Recovery of one
-- family can block recovery of the other if both need the same fee UTXO.

pred feeWalletContention {
  #{OPVaultFamily} >= 2
  #{FeeWallet.utxos} = 1  -- scarce fee resource
  some disj f1, f2 : OPVaultFamily |
    -- Both families need to recover simultaneously
    some r1 : OPVaultRecover | r1.family = f1 and
    some r2 : OPVaultRecover | r2.family = f2 and
    -- Both compete for the same fee UTXO
    r1.feeInput = r2.feeInput
}

-- Assertion: fee contention does not prevent recovery within CSV window
assert noRecoveryBlockedByContention {
  all disj f1, f2 : OPVaultFamily |
    #{FeeWallet.utxos} = 1 implies
      -- At least one family can always recover
      (some r : OPVaultRecover | r.family = f1) or
      (some r : OPVaultRecover | r.family = f2)
}

-- ============================================================
-- Mixed vault chain: CTV + CCV on same blockchain
-- ============================================================
pred mixedVaultChain {
  some f1 : CTVVaultFamily |
    some u1 : f1.allUTXOs | u1.status = VAULTED
  some f2 : CCVVaultFamily |
    some u2 : f2.allUTXOs | u2.status = VAULTED
}

-- ============================================================
-- CHECKS
-- ============================================================

-- Cross-vault injection (should HOLD if CCV properly configured)
check noCrossVaultInjection for 10 but 5 Int, 12 Time

-- Fee contention (should find counterexample — both families block each other)
check noRecoveryBlockedByContention for 10 but 5 Int, 12 Time

-- Splitting
run splittingTerminates for 10 but 5 Int, 12 Time
run indefiniteSplitting for 10 but 5 Int, 12 Time

-- Scenarios
run mixedVaultChain for 10 but 5 Int, 12 Time
run feeWalletContention for 10 but 5 Int, 12 Time
run crossInputInjection for 10 but 5 Int, 12 Time
