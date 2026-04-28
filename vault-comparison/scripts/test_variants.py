"""Smoke-test all registered variants per opcode.

For each (covenant, variant) pair, switches to the correct Bitcoin node,
sets up the adapter with the variant, and runs two minimal lifecycle flows:

  Flow A (withdraw):  create_vault → trigger_unvault → complete_withdrawal
  Flow B (recover):   create_vault → trigger_unvault → recover

Reports per-stage vsize and pass/fail per variant. The withdraw flow is
shared across all variants (no path-dependent change); the recover flow
is what variants actually exercise differently.

Usage:
    cd vault-comparison
    uv run scripts/test_variants.py                 # all covenants, all variants
    uv run scripts/test_variants.py --covenant ctv  # one covenant
    uv run scripts/test_variants.py --no-switch     # current node only
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

# Make sibling modules importable when invoked from any cwd.
THIS_DIR = Path(__file__).resolve().parent
ROOT = THIS_DIR.parent
sys.path.insert(0, str(ROOT))

from run import get_adapter, switch_and_init, connect_rpc  # type: ignore  # noqa: E402

# Order matters: groups variants by node mode so we minimise switch_and_init
# calls. CTV and CAT+CSFS share Inquisition; CCV uses ccv node; OP_VAULT uses
# its own; Simplicity uses Elements (excluded from this smoke run).
COVENANT_ORDER = ["ctv", "cat_csfs", "ccv", "opvault"]

VAULT_AMOUNT = 49_999_900


def _green(s: str) -> str:
    return f"\033[32m{s}\033[0m"


def _red(s: str) -> str:
    return f"\033[31m{s}\033[0m"


def _yellow(s: str) -> str:
    return f"\033[33m{s}\033[0m"


def _dim(s: str) -> str:
    return f"\033[2m{s}\033[0m"


def _bold(s: str) -> str:
    return f"\033[1m{s}\033[0m"


def run_variant(covenant: str, variant: str, rpc, do_withdraw: bool = True,
                do_recover: bool = True) -> dict:
    """Run lifecycle smoke test for one (covenant, variant).

    Flow alternates: each flow uses a fresh adapter so vault state across
    variants is isolated. The recovery flow is the discriminator — variants
    only change the recovery script path.
    """
    out = {"covenant": covenant, "variant": variant, "stages": {}, "errors": []}

    # Per-flow seed isolation: distinct seeds keep each flow's wallets,
    # monitors, and chain-state caches from leaking across into the next
    # flow. Required because the OP_VAULT monitor caches stale trigger
    # outputs across adapter instances when the seed is shared.
    flow_seed_suffix = variant.encode()

    if do_withdraw:
        adapter = get_adapter(covenant)
        try:
            adapter.setup(rpc, variant=variant, seed=b"vw-" + flow_seed_suffix)
            out["axes"] = adapter.axes()
            out["variant_id"] = adapter.variant_id
            v = adapter.create_vault(VAULT_AMOUNT)
            rec = adapter.collect_tx_metrics(_record("tovault", v.vault_txid, v.amount_sats), rpc)
            out["stages"]["tovault"] = rec.vsize
            u = adapter.trigger_unvault(v)
            rec = adapter.collect_tx_metrics(_record("unvault", u.unvault_txid, u.amount_sats), rpc)
            out["stages"]["unvault"] = rec.vsize
            w = adapter.complete_withdrawal(u, path="hot")
            rec = adapter.collect_tx_metrics(w, rpc)
            out["stages"]["withdraw"] = rec.vsize
        except Exception as e:
            out["errors"].append(f"withdraw: {type(e).__name__}: {e}\n{_short_tb()}")
        finally:
            try:
                adapter.teardown()
            except Exception:
                pass

    if do_recover:
        adapter = get_adapter(covenant)
        try:
            adapter.setup(rpc, variant=variant, seed=b"vr-" + flow_seed_suffix)
            out["axes"] = adapter.axes()
            out["variant_id"] = adapter.variant_id
            v = adapter.create_vault(VAULT_AMOUNT)
            u = adapter.trigger_unvault(v)
            r = adapter.recover(u)
            rec = adapter.collect_tx_metrics(r, rpc)
            out["stages"]["recover"] = rec.vsize
        except Exception as e:
            out["errors"].append(f"recover: {type(e).__name__}: {e}\n{_short_tb()}")
        finally:
            try:
                adapter.teardown()
            except Exception:
                pass
    return out


def _record(label: str, txid: str, amount: int):
    from adapters.base import TxRecord
    return TxRecord(txid=txid, label=label, amount_sats=amount)


def _short_tb() -> str:
    tb = traceback.format_exc().splitlines()
    # Keep the last ~6 frames.
    return "\n".join(tb[-12:])


def print_result(out: dict) -> None:
    cov = out["covenant"].upper().ljust(10)
    vid = out.get("variant_id", out["variant"]).ljust(28)
    axes = "/".join(out.get("axes", ()))
    if out["errors"]:
        # If any stage measured, still show it.
        stages = " ".join(f"{k}={v}" for k, v in out["stages"].items())
        line = f"  {_red('FAIL')}  {cov} {vid} axes={axes}  {_dim(stages)}"
        print(line)
        for err in out["errors"]:
            for ln in err.splitlines():
                print(f"        {_dim('│')}  {_red(ln)}")
    else:
        s = out["stages"]
        cells = [f"{k}={_bold(str(v))}vB" for k, v in s.items()]
        print(f"  {_green('OK  ')}  {cov} {vid} axes={axes}  {' '.join(cells)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--covenant", default="all",
                    choices=COVENANT_ORDER + ["all"],
                    help="One covenant or 'all'.")
    ap.add_argument("--variant", default="all",
                    help="Specific variant id (e.g. 'keygated') or 'all'.")
    ap.add_argument("--no-switch", action="store_true",
                    help="Skip switch-node.sh; assume the right node is running.")
    args = ap.parse_args()

    if args.covenant == "all":
        covenants = COVENANT_ORDER
    else:
        covenants = [args.covenant]

    all_results = []

    for covenant in covenants:
        adapter_cls = type(get_adapter(covenant))
        variants = adapter_cls.list_variants()
        if args.variant != "all":
            if args.variant not in variants:
                print(_yellow(f"skip {covenant}: variant {args.variant!r} not in {variants}"))
                continue
            variants = [args.variant]

        print(_bold(f"\n=== {covenant.upper()} ({len(variants)} variants) ==="))
        for v in variants:
            # Wipe chain per variant to avoid fee-wallet exhaustion and
            # cross-variant state bleed in shared monitors. switch-node.sh
            # wipes regtest data and restarts the node; do_init mines
            # initial blocks. With --no-switch we trust the caller has
            # done this already.
            if not args.no_switch:
                rpc = switch_and_init(covenant)
            else:
                rpc = connect_rpc()

            res = run_variant(covenant, v, rpc)
            print_result(res)
            all_results.append(res)

    # Summary
    print(_bold("\n=== Summary ==="))
    passes = sum(1 for r in all_results if not r["errors"])
    fails = len(all_results) - passes
    print(f"  {passes} pass / {fails} fail / {len(all_results)} total")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
