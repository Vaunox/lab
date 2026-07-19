# Planted violation for check_spec_isolation

`FIXTURE_CHANGED_FILES` is the diff under judgement: the path list a real run
would have taken from `git diff --name-only origin/main...HEAD`.

It touches all three tiers at once — `CONSTITUTION.md` and a frozen deep dive
(SPEC), `src/` and `tools/` (CODE), and `HANDOFF.md` (LOGS). That is failure
case 11, and the log entry is present deliberately: a checker that fails this
tree by counting *any* three-tier diff as mixed, rather than by pairing SPEC
with CODE, would also fail case 12 — and case 12 must pass.

This tree carries no `.git`, so `bootstrap_exception_applies` reports the
exception closed rather than granting an exception it cannot demonstrate an
entitlement to. The seam that reads this file is unreachable in the real
repository for the same reason, inverted: the real repository has a `.git`, so
its diff always comes from git and never from a tracked text file.
