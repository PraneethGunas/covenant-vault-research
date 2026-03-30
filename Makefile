# ============================================================
# Covenant Vault Comparison — Makefile
# ============================================================
# Wraps Docker commands for the full experiment lifecycle.
# 5 covenants: CTV, CCV, OP_VAULT, CAT+CSFS, Simplicity.
# 15 experiments across comparative, capability, and verification categories.
#
#   make build          Build the Docker image (~45 min first time)
#   make test           Quick smoke test (lifecycle_costs on CTV)
#   make run-all        Run all core experiments on all covenants
#   make analyze        Analyze latest results
#
# ============================================================

IMAGE    := vault-comparison:latest
COMPOSE  := docker compose
RUN      := $(COMPOSE) run --rm vault-comparison
RESULTS  := results

# ── Build ───────────────────────────────────────────────────

.PHONY: build build-from-source rebuild

build:                          ## Build using pre-built binaries (~3 min)
	DOCKER_BUILDKIT=1 docker build --platform linux/amd64 -t $(IMAGE) .

build-from-source:              ## Build compiling all nodes from source (~45 min)
	DOCKER_BUILDKIT=1 docker build --platform linux/amd64 --build-arg BUILD_FROM_SOURCE=1 -t $(IMAGE) .

rebuild:                        ## Force rebuild from scratch (no cache, pre-built binaries)
	DOCKER_BUILDKIT=1 docker build --platform linux/amd64 --no-cache -t $(IMAGE) .

# ── Run — by covenant ───────────────────────────────────────

.PHONY: run-all run-ctv run-ccv run-opvault run-cat-csfs run-simplicity

run-all:                        ## Run all core experiments on all 5 covenants
	$(RUN) run --tag core --covenant all

run-ctv:                        ## Run all core experiments on CTV
	$(RUN) run --tag core --covenant ctv

run-ccv:                        ## Run all core experiments on CCV
	$(RUN) run --tag core --covenant ccv

run-opvault:                    ## Run all core experiments on OP_VAULT
	$(RUN) run --tag core --covenant opvault

run-cat-csfs:                   ## Run all core experiments on CAT+CSFS
	$(RUN) run --tag core --covenant cat_csfs

run-simplicity:                 ## Run all core experiments on Simplicity (Elements)
	$(RUN) run --tag core --covenant simplicity

# ── Run — by tag ────────────────────────────────────────────

.PHONY: run-security run-quantitative run-fee

run-security:                   ## Run all security-tagged experiments on all covenants
	$(RUN) run --tag security --covenant all

run-quantitative:               ## Run all quantitative experiments on all covenants
	$(RUN) run --tag quantitative --covenant all

run-fee:                        ## Run all fee-management experiments on all covenants
	$(RUN) run --tag fee_management --covenant all

# ── Run — individual experiments ────────────────────────────

.PHONY: lifecycle fee-pinning fee-sensitivity recovery-griefing \
        watchtower-exhaustion address-reuse multi-input \
        revault-amplification ccv-mode-bypass \
        opvault-trigger-key-theft opvault-recovery-auth \
        cat-csfs-hot-key-theft cat-csfs-witness-manipulation \
        cat-csfs-destination-lock cat-csfs-cold-key-recovery

lifecycle: COVENANT ?= all      ## Run lifecycle_costs (COVENANT=ctv|ccv|opvault|cat_csfs|simplicity|all)
lifecycle:
	$(RUN) run lifecycle_costs --covenant $(COVENANT)

fee-pinning: COVENANT ?= all
fee-pinning:                    ## Run fee_pinning (fee mechanism comparison)
	$(RUN) run fee_pinning --covenant $(COVENANT)

fee-sensitivity: COVENANT ?= all
fee-sensitivity:                ## Run fee_sensitivity analysis
	$(RUN) run fee_sensitivity --covenant $(COVENANT)

recovery-griefing: COVENANT ?= all
recovery-griefing:              ## Run recovery_griefing (comparative)
	$(RUN) run recovery_griefing --covenant $(COVENANT)

