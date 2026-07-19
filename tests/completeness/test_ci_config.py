"""CI configuration. Deep dive P0 sections 5 and 5.2.

The `gate` context name is the subtlest trap in the phase, and it fails in the
worst possible direction: a completely green CI run that still blocks the merge,
with nothing in the logs to explain why. These tests exist so the trap is sprung
here rather than on `main`.
"""

from __future__ import annotations

from typing import Any

import yaml

from tests.completeness.registry import REPO_ROOT

WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
REQUIRED_CONTEXT = "gate"
REQUIRED_PLATFORMS = {"ubuntu-latest", "windows-latest", "macos-latest"}


def _workflow() -> dict[str, Any]:
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def _jobs() -> dict[str, Any]:
    # `on:` parses to the boolean True under the YAML 1.1 rules PyYAML follows,
    # which is a known wart and harmless here -- `jobs` is read by name.
    return dict(_workflow()["jobs"])


def test_gate_job_is_required() -> None:
    """Section 3.3: the status check must be named exactly `gate`.

    Branch protection already requires that literal string -- the piped `gh api`
    response in HANDOFF.md records `contexts: ["gate"]`. A job producing any
    other context leaves `main` permanently unmergeable.

    The job must also be matrix-free. GitHub names matrix checks
    `gate (ubuntu-latest)`, so a single matrix job called `gate` produces three
    contexts and none of them is `gate` -- which looks green and blocks anyway.
    """
    jobs = _jobs()

    assert REQUIRED_CONTEXT in jobs, (
        f"no job named {REQUIRED_CONTEXT!r}; branch protection requires that "
        f"exact context and would block every merge. Jobs: {sorted(jobs)}"
    )

    gate = jobs[REQUIRED_CONTEXT]
    assert (
        gate.get("name", REQUIRED_CONTEXT) == REQUIRED_CONTEXT
    ), "the job's `name:` overrides the context, and it must remain `gate`"
    assert "strategy" not in gate, (
        "the `gate` job must not be a matrix job: a matrix produces "
        "`gate (os)` contexts and never a bare `gate`"
    )
    assert gate.get("needs"), "the `gate` job must depend on the matrix it aggregates"


def test_gate_job_fails_closed_on_a_non_success_matrix() -> None:
    """A skipped or cancelled matrix is not a passing matrix.

    `if: always()` means the aggregate job runs even when the matrix fails, so
    the aggregation must test for success explicitly rather than relying on the
    job being skipped -- a skipped required check is not a passing one, and
    reasoning about which is which is exactly where this goes wrong.
    """
    gate = _jobs()[REQUIRED_CONTEXT]
    script = "\n".join(str(step.get("run", "")) for step in gate["steps"])

    assert "!= 'success'" in script or '!= "success"' in script
    assert "exit 1" in script


def test_os_matrix_covers_windows() -> None:
    """Section 5.2. Linux is primary; Windows and macOS are supported, not assumed.

    The ledger lock is `fcntl.flock` on POSIX and `msvcrt.locking` on Windows,
    and this is a library people will `pip install`. An untested lock on someone
    else's machine is a silently forked hash chain.
    """
    matrix_platforms: set[str] = set()
    for job in _jobs().values():
        strategy = job.get("strategy") or {}
        matrix = strategy.get("matrix") or {}
        matrix_platforms.update(str(value) for value in matrix.get("os", []))

    assert (
        matrix_platforms >= REQUIRED_PLATFORMS
    ), f"the OS matrix is missing {sorted(REQUIRED_PLATFORMS - matrix_platforms)}"


def test_ci_runs_the_gate_itself() -> None:
    """The matrix runs `python tools/gate.py`, not a hand-copied subset of it.

    This is also P0.GATE's call site: a workflow `run:` step is a genuine
    invocation edge, and the gate having no invoker was a real manifest failure
    until this workflow existed.
    """
    runs = [
        str(step.get("run", "")) for job in _jobs().values() for step in (job.get("steps") or [])
    ]

    assert any("tools/gate.py" in run for run in runs), runs


def test_ci_checks_out_full_history() -> None:
    """A shallow clone makes two checkers silently weaker rather than loudly broken.

    `check_attribution` reads the full history and `check_spec_isolation` diffs
    against `origin/main`. Under `fetch-depth: 1` both still exit zero, having
    examined almost nothing.
    """
    depths = [
        (step.get("with") or {}).get("fetch-depth")
        for job in _jobs().values()
        for step in (job.get("steps") or [])
        if "checkout" in str(step.get("uses", ""))
    ]

    assert depths, "no checkout step found"
    assert all(str(depth) == "0" for depth in depths), depths
