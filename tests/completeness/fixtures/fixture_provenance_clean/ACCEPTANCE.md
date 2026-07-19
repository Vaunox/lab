# ACCEPTANCE — negative control

One correctly declared fixture: the blob hash matches, and the derivation
document exists beside it.

<!-- gate_fixtures -->

```yaml
- id: GATE4.COSTS.A
  path: gates/costs_case_a.csv
  blob_sha: 1ce736e572c304c0bbed0e20eae6d09736533064
  derivation: gates/costs_case_a_derivation.md
```
