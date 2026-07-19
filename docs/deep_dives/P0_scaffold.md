# Deep Dive P0 — Repository, Remote, and the Enforcement Machinery

> **Status: COMPLETE. Manifest frozen.** This phase may open.
>
> This document is **authoritative**. Build **every row of §11 (MANIFEST)**, not merely the artifacts the gate touches.

---

## 1. Scope

The GitHub remote, branch protection, attribution suppression, the project scaffold, and **the seven checkers that police every phase after this one** — including this one.

**No `lab/` domain code is written in this phase** beyond the package skeleton, config, and logging. P0 builds the judge. P1 builds the first thing to be judged.

---

## 2. Why the machinery goes first

Every previous project built the code and then, later, the checks. That ordering has a specific consequence and it is not subtle:

> **The first phase is the one built unpoliced — and the first phase builds the substrate that everything else stands on.**

A stubbed hash chain passes P1's gate. By P6 you have four thousand trials in an append-only ledger nobody can verify, and there is no way back, because append-only is the point.

So the checkers exist before the code. This costs one session and it is the cheapest session in the program.

### 2.1 The self-bootstrap

P0's own gate is the machinery **passing on itself**: the manifest checker finds and validates P0's manifest; the no-stub checker finds no stubs in the checkers; the attribution checker finds no attribution in P0's own history.

There is no circularity problem here. You build the tool, then you run it on yourself. If it cannot validate its own phase, it will not validate any other.

### 2.2 The rule that makes a checker worth having

**A checker that always passes is worse than no checker**, because it manufactures confidence.

> **Every checker ships with a planted violation and a test proving the checker rejects it.**

This is DoD-(b) — *"the certifying test must fail if the machinery is removed"* — applied to the machinery itself. `tests/completeness/fixtures/` holds a deliberately broken tree per checker. `tests/completeness/test_checkers.py` asserts each checker exits non-zero on it.

If you build only one thing correctly in this phase, build this.

---

## 3. Bootstrap — the builder does all of it

**The operator's entire job is: unzip, open Claude Code, say "read CLAUDE.md and begin."**

Everything below is executed by the builder in session 0. There is no setup script for the operator to run, because a setup script the operator runs is a step the operator can get wrong, and it is the *first* step — the one where a mistake is most expensive.

### 3.0 — Preflight

Run before touching anything. Each failure has exactly one remedy, and the builder states it and stops.

```bash
git --version              # required
gh --version               # required
gh auth status             # required — see below
python3 --version          # >= 3.11
```

**`gh auth status` is the one thing the builder cannot fix.**

Authentication is the operator's, and the builder does not handle credentials, does not run `gh auth login`, and does not touch a token. If `gh auth status` fails:

> **STOP.** Print exactly: *"Run `gh auth login`, then say continue."* Do nothing else. Do not proceed with a local-only repo and "add the remote later" — later never comes, and a phase merged with no remote has no protected `main`, which means the invariant in §3.3 was never true.

This is the **only** operator action in the entire program, and it exists because credential handling is not the builder's to do.

### 3.1 — Local repository

```bash
git init -b main
git config core.hooksPath .githooks
git add -A
git commit -m "chore: governance, blueprint, and deep dives for P0 and P1"
```

The hook path is set **before** the first commit. A commit-msg hook that arrives after the first commit did not police the first commit, and in a history destined to go public, "all but the first" is not a property worth having.

### 3.2 — Remote

```bash
gh repo create lab --public --source=. --remote=origin --push
```

**Public from the first commit**, by operator decision (logged in `HANDOFF.md`). This removes the free-tier branch-protection problem — public repos get protection at no cost — and means the builder never pauses to ask about visibility. But there is **no private window in which to fix anything**: the entire git history is public from row zero, so attribution (§4) and the licence (§4.6) must be correct *in the first commit*, not cleaned up later. You cannot un-author a commit already in a public history without rewriting the whole thing. Public visibility is **not** release (Constitution S1): a readable repo that ships nothing has released nothing.

### 3.3 — Protect `main`

```bash
gh api -X PUT "repos/{owner}/lab/branches/main/protection" \
  -f 'required_status_checks[strict]=true' \
  -f 'required_status_checks[contexts][]=gate' \
  -f 'enforce_admins=true' \
  -f 'required_linear_history=true' \
  -f 'allow_force_pushes=false' \
  -f 'allow_deletions=false'
```

**`enforce_admins=true` is the load-bearing flag and it is not a formality.**

You are the admin. You are also the person the Constitution was written to constrain — the one who will be six months in, with a gate failing by a hair and a merge button that works. An admin bypass is a bypass, and a ratchet with an admin bypass is a suggestion.

