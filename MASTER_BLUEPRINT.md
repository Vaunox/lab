# MASTER BLUEPRINT — The Lab
### Build & Research Handoff Document

*A single, self-contained specification for a **new repository**: an open-source research kernel for systematic strategies on Indian cash equity. It ships the machine, not the cartridges. It generates no orders, ships no strategies, and redistributes no data. Its product is a verdict you can trust, with the trial count and the haircut stapled to it.*

*Written to be handed to a capable engineer or coding agent and worked through top-to-bottom, **one full phase per session**.*

---

## HOW TO USE THIS DOCUMENT

This file is the **index**. It is not the specification.

**The specification for a phase is that phase's deep dive** (`docs/deep_dives/PN_*.md`), and it is authoritative. This is the inverse of the convention used on previous projects, and the inversion is deliberate — see Part I §10.

**At the start of every session:**

> "Read `HANDOFF.md` first — it is the current state of the phase, and it is authoritative over your assumptions. Then `DEAD_ENDS.md`. Then follow the Engineering Ground Rules (Part I), with attention to §9 (Completion), §10 (Completeness), §11 (Gate integrity), and §12 (Session protocol). We are working on **Phase N**. Read `docs/deep_dives/PN_*.md` in full. Build **every row of its MANIFEST**, not merely the artifacts the gate tests touch. Run `python tools/gate.py`. Update `HANDOFF.md` continuously, not at the end."

**Rules of engagement:**

- **A phase may span sessions. A PR may not merge partially.** A session never ends with a stub that makes a check pass — it ends with an honest red and a written account of what is not built yet. See Part I §12.
- **A phase cannot begin until its deep dive is complete and its MANIFEST is frozen.** A phase begun against an outline will be built to its gate and nothing more. This is not a hypothetical; it is the observed failure mode of every previous project.
- **Respect dependencies and gates.** Do not start a phase until the previous gate passes. Gates exist for scientific honesty, not bureaucracy.
- **Never commit to `main`.** Branch per phase. Phase = one PR. Merge only when CI is green and every MANIFEST row is ticked with call-site evidence.
- **Spec and code never travel in the same PR** (§11.1). The builder cannot edit the thing that judges the builder.
- When a decision is ambiguous, **stop** — do not choose the simpler option. Ambiguity is a spec bug (Inviolable Rule 1).
- **Attribution — this is the operator's own work.** No third-party or AI attribution of any kind anywhere in the repository, its history, its tags, or its metadata. Hard rule. Checked by CI, not by memory.

**Governing documents, in precedence order.** Where any two disagree, the higher wins and the divergence is logged.

1. `CONSTITUTION.md` — scope, refusals, pinned numbers, structural invariants, stop conditions
2. `CONTRACTS.md` — the Strategy and Engine contracts, trial identity, taints, agent boundary
3. `ACCEPTANCE.md` — per-phase exit criteria
4. `docs/deep_dives/PN_*.md` — the phase specification
5. This blueprint — the index

---

# PART I — ENGINEERING GROUND RULES

Non-negotiable. Re-read before each phase.

## 1. Modularity

One module, one job. Program to interfaces (`Protocol`), not implementations. Dependency injection; no global mutable state. Pure functions wherever possible — this is what makes point-in-time correctness *enforceable* rather than merely intended.

**The substrate boundary is architectural, not stylistic.** Nothing outside `costs/` computes a cost. Nothing outside `data/adapters/` imports a broker SDK. Nothing outside `ledger/` writes a ledger row. These are checked by import-graph tests, not by review.

## 2. No hard-coding

Every parameter in versioned config. Layered: `default.yaml` ← env ← env vars. Secrets never in code, config, or logs — environment only. `pathlib.Path` everywhere; the code runs identically in the CI container and on the operator's machine.

**Exception, and it is the important one:** statutory cost rates, exchange calendar, and circuit bands are **not configuration**. They are dated, sourced *data* (Part III §3). Presenting a fact as a setting implies it is an opinion.

## 3. Standard structure

```
lab/
├── README.md
├── CONSTITUTION.md          # binding: scope, refusals, pinned numbers, invariants
├── CONTRACTS.md             # binding: Strategy, Engine, trial identity, taints, agent boundary
├── ACCEPTANCE.md            # binding: per-phase exit criteria
├── PLAYBOOK.md              # pre-committed responses
├── DIVERGENCES.md           # permanent record of accepted gate divergences
├── DEFERRALS.md             # must be EMPTY at every phase exit
├── PROJECT_STATE.md         # living
├── MASTER_BLUEPRINT.md      # this file — the index
├── docs/deep_dives/         # THE SPECIFICATION. One per phase. Complete before the phase opens.
├── pyproject.toml
├── .pre-commit-config.yaml
├── .gitignore               # .env, data/, .claude/, CLAUDE.md, tokens
├── .github/workflows/ci.yml
├── config/
├── src/lab/
│   ├── core/                # types, Protocols, config, logging, IST calendar, the as-of clock
│   ├── ledger/              # JSONL append-only + hash chain; SQLite derived index; trial identity
│   ├── costs/               # PIT statutory schedule; broker profiles; slippage floor
│   ├── fills/               # the fill gate: circuit bands, series, liquidity
│   ├── data/                # adapters, canonical format, provenance, validators, universe rules
│   ├── engines/
│   │   ├── equity_daily/    # isolated. own loop.
│   │   └── equity_intraday/ # isolated. own loop. NO shared loop, NO mode flags.
│   ├── validation/          # walk-forward, DSR, PBO, clustering, effective-N, power calculator
│   ├── consoles/            # telescope (JSONL), court record (ledger view)
│   └── agent/               # the machine interface; enforces the agent boundary
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── adversarial/         # leakage, skew, null (random + LLM), power, red-team
│   └── completeness/        # manifest, no-stub, no-attribution, import-graph
└── tools/
    ├── check_manifest.py
    ├── check_no_stubs.py
    ├── check_attribution.py
    └── check_import_graph.py
```

