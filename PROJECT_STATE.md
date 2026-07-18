# PROJECT STATE

Living document. Update at the end of every session.

Tracks **criteria met**, not days elapsed. There is no schedule here by design
(CONSTITUTION §11).

---

## Current phase

**P1 — Substrate: ledger, clock, haircut**

Status: not started

---

## Phase board

| Phase | Gate | Status |
|---|---|---|
| P0 — Repo, remote, enforcement machinery | self-bootstrap | not started |
| P1 — Substrate: ledger, clock, haircut | — | not started |
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

---

## Session log

| Date | Phase | What moved | What broke |
|---|---|---|---|
| — | P0 | Constitution, acceptance criteria, contracts, playbook ratified | — |
