# CONSTITUTION

Status: **binding**. Amendable only by the ratchet in §9.
Written before any code exists, by the party with nothing to defend.

---

## 1. What this is

The Lab is a research kernel for systematic strategies on Indian cash equity.

It is the machine, not the cartridges. It ships the substrate that every honest
backtest needs and that almost no retail backtest has: point-in-time data
handling, a correct and dated cost model, a fill gate that knows what could not
have been bought, a mandatory trial ledger, and a validation battery whose
multiple-testing correction cannot be routed around.

It ships no strategies, no signals, no data, and no path to an exchange.

## 2. The contract

> **Every hypothesis in the Lab must be expressible as a P&L stream after costs.**

This is a feature, not a limitation. It forecloses the standard research sin —
a statistically beautiful signal that is economically worthless once it pays the
spread. A hypothesis that cannot be stated as positions, fills, and costs is not
a hypothesis the Lab evaluates. That is the boundary, and it is deliberate.

The Lab is a **systematic strategy research lab**. It is not a tool for
"researching anything about Indian markets." Do not describe it that way.

## 3. In scope

- NSE/BSE cash equity. Delivery and intraday.
- Backtesting under point-in-time discipline.
- Statutory + broker cost modelling, dated, sourced, and locked.
- A fill gate: circuit limits, series eligibility, liquidity.
- An append-only, hash-chained trial ledger.
- Validation: walk-forward, DSR, PBO, cluster-adjusted effective-N.
- A power calculator that runs **before** research begins.
- **A machine-usable interface.** LLM agents are a first-class caller, designed
  for from P1, not adapted to later. See §8.11–§8.13 and CONTRACTS §Agent
  boundary.

## 4. Out of scope — permanently

These are refusals, not deferrals. They do not expire. They are the product's
identity, and every one of them will be attacked by a reasonable-sounding
request.

1. **No live execution.** No order ever leaves this machine. No broker order API
   is imported, wrapped, adapted, or wired, in any branch, for any reason.
2. **No strategies.** The repo contains no alpha. Fixtures used in tests are
   labelled as fixtures and are never presented with performance figures.
3. **No signals, recommendations, or verdicts** on live instruments.
4. **No market data redistribution.** Adapters, not data.
5. **No published backtest returns as marketing.** Calibration numbers (§7) are
   the only performance claims the Lab makes, and they are claims about the
   *machine*, not about any strategy.
6. **No telemetry.** Nothing phones home. Not usage counts, not error reports,
   not anonymised anything. Ever.
7. **No hosted service.** Local-first. Credentials never transit any
   infrastructure but the user's own.
8. **No SEBI-regulated activity.** The Lab generates no orders and therefore
   falls outside the retail algo framework. This is not incidental. It is the
   reason for refusals 1 and 3, and it is why they are permanent.

## 5. Deferred — not refused, but not v1

Deferral is a scope decision, not a promise.

| Item | Blocked on |
|---|---|
| Options engine | Its own cost model, incl. STT on exercised ITM |
| Paper trading | Must land as an **engine**, not a subsystem (see CONTRACTS §Engine) |
| Dashboard | v1 ships CLI + files; the haircut meter still prints every run |
| Index-relative universes | Dated constituent membership; PIT rule-based universes are the v1 default |
| Discrete-event engine | Only if a hypothesis class demands it |

## 6. The user, and the anti-user

**The user** wants to know whether their idea is real. They will accept "no."

**The anti-user** wants a prettier number. Their requests arrive reasonable,
polite, and technically framed. They are all the same request. Pre-registered,
so they are recognised on arrival:

- "Make the haircut optional for exploratory work."
- "Add a `--quick` / `--no-ledger` flag for iteration."
- "The DP charge is too conservative for my broker."
- "Let me disable the slippage floor — I get better fills."
- "Reset the trial count when I start a new idea."
- "Ship a starter strategy that actually works, for onboarding."
- "Can the ledger be per-run instead of persistent?"

The answer to every one of these is **no**.

The accommodation already exists and is sufficient: `unsafe` overrides (§8.8).
They work. They taint. That is the deal, and it is not renegotiated.

The Lab is designed to fail the anti-user. If it stops failing them, it has
become the thing it was built to replace.

**The anti-user now arrives with an agent.** That makes them faster, not more
careful. Someone will ship *"point an AI at the market and it finds you
strategies."* It will be a catastrophe. The Lab is the honest version of that
product, and the framing must never blur:

> **This is not an AI that finds strategies. It is an AI that will mostly tell
> you no, very quickly.**

If the README ever implies otherwise, S4 has already happened.

## 7. Pinned numbers

Pinned before any data contact. Changing them post-hoc invokes §9.

