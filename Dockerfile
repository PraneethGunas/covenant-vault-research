# ============================================================
# Bitcoin Covenant Vault Comparison — Multi-stage Docker Build
# ============================================================
# All 5 covenants: CTV, CCV, OP_VAULT, CAT+CSFS, Simplicity.
# linux/amd64 only (simplex pre-built binaries are platform-specific).
#
# Default: downloads pre-built binaries (~3 min build).
#   docker build --platform linux/amd64 -t vault-comparison .
#
# From source: compiles CCV and OP_VAULT nodes + vault-cli (~45 min).
#   docker build --platform linux/amd64 --build-arg BUILD_FROM_SOURCE=1 -t vault-comparison .
#
# ============================================================

ARG BUILD_FROM_SOURCE=0

# ── Stage 1: Base ────────────────────────────────────────────
FROM ubuntu:24.04 AS base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    # C++ build toolchain (needed for from-source builds and Python native extensions)
    build-essential cmake autoconf automake libtool pkg-config \
    # Bitcoin node dependencies
    libssl-dev libboost-all-dev libevent-dev libsqlite3-dev libzstd-dev \
    # Python
    python3 python3-dev python3-pip python3-venv python3-setuptools \
    # Utilities
    git curl jq \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Binary release base URL
ARG RELEASE_URL=https://github.com/PraneethGunas/vault-comparison/releases/download/docker-binaries

# ── Stage 2: Bitcoin Inquisition (CTV) — always pre-built ───
FROM base AS build-inquisition

RUN mkdir -p /opt/bitcoin-inquisition \
    && curl -L https://github.com/bitcoin-inquisition/bitcoin/releases/download/v29.2-inq/bitcoin-29.2-inq-x86_64-linux-gnu.tar.gz \
       | tar xz --strip-components=2 -C /opt/bitcoin-inquisition \
         bitcoin-29.2-inq/bin/bitcoind bitcoin-29.2-inq/bin/bitcoin-cli

# ── Stage 3a: CCV — pre-built binary ─────────────────────────
FROM base AS ccv-prebuilt

ARG RELEASE_URL
RUN mkdir -p /opt/merkleize-bitcoin-ccv \
    && curl -L ${RELEASE_URL}/ccv-linux-x86_64.tar.gz \
       | tar xz -C /opt/merkleize-bitcoin-ccv

# ── Stage 3b: CCV — build from source ────────────────────────
FROM base AS ccv-source

RUN git clone --depth 1 --single-branch -b inq-ccv \
    https://github.com/Merkleize/bitcoin.git /src/merkleize-bitcoin-ccv

WORKDIR /src/merkleize-bitcoin-ccv
RUN cmake -B build -DBUILD_TESTING=OFF -DBUILD_BENCH=OFF \
    && cmake --build build -j4

RUN mkdir -p /opt/merkleize-bitcoin-ccv \
    && cp build/bin/bitcoind build/bin/bitcoin-cli /opt/merkleize-bitcoin-ccv/

# ── Stage 3: CCV selector ────────────────────────────────────
FROM ccv-prebuilt AS ccv-0
FROM ccv-source AS ccv-1
FROM ccv-${BUILD_FROM_SOURCE} AS build-ccv

# ── Stage 4a: OP_VAULT — pre-built binary ────────────────────
FROM base AS opvault-prebuilt

ARG RELEASE_URL
RUN mkdir -p /opt/bitcoin-opvault \
    && curl -L ${RELEASE_URL}/opvault-linux-x86_64.tar.gz \
       | tar xz -C /opt/bitcoin-opvault

# ── Stage 4b: OP_VAULT — build from source ───────────────────
FROM base AS opvault-source

RUN git clone --depth 1 --single-branch -b 2023-02-opvault-inq \
    https://github.com/jamesob/bitcoin.git /src/bitcoin-opvault

