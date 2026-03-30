#!/usr/bin/env bash
# switch-node.sh — Stop whichever Bitcoin node is running, wipe regtest, start the requested one.
#
# Usage:
#   ./switch-node.sh inquisition      # Start bitcoin-inquisition (CTV)
#   ./switch-node.sh ccv              # Start merkleize-bitcoin-ccv (inq-ccv, CCV/MATT/CTV)
#   ./switch-node.sh opvault          # Start jamesob/bitcoin 2023-02-opvault-inq (OP_VAULT+CTV)
#   ./switch-node.sh elements         # Start Elements + electrs (Simplicity)
#
# All nodes use the default datadir and ports. Regtest data is wiped on every
# switch so the chains never conflict.
#
# Optional environment overrides for portability:
#   INQUISITION_DIR, CCV_DIR, OPVAULT_DIR
#   INQUISITION_BIN, INQUISITION_CLI
#   CCV_BIN, CCV_CLI
#   OPVAULT_BIN, OPVAULT_CLI
#   ELEMENTS_BIN, ELEMENTS_CLI, ELECTRS_BIN
#   BITCOIN_DATADIR, ELEMENTS_DATADIR

set -e

# macOS bash may default to 256 file descriptors — too low for bitcoind/elementsd
ulimit -n 10240 2>/dev/null || true

# ──────────────────────────────────────────────
# Node paths — override with env vars if your layout differs
# ──────────────────────────────────────────────
INQUISITION_DIR="${INQUISITION_DIR:-$HOME/bitcoin-inquisition}"
CCV_DIR="${CCV_DIR:-$HOME/merkleize-bitcoin-ccv}"
OPVAULT_DIR="${OPVAULT_DIR:-$HOME/bitcoin-opvault}"

INQUISITION_BIN="${INQUISITION_BIN:-$INQUISITION_DIR/build/bin/bitcoind}"
INQUISITION_CLI="${INQUISITION_CLI:-$INQUISITION_DIR/build/bin/bitcoin-cli}"
CCV_BIN="${CCV_BIN:-$CCV_DIR/build/bin/bitcoind}"
CCV_CLI="${CCV_CLI:-$CCV_DIR/build/bin/bitcoin-cli}"
OPVAULT_BIN="${OPVAULT_BIN:-$OPVAULT_DIR/src/bitcoind}"
OPVAULT_CLI="${OPVAULT_CLI:-$OPVAULT_DIR/src/bitcoin-cli}"

# Elements/Simplicity paths — simplex toolchain installs to ~/.simplex/bin/
SIMPLEX_BIN_DIR="${SIMPLEX_BIN_DIR:-$HOME/.simplex/bin}"
ELEMENTS_BIN="${ELEMENTS_BIN:-$SIMPLEX_BIN_DIR/elementsd}"
ELEMENTS_CLI="${ELEMENTS_CLI:-$SIMPLEX_BIN_DIR/elements-cli}"
ELECTRS_BIN="${ELECTRS_BIN:-$SIMPLEX_BIN_DIR/electrs}"

# ──────────────────────────────────────────────
# Derived paths
# ──────────────────────────────────────────────
if [[ -n "${BITCOIN_DATADIR:-}" ]]; then
    DATADIR="$BITCOIN_DATADIR"
elif [[ "$(uname)" == "Darwin" ]]; then
    DATADIR="$HOME/Library/Application Support/Bitcoin"
else
    DATADIR="$HOME/.bitcoin"
fi
REGTEST_DIR="$DATADIR/regtest"

# Elements uses a separate datadir
if [[ -n "${ELEMENTS_DATADIR:-}" ]]; then
    ELEMENTS_DIR="$ELEMENTS_DATADIR"
elif [[ "$(uname)" == "Darwin" ]]; then
    ELEMENTS_DIR="$HOME/Library/Application Support/Elements"
else
    ELEMENTS_DIR="$HOME/.elements"
fi
ELEMENTS_REGTEST_DIR="$ELEMENTS_DIR/liquidregtest"

# ──────────────────────────────────────────────
# Argument handling
# ──────────────────────────────────────────────
usage() {
    echo "Usage: $0 <inquisition|ccv|opvault|elements>"
    echo ""
    echo "  inquisition   Bitcoin Inquisition (CTV, APO)"
    echo "  ccv           Merkleize/bitcoin inq-ccv (CCV/MATT/CTV)"
    echo "  opvault       jamesob/bitcoin 2023-02-opvault-inq (OP_VAULT + CTV)"
    echo "  elements      Elements + electrs (Simplicity)"
    echo ""
    echo "Environment overrides:"
    echo "  INQUISITION_DIR, CCV_DIR, OPVAULT_DIR"
    echo "  INQUISITION_BIN, INQUISITION_CLI"
    echo "  CCV_BIN, CCV_CLI"
    echo "  OPVAULT_BIN, OPVAULT_CLI"
    echo "  ELEMENTS_BIN, ELEMENTS_CLI, ELECTRS_BIN"
    echo "  BITCOIN_DATADIR, ELEMENTS_DATADIR"
    exit 1
}

