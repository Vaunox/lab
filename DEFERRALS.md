# DEFERRALS

> **This file must be EMPTY at every phase exit.** A phase does not merge with an open deferral. `check_manifest.py` fails the build if this table has rows when a phase PR is opened for merge.

---

## Why this file exists

The observed failure mode of every previous project: **the builder built what the gate tested and quietly skipped the rest.** Every skipped item was individually reasonable. Together they left holes in a shared substrate, and a hole in the substrate does not block the phase that leaves it — it becomes load-bearing three phases later, under four thousand trials, in a ledger that is append-only and cannot now be rebuilt.

The previous program's Completion Standard catches a build that **claims more than it delivered**. It does not catch a build that **delivers less than the spec and claims exactly that.** That build is honest, incomplete, and passes every check.

This file, plus `check_no_stubs.py` and the MANIFEST gate, is what closes it.

---

## The rule

**Deferral is a logged amendment, never a silent skip.**

If a manifest row turns out to be genuinely unnecessary, the correct action is **not** to skip it. It is to:

1. **Amend the deep dive.** Dated entry in its §Amendment log: what changed, why.
2. **Amend the manifest.** Remove the row, citing the deep dive amendment.
3. The item is now **out of scope**, and the phase is complete without it.

Scope may be changed. Scope may not be changed *quietly*, and it may not be changed *retroactively*.

This is the same ratchet the Lab imposes on its users. The Lab is not exempt from its own methodology.

---

## What is *not* a deferral

Three things get confused with deferral and are not:

**A null object is not a stub.** `NullMarketView` is a complete, correct, tested implementation of the degenerate case. It ships. It is permanent. A stub raises `NotImplementedError` and fails the build.

**A conservative fake is not a stub.** The P1 raw-count haircut is *strictly more punitive* than the P6 clustered version, so it can only ever err toward rejecting a real strategy — never toward passing a fake one. It is complete, tested, and documented as conservative. It ships.

> A stub says *"this doesn't work yet."* A conservative fake says *"this works, and errs in the safe direction."* One is a lie waiting to be found. The other is engineering.

**Sequencing is not deferral.** P5's deep dive is written before P5 opens, not before P1 opens — because P5's spec depends on what P4 actually produced, and writing it now would be fiction. The safeguard that keeps this honest: **every phase's scope is already pinned in `ACCEPTANCE.md`.** Detail is elaborated later; scope cannot shrink later.

---

## Open deferrals

**Must be zero at every phase exit.**

| ID | Phase | Manifest row | What is missing | Why | Opened | Closes by |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

---

## Closed deferrals

Historical record. A closed deferral was either **built** or **removed by amendment**. It was never merely forgotten.

| ID | Phase | Manifest row | Resolution | Closed |
|---|---|---|---|---|
| — | — | — | — | — |
