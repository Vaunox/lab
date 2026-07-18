# DIVERGENCES

Permanent. Public. Append-only.

---

## What a divergence *is*

**There is no baseline to be wrong.**

The reproduction gates compare the engine against **ground truth derived by hand** — from the cost schedule and the fill rules, before the engine existed. So when an engine and a fixture disagree, there are exactly **two** possibilities:

1. **The derivation is wrong.** Fix the derivation, in its own PR, showing the corrected arithmetic. Re-run.
2. **The engine is wrong.** Fix the engine.

**There is no third case, and a divergence is never "accepted." It is resolved.**

This file therefore records something narrower and more useful than the usual: **the derivations that turned out to be wrong, and how.** Each one is a place where a human, working carefully from the schedule, still got the arithmetic wrong — which is a warning about the *next* derivation, and about the schedule's clarity.

## Why this matters more than it sounds

If we allowed a divergence to be *accepted* — "the engine says X, the derivation says Y, X is close enough" — then the gate would be decorative. The whole point of hand-derivation is that **someone who is not the engine computed the right answer.** Letting the engine win an argument with that person hands the specification back to the implementation — and the implementation is the thing on trial.

## Rules

1. **The cause is found before anything is changed.** "Small" is not a classification. An unexplained divergence in a machine whose product is trust is an unknown bug in a cost or fill path, and it will ship.
2. **The derivation and the engine never change in the same PR.** A derivation is a fixture; a fixture is spec-tier (§11.1). Changing both at once is the engine grading its own homework with a pencil.
3. **A corrected derivation is re-derived from the schedule, not from the engine's output.** If you find yourself reading the engine's number to "check" your arithmetic, stop — you are no longer deriving, you are transcribing.
4. **This file ships with the release.** A gate nobody can inspect is not a gate.

---

## Log

| Date | Gate | Fixture | Delta | Cause | Which was wrong | Resolution |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

---

## Template

```
### YYYY-MM-DD — Gate N — [one-line summary]

**Fixture:**    <id, derivation doc, blob hash>
**Expected:**   <the hand-derived value>
**Observed:**   <what the engine produced>
**Delta:**      <exact magnitude, per affected trade / statistic>

**Cause:**
<The mechanism. Not "it didn't match." What, specifically, was miscomputed,
 and by whom — the human or the engine?>

**Which was wrong:** <derivation | engine>

**Resolution:**
<If the derivation: the corrected arithmetic, shown. Re-derived from the
 schedule, NOT read off the engine.
 If the engine: the fix, and why the fixture was right.>

**What this invalidates:**
<Any other fixture, result, or claim that depended on the same mistake.
 A derivation error usually has siblings.>
```
