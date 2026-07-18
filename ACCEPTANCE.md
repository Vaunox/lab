# ACCEPTANCE CRITERIA

Status: **binding**. Written before any phase begins.

These are binding *because* they were written by the party with nothing to lose.
Present You has no results, no sunk cost, and nothing to defend. Future You will
be six months in with a gate failing by a hair. The agreement is between those
two parties, and Present You signed it.

**A phase is not complete until every criterion below is met.** Criteria are not
negotiated at the end by whoever is looking at the diff. Where a criterion is a
test, the test and its fixtures are committed **before** the code they judge.

---

## P1 — Substrate: ledger, clock, haircut

The ledger goes in first, before any engine exists.

**Deliverable**
- Trial schema (not backtest schema) — see `CONTRACTS.md`.
- Append-only JSONL ledger, hash-chained. SQLite derived read index.
- As-of clock, owned by the engine.
- Haircut computing from day one, using **raw trial count** as placeholder.
- `taints[]` in the schema from the first row ever written.

**Exit**
- [ ] `test_no_result_without_ledger` — no code path produces a `TrialResult`
      without a corresponding ledger row. Passing.
- [ ] `test_sqlite_is_derived` — no write path to SQLite bypasses JSONL.
      `rebuild-index` reconstructs the index from JSONL alone. Passing.
- [ ] `test_hash_chain_detects_tamper` — deleting or editing any row invalidates
      every subsequent hash. Passing.
- [ ] `test_strategy_cannot_read_clock` — a `Strategy` cannot obtain any
      timestamp beyond as-of. Passing.
- [ ] Trial identity is content-addressed. Re-running an identical trial records
      a re-execution event and does **not** increment the count.
- [ ] Changing only the seed produces a **new** trial hash.
- [ ] `taints[]` participates in the trial hash.

**Not in this phase**
Clustering. Real DSR. Any engine. Any data.

> Raw count is deliberately cruder than clustering and strictly *more* punitive.
> The placeholder can only over-penalise, never under. That is the safe direction
> for a placeholder to fail in.

---

## P2 — Cost kernel

Runs in parallel with P3.

**Deliverable**
- PIT-dated statutory schedule, ~2015 → present. Locked, not editable.
- Curated, versioned broker profiles (`zerodha`, `upstox`, `custom`).
- Slippage floor tied to tick size / spread / ADV participation.
  **The half-spread is not added on top of a midpoint-measured impact number.**
  A market order that crosses the book pays, relative to the midpoint, one
  *half*-spread (`δ = (ask − bid) / (ask + bid)`) — this is the standard
  Almgren-type execution result. And any impact figure *measured from the midpoint*
  (which is how NSE's, and essentially all, impact costs are defined) **already
  contains that half-spread.** So `fees + half_spread + midpoint_impact`
  double-charges the half-spread. The correct decomposition, documented in full in
  P2's deep dive, is **fees + midpoint-referenced impact** (which already embeds the
  crossing cost), with an explicit half-spread term added *only* in the limit-order
  case where the midpoint impact would otherwise not include it. The naive sum is
  wrong and P2 must not implement it. Verified against market-microstructure
  primary sources, not assumed.
- Cost-model hash stamped into every trial record.
- Instrument-class slots defined. **Only equity populated.**

**Exit**
- [ ] `test_pit_cost_lookup` — a 2019 backtest uses 2019's STT. The engine proves
      it, per trade date. Passing.
- [ ] **100%** of statutory rows carry an effective-from date **and** a primary
      source URL (SEBI circular, exchange circular, broker fee page).
- [ ] Statutory costs are not exposed as settings. They are extendable **data**:
      a user may add a row (rate, effective-from, source). An uncited row is
      accepted but permanently stamped `UNCITED_COST_ROW`.
- [ ] `test_money_is_not_float` — no float appears anywhere in the cost path.
      Passing.
- [ ] Options cost slot exists and is **empty**. README says so explicitly.

**Not in this phase**
Any options number. The slot is architecture; the number is a liability you do
not yet own.

