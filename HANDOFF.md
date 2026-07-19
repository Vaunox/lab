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

**GATE GREEN. All ten stages pass. 32/32 manifest rows, 0 open, 0 failures, 90 tests.**
All seven checkers are built, each with a planted violation **and** a negative control, and
`test_every_checker_rejects_its_fixture` passes over all seven. Q-003 was ruled on by the
operator mid-session and resolved as amendment **A-004** (see *Operator rulings*). Nothing is
stubbed, nothing was skipped, and no call site was manufactured.

**P0 is code-complete, its gate is green, and CI is green on all three platforms.**
[PR #1](https://github.com/Vaunox/lab/pull/1) is open, `mergeStateStatus: CLEAN`, and
**awaiting operator review — the merge was deliberately not taken.** The `gate-0-scaffold`
tag is cut on merge, not before.

The first CI run caught two real defects that the local gate could not see, both
environment-shaped. See the *first CI run* addendum at the end of this file, and DE-004/DE-005.

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

| # | Question | Blocks |
|---|---|---|
| — | None open. | — |

**Q-003 — RESOLVED 2026-07-19** by operator ruling R-008, applied as spec amendment A-004.
Six `call_site: required` rows asserted a relationship P0's design cannot honestly produce;
all six are now `call_site: n/a`, each tested against the guardrail first. Full reasoning in
`docs/deep_dives/P0_scaffold.md` §13. **The builder did not manufacture a caller while the
question stood** — the gate was left red for the operator rather than made green by the one
move the phase exists to refuse.

**Q-002 — DEFERRED 2026-07-19** by the same ruling. `DIVERGENCES.md` still defines no citable
ID, and §7.1's skip exemption still has nothing to cite. Fail-closed stays; it binds on
nothing in P0 (zero skips exist) and is behaviourally identical under every candidate scheme.
**The ID scheme is decided by the first phase that actually needs a divergence-citing skip
(P4/P5), and is not to be built speculatively now.**

## What to do next

1. **The phase PR is open on `phase/p0-scaffold` and awaits operator review.** Do not merge
   it yourself. §5.4: do not admin-bypass, and do not temporarily un-require the `gate`
   check — doing either on the *first* merge sets the precedent for every merge after it.
2. **The first CI run is the first real test of `ci.yml`.** No workflow has ever executed.
   If the `gate` context does not appear exactly as named, D-007's reasoning about matrix
   context naming is what to re-read first.
3. On merge: tag `gate-0-scaffold`. §9.3 — the tag commit contains the complete deliverables.
4. Then P1 opens against `docs/deep_dives/P1_substrate.md`. Its first act should be to give
   `load_config`, `get_secret` and `configure` their real consumers, which is what A-004
   recorded as arriving in P1.

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

**Run at:** 2026-07-19 · **Commit:** `824c1ef` · **Branch:** merged `main` + the durable-test fix
· **Exit code:** `0`

Piped verbatim. This is the run the `gate-0-scaffold` tag is cut against: a fresh checkout of
the tag reports **GATE GREEN**, which is the whole point of tagging a deliverable snapshot.

```
All checks passed!
Success: no issues found in 26 source files
........................................................................ [ 77%]
.....................                                                    [100%]
93 passed in 4.32s
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
    clean over 43 record(s)
--- attribution: ok

=== fixtures ===
--- fixtures: ok

=== substrate-purity ===
--- substrate-purity: ok

============================================================
GATE GREEN -- 10 stages passed
```

**Why this run and not the one on PR #1's head.** Merging PR #1 put `ci.yml` on `main`, which
**closed the section 5.4 bootstrap exception** — exactly as designed, and proved in advance by
`test_spec_isolation_bootstrap_exception_self_closes`. Two tests had asserted the exception was
*currently open on this repository*, and the closing falsified them, so the merge result
reported `GATE RED -- failed stages: tests` on a fresh checkout. The deliverables were complete;
the tests had encoded a precondition that expired at the moment it was met. Rewritten against
synthetic repositories, preserving both halves of the proof — that the exception **arms** under
the bootstrap precondition and that it **self-closes** once `main` carries the gate. See DE-006.

**Section 11.1 now binds absolutely.** PR #1 was the last PR permitted to carry spec and code
together, and `test_spec_isolation_exception_is_closed_on_this_repository` asserts the exception
is spent.

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

**Run at:** 2026-07-19 · **Commit:** `e77f098` · **Command:** `python tools/check_manifest.py`

```
phase:                        P0
rows total:                   32
rows built:                   32
rows open:                    0
spec sections without a row:  0
rows without a spec section:  0
failures:                     0
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

### Addendum — operator ruling R-008, and amendment A-004

- `[OPERATOR]` **R-008 — Q-003 resolves as a §10.5 amendment, same class as A-001**, riding
  the P0 phase PR (§5.4 / §11.3, the one PR permitted to carry spec and code together).

  **Rejected by the operator:** exiting P0 with the stage red (unmergeable without an
  admin-bypass or un-requiring the gate, both forbidden, and it would need an exception carved
  into *"a branch may be partial, `main` may not"*); and treating a non-certifying test as a
  call site as the sole remedy (addresses only three of the six, and reopens the
  test-manufactures-a-caller pattern R-006 was ruled against).

  **Adopted, refined:** for each of the six, prefer an honest design-intended call site if one
  genuinely exists; reclassify `required` → `n/a` only where none does. With the guardrail:
  **a genuine orphan — built but never wired, behaviour not actually certified — must NOT be
  reclassified.** That is a real defect, to be fixed or surfaced.

- **Applied.** All six were tested against the guardrail and none is an orphan. The three
  checker sub-symbols are invoked on the real path every run (`check_no_stubs.py:245`, `:261`,
  `check_spec_isolation.py:109`) and are certified. **`gate.py` was checked for an honest
  logging call site, as the ruling required, and rejected it**: importing `lab` into the gate
  means a syntax error in `lab/core/logging.py` crashes the gate instead of being *reported*
  by it — the judge losing the ability to report on the defendant. `load_config` and
  `get_secret` have no P0 consumer; none was manufactured.

- **Second amendment in the same ruling:** `check_manifest` now validates `call_site` against
  a closed set. It previously ran the assertion only on the exact string `required` and
  **silently ignored every other value**, so a typo disabled the check with no signal — the
  vacuous pass §6.2 closes for `kind`, left open one field over. Pinned by
  `test_manifest_rejects_an_unrecognised_call_site` and
  `test_manifest_call_site_registry_matches_the_frozen_manifest`.

- **Result: `GATE GREEN -- 10 stages passed`, exit 0, 90 tests.** Piped verbatim above.

- `[OPERATOR]` **Push authorized** for `phase/p0-scaffold`, after the amendment landed and the
  gate went green, so the phase PR opens green rather than red. **Merge is not authorized** —
  the PR opens and stops for operator review.

### Addendum — the first CI run, and what it caught

**`.github/workflows/ci.yml` has now executed.** Three runs were needed to go green, and the
two failures are the most valuable evidence this session produced, because **both were
invisible locally and both were environment-shaped.**

**Run 1 — `GATE RED` on all three legs.** `P0.BOOT.GIT: core.hooksPath is '', expected
'.githooks'`. This is **DE-003 one level over**: the finding had been diagnosed, written up,
and fixed in `test_hooks_path_set_before_first_commit` earlier in the same session, and the
identical assertion in `check_manifest.check_infra` was left standing — because the dead end
was filed against *the test it was noticed in* rather than against *the invariant*. The local
gate was green on the same commit, because a developer machine is exactly the environment
where the wrong assertion holds. → **DE-004**, whose lesson is the general one: when a dead
end is found, grep for every other site with the same shape before closing it.

**Run 2 — `checks (windows-latest)` passed, both POSIX legs failed.**
`git commit -am` restages tracked files from the working tree and reverts a mode that
`git update-index --chmod=+x` had only staged. Windows cannot reproduce it, because git does
not read filesystem executable bits there. → **DE-005**.

**Run 3 — all four checks green.**

```
checks (macos-latest)     pass
checks (ubuntu-latest)    pass
checks (windows-latest)   pass
gate                      pass
```

**D-007 is validated in production, not merely against the YAML.** The aggregate job produced
a status context named exactly `gate` — the literal string branch protection requires — and
on runs 1 and 2 it **failed closed** rather than being skipped, which is the property the
`if: always()` plus explicit success test was written for. A matrix job named `gate` would
have produced `gate (ubuntu-latest)` and friends and never the bare context, leaving `main`
permanently unmergeable behind a green run.

**`gh pr view 1 --json mergeStateStatus` reports `CLEAN`.** The PR is mergeable and has
**not** been merged: the operator authorized the push and the PR, and reserved the merge.

**The OS matrix paid for itself on its first run.** Section 5.2 justifies it by the ledger
lock, which does not exist yet — and it still caught two real defects that no amount of local
running would have surfaced. Both were of the same class the matrix exists to catch: code
that is correct on the machine it was written on.
