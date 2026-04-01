"""Simplicity vault adapter — Elements regtest with jet-based covenants.

Wraps the simple-simplicity-vault Rust CLI (vault-cli) via subprocess.
Requires ``simplex regtest`` to be running (starts elementsd + electrs).

Port discovery is automatic — the adapter reads the RPC and Esplora
ports from the running elementsd/electrs process arguments. No fixed
port assumptions.

The vault-cli binary must be pre-built at
    simple-simplicity-vault/target/release/vault-cli
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from adapters.base import VaultAdapter, VaultState, UnvaultState, TxRecord
from harness.rpc import RegTestRPC, RPCError
from harness.metrics import TxMetrics


# Elements regtest fee constant from plan.rs
_SIMPLICITY_TX_FEE_SATS = 500

# Default mnemonics (must match simple-simplicity-vault defaults)
_DEFAULT_HOT_MNEMONIC = (
    "exist carry drive collect lend cereal occur "
    "much tiger just involve mean"
)
_DEFAULT_COLD_MNEMONIC = (
    "abandon abandon abandon abandon abandon abandon "
    "abandon abandon abandon abandon abandon about"
)


def discover_simplex_ports():
    """Discover elementsd and electrs ports from running ``simplex regtest``.

    Parses process arguments to find:
        - elementsd: -rpcport=N
        - electrs:   --http-addr 0.0.0.0:N  and  --cookie USER:PASS

    Returns:
        (rpc_port, esplora_port, rpc_user, rpc_pass) or raises RuntimeError.
    """
    result = subprocess.run(["ps", "aux"], capture_output=True, text=True)

    rpc_port = esplora_port = None
    rpc_user = rpc_pass = None

    for line in result.stdout.splitlines():
        if "elementsd" in line and "-rpcport=" in line:
            m = re.search(r"-rpcport=(\d+)", line)
            if m:
                rpc_port = int(m.group(1))

        if "electrs" in line and "--http-addr" in line:
            m = re.search(r"--http-addr\s+\S+?:(\d+)", line)
            if m:
                esplora_port = int(m.group(1))
            m = re.search(r"--cookie\s+(\S+)", line)
            if m:
                cookie = m.group(1)
                parts = cookie.split(":", 1)
                if len(parts) == 2:
                    rpc_user, rpc_pass = parts

    if not all([rpc_port, esplora_port, rpc_user, rpc_pass]):
        missing = []
        if not rpc_port:
            missing.append("elementsd RPC port")
        if not esplora_port:
            missing.append("electrs Esplora port")
        if not rpc_user:
            missing.append("RPC credentials")
        raise RuntimeError(
            f"Cannot discover simplex regtest: {', '.join(missing)} not found.\n"
            f"Start it first:  simplex regtest"
        )

    return rpc_port, esplora_port, rpc_user, rpc_pass


class SimplicityAdapter(VaultAdapter):
    """Simplicity vault on Elements regtest via jet-based covenant enforcement."""

    # ── Identity ──────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "simplicity"

    @property
    def node_mode(self) -> str:
        return "elements"

    @property
    def description(self) -> str:
        return "Simplicity vault on Elements regtest (jet-based covenants)"

    # ── Setup ─────────────────────────────────────────────────

    def setup(self, rpc: RegTestRPC, block_delay: int = 10, **kwargs) -> None:
        self.block_delay = block_delay
        self._vault_repo = (
            Path(__file__).resolve().parents[1].parent / "simple-simplicity-vault"
        )

        # Auto-discover ports from running simplex regtest,
        # or use environment overrides if set.
        if os.getenv("ELEMENTS_RPC_PORT"):
            rpc_port = int(os.environ["ELEMENTS_RPC_PORT"])
            esplora_port = int(os.getenv("ESPLORA_PORT", "3000"))
            rpc_user = os.getenv("ELEMENTS_RPC_USER", "user")
            rpc_pass = os.getenv("ELEMENTS_RPC_PASSWORD", "password")
        else:
            rpc_port, esplora_port, rpc_user, rpc_pass = discover_simplex_ports()

        self._elements_rpc = RegTestRPC(
            host="127.0.0.1",
            port=rpc_port,
            user=rpc_user,
            password=rpc_pass,
        )
        self.rpc = self._elements_rpc
        self._esplora_url = f"http://127.0.0.1:{esplora_port}"

        self._binary = self._find_binary()
        self._work_dir = Path(tempfile.mkdtemp(prefix="simplicity_vault_"))
        self._hot_mnemonic = _DEFAULT_HOT_MNEMONIC
        self._cold_mnemonic = _DEFAULT_COLD_MNEMONIC
        self._vault_counter = 0
        self._mine_address = self._init_elements_wallet()
        self._electrs_delay = float(os.getenv("ELECTRS_DELAY", "0.5"))

    def _find_binary(self) -> str:
        release = self._vault_repo / "target" / "release" / "vault-cli"
        debug = self._vault_repo / "target" / "debug" / "vault-cli"
        if release.exists():
            return str(release)
        if debug.exists():
            return str(debug)
        raise FileNotFoundError(
            f"vault-cli not found. Build it:\n"
            f"  cd {self._vault_repo} && cargo build --release"
        )

    def _init_elements_wallet(self) -> str:
        """Get a mining address from the default Elements wallet.

        ``simplex regtest`` creates a default wallet automatically.
        We use it as-is rather than creating a separate wallet, which
        would force all RPC calls to specify a wallet path.
        """
        # Find the loaded wallet name — simplex regtest creates one
        wallets = self._elements_rpc._call("listwallets")
        if wallets:
            wallet_rpc = RegTestRPC(
                host=self._elements_rpc.host,
                port=self._elements_rpc.port,
                user=self._elements_rpc.user,
                password=self._elements_rpc.password,
                wallet=wallets[0],
            )
            return wallet_rpc._call("getnewaddress")
        # No wallet loaded — try base RPC (single-wallet mode)
        return self._elements_rpc._call("getnewaddress")

    def teardown(self) -> None:
        if hasattr(self, "_work_dir") and self._work_dir.exists():
            shutil.rmtree(self._work_dir, ignore_errors=True)

    # ── CLI invocation ────────────────────────────────────────

    def _cli(self, *args, parse_stdout: bool = True) -> str:
        """Run vault-cli with auto-discovered connection details."""
        cmd = [
            self._binary,
            "--rpc-url", f"http://{self._elements_rpc.host}:{self._elements_rpc.port}",
            "--esplora-url", self._esplora_url,
            "--rpc-user", self._elements_rpc.user,
            "--rpc-pass", self._elements_rpc.password,
            "--hot-mnemonic", self._hot_mnemonic,
            "--cold-mnemonic", self._cold_mnemonic,
            *args,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self._work_dir),
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"vault-cli {' '.join(args)} failed (exit {result.returncode}):\n"
                f"  stdout: {result.stdout.strip()}\n"
                f"  stderr: {result.stderr.strip()}"
            )
        return result.stdout.strip() if parse_stdout else result.stdout

    def _mine_and_wait(self, n: int = 1) -> None:
        """Mine blocks and wait for electrs to index them.

        Instead of a fixed sleep, polls the Esplora API until the
        reported tip height matches what elementsd reports. Falls back
        to a fixed delay if the Esplora endpoint can't be reached.
        """
        self._elements_rpc._call("generatetoaddress", n, self._mine_address)
        try:
            expected = int(self._elements_rpc._call("getblockcount"))
        except Exception:
            time.sleep(self._electrs_delay)
            return

        import urllib.request
        tip_url = f"{self._esplora_url}/blocks/tip/height"
        for _ in range(30):  # up to 15 seconds
            try:
                with urllib.request.urlopen(tip_url, timeout=2) as resp:
                    tip = int(resp.read().decode().strip())
                    if tip >= expected:
                        return
            except Exception:
                pass
            time.sleep(0.5)
        # Fallback if polling didn't converge
        time.sleep(self._electrs_delay)

    def _get_status(self, txid: str) -> dict:
        raw = self._cli("status", txid, parse_stdout=False)
        return json.loads(raw)

    # ── Core vault lifecycle ──────────────────────────────────

    def create_vault(self, amount_sats: int) -> VaultState:
        self._vault_counter += 1

        vault_txid = self._cli(
            "vault",
            "--amount", str(amount_sats),
            "--delay", str(self.block_delay),
        )

        if self._electrs_delay > 0:
            time.sleep(self._electrs_delay)

        state_data = self._get_status(vault_txid)

        return VaultState(
            vault_txid=vault_txid,
            amount_sats=amount_sats,
            vault_address=state_data.get("vault_address", ""),
            extra={
                "state_data": state_data,
                "block_delay": self.block_delay,
            },
        )

    def trigger_unvault(self, vault: VaultState) -> UnvaultState:
        unvault_txid = self._cli("trigger", vault.vault_txid)
        self._mine_and_wait(1)

        trigger_amount = vault.amount_sats - _SIMPLICITY_TX_FEE_SATS

        return UnvaultState(
            unvault_txid=unvault_txid,
            amount_sats=trigger_amount,
            blocks_remaining=self.block_delay,
            extra={
                "vault_txid": vault.vault_txid,
                "state_data": vault.extra["state_data"],
                "block_delay": self.block_delay,
            },
        )

    def complete_withdrawal(self, unvault: UnvaultState, path: str = "hot") -> TxRecord:
        if path != "hot":
            raise ValueError(
                "Simplicity adapter: use recover() for emergency recovery, "
                "not complete_withdrawal(path='cold')."
            )

        self._mine_and_wait(self.block_delay)
        withdraw_txid = self._cli("withdraw", unvault.extra["vault_txid"])
        self._mine_and_wait(1)

        withdraw_amount = unvault.amount_sats - _SIMPLICITY_TX_FEE_SATS

        return TxRecord(
            txid=withdraw_txid,
            label="withdraw",
            raw_hex="",
            amount_sats=withdraw_amount,
        )

    def recover(self, state) -> TxRecord:
        if isinstance(state, VaultState):
            ref_txid = state.vault_txid
            source_amount = state.amount_sats
        elif isinstance(state, UnvaultState):
            ref_txid = state.extra["vault_txid"]
            source_amount = state.amount_sats
        else:
            raise ValueError(f"Cannot recover from state type: {type(state)}")

        recover_txid = self._cli("recover", ref_txid)
        self._mine_and_wait(1)

        recover_amount = source_amount - _SIMPLICITY_TX_FEE_SATS

        return TxRecord(
            txid=recover_txid,
            label="recover",
            raw_hex="",
            amount_sats=recover_amount,
        )

    # ── Internals & Capabilities ──────────────────────────────

    def get_internals(self) -> dict:
        return {
            "elements_rpc": self._elements_rpc,
            "esplora_url": self._esplora_url,
            "vault_repo": self._vault_repo,
            "binary": self._binary,
            "work_dir": self._work_dir,
            "tx_fee_sats": _SIMPLICITY_TX_FEE_SATS,
        }

    def capabilities(self) -> dict:
        return {
            "revault": False,
            "batched_trigger": False,
            "keyless_recovery": False,
            "output_constrained_recovery": True,
            "csv_timelock": True,
            "dual_key": True,
            "max_batch_size": None,
            "recovery_requires_key": True,
        }

    def supports_revault(self) -> bool:
        return False

    def supports_batched_trigger(self) -> bool:
        return False

    def supports_keyless_recovery(self) -> bool:
        return False

    # ── Metrics collection ────────────────────────────────────

    def collect_tx_metrics(self, record: TxRecord, rpc: RegTestRPC) -> TxMetrics:
        """Collect metrics from Elements RPC.

        Elements uses explicit fee outputs instead of Bitcoin's implicit fees.
        """
        info = self._elements_rpc._call("getrawtransaction", record.txid, True)

        vsize = info.get("vsize", info.get("size", 0))
        weight = info.get("weight", vsize * 4)
        fee_sats = self._extract_elements_fee(info)

        metrics = TxMetrics(
            label=record.label,
            txid=record.txid,
            vsize=vsize,
            weight=weight,
            fee_sats=fee_sats,
            num_inputs=len(info.get("vin", [])),
            num_outputs=len(info.get("vout", [])),
            amount_sats=record.amount_sats,
        )

        metrics.script_type = "p2tr_simplicity"
        if record.label == "withdraw":
            metrics.csv_blocks = self.block_delay

        return metrics

    @staticmethod
    def _extract_elements_fee(tx_info: dict) -> int:
        """Extract explicit fee from an Elements transaction."""
        from decimal import Decimal
        fee_sats = 0
        for vout in tx_info.get("vout", []):
            spk = vout.get("scriptPubKey", {})
            if spk.get("type") == "fee" or (
                spk.get("hex", "x") == "" and spk.get("asm", "x") == ""
            ):
                value = vout.get("value", 0)
                try:
                    fee_sats += int(Decimal(str(value)) * 100_000_000)
                except Exception:
                    pass
        return fee_sats