> The cost schedule is the one part of this repo that strangers will
> independently audit. Someone will open an issue claiming your 2019 STT is
> wrong. You need a citation, not a memory. Re-derive from primary sources; do
> not port the numbers from the existing private systems.

---

## P3 — Data plane

Runs in parallel with P2.

**Deliverable**
- Adapter interface. Provenance tagging. Canonical internal format.
- Adapters: Kite, Upstox, CSV/Parquet (BYO). No scraping adapters shipped.
- **Synthetic dataset** — the null and power test fixtures.
- PIT rule-based universe (`top_N_by(adv_60d)` etc.), evaluated per date.
- Fill gate: circuit limits, series, liquidity.

**Exit**
- [ ] `test_null_hypothesis` — 1,000 **random** strategies on pure synthetic
      noise. Battery pass rate **≤ 10%** (target 5%). Passing.
- [ ] `test_null_hypothesis_llm` — 1,000 **LLM-generated** strategies on the same
      noise. Same bar: **≤ 10%**. **This is the load-bearing test in the
      repository.** Passing.
- [ ] `test_power` — planted net Sharpe 1.0, 5y daily, 50-trial budget.
      Detection **≥ 60%**. Passing.
- [ ] Adjustment status is a **required declared field**. Undeclared → refuse to
      run. Not a warning.
- [ ] Survivorship: a constituent list with no historical membership dates
      **hard-refuses** the cross-sectional engine. Not a warning.
- [ ] PIT universe reconstruction from bhavcopy is survivorship-free by
      construction: a company delisted in 2019 appears through 2019 and then
      stops.
- [ ] ISIN is the primary key throughout. Symbol is display-only.
- [ ] Series (`EQ` / `BE` / `BZ`) is a PIT field. The intraday engine refuses to
      square off a trade-to-trade series stock, because it cannot be squared off.
- [ ] Fill gate: an order into a stock locked at circuit **does not fill**.
      **Band category is a per-instrument, per-day PIT field, not a constant.** NSE
      cash-segment bands come in categories — 2%, 5%, 10%, 20%, and none — set daily
      from the prior close. **F&O-eligible stocks carry no fixed daily band**; they
      have dynamic intraday cooling-off breakers (10/15/20%) instead. A fill gate
      that assumes a single fixed band is wrong for both the small-cap 2% name and
      the F&O large-cap. The category is sourced where available and stamped when
      heuristic. (Verified against NSE circuit-filter documentation.)
      Sourced band files where available; heuristic fallback, tagged as such.
- [ ] Data provenance tier recorded: `self-captured` vs `third-party-archive`,
      with source and fetch date. Flows into the data snapshot hash.
- [ ] Validator battery on BYO data: monotonic timestamps, no duplicates, gaps
      against the exchange calendar, OHLC invariants, unexplained overnight jumps
      flagged as possible unhandled corporate actions.

**Not in this phase**
Real market data in the repo. Ever.

> The synthetic dataset is not onboarding decoration. It is the machine's honesty
> self-test. Nobody else ships a proof that their backtester correctly finds
> *nothing* in *nothing*. It is the strongest claim available and the cheapest to
> make.

> **Why the LLM null test is the binding one.** Random strategies are
> near-independent — effective-N ≈ raw N, clustering barely matters, and the test
> passes almost regardless of whether the clustering works. LLM-generated
> strategies are the opposite: momentum with forty-seven lookback windows, the
> same six factors recombined. A raw N of 1,000 may be an effective N of fifteen.
>
> A battery that clears the random test while failing the LLM one is broken under
> the exact conditions it will be used in, and its green light is worthless.
> Effective-N is the safety-critical component of this system. This is the test
> that proves it works.

---

## P4 — Engine A: daily cross-sectional → **GATE 4**

**Deliverable**
- First engine. Own loop. Satisfies the `Engine` contract.
- **Analytical fixtures**, hand-derived, landed in an *earlier* PR (see below).

**The engine is not its own oracle.** It is judged against **ground truth derived by
hand** — from the cost schedule and the fill rules, worked out before the engine
exists. Never against its own output.

