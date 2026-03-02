"""Vault adapters — one per covenant type.

Each adapter wraps a vault implementation and exposes a uniform interface
for creating vaults, triggering unvaults, recovering, and withdrawing.
"""

from adapters.base import VaultAdapter, VaultState, UnvaultState, TxRecord

__all__ = ["VaultAdapter", "VaultState", "UnvaultState", "TxRecord"]

# Lazy imports to avoid pulling in heavy deps at module load time:
#   from adapters.ctv_adapter import CTVAdapter
#   from adapters.ccv_adapter import CCVAdapter
#   from adapters.opvault_adapter import OPVaultAdapter
#   from adapters.cat_csfs_adapter import CATCSFSAdapter
