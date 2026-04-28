"""Integration lifecycle tests for each covenant adapter.

These tests require a running Bitcoin regtest node of the appropriate type.
They are tagged @pytest.mark.integration and skipped by default in CI.

Run them explicitly with:
    uv run pytest -m integration --covenant ctv
    uv run pytest -m integration                  # all covenants (needs node switching)

Each test exercises the full adapter lifecycle:
    create_vault → trigger_unvault → complete_withdrawal (hot path)
    create_vault → trigger_unvault → recover (emergency path)

And covenant-specific extras where supported (batched trigger, revault).
"""

import os
import pytest

from adapters.base import VaultState, UnvaultState, TxRecord
from harness.rpc import RegTestRPC


# ── Helpers ──────────────────────────────────────────────────────────

def _get_rpc(wallet: str = None) -> RegTestRPC:
    """Create an RPC connection from environment or defaults."""
    return RegTestRPC.from_env(wallet=wallet)


def _skip_unless_node(adapter_name: str):
    """Skip test if the required node isn't running."""
    rpc = _get_rpc()
    try:
        rpc.getblockchaininfo()
    except Exception:
        pytest.skip(f"No Bitcoin node running for {adapter_name}")


def _mine_initial_coins(rpc: RegTestRPC, n: int = 110):
    """Mine enough blocks to have spendable coinbase outputs."""
    addr = rpc.getnewaddress()
    rpc.generatetoaddress(n, addr)


VAULT_AMOUNT = 1_000_000  # 0.01 BTC


# ── CTV Lifecycle ────────────────────────────────────────────────────

@pytest.mark.integration
class TestCTVLifecycle:
    """Full lifecycle test for the CTV adapter."""

    def _get_adapter(self):
        from adapters.ctv_adapter import CTVAdapter
        return CTVAdapter()

    def test_happy_path(self):
        """create → trigger → CSV delay → withdraw (hot)."""
        _skip_unless_node("ctv")
        rpc = _get_rpc()
        adapter = self._get_adapter()
        adapter.setup(rpc, block_delay=10)

        vault = adapter.create_vault(VAULT_AMOUNT)
        assert isinstance(vault, VaultState)
        assert vault.vault_txid
        assert vault.amount_sats > 0

        unvault = adapter.trigger_unvault(vault)
        assert isinstance(unvault, UnvaultState)
        assert unvault.unvault_txid
        assert unvault.blocks_remaining == 10

        record = adapter.complete_withdrawal(unvault, path="hot")
        assert isinstance(record, TxRecord)
        assert record.txid
        assert record.amount_sats > 0

    def test_recovery_from_unvault(self):
        """create → trigger → recover (cold sweep)."""
        _skip_unless_node("ctv")
        rpc = _get_rpc()
        adapter = self._get_adapter()
        adapter.setup(rpc, block_delay=10)

        vault = adapter.create_vault(VAULT_AMOUNT)
        unvault = adapter.trigger_unvault(vault)

        record = adapter.recover(unvault)
        assert isinstance(record, TxRecord)
        assert record.label in ("recover", "tocold")

    def test_capabilities(self):
        """CTV should not support revault or batched trigger."""
        _skip_unless_node("ctv")
        adapter = self._get_adapter()
        adapter.setup(_get_rpc(), block_delay=10)

        assert not adapter.supports_revault()
        assert not adapter.supports_batched_trigger()
        assert not adapter.supports_keyless_recovery()


# ── CCV Lifecycle ────────────────────────────────────────────────────

