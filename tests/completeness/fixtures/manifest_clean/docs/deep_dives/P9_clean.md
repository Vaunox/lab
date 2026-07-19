# Deep Dive P9 — Negative control for check_manifest

> **Status: COMPLETE. Manifest frozen.** This phase may open.
>
> The inverse fixture. Nothing here is planted: the artifact exists, the loop
> closes, the certifying test resolves, `DEFERRALS.md` is empty.
>
> A checker is proven by two facts, not one. That it rejects a broken tree shows
> it can fail. That it accepts a clean one shows it is not merely always failing
> — which is the same vacuity as always passing, wearing the opposite sign.

---

## 1. Scope

Front matter, and exempt from section coverage.

---

## 2. The artifact that exists

`src/lab/present_by_design.py` is on disk and tracked, so the existence check
resolves rather than reporting a missing file.

---

## 3. MANIFEST — frozen

```yaml
manifest_version: 1
phase: P9
frozen: true

rows:
  - id: P9.CLEAN.PRESENT
    artifact: src/lab/present_by_design.py
    kind: file
    spec: "§2"
    call_site: n/a
    certifying_test: tests/planted_certifier.py::test_clean_row_is_present
```