**Verification is piped, not asserted.** The builder runs:

```bash
gh api "repos/{owner}/lab/branches/main/protection" | tee -a HANDOFF.md
```

CI cannot check this — verifying branch protection needs an admin-scoped token, and putting an admin-scoped token in CI to check that admins are restricted is a circle not worth closing. So the evidence goes in the handoff, verbatim, as output. Per §12.1: typed status is a claim; piped status is evidence.

> The invariant this buys: **a branch may be partial. `main` may not.** Every phase merged into `main` is *completely* built — every manifest row, not merely the ones the gate tests touch. It is the only property that makes the phase sequence trustworthy.

### 3.4 — Phase branch

```bash
git checkout -b phase/p0-scaffold
```

All P0 work happens here. **`main` is never committed to directly**, including now, including by the person who just created it.

---

## 4. Attribution suppression — three layers

The repository must read, end to end, as the operator's own work. No AI, tool, model, or vendor attribution anywhere: commits, PR bodies, tags, code, comments, metadata.

**Three layers, because one missed commit in a public history is permanent.**

### 4.1 Configure it off

`.claude/settings.json`:

```json
{
  "attribution": { "commit": "", "pr": "" }
}
```

`includeCoAuthoredBy` is **deprecated** as of Claude Code v2.0.62. Do not set both — they conflict. Use `attribution` alone.

This suppresses the auto-appended trailer and the PR footer. It does **not** sanitise the body of a commit message or a PR description, and it does nothing about commits already made.

### 4.2 Strip it at the hook

`.githooks/commit-msg` — strips any attribution trailer regardless of origin:

```bash
#!/usr/bin/env bash
set -euo pipefail
sed -i.bak -E '/^(Co-Authored-By|Co-authored-by):/Id' "$1"
sed -i.bak -E '/(Generated with|Assisted by|🤖)/Id' "$1"
rm -f "$1.bak"
```

Wire with `git config core.hooksPath .githooks`. Committed to the repo so it survives a fresh clone.

### 4.3 Fail the build on it — authorship, not topic

**The goal is that no commit, PR, or tag is *authored by* or *attributed to* an AI.
It is NOT to purge the *word* "Claude" from the repository.** These are different
things, and conflating them creates an unwinnable loop: `.gitignore` must contain the
literal `CLAUDE.md`, a docstring may legitimately reference the Anthropic API, a
comment may say "run this under Claude Code." A checker that greps file *contents* for
the string `claude` can never pass, and no exclusion list fixes it — the next
legitimate mention just trips it again. That is whack-a-mole, and it is the wrong
design.

So `tools/check_attribution.py` scans **authorship metadata only**, across the full
history:

- **Commit trailers and author/committer identity.**
  `git log --format='%an%x00%ae%x00%cn%x00%ce%x00%(trailers)'` — the author name, author
  email, committer name, committer email, and structured trailers (`Co-Authored-By`,
  `Co-authored-by`, `Signed-off-by`, etc.).
- **Commit-message trailers specifically** — the bottom block of each message, where
  `Co-Authored-By:` and `Generated with` lines land. Not the whole message body: a
  commit message may legitimately say "fix the Claude API client." The *trailer block*
  is where authorship is asserted, and that is what is scanned.
- **Tag tagger identity and tag-message trailers** — same logic as commits.
- **PR author and any auto-appended PR footer** (checked in CI against the PR metadata,
  not file contents).

**Banned in those metadata fields only** (case-insensitive): `co-authored-by` pointing
at any AI/vendor identity, `claude`, `anthropic`, `generated with`, `generated by`,
`assisted by`, `ai-generated`, `🤖`, and any author/committer name or email resolving to
an AI tool rather than the operator.

**File contents are NOT scanned for these words.** A tracked file may say "Claude",
"Anthropic", "AI", anything — that is topic, not authorship, and it is none of the
checker's business. This removes the `.gitignore` / `.claude/**` loop at the root
rather than papering over it with exclusions: there is nothing to exclude, because
contents were never in scope.

**The one file-content check that remains** is narrow and unambiguous: the checker
asserts `CLAUDE.md` and `.claude/` are **absent from tracked files** (they are
gitignored; §4.4). That is a check on *what is committed*, not *what words appear
inside committed files* — it prevents the tool's own config from entering the public
history, which is a genuine authorship-signature leak, without pretending the word
"Claude" is contraband.

### 4.4 `CLAUDE.md` is never committed

A committed `CLAUDE.md` is the loudest signature there is.

