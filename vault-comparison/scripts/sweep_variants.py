"""Variant differential sweep.

Runs each variant-relevant experiment on every variant susceptible to
or differentiated by the experiment's attack class, and emits a single
matrix (Markdown + JSON) suitable for thesis/paper integration.

Variant-relevant experiment matrix:

  attack class       experiment                relevant variants
  Z2 (griefing)      recovery_griefing         all (probes the g-axis)
  Z3 (revault)       revault_amplification     partial vs atomic on a-axis
                     watchtower_exhaustion     same
  Z5 (cold theft)    cat_csfs_cold_key_recovery  cat_csfs unbound vs bound
  axis_lifecycle     lifecycle_costs           every variant

Usage:
    cd vault-comparison
    uv run scripts/sweep_variants.py
    uv run scripts/sweep_variants.py --no-switch     # current node only
    uv run scripts/sweep_variants.py --covenant ccv  # one opcode

Outputs:
    results/<timestamp>/sweep_matrix.md
    results/<timestamp>/sweep_matrix.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
ROOT = THIS_DIR.parent
sys.path.insert(0, str(ROOT))

from run import get_adapter, switch_and_init, connect_rpc, run_experiment  # noqa: E402
from harness.report import Reporter  # noqa: E402

# Per-experiment relevance: which variants we should run it on.
# Empty list => skip on this opcode.
EXPERIMENT_RELEVANCE = {
    "lifecycle_costs":          {"ctv": "all", "ccv": "all", "opvault": "all", "cat_csfs": "all"},
    "recovery_griefing":        {"ctv": "all", "ccv": "all", "opvault": "all", "cat_csfs": ["reference"]},
    "revault_amplification":    {"ccv": "all", "opvault": "all", "ctv": ["reference"], "cat_csfs": ["reference"]},
    "watchtower_exhaustion":    {"ccv": "all", "opvault": "all"},
    "cat_csfs_cold_key_recovery": {"cat_csfs": "all"},
    "cat_csfs_destination_lock":  {"cat_csfs": "all"},
}

OPCODE_ORDER = ["ctv", "cat_csfs", "ccv", "opvault"]


def _resolve_variants(adapter_cls, spec):
    if spec == "all":
        return adapter_cls.list_variants()
    return list(spec)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--covenant", default="all",
                    choices=OPCODE_ORDER + ["all"])
    ap.add_argument("--experiment", default="all",
                    help="Single experiment id or 'all'.")
    ap.add_argument("--no-switch", action="store_true",
                    help="Skip switch-node.sh; assume the right node is up.")
    args = ap.parse_args()

    if args.covenant == "all":
        opcodes = OPCODE_ORDER
    else:
        opcodes = [args.covenant]

    if args.experiment == "all":
        exps = list(EXPERIMENT_RELEVANCE.keys())
    else:
        if args.experiment not in EXPERIMENT_RELEVANCE:
            print(f"Unknown experiment '{args.experiment}'", file=sys.stderr)
            sys.exit(1)
        exps = [args.experiment]

    reporter = Reporter()
    matrix = []  # list of {experiment, opcode, variant, status, observations, transactions}

    for opcode in opcodes:
        adapter_cls = type(get_adapter(opcode))
        for exp_name in exps:
            spec = EXPERIMENT_RELEVANCE.get(exp_name, {}).get(opcode)
            if spec is None:
                continue
            variants = _resolve_variants(adapter_cls, spec)

            for variant in variants:
                # Fresh chain per variant to isolate state.
                if args.no_switch:
                    rpc = connect_rpc()
                else:
                    rpc = switch_and_init(opcode)
                try:
                    result = run_experiment(
                        exp_name, opcode, rpc, variant=variant
                    )
                    reporter.save_result(result)
                    matrix.append({
                        "experiment": exp_name,
                        "opcode": opcode,
                        "variant": variant,
                        "variant_id": result.variant,
                        "status": "OK" if not result.error else "FAIL",
                        "error": result.error,
                        "tx_count": len(result.transactions),
                        "total_vsize": result.total_vsize(),
                        "probe_outcome": _extract_probe(result),
                    })
                except Exception as e:
                    matrix.append({
                        "experiment": exp_name,
                        "opcode": opcode,
                        "variant": variant,
                        "variant_id": f"{opcode}-{variant}" if variant != "reference" else opcode,
                        "status": "CRASH",
                        "error": str(e),
                    })

    out_md = reporter.run_dir / "sweep_matrix.md"
    out_json = reporter.run_dir / "sweep_matrix.json"
    out_json.write_text(json.dumps(matrix, indent=2))
    out_md.write_text(_render_md(matrix))
    print(f"\nWrote: {out_md}")
    print(f"Wrote: {out_json}")
    return 0


def _extract_probe(result) -> str:
    for obs in result.observations:
        if "Permissionless-recovery probe:" in obs:
            return obs.split(":", 1)[1].strip()[:80]
    return ""


def _render_md(matrix) -> str:
    lines = [
        "# Variant Differential Sweep",
        "",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "| Experiment | Opcode | Variant | Status | tx | vsize | Probe |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in matrix:
        lines.append(
            f"| {row['experiment']} | {row['opcode']} | {row.get('variant_id', row['variant'])} | "
            f"{row['status']} | {row.get('tx_count', '-')} | "
            f"{row.get('total_vsize', '-')} | {row.get('probe_outcome', '')} |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
