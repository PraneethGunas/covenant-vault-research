/**
 * cat_csfs_vault.als — CAT+CSFS (BIP-347 + BIP-348) Vault Model
 *
 * State machine:
 *   VAULTED -> UNVAULTING -> {WITHDRAWN, RECOVERED}
 *
 * CAT+CSFS semantics:
 *   - Dual-verification: OP_CHECKSIGFROMSTACK verifies signature against
 *     a stack-assembled sighash preimage, OP_CHECKSIG verifies the same
 *     key against the real transaction sighash. Both must agree.
 *   - Destination is fixed at creation via sha_single_output embedded
 *     in the script. Hot key cannot redirect outputs.
 *   - Recovery uses bare cold_pk OP_CHECKSIG with NO output constraints.
 *     Cold key compromise enables total fund theft.
 *
 * Key requirements:
 *   - VAULTED -> UNVAULTING: HotKey (dual CSFS+CHECKSIG verification)
 *   - UNVAULTING -> WITHDRAWN: HotKey + CSV delay (same dual verification)
 *   - {VAULTED, UNVAULTING} -> RECOVERED: ColdKey ONLY (bare OP_CHECKSIG,
 *     unconstrained — attacker can send funds to any address)
 *
 * No revault, no batching, fixed destination.
 * Recovery is unconstrained (weakest cold-key safety among all covenants).
 */
module cat_csfs_vault

open btc_base
open vault_base
open threat_model

-- ============================================================
-- CAT+CSFS-specific: Destination hash commitment
-- ============================================================
-- The sha_single_output hash is embedded in the script at vault creation.
-- It commits to the exact withdrawal destination. The dual-verification
-- ensures the hot key signature covers outputs matching this hash.

sig DestinationHash {
  committedAddr : one Address  -- the address committed at creation
}

-- ============================================================
-- CAT+CSFS vault UTXO subtypes
-- ============================================================

sig CATCSFSVaultedUTXO extends VaultUTXO {
  destHash : one DestinationHash  -- sha_single_output (fixed at creation)
} {
  status = VAULTED
}

sig CATCSFSUnvaultingUTXO extends VaultUTXO {
  destHash : one DestinationHash  -- inherited from vault stage
} {
  status = UNVAULTING
}

sig CATCSFSWithdrawnUTXO extends VaultUTXO {} {
  status = WITHDRAWN
}

sig CATCSFSRecoveredUTXO extends VaultUTXO {} {
  status = RECOVERED
}

-- ============================================================
-- CAT+CSFS Vault Family
-- ============================================================
sig CATCSFSVaultFamily extends VaultFamily {
  hotKey  : one Key,
  coldKey : one Key,
  destHash : one DestinationHash
} {
  hotKey = HotKey
  coldKey = ColdKey
  hotAddr.owner = HotKey
  -- Cold address ownership: cold key controls recovery destination
  -- BUT recovery is unconstrained (cold key can send ANYWHERE)
  coldAddr.owner = ColdKey
}

-- ============================================================
-- CAT+CSFS Transitions
-- ============================================================

-- Trigger: VAULTED -> UNVAULTING
-- Requires: HotKey signature (dual CSFS+CHECKSIG verification)
-- Outputs: constrained by destinationHash (CSFS preimage must match)
sig CATCSFSTrigger extends TriggerTransition {} {
  src in CATCSFSVaultedUTXO
  all d : dst | d in CATCSFSUnvaultingUTXO
  -- HotKey must sign (dual verification: CSFS + CHECKSIG)
  HotKey in txn.signers
  -- Dual verification enforces output binding:
  -- CSFS checks signature against stack-assembled preimage containing sha_single_output
  -- CHECKSIG checks same key against real sighash
  -- Both must agree → outputs are locked to destHash.committedAddr
  all d : dst | d.script = (src :> CATCSFSVaultedUTXO).destHash.committedAddr
}

-- Withdrawal: UNVAULTING -> WITHDRAWN (hot path)
-- Requires: HotKey + CSV delay (same dual CSFS+CHECKSIG verification)
sig CATCSFSWithdraw extends WithdrawTransition {} {
  src in CATCSFSUnvaultingUTXO
  all d : dst | d in CATCSFSWithdrawnUTXO
  HotKey in txn.signers
  -- Destination locked by dual verification (same as trigger)
  all d : dst | d.script = (src :> CATCSFSUnvaultingUTXO).destHash.committedAddr
}

-- Recovery: {VAULTED, UNVAULTING} -> RECOVERED (cold path)
-- Requires: ColdKey ONLY (bare OP_CHECKSIG)
-- CRITICAL: NO output constraint. Cold key holder chooses destination freely.
-- This is the fundamental weakness of CAT+CSFS recovery design.
sig CATCSFSRecover extends RecoverTransition {} {
  src.status in (VAULTED + UNVAULTING)
  all d : dst | d in CATCSFSRecoveredUTXO
  -- Cold key signature required
  ColdKey in txn.signers
  -- NO output constraint — cold key holder can send to ANY address
  -- This means recovery to AttackerAddr is possible with cold key
}

