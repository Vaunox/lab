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

**Phase:** P0 — Repository, remote, and the enforcement machinery
**Branch:** *(not yet created)*
**Last commit:** *(none)*
**Session:** 0 (nothing built)

## What is done

Nothing. Governance is ratified; no code exists.

## What to do next

**There is no `.git` yet. You are at session 0, and the bootstrap is yours to run.**

1. **§3.0 Preflight** — `git`, `gh`, `gh auth status`, `python3 >= 3.11`.
   If `gh auth status` fails: **stop**, tell the operator to run `gh auth login`, do nothing else.
2. **§3.1** `git init -b main`, `core.hooksPath .githooks` **before** the first commit, commit.
3. **§3.2** `gh repo create lab --public --source=. --remote=origin --push` (public from commit #1 — see below)
4. **§3.3** Protect `main` with `enforce_admins=true`. **Pipe the `gh api` response into this file.**
5. **§3.4** `git checkout -b phase/p0-scaffold`
6. Then P0 proper — and **build the checkers before the code they police.** Building enforcement after the substrate means the substrate is the one thing built unpoliced, and it is what everything else stands on.

## Public from commit #1 — what this forces

The repo is **public from the first commit**, by operator decision. There is no
private staging window. Two consequences the builder must respect from the start,
not retrofit:

- **Attribution must be clean in the *first* commit**, not cleaned up later. The
  `commit-msg` hook and `.claude/settings.json` are wired in §3.1 *before* that commit
  precisely so the public history is clean from row zero. A public history cannot be
  un-authored without a full rewrite.
- **`LICENSE` (Apache-2.0) and `NOTICE` are committed in the first commit** (§3.1 / §4.6),
  not at P8. A public repo with no licence is "all rights reserved" by default, and a
  contributor could open a PR into that vacuum on day one.

Public visibility is **not** release (Constitution S1): the repo being readable is not
the Lab being packaged, tagged, announced, or installable. Building in the open, with
red gates and a visible ledger of failures, is the same credibility play as the trial
ledger itself.

## What you must NOT do

*This section is not optional. A fresh agent's characteristic failure is seeing something half-built, deciding to "clean it up," and destroying an invariant it did not know was there.*

- **Do not write any `lab/` code before the checkers exist.** P0.4 first.
- **Do not touch a governance doc in a code PR.** `CONSTITUTION.md`, `CONTRACTS.md`, `ACCEPTANCE.md`, `PLAYBOOK.md`, `docs/deep_dives/**`. CI will reject it. This is deliberate: the builder must not be able to edit the thing that judges the builder.
- **Do not end a session with a stub that makes a check pass.** End red and honest. See §12.
- **Do not resolve an ambiguity in the deep dive.** Stop, and surface it. An agent resolving ambiguity resolves it toward whatever is cheapest to build — not dishonestly, it just genuinely looks like the reasonable reading from where you are standing.

## Blocking questions for the operator

*Nothing may proceed past these.*

| # | Question | Blocks |
|---|---|---|
| — | None. | — |

The only operator action in the entire program is `gh auth login`, and only if
preflight finds `gh` unauthenticated. Credential handling is not the builder's.

## Non-blocking — decided by the builder, needs review

*Proceed, but the operator should look.*

| # | Decision | Tag | Review by |
|---|---|---|---|
| — | — | — | — |

---

# ═══ MACHINE STATE ═══

*Generated. Never narrated. Paste `python tools/gate.py` output verbatim.*

## Last `python tools/gate.py`

```
(not yet run — no code exists)
```

**Run at:** —
**Commit:** —

## Manifest

*Generated by `check_manifest.py`. Never hand-counted.*

```
(not yet run)
```

| | |
|---|---|
| Rows built | 0 |
| Rows open | — |
| Spec sections without a row | — |
| Rows without a spec section | — |

## Gates

| Check | Status |
|---|---|
| tests | — |
| `check_manifest.py` | — |
| `check_no_stubs.py` | — |
| `check_spec_isolation.py` | — |
| `check_fixture_provenance.py` | — |
| `check_import_graph.py` | — |
| `check_attribution.py` | — |
| mutation ≥ 90% (substrate) | — |
| `DEFERRALS.md` empty | ☑ (empty) |

---

# ═══ SESSION LOG ═══

*Append-only. Never edit a past entry — append a correction.*

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

## Session 0 — 2026-07-13 — Phase P0 (pre-build)

### Built
Nothing. Governance ratified only.

### Decisions
- `[OPERATOR]` Name: **Lab**. Repo `lab`, package `src/lab/`.
- `[OPERATOR]` **Repo is PUBLIC from commit #1, permanently.** Public repos get branch
  protection free (the free-tier private-repo limitation that blocks it does not apply),
  so the builder never pauses to ask about visibility. Attribution and `LICENSE` must be
  correct in the first commit — there is no private window. Public visibility is not
  release (S1).
- `[OPERATOR]` Apache-2.0. `LICENSE` + `NOTICE` land at **P0**, not P8 — a repository with no licence is "all rights reserved" by default, and that is the wrong default to hold for even one day.
- `[OPERATOR]` Open source. Research and backtesting only — **no live execution, ever.**
- `[OPERATOR]` Paper trading is v2, and lands as an **engine**, not a subsystem.
- `[OPERATOR]` Users bring their own data and their own strategies.
- `[OPERATOR]` The Lab must be drivable by LLM agents as a first-class caller.
- `[OPERATOR]` No AI/tool attribution anywhere in the repo or its history.
- `[OPERATOR]` `tools/gate.py`, not `make` — the operator is on Windows, and a gate the operator cannot run is a gate the operator does not run.
- `[OPERATOR]` CI runs an OS matrix (ubuntu · windows · macos). The ledger lock differs by platform and an untested lock is a silently forked chain.
- `[BUILDER]` Calibration pinned: null ≤10% (random **and** LLM-generated), power ≥60% at net Sharpe 1.0. *Operator delegated the number; it is now a fixture and is not user-configurable.*

### Uncertain
- `[OPEN]` Whether NSE price-band files are freely and reliably archivable. Affects P3's fill gate. **The scraper should start running now regardless** — NSE does not backfill, and every day not saved is a hole that cannot later be filled.

### Blocked
- Nothing.

### tools/gate.py
```
(no code)
```
