# DEAD ENDS

> **Global. Permanent. Never pruned.** A dead end found in P1 still matters in P6.
>
> Read this after `HANDOFF.md`, before you write any code.

---

## Why this file exists

The single highest-value section of any handoff is *"what I tried that didn't work, and why"* — and it is the section everybody omits, because at the end of a session the failures feel like noise and the successes feel like the story.

They are backwards. **The successes are already in the code. The failures are only here.**

Without this file, the next session re-walks the same dead end. That is a wasted day, which is bad. But the real danger is worse: **it may not recognise the dead end as one.** It reaches the same wrong answer, sees no reason to distrust it, and ships it — because the reason to distrust it lived in a session that has since been garbage-collected.

## Rules

1. **Append-only.** A dead end is never deleted. If it is later shown to be wrong — the approach *does* work — append a `REOPENED` entry with the evidence. Do not edit the original.
2. **State the mechanism, not the vibe.** *"It was slow"* is useless. *"The advisory lock is held across the fsync, so 16 parallel agents serialise on disk flush and throughput collapses to ~40 rows/sec"* is a gift.
3. **Say what you would need for it to work.** Half of these are not permanently dead — they are dead *given current constraints*. Name the constraint.
4. **Log it while it is fresh.** At the end of the session you will not remember why it failed, only that it did — and *that* it did is the useless half.

## Categories

| Tag | Meaning |
|---|---|
| `[ARCH]` | Architecture / design approach that does not hold |
| `[PERF]` | Performance approach that does not pay for itself |
| `[LIB]` | Library or tool that does not do what its docs claim |
| `[DATA]` | Data source that is unusable, incomplete, or lying |
| `[TEST]` | Testing approach that certifies nothing |
| `[CONSTRAINT]` | Blocked by a constraint that may one day lift — **name the constraint** |

---

## Entries

### DE-001 — `[TEST]` — Word-boundary matching for the kill gate's engine vocabulary

**Session:** 2 · **Phase:** P0 · **Date:** 2026-07-19

**What was tried:**
`check_substrate_purity.scan_vocabulary` matched each banned term with `\bTERM\b`,
case-insensitively, reasoning that word boundaries prevent `daily` from firing inside
unrelated identifiers.

**Why it failed:**
`\bsquare_off\b` **does not match `square_off_at`**. `\b` requires a non-word character
after `off`, and `_` is a word character. The planted fixture added
`square_off_at: str | None = None` to `src/lab/ledger/schema.py` and the checker reported
clean on it.

This is the realistic shape of the failure, not a contrived one: engine vocabulary enters a
substrate as a *field name*, not as a bare word. The rule matters because the kill gate is
the mechanism behind Constitution S1 — a false negative there ships a contaminated substrate
under two engines, and it is discovered, if ever, by whoever audits the ledger.

**Evidence:**
`python tools/check_substrate_purity.py --root tests/completeness/fixtures/substrate_purity`
reported 3 findings and omitted `square_off`. After the fix: 5 findings, including it.
Pinned by `test_substrate_purity_rejects_engine_vocabulary`, which asserts `'square_off'`
explicitly with the message *"a suffixed identifier slipped through the kill gate"*.

**Would it ever work?**
Permanently dead for identifier-like terms. Substring matching, case-insensitive, is correct
here: §9.2b says *anywhere in the substrate*, and on a kill gate a false positive costs an
argument while a false negative costs the premise of the project.

**Do not retry unless:** never. The one term that *does* need word-boundary, case-sensitive
matching is `MIS` — as a case-insensitive substring it fires on "mismatch", "permission" and
"dismiss", and a kill gate that cries wolf on ordinary English is one somebody disables
before Gate 5.

---

### DE-002 — `[TEST]` — Grepping a file for the defect its own comments describe

**Session:** 2 · **Phase:** P0 · **Date:** 2026-07-19

**What was tried:**
`test_commit_msg_hook_uses_no_gnu_only_sed_extension` asserted `"sed -i" not in hook` and
`"/Id" not in hook`, reading the whole file.

**Why it failed:**
The rewritten hook's comment block **explains the defect it replaced**, and therefore quotes
`sed -i.bak -E '/.../Id'` verbatim. The test flagged the explanation as the offence. The
only ways to make it pass were to delete the explanation — losing the reason the code looks
the way it does — or to weaken the assertion.

This is DE-000l's mistake at small scale: **scanning text when the subject is behaviour.**
It recurs because it is always the cheapest thing to write.

**Evidence:** the test failed on a hook that was already correct and already portable.

**Would it ever work?** Yes, and it now does: comment lines are stripped before the
assertion, so the check reads executable content only. It also gained a positive assertion
(`"grep" in executable`) so that deleting the implementation entirely does not pass.

**Do not retry unless:** you are checking a property of *text*. For properties of *code*,
strip comments — or better, execute it.

---

### DE-003 — `[TEST]` — Asserting local git config in a test that must survive a fresh clone

**Session:** 2 · **Phase:** P0 · **Date:** 2026-07-19

