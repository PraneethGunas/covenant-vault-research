#!/usr/bin/env bash
# switch-node.sh — Stop whichever Bitcoin node is running, wipe regtest, start the requested one.
#
# Usage:
#   ./switch-node.sh inquisition      # Start bitcoin-inquisition (CTV)
#   ./switch-node.sh ccv              # Start merkleize-bitcoin-ccv (inq-ccv, CCV/MATT/CTV)
#   ./switch-node.sh opvault          # Start jamesob/bitcoin 2023-02-opvault-inq (OP_VAULT+CTV)
#
# All nodes use the default datadir and ports. Regtest data is wiped on every
# switch so the chains never conflict.
#
# Optional environment overrides for portability:
#   INQUISITION_DIR, CCV_DIR, OPVAULT_DIR
#   INQUISITION_BIN, INQUISITION_CLI
#   CCV_BIN, CCV_CLI
#   OPVAULT_BIN, OPVAULT_CLI
#   BITCOIN_DATADIR

set -e

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

# ──────────────────────────────────────────────
# Argument handling
# ──────────────────────────────────────────────
usage() {
    echo "Usage: $0 <inquisition|ccv|opvault>"
    echo ""
    echo "  inquisition   Bitcoin Inquisition (CTV, APO)"
    echo "  ccv           Merkleize/bitcoin inq-ccv (CCV/MATT/CTV)"
    echo "  opvault       jamesob/bitcoin 2023-02-opvault-inq (OP_VAULT + CTV)"
    echo ""
    echo "Environment overrides:"
    echo "  INQUISITION_DIR, CCV_DIR, OPVAULT_DIR"
    echo "  INQUISITION_BIN, INQUISITION_CLI"
    echo "  CCV_BIN, CCV_CLI"
    echo "  OPVAULT_BIN, OPVAULT_CLI"
    echo "  BITCOIN_DATADIR"
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
    *)
        usage
        ;;
esac

if [[ ! -x "$TARGET_BIN" ]]; then
    echo "ERROR: Binary not found or not executable: $TARGET_BIN"
    echo "       Build the node first."
    exit 1
fi

if [[ ! -x "$TARGET_CLI" ]]; then
    echo "ERROR: bitcoin-cli not found: $TARGET_CLI"
    echo "       Build the node first."
    exit 1
fi

# ──────────────────────────────────────────────
# 1. Kill any running bitcoind process
# ──────────────────────────────────────────────
echo "→ Stopping any running bitcoind..."

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
sleep 2

# If still alive, force kill
if pgrep -x bitcoind >/dev/null 2>&1; then
    echo "  graceful stop didn't work, killing process..."
    pkill -x bitcoind 2>/dev/null || true
    sleep 2
fi

# Final check — wait up to 10s for process to die
for i in $(seq 1 10); do
    pgrep -x bitcoind >/dev/null 2>&1 || break
    echo "  waiting for process to exit..."
    sleep 1
done

if pgrep -x bitcoind >/dev/null 2>&1; then
    echo "ERROR: Could not stop bitcoind. Kill it manually:"
    echo "       kill \$(pgrep -x bitcoind)"
    exit 1
fi

echo "  done"

# ──────────────────────────────────────────────
# 2. Wipe regtest data
# ──────────────────────────────────────────────
echo "→ Wiping regtest data: $REGTEST_DIR"
rm -rf "$REGTEST_DIR"

# ──────────────────────────────────────────────
# 3. Start the requested node
# ──────────────────────────────────────────────
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

# # ──────────────────────────────────────────────
# # 4. Create and fund testwallet
# # ──────────────────────────────────────────────
# echo "→ Creating testwallet..."
# "$TARGET_CLI" -regtest createwallet "testwallet" >/dev/null 2>&1

# ADDR=$("$TARGET_CLI" -regtest -rpcwallet=testwallet getnewaddress)
# echo "→ Mining 300 blocks to $ADDR..."
# "$TARGET_CLI" -regtest generatetoaddress 300 "$ADDR" >/dev/null

# # ──────────────────────────────────────────────
# # 5. Verify
# # ──────────────────────────────────────────────
# echo ""
# echo "════════════════════════════════════════"
# echo "  $TARGET_NAME is running"
# echo "  Binary:  $TARGET_BIN"
# echo "  Chain:   regtest (fresh)"
# BLOCKS=$("$TARGET_CLI" -regtest getblockcount)
# BALANCE=$("$TARGET_CLI" -regtest -rpcwallet=testwallet getbalance)
# echo "  Blocks:  $BLOCKS"
# echo "  Balance: $BALANCE BTC (testwallet)"
# echo "════════════════════════════════════════"