It is gitignored. It exists on disk, and it is a **thin pointer** — it contains no rules of its own, only instructions to read the governance docs. That way losing it loses nothing but a redirect, and the actual rules live in files that *are* committed and *are* the operator's own work.

### 4.5 Style is a signature too

Over-commented, over-docstringed, defensively over-engineered code has a smell. So do emoji in commit messages and `🎉 Initial commit`. In a repository whose product is credibility, smell matters. This is not mechanically checkable; it is a review obligation, and it is stated here so it cannot be claimed nobody said it.

---

## 5. Scaffold

```
pyproject.toml            # deps, ruff, black, mypy (strict), pytest, mutmut
.pre-commit-config.yaml   # ruff, black, mypy, check_no_stubs, check_attribution
.gitignore                # .env, data/, .claude/, CLAUDE.md, *.jsonl, tokens
.githooks/commit-msg
.github/workflows/ci.yml
tools/gate.py             # the gate entry point (no make on Windows)
src/lab/__init__.py       # __version__ only
tests/                    # unit/ integration/ adversarial/ completeness/
tools/                    # the seven checkers
```

**`mypy` runs strict.** Not "strict where convenient." The substrate's correctness argument leans on types, and a partially-typed substrate has the *appearance* of that argument without the substance.

### 5.1 `tools/gate.py` — the single entry point

```
python tools/gate.py
```

Runs, in order: lint · types · tests · manifest · stubs · spec-isolation · imports · attribution · fixtures · substrate-purity.

**Python, not `make`.** There is no `make` on Windows, and **a gate the operator cannot run is a gate the operator does not run.** A `Makefile` may exist as a thin Linux convenience wrapper; it is not load-bearing.

**`gate.py` fails closed on zero registered checkers.** *"Nothing to check"* is not *"all checks passed."* During P0, while the checkers are still being written, that distinction is the entire difference between a bootstrap and a bypass.

Mutation testing is **not** in `gate` — it is slow. It runs on gate PRs and nightly, threshold ≥90% on substrate modules, checked separately in CI.

### 5.2 CI runs an OS matrix

`ubuntu-latest` · `windows-latest` · `macos-latest`.

Not thoroughness for its own sake. The ledger lock is `fcntl.flock` on POSIX and `msvcrt.locking` on Windows (P1 §6.3), and this is a library people will `pip install`. **An untested lock on someone else's machine is a silently forked hash chain** — the exact failure the chain exists to make impossible, arriving down the one path nobody was watching.

Linux is primary: the container, the gates, the reproducibility contract. The matrix exists so Windows and macOS are *supported* paths rather than *assumed* ones.

### 5.3 `LICENSE` and `NOTICE` land here, not at P8

Apache-2.0, plus `NOTICE`. **A repository with no licence is "all rights reserved" by default**, and that is the wrong default to hold for even one day — least of all on a repo that may be public, where a contributor could open a PR into an IP vacuum.

### 5.4 The bootstrap exception — the first PR, and only the first

Branch protection requires a `gate` status check. **No workflow produces it until `ci.yml` exists.** So no PR — spec or code — can merge to `main` until one carrying CI does. §11.1 (spec and code never travel together) is therefore *unenforceable during P0 by construction*. That is a property of bootstrapping, not a flaw.

**One PR is permitted to mix the tiers: the first.** It carries governance, `LICENSE`, `NOTICE`, `.github/workflows/ci.yml`, `tools/gate.py`, and whichever checkers exist. GitHub runs workflows from the PR head, so **it self-satisfies its own gate** — genuinely, not vacuously, because `gate.py` fails closed on zero checkers.

**Do not admin-bypass. Do not temporarily un-require the `gate` check.** Both are the pattern this project exists to refuse, and doing either on the *first* merge sets the precedent for every merge after it.

§11.1 binds absolutely from the second PR onward.

---

## 6. `check_manifest.py`

The completeness gate. **This is the most important tool in the repository.**

### 6.1 What it does

1. Locate the active phase's deep dive: `docs/deep_dives/P{N}_*.md`.
2. **Refuse to run if the deep dive is absent or lacks `frozen: true`.** A phase cannot open against an outline. This is the mechanical form of the rule; without it the rule is prose.
3. Extract the YAML `manifest:` block.
4. For every row, assert the artifact **exists**.
5. For every row with `call_site: required`, assert the symbol is **referenced** outside its own defining module *and* outside its own certifying test.
6. **Closed loop, both directions:**
   - every `spec:` reference resolves to a real heading in the deep dive
   - every non-exempt heading in the deep dive has **≥1** manifest row
