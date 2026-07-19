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
**Last commit:** `4e474ad` — *chore: governance, blueprint, and deep dives for P0 and P1*
**Session:** 1 — bootstrap §3.0–§3.4 **complete**; P0 proper in progress.

## What is done

`[VERIFIED]` **§3.0 Preflight** — passed, no operator action required:

| Check | Result |
|---|---|
| `git --version` | 2.54.0.windows.1 |
| `gh --version` | 2.94.0 |
| `gh auth status` | logged in, account `Vaunox`, scopes `gist, read:org, repo, workflow` |
| Python `>= 3.11` | 3.11.9 (as `python`; `python3` is not a Windows alias — see Surprises) |
| Remote `lab` free? | yes — `gh repo view Vaunox/lab` → *Could not resolve to a Repository* (§10 case 18 not triggered) |

`[VERIFIED]` **§3.1 Local repository** — `git init -b main`; `core.hooksPath=.githooks` set
**before** the first commit; commit `4e474ad`, 20 files.

- `CLAUDE.md` and `.claude/` are **absent from the commit** (gitignored, §4.4) — verified against
  `git diff --cached --name-only` *before* committing, not after.
- `LICENSE` (Apache-2.0, canonical text, 202 lines / 11358 bytes) and `NOTICE` are **in commit #1**,
  per the Cold Start requirement and §5.3.
- Authorship metadata clean (§4.3): author and committer both `Vaunox <nevesia26@gmail.com>`;
  `%(trailers)` empty; no `Co-Authored-By`, no attribution of any kind.
- `.githooks/commit-msg` committed mode **100755** (§6.2 requires `kind: script` to be executable).

`[VERIFIED]` **§3.2 Remote** — `gh repo create lab --public --source=. --remote=origin --push`.
`origin` = https://github.com/Vaunox/lab, `main` pushed and tracking `origin/main`.

`[VERIFIED]` **§3.3 Protection** — applied and read back. Full `gh api` response is piped verbatim
into *MACHINE STATE* below, with a field-by-field table against §12's bootstrap gate. All six
required settings hold, including `enforce_admins.enabled: true`.

`[VERIFIED]` **§3.4 Phase branch** — `phase/p0-scaffold` created and checked out. `main` has not
been committed to since the bootstrap commit and will not be again.

## What to do next

**Bootstrap is done. P0 proper is open. Build the checkers before the code they police (§2).**

Nothing in `tools/`, `tests/`, or `src/` exists yet. **Not one manifest row is ticked.** Build in
the manifest's own order, which is bottom-up for a reason (§7.3: build in dependency order and the
stub escape hatch is never needed):

1. `tools/preflight.py` (P0.BOOT.PREFLIGHT) — per operator ruling R-001, **probe** interpreter
   names; do not hardcode `python3`.
2. `pyproject.toml`, `.pre-commit-config.yaml` (P0.PYPROJECT, P0.PRECOMMIT) — mypy **strict**.
3. `tools/gate.py` (P0.GATE) — **fails closed on zero registered checkers.** *"Nothing to check"*
   is not *"all checks passed."* During P0 that distinction is the whole difference between a
   bootstrap and a bypass.
4. The six checkers + their sub-symbol rows (P0.CHK.*) — 13 rows.
5. `tests/completeness/fixtures/` — the planted violations (P0.FIXTURES.VIOLATIONS), and
   `test_every_checker_rejects_its_fixture`. **§2.2: a checker that always passes is worse than no
   checker, because it manufactures confidence.** If only one thing in this phase is built
   correctly, build this.
6. `.github/workflows/ci.yml` (P0.REMOTE, P0.CI.MATRIX) — OS matrix; the `gate` context is already
   required by branch protection and **nothing produces it yet**, so `main` is unmergeable until
   this lands.
7. `src/lab/core/config.py`, `logging.py` (P0.CONFIG, P0.SECRETS, P0.LOGGING) — the only `lab/`
   code in P0. All three are `call_site: required`; see *Open problems* below.
8. Hook portability fix + executing test (operator ruling R-004).

## Open problems the next session must not discover the hard way

- **`call_site: required` on P0.CONFIG / P0.SECRETS / P0.LOGGING.** §6.3 demands each symbol be
  referenced outside its own defining module *and* outside its own certifying test. P0 ships no CLI
  and no engine, so there is no natural caller yet. This is a real design constraint, not a
  formality — DoD-(a) exists because *"a primitive that exists but nothing calls is not done."*
  Do **not** manufacture a fake caller to satisfy it; if no honest call site exists, that is a
  finding to surface, not to paper over.
- **The `gate` status-check context must be named exactly `gate`** in `ci.yml` — branch protection
  already requires that literal string. A job named anything else leaves `main` permanently
  unmergeable, and the failure mode is a green CI run that still blocks the merge.

