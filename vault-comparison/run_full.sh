#!/usr/bin/env bash
# run_full.sh — Run all experiments on all four vaults, then analyze.
#
# Usage:  ./run_full.sh
#
# What it does:
#   1. Runs all 16 experiments on CTV, CCV, OP_VAULT, and CAT+CSFS (auto-switches nodes)
#   2. Generates comparison JSONs for each experiment
#   3. Produces a consolidated full_analysis.md report

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════════"
echo "  Vault Comparison — Full Pipeline"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Snapshot results/ before the run so we can detect the new directory
RESULTS_DIR="$SCRIPT_DIR/results"
mkdir -p "$RESULTS_DIR"
BEFORE_DIRS=$(ls -1 "$RESULTS_DIR" 2>/dev/null | sort)

# ── Step 1: Run all experiments on all covenants ───────────────────
echo "── Step 1/3: Running all experiments on CTV, CCV, OP_VAULT, CAT+CSFS ──"
echo ""
uv run run.py run --all --covenant all
echo ""

# ── Step 2: Detect the new results directory ───────────────────────
AFTER_DIRS=$(ls -1 "$RESULTS_DIR" 2>/dev/null | sort)
NEW_DIR=$(comm -13 <(echo "$BEFORE_DIRS") <(echo "$AFTER_DIRS") | tail -1)

if [[ -z "$NEW_DIR" ]]; then
    NEW_DIR=$(ls -1t "$RESULTS_DIR" | head -1)
fi

if [[ -z "$NEW_DIR" ]]; then
    echo "ERROR: Could not detect results directory."
    exit 1
fi

RUN_DIR="$RESULTS_DIR/$NEW_DIR"
N_EXPERIMENTS=$(find "$RUN_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)
N_COMPARISONS=$(find "$RUN_DIR" -name "comparison.json" | wc -l)

echo "── Step 2/3: Generated $N_COMPARISONS comparisons across $N_EXPERIMENTS experiments"
echo ""

# ── Step 3: Generate consolidated analysis ─────────────────────────
echo "── Step 3/3: Generating full_analysis.md ──────────────────────"
echo ""
uv run analyze_results.py "$RUN_DIR"
echo ""

# ── Done ───────────────────────────────────────────────────────────
echo "════════════════════════════════════════════════════════════════"
echo "  Done.  Results: $RUN_DIR"
echo "  Report: $RUN_DIR/full_analysis.md"
echo "════════════════════════════════════════════════════════════════"
