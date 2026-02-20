"""Regtest Limitations and Fee Sensitivity Analysis

All experiments in this framework run on Bitcoin Core regtest.  This module
emits standardized caveats about what regtest can and cannot demonstrate,
and provides a fee sensitivity table that translates structural vsize
measurements into economic costs under different fee environments.

The key insight: regtest is valid for measuring STRUCTURAL costs (vsize,
weight, witness size, script complexity) but INVALID for measuring
ECONOMIC or TEMPORAL dynamics (fee markets, mempool competition, mining
delays, relay policy effects).

Every security experiment should call emit_regtest_caveats() in its
output to make these limitations explicit.
"""

from harness.metrics import ExperimentResult

# Standard fee rate scenarios for sensitivity analysis (sat/vB)
FEE_RATE_SCENARIOS = [1, 10, 50, 100, 300, 500]


def emit_regtest_caveats(result: ExperimentResult, experiment_specific: str = "") -> None:
    """Emit standardized regtest limitation caveats into an experiment result.

    Args:
        result: The ExperimentResult to annotate.
        experiment_specific: Optional experiment-specific caveat text that
            explains which findings are affected and how.
    """
    result.observe("\n=== Regtest Limitations ===")

    result.observe(
        "VALIDITY SCOPE: This experiment runs on Bitcoin Core regtest.  "
        "The vsize and weight measurements are structurally valid — they "
        "reflect the true on-chain cost of each transaction type under "
        "the current script and witness structure.  However, regtest "
        "cannot simulate the following mainnet dynamics:"
    )

    result.observe(
        "(1) NO MEMPOOL COMPETITION.  Regtest mines every transaction "
        "immediately (or on demand).  Attacks that depend on mempool "
        "dynamics — fee pinning, front-running via mempool observation, "
        "recovery races against timelocks — lose their temporal "
        "realism.  On mainnet, a recovery transaction must confirm "
        "before the CSV timelock expires, competing for block space "
        "against all other pending transactions."
    )

    result.observe(
        "(2) NO RELAY POLICY.  Bitcoin Core's relay policy (minimum "
        "relay fee, ancestor/descendant limits, RBF rules, TRUC/v3 "
        "transaction semantics) constrains transaction propagation on "
        "mainnet but does not meaningfully constrain regtest operations.  "
        "Fee pinning attacks depend entirely on relay policy details — "
        "the descendant chain limit (25 txs / 101 kvB) and RBF "
        "replacement rules.  While regtest enforces these limits in "
        "its mempool, the absence of competing traffic means the "
        "constraints are never stressed."
    )

    result.observe(
        "(3) NO FEE MARKET.  Transaction fees on regtest are arbitrary — "
        "miners accept anything above the dust relay threshold.  The "
        "fee amounts reported by these experiments are whatever the "
        "adapter's coin selection happened to set, NOT what a rational "
        "miner would demand on mainnet.  The vsize measurements are "
        "valid as structural costs; the fee amounts are artifacts."
    )

    result.observe(
        "(4) MINING IS INSTANT.  The block_delay / spend_delay parameter "
        "(e.g. 10 blocks ≈ 100 minutes on mainnet) resolves in "
        "milliseconds on regtest.  Time-critical attacks — the "
        "defender's recovery race, the attacker's sustained splitting, "
        "the griefing loop — lose all temporal realism.  We cannot "
        "empirically measure whether a watchtower can detect and "
        "respond to an attack within the CSV window under real latency."
    )

    result.observe(
        "METHODOLOGY: We treat vsize as the PRIMARY metric and fees as "
        "vsize × fee_rate, where fee_rate is an EXOGENOUS parameter.  "
        "Each economic analysis includes a fee sensitivity table showing "
        "how the threat model's rationality condition shifts across fee "
        "environments.  This separates what we CAN measure on regtest "
        "(structural transaction costs) from what we CANNOT (fee market "
        "dynamics)."
    )

    if experiment_specific:
        result.observe(f"EXPERIMENT-SPECIFIC: {experiment_specific}")


def emit_fee_sensitivity_table(
    result: ExperimentResult,
    threat_model_name: str,
    vsize_rows: list,
    vault_amount_sats: int = 0,
    fee_rates: list = None,
) -> None:
    """Emit a fee sensitivity table for one or more transaction types.

    Args:
        result: The ExperimentResult to annotate.
        threat_model_name: Name of the threat model this table serves.
        vsize_rows: List of dicts, each with:
            - "label": str — row label (e.g. "attacker_trigger", "defender_recovery")
            - "vsize": int — measured vsize in vbytes
            - "description": str — what this transaction does
        vault_amount_sats: If >0, include a "rounds to exhaust vault" row.
        fee_rates: Override default fee rate scenarios.
    """
    rates = fee_rates or FEE_RATE_SCENARIOS

    result.observe(f"\n--- Fee Sensitivity: {threat_model_name} ---")
    result.observe(
        "All costs below are vsize × fee_rate.  vsize is empirically "
        "measured; fee_rate is an exogenous parameter."
    )

    # Header
    rate_headers = " | ".join(f"{r:>6} s/vB" for r in rates)
    result.observe(f"{'Transaction':>25} | {'vsize':>6} | {rate_headers}")
    result.observe("-" * (36 + 13 * len(rates)))

    # Rows
    for row in vsize_rows:
        label = row["label"]
        vsize = row["vsize"]
        costs = " | ".join(f"{vsize * r:>10,}" for r in rates)
        result.observe(f"{label:>25} | {vsize:>4} vB | {costs}")

    # If we have exactly two rows (attacker/defender), show the ratio
    if len(vsize_rows) == 2:
        v0 = vsize_rows[0]["vsize"]
        v1 = vsize_rows[1]["vsize"]
        if v1 > 0:
            ratio = v0 / v1
            result.observe(
                f"{'cost ratio (row1/row2)':>25} | {'':>6} | "
                + " | ".join(f"{ratio:>10.2f}x" for _ in rates)
            )

    # Vault exhaustion analysis
    if vault_amount_sats > 0 and len(vsize_rows) >= 2:
        # Assume second row is the defender cost
        defender_vsize = vsize_rows[1]["vsize"]
        result.observe(f"\n{'Rounds to exhaust vault':>25} | {'':>6} | ", )
        result.observe(
            f"  (vault = {vault_amount_sats:,} sats, "
            f"defender pays {defender_vsize} vB/round)"
        )
        exhaustion = " | ".join(
            f"{vault_amount_sats // (defender_vsize * r):>10,}" if defender_vsize * r > 0 else f"{'∞':>10}"
            for r in rates
        )
        result.observe(f"{'rounds to exhaust':>25} | {'':>6} | {exhaustion}")

    result.observe("")  # blank line separator


def emit_vsize_is_primary(result: ExperimentResult) -> None:
    """Short reminder that vsize is the meaningful metric, not fee amounts."""
    result.observe(
        "NOTE: The fee amounts in sats above are artifacts of regtest's "
        "coin selection, not economically meaningful.  The vsize values "
        "are the structurally valid measurements.  To compute real-world "
        "costs, multiply vsize by the prevailing mainnet fee rate."
    )