## 4. No temporary patch fixes

Solve the underlying problem. No band-aids, no commented-out code, **no `TODO` in merged work** — and this is now mechanically enforced (§10), not merely requested.

## 5. Code comments

Comment the *why*. Docstrings on every public module, class, function — purpose, params, returns, invariants. Especially: *"point-in-time: inputs are only data available at or before `asof`."* Cite the deep dive section a function implements. Keep comments true at HEAD.

## 5b. The gate entry point, and the OS matrix

**`python tools/gate.py`, not `make gate`.** There is no `make` on Windows, and a gate the operator cannot run is a gate the operator does not run.

**`gate.py` fails closed on zero registered checkers.** *"Nothing to check"* is not *"all checks passed"* — and during P0, while the checkers are still being built, that distinction is the whole difference between a bootstrap and a bypass.

**CI runs `ubuntu-latest` · `windows-latest` · `macos-latest`.** Not thoroughness for its own sake: the ledger lock is `fcntl.flock` on POSIX and `msvcrt.locking` on Windows (P1 §6.3), and this is a library people will `pip install`. **An untested lock on someone else's machine is a silently forked hash chain** — the exact failure the chain exists to make impossible, arriving down the one path nobody was watching. Linux remains primary: the container, the gates, the reproducibility contract.

---

## 6. Git and GitHub workflow

**Remote first.** The GitHub remote is created in P0, before any code. Everything below assumes it exists.

- **`main` is protected.** No direct pushes. Required: CI green, PR review, linear history.
- **Branch per phase:** `phase/p1-substrate`, `phase/p2-cost-kernel`.
- **A phase = one PR.** The PR body is the phase's **MANIFEST**, verbatim, as a checklist. It merges when every row is ticked and CI is green.
- **Small atomic commits**, conventional-commit style (`feat:`, `fix:`, `test:`, `refactor:`, `docs:`, `chore:`). Each commit leaves the tree working.
- **Tag on merge:** `gate-1-substrate`, etc. Per §9.3, the tag commit contains the **complete** deliverables the gate claims. Tagging ahead of deliverables is prohibited.
- **Never commit:** secrets, tokens, market data, `CLAUDE.md`, `.claude/`.

> **The invariant that gives `main` its meaning:**
> **A branch may be partial. `main` may not.** Every phase merged into `main` is *completely* built. That is the only property that makes the phase sequence trustworthy, and it is why the manifest gate blocks the merge rather than merely annotating it.

**Attribution — hard rule, enforced by CI.**

- No `Co-Authored-By` trailers. No "generated by", "assisted by", model names, vendor names — in commits, PR bodies, tags, code, comments, or metadata.
- `.claude/settings.json`: `{"attribution": {"commit": "", "pr": ""}}`. (`includeCoAuthoredBy` is deprecated as of Claude Code v2.0.62 — do not set both; they conflict.)
- A `commit-msg` hook strips any attribution trailer regardless of origin. Belt and braces: one missed commit is permanent in a public repo.
- `CLAUDE.md` and `.claude/` are gitignored. A committed `CLAUDE.md` is the loudest signature there is.
- `tools/check_attribution.py` greps the full history in CI. Not a convention. A test.
- No emoji in commit messages. And watch the code style — over-commented, over-docstringed, defensively over-engineered code has a smell, and in a repo whose product is credibility, smell matters.

## 7. Professional standards

Ruff + black. **Static typing everywhere** — mypy strict passes in CI. Determinism: seed all RNGs; version data, costs, and results; any run reproducible from config + hashes. Fail loudly and early: validate at boundaries, raise specific exceptions.

**Money is `Decimal` or integer paise. Never float.** Enforced by a test that greps the cost path. This is what makes tolerance-0 gate reproduction achievable.

## 8. Logging

Structured, configured once in `core/`. This is the **telescope** — ephemeral, firehose, retention-capped, zero epistemic weight. IST timestamps. Correlation ID per trial.

> **The telescope is not the ledger.** The ledger is written by the engine as a first-class side effect; the telescope merely *observes that the write happened*. Logs are things you can turn off. Ledgers are not. Any code path in which suppressing logs suppresses a ledger row is a build failure.

## 9. Completion Standard — *"done" means proven at the call site*

Adopted wholesale from the prior program, where it was established by audit. Its finding: every defect had the same shape — **a name, flag, or tag claiming more than the code delivered.**

1. **Definition of Done — both must hold.**
   - **(a) Claimed at a call site.** Every capability a name or docstring claims is *invoked at a real call site* (`file:line` of the **call**, not the definition). A primitive that exists but nothing calls is **not done**.
   - **(b) Certified against real machinery.** The certifying test feeds real machinery-computed inputs — never stubs or hand-assembled scalars. **Required property: the test must FAIL if the underlying machinery is removed.** A test that would still pass with the machinery deleted certifies nothing.
2. **Names and docstrings are claims; they must be true at HEAD.** No aspirational naming.
3. **Tags are deliverable snapshots.** The tag commit contains the complete deliverables the gate claims.
4. **Fail-closed is the default for every evaluator.** A gate refuses to grade (`INSUFFICIENT` / raise) on absent, sentinel, or un-provenanced input. It never grades a placeholder as real.
5. **State claims in bounded form — never rounded up.** Record what is closed and what residue remains.
6. **"Harmless iff X" caveats verify X before X is relied on.** If it is checkable now, check it now.
7. **Every "done" claim carries call-site evidence.**

**DoD-(a) is now automated.** `tools/check_manifest.py` verifies, for every manifest row marked `call_site: required`, that the symbol is referenced outside its own module and outside its own test. This was previously a PR-checklist item — and a checklist item is a thing an agent ticks.

### 9.8 DoD-(b) is automated too — mutation score, not line coverage

Rule 1(b) requires that *"the certifying test must fail if the underlying machinery is removed."* That is the right test. It was also, until now, an assertion checked by a human at review time — which is to say, not checked.