**What was tried:**
`test_hooks_path_set_before_first_commit` asserting `git config --get core.hooksPath ==
".githooks"`, the literal reading of §3.1 and failure case 19.

**Why it failed:**
`core.hooksPath` is **working-copy state and leaves no trace in a repository's history.**
Every CI runner is a fresh clone and has none, so the test would have gone red on all three
legs of the §5.2 matrix while the invariant it names was perfectly intact — a false failure
that teaches the next agent the test is unreliable, which is how a real failure later gets
waved through.

Worse, the literal claim is *unverifiable after the fact by anyone*: nothing distinguishes a
repository where the config was set before the first commit from one where it was set after.

**Evidence:** reasoning, plus the observation that `git clone` copies no local config.

**Would it ever work?** Not as stated. What is checkable is the invariant's **shadow** — the
observable consequences that survive cloning:

  * `.githooks/commit-msg` is present in the **first commit**, at index mode `100755`
  * the first commit's message carries no attribution trailer

A hook wired up after the first commit cannot produce both. Recorded as D-006.

**Do not retry unless:** the test is scoped to a developer machine and is not in CI — at
which point it is not a gate.

---

### DE-004 — `[TEST]` — Fixing a finding where you found it, and not where else it lives

**Session:** 2 · **Phase:** P0 · **Date:** 2026-07-19

**What was tried:**
DE-003 established that `core.hooksPath` is working-copy state which `git clone` does not
carry, and that asserting it in anything CI runs is asserting a property of the runner.
`test_hooks_path_set_before_first_commit` was rewritten accordingly. **The identical
assertion in `check_manifest.check_infra` was left untouched**, because the finding was
filed as a fact about *that test* rather than as a fact about *the invariant*.

**Why it failed:**
The first real CI run went red on **all three matrix legs** with
`P0.BOOT.GIT: core.hooksPath is '', expected '.githooks'` — the same defect, in the
checker rather than the test, roughly forty minutes after it had been diagnosed, written
up, and fixed elsewhere in the same session.

The mechanism is not carelessness about the fix; the fix was correct. It is that a dead
end gets recorded against **the symptom's location** instead of **the invariant's scope**,
so the search for other instances never happens. The local gate stayed green throughout,
because the developer machine is precisely the environment where the wrong assertion
holds.

**Evidence:**
`gh run view 29679712178 --log-failed` — three legs, one message. Local `tools/gate.py`:
`GATE GREEN -- 10 stages passed`, on the same commit.

**Would it ever work?** The assertion never works anywhere a clone is fresh. The checker now
asserts what survives cloning — `.githooks/commit-msg` tracked at index mode `100755` — and
treats an **unset** hooks path as acceptable (CI never commits, so it needs no commit-msg
hook) while still failing a hooks path aimed **elsewhere**, which disables the hook without
removing it.

**Do not retry unless:** never. And the general lesson, which is the reason this entry exists
separately from DE-003: **when a dead end is found, grep for every other site with the same
shape before closing it.** Ask what the finding is about — here, "local git config is not a
repository property" — and search for *that*, not for the file it was noticed in. A green
local gate is not evidence of absence when the defect is environment-shaped.


---

## Template

```markdown
### DE-001 — [ARCH] — <one-line summary>

**Session:** N · **Phase:** PX · **Date:** YYYY-MM-DD

**What was tried:**
<The approach, concretely. Enough that someone could rebuild it.>

**Why it failed:**
<The MECHANISM. Not "it didn't work." What, specifically, broke, and why
was that inevitable rather than a bug we could have fixed?>

**Evidence:**
<Test that failed, benchmark number, error, or the reasoning that closed it.>

**Would it ever work?**
<Permanently dead, or dead given a constraint? If the latter — name the
constraint and what would have to change.>

**Do not retry unless:**
<The specific thing that would have to be different.>
```

---

## Pre-seeded — closed before the build, by design

These are not failures we suffered. They are approaches **ruled out during design**, recorded here so that a future session does not rediscover them as clever ideas and quietly adopt one.

### DE-000a — `[ARCH]` — One unified engine with a mode flag

**Do not** unify `equity-daily` and `equity-intraday` into one loop branching on instrument type or bar frequency.

**Why:** every subtle lookahead bug in this system's future would live *inside* those conditionals, where nobody looks. Duplicated engine loops are cheap; a wrong abstraction is not.

**This is a Constitution stop condition (S1).** If Gate 5 cannot clear without a mode flag, **the project stops** — it does not get a flag.

### DE-000b — `[ARCH]` — Trial identity from source text alone

**Do not** define a trial by hashing the strategy's AST alone.

**Why:** an LLM regenerates identical logic with new variable names indefinitely. Textual identity would inflate the haircut on *repetition* rather than on *search* — penalising the honest and rewarding the verbose. Identity is **behavioural**: the net P&L series. See `CONTRACTS.md` §Trial identity.

### DE-000c — `[ARCH]` — Trial identity from the position series

**Do not** use positions as the behavioural hash — it is the near-miss, and it looks right.

**Why:** two engines can produce *identical positions* and *different costs* (delivery pays the DP floor; intraday does not). Identical positions can therefore be different bets. The **net P&L series** is the bet.

