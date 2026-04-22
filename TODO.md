# TODO — Vault Comparison Framework

## Future Work

- [ ] **Formalization** — Alloy models in `formalization/alloy/` don't include Simplicity. Model the output-constrained recovery property and compare with CCV/OP_VAULT constrained recovery vs CAT+CSFS unconstrained.

- [ ] **Cross-chain fee comparison** — Simplicity vsizes are on Elements (different weight discount rules, ELIP-200 CT discount). A proper cross-chain comparison would need to account for Elements' different fee market dynamics.

- [ ] **Simplicity vault enhancements** — The current vault is minimal (no revault, no batching). Simplicity's expressiveness could support: recursive vaults (revault via `outputs_hash` chaining), batched triggers, oracle-gated withdrawals, multi-party recovery.