@pytest.mark.integration
class TestCCVLifecycle:
    """Full lifecycle test for the CCV adapter."""

    def _get_adapter(self):
        from adapters.ccv_adapter import CCVAdapter
        return CCVAdapter()

    def test_happy_path(self):
        """create → trigger → CSV delay → withdraw."""
        _skip_unless_node("ccv")
        rpc = _get_rpc()
        adapter = self._get_adapter()
        adapter.setup(rpc, locktime=10)

        vault = adapter.create_vault(VAULT_AMOUNT)
        assert isinstance(vault, VaultState)
        assert vault.vault_txid

        unvault = adapter.trigger_unvault(vault)
        assert isinstance(unvault, UnvaultState)
        assert unvault.unvault_txid

        record = adapter.complete_withdrawal(unvault, path="hot")
        assert isinstance(record, TxRecord)
        assert record.txid

    def test_recovery_from_unvault(self):
        """create → trigger → recover."""
        _skip_unless_node("ccv")
        rpc = _get_rpc()
        adapter = self._get_adapter()
        adapter.setup(rpc, locktime=10)

        vault = adapter.create_vault(VAULT_AMOUNT)
        unvault = adapter.trigger_unvault(vault)

        record = adapter.recover(unvault)
        assert isinstance(record, TxRecord)
        assert record.label == "recover"

    def test_recovery_from_vault(self):
        """create → recover (direct, no trigger)."""
        _skip_unless_node("ccv")
        rpc = _get_rpc()
        adapter = self._get_adapter()
        adapter.setup(rpc, locktime=10)

        vault = adapter.create_vault(VAULT_AMOUNT)
        record = adapter.recover(vault)
        assert isinstance(record, TxRecord)
        assert record.label == "recover"

    def test_batched_trigger(self):
        """create 2 vaults → trigger_batched → verify single UnvaultState."""
        _skip_unless_node("ccv")
        rpc = _get_rpc()
        adapter = self._get_adapter()
        adapter.setup(rpc, locktime=10)

        assert adapter.supports_batched_trigger()

        v1 = adapter.create_vault(VAULT_AMOUNT)
        v2 = adapter.create_vault(VAULT_AMOUNT)

        unvault = adapter.trigger_batched([v1, v2])
        assert isinstance(unvault, UnvaultState)
        assert unvault.unvault_txid

    def test_capabilities(self):
        """CCV should support revault, batched trigger, and keyless recovery."""
        _skip_unless_node("ccv")
        adapter = self._get_adapter()
        adapter.setup(_get_rpc(), locktime=10)

        assert adapter.supports_revault()
        assert adapter.supports_batched_trigger()
        assert adapter.supports_keyless_recovery()


# ── OP_VAULT Lifecycle ───────────────────────────────────────────────

@pytest.mark.integration
class TestOPVAULTLifecycle:
    """Full lifecycle test for the OP_VAULT adapter."""

    def _get_adapter(self):
        from adapters.opvault_adapter import OPVaultAdapter
        return OPVaultAdapter()

    def test_happy_path(self):
        """create → trigger → CSV delay → withdraw."""
        _skip_unless_node("opvault")
        rpc = _get_rpc()
        adapter = self._get_adapter()
        adapter.setup(rpc)

        vault = adapter.create_vault(VAULT_AMOUNT)
        assert isinstance(vault, VaultState)
        assert vault.vault_txid

        unvault = adapter.trigger_unvault(vault)
        assert isinstance(unvault, UnvaultState)
        assert unvault.unvault_txid

        record = adapter.complete_withdrawal(unvault, path="hot")
        assert isinstance(record, TxRecord)
        assert record.txid

    def test_recovery_from_unvault(self):
        """create → trigger → recover."""
        _skip_unless_node("opvault")
        rpc = _get_rpc()
        adapter = self._get_adapter()
        adapter.setup(rpc)

        vault = adapter.create_vault(VAULT_AMOUNT)
        unvault = adapter.trigger_unvault(vault)

        record = adapter.recover(unvault)
        assert isinstance(record, TxRecord)
        assert record.label == "recover"

    def test_capabilities(self):
        """OP_VAULT should not support revault or batched trigger."""
        _skip_unless_node("opvault")
        adapter = self._get_adapter()
        adapter.setup(_get_rpc())

        assert not adapter.supports_revault()
        assert not adapter.supports_batched_trigger()
        assert not adapter.supports_keyless_recovery()


