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
**Branch:** `phase/p0-scaffold`
**Remote:** https://github.com/Vaunox/lab (public)
**Last commit:** `9d90afa`
**Session:** 2 — **every manifest row is built.** The gate is red on one stage, for one
reason, and that reason is a finding for the operator rather than unbuilt work.

## The state in one paragraph

All 32 manifest rows exist. All seven checkers are built, each with a planted violation
**and** a negative control, and `test_every_checker_rejects_its_fixture` passes over all
seven. Nine of the gate's ten stages are green. The tenth — `manifest` — reports exactly
**six** failures, all of them the same failure: `call_site: required` on a symbol that has
no honest caller anywhere in P0. **Nothing is stubbed. Nothing was skipped.** The six are
listed under *Blocking questions*, and they need an operator ruling, not more code.

## What is done

`[VERIFIED]` **The planted-violation harness** — `tests/completeness/registry.py` +
`test_every_checker_rejects_its_fixture`. Each of the seven checkers is driven by
subprocess against a deliberately broken tree under `tests/completeness/fixtures/` and must
exit non-zero. An unbuilt checker fails the test; it is never skipped.

`[VERIFIED]` **The registry cannot silently shrink** — `test_checker_registry_matches_manifest`
derives the expected checker set from the **frozen manifest** and asserts equality with the
fixture registry. Adding a checker to the manifest now forces a fixture to exist for it.

`[VERIFIED]` **Every checker has a negative control as well as a planted violation.**
§2.2 asks for proof a checker can fail. A checker that *only* fails is equally vacuous, so
each ships a clean tree it must accept:

| Checker | Planted | Clean control | Certifying tests |
|---|---|---|---|
| `check_manifest` | `fixtures/manifest` | `fixtures/manifest_clean` | 6 |
| `check_no_stubs` | `fixtures/stubs` | `fixtures/stubs_clean` | 7 |
| `check_spec_isolation` | `fixtures/spec_isolation` | `fixtures/spec_isolation_logs` | 6 |
| `check_import_graph` | `fixtures/imports` | `fixtures/imports_clean` | 7 |
| `check_attribution` | `fixtures/attribution` | `fixtures/attribution_clean` | 6 |
| `check_fixture_provenance` | `fixtures/fixture_provenance` | `fixtures/fixture_provenance_clean` | 5 |
| `check_substrate_purity` | `fixtures/substrate_purity` | `fixtures/substrate_purity_clean` | 5 |

`[VERIFIED]` **`tools/preflight.py`** — probes interpreter names per R-001; stops with the
verbatim remedy on `gh auth status` failure.

`[VERIFIED]` **`.github/workflows/ci.yml`** — OS matrix (ubuntu · windows · macos) under a
job named `checks`, plus a **separate non-matrix job named exactly `gate`** that aggregates
it. See *Surprises* 3: a matrix job called `gate` would have produced three contexts and
never the bare `gate` branch protection requires.

`[VERIFIED]` **R-004 discharged** — `.githooks/commit-msg` is portable (`grep -ivE`, POSIX,
no GNU-only `sed -i` or `/Id`), and `test_commit_msg_hook_strips_trailer` **executes** it.

`[VERIFIED]` **`src/lab/core/config.py`** (`load_config`, `get_secret`) and
**`src/lab/core/logging.py`** (`configure`) — layered config, environment-only secrets,
structured IST-stamped JSON logging with key-name redaction. 13 certifying tests.

`[VERIFIED]` **Gate stages green:** lint · types · tests · stubs · spec-isolation · imports ·
attribution · fixtures · substrate-purity. **88 tests pass.**

## Blocking questions for the operator

*Nothing may proceed past these.*

### Q-003 — `[OPEN]` **BLOCKING.** Six `call_site: required` rows have no honest caller.

This is the single reason the gate is red. **Do not resolve it by writing a caller.** The
Cold Start of Session 1 and operator ruling R-006 both anticipate exactly this and both say
to surface it.

| Row | Symbol | Why no honest caller exists |
|---|---|---|
| `P0.CHK.STUBS.PROTOCOL` | `is_protocol_member` | An AST **node predicate**. The gate cannot call it; it is invoked per-node inside the scan loop. |
| `P0.CHK.STUBS.DEFERRAL` | `resolve_deferral_marker` | Invoked per-stub during the scan. Not a stage. |
| `P0.CHK.SPEC.LOGS` | `LOG_PATHS` | A **constant**. Nothing outside its module has a reason to read it. |
| `P0.CONFIG` | `load_config` | P0 ships no CLI and no engine. |
| `P0.SECRETS` | `get_secret` | Same. |
| `P0.LOGGING` | `configure` | Same. |

