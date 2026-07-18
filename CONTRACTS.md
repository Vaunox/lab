# CONTRACTS

Status: **binding**. Changes require a version bump.

Everything below this line is the shared kernel. Everything above it is alpha,
and the Lab does not contain any.

> **Engines may duplicate logic. Engines may never duplicate truth.**

---

## Shared vs isolated

**Single implementation, program-wide. Below the engines. No exceptions.**

- The trial ledger
- The as-of clock
- The cost kernel
- The fill gate (circuit / series / liquidity)
- The data plane and PIT correctness
- Trial identity and the haircut
- The validation battery

**Isolated, duplicated freely. The engines themselves.**

- The loop
- Fill mechanics
- Position lifecycle
- Square-off, expiry, assignment

Duplicated engine loops are cheap. A wrong abstraction is not. Unifying three
simulation semantics into one loop with mode flags produces conditionals that
nobody can reason about, and every subtle lookahead bug will live *inside* those
conditionals, where it is invisible.

**An engine is defined by its simulation semantics, not by what it computes.**
Feature and factor computation is a *library*, not an engine. If "features"
becomes an engine, the taxonomy is confused at the root and will not survive the
fourth thing.

Engines: `equity-daily`, `equity-intraday`. Later, possibly: `options`,
`paper` (v2), `discrete-event`.

---

## Strategy

The strategy is the cartridge. It is the only place alpha lives, and it lives on
the user's disk, not in this repo.

```python
class Strategy(Protocol):
    engine: EngineId          # DECLARED. Never inferred. Missing -> refuse.
    params: Mapping[str, Any]
    risk_free_rate: float     # MANDATORY. No default. Declaring 0.0 is fine;
                              #   forgetting it is not. See below.

    def on_bar(self, view: MarketView) -> Intents: ...
```

**`risk_free_rate` has no default, and that is deliberate.** The Sharpe ratio is
computed on the excess return over the risk-free rate. A silently-defaulted zero is
not a neutral choice — at ~6%/yr it is ~2.4 bps/day, which against a typical
intraday edge measured in low double-digit bps is a large and *invisible* inflation
of every Sharpe the Lab reports. The failure is silent, systematic, and identical
across every strategy that omits it.

So the contract requires it. A strategy that declares `0.0` has made a claim the
reader can see and dispute. A strategy that omits it does not type-check. The field
is on the frozen contract from the start because every strategy ever written
inherits the contract at the moment it is frozen — adding it later would leave every
prior strategy with an undefined rate and a permanently wrong Sharpe already written
into the ledger.



**`MarketView` is the only window onto the world.** It is constructed by the
engine at the as-of instant and contains nothing after it. The strategy has no
clock, no filesystem, no network, and no way to ask what time it is.

Lookahead is not discouraged here. It is **structurally impossible**.

`Intents` are desired positions or orders. They are *requests*. Whether they fill
is decided by the fill gate, which the strategy cannot see or influence.

---

## Engine

```python
class Engine(Protocol):
    id: EngineId

    def run(
        self,
        strategy: Strategy,
        universe: UniverseRule,     # a PIT rule, not a list
        period: DateRange,
        costs: CostProfile,
        data: DataSnapshot,
        seed: int,
    ) -> TrialResult: ...
```

Every engine:

1. Owns the as-of clock and never hands it to the strategy.
2. Routes **every** fill through the shared fill gate and the shared cost kernel.
   An engine that computes a cost is a build failure.
3. Writes to the ledger as a first-class side effect. There is no path to a
   `TrialResult` that does not write.
4. **Validates the strategy's engine declaration** and hard-errors on violation.
   It does not silently correct.

`equity-intraday` asserts: *no position survives the square-off bar.* A strategy
declaring `intraday` that attempts to hold overnight raises. It is **not**
auto-squared-off. Silent correction is the calculator that quietly converts miles
to kilometres and says nothing.

`equity-daily` asserts: *no intra-bar information is used.*

---

## Trial identity

Content-addressed, and **two-tier**. The unit of record is a **trial**, not a
backtest — so that a paper-trade engine (v2) slots in with no migration.

**Tier 1 — pre-check (textual).** Cheap. Skips the run entirely on an exact
match.

```
pre_id = H(
    normalized_ast(strategy_source),   # comments/whitespace/docstrings stripped
    canonical(params),
    cost_model_hash,
    data_snapshot_hash,
    universe_rule_hash,
    engine_id,
    engine_version,
    asof_window,
    seed,
    taints,
)
```

**Tier 2 — identity (behavioural).** Computed after the run, from what the
strategy actually *did*.

```
trial_id = H(
    position_series_hash,              # what it actually did
    cost_model_hash,
    data_snapshot_hash,
    asof_window,
    taints,
)
```

**A trial is defined by what it did, not by what it said.** Two strategies that
produce identical positions on identical data **are the same bet**, regardless of
how differently they are written. A match records a re-execution and does **not**
increment the trial count.

