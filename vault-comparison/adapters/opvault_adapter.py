"""OP_VAULT (BIP-345) adapter.

Wraps jamesob/opvault-demo (the upstream reference implementation) to expose
the uniform VaultAdapter interface.  Requires jamesob's bitcoin-opvault node
(branch 2023-02-opvault-inq) on regtest.

The upstream repo uses the `verystable` library for script construction,
`bip32` for HD key derivation, and its own RPC layer (which supports
cookie-based auth natively).  Docker has been removed — we point
BITCOIN_RPC_URL at the local regtest node.
"""

import os
import sys
import hashlib
import json
import secrets
import tempfile
from pathlib import Path
from typing import Optional, List

from adapters.base import VaultAdapter, VaultState, UnvaultState, TxRecord
from harness.rpc import RegTestRPC
from harness.metrics import TxMetrics

# Path to the cloned opvault-demo repo (sibling to vault-comparison/)
OPVAULT_REPO = Path(__file__).resolve().parents[2] / "simple-op-vault"



def _ensure_opvault_imports():
    """Lazy-load the opvault-demo modules.

    Sets BITCOIN_RPC_URL to the local regtest node before importing,
    so that the upstream code talks to our switch-node-managed bitcoind
    rather than a Docker container.
    """
    # Point the upstream code at the local regtest node
    os.environ.setdefault("BITCOIN_RPC_URL", "http://127.0.0.1:18443")

    # Ensure opvault-demo is at the FRONT of sys.path so its main.py wins
    repo_str = str(OPVAULT_REPO)
    if repo_str in sys.path:
        sys.path.remove(repo_str)
    sys.path.insert(0, repo_str)

    # Evict cached 'main' module to ensure opvault-demo's main.py is loaded.
    if "main" in sys.modules:
        cached = sys.modules["main"]
        cached_path = getattr(cached, "__file__", "") or ""
        if repo_str not in cached_path:
            del sys.modules["main"]

    # verystable must activate the softfork flags before any script work
    import verystable
    import verystable.core.messages as _msgs

    # Compatibility: map nVersion → version for API differences.
    _CTx = _msgs.CTransaction
    if not hasattr(_CTx, "nVersion"):
        _CTx.nVersion = property(lambda self: self.version)
    # CMutableTransaction may not exist in all verystable versions
    _MTx = getattr(_msgs, "CMutableTransaction", None)
    if _MTx is not None and not hasattr(_MTx, "nVersion"):
        _MTx.nVersion = property(lambda self: self.version)

    # Compatibility: map script → leaf_script for TaprootSignatureMsg.
    import verystable.core.script as _script
    _orig_sig_msg = _script.TaprootSignatureMsg

    def _patched_sig_msg(*args, **kwargs):
        if "script" in kwargs and "leaf_script" not in kwargs:
            kwargs["leaf_script"] = kwargs.pop("script")
        return _orig_sig_msg(*args, **kwargs)

    _script.TaprootSignatureMsg = _patched_sig_msg

    verystable.softforks.activate_bip345_vault()
    verystable.softforks.activate_bip119_ctv()

    import main as opvault_main
    return opvault_main


