# HANDOFF

> **Read this first. Every session. Before the deep dive, before the code, before anything.**
>
> This file is the current state of the active phase. It is **authoritative over your assumptions** — where your instinct and this file disagree, this file wins, and if it turns out to be wrong, you fix the file rather than acting on the instinct.
>
> Then read `DEAD_ENDS.md`. It will save you a day.

---

## HOW THIS FILE WORKS

**It is a ledger, and it obeys the Lab's own methodology.** Append-only history. Every claim carries its evidence. No "done" without a test name. If we would not accept an unevidenced claim from a user, we do not accept one from ourselves.

**It is written continuously, not at the end of the session.** A handoff composed by a context-exhausted agent is composed by the *worst* version of that agent, at exactly the moment its judgement is most degraded. Update it after each meaningful decision, each rejected approach, each surprise. The end-of-session ritual is a **checkpoint, not the writing**.

**Machine state is piped, never typed.** `python tools/gate.py` output goes in verbatim. Typed status is a claim. Piped status is evidence. Hand-counting the manifest tally is forbidden — `check_manifest.py` produces it.

### Provenance tags — every claim carries one

| Tag | Meaning |
|---|---|
| `[VERIFIED]` | A test proves it. **Cite the test.** |
| `[ASSERTED]` | The builder believes it. No test yet. Treat as unproven. |
| `[OPERATOR]` | The human decided it. Binding. |
| `[BUILDER]` | The builder decided it. **Provisional until the operator confirms.** |
| `[OPEN]` | Nobody has decided. Blocking or not — say which. |

**A builder's suggestion is not an operator's decision**, however warmly it was received. This file never promotes one to the other. If it is not marked `[OPERATOR]`, the human did not agree to it.

### Scope

This file covers **the current phase only**. At phase close it is archived to `docs/handoff/PN_HANDOFF.md` and reset.
`DEAD_ENDS.md` is **global and permanent** — a dead end found in P1 still matters in P6.

### Exempt from §11.1

Governance docs cannot travel in the same PR as code. **This file is a log, not a spec, and is exempt** — it is *required* to change alongside code. Same for `DEAD_ENDS.md`, `PROJECT_STATE.md`, `DIVERGENCES.md`.

---

# ═══ COLD START ═══

*Rewritten at the end of every session. Written for someone with zero context.*
*Test: could a fresh agent, reading only this block + the governance docs + the deep dive, resume correctly and safely? If not, it is incomplete.*

## Where we are

**Phase:** P1 — Substrate: ledger, clock, haircut
**Deep dive:** `docs/deep_dives/P1_substrate.md` — **read it in full before writing any code**
**Branch:** none yet. P1 opens on `phase/p1-substrate`, cut from `main`.
**Remote:** https://github.com/Vaunox/lab (public)
**Session:** 0 of P1 — **nothing built.**

## What happened immediately before this

**P0 is closed.** Gate 0 met, `gate-0-scaffold` tagged, and a fresh clone of that tag reports
`GATE GREEN -- 10 stages passed`. The full P0 record — every decision, every dead end, the
red gate it sat at for most of its build, and the operator rulings that resolved it — is
archived at `docs/handoff/P0_HANDOFF.md`. **Read it if anything here is surprising.**

What P0 leaves you:

- **Seven checkers**, each with a planted violation *and* a negative control, wired into
  `python tools/gate.py` (ten stages). They police P1. They were built before it deliberately.
- **`src/lab/core/config.py`** (`load_config`, `get_secret`) and **`src/lab/core/logging.py`**
  (`configure`) — complete, tested, and **called by nothing**. See *What to do first*.
- **CI on three platforms**, with the required status check named exactly `gate`.
- **§11.1 now binds absolutely.** The §5.4 bootstrap exception is spent — `origin/main` carries
  the `gate` workflow, so it has self-closed. **Spec and code may never travel in the same PR
  again.** If P1's deep dive needs amending, that is its own PR, before or after, never during.

## What to do first

1. **Read `docs/deep_dives/P1_substrate.md` in full.** It is the specification and it is
   authoritative. Build **every row of its MANIFEST**, not merely what the gate tests touch.
2. **Give `load_config`, `get_secret` and `configure` their real consumers.** Amendment A-004
   reclassified those three rows to `call_site: n/a` on the explicit record that *"the consumer
   arrives in P1"*. P1 is where that debt comes due. They are complete and certified; what they
   lack is a caller.
3. `git checkout -b phase/p1-substrate` from `main`.

## What you must NOT do

*A fresh agent's characteristic failure is seeing something half-built, deciding to "clean it
up," and destroying an invariant it did not know was there.*

- **Do not weaken a checker to make your code pass.** They flagged three of P0's own docstrings
  and one tautological assertion, and every one was a real finding. *The annoyance is the
  mechanism.*