This is not an optimisation. Textual identity alone is a hole an LLM walks
straight through: an agent will regenerate the same logic with different variable
names indefinitely, and every regeneration would count as a fresh trial. The
haircut would inflate on repetition rather than on search — penalising the honest
and rewarding the verbose.

**Consequences, all intended:**

- Reformatting the strategy → **same** trial. Reruns are free. A rerun is not
  searching.
- Rewriting the strategy so that it produces **identical positions** → **same**
  trial. Rephrasing is not research.
- Changing the logic such that positions change → **new** trial. Cannot be hidden.
- Changing the **seed** → **new** trial. Running one strategy across ten seeds
  and keeping the best *is* searching, and is one of the most common ways people
  fool themselves.
- Lowering the costs → **new** trial. Cost-tuning multiplies the trial count and
- Re-costing at a **different size** → **new** trial, computed by re-running at that
  size. There is deliberately no operation that rescales an existing net P&L series:
  costs are not linear in size (impact rises ~√size), so scaling a net stream is
  arithmetically wrong. The only correct way to ask "what if larger" is to re-cost
  at the larger size, which is a new trial by construction.
  the haircut reflects it. **Re-running with lower costs therefore makes a
  strategy harder to pass, not easier.** This closes the loophole permanently.
- Running the same strategy on two engines → **two** trials. It is two
  hypotheses.
- Adding a taint → **new** trial. Taint cannot be laundered by re-running.

---

## TrialResult

```python
@dataclass(frozen=True)
class TrialResult:
    trial_id: str
    engine_id: EngineId
    engine_version: str

    # evidence
    evidence_source: Literal["backtest", "paper", "oracle"]   # v2 adds "paper"
    asof_window: DateRange
    returns: ContentAddress          # pointer to daily P&L series (blob store)

    # truth stamps
    cost_model_hash: str
    data_snapshot_hash: str
    data_provenance: Literal["self-captured", "third-party-archive"]
    universe_rule_hash: str
    seed: int

    # verdict
    gross: Stats
    net: Stats                       # after costs. the only stats that count.
    haircut: Haircut                 # DSR, effective-N, PBO
    verdict: Verdict

    # contamination
    taints: frozenset[Taint]
```

**`evidence_source` is why the schema says *trial* and not *backtest*.** A paper
trade is a trial with a different evidence source and an expensive clock. It gets
the same ledger, the same clustering, the same effective-N, the same haircut. It
does not get a free pass that a backtest doesn't.

**`UNSTABLE_DISTRIBUTION` is a verdict, and it is not `INSUFFICIENT` or `FAIL`.**
It is returned when the DSR's variance is undefined because the return distribution
is pathological — high Sharpe with strong negative skew, the signature of unhedged
short volatility. Routing this to `INSUFFICIENT` would free-pass exactly the most
dangerous strategies (more data cannot stabilise an unstable distribution); routing
to a bare `FAIL` would hide *why*. This verdict is terminal, diagnostic, recorded,
and never pooled. (Added under adversarial review — see P1 §7.7.)

**`UNVERIFIABLE_WITHOUT_EXECUTION_DATA` is a verdict, and it is not `INSUFFICIENT`.**
The two are different epistemic claims and collapsing them is a category error:

- `INSUFFICIENT` — *not enough data of the right kind yet.* More history, more
  trials, a longer window, and the same battery would return a real verdict.
- `UNVERIFIABLE` — *no amount of this kind of data can ever grade this.* The
  finding depends on something the available data structurally cannot supply —
  realized fills, an exogenous market series, execution prices — and no backtest,
  however long, can manufacture it. The honest verdict is not a hedged PASS. It is
  "this cannot be checked with what exists."

A result that is `UNVERIFIABLE` is recorded, is **never** pooled into effective-N,
and carries the reason. It is the correct home for a finding that is not
contaminated but is structurally unprovable — the thing a caveat on a PASS would
otherwise quietly launder into a believed number.

`ORACLE_CEILING` is a **named result type**, not a hack. It answers *"if my signal
were perfect, what is the ceiling after costs?"* — a legitimate question requiring
declared lookahead. It never reports a Sharpe, never pools with real trials, and
never counts toward the haircut. It is a bound, not a search.

---

## Taints

Three layers of escape hatch. Only Layer 3 taints.

**Layer 1 — extendable data.** Cost rows, calendar, corporate actions. The user
adds a row with an effective-from date and a source. This is the schedule working
as designed, not a lock being broken. Uncited rows are accepted and stamped.

**Layer 2 — named research modes.** `ORACLE_CEILING`, `GROSS_ONLY`. Legitimate,
useful, and structurally incapable of being mistaken for a validated result,
because they do not return the same *type*.

**Layer 3 — `unsafe` overrides.** The crowbar, for the unanticipated. Granular.
Per-trial. Declared in the trial itself. **Never a global mode.**