WORKDIR /src/bitcoin-opvault
RUN ./autogen.sh \
    && ./configure --without-miniupnpc --without-gui --disable-tests --disable-bench \
    && make -j4

RUN mkdir -p /opt/bitcoin-opvault \
    && cp src/bitcoind src/bitcoin-cli /opt/bitcoin-opvault/

# ── Stage 4: OP_VAULT selector ───────────────────────────────
FROM opvault-prebuilt AS opvault-0
FROM opvault-source AS opvault-1
FROM opvault-${BUILD_FROM_SOURCE} AS build-opvault

# ── Stage 5a: Simplicity — pre-built vault-cli ───────────────
FROM base AS simplicity-prebuilt

# Simplex toolchain (elementsd + electrs + simplex CLI)
RUN curl -L https://smplx.simplicity-lang.org | bash \
    && /root/.simplex/bin/simplexup --install 0.0.2

ARG RELEASE_URL
RUN mkdir -p /opt/simplex-bin /opt/simplicity-vault \
    && cp /root/.simplex/bin/elementsd /opt/simplex-bin/ \
    && cp /root/.simplex/bin/electrs /opt/simplex-bin/ \
    && cp /root/.simplex/bin/simplex /opt/simplex-bin/ \
    && cp /root/.simplex/bin/simplexup /opt/simplex-bin/ \
    && cp /root/.simplex/bin/elements-cli /opt/simplex-bin/ 2>/dev/null || true \
    && curl -L ${RELEASE_URL}/vault-cli-linux-x86_64.tar.gz \
       | tar xz -C /opt/simplicity-vault

# ── Stage 5b: Simplicity — build vault-cli from source ───────
FROM base AS simplicity-source

# Simplex toolchain
RUN curl -L https://smplx.simplicity-lang.org | bash \
    && /root/.simplex/bin/simplexup --install 0.0.2

# Rust nightly (vault-cli build only)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain nightly
ENV PATH="/root/.cargo/bin:/root/.simplex/bin:${PATH}"

# Clone and build vault-cli
RUN git clone --depth 1 https://github.com/PraneethGunas/simple-simplicity-vault.git /src/simple-simplicity-vault
WORKDIR /src/simple-simplicity-vault
RUN cargo build --release

RUN mkdir -p /opt/simplex-bin /opt/simplicity-vault \
    && cp /root/.simplex/bin/elementsd /opt/simplex-bin/ \
    && cp /root/.simplex/bin/electrs /opt/simplex-bin/ \
    && cp /root/.simplex/bin/simplex /opt/simplex-bin/ \
    && cp /root/.simplex/bin/simplexup /opt/simplex-bin/ \
    && cp /root/.simplex/bin/elements-cli /opt/simplex-bin/ 2>/dev/null || true \
    && cp target/release/vault-cli /opt/simplicity-vault/

# ── Stage 5: Simplicity selector ─────────────────────────────
FROM simplicity-prebuilt AS simplicity-0
FROM simplicity-source AS simplicity-1
FROM simplicity-${BUILD_FROM_SOURCE} AS build-simplicity

# ── Stage 6: Final ──────────────────────────────────────────
FROM base AS final

# Copy node binaries from build stages
COPY --from=build-inquisition /opt/bitcoin-inquisition /opt/bitcoin-inquisition
COPY --from=build-ccv /opt/merkleize-bitcoin-ccv /opt/merkleize-bitcoin-ccv
COPY --from=build-opvault /opt/bitcoin-opvault /opt/bitcoin-opvault
COPY --from=build-simplicity /opt/simplex-bin /opt/simplex-bin
COPY --from=build-simplicity /opt/simplicity-vault /opt/simplicity-vault

# Create workspace
WORKDIR /workspace

