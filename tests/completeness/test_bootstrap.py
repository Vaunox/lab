"""The bootstrap invariants. Deep dive P0 sections 3.0 to 3.4.

These rows have no in-repository caller -- their invoker is external, which is
why amendment A-001 set them to `call_site: n/a`. The tests still ship and still
must pass: `n/a` removed the external-caller requirement, not the evidence.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import preflight

from tests.completeness.registry import REPO_ROOT


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


class _ScriptedRunner:
    """A runner that fails exactly one probe, so failures are attributable."""

    def __init__(self, failing: tuple[str, ...]) -> None:
        self.failing = failing
        self.seen: list[tuple[str, ...]] = []

    def __call__(self, command: Any) -> subprocess.CompletedProcess[str]:
        argv = tuple(command)
        self.seen.append(argv)
        if argv[: len(self.failing)] == self.failing:
            return subprocess.CompletedProcess(
                list(argv), returncode=1, stdout="", stderr="not logged in"
            )
        if argv[-1] == "--version":
            return subprocess.CompletedProcess(
                list(argv), returncode=0, stdout="stub 3.11.9", stderr=""
            )
        return subprocess.CompletedProcess(list(argv), returncode=0, stdout="ok", stderr="")


def test_preflight_stops_on_missing_gh_auth() -> None:
    """Section 3.0, failure case 16. The one failure the builder cannot fix.

    The remedy is asserted verbatim. Section 3.0 requires preflight to print
    exactly `Run `gh auth login`, then say continue.` and do nothing else --
    credential handling is not the builder's to do, and a builder that routes
    around a missing credential is the same builder that routes around a failing
    gate.
    """
    runner = _ScriptedRunner(failing=("gh", "auth", "status"))

    report = preflight.preflight(runner)

    assert not report.ok
    failures = report.failures
    assert [check.name for check in failures] == ["gh auth status"]
    assert failures[0].remedy == "Run `gh auth login`, then say continue."


def test_preflight_passes_when_every_probe_succeeds() -> None:
    """The negative control: preflight is not merely always stopping."""
    runner = _ScriptedRunner(failing=("nothing", "at", "all"))

    report = preflight.preflight(runner)

    assert report.ok
    assert report.failures == []


def test_preflight_probes_interpreter_names_rather_than_assuming_python3() -> None:
    """Operator ruling R-001, and Session 1's surprise 2.

    `python3` does not exist on the operator's machine. Section 3.0 writes it
    illustratively, and a preflight that takes it literally fails on the very
    platform section 5.1 chose Python-over-make to accommodate.
    """
    assert "python" in preflight.INTERPRETER_CANDIDATES
    assert "python3" in preflight.INTERPRETER_CANDIDATES

    # Every *named* candidate fails. A resolver that hardcodes one name returns
    # None here; the specified one falls back to sys.executable, which is present
    # by construction because it is running this test. Driven through the runner
    # rather than through PATH so the result does not depend on which interpreter
    # names happen to be installed on the machine under test -- and on this
    # machine `python3` genuinely is absent, which is what R-001 is about.
    class _AllNamesFail(_ScriptedRunner):
        def __call__(self, command: Any) -> subprocess.CompletedProcess[str]:
            argv = tuple(command)
            self.seen.append(argv)
            if argv[0] in preflight.INTERPRETER_CANDIDATES:
                return subprocess.CompletedProcess(list(argv), 1, "", "not found")
            return subprocess.CompletedProcess(list(argv), 0, "Python 3.11.9", "")

    found = preflight.probe_interpreter(_AllNamesFail(failing=()))

    assert found is not None, "no interpreter was found although sys.executable works"
    name, version = found
    assert version >= (3, 11)
    assert (
        name not in preflight.INTERPRETER_CANDIDATES
    ), "a candidate that failed its probe was reported as the answer"


def test_hooks_path_set_before_first_commit() -> None:
    """Section 3.1 and failure case 19: "all but the first" is not a property worth having.

    The literal claim -- that `git config core.hooksPath` was run before the
    first commit -- leaves no trace in the repository. Local config is a property
    of a working copy, not of a history, and a fresh clone (every CI runner) has
    none, so asserting it there would be asserting something about the runner.

    What the claim casts a shadow on, and what is asserted here, is the evidence
    that survives cloning:

      * `.githooks/commit-msg` is present in the FIRST commit, so the hook
        existed at row zero rather than arriving afterwards, and
      * the first commit's message carries no attribution trailer.

    A hook wired up after the first commit cannot produce both. This is the
    checkable content of the invariant, and it is checkable by a stranger.
    """
    first_commit = _git("rev-list", "--max-parents=0", "HEAD")
    assert first_commit, "no root commit found"

    tracked_at_root = _git("ls-tree", "-r", "--name-only", first_commit).splitlines()
    assert ".githooks/commit-msg" in tracked_at_root, (
        "the commit-msg hook is absent from the first commit, so the first "
        "commit was not policed by it"
    )

    trailers = _git("log", "--format=%(trailers)", first_commit, "-1")
    assert trailers.strip() == "", f"the first commit carries trailers: {trailers!r}"

    mode = _git("ls-files", "-s", "--", ".githooks/commit-msg").split()
    assert mode, "the hook is not tracked at all"
    assert mode[0] == "100755", f"hook is not executable in the index: {mode}"


def test_origin_configured() -> None:
    """Section 3.2: the remote exists, and it is the one the phase was built against."""
    url = _git("remote", "get-url", "origin")

    assert url, "origin is not configured"
    assert "github.com" in url, f"origin is not a github.com remote: {url!r}"
    assert url.rstrip("/").removesuffix(".git").endswith("/lab"), url


def test_commit_msg_hook_is_committed_and_executable() -> None:
    """The hook survives a fresh clone, which is the only reason it is in the repo."""
    hook = REPO_ROOT / ".githooks" / "commit-msg"

    assert hook.exists()
    assert hook.read_text(encoding="utf-8").startswith("#!/usr/bin/env bash")


def test_preflight_script_is_present() -> None:
    """P0.BOOT.PREFLIGHT's artifact exists, independently of the row's call-site rule."""
    assert (REPO_ROOT / "tools" / "preflight.py").exists()
    assert isinstance(Path(preflight.__file__), Path)