| Quantity | Value |
|---|---|
| Nominal α of the full battery | **0.05**, stated publicly |
| Null test — random strategies | **≤ 10%** of 1,000 random strategies on synthetic noise. Target 5%. |
| **Null test — LLM-generated** | **≤ 10%** of 1,000 **LLM-generated** strategies on synthetic noise. **This is the load-bearing test.** |
| Null test — floor | **< 1%** is also a failure signal; confirm against the power test |
| Power test — detection | **≥ 60%**, planted **net Sharpe 1.0**, 5y daily, 50-trial budget |
| Gate reproduction — cost & position paths | **tolerance 0** (Decimal / integer paise) |
| Gate reproduction — float statistics | **1e-10 relative**, same architecture, in-container |

The calibration effect size (net Sharpe 1.0) is a **test fixture, not a
setting**. It is not user-configurable. A calibration number the user can move
is not a calibration.

The user's own acceptance threshold *is* a setting — defaulted, editable,
ratcheted at project init. Its default is **computed by the power calculator**
from their data length and declared trial budget, not chosen. Overriding it
below what the data can support is a taint, not a preference.

**Why the LLM null test is the binding one.** Random strategies are
near-independent: effective-N ≈ raw N, clustering barely matters, and the test
passes almost regardless of whether clustering works. LLM-generated strategies
are the opposite — momentum with forty-seven lookback windows, the same six
factors recombined. Raw N of 1,000 may be an effective N of fifteen.

A battery that clears the random null test while failing the LLM one is broken
under the exact conditions it will be used in, and its green light is worthless.
**Effective-N is therefore not a P6 refinement. It is the safety-critical
component of this system, and the LLM null test is what proves it.**

## 8. Structural invariants

These are not conventions. Each is enforced by a test that fails the build.

1. **No `TrialResult` without a ledger row.** No dry-run path. No `--quiet` that
   suppresses the write. The ledger is a first-class side effect of the engine;
   the console merely observes that the write happened.
2. **The as-of clock is held by the engine.** A `Strategy` cannot obtain any
   timestamp beyond as-of. Lookahead is structurally impossible, not merely
   discouraged.
3. **Engines duplicate logic. Engines never duplicate truth.** No engine
   contains a cost calculation, a calendar, or a PIT lookup. The cost module is
   the sole importer of the rate schedule.
4. **Cross-engine cost reconciliation.** A daily strategy run through the
   intraday engine at one bar per day produces *identical* costs. CI test. If it
   diverges, a cost model has forked.
5. **Money is `Decimal` or integer paise. Never float.** This makes the cost path
   bit-exact and is what makes tolerance-0 reproduction achievable.
6. **ISIN is the identity.** Symbol is a display label. Tickers are renamed and
   reused; symbol-level identity will one day splice two companies into one
   price series and nothing will crash.
7. **JSONL is the source of truth. SQLite is a derived index.** Disposable,
   rebuildable, never written directly. Any write path to SQLite that bypasses
   JSONL is a build failure.
8. **Taint is contagious and irreversible.** Every override lands in `taints[]`
   on the `TrialResult` itself. Taint is in the trial hash (cannot be laundered
   by re-running), under the hash chain (cannot be deleted without breaking it),
   blocks pooling into effective-N (not comparable to clean trials), and appears
   on the export.
9. **The ledger is hash-chained.** Each row carries the hash of the previous.
   Deleting a failed trial invalidates every hash after it, and anyone can see.
   This is what makes the ledger export a *proof* rather than a screenshot.
10. **The engine is declared, never inferred.** A strategy states its engine.
    Missing declaration → refuse to run. The engine then validates the
    declaration and **hard-errors** on violation. It does not silently correct.
11. **Trial identity is behavioural, not textual.** Two strategies producing
    identical positions on identical data are **the same bet**, however
    differently they are written. An AST hash alone would let an infinitely
    verbose author manufacture unlimited "new" trials by renaming variables.
12. **`unsafe` is a human affordance. Agents never get the crowbar.** An agent
    handed an override will use it the moment an objective goes unmet — not from
    malice, but because routing around obstacles is what optimizers do. Any
    override requires a human in the loop, and the human's name goes on the
    taint.
13. **Every agent session declares a hard trial budget**, sized by the power
    calculator. On exhaustion the Lab stops issuing verdicts and says why. A
    human self-limits by boredom. An agent does not. **Compute is cheap; belief
    is not.**
14. **Completeness is a gate, not an aspiration.** Every phase has an exhaustive
    MANIFEST, frozen before the phase opens, and the phase does not merge until
    every row exists and is called. `DEFERRALS.md` is empty at every phase exit.
    Stubs fail the build mechanically.
