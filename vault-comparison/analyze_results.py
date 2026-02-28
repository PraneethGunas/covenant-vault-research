"""Consolidated results analysis for vault-comparison experiments.

Reads a full run directory (results/<timestamp>/) and produces a single
markdown report synthesizing findings across all experiments and covenants.

Usage:
    uv run analyze_results.py results/2026-02-24_153709
"""

import argparse
import csv
import io
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from harness.metrics import ExperimentResult, TxMetrics


# ── Data loading ────────────────────────────────────────────────────

# Fields in serialized JSON that aren't TxMetrics constructor params
_TX_EXTRA_KEYS = {"feerate_sat_vb"}


def _load_result(json_path: Path) -> Optional[ExperimentResult]:
    """Load a single covenant result JSON into an ExperimentResult."""
    try:
        data = json.loads(json_path.read_text())
    except Exception as e:
        print(f"  WARNING: cannot read {json_path}: {e}", file=sys.stderr)
        return None

    txs = []
    for tx_dict in data.get("transactions", []):
        clean = {k: v for k, v in tx_dict.items() if k not in _TX_EXTRA_KEYS}
        try:
            txs.append(TxMetrics(**clean))
        except TypeError:
            # Unknown field — filter to known fields only
            known = {f.name for f in TxMetrics.__dataclass_fields__.values()}
            txs.append(TxMetrics(**{k: v for k, v in clean.items() if k in known}))

    return ExperimentResult(
        experiment=data.get("experiment", json_path.parent.name),
        covenant=data.get("covenant", json_path.stem),
        timestamp=data.get("timestamp", ""),
        transactions=txs,
        observations=data.get("observations", []),
        params=data.get("params", {}),
        error=data.get("error"),
    )


def load_all_experiments(
    result_dir: Path,
) -> Dict[str, Dict[str, ExperimentResult]]:
    """Load every experiment result from a run directory.

    Returns: {"lifecycle_costs": {"ctv": ExperimentResult, ...}, ...}
    """
    experiments: Dict[str, Dict[str, ExperimentResult]] = {}
    for exp_dir in sorted(result_dir.iterdir()):
        if not exp_dir.is_dir():
            continue
        exp_name = exp_dir.name
        experiments[exp_name] = {}
        for jf in sorted(exp_dir.glob("*.json")):
            if jf.name == "comparison.json":
                continue
            result = _load_result(jf)
            if result:
                experiments[exp_name][result.covenant] = result
    return experiments


# ── Observation helpers ─────────────────────────────────────────────

_NOISE_MARKERS = [
    "VALIDITY SCOPE", "METHODOLOGY", "NO MEMPOOL", "NO RELAY",
    "NO FEE MARKET", "Regtest limitation", "=== Phase",
    "NOTE: The fee amounts", "=== ",
]


def _is_noise(obs: str) -> bool:
    return any(m in obs for m in _NOISE_MARKERS)


def _find_obs(observations: List[str], *keywords: str) -> Optional[str]:
    """Find first observation containing ALL keywords (case-insensitive)."""
    for obs in observations:
        low = obs.lower()
        if all(kw.lower() in low for kw in keywords):
            return obs
    return None


def _find_all_obs(observations: List[str], *keywords: str) -> List[str]:
    """Find all observations containing ALL keywords (case-insensitive)."""
    out = []
    for obs in observations:
        low = obs.lower()
        if all(kw.lower() in low for kw in keywords):
            out.append(obs)
    return out


# ── Section 1: Run summary ─────────────────────────────────────────