# ── CAT+CSFS Lifecycle ──────────────────────────────────────────────

@pytest.mark.integration
class TestCATCSFSLifecycle:
    """Full lifecycle test for the CAT+CSFS adapter."""

    def _get_adapter(self):
        from adapters.cat_csfs_adapter import CATCSFSAdapter
        return CATCSFSAdapter()

    def test_happy_path(self):
        """create → trigger → CSV delay → withdraw (hot)."""
        _skip_unless_node("cat_csfs")
        rpc = _get_rpc()
        adapter = self._get_adapter()
        adapter.setup(rpc, block_delay=10)

        vault = adapter.create_vault(VAULT_AMOUNT)
        assert isinstance(vault, VaultState)
        assert vault.vault_txid

        unvault = adapter.trigger_unvault(vault)
        assert isinstance(unvault, UnvaultState)
        assert unvault.unvault_txid

        record = adapter.complete_withdrawal(unvault, path="hot")
        assert isinstance(record, TxRecord)
        assert record.txid

    def test_recovery_from_vault(self):
        """create → recover (direct cold key sweep)."""
        _skip_unless_node("cat_csfs")
        rpc = _get_rpc()
        adapter = self._get_adapter()
        adapter.setup(rpc, block_delay=10)

        vault = adapter.create_vault(VAULT_AMOUNT)
        record = adapter.recover(vault)
        assert isinstance(record, TxRecord)
        assert record.label == "recover"

    def test_recovery_from_unvault(self):
        """create → trigger → recover (cold key sweep from unvault)."""
        _skip_unless_node("cat_csfs")
        rpc = _get_rpc()
        adapter = self._get_adapter()
        adapter.setup(rpc, block_delay=10)

        vault = adapter.create_vault(VAULT_AMOUNT)
        unvault = adapter.trigger_unvault(vault)

        record = adapter.recover(unvault)
        assert isinstance(record, TxRecord)
        assert record.label == "recover"

    def test_capabilities(self):
        """CAT+CSFS should not support revault or batched trigger."""
        _skip_unless_node("cat_csfs")
        adapter = self._get_adapter()
        adapter.setup(_get_rpc(), block_delay=10)

        assert not adapter.supports_revault()
        assert not adapter.supports_batched_trigger()
        assert not adapter.supports_keyless_recovery()


# ── Variant Defences ────────────────────────────────────────────────
#
# These tests verify that variants flipping a defensive axis empirically
# defend against the corresponding attack class. Each test attempts the
# attack and asserts the on-chain outcome is rejection.

@pytest.mark.integration
class TestCATCSFSBoundDefence:
    """cat_csfs-bound (b_bound) rejects cold-key destination redirection."""

    def test_bound_rejects_redirection(self):
        """On the bound variant the recover leaf binds the destination
        via CSFS+CAT, so the chain rejects a redirected recovery at
        script verification."""
        _skip_unless_node("cat_csfs")
        from adapters.cat_csfs_adapter import CATCSFSAdapter
        from experiments.exp_cat_csfs_cold_key_recovery import _run_cold_key_recovery
        from harness.metrics import ExperimentResult

        rpc = _get_rpc()
        adapter = CATCSFSAdapter()
        adapter.setup(rpc, block_delay=10, variant="bound")

        result = ExperimentResult(experiment="cat_csfs_cold_key_recovery",
                                  covenant="cat_csfs", params={})
        try:
            _run_cold_key_recovery(adapter, result)
        except Exception:
            pass

        rejected = any("REJECTED" in (o or "") for o in result.observations)
        assert rejected, (
            "Bound variant should record on-chain rejection of the "
            "redirected recovery"
        )
        assert result.error is None, (
            f"Bound variant unexpectedly errored: {result.error}"
        )