## Public from commit #1 — what this forces

The repo is **public from the first commit**, by operator decision. There is no
private staging window. Two consequences the builder must respect from the start,
not retrofit:

- **Attribution must be clean in the *first* commit**, not cleaned up later. The
  `commit-msg` hook and `.claude/settings.json` are wired in §3.1 *before* that commit
  precisely so the public history is clean from row zero. A public history cannot be
  un-authored without a full rewrite.
- **`LICENSE` (Apache-2.0) and `NOTICE` are committed in the first commit** (§3.1 / §5.3),
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
| — | None open. | — |

**Q-001 — RESOLVED 2026-07-18.** Harness permission for §3.2 granted by the operator; remote
created. The builder did **not** route around the denial while it stood (no `git remote add` +
`git push`, no `gh api` equivalent) — publishing a public repository under the operator's identity
is exactly the class of action such a gate exists for.

## Operator rulings — this session

*Binding. `[OPERATOR]` tags are not promotable from `[BUILDER]` suggestions; these were issued
directly.*

| # | Ruling |
|---|---|
| **R-001** | `[OPERATOR]` **Interpreter name.** `tools/preflight.py` **probes** interpreter names (`python`, `python3`, `sys.executable`) and asserts ≥ 3.11. Do **not** hardcode `python3`. §3.0's `python3` is *illustrative of intent* (verify Python ≥ 3.11 is present), not a literal command. **No amendment to the frozen deep dive.** Rationale: §5.1 chose Python-over-`make` for Windows, and Windows is the operator's primary platform — preflight must not fail on it. |
| **R-002** | `[OPERATOR]` **Harness classifier is an environment artifact, not a property of the Lab.** Do **not** amend §3.0, and the *"only operator action is `gh auth login`"* claim **stands** — it is a claim about the Lab's design, not about the harness it runs under. Recorded here (a log), never in frozen governance. Supersedes Session 1 Surprise 1, which proposed a §3.0 amendment. |
| **R-003** | Dangling `§4.6` in the Cold Start was a typo in a log. Corrected in place to `§3.1 / §5.3`. No ruling required. |
| **R-004** | `[OPERATOR]` **commit-msg hook portability — must-fix before Gate 0, not blocking the bootstrap.** The `/Id` case-insensitivity address modifier is GNU-only; BSD `sed` on `macos-latest` rejects it. Make the hook portable across GNU **and** BSD `sed`, and make `test_commit_msg_hook_strips_trailer` **execute** the hook — feed it a commit message carrying a trailer, run it, assert the trailer is gone — rather than inspect its source, so the failure surfaces on the macOS runner. **That is DoD-(b): the test must fail if the hook is broken.** Implementation approach is the builder's. |
| **R-005** | `[OPERATOR]` §5.4/§11.3 possible redundancy, and `ACCEPTANCE.md` having no P0 section: **noted, both left as-is.** P0's exit criteria live in P0 §12 (Gate 0); no `ACCEPTANCE.md` P0 section is required. Raise either again only if it blocks a checker. Supersedes Session 1 Surprises 4 and 5. |

## Non-blocking — decided by the builder, needs review

*Proceed, but the operator should look.*

| # | Decision | Tag | Review by |
|---|---|---|---|
| D-001 | **`.gitattributes` added** (`* text=auto eol=lf`) — not a manifest row. `core.autocrlf=true` is set system-wide on this machine, so a fresh Windows clone would check `.githooks/commit-msg` out with CRLF, making its `#!/usr/bin/env bash` shebang unexecutable and **silently removing one of the three attribution layers (§4.2)** on a platform §5.2 calls *supported, not assumed*. The manifest is a completeness floor, not a ceiling — it forbids missing rows, not extra files. | `[BUILDER]` | operator |
| D-002 | **`NOTICE` names the copyright holder `Vaunox`** (the operator's own git and GitHub identity). `LICENSE` is left **verbatim** — its `Copyright [yyyy] [name of copyright owner]` line sits inside the APPENDIX, which is instructional boilerplate addressed to *downstream* users, and Apache's own practice is to leave it unedited and carry attribution in `NOTICE`. If the operator wants a legal name rather than a handle, this is a one-line change. | `[BUILDER]` | operator |
| D-003 | **Commit #1 uses §3.1's message verbatim** despite also carrying `LICENSE`, `NOTICE`, and `.gitattributes`, which the message does not name. §3.1 prescribes the string literally; the deviation would be cosmetic; and the full composition is recorded here instead, which is where explanations belong. | `[BUILDER]` | operator |

---

# ═══ MACHINE STATE ═══

*Generated. Never narrated. Paste `python tools/gate.py` output verbatim.*

## Last `python tools/gate.py`

```
(not yet run — tools/gate.py does not exist; P0.GATE not built)
```

**Run at:** —
**Commit:** —

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