7. Assert `DEFERRALS.md` has **zero** rows in *Open deferrals*.
8. Emit the tally that `HANDOFF.md` pastes verbatim.

### 6.2 Existence, by kind

`function` · `method` · `class` · `protocol` · `enum` · `constant` · `exception` · `contextmanager` → resolve the dotted path by **AST walk of `src/`**, not by `importlib`.

`type` → same AST walk. Satisfied by a module-level `NewType(...)` binding, a `TypeAlias` or bare type-alias assignment, or a class definition matching the dotted path.

**Why AST and not import:** importing runs module-level code, which means a checker that can be made to pass by writing a clever `__getattr__`. AST inspection sees what is *written*, which is what the manifest is a claim about.

`script` → the file exists and is executable.

**The kind registry is closed, and an unrecognised `kind` is a hard error — never a skip.** A skip is the vacuous pass this tool exists to prevent, and an open-ended kind field is where a stub hides.

### 6.3 Call-site detection

For `lab.ledger.chain.append`, walk every AST in `src/` and `tools/`, and every test **other than** the row's `certifying_test`. A hit is any `Name` or `Attribute` node resolving to that symbol.

**A primitive that exists but nothing calls is not done.** This is DoD-(a), and it is the orphaned-`PurgedKFold` failure mode that the previous program's audit found. It was a checklist item there. Here it is a script.

### 6.4 The closed loop, and why both directions

- A **heading with no row** is unbuilt spec. Something was specified and nothing was built.
- A **row with no heading** is unspecified work. And unspecified work is where the agent guesses — and an agent guessing resolves toward whatever is cheapest to build.

Exempt headings (front matter, not deliverables): `Scope` · `Why…` · `Failure modes and edge cases` · `Test plan` · `MANIFEST` · `GATE` · `Amendment log`. The exempt list is **in the tool, hardcoded, and short**. A configurable exempt list is a loophole with a config file.

---

## 7. `check_no_stubs.py`

### 7.1 What fails the build

Over `src/lab/` and `tools/`:

| Pattern | Detection |
|---|---|
| `TODO`, `FIXME`, `XXX`, `HACK` | comments and string literals |
| `raise NotImplementedError` | AST |
| function body is only `pass` | AST |
| function body is only `...` | AST — **except Protocol members** (§7.2) |
| `@pytest.mark.skip` / `xfail` | AST — unless it cites a `DIVERGENCES.md` ID |
| deferral language in a docstring | `for now` · `later` · `temporary` · `placeholder` · `simplified` · `not implemented` |

### 7.2 The Protocol exception, which is real

A `Protocol` member's body **is** `...` by language convention. Flagging it would make the checker useless and it would be turned off within a day.

So: a `...` body is permitted **iff** its enclosing class inherits `Protocol` or is decorated `@runtime_checkable`. Everything else fails.

`tests/completeness/fixtures/stubs/` contains both — a legitimate Protocol (must pass) and a bare `...` function (must fail). A checker that cannot tell them apart is not shipped.

### 7.3 The mid-session escape hatch — and why it does not weaken anything

A session may end with work unfinished. **That does not require a stub.** Unfinished work is *absent* code: the manifest row is simply not ticked, the gate is red, and the handoff says so. That is the honest red, and it is the desired outcome.

But sometimes a module genuinely will not import without a placeholder, and forcing the agent to choose between a broken tree and a silent stub is how you *get* silent stubs.

So there is exactly one escape hatch, and it is loud:

```python
def compute_haircut(...) -> Haircut:  # STUB: DEF-001
```

- Without the `# STUB: DEF-nnn` marker → **build fails.**
- With it → build passes, **but** the ID must resolve to an open row in `DEFERRALS.md`.
- And `DEFERRALS.md` must be **empty to merge** (§6.1 step 7).

So: **mid-session stubs are legal and visible. Merge-time stubs are impossible.** The escape hatch cannot be used to ship, only to checkpoint — which is exactly the distinction that matters.

**Build in dependency order and you will not need it.** The manifest is ordered bottom-up for this reason.

---

## 8. `check_spec_isolation.py`

The manifest blocks the merge. The manifest is in the repo. The builder has write access to the repo.

> **The cheapest way to pass a manifest gate is to edit the manifest.**

A ratchet is not a ratchet if the builder is holding the wrench.

```python
SPEC = {"CONSTITUTION.md", "CONTRACTS.md", "ACCEPTANCE.md", "PLAYBOOK.md", "docs/deep_dives/"}
CODE = {"src/", "tools/", "tests/", "pyproject.toml", "Makefile", ".github/"}
LOGS = {"HANDOFF.md", "DEAD_ENDS.md", "PROJECT_STATE.md", "DIVERGENCES.md", "DEFERRALS.md"}
```