def section_run_summary(
    result_dir: Path, experiments: Dict[str, Dict[str, ExperimentResult]]
) -> List[str]:
    lines = [
        "# Vault Comparison — Full Analysis",
        "",
        f"**Run:** `{result_dir.name}`  ",
        f"**Experiments:** {len(experiments)}  ",
        "",
    ]

    # Experiment × covenant checklist
    all_covs = sorted({c for exp in experiments.values() for c in exp})
    lines.append("| Experiment | " + " | ".join(c.upper() for c in all_covs) + " | Error |")
    lines.append("|---" + "|---" * len(all_covs) + "|---|")
    for exp_name, covs in sorted(experiments.items()):
        cells = []
        for c in all_covs:
            if c in covs:
                r = covs[c]
                if r.error:
                    cells.append("ERR")
                elif r.transactions:
                    cells.append(f"{len(r.transactions)} tx")
                elif r.observations:
                    cells.append(f"{len(r.observations)} obs")
                else:
                    cells.append("—")
            else:
                cells.append("—")
        has_err = any(covs[c].error for c in covs if c in covs and covs[c].error)
        lines.append(f"| {exp_name} | " + " | ".join(cells) + f" | {'yes' if has_err else ''} |")

    # Covenant coverage
    lines.append("")
    for c in all_covs:
        count = sum(1 for exp in experiments.values() if c in exp and not exp[c].error)
        lines.append(f"**{c.upper()}** ran in {count}/{len(experiments)} experiments.  ")
    lines.append("")
    return lines


# ── Section 2: Lifecycle cost comparison ────────────────────────────

def section_lifecycle_costs(experiments: Dict[str, Dict[str, ExperimentResult]]) -> List[str]:
    lines = ["---", "", "## 2. Lifecycle Cost Comparison", ""]

    lc = experiments.get("lifecycle_costs")
    if not lc:
        lines.append("_No lifecycle_costs data found._")
        return lines

    # Collect all transaction labels in order seen
    label_order = []
    seen = set()
    for cov in ["ctv", "ccv", "opvault"]:
        if cov in lc:
            for tx in lc[cov].transactions:
                if tx.label not in seen:
                    label_order.append(tx.label)
                    seen.add(tx.label)

    covs = [c for c in ["ctv", "ccv", "opvault"] if c in lc]

    lines.append("| Step | " + " | ".join(f"{c.upper()} (vB)" for c in covs) + " |")
    lines.append("|---" + "|---:" * len(covs) + "|")

    for label in label_order:
        vals = {}
        for c in covs:
            tx = lc[c].tx_by_label(label)
            vals[c] = tx.vsize if tx else None
        cells = [str(vals.get(c, "—")) for c in covs]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")

    # Totals
    totals = {c: lc[c].total_vsize() for c in covs}
    cells = [f"**{totals[c]}**" for c in covs]
    lines.append(f"| **Total** | " + " | ".join(cells) + " |")

    # Delta commentary
    if len(totals) >= 2:
        best = min(totals, key=totals.get)
        lines.append("")
        for c in covs:
            if c == best:
                lines.append(f"- **{c.upper()}** is cheapest at {totals[c]} vB")
            else:
                pct = (totals[c] - totals[best]) / totals[best] * 100
                lines.append(f"- **{c.upper()}** is {pct:.0f}% more expensive ({totals[c]} vB)")

    lines.append("")
    return lines


# ── Section 3: Security findings ────────────────────────────────────

_SECURITY_EXPERIMENTS = [
    ("fee_pinning", "Fee Pinning (TM1)", "CTV-specific: descendant-chain CPFP blocking"),
    ("recovery_griefing", "Recovery Griefing (TM2)", "Forced-recovery cost asymmetry"),
    ("watchtower_exhaustion", "Watchtower Exhaustion (TM4)", "Splitting attack on revault-capable vaults"),
    ("address_reuse", "Address Reuse (TM7)", "Second deposit to same vault address"),
    ("ccv_edge_cases", "CCV Edge Cases (TM5)", "Mode confusion, keypath bypass, sentinel values"),
    ("ccv_mode_bypass", "CCV Mode Bypass (TM8)", "Full vault theft via OP_SUCCESS on undefined CCV modes"),
    ("opvault_recovery_auth", "OP_VAULT Recovery Auth", "Authorized recovery as defense and attack surface"),
    ("opvault_trigger_key_theft", "OP_VAULT Trigger Key Theft", "Trigger key compromise and recovery race"),
]