**Exit**
- [ ] **Analytical fixtures committed in a separate, earlier PR than the engine.**
      Each ships with a **derivation document**: the scenario, the schedule rows
      applied, the arithmetic step by step, to the paisa. A fixture that cannot be
      derived by hand is too large — shrink the scenario until it can.
- [ ] `check_fixture_provenance.py`: the fixture blob hash matches `ACCEPTANCE.md`,
      **and the fixture commit predates the engine commit.**
- [ ] The engine reproduces every fixture: **tolerance 0** on cost and position
      paths (Decimal / integer paise), **1e-10 relative** on float statistics.
- [ ] Property suite passes (invariants that must hold for *any* correct daily
      engine, independent of implementation).
- [ ] The engine contains **zero** cost calculations (import graph).
- [ ] The engine contains **zero** mode flags.
- [ ] `test_behavioural_dedup` — two differently-written strategies producing
      identical positions record as **one** trial. First phase in which positions
      exist.
- [ ] **SUBSTRATE FREEZE.** Tag `substrate-frozen` at this commit. Record the tree
      hash of `src/lab/{core,ledger,costs,fills,validation}` in `ACCEPTANCE.md`.

> A hand-derived fixture **has no platform.** Cost and position paths are Decimal
> and integer — bit-exact on any OS. Float statistics are simple moments and
> survive 1e-10 trivially. This dissolves the cross-platform reproduction problem
> entirely, rather than answering it.

---

## P5 — Engine B: intraday → **GATE 5: THE KILL GATE**

**This is the phase where the project dies if it should die.**

**Deliverable**
- Second engine. **Separate loop.** No shared loop with P4. No mode flags in either.
- Its own analytical fixtures, hand-derived, landed before the engine.

**Exit**
- [ ] Analytical fixtures, same discipline as P4: earlier PR, derivation document,
      provenance-checked.
- [ ] The engine reproduces them at the same tolerances.
- [ ] Intraday property suite: **no position survives the square-off bar** · a
      `BE`/`BZ` (trade-to-trade) instrument **cannot** be squared off intraday · an
      order into a circuit-locked instrument does not fill.
- [ ] `test_cross_engine_cost_reconciliation` — a daily strategy run through the
      **intraday** engine at one bar per day produces **identical** costs. If they
      diverge, a cost model has forked.
- [ ] A strategy declaring `intraday` that attempts to hold overnight
      **hard-errors**. It is not auto-squared-off — a silent fix teaches the user
      nothing and hides a bug.

### The kill gate proper — **substrate invariance**

- [ ] `check_substrate_purity.py` passes against the `substrate-frozen` tag:
      - Every change to `src/lab/{core,ledger,costs,fills,validation}` since Gate 4
        is declared **engine-agnostic** in the PR body, with a justification.
      - **Automatic failure** on any substrate file containing engine-specific
        vocabulary: `intraday` · `daily` · `square_off` · `squareoff` · `MIS` ·
        `engine_id ==` · `isinstance(engine`.
- [ ] Neither engine imports the other (import graph).

**STOP CONDITION — Constitution S1.**
If the intraday engine cannot be built without a mode flag in an engine loop, **or**
without an engine-specific change to shared truth, **the abstraction is wrong.**
**Stop.** The Lab is not released. Do not patch. Do not unify the engines. Do not
special-case the substrate.

> This is what the kill gate was always *for*, tested directly instead of by proxy.
> Two dissimilar simulation semantics — one daily rebalance, one intraday
> square-off — must fit one contract without either of them leaking into the shared
> truth beneath. If they cannot, the whole premise of the Lab is false, and the
> honest thing is to find that out here, cheaply, rather than after release.

> **Any accepted divergence between a fixture and the engine goes in
> `DIVERGENCES.md`** — but note what a divergence now *means*. There is no baseline
> to be wrong. Either the hand-derivation is wrong (fix the derivation, in its own
> PR) or the engine is wrong (fix the engine). **There is no third case**, and a
> divergence is never "accepted" — it is resolved.

---

## P6 — Validation battery

**Deliverable**
- Walk-forward orchestration. DSR. PBO.
- Cluster-adjusted effective-N, replacing the raw-count placeholder.
- Per-trial daily P&L series, content-addressed, stored beside the ledger.
- **Power calculator, at the front of the workflow.**

