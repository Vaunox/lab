# Deep dives — the specification

**A phase cannot open until its deep dive exists and is marked `frozen: true`.**
`tools/check_manifest.py` refuses to run otherwise. This is the mechanical form
of the rule; without it, the rule is prose.

## Present

| Phase | File | Status |
|---|---|---|
| P0 — Repository, remote, enforcement machinery | `P0_scaffold.md` | **frozen** |
| P1 — Substrate: ledger, clock, identity, haircut | `P1_substrate.md` | **frozen** |

## Absent, and why

There are no outlines here. **An outline is not a specification, and a phase begun
against one will be built to its gate and nothing more.** That is the observed
failure mode this whole apparatus exists to prevent, so we do not seed it with
stubs of our own.

**P2 (costs) and P3 (data)** depend only on contracts that are already frozen.
They can and should be written before P1 merges.

**P4–P9** genuinely depend on what earlier phases produce — P4's engine spec needs
the real `MarketView` shape from P3; P6's clustering needs the actual return-series
format from P4/P5. Writing them now would produce hedges and TBDs, which is
ambiguity, which is the thing that causes an agent to build the cheapest reading.

**This is sequencing, not deferral, and the distinction is enforced:** every phase's
*scope* is already pinned in `ACCEPTANCE.md`. Detail gets elaborated later. **Scope
cannot shrink later.** See `DEFERRALS.md` for why that line matters.

## Writing one

Copy the shape of `P1_substrate.md`. It is the reference for depth. Specifically:

1. **Scope**, and what is explicitly *not* in the phase.
2. **Why this ordering** — the failure modes being designed out.
3. **The specification proper.** Every type, every signature, every invariant.
   Precise everywhere, not just where the gate looks.
4. **Failure modes and edge cases** — a numbered table, each with a behaviour.
   The ones you leave out are the ones a user finds.
5. **Test plan** — exhaustive, named. A test that does not exist is a manifest
   failure, not an oversight.
6. **MANIFEST** — every module, function, test, script. Frozen.
7. **Gate** — correctness *and* completeness.
8. **Amendment log.**

If it is shorter than P1's, it is probably an outline.