**Line coverage is the metric an optimizer games.** Call every function, assert nothing, report 100%. A build that bans stubs but measures coverage has simply moved the failure from *missing code* to *plausible-looking wrong code*: `return Haircut(dsr=0.5)` passes the no-stub check, passes the manifest check (it exists, it is called), and is a lie.

**Mutation score is the metric that catches it**, because it asks the only question that matters: *would your tests notice if this code were wrong?* It is the mechanised form of DoD-(b), and it is the one check in this document that cannot be satisfied by writing more code.

> **Substrate modules — `ledger/`, `costs/`, `fills/`, `validation/`, `core/` — require a mutation score ≥ 90%.** Runs on gate PRs and nightly, not on every push (it is slow). Below the threshold, the gate does not pass.

Engines and consoles are held to standard coverage. The substrate is held to mutation, because the substrate is shared truth and a silent defect there contaminates every trial that ever runs.

## 10. Completeness Standard — *the gate is a sample of the spec, not a summary of it*

**This section exists because §9 does not close the hole.**

§9 catches a build that **claims more than it delivered**. It does not catch a build that **delivers less than the spec, and claims exactly that**. A gate-minimal implementation passes every rule in §9 — its names are honest, its tests certify real machinery, its tags match its deliverables. It is simply *incomplete*, and it says so, and nothing stops it.

That is the observed failure mode of every previous project. It is a **spec failure, not a discipline failure**: an agent given a vague reference and a precise gate will build the precise thing. The gate is the only unambiguous object in the room, so the gate becomes the target. This is Goodhart's law operating on the build process, and the cure is not to exhort the agent — it is to make completeness as precise as the gate, and mechanical.

### 10.1 The deep dive is the specification

Inverted from the prior convention, which read: *"the deep dives are optional expanded reference; their absence or stub state never blocks a phase."*

That sentence is the root cause. It **told the agent the detail was optional.**

The rule is now:

> **A phase cannot begin until its deep dive is complete and its MANIFEST is frozen.**
> The deep dive is authoritative. This blueprint is an index.
> An outline is not a specification. A phase begun against an outline will be built to its gate.

### 10.2 Every phase has a MANIFEST

The manifest is an **exhaustive** enumeration of every artifact the phase produces: every module, every public function, every test, every doc, every CI check. It lives at the end of the phase's deep dive and is frozen before the phase opens.

```yaml
- id: P1.LEDGER.CHAIN
  artifact: lab.ledger.chain.append
  kind: function
  spec: "deep_dives/P1_substrate.md §4.2"
  call_site: required
  certifying_test: tests/unit/ledger/test_chain.py::test_append_links_prev_hash
```

**Two gates, not one:**

| Gate | Asks | Enforced by |
|---|---|---|
| **Correctness gate** | Does what exists behave correctly? | the phase's tests |
| **Completeness gate** | Does everything that should exist, exist — and is it called? | `check_manifest.py` |

A phase passes when **both** pass. The correctness gate alone has never been sufficient, and every previous project proved it.

### 10.3 Closed loop between spec and manifest

- Every deep dive section maps to **≥ 1** manifest row. A section with no row is unbuilt spec.
- Every manifest row maps to **exactly 1** deep dive section. A row with no section is unspecified work — and unspecified work is where the agent guesses, and guessing is where it minimises.

**Granularity is integer-section (heading depth 2: `## N. Title`).** Not subsection. Per-subsection coverage is provably impossible against the frozen manifests — P1 leaves §5.4, §9.1 and §9.2 rowless by design, as does P0 — and a rule that no frozen manifest can satisfy is a rule that gets turned off.

**Exempt sections** (front matter, not deliverables): `Scope` · `Why…` · `Failure modes and edge cases` · `Test plan` · `MANIFEST` · `GATE` · `Amendment log`. The list is hardcoded in the tool and short. A configurable exempt list is a loophole with a config file.

**Test plan ⊆ manifest.** The Test Plan section is exempt from *section* coverage — but every test **named** in it must be cited by some row's `certifying_test`, or listed in the manifest's `additional_tests:` block. Without this, a test can be specified in the deep dive and required by nothing, which is exactly the hole the exempt list would otherwise open. `check_manifest.py` parses both and asserts the containment.

**The residual risk — a deliverable subsection hiding under a covered parent — is not closed by the checker, and is not closed by a review step either.** It is closed by writing the manifest at the same time as the deep dive, before the phase opens, which is when the author still knows what every subsection was for.

`check_manifest.py` verifies both directions. The loop is what makes "build everything in the deep dive" a *well-defined instruction* rather than an aspiration.

### 10.4 No stubs. Mechanically.

`tools/check_no_stubs.py` fails the build on any of the following inside phase-scoped source:

- `TODO`, `FIXME`, `XXX`, `HACK`
- `NotImplementedError`
- a function body that is only `pass` or only `...`
- `@pytest.mark.skip` / `xfail` without an open, referenced `DIVERGENCES.md` entry
- a docstring containing "for now", "later", "temporary", "placeholder", "simplified"

This is blunt and it will occasionally be annoying. That is the intent. **The annoyance is the mechanism** — every one of these is the textual signature of a deferral, and a deferral that cannot be written down cannot be made silently.

### 10.5 Deferral is a logged amendment, never a silent skip

`DEFERRALS.md` **must be empty at every phase exit.** A phase does not merge with an open deferral.

If something in the manifest turns out to be genuinely unnecessary, the correct action is **not** to skip it. It is to:

1. Amend the deep dive (dated entry, what changed, why).
2. Amend the manifest (remove the row, citing the deep dive amendment).
3. Then it is out of scope, and the phase is complete without it.

**Scope may be changed. Scope may not be changed *quietly*, and it may not be changed *retroactively*.** This is the same ratchet the Lab imposes on its users, applied to its own construction. The Lab is not exempt from its own methodology.

### 10.6 Why completeness, and not YAGNI

The obvious objection: building everything in a phase, including what no gate tests, is speculative generality — and YAGNI exists for a reason.

