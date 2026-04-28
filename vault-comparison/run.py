#!/usr/bin/env python3
"""Vault Comparison Runner

CLI entry point for running comparative experiments across CTV, CCV,
and OP_VAULT vault implementations.

Usage:
    # List available experiments
    uv run run.py list

    # Run a single experiment (auto-switches node + initializes regtest)
    uv run run.py run lifecycle_costs --covenant ctv

    # Run on all covenants (CTV → CCV → OP_VAULT → CAT+CSFS → Simplicity)
    uv run run.py run lifecycle_costs --covenant all

    # Run all core experiments across all covenants
    uv run run.py run --tag core --covenant all

    # Run all experiments on all covenants
    uv run run.py run --all --covenant all

    # Skip node switching (node already running)
    uv run run.py run lifecycle_costs --covenant ctv --no-switch

    # Compare previously saved results
    uv run run.py compare results/20260218_143000_lifecycle_costs

Node switching:
    By default, `run` automatically calls switch-node.sh to start the
    correct Bitcoin node and initializes regtest (wallet + blocks).
    Use --no-switch to skip this if the node is already running.

    - CTV experiments        → Bitcoin Inquisition (switch-node.sh inquisition)
    - CCV experiments        → Merkleize Bitcoin (switch-node.sh ccv)
    - OP_VAULT experiments   → jamesob/bitcoin opvault (switch-node.sh opvault)
    - Simplicity experiments → Elements + electrs (switch-node.sh elements)

    RPC connection is configured via environment variables or .env file:
    - RPC_HOST (default: localhost)
    - RPC_PORT (default: 18443)
    - RPC_USER (default: rpcuser)
    - RPC_PASSWORD (default: rpcpass)
"""

import argparse
import json
import subprocess
import sys
import os
import time
import threading
from pathlib import Path


# ── ANSI colors (disabled if not a TTY) ──────────────────────
_USE_COLOR = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text

def _dim(t):     return _c("2", t)
def _bold(t):    return _c("1", t)
def _green(t):   return _c("32", t)
def _red(t):     return _c("31", t)
def _yellow(t):  return _c("33", t)
def _cyan(t):    return _c("36", t)
def _magenta(t): return _c("35", t)
def _blue(t):    return _c("34", t)

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from harness.rpc import RegTestRPC, RPCError
from harness.metrics import ExperimentResult, ComparisonResult
from harness.report import Reporter
from experiments.registry import EXPERIMENTS, get_experiment
# Force-import all experiment modules so @register decorators fire
import experiments.exp_lifecycle_costs
import experiments.exp_address_reuse
import experiments.exp_fee_pinning
import experiments.exp_revault_amplification
import experiments.exp_multi_input
import experiments.exp_recovery_griefing

import experiments.exp_watchtower_exhaustion
import experiments.exp_fee_sensitivity
import experiments.exp_opvault_recovery_auth
import experiments.exp_opvault_trigger_key_theft
import experiments.exp_ccv_mode_bypass
import experiments.exp_cat_csfs_hot_key_theft
import experiments.exp_cat_csfs_witness_manipulation
import experiments.exp_cat_csfs_destination_lock
import experiments.exp_cat_csfs_cold_key_recovery


def get_adapter(covenant: str):
    """Instantiate the adapter for the given covenant type."""
    if covenant == "ctv":
        from adapters.ctv_adapter import CTVAdapter
        return CTVAdapter()
    elif covenant == "ccv":
        from adapters.ccv_adapter import CCVAdapter
        return CCVAdapter()
    elif covenant == "opvault":
        from adapters.opvault_adapter import OPVaultAdapter
        return OPVaultAdapter()
    elif covenant == "cat_csfs":
        from adapters.cat_csfs_adapter import CATCSFSAdapter
        return CATCSFSAdapter()
    elif covenant == "simplicity":
        from adapters.simplicity_adapter import SimplicityAdapter
        return SimplicityAdapter()
    else:
        raise ValueError(f"Unknown covenant type: {covenant}")


