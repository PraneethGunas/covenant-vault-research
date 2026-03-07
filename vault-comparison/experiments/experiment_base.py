"""Base infrastructure for experiments.

Provides ExperimentContext (injected state) and shared helper functions
used across multiple experiment modules to avoid duplication.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from adapters.base import VaultAdapter, VaultState, UnvaultState, TxRecord
from harness.metrics import ExperimentResult, TxMetrics
from harness.rpc import RegTestRPC


@dataclass
class ExperimentContext:
    """Injected into experiment run functions.

    Bundles the adapter, result accumulator, RPC, and experiment-specific
    parameters so that helpers don't need to pass 4+ positional args.
    """
    adapter: VaultAdapter
    result: ExperimentResult
    rpc: Any  # RegTestRPC or MockRPC
    params: Dict = field(default_factory=dict)

    def observe(self, note: str):
        """Record an observation in the result."""
        self.result.observe(note)

    def add_tx(self, metrics: TxMetrics):
        """Record a transaction metric."""
        self.result.add_tx(metrics)

    @property
    def covenant(self) -> str:
        return self.adapter.name


def make_record(label: str, txid: str, amount_sats: int) -> TxRecord:
    """Create a TxRecord from basic fields (used across experiments)."""
    return TxRecord(txid=txid, label=label, amount_sats=amount_sats)


# ── Shared lifecycle helpers ──────────────────────────────────────────


def create_and_measure_vault(ctx: ExperimentContext, amount_sats: int,
                              label: str = "tovault") -> VaultState:
    """Create a vault and record its metrics."""
    vault = ctx.adapter.create_vault(amount_sats)
    record = make_record(label, vault.vault_txid, vault.amount_sats)
    metrics = ctx.adapter.collect_tx_metrics(record, ctx.rpc)
    ctx.add_tx(metrics)
    return vault


def trigger_and_measure(ctx: ExperimentContext, vault: VaultState,
                         label: str = "unvault") -> UnvaultState:
    """Trigger unvault and record its metrics."""
    unvault = ctx.adapter.trigger_unvault(vault)
    record = make_record(label, unvault.unvault_txid, unvault.amount_sats)
    metrics = ctx.adapter.collect_tx_metrics(record, ctx.rpc)
    ctx.add_tx(metrics)
    return unvault


def withdraw_and_measure(ctx: ExperimentContext, unvault: UnvaultState,
                          path: str = "hot") -> TxRecord:
    """Complete withdrawal and record its metrics."""
    record = ctx.adapter.complete_withdrawal(unvault, path=path)
    metrics = ctx.adapter.collect_tx_metrics(record, ctx.rpc)
    ctx.add_tx(metrics)
    return record


def recover_and_measure(ctx: ExperimentContext, state) -> TxRecord:
    """Execute recovery and record its metrics."""
    record = ctx.adapter.recover(state)
    metrics = ctx.adapter.collect_tx_metrics(record, ctx.rpc)
    ctx.add_tx(metrics)
    return record


# ── Shared comparison helpers ─────────────────────────────────────────


def run_comparison_lifecycle(ctx: ExperimentContext, amount_sats: int):
    """Run a standard vault→trigger→withdraw lifecycle.

    Used by fee pinning, multi-input, and other experiments that need
    to compare the lifecycle across covenants.

    Returns (vault, unvault, withdraw_record) tuple.
    """
    vault = ctx.adapter.create_vault(amount_sats)
    unvault = ctx.adapter.trigger_unvault(vault)
    withdraw = ctx.adapter.complete_withdrawal(unvault)
    return vault, unvault, withdraw


def inspect_anchor_outputs(ctx: ExperimentContext, unvault: UnvaultState):
    """Inspect the unvault tx for anchor/fee outputs.

    Common pattern in fee_pinning and other experiments — checks if the
    unvault transaction has sub-1000 sat outputs (anchor outputs used
    for CPFP fee bumping).
    """
    try:
        info = ctx.rpc.get_tx_info(unvault.unvault_txid)
        small_outputs = []
        for vout in info.get("vout", []):
            val_sats = int(vout.get("value", 0) * 1e8)
            if val_sats < 1000:
                small_outputs.append(val_sats)
        return {
            "num_outputs": len(info.get("vout", [])),
            "small_outputs": small_outputs,
            "has_anchors": len(small_outputs) > 0,
        }
    except Exception:
        return {"num_outputs": 0, "small_outputs": [], "has_anchors": False}