**What was already tried and is NOT available:**

- **R-006's remedy — call it from `gate.py`'s real path — was applied wherever it honestly
  works.** `scan_authorship_metadata` (`P0.CHK.ATTRIB.SCOPE`) is now invoked in-process by
  `stage_attribution`, and that row **passes**. The three checker sub-symbols above are not
  stage-shaped, so the same move would be a manufactured caller.
- **A second test module would satisfy §6.3 as literally written** — the rule's search space
  is *"every AST in `src/` and `tools/`, and every test other than the row's
  `certifying_test`"*. **R-006 explicitly superseded that route** ("certifying tests prove
  behaviour; they do not supply call sites") and attached the standing instruction to stop
  and surface instead.
- **Manufacturing a caller for `lab.core.*` is forbidden in writing** by the Session 1 Cold
  Start: *"Do not manufacture a fake caller to satisfy it; if no honest call site exists,
  that is a finding to surface, not to paper over."*

**The finding.** Six of P0's `call_site: required` fields assert a relationship P0's own
design cannot produce. Three possible rulings, none of which the builder may pick:

1. **Amend the manifest** (§10.5 procedure): these six become `call_site: n/a`, exactly as
   A-001 did for `P0.BOOT.PREFLIGHT`, citing that their callers arrive in P1.
2. **Rule that a non-certifying test is a valid call site** for node-level predicates and
   constants, narrowing R-006 to stage-shaped symbols.
3. **Rule that P0 exits with this stage red**, and the rows tick when P1 supplies callers.

### Q-002 — `[OPEN]` **Non-blocking, but unresolvable by the builder.** `DIVERGENCES.md` defines no citable ID.

§7.1 permits `@pytest.mark.skip`/`xfail` *"unless it cites a `DIVERGENCES.md` ID"*.
`DIVERGENCES.md`'s Log table is keyed by Date/Gate/Fixture and **has no ID column**, so
there is no ID for a marker to cite. Inventing an ID scheme is a spec decision.

**Implemented meanwhile:** fail-closed — every skip/xfail is rejected, and the message says
why. This is behaviourally identical under *every* candidate ID scheme, because with no IDs
in the file no citation could resolve today. Inert in P0 (no skips exist). Only the
resolution half changes once the operator rules.

## What to do next

1. **Rule on Q-003.** The gate cannot go green without it, and no amount of building helps.
2. Q-002, at leisure.
3. Review D-004 and D-005 below.
4. Then Gate 0's remaining bootstrap items: the phase PR, and the `gate-0-scaffold` tag.

## What you must NOT do

- **Do not write a caller to make Q-003 go away.** That is the specific failure this project
  was arranged to refuse, and it is pre-refused in writing twice.
- **Do not weaken a checker to make a docstring pass.** §7.1 flagged three of this session's
  own docstrings; all three were reworded. *The annoyance is the mechanism.*
- **Do not touch a governance doc in a code PR.** §11.1.
- **Do not resolve an ambiguity in the deep dive.** Stop and surface it.

## Non-blocking — decided by the builder, needs review

| # | Decision | Tag |
|---|---|---|
| D-004 | **Gate-fixture declaration format.** §9.2 fixes the three provenance assertions but not the syntax carrying them, and `ACCEPTANCE.md` has no P4 fixture block yet. `check_fixture_provenance.py` reads a `<!-- gate_fixtures -->` marker followed by a fenced yaml list (`id`, `path`, `blob_sha`, `derivation`, optional `engine_path`). Zero declarations is P0's correct state and is reported explicitly, never passed in silence. P4 should confirm or amend. | `[BUILDER]` |
| D-005 | **Fixture injection seams.** Four checkers take their input from git (spec isolation, attribution, fixture provenance, substrate purity). Each reads a tracked, reviewable file (`FIXTURE_CHANGED_FILES`, `FIXTURE_GIT_LOG`, `FIXTURE_SUBSTRATE_DIFF`) **only when the tree has no `.git`** — so the seam is unreachable in the real repository, and dropping such a file beside the checker accomplishes nothing. Where the parse differs from git's output, the *judge* is shared and the git path is covered separately against the real repo. | `[BUILDER]` |
| D-006 | **`test_hooks_path_set_before_first_commit` asserts the invariant's shadow, not `git config`.** `core.hooksPath` is working-copy state with no trace in history, and every CI runner is a fresh clone with none — asserting it there asserts a property of the runner. The test instead asserts what survives cloning: the hook is **in the first commit**, at mode `100755`, and the first commit carries no trailers. A hook wired up afterwards cannot produce all three. | `[BUILDER]` |
| D-007 | **`ci.yml` splits matrix from context.** Job `checks` runs the OS matrix; job `gate` (no matrix, `needs: [checks]`, `if: always()`) aggregates and is the required context. It fails closed on any non-success result, because a skipped required check is not a passing one. | `[BUILDER]` |

