"""Vault adapters — one per covenant type.

Each adapter wraps a vault implementation and exposes a uniform interface
for creating vaults, triggering unvaults, recovering, and withdrawing.
"""

from adapters.base import VaultAdapter, VaultState, UnvaultState, TxRecord

__all__ = ["VaultAdapter", "VaultState", "UnvaultState", "TxRecord"]
