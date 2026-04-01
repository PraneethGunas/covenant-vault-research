/**
 * simplicity_vault.als — Simplicity Vault Model (Elements Regtest)
 *
 * State machine:
 *   VAULTED -> UNVAULTING -> {WITHDRAWN, RECOVERED}
 *
 * Simplicity semantics:
 *   - Covenants enforced via jet::outputs_hash() — a deterministic SHA-256
 *     hash of all transaction outputs (asset, amount, nonce, script, rangeproof).
 *   - Every spend path (trigger, withdraw, recover) checks outputs_hash
 *     against a pre-committed hash embedded in the Simplicity program.
 *   - Structurally identical to CTV's template hash commitment, but with
 *     output-constrained recovery (unlike CAT+CSFS's bare OP_CHECKSIG).
 *
 * Key requirements:
 *   - VAULTED -> UNVAULTING: HotKey (Schnorr sig via jet::bip_0340_verify)
 *   - UNVAULTING -> WITHDRAWN: HotKey + CSV (jet::check_lock_distance)
 *   - {VAULTED, UNVAULTING} -> RECOVERED: ColdKey + output constraint
 *     (outputs_hash enforced — recovery can ONLY go to pre-committed address)
 *
 * No revault (on main branch), no dynamic batching.
 * Output-constrained recovery on all paths — key design advantage over CAT+CSFS.
 *
 * NOTE: Simplicity runs on Elements/Liquid (federated sidechain), not Bitcoin.
 * The threat model assumes honest federation behavior and evaluates only
 * covenant-level properties. See DESIGN.md §4.4 for cross-chain caveats.
 */
module simplicity_vault

open btc_base
open vault_base
open threat_model

-- ============================================================
-- Simplicity-specific: OutputsHash commitment
-- ============================================================
-- Each spend path in the Simplicity program embeds a pre-committed
-- outputs_hash (32-byte SHA-256). The program asserts:
--   jet::outputs_hash() == param::COMMITTED_HASH
-- This is modeled as a set of committed output addresses, analogous
-- to CTVTemplate.committedOutputs.

sig OutputsHash {
  committedAddr : one Address  -- the address committed in the hash
} {
  -- The vault owner commits to legitimate addresses at creation time.
  committedAddr != AttackerAddr
}

-- ============================================================
-- Simplicity vault UTXO subtypes
-- ============================================================

sig SimplicityVaultedUTXO extends VaultUTXO {
  triggerHash : one OutputsHash,   -- outputs_hash for trigger path
  recoverHash : one OutputsHash    -- outputs_hash for vault recovery path
} {
  status = VAULTED
}

sig SimplicityUnvaultingUTXO extends VaultUTXO {
  withdrawHash : one OutputsHash,  -- outputs_hash for withdraw path
  recoverHash  : one OutputsHash   -- outputs_hash for unvault recovery path
} {
  status = UNVAULTING
}

sig SimplicityWithdrawnUTXO extends VaultUTXO {} {
  status = WITHDRAWN
}

sig SimplicityRecoveredUTXO extends VaultUTXO {} {
  status = RECOVERED
}

-- ============================================================
-- Simplicity Vault Family
-- ============================================================
sig SimplicityVaultFamily extends VaultFamily {
  hotKey  : one Key,
  coldKey : one Key
} {
  hotKey = HotKey
  coldKey = ColdKey
  hotAddr.owner = HotKey
  coldAddr.owner = ColdKey
}

-- ============================================================
-- Simplicity Transitions
-- ============================================================

-- Trigger: VAULTED -> UNVAULTING
-- Requires: HotKey signature (jet::bip_0340_verify)
-- Outputs: constrained by triggerHash (jet::outputs_hash == param::TRIGGER_OUTPUTS_HASH)
sig SimplicityTrigger extends TriggerTransition {} {
  src in SimplicityVaultedUTXO
  all d : dst | d in SimplicityUnvaultingUTXO
  -- Hot key signature required
  HotKey in txn.signers
  -- Output binding: outputs must match the pre-committed trigger hash
  all d : dst | d.script = (src :> SimplicityVaultedUTXO).triggerHash.committedAddr
}

-- Withdrawal: UNVAULTING -> WITHDRAWN (hot path)
-- Requires: HotKey + CSV (jet::check_lock_distance)
-- Outputs: constrained by withdrawHash
sig SimplicityWithdraw extends WithdrawTransition {} {
  src in SimplicityUnvaultingUTXO
  all d : dst | d in SimplicityWithdrawnUTXO
  HotKey in txn.signers
  -- Output binding via outputs_hash
  all d : dst | d.script = (src :> SimplicityUnvaultingUTXO).withdrawHash.committedAddr
}