On a PR: `git diff --name-only origin/main...HEAD`. **If the diff touches both SPEC and CODE → fail.**

`LOGS` are exempt and *must* be — the handoff is required to travel with the code, and `DIVERGENCES` and `DEFERRALS` are written during the work they describe. A log is not a spec. It records what happened; it does not decide what must happen.

Spec changes ship in their **own PR**, reviewed as spec changes, with the amendment-log entry attached.

---

## 9. The remaining three

### 9.1 `check_import_graph.py`

Rules as data (`tools/import_rules.yaml`), enforced by AST:

```yaml
- symbol: TrialResult
  constructed_only_in: ["lab.ledger.*"]
  reason: "The engine cannot mint a result. Only the ledger can. Deep dive P1 §9."

- module: lab.costs.schedule
  imported_only_by: ["lab.costs.*"]
  reason: "Engines may duplicate logic. Engines may never duplicate truth."

- module: lab.ledger.store
  imported_only_by: ["lab.ledger.*"]
  reason: "There is one write path. Deep dive P1 §9."
```

**Every rule carries its `reason`, and the checker prints it on failure.** A violation message that says only *"import rule violated"* teaches the next agent nothing, and it will simply route around it. A message that says *"the engine cannot mint a result"* teaches it the invariant.

The file is empty of `lab.*` rules in P0 (there is no `lab` code yet) but the **tool ships and is tested against a fixture tree**. This is the pattern for the whole phase: the machinery is complete; the rules arrive with the code they police.

### 9.2 `check_fixture_provenance.py`

**The engine may not be its own oracle.** Gate fixtures are **derived by hand** from the cost schedule and the fill rules — never generated by the engine they judge.

The checker asserts, for each fixture in `ACCEPTANCE.md`:
- the blob hash matches
- a **derivation document** exists alongside it
- **the fixture commit predates the engine commit** (`git merge-base --is-ancestor`)

> **A fixture the engine produced is not a gate. It is a mirror.** With no external baseline, this is the only remaining way to cheat, and it is the obvious one.

No fixtures exist in P0. **The tool ships anyway**, tested against a fixture-of-fixtures. Building it in P4 — the phase it polices — would mean building the judge and the defendant in the same session.

### 9.2b `check_substrate_purity.py` — the kill gate

**This is the mechanism behind Constitution S1.** It does nothing until Gate 4 cuts the `substrate-frozen` tag, and everything at Gate 5.

Against `git diff substrate-frozen..HEAD -- src/lab/{core,ledger,costs,fills,validation}`:

- **Automatic failure** on engine-specific vocabulary anywhere in the substrate:
  `intraday` · `daily` · `square_off` · `squareoff` · `MIS` · `engine_id ==` · `isinstance(engine`
- Every other substrate change must be declared **engine-agnostic** in the PR body, with a justification.

If the second engine cannot be built without changing shared truth in an engine-specific way, **the abstraction is wrong and the project stops.** That is the thing the kill gate was always *for*, tested directly rather than by proxy: *can one contract hold two dissimilar simulation semantics without contaminating the truth beneath them?*

Ships in P0, inert until P4. Like every other checker here, it is built before the code it polices.

### 9.3 `check_attribution.py`

§4.3.

---

## 10. Failure modes and edge cases

| # | Case | Behaviour |
|---|---|---|
| 1 | Deep dive missing for the active phase | `check_manifest` **refuses to run**. Phase cannot open. |
| 2 | Deep dive present but not `frozen: true` | Same. An outline is not a specification. |
| 3 | Protocol member with `...` body | **Passes.** §7.2 |
| 4 | Bare function with `...` body | Fails. |
| 5 | Stub with a valid `# STUB: DEF-nnn` | Passes the stub check; **blocks the merge** via non-empty `DEFERRALS.md`. §7.3 |
| 6 | Stub with an ID not in `DEFERRALS.md` | Fails. |
| 7 | `.gitignore` contains `CLAUDE.md`; a docstring says "Claude API" | **Passes.** The checker scans authorship metadata, not file contents. The word "Claude" is topic, not attribution. §4.3 |
| 8 | Manifest row for a symbol only used in its own test | **Fails** `call_site: required`. Definition is not use. |
| 9 | Deep dive heading with no manifest row | Fails. Unbuilt spec. |
| 10 | Manifest row citing a heading that does not exist | Fails. Unspecified work. |
| 11 | PR touches `CONSTITUTION.md` and `src/` | Fails `check_spec_isolation`. |
| 12 | PR touches `HANDOFF.md` and `src/` | **Passes.** Logs are exempt and must be. |
| 13 | Admin force-push to `main` | Blocked. `enforce_admins=true`. §3.2 |
| 14 | Checker itself contains a stub | Fails. The checkers are `src`-equivalent and check themselves. |
| 15 | A checker that never fails | Caught by `test_checkers.py` — every checker must reject its planted violation. §2.2 |
| 16 | `gh auth status` fails | **STOP.** Print the remedy. Do not proceed local-only. §3.0 |
| 17 | `gh` not installed | STOP. Print the remedy. Do not fall back to `git remote add` — the protection step needs `gh`. |
| 18 | Repo `lab` already exists on the remote | STOP and ask. Do **not** force, do **not** pick `lab-2`. |
| 19 | Hooks path set after the first commit | Fails `test_hooks_path_set_before_first_commit`. "All but the first" is not a property worth having. |

