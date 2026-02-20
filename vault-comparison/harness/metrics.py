"""Data structures for experiment measurements.

Every transaction in a vault lifecycle produces a TxMetrics record.
An ExperimentResult collects all measurements from a single run
against a single covenant type.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import json
import time


@dataclass
class TxMetrics:
    """Measurements for a single transaction."""

    label: str  # e.g. "tovault", "unvault", "withdraw", "recover"
    txid: str = ""
    vsize: int = 0
    weight: int = 0
    fee_sats: int = 0
    num_inputs: int = 0
    num_outputs: int = 0
    amount_sats: int = 0

    # Optional extras depending on the experiment
    witness_items: int = 0
    script_type: str = ""  # e.g. "bare_ctv", "p2wsh", "p2tr"
    locktime_blocks: int = 0
    csv_blocks: int = 0

    def feerate_sat_vb(self) -> float:
        return self.fee_sats / self.vsize if self.vsize else 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["feerate_sat_vb"] = round(self.feerate_sat_vb(), 2)
        return d


@dataclass
class ExperimentResult:
    """Collects all measurements from running one experiment against one covenant."""

    experiment: str  # e.g. "lifecycle_costs"
    covenant: str  # e.g. "ctv", "ccv"
    timestamp: str = ""
    transactions: List[TxMetrics] = field(default_factory=list)
    observations: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")

    def add_tx(self, tx: TxMetrics) -> None:
        self.transactions.append(tx)

    def observe(self, note: str) -> None:
        self.observations.append(note)

    def total_vsize(self) -> int:
        return sum(tx.vsize for tx in self.transactions)

    def total_fees(self) -> int:
        return sum(tx.fee_sats for tx in self.transactions)

    def tx_by_label(self, label: str) -> Optional[TxMetrics]:
        for tx in self.transactions:
            if tx.label == label:
                return tx
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment": self.experiment,
            "covenant": self.covenant,
            "timestamp": self.timestamp,
            "params": self.params,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "observations": self.observations,
            "totals": {
                "vsize": self.total_vsize(),
                "fees_sats": self.total_fees(),
                "tx_count": len(self.transactions),
            },
            "error": self.error,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


@dataclass
class ComparisonResult:
    """Side-by-side results for the same experiment across covenants."""

    experiment: str
    results: Dict[str, ExperimentResult] = field(default_factory=dict)

    def add(self, result: ExperimentResult) -> None:
        self.results[result.covenant] = result

    @property
    def covenants(self) -> List[str]:
        return sorted(self.results.keys())

    def delta(self, metric: str, label: str) -> Dict[str, Any]:
        """Compare a specific tx metric across covenants.

        Returns dict like {"ctv": 180, "ccv": 154, "diff": 26, "pct": "16.9%"}
        """
        values = {}
        for cov, result in self.results.items():
            tx = result.tx_by_label(label)
            values[cov] = getattr(tx, metric, None) if tx else None

        nums = {k: v for k, v in values.items() if v is not None}
        if len(nums) >= 2:
            keys = sorted(nums.keys())
            diff = nums[keys[0]] - nums[keys[1]]
            base = nums[keys[1]] if nums[keys[1]] else 1
            values["diff"] = diff
            values["pct"] = f"{abs(diff) / base * 100:.1f}%"
        return values

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment": self.experiment,
            "results": {k: v.to_dict() for k, v in self.results.items()},
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)
