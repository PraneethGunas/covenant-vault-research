"""CAT+CSFS vault adapter.

Wraps simple-cat-csfs-vault's VaultPlan / VaultExecutor to expose the
uniform VaultAdapter interface. Requires an OP_CAT + OP_CSFS enabled
regtest node (Bitcoin Inquisition >= v28.0).

Uses the same Bitcoin Inquisition node as CTV — no additional node
build required.
"""

import sys
from pathlib import Path
from typing import Optional, List, Tuple

from adapters.base import VaultAdapter, VaultState, UnvaultState, TxRecord
from harness.rpc import RegTestRPC
from harness.metrics import TxMetrics

# Add simple-cat-csfs-vault to the Python path so we can import its modules.
CAT_CSFS_REPO = Path(__file__).resolve().parents[2] / "simple-cat-csfs-vault"

# Counter for generating unique seeds per vault instance
_vault_counter = 0


def _ensure_cat_csfs_imports():
    """Lazy-load the CAT+CSFS vault modules."""
    repo_str = str(CAT_CSFS_REPO)
    if repo_str in sys.path:
        sys.path.remove(repo_str)
    sys.path.insert(0, repo_str)

    # Evict cached modules from other repos (e.g. simple-ctv-vault's main.py)
    for mod_name in ("main", "rpc", "vault", "taproot"):
        if mod_name in sys.modules:
            cached = sys.modules[mod_name]
            cached_path = getattr(cached, "__file__", "") or ""
            if repo_str not in cached_path:
                del sys.modules[mod_name]

    from bitcoin import SelectParams
    SelectParams("regtest")

    import vault as cat_vault
    import rpc as cat_rpc
    import taproot as cat_taproot
    return cat_vault, cat_rpc, cat_taproot


