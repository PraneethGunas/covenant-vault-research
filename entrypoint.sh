#!/usr/bin/env bash
# entrypoint.sh — Docker entrypoint for vault-comparison framework.
#
# Usage:
#   docker run vault-comparison --help
#   docker run vault-comparison run lifecycle_costs --covenant ctv
#   docker run vault-comparison run --tag core --covenant all
#   docker run vault-comparison analyze results/<dir>
#   docker run vault-comparison bash
#
set -e

WORKSPACE=/workspace
RESULTS_HOST="${RESULTS_DIR:-/data/results}"

show_help() {
    cat <<'EOF'
════════════════════════════════════════════════════════════
  Bitcoin Covenant Vault Comparison — Docker
════════════════════════════════════════════════════════════

Commands:
  run <experiment> --covenant <ctv|ccv|opvault|cat_csfs|all>
  run --tag <tag> --covenant <ctv|ccv|opvault|cat_csfs|all>
  list                          List all experiments and tags
  analyze <results-dir>         Analyze a results directory
  bash                          Interactive shell

Experiments:
  lifecycle_costs               Deposit → trigger → withdraw cost measurement
  fee_pinning                   CTV fee pinning attack (TM1)
  fee_sensitivity               Fee-dependent security inversion analysis
  recovery_griefing             Forced-recovery griefing (TM2)
  watchtower_exhaustion         Splitting attack against watchtower budget (TM4/TM7)
  address_reuse                 Address reuse safety across covenants
  multi_input                   Batched trigger efficiency
  revault_amplification         Partial withdrawal cost amplification
  ccv_mode_bypass               CCV OP_SUCCESS mode flag exploit (TM8, CCV only)
  ccv_edge_cases                CCV developer footguns (CCV only)
  opvault_trigger_key_theft     OP_VAULT key theft + two-key compromise (OP_VAULT only)
  opvault_recovery_auth         OP_VAULT recoveryauth griefing (OP_VAULT only)

Tags:
  core                          Primary experiments (lifecycle, attacks, comparisons)
  security                      All threat model experiments
  quantitative                  Experiments with measurable outputs
  comparative                   Cross-covenant comparisons
  fee_management                Fee-related experiments
  capability_gap                Features unique to specific covenants
  ccv_only                      CCV-specific experiments
  opvault_specific              OP_VAULT-specific experiments

Covenants:
  ctv                           CTV (BIP 119) — Bitcoin Inquisition node
  ccv                           CCV (BIP 443) — Merkleize Bitcoin node
  opvault                       OP_VAULT (BIP 345) — jamesob/bitcoin node
  cat_csfs                      CAT+CSFS (BIP 347 + BIP 348) — Bitcoin Inquisition node
  all                           Run on all applicable covenants (auto-switches nodes)

Environment variables:
  RPC_USER                      RPC username (default: rpcuser)
  RPC_PASSWORD                  RPC password (default: rpcpass)
  RPC_PORT                      RPC port (default: 18443)
  RESULTS_DIR                   Host mount point for results (default: /data/results)

Examples:
  # Run all core experiments across all covenants
  docker run -v ./results:/data/results vault-comparison run --tag core --covenant all

  # Run a single experiment on one covenant
  docker run -v ./results:/data/results vault-comparison run lifecycle_costs --covenant ctv

  # Run all security experiments
  docker run -v ./results:/data/results vault-comparison run --tag security --covenant all

  # CCV-specific: test mode bypass exploit
  docker run -v ./results:/data/results vault-comparison run ccv_mode_bypass --covenant ccv

  # Analyze results from a previous run
  docker run -v ./results:/data/results vault-comparison analyze /data/results/<timestamp>

  # Interactive shell (inspect node binaries, run ad-hoc commands)
  docker run -it vault-comparison bash

Node binaries (inside container):
  /opt/bitcoin-inquisition/     bitcoind + bitcoin-cli (CTV, CAT+CSFS)
  /opt/merkleize-bitcoin-ccv/   bitcoind + bitcoin-cli (CCV)
  /opt/bitcoin-opvault/         bitcoind + bitcoin-cli (OP_VAULT)
EOF
    exit 0
}

# ── Handle special commands ──────────────────────────────────

case "${1:-}" in
    --help|-h|"")
        show_help
        ;;
    bash|sh)
        exec "$@"
        ;;
    analyze)
        shift
        cd "$WORKSPACE/vault-comparison"
        exec uv run analyze_results.py "$@"
        ;;
    list)
        cd "$WORKSPACE/vault-comparison"
        exec uv run run.py list
        ;;
    run)
        # Fall through to experiment runner below
        ;;
    *)
        # Pass through unknown commands
        exec "$@"
        ;;
esac

# ── Experiment runner ────────────────────────────────────────

cd "$WORKSPACE/vault-comparison"

echo "════════════════════════════════════════"
echo "  Vault Comparison Framework"
echo "════════════════════════════════════════"
echo ""

# Run experiments via run.py (handles node switching internally)
uv run run.py "$@"
RUN_EXIT=$?

# Copy results to mounted volume if available
if [[ -d "$RESULTS_HOST" ]]; then
    LATEST=$(ls -td results/*/ 2>/dev/null | head -1)
    if [[ -n "$LATEST" ]]; then
        cp -r "$LATEST" "$RESULTS_HOST/"
        echo ""
        echo "Results copied to $RESULTS_HOST/$(basename "$LATEST")"
    fi
fi

exit $RUN_EXIT