**Exit**
- [ ] **All three** calibration tests still pass after clustering replaces raw
      count: random null, **LLM null**, power. (Re-run all three. Clustering
      *reduces* effective-N and therefore *loosens* the haircut — this is exactly
      where a null test starts failing, and the LLM one will fail first.)
- [ ] Effective-N exposed as a **navigation signal**, not only a penalty:
      *"your last 200 proposals collapsed to 4 effective clusters — you are not
      exploring, you are jittering."*
- [ ] Pre-flight correlation check: a candidate's positions are correlated against
      the ledger **before** the full battery runs. High correlation is reported as
      a re-test, not an idea.
- [ ] Return series stored per trial. Ledger holds metadata + content-addressed
      pointer; the series live in a blob store. Ledger stays diffable.
- [ ] Tainted trials cannot pool into effective-N alongside clean ones.
- [ ] Power calculator runs **before** research begins and reports: *given your
      data length and declared trial budget, here is the minimum Sharpe that
      could ever be believable.*
- [ ] Trials run under different cost-model hashes are not pooled without an
      explicit, logged decision.

### Reserved — the P6 deep dive must address each of these

*These are not specified here. They are **named** here so the closed-loop manifest
check forces each to have a home when P6's deep dive is written. A pointer is not a
spec; it is a commitment that the spec will exist. Each traces to a known error
class in metric and cost design.*

- [ ] **Canonical Sharpe domain.** σ and its annualisation are computed on the same
      calendar-daily mark-to-market stream. Mixing an event-time σ with a
      calendar-time annualisation understates Sharpe by a large factor. Path metrics
      (drawdown, time-under-water) are calendar-native and are computed on the
      calendar stream only.
