# Deep Dive P9 — Planted violation for check_manifest

> **Status: COMPLETE. Manifest frozen.** This phase may open.
>
> This tree is a fixture. It is not a phase. It exists so that
> `check_manifest.py` has something it must reject, and it carries exactly one
> planted violation so that a rejection is attributable to that violation and
> not to fixture sloppiness.

---

## 1. Scope

Front matter, and exempt from section coverage. Present so the fixture exercises
the exemption path rather than avoiding it.

---

## 2. The planted violation

One manifest row names an artifact that does not exist on disk.

Everything else in this fixture is well formed: the loop closes in both
directions, the certifying test resolves, and `DEFERRALS.md` is empty. A checker
that rejects this tree rejects it for the missing artifact, which is the only
thing wrong with it.

---

## 3. MANIFEST — frozen

```yaml
manifest_version: 1
phase: P9
frozen: true

rows:
  - id: P9.PLANTED.MISSING
    artifact: src/lab/absent_by_design.py
    kind: file
    spec: "§2"
    call_site: n/a
    certifying_test: tests/planted_certifier.py::test_planted_row_is_absent
```
