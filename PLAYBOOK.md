# PLAYBOOK

Pre-committed responses, written before the pressure exists.

Read the trigger. Do the response. Do not re-litigate it in the moment — the
moment is precisely when your judgement is compromised, which is the entire
reason this file exists.

---

## Against the builder

### B1 — A fixture and the engine disagree by a small margin

**Trigger:** The engine matches the hand-derived fixture everywhere except a handful of trades, and the difference is small.

**Response:** Do not adjust the engine to match. Do not adjust the fixture. Find the cause first. Then classify — and note there are only **two** cases, because **there is no baseline to be wrong**:

- **The derivation is wrong** → fix the derivation, **in its own PR**, showing the corrected arithmetic. Then re-run.
- **The engine is wrong** → fix the engine.

There is no third case. **A divergence is never "accepted" — it is resolved.**

"Small" is not a classification. An unexplained divergence in a machine whose product is trust is an unknown bug in a cost or fill path, and it will ship.

### B2 — The builder proposes a flag in the shared loop

**Trigger:** *"We can unify these two engines and branch on `instrument_type`."*

**Response:** No. This is S1 territory (CONSTITUTION §10). Duplicated engine
loops are cheap; a wrong abstraction is not. Every subtle lookahead bug in this
system's future lives inside conditionals that nobody is looking at.

### B3 — The builder proposes relaxing a fixture or a tolerance

**Trigger:** *"1e-10 is unrealistically strict; 1e-6 would be reasonable."*

**Response:** No, on the cost and position paths — those are Decimal and integer
and must be exact. On float statistics, 1e-10 was chosen because it is achievable
in-container on one architecture. If it is not achievable, the cause is a
non-determinism you have not found yet. Find it.

### B4 — The builder is confidently wrong about a cost

**Trigger:** A statutory rate appears without a citation.

**Response:** Reject. Every statutory row carries an effective-from date and a
primary source URL. The cost schedule is the one part of this repo that strangers
will independently audit. Memory is not a source.

---

## Against yourself

### Y1 — You want to add a deadline

**Trigger:** *"I'd like to ship by [month]."*

**Response:** No. A deadline is a force pushing against a gate that must not
bend. Phases gate on criteria, not dates. This is the one PM artifact excluded
deliberately (CONSTITUTION §11).

If you need a sense of progress, look at `PROJECT_STATE.md`. It tracks criteria
met, not days elapsed.

### Y2 — Adoption is slow and you want to ship a working example strategy

**Trigger:** *"Nobody can get started. One good example strategy would fix it."*

**Response:** No. This is refusal #2 and it is also the RA line. The moment you
ship a working cartridge with a backtest attached, you are arguably a signal
provider, and the entire regulatory shape changes.

Ship better **fixtures** (labelled, noise-based, no performance figures) and a
better tutorial on the synthetic dataset. The onboarding problem is real; this is
not its solution.

### Y3 — The null test comes back at 25%

**Trigger:** The battery passes a quarter of random strategies on pure noise.

**Response:** **S2. Do not release.** The multiple-testing correction is broken.
The machine currently launders bad research under a credibility claim, which is
strictly worse than not existing.

Debug order: (1) is effective-N being computed at all? (2) is clustering
collapsing N too aggressively? (3) is the DSR using the wrong Sharpe dispersion?
(4) are costs actually being applied in the null path?

### Y4 — The null test comes back at 0.2%

**Trigger:** The battery passes almost nothing.

**Response:** This is **also** a failure signal, and it will feel like a success.
Run the power test. If detection is below 60% at net Sharpe 1.0, the battery is
not rigorous — it is blunt. Rejecting everything is not rigour; it is an
expensive way to have no opinion. **S3.**

### Y5 — The power calculator says your search budget is tiny

**Trigger:** With five years of data and a Sharpe bar of 1.0, the arithmetic
permits roughly fifty trials program-wide before nothing is believable any more.

**Response:** This is correct and it is the machine working. It is not a bug to
be engineered around. It is the central teaching of the Lab, arriving early
enough to be useful.

Do not respond by loosening the haircut. Respond by getting more data, raising
the bar, or accepting that you have fifty shots.

### Y6 — You want the public kernel to do something private

**Trigger:** Your own private research needs an API change in the Lab that would reveal what you are researching.

**Response:** **This is a boundary alarm, not a feature request.** The kernel contains no alpha *by construction*. If a public API change would telegraph your research, alpha has leaked into the kernel.

Fix the boundary. **Do not fork.** A fork guarantees the cost models drift, and drift in a cost model is fatal.

### Y7 — Someone forks and strips the ledger

**Trigger:** A fork appears with the haircut removed.

**Response:** Expected. Do nothing.

You cannot stop this and were never trying to. The `unsafe` crowbar exists
precisely so that people stay *inside* the system where the hash chain, the
taints, and the record still apply to them. A fork carries none of that, and its
results carry no credibility. The market will sort it.