### DE-000d — `[PERF]` — Batching the ledger fsync, or dropping the append lock

**Do not**, under any pressure, including your own.

**Why:** batched fsync loses the last rows on a crash — a bypass triggered by pulling the power cable. Dropping the lock silently forks the chain the moment two agent processes run in parallel, which is the *first* thing anyone does with an agent.

**Inviolable Rule 2:** if the ledger is too slow, build a faster ledger. Not a weaker one.

### DE-000e — `[TEST]` — Line coverage as the substrate quality bar

**Do not** gate the substrate on line coverage.

**Why:** it is the metric an optimizer games — call every function, assert nothing, report 100%. The substrate is gated on **mutation score ≥ 90%**, which asks the only question that matters: *would the tests notice if this code were wrong?*

### DE-000f — `[TEST]` — Letting the engine be its own oracle

**Do not** produce the P4/P5 reproduction fixtures by running the engine and recording what it said. **Do not** take an expected value from any implementation, of any kind.

**Why:** a fixture the engine produced is not a gate. **It is a mirror.** It will pass, it will look like rigour, and it will certify whatever the engine happens to do — including whatever it does wrong.

Fixtures are **derived by hand** from the cost schedule and the fill rules, before the engine exists, with the arithmetic shown to the paisa. If a scenario is too big to derive by hand, it is too big — shrink it. **If you cannot compute the right answer yourself, you cannot tell whether the engine did.**

This is the single easiest way to defeat Gates 4 and 5, and it will present itself as a shortcut every time. `check_fixture_provenance.py` asserts the fixture commit predates the engine commit for exactly this reason.

### DE-000g — `[DATA]` — Current index constituents as a backtest universe

**Do not** build a cross-sectional universe from today's NIFTY 500 membership.

**Why:** survivorship bias, and it will look *fantastic*. Every result is garbage and nothing crashes. The universe is a **PIT rule** evaluated per date against bhavcopy (`top_N_by(adv_60d)`), which is survivorship-free by construction — the bias is never *introduced*, so it never needs *fixing*.

An undated constituent list **hard-refuses** the cross-sectional engine. It does not warn.

### DE-000h — `[DATA]` — Symbol as the primary key

**Do not.** ISIN is the identity; symbol is a display label.

**Why:** tickers are renamed and *reused*. Symbol-level identity will one day splice two different companies into a single continuous price series, and **nothing will crash.** The backtest will simply be wrong, plausibly, forever.


### DE-000j — `[TEST]` — Coarse-bucketing the P&L hash to absorb float drift

**Do not** quantise the net-P&L series into coarse buckets (e.g. 10-paisa) before
hashing to paper over cross-platform floating-point divergence.

**Why:** it trades a load-bearing invariant for a platform convenience. Coarse buckets
mean two *genuinely different* strategies whose P&L differs by less than a bucket
collapse to one `trial_id` — the identity-collision failure that **under-counts trials
and loosens the haircut.** You would defeat the multiple-testing correction to fix a
reproducibility seam. The seam is closed the right way: integer-paise cost paths,
per-charge `ROUND_HALF_UP`, and the gate's tolerance-0 requirement on cost/position
paths — and where float drift does perturb a P&L series, the two runs record as two
trials, which *over-counts* and thus fails safe (tightens the haircut).

Raised and rejected in adversarial review.

### DE-000k — `[ARCH]` — AST-semantic hash as the *identity* of a trial

**Do not** replace behavioural identity (net-P&L hash) with an AST-level semantic hash
of the weight-generation logic to escape hardware-dependent float divergence.

**Why:** an AST hash sees what a strategy *said*, not what it *did*. Two strategies with
different ASTs can produce the same bet and must count once; behavioural identity exists
precisely to catch that. An AST identity reopens the LLM-verbosity and seed-sweep gaming
the whole design closes. The AST hash already exists — as the *pre-check* tier (P1 §5.1),
whose only job is to skip exact reruns. It is not, and must not become, the identity.

Raised and rejected in adversarial review.

### DE-000l — `[TEST]` — Grepping file *contents* for "claude"/"anthropic" in the attribution checker

**Do not** make `check_attribution.py` scan tracked file contents for the strings
`claude`, `anthropic`, etc. It creates an **unwinnable loop**: `.gitignore` must contain
`CLAUDE.md`, `.claude/settings.json` contains `claude`, and legitimate docstrings/comments
reference the Anthropic API or "Claude Code". The checker would never pass, and an
exclusion list is whack-a-mole — the next legitimate mention trips it again.

**The goal is that no commit/PR/tag is *authored by* an AI — not that the word "Claude"
is absent from the repo.** Authorship lives in metadata: author/committer identity,
commit-message *trailers*, tag taggers, PR footers. Scan those only. File contents are
topic, not attribution, and are out of scope. The only content check that remains is that
`CLAUDE.md` and `.claude/` are not *tracked* (a config leak), which is about *what is
committed*, not *what words are inside committed files*.

This loop was hit in an earlier build attempt. The corrected scope (§4.3) exists so it is
not re-derived.