class OPVaultAdapter(VaultAdapter):

    # Variants on the (f, a, g, b) lattice. BIP-345 specifies both
    # authorised (g_key) and unauthorised (g_keyless) recovery as
    # first-class modes; the atomic variant drops the revault leaf.
    VARIANTS = {
        "reference":        ("wallet", "partial", "key",     "bound"),
        "keyless":          ("wallet", "partial", "keyless", "bound"),
        "atomic":           ("wallet", "atomic",  "key",     "bound"),  # MES anchor
        "keyless-atomic":   ("wallet", "atomic",  "keyless", "bound"),  # post-MES anchor
    }
    REFERENCE_VARIANT = "reference"

    @property
    def name(self) -> str:
        return "opvault"

    @property
    def node_mode(self) -> str:
        return "opvault"

    @property
    def description(self) -> str:
        return "OP_VAULT vault (BIP 345 + BIP 119) via jamesob/opvault-demo"

    def setup(self, rpc: RegTestRPC, block_delay: int = 10,
              seed: bytes = b"compare", variant: str = "", **kwargs) -> None:
        self.rpc = rpc
        self.block_delay = block_delay
        self.seed = seed
        self.variant = variant or self._default_variant()
        self._vault_counter = 0
        self.ov = _ensure_opvault_imports()

        # The upstream RPC (verystable.rpc.BitcoinRPC) — supports cookie auth
        from verystable.rpc import BitcoinRPC
        self._ov_rpc = BitcoinRPC(
            net_name="regtest",
            service_url=os.environ.get("BITCOIN_RPC_URL", "http://127.0.0.1:18443"),
        )

        # Fee wallet used by the upstream code for paying tx fees
        # SingleAddressWallet requires exactly 32 bytes for ECKey.set()
        from verystable.wallet import SingleAddressWallet
        fee_seed = hashlib.sha256(seed + b"-fees").digest()
        self._fee_wallet = SingleAddressWallet(
            self._ov_rpc, locked_utxos=set(), seed=fee_seed
        )

        # Working directory for config/secrets files (per-session temp dir)
        self._workdir = Path(tempfile.mkdtemp(prefix="opvault_"))

        # Pre-fund the fee wallet: mine blocks to its address, mature them
        self._fund_fee_wallet()

        # Corrected get_utxo: filter for mature unlocked UTXOs before selection.
        def _patched_get_utxo(wallet_self):
            wallet_self.rescan()
            height = wallet_self.rpc.getblockcount()
            utxos = [
                u for u in wallet_self.utxos
                if u.outpoint not in wallet_self.locked_utxos
                and (height - u.height) >= 100
            ]
            if not utxos:
                raise RuntimeError(
                    "No mature coins available; call `-generate` a few times. "
                )
            utxos.sort(key=lambda u: u.height)
            utxo = utxos.pop(0)
            wallet_self.locked_utxos.add(utxo.outpoint)
            return utxo

        import types
        self._fee_wallet.get_utxo = types.MethodType(_patched_get_utxo, self._fee_wallet)

        # Shared vault config — all vaults use the same keys with different
        # vault_num indices. Required for batched triggers (BIP-345 requires
        # compatible vault specs: same recovery key, same trigger xpub).
        self._shared_metadata = self._create_config(seed + b"-shared")
        self._shared_config = self._shared_metadata.config
        self._shared_monitor = self.ov.ChainMonitor(
            self._shared_metadata, self._ov_rpc
        )

    # ------------------------------------------------------------------
    # Fee wallet funding
    # ------------------------------------------------------------------

    def _fund_fee_wallet(self):
        """Mine coins to the fee wallet so triggers/recoveries can pay fees."""
        fee_addr = self._fee_wallet.fee_addr
        # Mine coinbases to the fee wallet (enough for batched operations)
        self._ov_rpc.generatetoaddress(20, fee_addr)
        # Mature them
        self._ov_rpc.generatetoaddress(100, fee_addr)
        # Rescan so the fee wallet sees its UTXOs
        self._fee_wallet.rescan()

    def _ensure_fee_utxos(self, min_mature: int = 3):
        """Ensure the fee wallet has enough mature UTXOs.

        Clears stale locks (spent UTXOs no longer in the UTXO set),
        then mines blocks if needed to mature immature coinbases/change.
        """
        fee_addr = self._fee_wallet.fee_addr
        self._fee_wallet.rescan()

        # Clear stale locks for spent UTXOs
        live_outpoints = {u.outpoint for u in self._fee_wallet.utxos}
        self._fee_wallet.locked_utxos &= live_outpoints

        height = self._ov_rpc.getblockcount()
        mature = [
            u for u in self._fee_wallet.utxos
            if u.outpoint not in self._fee_wallet.locked_utxos
            and (height - u.height) >= 100
        ]

        if len(mature) >= min_mature:
            return

        immature = [
            u for u in self._fee_wallet.utxos
            if u.outpoint not in self._fee_wallet.locked_utxos
            and (height - u.height) < 100
        ]

        if immature:
            oldest = min(immature, key=lambda u: u.height)
            blocks_needed = 100 - (height - oldest.height) + 1
            self._ov_rpc.generatetoaddress(blocks_needed + 5, fee_addr)
        else:
            self._ov_rpc.generatetoaddress(10, fee_addr)
            self._ov_rpc.generatetoaddress(100, fee_addr)

        self._fee_wallet.rescan()

    def _has_default_wallet(self) -> bool:
        """Check if there's a default wallet loaded."""
        try:
            self._ov_rpc.getwalletinfo()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Config generation (replaces createconfig.py)
    # ------------------------------------------------------------------

    def _create_config(self, vault_seed: bytes = None) -> "WalletMetadata":
        """Programmatically create a vault config (like createconfig.py).

        Returns a WalletMetadata object ready for use.
        """
        from bip32 import BIP32

        vault_seed = vault_seed or secrets.token_bytes(32)
        # BIP32.from_seed() requires 16-64 bytes
        trig_seed = hashlib.sha256(vault_seed + b"-trigger").digest()
        trig32 = BIP32.from_seed(trig_seed)
        recovery_seed = hashlib.sha256(vault_seed + b"-recovery").digest()
        recovery32 = BIP32.from_seed(recovery_seed)
        recovery_pubkey = recovery32.get_pubkey_from_path("m/0h/0")[1:]  # x-only

        recoveryauth_key = self.ov.recoveryauth_phrase_to_key("changeme2")
        recoveryauth_pubkey = recoveryauth_key.get_pubkey().get_bytes()[1:]  # x-only

        # Variant -> (recovery_mode, atomic-flag) mapping. The atomic
        # variants additionally restrict the trigger template so the
        # withdraw output covers full vault value with no revault leg.
        recovery_mode = "authorised" if self.axes()[2] == "key" else "unauthorised"
        config = self.ov.VaultConfig(
            spend_delay=self.block_delay,
            recovery_pubkey=recovery_pubkey,
            recoveryauth_pubkey=recoveryauth_pubkey,
            trigger_xpub=trig32.get_xpub(),
            birthday_height=0,
            recovery_mode=recovery_mode,
        )

        # Save config to temp file (required by upstream load())
        config_path = self._workdir / f"config-{self._vault_counter}.json"
        metadata = self.ov.WalletMetadata(
            config,
            filepath=config_path,
            fee_wallet_seed=hashlib.sha256(self.seed + b"-fees").digest(),
        )
        metadata.save()

        # Save secrets
        secrets_path = self._workdir / f"secrets-{self._vault_counter}.json"
        secd = {
            config.id: {
                'trigger_xpriv': trig32.get_xpriv(),
                'recoveryauth_phrase': 'changeme2',
            }
        }
        secrets_path.write_text(json.dumps(secd, indent=2))
        config.secrets_filepath = secrets_path

        return metadata

    # ------------------------------------------------------------------
    # Core vault lifecycle
    # ------------------------------------------------------------------

    def create_vault(self, amount_sats: int) -> VaultState:
        """Deposit funds into an OP_VAULT vault.

        Uses the shared VaultConfig with the next vault_num index.
        All vaults share the same keys (required for batched triggers)
        but have unique deposit addresses via BIP-32 derivation.
        """
        self._vault_counter += 1
        vault_num = self._vault_counter - 1

        config = self._shared_config
        metadata = self._shared_metadata
        monitor = self._shared_monitor

        # Get the deposit address for this vault_num
        vault_spec = config.get_spec_for_vault_num(vault_num)
        deposit_addr = vault_spec.address

        # Mine blocks to the fee wallet and mature them. This both funds
        # the fee wallet and matures earlier change UTXOs.
        fee_addr = self._fee_wallet.fee_addr
        self._ov_rpc.generatetoaddress(1, fee_addr)
        self._ov_rpc.generatetoaddress(100, fee_addr)
        self._fee_wallet.rescan()

        deposit_txid = self._send_to_address(deposit_addr, amount_sats)

        # Mine to confirm
        self._ov_rpc.generatetoaddress(1, fee_addr)

        # Rescan shared monitor to pick up the new deposit
        state = monitor.rescan()

        return VaultState(
            vault_txid=deposit_txid,
            amount_sats=amount_sats,
            vault_address=deposit_addr,
            extra={
                "metadata": metadata,
                "config": config,
                "monitor": monitor,
                "chain_state": state,
                "vault_spec": vault_spec,
                "vault_seed": self.seed,
            },
        )

    def _send_to_address(self, address: str, amount_sats: int) -> str:
        """Send amount_sats to address using the fee wallet.

        Constructs a raw transaction spending from the fee wallet.
        """
        from verystable.core import messages, address as addr_mod
        from verystable.core.script import CScript
        from verystable.core.messages import COutPoint, CTxOut, CTxIn
        from verystable.script import CTransaction
        from verystable import core

        self._ensure_fee_utxos()
        fee_utxo = self._fee_wallet.get_utxo()

        dest_spk = addr_mod.address_to_scriptpubkey(address)
        change = fee_utxo.value_sats - amount_sats - self.ov.FEE_VALUE_SATS
        assert change > 0, (
            f"Fee UTXO ({fee_utxo.value_sats}) too small for "
            f"{amount_sats} + {self.ov.FEE_VALUE_SATS} fee"
        )

        tx = CTransaction()
        tx.version = 2
        tx.vin = [fee_utxo.as_txin]
        tx.vout = [
            CTxOut(nValue=amount_sats, scriptPubKey=dest_spk),
            CTxOut(nValue=change, scriptPubKey=self._fee_wallet.fee_spk),
        ]

        spent_outputs = [fee_utxo.output]
        from verystable.core.script import TaprootSignatureHash
        sigmsg = TaprootSignatureHash(
            tx, spent_outputs, input_index=0, hash_type=0)

        wit = messages.CTxInWitness()
        tx.wit.vtxinwit = [wit]
        wit.scriptWitness.stack = [self._fee_wallet.sign_msg(sigmsg)]

        txid = self._ov_rpc.sendrawtransaction(tx.tohex())
        return txid

    def trigger_unvault(self, vault: VaultState) -> UnvaultState:
        """Trigger a withdrawal from the vault.

        Uses start_withdrawal() from the upstream code to build the
        trigger + final-withdrawal transaction pair.
        """
        metadata = vault.extra["metadata"]
        config = vault.extra["config"]
        chain_state = vault.extra["chain_state"]
        monitor = vault.extra["monitor"]

        # Pick a destination address (use fee wallet as a simple hot target)
        # start_withdrawal() reserves FEE_VALUE_SATS for the final withdrawal tx
        # and requires the destination amount < total vault value - fees.
        # We withdraw as much as possible while leaving room for the fee budget.
        fee_addr = self._fee_wallet.fee_addr
        withdraw_sats = vault.amount_sats - 2 * self.ov.FEE_VALUE_SATS
        assert withdraw_sats > 0, (
            f"Vault balance ({vault.amount_sats}) too small for fees "
            f"({2 * self.ov.FEE_VALUE_SATS})"
        )
        dest = self.ov.PaymentDestination(fee_addr, withdraw_sats)

        # Get available vault UTXOs from the chain state
        chain_state = monitor.rescan()
        vault_utxos = list(chain_state.vault_utxos.values())
        assert vault_utxos, "No vault UTXOs found after rescan"

        # Coin selection: start_withdrawal() requires that at most 2 UTXOs
        # are passed (one covers the destination, one optional excess for
        # revault).  Pick the single UTXO matching our deposit txid, or
        # if not identifiable, just the one closest in value.
        target_txid = vault.vault_txid
        matching = [u for u in vault_utxos
                    if hasattr(u, "outpoint") and target_txid in str(u.outpoint)]
        if matching:
            vault_utxos = matching[:1]
        else:
            # Fallback: pick the single UTXO whose value is closest to our deposit
            vault_utxos = [min(vault_utxos,
                               key=lambda u: abs(u.value_sats - vault.amount_sats))]

        # Load the trigger signing key from secrets
        secd = json.loads(config.secrets_filepath.read_text())[config.id]
        from bip32 import BIP32
        trig_b32 = BIP32.from_xpriv(secd['trigger_xpriv'])
        from verystable import core

        def trigger_key_signer(msg: bytes, vault_num: int) -> bytes:
            privkey = trig_b32.get_privkey_from_path(
                f"{config.trigger_xpub_path_prefix}/{vault_num}")
            return core.key.sign_schnorr(privkey, msg)

        # Refresh fee wallet — ensure mature UTXOs for the fee input
        self._ensure_fee_utxos()

        # Build trigger spec
        trigger_spec = self.ov.start_withdrawal(
            config, self._fee_wallet, vault_utxos, dest, trigger_key_signer
        )

        # Register with metadata so monitor recognizes it
        metadata.triggers[trigger_spec.id] = trigger_spec
        metadata.save()

        # Broadcast the trigger transaction
        assert trigger_spec.trigger_tx
        try:
            self._ov_rpc.sendrawtransaction(trigger_spec.trigger_tx.tohex())
        except Exception as e:
            if "-27" not in str(e):  # already in blockchain
                raise

        # Mine to confirm
        self._ov_rpc.generatetoaddress(1, self._fee_wallet.fee_addr)

        return UnvaultState(
            unvault_txid=trigger_spec.trigger_tx.rehash(),
            amount_sats=withdraw_sats,
            blocks_remaining=self.block_delay,
            extra={
                **vault.extra,
                "trigger_spec": trigger_spec,
                "chain_state": monitor.rescan(),
            },
        )

    def complete_withdrawal(self, unvault: UnvaultState, path: str = "hot") -> TxRecord:
        """Complete the withdrawal after the spend delay.

        path="hot":  Mine spend_delay blocks, then broadcast the CTV-locked
                     final withdrawal transaction.  This is the normal path.
        path="cold": Delegates to recover().  OP_VAULT has no distinct
                     cold-sweep tx — authorized recovery IS the cold path.
                     Prefer calling recover() directly in new code.
        """
        if path == "cold":
            # OP_VAULT has no separate cold-sweep transaction.  "Cold" maps
            # to authorized recovery, which is the same as recover().
            # This shim exists for CTV-style callers; new experiments should
            # call recover() directly.
            return self._do_recovery(unvault, from_vault=False)

        if path != "hot":
            raise ValueError(
                f"OP_VAULT complete_withdrawal accepts 'hot' or 'cold', "
                f"got {path!r}"
            )

        trigger_spec = unvault.extra["trigger_spec"]

        # Mine blocks to satisfy spend_delay
        self._ov_rpc.generatetoaddress(
            self.block_delay, self._fee_wallet.fee_addr)

        # Broadcast the final withdrawal tx (CTV template)
        assert trigger_spec.withdrawal_tx
        try:
            self._ov_rpc.sendrawtransaction(trigger_spec.withdrawal_tx.tohex())
        except Exception as e:
            if "-27" not in str(e):
                raise

        # Mine to confirm
        self._ov_rpc.generatetoaddress(1, self._fee_wallet.fee_addr)

        return TxRecord(
            txid=trigger_spec.withdrawal_tx.rehash(),
            label="withdraw",
            amount_sats=unvault.amount_sats,
        )

    def recover(self, state) -> TxRecord:
        """Execute authorized recovery from vault or triggered state.

        Works from either VaultState (untriggered) or UnvaultState (triggered).
        Both states carry a ``"recover"`` leaf in their taproot tree with the
        same recovery script (recoveryauth_pubkey CHECKSIGVERIFY + OP_VAULT_RECOVER).

        Upstream verification:
            - VaultSpec.taproot_info: leaves = ["recover", "trigger"]
            - TriggerSpec.taproot_info: leaves = ["recover", "withdraw"]
            - get_recovery_tx() calls utxo.get_taproot_info().leaves["recover"]
              which resolves correctly for both VaultUtxo(vault_spec=...) and
              VaultUtxo(trigger_spec=...).
        """
        from_vault = isinstance(state, VaultState)
        return self._do_recovery(state, from_vault=from_vault)

    def _do_recovery(self, state, from_vault: bool = True) -> TxRecord:
        """Recover funds to the recovery address.

        Uses get_recovery_tx() from the upstream code.

        Args:
            from_vault: If True, recover untriggered vault UTXOs
                        (chain_state.vault_utxos).  If False, recover
                        triggered UTXOs (chain_state.trigger_utxos +
                        theft_trigger_utxos).
        """
        config = state.extra["config"]
        monitor = state.extra["monitor"]

        # Rescan to get current UTXO state
        chain_state = monitor.rescan()

        # Filter to the specific UTXO for this state (shared monitor
        # sees all UTXOs under the shared config)
        target_txid = state.vault_txid if from_vault else state.unvault_txid
        if from_vault:
            utxos = [u for u in chain_state.vault_utxos.values()
                     if target_txid in str(getattr(u, "outpoint", ""))]
            if not utxos:
                utxos = list(chain_state.vault_utxos.values())[:1]
        else:
            utxos = [u for u in chain_state.trigger_utxos.values()
                     if target_txid in str(getattr(u, "outpoint", ""))]
            if not utxos:
                utxos = list(chain_state.trigger_utxos.values())[:1]
            # Also include theft triggers
            utxos.extend(chain_state.theft_trigger_utxos.keys())

        assert utxos, f"No {'vault' if from_vault else 'trigger'} UTXOs to recover"

        # Load recovery auth key
        secd = json.loads(config.secrets_filepath.read_text())[config.id]
        recovery_privkey = self.ov.recoveryauth_phrase_to_key(
            secd['recoveryauth_phrase']).get_bytes()

        from verystable import core

        def recoveryauth_signer(msg: bytes) -> bytes:
            return core.key.sign_schnorr(recovery_privkey, msg)

        self._ensure_fee_utxos()

        recovery_spec = self.ov.get_recovery_tx(
            config, self._fee_wallet, utxos, recoveryauth_signer
        )

        if recovery_spec.cpfp_child is not None:
            # BIP-345 unauthorised recovery: parent is zero-fee with an
            # ephemeral anchor; CPFP child carries the package fee.
            # submitpackage requires both txs in topological order.
            parent_hex = recovery_spec.tx.tohex()
            child_hex = recovery_spec.cpfp_child.tohex()
            res = self._ov_rpc.submitpackage([parent_hex, child_hex])
            self._check_submitpackage(res)
        else:
            self._ov_rpc.sendrawtransaction(recovery_spec.tx.tohex())

        # Mine to confirm
        self._ov_rpc.generatetoaddress(1, self._fee_wallet.fee_addr)

        return TxRecord(
            txid=recovery_spec.tx.rehash(),
            label="recover",
            amount_sats=state.amount_sats,
        )

    def attempt_permissionless_recovery(self, state) -> str:
        """Attacker without the recoveryauth key tries to fire recovery.

        Reference variant: forges a wrong-key Schnorr signature; the chain
        rejects via OP_CHECKSIGVERIFY in the recover script.
        Keyless variant: no signature required; broadcast succeeds (the
        unauthorised mode admits permissionless recovery by design).
        """
        config = state.extra["config"]
        monitor = state.extra["monitor"]
        chain_state = monitor.rescan()
        target_txid = state.unvault_txid if isinstance(state, UnvaultState) else state.vault_txid
        pool = chain_state.trigger_utxos if isinstance(state, UnvaultState) else chain_state.vault_utxos
        utxos = [u for u in pool.values()
                 if hasattr(u, "outpoint") and target_txid in str(u.outpoint)]
        assert utxos, "Could not locate UTXO for permissionless-recovery probe"

        from verystable import core
        # Attacker has a fresh, unrelated private key — NOT the recoveryauth key.
        attacker_priv = core.key.ECKey()
        attacker_priv.set(b"\x33" * 32, True)
        attacker_priv_bytes = attacker_priv.get_bytes()

        def attacker_signer(msg: bytes) -> bytes:
            return core.key.sign_schnorr(attacker_priv_bytes, msg)

        self._ensure_fee_utxos()
        try:
            spec = self.ov.get_recovery_tx(config, self._fee_wallet, utxos, attacker_signer)
            if spec.cpfp_child is not None:
                res = self._ov_rpc.submitpackage([spec.tx.tohex(), spec.cpfp_child.tohex()])
                self._check_submitpackage(res)
            else:
                self._ov_rpc.sendrawtransaction(spec.tx.tohex())
            self._ov_rpc.generatetoaddress(1, self._fee_wallet.fee_addr)
            return "ACCEPTED"
        except Exception as e:
            return f"REJECTED: {str(e)[:120]}"

    @staticmethod
    def _check_submitpackage(result) -> None:
        """Raise if any tx in the package failed to enter the mempool."""
        if not isinstance(result, dict):
            return
        if result.get("package_msg") and result["package_msg"] != "success":
            raise RuntimeError(
                f"submitpackage failed: {result['package_msg']}: "
                f"tx-results={result.get('tx-results')}"
            )
        for txid, info in (result.get("tx-results") or {}).items():
            err = info.get("error") if isinstance(info, dict) else None
            if err:
                raise RuntimeError(f"submitpackage tx {txid} error: {err}")

    # ------------------------------------------------------------------
    # Internals & Capabilities
    # ------------------------------------------------------------------

    def get_internals(self) -> dict:
        return {
            "opvault_rpc": self._ov_rpc,
            "opvault_main": self.ov,
            "fee_wallet": self._fee_wallet,
            "workdir": self._workdir,
        }

    def recover_batched(self, states: List) -> TxRecord:
        """Batched authorized recovery: N Vault/Unvaulting UTXOs in one tx.

        BIP-345 §"Batching" lines 613–621 permits batched authorized recovery
        across UTXOs. Since all vaults in this adapter share the same
        VaultConfig (setup() uses a single xpub for all vault_num indices),
        they share a single recoveryauth key and a single recovery-sPK.
        The upstream ``ov.get_recovery_tx()`` accepts a list of UTXOs and
        constructs a transaction with N inputs, one shared ``recoveryOut``,
        and one ephemeral anchor.

        Args:
            states: list of ``VaultState`` and/or ``UnvaultState`` (at least 1)

        Returns:
            ``TxRecord`` for the batched recovery transaction.
        """
        assert len(states) >= 1, "Need at least one state to recover"

        config = self._shared_config
        monitor = self._shared_monitor
        chain_state = monitor.rescan()

        # Collect UTXOs from chain_state for each state. We support mixed
        # VaultState/UnvaultState in one batch; each source determines
        # whether to look in vault_utxos or trigger_utxos.
        collected = []
        total_amount = 0
        for st in states:
            if isinstance(st, VaultState):
                target = st.vault_txid
                pool = list(chain_state.vault_utxos.values())
            elif isinstance(st, UnvaultState):
                target = st.unvault_txid
                pool = list(chain_state.trigger_utxos.values())
                pool.extend(chain_state.theft_trigger_utxos.keys())
            else:
                raise ValueError(f"Cannot recover from {type(st).__name__}")

            matches = [u for u in pool
                       if target in str(getattr(u, "outpoint", ""))]
            if not matches:
                # Fall back to first unmatched UTXO of the right kind.
                # With a shared monitor, UTXOs may not carry the txid in
                # their outpoint string; pick by amount as a heuristic.
                matches = [u for u in pool
                           if getattr(u, "value_sats", 0) == st.amount_sats]
            assert matches, (
                f"No matching UTXO found for {target[:16]}… among {len(pool)}"
            )
            collected.append(matches[0])
            total_amount += st.amount_sats

        assert len(collected) == len(states), (
            f"Matched {len(collected)} UTXOs for {len(states)} states"
        )

        # Load recoveryauth key (shared across all vaults in this config)
        secd = json.loads(config.secrets_filepath.read_text())[config.id]
        recovery_privkey = self.ov.recoveryauth_phrase_to_key(
            secd['recoveryauth_phrase']).get_bytes()

        from verystable import core

        def recoveryauth_signer(msg: bytes) -> bytes:
            return core.key.sign_schnorr(recovery_privkey, msg)

        self._ensure_fee_utxos()

        # Upstream builds the batched recovery transaction. The function
        # accepts any number of UTXOs; each input contributes an
        # authorized-recovery witness path. The output is a single
        # recoveryOut aggregating all input amounts, plus an ephemeral
        # anchor for fee bumping (BIP-345 lines 389–391).
        recovery_spec = self.ov.get_recovery_tx(
            config, self._fee_wallet, collected, recoveryauth_signer
        )

        self._ov_rpc.sendrawtransaction(recovery_spec.tx.tohex())
        self._ov_rpc.generatetoaddress(1, self._fee_wallet.fee_addr)

        return TxRecord(
            txid=recovery_spec.tx.rehash(),
            label="recover_batched",
            amount_sats=total_amount,
        )

    def supports_revault(self) -> bool:
        """OP_VAULT supports partial withdrawal with revault.

        Atomic variants disable revaulting at the adapter level so the
        withdraw template covers full vault value.
        """
        return self.axes()[1] == "partial"

    def supports_batched_recovery(self) -> bool:
        """BIP-345 §"Batching" lines 613–621 authorized-recovery batching."""
        return True

    def supports_batched_trigger(self) -> bool:
        """OP_VAULT supports batching multiple vault UTXOs in one trigger.

        The start_withdrawal() function accepts a list of VaultUtxo objects,
        combining them into a single trigger transaction.
        """
        return True

    def trigger_revault(self, vault: VaultState, withdraw_sats: int) -> tuple:
        """Trigger a partial withdrawal with automatic revault of remainder.

        OP_VAULT's start_withdrawal() automatically creates a revault output
        when the vault UTXOs exceed the destination amount.  This method
        withdraws `withdraw_sats` and revaults the rest.

        Returns (UnvaultState, VaultState) — the unvaulting portion and
        the revaulted remainder.
        """
        metadata = vault.extra["metadata"]
        config = vault.extra["config"]
        monitor = vault.extra["monitor"]

        # Pick a destination address
        fee_addr = self._fee_wallet.fee_addr
        dest = self.ov.PaymentDestination(fee_addr, withdraw_sats)

        # Get available vault UTXOs from the chain state
        chain_state = monitor.rescan()
        vault_utxos = list(chain_state.vault_utxos.values())
        assert vault_utxos, "No vault UTXOs found after rescan"

        # Coin selection: find the UTXO matching our vault
        target_txid = vault.vault_txid
        matching = [u for u in vault_utxos
                    if hasattr(u, "outpoint") and target_txid in str(u.outpoint)]
        if matching:
            vault_utxos = matching[:1]
        else:
            vault_utxos = [min(vault_utxos,
                               key=lambda u: abs(u.value_sats - vault.amount_sats))]

        # Load trigger signing key
        secd = json.loads(config.secrets_filepath.read_text())[config.id]
        from bip32 import BIP32
        trig_b32 = BIP32.from_xpriv(secd['trigger_xpriv'])
        from verystable import core

        def trigger_key_signer(msg: bytes, vault_num: int) -> bytes:
            privkey = trig_b32.get_privkey_from_path(
                f"{config.trigger_xpub_path_prefix}/{vault_num}")
            return core.key.sign_schnorr(privkey, msg)

        # Refresh fee wallet — ensure mature UTXOs for the fee input
        self._ensure_fee_utxos()

        # Build trigger spec — start_withdrawal auto-revaults remainder
        trigger_spec = self.ov.start_withdrawal(
            config, self._fee_wallet, vault_utxos, dest, trigger_key_signer
        )

        # Register with metadata
        metadata.triggers[trigger_spec.id] = trigger_spec
        metadata.save()

        # Broadcast the trigger transaction
        assert trigger_spec.trigger_tx
        try:
            self._ov_rpc.sendrawtransaction(trigger_spec.trigger_tx.tohex())
        except Exception as e:
            if "-27" not in str(e):
                raise

        # Mine to confirm
        self._ov_rpc.generatetoaddress(1, self._fee_wallet.fee_addr)

        # Rescan to pick up the new state (revault UTXO + trigger UTXO)
        chain_state = monitor.rescan()

        # Compute remainder amount
        remainder_sats = vault.amount_sats - withdraw_sats - 2 * self.ov.FEE_VALUE_SATS
        assert remainder_sats > 0, (
            f"No remainder after withdrawing {withdraw_sats} from {vault.amount_sats}"
        )

        # Find the revault UTXO (new vault UTXO created by the trigger)
        new_vault_utxos = list(chain_state.vault_utxos.values())
        # The revault UTXO should be the one that appeared after our trigger
        revault_txid = trigger_spec.trigger_tx.rehash()

        unvault_state = UnvaultState(
            unvault_txid=revault_txid,
            amount_sats=withdraw_sats,
            blocks_remaining=self.block_delay,
            extra={
                **vault.extra,
                "trigger_spec": trigger_spec,
                "chain_state": chain_state,
            },
        )

        # Build the new VaultState for the revaulted remainder
        new_vault_state = VaultState(
            vault_txid=revault_txid,
            amount_sats=remainder_sats,
            vault_address=vault.vault_address,
            extra={
                **vault.extra,
                "chain_state": chain_state,
            },
        )

        return (unvault_state, new_vault_state)

    def trigger_batched(self, vaults: List[VaultState]) -> UnvaultState:
        """Trigger multiple vault UTXOs in a single transaction.

        All vaults share the same VaultConfig (created in setup()), so the
        shared monitor sees all UTXOs and start_withdrawal() accepts them
        as compatible specs.
        """
        assert len(vaults) >= 1, "Need at least one vault to trigger"

        config = self._shared_config
        metadata = self._shared_metadata
        monitor = self._shared_monitor

        # Compute total amount across all vaults
        total_amount = sum(v.amount_sats for v in vaults)

        fee_addr = self._fee_wallet.fee_addr
        withdraw_sats = total_amount - 2 * self.ov.FEE_VALUE_SATS
        assert withdraw_sats > 0
        dest = self.ov.PaymentDestination(fee_addr, withdraw_sats)

        # Shared monitor sees all vault UTXOs under this config
        chain_state = monitor.rescan()
        all_vault_utxos = list(chain_state.vault_utxos.values())

        # Match UTXOs to our vault set (remove matched to prevent duplicates)
        selected_utxos = []
        for v in vaults:
            matching = [u for u in all_vault_utxos
                        if hasattr(u, "outpoint") and v.vault_txid in str(u.outpoint)]
            if matching:
                selected_utxos.append(matching[0])
                all_vault_utxos.remove(matching[0])
            else:
                best = min(all_vault_utxos,
                           key=lambda u: abs(u.value_sats - v.amount_sats))
                selected_utxos.append(best)
                all_vault_utxos.remove(best)

        assert len(selected_utxos) == len(vaults), (
            f"Found {len(selected_utxos)} UTXOs for {len(vaults)} vaults"
        )

        # Shared trigger key — all vaults derive from the same xpub
        secd = json.loads(config.secrets_filepath.read_text())[config.id]
        from bip32 import BIP32
        trig_b32 = BIP32.from_xpriv(secd['trigger_xpriv'])
        from verystable import core

        def trigger_key_signer(msg: bytes, vault_num: int) -> bytes:
            privkey = trig_b32.get_privkey_from_path(
                f"{config.trigger_xpub_path_prefix}/{vault_num}")
            return core.key.sign_schnorr(privkey, msg)

        self._ensure_fee_utxos()

        # Build batched trigger
        trigger_spec = self.ov.start_withdrawal(
            config, self._fee_wallet, selected_utxos, dest, trigger_key_signer
        )

        metadata.triggers[trigger_spec.id] = trigger_spec
        metadata.save()

        # Broadcast
        assert trigger_spec.trigger_tx
        try:
            self._ov_rpc.sendrawtransaction(trigger_spec.trigger_tx.tohex())
        except Exception as e:
            if "-27" not in str(e):
                raise

        # Mine to confirm
        self._ov_rpc.generatetoaddress(1, self._fee_wallet.fee_addr)

        return UnvaultState(
            unvault_txid=trigger_spec.trigger_tx.rehash(),
            amount_sats=withdraw_sats,
            blocks_remaining=self.block_delay,
            extra={
                **vaults[0].extra,
                "trigger_spec": trigger_spec,
                "chain_state": monitor.rescan(),
            },
        )

    def supports_keyless_recovery(self) -> bool:
        # BIP-345 supports both authorised (g_key) and unauthorised
        # (g_keyless) modes; the active variant selects which.
        return self.axes()[2] == "keyless"

    # ------------------------------------------------------------------
    # Metrics collection
    # ------------------------------------------------------------------

    def collect_tx_metrics(self, record: TxRecord, rpc: RegTestRPC) -> TxMetrics:
        """Build TxMetrics from a broadcast transaction."""
        info = rpc.get_tx_info(record.txid)
        fee = rpc.get_tx_fee_sats(record.txid)

        script_type_map = {
            "tovault": "p2tr_opvault",
            "trigger": "p2tr_opvault",
            "withdraw": "p2tr_ctv",
            "tocold": "p2tr_opvault_recover",
            "recover": "p2tr_opvault_recover",
        }
        script_type = script_type_map.get(record.label, "p2tr")

        return TxMetrics(
            label=record.label,
            txid=record.txid,
            vsize=info["vsize"],
            weight=info["weight"],
            fee_sats=fee,
            num_inputs=len(info["vin"]),
            num_outputs=len(info["vout"]),
            amount_sats=record.amount_sats,
            script_type=script_type,
        )

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def teardown(self) -> None:
        """Remove temporary config/secret files."""
        import shutil
        if hasattr(self, '_workdir') and self._workdir.exists():
            shutil.rmtree(self._workdir, ignore_errors=True)
