# Deep Dive P1 — Substrate: Ledger, Clock, Identity, Haircut

> **Status: COMPLETE. Manifest frozen.** This phase may open.
>
> This document is **authoritative**. `MASTER_BLUEPRINT.md` Part IV is an index of it, not a substitute for it. Where they differ, this file governs and the divergence is logged in `PROJECT_STATE.md`.
>
> **Build every row of §12 (MANIFEST), not merely the artifacts the gate tests touch.** The gate is a *sample* of this spec, not a summary of it. See `MASTER_BLUEPRINT.md` Part I §10.

---

## 1. Scope

Everything from an engine finishing a simulation to a sealed, tamper-evident, haircut-carrying `TrialResult` on disk — and the structural guarantees that make it impossible to obtain a result without that record existing.

**No engine exists yet. No data exists yet. No costs exist yet.** This phase builds the thing that judges, before there is anything to judge. That ordering is deliberate: a ledger retrofitted onto a working backtester is a ledger with a bypass, because the bypass was the original code path.

**In this phase:** the trial schema · the as-of clock · two-tier trial identity · the append-only hash-chained ledger · the derived SQLite index · the raw-count haircut placeholder · taint mechanics · the sealed write path.

**Not in this phase:** clustering (P6) · real DSR calibration (P6) · costs (P2) · data (P3) · engines (P4/P5). Where P1 must stand in for one of these, it does so with a **fake that is strictly more punitive than the real thing** (§7.4), never with a stub.

---

## 2. Why the ledger goes first

Three failure modes are designed out here, structurally. Each one has killed a real research program.

**2.1 — The bypass.** In every backtester ever written, "run a backtest" and "record that you ran a backtest" are two operations, and the second is optional. It is a logging call. Logging calls get suppressed, disabled in tests, skipped in "quick" modes, and eventually forgotten. The result is a trial ledger that is systematically missing exactly the trials the researcher was embarrassed by.

The defence is not discipline. It is that **the engine cannot construct a `TrialResult` at all.** It constructs a `TrialDraft`, hands it to the ledger, and the ledger mints the identity, writes the row, and returns the sealed result. There is no other constructor. `check_import_graph.py` enforces that `TrialResult` is instantiated nowhere outside `lab/ledger/`.

**2.2 — The quiet deletion.** A researcher with 247 failures and 3 successes has an obvious incentive. An unchained log offers no resistance. A hash chain does: delete row 47 and every hash from 48 onward is wrong, verifiably, by anyone who runs `lab ledger verify`.

This is what converts the ledger export from a *claim* into a *proof*, and the export is the Lab's only real distribution mechanism.

**2.3 — The retrofit.** `taints[]`, `evidence_source`, and the behavioural hash must be present in the very first row ever written. Adding a field to a hash-chained, append-only log means either rewriting history (which breaks the chain, which is the point of the chain) or maintaining two schema versions forever.

**There is no cheap moment to add these later. This is the cheap moment.**

---

## 3. Domain types

Location: `lab/core/types.py` (types) and `lab/ledger/schema.py` (ledger-owned types).

### 3.1 `Money`

```python
Paise = NewType("Paise", int)   # integer paise. NEVER float.
```

All monetary quantities — costs, P&L, capital, prices where used in cost arithmetic — are integer paise. `Decimal` is permitted at boundaries where a rate must be multiplied (e.g. `STT = 0.001 * turnover`), but the result is quantised to `Paise` immediately, with an explicit, documented rounding rule.

**Rounding rule:** `ROUND_HALF_UP` on the paise, applied per-charge, not per-trade. This mirrors how brokers actually bill. Deviating from it introduces a systematic, compounding error in high-turnover strategies — exactly the regime the Lab exists to keep honest.

**Why this matters here, in P1, before costs exist:** the gate tolerance for P4/P5 reproduction is *zero* on the cost and P&L paths. That is only achievable if money is exact. If P1 admits a float anywhere in the P&L series, the gate can never be met and nobody will discover why until P4.

`tests/unit/core/test_money.py::test_no_float_in_money_path` greps the AST of `lab/ledger/` and `lab/core/` for `float` annotations on monetary fields. It fails the build.

### 3.2 `AsOf` and `DateRange`

```python
@dataclass(frozen=True, order=True)
class AsOf:
    """An instant in the simulation. IST. Derived from DATA, never from wall clock."""
    ts: datetime          # tz-aware, Asia/Kolkata

@dataclass(frozen=True)
class DateRange:
    start: date
    end: date             # inclusive
```

**`AsOf` is never constructed from `datetime.now()`.** It is always derived from a bar's timestamp. This is what makes the clock reproducible: a backtest run today and the same backtest run in a year produce the same `AsOf` sequence, because wall-clock time is not an input.

`tests/adversarial/test_clock.py::test_asof_never_from_wall_clock` asserts that `lab.core.clock` does not reference `datetime.now`, `time.time`, `date.today`, or `utcnow`.

### 3.3 `Taint`

```python
class Taint(StrEnum):
    UNSAFE_COST_OVERRIDE         = "unsafe:cost-override"
    UNSAFE_SLIPPAGE_BELOW_FLOOR  = "unsafe:slippage-below-floor"
    UNSAFE_LOOKAHEAD             = "unsafe:lookahead"
    UNSAFE_FILL_GATE_DISABLED    = "unsafe:fill-gate-disabled"
    UNSAFE_THRESHOLD_BELOW_POWER = "unsafe:threshold-below-power"
    UNCITED_COST_ROW             = "data:uncited-cost-row"
    UNTRUSTED_DATA_SOURCE        = "data:untrusted-source"
    HEURISTIC_CIRCUIT_BANDS      = "data:heuristic-circuit-bands"
    RULE_CHANGED_MID_PROGRAM     = "meta:rule-changed-mid-program"
```

The full enum ships in P1 even though most values cannot yet be *produced* — the producers arrive in P2 and P3. This is not speculative generality: the enum is part of the hash preimage, and adding a member later changes nothing, but **adding the field later would require migrating the chain.**

`Taints = frozenset[Taint]`, canonicalised as a **sorted list of strings** for hashing.

### 3.4 `TrialDraft` — what an engine may construct

```python
@dataclass(frozen=True)
class TrialDraft:
    """What an engine hands to the ledger. Carries NO identity and NO sequence."""
    engine_id: str
    engine_version: str
    evidence_source: Literal["backtest", "paper", "oracle"]
    asof_window: DateRange

    strategy_ast_hash: str        # for the pre-check (§5.1)
    params_hash: str
    universe_rule_hash: str
    cost_model_hash: str
    data_snapshot_hash: str
    data_provenance: Literal["self-captured", "third-party-archive"]
    seed: int

    net_pnl: tuple[Paise, ...]    # CALENDAR-daily net mark-to-market. integer paise. THE identity.
    positions: PositionSeries     # retained for clustering and diagnostics
    gross: Stats
    net: Stats

    taints: Taints
```

### 3.5 `TrialResult` — what only the ledger may construct

