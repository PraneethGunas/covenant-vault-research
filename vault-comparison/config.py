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
    # CTV vsizes (regtest-measured via lifecycle_costs experiment)
    ctv_tovault_vsize: int = 122
    ctv_trigger_vsize: int = 94
    ctv_withdraw_vsize: int = 152
    ctv_recover_vsize: int = 133

    # CCV vsizes (regtest-measured via lifecycle_costs experiment)
    ccv_tovault_vsize: int = 300
    ccv_trigger_vsize: int = 154
    ccv_withdraw_vsize: int = 111
    ccv_recover_vsize: int = 122

    # OP_VAULT vsizes (regtest-measured via lifecycle_costs experiment)
    opvault_tovault_vsize: int = 154
    opvault_trigger_vsize: int = 292
    opvault_withdraw_vsize: int = 121
    opvault_recover_vsize: int = 246

    # CAT+CSFS vsizes (regtest-measured via lifecycle_costs experiment)
    cat_csfs_tovault_vsize: int = 122
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

    def for_variant(self, variant_id: str) -> Dict[str, int]:
        """Get vsize constants for a specific (covenant, variant) pair.

        ``variant_id`` is the canonical id from the adapter
        (``adapter.variant_id``): e.g. ``"opvault"`` for the reference,
        ``"opvault-keyless"`` for the unauthorised mode, etc.

        Variants share tovault/trigger/withdraw vsizes with their
        reference; only the recover-tx vsize differs (per the regtest
        measurements documented in DESIGN.md §3.8).
        """
        # Normalise: drop reference-equivalents, parse opcode + variant suffix
        if variant_id == "reference" or "-" not in variant_id:
            return self.for_covenant(variant_id)

        # Split off the opcode and the variant suffix
        parts = variant_id.split("-", 1)
        if len(parts) != 2:
            return self.for_covenant(variant_id)
        covenant, variant = parts
        base = self.for_covenant(covenant)

        # Per-variant recover-tx vsize deltas (regtest-measured).
        # Other lifecycle vsizes are unchanged across variants.
        recover_overrides = {
            ("ctv", "keygated"):                 160,
            ("ccv", "atomic"):                   122,
            ("ccv", "keygated"):                 147,
            ("ccv", "keygated-atomic"):          147,
            ("opvault", "keyless"):              131,
            ("opvault", "atomic"):               246,
            ("opvault", "keyless-atomic"):       131,
            ("cat_csfs", "bound"):               209,
        }
        if (covenant, variant) in recover_overrides:
            base = dict(base)
            base["recover"] = recover_overrides[(covenant, variant)]
        return base


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
    simplicity_repo: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[1] / "simple-simplicity-vault"
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
            "simplicity": self.simplicity_repo,
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