It does not apply here, for a structural reason:

> **The phases are already minimal, and the substrate is shared.**

Options, paper trading, and the dashboard were cut from v1 already. What remains in a phase is the phase. And P1–P3 build the **substrate** — shared truth that every engine and every trial stands on. A hole in the substrate does not block the phase that leaves it. It blocks nothing at all. It simply becomes **load-bearing three phases later**, under four thousand trials, in a ledger nobody can now verify.

A stubbed hash chain passes P1's gate. By P6 you have an unverifiable ledger and no way back — it is append-only by design.

**Completeness is mandatory below the gate line (the substrate). Ordinary engineering judgement applies above it (strategies, which live on the user's disk and are not ours).**

---

## 11. Gate Integrity — *the gate must be out of the builder's reach*

Everything in §9 and §10 is enforcement. Enforcement that the builder can edit is decoration.

### 11.1 The spec is not writable in the same PR as the code

The manifest blocks the merge. The manifest is in the repo. The builder has write access to the repo.

**The cheapest way to pass a manifest gate is to edit the manifest.** The same is true of `CONSTITUTION.md`, `ACCEPTANCE.md`, and every frozen deep dive. A ratchet is not a ratchet if the builder is holding the wrench.

> **Any diff touching a governance document or a frozen MANIFEST *in the same PR as implementation code* fails CI.**
>
> Spec changes ship in their own PR, reviewed as spec changes, with the amendment-log entry attached and the reason stated.

Governed files: `CONSTITUTION.md`, `CONTRACTS.md`, `ACCEPTANCE.md`, `PLAYBOOK.md`, `docs/deep_dives/**`.

**Carve-out:** `HANDOFF.md`, `DEAD_ENDS.md`, `PROJECT_STATE.md`, and `DIVERGENCES.md` are **logs, not specs**. They are *required* to change alongside code and are exempt. `tools/check_spec_isolation.py` implements exactly this split.

### 11.2 Gate fixtures are derived, not recorded

**The engine may not be its own oracle.** The reproduction gates compare it against values **derived by hand**, from the cost schedule and the fill rules, before the engine exists.

- Each fixture ships with a **derivation document**: the scenario, the schedule rows applied, the arithmetic step by step, to the paisa.
- **A fixture that cannot be derived by hand is too large.** Shrink the scenario — a handful of instruments, a handful of bars — until it can. If you cannot compute the right answer yourself, you cannot tell whether the engine did.
- Fixtures land in a **separate, earlier PR** than the engine that must match them. `check_fixture_provenance.py` asserts the blob hash matches `ACCEPTANCE.md` **and that the fixture commit predates the engine commit**.

> **A fixture the engine produced is not a gate. It is a mirror.**
>
> This is the obvious way to cheat, and with hand-derivation it is the *only* one. It is therefore the thing the provenance check exists to stop.

**A hand-derived fixture has no platform.** Cost and position paths are `Decimal`/integer and bit-exact on any OS; float statistics are simple moments and survive 1e-10 trivially. The cross-platform reproduction problem is not *answered* by this design — it is *dissolved*.

### 11.3 The P0 bootstrap exception

The judge cannot be separated from the judged when the judge *is* the deliverable. Branch protection requires a `gate` status check that no workflow produces until `ci.yml` exists — so no PR, spec or code, can merge until one carrying CI does.

**One PR is permitted to mix the tiers: the first.** It carries governance, `LICENSE`, `NOTICE`, `.github/workflows/ci.yml`, `tools/gate.py`, and whichever checkers exist. GitHub runs workflows from the PR head, so it self-satisfies its own gate — genuinely, not vacuously, because `tools/gate.py` **fails closed on zero registered checkers.** *"Nothing to check"* is not *"all checks passed."*

**Do not admin-bypass. Do not temporarily un-require the gate.** Both are the pattern this project exists to refuse, and doing either on the *first* merge sets the precedent for every merge after it. §11.1 binds absolutely from the second PR onward.

---

## 12. Session Protocol — *the branch is the unit of completeness, not the session*

P1 alone has ~40 manifest rows and ~50 tests. **It will not fit in one session, and pretending otherwise creates the exact pressure this document exists to remove.**

The specific danger is precise: an agent running low on context degrades, begins economising, and the manifest gate stops being a thing to satisfy *honestly* and becomes a thing to satisfy. **The rule intended to enforce completeness would then cause the stubbing.**

So the unit changes:

> **A phase may span sessions. A PR may not merge partially.**
>
> A session **never** ends with a stub that makes a check pass. It ends with an honest red and a written account of what is not built yet.

### 12.1 Session-end ritual — every session, without exception

1. Run `python tools/gate.py`. **Paste the output verbatim** into `HANDOFF.md`. Do not summarise it, do not retype it — pipe it. Typed status is a claim; piped status is evidence.
2. Update the manifest tally (generated by `check_manifest.py`, never hand-counted).
3. Write the session-log entry: built · rejected · uncertain · blocked.
4. Append anything learned the hard way to `DEAD_ENDS.md`.
5. Rewrite the **Cold Start** block at the top of `HANDOFF.md`.
6. Commit on the phase branch: `docs: session N handoff`.

### 12.2 The handoff is written continuously, not at the end

A handoff composed by a context-exhausted agent is composed by the *worst* version of that agent, at the moment its judgement is most degraded. Update `HANDOFF.md` as the session runs — after each meaningful decision, each rejected approach, each surprise.

The end-of-session ritual is a **checkpoint, not the writing**.

### 12.3 The handoff obeys the Lab's own methodology

`HANDOFF.md` is a ledger. It carries the same properties as the trial ledger, and for the same reasons: append-only history, every claim tagged with its evidence, no "done" without a test name, and a hard distinction between what was **verified**, what is merely **asserted**, what the **operator** decided, and what the **builder** decided and still needs review.

A builder's suggestion is not an operator's decision, however enthusiastically it was received. The handoff never promotes one to the other.

---

## Project-Specific Inviolable Rules

These override convenience, "just make it work," and the operator.

**1. Ambiguity is a spec bug, not a decision to be made.**
An agent resolving ambiguity resolves it toward the interpretation that is **cheapest to build**. Not dishonestly — it genuinely looks like the reasonable reading from where it is standing.

If a deep dive is ambiguous mid-phase, the deep dive was incomplete, which means **the phase should never have opened**. Stop. Amend the deep dive. Re-freeze the manifest. Resume. Do not choose. Do not choose-and-note.

**2. No optimisation may weaken an invariant.**
The ledger will feel slow. The proposals will arrive on schedule: *"batch the fsync"*, *"drop the lock — appends are atomic anyway."* Both sound reasonable. One loses your last row on a crash; the other silently forks the chain the moment two agent processes run in parallel.

**If the ledger is too slow, build a faster ledger. Not a weaker one.**

**3. The builder refuses the operator when the operator is wrong.**
`PLAYBOOK.md` tells the *operator* what to do under pressure. Nothing else tells the *builder* what to do when the **operator** is the one erring — and the operator is the sole reviewer, and the operator is the one who will be six months in with sunk cost, asking for one small softening.

> The builder refuses any instruction that violates the Constitution, cites the section, and does not proceed. **Including — especially — when it comes from the operator.**

This rule is uncomfortable. That discomfort is the evidence it is correct: the Constitution was written precisely because future-you cannot be trusted with it.

**4. The engine is never its own oracle.**

Gate fixtures are **derived by hand** — from the cost schedule and the fill rules, before the engine exists, with the arithmetic shown to the paisa. No expected value is ever taken from an implementation. Not the engine's. Not any other program's.

**If you cannot compute the right answer yourself, you cannot tell whether the engine did.**

**5. The kill-gate is sacred.** No strategy is an edge without passing the full battery. No tweaking-until-it-passes — every variant it spawns is charged to the ledger. **Most strategies should die at the gate. That is success.**

**6. Point-in-time correctness, always.** Structurally, not by discipline.

**7. Costs are always modelled.** No gross-only results outside the named `GROSS_ONLY` research mode, which does not return a Sharpe.

**8. Build in dependency order; respect the gates.** Do not proceed past a failed gate.

**9. Ground every decision in the deep dive, and cite it.** The deep dive is authoritative and complete before the phase opens. If it is silent or self-contradictory, that is Rule 1 — stop and amend, do not guess.

---

# PART II — SYSTEM OVERVIEW & LOCKED DECISIONS

`CONSTITUTION.md` is authoritative for everything in this Part. What follows is a summary for orientation. Where they differ, the Constitution wins.

## What we are building

The machine, not the cartridges. A research kernel that makes an honest backtest possible and a dishonest one difficult, for Indian cash equity, released open-source under Apache-2.0.

**The contract:** *every hypothesis must be expressible as a P&L stream after costs.* A signal that cannot pay the spread is not a finding.

## Refusals — permanent, not deferrals

No live execution. No strategies. No signals. No data redistribution. No published backtest returns as marketing. **No telemetry, ever.** No hosted service. Not "research anything" — systematic strategy research only.

These are the product's identity, and every one will be attacked by a reasonable-sounding request. See `CONSTITUTION.md` §4, §6.

## Locked decisions

| Decision | Rationale |
|---|---|
| Apache-2.0 | Explicit patent grant; appropriate for finance-adjacent |
| Engines isolated; substrate shared | Engines may duplicate logic, never truth |
| Engine declared, never inferred | Misrouting is a silently wrong cost model, and it does not crash |
| Money is Decimal / integer paise | Makes tolerance-0 gate reproduction achievable |
| JSONL source of truth; SQLite derived | The ledger export must be diffable and hash-verifiable by a stranger |
| Ledger is hash-chained | Otherwise the export is a screenshot, not a proof |
| Trial identity is **behavioural** | An LLM regenerates identical logic with new variable names indefinitely |
| Recording install-wide; **counting scope** is the setting | Preserves user choice, makes evasion visible rather than impossible |
| `unsafe` overrides taint; agents never get them | An agent that could taint its own trials would taint them all and proceed |
| Defaults ship, but ratchet | A tool with no defaults is a religion; a default that moves quietly is a lie |
| **No timeline. Ever.** | A deadline is a force pushing against a gate that must not bend |

## Realistic-expectations frame — keep visible

SEBI's own data: over 90% of retail F&O traders lose money. Build this honestly and **the modal outcome for a user is that the Lab correctly tells them they have no edge.** That is the socially valuable result and a catastrophic growth funnel. Every competitor will show them a prettier number.

If we are at peace with a small user base of people who wanted the truth, we have a real product. If we are not, we will start softening the machine — and the softening is indistinguishable from becoming everyone else.

---

# PART III — TECHNICAL REFERENCE

`CONTRACTS.md` is authoritative. This Part orients; the deep dives specify.

## 1. The substrate (shared, single implementation, program-wide)

The trial ledger · the as-of clock · the cost kernel · the fill gate · the data plane and PIT correctness · trial identity and the haircut · the validation battery.

**An engine that computes a cost is a build failure.** Enforced by import-graph test.

## 2. The engines (isolated, duplicated freely)

The loop · fill mechanics · position lifecycle · square-off, expiry, assignment.

`equity-daily` and `equity-intraday` are **separate loops**. No shared loop. No mode flags. Duplicated engine loops are cheap; a wrong abstraction is not, and every subtle lookahead bug in this system's future would live inside those conditionals, unlooked-at.

**An engine is defined by its simulation semantics, not by what it computes.** Feature computation is a *library*, not an engine.

## 3. Costs are dated facts, not settings

Statutory rates (STT, exchange charges, SEBI turnover fee, stamp duty, GST) are **identical for every Indian retail trader** and are precisely the costs retail systematically forgets. They are locked. Brokerage, plan, and DP markup are the **broker profile** — curated, versioned, named (`zerodha`, `upstox`, `custom`), never a blank form.

**Costs are point-in-time data.** STT has moved; stamp duty was unified in 2020; exchange charges have been revised more than once. A 2019 backtest run against today's schedule has a **lookahead leak in the cost model** — in a system whose entire pitch is honest costs. The schedule carries an effective-from date and the engine looks it up per trade date, exactly as it looks up prices.

Every statutory row carries a **primary source URL**.

**One decomposition trap, flagged now because it is a live error class, not a P2 detail:** a market order pays one *half*-spread relative to the midpoint, and a midpoint-measured impact number already contains it. Summing `fees + half_spread + midpoint_impact` double-charges the crossing cost. Cost correctness is the product; this sum is wrong and P2 must not implement it. (Verified against market-microstructure primary sources.) This is the one part of the repo strangers will independently audit; you will need a citation, not a memory.

## 4. The fill gate — *could this order have been filled?*

One question, one implementation, every engine, every fill.

- **Circuit bands.** You cannot buy a stock locked at upper circuit — there is no seller. Every momentum and breakout backtest in Indian small- and mid-caps has been enormously profitable by buying stocks at the exact moment they became unbuyable. This is *the* systematic fiction in Indian retail backtesting, and no generic backtester models it because it is not a US phenomenon.
- **Series.** `EQ` is normal. `BE`/`BZ` are trade-to-trade — **intraday square-off is impossible; delivery is compulsory.** A stock *moving into* BE is itself an event.
- **Liquidity.** ADV participation, spread.

## 5. Point-in-time universe — a rule, not a list

`top_500_by(adv_60d)` filtered on price, listing age, and series — evaluated **fresh at every date** against bhavcopy.

Survivorship-free **by construction**: the day's bhavcopy contains the stocks that traded that day; a company delisted in 2019 appears through 2019 and then stops. The bias is not *fixed* — it is never *introduced*.

**ISIN is the primary key. Never the symbol.** Tickers are renamed and reused; symbol identity will one day splice two companies into one price series, and nothing will crash.

Index membership is an *optional* adapter for index-relative research. Without dated membership, the cross-sectional engine **hard-refuses**. It does not warn.

## 6. The ledger, and why it cannot be a log level

Append-only JSONL, hash-chained. SQLite is a derived, disposable index. Trial identity is **behavioural** (position-series hash), with an AST pre-check for free reruns.

The hash chain is what converts the export from a claim into a **proof**: delete trial #47 and every subsequent hash breaks, visibly, to anyone. In a market saturated with screenshotted fake backtests, a verifiable ledger — *every trial, every failure, every parameter change* — is a flex nobody can currently make, precisely because the failures are what make it credible.

## 7. Validation, and the number that matters

Walk-forward · DSR · PBO · **cluster-adjusted effective-N**.

The DSR threshold grows as `√(2 ln N)` — brutally slowly. Fifty trials needs an observed Sharpe of ~1.0; a thousand needs ~1.5; a hundred thousand needs ~1.9. **The arithmetic is robust to agent-scale search — but only if effective-N is right.**

Which is why the **LLM-generated null test is the load-bearing calibration**, not the random one. Random strategies are near-independent, so the random null test passes whether or not clustering works. LLM strategies are momentum with forty-seven lookbacks. Raw N of 1,000 may be an effective N of fifteen.

**Effective-N is the safety-critical component of this system.**

## 8. The power calculator — at the front, not the end

*Given your data length and your declared trial budget, here is the minimum Sharpe that could ever be believable.*

Nobody ships this. It changes behaviour in a way no post-hoc haircut ever will, because it fires **before** someone burns six months. It is the natural companion to the cost-viability pre-check: one says the costs make it impossible; the other says the search budget makes it unprovable.

## 9. The agent boundary

LLM agents are a first-class caller and, structurally, an adversary — not from malice, but because an optimizer told to obtain a PASS routes around whatever stands between it and a PASS.

| Agent gets | Agent never gets |
|---|---|
| Read: ledger, verdicts, taints, cost breakdown, power calculator | The cost model |
| Write: **hypotheses only** | The slippage floor |
| The graveyard, as context | The haircut scope |
| Its trial count, haircut, and remaining budget | The thresholds |
| | **`unsafe`** |

**Effective-N flips from tax to instrument.** *"Your last 200 proposals collapsed to 4 effective clusters. You are not exploring. You are jittering."* The failure mode of an automated quant loop is not running out of compute — it is mistaking repetition for exploration.

---

# PART IV — THE BUILD PROGRAM

One ordered path. P0–P3 build the substrate. P4–P5 build the engines and prove the abstraction. P6–P7 build the judge and the surfaces. P8–P9 release.

`ACCEPTANCE.md` holds the binding exit criteria for every phase. Each phase's deep dive holds its MANIFEST. **Neither is negotiated at the end by whoever is looking at the diff.**

---

## PHASE 0 — Repository, remote, and the enforcement machinery

*Deep dive: `docs/deep_dives/P0_scaffold.md`*

- **P0.1 — GitHub remote.** Private repo created **first**, before any code. `main` protected: CI required, linear history, no direct push.
- **P0.2 — Scaffold.** Structure per Part I §3. `pyproject.toml`, ruff/black/mypy/pytest, `.pre-commit-config.yaml`, `.gitignore` (incl. `CLAUDE.md`, `.claude/`), `.github/workflows/ci.yml`.
- **P0.3 — Attribution suppression.** `.claude/settings.json` with `attribution: {commit: "", pr: ""}`; `commit-msg` hook stripping trailers; `tools/check_attribution.py` scanning full history in CI.
- **P0.4 — The completeness machinery.** `tools/check_manifest.py`, `tools/check_no_stubs.py`, `tools/check_import_graph.py`. `tools/gate.py` runs all of them plus the tests. **These are built before the code they police.**
- **P0.5 — Governance and legal.** Constitution, Contracts, Acceptance, Playbook, Divergences, Deferrals, Project State — **plus `LICENSE` (Apache-2.0) and `NOTICE`.** A repository with no licence is "all rights reserved" by default, and that is the wrong default to hold for even one day.
- **P0.6 — Core types and Protocols.** `Strategy`, `Engine`, `TrialResult`, `Taint`, `MarketView`, `CostProfile`, `DataSnapshot`. Fully typed; trivial fakes type-check.

**GATE 0:** remote exists, `main` protected, CI green, the completeness machinery **passes on itself** (the manifest check finds its own manifest; the no-stub check finds no stubs; the attribution check finds no attribution). Tag `gate-0-scaffold`.

> P0.4 before everything is not ceremony. Building the enforcement machinery *after* the code it polices means the first phase is built unpoliced — and that is the phase that builds the substrate everything else stands on.

---

## PHASE 1 — Substrate: ledger, clock, haircut

*Deep dive: `docs/deep_dives/P1_substrate.md` — **complete before this phase opens***

The ledger goes in **first**, before any engine exists.

- **P1.1 — Trial schema.** `TrialResult`, `Taint`, ledger row. `taints[]` present from the first row ever written — retrofitting it later means migrating a hash-chained append-only log, which is the one data structure designed to make that painful.
- **P1.2 — Append-only JSONL + hash chain.**
- **P1.3 — SQLite derived index.** Disposable. `rebuild-index` from JSONL alone. No write path bypasses JSONL.
- **P1.4 — The as-of clock.** Owned by the engine. `MarketView` contains nothing after `asof`. A `Strategy` has no clock, no filesystem, no network.
- **P1.5 — Trial identity.** Two-tier: AST pre-check, position-series behavioural hash.
- **P1.6 — Haircut, raw-count placeholder.** Deliberately cruder and *strictly more punitive* than clustering — a placeholder that can only over-penalise, never under.
- **P1.7 — Taint mechanics.** In the hash, under the chain, blocks pooling, on the export.

**GATE 1:** no `TrialResult` can exist without a ledger row; tamper is detectable; a strategy cannot read the clock; reruns are free; a seed change is a new trial.

---

## PHASE 2 — Cost kernel *(parallel with P3)*

*Deep dive: `docs/deep_dives/P2_costs.md`*

- **P2.1 — PIT statutory schedule**, ~2015→present, every row dated and **source-cited**.
- **P2.2 — Broker profiles**, curated and versioned.
- **P2.3 — Slippage floor**, tied to tick size / spread / ADV participation.
- **P2.4 — Cost-model hash** stamped into every trial.
- **P2.5 — Instrument-class slots.** Equity populated. **Options slot exists and is empty**, and the README says so — shipping an options number means owning the STT-on-exercised-ITM trap, and a Lab that claims options and gets that wrong is a liability with a nice API.

**GATE 2:** a 2019 backtest uses 2019's STT, and the engine proves it. 100% of statutory rows carry a date and a source URL. No float in the cost path.

---

## PHASE 3 — Data plane *(parallel with P2)*

*Deep dive: `docs/deep_dives/P3_data.md`*

- **P3.1 — Adapter interface + provenance tiering** (`self-captured` vs `third-party-archive`).
- **P3.2 — Adapters:** Kite, Upstox, CSV/Parquet. **No scraping adapters shipped** — that is ToS exposure handed to users.
- **P3.3 — Canonical format.** Nothing enters an engine un-normalised.
- **P3.4 — Validator battery.** Adjustment status is a **required declared field**; undeclared refuses to run. Survivorship: an undated constituent list **hard-refuses** the cross-sectional engine.
- **P3.5 — PIT rule-based universe** from bhavcopy. ISIN identity. Series as a PIT field.
- **P3.6 — The fill gate.** Circuit bands (sourced, heuristic fallback tagged), series, liquidity.
- **P3.7 — Synthetic dataset.** The null and power fixtures.

**GATE 3 — the honesty self-test:**
- `test_null_hypothesis` — 1,000 random strategies on noise → **≤10%** pass
- `test_null_hypothesis_llm` — 1,000 **LLM-generated** strategies on noise → **≤10%** pass. **Load-bearing.**
- `test_power` — planted net Sharpe 1.0, 5y daily, 50-trial budget → **≥60%** detection

> Nobody else ships a proof that their backtester correctly finds *nothing* in *nothing*. It is the strongest claim available and the cheapest to make.

---

## PHASE 4 — Engine A: daily cross-sectional → **GATE 4**

*Deep dive: `docs/deep_dives/P4_engine_daily.md`*

**The engine is not its own oracle.** It is judged against **ground truth derived by hand** from the cost schedule and the fill rules — never against its own output.

Analytical fixtures land in an **earlier PR**, each with a derivation document showing the arithmetic to the paisa. Then: tolerance 0 on cost and position paths, 1e-10 relative on float statistics. Property suite. `test_behavioural_dedup`.

**Ends with the SUBSTRATE FREEZE** — tag `substrate-frozen`. Everything the second engine does must fit under it.

---

## PHASE 5 — Engine B: intraday → **GATE 5: THE KILL GATE**

*Deep dive: `docs/deep_dives/P5_engine_intraday.md`*

**This is the phase where the project dies if it should die.**

Separate loop. No shared loop with P4. No mode flags in either. Its own hand-derived fixtures. Intraday property suite. `test_cross_engine_cost_reconciliation` — a daily strategy through the intraday engine at one bar per day must produce **identical** costs, or a cost model has forked.

### The kill gate proper — substrate invariance

`check_substrate_purity.py`, against the `substrate-frozen` tag:

- every change to `src/lab/{core,ledger,costs,fills,validation}` since Gate 4 is declared **engine-agnostic** in the PR body, with justification
- **automatic failure** on engine-specific vocabulary anywhere in the substrate: `intraday` · `daily` · `square_off` · `squareoff` · `MIS` · `engine_id ==` · `isinstance(engine`

**STOP CONDITION (Constitution S1):** if the intraday engine cannot be built without a mode flag in an engine loop, **or** without an engine-specific change to shared truth, the abstraction is wrong. **Stop.** The Lab is not released. Do not patch.

> This tests the thing that was actually at stake, directly rather than by proxy: **can one contract hold two dissimilar simulation semantics without contaminating the truth beneath them?** If it cannot, the premise of the Lab is false, and the honest thing is to discover that here — cheaply, before release — rather than after.

> An agentic builder confronted with a failing gate will try to make it pass. That is the single largest threat to this project's integrity. It is why the fixtures exist before the engine, and why the substrate is tagged before the second engine is written.

---

## PHASE 6 — Validation battery

*Deep dive: `docs/deep_dives/P6_validation.md`*

Walk-forward · DSR · PBO · **cluster-adjusted effective-N** replacing the raw-count placeholder · per-trial daily P&L series, content-addressed · **the power calculator, at the front of the workflow**.

**GATE 6:** all three calibration tests re-pass *after* clustering. Clustering *reduces* effective-N and therefore *loosens* the haircut — this is exactly where a null test starts failing, and the LLM one will fail first.

---

## PHASE 7 — Consoles and the machine interface

*Deep dive: `docs/deep_dives/P7_consoles.md`*

Telescope (human, debug) · court record (human, epistemic) · machine interface (agent, boundary-enforced).

The meter prints at the start **and** end of every run: `trials: N (install) / M (scope) | haircut: DSR x → y`. Not in a report at the end. **In your face, while you search** — that is the whole psychological mechanism, and it costs one line of code.

The graveyard shows beside the survivors, with equal weight. Hide the pile and the survivors look like skill.

---

## PHASE 8 — Release hardening → **GATE 8: RED TEAM**

*Deep dive: `docs/deep_dives/P8_release.md`*

API freeze · semver · Apache-2.0 + NOTICE · Docker + `uv.lock` + content-addressed data snapshots · honest reproducibility contract in the README · security review of the credential path · zero telemetry verified by grep, not intent · lawyer.

**Red-team gate:** point an agent at the Lab with the objective *"obtain a PASS verdict on pure noise, by any means."* Every seam it finds is a bug. Close it. Re-run.

---

## PHASE 9 — Private alpha → public

*Deep dive: `docs/deep_dives/P9_release.md`*

Small N of users chosen for their willingness to say the machine is wrong. Publish both calibration numbers — they are the only performance claims the Lab makes. Review the stop conditions.

---

# PART V — PROGRESS LOG

Updated at the end of every session. Tracks **criteria met, not days elapsed** — there is no schedule here by design.

**Gate status:** G0 ☑ · G1 ☐ · G2 ☐ · G3 ☐ · G4 ☐ · **G5 (kill gate)** ☐ · G6 ☐ · G7 ☐ · G8 (red team) ☐ · G9 ☐

**Deferrals open:** must be **0** at every phase exit.

| Date | Phase | What moved | What broke |
|---|---|---|---|
| — | P0 | Governance ratified; blueprint written | — |
| 2026-07-19 | P0 | **GATE 0 MET.** Tagged `gate-0-scaffold`. The enforcement machinery is built and passes on itself: seven checkers, each with a planted violation and a negative control; 32/32 manifest rows; 93 tests; CI green on three platforms. | The §5.4 bootstrap exception has self-closed — §11.1 binds absolutely from here. Six manifest rows reclassified `required` → `n/a` by amendment A-004; their consumers arrive in P1. |

---

# PART VI — REFERENCE FILES

| File | Status | Purpose |
|---|---|---|
| `HANDOFF.md` | **live log** | Current phase state. **Read first, every session.** Updated continuously, not at the end. Exempt from §11.1. |
| `DEAD_ENDS.md` | permanent | What was tried and failed, and why. Never pruned. Saves the next session a day. Exempt from §11.1. |
| `CONSTITUTION.md` | binding · spec | Scope, refusals, pinned numbers, invariants, stop conditions |
| `CONTRACTS.md` | binding · spec | Strategy, Engine, trial identity, taints, agent boundary |
| `ACCEPTANCE.md` | binding · spec | Per-phase exit criteria; gate fixture blob hashes |
| `PLAYBOOK.md` | pre-committed · spec | Responses to the builder, to yourself, to users, to the agent |
| `DIVERGENCES.md` | permanent · log | Accepted gate divergences. Public. |
| `DEFERRALS.md` | living · log | **Must be empty at every phase exit** |
| `PROJECT_STATE.md` | living · log | Phase board, decisions, blocked items |
| `docs/deep_dives/PN_*.md` | **the specification** | Complete before its phase opens. Contains the phase MANIFEST. |

**Tools** (`tools/`, all wired into `tools/gate.py`):

| Tool | Enforces |
|---|---|
| `check_manifest.py` | Every manifest row exists and is called (DoD-a, §9) · spec↔manifest closed loop (§10.3) · `DEFERRALS.md` empty |
| `check_no_stubs.py` | No `TODO`, `NotImplementedError`, `pass`-only bodies, or deferral language (§10.4) |
| `check_spec_isolation.py` | Spec and code never in the same PR (§11.1) |
| `check_fixture_provenance.py` | Gate fixture blob hashes match `ACCEPTANCE.md` (§11.2) |
| `check_import_graph.py` | Substrate boundaries: nothing outside `costs/` computes a cost; `TrialResult` constructed only in `ledger/` |
| `check_attribution.py` | No AI **authorship** in commit/tag/PR *metadata* (trailers, author/committer identity) — **not** a grep of file contents for the word "Claude" (§6, P0 §4.3) |
| `check_substrate_purity.py` | **The kill gate.** No engine-specific change to shared truth since `substrate-frozen` (§11.2, Constitution S1) |
| `gate.py` | Runs all of the above. **Fails closed on zero checkers.** |
| `mutmut` / `cosmic-ray` | Mutation score ≥ 90% on substrate modules (DoD-b, §9.8) |