if [[ $# -ne 1 ]]; then
    usage
fi

case "$1" in
    inquisition)
        TARGET_BIN="$INQUISITION_BIN"
        TARGET_CLI="$INQUISITION_CLI"
        TARGET_NAME="bitcoin-inquisition"
        ;;
    ccv)
        TARGET_BIN="$CCV_BIN"
        TARGET_CLI="$CCV_CLI"
        TARGET_NAME="merkleize-bitcoin-ccv (inq-ccv)"
        ;;
    opvault)
        TARGET_BIN="$OPVAULT_BIN"
        TARGET_CLI="$OPVAULT_CLI"
        TARGET_NAME="bitcoin-opvault (jamesob 2023-02-opvault-inq)"
        ;;
    elements)
        # Elements uses a completely different startup path — handled below.
        # No elements-cli needed; we use curl for RPC health checks.
        TARGET_BIN="$ELEMENTS_BIN"
        TARGET_CLI="$ELEMENTS_BIN"  # placeholder — CLI check skipped below
        TARGET_NAME="Elements + electrs (Simplicity)"
        IS_ELEMENTS=true
        ;;
    *)
        usage
        ;;
esac

if [[ ! -x "$TARGET_BIN" ]]; then
    echo "ERROR: Binary not found or not executable: $TARGET_BIN"
    if [[ "${IS_ELEMENTS:-}" == "true" ]]; then
        echo "       Install simplex first: curl -L https://smplx.simplicity-lang.org | bash && simplexup"
    else
        echo "       Build the node first."
    fi
    exit 1
fi

if [[ "${IS_ELEMENTS:-}" != "true" ]]; then
    # Bitcoin nodes need their CLI binary for RPC checks
    if [[ ! -x "$TARGET_CLI" ]]; then
        echo "ERROR: CLI not found: $TARGET_CLI"
        echo "       Build the node first."
        exit 1
    fi
fi

# Elements also needs electrs for Esplora API
if [[ "${IS_ELEMENTS:-}" == "true" && ! -x "$ELECTRS_BIN" ]]; then
    echo "ERROR: electrs not found: $ELECTRS_BIN"
    echo "       Install simplex first: curl -L https://smplx.simplicity-lang.org | bash && simplexup"
    exit 1
fi

# ──────────────────────────────────────────────
# 1. Kill any running bitcoind / elementsd process and free port 18444
# ──────────────────────────────────────────────
echo "→ Stopping any running nodes..."

# Try graceful stop with all CLIs (one might auth-match the running node)
if [[ -x "$INQUISITION_CLI" ]]; then
    "$INQUISITION_CLI" -datadir="$DATADIR" -regtest stop 2>/dev/null || true
fi
if [[ -x "$CCV_CLI" ]]; then
    "$CCV_CLI" -datadir="$DATADIR" -regtest stop 2>/dev/null || true
fi
if [[ -x "$OPVAULT_CLI" ]]; then
    "$OPVAULT_CLI" -datadir="$DATADIR" -regtest stop 2>/dev/null || true
fi

# Also stop elementsd + electrs if running (simplex regtest or manual)
pkill -x elementsd 2>/dev/null || true
pkill -f electrs 2>/dev/null || true

sleep 2

# If still alive, force kill all bitcoin-like daemons
if pgrep -x "bitcoind|elementsd" >/dev/null 2>&1; then
    echo "  graceful stop didn't work, killing processes..."
    pkill -x "bitcoind|elementsd" 2>/dev/null || true
    sleep 2
fi

# Also kill anything holding port 18444 (the regtest p2p port)
if command -v lsof >/dev/null 2>&1; then
    PORT_PID=$(lsof -ti :18444 2>/dev/null || true)
    if [[ -n "$PORT_PID" ]]; then
        echo "  killing process(es) holding port 18444: $PORT_PID"
        kill $PORT_PID 2>/dev/null || true
        sleep 2
        # Force kill if still there
        PORT_PID=$(lsof -ti :18444 2>/dev/null || true)
        if [[ -n "$PORT_PID" ]]; then
            kill -9 $PORT_PID 2>/dev/null || true
            sleep 1
        fi
    fi
fi

# Final check — wait up to 10s for port to free up
for i in $(seq 1 10); do
    if ! lsof -ti :18444 >/dev/null 2>&1 && ! pgrep -x "bitcoind|elementsd" >/dev/null 2>&1; then
        break
    fi
    echo "  waiting for port 18444 to free up..."
    sleep 1
done

# Verify port is free
if lsof -ti :18444 >/dev/null 2>&1; then
    echo "ERROR: Port 18444 still in use. Process holding it:"
    lsof -i :18444 2>/dev/null
    echo ""
    echo "Kill it manually:  kill \$(lsof -ti :18444)"
    exit 1
