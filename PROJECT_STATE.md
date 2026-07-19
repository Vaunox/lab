# PROJECT STATE

Living document. Update at the end of every session.

Tracks **criteria met**, not days elapsed. There is no schedule here by design
(CONSTITUTION §11).

---

## Current phase

**P1 — Substrate: ledger, clock, haircut**

Status: **not started.** Opens on `phase/p1-substrate`, cut from `main`.

Previous phase **P0 is complete** — Gate 0 met, tagged `gate-0-scaffold`. A fresh clone of
that tag reports `GATE GREEN -- 10 stages passed`. Archived handoff:
`docs/handoff/P0_HANDOFF.md`.

*(This header read "P1" while the board still read "P0 — not started". The board was right and
the header was aspirational. They now agree, and the header is true for the first time.)*

---

## Phase board

| Phase | Gate | Status |
|---|---|---|
| P0 — Repo, remote, enforcement machinery | self-bootstrap | **done** — G0 met, tagged `gate-0-scaffold` |
| P1 — Substrate: ledger, clock, haircut | **GATE 1** | **current** — not started |
| P2 — Cost kernel | — | not started |
| P3 — Data plane | random null + **LLM null** + power | not started |
| P4 — Engine A: daily cross-sectional | **GATE 1** | not started |
| P5 — Engine B: intraday | **GATE 2 (kill gate)** | not started |
| P6 — Validation battery | all three calibration tests re-run | not started |
| P7 — Consoles + machine interface | agent boundary enforced | not started |
| P8 — Release hardening | **red-team gate** | not started |
| P9 — Alpha → public | stop conditions review | not started |

P2 and P3 may run in parallel.

---

## Open acceptance criteria — current phase

Copied from `ACCEPTANCE.md`. Tick only when the test passes, not when the code
looks right.

- [ ] `test_no_result_without_ledger`
- [ ] `test_sqlite_is_derived`
- [ ] `test_hash_chain_detects_tamper`
- [ ] `test_strategy_cannot_read_clock`
- [ ] Content-addressed trial identity; rerun ≠ new trial
- [ ] Seed change → new trial hash
- [ ] `taints[]` participates in the trial hash

---

## Decisions log

Decisions that are settled and are not re-opened. If something here is
re-litigated, it belongs in the CONSTITUTION amendment log instead.

| Decision | Rationale |
|---|---|
| Apache-2.0 | Explicit patent grant; appropriate for finance-adjacent |
| **The engine is never its own oracle** | A fixture the engine produced is not a gate. It is a mirror. |
| Gates compare against **hand-derived** ground truth | If you cannot compute the right answer yourself, you cannot tell whether the engine did |
| The kill gate is **substrate invariance** | It tests what is actually at stake: one contract, two dissimilar semantics, no contamination of shared truth |
| Defaults ship, but ratchet | A tool with no defaults is a religion; a default that moves quietly is a lie |
| Recording install-wide; **counting scope** is the setting | Preserves user choice, makes evasion visible rather than impossible |
| Engines isolated; substrate shared | Engines may duplicate logic, never truth |
| Engine declared, never inferred | Misrouting is a silently wrong cost model |
| Money is Decimal/integer paise | Makes tolerance-0 reproduction achievable |
| No timeline, ever | A deadline is a force pushing against a gate that must not bend |
| Calibration effect size is a fixture, not a setting | A calibration the user can move is not a calibration |
| Paper trading is an **engine** (v2), not a subsystem | Otherwise it becomes a trial-generating machine the ledger cannot see |
| LLM agents are a first-class caller, designed for from P1 | Adapting to them later would mean retrofitting the ledger, which is hash-chained and append-only |
| Trial identity is **behavioural**, not textual | An LLM regenerates identical logic with new variable names indefinitely; AST-only identity inflates the haircut on repetition rather than on search |
| The **LLM null test** is the load-bearing calibration | Random strategies are near-independent, so the random null test passes almost regardless of whether clustering works. LLM strategies are heavily correlated. Effective-N is now safety-critical. |
| `unsafe` is human-only; agents never get the crowbar | An agent that could taint its own trials would taint them all and proceed |
| Hard trial budget per agent session | Compute is cheap; belief is not |

