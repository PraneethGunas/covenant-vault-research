"""Tests for centralized configuration."""

from pathlib import Path
from config import CFG, FrameworkConfig, FeeConstants, load_config


def test_default_config_loads():
    cfg = FrameworkConfig()
    assert cfg.default_block_delay == 10
    assert cfg.default_vault_amount == 100_000
    assert cfg.rpc_port == 18443


def test_fee_constants_exist():
    fees = FeeConstants()
    assert fees.ctv_trigger_vsize > 0
    assert fees.ccv_trigger_vsize > 0
    assert fees.opvault_trigger_vsize > 0
    assert fees.cat_csfs_trigger_vsize > 0


def test_fee_constants_for_covenant():
    fees = FeeConstants()
    ctv = fees.for_covenant("ctv")
    assert "tovault" in ctv
    assert "trigger" in ctv
    assert "withdraw" in ctv
    assert "recover" in ctv
    assert ctv["trigger"] == 94


def test_fee_constants_for_cat_csfs():
    fees = FeeConstants()
    cat = fees.for_covenant("cat_csfs")
    assert cat["trigger"] == 221
    assert cat["withdraw"] == 210


def test_repo_for():
    cfg = FrameworkConfig()
    ctv_repo = cfg.repo_for("ctv")
    assert "simple-ctv-vault" in str(ctv_repo)
    cat_repo = cfg.repo_for("cat_csfs")
    assert "simple-cat-csfs-vault" in str(cat_repo)
    sim_repo = cfg.repo_for("simplicity")
    assert "simple-simplicity-vault" in str(sim_repo)


def test_cfg_singleton():
    """Module-level CFG should be a FrameworkConfig instance."""
    assert isinstance(CFG, FrameworkConfig)
    assert CFG.rpc_host == "127.0.0.1"


def test_load_config_nonexistent_toml():
    """Loading from a nonexistent path should return defaults."""
    cfg = load_config(Path("/nonexistent/config.toml"))
    assert cfg.default_block_delay == 10


def test_results_dir_is_path():
    cfg = FrameworkConfig()
    assert isinstance(cfg.results_dir, Path)
