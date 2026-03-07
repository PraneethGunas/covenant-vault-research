"""Framework-wide configuration.

Single source of truth for paths, fee constants, and experiment defaults.
Loaded from config.toml, overridable by environment variables.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional
import os

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # Python 3.10 fallback


@dataclass(frozen=True)
class FeeConstants:
    """Transaction vsize constants per covenant, per step.

    These drive the analytical fee_sensitivity experiment and provide
    reference values for metric validation in other experiments.
    """
    # CTV vsizes (from BIP-119 reference implementation measurements)
    ctv_tovault_vsize: int = 122
    ctv_trigger_vsize: int = 175
    ctv_withdraw_vsize: int = 155
    ctv_recover_vsize: int = 110

    # CCV vsizes (from pymatt vault measurements)
    ccv_tovault_vsize: int = 135
    ccv_trigger_vsize: int = 190
    ccv_withdraw_vsize: int = 168
    ccv_recover_vsize: int = 125

    # OP_VAULT vsizes (from BIP-345 reference)
    opvault_tovault_vsize: int = 130
    opvault_trigger_vsize: int = 185
    opvault_withdraw_vsize: int = 160
    opvault_recover_vsize: int = 115

    # CAT+CSFS vsizes (from simple-cat-csfs-vault measurements)
    cat_csfs_tovault_vsize: int = 153
    cat_csfs_trigger_vsize: int = 221
    cat_csfs_withdraw_vsize: int = 210
    cat_csfs_recover_vsize: int = 125

    def for_covenant(self, covenant: str) -> Dict[str, int]:
        """Get vsize constants for a specific covenant as a dict."""
        prefix = covenant.replace("-", "_").replace("+", "_")
        # Normalize: "cat_csfs" -> "cat_csfs", "opvault" -> "opvault"
        return {
            "tovault": getattr(self, f"{prefix}_tovault_vsize"),
            "trigger": getattr(self, f"{prefix}_trigger_vsize"),
            "withdraw": getattr(self, f"{prefix}_withdraw_vsize"),
            "recover": getattr(self, f"{prefix}_recover_vsize"),
        }


@dataclass(frozen=True)
class FrameworkConfig:
    """Top-level configuration for the vault comparison framework."""
    # Paths — resolved relative to vault-comparison/ root
    project_root: Path = field(default_factory=lambda: Path(__file__).parent)
    results_dir: Path = field(default_factory=lambda: Path(__file__).parent / "results")
    ctv_repo: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[1] / "simple-ctv-vault"
    )
    ccv_repo: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[1] / "pymatt"
    )
    opvault_repo: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[1] / "simple-op-vault"
    )
    cat_csfs_repo: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[1] / "simple-cat-csfs-vault"
    )

    # Experiment defaults
    default_block_delay: int = 10
    default_vault_amount: int = 100_000
    default_fee_rate: int = 5  # sat/vB

    # Fee model
    fees: FeeConstants = field(default_factory=FeeConstants)

    # RPC
    rpc_host: str = "127.0.0.1"
    rpc_port: int = 18443
    rpc_user: str = "rpcuser"
    rpc_password: str = "rpcpassword"

    def repo_for(self, covenant: str) -> Path:
        """Get the upstream repo path for a covenant."""
        mapping = {
            "ctv": self.ctv_repo,
            "ccv": self.ccv_repo,
            "opvault": self.opvault_repo,
            "cat_csfs": self.cat_csfs_repo,
        }
        return mapping[covenant]


def load_config(path: Path = None) -> FrameworkConfig:
    """Load config from TOML file, falling back to defaults.

    Environment variables override TOML values:
        VAULT_RPC_HOST, VAULT_RPC_PORT, VAULT_RPC_USER, VAULT_RPC_PASSWORD
    """
    kwargs = {}

    # Load from TOML if available
    if path is None:
        path = Path(__file__).parent / "config.toml"
    if path.exists():
        with open(path, "rb") as f:
            data = tomllib.load(f)

        if "paths" in data:
            for key, val in data["paths"].items():
                kwargs[key] = Path(val)
        if "defaults" in data:
            kwargs.update(data["defaults"])
        if "rpc" in data:
            for key, val in data["rpc"].items():
                kwargs[f"rpc_{key}"] = val

    # Environment variable overrides
    if os.environ.get("VAULT_RPC_HOST"):
        kwargs["rpc_host"] = os.environ["VAULT_RPC_HOST"]
    if os.environ.get("VAULT_RPC_PORT"):
        kwargs["rpc_port"] = int(os.environ["VAULT_RPC_PORT"])
    if os.environ.get("VAULT_RPC_USER"):
        kwargs["rpc_user"] = os.environ["VAULT_RPC_USER"]
    if os.environ.get("VAULT_RPC_PASSWORD"):
        kwargs["rpc_password"] = os.environ["VAULT_RPC_PASSWORD"]

    return FrameworkConfig(**kwargs)


# Module-level singleton — import as `from config import CFG`
CFG = load_config()