---

# ═══ MACHINE STATE ═══

*Generated. Never narrated. Paste `python tools/gate.py` output verbatim.*

## Last `python tools/gate.py`

**Run at:** 2026-07-19 · **Commit:** `9d90afa` · **Exit code:** `1`

Piped verbatim. Nine of ten stages green; `manifest` red on six `call_site` rows and
nothing else. Every row exists — `rows open: 0`.

```
All checks passed!
Success: no issues found in 26 source files
........................................................................ [ 81%]
................                                                         [100%]
88 passed in 2.14s
    P0.CONFIG: lab.core.config.load_config is never referenced outside its own module and certifying test. Definition is not use (section 6.3)
    P0.SECRETS: lab.core.config.get_secret is never referenced outside its own module and certifying test. Definition is not use (section 6.3)
    P0.LOGGING: lab.core.logging.configure is never referenced outside its own module and certifying test. Definition is not use (section 6.3)
    P0.CHK.STUBS.PROTOCOL: tools.check_no_stubs.is_protocol_member is never referenced outside its own module and certifying test. Definition is not use (section 6.3)
    P0.CHK.STUBS.DEFERRAL: tools.check_no_stubs.resolve_deferral_marker is never referenced outside its own module and certifying test. Definition is not use (section 6.3)
    P0.CHK.SPEC.LOGS: tools.check_spec_isolation.LOG_PATHS is never referenced outside its own module and certifying test. Definition is not use (section 6.3)
check_no_stubs: clean over 13 file(s)
check_spec_isolation: spec and code both touched, permitted by the section 5.4 bootstrap exception -- no workflow on origin/main produces the 'gate' check yet. This exception closes itself the moment one does.
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
failures:                     6
--- manifest: FAILED

=== stubs ===
--- stubs: ok

=== spec-isolation ===
--- spec-isolation: ok

=== imports ===
--- imports: ok

=== attribution ===
    clean over 17 record(s)
--- attribution: ok

=== fixtures ===
--- fixtures: ok

=== substrate-purity ===
--- substrate-purity: ok

============================================================
GATE RED -- failed stages: manifest
```

**The six manifest failures, verbatim:**

```
P0.CONFIG: lab.core.config.load_config is never referenced outside its own module and certifying test. Definition is not use (section 6.3)
P0.SECRETS: lab.core.config.get_secret is never referenced outside its own module and certifying test. Definition is not use (section 6.3)
P0.LOGGING: lab.core.logging.configure is never referenced outside its own module and certifying test. Definition is not use (section 6.3)
P0.CHK.STUBS.PROTOCOL: tools.check_no_stubs.is_protocol_member is never referenced outside its own module and certifying test. Definition is not use (section 6.3)
P0.CHK.STUBS.DEFERRAL: tools.check_no_stubs.resolve_deferral_marker is never referenced outside its own module and certifying test. Definition is not use (section 6.3)
P0.CHK.SPEC.LOGS: tools.check_spec_isolation.LOG_PATHS is never referenced outside its own module and certifying test. Definition is not use (section 6.3)
```

**Read the tally, not the prose:** `rows built: 32`, `rows open: 0`, `spec sections without
a row: 0`, `rows without a spec section: 0`. The phase is *built*. It is not *cleared*,
because six rows assert a call-site relationship P0 cannot honestly supply — Q-003.

## Branch protection — `gh api` response, verbatim

*§3.3 / §12.1: CI cannot verify this without an admin-scoped token, and putting an admin-scoped
token in CI to check that admins are restricted is a circle not worth closing. So the evidence is
piped here, as output. Typed status is a claim; piped status is evidence.*

