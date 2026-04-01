"""Cross-validation test for fee_sensitivity vsize constants.

Compares the hardcoded structural vsize constants in exp_fee_sensitivity.py
against values measured by a lifecycle_costs run.  This test requires
experiment results in vault-comparison/results/ and is skipped if no
results are available.

Usage:
    pytest tests/test_fee_sensitivity_constants.py -v

To generate the reference data, run:
    uv run run.py run lifecycle_costs --covenant all

Reviewer note (FC 2027): This test addresses the concern that hardcoded
vsize constants could silently drift if upstream adapters change their
script/witness structure.  Since vsize is structurally deterministic
(range=0 across repeated measurements), any mismatch indicates a real
adapter change, not measurement noise.
"""

import json
import pytest
from pathlib import Path

# The constants under test
from experiments.exp_fee_sensitivity import (
    CTV_TOVAULT_VSIZE, CTV_UNVAULT_VSIZE, CTV_WITHDRAW_VSIZE,
    CCV_TOVAULT_VSIZE, CCV_TRIGGER_VSIZE, CCV_WITHDRAW_VSIZE, CCV_RECOVER_VSIZE,
    OPV_TOVAULT_VSIZE, OPV_TRIGGER_VSIZE, OPV_WITHDRAW_VSIZE, OPV_RECOVER_VSIZE,
    CATCSFS_TOVAULT_VSIZE, CATCSFS_TRIGGER_VSIZE, CATCSFS_WITHDRAW_VSIZE, CATCSFS_RECOVER_VSIZE,
)

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

# Map from (covenant, tx_label) to the expected constant
EXPECTED = {
    ("ctv", "tovault"): CTV_TOVAULT_VSIZE,
    ("ctv", "unvault"): CTV_UNVAULT_VSIZE,
    ("ctv", "withdraw"): CTV_WITHDRAW_VSIZE,
    ("ccv", "tovault"): CCV_TOVAULT_VSIZE,
    ("ccv", "trigger"): CCV_TRIGGER_VSIZE,
    ("ccv", "withdraw"): CCV_WITHDRAW_VSIZE,
    ("ccv", "recover"): CCV_RECOVER_VSIZE,
    ("opvault", "tovault"): OPV_TOVAULT_VSIZE,
    ("opvault", "trigger"): OPV_TRIGGER_VSIZE,
    ("opvault", "withdraw"): OPV_WITHDRAW_VSIZE,
    ("opvault", "recover"): OPV_RECOVER_VSIZE,
    ("cat_csfs", "tovault"): CATCSFS_TOVAULT_VSIZE,
    ("cat_csfs", "trigger"): CATCSFS_TRIGGER_VSIZE,
    ("cat_csfs", "withdraw"): CATCSFS_WITHDRAW_VSIZE,
    ("cat_csfs", "recover"): CATCSFS_RECOVER_VSIZE,
}


def _find_latest_lifecycle_results():
    """Find the most recent lifecycle_costs results directory."""
    if not RESULTS_DIR.exists():
        return None
    candidates = sorted(RESULTS_DIR.glob("*/lifecycle_costs_*.json"), reverse=True)
    if not candidates:
        # Try alternate naming patterns
        candidates = sorted(RESULTS_DIR.glob("**/lifecycle_costs*.json"), reverse=True)
    return candidates if candidates else None


def _load_measured_vsizes(result_files):
    """Extract measured vsizes from lifecycle result JSON files."""
    measured = {}
    for fpath in result_files:
        try:
            data = json.loads(fpath.read_text())
            covenant = data.get("covenant", "")
            for tx in data.get("transactions", []):
                label = tx.get("label", "")
                vsize = tx.get("vsize", 0)
                if vsize > 0:
                    measured[(covenant, label)] = vsize
        except (json.JSONDecodeError, KeyError):
            continue
    return measured


@pytest.fixture
def lifecycle_results():
    files = _find_latest_lifecycle_results()
    if not files:
        pytest.skip("No lifecycle_costs results found — run lifecycle_costs first")
    return _load_measured_vsizes(files)


@pytest.mark.parametrize("key", list(EXPECTED.keys()))
def test_vsize_constant_matches_measurement(lifecycle_results, key):
    """Verify each hardcoded vsize constant matches the latest measurement."""
    covenant, label = key
    expected_vsize = EXPECTED[key]
    if key not in lifecycle_results:
        pytest.skip(f"No measurement for {covenant}/{label} in results")
    measured = lifecycle_results[key]
    assert measured == expected_vsize, (
        f"{covenant}/{label}: hardcoded={expected_vsize} vB, "
        f"measured={measured} vB. Update exp_fee_sensitivity.py constants."
    )
