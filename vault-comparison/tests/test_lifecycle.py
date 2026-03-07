"""Verify the MockAdapter implements the full lifecycle correctly."""

from adapters.base import VaultState, UnvaultState, TxRecord


def test_full_lifecycle(mock_adapter):
    vault = mock_adapter.create_vault(100_000)
    assert vault.vault_txid.startswith("vault_")
    assert vault.amount_sats == 99_700

    unvault = mock_adapter.trigger_unvault(vault)
    assert unvault.blocks_remaining == 10
    assert unvault.amount_sats == 99_500

    withdrawal = mock_adapter.complete_withdrawal(unvault)
    assert withdrawal.label == "withdraw"
    assert withdrawal.amount_sats == 99_300


def test_recovery_from_vault(mock_adapter):
    vault = mock_adapter.create_vault(100_000)
    recovery = mock_adapter.recover(vault)
    assert recovery.label == "recover"
    assert recovery.amount_sats == vault.amount_sats - 200


def test_recovery_from_unvault(mock_adapter):
    vault = mock_adapter.create_vault(100_000)
    unvault = mock_adapter.trigger_unvault(vault)
    recovery = mock_adapter.recover(unvault)
    assert recovery.label == "recover"
    assert recovery.amount_sats == unvault.amount_sats - 200


def test_multiple_vaults_get_unique_txids(mock_adapter):
    v1 = mock_adapter.create_vault(100_000)
    v2 = mock_adapter.create_vault(200_000)
    assert v1.vault_txid != v2.vault_txid


def test_capabilities_default(mock_adapter):
    assert not mock_adapter.supports_revault()
    assert not mock_adapter.supports_batched_trigger()
    assert not mock_adapter.supports_keyless_recovery()


def test_capabilities_override(mock_adapter_with_revault):
    assert mock_adapter_with_revault.supports_revault()
    assert mock_adapter_with_revault.supports_batched_trigger()
    assert not mock_adapter_with_revault.supports_keyless_recovery()


def test_collect_tx_metrics(mock_adapter, mock_rpc):
    vault = mock_adapter.create_vault(100_000)
    unvault = mock_adapter.trigger_unvault(vault)
    withdrawal = mock_adapter.complete_withdrawal(unvault)
    metrics = mock_adapter.collect_tx_metrics(withdrawal, mock_rpc)
    assert metrics.label == "withdraw"
    assert metrics.vsize == 200
    assert metrics.fee_sats == 300


def test_extra_state_propagated(mock_adapter):
    vault = mock_adapter.create_vault(100_000)
    assert vault.extra["mock_plan"] is True
    assert vault.extra["step"] == 1

    unvault = mock_adapter.trigger_unvault(vault)
    assert unvault.extra["step"] == 2
    assert unvault.extra["mock_plan"] is True