def section_security_findings(experiments: Dict[str, Dict[str, ExperimentResult]]) -> List[str]:
    lines = ["---", "", "## 3. Security Findings", ""]

    for exp_name, title, subtitle in _SECURITY_EXPERIMENTS:
        if exp_name not in experiments:
            continue

        exp = experiments[exp_name]
        lines.append(f"### {title}")
        lines.append(f"_{subtitle}_")
        lines.append("")

        for cov in ["ctv", "ccv", "opvault"]:
            if cov not in exp:
                continue
            r = exp[cov]
            if r.error:
                lines.append(f"**{cov.upper()}:** Error — {r.error}")
                lines.append("")
                continue

            # Extract key observations (skip noise, cap at 7)
            key_obs = [o for o in r.observations if not _is_noise(o)]

            # Prefer CONCLUSION / VERDICT / KEY FINDING lines
            priority = [o for o in key_obs if any(
                kw in o.upper() for kw in ["CONCLUSION", "VERDICT", "KEY FINDING", "CONFIRMED", "SEVERITY"]
            )]
            other = [o for o in key_obs if o not in priority]

            selected = priority[:4] + other[:max(0, 5 - len(priority))]

            if not selected and not r.transactions:
                lines.append(f"**{cov.upper()}:** N/A (no data)")
                lines.append("")
                continue

            lines.append(f"**{cov.upper()}** ({len(r.transactions)} txs, {r.total_vsize()} vB total):")
            for obs in selected:
                lines.append(f"- {obs}")
            remaining = len(key_obs) - len(selected)
            if remaining > 0:
                lines.append(f"- _(+{remaining} more observations)_")
            lines.append("")

        lines.append("")
    return lines


# ── Section 4: Capability comparison ────────────────────────────────

def section_capability_comparison(
    result_dir: Path, experiments: Dict[str, Dict[str, ExperimentResult]]
) -> List[str]:
    lines = ["---", "", "## 4. Capability Comparison", ""]

    # Feature matrix
    lines.append("### Feature Matrix")
    lines.append("")
    lines.append("| Feature | CTV | CCV | OP_VAULT |")
    lines.append("|---|---|---|---|")
    lines.append("| Partial withdrawal (revault) | No | Yes | Yes |")
    lines.append("| Batched trigger | No | Yes | Yes |")
    lines.append("| Keyless recovery | No | Yes | No |")
    lines.append("| Authorized recovery | No | No | Yes |")
    lines.append("| Address reuse safe | No | Yes | Yes |")
    lines.append("| CPFP anchor output | Yes | No | No |")
    lines.append("")

    # Multi-input scaling
    mi_dir = result_dir / "multi_input"
    comparison_csv = mi_dir / "scaling_comparison.csv" if mi_dir.exists() else None
    if comparison_csv and comparison_csv.exists():
        lines.append("### Multi-Input Batching")
        lines.append("")
        csv_text = comparison_csv.read_text().strip()
        reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(reader)
        if rows:
            headers = list(rows[0].keys())
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("|" + "---|" * len(headers))
            for row in rows:
                lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
        lines.append("")
    elif "multi_input" in experiments:
        # Fall back to observation extraction
        lines.append("### Multi-Input Batching")
        lines.append("")
        for cov in ["ctv", "ccv", "opvault"]:
            if cov in experiments["multi_input"]:
                r = experiments["multi_input"][cov]
                key = _find_obs(r.observations, "ceiling") or _find_obs(r.observations, "savings") or _find_obs(r.observations, "N=")
                if key:
                    lines.append(f"- **{cov.upper()}:** {key}")
        lines.append("")

    # Revault amplification scaling
    ra_dir = result_dir / "revault_amplification"
    comparison_csv = ra_dir / "scaling_comparison.csv" if ra_dir.exists() else None
    if comparison_csv and comparison_csv.exists():
        lines.append("### Revault Amplification")
        lines.append("")
        csv_text = comparison_csv.read_text().strip()
        reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(reader)
        if rows:
            headers = list(rows[0].keys())
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("|" + "---|" * len(headers))
            for row in rows[:10]:  # Cap at 10 rows
                lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
            if len(rows) > 10:
                lines.append(f"| ... | ({len(rows) - 10} more rows) |")
        lines.append("")
    elif "revault_amplification" in experiments:
        lines.append("### Revault Amplification")
        lines.append("")
        for cov in ["ctv", "ccv", "opvault"]:
            if cov in experiments["revault_amplification"]:
                r = experiments["revault_amplification"][cov]
                completed = _find_obs(r.observations, "completed", "partial") or _find_obs(r.observations, "completed")
                if completed:
                    lines.append(f"- **{cov.upper()}:** {completed}")
        lines.append("")

    return lines