class CATCSFSAdapter(VaultAdapter):

    @property
    def name(self) -> str:
        return "cat_csfs"

    @property
    def node_mode(self) -> str:
        return "inquisition"

    @property
    def description(self) -> str:
        return "CAT+CSFS vault (BIP 347 + BIP 348) via simple-cat-csfs-vault"

    def setup(self, rpc: RegTestRPC, block_delay: int = 10, seed: bytes = b"compare", **kwargs) -> None:
        self.rpc = rpc
        self.block_delay = block_delay
        self.seed = seed
        self.cat_vault, self.cat_rpc, self.cat_taproot = _ensure_cat_csfs_imports()

        self.fee_wallet = self.cat_vault.Wallet.generate(b"fee-" + seed)
        self.cold_wallet = self.cat_vault.Wallet.generate(b"cold-" + seed)
        self.hot_wallet = self.cat_vault.Wallet.generate(b"hot-" + seed)
        self.dest_wallet = self.cat_vault.Wallet.generate(b"dest-" + seed)

        # Use cat_rpc's BitcoinRPC for CAT+CSFS-specific operations
        self._cat_rpc = self.cat_rpc.BitcoinRPC(net_name="regtest")

        # Coin pool: mine once, split many times.
        self._bank_wallet = self.cat_vault.Wallet.generate(b"bank-" + seed)
        self._bank_coins: list = []
        self._bank_initialized = False

    def _ensure_bank(self):
        """Mine a single coinbase and mature it. Called lazily on first use."""
        if self._bank_initialized:
            return
        self._bank_initialized = True

        bank_addr = self._bank_wallet.p2wpkh_address
        self._cat_rpc.generatetoaddress(1, bank_addr)

        # Mine 100 more blocks to mature the coinbase
        from buidl.hd import HDPrivateKey
        throwaway_addr = (
            HDPrivateKey.from_seed(b"throwaway-maturity")
            .get_private_key(1)
            .point.p2wpkh_address(network="regtest")
        )
        self._cat_rpc.generatetoaddress(100, throwaway_addr)

        # Scan for the mature coinbase
        from main import scan_utxos
        from vault import Coin, txid_to_bytes
        from bitcoin.core import COutPoint, COIN

        scan = scan_utxos(self._cat_rpc, bank_addr)
        if scan["success"]:
            for utxo in scan["unspents"]:
                coin = Coin(
                    COutPoint(txid_to_bytes(utxo["txid"]), utxo["vout"]),
                    int(utxo["amount"] * COIN),
                    bytes.fromhex(utxo["scriptPubKey"]),
                    utxo.get("height", 0),
                )
                self._bank_coins.append(coin)

    def _unique_seed(self) -> bytes:
        """Generate a unique seed for each vault to avoid tx collisions."""
        global _vault_counter
        _vault_counter += 1
        return self.seed + b"-vault-" + str(_vault_counter).encode()

    def _split_coin(self, source_coin, source_wallet, amount_sats: int):
        """Split a source coin, returning (target_coin, target_wallet, change_coin)."""
        from bitcoin.core import (
            CMutableTransaction, CTxIn, CTxOut, CTransaction,
            CTxInWitness, CScriptWitness, CTxWitness, COutPoint, COIN,
        )
        from bitcoin.core.script import CScript, OP_0
        from bitcoin.wallet import CBech32BitcoinAddress
        import bitcoin.core.script as script
        from vault import Coin, txid_to_bytes

        unique_seed = self._unique_seed()
        target_wallet = self.cat_vault.Wallet.generate(b"split-" + unique_seed)
        target_addr = target_wallet.p2wpkh_address
        target_h160 = CBech32BitcoinAddress(target_addr)
        target_script = CScript([OP_0, target_h160])

        source_addr = source_wallet.p2wpkh_address
        change_h160 = CBech32BitcoinAddress(source_addr)
        change_script = CScript([OP_0, change_h160])
        change_amount = source_coin.amount - amount_sats - 1000  # 1000 sat fee

        tx = CMutableTransaction()
        tx.nVersion = 2
        tx.vin = [CTxIn(source_coin.outpoint, nSequence=0)]
        tx.vout = [CTxOut(amount_sats, target_script)]

        change_coin = None
        change_vout_idx = None
        if change_amount > 546:
            tx.vout.append(CTxOut(change_amount, change_script))
            change_vout_idx = 1

        # Sign (P2WPKH)
        redeem_script = CScript([
            script.OP_DUP, script.OP_HASH160,
            CBech32BitcoinAddress(source_addr),
            script.OP_EQUALVERIFY, script.OP_CHECKSIG,
        ])
        sighash = script.SignatureHash(
            redeem_script, tx, 0, script.SIGHASH_ALL,
            amount=source_coin.amount, sigversion=script.SIGVERSION_WITNESS_V0,
        )
        sig = source_wallet.privkey.sign(int.from_bytes(sighash, "big")).der() + bytes([script.SIGHASH_ALL])
        tx.wit = CTxWitness([CTxInWitness(CScriptWitness([sig, source_wallet.privkey.point.sec()]))])

        split_tx = CTransaction.from_tx(tx)
        split_hex = split_tx.serialize().hex()
        split_txid = self._cat_rpc.sendrawtransaction(split_hex)

        from main import get_rpc
        self._cat_rpc.generatetoaddress(1, self.fee_wallet.p2wpkh_address)

        # Build target coin
        target_coin = Coin(
            COutPoint(txid_to_bytes(split_txid), 0),
            amount_sats,
            bytes(target_script),
            0,
        )

        # Build change coin for reuse
        if change_vout_idx is not None and change_amount > 546:
            change_coin = Coin(
                COutPoint(txid_to_bytes(split_txid), change_vout_idx),
                change_amount,
                bytes(change_script),
                0,
            )

        return target_coin, target_wallet, change_coin

    def _fund_coin(self, amount_sats: int):
        """Get a coin of the desired amount from the coin pool."""
        self._ensure_bank()

        for i, coin in enumerate(self._bank_coins):
            if coin.amount >= amount_sats + 1546:
                source_coin = self._bank_coins.pop(i)
                target_coin, target_wallet, change_coin = self._split_coin(
                    source_coin, self._bank_wallet, amount_sats
                )
                if change_coin and change_coin.amount > 10_000:
                    self._bank_coins.append(change_coin)
                return target_coin, target_wallet

        # No coin large enough — mine a new coinbase
        bank_addr = self._bank_wallet.p2wpkh_address
        self._cat_rpc.generatetoaddress(1, bank_addr)

        from buidl.hd import HDPrivateKey
        throwaway_addr = (
            HDPrivateKey.from_seed(b"throwaway-maturity-extra")
            .get_private_key(1)
            .point.p2wpkh_address(network="regtest")
        )
        self._cat_rpc.generatetoaddress(100, throwaway_addr)

        from main import scan_utxos
        from vault import Coin, txid_to_bytes
        from bitcoin.core import COutPoint, COIN

        scan = scan_utxos(self._cat_rpc, bank_addr)
        if scan["success"]:
            for utxo in scan["unspents"]:
                coin = Coin(
                    COutPoint(txid_to_bytes(utxo["txid"]), utxo["vout"]),
                    int(utxo["amount"] * COIN),
                    bytes.fromhex(utxo["scriptPubKey"]),
                    utxo.get("height", 0),
                )
                if coin not in self._bank_coins:
                    self._bank_coins.append(coin)

        # Retry
        for i, coin in enumerate(self._bank_coins):
            if coin.amount >= amount_sats + 1546:
                source_coin = self._bank_coins.pop(i)
                target_coin, target_wallet, change_coin = self._split_coin(
                    source_coin, self._bank_wallet, amount_sats
                )
                if change_coin and change_coin.amount > 10_000:
                    self._bank_coins.append(change_coin)
                return target_coin, target_wallet

        raise RuntimeError(
            f"Cannot fund {amount_sats} sats — bank coins: "
            f"{[c.amount for c in self._bank_coins]}"
        )

    def create_vault(self, amount_sats: int) -> VaultState:
        """Fund a wallet, then create a vault of the specified amount."""
        coin, from_wallet = self._fund_coin(amount_sats)

        plan = self.cat_vault.VaultPlan(
            hot_wallet=self.hot_wallet,
            cold_wallet=self.cold_wallet,
            dest_wallet=self.dest_wallet,
            fee_wallet=self.fee_wallet,
            coin_in=coin,
            block_delay=self.block_delay,
        )
        executor = self.cat_vault.VaultExecutor(plan, self._cat_rpc)

        # Sign and broadcast tovault transaction
        tovault_tx = plan.sign_tovault(from_wallet.privkey)
        tovault_hex = tovault_tx.serialize().hex()
        txid = self._cat_rpc.sendrawtransaction(tovault_hex)

        # Mine to confirm
        self._cat_rpc.generatetoaddress(1, self.fee_wallet.p2wpkh_address)

        return VaultState(
            vault_txid=txid,
            amount_sats=plan.amount_at_step(1),
            extra={
                "plan": plan,
                "executor": executor,
                "coin": coin,
                "from_wallet": from_wallet,
            },
        )

    def trigger_unvault(self, vault: VaultState) -> UnvaultState:
        """Broadcast the trigger transaction (hot key + CSFS introspection)."""
        plan = vault.extra["plan"]
        executor = vault.extra["executor"]

        unvault_txid = executor.trigger_unvault()
        self._cat_rpc.generatetoaddress(1, self.fee_wallet.p2wpkh_address)

        return UnvaultState(
            unvault_txid=unvault_txid,
            amount_sats=plan.amount_at_step(2),
            blocks_remaining=self.block_delay,
            extra=vault.extra,
        )

    def complete_withdrawal(self, unvault: UnvaultState, path: str = "hot") -> TxRecord:
        """Complete withdrawal via hot path (after CSV) or cold path (recovery).

        CAT+CSFS vault paths:
            path="hot":  withdraw_tx — sends to destination after CSV timelock.
                         Uses hot key + CSFS introspection.
            path="cold": recover — immediate sweep to cold wallet (cold key only).

        For cross-covenant experiments: use path="hot" for normal withdrawal,
        and recover() for emergency recovery.
        """
        plan = unvault.extra["plan"]
        executor = unvault.extra["executor"]

        if path == "hot":
            # Mine enough blocks for CSV to pass
            self._cat_rpc.generatetoaddress(
                self.block_delay, self.fee_wallet.p2wpkh_address
            )
            withdraw_txid = executor.complete_withdrawal()
            label = "withdraw"
            amount = plan.amount_at_step(3)
        else:
            # Cold sweep from loop
            recover_txid = executor.recover(from_vault=False)
            self._cat_rpc.generatetoaddress(1, self.fee_wallet.p2wpkh_address)
            return TxRecord(
                txid=recover_txid,
                label="recover",
                raw_hex="",
                amount_sats=plan.amount_at_step(2) - plan.fees_per_step,
            )

        self._cat_rpc.generatetoaddress(1, self.fee_wallet.p2wpkh_address)

        tx = plan.sign_withdraw()
        return TxRecord(
            txid=withdraw_txid,
            label=label,
            raw_hex=tx.serialize().hex(),
            amount_sats=amount,
        )

    def recover(self, state) -> TxRecord:
        """Execute emergency recovery to cold wallet.

        CAT+CSFS recovery uses the cold key via OP_CHECKSIG in the recover
        leaf — no introspection needed, just a Schnorr signature.

        Works from both VaultState (recover from vault) and UnvaultState
        (recover from vault-loop).
        """
        plan = state.extra["plan"]
        executor = state.extra["executor"]

        if isinstance(state, VaultState):
            recover_txid = executor.recover(from_vault=True)
            source_amount = plan.amount_at_step(1)
        elif isinstance(state, UnvaultState):
            recover_txid = executor.recover(from_vault=False)
            source_amount = plan.amount_at_step(2)
        else:
            raise ValueError(f"Cannot recover from state type: {type(state)}")

        self._cat_rpc.generatetoaddress(1, self.fee_wallet.p2wpkh_address)

        recover_amount = source_amount - plan.fees_per_step
        return TxRecord(
            txid=recover_txid,
            label="recover",
            raw_hex="",
            amount_sats=recover_amount,
        )

    # ── Capabilities ─────────────────────────────────────────────────

    def supports_revault(self) -> bool:
        return False

    def supports_batched_trigger(self) -> bool:
        return False

    def supports_keyless_recovery(self) -> bool:
        return False  # Requires cold key signature

    # ── Metrics enrichment ───────────────────────────────────────────

    def collect_tx_metrics(self, record: TxRecord, rpc: RegTestRPC) -> TxMetrics:
        metrics = super().collect_tx_metrics(record, rpc)

        # Annotate with CAT+CSFS-specific script type info
        if record.label == "tovault":
            metrics.script_type = "p2wpkh_to_p2tr"
        elif record.label in ("trigger", "unvault"):
            metrics.script_type = "p2tr_cat_csfs"
        elif record.label == "withdraw":
            metrics.script_type = "p2tr_cat_csfs"
            metrics.csv_blocks = self.block_delay
        elif record.label == "recover":
            metrics.script_type = "p2tr_checksig"

        return metrics
