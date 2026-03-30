"""Tests for experiment registry and discovery."""

import pytest

from experiments.registry import ExperimentSpec, EXPERIMENTS, get_experiment


def _ensure_experiments_loaded():
    """Import all experiment modules so they register themselves."""
    import experiments.exp_lifecycle_costs  # noqa: F401
    import experiments.exp_address_reuse  # noqa: F401
    import experiments.exp_fee_pinning  # noqa: F401
    import experiments.exp_revault_amplification  # noqa: F401
    import experiments.exp_multi_input  # noqa: F401
    import experiments.exp_recovery_griefing  # noqa: F401
    # exp_ccv_edge_cases removed — subsumed by exp_ccv_mode_bypass
    import experiments.exp_watchtower_exhaustion  # noqa: F401
    import experiments.exp_fee_sensitivity  # noqa: F401
    import experiments.exp_opvault_recovery_auth  # noqa: F401
    import experiments.exp_opvault_trigger_key_theft  # noqa: F401
    import experiments.exp_ccv_mode_bypass  # noqa: F401
    import experiments.exp_cat_csfs_hot_key_theft  # noqa: F401
    import experiments.exp_cat_csfs_witness_manipulation  # noqa: F401
    import experiments.exp_cat_csfs_destination_lock  # noqa: F401
    import experiments.exp_cat_csfs_cold_key_recovery  # noqa: F401


def test_registry_populated():
    """At least some experiments should be registered on import."""
    _ensure_experiments_loaded()
    assert len(EXPERIMENTS) > 0, "No experiments registered"


def test_get_experiment():
    _ensure_experiments_loaded()
    spec = get_experiment("lifecycle_costs")
    assert spec.name == "lifecycle_costs"
    assert spec.run_fn is not None


def test_get_unknown_experiment():
    with pytest.raises(KeyError, match="Unknown experiment"):
        get_experiment("nonexistent_experiment_xyz")


def test_experiment_spec_supports_all(mock_adapter):
    """ExperimentSpec with required_covenants=None supports all adapters."""
    spec = ExperimentSpec(
        name="test",
        description="test",
        run_fn=lambda a: None,
        required_covenants=None,
    )
    assert spec.supports(mock_adapter)


def test_experiment_spec_supports_specific(mock_adapter):
    """ExperimentSpec with required_covenants filters by adapter name."""
    spec = ExperimentSpec(
        name="test",
        description="test",
        run_fn=lambda a: None,
        required_covenants=["ctv", "ccv"],
    )
    assert not spec.supports(mock_adapter)


def test_all_registered_experiments_have_tags():
    """Every registered experiment should have a tags list (possibly empty)."""
    _ensure_experiments_loaded()
    for name, spec in EXPERIMENTS.items():
        assert isinstance(spec.tags, list), f"{name} has no tags list"


def test_core_experiments_present():
    """Verify the expected core experiments exist."""
    _ensure_experiments_loaded()
    expected_core = [
        "lifecycle_costs",
        "fee_sensitivity",
        "fee_pinning",
        "recovery_griefing",
    ]
    for exp_name in expected_core:
        assert exp_name in EXPERIMENTS, f"Missing core experiment: {exp_name}"


def test_experiment_count():
    """Verify we have the expected 15 experiments."""
    _ensure_experiments_loaded()
    assert len(EXPERIMENTS) == 15, (
        f"Expected 15 experiments, got {len(EXPERIMENTS)}: {sorted(EXPERIMENTS.keys())}"
    )