- **Do not touch a governance doc in a code PR.** `CONSTITUTION.md`, `CONTRACTS.md`,
  `ACCEPTANCE.md`, `PLAYBOOK.md`, `docs/deep_dives/**`. The bootstrap exception is gone; CI
  will reject it, correctly.
- **Do not end a session with a stub that makes a check pass.** End red and honest.
- **Do not resolve an ambiguity in the deep dive.** Stop and surface it. An agent resolving
  ambiguity resolves it toward whatever is cheapest to build.
- **Do not let the engine be its own oracle**, and do not take an expected value from any
  implementation. Fixtures are derived by hand. DE-000f.
- **Read `DEAD_ENDS.md`.** Six entries are from P0 and three of them (DE-003, DE-004, DE-006)
  are about tests that asserted environment state. P1 introduces a file lock with per-platform
  implementations, which is the same trap with more surface.

## Blocking questions for the operator

| # | Question | Blocks |
|---|---|---|
| — | None open. | — |

## Standing, deferred by operator ruling — do NOT build speculatively

| # | Item | Decided by |
|---|---|---|
| Q-002 | `DIVERGENCES.md` has no citable ID, so §7.1's skip exemption has nothing to cite. `check_no_stubs` fails closed on every skip, which is correct under every candidate scheme and binds on nothing today. **The ID scheme is decided by the first phase that actually needs a divergence-citing skip (P4/P5).** | operator, 2026-07-19 |
| D-004 | The gate-fixture declaration format in `ACCEPTANCE.md` (`<!-- gate_fixtures -->` + fenced yaml). Confirmed a non-blocker for Gate 0; **P4 confirms or amends it** when the first real fixture lands. | operator, 2026-07-19 |

---

# ═══ MACHINE STATE ═══

*Generated. Never narrated. Paste `python tools/gate.py` output verbatim.*

## Last `python tools/gate.py`

**Run at:** 2026-07-19 · **Ref:** `gate-0-scaffold`, fresh clone from GitHub · **Exit code:** `0`

The P0 exit state, carried forward as P1's starting line. Re-run and re-pipe at the end of
P1's first session.

```
All checks passed!
Success: no issues found in 26 source files
........................................................................ [ 77%]
.....................                                                    [100%]
93 passed in 4.88s
check_no_stubs: clean over 13 file(s)
check_spec_isolation: clean -- spec 0, code 0, logs 0 (exempt)
check_import_graph: clean -- 0 rule(s) over 4 module(s)
check_fixture_provenance: no gate fixtures declared in ACCEPTANCE.md. That is the expected P0 state -- the tool ships before the phase it polices, so the judge is never built in the same session as the defendant.
check_substrate_purity: inert -- no substrate-frozen tag exists yet. The kill gate arms at Gate 4 and fires at Gate 5. Reported rather than passed silently: nothing to compare is not a clean substrate.

=== lint ===
--- lint: ok

=== types ===
--- types: ok

=== tests ===
--- tests: ok

=== manifest ===
phase:                        P0
rows total:                   32
rows built:                   32
rows open:                    0
spec sections without a row:  0
rows without a spec section:  0
failures:                     0
--- manifest: ok

=== stubs ===
--- stubs: ok

=== spec-isolation ===
--- spec-isolation: ok

=== imports ===
--- imports: ok

=== attribution ===
    clean over 45 record(s)
--- attribution: ok

=== fixtures ===
--- fixtures: ok

=== substrate-purity ===
--- substrate-purity: ok

============================================================
GATE GREEN -- 10 stages passed
```

## Branch protection — `gh api` response, verbatim

*§3.3 / §12.1: CI cannot verify this without an admin-scoped token, and putting an admin-scoped
token in CI to check that admins are restricted is a circle not worth closing. So the evidence is
piped here, as output. Typed status is a claim; piped status is evidence.*

**Captured at:** commit `4e474adbec3b68d4ba47fee24cb347b164050ece`
**Command:** `gh api "repos/Vaunox/lab/branches/main/protection"`

> ### DO NOT REMOVE THIS BLOCK ON A PHASE RESET
>
> **The marker below and the JSON block after it are `P0.BOOT.PROTECTION`'s certifying
> evidence**, cited by the frozen manifest as `certifying_test: HANDOFF.md::piped_gh_api_output`
> and resolved by `check_manifest._check_evidence_block`. This file is archived and reset at
> every phase close (see *Scope*, above) — **this block is the one part of it that must be
> carried across verbatim, every time, forever.** It is not P0 history. It is a live gate input.
>
> **The trap, stated so you read the right fix at the moment of contact:** if you have just
> rewritten this file for a new phase and the `manifest` stage has gone red on
> `P0.BOOT.PROTECTION`, you deleted this block. **The fix is to restore it.**
>
> The fix is **not** to relax `check_manifest`, and it is **not** to edit or delete the manifest
> row — that row lives in a frozen deep dive, editing it in a code PR fails `check_spec_isolation`
> (§11.1), and it is exactly the "cheapest way to pass a manifest gate is to edit the manifest"
> move that §8 exists to refuse. A branch-protection claim with its evidence removed is a typed
> status, not a piped one (§12.1).
>
> Keep prose out of the fenced block, and do not put a fenced `json` block between the marker and
> the evidence: `_check_evidence_block` grades the **first** JSON block following the marker.
> A note placed *above* the marker, like this one, cannot affect the match at all.
>
> The durable copy of this warning is in `PROJECT_STATE.md`, "Blocked / needs a decision", which
> is never reset — read it if this note has already been lost.

