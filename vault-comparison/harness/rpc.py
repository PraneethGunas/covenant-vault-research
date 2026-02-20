"""Unified RPC client for regtest nodes.

Thin wrapper over JSON-RPC that works with both Bitcoin Inquisition (CTV)
and Merkleize Bitcoin (CCV) nodes. Provides helpers for common operations
used by adapters and experiments.
"""

import json
import http.client
import base64
import os
import platform
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional


SATS_PER_BTC = 100_000_000


class RPCError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"RPC error {code}: {message}")


@dataclass
class RegTestRPC:
    """JSON-RPC client for a regtest Bitcoin node."""

    host: str = "localhost"
    port: int = 18443
    user: str = "rpcuser"
    password: str = "rpcpass"
    wallet: Optional[str] = None
    timeout: int = 30

    _id_counter: int = 0

    @classmethod
    def from_env(cls, wallet: Optional[str] = None) -> "RegTestRPC":
        """Create from environment variables, falling back to defaults."""
        return cls(
            host=os.getenv("RPC_HOST", "localhost"),
            port=int(os.getenv("RPC_PORT", "18443")),
            user=os.getenv("RPC_USER", "rpcuser"),
            password=os.getenv("RPC_PASSWORD", "rpcpass"),
            wallet=wallet or os.getenv("WALLET_NAME"),
        )

    @classmethod
    def from_cookie(cls, net_name: str = "regtest") -> "RegTestRPC":
        """Create from bitcoin.conf cookie authentication."""
        if platform.system() == "Darwin":
            datadir = os.path.expanduser("~/Library/Application Support/Bitcoin/")
        else:
            datadir = os.path.expanduser("~/.bitcoin/")
        cookie_path = os.path.join(datadir, net_name, ".cookie")
        try:
            with open(cookie_path) as f:
                authpair = f.read().strip()
            user, password = authpair.split(":", 1)
            return cls(user=user, password=password)
        except FileNotFoundError:
            return cls.from_env()

    def _call(self, method: str, *params: Any) -> Any:
        self._id_counter += 1
        path = f"/wallet/{self.wallet}" if self.wallet else "/"
        body = json.dumps({
            "jsonrpc": "2.0",
            "id": self._id_counter,
            "method": method,
            "params": list(params),
        })
        auth = base64.b64encode(f"{self.user}:{self.password}".encode()).decode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth}",
        }
        conn = http.client.HTTPConnection(self.host, self.port, timeout=self.timeout)
        conn.request("POST", path, body, headers)
        resp = conn.getresponse()
        raw = resp.read().decode()
        if not raw.strip():
            raise RPCError(-1, f"Empty response from node (HTTP {resp.status} {resp.reason}) for {method} at {path}")
        data = json.loads(raw, parse_float=Decimal)
        if data.get("error"):
            raise RPCError(data["error"]["code"], data["error"]["message"])
        return data["result"]

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        def caller(*args, **kwargs):
            return self._call(name, *args)
        caller.__name__ = name
        return caller

    # ── Convenience helpers ──────────────────────────────────────────

    def wait_for_ready(self, retries: int = 30, delay: float = 1.0) -> None:
        """Block until the node responds to RPC."""
        for _ in range(retries):
            try:
                self.getblockchaininfo()
                return
            except (ConnectionRefusedError, OSError, RPCError):
                time.sleep(delay)
        raise TimeoutError("Node did not become ready")

    def mine(self, n: int = 1, address: str = None) -> List[str]:
        if not address:
            address = self.getnewaddress()
        return self.generatetoaddress(n, address)

    def get_tx_info(self, txid: str) -> Dict:
        """Get decoded transaction with full details."""
        return self.getrawtransaction(txid, True)

    def get_tx_vsize(self, txid: str) -> int:
        info = self.get_tx_info(txid)
        return info["vsize"]

    def get_tx_weight(self, txid: str) -> int:
        info = self.get_tx_info(txid)
        return info["weight"]

    def get_tx_fee_sats(self, txid: str) -> int:
        """Calculate fee by summing inputs - outputs. Requires txindex=1."""
        info = self.get_tx_info(txid)
        input_total = 0
        for vin in info["vin"]:
            if "coinbase" in vin:
                return 0
            prev = self.get_tx_info(vin["txid"])
            input_total += int(prev["vout"][vin["vout"]]["value"] * SATS_PER_BTC)
        output_total = sum(int(v["value"] * SATS_PER_BTC) for v in info["vout"])
        return input_total - output_total

    def btc_to_sats(self, btc: Decimal) -> int:
        return int(btc * SATS_PER_BTC)