@pytest.mark.integration
class TestCCVKeygatedDefence:
    """ccv-keygated rejects permissionless recovery (no auth key)."""

    def test_keygated_rejects_permissionless(self):
        _skip_unless_node("ccv")
        from adapters.ccv_adapter import CCVAdapter
        rpc = _get_rpc()
        adapter = CCVAdapter()
        adapter.setup(rpc, locktime=10, variant="keygated")

        vault = adapter.create_vault(VAULT_AMOUNT)
        unvault = adapter.trigger_unvault(vault)
        outcome = adapter.attempt_permissionless_recovery(unvault)
        assert outcome.startswith("REJECTED"), (
            f"keygated variant must reject permissionless recovery; got: {outcome}"
        )

    def test_reference_accepts_permissionless(self):
        _skip_unless_node("ccv")
        from adapters.ccv_adapter import CCVAdapter
        rpc = _get_rpc()
        adapter = CCVAdapter()
        adapter.setup(rpc, locktime=10, variant="reference")

        vault = adapter.create_vault(VAULT_AMOUNT)
        unvault = adapter.trigger_unvault(vault)
        outcome = adapter.attempt_permissionless_recovery(unvault)
        assert outcome == "ACCEPTED", (
            f"reference (keyless) should accept permissionless recovery; got: {outcome}"
        )


@pytest.mark.integration
class TestOPVaultAuthDefence:
    """opvault (authorised) rejects permissionless recovery; opvault-keyless
    accepts it. Chain-level proof of class \\classgrief{} susceptibility."""

    def test_authorised_rejects_permissionless(self):
        _skip_unless_node("opvault")
        from adapters.opvault_adapter import OPVaultAdapter
        rpc = _get_rpc()
        adapter = OPVaultAdapter()
        adapter.setup(rpc, block_delay=10, variant="reference")

        vault = adapter.create_vault(VAULT_AMOUNT)
        unvault = adapter.trigger_unvault(vault)
        outcome = adapter.attempt_permissionless_recovery(unvault)
        assert outcome.startswith("REJECTED"), outcome
        assert "Schnorr" in outcome or "verify" in outcome.lower(), (
            f"expected schnorr/verify rejection on chain; got: {outcome}"
        )

    def test_keyless_accepts_permissionless(self):
        _skip_unless_node("opvault")
        from adapters.opvault_adapter import OPVaultAdapter
        rpc = _get_rpc()
        adapter = OPVaultAdapter()
        adapter.setup(rpc, block_delay=10, variant="keyless")

        vault = adapter.create_vault(VAULT_AMOUNT)
        unvault = adapter.trigger_unvault(vault)
        outcome = adapter.attempt_permissionless_recovery(unvault)
        assert outcome == "ACCEPTED", outcome


@pytest.mark.integration
class TestCTVKeygatedDefence:
    """ctv-keygated rejects permissionless cold sweep; ctv reference accepts."""

    def test_keygated_rejects_permissionless(self):
        _skip_unless_node("ctv")
        from adapters.ctv_adapter import CTVAdapter
        rpc = _get_rpc()
        adapter = CTVAdapter()
        adapter.setup(rpc, block_delay=10, variant="keygated")

        vault = adapter.create_vault(VAULT_AMOUNT)
        unvault = adapter.trigger_unvault(vault)
        outcome = adapter.attempt_permissionless_recovery(unvault)
        assert outcome.startswith("REJECTED"), outcome

    def test_reference_accepts_permissionless(self):
        _skip_unless_node("ctv")
        from adapters.ctv_adapter import CTVAdapter
        rpc = _get_rpc()
        adapter = CTVAdapter()
        adapter.setup(rpc, block_delay=10, variant="reference")

        vault = adapter.create_vault(VAULT_AMOUNT)
        unvault = adapter.trigger_unvault(vault)
        outcome = adapter.attempt_permissionless_recovery(unvault)
        assert outcome == "ACCEPTED", outcome
