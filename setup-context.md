# Node Setup Context — Bitcoin Covenant Vault Comparison

This document captures the local Bitcoin node environment used by this workspace, including branch state, RPC/datadir assumptions, helper scripts, and operational workflow.

It is intended as a reproducible setup reference for running:

- CTV-oriented experiments (`simple-ctv-vault`)
- MATT/CCV experiments (`pymatt`)
- OP_VAULT experiments (`simple-op-vault`)

## 1. Local Layout

### 1.1 Workspace

- Workspace root: `/Users/praneeth/Desktop/research experiments`
- Key local projects:
  - `simple-ctv-vault/`
  - `simple-op-vault/`
  - `pymatt/`

### 1.2 Node Source Trees

- Bitcoin Inquisition tree:
  - Path: `/Users/praneeth/bitcoin-inquisition`
  - Current branch (last verified): `29.x`
  - Current commit (last verified): `88ba899b26`
- Merkleize bitcoin tree:
  - Path: `/Users/praneeth/merkleize-bitcoin-ccv`
  - Current branch (last verified): `inq-ccv`
  - Current commit (last verified): `f2b542cf95`
- OP_VAULT bitcoin tree:
  - Path: `/Users/praneeth/bitcoin-opvault`
  - Branch: `2023-02-opvault-inq`
  - Build system: autotools (not cmake)
  - Build: `arch -x86_64 bash -c './autogen.sh && ./configure --without-miniupnpc && make -j$(nproc)'`
  - Binaries: `src/bitcoind`, `src/bitcoin-cli`

## 2. Node Binaries and Runtime

### 2.1 Binary Paths

From `switch-node.sh` defaults:

- Inquisition:
  - `bitcoind`: `$INQUISITION_BIN` (defaults to `$INQUISITION_DIR/build/bin/bitcoind`)
  - `bitcoin-cli`: `$INQUISITION_CLI` (defaults to `$INQUISITION_DIR/build/bin/bitcoin-cli`)
- Merkleize (CCV/MATT):
  - `bitcoind`: `$CCV_BIN` (defaults to `$CCV_DIR/build/bin/bitcoind`)
  - `bitcoin-cli`: `$CCV_CLI` (defaults to `$CCV_DIR/build/bin/bitcoin-cli`)

### 2.2 Datadir and Network

- OS-specific datadir (macOS):  
  `/Users/praneeth/Library/Application Support/Bitcoin`
- Regtest dir:  
  `/Users/praneeth/Library/Application Support/Bitcoin/regtest`
- Default regtest RPC port used in this setup: `18443`

Important: both node variants share this datadir/port model, and switching wipes the regtest directory (see script behavior below).

## 3. `switch-node.sh` Behavior

Script path:

- `switch-node.sh` (workspace root)

Usage:

```bash
./switch-node.sh inquisition
./switch-node.sh ccv
./switch-node.sh opvault
```

Behavior summary:

1. Attempts to stop any running `bitcoind` (using both CLIs, then `pkill` fallback).
2. Deletes regtest data:
   - `rm -rf "$REGTEST_DIR"`
3. Starts selected node with:
   - `-datadir="$DATADIR" -regtest -daemon`
4. Polls RPC readiness via `getblockchaininfo`.

Environment overrides supported by `switch-node.sh`:

- `INQUISITION_DIR`, `CCV_DIR`
- `INQUISITION_BIN`, `INQUISITION_CLI`
- `CCV_BIN`, `CCV_CLI`
- `BITCOIN_DATADIR`

Current `ccv` target label:

- `"merkleize-bitcoin-ccv (inq-ccv)"`

## 4. Node Configuration (Reference Values)

Configured values:

- `regtest=1`
- `server=1`
- `txindex=1`
- `fallbackfee=0.00001`
- `minrelaytxfee=0`
- `blockmintxfee=0`
- `acceptnonstdtxn=1`
- `[regtest] rpcuser=rpcuser`
- `[regtest] rpcpassword=rpcpass`
- `[regtest] rpcport=18443`
- `[regtest] rpcbind=0.0.0.0`
- `[regtest] rpcallowip=0.0.0.0/0`

## 5. `pymatt` RPC Wiring and Helper Scripts

### 5.1 `.env`

File:

- `pymatt/.env`

Values:

- `RPC_HOST = "localhost"`
- `RPC_USER = "rpcuser"`
- `RPC_PASSWORD = "rpcpass"`
- `RPC_PORT = "18443"`

### 5.2 Init/Fund Scripts

Files:

- `pymatt/examples/init.sh`
- `pymatt/examples/fund.sh`

Both scripts use `bitcoin-cli` from `PATH` by default and can be configured with:

- `BITCOIN_CLI_BIN=/absolute/path/to/bitcoin-cli`
- optional RPC overrides: `RPC_HOST`, `RPC_PORT`, `RPC_USER`, `RPC_PASSWORD`
- optional wallet override: `WALLET_NAME`

Operational meaning:

- These helpers remain regtest/testwallet-oriented by default.
- They no longer require machine-specific absolute paths.

## 6. Current Verified Runtime Status

Last verified with current build:

- `switch-node.sh ccv` starts the Merkleize node from `inq-ccv` binaries.
- `pymatt/examples/init.sh` works (creates/loads `testwallet`, mines 300 blocks).
- `pymatt/examples/fund.sh` works.
- `getdeploymentinfo` on current Merkleize node reports both:
  - `checktemplateverify` active
  - `checkcontractverify` active

## 7. Standard Operating Runbook

### 7.1 Run MATT/CCV (and CTV-enabled) `pymatt` Vault Flows

```bash
cd "/Users/praneeth/Desktop/research experiments"
./switch-node.sh ccv
bash pymatt/examples/init.sh
cd pymatt
uv sync --extra examples
uv run --no-sync python examples/vault/vault.py -m
```

### 7.2 Run Inquisition-Side Experiments

```bash
cd "/Users/praneeth/Desktop/research experiments"
./switch-node.sh inquisition
```

Then run the relevant project commands (`simple-ctv-vault` or `simple-op-vault`) against that node.

## 8. Notes and Constraints

- Switching nodes wipes regtest state every time.
- Wallet/blockchain state is not preserved across `switch-node.sh` runs.
- If any workflow depends on persistent chain state, do not use the switch script between steps.
- If paths differ from defaults, set the supported `switch-node.sh` and helper-script env vars.