Case 15 is the one that matters. **A checker with no proof that it can fail is a checker that will one day silently stop working**, and nobody will notice, because everything will be green.

---

## 11. MANIFEST — frozen

```yaml
manifest_version: 1
phase: P0
frozen: true

rows:
  # ---- bootstrap (session 0, builder-executed) ----
  - id: P0.BOOT.PREFLIGHT
    artifact: tools/preflight.py
    kind: script
    spec: "§3.0"
    call_site: n/a
    certifying_test: tests/completeness/test_bootstrap.py::test_preflight_stops_on_missing_gh_auth

  - id: P0.BOOT.GIT
    artifact: .git
    kind: infra
    spec: "§3.1"
    call_site: n/a
    certifying_test: tests/completeness/test_bootstrap.py::test_hooks_path_set_before_first_commit

  - id: P0.BOOT.REMOTE
    artifact: git.remote.origin
    kind: infra
    spec: "§3.2"
    call_site: n/a
    certifying_test: tests/completeness/test_bootstrap.py::test_origin_configured

  - id: P0.BOOT.PROTECTION
    artifact: github.branch_protection.main
    kind: infra
    spec: "§3.3"
    call_site: n/a
    certifying_test: HANDOFF.md::piped_gh_api_output

  # ---- CI ----
  - id: P0.REMOTE
    artifact: .github/workflows/ci.yml
    kind: file
    spec: "§5"
    call_site: n/a
    certifying_test: tests/completeness/test_ci_config.py::test_gate_job_is_required

  - id: P0.HOOKS
    artifact: .githooks/commit-msg
    kind: script
    spec: "§4.2"
    call_site: n/a
    certifying_test: tests/completeness/test_checkers.py::test_commit_msg_hook_strips_trailer

  # ---- scaffold ----
  - id: P0.PYPROJECT
    artifact: pyproject.toml
    kind: file
    spec: "§5"
    call_site: n/a
    certifying_test: tests/completeness/test_scaffold.py::test_mypy_is_strict

  - id: P0.PRECOMMIT
    artifact: .pre-commit-config.yaml
    kind: file
    spec: "§5"
    call_site: n/a
    certifying_test: tests/completeness/test_scaffold.py::test_precommit_runs_stub_check

  - id: P0.GATE
    artifact: tools/gate.py
    kind: script
    spec: "§5.1"
    call_site: required
    certifying_test: tests/completeness/test_gate.py::test_gate_fails_closed_on_zero_checkers

  - id: P0.CI.MATRIX
    artifact: .github/workflows/ci.yml
    kind: file
    spec: "§5.2"
    call_site: n/a
    certifying_test: tests/completeness/test_ci_config.py::test_os_matrix_covers_windows

  - id: P0.LICENSE
    artifact: LICENSE
    kind: file
    spec: "§5.3"
    call_site: n/a
    certifying_test: tests/completeness/test_scaffold.py::test_license_is_apache_2

  - id: P0.NOTICE
    artifact: NOTICE
    kind: file
    spec: "§5.3"
    call_site: n/a
    certifying_test: tests/completeness/test_scaffold.py::test_notice_present

  - id: P0.GITIGNORE
    artifact: .gitignore
    kind: file
    spec: "§4.4"
    call_site: n/a
    certifying_test: tests/completeness/test_scaffold.py::test_claude_md_is_ignored

  # ---- config & logging (the only lab/ code in P0) ----
  - id: P0.CONFIG
    artifact: lab.core.config.load_config
    kind: function
    spec: "§5"
    call_site: required
    certifying_test: tests/unit/core/test_config.py::test_layered_override

  - id: P0.SECRETS
    artifact: lab.core.config.get_secret
    kind: function
    spec: "§5"
    call_site: required
    certifying_test: tests/unit/core/test_config.py::test_missing_secret_raises

  - id: P0.LOGGING
    artifact: lab.core.logging.configure
    kind: function
    spec: "§5"
    call_site: required
    certifying_test: tests/unit/core/test_logging.py::test_structured_and_redacted

  # ---- the seven checkers ----
  - id: P0.CHK.MANIFEST
    artifact: tools/check_manifest.py
    kind: script
    spec: "§6"
    call_site: required
    certifying_test: tests/completeness/test_checkers.py::test_manifest_rejects_missing_row

  - id: P0.CHK.MANIFEST.CALLSITE
    artifact: tools.check_manifest.assert_called_outside_own_module
    kind: function
    spec: "§6.3"
    call_site: required
    certifying_test: tests/completeness/test_checkers.py::test_manifest_rejects_uncalled_symbol

  - id: P0.CHK.MANIFEST.LOOP
    artifact: tools.check_manifest.assert_closed_loop
    kind: function
    spec: "§6.4"
    call_site: required
    certifying_test: tests/completeness/test_checkers.py::test_manifest_rejects_unspecified_row

  - id: P0.CHK.MANIFEST.FROZEN
    artifact: tools.check_manifest.assert_deep_dive_frozen
    kind: function
    spec: "§6.1"
    call_site: required
    certifying_test: tests/completeness/test_checkers.py::test_manifest_refuses_unfrozen_deep_dive

  - id: P0.CHK.STUBS
    artifact: tools/check_no_stubs.py
    kind: script
    spec: "§7"
    call_site: required
    certifying_test: tests/completeness/test_checkers.py::test_stubs_rejects_bare_pass

  - id: P0.CHK.STUBS.PROTOCOL
    artifact: tools.check_no_stubs.is_protocol_member
    kind: function
    spec: "§7.2"
    call_site: required
    certifying_test: tests/completeness/test_checkers.py::test_stubs_allows_protocol_ellipsis

  - id: P0.CHK.STUBS.DEFERRAL
    artifact: tools.check_no_stubs.resolve_deferral_marker
    kind: function
    spec: "§7.3"
    call_site: required
    certifying_test: tests/completeness/test_checkers.py::test_stubs_rejects_unregistered_marker

  - id: P0.CHK.SPEC
    artifact: tools/check_spec_isolation.py
    kind: script
    spec: "§8"
    call_site: required
    certifying_test: tests/completeness/test_checkers.py::test_spec_isolation_rejects_mixed_pr

  - id: P0.CHK.SPEC.LOGS
    artifact: tools.check_spec_isolation.LOG_PATHS
    kind: constant
    spec: "§8"
    call_site: required
    certifying_test: tests/completeness/test_checkers.py::test_spec_isolation_allows_handoff_with_code

  - id: P0.CHK.IMPORTS
    artifact: tools/check_import_graph.py
    kind: script
    spec: "§9.1"
    call_site: required
    certifying_test: tests/completeness/test_checkers.py::test_import_graph_rejects_violation

  - id: P0.CHK.IMPORTS.RULES
    artifact: tools/import_rules.yaml
    kind: file
    spec: "§9.1"
    call_site: n/a
    certifying_test: tests/completeness/test_checkers.py::test_import_graph_prints_reason_on_failure

  - id: P0.CHK.FIXTURES
    artifact: tools/check_fixture_provenance.py
    kind: script
    spec: "§9.2"
    call_site: required
    certifying_test: tests/completeness/test_checkers.py::test_fixture_provenance_rejects_bad_hash

  - id: P0.CHK.SUBSTRATE
    artifact: tools/check_substrate_purity.py
    kind: script
    spec: "§9.2b"
    call_site: required
    certifying_test: tests/completeness/test_checkers.py::test_substrate_purity_rejects_engine_vocabulary

  - id: P0.CHK.ATTRIB
    artifact: tools/check_attribution.py
    kind: script
    spec: "§4.3"
    call_site: required
    certifying_test: tests/completeness/test_checkers.py::test_attribution_rejects_trailer_in_history

  - id: P0.CHK.ATTRIB.SCOPE
    artifact: tools.check_attribution.scan_authorship_metadata
    kind: function
    spec: "§4.3"
    call_site: required
    certifying_test: tests/completeness/test_checkers.py::test_attribution_ignores_file_contents

  # ---- the planted violations ----
  - id: P0.FIXTURES.VIOLATIONS
    artifact: tests/completeness/fixtures/
    kind: file
    spec: "§2.2"
    call_site: n/a
    certifying_test: tests/completeness/test_checkers.py::test_every_checker_rejects_its_fixture
```