<!-- piped_gh_api_output -->

```json
{
    "url": "https://api.github.com/repos/Vaunox/lab/branches/main/protection",
    "required_status_checks": {
        "url": "https://api.github.com/repos/Vaunox/lab/branches/main/protection/required_status_checks",
        "strict": true,
        "contexts": [
            "gate"
        ],
        "contexts_url": "https://api.github.com/repos/Vaunox/lab/branches/main/protection/required_status_checks/contexts",
        "checks": [
            {
                "context": "gate",
                "app_id": null
            }
        ]
    },
    "required_signatures": {
        "url": "https://api.github.com/repos/Vaunox/lab/branches/main/protection/required_signatures",
        "enabled": false
    },
    "enforce_admins": {
        "url": "https://api.github.com/repos/Vaunox/lab/branches/main/protection/enforce_admins",
        "enabled": true
    },
    "required_linear_history": {
        "enabled": true
    },
    "allow_force_pushes": {
        "enabled": false
    },
    "allow_deletions": {
        "enabled": false
    },
    "block_creations": {
        "enabled": false
    },
    "required_conversation_resolution": {
        "enabled": false
    },
    "lock_branch": {
        "enabled": false
    },
    "allow_fork_syncing": {
        "enabled": false
    }
}
```

**Against §12 Gate 0 — bootstrap gate:**

| §12 requirement | Field | Value |
|---|---|---|
| CI required | `required_status_checks.contexts` | `["gate"]` ☑ |
| — strict | `required_status_checks.strict` | `true` ☑ |
| `enforce_admins=true` | `enforce_admins.enabled` | `true` ☑ |
| linear history | `required_linear_history.enabled` | `true` ☑ |
| force-push off | `allow_force_pushes.enabled` | `false` ☑ |
| deletion off | `allow_deletions.enabled` | `false` ☑ |

The `gate` context is required but **no workflow produces it yet** — `.github/workflows/ci.yml`
is unbuilt. `main` is therefore currently unmergeable-to by any PR, which is the correct and
intended state: §5.4 notes protection precedes CI by construction, and the first PR is the one
that supplies the check it must satisfy.

## Manifest

*Generated by `check_manifest.py`. Never hand-counted.*

**P1 has not opened.** The tally below is P0's exit state. `check_manifest` resolves the
active deep dive by sorted filename, so it still reports P0 until P1's branch is cut —
**re-run it once `phase/p1-substrate` exists and confirm it targets P1**, because a P1 session
validating P0's manifest would be green for the wrong reason.

```
phase:                        P0
rows total:                   32
rows built:                   32
rows open:                    0
spec sections without a row:  0
rows without a spec section:  0
failures:                     0
```

---

# ═══ SESSION LOG ═══

*Append-only. Never edit a past entry — append a correction.*
*P0's log is archived at `docs/handoff/P0_HANDOFF.md`.*

**Template — every session, no exceptions:**

```markdown
## Session N — YYYY-MM-DD — Phase PX

### Built
- `manifest.row.id` — [VERIFIED] `tests/path::test_name`
- `manifest.row.id` — [ASSERTED] no test yet; do not trust

### Tried and rejected
*The highest-value section in this file. Without it the next session
re-walks the same dead end — and may not recognise it as one.*
- Approach: <what>
  Failed because: <mechanism, not vibes>
  → appended to DEAD_ENDS.md as DE-NNN

### Decisions
- [BUILDER] <what, and why> — needs operator review
- [OPERATOR] <what the human decided this session>

### Uncertain
*What the next session should not inherit as confidence.*
- <thing I believe but did not verify>

### Blocked
- <what, on whom, since when>

### Surprises
*Where reality disagreed with the deep dive. Each of these is either a
spec bug (amend it) or a dead end (log it). Neither is "just proceed."*
- <what surprised me>

### tools/gate.py
<piped output>
```

---

## Session 0 — 2026-07-19 — Phase P1 (not started)

### Built
Nothing. P0 closed; P1 opens in its own session, on full context, after reading
`docs/deep_dives/P1_substrate.md` in full.

### Blocked
- Nothing.

### tools/gate.py
```
GATE GREEN -- 10 stages passed
```