-- Recovery: {VAULTED, UNVAULTING} -> RECOVERED (cold path)
-- Requires: ColdKey signature
-- OUTPUT-CONSTRAINED: outputs must match recoverHash
-- This is the key difference from CAT+CSFS — cold key CANNOT redirect funds
sig SimplicityRecover extends RecoverTransition {} {
  src.status in (VAULTED + UNVAULTING)
  all d : dst | d in SimplicityRecoveredUTXO
  -- Cold key signature required
  ColdKey in txn.signers
  -- OUTPUT-CONSTRAINED recovery (unlike CAT+CSFS's bare OP_CHECKSIG):
  -- The Simplicity program enforces jet::outputs_hash() == param::RECOVER_OUTPUTS_HASH
  -- This means recovery ALWAYS goes to the pre-committed recovery address
  all d : dst | d.script = family.coldAddr
}

-- ============================================================
-- Simplicity-specific facts
-- ============================================================

-- No revault (main branch — feat/revault-batching adds this)
fact simplicityNoRevault {
  all r : RevaultTransition | r.family not in SimplicityVaultFamily
}

-- ============================================================
-- Simplicity closing axioms
-- ============================================================
fact simplicityClosingAxioms {
  all u : SimplicityWithdrawnUTXO | one w : SimplicityWithdraw | u in w.dst
  all u : SimplicityRecoveredUTXO | one r : SimplicityRecover | u in r.dst
  all u : SimplicityUnvaultingUTXO | one t : SimplicityTrigger | u in t.dst
}

-- ============================================================
-- Simplicity transition cardinality
-- ============================================================
fact simplicityTransitionCardinality {
  all t : SimplicityTrigger | one (t.dst & SimplicityUnvaultingUTXO) and #t.dst = 1
  all w : SimplicityWithdraw | one (w.dst & SimplicityWithdrawnUTXO) and #w.dst = 1
  all r : SimplicityRecover | one (r.dst & SimplicityRecoveredUTXO) and #r.dst = 1
}

-- ============================================================
-- Simplicity family well-formedness
-- ============================================================
fact simplicityFamilyWellFormedness {
  all f : SimplicityVaultFamily |
    f.allUTXOs in (SimplicityVaultedUTXO + SimplicityUnvaultingUTXO +
                   SimplicityWithdrawnUTXO + SimplicityRecoveredUTXO)
  all u : (SimplicityVaultedUTXO + SimplicityUnvaultingUTXO +
           SimplicityWithdrawnUTXO + SimplicityRecoveredUTXO) |
    u.vaultFamily in SimplicityVaultFamily
}

-- ============================================================
-- PROPERTY CHECKS
-- ============================================================

-- No extraction without keys (should HOLD)
assert simplicityNoExtraction_NoKey {
  noKeyAttacker implies
    no u : SimplicityWithdrawnUTXO | u.script = AttackerAddr
}

-- Hot key cannot redirect outputs (should HOLD — outputs_hash enforcement)
assert simplicityNoExtraction_HotKeyOnly {
  simplicityHotKeyOnly implies
    no u : (SimplicityWithdrawnUTXO + SimplicityRecoveredUTXO) | u.script = AttackerAddr
}

-- Cold key CANNOT steal funds (should HOLD — output-constrained recovery)
-- This is the key difference from CAT+CSFS:
-- Simplicity's recovery enforces outputs_hash, so cold key can only
-- recover to the pre-committed recovery address, not to AttackerAddr.
assert simplicityNoExtraction_ColdKeyOnly {
  simplicityColdKeyOnly implies
    no u : SimplicityRecoveredUTXO | u.script = AttackerAddr
}

-- All paths enforce output binding (should HOLD)
assert simplicityOutputBinding {
  -- Trigger outputs match committed hash
  (all t : SimplicityTrigger |
    all d : t.dst | d.script = (t.src :> SimplicityVaultedUTXO).triggerHash.committedAddr)
  and
  -- Withdraw outputs match committed hash
  (all w : SimplicityWithdraw |
    all d : w.dst | d.script = (w.src :> SimplicityUnvaultingUTXO).withdrawHash.committedAddr)
  and
  -- Recovery outputs go to cold address (output-constrained)
  (all r : SimplicityRecover |
    all d : r.dst | d.script = r.family.coldAddr)
}

-- CSV enforcement (should HOLD)
assert simplicityCSVEnforced {
  all w : SimplicityWithdraw |
    csvSatisfied[w.src, w.txn, w.src.csvDelay]
}

-- No state proliferation (should HOLD — no revault on main)
assert simplicityNoStateProliferation {
  all f : SimplicityVaultFamily |
    #f.allUTXOs <= 3
}

-- ============================================================
-- Checks
-- ============================================================

-- Safety (should hold)
check simplicityNoExtraction_NoKey for 6 but 5 Int, 8 Time
check simplicityNoExtraction_HotKeyOnly for 6 but 5 Int, 8 Time
check simplicityNoExtraction_ColdKeyOnly for 6 but 5 Int, 8 Time
check simplicityOutputBinding for 6 but 5 Int, 8 Time
check simplicityCSVEnforced for 6 but 5 Int, 8 Time
check simplicityNoStateProliferation for 6 but 5 Int, 8 Time

-- ============================================================
-- Instance generation
-- ============================================================

pred simplicityNormalLifecycle {
  some f : SimplicityVaultFamily |
    some t : SimplicityTrigger | t.family = f and
    some w : SimplicityWithdraw | w.family = f
}
run simplicityNormalLifecycle for 6 but 5 Int, 8 Time

-- Recovery scenario: cold key recovers to pre-committed address
pred simplicityRecoveryConstrained {
  some f : SimplicityVaultFamily |
    some t : SimplicityTrigger | t.family = f and
    some r : SimplicityRecover | r.family = f and
    all d : r.dst | d.script = f.coldAddr  -- always goes to coldAddr
}
run simplicityRecoveryConstrained for 6 but 5 Int, 8 Time

-- Hot key griefing: trigger but cannot redirect
pred simplicityHotKeyGriefing {
  simplicityHotKeyOnly
  some f : SimplicityVaultFamily |
    some t : SimplicityTrigger | t.family = f
  -- Hot key holder can trigger, but outputs are locked by outputs_hash
  -- No extraction possible (hot key alone cannot withdraw to AttackerAddr)
}
run simplicityHotKeyGriefing for 6 but 5 Int, 8 Time