# ── Section 5: Threat model matrix ──────────────────────────────────

_THREAT_MODELS = [
    ("TM1", "Fee pinning (anchor-chain DoS)", "fee_pinning",
     {"ctv": "CRITICAL", "ccv": "N/A", "opvault": "N/A"}),
    ("TM2", "Recovery griefing (forced-recovery DoS)", "recovery_griefing",
     {"ctv": "MODERATE", "ccv": "SEVERE", "opvault": "LOW"}),
    ("TM3", "Trigger key theft (fund theft attempt)", "opvault_trigger_key_theft",
     {"ctv": "SEVERE", "ccv": "SEVERE", "opvault": "MODERATE"}),
    ("TM4", "Watchtower exhaustion (splitting attack)", "watchtower_exhaustion",
     {"ctv": "N/A", "ccv": "SEVERE", "opvault": "SEVERE"}),
    ("TM5", "Trigger key theft (xpub-derived, OP_VAULT)", "opvault_trigger_key_theft",
     {"ctv": "N/A", "ccv": "N/A", "opvault": "MODERATE"}),
    ("TM6", "Dual-key compromise (trigger + auth)", "opvault_trigger_key_theft",
     {"ctv": "CRITICAL", "ccv": "N/A", "opvault": "HIGH"}),
    ("TM7", "Address reuse (user/wallet error)", "address_reuse",
     {"ctv": "CRITICAL", "ccv": "SAFE", "opvault": "SAFE"}),
    ("TM8", "CCV mode bypass (OP_SUCCESS)", "ccv_mode_bypass",
     {"ctv": "N/A", "ccv": "CRITICAL", "opvault": "N/A"}),
]


def section_threat_matrix(experiments: Dict[str, Dict[str, ExperimentResult]]) -> List[str]:
    lines = ["---", "", "## 5. Threat Model Summary Matrix", ""]

    lines.append("| TM | Attack | CTV | CCV | OP_VAULT | Measured |")
    lines.append("|---|---|---|---|---|---|")

    for tm_id, attack_name, exp_name, severity in _THREAT_MODELS:
        # Try to extract a measured vsize from the experiment
        measured = "—"
        if exp_name in experiments:
            exp = experiments[exp_name]
            # Look across covenants for a key measurement
            for cov in ["ctv", "ccv", "opvault"]:
                if cov in exp:
                    r = exp[cov]
                    # Find a clean vsize observation (not a phase header)
                    candidates = [
                        o for o in r.observations
                        if ("vsize" in o.lower() or "vb" in o.lower())
                        and not o.startswith("===")
                        and not _is_noise(o)
                        and len(o) < 120
                    ]
                    if candidates:
                        measured = candidates[0].strip()[:80]
                        break
                    # Fall back to total vsize if transactions exist
                    if r.transactions and r.total_vsize() > 0:
                        measured = f"{r.total_vsize()} vB total"
                        break

        ctv_sev = severity["ctv"]
        ccv_sev = severity["ccv"]
        opv_sev = severity["opvault"]
        lines.append(f"| {tm_id} | {attack_name} | {ctv_sev} | {ccv_sev} | {opv_sev} | {measured} |")

    lines.append("")

    # Inverse hierarchies
    lines.append("**Inverse hierarchies** (structural tradeoffs):")
    lines.append("")
    lines.append("- Griefing resistance: OP_VAULT > CTV > CCV (recoveryauth blocks anonymous griefing)")
    lines.append("- Fund safety under key loss: CCV > CTV > OP_VAULT (keyless recovery has no key-loss failure)")
    lines.append("- On-chain efficiency: CTV > CCV > OP_VAULT (simpler scripts = smaller transactions)")
    lines.append("")
    return lines


# ── Section 6: Key numbers ──────────────────────────────────────────