```python
@dataclass(frozen=True)
class TrialResult:
    seq: int                      # ledger sequence. minted by the ledger.
    trial_id: str                 # behavioural identity. minted by the ledger.
    pre_id: str
    row_hash: str

    draft: TrialDraft
    haircut: Haircut
    verdict: Verdict

    is_reexecution: bool          # True => this trial already existed; count NOT incremented

    _seal: SealToken              # only lab.ledger can mint one
```

**`SealToken`** is a module-private sentinel in `lab/ledger/seal.py`. `TrialResult.__post_init__` raises `SealError` if the token is not the module singleton. This is defence in depth — the primary enforcement is the import-graph test, but a runtime seal catches the case where someone adds a new module inside `lab/ledger/` and constructs a result without going through `record()`.

---

## 4. The as-of clock

Location: `lab/core/clock.py`

### 4.1 The invariant

> **The engine holds the clock. The strategy never sees it.**

Lookahead is not *discouraged* by convention. It is **structurally impossible**, because the strategy is handed a `MarketView` that physically does not contain any datum after `asof`, and it has no other channel to the world.

### 4.2 `MarketView`

```python
class MarketView(Protocol):
    """The only window a Strategy has onto the world. Constructed by the engine AT asof."""
    asof: AsOf

    def history(self, isin: ISIN, lookback: int) -> BarSeries: ...
    def universe(self) -> frozenset[ISIN]: ...
    def series(self, isin: ISIN) -> SeriesCode: ...   # EQ / BE / BZ, point-in-time
```

`MarketView` is a **Protocol** in P1 with a `NullMarketView` implementation used by the P1 test suite. The real implementation lands in P3. `NullMarketView` is not a stub — it is a complete, tested implementation over an empty universe, and it exists so that P1's tests can exercise the clock invariants without a data plane.

> This is the distinction §10.4 of the blueprint draws. A **stub** raises `NotImplementedError` and fails the build. A **null object** is a complete, correct implementation of the degenerate case, is tested, and is permanent.

### 4.3 Enforced strategy isolation

`lab/core/sandbox.py` provides `run_isolated(strategy, view)`, which invokes the strategy with:

- no access to `datetime.now`, `time.time`, `date.today` — the `lab.core.clock` module is the only sanctioned time source and it accepts no argument-free "now"
- an import guard: a strategy module importing `requests`, `urllib`, `socket`, `os`, or `pathlib` raises `StrategyIsolationError` at registration

**This is checked at registration, not at runtime,** by AST-inspecting the strategy module. Runtime patching (`sys.modules` surgery, monkeypatching builtins) is deliberately *not* attempted: it is defeatable, slow, and would give a false sense of security. AST inspection at registration is honest about what it can and cannot catch, and it catches every accident and every casual attempt.

**What it does not catch:** a determined adversary using `eval`, `__import__`, or C extensions. This is documented in the README under known limitations. **We do not pretend otherwise.** The taint system, not the sandbox, is the real defence against deliberate cheating — and the taint system's premise is that the user is lying to themselves, not to us.

---

## 5. Trial identity

Location: `lab/ledger/identity.py`

### 5.1 Tier 1 — the pre-check (textual, cheap, pre-run)

```python
pre_id = blake2b_256(canonical_json({
    "ast":      normalized_ast_hash(strategy_source),
    "params":   params_hash,
    "cost":     cost_model_hash,
    "data":     data_snapshot_hash,
    "universe": universe_rule_hash,
    "engine":   f"{engine_id}@{engine_version}",
    "window":   [str(start), str(end)],
    "seed":     seed,
    "taints":   sorted(taints),
}))
```

**Purpose:** skip the run entirely on an exact match. Look up `pre_id` in the SQLite index; on a hit, return the stored `TrialResult` with `is_reexecution=True`, append a `re-execution` ledger row, and **do not increment the trial count.** A rerun is not searching.

**`normalized_ast_hash`** parses the strategy source with `ast`, strips docstrings, comments, and all position/formatting information (`ast.dump(tree, annotate_fields=True, include_attributes=False)`), then hashes. Reformatting the strategy costs nothing. Renaming a *variable* does change the AST and therefore the `pre_id` — which is fine, because Tier 2 catches it.

### 5.2 Tier 2 — identity (behavioural, post-run)

```python
trial_id = blake2b_256(canonical_json({
    "pnl":    net_pnl_series_hash,      # tuple[Paise, ...] -> exact, integer
    "data":   data_snapshot_hash,
    "window": [str(start), str(end)],
    "taints": sorted(taints),
}))
```

> **A trial is defined by what it did, not by what it said.**

**The series is calendar-native daily mark-to-market — one point per trading day
the engine's calendar recognises, not one point per event or fill.** An event-time
stream would satisfy the type but break every downstream metric: a σ measured in
event time and annualised in calendar time understates Sharpe by a large factor,
and drawdown over event-time is not a drawdown anyone experiences. Non-trading days
carry the mark forward; days with no position contribute an earned zero (§5.4), not
a padded one. Event-time streams are forbidden as the metric domain.

**Why the net P&L series and not the position series.** Positions alone are insufficient: two engines can produce identical positions and different costs (delivery pays the DP floor; intraday does not), so identical positions can be *different bets*. The net P&L series is the bet. It is integer-exact because money is integer paise. Hashing it is deterministic, cross-platform, and cheap.

**Three consequences, all correct, and the third is a gift:**

1. **Rephrasing is not research.** An LLM regenerating the same logic with different variable names produces a different `pre_id` and the *same* `trial_id`. It is one trial. Without this, an agent inflates its own haircut by being verbose, and the haircut would penalise repetition instead of search — punishing the honest and rewarding the prolix.

2. **A seed sweep on a *deterministic* strategy is free.** Ten seeds, ten different `pre_id`s, one `trial_id`, because the P&L never changed. One trial.

3. **A seed sweep on a *stochastic* strategy costs ten trials** — because the P&L *did* change, so it was a real search over ten outcomes, and picking the best of ten is exactly the sin the haircut exists to price.

**The system does the right thing in both cases without being told which case it is in.** That is not a coincidence; it is what behavioural identity *means*.

### 5.3 Canonical JSON

Cross-language verifiability is a hard requirement — a stranger must be able to verify the chain. `lab/ledger/canonical.py`:

- keys sorted, UTF-8, `separators=(",", ":")`, no trailing whitespace
- integers as JSON integers
- **`Decimal` and `Paise` serialised as strings**, never as JSON numbers
- **floats serialised as `format(x, ".17g")`** — round-trip exact for IEEE-754 double, and stable across platforms. Floats appear only in `Stats` (Sharpe, etc.), never in the money path.
- `None` is forbidden in the hash preimage; absent fields are omitted, and the field set is fixed by schema version

`tests/unit/ledger/test_canonical.py::test_canonical_json_is_stable` round-trips a fixture through serialise → parse → serialise and asserts byte equality. `::test_float_repr_round_trips` asserts `float(format(x, ".17g")) == x` over a fuzz corpus including subnormals, ±inf, and NaN (NaN in a `Stats` field is a `SchemaError` — it is never hashed).