**Captured at:** commit `4e474adbec3b68d4ba47fee24cb347b164050ece`
**Command:** `gh api "repos/Vaunox/lab/branches/main/protection"`

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

**Run at:** 2026-07-19 · **Commit:** `9d90afa` · **Command:** `python tools/check_manifest.py`

```
phase:                        P0
rows total:                   32
rows built:                   32
rows open:                    0
spec sections without a row:  0
rows without a spec section:  0
failures:                     6
```

**The closed loop closes in both directions** — this is the self-bootstrap (§2.1) working:
`check_manifest.py` validates P0's own manifest, and every non-exempt section has a row while
every row cites a real section.

**66 failures is the honest red.** 19 rows are unbuilt and say so. Nothing is stubbed.

> **`rows total` is 32, not 33.** An earlier hand-count in this file and in the session plan said
> 33. §12.1 forbids hand-counting the tally for exactly this reason, and the prohibition earned
> itself inside one session. Every number in this block is piped from the tool.

## Gates

| Check | Status |
|---|---|
| lint (`ruff`) | ☑ passing |
| format (`black`) | ☑ passing |
| types (`mypy --strict`) | ☒ `tests/` does not exist |
| tests | ☒ no test exists |
| `tools/gate.py` | ☑ built · fails closed on zero checkers `[ASSERTED]` |
| `check_manifest.py` | ☑ built · validates P0's own manifest `[ASSERTED]` |
| `check_no_stubs.py` | ☒ not written |
| `check_spec_isolation.py` | ☒ not written |
| `check_import_graph.py` | ☒ not written |
| `check_fixture_provenance.py` | ☒ not written |
| `check_substrate_purity.py` | ☒ not written |
| `check_attribution.py` | ☒ not written |
| planted violations (7 required) | ☒ **none exist — §2.2, the highest-priority remaining work** |
| mutation ≥ 90% (substrate) | — no substrate code in P0 |
| `DEFERRALS.md` empty | ☑ (empty — and it stays empty; nothing was deferred) |

**Not one certifying test exists.** Everything marked ☑ above is `[ASSERTED]`, observed by running
it, never `[VERIFIED]`. Per §2.2 a checker with no proof it can fail is worse than no checker,
because it manufactures confidence — and right now both built checkers are in exactly that state.

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

---

## Session 1 — 2026-07-18 — Phase P0