# Clone upstream vault implementations
RUN git clone --depth 1 https://github.com/jamesob/simple-ctv-vault.git \
    && git clone --depth 1 https://github.com/Merkleize/pymatt.git \
    && git clone --depth 1 https://github.com/jamesob/opvault-demo.git simple-op-vault \
    && git clone --depth 1 https://github.com/PraneethGunas/cat-csfs-vault.git simple-cat-csfs-vault \
    && git clone --depth 1 https://github.com/PraneethGunas/simple-simplicity-vault.git

# Place pre-built vault-cli where the adapter expects it
RUN mkdir -p simple-simplicity-vault/target/release \
    && cp /opt/simplicity-vault/vault-cli simple-simplicity-vault/target/release/vault-cli

# Copy framework source
COPY vault-comparison/ vault-comparison/
COPY switch-node.sh .
COPY entrypoint.sh .
RUN chmod +x switch-node.sh entrypoint.sh

# Enable RIPEMD-160 (disabled by default in OpenSSL 3.x, needed by buidl/python-bitcoinlib)
RUN sed -i '1s/^/openssl_conf = openssl_init\n/' /etc/ssl/openssl.cnf \
    && printf '\n[openssl_init]\nproviders = provider_sect\n[provider_sect]\ndefault = default_sect\nlegacy = legacy_sect\n[default_sect]\nactivate = 1\n[legacy_sect]\nactivate = 1\n' >> /etc/ssl/openssl.cnf

# Install Python dependencies via uv (cached at build time so runtime is fast)
# pymatt's lockfile pins numpy==1.24.4 which needs distutils (removed in Python 3.12).
# Delete the lockfile and re-resolve to get a Python 3.12-compatible numpy.
RUN cd vault-comparison && uv sync --extra all \
    && cd ../pymatt && rm -f uv.lock && uv sync --extra examples \
    && pip3 install --no-cache-dir --break-system-packages -r ../simple-op-vault/requirements.txt

# Write pymatt .env for RPC
RUN printf 'RPC_HOST=localhost\nRPC_USER=rpcuser\nRPC_PASSWORD=rpcpass\nRPC_PORT=18443\n' > pymatt/.env

# Write bitcoin.conf for regtest
RUN mkdir -p /root/.bitcoin && printf '\
    regtest=1\n\
    server=1\n\
    txindex=1\n\
    fallbackfee=0.00001\n\
    minrelaytxfee=0\n\
    blockmintxfee=0\n\
    acceptnonstdtxn=1\n\
    [regtest]\n\
    rpcuser=rpcuser\n\
    rpcpassword=rpcpass\n\
    rpcport=18443\n\
    rpcbind=0.0.0.0\n\
    rpcallowip=0.0.0.0/0\n' > /root/.bitcoin/bitcoin.conf

# Set node path env vars for switch-node.sh
ENV INQUISITION_BIN=/opt/bitcoin-inquisition/bitcoind \
    INQUISITION_CLI=/opt/bitcoin-inquisition/bitcoin-cli \
    CCV_BIN=/opt/merkleize-bitcoin-ccv/bitcoind \
    CCV_CLI=/opt/merkleize-bitcoin-ccv/bitcoin-cli \
    OPVAULT_BIN=/opt/bitcoin-opvault/bitcoind \
    OPVAULT_CLI=/opt/bitcoin-opvault/bitcoin-cli \
    BITCOIN_DATADIR=/root/.bitcoin \
    SIMPLEX_BIN_DIR=/opt/simplex-bin \
    ELEMENTS_BIN=/opt/simplex-bin/elementsd \
    ELEMENTS_CLI=/opt/simplex-bin/elements-cli \
    ELECTRS_BIN=/opt/simplex-bin/electrs \
    SIMPLICITY_VAULT_DIR=/workspace/simple-simplicity-vault

# RPC defaults
ENV RPC_HOST=localhost \
    RPC_PORT=18443 \
    RPC_USER=rpcuser \
    RPC_PASSWORD=rpcpass

# Results volume
VOLUME /data/results

EXPOSE 18443

ENTRYPOINT ["/workspace/entrypoint.sh"]
CMD ["--help"]
