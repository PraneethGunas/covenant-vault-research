"""Shared fixtures for vault-comparison tests.

The MockAdapter simulates a complete vault lifecycle without any Bitcoin node.
It returns deterministic, realistic-looking data so that experiments can run
against it in CI.  Every TxRecord gets a fake txid, every VaultState gets
a fake extra dict, and mine_blocks is a no-op.
"""
import pytest
from typing import Dict, List, Optional

from adapters.base import VaultAdapter, VaultState, UnvaultState, TxRecord, TxMetrics
from harness.rpc import RegTestRPC


class MockRPC:
    """Fake RPC that records calls and returns canned responses.

    Every method call is recorded in self.calls as (method_name, args, kwargs).
    Default responses are set via self.responses[method_name] = return_value.
    """
    def __init__(self):
        self.calls: List[tuple] = []
        self.responses: Dict[str, object] = {
            "getblockcount": 100,
            "sendrawtransaction": "aa" * 32,
            "generatetoaddress": ["bb" * 32],
            "getrawtransaction": {"hex": "00" * 100, "vsize": 200, "weight": 800},
        }

    def __getattr__(self, name):
        def mock_method(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return self.responses.get(name, None)
        return mock_method


class MockAdapter(VaultAdapter):
    """Minimal adapter for testing experiment logic without Bitcoin.

    Configurable via constructor kwargs:
        vault_amount:   sats returned by create_vault (default 100_000)
        supports:       dict of capability overrides
    """

    def __init__(self, vault_amount=100_000, supports=None):
        self._vault_amount = vault_amount
        self._counter = 0
        self._supports = supports or {}

    @property
    def name(self) -> str:
        return "mock"

    @property
    def node_mode(self) -> str:
        return "mock"

    @property
    def description(self) -> str:
        return "Mock adapter for testing"

    def setup(self, rpc, block_delay=10, **kwargs):
        self.rpc = rpc
        self.block_delay = block_delay

    def create_vault(self, amount_sats):
        self._counter += 1
        return VaultState(
            vault_txid=f"vault_{self._counter:04d}_" + "aa" * 28,
            amount_sats=amount_sats - 300,  # Simulate fee deduction
            extra={"mock_plan": True, "step": 1},
        )

    def trigger_unvault(self, vault):
        self._counter += 1
        return UnvaultState(
            unvault_txid=f"unvlt_{self._counter:04d}_" + "bb" * 28,
            amount_sats=vault.amount_sats - 200,
            blocks_remaining=self.block_delay,
            extra={**(vault.extra or {}), "step": 2},
        )

    def complete_withdrawal(self, unvault, path="hot"):
        self._counter += 1
        return TxRecord(
            txid=f"wdrw_{self._counter:04d}_" + "cc" * 29,
            label="withdraw" if path == "hot" else "cold_sweep",
            raw_hex="00" * 150,
            amount_sats=unvault.amount_sats - 200,
        )

    def recover(self, state):
        self._counter += 1
        src = state.amount_sats if hasattr(state, "amount_sats") else 0
        return TxRecord(
            txid=f"rcvr_{self._counter:04d}_" + "dd" * 29,
            label="recover",
            raw_hex="00" * 100,
            amount_sats=src - 200,
        )

    def supports_revault(self):
        return self._supports.get("revault", False)

    def supports_batched_trigger(self):
        return self._supports.get("batched_trigger", False)

    def supports_keyless_recovery(self):
        return self._supports.get("keyless_recovery", False)

    def mine_blocks(self, n: int) -> None:
        """No-op for mock adapter."""
        pass

    def collect_tx_metrics(self, record: TxRecord, rpc) -> TxMetrics:
        """Return deterministic metrics without RPC."""
        return TxMetrics(
            label=record.label,
            txid=record.txid,
            vsize=200,
            weight=800,
            fee_sats=300,
            num_inputs=1,
            num_outputs=2,
            amount_sats=record.amount_sats,
        )


@pytest.fixture
def mock_rpc():
    return MockRPC()


@pytest.fixture
def mock_adapter(mock_rpc):
    adapter = MockAdapter()
    adapter.setup(mock_rpc)
    return adapter


@pytest.fixture
def mock_adapter_with_revault(mock_rpc):
    adapter = MockAdapter(supports={"revault": True, "batched_trigger": True})
    adapter.setup(mock_rpc)
    return adapter
