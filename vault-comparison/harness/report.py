"""Report generation for experiment results.

Produces markdown summary tables and JSON raw data.
Results are saved to timestamped directories under results/.
"""

import json
import os
import time
from pathlib import Path
from typing import List

from harness.metrics import ComparisonResult, ExperimentResult


RESULTS_DIR = Path(__file__).parent.parent / "results"


class Reporter:
    """Writes experiment results to files.

    Creates a timestamped run directory.  When running multiple experiments,
    each experiment gets a subdirectory.  When running a single experiment,
    results go directly in the run directory.
    """

    def __init__(self, run_id: str = None):
        self.run_id = run_id or time.strftime("%Y-%m-%d_%H%M%S")
        self.run_dir = RESULTS_DIR / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._experiment_dirs: dict = {}

    def _exp_dir(self, experiment: str) -> Path:
        """Get or create the subdirectory for an experiment."""
        if experiment not in self._experiment_dirs:
            d = self.run_dir / experiment
            d.mkdir(parents=True, exist_ok=True)
            self._experiment_dirs[experiment] = d
        return self._experiment_dirs[experiment]

    def save_result(self, result: ExperimentResult) -> Path:
        """Save a single covenant's result as JSON."""
        d = self._exp_dir(result.experiment)
        path = d / f"{result.covenant}.json"
        path.write_text(result.to_json())
        return path

    def save_sweep(self, experiment: str, label: str,
                   table_md: str, csv_data: str) -> None:
        """Save sweep scaling table (markdown) and CSV."""
        d = self._exp_dir(experiment)
        (d / f"scaling_{label}.md").write_text(table_md)
        if csv_data:
            (d / f"scaling_{label}.csv").write_text(csv_data)

    def save_comparison(self, comparison: ComparisonResult) -> Path:
        """Save the full comparison (all covenants) as JSON."""
        d = self._exp_dir(comparison.experiment)
        path = d / "comparison.json"
        path.write_text(comparison.to_json())
        return path

    def write_summary(self, comparison: ComparisonResult) -> Path:
        """Generate a markdown summary table."""
        d = self._exp_dir(comparison.experiment)
        path = d / "summary.md"
        lines = []
        lines.append(f"# {comparison.experiment}")
        lines.append(f"\nRun: `{self.run_id}`\n")

        # Transaction comparison table
        all_labels = set()
        for result in comparison.results.values():
            for tx in result.transactions:
                all_labels.add(tx.label)
        labels = sorted(all_labels)
        covenants = comparison.covenants

        if labels and covenants:
            lines.append("## Transaction Sizes (vbytes)\n")
            header = "| Step | " + " | ".join(covenants) + " | Delta |"
            sep = "|------|" + "|--------|" * len(covenants) + "|-------|"
            lines.append(header)
            lines.append(sep)

            for label in labels:
                d = comparison.delta("vsize", label)
                row_vals = [str(d.get(c, "—")) for c in covenants]
                delta = d.get("pct", "—")
                lines.append(f"| {label} | " + " | ".join(row_vals) + f" | {delta} |")

            # Totals row
            totals = {c: r.total_vsize() for c, r in comparison.results.items()}
            total_vals = [str(totals.get(c, "—")) for c in covenants]
            lines.append(f"| **Total** | " + " | ".join(f"**{v}**" for v in total_vals) + " | |")

            lines.append("\n## Fees (sats)\n")
            header = "| Step | " + " | ".join(covenants) + " | Delta |"
            lines.append(header)
            lines.append(sep)

            for label in labels:
                d = comparison.delta("fee_sats", label)
                row_vals = [str(d.get(c, "—")) for c in covenants]
                delta = d.get("pct", "—")
                lines.append(f"| {label} | " + " | ".join(row_vals) + f" | {delta} |")

        # Observations
        for cov, result in comparison.results.items():
            if result.observations:
                lines.append(f"\n## Observations — {cov.upper()}\n")
                for obs in result.observations:
                    lines.append(f"- {obs}")

        # Errors
        for cov, result in comparison.results.items():
            if result.error:
                lines.append(f"\n## Error — {cov.upper()}\n")
                lines.append(f"```\n{result.error}\n```")

        lines.append("")
        path.write_text("\n".join(lines))
        return path

    def save_all(self, comparison: ComparisonResult) -> dict:
        """Save everything and return paths."""
        paths = {}
        for result in comparison.results.values():
            paths[f"{result.covenant}_json"] = str(self.save_result(result))
        paths["comparison_json"] = str(self.save_comparison(comparison))
        paths["summary_md"] = str(self.write_summary(comparison))
        return paths
