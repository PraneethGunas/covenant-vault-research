# Empirical Comparison of Bitcoin Covenant Vault Designs

Comparative analysis framework for CTV (BIP-119), CCV (BIP-443), and OP_VAULT (BIP-345) vault implementations on Bitcoin regtest.

## Overview

This framework runs side-by-side experiments against covenant vault implementations, measuring transaction costs, security properties, and capability differences.

## Repository Layout

```
research experiments/
├── README.md                 # This file
├── REFERENCES.md             # Prior art and per-experiment citations
├── context.md                # Architecture, threat models, experiment catalog
├── setup-context.md          # Node environment and build instructions
├── switch-node.sh            # Node manager (Inquisition / CCV / OP_VAULT)
├── vault-comparison/         # Framework source
│   ├── run.py                # CLI runner
│   ├── harness/              # Shared infra (RPC, metrics, reporting)
│   ├── adapters/             # Vault drivers (CTV, CCV, OP_VAULT)
│   ├── experiments/          # Experiment modules
│   └── results/              # Timestamped output (gitignored)
├── simple-ctv-vault/         # CTV vault (upstream clone)
├── pymatt/                   # CCV vault (upstream clone)
└── simple-op-vault/          # OP_VAULT demo (upstream clone)
```

## Setup

Requires vault implementations as siblings:

```bash
# Clone upstream repos
git clone https://github.com/AlejandroAkbal/simple-ctv-vault.git
git clone https://github.com/Merkleize/pymatt.git
git clone https://github.com/jamesob/opvault-demo.git simple-op-vault
```

Install dependencies:

```bash
cd vault-comparison
uv pip install -e ".[ctv,ccv]"
```

## Node Requirements

Each adapter requires a specific Bitcoin node variant:

- **CTV:** Bitcoin Inquisition (`./switch-node.sh inquisition`)
- **CCV:** Merkleize Bitcoin (`./switch-node.sh ccv`)
- **OP_VAULT:** jamesob/bitcoin opvault branch (`./switch-node.sh opvault`)

See `setup-context.md` for build instructions.

## Usage

The `run` command automatically switches Bitcoin nodes and initializes regtest.

```bash
cd vault-comparison

# List available experiments
uv run run.py list

# Run an experiment (auto-switches to correct node)
uv run run.py run lifecycle_costs --covenant ctv
uv run run.py run lifecycle_costs --covenant ccv

# Run on both covenants
uv run run.py run lifecycle_costs --covenant both

# Run all core experiments on both
uv run run.py run --tag core --covenant both

# Skip node switching (node already running)
uv run run.py run lifecycle_costs --covenant ctv --no-switch

# View saved results
uv run run.py compare results/<timestamp_directory>
```

## Experiments

### Category Taxonomy

Not all experiments are head-to-head comparisons. They fall into three scope categories:

- **Comparative** — same test, both covenants, finding comes from the difference
- **Capability gap** — CCV feature that CTV cannot do (CTV reports "unsupported")
- **CCV-only** — CCV-specific semantics with no CTV analog

| Name | Category | Description |
|------|----------|-------------|
| lifecycle_costs | Comparative | Full vault lifecycle transaction sizes and fees |
| address_reuse | Comparative | Second-deposit safety (stuck funds vs safe re-funding) |
| fee_pinning | Comparative | Fee mechanism and descendant-chain pinning surface |
| recovery_griefing | Comparative | Forced-recovery griefing: asymmetric cost analysis |
| revault_amplification | Capability gap | Partial withdrawal chaining and cost accumulation |
| multi_input | Capability gap | Batched trigger efficiency and cross-input accounting |
| ccv_edge_cases | CCV-only | Mode confusion, keypath bypass, sentinel values |
| watchtower_exhaustion | CCV-only | Revault-splitting watchtower fee exhaustion |

### Running by Category

```bash
cd vault-comparison

# All comparative experiments on both covenants (auto-switches nodes)
uv run run.py run --tag comparative --covenant both

# Capability-gap experiments (CCV features CTV lacks)
uv run run.py run --tag capability_gap --covenant ccv

# CCV-only edge cases
uv run run.py run --tag ccv_only --covenant ccv

# Only experiments that collect cost metrics
uv run run.py run --tag quantitative --covenant both

# All security-focused experiments
uv run run.py run --tag security --covenant both

# Run everything
uv run run.py run --all --covenant both
```

### Standalone Fee Analysis

The fee sensitivity analysis runs analytically (no Bitcoin node required):

```bash
cd vault-comparison
python3 run_fee_analysis.py
```

## Output Structure

Results are saved to timestamped directories under `vault-comparison/results/`:

```
results/2026-02-19_143000/
├── lifecycle_costs/
│   ├── ctv.json          # Raw ExperimentResult
│   ├── ccv.json
│   ├── comparison.json   # Side-by-side data
│   └── summary.md        # Markdown comparison table
├── multi_input/
│   ├── scaling_ctv.csv   # For plotting
│   ├── scaling_ccv.csv
│   └── scaling_comparison.md
└── ...
```

## Further Reading

- `context.md` — Architecture, adapter pattern, threat model methodology, full experiment catalog with threat models, regtest limitations
- `REFERENCES.md` — Prior art survey with per-experiment attribution to academic work
- `setup-context.md` — Node build instructions and environment setup