---

## Blocked / needs a decision

| Item | Blocking | Notes |
|---|---|---|
| NSE price-band file archive | P3 fill gate | **Start the daily scraper now.** NSE does not backfill. Every day not saved is a hole that cannot be filled later. This is the one deferral that has a running cost. |
| Bhavcopy provenance tiering | P3 | Self-captured vs third-party archive. Field exists; source list needs writing. |
| **Q-002 — the skip/xfail citation rule is inert** | **P4/P5** — the first phase producing a divergence-citing skip | Two defects, and they compound. (1) `DIVERGENCES.md` has **no ID column**, so §7.1's *"`@pytest.mark.skip`/`xfail` — unless it cites a `DIVERGENCES.md` ID"* row has nothing to cite. (2) `check_no_stubs` scans `SCAN_ROOTS = ("src/lab", "tools")` and **never scans `tests/`** — and a divergence-citing skip lives only in `tests/`. So that row **can never fire where it applies**: such a skip passes the gate in silence. Verified empirically — the identical `@pytest.mark.skip` is reported in `tools/` and not reported in `tests/`. `pytest --strict-markers` does **not** backstop it, because `skip`/`xfail` are builtin markers (observed: `1 skipped`, exit 0). **Resolve as one package, at the owning phase:** decide the ID/citation scheme, **fix the scan scope in the checker** — a column or marker alone leaves the checker vacuous — and **add a planted-violation fixture proving the row can fail** (§2.2). Not fixed at P0 by operator ruling: fixing the scan scope in isolation couples it to an undecided citation scheme and could hard-fail a legitimate P1 skip. |
| **D-004 — the fixture-provenance checker fails open** | **P4** — when the first hand-derived gate fixtures land | `check_fixture_provenance.parse_declarations` returns `[]` when `DECLARATION_MARKER` (`<!-- gate_fixtures -->`) is absent, so `check()` reports zero declarations and **exits 0**. With real hand-derived fixtures on disk and no declaration block, it therefore passes — while printing the P0 rationale *"no gate fixtures declared… that is the expected P0 state"* **beside P4's fixtures**. It cannot distinguish *no fixtures exist* from *fixtures exist and nobody declared them*, so the checker guarding Inviolable Rule 4 (**the engine is never its own oracle**) becomes a no-op exactly when it first matters. **Resolve at P4:** define what counts as *fixture-shaped*, **make the checker fail closed when fixture-shaped files exist undeclared** — confirming or amending the declaration format alone leaves it vacuous — and **add a planted-violation fixture for the undeclared-fixture case** (§2.2). The declaration format itself (`<!-- gate_fixtures -->` + fenced yaml: `id`, `path`, `blob_sha`, `derivation`, optional `engine_path`) is a `[BUILDER]` decision from P0 awaiting P4's confirmation. |

---

## Session log

| Date | Phase | What moved | What broke |
|---|---|---|---|
| — | P0 | Constitution, acceptance criteria, contracts, playbook ratified | — |
| 2026-07-18 | P0 | Bootstrap: repo, public remote, protected `main`, phase branch. `gate.py` and `check_manifest.py` built. | Gate red — no certifying test existed for either checker. |
| 2026-07-19 | P0 | **Gate 0 met.** All seven checkers built, each with a planted violation and a negative control. 32/32 manifest rows, 93 tests, CI green on ubuntu/windows/macos. PR #1 and #2 merged, `gate-0-scaffold` tagged. | Six `call_site: required` rows had no honest caller — resolved by operator ruling as amendment A-004, not by manufacturing callers. First CI run caught two environment-shaped defects invisible locally (DE-004, DE-005). Merging PR #1 closed the §5.4 exception and falsified two tests that had asserted it was open (DE-006). |
