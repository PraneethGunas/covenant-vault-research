"""Sweep table generation — extract labeled TxMetrics into scaling tables.

Takes an ExperimentResult containing multiple data points (labeled
"batch_1_total", "batch_2_total", etc.) and produces comparison tables
for the paper.

Supports N-covenant comparisons (CTV, CCV, OP_VAULT, CAT+CSFS, or any
subset).  The legacy two-argument functions (build_comparison_table,
comparison_csv) are preserved as wrappers for backward compatibility.
"""

import re
from typing import Dict, List, Optional, Tuple

from harness.metrics import ExperimentResult, TxMetrics


# Display names for covenant identifiers
COVENANT_LABELS = {
    "ctv": "CTV",
    "ccv": "CCV",
    "opvault": "OPV",
    "cat_csfs": "CATCSFS",
}


def _label(cov: str) -> str:
    """Get display label for a covenant identifier."""
    return COVENANT_LABELS.get(cov, cov.upper())


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
    | N | vsize | weight | fee (sats) | inputs | outputs |
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


# ── N-covenant comparison ────────────────────────────────────────────


def build_multi_comparison_table(
    results: Dict[str, ExperimentResult],
    label_pattern: str,
    param_name: str = "N",
) -> str:
    """Build a side-by-side scaling table for N covenants.

    Args:
        results: dict mapping covenant name → ExperimentResult
        label_pattern: e.g. "batch_{}_total"
        param_name: label for the sweep variable column

    Returns markdown table with columns for each covenant's vsize and fee.
    """
    if not results:
        return "No results to compare"

    # Extract sweep points per covenant
    covenant_points = {}
    all_vals = set()
    covenants = sorted(results.keys())
    for cov in covenants:
        pts = dict(extract_sweep_points(results[cov], label_pattern))
        covenant_points[cov] = pts
        all_vals.update(pts.keys())

    all_vals = sorted(all_vals)
    if not all_vals:
        return f"No data points matching '{label_pattern}'"

    # Build header
    vsize_cols = " | ".join(f"{_label(c)} vsize" for c in covenants)
    fee_cols = " | ".join(f"{_label(c)} fee" for c in covenants)
    header = f"| {param_name} | {vsize_cols} | {fee_cols} |"
    sep_parts = ["------"] + ["----------"] * len(covenants) + ["----------"] * len(covenants)
    sep = "|" + "|".join(sep_parts) + "|"

    lines = [header, sep]

    for val in all_vals:
        vsize_vals = []
        fee_vals = []
        for cov in covenants:
            tx = covenant_points[cov].get(val)
            vsize_vals.append(str(tx.vsize) if tx else "—")
            fee_vals.append(str(tx.fee_sats) if tx else "—")

        row = f"| {val} | " + " | ".join(vsize_vals) + " | " + " | ".join(fee_vals) + " |"
        lines.append(row)

    return "\n".join(lines)


def multi_comparison_csv(
    results: Dict[str, ExperimentResult],
    label_pattern: str,
    param_name: str = "n",
) -> str:
    """Export N-covenant side-by-side CSV for plotting.

    Args:
        results: dict mapping covenant name → ExperimentResult
        label_pattern: e.g. "batch_{}_total"
        param_name: label for the sweep variable column

    Returns CSV with columns: n, <cov1>_vsize, <cov2>_vsize, ..., <cov1>_fee, ...
    """
    if not results:
        return ""

    covenant_points = {}
    all_vals = set()
    covenants = sorted(results.keys())
    for cov in covenants:
        pts = dict(extract_sweep_points(results[cov], label_pattern))
        covenant_points[cov] = pts
        all_vals.update(pts.keys())

    all_vals = sorted(all_vals)
    if not all_vals:
        return ""

    # Header
    cols = [param_name]
    for cov in covenants:
        cols.append(f"{cov}_vsize")
    for cov in covenants:
        cols.append(f"{cov}_fee")
    lines = [",".join(cols)]

    for val in all_vals:
        row = [str(val)]
        for cov in covenants:
            tx = covenant_points[cov].get(val)
            row.append(str(tx.vsize) if tx else "")
        for cov in covenants:
            tx = covenant_points[cov].get(val)
            row.append(str(tx.fee_sats) if tx else "")
        lines.append(",".join(row))

    return "\n".join(lines)


# ── Single-result CSV export ─────────────────────────────────────────


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


# ── Legacy two-covenant wrappers (backward compat) ───────────────────


def build_comparison_table(
    ctv_result: ExperimentResult,
    ccv_result: ExperimentResult,
    label_pattern: str,
    param_name: str = "N",
) -> str:
    """Build a side-by-side CTV vs CCV scaling table.

    Legacy wrapper — use build_multi_comparison_table for N-covenant support.
    """
    return build_multi_comparison_table(
        {"ctv": ctv_result, "ccv": ccv_result},
        label_pattern,
        param_name,
    )


def comparison_csv(
    ctv_result: ExperimentResult,
    ccv_result: ExperimentResult,
    label_pattern: str,
    param_name: str = "n",
) -> str:
    """Export side-by-side CSV for plotting both covenants.

    Legacy wrapper — use multi_comparison_csv for N-covenant support.
    """
    return multi_comparison_csv(
        {"ctv": ctv_result, "ccv": ccv_result},
        label_pattern,
        param_name,
    )