15. **The engine is never its own oracle.** Gate fixtures are **derived by hand**
    — from the cost schedule and the fill rules, before the engine exists, with
    the arithmetic shown to the paisa. **No expected value is ever taken from an
    implementation**, the engine's or any other program's.
    *A fixture the engine produced is not a gate. It is a mirror. If you cannot
    compute the right answer yourself, you cannot tell whether the engine did.*
16. **Pre-registration is what makes a search space countable.** Any *open,
    generative* search space (strategies the agent invents in response to results)
    requires behavioural counting — effective-N over what was actually produced. Any
    *closed, pre-registered* set declared before data contact (e.g. the regime
    conditioning menu) is a static multiplier, measured a priori, not searched. This is
    why search-counting terminates and does not recurse infinitely: declaring a set
    before data contact converts an open search into a closed measurement. Corollary:
    extending a pre-registered set *after* data contact is epistemically identical to
    deleting the ledger, and is forbidden — the honest response is a new project. And
    the terminus: the Lab prices every search it can see and makes **no** claim to price
    the one it structurally cannot — the researcher's own accumulated intuition across
    projects — because pricing that would require surveillance that violates §4 and would
    not work anyway. *You pay for testing, not for thinking.*
17. **The substrate is frozen at Gate 4.** Building the second engine may not
    change shared truth in an engine-specific way. If it must, the abstraction is
    wrong (S1). Enforced by `check_substrate_purity.py` against the
    `substrate-frozen` tag.
    *The Completion Standard catches a build that claims more than it delivered.
    It does not catch a build that delivers less than the spec and claims exactly
    that — and that is the observed failure mode. A gate is a sample of the spec,
    not a summary of it.*

> One sentence for the README: **you can unlock anything; you cannot unlock it
> quietly.**

## 9. Amendment (the ratchet)

This document is amendable. It is not amendable *quietly*, and it is not
amendable *retroactively*.

Any change requires an entry in the log below: date, what changed, why, and what
it invalidates.

Changing a pinned number (§7) after any gate has been run stamps **every prior
trial** as run under a different rule. That stamp is permanent and appears in the
ledger and on the export.

This is the same discipline the Lab imposes on its users. It is not exempt from
its own methodology.

### Amendment log

| Date | Section | Change | Invalidates |
|---|---|---|---|
| 2026-07-13 | — | Initial ratification | — |

## 10. Stop conditions

Pre-committed while nothing is invested. Each is a condition under which the
correct action is to **stop**, not to patch.

**S1 — The abstraction is wrong.**
The second engine (intraday) cannot be built without **either**:
  (a) a mode flag inside an engine loop, **or**
  (b) an engine-specific change to the shared substrate — detected by
      `check_substrate_purity.py` against the `substrate-frozen` tag cut at Gate 4.

→ **Stop.** The Lab is **not released**. Do not patch. Do not unify the engines.
Do not special-case the substrate.

*"Not released" means: not packaged, not tagged, not announced, not installable.
Repository visibility is irrelevant, and note that **the repo is public from the first
commit** — so "stop, do not release" can never be satisfied by flipping to private. It is
satisfied only by not shipping: no package, no tag, no announcement, no install path. A
public repo that ships nothing has released nothing.*

**S2 — The machine lies in the permissive direction.**
Either null test passes > 10% on pure noise — **and the LLM-generated one is the
binding one.**
→ Do not release. A dishonest honest-backtester is strictly worse than no
backtester, because it launders bad research under a credibility claim. At agent
scale it launders it at industrial volume.

**S3 — The machine is blunt, not rigorous.**
Power test detects < 60% at net Sharpe 1.0.
→ Do not release. Rejecting everything is not rigour. It is an expensive way to
have no opinion.

**S4 — The product failed at its only purpose.**
Six months post-release, the dominant usage pattern is scoping the haircut away
or forking out the ledger.
→ Archive. (No telemetry exists to measure this. It is a judgement read from
issues, forks, and discussion — which is why it is written down now, before
there is anything to rationalise.)

**S5 — The kernel is eating the research.**
Maintaining the public Lab measurably slows own research for two consecutive
quarters.
→ Fork or archive. The Lab was extracted to make research faster. If it makes it
slower, it has inverted its own purpose.

## 11. What is *not* in this document

No timeline. No deadlines. No Gantt.

Phases gate on criteria, not dates. A deadline is a force pushing against a gate
that must not bend, and the only thing standing between this project and a
dishonest tool is a gate that refuses to soften.

Every project-management instinct says add a schedule. It is the one PM artifact
that is actively harmful here, and it is excluded deliberately.