def connect_rpc() -> RegTestRPC:
    """Build an RPC connection from environment, falling back to cookie auth."""
    rpc = RegTestRPC.from_env()
    try:
        rpc._call("getblockchaininfo")
    except Exception:
        # Env-based auth failed — try cookie auth (needed for opvault node)
        try:
            rpc = RegTestRPC.from_cookie()
            rpc._call("getblockchaininfo")
        except Exception as e:
            print(f"WARNING: RPC connection check failed: {e}", file=sys.stderr)
            return rpc
    info = rpc._call("getblockchaininfo")
    chain = info.get("chain", "unknown")
    blocks = info.get("blocks", 0)
    print(f"Connected to {chain} node at block {blocks}")
    return rpc


COVENANT_TO_NODE = {
    "ctv": "inquisition",
    "ccv": "ccv",
    "opvault": "opvault",
    "cat_csfs": "inquisition",
    "simplicity": "elements",
}
SWITCH_SCRIPT = PROJECT_ROOT.parent / "switch-node.sh"


def do_init(rpc: RegTestRPC, blocks: int = 300):
    """Initialize regtest: create wallet + mine blocks.

    Works with both wallet-enabled (CCV/Merkleize) and no-wallet
    (CTV/Inquisition) node builds automatically.
    """
    wallet_name = os.getenv("WALLET_NAME", "testwallet")
    has_wallet = True

    print(f"  Initializing regtest ({blocks} blocks)...")

    # Try to create/load wallet — CTV nodes may not have wallet support
    try:
        rpc._call("createwallet", wallet_name)
        print(f"    Created wallet '{wallet_name}'")
    except RPCError as e1:
        if e1.code == -32601:
            has_wallet = False
            print(f"    No wallet support (CTV/Inquisition build)")
        else:
            try:
                rpc._call("loadwallet", wallet_name)
                print(f"    Loaded existing wallet '{wallet_name}'")
            except RPCError as e2:
                if e2.code == -32601:
                    has_wallet = False
                    print(f"    No wallet support (CTV/Inquisition build)")
                else:
                    try:
                        loaded = rpc._call("listwallets")
                        if wallet_name in loaded:
                            print(f"    Wallet '{wallet_name}' already loaded")
                        else:
                            print(f"    WARNING: Could not create/load wallet: {e1} / {e2}")
                    except Exception:
                        has_wallet = False
                        print(f"    Could not set up wallet: {e1}")
    except Exception as e1:
        has_wallet = False
        print(f"    Wallet setup skipped: {e1}")

    # Mine initial blocks
    if has_wallet:
        wallet_rpc = RegTestRPC(
            host=rpc.host, port=rpc.port,
            user=rpc.user, password=rpc.password,
            wallet=wallet_name,
        )
        addr = wallet_rpc._call("getnewaddress")
        rpc._call("generatetoaddress", blocks, addr)
        print(f"    Mined {blocks} blocks to wallet address")
    else:
        dummy_addr = "bcrt1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqdku202"
        try:
            rpc._call("generatetoaddress", blocks, dummy_addr)
            print(f"    Mined {blocks} blocks to dummy address (no-wallet mode)")
        except Exception as e:
            print(f"    WARNING: Could not mine blocks: {e}")
            print(f"    CTV experiments mine blocks on-the-fly, so this may be OK.")

    # Verify
    info = rpc._call("getblockchaininfo")
    print(f"    Chain height: {info['blocks']}  ✓")


