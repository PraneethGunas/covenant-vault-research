# ============================================================
# Bitcoin Covenant Vault Comparison — Makefile
# ============================================================
# Wraps Docker commands for the full experiment lifecycle.
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

.PHONY: build rebuild

build:                          ## Build the Docker image (caches node compilations)
	DOCKER_BUILDKIT=1 docker build -t $(IMAGE) .

rebuild:                        ## Force rebuild from scratch (no cache)
	DOCKER_BUILDKIT=1 docker build --no-cache -t $(IMAGE) .

# ── Run — by covenant ───────────────────────────────────────

.PHONY: run-all run-ctv run-ccv run-opvault run-cat-csfs

run-all:                        ## Run all core experiments on all covenants
	$(RUN) run --tag core --covenant all

run-ctv:                        ## Run all core experiments on CTV
	$(RUN) run --tag core --covenant ctv

run-ccv:                        ## Run all core experiments on CCV
	$(RUN) run --tag core --covenant ccv

run-opvault:                    ## Run all core experiments on OP_VAULT
	$(RUN) run --tag core --covenant opvault

run-cat-csfs:                   ## Run all core experiments on CAT+CSFS
	$(RUN) run --tag core --covenant cat_csfs

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
        revault-amplification ccv-mode-bypass ccv-edge-cases \
        opvault-trigger-key-theft opvault-recovery-auth

lifecycle: COVENANT ?= all      ## Run lifecycle_costs (COVENANT=ctv|ccv|opvault|all)
lifecycle:
	$(RUN) run lifecycle_costs --covenant $(COVENANT)

fee-pinning: COVENANT ?= all
fee-pinning:                    ## Run fee_pinning (CTV-specific attack)
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

ccv-mode-bypass:                ## Run ccv_mode_bypass (CCV-only, critical)
	$(RUN) run ccv_mode_bypass --covenant ccv

ccv-edge-cases:                 ## Run ccv_edge_cases (CCV-only, developer footguns)
	$(RUN) run ccv_edge_cases --covenant ccv

opvault-trigger-key-theft:      ## Run opvault_trigger_key_theft (OP_VAULT-only)
	$(RUN) run opvault_trigger_key_theft --covenant opvault

opvault-recovery-auth:          ## Run opvault_recovery_auth (OP_VAULT-only)
	$(RUN) run opvault_recovery_auth --covenant opvault

# ── Analysis ────────────────────────────────────────────────

.PHONY: analyze list

analyze:                        ## Analyze results (dir=results/<timestamp>)
	$(RUN) analyze $(dir)

list:                           ## List available experiments and tags
	$(RUN) list

# ── Testing ─────────────────────────────────────────────────

.PHONY: test test-ctv test-ccv test-opvault test-cat-csfs

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