def section_key_numbers(experiments: Dict[str, Dict[str, ExperimentResult]]) -> List[str]:
    lines = ["---", "", "## 6. Key Numbers at a Glance", ""]

    nums: List[str] = []

    # Lifecycle totals
    lc = experiments.get("lifecycle_costs", {})
    for cov in ["ctv", "ccv", "opvault"]:
        if cov in lc:
            nums.append(f"**{cov.upper()} lifecycle:** {lc[cov].total_vsize()} vB")

    # Recovery griefing asymmetry
    rg = experiments.get("recovery_griefing", {})
    for cov in ["ccv", "opvault"]:
        if cov in rg:
            asym = _find_obs(rg[cov].observations, "asymmetry")
            if asym:
                nums.append(f"**{cov.upper()} griefing asymmetry:** {asym}")

    # Watchtower exhaustion
    we = experiments.get("watchtower_exhaustion", {})
    for cov in ["ccv", "opvault"]:
        if cov in we:
            splits = _find_obs(we[cov].observations, "completed", "splits")
            if splits:
                nums.append(f"**{cov.upper()} watchtower:** {splits}")

    # Fee pinning
    fp = experiments.get("fee_pinning", {})
    if "ctv" in fp:
        pin = _find_obs(fp["ctv"].observations, "CONCLUSION")
        if pin:
            nums.append(f"**CTV fee pinning:** {pin}")

    # CCV mode bypass
    cmb = experiments.get("ccv_mode_bypass", {})
    if "ccv" in cmb:
        bypass = _find_obs(cmb["ccv"].observations, "bypass", "accepted")
        if bypass:
            nums.append(f"**CCV mode bypass:** {bypass}")
        else:
            bypass = _find_obs(cmb["ccv"].observations, "CONFIRMED")
            if bypass:
                nums.append(f"**CCV mode bypass:** {bypass}")

    # Address reuse
    ar = experiments.get("address_reuse", {})
    if "ctv" in ar:
        nums.append("**CTV address reuse:** single-use — second deposit creates unspendable UTXO")
    if "ccv" in ar:
        nums.append("**CCV/OPV address reuse:** safe — each deposit independently spendable")

    # Multi-input efficiency
    mi = experiments.get("multi_input", {})
    for cov in ["ccv", "opvault"]:
        if cov in mi:
            eff = _find_obs(mi[cov].observations, "savings") or _find_obs(mi[cov].observations, "marginal")
            if eff:
                nums.append(f"**{cov.upper()} batching:** {eff}")

    for n in nums:
        lines.append(f"- {n}")

    lines.append("")
    return lines


# ── Report assembly ─────────────────────────────────────────────────

def generate_full_analysis(
    result_dir: Path,
    experiments: Dict[str, Dict[str, ExperimentResult]],
) -> str:
    sections = []
    sections.extend(section_run_summary(result_dir, experiments))
    sections.extend(section_lifecycle_costs(experiments))
    sections.extend(section_security_findings(experiments))
    sections.extend(section_capability_comparison(result_dir, experiments))
    sections.extend(section_threat_matrix(experiments))
    sections.extend(section_key_numbers(experiments))
    return "\n".join(sections)


# ── CLI ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate consolidated analysis from vault-comparison results"
    )
    parser.add_argument(
        "directory",
        help="Results timestamp directory (e.g. results/2026-02-24_153709)",
    )
    args = parser.parse_args()

    result_dir = Path(args.directory).resolve()
    if not result_dir.exists():
        print(f"ERROR: Directory not found: {result_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading results from {result_dir.name}...")
    experiments = load_all_experiments(result_dir)
    if not experiments:
        print("ERROR: No experiment results found.", file=sys.stderr)
        sys.exit(1)

    total_exps = len(experiments)
    total_results = sum(len(covs) for covs in experiments.values())
    print(f"  Found {total_exps} experiments, {total_results} covenant results")

    report = generate_full_analysis(result_dir, experiments)

    output_path = result_dir / "full_analysis.md"
    output_path.write_text(report)
    print(f"\nReport written to: {output_path}")
    print(f"  ({len(report)} chars, {report.count(chr(10))} lines)")


if __name__ == "__main__":
    main()
