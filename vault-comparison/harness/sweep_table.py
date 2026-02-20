"""Sweep table generation — extract labeled TxMetrics into scaling tables.

Takes an ExperimentResult containing multiple data points (labeled
"batch_1_total", "batch_2_total", etc.) and produces comparison tables
for the paper.
"""

import re
from typing import Dict, List, Optional, Tuple

from harness.metrics import ExperimentResult, TxMetrics


def extract_sweep_points(
    result: ExperimentResult,
    label_pattern: str,
) -> List[Tuple[int, TxMetrics]]:
    """Extract TxMetrics matching a pattern like 'batch_{}_total'.

    The {} placeholder captures the sweep variable (converted to int).
    Returns sorted list of (sweep_value, TxMetrics).
    """
    # Convert "batch_{}_total" to regex "batch_(\d+)_total"
    regex = re.compile(label_pattern.replace("{}", r"(\d+)"))
    points = []
    for tx in result.transactions:
        m = regex.match(tx.label)
        if m:
            points.append((int(m.group(1)), tx))
    return sorted(points, key=lambda x: x[0])


def build_scaling_table(
    result: ExperimentResult,
    label_pattern: str,
    param_name: str = "N",
) -> str:
    """Build a markdown table from sweep points in one ExperimentResult.

    Returns a table like:
    | N | vsize | weight | fee (sats) | marginal vsize |
    """
    points = extract_sweep_points(result, label_pattern)
    if not points:
        return f"No data points matching '{label_pattern}'"

    lines = []
    lines.append(f"| {param_name} | vsize | weight | fee (sats) | inputs | outputs |")
    lines.append("|------|-------|--------|------------|--------|---------|")

    prev_vsize = 0
    for val, tx in points:
        lines.append(
            f"| {val} | {tx.vsize} | {tx.weight} | {tx.fee_sats} "
            f"| {tx.num_inputs} | {tx.num_outputs} |"
        )
        prev_vsize = tx.vsize

    return "\n".join(lines)


def build_comparison_table(
    ctv_result: ExperimentResult,
    ccv_result: ExperimentResult,
    label_pattern: str,
    param_name: str = "N",
) -> str:
    """Build a side-by-side CTV vs CCV scaling table.

    Returns:
    | N | CTV vsize | CCV vsize | Savings % | CTV fee | CCV fee |
    """
    ctv_points = dict(extract_sweep_points(ctv_result, label_pattern))
    ccv_points = dict(extract_sweep_points(ccv_result, label_pattern))

    all_vals = sorted(set(ctv_points.keys()) | set(ccv_points.keys()))
    if not all_vals:
        return f"No data points matching '{label_pattern}'"

    lines = []
    lines.append(
        f"| {param_name} | CTV vsize | CCV vsize | Savings % "
        f"| CTV fee (sats) | CCV fee (sats) |"
    )
    lines.append("|------|-----------|-----------|-----------|----------------|----------------|")

    for val in all_vals:
        ctv_tx = ctv_points.get(val)
        ccv_tx = ccv_points.get(val)

        ctv_vs = ctv_tx.vsize if ctv_tx else "—"
        ccv_vs = ccv_tx.vsize if ccv_tx else "—"
        ctv_fee = ctv_tx.fee_sats if ctv_tx else "—"
        ccv_fee = ccv_tx.fee_sats if ccv_tx else "—"

        if isinstance(ctv_vs, int) and isinstance(ccv_vs, int) and ctv_vs > 0:
            savings = f"{(1.0 - ccv_vs / ctv_vs) * 100:.1f}%"
        else:
            savings = "—"

        lines.append(
            f"| {val} | {ctv_vs} | {ccv_vs} | {savings} "
            f"| {ctv_fee} | {ccv_fee} |"
        )

    return "\n".join(lines)


def to_csv(
    result: ExperimentResult,
    label_pattern: str,
    param_name: str = "n",
) -> str:
    """Export sweep points as CSV for matplotlib/plotting."""
    points = extract_sweep_points(result, label_pattern)
    if not points:
        return ""

    lines = [f"{param_name},vsize,weight,fee_sats,num_inputs,num_outputs,feerate_sat_vb"]
    for val, tx in points:
        lines.append(
            f"{val},{tx.vsize},{tx.weight},{tx.fee_sats},"
            f"{tx.num_inputs},{tx.num_outputs},{tx.feerate_sat_vb():.2f}"
        )
    return "\n".join(lines)


def comparison_csv(
    ctv_result: ExperimentResult,
    ccv_result: ExperimentResult,
    label_pattern: str,
    param_name: str = "n",
) -> str:
    """Export side-by-side CSV for plotting both covenants."""
    ctv_points = dict(extract_sweep_points(ctv_result, label_pattern))
    ccv_points = dict(extract_sweep_points(ccv_result, label_pattern))
    all_vals = sorted(set(ctv_points.keys()) | set(ccv_points.keys()))

    if not all_vals:
        return ""

    lines = [f"{param_name},ctv_vsize,ccv_vsize,ctv_fee,ccv_fee,savings_pct"]
    for val in all_vals:
        ctv_tx = ctv_points.get(val)
        ccv_tx = ccv_points.get(val)
        ctv_vs = ctv_tx.vsize if ctv_tx else ""
        ccv_vs = ccv_tx.vsize if ccv_tx else ""
        ctv_fee = ctv_tx.fee_sats if ctv_tx else ""
        ccv_fee = ccv_tx.fee_sats if ccv_tx else ""

        if ctv_vs and ccv_vs and ctv_vs > 0:
            savings = f"{(1.0 - ccv_vs / ctv_vs) * 100:.1f}"
        else:
            savings = ""

        lines.append(f"{val},{ctv_vs},{ccv_vs},{ctv_fee},{ccv_fee},{savings}")

    return "\n".join(lines)