def switch_and_init(covenant: str, blocks: int = 300) -> RegTestRPC:
    """Switch to the correct Bitcoin node and initialize regtest.

    1. Calls switch-node.sh to stop current node, wipe regtest, start target
    2. Waits for RPC to become available
    3. Creates wallet + mines initial blocks
    4. Returns a connected RegTestRPC instance
    """
    node_mode = COVENANT_TO_NODE[covenant]

    if not SWITCH_SCRIPT.exists():
        print(f"ERROR: switch-node.sh not found at {SWITCH_SCRIPT}", file=sys.stderr)
        print(f"Expected location: {SWITCH_SCRIPT}", file=sys.stderr)
        print(f"Use --no-switch if the correct node is already running.", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'─'*60}")
    print(f"Switching to {node_mode} node for {covenant.upper()} experiments...")
    print(f"{'─'*60}")

    result = subprocess.run(
        ["bash", str(SWITCH_SCRIPT), node_mode],
        capture_output=False,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: switch-node.sh exited with code {result.returncode}", file=sys.stderr)
        sys.exit(1)

    # Connect and initialize
    if covenant == "simplicity":
        # Elements RPC — auto-discover ports from simplex regtest
        from adapters.simplicity_adapter import discover_simplex_ports
        rpc_port, _, rpc_user, rpc_pass = discover_simplex_ports()
        rpc = RegTestRPC(
            host="127.0.0.1",
            port=rpc_port,
            user=rpc_user,
            password=rpc_pass,
        )
        info = rpc._call("getblockchaininfo")
        print(f"Connected to Elements {info.get('chain', 'unknown')} at block {info.get('blocks', 0)}")
        # Skip do_init for Elements — simplex regtest seeds its own wallet
        # and coins. Creating a second wallet breaks the single-wallet RPC path
        # that the vault-cli depends on.
    else:
        rpc = connect_rpc()
        do_init(rpc, blocks=blocks)
    return rpc


class _Spinner:
    """Live progress indicator that overwrites itself on the same line."""
    _FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, message: str):
        self._msg = message
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        i = 0
        while not self._stop.is_set():
            frame = self._FRAMES[i % len(self._FRAMES)]
            sys.stderr.write(f"\r  {frame} {self._msg}")
            sys.stderr.flush()
            i += 1
            self._stop.wait(0.12)
        # Clear the spinner line
        sys.stderr.write(f"\r{' ' * (len(self._msg) + 6)}\r")
        sys.stderr.flush()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)


def run_experiment(name: str, covenant: str, rpc: RegTestRPC,
                   adapter=None, verbose: bool = False,
                   variant: str = "") -> ExperimentResult:
    """Run a single experiment against a single covenant.

    If `adapter` is provided, reuses it (preserving the coin pool).
    Otherwise creates and sets up a fresh adapter.

    Console output is compact by default (one-line summary per experiment).
    Use verbose=True for full observation dump.
    """
    spec = get_experiment(name)
    if spec is None:
        print(f"ERROR: Unknown experiment '{name}'", file=sys.stderr)
        print(f"Available: {', '.join(sorted(EXPERIMENTS.keys()))}", file=sys.stderr)
        sys.exit(1)

    if adapter is None:
        adapter = get_adapter(covenant)
        adapter.setup(rpc, variant=variant) if variant else adapter.setup(rpc)

    # Show a spinner while the experiment runs
    cov_upper = adapter.name.upper()
    spinner = _Spinner(f"{cov_upper} | {spec.name} ...")
    spinner.start()
    try:
        result = spec.run_fn(adapter)
    finally:
        spinner.stop()

    # Backfill variant from adapter (experiments that don't set it explicitly).
    if hasattr(adapter, "variant") and adapter.variant:
        result.variant = adapter.variant

    # ── Console output ─────────────────────────────────────────
    cov_label = _cyan(adapter.name.upper().ljust(11))
    exp_label = _bold(spec.name.ljust(32))

    if result.error:
        status = _red("FAIL")
        print(f"  {cov_label} {_dim('│')} {exp_label} {_dim('│')} {status} {_dim('│')} {_red(_first_line(result.error))}")
    elif result.transactions:
        total_vsize = result.total_vsize()
        tx_count = len(result.transactions)
        status = _green("OK  ")
        print(f"  {cov_label} {_dim('│')} {exp_label} {_dim('│')} {status} {_dim('│')} {tx_count} tx, total={_bold(str(total_vsize)+'vB')}")
        # Transaction table
        measured = [(m.label, m.vsize) for m in result.transactions if m.vsize and m.vsize > 0]
        if measured:
            max_label = max(len(l) for l, _ in measured)
            for label, vsize in measured:
                print(f"             {_dim('│')}   {_dim(f'{label:<{max_label}}')}  {_magenta(f'{vsize:>6}')} {_dim('vB')}")
    else:
        first_obs = result.observations[0] if result.observations else ""
        if "skip" in first_obs.lower():
            status = _yellow("SKIP")
            print(f"  {cov_label} {_dim('│')} {exp_label} {_dim('│')} {status} {_dim('│')}")
        else:
            n_obs = len(result.observations)
            status = _green("OK  ")
            print(f"  {cov_label} {_dim('│')} {exp_label} {_dim('│')} {status} {_dim('│')} {n_obs} observations")

    # ── Findings ──────────────────────────────────────────────
    _NOISE = (
        "=== Regtest", "VALIDITY SCOPE:", "(1) NO MEMPOOL", "(2) NO RELAY",
        "(3) NO FEE MARKET", "(4) MINING IS INSTANT", "METHODOLOGY: We treat",
        "EXPERIMENT-SPECIFIC:", "PRIOR ART:", "--- Fee Sensitivity:",
        "All costs below are vsize", "Skipping", "NOTE:",
        "FORWARD-LOOKING", "WARNING: Could not measure",
    )

    printable = [
        obs for obs in result.observations
        if obs.strip() and not any(obs.strip().startswith(m) for m in _NOISE)
    ]

    if verbose:
        for obs in result.observations:
            if obs.strip():
                print(f"             {_dim(':')}  {_dim(obs)}")
    elif len(printable) <= 25:
        for obs in printable:
            print(f"             {_dim(':')}  {_dim(obs)}")

    return result