watchtower-exhaustion: COVENANT ?= all
watchtower-exhaustion:          ## Run watchtower_exhaustion (splitting attack)
	$(RUN) run watchtower_exhaustion --covenant $(COVENANT)

address-reuse: COVENANT ?= all
address-reuse:                  ## Run address_reuse safety test
	$(RUN) run address_reuse --covenant $(COVENANT)

multi-input: COVENANT ?= all
multi-input:                    ## Run multi_input batching efficiency
	$(RUN) run multi_input --covenant $(COVENANT)

revault-amplification: COVENANT ?= all
revault-amplification:          ## Run revault_amplification cost analysis
	$(RUN) run revault_amplification --covenant $(COVENANT)

ccv-mode-bypass:                ## Run ccv_mode_bypass (CCV-only, verification)
	$(RUN) run ccv_mode_bypass --covenant ccv

opvault-trigger-key-theft:      ## Run opvault_trigger_key_theft (OP_VAULT-only)
	$(RUN) run opvault_trigger_key_theft --covenant opvault

opvault-recovery-auth:          ## Run opvault_recovery_auth (OP_VAULT-only)
	$(RUN) run opvault_recovery_auth --covenant opvault

cat-csfs-hot-key-theft:         ## Run cat_csfs_hot_key_theft (CAT+CSFS-only)
	$(RUN) run cat_csfs_hot_key_theft --covenant cat_csfs

cat-csfs-witness-manipulation:  ## Run cat_csfs_witness_manipulation (CAT+CSFS-only)
	$(RUN) run cat_csfs_witness_manipulation --covenant cat_csfs

cat-csfs-destination-lock:      ## Run cat_csfs_destination_lock (CAT+CSFS-only)
	$(RUN) run cat_csfs_destination_lock --covenant cat_csfs

cat-csfs-cold-key-recovery:     ## Run cat_csfs_cold_key_recovery (CAT+CSFS-only)
	$(RUN) run cat_csfs_cold_key_recovery --covenant cat_csfs

# ── Analysis ────────────────────────────────────────────────

.PHONY: analyze list

analyze:                        ## Analyze results (dir=results/<timestamp>)
	$(RUN) analyze $(dir)

list:                           ## List available experiments and tags
	$(RUN) list

# ── Testing ─────────────────────────────────────────────────

.PHONY: test test-ctv test-ccv test-opvault test-cat-csfs test-simplicity

test:                           ## Quick smoke test — lifecycle_costs on CTV
	$(RUN) run lifecycle_costs --covenant ctv

test-ctv:                       ## Smoke test CTV (lifecycle + fee_pinning)
	$(RUN) run lifecycle_costs --covenant ctv
	$(RUN) run fee_pinning --covenant ctv

test-ccv:                       ## Smoke test CCV (lifecycle + mode_bypass)
	$(RUN) run lifecycle_costs --covenant ccv
	$(RUN) run ccv_mode_bypass --covenant ccv

test-opvault:                   ## Smoke test OP_VAULT (lifecycle + recovery_auth)
	$(RUN) run lifecycle_costs --covenant opvault
	$(RUN) run opvault_recovery_auth --covenant opvault

test-cat-csfs:                  ## Smoke test CAT+CSFS (lifecycle)
	$(RUN) run lifecycle_costs --covenant cat_csfs

test-simplicity:                ## Smoke test Simplicity (lifecycle on Elements)
	$(RUN) run lifecycle_costs --covenant simplicity

# ── Utilities ───────────────────────────────────────────────

.PHONY: shell logs clean clean-results clean-image help

shell:                          ## Interactive shell inside the container
	$(COMPOSE) run --rm vault-comparison bash

logs:                           ## Show latest results directory
	@ls -td $(RESULTS)/*/ 2>/dev/null | head -5 || echo "No results yet."

clean: clean-results clean-image  ## Remove results and Docker image

clean-results:                  ## Remove local results directory
	rm -rf $(RESULTS)/

clean-image:                    ## Remove the Docker image
	docker image rm $(IMAGE) 2>/dev/null || true

help:                           ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