fi

echo "  done"

# ──────────────────────────────────────────────
# 2. Wipe regtest data
# ──────────────────────────────────────────────
if [[ "${IS_ELEMENTS:-}" == "true" ]]; then
    # Wipe any stale Elements data from manual runs or previous sessions
    echo "→ Wiping Elements data: $ELEMENTS_DIR"
    rm -rf "$ELEMENTS_DIR"
else
    echo "→ Wiping regtest data: $REGTEST_DIR"
    rm -rf "$REGTEST_DIR"
fi

# ──────────────────────────────────────────────
# 3. Start the requested node
# ──────────────────────────────────────────────
if [[ "${IS_ELEMENTS:-}" == "true" ]]; then
    # ─── Elements (Simplicity) via simplex regtest ─────────
    #
    # `simplex regtest` manages elementsd + electrs with the correct
    # Simplicity consensus flags. It assigns random ports — the
    # adapter discovers them automatically from process arguments.
    echo "→ Starting simplex regtest (fresh)..."

    SIMPLEX_CMD="${SIMPLEX_BIN_DIR}/simplex"
    if command -v simplex >/dev/null 2>&1; then
        SIMPLEX_CMD="simplex"
    elif [[ ! -x "$SIMPLEX_CMD" ]]; then
        echo "ERROR: simplex not found."
        echo "       Install: curl -L https://smplx.simplicity-lang.org | bash && simplexup --install"
        exit 1
    fi

    # simplex regtest reads simplex.toml from cwd
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    SIMPLICITY_VAULT_DIR="${SIMPLICITY_VAULT_DIR:-$SCRIPT_DIR/simple-simplicity-vault}"
    if [[ ! -f "$SIMPLICITY_VAULT_DIR/simplex.toml" ]]; then
        echo "ERROR: simplex.toml not found at $SIMPLICITY_VAULT_DIR"
        echo "       Clone simple-simplicity-vault next to this script."
        exit 1
    fi

    # Ensure simplex binaries (elementsd, electrs) are on PATH
    export PATH="$SIMPLEX_BIN_DIR:$PATH"

    cd "$SIMPLICITY_VAULT_DIR"
    "$SIMPLEX_CMD" regtest &
    SIMPLEX_PID=$!
    cd "$SCRIPT_DIR"
    SIMPLEX_PID=$!

    # Wait for elementsd to appear
    echo "  waiting for elementsd..."
    for i in $(seq 1 45); do
        if pgrep -x elementsd >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    if ! pgrep -x elementsd >/dev/null 2>&1; then
        echo "ERROR: simplex regtest did not start within 45 seconds."
        exit 1
    fi
    echo "  elementsd is running"

    # Wait for electrs Esplora HTTP
    echo "  waiting for electrs..."
    ELECTRS_UP=false
    for i in $(seq 1 30); do
        ESPLORA_PORT=$(ps aux | grep "[e]lectrs" | grep -oE "\-\-http-addr\s+\S+:([0-9]+)" | grep -oE "[0-9]+$" | head -1)
        if [[ -n "$ESPLORA_PORT" ]] && curl -sf "http://127.0.0.1:$ESPLORA_PORT/blocks/tip/height" >/dev/null 2>&1; then
            ELECTRS_UP=true
            break
        fi
        sleep 1
    done

    if [[ "$ELECTRS_UP" != "true" ]]; then
        echo "WARNING: electrs not reachable within 30s. Vault experiments may fail."
    else
        RPC_PORT=$(ps aux | grep "[e]lementsd" | grep -oE "\-rpcport=([0-9]+)" | grep -oE "[0-9]+" | head -1)
        echo "  elementsd RPC:   127.0.0.1:${RPC_PORT:-?}"
        echo "  electrs Esplora: 127.0.0.1:${ESPLORA_PORT}"
    fi

else
    # ─── Bitcoin Core startup (inquisition/ccv/opvault) ───
    echo "→ Starting $TARGET_NAME..."
    "$TARGET_BIN" -datadir="$DATADIR" -regtest -daemon -blockfilterindex=1 -peerblockfilters=1

    # Wait for RPC to become available
    echo "  waiting for RPC..."
    RPC_UP=false
    for i in $(seq 1 30); do
        if "$TARGET_CLI" -datadir="$DATADIR" -regtest getblockchaininfo >/dev/null 2>&1; then
            RPC_UP=true
            break
        fi
        sleep 1
    done

    if [[ "$RPC_UP" != "true" ]]; then
        echo ""
        echo "ERROR: Node did not become reachable within 30 seconds."
        echo ""
        echo "── Last 20 lines of debug.log ──"
        tail -20 "$REGTEST_DIR/debug.log" 2>/dev/null || echo "(no debug.log found)"
        exit 1
    fi
fi

echo ""
echo "════════════════════════════════════════"
echo "  $TARGET_NAME is running"
echo "════════════════════════════════════════"