### 5.4 The degenerate case: the null strategy

A strategy that takes no positions produces an all-zero P&L series. Every such strategy collapses to the same `trial_id`.

**This is correct** — a strategy that never trades is not a hypothesis about the market — but it is confusing when it happens by accident, which it usually does (a filter that excluded everything, a universe rule with no members).

So it is handled explicitly: an all-zero `net_pnl` yields `Verdict.NO_POSITIONS`, not a normal verdict. The result is written to the ledger (recording is unconditional), it does **not** count toward the haircut, and the console says plainly: *"this strategy took no positions — that is almost certainly a bug in your filter, not a finding."*

---

## 6. The ledger

Location: `lab/ledger/store.py`, `lab/ledger/chain.py`

### 6.1 The row

```json
{
  "v": 1,
  "seq": 1417,
  "ts": "2026-07-13T09:14:22+05:30",
  "kind": "trial",
  "prev_hash": "…64 hex…",
  "row_hash": "…64 hex…",
  "payload": { }
}
```

`kind ∈ {"genesis", "trial", "re-execution", "rule-change", "chain-repair"}`.

`row_hash = blake2b_256(prev_hash || canonical_json(payload_and_envelope_minus_row_hash))`

Genesis row: `seq=0`, `prev_hash = "0"*64`, `kind="genesis"`, payload carries the schema version, the creation timestamp, and the Lab version.

### 6.2 Append-only, mechanically

- The file is opened with `open(path, "a", encoding="utf-8")` — **`O_APPEND`, never `w`, never `r+`.**
- `tests/unit/ledger/test_store.py::test_never_opens_truncating` AST-greps `lab/ledger/` for any `open(...)` whose mode contains `w`, `x`, or `+`. Fails the build.
- One `write()` per row, of the complete line including the terminating `\n`, followed by `flush()` and `os.fsync()`. The fsync is not optional and it is not a performance knob: a ledger that loses its last row on a crash is a ledger with a bypass triggered by pulling the power cable.

### 6.3 Concurrency — the failure an agent will find first

Two processes appending simultaneously will interleave, and the chain will be silently corrupt: both read the same tail, both compute the same `prev_hash`, both append. The chain now forks and `verify` fails — *after* the trials are already recorded.

This is not a hypothetical. **The Lab is explicitly designed to be driven by agents, and the first thing anyone does with an agent is run backtests in parallel.**

Defence: `lab/ledger/lock.py` takes an **exclusive advisory lock** (`fcntl.flock(LOCK_EX)` on POSIX, `msvcrt.locking` on Windows) held across the *entire* critical section:

```
acquire lock
  → read tail row
  → compute prev_hash
  → compute row_hash
  → append line
  → flush + fsync
release lock
```

Lock acquisition blocks with a timeout (default 30s, configurable) and raises `LedgerBusyError` on expiry rather than proceeding. **Never proceed without the lock.** A corrupted chain is unrecoverable by design; a blocked write is an inconvenience.

`tests/integration/ledger/test_concurrent_append.py` spawns 16 processes appending 100 rows each and asserts: 1,600 rows, chain verifies, no duplicate `seq`, no lost rows.

### 6.4 Crash recovery — the one permitted truncation

A crash between `write()` and `fsync()` can leave a trailing partial line with no terminating newline.

On open, `Ledger` reads the last line. If it lacks a terminating `\n` **or** fails to parse:

1. It is a **trailing partial write** — the only recoverable corruption.
2. Truncate exactly that partial line.
3. Append a `chain-repair` row recording: the bytes discarded, their sha256, and the timestamp.
4. Log at `ERROR`. Print to the console. **Do not proceed silently.**

Any corruption that is *not* a trailing partial line — a bad hash mid-chain, a duplicate `seq`, an unparseable interior row — raises `ChainCorruptError` and the Lab **refuses to run.** It does not repair. It does not skip. A ledger whose interior cannot be verified is not a ledger, and continuing to append to it manufactures the appearance of an audit trail where none exists.

`tests/adversarial/test_ledger_tamper.py` covers: edit an interior row · delete an interior row · reorder two rows · truncate mid-file · duplicate a `seq` · forge a `row_hash`. Every one must be detected. Every one must refuse to run.

### 6.5 Verification

`lab ledger verify [--from SEQ]` walks from genesis, recomputes every hash, and reports the first divergence with its `seq`.

It is **a standalone entry point with no dependency on the rest of the Lab**, so a third party can verify an exported ledger without installing the engines, the cost kernel, or the data plane. The verifier is ~60 lines and its only dependencies are `json` and `hashlib`. This is deliberate: a proof that requires trusting the prover's whole stack is not a proof.

### 6.6 Location and scope

- **Recording is install-wide and non-optional.** Default: `${XDG_DATA_HOME:-~/.local/share}/lab/ledger.jsonl`, via `platformdirs`.
- **Counting scope is a setting.** `project` or `install`. It changes *which* rows the haircut computation reads. It changes **nothing** about what is recorded.

The console always shows both:

```
340 trials recorded (install). Haircut counts 12 (scope: project).
Recommended: install-wide.
```

> You cannot stop someone lying to themselves. You can make sure they have to look at the number while they do it.

---

## 7. The haircut

Location: `lab/validation/haircut.py` — placed under `validation/` in P1 *precisely so that P6 replaces its internals without moving it.*

### 7.1 The interface, which does not change in P6

```python
def compute_haircut(
    candidate_sharpe: float,          # PER-PERIOD (per-observation). NOT annualised. See below.
    trial_sharpes: Sequence[float],   # all in-scope trials, ALSO per-period
    n_effective: float,               # P1: raw count. P6: cluster-adjusted.
    n_obs: int,                       # return observations (T)
    skew: float,
    kurtosis: float,                  # NON-excess (Fisher=False): a normal dist is 3, not 0
) -> Haircut: ...
```

**UNITS CONTRACT — the Sharpe ratios are per-period, never annualised.** This is
not a stylistic choice; it is load-bearing, and getting it wrong silently corrupts
every verdict. The variance term (§7.2) divides by `T`, and the expression is only
dimensionally correct when the Sharpe is expressed per-observation — the same
frequency as `n_obs` counts. Feeding an annualised Sharpe (e.g. 2.5) where the
formula expects the per-day value (e.g. `2.5/√252 ≈ 0.157`) makes the
`√(n_obs − 1)` scaling double-count the horizon, and the DSR becomes meaningless
while still returning a plausible-looking number between 0 and 1 — the worst kind
of wrong.

The verified reference implementations are explicit and unanimous on this:
*"sr_list must be unannualised."* So the contract is enforced, not trusted:

- `compute_haircut` accepts **per-period** Sharpes only.
- Conversion from any annualised figure happens **once**, at the boundary where a
  `TrialResult` is assembled, using the strategy's own observation frequency — never
  inside the haircut, and never twice.