def _first_line(s: str) -> str:
    """Extract the first meaningful line from an error string."""
    for line in s.strip().splitlines():
        line = line.strip()
        if line:
            return line[:80]
    return s[:80]


def cmd_init(args):
    """Initialize the regtest environment: create wallet + mine initial blocks.

    For CCV (pymatt) nodes: creates a wallet, mines blocks to that wallet.
    For CTV nodes (no-wallet builds): mines blocks to a dummy address.
    Works with both node types automatically.
    """
    rpc = connect_rpc()
    do_init(rpc, blocks=args.blocks)
    print("Ready.")


def cmd_list(args):
    """List available experiments."""
    print(f"\n{'Name':<30} {'Tags':<30} Description")
    print(f"{'-'*30} {'-'*30} {'-'*40}")
    for name in sorted(EXPERIMENTS.keys()):
        spec = EXPERIMENTS[name]
        tags = ", ".join(spec.tags)
        print(f"{spec.name:<30} {tags:<30} {spec.description}")
    print()


def cmd_run(args):
    """Run experiments.

    By default, automatically switches to the correct Bitcoin node and
    initializes regtest before running. Use --no-switch to skip this
    if the node is already running.

    When --covenant all, runs experiments on CTV first (Inquisition),
    then CCV (Merkleize), then OP_VAULT (opvault branch), then CAT+CSFS
    (Inquisition), then Simplicity (Elements + electrs).
    --covenant both is a legacy alias that runs CTV + CCV only.
    """
    # Determine which experiments to run
    if args.all:
        experiments = sorted(EXPERIMENTS.keys())
    elif args.tag:
        experiments = sorted(
            name for name, spec in EXPERIMENTS.items()
            if args.tag in spec.tags
        )
        if not experiments:
            print(f"No experiments found with tag '{args.tag}'")
            sys.exit(1)
    elif args.experiment:
        experiments = [args.experiment]
    else:
        print("Specify an experiment name, --tag, or --all")
        sys.exit(1)

    # Determine covenants
    if args.covenant in ("all", "all_covenants"):
        covenants = ["ctv", "ccv", "opvault", "cat_csfs", "simplicity"]
    elif args.covenant == "both":
        covenants = ["ctv", "ccv"]
    else:
        covenants = [args.covenant]

    reporter = Reporter()
    all_results = {}

    # Run each covenant in sequence.  When auto-switching is enabled,
    # each covenant gets its own node + fresh regtest + fresh adapter.
    requested_variant = (getattr(args, "variant", "") or "").strip()

    for cov in covenants:
        # Resolve variant list for this covenant.
        adapter_cls = type(get_adapter(cov))
        if requested_variant == "all":
            variants_to_run = adapter_cls.list_variants() or [""]
        elif requested_variant:
            variants_to_run = [requested_variant]
        else:
            variants_to_run = [""]  # adapter's reference variant

        for variant in variants_to_run:
            if args.no_switch:
                # Manual mode: assume correct node is already running
                if cov == "simplicity":
                    from adapters.simplicity_adapter import discover_simplex_ports
                    rpc_port, _, rpc_user, rpc_pass = discover_simplex_ports()
                    rpc = RegTestRPC(host="127.0.0.1", port=rpc_port,
                                     user=rpc_user, password=rpc_pass)
                else:
                    rpc = connect_rpc()
            else:
                # Auto mode: switch node + init regtest. Each variant gets
                # a fresh chain to avoid cross-variant fee/state bleed.
                rpc = switch_and_init(cov, blocks=args.blocks)

            adapter = get_adapter(cov)
            if variant:
                adapter.setup(rpc, variant=variant)
            else:
                adapter.setup(rpc)

            if args.vault_counts:
                adapter.vault_counts = [int(x) for x in args.vault_counts.split(",")]
            if args.max_withdrawals:
                adapter.max_withdrawals = args.max_withdrawals
            if getattr(args, "max_splits", None):
                adapter.max_splits = args.max_splits

            verbose = getattr(args, "verbose", False)
            label = adapter.variant_id if hasattr(adapter, "variant_id") else cov
            print(f"\n  {_dim('─'*70)}")
            print(f"  {_bold(_cyan(label.upper()))} {_dim('—')} {adapter.description}")
            print(f"  {_dim('─'*70)}")

            for exp_name in experiments:
                key = adapter.variant_id if hasattr(adapter, "variant_id") else cov
                if exp_name not in all_results:
                    all_results[exp_name] = {}

                try:
                    result = run_experiment(
                        exp_name, cov, rpc, adapter=adapter, verbose=verbose,
                        variant=variant,
                    )
                    all_results[exp_name][key] = result
                    reporter.save_result(result)
                except Exception as e:
                    cov_label = _cyan(key.upper().ljust(11))
                    exp_label = _bold(exp_name.ljust(32))
                    print(f"  {cov_label} {_dim('│')} {exp_label} {_dim('│')} {_red('CRASH')} {_dim('│')} {_red(str(e)[:60])}")
                    err_result = ExperimentResult(
                        experiment=exp_name, covenant=cov, params={},
                        variant=variant or "reference",
                    )
                    err_result.error = str(e)
                    all_results[exp_name][key] = err_result

    # Generate comparison reports for experiments run on multiple covenants
    for exp_name, results in all_results.items():
        if len(results) >= 2:
            comparison = ComparisonResult(
                experiment=exp_name,
                results=results,
            )
            reporter.save_comparison(comparison)

    # Generate sweep scaling tables for experiments with sweep data
    from harness import sweep_table

    SWEEP_PATTERNS = {
        "multi_input": ("batch_{}_total", "N Vaults"),
        "revault_amplification": ("revault_step_{}", "Step"),
    }

    for exp_name, results in all_results.items():
        if exp_name not in SWEEP_PATTERNS:
            continue
        pattern, param_name = SWEEP_PATTERNS[exp_name]

        # Per-covenant scaling tables
        for cov, result in results.items():
            table = sweep_table.build_scaling_table(result, pattern, param_name)
            csv = sweep_table.to_csv(result, pattern, param_name.lower().replace(" ", "_"))
            reporter.save_sweep(exp_name, cov, table, csv)

        # Cross-covenant comparison table (all covenants that have results)
        if len(results) >= 2:
            comp_table = sweep_table.build_multi_comparison_table(
                results, pattern, param_name
            )
            comp_csv = sweep_table.multi_comparison_csv(
                results, pattern,
                param_name.lower().replace(" ", "_")
            )
            reporter.save_sweep(exp_name, "comparison", comp_table, comp_csv)

    print(f"\n{_green('Results saved to:')} {reporter.run_dir}")


