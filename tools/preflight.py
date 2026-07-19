#!/usr/bin/env python
"""Session-0 preflight. Deep dive P0 section 3.0.

Run before touching anything. Each failure has exactly one remedy, and the
builder states it and stops.

**`gh auth status` is the one thing the builder cannot fix.** Authentication is
the operator's; the builder does not handle credentials, does not run
`gh auth login`, and does not touch a token. On that failure it prints the remedy
and stops -- it does not proceed with a local-only repository and add the remote
later, because later never comes and a phase merged with no protected `main`
means the section 3.3 invariant was never true.

**Interpreter names are probed, never assumed** (operator ruling R-001). Section
3.0 writes `python3 --version` illustratively; on Windows -- the operator's
primary platform, and the platform section 5.1 chose Python over `make` to
accommodate -- there is no `python3`. A preflight that fails there fails for the
person it was written for.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

MINIMUM_PYTHON = (3, 11)
INTERPRETER_CANDIDATES: tuple[str, ...] = ("python", "python3", "py")

REMEDY_GH_AUTH = "Run `gh auth login`, then say continue."
REMEDY_GIT = "Install git, then re-run preflight."
REMEDY_GH = "Install the GitHub CLI (`gh`), then re-run preflight."
REMEDY_PYTHON = f"Install Python >= {MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]}, then re-run preflight."

VERSION_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")

Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class Check:
    """One preflight probe: what was asked, what came back, and the one remedy."""

    name: str
    ok: bool
    detail: str
    remedy: str = ""


@dataclass
class Report:
    checks: list[Check] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)

    @property
    def failures(self) -> list[Check]:
        return [check for check in self.checks if not check.ok]


def default_runner(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Run a probe. Absent executables become a non-zero result, never an exception."""
    try:
        return subprocess.run(list(command), capture_output=True, text=True, check=False)
    except (OSError, ValueError) as exc:
        return subprocess.CompletedProcess(
            list(command), returncode=127, stdout="", stderr=str(exc)
        )


def check_git(runner: Runner = default_runner) -> Check:
    result = runner(["git", "--version"])
    return Check(
        name="git",
        ok=result.returncode == 0,
        detail=result.stdout.strip() or result.stderr.strip(),
        remedy="" if result.returncode == 0 else REMEDY_GIT,
    )


def check_gh(runner: Runner = default_runner) -> Check:
    result = runner(["gh", "--version"])
    first = (result.stdout.strip() or result.stderr.strip()).splitlines()
    return Check(
        name="gh",
        ok=result.returncode == 0,
        detail=first[0] if first else "",
        remedy="" if result.returncode == 0 else REMEDY_GH,
    )


def check_gh_auth(runner: Runner = default_runner) -> Check:
    """The one failure the builder cannot fix, and must not try to.

    Section 3.0 and failure case 16. The remedy is printed verbatim and nothing
    else happens: credential handling is not the builder's to do, and a builder
    that works around a missing credential is the same builder that works around
    a failing gate.
    """
    result = runner(["gh", "auth", "status"])
    return Check(
        name="gh auth status",
        ok=result.returncode == 0,
        detail=(
            (result.stdout.strip() or result.stderr.strip()).splitlines()[0]
            if (result.stdout.strip() or result.stderr.strip())
            else "not authenticated"
        ),
        remedy="" if result.returncode == 0 else REMEDY_GH_AUTH,
    )


def parse_version(text: str) -> tuple[int, int] | None:
    match = VERSION_RE.search(text)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def probe_interpreter(runner: Runner = default_runner) -> tuple[str, tuple[int, int]] | None:
    """Find an interpreter meeting the floor, trying each candidate name in turn.

    `sys.executable` is tried last and always: whatever is running this file is
    by construction present, so a machine with no `python` and no `python3` on
    PATH still reports honestly rather than failing on a naming convention.
    """
    for name in (*INTERPRETER_CANDIDATES, sys.executable):
        if name != sys.executable and shutil.which(name) is None:
            continue
        result = runner([name, "--version"])
        if result.returncode != 0:
            continue
        version = parse_version(result.stdout.strip() or result.stderr.strip())
        if version is not None and version >= MINIMUM_PYTHON:
            return name, version
    return None


def check_python(runner: Runner = default_runner) -> Check:
    found = probe_interpreter(runner)
    if found is None:
        return Check(
            name="python",
            ok=False,
            detail=f"no interpreter >= {MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]} found",
            remedy=REMEDY_PYTHON,
        )
    name, version = found
    return Check(name="python", ok=True, detail=f"{name} {version[0]}.{version[1]}")


def preflight(runner: Runner = default_runner) -> Report:
    """Run every section 3.0 probe."""
    return Report(
        checks=[
            check_git(runner),
            check_gh(runner),
            check_gh_auth(runner),
            check_python(runner),
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preflight (deep dive P0 section 3.0).")
    parser.parse_args(argv)

    report = preflight()
    for check in report.checks:
        status = "ok  " if check.ok else "FAIL"
        print(f"  {status}  {check.name}: {check.detail}")

    if report.ok:
        print("preflight: passed. No operator action required.")
        return 0

    print("\npreflight: STOP.", file=sys.stderr)
    for check in report.failures:
        print(check.remedy, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
