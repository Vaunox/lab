#!/usr/bin/env python
"""Spec and code never travel in the same PR. Deep dive P0 section 8.

> The cheapest way to pass a manifest gate is to edit the manifest.

The manifest blocks the merge, the manifest is in the repo, and the builder has
write access to the repo. A ratchet is not a ratchet if the builder is holding
the wrench, so the tier the builder is judged by is placed out of the builder's
reach within any PR that also carries implementation.

Logs are exempt and must be: the handoff is *required* to travel with the code it
describes. A log records what happened; it does not decide what must happen.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# Section 8. Prefix sets, and the distinction is load-bearing -- see `classify`.
SPEC_PATHS = (
    "CONSTITUTION.md",
    "CONTRACTS.md",
    "ACCEPTANCE.md",
    "PLAYBOOK.md",
    "docs/deep_dives/",
)
CODE_PATHS = (
    "src/",
    "tools/",
    "tests/",
    "pyproject.toml",
    "Makefile",
    ".github/",
)
LOG_PATHS = (
    "HANDOFF.md",
    "DEAD_ENDS.md",
    "PROJECT_STATE.md",
    "DIVERGENCES.md",
    "DEFERRALS.md",
)

# The status-check context branch protection requires (section 3.3). The
# bootstrap exception is open exactly while no workflow on origin/main produces
# it, which is what makes the exception self-closing rather than permanent.
REQUIRED_CHECK = "gate"

# Fixture seam. Unreachable in any tree that has a .git -- see `changed_paths`.
FIXTURE_DIFF = "FIXTURE_CHANGED_FILES"


@dataclass
class Report:
    """Which tiers the diff touched, and whether that combination is allowed."""

    spec: list[str] = field(default_factory=list)
    code: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    exception_applies: bool = False

    @property
    def mixed(self) -> bool:
        return bool(self.spec) and bool(self.code)

    @property
    def ok(self) -> bool:
        return not self.mixed or self.exception_applies


class SpecIsolationError(RuntimeError):
    """The checker cannot run. Distinct from the checker finding a violation."""


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def classify(paths: list[str]) -> Report:
    """Sort changed paths into the three tiers. Section 8.

    Matching is by PREFIX and never by substring, and that is not a stylistic
    preference. The planted fixtures live at
    `tests/completeness/fixtures/*/docs/deep_dives/*.md` -- a substring test for
    "docs/deep_dives/" classifies a test fixture as a governance document, and
    the checker then reports every commit that touches a fixture as a spec-and-
    code violation. The rule would be turned off inside a day, and it would
    deserve to be.

    Logs are checked first because the exemption must win: `HANDOFF.md` is
    required to travel with code, and a tier order that let it match anything
    else would break the one carve-out section 8 insists on.
    """
    report = Report()
    for path in paths:
        normalised = path.replace("\\", "/").strip()
        if not normalised:
            continue
        if normalised.startswith(LOG_PATHS):
            report.logs.append(normalised)
        elif normalised.startswith(SPEC_PATHS):
            report.spec.append(normalised)
        elif normalised.startswith(CODE_PATHS):
            report.code.append(normalised)
    return report


def changed_paths(root: Path) -> list[str]:
    """The diff under judgement: `git diff --name-only origin/main...HEAD`.

    A tree carrying a `.git` is always read from git. The fixture seam below is
    reachable only in a tree that has none, which is what stops it being a
    bypass: dropping a FIXTURE_CHANGED_FILES into the real repository does
    nothing at all, because the real repository has a `.git`.
    """
    if (root / ".git").exists():
        result = _git(root, "diff", "--name-only", "origin/main...HEAD")
        if result.returncode != 0:
            raise SpecIsolationError(
                f"cannot diff origin/main...HEAD in {root}: {result.stderr.strip()}"
            )
        return result.stdout.splitlines()

    fixture = root / FIXTURE_DIFF
    if not fixture.exists():
        raise SpecIsolationError(
            f"{root} is not a git repository and carries no {FIXTURE_DIFF}; "
            "there is no diff to judge, and no diff is not a clean diff"
        )
    return fixture.read_text(encoding="utf-8").splitlines()


def bootstrap_exception_applies(root: Path) -> bool:
    """Whether section 5.4's one-PR exception is still open.

    Branch protection requires a `gate` status check that no workflow produces
    until `ci.yml` exists, so no PR -- spec or code -- can merge until one
    carrying CI does. Section 11.1 is therefore unenforceable during P0 *by
    construction*, and exactly one PR is permitted to mix the tiers: the first.

    The exception closes itself. Once a workflow on `origin/main` defines the
    `gate` job, the condition that justified the exception is gone and this
    returns False for every subsequent PR. Nobody has to remember to switch it
    off, which is the only kind of exception worth writing.

    An unknown bootstrap state is treated as closed, not open. A tree with no
    git to interrogate does not get an exception it cannot demonstrate it is
    entitled to.
    """
    if not (root / ".git").exists():
        return False

    listing = _git(root, "ls-tree", "-r", "origin/main", "--name-only", "--", ".github/workflows/")
    if listing.returncode != 0:
        return False

    for workflow in listing.stdout.splitlines():
        if not workflow.strip():
            continue
        blob = _git(root, "show", f"origin/main:{workflow.strip()}")
        if blob.returncode != 0:
            continue
        try:
            document = yaml.safe_load(blob.stdout)
        except yaml.YAMLError:
            continue
        jobs = (document or {}).get("jobs", {}) or {}
        for job_id, job in jobs.items():
            name = str((job or {}).get("name", job_id))
            if name == REQUIRED_CHECK or job_id == REQUIRED_CHECK:
                return False
    return True


def check(root: Path, *, assume_gate_on_main: bool = False) -> Report:
    """Judge the diff. Section 8."""
    report = classify(changed_paths(root))
    report.exception_applies = not assume_gate_on_main and bootstrap_exception_applies(root)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Spec isolation (deep dive P0 section 8).")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument(
        "--assume-gate-on-main",
        action="store_true",
        help=(
            "treat the section 5.4 bootstrap exception as already closed. Only "
            "ever tightens: there is deliberately no flag that opens it"
        ),
    )
    args = parser.parse_args(argv)

    try:
        report = check(args.root, assume_gate_on_main=args.assume_gate_on_main)
    except SpecIsolationError as exc:
        print(f"check_spec_isolation: REFUSED TO RUN: {exc}", file=sys.stderr)
        return 2

    if report.ok:
        if report.mixed:
            print(
                "check_spec_isolation: spec and code both touched, permitted by "
                "the section 5.4 bootstrap exception -- no workflow on "
                "origin/main produces the 'gate' check yet. This exception "
                "closes itself the moment one does."
            )
        else:
            print(
                f"check_spec_isolation: clean -- spec {len(report.spec)}, "
                f"code {len(report.code)}, logs {len(report.logs)} (exempt)"
            )
        return 0

    print(
        "check_spec_isolation: this PR touches BOTH the spec tier and the code "
        "tier. The builder may not edit the thing that judges the builder "
        "(section 11.1). Ship the spec change in its own PR, with its "
        "amendment-log entry attached.",
        file=sys.stderr,
    )
    for path in report.spec:
        print(f"  SPEC  {path}", file=sys.stderr)
    for path in report.code:
        print(f"  CODE  {path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
