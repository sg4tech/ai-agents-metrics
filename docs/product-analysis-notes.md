# Product Analysis Notes

Use this file as a short-lived memory aid for product and metrics ideas that are not yet mature enough to become confirmed framing.

## 2026-04-02

### Token speed hypothesis review

- Rejected the idea that raw token consumption speed should be the primary metric.
- Current history did not show a statistically significant relationship between `attempts > 1` and higher token speed.
- The strongest observed driver of total token usage was session duration, not retries.
- Task type mattered more than retries for token speed:
  - `product` work had higher `tokens/min` than `retro`
  - that difference was statistically significant, but it looks more like task-mix confounding than a general quality signal
- Practical takeaway:
  - keep `token speed` as a secondary diagnostic signal only
  - prefer normalized views such as `tokens per accepted goal` or `tokens per product goal`

### Retro/meta hypothesis review

- Current history is too sparse to support a strong claim that `retro` or `meta` work causally improves product throughput or lowers cost.
- There are only 4 independent days with usable timed history, so day-level conclusions are weak.
- Descriptively, days with more `retro/meta` activity also had more `product` activity, but this is not statistically convincing:
  - day-level `rm_count` vs `product_count` had a positive rank correlation
  - exact permutation test on the 4-day sample was not significant
- Practical takeaway:
  - treat the idea as a plausible process hypothesis
  - do not treat the current history as proof