```python
class Taint(StrEnum):
    UNSAFE_COST_OVERRIDE      = "unsafe:cost-override"
    UNSAFE_SLIPPAGE_BELOW_FLOOR = "unsafe:slippage-below-floor"
    UNSAFE_LOOKAHEAD          = "unsafe:lookahead"
    UNSAFE_FILL_GATE_DISABLED = "unsafe:fill-gate-disabled"
    UNSAFE_THRESHOLD_BELOW_POWER = "unsafe:threshold-below-power"
    UNCITED_COST_ROW          = "data:uncited-cost-row"
    UNTRUSTED_DATA_SOURCE     = "data:untrusted-source"
    HEURISTIC_CIRCUIT_BANDS   = "data:heuristic-circuit-bands"
    RULE_CHANGED_MID_PROGRAM  = "meta:rule-changed-mid-program"
```

**Taint is contagious and irreversible:**

- in the **trial hash** → cannot be laundered by re-running
- in the **ledger row**, under the hash chain → cannot be deleted quietly
- **blocks pooling** into effective-N → not comparable to clean trials
- on the **export** → the credibility artifact shows it

Call it `unsafe`, not "developer mode." *Developer mode* signals *for the people
who know better*, which is exactly the psychology that gets it used casually.
`unsafe` is the right precedent: it does not disable the checker globally, it
opens a **bounded, labelled region** where you accept responsibility, and the
label lives in the record forever.

**Reaching for `unsafe` frequently is a bug report about the design.** If users
keep needing the crowbar for the same thing, Layer 2 is missing a feature. Go
build it. Layer 3 should be rare by construction.

---

## Ledger row

Append-only JSONL. Hash-chained. SQLite is a derived, disposable read index.

```json
{
  "seq": 1417,
  "prev_hash": "…",
  "row_hash": "…",
  "ts": "2026-07-13T09:14:22Z",
  "kind": "trial | re-execution | rule-change | divergence",
  "trial_id": "…",
  "taints": [],
  "result": { }
}
```

**Recording is install-wide and non-optional.** What the user configures is only
the **scope of the haircut computation** (project vs install-wide). The console
then says:

```
340 trials recorded (install). Haircut counts 12 (scope: project).
Recommended: install-wide.
```

This preserves user choice and makes the evasion **visible rather than
impossible**. You cannot stop someone lying to themselves. You can make sure they
have to look at the number while they do it.

---

## Agent boundary

LLM agents are a first-class caller. They are also, structurally, an adversary —
not from malice, but because an optimizer told to obtain a PASS will route around
any obstacle between it and a PASS. Every rule in this document that was written
against a lazy human is load-bearing against an agent. That is not luck; it is
what happens when you design against Goodhart.

The boundary is not advisory. It is enforced at the interface.

| Agent gets | Agent never gets |
|---|---|
| **Read:** ledger, verdicts, taints, cost breakdown, power calculator | The cost model |
| **Write:** hypotheses only | The slippage floor |
| The graveyard, as context | The haircut scope |
| Its own trial count and current haircut | The thresholds |
| Its remaining trial budget | **`unsafe`** |

**`unsafe` is a human affordance** (CONSTITUTION §8.12). An override requires a
human in the loop and the human's name lands on the taint. An agent that could
taint its own trials would simply taint them all and proceed.

**Every agent session declares a hard trial budget**, sized by the power
calculator. On exhaustion the Lab stops issuing verdicts and says why. A human
self-limits by boredom. An agent does not.

### Effective-N as a navigation instrument

For a human, effective-N is a penalty. For an agent it is the **most useful
signal the Lab can emit**, and nobody else can emit it because nobody else tracks
it:

```
Last 200 proposals collapsed to 4 effective clusters.
You are not exploring. You are jittering.
```

The failure mode of an automated quant loop is not running out of compute. It is
**mistaking repetition for exploration.** The clustering machinery — built as a
tax — turns out to be the thing that makes agentic search work at all.

**Pre-flight correlation check.** Before running the full battery, correlate a
candidate's positions against the ledger:

```
Candidate is 0.94 correlated with trial #4112.
Running this is a re-test, not an idea.
```

Cheap, and it converts the ledger from a record of the past into a map of the
search space.

---

## Settings taxonomy

Binary editable/not-editable is too coarse. There are four categories.

| Category | Examples | Editable? |
|---|---|---|
| **Facts** | Statutory costs, exchange calendar, corporate actions, as-of clock | No. Not even *visible* as settings — presenting them as settings implies they are opinions. Extendable as **data** (Layer 1). |
| **Profile** | Broker, capital, universe, instrument class, date range | Freely. This is the point of the abstraction. |
| **Pre-commitments** | Kill-gate thresholds, DSR haircut, clustering params | Once, at project init, **before data contact**. Then frozen. Later changes are a logged, timestamped `rule-change` row that stamps every prior trial `RULE_CHANGED_MID_PROGRAM`. |
| **Free knobs** | Cost overrides, slippage, strategy params | Freely — but every edit spawns a trial. |

Pre-commitments ship **with defaults**, because a tool with no defaults is a
religion. The defaults carry provenance in the docs: *calibrated on Indian cash
equity by one researcher; a starting point, not law.*

The mechanism is a **ratchet, not a lock**. You may change your kill gate. You
may not change it *quietly*, and you may not change it *retroactively*.