- [ ] **Effective-N clustering is on signal/weight vectors, not realised P&L.**
      Realised-P&L correlation is evadable — same edge on randomly-split universe halves
      gives two economically-identical strategies with near-zero P&L correlation. The
      weight-generating function is identical before the universe mask, so cluster on the
      pre-execution signal/weight vectors. `N_eff` within a correlation block is an
      eigenvalue/participation-ratio functional `(Σλ)²/Σλ²`, not a raw cluster count.
      Distance correlation (not Pearson) is the secondary layer for nonlinear dependence
      (one strategy trading the square of another's signal). The **LLM-generated null
      test is the calibration that proves this works** — random strategies are
      near-independent so the correction is untested by them; correlated LLM strategies
      are what exercise it.
- [ ] **Absolute risk gates use a vol-normalised stream.** Sharpe is scale-invariant;
      drawdown, VaR, and vol are not. A cash-heavy book reports σ far below reality
      and clears an absolute max-drawdown gate it should fail. Absolute gates
      evaluate a vol-normalised stream, capped at feasible leverage — and the
      normalisation **re-costs at the scaled size**, never rescales a net stream
      (costs are not linear in size). `CannotReachTargetVol` is a first-class finding.
- [ ] **CPCV yields a distribution, not a number.** Drawdown over a stitched ordering
      that never occurred chronologically is not a real drawdown. Report chronological
      drawdown plus a pre-registered percentile of the CPCV distribution, labelled a
      stress test. **Hard guard: recomputing features after a stitch raises.**
- [ ] **Regime conditioning — the full mechanism, forged under adversarial review.**
      Regime selection is a *meta-search*: choosing which regime to condition on,
      after seeing which regimes looked good, is a multiple-testing sin the trial
      ledger cannot see because the choice happens in the researcher's head. The
      design that closes it:
      - **Pre-registered exogenous menu.** The set of admissible regime conditioners
        (e.g. `{always, VIX, realized_vol, dispersion, trend}`) is declared in the
        environment config **before any data contact**. Conditioners must be
        exogenous, Snapshot-computed series — never computed from the names being
        traded (endogenous labelling lets an agent define "regime" as an indicator on
        its own best/worst days).
      - **Effective menu size `K_eff`.** Compute the correlation matrix of the
        exogenous menu series a priori and reduce it by an eigenvalue/participation
        -ratio metric. `{VIX, realized_vol}` → K≈2 but `K_eff≈1.1`; `{VIX, trend}` →
        `K_eff≈2.0`. This does not recurse: the menu is a *closed, pre-registered set
        of static arrays*, so `K_eff` is a measurement, not a search. Pre-registration
        is what converts an open search into a countable measurement — the recursion
        terminates at exactly one level.
      - **Multiplicative haircut.** A regime-conditioned strategy is graded with
        `total_trials = N_eff × K_eff` in the expected-maximum-Sharpe term. Fifty
        strategies across three independent regimes is 150 draws from the null, not 50.
      - **The baseline is the identity axis, not a privileged first draw.** The
        unconditioned "all-weather" run is conditioning on the trivial regime `always`,
        which is a member of the menu. It pays the same `N_eff × K_eff` as any other
        trial. Privileging it would reopen the meta-search: it would make all-weather
        the free default and conditioning the paid exception, so the *choice* to
        condition would again be an unpriced data-dependent decision. Cost is incurred
        at **menu declaration**, not at conditioning — so declaring a rich menu raises
        the haircut on *every* trial run under it, including the plain ones. This
        prices optionality and incentivises the smallest honest menu.
      - **Strict lockout on mid-study extension.** A regime discovered mid-study was
        discovered *by observing the data*: the data generated the hypothesis. Appending
        it to the menu and recomputing `K_eff` would charge only for the winner of an
        implicit search over every variable the researcher mentally scanned — epistemically
        identical to deleting the ledger. Adding a conditioner post-data-contact is
        forbidden. The only honest response is to **start a new project** with the
        expanded menu pre-registered (same ratchet the Constitution already imposes on
        threshold changes).
- [ ] **Every regime bucket reports conditional beta**, regressed on the exogenous
      series. Dollar-neutral is not beta-neutral within a regime; full-sample OLS
      averages the conditional exposure away.
- [ ] **Cross-project contamination is explicitly NOT policed, and this is a design
      result, not a gap.** A researcher who burns a ledger, learns that dispersion was
      the driver, and pre-registers `{always, dispersion}` in a new project has formed a
      better *hypothesis* — they have not imported an *edge*. The new DSR knows nothing
      of the old failures; the strategy must prove itself from scratch, on new data, at
      the new `N_eff × K_eff`. What crossed the boundary is a question, not an answer, and
      questions were always free. Detecting the carry-over would require cross-project
      identity tracking and a model of human intent — surveillance that violates the
      local-first, no-telemetry refusals and would not even work. **You pay for testing,
      not for thinking.** The clustering/`K_eff` machinery prices every search the machine
      can see; it makes no claim to price the one search it structurally cannot — the
      human's — because pricing that would make the Lab worse than the leak.
- [ ] **Capacity is an impact *budget*, not a fitted coefficient.** The impact `c` is
      not identifiable from OHLCV — it needs realized fills. Solve instead for the bps
      budget (`gross − fees`) and compare to NSE's measured impact; the crossing point
      is the capacity ceiling. Report the **per-name budget distribution** — the thin
      name is the one that kills the book. Where fills are required and absent, the
      verdict is **`UNVERIFIABLE`**.
- [ ] **Minimum Track Record Length (MinTRL) as a reported quantity.** For any
      strategy that passes, report how long a track record would need to be to trust
      its Sharpe against the threshold at the chosen confidence — the Bailey–López de
      Prado MinTRL. A PASS on a track record shorter than its own MinTRL is reported
      with that fact attached. (P1 already refuses to *grade* below a numerical floor
      of 30 observations; MinTRL is the richer, strategy-specific significance
      statement that belongs with the full battery.)
- [ ] **Regime-conditional cost.** Trailing σ and trailing volume both understate
      impact in exactly the dislocation regime where spreads are widest. Costs in a
      regime bucket are computed on that regime's microstructure, not the full-sample
      average.

> The power calculator is the highest-leverage thing in the project. Nobody ships
> it. It changes behaviour in a way no post-hoc haircut ever will, because it
> fires *before* someone burns six months. It is the natural companion to the
> cost-viability pre-check: one says the costs make it impossible, the other says
> the search budget makes it unprovable.

---

## P7 — Consoles

**Deliverable**

Three surfaces onto the same substrate.

- **Telescope** (human, debug) — structured JSONL, ephemeral, retention-capped,
  firehose, zero epistemic weight. Adapter provenance, cache hits, clock ticks,
  cost lookups, seeds, engine internals.
- **Court record** (human, epistemic) — append-only, immutable, not clearable,
  exportable.
- **Machine interface** (agent) — typed schemas, structured verdicts,
  machine-readable taints and errors. Enforces the agent boundary
  (CONTRACTS §Agent boundary).

**Exit**
- [ ] `test_suppressing_logs_cannot_suppress_ledger`. Passing. The ledger is
      written by the engine; the console only observes the write. Logs are things
      you can turn off. Ledgers are not.
- [ ] The meter prints at the start **and** end of every run, in v1 CLI:
      `trials: N (install) / M (scope) | haircut: DSR x → y`
      Not in a report generated at the end. In your face, while you search.
- [ ] The graveyard is shown beside the survivors, with equal weight. Three
      winners next to 247 corpses. Hide the pile and the survivors look like
      skill.
- [ ] Ledger export is a single command, and is hash-chain verifiable by a third
      party.
- [ ] Telescope retention policy set. "Everything" at tick granularity is
      gigabytes per session.
- [ ] `test_agent_cannot_reach_unsafe` — the machine interface exposes no path to
      an override. Any override requires a human in the loop, and the human's name
      lands on the taint. Passing.
- [ ] `test_agent_budget_enforced` — on exhaustion of a declared trial budget, the
      Lab stops issuing verdicts and says why. Passing.
- [ ] The machine interface exposes no path to the cost model, the slippage floor,
      the haircut scope, or the thresholds.

**Not in this phase**
The dashboard. v2.

---

## P8 — Release hardening

**Deliverable**
- API freeze. Semver. Apache-2.0 + NOTICE.
- Docker image + `uv.lock` + content-addressed data snapshots.
- README, including the refusals list.

**Exit**
- [ ] Reproducibility contract stated honestly in the README:
      - cost and position paths: **tolerance 0**, guaranteed (Decimal/integer)
      - return and statistic paths: **1e-10 relative**, same architecture,
        in-container
      - bit-identical floating point **across** architectures is **not**
        guaranteed, and the README says so.
- [ ] Refusals list is in the README, not a wiki page.
- [ ] Options cost slot documented as empty. Explicitly.
- [ ] Security review of the credential path. BYO token, local-first, nothing
      transits any infrastructure but the user's own.
- [ ] Zero telemetry. Verified by grep, not by intent.
- [ ] Lawyer has read the refusals list and the release shape.
- [ ] No `Co-Authored-By` trailers anywhere in history. No `CLAUDE.md` committed.
      No emoji in commit messages.

**Red-team gate**

- [ ] Point an agent at the Lab with the objective: **"obtain a PASS verdict on
      pure noise, by any means."** Give it the machine interface and nothing more.
- [ ] Every seam it finds is a bug. Close it. Re-run.
- [ ] The gate is cleared when the agent's best result on pure noise is
      indistinguishable from the null test's own pass rate.

> This is not a formality. Every guardrail in this system was designed against a
> lazy human. An optimizer is a different opponent: it will not get bored, it will
> not feel embarrassed, and it will try the thing you assumed nobody would try.
> Assume the boundary holds and you have assumed the one thing that must be
> tested.

> Over-claiming reproducibility in a project whose entire pitch is honesty would
> be self-immolating. The honest contract is a *stronger* claim than a vague
> "reproducible," because it is one you can actually keep.

---

## P9 — Private alpha → public

**Deliverable**
- Small N of real users, chosen for their willingness to say the machine is
  wrong.

**Exit**
- [ ] Null test and power test re-run on the release artifact. Both pass.
- [ ] Both calibration numbers published in the README. They are the only
      performance claims the Lab makes.
- [ ] Gate 1 and Gate 2 reproductions are re-runnable by a third party from the
      container.
- [ ] CONSTITUTION §10 stop conditions reviewed and none triggered.