def cmd_compare(args):
    """Compare previously saved results."""
    result_dir = Path(args.directory)
    if not result_dir.exists():
        print(f"Directory not found: {result_dir}")
        sys.exit(1)

    json_files = sorted(result_dir.glob("*.json"))
    if not json_files:
        print(f"No JSON result files found in {result_dir}")
        sys.exit(1)

    print(f"\nResults in {result_dir}:")
    for f in json_files:
        data = json.loads(f.read_text())
        exp = data.get("experiment", "?")
        cov = data.get("covenant", "?")
        err = data.get("error", "")
        n_obs = len(data.get("observations", []))
        n_tx = len(data.get("transactions", []))
        status = "ERROR" if err else "OK"
        print(f"  {f.name}: {exp}/{cov} — {status}, {n_obs} observations, {n_tx} tx metrics")

    md_files = sorted(result_dir.glob("*.md"))
    if md_files:
        print(f"\nReports:")
        for f in md_files:
            print(f"  {f.name}")


def main():
    parser = argparse.ArgumentParser(
        description="Vault Comparison Runner — CTV vs CCV vs OP_VAULT vs CAT+CSFS vs Simplicity experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command")

    # init
    sub_init = subparsers.add_parser("init", help="Initialize regtest: create wallet + mine blocks")
    sub_init.add_argument("--blocks", type=int, default=300,
                          help="Number of blocks to mine (default: 300)")
    sub_init.set_defaults(func=cmd_init)

    # list
    sub_list = subparsers.add_parser("list", help="List available experiments")
    sub_list.set_defaults(func=cmd_list)

    # run
    sub_run = subparsers.add_parser("run", help="Run experiments")
    sub_run.add_argument("experiment", nargs="?", help="Experiment name")
    sub_run.add_argument("--covenant", choices=["ctv", "ccv", "opvault", "cat_csfs",
                                                "simplicity",
                                                "both", "all", "all_covenants"],
                         default="ctv",
                         help="Which covenant to test (default: ctv). "
                              "'all' runs CTV, CCV, OP_VAULT, CAT+CSFS, and Simplicity. "
                              "'both' is a legacy alias for CTV+CCV only.")
    sub_run.add_argument("--tag", help="Run all experiments with this tag")
    sub_run.add_argument("--all", action="store_true", help="Run all experiments")
    sub_run.add_argument("--no-switch", action="store_true",
                         help="Skip node switching (assume correct node is running)")
    sub_run.add_argument("--variant", default="",
                         help="Variant id within the selected covenant "
                              "(e.g. 'keygated', 'atomic', 'keyless-atomic'); "
                              "use 'all' to sweep every registered variant. "
                              "Defaults to the adapter's reference variant.")
    sub_run.add_argument("--blocks", type=int, default=300,
                         help="Blocks to mine during init (default: 300)")
    sub_run.add_argument("--vault-counts", type=str, default=None,
                         help="Comma-separated vault counts for multi_input sweep "
                              "(default: 1,2,3,5,10)")
    sub_run.add_argument("--max-withdrawals", type=int, default=None,
                         help="Max partial withdrawals for revault_amplification "
                              "(default: 10)")
    sub_run.add_argument("--max-splits", type=int, default=None,
                         help="Max splitting rounds for watchtower_exhaustion "
                              "(default: 50)")
    sub_run.add_argument("-v", "--verbose", action="store_true",
                         help="Print full observations and metrics (default: compact)")
    sub_run.set_defaults(func=cmd_run)

    # compare
    sub_compare = subparsers.add_parser("compare", help="View saved results")
    sub_compare.add_argument("directory", help="Results directory to inspect")
    sub_compare.set_defaults(func=cmd_compare)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