Do **not** respond by making the official tool more permissive to compete.

---

## From users

### U1 — "Add a `--no-ledger` / `--quick` flag"

**Response:** No. See CONSTITUTION §6. The ledger is not a log level. Anything
that suppresses logging must not suppress the ledger; a `--quiet` flag that
became `--no-ledger` by accident is exactly the failure this architecture was
built to prevent.

Point them at `unsafe`. It works. It taints. That is the deal.

### U2 — "Your Sharpe numbers are lower than [other tool]'s"

**Response:** Correct. That complaint is the product working.

Every competing library lets people lie to themselves *fast*, which is what most
of them want. The Lab is the backtester that tells you no. If you flinch and add
the flag, you have shipped a commodity backtester with extra steps.

### U3 — "The DP charge is too conservative"

**Response:** The DP charge is a **fact**, not a setting (CONTRACTS §Settings).
It is broker-level and lives in the broker profile — if their broker genuinely
charges less, the fix is a corrected, cited broker profile, submitted as a PR.

If they want it lower than their broker actually charges, that is `unsafe`, and
it taints.

### U4 — "Your 2019 STT is wrong"

**Response:** Thank them, and check. This is the audit working. Every statutory
row has a citation for exactly this conversation. If they are right, correct the
row, bump the cost model version, and note that all trials under the old hash are
now under a different cost model and are not pooled with new ones.

### U5 — "Can you add options?"

**Response:** Deferred, not refused. The blocker is not the engine — it is owning
the cost model, including the STT-on-exercised-ITM trap that vaporises retail
accounts and that no generic backtester models.

A Lab with a calibrated equity cost model and no options support is credible. A
Lab that claims options and gets the STT wrong is a liability with a nice API.

---

---

## Against the agent

An agent is not malicious. It is an optimizer, and an optimizer told to obtain a
PASS will route around anything standing between it and a PASS. Treat every entry
below as *expected behaviour*, not misconduct.

### A1 — The agent asks for `unsafe`

**Trigger:** *"The slippage floor is preventing me from validating this strategy.
Requesting an override."*

**Response:** No. `unsafe` is a human affordance (CONSTITUTION §8.12). An agent
that could taint its own trials would taint them all and proceed, and the taint
system would become a formality it fills in on its way past.

Any override requires a human in the loop, and the human's name lands on the
taint. If you find yourself approving these routinely, that is B-series
behaviour with the agent in the builder's seat, and it means Layer 2 is missing a
named research mode. Go build it.

### A2 — The agent burns its budget and asks for more

**Trigger:** *"Trial budget exhausted at 500. Requesting an increase to continue
the search."*

**Response:** The budget is not a rate limit. It is the number of trials your data
can support before nothing is believable any more, and it came out of the power
calculator, not out of a preference.

Raising it does not buy more search. It buys a higher Sharpe bar, which the agent
will then also fail to clear. Granting the increase feels like unblocking
progress. It is unblocking *nothing* — the arithmetic moved with it.

**Compute is cheap. Belief is not.**

### A3 — The agent generates a thousand strategies and half of them are the same

**Trigger:** 200 proposals, 4 effective clusters.

**Response:** This is the system working, and it is the most useful thing the Lab
can tell an agent. It is not exploring; it is jittering. Report the cluster count
back to it as a navigation signal.

The failure mode of an automated quant loop is not running out of compute. It is
**mistaking repetition for exploration.**

### A4 — The agent finds a genuine seam

**Trigger:** During the red-team gate, the agent obtains a PASS on pure noise.

**Response:** **Excellent.** That seam was going to be found by someone. Better
here, before release, by a machine you pointed at yourself.

Close it. Re-run the gate. Add the seam to this playbook.

### A5 — The agent proposes a strategy that passes

**Trigger:** After a legitimate, budgeted search, something clears the haircut.

**Response:** Treat it exactly as you would a human's result, with one addition:
**check the correlation against the graveyard.** An agent that produced 500 near
-identical proposals and one outlier has not found an edge; it has found the tail
of its own distribution, and the haircut is the only thing standing between you
and believing it.

If the haircut cleared it honestly, it cleared it. That is what the haircut is
for. Do not add a second, ad-hoc layer of suspicion *only* because a machine
proposed it — that would be moving the goalposts, which is the sin this entire
project exists to prevent.

---

## The recurring shape

Almost every entry above is the same request wearing a different hat:

> *Make the number better without making the strategy better.*

The Lab's only job is to refuse that. Everything else it does — the PIT clock,
the dated costs, the fill gate, the ledger, the hash chain, the haircut, the
graveyard — is machinery in service of that one refusal.

If the Lab stops refusing, it has become the thing it was built to replace, and
`S4` applies.
