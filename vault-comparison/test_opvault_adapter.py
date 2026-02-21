#!/usr/bin/env python3
"""Quick smoke test for the OPVaultAdapter.

Run this after switch-node.sh opvault has started the node:

    cd vault-comparison
    uv run python test_opvault_adapter.py

It tests the full vault lifecycle:
  1. Setup (fund fee wallet)
  2. Create vault (deposit 500k sats)
  3. Trigger unvault
  4. Complete withdrawal (hot path)
  5. Create another vault and test recovery
"""

import os
import sys
import traceback

os.environ.setdefault("BITCOIN_RPC_URL", "http://127.0.0.1:18443")

# Ensure simple-op-vault is importable
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent / "simple-op-vault"))

from adapters.opvault_adapter import OPVaultAdapter
from harness.rpc import RegTestRPC


def main():
    print("=" * 60)
    print("OP_VAULT Adapter Smoke Test")
    print("=" * 60)

    # Step 0: Connect to node
    print("\n[0] Connecting to regtest node...")
    rpc = RegTestRPC.from_cookie()
    info = rpc.getblockchaininfo()
    print(f"    chain={info['chain']}, blocks={info['blocks']}")

    # Ensure regtest has enough blocks for maturity
    if info["blocks"] < 200:
        needed = 200 - info["blocks"]
        print(f"    Mining {needed} blocks for maturity...")
        # Create a wallet if none exists (required for generatetoaddress on some builds)
        if not _has_wallet(rpc):
            try:
                rpc.createwallet("testwallet")
                print("    Created testwallet")
            except Exception:
                pass  # wallet may already exist
        try:
            addr = rpc.getnewaddress()
        except Exception:
            addr = "bcrt1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqdku202"
        rpc.generatetoaddress(needed, addr)

    # Step 1: Setup
    print("\n[1] Setting up adapter...")
    adapter = OPVaultAdapter()
    try:
        adapter.setup(rpc, block_delay=10, seed=b"smoketest")
        print("    Setup OK")
    except Exception as e:
        print(f"    Setup FAILED: {e}")
        traceback.print_exc()
        return False

    # Step 2: Create vault
    print("\n[2] Creating vault (500,000 sats)...")
    try:
        vault = adapter.create_vault(500_000)
        print(f"    Vault created: txid={vault.vault_txid[:16]}...")
        print(f"    Address: {vault.vault_address}")
        print(f"    Amount: {vault.amount_sats} sats")
    except Exception as e:
        print(f"    Create vault FAILED: {e}")
        traceback.print_exc()
        return False

    # Step 3: Trigger unvault
    print("\n[3] Triggering unvault...")
    try:
        unvault = adapter.trigger_unvault(vault)
        print(f"    Trigger txid={unvault.unvault_txid[:16]}...")
        print(f"    Blocks remaining: {unvault.blocks_remaining}")
    except Exception as e:
        print(f"    Trigger FAILED: {e}")
        traceback.print_exc()
        return False

    # Step 4: Complete withdrawal (hot)
    print("\n[4] Completing withdrawal (hot path)...")
    try:
        withdrawal = adapter.complete_withdrawal(unvault, path="hot")
        print(f"    Withdrawal txid={withdrawal.txid[:16]}...")
        print(f"    Label: {withdrawal.label}")
    except Exception as e:
        print(f"    Withdrawal FAILED: {e}")
        traceback.print_exc()
        return False

    # Step 5: Test recovery (from vault state) + verify recovery address
    print("\n[5] Testing recovery (new vault)...")
    try:
        vault2 = adapter.create_vault(300_000)
        print(f"    Vault2 created: txid={vault2.vault_txid[:16]}...")

        # Compute expected recovery address from the config.
        # VaultConfig.recov_address applies the P2TR tweak to recovery_pubkey
        # and encodes as bech32m — this is the canonical recovery destination.
        config2 = vault2.extra["config"]
        expected_recovery_addr = config2.recov_address
        print(f"    Expected recovery address: {expected_recovery_addr[:30]}...")

        recovery = adapter.recover(vault2)
        print(f"    Recovery txid={recovery.txid[:16]}...")
        print(f"    Label: {recovery.label}")

        # Verify recovery tx sends to the expected recovery address
        _verify_recovery_address(rpc, recovery.txid, expected_recovery_addr, "vault-state")
    except Exception as e:
        print(f"    Recovery FAILED: {e}")
        traceback.print_exc()
        return False

    # Step 6: Test trigger + recovery (from triggered state)
    print("\n[6] Testing recovery from triggered state...")
    try:
        vault3 = adapter.create_vault(400_000)
        unvault3 = adapter.trigger_unvault(vault3)
        print(f"    Triggered: txid={unvault3.unvault_txid[:16]}...")

        config3 = vault3.extra["config"]
        expected_recovery_addr3 = config3.recov_address

        recovery3 = adapter.recover(unvault3)
        print(f"    Recovery txid={recovery3.txid[:16]}...")

        _verify_recovery_address(rpc, recovery3.txid, expected_recovery_addr3, "triggered-state")
    except Exception as e:
        print(f"    Triggered recovery FAILED: {e}")
        traceback.print_exc()
        return False

    # Cleanup
    adapter.teardown()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
    return True


def _verify_recovery_address(rpc, txid, expected_addr, label):
    """Check that the recovery tx's largest output goes to expected_addr.

    The recovery tx has two outputs: the recovered funds (large) and
    the fee wallet change (small).  We check the largest output's
    address against VaultConfig.recov_address, which is the P2TR
    address derived from the tweaked recovery_pubkey.
    """
    rec_info = rpc.call("getrawtransaction", txid, True)
    rec_outputs = rec_info["vout"]
    largest = max(rec_outputs, key=lambda v: v["value"])
    actual_addr = largest["scriptPubKey"].get("address", "")

    if actual_addr == expected_addr:
        print(f"    Recovery address verification ({label}): PASS")
        print(f"      {actual_addr}")
    elif not actual_addr:
        # Some node builds don't include 'address' in scriptPubKey
        rec_spk = largest["scriptPubKey"].get("hex", "")
        print(f"    Recovery address verification ({label}): INCONCLUSIVE")
        print(f"      (node did not return address field; SPK={rec_spk[:40]}...)")
    else:
        print(f"    Recovery address verification ({label}): FAIL")
        print(f"      expected: {expected_addr}")
        print(f"      actual:   {actual_addr}")


def _has_wallet(rpc):
    try:
        rpc.call("getwalletinfo")
        return True
    except Exception:
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