- **Non-excess kurtosis** (a normal distribution reads 3). The `(kurt − 1)` term in
  the denominator assumes this convention; passing excess kurtosis (normal = 0)
  shifts the variance and is a silent error. `test_haircut.py::test_kurtosis_convention`
  pins it with a Gaussian fixture whose kurtosis must read 3.0.

**P6 changes exactly one call site: the argument passed as `n_effective`.** Nothing else. If P6 requires a signature change, the P1 interface was wrong, and that is a design defect to be caught here, not there.

### 7.2 Deflated Sharpe Ratio

Expected maximum Sharpe under the null across `N` independent trials (Bailey & López de Prado):

```
E[max SR] ≈ σ_SR · [ (1 − γ)·Φ⁻¹(1 − 1/N) + γ·Φ⁻¹(1 − 1/(N·e)) ]
```

where `γ` is Euler–Mascheroni (0.5772156649…) and `σ_SR` is the cross-trial standard deviation of the observed trial Sharpes.

```
DSR = Φ( (SR − E[max SR]) · √(n_obs − 1) / √(1 − skew·SR + ((kurt − 1)/4)·SR²) )
```

**Guard — the denominator can go imaginary, and it does so on exactly the dangerous
strategies.** The radicand `1 − skew·SR + ((kurt − 1)/4)·SR²` is not guaranteed
positive. For a strategy with strong negative skew and high Sharpe — the profile of
a short-volatility or premium-selling book, which is most of Indian retail F&O — it
can go negative, and `√(negative)` is `nan`. A `nan` DSR does not raise; it
*propagates*, and `nan` compares false against every threshold, so the strategy
would **neither pass nor fail — it would vanish from the gate.** The most dangerous
strategies are the ones this silently drops.

