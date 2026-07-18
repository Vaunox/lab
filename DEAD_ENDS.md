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

*None yet — the build has not started.*

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