### Built
- `P0.BOOT.PREFLIGHT` — **partial.** §3.0 preflight was *executed* and passed, but
  `tools/preflight.py` (the manifest row's artifact) is **not written**. The row is **not ticked.**
  Running the checks by hand is not the same as shipping the script the manifest requires.
- `P0.BOOT.GIT` — `[ASSERTED]` `.git` exists; `core.hooksPath=.githooks` set before commit `4e474ad`.
  **No test yet** — `test_hooks_path_set_before_first_commit` does not exist. Do not trust this row.
- `P0.LICENSE` / `P0.NOTICE` — `[ASSERTED]` files exist and are in commit #1. Certifying tests
  (`test_license_is_apache_2`, `test_notice_present`) do not exist yet.
- `P0.HOOKS` — `[ASSERTED]` `.githooks/commit-msg` committed at mode 100755, and manually
  smoke-tested: fed a message carrying `Co-Authored-By:` and `Generated with`, both lines were
  stripped. **This is not the certifying test** (`test_commit_msg_hook_strips_trailer`), which
  does not exist.

**Nothing above is `[VERIFIED]`.** Not one certifying test exists, because `tools/` and `tests/`
have not been started. The gate is red and there is no gate to run it with.

### Tried and rejected
- Approach: fetch the Apache-2.0 text with `gh api /licenses/apache-2.0 --jq .body` piped through
  PowerShell `Out-File -NoNewline`.
  Failed because: PowerShell splits native-command stdout into a **`string[]` of lines**, so
  `$body.Length` reported `202` (the line count, read at first glance as a byte count) and
  `-NoNewline` concatenated all 202 elements into a **single 11156-byte line**. A licence file that
  is textually complete but structurally destroyed. Caught by re-measuring the written file rather
  than trusting the write.
  → not a dead end worth a DE- entry (tooling misuse, not a design finding), but see Surprises.
- Approach: measure CRLF contamination with `grep -c $'\r' <file>` inside the Bash tool.
  Failed because: `$'...'` ANSI-C quoting does not survive the tool's `eval` layer, so the pattern
  degraded to the **empty string, which matches every line**. Every file reported `CR = its own
  line count`, which reads exactly like "this file is entirely CRLF." It produced a *false positive
  on every file simultaneously* — the shape of a broken instrument, not a broken repo, and that
  shape is the thing to recognise. Re-measured by counting raw `0x0D` bytes in PowerShell: all
  files were pure LF and always had been.

### Decisions
- `[BUILDER]` D-001 `.gitattributes` — see *Non-blocking* table.
- `[BUILDER]` D-002 `NOTICE` copyright holder; `LICENSE` left verbatim — see *Non-blocking* table.
- `[BUILDER]` D-003 commit #1 message verbatim per §3.1 — see *Non-blocking* table.
- `[BUILDER]` Did **not** work around the §3.2 permission denial. `git remote add` + `git push`, or
  `gh api user/repos`, would both have achieved the same effect and both would have defeated the
  point of the gate. A builder that routes around an external permission check is the same builder
  that routes around a failing gate; the reflex is the thing being refused, not the command.

### Uncertain
*What the next session should not inherit as confidence.*
- `.githooks/commit-msg` was smoke-tested **under Git Bash on Windows only**. Its `sed -i.bak -E
  '/…/Id'` relies on the GNU `sed` `I` (case-insensitive address) extension. **macOS ships BSD
  `sed`, which does not support it** — the hook may fail or silently no-op on macOS. §5.2 puts
  `macos-latest` in the CI matrix, so this will surface there. Not yet investigated; do not assume
  the hook is portable.
- The `[VERIFIED]` tags in *What is done* rest on piped command output, not on tests. They are
  verified as *observations*, not as *certified rows*. No manifest row is ticked.

### Blocked
- **Q-001** — §3.2 remote creation, on the operator, since 2026-07-18. Blocks all of P0.

### Surprises
*Each is either a spec bug (amend it) or a dead end (log it). Neither is "just proceed."*
1. **The harness has a permission gate the governance did not model.** §3.0 and `SESSION_PROMPT.md`
   both state that `gh auth login` is *the only* operator action in the entire program. That is now
   false: the classifier's denial of `gh repo create --public` is a second one. The claim is true of
   the Lab and false of the environment the Lab runs in. **Candidate spec amendment to §3.0** — the
   builder may not make it (§11.1, and a code session may not edit a deep dive), so it is recorded
   here for the operator.
2. **`python3` does not exist on this machine**; `python` is 3.11.9. §3.0's preflight block calls
   `python3 --version` literally. The *requirement* (>= 3.11) is met, but `tools/preflight.py` must
   probe interpreter names rather than assume `python3`, or preflight will fail on the operator's
   own primary platform — the platform §5.1 chose `tools/gate.py` over `make` to accommodate.
   Worth noting the shape: the spec chose Python-not-`make` *for* Windows, then wrote `python3`.
3. **The Cold Start block cites `§3.1 / §4.6` for `LICENSE`/`NOTICE`. `P0_scaffold.md` §4 ends at
   §4.5 — there is no §4.6.** The substantive instruction is unambiguous and corroborated by §5.3
   ("`LICENSE` and `NOTICE` land here, not at P8"), so this was followed rather than treated as a
   blocking ambiguity: it is a dangling cross-reference in a *log*, not a contradiction in a *spec*.
   Flagged so it is corrected rather than propagated.
4. **`ACCEPTANCE.md` has no P0 section** — it opens at P1. P0's exit criteria live only in
   `P0_scaffold.md` §12. This appears deliberate (P0 predates the acceptance regime it installs),
   but `MASTER_BLUEPRINT.md` Part IV calls `ACCEPTANCE.md` the holder of "the binding exit criteria
   for **every** phase." Not blocking; noted so P0's gate is read from §12 and nowhere else.
5. **§5.4's bootstrap exception may be self-resolving.** It permits the first PR to mix spec and
   code tiers. But governance landed on `main` in commit #1, so the eventual
   `origin/main...phase/p0-scaffold` diff will contain `CODE` + `LOGS` and **no `SPEC` at all** —
   meaning `check_spec_isolation.py` should pass on the first PR without needing an exception.
   `[ASSERTED]`, untested; the checker does not exist. If it holds, the exception is a safety net
   that never has to deploy, which is the good outcome. **Do not use this as a reason to weaken the
   checker** — verify it empirically once the checker exists.

### tools/gate.py
```
(not built — P0.GATE not reached; blocked at §3.2 before P0 proper opened)
```

---

## Session 1 (continued) — 2026-07-18 — Phase P0

*Bootstrap unblocked by the operator; P0 proper opened.*

### Built
- **Spec amendments A-001 / A-002 / A-003** — `[OPERATOR]`-ruled, §13 log entries, commit `e435a15`.
- `P0.PYPROJECT`, `P0.PRECOMMIT` — `[ASSERTED]`, certifying tests do not exist.
- `tools/check_manifest.py` with `assert_deep_dive_frozen`, `assert_closed_loop`,
  `assert_called_outside_own_module` — `[ASSERTED]`. It runs and validates P0's own manifest, but
  **not one of its certifying tests exists**, so nothing about it is `[VERIFIED]`.

### Tried and rejected
- Approach: while applying A-002, also amending §6.2 to record that "executable" is read from the
  git index rather than `os.access`.
  Failed because: **that is R3, an implementation rule the operator explicitly settled as needing no
  ruling — not one of the three approved amendments.** Editing the frozen spec beyond what was
  approved is precisely what §11.1 forbids, and the builder had just finished arguing that the gate
  must be out of the builder's reach. Reverted within the same edit sequence. The rule still holds;
  it lives in the code and in this log, where implementation decisions belong.

### Decisions
- `[BUILDER]` **Call sites for the three `check_manifest` sub-symbols** (`assert_closed_loop`,
  `assert_called_outside_own_module`, `assert_deep_dive_frozen`) will come from a test module that
  is **not** any row's `certifying_test`. §6.3 defines the search space as *"every AST in `src/` and
  `tools/`, and every test other than the row's `certifying_test`"*, so this satisfies the rule as
  written, and failure case 8 (*"only used in its own test"*) is the thing being avoided. Flagged
  because it satisfies the letter more comfortably than the spirit: DoD-(a) is about primitives
  nothing calls, and these three are genuinely called — by `check()`, inside their own module.
  If the operator prefers a non-test caller, `gate.py` can call them directly instead.

### Uncertain
- `check_manifest.py` has **no test coverage at all.** Its 66 reported failures look right and the
  closed-loop result was independently demonstrated, but a checker with no certifying test is
  exactly what §2.2 warns about. Do not trust it until `test_checkers.py` exists.
- `_find_script_invocation` and `check_infra` have never been exercised against a *passing* case —
  only against absent artifacts. The negative control (clean tree → exit 0) is unwritten.

### Surprises
6. **The hand-counted manifest tally was wrong inside one session.** This file and the session plan
   both said 33 rows; `check_manifest.py` reports **32**. §12.1 forbids hand-counting for exactly
   this reason, and the prohibition proved itself before the tool that enforces it was finished.
7. **Exempt-heading matching must be by prefix, and this was demonstrated rather than argued.**
   Swapping `is_exempt` for exact-title equality and re-running `assert_closed_loop` leaves
   **§11 (`MANIFEST — frozen`) and §12 (`GATE 0 — exit`) uncovered**, so P0 fails its own
   completeness gate. The operator's confirmation had restated this rule inverted ("exact-title
   heading equality, not prefix match"); read as a transcription slip, since the same sentence
   endorsed the call as correct. Recorded as evidence so it is not re-litigated from memory.

### tools/gate.py
Piped verbatim into *MACHINE STATE* above. `GATE RED`, exit 1, nine of ten stages failing —
all of them unbuilt work, none a defect.

### Addendum — operator ruling R-006

- `[OPERATOR]` **R-006 — the three `check_manifest` sub-symbols are wired into `gate.py`'s real
  call path**, not referenced from a non-certifying test. This **supersedes the `[BUILDER]`
  decision recorded earlier this session**, which proposed the test-reference route and flagged it
  as satisfying §6.3 "more in letter than spirit." The ruling: §9 DoD-(a) is about a genuine call
  site, and the honest invoker of a manifest sub-check is the gate that runs it. **Certifying tests
  prove behaviour; they do not supply call sites.** Implemented — `stage_manifest` calls
  `assert_deep_dive_frozen`, `assert_called_outside_own_module`, and `assert_closed_loop` directly,
  and the four `P0.CHK.MANIFEST*` rows now satisfy `call_site: required` through the gate.
  Standing instruction attached: if a future sub-check has no honest place on the gate's real path,
  **stop and surface it** — that is a signal the manifest decomposition is wrong, not something to
  route around.

  *Side benefit, not the reason:* running them as named stages means a manifest failure says which
  of the four broke, instead of an opaque "manifest failed".

### Addendum — what the next session must do first

**`test_every_checker_rejects_its_fixture` and the seven planted violations.** §2.2, and the
operator has named it the top priority twice. Two checkers now exist and **neither has any proof it
can fail.** Build the fixture-and-rejection harness before writing a third checker, so the pattern
is established once and every later checker inherits it.

The `tests/` tree does not exist at all, which is why `mypy` and `pytest` both fail. Creating it
turns three red stages green at once.

---

## Session 2 — 2026-07-19 — Phase P0

*Operator ruling R-007 followed in order: harness first, retrofit second, remaining checkers
third, each landing with its proof-of-failure.*

### Built

**The harness (R-007 step 1).**
- `tests/completeness/registry.py`, `test_every_checker_rejects_its_fixture` —
  `[VERIFIED]` all seven checkers rejected their planted violations.
- `test_checker_registry_matches_manifest` — `[VERIFIED]`. The registry is derived from the
  frozen manifest, so it cannot shrink to "the checkers that happen to exist".

**The retrofit (R-007 step 2).** `check_manifest` and `gate` were `[ASSERTED]` at session
start with no proof either could fail. Both are now `[VERIFIED]`:
- `test_manifest_rejects_missing_row`, `..._uncalled_symbol`, `..._unspecified_row`,
  `..._refuses_unfrozen_deep_dive`, plus `test_manifest_accepts_clean_tree` — which closes
  the Session 1 uncertainty that `check_infra`/`check_existence` had never been exercised
  against a *passing* tree.
- `test_gate_fails_closed_on_zero_checkers` and five more.

**The five remaining checkers (R-007 step 3),** each with planted violation, negative
control, and certifying tests: `check_no_stubs`, `check_spec_isolation`,
`check_import_graph`, `check_attribution`, `check_fixture_provenance`,
`check_substrate_purity`.

**The rest of the manifest.** `tools/preflight.py`, `.github/workflows/ci.yml`,
`tools/import_rules.yaml`, `src/lab/core/config.py`, `src/lab/core/logging.py`,
`tests/completeness/test_bootstrap.py`, `test_ci_config.py`, `test_scaffold.py`,
`tests/unit/core/`. R-004 discharged.

**Result: `rows built: 32`, `rows open: 0`, 88 tests, nine of ten gate stages green.**

### Tried and rejected

- Approach: word-boundary matching for the kill gate's engine vocabulary, on the reasoning
  that `\bdaily\b` avoids firing inside unrelated identifiers.
  Failed because: it **silently missed `square_off_at`** in the planted fixture — `\b`
  requires a non-word character after `off`, and `_` is a word character. A suffixed
  identifier is precisely how this vocabulary actually arrives in a substrate. Caught only
  because the fixture contained the realistic shape rather than the bare term.
  → DE-001. Now substring + case-insensitive, with `MIS` alone matched case-sensitively as
  a whole word so it does not fire on "mismatch"/"permission"/"dismiss".

- Approach: `test_commit_msg_hook_uses_no_gnu_only_sed_extension` grepping the hook file for
  `sed -i` and `/Id`.
  Failed because: **the hook's own comment block explains the defect it replaced**, quoting
  both strings verbatim. The test flagged the explanation as the offence. Same shape as
  DE-000l — scanning text when the subject is behaviour. → DE-002. Comments are stripped
  first.

- Approach: `test_hooks_path_set_before_first_commit` asserting `git config core.hooksPath`.
  Failed because: local config is working-copy state with no trace in history, and **every
  CI runner is a fresh clone that has none** — the test would have gone red on all three
  matrix legs while the invariant it names was perfectly intact. → DE-003, and D-006.

- Approach: `assert name != "python3" or True` in the preflight interpreter test.
  Failed because: it is a tautology and asserts nothing. **Ruff caught it, not review.**
  Rewritten to drive every named candidate to failure through the injected runner and assert
  the `sys.executable` fallback resolves — which is also environment-independent, where the
  first version depended on whether `python3` happened to be installed.

### Decisions

- `[BUILDER]` D-004 gate-fixture declaration format — see *Non-blocking*.
- `[BUILDER]` D-005 fixture injection seams, unreachable wherever a `.git` exists.
- `[BUILDER]` D-006 hooks-path test asserts the invariant's shadow.
- `[BUILDER]` D-007 `ci.yml` splits the matrix job from the `gate` context job.
- `[BUILDER]` **Uniform `--root` CLI across all seven checkers**, so one test can drive them
  all. `check_manifest`'s `--repo` was renamed; no spec names the flag.
- `[BUILDER]` **`check_no_stubs` assembles its own banned words at import** (`_assemble`).
  The checker scans `tools/` and lives in `tools/`; spelling `TODO` as a literal would make
  it violate its own rule, and the obvious escape — excluding itself — is a hole in the one
  place a hole must not be.
- `[BUILDER]` **R-006 applied where it honestly works, and only there.**
  `scan_authorship_metadata` is now called by `gate.stage_attribution` on the real path, and
  that row passes. The three sub-symbols that are not stage-shaped were **not** given
  manufactured callers. See Q-003.

### Uncertain

*What the next session should not inherit as confidence.*

- **`ci.yml` has never run.** No workflow has executed on any runner — the repo has no PR
  yet. The `gate` context name, the matrix, and the aggregate job are asserted by
  `test_ci_config.py` **against the YAML**, not against a GitHub run. The first PR is the
  first real test, and D-007's reasoning about matrix context naming is the thing most
  likely to be wrong in a way only GitHub can reveal.
- **The hook is executed on Windows only.** `test_commit_msg_hook_strips_trailer` genuinely
  runs the hook, which is what R-004 asked for — but so far only under Git Bash on this
  machine. The macOS/BSD leg that motivated R-004 is still unexercised until CI runs.
- **`check_attribution`'s tag scanning has never seen a tag.** No tag exists. The commit
  path is covered over the full real history; the tagger path is code that has run against
  an empty input.
- **`fixture_predates_engine` is proven on a synthetic two-commit repository**, not on a
  real fixture-then-engine sequence, because no gate fixtures exist until P4.

### Blocked

- **Q-003** — six `call_site: required` rows with no honest caller, on the operator, since
  2026-07-19. **Blocks Gate 0.** This is the only reason the gate is red.

### Surprises

*Each is either a spec bug (amend it) or a dead end (log it). Neither is "just proceed."*

8. **Session 1's Surprise 5 is falsified.** It predicted the §5.4 bootstrap exception would
   never need to deploy, reasoning that the phase branch would carry `CODE` + `LOGS` and no
   `SPEC`. But amendments A-001–A-003 edited `docs/deep_dives/P0_scaffold.md` **on this
   branch**, so `origin/main...HEAD` carries SPEC and CODE together and the exception is
   load-bearing right now. `test_spec_isolation_bootstrap_exception_is_open_on_this_repo`
   pins the fact; `..._self_closes` proves the same diff is denied once `origin/main`
   produces the `gate` check. The exception is narrow and self-closing, as designed — but it
   is *deploying*, which Session 1 believed it would not.

9. **The `gate` status-check context is a trap with a green face.** GitHub names matrix
   checks `job (os)`, so a single matrix job named `gate` produces
   `gate (ubuntu-latest)` and friends — and **never a context called `gate`**. Branch
   protection requires the literal string, so `main` would have been permanently unmergeable
   behind a fully green CI run with nothing in the logs to explain it. Resolved by D-007.
   The HANDOFF warned about the name; it did not warn that a matrix changes it.

10. **The no-stub checker flagged three of this session's own docstrings**, including
    *"Later layers override earlier ones"* — where "Later" is an ordinal, not a deferral.
    All three were reworded rather than the rule loosened. §7.1 says the bluntness *is* the
    mechanism, and the first instinct on being flagged was to add an exception, which is
    exactly the instinct the rule exists to overrule.

11. **`shutil.which("bash")` returns `None` on Windows even where bash exists.** Git for
    Windows ships `bash.exe` in `Git/bin/` but only puts `Git/cmd/` on PATH. Taken at face
    value this would have turned the one test R-004 requires to *execute* the hook into a
    test that silently never runs on the operator's primary platform.

### tools/gate.py

Piped verbatim into *MACHINE STATE* above. `GATE RED`, exit 1, one failing stage, six
failures, all Q-003.
