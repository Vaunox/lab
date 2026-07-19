# ACCEPTANCE — fixture-of-fixtures

Planted violations for check_fixture_provenance. Two declarations, two distinct
defects: a blob hash that does not match the file, and a derivation document
that does not exist.

<!-- gate_fixtures -->

```yaml
- id: GATE4.COSTS.A
  path: gates/costs_case_a.csv
  blob_sha: 0000000000000000000000000000000000000000
  derivation: gates/costs_case_a_derivation.md

- id: GATE4.COSTS.B
  path: gates/costs_case_a.csv
  blob_sha: 0000000000000000000000000000000000000000
  derivation: gates/absent_derivation.md
```
