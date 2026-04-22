#!/usr/bin/env python3
"""
update_paper_from_results.py — Populate LaTeX measurement macros from
watchtower_exhaustion results.

The FC 2027 paper (conference/FC-2027/paper/) uses placeholder macros
(\\overheadCCV, \\perinputCCV, \\overheadOPV, \\perinputOPV) for
measured batched-recovery constants, and \\measured{...} tokens for
derived quantities (batched r^\\dagger, fee-range multipliers). This
script reads the latest results JSONs, extracts the Phase-6a linear
regression, computes the derived values, and rewrites the macros.

Usage:
    python3 scripts/update_paper_from_results.py \\
        --results-dir vault-comparison/results \\
        --paper-tex   conference/FC-2027/paper/fc27-paper.tex

If --results-dir is omitted it defaults to ``vault-comparison/results``.
The script picks the most recent timestamped subdirectory that contains
``watchtower_exhaustion/<covenant>.json`` for both ``ccv`` and
``opvault``.

Exits non-zero on missing data. Prints a summary of every substitution
made.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ── Measurement model ──────────────────────────────────────────────────

@dataclass
class BatchedRecoveryFit:
    """Linear-regression fit of vsize(N) = overhead + per_input × N."""
    overhead: int
    per_input: int
    points: dict[int, int]  # N -> measured vsize
    source_json: Path


# ── Design constants (must match paper §3.3.4) ────────────────────────

# Unbatched per-UTXO recovery vsize, by design.
UNBATCHED_RECOVER_VB = {"ccv": 122, "opvault": 246}

# Attacker's trigger_and_revault size → implies splits per block
# (S = 4,000,000 / weight_of_trigger_revault).
TRIGGER_REVAULT_WU = {"ccv": 648, "opvault": 1168}
SPLITS_PER_BLOCK = {
    k: 4_000_000 // v for k, v in TRIGGER_REVAULT_WU.items()
}

# Default vault value used in paper §4.7 derivations.
DEFAULT_V_SATS = 50_000_000  # 0.5 BTC


# ── JSON parsing ───────────────────────────────────────────────────────

LINEAR_FIT_RE = re.compile(
    r"Linear fit:\s*vsize\(N\)\s*=\s*([0-9.]+)\s*\+\s*([0-9.]+)\s*×\s*N"
)


def find_latest_result(results_root: Path, covenant: str) -> Path:
    """Return the newest watchtower_exhaustion/<covenant>.json.

    Scans ``<results_root>/<timestamp>/watchtower_exhaustion/`` in reverse
    chronological order. Returns the first JSON that parses and contains
    at least one recover_batched_n* transaction record.
    """
    timestamped_dirs = sorted(
        (p for p in results_root.iterdir() if p.is_dir()),
        reverse=True,
    )
    for d in timestamped_dirs:
        candidate = d / "watchtower_exhaustion" / f"{covenant}.json"
        if not candidate.is_file():
            continue
        try:
            data = json.loads(candidate.read_text())
        except json.JSONDecodeError:
            continue
        tx_labels = {t.get("label", "") for t in data.get("transactions", [])}
        if any(lbl.startswith("recover_batched_n") for lbl in tx_labels):
            return candidate
    raise FileNotFoundError(
        f"No watchtower_exhaustion result with batched-recovery data found "
        f"for {covenant} under {results_root}"
    )


def parse_fit(json_path: Path) -> BatchedRecoveryFit:
    """Extract the Phase-6a linear regression from the result JSON.

    The experiment emits a line of the form
    ``  Linear fit: vsize(N) = 54.0 + 68.00 × N`` in its observations,
    and records each measured point as a ``recover_batched_n<N>``
    transaction with its vsize.
    """
    data = json.loads(json_path.read_text())

    overhead = per_input = None
    for obs in data.get("observations", []):
        m = LINEAR_FIT_RE.search(obs)
        if m:
            overhead = round(float(m.group(1)))
            per_input = round(float(m.group(2)))
            break
    if overhead is None or per_input is None:
        raise ValueError(
            f"No linear-fit observation found in {json_path}. The experiment "
            f"may have skipped Phase 6a (needs supports_batched_recovery())."
        )

    points: dict[int, int] = {}
    for tx in data.get("transactions", []):
        label = tx.get("label", "")
        if label.startswith("recover_batched_n"):
            try:
                n = int(label.rsplit("_n", 1)[1])
                points[n] = int(tx.get("vsize", 0))
            except (ValueError, IndexError):
                continue

    return BatchedRecoveryFit(
        overhead=overhead,
        per_input=per_input,
        points=points,
        source_json=json_path,
    )


# ── Derived values ─────────────────────────────────────────────────────

def compute_r_dagger(beta: int, splits_per_block: int,
                     vault_sats: int = DEFAULT_V_SATS) -> float:
    """Single-block-feasibility threshold fee rate in sat/vB.

    r^\\dagger = V / (vsize_rec × S). For batched, vsize_rec is the
    amortized per-input cost β; for unbatched, the raw recovery vsize.
    """
    return vault_sats / (beta * splits_per_block)


def compute_derived(fits: dict[str, BatchedRecoveryFit]) -> dict[str, float]:
    """Compute all derived paper values from the fits."""
    out: dict[str, float] = {}
    for covenant, fit in fits.items():
        S = SPLITS_PER_BLOCK[covenant]
        vsize_unbatched = UNBATCHED_RECOVER_VB[covenant]
        r_dagger_unbatched = compute_r_dagger(vsize_unbatched, S)
        r_dagger_batched = compute_r_dagger(fit.per_input, S)
        out[f"r_dagger_unbatched_{covenant}"] = r_dagger_unbatched
        out[f"r_dagger_batched_{covenant}"] = r_dagger_batched
        out[f"fee_range_factor_{covenant}"] = r_dagger_batched / r_dagger_unbatched
    return out


# ── LaTeX substitution ─────────────────────────────────────────────────

# Pattern: \newcommand{\overheadCCV}{\measured{overhead-CCV}}
# Target:  \newcommand{\overheadCCV}{54}
# We allow one level of brace nesting inside the replacement value so
# that ``\measured{key}`` placeholders match correctly. A literal numeric
# value (no nested braces) also matches.
NEWCMD_RE = re.compile(
    r"(\\newcommand\{\\(overhead|perinput)(CCV|OPV)\}\{)"
    r"((?:[^{}]|\{[^{}]*\})*)"
    r"(\})"
)

# Inline \measured{foo-bar} replacements. We map known keys to computed
# values; unknown keys are left as-is so reviewers can see them in the
# rendered PDF and finish them manually.
MEASURED_RE = re.compile(r"\\measured\{([a-zA-Z0-9-]+)\}")


def substitute_constants(tex: str, fits: dict[str, BatchedRecoveryFit]) -> tuple[str, list[str]]:
    """Replace \\newcommand macros for the four (alpha, beta) constants."""
    changes: list[str] = []

    def repl(match: re.Match) -> str:
        prefix = match.group(1)       # \newcommand{\overheadCCV}{
        kind = match.group(2)         # overhead | perinput
        covenant_tag = match.group(3) # CCV | OPV
        old_value = match.group(4)
        closing = match.group(5)

        covenant = "ccv" if covenant_tag == "CCV" else "opvault"
        fit = fits.get(covenant)
        if fit is None:
            return match.group(0)  # leave unchanged

        new_value = str(fit.overhead if kind == "overhead" else fit.per_input)
        if old_value != new_value:
            changes.append(
                f"  \\{kind}{covenant_tag}: {old_value!r} → {new_value}"
            )
        return f"{prefix}{new_value}{closing}"

    new_tex = NEWCMD_RE.sub(repl, tex)
    return new_tex, changes


def substitute_measured(tex: str, derived: dict[str, float]) -> tuple[str, list[str]]:
    """Replace \\measured{key} tokens with computed derived values.

    The key namespace used in the paper:
      r-dagger-CCV-batched       → batched r^\\dagger for CCV (sat/vB, 1 dp)
      r-dagger-OPV-batched       → batched r^\\dagger for OP_VAULT
      fee-range-multiplier       → ratio, reported with 1 decimal place
                                   and a "×" suffix
    Unknown keys are preserved; we only replace what we know.
    """
    changes: list[str] = []

    key_map = {
        "r-dagger-CCV-batched":
            f"{derived['r_dagger_batched_ccv']:.0f}",
        "r-dagger-OPV-batched":
            f"{derived['r_dagger_batched_opvault']:.0f}",
        # Per-design fee-range multipliers. Values are pure numbers; the
        # surrounding LaTeX supplies the $\times$ symbol so no nested
        # math-mode markers are introduced.
        "fee-range-factor-CCV":
            f"{derived['fee_range_factor_ccv']:.1f}",
        "fee-range-factor-OPV":
            f"{derived['fee_range_factor_opvault']:.1f}",
    }

    def repl(match: re.Match) -> str:
        key = match.group(1)
        replacement = key_map.get(key)
        if replacement is None:
            return match.group(0)
        changes.append(f"  \\measured{{{key}}} → {replacement}")
        return replacement

    new_tex = MEASURED_RE.sub(repl, tex)
    return new_tex, changes


# ── Entry point ────────────────────────────────────────────────────────

def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Populate paper LaTeX macros from watchtower_exhaustion results."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=project_root / "vault-comparison" / "results",
        help="Root directory containing timestamped result folders.",
    )
    parser.add_argument(
        "--paper-tex",
        type=Path,
        default=project_root / "conference" / "FC-2027" / "paper" / "fc27-paper.tex",
        help="Main LaTeX file containing the \\newcommand macros to update.",
    )
    parser.add_argument(
        "--sections-dir",
        type=Path,
        default=project_root / "conference" / "FC-2027" / "paper" / "sections",
        help="Sections directory where \\measured{...} tokens are replaced.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change but don't write files.",
    )
    args = parser.parse_args()

    # 1. Locate the latest result file per covenant.
    fits: dict[str, BatchedRecoveryFit] = {}
    for covenant in ("ccv", "opvault"):
        try:
            result_path = find_latest_result(args.results_dir, covenant)
        except FileNotFoundError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        try:
            fits[covenant] = parse_fit(result_path)
        except ValueError as e:
            print(f"ERROR parsing {result_path}: {e}", file=sys.stderr)
            return 1
        print(f"[{covenant}] {result_path.relative_to(project_root)}")
        print(f"    α = {fits[covenant].overhead} vB, "
              f"β = {fits[covenant].per_input} vB, "
              f"{len(fits[covenant].points)} data points")

    # 2. Compute derived values (batched r^\dagger, fee-range multipliers).
    derived = compute_derived(fits)
    print("\nDerived values:")
    for k, v in derived.items():
        print(f"    {k} = {v:.2f}")

    # 3. Rewrite the main .tex to substitute the \newcommand macros.
    paper_tex = args.paper_tex.read_text()
    new_paper, const_changes = substitute_constants(paper_tex, fits)
    if const_changes:
        print(f"\n{args.paper_tex.name}:")
        for change in const_changes:
            print(change)

    if not args.dry_run:
        args.paper_tex.write_text(new_paper)

    # 4. Rewrite each sections/*.tex to substitute \measured{...} tokens.
    total_measured_changes: list[str] = []
    for section_file in sorted(args.sections_dir.glob("*.tex")):
        section_tex = section_file.read_text()
        new_section, section_changes = substitute_measured(section_tex, derived)
        if section_changes:
            print(f"\n{section_file.relative_to(project_root)}:")
            for change in section_changes:
                print(change)
            total_measured_changes.extend(section_changes)
        if not args.dry_run and section_changes:
            section_file.write_text(new_section)

    # 5. Summary.
    print()
    if args.dry_run:
        print("DRY RUN — no files written.")
    else:
        print(
            f"Updated {len(const_changes)} \\newcommand macros and "
            f"{len(total_measured_changes)} \\measured{{...}} tokens."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