-- ============================================================
-- CAT+CSFS-specific facts
-- ============================================================

-- No revault capability
fact catcsfsNoRevault {
  all r : RevaultTransition | r.family not in CATCSFSVaultFamily
}

-- ============================================================
-- CAT+CSFS closing axioms
-- ============================================================
fact catcsfsClosingAxioms {
  all u : CATCSFSWithdrawnUTXO | one w : CATCSFSWithdraw | u in w.dst
  all u : CATCSFSRecoveredUTXO | one r : CATCSFSRecover | u in r.dst
  all u : CATCSFSUnvaultingUTXO | one t : CATCSFSTrigger | u in t.dst
}

-- ============================================================
-- CAT+CSFS transition cardinality
-- ============================================================
fact catcsfsTransitionCardinality {
  all t : CATCSFSTrigger | one (t.dst & CATCSFSUnvaultingUTXO) and #t.dst = 1
  all w : CATCSFSWithdraw | one (w.dst & CATCSFSWithdrawnUTXO) and #w.dst = 1
  all r : CATCSFSRecover | one (r.dst & CATCSFSRecoveredUTXO) and #r.dst = 1
}

-- ============================================================
-- CAT+CSFS family well-formedness
-- ============================================================
fact catcsfsFamilyWellFormedness {
  all f : CATCSFSVaultFamily |
    f.allUTXOs in (CATCSFSVaultedUTXO + CATCSFSUnvaultingUTXO +
                   CATCSFSWithdrawnUTXO + CATCSFSRecoveredUTXO)
  all u : (CATCSFSVaultedUTXO + CATCSFSUnvaultingUTXO +
           CATCSFSWithdrawnUTXO + CATCSFSRecoveredUTXO) |
    u.vaultFamily in CATCSFSVaultFamily
}

-- ============================================================
-- PROPERTY CHECKS
-- ============================================================

-- No extraction without keys (should HOLD)
assert catcsfsNoExtraction_NoKey {
  noKeyAttacker implies
    no u : CATCSFSWithdrawnUTXO | u.script = AttackerAddr
}

-- Hot key cannot redirect outputs (should HOLD — dual verification)
assert catcsfsNoExtraction_HotKeyOnly {
  catcsfsHotKeyOnly implies
    no u : (CATCSFSWithdrawnUTXO + CATCSFSRecoveredUTXO) | u.script = AttackerAddr
}

-- Cold key CAN steal funds (should find COUNTEREXAMPLE)
-- This is the key finding: unconstrained recovery = total theft
assert catcsfsNoExtraction_ColdKeyOnly {
  catcsfsColdKeyOnly implies
    no u : CATCSFSRecoveredUTXO | u.script = AttackerAddr
}

-- Destination lock holds (should HOLD)
-- All withdrawals go to the pre-committed destination
assert catcsfsDestinationLock {
  all w : CATCSFSWithdraw |
    all d : w.dst | d.script = w.family.hotAddr
}

-- CSV enforcement (should HOLD)
assert catcsfsCSVEnforced {
  all w : CATCSFSWithdraw |
    csvSatisfied[w.src, w.txn, w.src.csvDelay]
}

-- No state proliferation (should HOLD — no revault)
assert catcsfsNoStateProliferation {
  all f : CATCSFSVaultFamily |
    #f.allUTXOs <= 3
}

-- ============================================================
-- Checks
-- ============================================================

-- Safety (should hold)
check catcsfsNoExtraction_NoKey for 6 but 5 Int, 8 Time
check catcsfsNoExtraction_HotKeyOnly for 6 but 5 Int, 8 Time
check catcsfsDestinationLock for 6 but 5 Int, 8 Time
check catcsfsCSVEnforced for 6 but 5 Int, 8 Time
check catcsfsNoStateProliferation for 6 but 5 Int, 8 Time

-- Cold key vulnerability (should find counterexample)
check catcsfsNoExtraction_ColdKeyOnly for 6 but 5 Int, 8 Time

-- ============================================================
-- Instance generation
-- ============================================================

pred catcsfsNormalLifecycle {
  some f : CATCSFSVaultFamily |
    some t : CATCSFSTrigger | t.family = f and
    some w : CATCSFSWithdraw | w.family = f
}
run catcsfsNormalLifecycle for 6 but 5 Int, 8 Time

-- Cold key theft scenario: attacker recovers to their own address
pred catcsfsRecoveryTheft {
  catcsfsColdKeyOnly
  some f : CATCSFSVaultFamily |
    some r : CATCSFSRecover | r.family = f and
    some d : r.dst | d.script = AttackerAddr
}
run catcsfsRecoveryTheft for 6 but 5 Int, 8 Time

-- Recovery scenario (legitimate)
pred catcsfsRecoveryScenario {
  some f : CATCSFSVaultFamily |
    some t : CATCSFSTrigger | t.family = f and
    some r : CATCSFSRecover | r.family = f
}
run catcsfsRecoveryScenario for 6 but 5 Int, 8 Time