So: **before the square root, if the radicand is ≤ 0, return
`Verdict.UNSTABLE_DISTRIBUTION`, not a number and not `INSUFFICIENT`.** This routing
was corrected under adversarial review (see §7.7). A negative radicand is not a
sample-size problem — more data will not fix it — so `INSUFFICIENT` ("wait for more
data") would be a *free pass for a toxic strategy*. The radicand goes negative under
exactly the high-Sharpe, strong-negative-skew profile of picking up pennies in front
of a steamroller (unhedged short vol). The statistic is undefined *because the
strategy is a time bomb*, and the verdict must say so. Tested by
`test_haircut.py::test_negative_radicand_is_unstable` with a high-Sharpe
negative-skew fixture; a required member of the P1 test plan.

### 7.3 `σ_SR` — analytic under the null, never a fitted constant

**This section was rewritten under adversarial review. The prior design used a
smuggled empirical constant `σ_SR = 0.5`, which carried the wrong units (it was an
annualised figure mixed into a per-period equation) and was never derivable. Two
independent adversaries converged on this as a real defect.**

`σ_SR` is the cross-trial dispersion of the Sharpe estimator **under the null of no
edge**. Because the null fixes the true `SR = 0`, `σ_SR` is not a property of history
to be *fitted* — it is a property of the sampling distribution, to be *computed*.
Fitting it to real returns would be a search over the data to set the hurdle that
judges strategies-run-on-that-data: circular, and forbidden.

From the Opdyke/Lopez de Prado asymptotic variance of the Sharpe estimator,
`Var(SR) = (1 − γ₃·SR + ((γ₄−1)/4)·SR²)/(T−1)`, evaluated at the null `SR = 0`:

```
σ_SR = 1 / √(T − 1)
```

**The moment terms vanish at the null, and that is correct, not a loss.** A second
adversary flagged that γ₃ and γ₄ annihilate at `SR = 0`, making the *benchmark*
moment-blind. This is the intended asymmetry: the null hypothesis is a claim about
*no edge* (the mean), and "no edge" has no right to assume a fat-tailed noise
distribution that would artificially lower the pass bar. The **benchmark** is
moment-blind; the **candidate** is still penalised for its own skew and kurtosis in
the DSR denominator (§7.2). Noise is graded as noise; the strategy is graded as
itself.

This is per-period by construction (it is a function of `T`, the observation count),
so the units contradiction that the fitted 0.5 introduced cannot arise. There is no
`SIGMA_SR_THIN_LEDGER_FALLBACK` constant; there is a formula.

**What this does to the trial budget — the mechanised Minimum Backtest Length.**
With `σ_SR = 1/√(T−1)`, requiring that a planted annualised Sharpe of 1.0 (per-day
≈ 0.063) clear `E[max SR] ≈ σ_SR·√(2 ln N)` with power solves for the *admissible*
`N`. At `T = 1250` (5y daily), `N ≈ 12`. This is not a constraint bolted on; it is
Minimum Backtest Length falling out of the same machinery, and it is what the power
calculator reports: *at your data length and effect size, your trial budget is
~12 — spend it wisely.* `N` is an **output** of the calculator, never a pinned input.

### 7.4 The raw-count placeholder — a fake, not a stub

P1 passes `n_effective = raw_count`. P6 passes the clustered value.

**Clustering is on the signal/weight vectors, not the realised P&L** — corrected
under adversarial review. Realised-P&L correlation is evadable: an agent runs the
same edge on randomly-split universe halves, producing two economically-identical
strategies with near-zero P&L correlation, inflating `N_eff` and evading the haircut.
The weight-generating function is identical *before* the universe mask is applied, so
clustering on the pre-execution signal/weight vectors catches what P&L correlation
misses. Distance correlation (not Pearson) is the secondary layer for the nonlinear
case (one strategy trading the square of another's signal). Full design in P6.

Raw count is **strictly more punitive** than any clustering, because clustering can only *reduce* effective N, and reducing N *loosens* the haircut. So the P1 placeholder can only ever be too harsh — never too permissive.

**That is what makes it a legitimate fake and not a stub.** It is a complete, correct, tested implementation of a *more conservative* rule. It ships. It works. It is documented as conservative. `check_no_stubs.py` passes it because there is nothing to defer.

> A stub says *"this doesn't work yet."* A conservative fake says *"this works, and errs in the safe direction."* One of those is a lie waiting to be found; the other is engineering.

### 7.5 Verdicts

```python
class Verdict(StrEnum):
    PASS               = "pass"
    FAIL               = "fail"
    INSUFFICIENT       = "insufficient"     # fail-closed. not enough data OF THE RIGHT KIND yet.
    UNVERIFIABLE       = "unverifiable"     # no amount of THIS kind of data can grade it. §7.6
    UNSTABLE_DISTRIBUTION = "unstable-distribution"  # the statistic is undefined because the strategy is a time bomb. §7.7
    NO_POSITIONS       = "no-positions"     # §5.4
    TAINTED            = "tainted"          # cannot be graded against clean trials
```

**`INSUFFICIENT` is not a soft fail. It is a refusal to grade.** Per the Completion Standard, a gate never grades absent, sentinel, or un-provenanced input.

**The boundary is defined, not left to the builder.** `INSUFFICIENT` is returned when **any** of:

- `n_obs < 30` — this is a **numerical-stability floor, not a significance threshold**, and the distinction matters. There is nothing magic about 30; it is the point below which the Sharpe estimator's asymptotic-normality approximation (Jobson–Korkie / Opdyke), on which the DSR's `Φ` and `√(n_obs − 1)` both rest, becomes actively unreliable rather than merely wide. It does **not** mean 30 observations suffice for significance — the literature's Minimum Track Record Length can run to hundreds or thousands of observations to clear a benchmark at 95%. MinTRL as a *reported quantity* (how long a track record would need to be to trust this Sharpe) is a P6 concern, reserved below. Here, `n_obs < 30` is only the boundary below which the arithmetic is not to be trusted at all.
- `N < 2` — the expected-maximum-Sharpe term needs at least two trials to have a maximum over trials at all. `Φ⁻¹(1 − 1/1) = Φ⁻¹(0) = −∞`.
- *(radicand ≤ 0 does NOT route here — it routes to `UNSTABLE_DISTRIBUTION`; see §7.7)*
- the P&L series contains a `nan` or `inf`, or the cost-model hash is absent.

A number with a caveat attached is not an option, because caveats are not read and numbers are. Leaving the threshold unstated is not an option either — an unstated threshold is one the builder picks, and picks conveniently. These constants (`MIN_OBS_FOR_DSR = 30`, `MIN_TRIALS_FOR_DSR = 2`) are named, documented, and **not configurable.**

### 7.6 `UNVERIFIABLE` — the refusal that is not about quantity

`INSUFFICIENT` says *not enough data yet* — more history would fix it.
`UNVERIFIABLE` says *no amount of this kind of data can ever fix it.* The finding
needs something a price-and-volume backtest structurally cannot provide — realized
fills, execution prices, an exogenous market series — and a longer window
manufactures none of it.

The two must not be collapsed. A finding mislabelled `INSUFFICIENT` invites *"just
get more data"*; correctly labelled `UNVERIFIABLE`, it says the honest thing: this
question is out of reach of this instrument, and pretending otherwise with a
caveated PASS is how an unprovable number gets believed.

`UNVERIFIABLE` is recorded, never pooled into effective-N, and carries its reason
string. The producers of this verdict arrive in later phases (a regime layer with
no exogenous series; a capacity finding with no fill data) — but the verdict is in
the enum from the first row, because it is part of the frozen `TrialResult` and
adding it later would mean migrating a hash-chained append-only log (§2.3).

---

## 8. Taint mechanics

Location: `lab/ledger/taint.py`

Four properties, each independently tested:

| Property | Mechanism | Test |
|---|---|---|
| **In the hash** | `taints` is in both `pre_id` and `trial_id` preimages | `test_taint_changes_trial_id` |
| **Under the chain** | taint lives in the payload, which is hashed into `row_hash` | `test_taint_cannot_be_deleted_silently` |
| **Blocks pooling** | `haircut` reads only untainted rows for `trial_sharpes` | `test_tainted_trial_excluded_from_pool` |
| **On the export** | export includes `taints` per row and a summary header | `test_export_surfaces_taints` |

**Contagion:** a tainted trial cannot be laundered by re-running, because the taint is in the identity — the re-run is a *different trial*, and the tainted one is still in the chain.

**`unsafe` is human-only.** In P1 the machine interface does not yet exist (P7), but the *seam* does: `apply_taint()` requires an `Authorization` carrying a human principal. `lab/ledger/authz.py` ships the `HumanAuthorization` implementation and the `Authorization` Protocol. P7's agent surface will be structurally unable to produce one.

> Building the seam now, rather than the check later, is the difference between a boundary and an intention. An agent handed a crowbar will use it the moment an objective goes unmet — not from malice, but because routing around obstacles is what optimizers do.

---

## 9. The sealed write path

Location: `lab/ledger/record.py`

**This is the most important function in the repository.**

```python
def record(draft: TrialDraft, *, scope: Scope) -> TrialResult:
    """The ONLY way a TrialResult comes into existence."""
```

Sequence:

1. Compute `pre_id`.
2. **Pre-check.** `pre_id` in the index? → append `re-execution` row, return the stored result with `is_reexecution=True`. Trial count **not** incremented. *(No run happened — the engine called `record` only after the pre-check missed. See §9.1.)*
3. Compute `trial_id` from `net_pnl`.
4. **Behavioural check.** `trial_id` in the index? → append `re-execution` row, return stored result. Count **not** incremented. The compute was spent; the trial budget was not.
5. Acquire the ledger lock.
6. Read the in-scope trial Sharpes; compute the haircut.
7. Determine the verdict.
8. Mint `seq`, `prev_hash`, `row_hash`. Append. Flush. Fsync.
9. Release the lock.
10. Seal and return.


### 7.7 `UNSTABLE_DISTRIBUTION` — the strategy is a time bomb, not underpowered

Added under adversarial review. When the DSR radicand
`1 − γ₃·SR + ((γ₄−1)/4)·SR²` goes `≤ 0`, the Sharpe estimator's variance is
undefined — but the *reason* it is undefined is itself a damning fact about the
strategy. The radicand goes negative under high Sharpe with strong negative skew:
the signature of unhedged short volatility, selling insurance, picking up pennies in
front of a steamroller. The distribution has no stable second moment in the region
that matters.

Routing this to `INSUFFICIENT` ("not enough data yet") would be a **free pass for the
most dangerous strategies in the book** — more data does not stabilise a structurally
unstable distribution. Routing it to `FAIL` would be defensible but silent about
*why*. `UNSTABLE_DISTRIBUTION` is terminal and diagnostic: it says the strategy was
rejected because its return distribution is pathological, not because the sample was
small. It is recorded, never pooled, and carries the radicand value.


### 9.1 The pre-check happens in the engine, and that is not a bypass

The engine calls `identity.pre_id(...)` *before* simulating, so that an exact rerun costs no compute. This is the one place where the engine touches identity, and it is safe: `pre_id` is pure, it writes nothing, and the engine still cannot construct a `TrialResult` — only `record()` can.

`tests/adversarial/test_no_bypass.py::test_engine_cannot_construct_result` asserts, via the import graph, that `TrialResult(` appears nowhere outside `lab/ledger/`.

### 9.2 What happens if the haircut computation raises

The row is **still written**, with `Verdict.INSUFFICIENT` and the exception recorded in the payload.

Recording is unconditional. A trial that was run but could not be graded is still a trial that was run, and it still consumed a hypothesis from the search budget. Dropping it would be the single most useful bug an adversary could hope for — *"make my failed trials un-gradeable and they vanish from the count."*

---

## 10. Failure modes and edge cases

Each is specified, each has a test, and none of them is left to be discovered later.

| # | Case | Behaviour |
|---|---|---|
| 1 | Two processes append concurrently | Advisory lock; second blocks. §6.3 |
| 2 | Lock timeout | `LedgerBusyError`. **Never proceed unlocked.** |
| 3 | Crash mid-write, trailing partial line | Truncate the partial line only; `chain-repair` row; log ERROR. §6.4 |
| 4 | Interior corruption | `ChainCorruptError`. **Refuse to run.** No repair. |
| 5 | Ledger file missing | Create with a genesis row. |
| 6 | Ledger file empty (zero bytes) | Same as missing. |
| 7 | SQLite index missing or stale | Rebuild from JSONL. Index is disposable. |
| 8 | SQLite index disagrees with JSONL | **JSONL wins.** Rebuild. Log ERROR. |
| 9 | Direct write to SQLite | `test_sqlite_is_derived` fails the build. |
| 10 | Strategy takes no positions | `Verdict.NO_POSITIONS`. Recorded, not counted. §5.4 |
| 11 | NaN or inf in `Stats` | `SchemaError`. Never hashed. |
| 12 | `net_pnl` contains a float | `SchemaError` at draft construction. |
| 13 | Exact rerun (same `pre_id`) | Cached; `re-execution` row; count unchanged. |
| 14 | Rewritten strategy, same P&L (same `trial_id`) | `re-execution`; count unchanged. Compute spent, budget not. |
| 15 | Seed sweep, deterministic strategy | Collapses to 1 trial. §5.2 |
| 16 | Seed sweep, stochastic strategy | 10 trials. §5.2 |
| 17 | Taint added to an existing trial | New `trial_id`; new row. Old row remains. |
| 18 | Agent attempts `apply_taint` | No `Authorization` obtainable. §8 |
| 19 | `n_obs` too small for DSR | `Verdict.INSUFFICIENT`. Fail-closed. |
| 20 | `N < 5` in-scope trials | `SIGMA_SR_THIN_LEDGER_FALLBACK`. §7.3 |
| 21 | Haircut raises | Row written with `INSUFFICIENT` + exception. §9.2 |
| 22 | Scope switched project ↔ install | Recording unaffected. Console shows both counts. |
| 23 | Clock queried by a strategy | `StrategyIsolationError` at registration. §4.3 |
| 24 | Ledger on a filesystem without `flock` (e.g. some NFS) | Detect at startup; **refuse to run**; document. A silent no-op lock is worse than no lock. |

Case 24 is the kind of thing that gets discovered in production by a user whose ledger is quietly forked across two machines on a network share. It is cheap to detect and catastrophic to miss.

---

## 11. Test plan

Every test below is in the MANIFEST. **A test that does not exist is a manifest failure, not an oversight.**

### `tests/unit/core/`
- `test_money.py::test_paise_is_int`
- `test_money.py::test_rounding_half_up_per_charge`
- `test_money.py::test_no_float_in_money_path` *(AST grep — fails the build)*
- `test_clock.py::test_asof_is_tz_aware_ist`
- `test_clock.py::test_asof_ordering`

### `tests/unit/ledger/`
- `test_canonical.py::test_canonical_json_is_stable`
- `test_canonical.py::test_float_repr_round_trips` *(fuzz: subnormals, ±inf, NaN)*
- `test_canonical.py::test_decimal_and_paise_serialise_as_strings`
- `test_identity.py::test_pre_id_ignores_formatting`
- `test_identity.py::test_pre_id_changes_on_logic_change`
- `test_identity.py::test_trial_id_from_pnl_only`
- `test_identity.py::test_rewritten_strategy_same_pnl_same_trial_id`
- `test_identity.py::test_deterministic_seed_sweep_collapses_to_one_trial`
- `test_identity.py::test_stochastic_seed_sweep_yields_n_trials`
- `test_chain.py::test_genesis_row`
- `test_chain.py::test_append_links_prev_hash`
- `test_chain.py::test_verify_walks_from_genesis`
- `test_store.py::test_never_opens_truncating` *(AST grep)*
- `test_store.py::test_fsync_called_on_every_append`
- `test_store.py::test_missing_file_creates_genesis`
- `test_store.py::test_empty_file_creates_genesis`
- `test_index.py::test_rebuild_from_jsonl_alone`
- `test_index.py::test_index_disagreement_jsonl_wins`
- `test_taint.py::test_taint_changes_trial_id`
- `test_taint.py::test_tainted_trial_excluded_from_pool`
- `test_taint.py::test_export_surfaces_taints`
- `test_taint.py::test_apply_taint_requires_human_authorization`
- `test_record.py::test_reexecution_does_not_increment_count`
- `test_record.py::test_haircut_exception_still_writes_row`
- `test_record.py::test_no_positions_verdict`

### `tests/unit/validation/`
- `test_haircut.py::test_dsr_matches_reference_values` *(fixture: published worked examples)*
- `test_haircut.py::test_expected_max_sharpe_grows_with_n`
- `test_haircut.py::test_sigma_sr_is_analytic_null` *(σ_SR = 1/√(T−1); no fitted constant; per-period by construction)*
- `test_haircut.py::test_raw_count_is_at_least_as_punitive_as_clustered` *(property test: for any clustering, raw ≥ clustered ⇒ haircut is never looser)*
- `test_haircut.py::test_insufficient_when_n_obs_too_small`
- `test_haircut.py::test_negative_radicand_is_unstable` *(high-Sharpe negative-skew fixture; asserts UNSTABLE_DISTRIBUTION, never nan, never INSUFFICIENT)*
- `test_haircut.py::test_insufficient_boundaries` *(n_obs=29→INSUFFICIENT, 30→graded; N=1→INSUFFICIENT, 2→graded)*
- `test_haircut.py::test_kurtosis_convention` *(Gaussian fixture reads non-excess kurtosis 3.0)*
- `test_haircut.py::test_annualised_sharpe_rejected_or_converted_once` *(feeding an annualised value produces a different, wrong DSR — pins the units contract)*

### `tests/integration/ledger/`
- `test_concurrent_append.py::test_16_processes_1600_rows` *(chain verifies; no dupes; no losses)*
- `test_crash_recovery.py::test_trailing_partial_line_repaired`
- `test_crash_recovery.py::test_interior_corruption_refuses_to_run`
- `test_verify_standalone.py::test_verifier_runs_without_lab_installed` *(subprocess, clean venv, `json` + `hashlib` only)*

### `tests/adversarial/`
- `test_no_bypass.py::test_engine_cannot_construct_result` *(import graph)*
- `test_no_bypass.py::test_no_result_without_ledger_row`
- `test_no_bypass.py::test_suppressing_logs_does_not_suppress_ledger`
- `test_ledger_tamper.py::test_edit_interior_row_detected`
- `test_ledger_tamper.py::test_delete_interior_row_detected`
- `test_ledger_tamper.py::test_reorder_rows_detected`
- `test_ledger_tamper.py::test_duplicate_seq_detected`
- `test_ledger_tamper.py::test_forged_row_hash_detected`
- `test_clock.py::test_asof_never_from_wall_clock` *(AST grep)*
- `test_clock.py::test_strategy_importing_network_is_rejected`
- `test_clock.py::test_strategy_calling_datetime_now_is_rejected`
- `test_flock_unavailable_refuses_to_run.py`

### `tests/completeness/`
- `test_manifest.py::test_every_manifest_row_exists`
- `test_manifest.py::test_every_call_site_required_row_is_called`
- `test_manifest.py::test_every_deep_dive_section_has_a_manifest_row`
- `test_manifest.py::test_every_manifest_row_cites_a_deep_dive_section`
- `test_no_stubs.py::test_no_stubs_in_phase_scope`
- `test_attribution.py::test_no_attribution_in_history`

---

## 12. MANIFEST — frozen

**Every row is built in this phase.** Not the ones the gate touches. Every row.

A row removed requires an amendment to this deep dive (dated, reasoned) and a corresponding removal here, per `MASTER_BLUEPRINT.md` §10.5. **Silent omission is a build failure, not a judgement call.**

```yaml
manifest_version: 1
phase: P1
frozen: true

rows:
  # ---- core types ----
  - id: P1.CORE.MONEY
    artifact: lab.core.types.Paise
    kind: type
    spec: "§3.1"
    call_site: required
    certifying_test: tests/unit/core/test_money.py::test_paise_is_int

  - id: P1.CORE.ROUNDING
    artifact: lab.core.money.quantise_paise
    kind: function
    spec: "§3.1"
    call_site: required
    certifying_test: tests/unit/core/test_money.py::test_rounding_half_up_per_charge

  - id: P1.CORE.ASOF
    artifact: lab.core.types.AsOf
    kind: type
    spec: "§3.2"
    call_site: required
    certifying_test: tests/unit/core/test_clock.py::test_asof_is_tz_aware_ist

  - id: P1.CORE.DATERANGE
    artifact: lab.core.types.DateRange
    kind: type
    spec: "§3.2"
    call_site: required
    certifying_test: tests/unit/core/test_clock.py::test_asof_ordering

  - id: P1.CORE.CLOCK
    artifact: lab.core.clock.Clock
    kind: class
    spec: "§4.1"
    call_site: required
    certifying_test: tests/adversarial/test_clock.py::test_asof_never_from_wall_clock

  - id: P1.CORE.MARKETVIEW
    artifact: lab.core.view.MarketView
    kind: protocol
    spec: "§4.2"
    call_site: required
    certifying_test: tests/unit/core/test_clock.py::test_asof_ordering

  - id: P1.CORE.NULLVIEW
    artifact: lab.core.view.NullMarketView
    kind: class
    spec: "§4.2"
    call_site: required
    certifying_test: tests/adversarial/test_clock.py::test_strategy_calling_datetime_now_is_rejected

  - id: P1.CORE.SANDBOX
    artifact: lab.core.sandbox.run_isolated
    kind: function
    spec: "§4.3"
    call_site: required
    certifying_test: tests/adversarial/test_clock.py::test_strategy_importing_network_is_rejected

  - id: P1.CORE.ISOLATION_AST
    artifact: lab.core.sandbox.inspect_strategy_ast
    kind: function
    spec: "§4.3"
    call_site: required
    certifying_test: tests/adversarial/test_clock.py::test_strategy_calling_datetime_now_is_rejected

  # ---- ledger schema ----
  - id: P1.SCHEMA.TAINT
    artifact: lab.ledger.schema.Taint
    kind: enum
    spec: "§3.3"
    call_site: required
    certifying_test: tests/unit/ledger/test_taint.py::test_taint_changes_trial_id

  - id: P1.SCHEMA.DRAFT
    artifact: lab.ledger.schema.TrialDraft
    kind: type
    spec: "§3.4"
    call_site: required
    certifying_test: tests/unit/ledger/test_record.py::test_no_positions_verdict

  - id: P1.SCHEMA.RESULT
    artifact: lab.ledger.schema.TrialResult
    kind: type
    spec: "§3.5"
    call_site: required
    certifying_test: tests/adversarial/test_no_bypass.py::test_engine_cannot_construct_result

  - id: P1.SCHEMA.SEAL
    artifact: lab.ledger.seal.SealToken
    kind: type
    spec: "§3.5"
    call_site: required
    certifying_test: tests/adversarial/test_no_bypass.py::test_engine_cannot_construct_result

  - id: P1.SCHEMA.VERDICT
    artifact: lab.ledger.schema.Verdict
    kind: enum
    spec: "§7.5"
    call_site: required
    certifying_test: tests/unit/validation/test_haircut.py::test_insufficient_when_n_obs_too_small

  # ---- canonical form ----
  - id: P1.CANON.DUMPS
    artifact: lab.ledger.canonical.dumps
    kind: function
    spec: "§5.3"
    call_site: required
    certifying_test: tests/unit/ledger/test_canonical.py::test_canonical_json_is_stable

  - id: P1.CANON.FLOAT
    artifact: lab.ledger.canonical.encode_float
    kind: function
    spec: "§5.3"
    call_site: required
    certifying_test: tests/unit/ledger/test_canonical.py::test_float_repr_round_trips

  # ---- identity ----
  - id: P1.ID.AST
    artifact: lab.ledger.identity.normalized_ast_hash
    kind: function
    spec: "§5.1"
    call_site: required
    certifying_test: tests/unit/ledger/test_identity.py::test_pre_id_ignores_formatting

  - id: P1.ID.PRE
    artifact: lab.ledger.identity.pre_id
    kind: function
    spec: "§5.1"
    call_site: required
    certifying_test: tests/unit/ledger/test_identity.py::test_pre_id_changes_on_logic_change

  - id: P1.ID.TRIAL
    artifact: lab.ledger.identity.trial_id
    kind: function
    spec: "§5.2"
    call_site: required
    certifying_test: tests/unit/ledger/test_identity.py::test_trial_id_from_pnl_only

  # ---- chain ----
  - id: P1.CHAIN.GENESIS
    artifact: lab.ledger.chain.genesis_row
    kind: function
    spec: "§6.1"
    call_site: required
    certifying_test: tests/unit/ledger/test_chain.py::test_genesis_row

  - id: P1.CHAIN.HASH
    artifact: lab.ledger.chain.row_hash
    kind: function
    spec: "§6.1"
    call_site: required
    certifying_test: tests/unit/ledger/test_chain.py::test_append_links_prev_hash

  - id: P1.CHAIN.VERIFY
    artifact: lab.ledger.chain.verify
    kind: function
    spec: "§6.5"
    call_site: required
    certifying_test: tests/adversarial/test_ledger_tamper.py::test_edit_interior_row_detected

  - id: P1.CHAIN.VERIFY_CLI
    artifact: tools/verify_ledger.py
    kind: script
    spec: "§6.5"
    call_site: required
    certifying_test: tests/integration/ledger/test_verify_standalone.py::test_verifier_runs_without_lab_installed

  # ---- store ----
  - id: P1.STORE.APPEND
    artifact: lab.ledger.store.Ledger.append
    kind: method
    spec: "§6.2"
    call_site: required
    certifying_test: tests/unit/ledger/test_store.py::test_fsync_called_on_every_append

  - id: P1.STORE.LOCK
    artifact: lab.ledger.lock.ledger_lock
    kind: contextmanager
    spec: "§6.3"
    call_site: required
    certifying_test: tests/integration/ledger/test_concurrent_append.py::test_16_processes_1600_rows

  - id: P1.STORE.FLOCK_CHECK
    artifact: lab.ledger.lock.assert_locking_supported
    kind: function
    spec: "§10 case 24"
    call_site: required
    certifying_test: tests/adversarial/test_flock_unavailable_refuses_to_run.py

  - id: P1.STORE.RECOVER
    artifact: lab.ledger.store.Ledger.recover_trailing_partial
    kind: method
    spec: "§6.4"
    call_site: required
    certifying_test: tests/integration/ledger/test_crash_recovery.py::test_trailing_partial_line_repaired

  - id: P1.STORE.SCOPE
    artifact: lab.ledger.store.Scope
    kind: enum
    spec: "§6.6"
    call_site: required
    certifying_test: tests/unit/ledger/test_record.py::test_reexecution_does_not_increment_count

  # ---- index ----
  - id: P1.INDEX.REBUILD
    artifact: lab.ledger.index.rebuild
    kind: function
    spec: "§6.6"
    call_site: required
    certifying_test: tests/unit/ledger/test_index.py::test_rebuild_from_jsonl_alone

  - id: P1.INDEX.LOOKUP
    artifact: lab.ledger.index.lookup
    kind: function
    spec: "§9"
    call_site: required
    certifying_test: tests/unit/ledger/test_index.py::test_index_disagreement_jsonl_wins

  # ---- taint ----
  - id: P1.TAINT.APPLY
    artifact: lab.ledger.taint.apply_taint
    kind: function
    spec: "§8"
    call_site: required
    certifying_test: tests/unit/ledger/test_taint.py::test_apply_taint_requires_human_authorization

  - id: P1.TAINT.AUTHZ
    artifact: lab.ledger.authz.Authorization
    kind: protocol
    spec: "§8"
    call_site: required
    certifying_test: tests/unit/ledger/test_taint.py::test_apply_taint_requires_human_authorization

  - id: P1.TAINT.HUMAN
    artifact: lab.ledger.authz.HumanAuthorization
    kind: class
    spec: "§8"
    call_site: required
    certifying_test: tests/unit/ledger/test_taint.py::test_apply_taint_requires_human_authorization

  - id: P1.TAINT.POOL
    artifact: lab.ledger.taint.filter_untainted
    kind: function
    spec: "§8"
    call_site: required
    certifying_test: tests/unit/ledger/test_taint.py::test_tainted_trial_excluded_from_pool

  - id: P1.TAINT.EXPORT
    artifact: lab.ledger.export.export_ledger
    kind: function
    spec: "§8"
    call_site: required
    certifying_test: tests/unit/ledger/test_taint.py::test_export_surfaces_taints

  # ---- the sealed write path ----
  - id: P1.RECORD
    artifact: lab.ledger.record.record
    kind: function
    spec: "§9"
    call_site: required
    certifying_test: tests/adversarial/test_no_bypass.py::test_no_result_without_ledger_row

  # ---- haircut ----
  - id: P1.HAIRCUT.COMPUTE
    artifact: lab.validation.haircut.compute_haircut
    kind: function
    spec: "§7.1"
    call_site: required
    certifying_test: tests/unit/validation/test_haircut.py::test_dsr_matches_reference_values

  - id: P1.HAIRCUT.EMAXSR
    artifact: lab.validation.haircut.expected_max_sharpe
    kind: function
    spec: "§7.2"
    call_site: required
    certifying_test: tests/unit/validation/test_haircut.py::test_expected_max_sharpe_grows_with_n

  - id: P1.HAIRCUT.FALLBACK
    artifact: lab.validation.haircut.SIGMA_SR_THIN_LEDGER_FALLBACK
    kind: constant
    spec: "§7.3"
    call_site: required
    certifying_test: tests/unit/validation/test_haircut.py::test_thin_ledger_fallback_is_punitive

  - id: P1.HAIRCUT.RAWCOUNT
    artifact: lab.validation.haircut.raw_effective_n
    kind: function
    spec: "§7.4"
    call_site: required
    certifying_test: tests/unit/validation/test_haircut.py::test_raw_count_is_at_least_as_punitive_as_clustered

  # ---- errors ----
  - id: P1.ERR.CHAIN
    artifact: lab.ledger.errors.ChainCorruptError
    kind: exception
    spec: "§6.4"
    call_site: required
    certifying_test: tests/integration/ledger/test_crash_recovery.py::test_interior_corruption_refuses_to_run

  - id: P1.ERR.BUSY
    artifact: lab.ledger.errors.LedgerBusyError
    kind: exception
    spec: "§6.3"
    call_site: required
    certifying_test: tests/integration/ledger/test_concurrent_append.py::test_16_processes_1600_rows

  - id: P1.ERR.SEAL
    artifact: lab.ledger.errors.SealError
    kind: exception
    spec: "§3.5"
    call_site: required
    certifying_test: tests/adversarial/test_no_bypass.py::test_engine_cannot_construct_result

  - id: P1.ERR.SCHEMA
    artifact: lab.ledger.errors.SchemaError
    kind: exception
    spec: "§10 cases 11,12"
    call_site: required
    certifying_test: tests/unit/ledger/test_canonical.py::test_float_repr_round_trips

  - id: P1.ERR.ISOLATION
    artifact: lab.core.errors.StrategyIsolationError
    kind: exception
    spec: "§4.3"
    call_site: required
    certifying_test: tests/adversarial/test_clock.py::test_strategy_importing_network_is_rejected

  # ---- console meter (v1 CLI) ----
  - id: P1.METER
    artifact: lab.consoles.meter.render_meter
    kind: function
    spec: "§6.6"
    call_site: required
    certifying_test: tests/unit/ledger/test_record.py::test_reexecution_does_not_increment_count
```

---

## 13. GATE 1 — exit

Both gates. Neither alone is sufficient.

**Correctness gate** — every test in §11 passes.

**Completeness gate** —
- `check_manifest.py`: every row in §12 exists; every `call_site: required` row is referenced outside its own module and its own test; every §-section has ≥1 row; every row cites a §-section.
- `check_no_stubs.py`: clean over `src/lab/`.
- `check_import_graph.py`: `TrialResult` constructed nowhere outside `lab/ledger/`; nothing outside `lab/ledger/` writes the ledger.
- `check_attribution.py`: clean over the full history.
- `DEFERRALS.md` is **empty**.

Merge the phase PR. Tag `gate-1-substrate`. The tag commit contains the complete deliverables.

---

## 14. Amendment log

| Date | Section | Change | Reason |
|---|---|---|---|
| 2026-07-13 | — | Initial. Manifest frozen. | — |