---

## 12. GATE 0 — exit

**Correctness gate**
- Every test in the manifest passes.
- **`test_every_checker_rejects_its_fixture` passes.** Each of the seven rejects its planted violation. A checker that cannot fail has not been built.

**Completeness gate**
- `check_manifest.py` validates **its own manifest** — every row exists, every `call_site: required` row is called, the loop closes both ways.
- `check_no_stubs.py` clean over `tools/` and `src/`.
- `check_attribution.py` clean over the **full history**.
- `DEFERRALS.md` empty.

**Bootstrap gate**
- Preflight passed, or the operator was told to run `gh auth login` and did.
- `origin` configured. `core.hooksPath` set **before** the first commit.
- `main` protected: CI required · `enforce_admins=true` · linear history · force-push and deletion off.
- **The `gh api` protection response is pasted verbatim into `HANDOFF.md`.** Piped, not asserted — CI cannot verify this without an admin-scoped token, and putting one in CI to check that admins are restricted is a circle not worth closing.
- The phase PR merged from `phase/p0-scaffold`, **never a direct push** — including by the person who just created the repo.

Tag `gate-0-scaffold`. The tag commit contains the complete deliverables.

---

## 13. Amendment log

| Date | Section | Change | Reason |
|---|---|---|---|
| 2026-07-13 | — | Initial. Manifest frozen. | — |
| 2026-07-18 | §11 | `P0.BOOT.PREFLIGHT`: `call_site: required` → `call_site: n/a` | `[OPERATOR]` A-001. No tracked file can honestly invoke `tools/preflight.py`. §5.1 enumerates the gate's stages exhaustively and preflight is not among them; §6.3 excludes the row's own certifying test; and §12's bootstrap gate already treats preflight as documentary evidence (*"Preflight passed, or the operator was told to run `gh auth login` and did"*). Preflight is a one-time session-0 script run by hand, and wiring it into `gate.py` or `ci.yml` to satisfy the field would fail on runners without `gh auth`, breaking the gate for outside contributors on a public repo — a call site manufactured to satisfy a checker, which is §2.2 inverted. Its three bootstrap siblings (`P0.BOOT.GIT`, `.REMOTE`, `.PROTECTION`) are all `n/a` for the same reason: their invoker is external to the repository. **`test_preflight_stops_on_missing_gh_auth` still ships and must pass** — `n/a` removes the external-caller requirement, not the test. |
| 2026-07-18 | §6.2 | Add `type` to the kind registry, resolved by the same AST walk. State that the registry is closed and an unrecognised kind is a hard error. | `[OPERATOR]` A-002. Contradiction between two frozen specs: P1's frozen manifest uses `kind: type` six times (`lab.core.types.Paise`, `AsOf`, `DateRange`, `lab.ledger.schema.TrialDraft`, `TrialResult`, `lab.ledger.seal.SealToken`), which a checker written strictly to §6.2 would refuse on day one of P1. Resolved in favour of the document that already shipped the usage. Fail-closed behaviour is preserved and made explicit: unknown kinds do not pass leniently, because an open-ended kind field is where a stub hides. |
| 2026-07-18 | §1, §5, §11, §12 | "six checkers" → "seven" (4 occurrences) | `[OPERATOR]` A-003. Stale prose count. The manifest enumerates **seven** checker scripts — manifest, stubs, spec-isolation, imports, fixtures, substrate-purity, attribution — and §9.2b states `check_substrate_purity.py` *"Ships in P0."* The §11 occurrence was a YAML section comment reading `# ---- the six checkers ----` directly above seven rows. Left uncorrected, a builder reading "six" ships `check_substrate_purity.py` **without a planted violation**, which is failure case 15 — the one §10 calls *"the one that matters."* The §12 edit raises the correctness gate from six planted violations to seven: strictly tightening, a ratchet in the safe direction. |

**Amendment procedure followed:** §10.5 — the deep dive is amended with a dated entry, and the
manifest row is changed citing it. Applied on `phase/p0-scaffold` within the bootstrap PR, which
§5.4 / §11.3 designate as the one PR permitted to carry spec and code together; a separate
spec-only PR is not viable during P0, because no PR can merge to `main` before `ci.yml` produces the
required `gate` check. **§11.1 binds absolutely from the second PR onward**, and
`check_spec_isolation.py` implements that exception narrowly and self-closingly (§8).
