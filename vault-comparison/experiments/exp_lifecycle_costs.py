"""FRAMING TAGS (conference/AXES.md canonical reference)
    Class: Axis measurement (not an attack class)
    Enabling axis-value: A3, A4, A5 consequences on transaction vsize
    Susceptible covenants: N/A
    Immune covenants: N/A
    Notes: Baseline lifecycle vsize measurements. Foundation for all class cost-function computations.
    (Full Rationality-and-Scope block: Thesis Appendix D; FC Appendix B.2.)
"""

"""Experiment A: Vault Lifecycle Transaction Costs

Measures the on-chain cost of the complete vault lifecycle for each
covenant type: deposit → unvault → withdrawal.

This is the foundational comparison — every vault design must support
this basic flow, and the transaction sizes directly determine the
minimum cost of using the vault.

Metrics collected:
- vsize and weight of each transaction in the lifecycle
- Fee paid at each step
- Total lifecycle cost
- Script types used (bare CTV, P2WSH, P2TR, etc.)
- Number of inputs/outputs per step
"""

from adapters.base import VaultAdapter
from harness.metrics import ExperimentResult, TxMetrics
from harness.rpc import RegTestRPC
from harness.regtest_caveats import emit_vsize_is_primary, emit_regtest_caveats
from experiments.registry import register


VAULT_AMOUNT = 49_999_900  # sats


@register(
    name="lifecycle_costs",
    description="Full vault lifecycle transaction sizes and fees",
    tags=["core", "comparative", "quantitative"],
)
def run(adapter: VaultAdapter) -> ExperimentResult:
    result = ExperimentResult(
        experiment="lifecycle_costs",
        covenant=adapter.name,
        params={"vault_amount_sats": VAULT_AMOUNT},
    )

    rpc = adapter.rpc

    try:
        # Step 1: Create vault
        vault = adapter.create_vault(VAULT_AMOUNT)
        tovault_record = _make_record("tovault", vault.vault_txid, vault.amount_sats)
        tovault_metrics = adapter.collect_tx_metrics(tovault_record, rpc)
        result.add_tx(tovault_metrics)
        result.observe(f"Vault created: {vault.vault_txid[:16]}... ({vault.amount_sats} sats)")

        # Step 2: Trigger unvault
        unvault = adapter.trigger_unvault(vault)
        unvault_record = _make_record("unvault", unvault.unvault_txid, unvault.amount_sats)
        unvault_metrics = adapter.collect_tx_metrics(unvault_record, rpc)
        result.add_tx(unvault_metrics)
        result.observe(f"Unvault triggered: {unvault.unvault_txid[:16]}... (timelock: {unvault.blocks_remaining} blocks)")

        # Step 3: Complete withdrawal
        withdraw_record = adapter.complete_withdrawal(unvault)
        withdraw_metrics = adapter.collect_tx_metrics(withdraw_record, rpc)
        result.add_tx(withdraw_metrics)
        result.observe(f"Withdrawal complete: {withdraw_record.txid[:16]}... via {withdraw_record.label}")

        result.observe(f"Total lifecycle vsize: {result.total_vsize()} vbytes")
        result.observe(f"Total lifecycle fees: {result.total_fees()} sats")

        # Attribution: lifecycle model and threat vocabulary
        result.observe(
            "PRIOR ART: The deposit→unvault→withdraw lifecycle model follows "
            "Swambo et al. [SHMB20] ('Custody Protocols Using Bitcoin Vaults', "
            "arXiv:2005.11776), who formalized vault state transitions and the "
            "watchtower monitoring assumption.  Our contribution is empirical "
            "measurement of transaction sizes across four covenant designs under "
            "a uniform adapter interface — prior analyses used hand-estimated vsizes."
        )

    except Exception as e:
        result.error = str(e)
        result.observe(f"FAILED: {e}")

    emit_regtest_caveats(
        result,
        experiment_specific=(
            "Lifecycle vsize measurements are fully valid on regtest — the "
            "script structure and witness sizes are identical to mainnet.  "
            "Fee amounts are regtest artifacts; multiply vsize by prevailing "
            "mainnet fee rate for real-world cost estimates.  "
            "DETERMINISM NOTE: vsize is structurally deterministic for a given "
            "script template and input count.  The same covenant design with "
            "the same key configuration produces identical vsize regardless "
            "of vault amount, block height, or fee environment.  This is "
            "because vsize depends only on: (1) the scriptPubKey structure "
            "(fixed per covenant design), (2) the witness program (fixed per "
            "key configuration), and (3) the number of inputs/outputs (fixed "
            "per vault operation).  We verified this independence in "
            "watchtower_exhaustion (trigger/recover vsize stable across 50 "
            "splits with balance ranging from 50M to <1K sats, range=0 vB) "
            "and in lifecycle_costs (single-run is sufficient because the "
            "measurement is deterministic, not statistical)."
        ),
    )
    return result


def _make_record(label, txid, amount):
    from adapters.base import TxRecord
    return TxRecord(txid=txid, label=label, amount_sats=amount)
