# Readiness

**Verdict: CONDITIONAL PASS for the simplified paper. NOT READY for the old Stage II system, and NOT READY for the external table that cited missing scripts.**

A student can defend this sentence, because every number in it is in `revision/results/` and the comparisons that go the wrong way are in the same table:

Under a sequential settlement and quotes lagged by at least one day, 41.47% of attractive gaps lose money in the model (N = 56,172). A ₹200 margin rule, frozen on the validation months, has a higher mean than a yesterday's-quote road rule at almost the same dispatch rate, and a worse loss rate and a worse ES10. ES10 moves by hundreds of rupees per quintal when the missing-price return multiple changes. The older same-day test against the road rule was inconclusive. Grade-explicit apples were not fixed.

Do not defend: a conformal theorem, a field-income gain, "closed markets," the unreproduced figures MG ₹397.24 and N ≈ 67,675, or a claim that the cautious rule reduces downside risk relative to the road rule.

## Checklist

- [x] Lagged replay code committed under `revision/`.
- [x] Paper names `revision/build_run.py` and commit `eef9c98938969354136be7396e6854e3abedf034`.
- [x] ES10 defined, tested, and used in the new tables.
- [x] Old quantile-tail means labeled as not ES10.
- [x] H2 left inconclusive. Apple failure left standing. Penalty dependence reported.
- [x] No merge.
- [ ] scikit-learn 1.3.0 replay of the 2024 pickle. Blocked on this Python.
- [ ] Grade-explicit lagged rebuild. Not done; apple file lacks settlement columns.
